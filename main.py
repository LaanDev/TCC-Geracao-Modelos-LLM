"""
API RESTful para Modelagem de Sistemas de Controle via LLM.
Trabalho de Conclusão de Curso - Engenharia de Controle e Automação.

Autor: Laan Carlos Nunes Mendes de Barros
"""

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
    ValidacaoRequest,
    FuncaoTransferenciaRequest,
    FuncaoTransferenciaResponse,
    DiagramaBlocosResponse,
    FuncaoTransferenciaEDiagramaResponse,
    AnaliseCompletaResponse,
    ValidacaoResponse,
    EnsembleFTResponse,
    ProviderRespostaSchema,
    ErrorResponse,
)
from prompts import (
    formatar_prompt_ft,
    formatar_prompt_analise_completa,
    formatar_prompt_validacao,
    formatar_prompt_diagrama_por_ft,
    formatar_prompt_ft_e_diagrama,
    formatar_prompt_correcao_apenas_ft,
    formatar_prompt_correcao_ft_e_diagrama,
    formatar_prompt_correcao_diagrama_por_ft,
)
from llm_service import get_llm_service, LLMError, LLMParseError
from diagram_executor import DiagramExecResult, execute_diagram_python
from ft_verification import (
    FTVerificationOutcome,
    merge_outcomes_ft_e_diagrama,
    mensagem_verificacao_consolidada,
    verify_diagram_physical_layout,
    verify_transfer_function,
)
from graph_validation import DiagramGraph, verify_diagram_graph
from ensemble_service import run_ensemble_ft, verify_ft_with_ensemble

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("api")

APP_VERSION = "6.2.0"
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
    payload["diagramas_arquivos"] = exe.diagramas_arquivos
    if not exe.execucao_ok or settings.debug:
        payload["log_execucao_diagrama"] = exe.log_execucao
    else:
        payload["log_execucao_diagrama"] = None


_DIAGRAM_SAVE_PREFIX: dict[str, str] = {
    "gerar-diagrama-por-ft": "diagrama_rota3",
    "gerar-ft-e-diagrama": "diagrama_rota4",
    "gerar-analise-completa": "diagrama_rota5",
}


def _attach_verification_standard(
    payload: dict[str, Any],
    outcome: FTVerificationOutcome,
    *,
    executed: bool,
    retried: bool,
) -> None:
    """Campos comuns de verificação (FT / FT da requisição)."""
    payload["verificacao_executada"] = executed
    payload["nova_tentativa_pos_verificacao"] = retried
    if not executed:
        payload["verificacao_ft_ok"] = True
        payload["mensagem_verificacao"] = None
        return
    payload["verificacao_ft_ok"] = outcome.ok
    msg = mensagem_verificacao_consolidada(outcome)
    if msg is None and settings.debug:
        payload["mensagem_verificacao"] = "Verificação executada: nenhum problema detectado."
    else:
        payload["mensagem_verificacao"] = msg


def _attach_verification_ft_diagram(
    payload: dict[str, Any],
    outcome: FTVerificationOutcome,
    *,
    executed: bool,
    retried: bool,
) -> None:
    """Verificação no fluxo descrição → FT + código (inclui layout físico quando aplicável)."""
    _attach_verification_standard(payload, outcome, executed=executed, retried=retried)
    if not executed:
        payload["verificacao_layout_fisico_ok"] = None
    else:
        payload["verificacao_layout_fisico_ok"] = outcome.layout_diagrama_fisico_ok


def _attach_graph_verification(payload: dict[str, Any], funcao_transferencia: str) -> None:
    """
    Valida, quando presente, o grafo do diagrama por redução algébrica (Fórmula de Ganho
    de Mason) contra `funcao_transferencia`. Ausência ou malformação do grafo nunca bloqueia
    a resposta — só fica registrada como verificacao_grafo_executada=False (sem grafo) ou
    verificacao_grafo_ok=False (grafo presente, mas inválido/incoerente).
    """
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
    except Exception as exc:  # noqa: BLE001 — domínio: estrutura arbitrária vinda do LLM
        payload["verificacao_grafo_executada"] = True
        payload["verificacao_grafo_ok"] = False
        payload["mensagem_verificacao_grafo"] = f"grafo: estrutura inválida — {exc}"
        payload["ft_derivada_grafo"] = None
        return

    payload["verificacao_grafo_executada"] = True
    payload["verificacao_grafo_ok"] = out.ok
    payload["ft_derivada_grafo"] = out.ft_derivada_grafo
    payload["mensagem_verificacao_grafo"] = None if out.ok else "; ".join(out.problemas)


