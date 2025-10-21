import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, Response, status
from pydantic import BaseModel, Field # Importamos Field para exemplos
import uvicorn
import json

# --- MODELOS DE DADOS COM EXEMPLOS PARA A DOCUMENTAÇÃO ---
class ProblemaRequest(BaseModel):
    descricao: str

    class Config:
        schema_extra = {
            "example": {
                "descricao": "Um sistema é composto por um bloco de massa 'M' e uma mola 'K'. Encontre a função de transferência G(s) = X(s)/F(s)."
            }
        }

class ValidacaoRequest(BaseModel):
    descricao: str
    funcao_transferencia_usuario: str

    class Config:
        schema_extra = {
            "example": {
                "descricao": "Um circuito RC em série. A saída é a tensão no capacitor.",
                "funcao_transferencia_usuario": "G(s) = R / (RCs + 1)"
            }
        }

# --- INICIALIZAÇÃO DA APLICAÇÃO FASTAPI ---
app = FastAPI(
    title="Parceiro do TCC - API de Modelagem",
    description="API com múltiplos endpoints para gerar e validar modelos de sistemas de controle.",
    version="5.0.0"
)

# --- CONFIGURAÇÃO DA API DO GOOGLE ---
try:
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    llm_model = genai.GenerativeModel('models/gemma-3-12b-it')
except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível configurar a API do Google. Erro: {e}")

# --- FUNÇÃO GENÉRICA PARA CHAMAR O LLM ---
def chamar_llm(prompt: str) -> dict:
    """Função central que envia um prompt e retorna um JSON ou um erro."""
    try:
        response = llm_model.generate_content(prompt)
        texto_limpo = response.text.strip().replace("```json", "").replace("```", "")
        dados_json = json.loads(texto_limpo)
        return {"sucesso": True, "dados": dados_json}
    except json.JSONDecodeError:
        return {"sucesso": False, "erro": "O LLM não retornou um JSON válido.", "resposta_bruta": response.text}
    except Exception as e:
        return {"sucesso": False, "erro": f"Falha na API do LLM: {e}"}

# --- ADICIONANDO DESCRIÇÕES ÀS ROTAS PARA MELHORAR O /docs ---

@app.post("/gerar-apenas-ft", 
            summary="Gera apenas a Função de Transferência",
            description="Recebe a descrição de um sistema e retorna um JSON simples contendo apenas a string da função de transferência final.")
def api_gerar_apenas_ft(request: ProblemaRequest, http_response: Response):
    prompt = f"""
    Analise a descrição do sistema e retorne APENAS sua função de transferência.
    Descrição: "{request.descricao}"
    Sua resposta DEVE ser um objeto JSON válido contendo uma única chave: "funcao_transferencia".
    Exemplo de resposta: {{"funcao_transferencia": "G(s) = 1 / (RCs + 1)"}}
    """
    resultado = chamar_llm(prompt)
    if not resultado["sucesso"]:
        http_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return resultado
    return resultado["dados"]

@app.post("/gerar-analise-completa",
            summary="Gera a análise completa do sistema",
            description="Recebe a descrição de um sistema e retorna um JSON detalhado com 5 campos: lei aplicada, equação diferencial, passos de Laplace, função de transferência e análise do resultado.")
def api_gerar_analise_completa(request: ProblemaRequest, http_response: Response):
    prompt = f"""
    Sua tarefa é analisar a descrição de um sistema de controle e derivar sua função de transferência.
    Descrição do Sistema: "{request.descricao}"
    Instruções de Formato: Sua resposta DEVE ser um objeto JSON válido contendo as seguintes chaves: "lei_aplicada", "equacao_diferencial", "passos_laplace", "funcao_transferencia", "analise_resultado".
    """
    resultado = chamar_llm(prompt)
    if not resultado["sucesso"]:
        http_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return resultado
    return resultado["dados"]

@app.post("/validar-minha-resposta",
            summary="Valida a resposta de um usuário",
            description="Atua como um tutor interativo. Recebe a descrição de um sistema e a FT calculada pelo usuário, retornando se está correta, um feedback e a solução correta.")
def api_validar_resposta(request: ValidacaoRequest, http_response: Response):
    prompt = f"""
    Sua tarefa é atuar como um tutor de engenharia de controle. Avalie se a resposta do aluno está correta.
    Descrição do Sistema: "{request.descricao}"
    Função de Transferência do aluno: "{request.funcao_transferencia_usuario}"
    Instruções de Formato: Sua resposta DEVE ser um objeto JSON válido contendo as chaves: "resposta_correta" (booleano), "feedback" (string) e "solucao_correta" (string).
    """
    resultado = chamar_llm(prompt)
    if not resultado["sucesso"]:
        http_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return resultado
    return resultado["dados"]

# --- FUNÇÃO PARA INICIAR O SERVIDOR ---
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)