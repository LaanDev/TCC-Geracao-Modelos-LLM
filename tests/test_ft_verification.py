"""Testes do verificador simbólico pós-LLM (casos canônicos e layout físico)."""

import os
import sys

import pytest
from sympy import degree, fraction, simplify, symbols

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ft_verification import (
    codigo_diagrama_sugere_layout_fisico_blocos,
    descricao_esquema_fisico_mecanico,
    merge_outcomes_ft_e_diagrama,
    parse_transfer_function_expr,
    verify_diagram_physical_layout,
    verify_transfer_function,
)


@pytest.mark.unit
class TestExtracaoFtEmTextoVerboso:
    """
    Regressão: o gemini-2.5-flash costuma devolver 'funcao_transferencia' embutida em
    texto corrido/markdown em vez de uma linha só — isso quebrava o parser mesmo quando
    a matemática estava certa (achado real do Caso de Teste 2 / RLC do Cap. 4).
    """

    def test_atribuicao_encadeada_com_continuacao_apos_quebra_de_linha(self):
        # Mesmo padrão do exemplo few-shot em prompts.py (PROMPT_FT contém este formato).
        ft = (
            "G(s) = Vc(s)/Vin(s) = 1 / (RCs + 1)\n\n"
            "Forma padrão de 1ª ordem: G(s) = K / (τs + 1)\n"
            "Onde: K = 1 (ganho DC) e τ = RC (constante de tempo)"
        )
        expr = parse_transfer_function_expr(ft)
        R, C, s = symbols("R C s")
        assert simplify(expr - 1 / (R * C * s + 1)) == 0

    def test_negrito_markdown_e_notacao_unicode_de_potencia_e_produto(self):
        ft = (
            "A função de transferência final do sistema RLC série é:\n\n"
            "**G(s) = Vc(s)/Vin(s) = 1 / (L · C · s² + R · C · s + 1)**\n\n"
            "Esta é a forma característica de uma função de transferência de 2ª ordem."
        )
        expr = parse_transfer_function_expr(ft)
        L, C, R, s = symbols("L C R s")
        assert simplify(expr - 1 / (L * C * s**2 + R * C * s + 1)) == 0

    def test_frase_apos_ponto_final_na_mesma_linha_nao_entra_na_extracao(self):
        ft = "G(s) = 1 / (s + 1). Este é um sistema de primeira ordem estável."
        expr = parse_transfer_function_expr(ft)
        s = symbols("s")
        assert simplify(expr - 1 / (s + 1)) == 0

    def test_formato_simples_de_uma_linha_continua_funcionando(self):
        expr = parse_transfer_function_expr("G(s) = 1 / (RCs + 1)")
        R, C, s = symbols("R C s")
        assert simplify(expr - 1 / (R * C * s + 1)) == 0

    def test_definicao_provisoria_seguida_de_forma_final_mais_adiante(self):
        """
        Achado real (2ª reexecução do Caso de Teste 2): o modelo escreve
        'G(s) = Vc(s)/Vin(s):' como definição provisória (não parseável — treinada
        pelo próprio ':' final), cita a forma padrão genérica com símbolos alheios ao
        problema (K, ωn, ζ) e só then, na ÚLTIMA linha, dá a expressão final reduzida
        em termos de R, L, C. Deve pular as duas primeiras e usar a última.
        """
        ft = (
            "A função de transferência G(s) é a razão entre a Transformada de Laplace "
            "da saída e a Transformada de Laplace da entrada. Do passo anterior:\n\n"
            "Vc(s) · (LCs² + RCs + 1) = Vin(s)\n\n"
            "Então, isolando G(s) = Vc(s)/Vin(s):\n\n"
            "**G(s) = 1 / (LCs² + RCs + 1)**\n\n"
            "Esta é a forma padrão de 2ª ordem, comparável com "
            "G(s) = K · ωn² / (s² + 2ζωn s + ωn²).\n\n"
            "Dividindo numerador e denominador por LC:\n\n"
            "G(s) = (1/LC) / (s² + (R/L)s + (1/LC))"
        )
        expr = parse_transfer_function_expr(ft)
        L, C, R, s = symbols("L C R s")
        assert simplify(expr - 1 / (L * C * s**2 + R * C * s + 1)) == 0

    def test_forma_padrao_com_parametro_fisico_misturado_a_tau_nao_vence(self):
        """
        Achado real (endpoint de análise térmica, verificação por grafos): o modelo
        substitui K pelo parâmetro físico real (R_th) mas mantém τ simbólico ("K = R_th
        e τ = R_th·C_th" definido só em prosa) na ÚLTIMA declaração "G(s) = ...". Como
        essa expressão mistura R_th (não-genérico) com τ (genérico), o filtro antigo
        (`_looks_like_generic_template`, que exige TODOS os símbolos genéricos) não a
        rejeitava — fazendo o parser comparar contra "R_th/(τs+1)" em vez da forma
        expandida "R_th/(R_th·C_th·s+1)", que é a que bate com o grafo estrutural.
        """
        ft = (
            "G(s) = R_th / (R_th * C_th * s + 1)\n\n"
            "Na forma padrão de 1ª ordem, G(s) = K / (τs + 1), "
            "onde K = R_th (ganho DC) e τ = R_th * C_th (constante de tempo)."
        )
        expr = parse_transfer_function_expr(ft)
        R_th, C_th, s = symbols("R_th C_th s")
        assert simplify(expr - R_th / (R_th * C_th * s + 1)) == 0

    def test_notacao_t_de_malha_fechada_e_reconhecida_como_g(self):
        """
        Achado real (endpoint de análise completa, verificação por grafos): para
        sistemas de malha fechada, o modelo costuma nomear a FT resultante "T(s)"
        (convenção padrão para FT de malha fechada, reservando "G(s)" para o caminho
        direto) em vez de "G(s)" — o que o extrator antigo (só reconhecia "G(s) =")
        nunca encontrava, caindo no fallback lenient que pega o primeiro "=" do texto
        (nesse caso, uma frase de definição informal "T(s) = Y(s)/R(s), e:", não
        parseável) em vez da equação de verdade, mais adiante no texto.
        """
        ft = (
            "A função de transferência de malha fechada, T(s) = Y(s)/R(s), é:\n\n"
            "T(s) = K / (s^2 + 3s + (2 + K * H))\n\n"
            "Esta é a forma padrão de uma função de transferência de segunda ordem."
        )
        expr = parse_transfer_function_expr(ft)
        s, K, H = symbols("s K H")
        assert simplify(expr - K / (s**2 + 3 * s + (2 + K * H))) == 0

    def test_subscrito_g_mf_de_malha_fechada_e_reconhecido(self):
        """
        Achado real (mesmo endpoint): quando o modelo nomeia a FT de malha fechada
        "G_mf(s)" (subscrito, "malha fechada") em vez de "G(s)" puro, o extrator antigo
        (só reconhecia "G(s) =" ou "T(s) =" adjacentes, sem subscrito) não encontrava
        nenhum candidato correspondente a essa linha — sobrando só a citação didática da
        forma padrão genérica (K·ωn²/...) mais adiante no texto, que então "vencia" por
        ser o único candidato disponível.
        """
        ft = (
            "A função de transferência de malha fechada do sistema, relacionando a "
            "saída Y(s) com a referência R(s), é:\n\n"
            "**G_mf(s) = Y(s) / R(s) = K / (s^2 + 3s + (2 + K * H))**\n\n"
            "Esta é a forma padrão de uma função de transferência de segunda ordem. "
            "Podemos compará-la com a forma geral:\n\n"
            "G(s) = K * ωn² / (s² + 2ζωn s + ωn²)"
        )
        expr = parse_transfer_function_expr(ft)
        s, K, H = symbols("s K H")
        assert simplify(expr - K / (s**2 + 3 * s + (2 + K * H))) == 0

    def test_crase_de_codigo_e_colchetes_como_agrupamento(self):
        """
        Achado real (Caso de Teste 5 / motor CC): o modelo envolveu a FT em crases de
        código inline e usou colchetes como agrupamento matemático ("Kt / [X]"), que em
        Python/SymPy formam um literal de lista em vez de uma expressão — sem a
        conversão de colchetes para parênteses, isso nem chega a fazer parse.

        Não comparamos com uma expressão "bonita" reconstruída à mão porque nomes de
        duas letras sem dígito (Kt, La, Ra, Kb) são deliberadamente decompostos pela
        multiplicação implícita do parser em K*t, L*a, etc. (mesma convenção que faz
        "RCs" virar R*C*s) — o que importa aqui é que o parse não falha mais, e que a
        estrutura resultante (grau 3 no denominador, com fator de s isolado) bate com
        o sistema de 3ª ordem esperado.
        """
        ft = (
            "A função de transferência final é:\n\n"
            "`G(s) = Θ(s) / Va(s) = Kt / [La·J · s³ + (Ra·J + La·B) · s² + "
            "(Ra·B + Kt·Kb) · s]`\n\n"
            "Podemos fatorar `s` do denominador para uma análise mais clara:\n\n"
            "`G(s) = Kt / [s · (La·J · s² + (Ra·J + La·B) · s + (Ra·B + Kt·Kb))]`"
        )
        expr = parse_transfer_function_expr(ft)
        s = symbols("s")
        assert degree(fraction(expr)[1], s) == 3


