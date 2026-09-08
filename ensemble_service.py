"""
Ensemble entre múltiplos provedores de LLM (Google, Anthropic, Groq, OpenAI) para a
geração da função de transferência.

Cada provedor configurado (com chave de API presente) responde à mesma pergunta em
paralelo; o consenso final é decidido por equivalência simbólica via SymPy
(`ft_verification.rationals_equivalent_safe`), não por comparação de string — duas FTs
escritas diferente mas matematicamente iguais (ex.: "1/(RCs+1)" e "1/(1+RCs)") contam
como o mesmo voto. Segue a estratégia de self-consistency descrita na Seção 2.4 do
trabalho (WANG et al., 2022): amostragem paralela + seleção por frequência.

Provedores sem chave configurada são simplesmente pulados — o ensemble só roda de fato
com pelo menos 2 provedores disponíveis; com menos que isso, não há "consenso" possível.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Optional

from config import settings
from prompts import SYSTEM_PROMPT, formatar_prompt_ft
from llm_service import _parse_json_from_text
from ft_verification import parse_transfer_function_expr, rationals_equivalent_safe

logger = logging.getLogger("ensemble_service")


@dataclass
class ProviderResponse:
    """Resultado de um único provedor para a mesma pergunta."""

    provedor: str
    modelo: str
    sucesso: bool
    funcao_transferencia: Optional[str] = None
    erro: Optional[str] = None


@dataclass
class EnsembleOutcome:
    executado: bool
    respostas: list[ProviderResponse] = field(default_factory=list)
    consenso_ft: Optional[str] = None
    concordancia: Optional[str] = None  # ex.: "2/3"
    mensagem: Optional[str] = None


def _extrair_ft(texto_resposta: str) -> str:
    """
    Tenta extrair a FT via JSON estruturado (mesmo contrato do endpoint /gerar-apenas-ft);
    se o provedor não seguir o formato, recua para o texto bruto — `parse_transfer_function_expr`
    já sabe extrair "G(s) = ..." de texto livre/verboso.
    """
    try:
        data = _parse_json_from_text(texto_resposta)
        ft = data.get("funcao_transferencia")
        if isinstance(ft, str) and ft.strip():
            return ft
    except Exception:  # noqa: BLE001 — domínio: formatos arbitrários entre 3 provedores
        pass
    return texto_resposta


def _call_google(prompt: str) -> str:
    from llm_service import get_llm_service

    payload = get_llm_service().generate(prompt)
    ft = payload.get("funcao_transferencia")
    return ft if isinstance(ft, str) and ft.strip() else str(payload)


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ensemble_timeout)
    resp = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    texto = resp.choices[0].message.content or ""
    return _extrair_ft(texto)


def _call_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=settings.ensemble_timeout)
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = "".join(getattr(bloco, "text", "") for bloco in resp.content)
    return _extrair_ft(texto)


def _call_groq(prompt: str) -> str:
    # API da Groq é compatível com o formato da OpenAI — mesmo SDK `openai`, só troca a
    # `base_url`. Tier gratuito, sem cartão de crédito (console.groq.com/keys).
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=settings.ensemble_timeout,
    )
    resp = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    texto = resp.choices[0].message.content or ""
    return _extrair_ft(texto)


# (disponível?, função de chamada, modelo configurado) por provedor.
_PROVIDERS: dict[str, tuple[Callable[[], bool], Callable[[str], str], Callable[[], str]]] = {
    "google": (lambda: bool(settings.google_api_key), _call_google, lambda: settings.llm_model),
    "anthropic": (
        lambda: bool(settings.anthropic_api_key),
        _call_anthropic,
        lambda: settings.anthropic_model,
    ),
    "groq": (lambda: bool(settings.groq_api_key), _call_groq, lambda: settings.groq_model),
    "openai": (lambda: bool(settings.openai_api_key), _call_openai, lambda: settings.openai_model),
}


def provedores_disponiveis() -> list[str]:
    """Provedores com chave de API configurada, na ordem fixa google -> anthropic -> groq -> openai."""
    return [nome for nome, (disponivel, _, _) in _PROVIDERS.items() if disponivel()]


def _agrupar_por_equivalencia(respostas: list[ProviderResponse]) -> list[list[ProviderResponse]]:
    """Agrupa respostas bem-sucedidas em classes de equivalência simbólica (não por string)."""
    grupos: list[list[ProviderResponse]] = []
    expr_por_provedor: dict[str, object] = {}

    for r in respostas:
        if not r.sucesso or not r.funcao_transferencia:
            continue
        try:
            expr = parse_transfer_function_expr(r.funcao_transferencia)
        except Exception as exc:  # noqa: BLE001 — domínio: texto arbitrário de 3 provedores
            logger.warning("Ensemble: FT de '%s' não parseável: %s", r.provedor, exc)
            continue

        colocado = False
        for grupo in grupos:
            ref_expr = expr_por_provedor[grupo[0].provedor]
            if rationals_equivalent_safe(expr, ref_expr):
                grupo.append(r)
                colocado = True
                break
        if not colocado:
            grupos.append([r])
        expr_por_provedor[r.provedor] = expr

    grupos.sort(key=len, reverse=True)
    return grupos


def run_ensemble_ft(descricao: str) -> EnsembleOutcome:
    """Chama todos os provedores configurados em paralelo e apura o consenso simbólico."""
    provedores = provedores_disponiveis()
    if not settings.ensemble_enabled or len(provedores) < 2:
        return EnsembleOutcome(
            executado=False,
            mensagem=(
                "Ensemble não executado: são necessários pelo menos 2 provedores com chave "
                f"de API configurada (disponíveis: {provedores or 'nenhum'})."
            ),
        )

    prompt = formatar_prompt_ft(descricao)
    respostas: list[ProviderResponse] = []

    with ThreadPoolExecutor(max_workers=len(provedores)) as executor:
        futuros = {executor.submit(_PROVIDERS[nome][1], prompt): nome for nome in provedores}
        for futuro in as_completed(futuros):
            nome = futuros[futuro]
            modelo = _PROVIDERS[nome][2]()
            try:
                ft = futuro.result()
                respostas.append(
                    ProviderResponse(provedor=nome, modelo=modelo, sucesso=True, funcao_transferencia=ft)
                )
            except Exception as exc:  # noqa: BLE001 — domínio: rede/API de 3 provedores distintos
                logger.warning("Ensemble: provedor '%s' falhou: %s", nome, exc)
                respostas.append(ProviderResponse(provedor=nome, modelo=modelo, sucesso=False, erro=str(exc)))

    ordem = {nome: i for i, nome in enumerate(provedores)}
    respostas.sort(key=lambda r: ordem[r.provedor])

    grupos = _agrupar_por_equivalencia(respostas)
    if not grupos:
        return EnsembleOutcome(
            executado=True,
            respostas=respostas,
            mensagem="Nenhum provedor produziu uma FT parseável; sem consenso possível.",
        )

    maior_grupo = grupos[0]
    total_sucesso = sum(1 for r in respostas if r.sucesso)
    return EnsembleOutcome(
        executado=True,
        respostas=respostas,
        consenso_ft=maior_grupo[0].funcao_transferencia,
        concordancia=f"{len(maior_grupo)}/{total_sucesso}",
    )


# -----------------------------------------------------------------------------
# Camada de verificação: FT já obtida por outro meio x consenso do ensemble
# -----------------------------------------------------------------------------


@dataclass
class EnsembleVerificationOutcome:
    """Resultado de checar uma FT já gerada contra o consenso do ensemble."""

    executado: bool
    ok: bool = True
    concordancia: Optional[str] = None
    consenso_ft: Optional[str] = None
    mensagem: Optional[str] = None


def verify_ft_with_ensemble(descricao: str, ft_primaria: str) -> EnsembleVerificationOutcome:
    """
    Roda o ensemble completo para `descricao` e verifica se `ft_primaria` (já obtida por um
    dos endpoints principais, tipicamente do Google) é simbolicamente equivalente ao consenso.

    Camada de verificação adicional, no mesmo espírito de `ft_verification.py` e
    `graph_validation.py`: nunca bloqueia a resposta. Se o ensemble não rodar (menos de 2
    provedores configurados) ou não houver FT parseável em nenhum provedor, `ok=True` —
    a ausência de dados não reprova nada, só fica registrada como `executado=False`.
    """
    outcome = run_ensemble_ft(descricao)
    if not outcome.executado:
        return EnsembleVerificationOutcome(executado=False, ok=True, mensagem=outcome.mensagem)
    if outcome.consenso_ft is None:
        return EnsembleVerificationOutcome(
            executado=True, ok=True, mensagem=outcome.mensagem, concordancia=outcome.concordancia
        )

    try:
        primaria_expr = parse_transfer_function_expr(ft_primaria)
        consenso_expr = parse_transfer_function_expr(outcome.consenso_ft)
        concorda = rationals_equivalent_safe(primaria_expr, consenso_expr)
    except Exception as exc:  # noqa: BLE001 — domínio: texto arbitrário de múltiplos provedores
        return EnsembleVerificationOutcome(
            executado=True,
            ok=True,
            concordancia=outcome.concordancia,
            consenso_ft=outcome.consenso_ft,
            mensagem=f"ensemble: não foi possível comparar com o consenso ({exc})",
        )

    return EnsembleVerificationOutcome(
        executado=True,
        ok=concorda,
        concordancia=outcome.concordancia,
        consenso_ft=outcome.consenso_ft,
        mensagem=(
            None
            if concorda
            else (
                "ensemble: a FT gerada não é equivalente ao consenso entre provedores "
                f"(consenso: {outcome.consenso_ft}, concordância {outcome.concordancia})."
            )
        ),
    )
