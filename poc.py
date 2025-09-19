import os
from dotenv import load_dotenv

# --- SEÇÃO DE CONFIGURAÇÃO (ESCOLHA SEU PROVEDOR DE LLM) ---

# Descomente esta seção se estiver usando a API da OpenAI (ChatGPT)
# import openai
# load_dotenv()
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Descomente esta seção se estiver usando a API do Google (Gemini)
import google.generativeai as genai
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --------------------------------------------------------------------

def gerar_modelo_com_llm(descricao_problema: str) -> str:
    """
    Envia a descrição de um problema de modelagem para o LLM e retorna a resposta.
    """
    
    # O prompt é a parte mais crítica. Ele define o "contrato" com o LLM.
    # Instruímos seu papel, a tarefa, o contexto e, crucialmente, o formato da saída.
    prompt = f"""
    Você é um especialista sênior em Engenharia de Controle e Automação, com vasta
    experiência em modelagem de sistemas dinâmicos. Sua principal habilidade é 
    transformar descrições de sistemas físicos em modelos matemáticos.

    Tarefa:
    Analise a seguinte descrição de um sistema dinâmico, fornecida pelo usuário,
    e derive a sua função de transferência no domínio de Laplace, G(s).

    Descrição do Sistema:
    "{descricao_problema}"

    Formato da Resposta:
    Sua resposta DEVE ser estruturada em duas partes, separadas por '---'.

    Parte 1: Passo a Passo da Modelagem
    Explique de forma clara e didática todo o raciocínio para chegar à equação 
    diferencial do sistema. Cite a lei física fundamental aplicada (ex: Segunda Lei 
    de Newton, Lei de Kirchhoff, etc.). Em seguida, demonstre a aplicação da 
    Transformada de Laplace, considerando condições iniciais nulas, para obter a 
    função de transferência.

    ---

    Parte 2: Função de Transferência Final
    Apresente APENAS a função de transferência final no formato exato:
    G(s) = [numerador] / [denominador]
    
    Exemplo para um sistema RC: G(s) = 1 / (R*C*s + 1)
    """

    print("--- ENVIANDO PROMPT PARA O LLM ---")
    print(prompt)
    print("------------------------------------")
    
    try:
        # --- LÓGICA DE CHAMADA DA API (ESCOLHA SEU PROVEDOR) ---

        # Descomente esta seção se estiver usando a API da OpenAI (ChatGPT)
        # response = client.chat.completions.create(
        #     model="gpt-4-turbo", # ou outro modelo de sua preferência
        #     messages=[
        #         {"role": "system", "content": "Você é um especialista em Engenharia de Controle."},
        #         {"role": "user", "content": prompt}
        #     ]
        # )
        # return response.choices[0].message.content

        # Descomente esta seção se estiver usando a API do Google (Gemini)
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        return response.text

        # -------------------------------------------------------------

    except Exception as e:
        return f"Ocorreu um erro ao chamar a API: {e}"

# --- EXECUÇÃO PRINCIPAL DO SCRIPT ---
if __name__ == "__main__":
    
    # Descrição do nosso problema de teste
    descricao_massa_mola = (
        "Um sistema é composto por um bloco de massa 'M' conectado a uma parede por "
        "uma mola de constante elástica 'K' e um amortecedor com coeficiente de "
        "amortecimento viscoso 'B'. Uma força externa 'F(t)' é aplicada ao bloco. "
        "Considere o deslocamento do bloco 'x(t)' como a saída do sistema. "
        "O objetivo é encontrar a função de transferência G(s) = X(s) / F(s)."
    )

    # Chama a função que interage com o LLM
    resultado_llm = gerar_modelo_com_llm(descricao_massa_mola)

    print("\n--- RESPOSTA RECEBIDA DO LLM ---")
    print(resultado_llm)
    print("----------------------------------")

    # Próximo passo (para as próximas fases do TCC):
    # Aqui entrará a lógica para validar e parsear a resposta.
    # Por exemplo, poderíamos dividir a resposta pelo '---' e usar 
    # a segunda parte para instanciar um objeto na biblioteca 'control'.
    
    if '---' in resultado_llm:
        partes = resultado_llm.split('---')
        ft_string = partes[1].strip()
        print(f"\n[PoC] Função de Transferência extraída: {ft_string}")
        # Exemplo de como usaríamos a string no futuro:
        # G_s_texto = ft_string.replace('G(s) = ', '')
        # numerador, denominador = parse_ft(G_s_texto) # (função a ser criada)
        # G = control.tf(numerador, denominador)