@pytest.mark.unit
def test_verify_rc_canonical_passa():
    desc = (
        "Circuito com resistor R e capacitor C em série. "
        "Entrada: tensão da fonte Vin. Saída: tensão no capacitor Vc."
    )
    ft = "G(s) = 1 / (RCs + 1)"
    out = verify_transfer_function(desc, ft)
    assert out.ok is True
    assert out.caso_canonico_id == "rc_vc"


@pytest.mark.unit
def test_verify_rc_canonical_fracasso_numerador():
    desc = (
        "Circuito RC em série com saída no capacitor Vc "
        "(entrada Vin). Derive Vc/Vin."
    )
    ft = "G(s) = R / (RCs + 1)"
    out = verify_transfer_function(desc, ft)
    assert out.ok is False
    assert out.caso_canonico_id == "rc_vc"


@pytest.mark.unit
def test_verify_rc_com_saida_no_resistor_nao_usa_gabarito_vc():
    """
    RC série mencionando 'capacitor' apenas como componente, com saída no RESISTOR, não pode
    ser comparado ao gabarito de Vc/Vin — regressão do falso positivo em _match_rc_vc.
    """
    desc = (
        "Circuito com resistor R e capacitor C em série. Entrada: tensão da fonte Vin. "
        "Saída: tensão sobre o resistor VR."
    )
    ft_correta_para_vr = "G(s) = RCs / (RCs + 1)"
    out = verify_transfer_function(desc, ft_correta_para_vr)
    assert out.caso_canonico_id is None
    assert out.ok is True


