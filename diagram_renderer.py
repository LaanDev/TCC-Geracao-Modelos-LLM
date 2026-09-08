"""
Renderização determinística do diagrama de blocos a partir do `DiagramGraph` já
validado por `graph_validation.py` — sem depender do LLM escrever código matplotlib
à mão (que é frágil: ver os erros de execução capturados em `diagram_executor.py`).

Layout: detecta arestas de retorno (back edges) por DFS clássico (a mesma ideia usada
para achar laços em `graph_validation.py`, só que aqui precisamos de UMA classificação
adiante/retorno para desenhar, não da enumeração exaustiva de ciclos simples). O grafo
remanescente (sem as arestas de retorno) é um DAG; a camada de cada nó é a distância do
caminho mais longo a partir da 'entrada'. Nós que não caem no caminho principal
entrada->saída ganham uma "linha" (row) abaixo, e as arestas de retorno são desenhadas
como curvas fechando o laço.
"""

from __future__ import annotations

import io
from collections import deque

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

from graph_validation import DiagramGraph, GraphValidationError

_LAYER_DX = 2.4
_ROW_DY = 1.6
_BLOCK_H = 0.7
_BLOCK_MIN_W = 1.1
_SOMADOR_R = 0.22
_TERMINAL_R = 0.06


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


def _node_by_id(graph: DiagramGraph):
    by_id = {n.id: n for n in graph.nos}
    if len(by_id) != len(graph.nos):
        raise GraphValidationError("IDs de nós duplicados no grafo.")
    return by_id


def _single_node_of_type(graph: DiagramGraph, tipo: str):
    matches = [n for n in graph.nos if n.tipo == tipo]
    if len(matches) != 1:
        raise GraphValidationError(
            f"Esperava exatamente 1 nó do tipo '{tipo}', encontrado {len(matches)}."
        )
    return matches[0]


