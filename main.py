"""
API RESTful para Modelagem de Sistemas de Controle via LLM.
Trabalho de Conclusão de Curso - Engenharia de Controle e Automação.

Autor: Laan Carlos Nunes Mendes de Barros
"""

import base64
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Any, Callable

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from schemas import (
    ProblemaRequest,
    AnaliseCompletaResponse,
    ProviderRespostaSchema,
    ErrorResponse,
)
from llm_service import get_llm_service, LLMError, LLMParseError
from diagram_executor import execute_diagram_python, save_diagram_pngs_to_disk
from diagram_renderer import render_diagram_graph
from ft_verification import (
    mensagem_verificacao_consolidada,
    verify_transfer_function,
)
from graph_validation import DiagramGraph, verify_diagram_graph
from ensemble_service import EnsembleOutcome, run_ensemble_analise

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api")

APP_VERSION = "7.0.0"
MAX_DESCRIPTION_LOG_LENGTH = 100


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando API de Modelagem...")
    logger.info("Modelo LLM configurado: %s", settings.llm_model)
    try:
        get_llm_service()
        logger.info("Serviço LLM inicializado com sucesso.")
    except Exception as e:
        logger.error("Falha ao inicializar serviço LLM: %s", e)
    yield
    logger.info("Encerrando API...")


