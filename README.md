# Geração Automática de Modelos para Controle Automático via LLMs: Uma Ferramenta de Apoio ao Ensino-Aprendizagem

**Autor:** Laan Carlos Nunes Mendes de Barros
**Orientador:** José Eduardo Henriques da Silva
**Coorientador:** Fernando Garcia Diniz Campos Ferreira

---

## 1. Sobre o Projeto

Este repositório contém o código-fonte e a documentação técnica do Trabalho de Conclusão de Curso (TCC) em Engenharia de Controle e Automação.

O projeto consiste no desenvolvimento de uma ferramenta de software baseada em Inteligência Artificial (LLMs) para auxiliar estudantes na modelagem de sistemas dinâmicos. A solução foi arquitetada como uma **API RESTful**, capaz de interpretar descrições de sistemas físicos em linguagem natural e retornar:

1. A Lei Física fundamental aplicada.
2. A Equação Diferencial (EDO) do sistema.
3. O passo a passo da aplicação da Transformada de Laplace.
4. A Função de Transferência final $G(s)$.
5. Código Python pronto para gerar o Diagrama de Blocos (via biblioteca `python-control`).

O objetivo é criar um "tutor virtual" que não apenas resolve o problema, mas ensina a metodologia de resolução.

## 2. Funcionalidades e Endpoints da API

A ferramenta possui um *backend* robusto desenvolvido em **FastAPI**, expondo três rotas principais:

- **`POST /gerar-apenas-ft`**: Rota rápida. Recebe a descrição e retorna apenas a função de transferência final para validação ágil.
- **`POST /gerar-analise-completa`**: Rota principal. Retorna um objeto JSON detalhado contendo todo o raciocínio matemático, a explicação didática e o código para geração do diagrama.
- **`POST /validar-minha-resposta`**: Rota de tutor. O aluno envia o problema e a sua própria resposta; a IA avalia se está correto e fornece feedback construtivo.

## 3. Tecnologias Utilizadas

O projeto foi construído sobre uma *stack* moderna de desenvolvimento em Python:

- **Linguagem:** Python 3.x
- **API Framework:** `FastAPI` (para criação de rotas assíncronas e documentação automática).
- **Servidor:** `Uvicorn` (servidor ASGI de alta performance).
- **IA Generativa:** `google-generativeai` (Integração com modelo Gemini 1.5/Gemma).
- **Engenharia:** `control` (Biblioteca Python de Sistemas de Controle).
- **Frontend:** React (Vite) – interface para consumir a API.
- **Ambiente:** Gerenciado via `venv` (backend) e `npm` (frontend).

## 4. Status do Projeto

✅ **Fase 1:** Fundamentação Teórica e Prova de Conceito (`scripts/poc_inicial.py`).
✅ **Fase 2:** Desenvolvimento do Backend/API (`main.py`).
✅ **Fase 3:** Implementação da Engenharia de Prompt e Saídas Estruturadas (JSON).
✅ **Fase 4:** Validação com problemas canônicos (Massa-Mola, RLC, Tanques, etc.).
✅ **Fase 5:** Desenvolvimento do Frontend (Interface Visual em React).

### Estrutura do repositório

| Pasta/arquivo | Conteúdo |
|---------------|----------|
| **Raiz** | API: `main.py`, `config.py`, `schemas.py`, `prompts.py`, `llm_service.py`, `requirements.txt`, `.env.example` |
| **`docs/`** | Documentação: guias de instalação, solução de problemas, quota da API, etc. (índice em `docs/README.md`) |
| **`scripts/`** | Scripts de utilidade: `verificar_instalacao.py`, `corrigir_pip.py`, `check_models.py`, `ativar_venv.bat`, `poc_inicial.py` |
| **`frontend/`** | Interface React (Vite) para consumir a API |
| **`tests/`** | Testes automatizados (pytest) |

## 5. Como Executar o Projeto

### Pré-requisitos
- **Python 3.11 ou superior** instalado
- **Chave de API do Google** (Google AI Studio)
- **Git** (opcional, para clonar o repositório)

> 📖 **Não tem Python instalado?** Consulte o guia completo: [`docs/INSTALACAO_PYTHON.md`](docs/INSTALACAO_PYTHON.md)

### Passo a Passo

#### 1. Verificar Instalação do Python
Abra o **PowerShell** ou **Prompt de Comando** e execute:

