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
- **Ambiente:** Gerenciado via `venv`.

## 4. Status do Projeto

✅ **Fase 1:** Fundamentação Teórica e Prova de Conceito (`poc_inicial.py`).
✅ **Fase 2:** Desenvolvimento do Backend/API (`main.py`).
✅ **Fase 3:** Implementação da Engenharia de Prompt e Saídas Estruturadas (JSON).
✅ **Fase 4:** Validação com problemas canônicos (Massa-Mola, RLC, Tanques, etc.).
🚧 **Fase 5:** Desenvolvimento do Frontend (Interface Visual) - *Próxima Etapa*.

## 5. Como Executar o Projeto

### Pré-requisitos
É necessário ter o Python instalado e uma chave de API do Google (Google AI Studio).

1. **Clone o repositório:**
   ```bash
   git clone [SEU LINK DO GIT AQUI]
   cd TCC-Geracao-Modelos-LLM
2. **Crie e ative o ambiente virtual:**
   python -m venv venv
  # Windows
  .\venv\Scripts\activate
  # macOS/Linux
  source venv/bin/activate
4. **Instale as dependências:**
  pip install -r requirements.txt
5. **Configure as variáveis de ambiente:**
  Crie um arquivo chamado .env na raiz do projeto.
  Adicione sua chave de API dentro dele:
    GOOGLE_API_KEY="SUA_CHAVE_AQUI"
6. **Execute a API:**
  python main.py
7. **Acesse a Documentação Interativa:**
  Com o servidor rodando, abra seu navegador e acesse: 👉 http://127.0.0.1:8000/docs
  Lá você poderá testar todos os endpoints da ferramenta diretamente pelo navegador (Swagger UI).
