"""
Verificação pós-geração da função de transferência (anti-delírio leve).

- Sempre tenta parsing simbólico (forma racional em s).
- Casos canônicos: compara com referência SymPy + grau do denominador.
- Diagrama físico: heurística de layout em duas colunas quando a descrição é mecânica translacional.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Optional

from sympy import degree, fraction, simplify, symbols
from sympy.core.expr import Expr
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


Transformations = standard_transformations + (implicit_multiplication_application,)


def _strip_accents(text: str) -> str:
    nk = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nk if not unicodedata.combining(c))


def normalize_descricao(text: str) -> str:
    return " ".join(_strip_accents(text).lower().split())


def descricao_esquema_fisico_mecanico(descricao: str) -> bool:
    """
    Heurística: enunciados que devem obrigar dois painéis (físico + blocos).
    """
    d = normalize_descricao(descricao)

    # `d` já passou por normalize_descricao (sem acentos); formas acentuadas nunca
    # casariam aqui, então mantemos só as variantes que de fato podem aparecer.
    mechanics = (
        "massa",
        "mola",
        "molad",
        "amortecedor",
        "amortec",
        "suspensao",
    )
    if not any(k in d for k in mechanics):
        return False

    hints = (
        "deslocamento",
        "forca",
        "grau de liberdade",
        "newton",
        "translaci",
        "mecani",
    )
    if any(h in d for h in hints):
        return True
    if ("massa" in d or "massas" in d) and ("mola" in d or "molas" in d):
        return True
    return False


def codigo_diagrama_sugere_layout_fisico_blocos(codigo: str) -> bool:
    """Detecta layout típico 1×2 (esquema físico | diagrama de blocos)."""
    c = codigo.lower()
    c_nospace = c.replace(" ", "")
    if "subplots" in c and "1,2" in c_nospace:
        return True
    if re.search(r"\bsubplots\s*\(\s*1\s*,\s*2\b", c):
        return True
    if re.search(r"\bsubplot\s*\(\s*1\s*,\s*2\s*,", c):
        return True
    if "gridspec" in c and "ncols=2" in c_nospace:
        return True
    return False


_GS_ASSIGN = re.compile(r"[Gg]\s*\(\s*s\s*\)\s*=")
_STATEMENT_BOUNDARY = re.compile(r"[\n\r]|(?<=[a-zA-Z0-9\)\]])\.\s")


def _clean_math_unicode(text: str) -> str:
    """Normaliza notação matemática de texto livre (LLM) para sintaxe SymPy/Python."""
    text = text.replace("·", "*").replace("×", "*")
    text = text.replace("²", "**2").replace("³", "**3")
    text = text.replace("^", "**")
    # Alguns modelos usam colchetes como agrupamento matemático ("Kt / [X + Y]"),
    # que em Python/SymPy formam um literal de lista, não uma expressão.
    return text.replace("[", "(").replace("]", ")")


_MARKDOWN_WRAPPER = re.compile(r"^(?:\*\*|`)+|(?:\*\*|`)+$")


def _statement_rhs(tail: str) -> Optional[str]:
    """Restringe `tail` à mesma sentença/linha e devolve o último segmento pós-'='."""
    boundary = _STATEMENT_BOUNDARY.search(tail)
    statement = tail[: boundary.start()] if boundary else tail
    segments = statement.split("=")
    rhs = segments[-1].strip()
    rhs = _MARKDOWN_WRAPPER.sub("", rhs).strip()  # bordas de **negrito**/`código` markdown
    return _clean_math_unicode(rhs) if rhs else None


def _candidate_rhs_list(ft_raw: str) -> list[str]:
    """
    Gera candidatos a lado-direito de 'G(s) = ...', na ordem em que aparecem no texto.

    Modelos mais verbosos costumam reapresentar a FT várias vezes ('G(s) = Vc(s)/Vin(s)'
    como definição provisória, uma forma "padrão" genérica de comparação, e só então a
    expressão final/reduzida) — às vezes na mesma sentença encadeada ('G(s) = razão =
    expressão'), às vezes em declarações 'G(s) = ...' totalmente separadas mais adiante
    no texto. `parse_transfer_function_expr` tenta estes candidatos do ÚLTIMO para o
    PRIMEIRO, porque a forma final/mais reduzida tende a vir por último.
    """
    s = ft_raw.strip()
    matches = list(_GS_ASSIGN.finditer(s))
    candidates: list[str] = []
    for m in matches:
        rhs = _statement_rhs(s[m.end() :])
        if rhs:
            candidates.append(rhs)
    if candidates:
        return candidates

    # Fallback leniente: nenhum "G(s) =" literal — aceita o primeiro '=' genérico,
    # caso o modelo nomeie a razão de outra forma (ex.: "Y(s)/U(s) = ...").
    generic = re.search(r"=\s*", s)
    if generic:
        rhs = _statement_rhs(s[generic.end() :])
        if rhs:
            candidates.append(rhs)
    return candidates


_SUBSCRIPT_ID = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*\d+)\b")


def _local_dict_for_rhs(rhs: str) -> dict[str, Expr]:
    """Variáveis locais para parse_expr, incluindo identificadores com subíndice (M1, K2, ...)."""
    s_sym = symbols("s")
    local: dict[str, Expr] = {"s": s_sym}
    for match in _SUBSCRIPT_ID.finditer(rhs):
        name = match.group(1)
        if name not in local:
            local[name] = symbols(name)
    return local


_GENERIC_TEMPLATE_SYMBOLS = {
    "K", "τ", "tau", "ωn", "wn", "ω", "omega", "ζ", "zeta", "ξ",
    # "ωn" (ômega-n) não sobrevive como um símbolo só: a multiplicação implícita do
    # parser (a mesma que faz "RCs" virar R*C*s) o decompõe em "ω" * "n" — então "n"
    # sozinho também entra na lista, só nesse contexto de forma padrão de controle.
    "n",
}


def _looks_like_generic_template(expr: Expr) -> bool:
    """
    True quando a expressão só usa símbolos convencionais de "forma padrão" de
    controle (K, τ, ωn, ζ, ...). LLMs costumam citar essa forma genérica para
    comparação pedagógica ("compare com G(s) = K·ωn²/(s²+2ζωn·s+ωn²)") depois de já
    terem dado a resposta específica do problema — não é a expressão que queremos
    comparar com o gabarito, que usa os parâmetros físicos do enunciado (R, L, C, M...).
    """
    names = {str(sym) for sym in expr.free_symbols} - {"s"}
    return bool(names) and names.issubset(_GENERIC_TEMPLATE_SYMBOLS)


def parse_transfer_function_expr(ft_string: str) -> Expr:
    """
    Converte 'G(s) = ...' em expressão SymPy (variável simbólica s + demais identificadores).

    Quando o texto contém mais de uma declaração 'G(s) = ...', tenta a última primeiro
    (ver `_candidate_rhs_list`) e recua para as anteriores se a mais recente não fizer
    parse, ou se só usar símbolos de "forma padrão" genérica (ver
    `_looks_like_generic_template`) — assim nem uma definição provisória mal-formada
    ('G(s) = Vc(s)/Vin(s):') nem uma citação didática da forma padrão genérica impedem
    a leitura da expressão específica do problema.
    """
    candidates = _candidate_rhs_list(ft_string)
    if not candidates:
        raise ValueError("FT sem '=' explícito (esperado 'G(s) = ...').")

    last_error: Optional[Exception] = None
    generic_fallback: Optional[Expr] = None
    for rhs in reversed(candidates):
        try:
            parsed = simplify(
                parse_expr(rhs, transformations=Transformations, local_dict=_local_dict_for_rhs(rhs))
            )
        except Exception as exc:  # noqa: BLE001 — domínio: strings arbitrárias do LLM
            last_error = exc
            continue
        if _looks_like_generic_template(parsed):
            if generic_fallback is None:
                generic_fallback = parsed
            continue
        return parsed

    if generic_fallback is not None:
        return generic_fallback
    raise ValueError(f"Nenhuma expressão de G(s) pôde ser interpretada: {last_error}")


def deg_den_in_s(expr: Expr) -> int:
    s_sym = symbols("s")
    n, d = fraction(simplify(expr))
    if d == 1:
        return 0
    return int(degree(d, s_sym))


def rationals_equivalent_safe(user: Expr, ref: Expr) -> bool:
    u_expr = simplify(user)
    r_expr = simplify(ref)
    n_u, d_u = fraction(u_expr)
    n_r, d_r = fraction(r_expr)
    return simplify(n_u * d_r - n_r * d_u) == 0


@dataclass
class CanonicalCase:
    id: str
    description_match: Callable[[str], bool]
    expected_denom_degree: int
    reference_expr: Expr


def _match_rc_vc(d: str) -> bool:
    if any(x in d for x in ("indutor", "bobina")):
        return False  # é RLC (tem indutor), não RC — evita colidir com o gabarito rlc_serie_vc
    if not any(x in d for x in ("rc", "resistor", "resistencia")):
        return False
    if not any(x in d for x in ("capacitor", "capacitancia")):
        return False
    if not any(x in d for x in ("serie", "em serie", "circuito rc")):
        return False
    # A mera presença de "capacitor" já foi checada acima; aqui exigimos uma frase que
    # aponte a SAÍDA no capacitor — senão um RC com saída no resistor (G(s) = RCs/(RCs+1))
    # seria comparado (e rejeitado) contra o gabarito de Vc/Vin por engano.
    if not any(
        x in d
        for x in (
            "vc",
            "tensao no capacitor",
            "saida no capacitor",
            "sobre o capacitor",
        )
    ):
        return False
    return True


def _is_multi_dof_mecanico(d: str) -> bool:
    """Detecta enunciados com dois (ou mais) GDL mecânicos translacionais."""
    if any(x in d for x in ("duas massas", "2 massas", "dois graus", "2 graus", "multiplas massas")):
        return True
    if ("m1" in d or "massa m1" in d) and ("m2" in d or "massa m2" in d):
        return True
    if "chassi" in d and "roda" in d:
        return True
    if "quarto de" in d and "carro" in d:
        return True
    if ("k1" in d or "mola (k1)" in d or "mola k1" in d) and (
        "k2" in d or "mola (k2)" in d or "mola k2" in d
    ):
        return True
    return False


def _match_msd(d: str) -> bool:
    if _is_multi_dof_mecanico(d):
        return False
    if not any(x in d for x in ("massa", "bloco de massa", "bloco rigido")):
        return False
    if not any(x in d for x in ("mola", "molad", "molas")):
        return False
    if not any(x in d for x in ("forca", "force", "entrada f")):
        return False
    if not any(x in d for x in ("deslocamento", "posicao", "x(", " x ")):
        return False
    return True


def _match_quarter_car_x1_u(d: str) -> bool:
    """Suspensão quarter-car ativa: X1(s)/U(s) com duas massas acopladas."""
    if not _is_multi_dof_mecanico(d):
        return False
    if not any(x in d for x in ("mola", "molad", "molas", "amortecedor", "amortec")):
        return False
    if not any(x in d for x in ("atuador", "forca controlada")):
        return False
    if not any(x in d for x in ("deslocamento", "x1", " chassi")):
        return False
    return True


def _match_rlc_vc(d: str) -> bool:
    condensed = d.replace(" ", "")
    mentions_rlc = "rlc" in condensed or "circuito rlc" in d
    has_r = "resistor" in d or "resistencia" in d
    has_l = "indutor" in d or "bobina" in d
    has_c = "capacitor" in d or "capacit" in d
    has_three = has_r and has_l and has_c
    if not (mentions_rlc or has_three):
        return False
    # Idem RC: "capacitor" já é exigido acima (via has_c); só o casamos como Vc/Vin quando
    # a descrição aponta a saída explicitamente no capacitor.
    if not any(
        x in d
        for x in (
            "vc",
            "tensao no capacitor",
            "saida no capacitor",
        )
    ):
        return False
    serie_ok = any(x in d for x in ("serie", "em serie"))
    if not (serie_ok or mentions_rlc):
        return False
    return True


def _canonical_cases() -> list[CanonicalCase]:
    s_sym = symbols("s")
    R, C, L, M, B, K = symbols("R C L M B K")
    M1, M2, K1, K2, B1 = symbols("M1 M2 K1 K2 B1")

    rc_ref = 1 / (R * C * s_sym + 1)
    msd_ref = 1 / (M * s_sym**2 + B * s_sym + K)
    rlc_ref = 1 / (L * C * s_sym**2 + R * C * s_sym + 1)
    quarter_car_ref = (M2 * s_sym**2 + K2) / (
        M1 * M2 * s_sym**4
        + B1 * (M1 + M2) * s_sym**3
        + (K1 * (M1 + M2) + M1 * K2) * s_sym**2
        + B1 * K2 * s_sym
        + K1 * K2
    )

    return [
        CanonicalCase("rc_vc", _match_rc_vc, 1, rc_ref),
        CanonicalCase(
            "quarter_car_ativo_x1_u",
            _match_quarter_car_x1_u,
            4,
            quarter_car_ref,
        ),
        CanonicalCase("massa_mola_amort_desloc_vs_forca", _match_msd, 2, msd_ref),
        CanonicalCase("rlc_serie_vc", _match_rlc_vc, 2, rlc_ref),
    ]


def _matching_canonical(d_norm: str) -> Optional[CanonicalCase]:
    for case in _canonical_cases():
        if case.description_match(d_norm):
            return case
    return None


@dataclass
class FTVerificationOutcome:
    ok: bool
    problemas: list[str] = field(default_factory=list)
    caso_canonico_id: Optional[str] = None
    parseavel: bool = False
    layout_diagrama_fisico_ok: Optional[bool] = None


def verify_transfer_function(descricao: str, funcao_transferencia: str) -> FTVerificationOutcome:
    problemas: list[str] = []
    d_norm = normalize_descricao(descricao)

    try:
        user_expr = parse_transfer_function_expr(funcao_transferencia)
        parseavel = True
    except Exception as exc:  # noqa: BLE001 — domínio: strings arbitrárias do LLM
        return FTVerificationOutcome(
            ok=False,
            problemas=[f"parse_ft: falha ao interpretar G(s): {exc}"],
            caso_canonico_id=None,
            parseavel=False,
            layout_diagrama_fisico_ok=None,
        )

    caso = _matching_canonical(d_norm)
    if caso is None:
        return FTVerificationOutcome(
            ok=True,
            problemas=[],
            caso_canonico_id=None,
            parseavel=parseavel,
            layout_diagrama_fisico_ok=None,
        )

    canon_problems: list[str] = []
    if deg_den_in_s(user_expr) != caso.expected_denom_degree:
        canon_problems.append(
            f"cano_{caso.id}: grau esperado do denominador em s é {caso.expected_denom_degree}, "
            f"obtido {deg_den_in_s(user_expr)}."
        )

    if not rationals_equivalent_safe(user_expr, caso.reference_expr):
        canon_problems.append(
            f"cano_{caso.id}: expressão não é equivalente à referência canônica esperada para este enunciado."
        )

    problemas.extend(canon_problems)
    return FTVerificationOutcome(
        ok=len(canon_problems) == 0,
        problemas=problemas,
        caso_canonico_id=caso.id,
        parseavel=True,
        layout_diagrama_fisico_ok=None,
    )


_PHYSICAL_ELEMENT_HINTS = ("mola", "amortecedor", "amortec", "massa")


def codigo_menciona_elementos_fisicos(codigo: str) -> bool:
    """
    Heurística complementar ao layout 1×2: exige que o código ao menos rotule/mencione
    massa/mola/amortecedor, para não aceitar dois painéis estruturalmente corretos porém
    vazios (dois `plot([0])` genéricos, por exemplo) como esquema físico válido.
    """
    c = codigo.lower()
    return any(hint in c for hint in _PHYSICAL_ELEMENT_HINTS)


def verify_diagram_physical_layout(descricao: str, codigo_diagrama: str) -> Optional[FTVerificationOutcome]:
    """Retorna apenas flags de diagrama quando descrição for mecânica; senão None (N/A)."""
    if not descricao_esquema_fisico_mecanico(descricao):
        return None

    has_layout = codigo_diagrama_sugere_layout_fisico_blocos(codigo_diagrama)
    has_elements = codigo_menciona_elementos_fisicos(codigo_diagrama)
    if has_layout and has_elements:
        return FTVerificationOutcome(
            ok=True,
            problemas=[],
            caso_canonico_id=None,
            parseavel=False,
            layout_diagrama_fisico_ok=True,
        )

    problemas = []
    if not has_layout:
        problemas.append(
            "layout_diag: para sistema mecânico translacional, o código deve usar layout com "
            "**dois painéis lado a lado** (ex.: `plt.subplots(1, 2, ...)`): esquema físico (massas/"
            "molas/amortecedores rotulados) + diagrama de blocos no painel seguinte.",
        )
    if not has_elements:
        problemas.append(
            "layout_diag: o código não menciona massa/mola/amortecedor — dois painéis vazios "
            "não satisfazem o esquema físico exigido; rotule os elementos no painel esquerdo.",
        )
    return FTVerificationOutcome(
        ok=False,
        problemas=problemas,
        caso_canonico_id=None,
        parseavel=False,
        layout_diagrama_fisico_ok=False,
    )


def merge_outcomes_ft_e_diagrama(
    ft_out: FTVerificationOutcome,
    layout_out: Optional[FTVerificationOutcome],
) -> FTVerificationOutcome:
    if layout_out is None:
        return FTVerificationOutcome(
            ok=ft_out.ok,
            problemas=list(ft_out.problemas),
            caso_canonico_id=ft_out.caso_canonico_id,
            parseavel=ft_out.parseavel,
            layout_diagrama_fisico_ok=None,
        )

    ok = ft_out.ok and layout_out.ok
    prob = list(ft_out.problemas) + list(layout_out.problemas)
    return FTVerificationOutcome(
        ok=ok,
        problemas=prob,
        caso_canonico_id=ft_out.caso_canonico_id,
        parseavel=ft_out.parseavel,
        layout_diagrama_fisico_ok=layout_out.layout_diagrama_fisico_ok,
    )


def mensagem_verificacao_consolidada(out: FTVerificationOutcome) -> Optional[str]:
    """Mensagem curta para a API; None quando não há alerta."""

    def _ambi() -> bool:
        t = "; ".join(out.problemas).lower()
        return "ambig" in t or "incomplet" in t

    if out.ok:
        return None
    prefix = (
        "Atenção — verificação automática encontrou problema(s): "
        if not _ambi()
        else "Resposta tratada conservadoramente por ambiguidade ou inconsistência: "
    )
    return prefix + " ".join(out.problemas)
