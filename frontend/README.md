# Frontend – TCC API de Modelagem

Interface em **React** (Vite) para usar a API de modelagem de sistemas de controle.

## Pré-requisitos

- **Node.js** instalado (recomendado: 18 ou 20)
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
npm run dev
```

O frontend abre em **http://localhost:3000**.

### 3. Usar a aplicação

- **Descrição do sistema:** digite ou edite o texto (ex.: circuito RC, massa-mola, etc.).
- **Gerar apenas FT:** retorna só a função de transferência.
- **Análise completa:** retorna lei aplicada, EDO, passos de Laplace, FT e código Python.
- **Validar minha resposta:** preencha o campo “Sua função de transferência” e clique no botão para o modo tutor.

O resultado aparece em JSON abaixo dos botões.

## Estrutura do projeto (React)

```
frontend/
├── public/          # Arquivos estáticos (favicon etc.)
├── src/
│   ├── App.jsx      # Componente principal e lógica da tela
│   ├── App.css      # Estilos do App
│   ├── main.jsx     # Entrada da aplicação React
│   └── index.css    # Estilos globais
├── index.html       # HTML raiz
├── vite.config.js   # Configuração do Vite (proxy para a API)
├── package.json     # Dependências e scripts
└── README.md        # Este arquivo
```

## Proxy da API

No `vite.config.js`, as chamadas a **`/api`** são redirecionadas para **`http://127.0.0.1:8000`**.  
Assim, o frontend usa `fetch('/api/gerar-apenas-ft', ...)` e o Vite envia a requisição para a API.

## Scripts

| Comando        | Descrição                          |
|----------------|------------------------------------|
| `npm run dev`  | Sobe o servidor de desenvolvimento |
| `npm run build`| Gera o build para produção         |
| `npm run preview` | Sobe um servidor local para testar o build |

## Build para produção

Para gerar os arquivos estáticos e servir pela API (opcional):

```bash
npm run build
```

Os arquivos ficam em `frontend/dist/`. Depois você pode configurar o FastAPI para servir essa pasta em `/` (ver documentação do backend).

## Aprendendo React

- **Componentes:** `App.jsx` é um componente que usa `useState` para o texto, resultado e loading.
- **Eventos:** os botões usam `onClick` para chamar funções que fazem `fetch` na API.
- **Estado:** `loading`, `resultado` e `erro` controlam o que aparece na tela (loading, JSON ou mensagem de erro).

Para ir além: [React – Documentação](https://react.dev).
