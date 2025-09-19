import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega a chave de API do arquivo .env
load_dotenv()
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    print("Modelos de IA generativa disponíveis que suportam 'generateContent':")
    print("-----------------------------------------------------------------")

    # Itera sobre a lista de modelos e verifica se eles suportam o método que precisamos
    for m in genai.list_models():
      if 'generateContent' in m.supported_generation_methods:
        print(m.name)

except Exception as e:
    print(f"Ocorreu um erro ao listar os modelos: {e}")