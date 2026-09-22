"""
Validação estrutural do diagrama de blocos via grafo de fluxo de sinal.

Reduz um grafo (blocos com ganho + somadores + arestas com sinal) à função de
transferência equivalente pela Fórmula de Ganho de Mason, e compara simbolicamente
(SymPy) o resultado com a FT declarada pelo LLM. Isso é uma checagem de coerência
*topológica* real — diferente da heurística textual em ft_verification.py
(codigo_diagrama_sugere_layout_fisico_blocos), que só olha se o código "parece"
certo (dois painéis + palavras-chave), sem nunca confirmar que o diagrama desenhado
de fato reduz à FT anunciada.

A lógica de redução está ligada ao fluxo único `/gerar-analise-completa`:
`prompts.py` pede `grafo_diagrama` e `main.py` chama `_attach_graph_verification()`.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Literal, Optional

import sympy
from pydantic import BaseModel, Field
from sympy import Expr, simplify

from ft_verification import parse_transfer_function_expr, rationals_equivalent_safe


# -----------------------------------------------------------------------------
# Estrutura do grafo (o que o LLM emite em "grafo_diagrama")
# -----------------------------------------------------------------------------


class GraphNode(BaseModel):
    """Um bloco, somador, ou terminal (entrada/saída) do diagrama."""

    id: str
    tipo: Literal["bloco", "somador", "entrada", "saida"]
    ganho: Optional[str] = Field(
        None,
        description="Expressão em s (ex.: '1/(R*C*s+1)'); usado só quando tipo='bloco'.",
    )


class GraphEdge(BaseModel):
    """Uma conexão de sinal entre dois nós, com a polaridade usada em somadores."""

    origem: str
    destino: str
    sinal: Literal["+", "-"] = "+"


class DiagramGraph(BaseModel):
    """Grafo completo do diagrama: exatamente 1 nó 'entrada' e 1 nó 'saida'."""

    nos: list[GraphNode]
    arestas: list[GraphEdge]


class GraphValidationError(Exception):
    """Grafo malformado ou irredutível (desconectado, Δ=0, ganho não parseável)."""


@dataclass
class GraphVerificationOutcome:
    ok: bool
    problemas: list[str] = field(default_factory=list)
    ft_derivada_grafo: Optional[str] = None


# -----------------------------------------------------------------------------
# Montagem do grafo
# -----------------------------------------------------------------------------


def _node_by_id(graph: DiagramGraph) -> dict[str, GraphNode]:
    by_id = {n.id: n for n in graph.nos}
    if len(by_id) != len(graph.nos):
        raise GraphValidationError("IDs de nós duplicados no grafo.")
    return by_id


def _single_node_of_type(graph: DiagramGraph, tipo: str) -> GraphNode:
    matches = [n for n in graph.nos if n.tipo == tipo]
    if len(matches) != 1:
        raise GraphValidationError(
            f"Esperava exatamente 1 nó do tipo '{tipo}', encontrado {len(matches)}."
        )
    return matches[0]


def _node_gain(node: GraphNode) -> Expr:
    if node.tipo != "bloco":
        return sympy.Integer(1)
    if not node.ganho:
        raise GraphValidationError(f"Nó '{node.id}' é bloco mas não tem 'ganho'.")
    try:
        return parse_transfer_function_expr(f"G(s) = {node.ganho}")
    except Exception as exc:  # noqa: BLE001 — domínio: strings arbitrárias do LLM
        raise GraphValidationError(f"Ganho do nó '{node.id}' não parseável: {exc}") from exc


def _adjacency(graph: DiagramGraph) -> dict[str, list[tuple[str, str]]]:
    node_ids = {n.id for n in graph.nos}
    adj: dict[str, list[tuple[str, str]]] = {nid: [] for nid in node_ids}
    for e in graph.arestas:
        if e.origem not in node_ids or e.destino not in node_ids:
            raise GraphValidationError(
                f"Aresta referencia nó inexistente: {e.origem} -> {e.destino}"
            )
        adj[e.origem].append((e.destino, e.sinal))
    return adj


def _edge_sign(adj: dict[str, list[tuple[str, str]]], a: str, b: str) -> int:
    for dest, sinal in adj.get(a, []):
        if dest == b:
            return 1 if sinal == "+" else -1
    raise GraphValidationError(f"Aresta {a}->{b} não encontrada.")


# -----------------------------------------------------------------------------
# Enumeração de caminhos diretos e laços (DFS — grafos pequenos, sem necessidade
# de networkx: diagramas didáticos têm poucos nós)
# -----------------------------------------------------------------------------


def _all_simple_paths(adj: dict, start: str, end: str) -> list[list[str]]:
    paths: list[list[str]] = []

    def dfs(node: str, path: list[str], visited: set[str]) -> None:
        if node == end:
            paths.append(list(path))
            return
        for nxt, _sinal in adj.get(node, []):
            if nxt in visited:
                continue
            visited.add(nxt)
            path.append(nxt)
            dfs(nxt, path, visited)
            path.pop()
            visited.discard(nxt)

    dfs(start, [start], {start})
    return paths


def _all_simple_cycles(adj: dict, node_ids: list[str]) -> list[list[str]]:
    """
    Enumera ciclos simples uma única vez cada: um ciclo só é reportado a partir do
    nó de menor índice em `node_ids` que ele contém, evitando duplicar rotações do
    mesmo laço.
    """
    cycles: list[list[str]] = []
    order = {nid: i for i, nid in enumerate(node_ids)}

    def dfs(start: str, node: str, path: list[str], visited: set[str]) -> None:
        for nxt, _sinal in adj.get(node, []):
            if nxt == start:
                cycles.append(list(path))
            elif nxt not in visited and order[nxt] > order[start]:
                visited.add(nxt)
                path.append(nxt)
                dfs(start, nxt, path, visited)
                path.pop()
                visited.discard(nxt)

    for nid in node_ids:
        dfs(nid, nid, [nid], {nid})
    return cycles


# -----------------------------------------------------------------------------
# Ganhos de caminho/laço e Fórmula de Ganho de Mason
# -----------------------------------------------------------------------------


def _path_gain(path_ids: list[str], nodes_by_id: dict[str, GraphNode], adj: dict) -> Expr:
    gain: Expr = sympy.Integer(1)
    for nid in path_ids:
        gain *= _node_gain(nodes_by_id[nid])
    for a, b in zip(path_ids, path_ids[1:]):
        gain *= _edge_sign(adj, a, b)
    return gain


def _cycle_gain(cycle_ids: list[str], nodes_by_id: dict[str, GraphNode], adj: dict) -> Expr:
    gain: Expr = sympy.Integer(1)
    for nid in cycle_ids:
        gain *= _node_gain(nodes_by_id[nid])
    n = len(cycle_ids)
    for i in range(n):
        a, b = cycle_ids[i], cycle_ids[(i + 1) % n]
        gain *= _edge_sign(adj, a, b)
    return gain


def _mutually_non_touching(node_sets: list[frozenset[str]]) -> bool:
    seen: set[str] = set()
    for s in node_sets:
        if seen & s:
            return False
        seen |= s
    return True


def _delta(loop_gains: list[Expr], loop_node_sets: list[frozenset[str]]) -> Expr:
    """Δ = 1 − ΣL(laços) + ΣL(pares não-tocantes) − ΣL(trios não-tocantes) + ..."""
    delta: Expr = sympy.Integer(1)
    n = len(loop_gains)
    for r in range(1, n + 1):
        sign = (-1) ** r
        term: Expr = sympy.Integer(0)
        for combo in itertools.combinations(range(n), r):
            sets = [loop_node_sets[i] for i in combo]
            if not _mutually_non_touching(sets):
                continue
            prod: Expr = sympy.Integer(1)
            for i in combo:
                prod *= loop_gains[i]
            term += prod
        delta += sign * term
    return simplify(delta)


def _delta_for_path(
    path_node_set: frozenset[str],
    loop_gains: list[Expr],
    loop_node_sets: list[frozenset[str]],
) -> Expr:
    """Δ_k: só laços que não tocam o caminho k entram na conta."""
    filtered = [
        (g, s) for g, s in zip(loop_gains, loop_node_sets) if not (s & path_node_set)
    ]
    if not filtered:
        return sympy.Integer(1)
    return _delta([g for g, _ in filtered], [s for _, s in filtered])


def mason_reduce(graph: DiagramGraph) -> Expr:
    """
    Reduz `graph` à função de transferência equivalente entre o nó 'entrada' e o
    nó 'saida', pela Fórmula de Ganho de Mason. Levanta `GraphValidationError`
    para grafos desconectados, com IDs inválidos/duplicados, ganho não parseável,
    ou Δ algebricamente nulo.
    """
    nodes_by_id = _node_by_id(graph)
    entrada = _single_node_of_type(graph, "entrada")
    saida = _single_node_of_type(graph, "saida")
    adj = _adjacency(graph)
    node_ids = [n.id for n in graph.nos]

    paths = _all_simple_paths(adj, entrada.id, saida.id)
    if not paths:
        raise GraphValidationError(
            f"Nenhum caminho direto de '{entrada.id}' até '{saida.id}' — grafo desconectado."
        )

    cycles = _all_simple_cycles(adj, node_ids)
    loop_gains = [_cycle_gain(c, nodes_by_id, adj) for c in cycles]
    loop_node_sets = [frozenset(c) for c in cycles]

    delta = _delta(loop_gains, loop_node_sets)
    if simplify(delta) == 0:
        raise GraphValidationError("Δ = 0 — grafo degenerado (malha algebricamente singular).")

    total: Expr = sympy.Integer(0)
    for p in paths:
        path_gain = _path_gain(p, nodes_by_id, adj)
        delta_k = _delta_for_path(frozenset(p), loop_gains, loop_node_sets)
        total += path_gain * delta_k

    return simplify(total / delta)


# -----------------------------------------------------------------------------
# API de verificação (nunca levanta exceção — sempre devolve um outcome)
# -----------------------------------------------------------------------------


def verify_diagram_graph(
    graph: DiagramGraph, funcao_transferencia_declarada: str
) -> GraphVerificationOutcome:
    """Reduz `graph` e compara simbolicamente com a FT que o LLM declarou."""
    try:
        ft_grafo = mason_reduce(graph)
    except GraphValidationError as exc:
        return GraphVerificationOutcome(ok=False, problemas=[f"grafo: {exc}"])

    try:
        ft_declarada = parse_transfer_function_expr(funcao_transferencia_declarada)
    except Exception as exc:  # noqa: BLE001 — domínio: strings arbitrárias do LLM
        return GraphVerificationOutcome(
            ok=False,
            problemas=[f"grafo: FT declarada não parseável para comparação: {exc}"],
            ft_derivada_grafo=str(ft_grafo),
        )

    if rationals_equivalent_safe(ft_grafo, ft_declarada):
        return GraphVerificationOutcome(ok=True, ft_derivada_grafo=str(ft_grafo))

    return GraphVerificationOutcome(
        ok=False,
        problemas=[
            "grafo: a FT reduzida do diagrama (Mason) não é equivalente à FT declarada "
            f"— grafo produz {ft_grafo}, declarado foi {ft_declarada}."
        ],
        ft_derivada_grafo=str(ft_grafo),
    )