@pytest.mark.unit
def test_verify_rlc_nao_colide_com_gabarito_rc():
    """
    Regressão: descrição de RLC série menciona resistor+capacitor+série+'tensão sobre o
    capacitor' — tudo que _match_rc_vc exige — então também batia (errado) com o
    gabarito de RC (grau 1) em vez do gabarito de RLC (grau 2), rejeitando a FT correta.
    """
    desc = (
        "Um circuito elétrico é composto por um resistor 'R', um indutor 'L' e um "
        "capacitor 'C' conectados em série a uma fonte de tensão de entrada 'Vin(t)'. "
        "Considere a tensão sobre o capacitor, 'Vc(t)', como a saída do sistema."
    )
    ft = "G(s) = 1 / (L*C*s**2 + R*C*s + 1)"
    out = verify_transfer_function(desc, ft)
    assert out.caso_canonico_id == "rlc_serie_vc"
    assert out.ok is True


@pytest.mark.unit
def test_verify_msd_canonical_passa():
    desc = (
        "Bloco de massa M, mola K e amortecedor B em série com parede; "
        "entrada força F, saída deslocamento x."
    )
    ft = "G(s) = 1/(M*s**2+B*s+K)"
    out = verify_transfer_function(desc, ft)
    assert out.ok is True
    assert out.caso_canonico_id == "massa_mola_amort_desloc_vs_forca"


