"""
API RESTful para Modelagem de Sistemas de Controle via LLM.
Trabalho de Conclusão de Curso - Engenharia de Controle e Automação.

Autor: Laan Carlos Nunes Mendes de Barros
"""

import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable, Type

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from schemas import (
    ProblemaRequest,
    ValidacaoRequest,
    FuncaoTransferenciaRequest,
    FuncaoTransferenciaResponse,
    DiagramaBlocosResponse,
    FuncaoTransferenciaEDiagramaResponse,
    AnaliseCompletaResponse,
    ValidacaoResponse,
    ErrorResponse,
)
from prompts import (
    formatar_prompt_ft,
    formatar_prompt_analise_completa,
    formatar_prompt_validacao,
    formatar_prompt_diagrama_por_ft,
    formatar_prompt_ft_e_diagrama,
)
from pydantic import BaseModel

from llm_service import get_llm_service, LLMError, LLMParseError
from diagram_executor import DiagramExecResult, execute_diagram_python

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api")

APP_VERSION = "6.1.0"
MAX_DESCRIPTION_LOG_LENGTH = 100


# -----------------------------------------------------------------------------
# Lifecycle
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    logger.info("Iniciando API de Modelagem...")
    logger.info("Modelo LLM configurado: %s", settings.llm_model)

    try:
        get_llm_service()
        logger.info("Serviço LLM inicializado com sucesso.")
    except Exception as e:
        logger.error("Falha ao inicializar serviço LLM: %s", e)

    yield

    logger.info("Encerrando API...")


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------

app = FastAPI(
    title="TCC - API de Modelagem de Sistemas de Controle",
    description="""
API baseada em Inteligência Artificial (LLMs) para auxiliar estudantes
na modelagem de sistemas dinâmicos.

## Funcionalidades

* **Gerar Função de Transferência** - Retorna apenas a FT do sistema
* **Análise Completa** - Retorna análise detalhada com explicação didática
* **Validar Resposta** - Modo tutor que avalia respostas do aluno

## Tecnologias

* FastAPI + Uvicorn
* Google Gemini/Gemma (LLM)
* Python Control (Diagramas de Blocos)
    """,
    version=APP_VERSION,
    lifespan=lifespan,
    contact={"name": "Laan Carlos Barros", "email": "laancarlosbarros@gmail.com"},
    license_info={"name": "CEFET-MG"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.cors_allow_headers_list,
)


# -----------------------------------------------------------------------------
# Error handling (single place, DRY)
# -----------------------------------------------------------------------------

def _error_content(message: str, raw_response: str | None = None) -> dict:
    """Conteúdo JSON padrão para respostas de erro (DRY)."""
    content = {"sucesso": False, "erro": message}
    if raw_response:
        content["resposta_bruta"] = raw_response[:1000]
    return content


def _llm_error_to_json_response(exception: Exception) -> JSONResponse:
    """Converte exceção do LLM em JSONResponse com status 500."""
    logger.error("Erro no processamento: %s", exception)
    raw = getattr(exception, "raw_response", None) if isinstance(exception, LLMParseError) else None
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_content(str(exception), raw),
    )


def with_llm_error_handling(handler: Callable):
    """Decorator: trata LLMError e Exception e retorna JSONResponse em caso de erro."""

    @wraps(handler)
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except LLMError as e:
            return _llm_error_to_json_response(e)
        except Exception as e:
            logger.exception("Erro inesperado em %s", handler.__name__)
            return JSONResponse(
                status_code=500,
                content=_error_content(str(e)),
            )

    return wrapper


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    """Verificação de saúde da API."""
    return {
        "status": "online",
        "versao": APP_VERSION,
        "modelo_llm": settings.llm_model,
    }


def _truncate_for_log(description: str, max_len: int = MAX_DESCRIPTION_LOG_LENGTH) -> str:
    """Retorna descrição truncada para log."""
    return (description[:max_len] + "...") if len(description) > max_len else description


def _attach_diagram_execution(payload: dict[str, Any], exe: DiagramExecResult) -> None:
    """Acrescenta campos de execução automática do código matplotlib ao payload."""
    payload["diagramas_png_base64"] = exe.diagramas_png_base64
    payload["execucao_diagrama_ok"] = exe.execucao_ok
    if not exe.execucao_ok or settings.debug:
        payload["log_execucao_diagrama"] = exe.log_execucao
    else:
        payload["log_execucao_diagrama"] = None


def _generate_diagram_then_execute(
    prompt: str, response_schema: Type[BaseModel], handler_name: str
) -> dict[str, Any]:
    """Chama LLM e executa código de diagrama no subprocesso quando habilitado."""
    llm = get_llm_service()
    payload = llm.generate(prompt, response_schema)
    exe = execute_diagram_python(payload.get("codigo_diagrama") or "")
    _attach_diagram_execution(payload, exe)
    logger.info("%s exec diagram: ok=%s imagens=%d", handler_name, exe.execucao_ok, len(exe.diagramas_png_base64))
    return payload


