# =============================================================================
# Dockerfile para API de Modelagem de Sistemas de Controle
# TCC - Engenharia de Controle e Automação
# =============================================================================

# --- Imagem Base ---
FROM python:3.11-slim

# --- Metadados ---
LABEL maintainer="Laan Carlos"
LABEL description="API de Modelagem de Sistemas de Controle via LLM"
LABEL version="6.0.0"

# --- Variáveis de Ambiente ---
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# --- Diretório de Trabalho ---
WORKDIR /app

# --- Instalação de Dependências do Sistema ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# --- Copia arquivos de dependências primeiro (para cache do Docker) ---
COPY requirements.txt .

# --- Instalação de Dependências Python ---
RUN pip install --no-cache-dir -r requirements.txt

# --- Copia código fonte ---
COPY *.py ./

# --- Cria usuário não-root para segurança ---
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app
USER appuser

# --- Porta exposta ---
EXPOSE 8000

# --- Health Check ---
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# --- Comando de Inicialização ---
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
