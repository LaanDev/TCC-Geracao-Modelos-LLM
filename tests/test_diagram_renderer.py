"""
Testes do renderizador determinístico do diagrama de blocos (`diagram_renderer.py`).

Reaproveita os mesmos grafos clássicos de `test_graph_validation.py` (bloco único,
cascata, realimentação unitária, realimentação com H, dois laços não-tocantes) —
o objetivo aqui não é reavaliar a Fórmula de Mason, e sim garantir que o desenho
não depende do LLM e não quebra para nenhuma dessas topologias.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagram_renderer import render_diagram_graph
from graph_validation import DiagramGraph, GraphEdge, GraphNode, GraphValidationError

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _assert_valid_png(png_bytes: bytes) -> None:
    assert isinstance(png_bytes, bytes)
    assert png_bytes.startswith(_PNG_MAGIC)
    assert len(png_bytes) > 500  # PNG vazio/corrompido não passaria disso


@pytest.mark.unit
def test_render_bloco_unico_em_serie():
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
    _assert_valid_png(render_diagram_graph(graph))


@pytest.mark.unit
def test_render_dois_blocos_em_cascata():
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
    _assert_valid_png(render_diagram_graph(graph))


@pytest.mark.unit
def test_render_realimentacao_unitaria_negativa():
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
    _assert_valid_png(render_diagram_graph(graph))


@pytest.mark.unit
def test_render_realimentacao_com_h_no_ramo():
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
    _assert_valid_png(render_diagram_graph(graph))


@pytest.mark.unit
def test_render_dois_lacos_nao_tocantes():
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
            GraphEdge(origem="g1", destino="f1", sinal="+"),
            GraphEdge(origem="f1", destino="suma", sinal="-"),
            GraphEdge(origem="g2", destino="f2", sinal="+"),
            GraphEdge(origem="f2", destino="sumb", sinal="-"),
        ],
    )
    _assert_valid_png(render_diagram_graph(graph))


@pytest.mark.unit
def test_render_ganho_nao_parseavel_nao_quebra_desenho():
    """Ganho inválido não impede o desenho — só cai no texto puro em vez do LaTeX."""
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="isso nao eh uma expressao valida((("),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[
            GraphEdge(origem="u", destino="g"),
            GraphEdge(origem="g", destino="y"),
        ],
    )
    _assert_valid_png(render_diagram_graph(graph))


@pytest.mark.unit
def test_render_grafo_desconectado_levanta_erro():
    graph = DiagramGraph(
        nos=[
            GraphNode(id="u", tipo="entrada"),
            GraphNode(id="g", tipo="bloco", ganho="1/(s+1)"),
            GraphNode(id="y", tipo="saida"),
        ],
        arestas=[GraphEdge(origem="u", destino="g")],  # falta g -> y
    )
    with pytest.raises(GraphValidationError):
        render_diagram_graph(graph)