def _attach_ensemble_verification(payload: dict[str, Any], descricao: str) -> None:
    """
    Cruza a FT já obtida (tipicamente do Google) com o consenso entre os provedores de
    LLM configurados (Ensemble, Seção 3.4). Como as demais camadas de verificação, nunca
    bloqueia a resposta: sem provedores suficientes, fica só marcada como não executada.
    """
    if not settings.ensemble_enabled:
        payload["verificacao_ensemble_executada"] = False
        payload["verificacao_ensemble_ok"] = True
        payload["mensagem_verificacao_ensemble"] = None
        payload["ensemble_concordancia"] = None
        payload["ensemble_consenso_ft"] = None
        return

    out = verify_ft_with_ensemble(descricao, payload["funcao_transferencia"])
    payload["verificacao_ensemble_executada"] = out.executado
    payload["verificacao_ensemble_ok"] = out.ok
    payload["mensagem_verificacao_ensemble"] = out.mensagem
    payload["ensemble_concordancia"] = out.concordancia
    payload["ensemble_consenso_ft"] = out.consenso_ft


def _merged_verify_ft_e_diagrama(descricao: str, payload: dict[str, Any]) -> FTVerificationOutcome:
    ft_out = verify_transfer_function(descricao, payload["funcao_transferencia"])
    layout_out = verify_diagram_physical_layout(descricao, payload.get("codigo_diagrama") or "")
    return merge_outcomes_ft_e_diagrama(ft_out, layout_out)


def _execute_diagram_on_payload(payload: dict[str, Any], handler_name: str) -> None:
    prefix = _DIAGRAM_SAVE_PREFIX.get(handler_name, "diagrama")
    exe = execute_diagram_python(
        payload.get("codigo_diagrama") or "",
        save_prefix=prefix,
    )
    _attach_diagram_execution(payload, exe)
    logger.info(
        "%s exec diagram: ok=%s imagens=%d salvos=%s",
        handler_name,
        exe.execucao_ok,
        len(exe.diagramas_png_base64),
        exe.diagramas_arquivos,
    )


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
    payload = llm.generate(prompt, FuncaoTransferenciaResponse)

    if settings.ft_verification_enabled:
        out = verify_transfer_function(request.descricao, payload["funcao_transferencia"])
        retried = False
        if not out.ok and settings.ft_verification_retry_llm:
            corr = formatar_prompt_correcao_apenas_ft(
                request.descricao,
                out.problemas,
                payload["funcao_transferencia"],
            )
            payload = llm.generate(corr, FuncaoTransferenciaResponse)
            out = verify_transfer_function(request.descricao, payload["funcao_transferencia"])
            retried = True
        _attach_verification_standard(payload, out, executed=True, retried=retried)
    else:
        _attach_verification_standard(
            payload,
            FTVerificationOutcome(ok=True),
            executed=False,
            retried=False,
        )
    _attach_ensemble_verification(payload, request.descricao)
    return payload


