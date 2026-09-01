# Frontend – TCC API de Modelagem

Interface em **Angular** (standalone components, signals) para usar a API de modelagem de sistemas de controle.

## Pré-requisitos

- **Node.js** instalado (recomendado: 20 ou superior)
- **API rodando** em `http://127.0.0.1:8000` (rode `python main.py` na raiz do projeto)

## Como rodar

### 1. Instalar dependências

No terminal, na pasta **frontend**:

```bash
cd frontend
npm install
```

### 2. Subir o servidor de desenvolvimento

```bash
npm start
```

O frontend abre em **http://localhost:3000**.

### 3. Usar a aplicação

- **Descrição do sistema:** digite ou edite o texto (ex.: circuito RC, massa-mola, etc.).
- **Gerar apenas FT:** retorna só a função de transferência.
- **Análise completa:** retorna lei aplicada, EDO, passos de Laplace, FT e código Python.
- **Validar minha resposta:** preencha o campo "Sua função de transferência" e clique no botão para o modo tutor.

O resultado aparece em JSON abaixo dos botões.

## Estrutura do projeto (Angular)

```
frontend/
├── public/               # Arquivos estáticos (favicon etc.)
├── src/
│   ├── app/
│   │   ├── app.ts        # Componente principal (standalone) e lógica da tela
│   │   ├── app.html      # Template do componente
│   │   ├── app.css       # Estilos do componente
│   │   └── app.config.ts # Configuração da aplicação (providers: HttpClient etc.)
│   ├── main.ts            # Bootstrap da aplicação Angular
│   └── styles.css         # Estilos globais
├── index.html              # HTML raiz
├── proxy.conf.json         # Proxy do dev server (Angular CLI) para a API
├── angular.json             # Configuração do workspace/CLI Angular
├── package.json              # Dependências e scripts
└── README.md                  # Este arquivo
```

## Proxy da API

Em `proxy.conf.json`, as chamadas a **`/api`** são redirecionadas para **`http://127.0.0.1:8000`**.
Assim, o frontend usa `HttpClient` apontando para `/api/gerar-apenas-ft`, e o Angular CLI (`ng serve --proxy-config proxy.conf.json`, já configurado no script `npm start`) encaminha a requisição para a API.

## Scripts

| Comando         | Descrição                                   |
|-----------------|----------------------------------------------|
| `npm start`     | Sobe o servidor de desenvolvimento (com proxy) |
| `npm run build` | Gera o build para produção                    |
| `npm test`      | Roda os testes unitários (Vitest)             |

## Build para produção

Para gerar os arquivos estáticos e servir pela API (opcional):

```bash
npm run build
```

Os arquivos ficam em `frontend/dist/frontend-angular/browser/`. Depois você pode configurar o FastAPI para servir essa pasta em `/` (ver documentação do backend).

## Aprendendo Angular

- **Componentes standalone:** `App` (em `app.ts`) é um componente autocontido — sem `NgModule` — que declara suas próprias `imports` (`FormsModule`, para o `[(ngModel)]`).
- **Signals:** o estado da tela (`descricao`, `resultado`, `loading`, `erro`) é armazenado em `signal()`, o mecanismo de reatividade mais recente do Angular (substitui `useState` do React).
- **Injeção de dependência:** `HttpClient` é injetado no construtor do componente e usado para chamar a API — configurado em `app.config.ts` via `provideHttpClient()`.
- **Novo *control flow*:** o template usa `@if` diretamente (sintaxe moderna do Angular), em vez da antiga diretiva `*ngIf`.

Para ir além: [Angular – Documentação](https://angular.dev).
