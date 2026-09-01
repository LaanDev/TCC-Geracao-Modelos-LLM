import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

// URL base da API (em dev o Angular CLI faz proxy de /api para 127.0.0.1:8000, ver proxy.conf.json)
const API_BASE = '/api';

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected readonly descricao = signal(
    'Um sistema é composto por um bloco de massa M e uma mola K. Encontre a função de transferência G(s) = X(s)/F(s).'
  );
  protected readonly funcaoUsuario = signal('G(s) = 1 / (Ms² + K)');
  protected readonly loading = signal(false);
  protected readonly resultado = signal<unknown>(null);
  protected readonly resultadoJson = signal('');
  protected readonly erro = signal<string | null>(null);

  constructor(private readonly http: HttpClient) {}

  private async chamarAPI(endpoint: string, body: unknown): Promise<void> {
    this.loading.set(true);
    this.erro.set(null);
    this.resultado.set(null);
    try {
      const data = await firstValueFrom(
        this.http.post(`${API_BASE}${endpoint}`, body)
      );
      this.resultado.set(data);
      this.resultadoJson.set(JSON.stringify(data, null, 2));
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

  protected validarResposta(): void {
    this.chamarAPI('/validar-minha-resposta', {
      descricao: this.descricao(),
      funcao_transferencia_usuario: this.funcaoUsuario(),
    });
  }
}
