"""
Testes da validação por grafos (Fórmula de Ganho de Mason).

Cada teste de redução compara o resultado de `mason_reduce` com a fórmula clássica
conhecida do circuito equivalente, verificando `sympy.simplify(obtido - esperado) == 0`
em vez de igualdade de string (a forma simbólica pode variar).
"""

import os
import sys

import pytest
import sympy
from sympy import simplify, symbols

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_validation import (
    DiagramGraph,
    GraphEdge,
    GraphNode,
    GraphValidationError,
    mason_reduce,
    verify_diagram_graph,
)


def _expr_equal(a, b) -> bool:
    return simplify(a - b) == 0


@pytest.mark.unit
def test_bloco_unico_em_serie():
    """entrada -> G -> saida  =>  T = G"""
    s = symbols("s")
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="1/(s+1)"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="g", sinal="+"),
            GraphEdge(origem="g", destino="y", sinal="+"),
        ],
    )
    t = mason_reduce(graph)
    assert _expr_equal(t, 1 / (s + 1))


@pytest.mark.unit
def test_dois_blocos_em_cascata():
    """entrada -> G1 -> G2 -> saida  =>  T = G1*G2"""
    s = symbols("s")
    K = symbols("K")
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g1", tipo="bloco", ganho="K"),
            GraphNode(id="g2", tipo="bloco", ganho="1/(s+2)"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="g1"),
            GraphEdge(origem="g1", destino="g2"),
            GraphEdge(origem="g2", destino="y"),
        ],
    )
    t = mason_reduce(graph)
    assert _expr_equal(t, K / (s + 2))


@pytest.mark.unit
def test_realimentacao_unitaria_negativa():
    """
    Malha clássica: T = G / (1 + G).
    Usa símbolo de uma letra ('G') de propósito: o parser reaproveitado de
    ft_verification.py aplica multiplicação implícita (é assim que "RCs" vira
    R*C*s), então um nome de ganho de duas letras sem dígito, como "Gc", seria
    lido como G*c em vez de um símbolo único — comportamento herdado e correto
    para o caso RC, mas que exige nomes de 1 letra (ou com dígito, tipo "G1")
    para ganhos avulsos como este.
    """
    G = symbols("G")
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="soma", tipo="somador"),
            GraphNode(id="g", tipo="bloco", ganho="G"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="soma", sinal="+"),
            GraphEdge(origem="soma", destino="g", sinal="+"),
            GraphEdge(origem="g", destino="y", sinal="+"),
            GraphEdge(origem="y", destino="soma", sinal="-"),
        ],
    )
    t = mason_reduce(graph)
    assert _expr_equal(t, G / (1 + G))


@pytest.mark.unit
def test_realimentacao_com_h_no_ramo():
    """Malha com H(s) no ramo de realimentação: T = G / (1 + G*H)"""
    G, H = symbols("G H")
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="soma", tipo="somador"),
            GraphNode(id="g", tipo="bloco", ganho="G"),
            GraphNode(id="y", tipo="saida"),
            GraphNode(id="h", tipo="bloco", ganho="H"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="soma", sinal="+"),
            GraphEdge(origem="soma", destino="g", sinal="+"),
            GraphEdge(origem="g", destino="y", sinal="+"),
            GraphEdge(origem="y", destino="h", sinal="+"),
            GraphEdge(origem="h", destino="soma", sinal="-"),
        ],
    )
    t = mason_reduce(graph)
    assert _expr_equal(t, G / (1 + G * H))


@pytest.mark.unit
def test_dois_lacos_nao_tocantes():
    """
    Dois laços de realimentação independentes em cascata — exercita o termo de
    pares não-tocantes (ΣL2) da Fórmula de Mason, não só o caso trivial de 1 laço.
    T = p*r / [(1+p*q)*(1+r*t)]
    """
    p, q, r, t = symbols("p q r t")
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="suma", tipo="somador"),
            GraphNode(id="g1", tipo="bloco", ganho="p"),
            GraphNode(id="f1", tipo="bloco", ganho="q"),
            GraphNode(id="sumb", tipo="somador"),
            GraphNode(id="g2", tipo="bloco", ganho="r"),
            GraphNode(id="f2", tipo="bloco", ganho="t"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="suma", sinal="+"),
            GraphEdge(origem="suma", destino="g1", sinal="+"),
            GraphEdge(origem="g1", destino="sumb", sinal="+"),
            GraphEdge(origem="sumb", destino="g2", sinal="+"),
            GraphEdge(origem="g2", destino="y", sinal="+"),
            # laço 1: em torno de g1
            GraphEdge(origem="g1", destino="f1", sinal="+"),
            GraphEdge(origem="f1", destino="suma", sinal="-"),
            # laço 2: em torno de g2 (não compartilha nós com o laço 1)
            GraphEdge(origem="g2", destino="f2", sinal="+"),
            GraphEdge(origem="f2", destino="sumb", sinal="-"),
        ],
    )
    mason_t = mason_reduce(graph)
    esperado = (p * r) / ((1 + p * q) * (1 + r * t))
    assert _expr_equal(mason_t, esperado)


@pytest.mark.unit
def test_verify_diagram_graph_ft_coerente():
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="1/(R*C*s+1)"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="g"),
            GraphEdge(origem="g", destino="y"),
        ],
    )
    out = verify_diagram_graph(graph, "G(s) = 1 / (RCs + 1)")
    assert out.ok is True
    assert out.ft_derivada_grafo is not None


@pytest.mark.unit
def test_verify_diagram_graph_ft_incoerente():
    """Grafo desenha só um bloco 1/(RCs+1), mas a FT declarada é outra — deve reprovar."""
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="1/(R*C*s+1)"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="g"),
            GraphEdge(origem="g", destino="y"),
        ],
    )
    out = verify_diagram_graph(graph, "G(s) = RCs / (RCs + 1)")
    assert out.ok is False
    assert any("não é equivalente" in p for p in out.problemas)


@pytest.mark.unit
def test_grafo_desconectado_reporta_erro():
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="1/(s+1)"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[GraphEdge(origem="u", destino="g")],  # falta g -> y
    )
    with pytest.raises(GraphValidationError, match="desconectado"):
        mason_reduce(graph)

    out = verify_diagram_graph(graph, "G(s) = 1/(s+1)")
    assert out.ok is False


@pytest.mark.unit
def test_ganho_nao_parseavel_reporta_erro():
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="isso nao eh uma expressao valida ((("),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="g"),
            GraphEdge(origem="g", destino="y"),
        ],
    )
    out = verify_diagram_graph(graph, "G(s) = 1/(s+1)")
    assert out.ok is False
    assert any("não parseável" in p for p in out.problemas)


@pytest.mark.unit
def test_quantidade_errada_de_entradas_ou_saidas():
    graph_sem_saida = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="1/(s+1)"),
        ],
        arestas=[GraphEdge(origem="u", destino="g")],
    )
    with pytest.raises(GraphValidationError, match="saida"):
        mason_reduce(graph_sem_saida)