@app.post(
    "/gerar-apenas-ft-ensemble",
    response_model=EnsembleFTResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Gera a FT com consenso entre múltiplos provedores de LLM (Ensemble)",
    description="""
Envia a mesma descrição, em paralelo, para todos os provedores de LLM configurados
(Google, Anthropic, Groq, OpenAI — cada um só participa se tiver chave de API no `.env`) e
apura o consenso por **equivalência simbólica** (SymPy), não por comparação de string:
FTs escritas diferente mas matematicamente iguais contam como o mesmo voto.

**Requer pelo menos 2 provedores configurados** para produzir consenso; com só 1 (ou
nenhum), `ensemble_executado` vem `false` e a mensagem explica o motivo.
    """,
    tags=["Modelagem"],
)
@with_llm_error_handling
def api_gerar_apenas_ft_ensemble(request: ProblemaRequest):
    """Gera a FT via consenso entre múltiplos provedores de LLM (Google/Anthropic/Groq/OpenAI)."""
    logger.info(
        "Requisição /gerar-apenas-ft-ensemble: %s", _truncate_for_log(request.descricao)
    )
    outcome = run_ensemble_ft(request.descricao)
    return EnsembleFTResponse(
        ensemble_executado=outcome.executado,
        respostas=[
            ProviderRespostaSchema(
                provedor=r.provedor,
                modelo=r.modelo,
                sucesso=r.sucesso,
                funcao_transferencia=r.funcao_transferencia,
                erro=r.erro,
            )
            for r in outcome.respostas
        ],
        consenso_ft=outcome.consenso_ft,
        concordancia=outcome.concordancia,
        mensagem=outcome.mensagem,
    )


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
    llm = get_llm_service()
    prompt = formatar_prompt_diagrama_por_ft(request.funcao_transferencia)
    payload = llm.generate(prompt, DiagramaBlocosResponse)

    if settings.ft_verification_enabled:
        out = verify_transfer_function("", request.funcao_transferencia)
        retried = False
        if not out.ok and settings.ft_verification_retry_llm:
            # A FT de entrada não parseia; não dá para "corrigi-la" (é do usuário), mas
            # pedimos um código de diagrama mais defensivo/explícito diante da FT malformada.
            corr = formatar_prompt_correcao_diagrama_por_ft(
                out.problemas,
                request.funcao_transferencia,
            )
            payload = llm.generate(corr, DiagramaBlocosResponse)
            retried = True
        _attach_verification_standard(payload, out, executed=True, retried=retried)
    else:
        _attach_verification_standard(
            payload,
            FTVerificationOutcome(ok=True),
            executed=False,
            retried=False,
        )
    _attach_graph_verification(payload, request.funcao_transferencia)
    _execute_diagram_on_payload(payload, "gerar-diagrama-por-ft")
    return payload


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
    llm = get_llm_service()
    prompt = formatar_prompt_ft_e_diagrama(request.descricao)
    payload = llm.generate(prompt, FuncaoTransferenciaEDiagramaResponse)

    if settings.ft_verification_enabled:
        out = _merged_verify_ft_e_diagrama(request.descricao, payload)
        retried = False
        if not out.ok and settings.ft_verification_retry_llm:
            corr = formatar_prompt_correcao_ft_e_diagrama(
                request.descricao,
                out.problemas,
                payload["funcao_transferencia"],
                payload.get("codigo_diagrama", ""),
            )
            payload = llm.generate(corr, FuncaoTransferenciaEDiagramaResponse)
            out = _merged_verify_ft_e_diagrama(request.descricao, payload)
            retried = True
        _attach_verification_ft_diagram(payload, out, executed=True, retried=retried)
    else:
        _attach_verification_ft_diagram(
            payload,
            FTVerificationOutcome(ok=True),
            executed=False,
            retried=False,
        )
    _attach_graph_verification(payload, payload["funcao_transferencia"])
    _execute_diagram_on_payload(payload, "gerar-ft-e-diagrama")
    return payload


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
    payload = llm.generate(prompt, AnaliseCompletaResponse)

    if settings.ft_verification_enabled:
        # Sem retry aqui: uma correção precisaria refazer a análise completa (lei aplicada,
        # EDO, Laplace, etc.) inteira, custando uma segunda chamada tão cara quanto a primeira.
        out = verify_transfer_function(request.descricao, payload["funcao_transferencia"])
        _attach_verification_standard(payload, out, executed=True, retried=False)
    else:
        _attach_verification_standard(
            payload,
            FTVerificationOutcome(ok=True),
            executed=False,
            retried=False,
        )

    _attach_graph_verification(payload, payload["funcao_transferencia"])
    _attach_ensemble_verification(payload, request.descricao)
    if payload.get("codigo_diagrama"):
        _execute_diagram_on_payload(payload, "gerar-analise-completa")
    return payload


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
