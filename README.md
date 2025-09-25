# Geração Automática de Modelos para Controle Automático via LLMs: Uma Ferramenta de Apoio ao Ensino-Aprendizagem

**Autor:** Laan Carlos Nunes Mendes de Barros
**Orientador:** José Eduardo
**Coorientador:** Fernando

---

## 1. Sobre o Projeto

Este repositório contém o código-fonte e a documentação do Trabalho de Conclusão de Curso (TCC) em Engenharia de Controle e Automação.

O projeto consiste no desenvolvimento de uma ferramenta de software que utiliza Modelos de Linguagem de Larga Escala (LLMs) para auxiliar estudantes no aprendizado de modelagem de sistemas dinâmicos. A ferramenta permitirá que o usuário descreva um sistema físico (mecânico, elétrico, etc.) em linguagem natural e receberá, como resposta, a função de transferência correspondente, o diagrama de blocos e uma explicação didática do passo a passo da resolução.

O objetivo principal é criar um recurso educacional que não apenas forneça a solução, mas que reforce a compreensão teórica dos conceitos fundamentais de controle automático.

## 2. Funcionalidades Planejadas

- **Entrada em Linguagem Natural:** Interpretação de descrições de problemas de modelagem.
- **Geração de Função de Transferência:** Cálculo e apresentação da função de transferência $G(s)$ do sistema.
- **Construção de Diagrama de Blocos:** Geração de uma representação visual do sistema.
- **Explicação Didática:** Apresentação detalhada da metodologia utilizada para chegar à solução, servindo como material de estudo.

## 3. Tecnologias Utilizadas

- **Linguagem:** Python 3.x
- **Bibliotecas Principais:**
  - `control`: Para manipulação de funções de transferência e simulações.
  - `numpy`: Para operações numéricas.
  - `matplotlib`: Para a geração de gráficos e diagramas.
  - `[openai ou google-generativeai]`: Para interação com a API do LLM.
- **Ambiente:** Gerenciado via `venv` e `requirements.txt`.

## 4. Status do Projeto

**Fase Atual:** Fase 1 - Fundamentação e Prova de Conceito.

## 5. Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/TCC-Geracao-Modelos-LLM.git](https://github.com/seu-usuario/TCC-Geracao-Modelos-LLM.git)
    cd TCC-Geracao-Modelos-LLM
    ```

2.  **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    pip install python-dotenv
    pip install google-generativeai
    ```

4.  **Configure as variáveis de ambiente:**
    - Crie um arquivo `.env` na raiz do projeto.
    - Adicione sua chave de API: `GOOGLE_API_KEY="sua_chave_secreta"`

---