@pytest.mark.unit
def test_verify_quarter_car_ativo_passa():
    desc = (
        "Um sistema de suspensão ativa do quarto de um carro é composto pela massa do chassi (M1) "
        "e a massa da roda (M2). O chassi está conectado à roda por uma mola (K1) e um amortecedor "
        "(B1) em paralelo. A roda está conectada ao solo por uma mola (K2) que representa o pneu. "
        "Um atuador hidráulico gera uma força controlada (u) entre o chassi e a roda. "
        "Encontre G(s) = X1(s)/U(s), deslocamento vertical do chassi."
    )
    ft = (
        "G(s) = (M2*s^2 + K2) / (M1*M2*s^4 + B1*(M1 + M2)*s^3 + "
        "(K1*(M1 + M2) + M1*K2)*s^2 + B1*K2*s + K1*K2)"
    )
    out = verify_transfer_function(desc, ft)
    assert out.ok is True
    assert out.caso_canonico_id == "quarter_car_ativo_x1_u"


@pytest.mark.unit
def test_suspensao_ativa_nao_cai_no_msd_1gdl():
    desc = (
        "Suspensão ativa do quarto de um carro: massa do chassi (M1), massa da roda (M2), "
        "mola K1, amortecedor B1, mola K2 no pneu, atuador com força u, saída deslocamento X1."
    )
    ft_wrong_1gdl = "G(s) = 1/(M*s**2+B*s+K)"
    out = verify_transfer_function(desc, ft_wrong_1gdl)
    assert out.caso_canonico_id == "quarter_car_ativo_x1_u"
    assert out.ok is False


@pytest.mark.unit
def test_descricao_mecanica_detectada():
    desc = "Duas massas M1 e M2 ligadas por mola k2 com amortecedores b."
    assert descricao_esquema_fisico_mecanico(desc) is True


@pytest.mark.unit
def test_layout_fisico_exige_subplots():
    desc = (
        "Sistema massa-mola-amortecedor translacional com massa M, "
        "mola K e amortecedor B; força F e deslocamento x."
    )
    bad = "import matplotlib.pyplot as plt\nplt.figure(); plt.plot([0, 1])\nplt.show()"
    out = verify_diagram_physical_layout(desc, bad)
    assert out is not None
    assert out.ok is False

    ok_code = (
        "import matplotlib.pyplot as plt\n"
        "_, (a, b) = plt.subplots(1, 2)\n"
        "a.text(0.5, 0.5, 'Massa M, mola K e amortecedor B')\n"
        "b.plot([0])\nplt.show()"
    )
    out2 = verify_diagram_physical_layout(desc, ok_code)
    assert out2 is not None
    assert out2.ok is True


@pytest.mark.unit
def test_layout_fisico_rejeita_dois_paineis_vazios():
    """Estrutura 1x2 correta não basta: sem rótulos de massa/mola/amortecedor, é reprovado."""
    desc = (
        "Sistema massa-mola-amortecedor translacional com massa M, "
        "mola K e amortecedor B; força F e deslocamento x."
    )
    paineis_vazios = (
        "import matplotlib.pyplot as plt\n"
        "_, (a, b) = plt.subplots(1, 2); a.plot([0]); b.plot([0])\nplt.show()"
    )
    out = verify_diagram_physical_layout(desc, paineis_vazios)
    assert out is not None
    assert out.ok is False
    assert out.layout_diagrama_fisico_ok is False


@pytest.mark.unit
def test_codigo_detecta_subplot_1x2():
    assert codigo_diagrama_sugere_layout_fisico_blocos("plt.subplot ( 1 , 2 , 1)") is True
    assert codigo_diagrama_sugere_layout_fisico_blocos("plt.plot([1])") is False


@pytest.mark.unit
def test_merge_ft_e_layout():
    from ft_verification import FTVerificationOutcome

    ft_ok = FTVerificationOutcome(ok=True, parseavel=True)
    lay_bad = FTVerificationOutcome(
        ok=False,
        problemas=["layout_diag: ..."],
        layout_diagrama_fisico_ok=False,
        parseavel=False,
    )
    merged = merge_outcomes_ft_e_diagrama(ft_ok, lay_bad)
    assert merged.ok is False
    assert merged.layout_diagrama_fisico_ok is False