def _detect_back_edges(node_ids: list[str], adj: dict[str, list[tuple[str, str]]]) -> set[tuple[str, str]]:
    """DFS branco/cinza/preto: aresta p/ nó cinza (na pilha de recursão) é de retorno."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in node_ids}
    back_edges: set[tuple[str, str]] = set()

    def dfs(u: str) -> None:
        color[u] = GRAY
        for v, _sinal in adj.get(u, []):
            if color[v] == WHITE:
                dfs(v)
            elif color[v] == GRAY:
                back_edges.add((u, v))
        color[u] = BLACK

    for n in node_ids:
        if color[n] == WHITE:
            dfs(n)
    return back_edges


def _forward_adjacency(
    node_ids: list[str], adj: dict[str, list[tuple[str, str]]], back_edges: set[tuple[str, str]]
) -> dict[str, list[tuple[str, str]]]:
    fwd: dict[str, list[tuple[str, str]]] = {nid: [] for nid in node_ids}
    for u in node_ids:
        for v, sinal in adj.get(u, []):
            if (u, v) not in back_edges:
                fwd[u].append((v, sinal))
    return fwd


def _longest_path_layers(node_ids: list[str], fwd: dict[str, list[tuple[str, str]]]) -> dict[str, int]:
    """Camada de cada nó = comprimento do caminho mais longo a partir de uma fonte, no DAG `fwd`."""
    indeg = {n: 0 for n in node_ids}
    for u in node_ids:
        for v, _ in fwd.get(u, []):
            indeg[v] += 1

    layer = {n: 0 for n in node_ids}
    queue: deque[str] = deque(n for n in node_ids if indeg[n] == 0)
    indeg_work = dict(indeg)
    visited = 0
    while queue:
        u = queue.popleft()
        visited += 1
        for v, _ in fwd.get(u, []):
            layer[v] = max(layer[v], layer[u] + 1)
            indeg_work[v] -= 1
            if indeg_work[v] == 0:
                queue.append(v)
    if visited < len(node_ids):
        # Sobrou nó não alcançado por topological sort (grafo malformado) — layout degradado
        # em vez de travar: qualquer nó não visitado fica na camada 0.
        pass
    return layer


def _shortest_path(
    fwd: dict[str, list[tuple[str, str]]], start: str, end: str
) -> list[str]:
    """BFS simples só para achar UM caminho principal (uso puramente estético no layout)."""
    prev: dict[str, str | None] = {start: None}
    queue: deque[str] = deque([start])
    while queue:
        u = queue.popleft()
        if u == end:
            break
        for v, _ in fwd.get(u, []):
            if v not in prev:
                prev[v] = u
                queue.append(v)
    if end not in prev:
        return []
    path = [end]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return list(reversed(path))


def _assign_rows(
    node_ids: list[str], layer: dict[str, int], primary_path: set[str]
) -> dict[str, int]:
    """Linha 0 para o caminho principal; demais nós de cada camada ganham linhas negativas."""
    row: dict[str, int] = {}
    by_layer: dict[int, list[str]] = {}
    for n in node_ids:
        by_layer.setdefault(layer[n], []).append(n)
    for _lyr, nodes_here in by_layer.items():
        secondary = [n for n in nodes_here if n not in primary_path]
        for n in nodes_here:
            row[n] = 0 if n in primary_path else -(1 + secondary.index(n))
    return row


def _format_gain_label(ganho: str | None) -> str:
    if not ganho:
        return ""
    try:
        from ft_verification import parse_transfer_function_expr
        import sympy

        expr = parse_transfer_function_expr(f"G(s) = {ganho}")
        return f"${sympy.latex(expr)}$"
    except Exception:  # noqa: BLE001 — fallback puramente cosmético
        return ganho


def render_diagram_graph(graph: DiagramGraph) -> bytes:
    """
    Desenha `graph` como diagrama de blocos (PNG) sem executar nenhum código do LLM.
    Levanta `GraphValidationError` para estrutura inválida (mesmas condições checadas
    em `graph_validation.mason_reduce`); quem chama decide se isso bloqueia ou não.
    """
    nodes_by_id = _node_by_id(graph)
    node_ids = [n.id for n in graph.nos]
    entrada = _single_node_of_type(graph, "entrada")
    saida = _single_node_of_type(graph, "saida")
    adj = _adjacency(graph)

    back_edges = _detect_back_edges(node_ids, adj)
    fwd = _forward_adjacency(node_ids, adj, back_edges)
    path_nodes = _shortest_path(fwd, entrada.id, saida.id)
    if not path_nodes:
        raise GraphValidationError(
            f"Nenhum caminho direto de '{entrada.id}' até '{saida.id}' — grafo desconectado."
        )
    layer = _longest_path_layers(node_ids, fwd)
    primary_path = set(path_nodes)
    row = _assign_rows(node_ids, layer, primary_path)

    pos = {nid: (layer[nid] * _LAYER_DX, row[nid] * _ROW_DY) for nid in node_ids}

    max_x = max((p[0] for p in pos.values()), default=0)
    min_y = min((p[1] for p in pos.values()), default=0)
    max_y = max((p[1] for p in pos.values()), default=0)

    fig, ax = plt.subplots(figsize=(max(4.0, max_x / 1.6 + 2.5), max(2.2, (max_y - min_y) / 1.4 + 2.0)))
    ax.set_xlim(-1.2, max_x + 1.2)
    ax.set_ylim(min_y - 1.2, max_y + 1.2)
    ax.axis("off")
    ax.set_aspect("equal")

    patches: dict[str, object] = {}
    for nid in node_ids:
        node = nodes_by_id[nid]
        x, y = pos[nid]
        if node.tipo == "bloco":
            label = _format_gain_label(node.ganho)
            width = max(_BLOCK_MIN_W, 0.22 * max(3, len(node.ganho or "")))
            patch = FancyBboxPatch(
                (x - width / 2, y - _BLOCK_H / 2),
                width,
                _BLOCK_H,
                boxstyle="round,pad=0.05",
                facecolor="white",
                edgecolor="black",
                linewidth=1.4,
            )
            ax.add_patch(patch)
            ax.text(x, y, label, ha="center", va="center", fontsize=11)
        elif node.tipo == "somador":
            patch = Circle((x, y), _SOMADOR_R, facecolor="white", edgecolor="black", linewidth=1.4)
            ax.add_patch(patch)
            ax.text(x, y, "+", ha="center", va="center", fontsize=9)
        else:  # entrada / saida
            patch = Circle((x, y), _TERMINAL_R, facecolor="black", edgecolor="black")
            ax.add_patch(patch)
            label_y = y + 0.35 if row[nid] >= 0 else y - 0.35
            va = "bottom" if row[nid] >= 0 else "top"
            ax.text(x, label_y, nid, ha="center", va=va, fontsize=10, style="italic")
        patches[nid] = patch

    for u in node_ids:
        for v, sinal in adj.get(u, []):
            is_back = (u, v) in back_edges
            rad = 0.0 if not is_back else (-0.5 if pos[u][1] <= pos[v][1] else 0.5)
            arrow = FancyArrowPatch(
                pos[u],
                pos[v],
                patchA=patches[u],
                patchB=patches[v],
                arrowstyle="-|>",
                mutation_scale=14,
                lw=1.3,
                color="black",
                shrinkA=0,
                shrinkB=0,
                connectionstyle=f"arc3,rad={rad}",
            )
            ax.add_patch(arrow)

            if sinal == "-" and nodes_by_id[v].tipo == "somador":
                mx, my = (pos[u][0] + pos[v][0]) / 2, (pos[u][1] + pos[v][1]) / 2
                if is_back:
                    # Ponto médio (t=0.5) da bezier quadrática do "arc3,rad=r": o controle
                    # fica deslocado da reta por rad*dist ao longo da perpendicular, e o
                    # ponto médio da curva é a metade desse deslocamento.
                    dx, dy = pos[v][0] - pos[u][0], pos[v][1] - pos[u][1]
                    dist = (dx**2 + dy**2) ** 0.5 or 1.0
                    perp_x, perp_y = dy / dist, -dx / dist
                    mx += 0.5 * rad * dist * perp_x
                    my += 0.5 * rad * dist * perp_y
                ax.text(mx, my, "−", ha="center", va="center", fontsize=13, color="black")

    fig.tight_layout(pad=0.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