@app.post(
    "/gerar-apenas-ft",
    response_model=FuncaoTransferenciaResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Gera apenas a Função de Transferência",
    description="""
Recebe a descrição de um sistema dinâmico e retorna um JSON simples
contendo apenas a string da função de transferência final.

**Ideal para:** Validação rápida de respostas.
    """,
    tags=["Modelagem"],
)
@with_llm_error_handling
def api_gerar_apenas_ft(request: ProblemaRequest):
    """Gera apenas a função de transferência do sistema."""
    logger.info("Requisição /gerar-apenas-ft: %s", _truncate_for_log(request.descricao))
    llm = get_llm_service()
    prompt = formatar_prompt_ft(request.descricao)
    return llm.generate(prompt, FuncaoTransferenciaResponse)


@app.post(
    "/gerar-diagrama-por-ft",
    response_model=DiagramaBlocosResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Gera diagrama de blocos a partir da FT",
    description="""
Recebe uma função de transferência textual e devolve código Python que desenha
**diagrama de blocos completo** (blocos, setas, malha de soma, realimentação quando
cabível — incluindo vista equivalente com H(s)=1 além da cadeia U→[G]→Y) com matplotlib,
além de `control` para simulação quando a FT permitir valores numéricos.

**Ideal para:** quando a FT já foi obtida e você quer o esquema e gráficos de apoio.
    """,
    tags=["Modelagem"],
)
@with_llm_error_handling
def api_gerar_diagrama_por_ft(request: FuncaoTransferenciaRequest):
    """Gera código de diagrama de blocos usando uma FT já informada."""
    logger.info("Requisição /gerar-diagrama-por-ft")
    prompt = formatar_prompt_diagrama_por_ft(request.funcao_transferencia)
    return _generate_diagram_then_execute(prompt, DiagramaBlocosResponse, "gerar-diagrama-por-ft")


@app.post(
    "/gerar-ft-e-diagrama",
    response_model=FuncaoTransferenciaEDiagramaResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Gera FT e diagrama de blocos no mesmo endpoint",
    description="""
Recebe a descrição do sistema dinâmico e retorna a FT mais código Python para
**diagrama de blocos completo** segundo a física/topologia inferida (sem inventar malha
fechada quando o problema for explicitamente malha aberta), com matplotlib e `control`.

**Ideal para:** fluxo completo de modelagem mais esquema de blocos pronto para executar.
    """,
    tags=["Modelagem"],
)
@with_llm_error_handling
def api_gerar_ft_e_diagrama(request: ProblemaRequest):
    """Gera FT e código de diagrama de blocos em uma única resposta."""
    logger.info("Requisição /gerar-ft-e-diagrama: %s", _truncate_for_log(request.descricao))
    prompt = formatar_prompt_ft_e_diagrama(request.descricao)
    return _generate_diagram_then_execute(prompt, FuncaoTransferenciaEDiagramaResponse, "gerar-ft-e-diagrama")


@app.post(
    "/gerar-analise-completa",
    response_model=AnaliseCompletaResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Gera a análise completa do sistema",
    description="""
Recebe a descrição de um sistema dinâmico e retorna um JSON detalhado
com análise completa: lei aplicada, EDO, Laplace, FT, análise e código.

**Ideal para:** Aprendizado e estudo detalhado.
    """,
    tags=["Modelagem"],
)
@with_llm_error_handling
def api_gerar_analise_completa(request: ProblemaRequest):
    """Gera análise completa do sistema com explicação didática."""
    logger.info("Requisição /gerar-analise-completa: %s", _truncate_for_log(request.descricao))
    llm = get_llm_service()
    prompt = formatar_prompt_analise_completa(request.descricao)
    return llm.generate(prompt, AnaliseCompletaResponse)


@app.post(
    "/validar-minha-resposta",
    response_model=ValidacaoResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Valida a resposta de um usuário",
    description="""
Tutor interativo: o aluno envia a descrição e sua FT; a IA avalia e dá feedback.

**Ideal para:** Prática e auto-avaliação.
    """,
    tags=["Tutor"],
)
@with_llm_error_handling
def api_validar_resposta(request: ValidacaoRequest):
    """Valida a resposta do usuário e fornece feedback."""
    logger.info("Requisição /validar-minha-resposta: %s", _truncate_for_log(request.descricao))
    logger.info("Resposta do usuário: %s", request.funcao_transferencia_usuario)
    llm = get_llm_service()
    prompt = formatar_prompt_validacao(
        request.descricao,
        request.funcao_transferencia_usuario,
    )
    return llm.generate(prompt, ValidacaoResponse)


# -----------------------------------------------------------------------------
# Server
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
