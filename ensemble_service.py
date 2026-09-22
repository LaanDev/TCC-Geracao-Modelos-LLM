"""
Ensemble: vários LLMs geram a análise completa em paralelo; o voto escolhe o resultado.

Cada provedor com chave configurada recebe o mesmo prompt de análise completa.
O consenso é a FT mais frequente por equivalência simbólica (SymPy), não por string.
A análise inteira do provedor vencedor é o que a API devolve.

Com menos de 2 provedores (ou ENSEMBLE_ENABLED=false) não há voto: usa-se o único
provedor disponível (em geral o Google).
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Optional

from config import settings
from ft_verification import parse_transfer_function_expr, rationals_equivalent_safe
from llm_service import _parse_json_from_text
from prompts import SYSTEM_PROMPT, formatar_prompt_analise_completa

logger = logging.getLogger("ensemble_service")

_CAMPOS_ANALISE = (
    "lei_aplicada",
    "equacao_diferencial",
    "passos_laplace",
    "funcao_transferencia",
    "analise_resultado",
    "codigo_diagrama",
    "grafo_diagrama",
)


@dataclass
class ProviderResponse:
    provedor: str
    modelo: str
    sucesso: bool
    funcao_transferencia: Optional[str] = None
    payload: Optional[dict] = None
    erro: Optional[str] = None


@dataclass
class EnsembleOutcome:
    executado: bool
    respostas: list[ProviderResponse] = field(default_factory=list)
    consenso_ft: Optional[str] = None
    concordancia: Optional[str] = None
    mensagem: Optional[str] = None
    payload_vencedor: Optional[dict] = None
    provedor_vencedor: Optional[str] = None


def _validar_analise(data: dict) -> dict:
    from schemas import AnaliseCompletaResponse

    filtrado = {k: data[k] for k in _CAMPOS_ANALISE if k in data}
    return AnaliseCompletaResponse(**filtrado).model_dump()


def _call_google(prompt: str) -> dict:
    from llm_service import get_llm_service
    from schemas import AnaliseCompletaResponse

    payload = get_llm_service().generate(prompt, AnaliseCompletaResponse)
    return _validar_analise(payload)


def _call_openai(prompt: str) -> dict:
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
    return _validar_analise(_parse_json_from_text(texto))


def _call_anthropic(prompt: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(
        api_key=settings.anthropic_api_key, timeout=settings.ensemble_timeout
    )
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = "".join(getattr(bloco, "text", "") for bloco in resp.content)
    return _validar_analise(_parse_json_from_text(texto))


def _call_groq(prompt: str) -> dict:
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
    return _validar_analise(_parse_json_from_text(texto))


_PROVIDERS: dict[str, tuple[Callable[[], bool], Callable[[str], dict], Callable[[], str]]] = {
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
    """Provedores com chave, na ordem google → anthropic → groq → openai."""
    return [nome for nome, (disponivel, _, _) in _PROVIDERS.items() if disponivel()]


def _agrupar_por_equivalencia(respostas: list[ProviderResponse]) -> list[list[ProviderResponse]]:
    """Agrupa análises bem-sucedidas em classes de equivalência simbólica da FT."""
    grupos: list[list[ProviderResponse]] = []
    expr_por_provedor: dict[str, object] = {}

    for r in respostas:
        if not r.sucesso or not r.funcao_transferencia:
            continue
        try:
            expr = parse_transfer_function_expr(r.funcao_transferencia)
        except Exception as exc:  # noqa: BLE001 — texto arbitrário de vários provedores
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


def _consultar(nomes: list[str], prompt: str) -> list[ProviderResponse]:
    respostas: list[ProviderResponse] = []
    with ThreadPoolExecutor(max_workers=max(len(nomes), 1)) as executor:
        futuros = {executor.submit(_PROVIDERS[nome][1], prompt): nome for nome in nomes}
        for futuro in as_completed(futuros):
            nome = futuros[futuro]
            modelo = _PROVIDERS[nome][2]()
            try:
                payload = futuro.result()
                ft = payload.get("funcao_transferencia")
                respostas.append(
                    ProviderResponse(
                        provedor=nome,
                        modelo=modelo,
                        sucesso=True,
                        funcao_transferencia=ft if isinstance(ft, str) else None,
                        payload=payload,
                    )
                )
            except Exception as exc:  # noqa: BLE001 — rede/API de provedores distintos
                logger.warning("Ensemble: provedor '%s' falhou: %s", nome, exc)
                respostas.append(
                    ProviderResponse(provedor=nome, modelo=modelo, sucesso=False, erro=str(exc))
                )

    ordem = {nome: i for i, nome in enumerate(nomes)}
    respostas.sort(key=lambda r: ordem[r.provedor])
    return respostas


def _escolher_vencedor(respostas: list[ProviderResponse]) -> EnsembleOutcome:
    grupos = _agrupar_por_equivalencia(respostas)
    total_sucesso = sum(1 for r in respostas if r.sucesso)
    if not grupos:
        primeiro_ok = next((r for r in respostas if r.sucesso and r.payload), None)
        return EnsembleOutcome(
            executado=True,
            respostas=respostas,
            mensagem="Nenhum provedor produziu uma FT parseável; sem consenso possível.",
            payload_vencedor=primeiro_ok.payload if primeiro_ok else None,
            provedor_vencedor=primeiro_ok.provedor if primeiro_ok else None,
        )

    vencedor = grupos[0][0]
    return EnsembleOutcome(
        executado=True,
        respostas=respostas,
        consenso_ft=vencedor.funcao_transferencia,
        concordancia=f"{len(grupos[0])}/{total_sucesso}",
        payload_vencedor=vencedor.payload,
        provedor_vencedor=vencedor.provedor,
    )


def run_ensemble_analise(descricao: str) -> EnsembleOutcome:
    """Gera a análise com os provedores disponíveis e devolve o payload vencedor."""
    provedores = provedores_disponiveis()
    if not provedores:
        return EnsembleOutcome(
            executado=False,
            mensagem="Nenhum provedor de LLM com chave de API configurada.",
        )

    prompt = formatar_prompt_analise_completa(descricao)
    votar = settings.ensemble_enabled and len(provedores) >= 2
    nomes = provedores if votar else provedores[:1]
    respostas = _consultar(nomes, prompt)

    if not votar:
        escolhido = next((r for r in respostas if r.sucesso and r.payload), None)
        return EnsembleOutcome(
            executado=False,
            respostas=respostas,
            payload_vencedor=escolhido.payload if escolhido else None,
            provedor_vencedor=escolhido.provedor if escolhido else None,
            consenso_ft=escolhido.funcao_transferencia if escolhido else None,
            mensagem=(
                "Ensemble não executado: são necessários pelo menos 2 provedores com chave "
                f"de API configurada (disponíveis: {provedores})."
                if settings.ensemble_enabled
                else "Ensemble desabilitado (ENSEMBLE_ENABLED=false)."
            ),
        )

    return _escolher_vencedor(respostas)
