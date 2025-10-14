import os
from dotenv import load_dotenv
import google.generativeai as genai

# --- CONFIGURAÇÃO DA API ---
# Carrega as variáveis de ambiente (sua chave de API) do arquivo .env
load_dotenv()
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Erro ao configurar a API. Verifique seu arquivo .env e a chave. Erro: {e}")
    exit()

# --------------------------------------------------------------------

def gerar_modelo_com_llm(descricao_problema: str) -> str:
    """
    Envia a descrição de um problema de modelagem para o LLM e retorna a resposta.
    """
    
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
    de Newton, Lei de Kirchhoff das Tensões, etc.). Em seguida, demonstre a aplicação da 
    Transformada de Laplace, considerando condições iniciais nulas, para obter a 
    função de transferência.

    ---

    Parte 2: Função de Transferência Final
    Apresente APENAS a função de transferência final no formato exato:
    G(s) = [numerador] / [denominador]
    
    Exemplo para um sistema RC: G(s) = 1 / (R*C*s + 1)
    """

    print("--- ENVIANDO PROMPT PARA O LLM ---")
    print(f"Descrição do Problema Enviado:\n\"{descricao_problema}\"")
    print("------------------------------------")
    
    try:
        # Modelo que se provou estável para sua chave de API
        model = genai.GenerativeModel('models/gemma-3-12b-it')
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Ocorreu um erro ao chamar a API: {e}"

# --- EXECUÇÃO PRINCIPAL DO SCRIPT ---
if __name__ == "__main__":
    
    # --- BANCADA DE TESTES ---
    # Para rodar um teste, comente os outros e descomente o desejado.
    
    # Teste 1: Sistema Massa-Mola-Amortecedor (Mecânico Translacional)
    # descricao_problema = "Um sistema é composto por um bloco de massa 'M' conectado a uma parede por uma mola de constante elástica 'K' e um amortecedor com coeficiente de amortecimento viscoso 'B'. Uma força externa 'F(t)' é aplicada ao bloco. Considere o deslocamento do bloco 'x(t)' como a saída do sistema. O objetivo é encontrar a função de transferência G(s) = X(s) / F(s)."
    
    # Teste 2: Circuito RLC Série (Elétrico)
    # descricao_problema = "Um circuito elétrico é composto por um resistor 'R', um indutor 'L' e um capacitor 'C' conectados em série a uma fonte de tensão de entrada 'Vin(t)'. Considere a tensão sobre o capacitor, 'Vc(t)', como a saída do sistema. O objetivo é encontrar a função de transferência G(s) = Vc(s) / Vin(s)."

    # Teste 3: Circuito RC (Elétrico - 1ª Ordem)
    descricao_problema = "Um circuito elétrico é composto por um resistor 'R' e um capacitor 'C' em série, alimentado por uma fonte de tensão de entrada 'Vin(t)'. A saída do sistema é a tensão sobre o capacitor, 'Vc(t)'. Encontre a função de transferência G(s) = Vc(s) / Vin(s)."

    # Teste 4: Sistema de Nível de Tanque (Processos)
    # descricao_problema = "Um tanque possui uma área de seção transversal constante 'A' e uma resistência hidráulica de saída 'R'. A vazão de entrada no tanque é 'q_in(t)' e a altura do líquido é 'h(t)'. A vazão de saída é proporcional à altura, de modo que 'q_out(t) = h(t)/R'. Considere a vazão de entrada como a entrada do sistema e a altura do líquido como a saída. Encontre a função de transferência G(s) = H(s) / Q_in(s)."

    # Teste 5: Motor CC Controlado pela Armadura (Eletromecânico)
    # descricao_problema = "Considere um motor CC controlado pela armadura. A tensão de armadura é 'Va(t)', a corrente de armadura é 'ia(t)', a resistência da armadura é 'Ra' e a indutância é 'La'. O motor tem uma constante de torque 'Kt' e uma constante de força contra-eletromotriz 'Kb'. O rotor tem inércia 'J' e atrito viscoso 'B'. A saída do sistema é a posição angular do eixo, 'theta(t)'. Encontre a função de transferência G(s) = Theta(s) / Va(s)."

    # ----------------------------------------------------------------

    # Chama a função que interage com o LLM
    resultado_llm = gerar_modelo_com_llm(descricao_problema)

    print("\n--- RESPOSTA RECEBIDA DO LLM ---")
    print(resultado_llm)
    print("----------------------------------")