app = FastAPI(
    title="TCC - API de Modelagem de Sistemas de Controle",
    description="""
API baseada em LLMs para auxiliar estudantes na modelagem de sistemas dinâmicos.

Fluxo único: a descrição do sistema é enviada em paralelo aos provedores configurados
(Google, Anthropic, Groq, OpenAI). O voto por equivalência simbólica da função de
transferência escolhe a análise completa que será devolvida.
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


def _error_content(message: str, raw_response: str | None = None) -> dict:
    content = {"sucesso": False, "erro": message}
    if raw_response:
        content["resposta_bruta"] = raw_response[:1000]
    return content


def _llm_error_to_json_response(exception: Exception) -> JSONResponse:
    logger.error("Erro no processamento: %s", exception)
    raw = getattr(exception, "raw_response", None) if isinstance(exception, LLMParseError) else None
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_content(str(exception), raw),
    )


def with_llm_error_handling(handler: Callable):
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


@app.get("/", tags=["Health"])
def root():
    """Verificação de saúde da API."""
    return {
        "status": "online",
        "versao": APP_VERSION,
        "modelo_llm": settings.llm_model,
    }


def _truncate_for_log(description: str, max_len: int = MAX_DESCRIPTION_LOG_LENGTH) -> str:
    return (description[:max_len] + "...") if len(description) > max_len else description


def _attach_verification(payload: dict[str, Any], descricao: str) -> None:
    if not settings.ft_verification_enabled:
        payload["verificacao_executada"] = False
        payload["verificacao_ft_ok"] = True
        payload["mensagem_verificacao"] = None
        return

    out = verify_transfer_function(descricao, payload["funcao_transferencia"])
    payload["verificacao_executada"] = True
    payload["verificacao_ft_ok"] = out.ok
    msg = mensagem_verificacao_consolidada(out)
    if msg is None and settings.debug:
        payload["mensagem_verificacao"] = "Verificação executada: nenhum problema detectado."
    else:
        payload["mensagem_verificacao"] = msg


def _attach_graph_verification(payload: dict[str, Any], funcao_transferencia: str) -> None:
    grafo_data = payload.get("grafo_diagrama")
    if not settings.graph_validation_enabled or not grafo_data:
        payload["verificacao_grafo_executada"] = False
        payload["verificacao_grafo_ok"] = True
        payload["mensagem_verificacao_grafo"] = None
        payload["ft_derivada_grafo"] = None
        return

    try:
        graph = DiagramGraph(**grafo_data)
        out = verify_diagram_graph(graph, funcao_transferencia)
    except Exception as exc:  # noqa: BLE001 — estrutura arbitrária vinda do LLM
        payload["verificacao_grafo_executada"] = True
        payload["verificacao_grafo_ok"] = False
        payload["mensagem_verificacao_grafo"] = f"grafo: estrutura inválida — {exc}"
        payload["ft_derivada_grafo"] = None
        return

    payload["verificacao_grafo_executada"] = True
    payload["verificacao_grafo_ok"] = out.ok
    payload["ft_derivada_grafo"] = out.ft_derivada_grafo
    payload["mensagem_verificacao_grafo"] = None if out.ok else "; ".join(out.problemas)


def _attach_diagrams(payload: dict[str, Any]) -> None:
    """Anexa imagens: opcionalmente executa código da LLM; sempre tenta o render do grafo."""
    codigo = (payload.get("codigo_diagrama") or "").strip()
    if settings.execute_diagram_code and codigo:
        exe = execute_diagram_python(codigo, save_prefix="diagrama")
        payload["diagramas_png_base64"] = list(exe.diagramas_png_base64)
        payload["execucao_diagrama_ok"] = exe.execucao_ok
        payload["diagramas_arquivos"] = list(exe.diagramas_arquivos)
        payload["log_execucao_diagrama"] = (
            exe.log_execucao if (not exe.execucao_ok or settings.debug) else None
        )
        logger.info(
            "exec diagram: ok=%s imagens=%d",
            exe.execucao_ok,
            len(exe.diagramas_png_base64),
        )
    else:
        payload.setdefault("diagramas_png_base64", [])
        payload["execucao_diagrama_ok"] = False
        payload.setdefault("diagramas_arquivos", [])
        payload["log_execucao_diagrama"] = None

    grafo_data = payload.get("grafo_diagrama")
    if not settings.graph_render_enabled or not grafo_data:
        return
    try:
        graph = DiagramGraph(**grafo_data)
        png_bytes = render_diagram_graph(graph)
    except Exception as exc:  # noqa: BLE001 — grafo malformado
        logger.warning("Falha ao renderizar grafo deterministicamente: %s", exc)
        return

    saved = save_diagram_pngs_to_disk([png_bytes], "diagrama_grafo")
    b64 = base64.standard_b64encode(png_bytes).decode("ascii")
    payload.setdefault("diagramas_png_base64", []).append(b64)
    payload.setdefault("diagramas_arquivos", []).extend(saved)


def _attach_ensemble(payload: dict[str, Any], outcome: EnsembleOutcome) -> None:
    payload["ensemble_executado"] = outcome.executado
    payload["ensemble_concordancia"] = outcome.concordancia
    payload["ensemble_consenso_ft"] = outcome.consenso_ft
    payload["ensemble_provedor_vencedor"] = outcome.provedor_vencedor
    payload["ensemble_mensagem"] = outcome.mensagem
    payload["ensemble_respostas"] = [
        ProviderRespostaSchema(
            provedor=r.provedor,
            modelo=r.modelo,
            sucesso=r.sucesso,
            funcao_transferencia=r.funcao_transferencia,
            erro=r.erro,
        ).model_dump()
        for r in outcome.respostas
    ]


@app.post(
    "/gerar-analise-completa",
    response_model=AnaliseCompletaResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Gera a análise completa do sistema (com ensemble)",
    description="""
Recebe a descrição de um sistema dinâmico. Os LLMs configurados geram a análise
em paralelo; o voto pela função de transferência (equivalência simbólica) escolhe
qual resposta é devolvida — lei aplicada, EDO, Laplace, FT, análise, grafo e diagramas.
    """,
    tags=["Modelagem"],
)
@with_llm_error_handling
def api_gerar_analise_completa(request: ProblemaRequest):
    """Gera análise completa: o resultado mostrado é o mais votado no ensemble."""
    logger.info("Requisição /gerar-analise-completa: %s", _truncate_for_log(request.descricao))

    outcome = run_ensemble_analise(request.descricao)
    if not outcome.payload_vencedor:
        raise LLMError(
            outcome.mensagem or "Nenhum provedor conseguiu gerar a análise completa."
        )

    payload = dict(outcome.payload_vencedor)
    _attach_ensemble(payload, outcome)
    _attach_verification(payload, request.descricao)
    _attach_graph_verification(payload, payload["funcao_transferencia"])
    if payload.get("grafo_diagrama") or payload.get("codigo_diagrama"):
        _attach_diagrams(payload)
    return payload


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
