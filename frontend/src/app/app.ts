import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { DiagramGraph } from './grafo-layout';
import { GrafoDiagramaComponent } from './grafo-diagrama/grafo-diagrama';

// URL base da API (em dev o Angular CLI faz proxy de /api para 127.0.0.1:8000, ver proxy.conf.json)
const API_BASE = '/api';

// Chave que carrega a lista de imagens do diagrama em base64 (sem prefixo data:) na resposta da API.
const CHAVE_DIAGRAMAS = 'diagramas_png_base64';

@Component({
  selector: 'app-root',
  imports: [FormsModule, GrafoDiagramaComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly descricao = signal(
    'Um sistema é composto por um bloco de massa M e uma mola K. Encontre a função de transferência G(s) = X(s)/F(s).'
  );
  protected readonly loading = signal(false);
  protected readonly resultado = signal<Record<string, unknown> | null>(null);
  protected readonly erro = signal<string | null>(null);

  // Imagens do diagrama, prontas para uso em <img [src]>.
  protected readonly diagramas = computed<string[]>(() => {
    const lista = this.resultado()?.[CHAVE_DIAGRAMAS];
    return Array.isArray(lista)
      ? lista.map((b64: string) => `data:image/png;base64,${b64}`)
      : [];
  });

  // Função de transferência, exibida em destaque separada do restante do JSON.
  protected readonly funcaoTransferencia = computed<string | null>(() => {
    const ft = this.resultado()?.['funcao_transferencia'];
    return typeof ft === 'string' && ft.trim() ? ft : null;
  });

  // Grafo estruturado do diagrama (mesma topologia, verificada pela Fórmula de Mason no backend).
  protected readonly grafoDiagrama = computed<DiagramGraph | null>(() => {
    const grafo = this.resultado()?.['grafo_diagrama'];
    return grafo && typeof grafo === 'object' ? (grafo as DiagramGraph) : null;
  });

  protected readonly grafoDiagramaJson = computed(() => {
    const grafo = this.grafoDiagrama();
    return grafo ? JSON.stringify(grafo, null, 2) : '';
  });

  protected readonly verificacaoGrafoExecutada = computed(
    () => this.resultado()?.['verificacao_grafo_executada'] === true
  );
  protected readonly verificacaoGrafoOk = computed(
    () => this.resultado()?.['verificacao_grafo_ok'] === true
  );
  protected readonly mensagemVerificacaoGrafo = computed<string | null>(() => {
    const msg = this.resultado()?.['mensagem_verificacao_grafo'];
    return typeof msg === 'string' ? msg : null;
  });

  // JSON do resultado para exibição, com a lista de imagens (potencialmente enorme) resumida,
  // já que as imagens em si aparecem como <img> logo acima.
  protected readonly resultadoJson = computed(() => {
    const data = this.resultado();
    if (!data) return '';
    const { [CHAVE_DIAGRAMAS]: diagramasBase64, ...resto } = data;
    const exibicao =
      Array.isArray(diagramasBase64) && diagramasBase64.length > 0
        ? { ...resto, [CHAVE_DIAGRAMAS]: `[${diagramasBase64.length} imagem(ns) — ver acima]` }
        : resto;
    return JSON.stringify(exibicao, null, 2);
  });

  constructor(private readonly http: HttpClient) {}

  private async chamarAPI(endpoint: string, body: unknown): Promise<void> {
    this.loading.set(true);
    this.erro.set(null);
    this.resultado.set(null);
    try {
      const data = await firstValueFrom(
        this.http.post<Record<string, unknown>>(`${API_BASE}${endpoint}`, body)
      );
      this.resultado.set(data);
    } catch (err: any) {
      const mensagem =
        err?.error?.erro ??
        (err?.status ? `Erro ${err.status}` : null) ??
        err?.message ??
        'Falha ao conectar na API. Verifique se a API está rodando (python main.py).';
      this.erro.set(mensagem);
    } finally {
      this.loading.set(false);
    }
  }

  protected gerarApenasFT(): void {
    this.chamarAPI('/gerar-apenas-ft', { descricao: this.descricao() });
  }

  protected gerarAnaliseCompleta(): void {
    this.chamarAPI('/gerar-analise-completa', { descricao: this.descricao() });
  }
}