```powershell
python --version
```

Você deve ver algo como: `Python 3.11.9`

Se aparecer erro, siga o guia de instalação: [`docs/INSTALACAO_PYTHON.md`](docs/INSTALACAO_PYTHON.md)

> 💡 **Dica:** Após instalar o Python e configurar o projeto, execute `python scripts/verificar_instalacao.py` para verificar se tudo está correto!

#### 2. Clone ou Baixe o Repositório
```bash
git clone [SEU LINK DO GIT AQUI]
cd TCC-Geracao-Modelos-LLM
```

Ou baixe o ZIP e extraia os arquivos.

#### 3. Criar Ambiente Virtual
```powershell
# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual (Windows)
.\venv\Scripts\activate

# Ativar o ambiente virtual (macOS/Linux)
source venv/bin/activate
```

**Dica:** Quando o ambiente virtual estiver ativo, você verá `(venv)` no início da linha do terminal.

> ⚠️ **Problema ao ativar no PowerShell?** Se aparecer erro de "execução de scripts desabilitada", use uma destas soluções:
> - **Opção 1 (Recomendada):** Use o **Prompt de Comando (CMD)** em vez do PowerShell: `venv\Scripts\activate`
> - **Opção 2:** Execute no PowerShell: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
> - 📖 **Guia completo:** [`docs/SOLUCAO_POWERSHELL.md`](docs/SOLUCAO_POWERSHELL.md)

#### 4. Instalar Dependências
```powershell
# Atualizar pip (recomendado)
python -m pip install --upgrade pip

# Instalar todas as dependências
pip install -r requirements.txt
```

#### 5. Configurar Variáveis de Ambiente
```powershell
# Copiar o template
copy .env.example .env
```

Depois, edite o arquivo `.env` e adicione sua chave de API:

```env
GOOGLE_API_KEY=sua_chave_api_aqui
```

**Como obter a chave:**
1. Acesse: https://aistudio.google.com/app/apikey
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave e cole no arquivo `.env`

#### 6. Executar a API
```powershell
python main.py
```

Você deve ver uma mensagem como:
```
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### 7. Acessar a Documentação Interativa
Com o servidor rodando, abra seu navegador e acesse:

👉 **http://127.0.0.1:8000/docs**

Lá você poderá:
- Ver todos os endpoints disponíveis
- Testar a API diretamente pelo navegador (Swagger UI)
- Ver exemplos de requisições e respostas

**Alternativa:** Acesse **http://127.0.0.1:8000/redoc** para documentação no formato ReDoc.

#### 8. Executar o Frontend (React) – opcional
Para usar a interface web em React:

1. **Instale o Node.js** (se ainda não tiver): https://nodejs.org/
2. **Com a API rodando** em um terminal, abra outro terminal e execute:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
3. Acesse **http://localhost:3000** no navegador.

O frontend chama a API automaticamente (proxy configurado no Vite). Consulte [`frontend/README.md`](frontend/README.md) para mais detalhes.

---

### Comandos Úteis

```powershell
# Desativar ambiente virtual (quando terminar)
deactivate

# Verificar dependências instaladas
pip list

# Executar testes (após instalar pytest)
pytest tests/ -v

# Executar com Docker (se tiver Docker instalado)
docker-compose up -d api

# Frontend (em outro terminal, com a API rodando)
cd frontend && npm install && npm run dev
```

---

### Solução de Problemas

**Problema:** `ModuleNotFoundError: No module named 'fastapi'`
- **Solução:** Certifique-se de que o ambiente virtual está ativado e execute `pip install -r requirements.txt`

**Problema:** `GOOGLE_API_KEY not found`
- **Solução:** Verifique se o arquivo `.env` existe na raiz do projeto e contém `GOOGLE_API_KEY=sua_chave`

**Problema:** `Port 8000 is already in use`
- **Solução:** Pare o processo que está usando a porta 8000 ou altere a porta no `config.py`

Para mais detalhes, consulte a pasta **docs/** (por exemplo [`docs/INSTALACAO_PYTHON.md`](docs/INSTALACAO_PYTHON.md), [`docs/PASSO_A_PASSO.md`](docs/PASSO_A_PASSO.md), [`docs/QUOTA_API.md`](docs/QUOTA_API.md), [`docs/SOLUCAO_ERRO_500.md`](docs/SOLUCAO_ERRO_500.md)).
