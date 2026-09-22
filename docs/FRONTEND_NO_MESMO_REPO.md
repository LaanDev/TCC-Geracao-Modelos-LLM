# Desenvolvendo o Frontend no Mesmo Repositório

Sim, você pode (e faz sentido) desenvolver o frontend neste mesmo repositório.

---

## Estrutura sugerida

```
TCC-Geracao-Modelos-LLM/
├── backend/                 # API (opcional: mover main.py, config.py etc. para aqui)
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── prompts.py
│   ├── llm_service.py
│   └── requirements.txt
├── frontend/                # Interface web
│   ├── src/
│   ├── package.json
│   ├── vite.config.js       # ou react-scripts, etc.
│   └── ...
├── main.py                  # ou manter na raiz (como está hoje)
├── frontend/                # pasta do frontend na raiz
├── .env
├── README.md
└── ...
```

**Opção mais simples (sem mover nada):** manter a API na raiz como está e criar só a pasta `frontend/` na raiz.

---

## Duas formas de organizar

### Opção A: API na raiz + pasta `frontend/` (recomendado para começar)

- Tudo que é API continua na raiz: `main.py`, `config.py`, `schemas.py`, `prompts.py`, `llm_service.py`, `requirements.txt`, `.env`.
- Você cria uma pasta **`frontend/`** na raiz e desenvolve o frontend dentro dela (React, Vue, HTML puro, etc.).

```
TCC-Geracao-Modelos-LLM/
├── main.py
├── config.py
├── schemas.py
├── prompts.py
├── llm_service.py
├── requirements.txt
├── .env
├── docs/                    # documentação
├── scripts/                 # scripts de utilidade
├── frontend/           # ← frontend
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── README.md
└── ...
```

- **Durante o desenvolvimento:** você sobe a API (`python main.py` → porta 8000) e o frontend (ex.: `npm run dev` → porta 3000). O frontend chama a API em `http://127.0.0.1:8000` (já temos CORS configurado).
- **Para entregar/TCC:** você pode gerar o build do frontend (`npm run build`) e configurar o FastAPI para servir os arquivos estáticos da pasta `frontend/dist` (ou `frontend/build`), assim tudo fica em um único servidor.

### Opção B: Tudo em subpastas (`backend/` e `frontend/`)

- Você move a API para **`backend/`** (main.py, config.py, etc.) e cria **`frontend/`** como acima.
- Fica mais organizado se o projeto crescer, mas exige ajustar imports, `requirements.txt`, `.env` e como você roda a API (por exemplo `python backend/main.py` ou `cd backend && python main.py`).

Para um TCC, a **Opção A** costuma ser suficiente: mesmo repositório, API na raiz, frontend em `frontend/`.

---

## Tecnologias possíveis para o frontend

| Opção | Quando usar |
|-------|-------------|
| **React** (Vite ou Create React App) | Se quiser SPA moderna e reutilizável. |
| **Vue.js** | Similar ao React, curva de aprendizado um pouco menor. |
| **HTML + CSS + JavaScript** | Simples, sem build; ideal para protótipo rápido. |
| **Streamlit** (Python) | Tudo em Python, rápido para demo; menos "frontend clássico". |

---

## CORS

A API já está com CORS configurado (incluindo `allow_origins`), então um frontend rodando em outro port (ex.: 3000) consegue chamar `http://127.0.0.1:8000` sem problema.

---

## Resumo

- **Pode fazer no mesmo repositório?** Sim.
- **Onde colocar?** Criar uma pasta **`frontend/`** na raiz e deixar a API como está.
- **Como rodar?** API: `python main.py` (porta 8000). Frontend: dentro de `frontend/`, `npm install` e `npm start` em outra porta.
- **Para o TCC:** depois pode servir o build do frontend pelo próprio FastAPI para ter um único deploy.

O frontend em **Angular** já está na pasta **`frontend/`**. Para rodar:

```bash
cd frontend
npm install
npm start
```

Depois acesse http://localhost:3000. A API deve estar rodando em outro terminal (`python main.py`). Consulte **`frontend/README.md`** para mais detalhes.
