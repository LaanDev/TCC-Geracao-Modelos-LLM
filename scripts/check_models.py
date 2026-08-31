"""
Lista modelos da API Google GenAI que suportam generateContent.
Execute na raiz do projeto (com .env configurado): python scripts/check_models.py
"""
import os
from pathlib import Path
from google import genai
from dotenv import load_dotenv

# Carrega a chave de API do arquivo .env (na raiz do projeto)
raiz = Path(__file__).resolve().parent.parent
load_dotenv(raiz / ".env")
try:
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    print("Modelos de IA generativa disponíveis que suportam 'generateContent':")
    print("-----------------------------------------------------------------")

    # Itera sobre a lista de modelos e verifica se eles suportam a ação que precisamos
    for m in client.models.list():
        if "generateContent" in (m.supported_actions or []):
            print(m.name)

except Exception as e:
    print(f"Ocorreu um erro ao listar os modelos: {e}")
