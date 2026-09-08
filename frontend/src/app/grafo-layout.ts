// Layout automático (esquerda -> direita) do grafo estruturado do diagrama
// (grafo_diagrama, ver graph_validation.py), para renderização em SVG.
// Puramente geométrico: não faz nenhuma verificação — só organiza os mesmos
// nós/arestas que o backend já validou pela Fórmula de Ganho de Mason.

export type TipoNo = 'bloco' | 'somador' | 'entrada' | 'saida';

export interface GraphNode {
  id: string;
  tipo: TipoNo;
  ganho?: string | null;
}

export interface GraphEdge {
  origem: string;
  destino: string;
  sinal?: '+' | '-';
}

export interface DiagramGraph {
  nos: GraphNode[];
  arestas: GraphEdge[];
}

export interface LayoutNode {
  id: string;
  tipo: TipoNo;
  ganho: string | null;
  x: number;
  y: number;
  halfW: number;
  halfH: number;
  ganhoFontSize: number;
}

export interface LayoutEdge {
  backward: boolean;
  d: string;
  sinal: '+' | '-';
  labelX: number;
  labelY: number;
  showLabel: boolean;
}

export interface GrafoLayout {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  width: number;
  height: number;
}

const DIM: Record<TipoNo, { halfW: number; halfH: number }> = {
  bloco: { halfW: 60, halfH: 30 },
  somador: { halfW: 20, halfH: 20 },
  entrada: { halfW: 12, halfH: 8 },
  saida: { halfW: 12, halfH: 8 },
};

const BLOCO_HALF_W_MAX = 130;
const GANHO_FONT_SIZE_PADRAO = 11;
const GANHO_FONT_SIZE_MIN = 7;

const GAP = 46;
const ROW_Y = 90;
const MARGIN = 30;
const RAIL_GAP = 24;
const RAIL_BASE = 40;

// Ganhos curtos ("1/(RCs+1)") cabem na caixa padrão; ganhos longos (ex.: motor CC) alargam
// a caixa até um teto e, a partir daí, reduzem a fonte — para não estourar o layout.
function dimensoesBloco(ganho: string | null | undefined): { halfW: number; halfH: number; fontSize: number } {
  const base = DIM.bloco;
  const len = ganho?.length ?? 0;
  if (len <= 12) return { ...base, fontSize: GANHO_FONT_SIZE_PADRAO };
  const halfWDesejado = 30 + len * 3.4;
  if (halfWDesejado <= BLOCO_HALF_W_MAX) {
    return { halfW: halfWDesejado, halfH: base.halfH, fontSize: GANHO_FONT_SIZE_PADRAO };
  }
  const excesso = halfWDesejado / BLOCO_HALF_W_MAX;
  const fontSize = Math.max(GANHO_FONT_SIZE_MIN, GANHO_FONT_SIZE_PADRAO / excesso);
  return { halfW: BLOCO_HALF_W_MAX, halfH: base.halfH, fontSize };
}

export function layoutGrafo(grafo: DiagramGraph | null | undefined): GrafoLayout | null {
  if (!grafo || !Array.isArray(grafo.nos) || grafo.nos.length === 0) return null;

  const adjacency = new Map<string, string[]>();
  for (const n of grafo.nos) adjacency.set(n.id, []);
  for (const e of grafo.arestas ?? []) {
    if (adjacency.has(e.origem)) adjacency.get(e.origem)!.push(e.destino);
  }

  // Ordena colunas via BFS a partir do nó "entrada" — a primeira visita a cada nó vence, então
  // arestas de realimentação (que sempre apontam para um nó já visitado) viram "para trás".
  const entradaNode = grafo.nos.find((n) => n.tipo === 'entrada');
  const order = new Map<string, number>();
  if (entradaNode) {
    const fila: string[] = [entradaNode.id];
    order.set(entradaNode.id, 0);
    while (fila.length) {
      const atual = fila.shift()!;
      for (const prox of adjacency.get(atual) ?? []) {
        if (!order.has(prox)) {
          order.set(prox, order.get(atual)! + 1);
          fila.push(prox);
        }
      }
    }
  }
  // Nós não alcançados a partir de "entrada" (grafo desconectado/malformado) entram no final,
  // na ordem em que aparecem em "nos", para que nada deixe de ser desenhado.
  let proximaOrdem = order.size ? Math.max(...order.values()) + 1 : 0;
  for (const n of grafo.nos) {
    if (!order.has(n.id)) order.set(n.id, proximaOrdem++);
  }

  const ordenados = [...grafo.nos].sort((a, b) => order.get(a.id)! - order.get(b.id)!);

  const porId = new Map<string, LayoutNode>();
  let x = MARGIN;
  for (const n of ordenados) {
    const dim = n.tipo === 'bloco' ? dimensoesBloco(n.ganho) : { ...(DIM[n.tipo] ?? DIM.bloco), fontSize: GANHO_FONT_SIZE_PADRAO };
    x += dim.halfW;
    porId.set(n.id, {
      id: n.id,
      tipo: n.tipo,
      ganho: n.ganho ?? null,
      x,
      y: ROW_Y,
      halfW: dim.halfW,
      halfH: dim.halfH,
      ganhoFontSize: dim.fontSize,
    });
    x += dim.halfW + GAP;
  }
  const largura = x - GAP + MARGIN;

  const edges: LayoutEdge[] = [];
  let railIndex = 0;
  let maxRailY = ROW_Y;

  for (const e of grafo.arestas ?? []) {
    const from = porId.get(e.origem);
    const to = porId.get(e.destino);
    if (!from || !to) continue;
    const sinal = e.sinal ?? '+';

    if (to.x > from.x) {
      // Aresta "para frente": linha reta na fileira principal.
      const x1 = from.x + from.halfW;
      const x2 = to.x - to.halfW;
      edges.push({
        backward: false,
        d: `M ${x1} ${ROW_Y} L ${x2} ${ROW_Y}`,
        sinal,
        labelX: (x1 + x2) / 2,
        labelY: ROW_Y - 10,
        showLabel: to.tipo === 'somador',
      });
    } else {
      // Aresta "para trás" (realimentação): desce, percorre um trilho abaixo da fileira
      // principal e sobe de volta — mesmo estilo dos diagramas de blocos gerados pelo LLM.
      const railY = ROW_Y + RAIL_BASE + railIndex * RAIL_GAP;
      railIndex++;
      maxRailY = Math.max(maxRailY, railY);
      const x1 = from.x;
      const x2 = to.x;
      const y1 = ROW_Y + from.halfH;
      const y2 = ROW_Y + to.halfH;
      edges.push({
        backward: true,
        d: `M ${x1} ${y1} L ${x1} ${railY} L ${x2} ${railY} L ${x2} ${y2}`,
        sinal,
        labelX: x2 + 14,
        labelY: railY,
        showLabel: true,
      });
    }
  }

  const altura = maxRailY + 40;

  return {
    nodes: [...porId.values()],
    edges,
    width: Math.max(largura, 200),
    height: altura,
  };
}
