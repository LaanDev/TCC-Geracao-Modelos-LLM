"""
Modelos de entrada e saída da API (Pydantic v2).
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Request
# -----------------------------------------------------------------------------


class ProblemaRequest(BaseModel):
    """Requisição: descrição do sistema a ser modelado."""

    descricao: str = Field(
        ...,
        description="Descrição em linguagem natural do sistema dinâmico a ser modelado",
        min_length=10,
        examples=["Um sistema é composto por um bloco de massa 'M' e uma mola 'K'. Encontre a função de transferência G(s) = X(s)/F(s)."]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Um sistema é composto por um bloco de massa 'M' e uma mola 'K'. Encontre a função de transferência G(s) = X(s)/F(s)."
                },
                {
                    "descricao": "Um circuito elétrico é composto por um resistor 'R' e um capacitor 'C' em série. A saída é a tensão no capacitor. Encontre G(s) = Vc(s)/Vin(s)."
                }
            ]
        }
    }


class ValidacaoRequest(BaseModel):
    """Requisição: problema + FT calculada pelo aluno para validação."""

    descricao: str = Field(
        ...,
        description="Descrição do sistema dinâmico",
        min_length=10
    )
    funcao_transferencia_usuario: str = Field(
        ...,
        description="Função de transferência calculada pelo usuário para validação",
        examples=["G(s) = 1 / (RCs + 1)"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Um circuito RC em série. A saída é a tensão no capacitor.",
                    "funcao_transferencia_usuario": "G(s) = 1 / (RCs + 1)"
                }
            ]
        }
    }


class FuncaoTransferenciaRequest(BaseModel):
    """Requisição: função de transferência para gerar diagrama de blocos."""

    funcao_transferencia: str = Field(
        ...,
        description="Função de transferência no formato G(s) = numerador / denominador",
        min_length=5,
        examples=["G(s) = 1 / (RCs + 1)"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"funcao_transferencia": "G(s) = 1 / (RCs + 1)"},
                {"funcao_transferencia": "G(s) = (c2*s + k2) / (m1*m2*s^4 + a*s^3 + b*s^2 + c*s + d)"},
            ]
        }
    }


# -----------------------------------------------------------------------------
# Response
# -----------------------------------------------------------------------------


class FuncaoTransferenciaResponse(BaseModel):
    """Resposta: apenas a função de transferência G(s)."""

    funcao_transferencia: str = Field(
        ...,
        description="Função de transferência no formato G(s) = numerador / denominador"
    )


class AnaliseCompletaResponse(BaseModel):
    """Resposta: análise completa (lei, EDO, Laplace, FT, análise, código)."""

    lei_aplicada: str = Field(
        ...,
        description="Lei física fundamental aplicada (ex: Segunda Lei de Newton, Lei de Kirchhoff)"
    )
    equacao_diferencial: str = Field(
        ...,
        description="Equação diferencial ordinária (EDO) do sistema"
    )
    passos_laplace: str = Field(
        ...,
        description="Passo a passo da aplicação da Transformada de Laplace"
    )
    funcao_transferencia: str = Field(
        ...,
        description="Função de transferência final G(s)"
    )
    analise_resultado: str = Field(
        ...,
        description="Análise e interpretação do resultado obtido"
    )
    codigo_diagrama: Optional[str] = Field(
        None,
        description="Código Python para gerar o diagrama de blocos usando python-control"
    )


class ValidacaoResponse(BaseModel):
    """Resposta: veredicto, feedback e solução correta."""

    resposta_correta: bool = Field(
        ...,
        description="Indica se a resposta do usuário está correta"
    )
    feedback: str = Field(
        ...,
        description="Feedback construtivo sobre a resposta do usuário"
    )
    solucao_correta: str = Field(
        ...,
        description="Solução correta do problema"
    )


class DiagramaBlocosResponse(BaseModel):
    """Resposta: código Python para gerar diagrama de blocos."""

    codigo_diagrama: str = Field(
        ...,
        description=(
            "Código Python: diagrama de blocos completo (matplotlib: blocos, setas, somadores ⊕, "
            "realimentação) + uso de control para FT numérica e gráfico de apoio quando possível"
        ),
    )
    diagramas_png_base64: List[str] = Field(
        default_factory=list,
        description=(
            "Imagens PNG geradas pela execução automática do código (ordem: mais antigas primeiro). "
            "No frontend use data:image/png;base64,<valor>."
        ),
    )
    execucao_diagrama_ok: bool = Field(
        False,
        description="True se subprocesso terminou com sucesso e pelo menos um PNG foi capturado",
    )
    log_execucao_diagrama: Optional[str] = Field(
        None,
        description="Saída do subprocesso (stdout/stderr, truncada) para depuração",
    )


class FuncaoTransferenciaEDiagramaResponse(BaseModel):
    """Resposta: função de transferência e código do diagrama no mesmo payload."""

    funcao_transferencia: str = Field(
        ...,
        description="Função de transferência final G(s)",
    )
    codigo_diagrama: str = Field(
        ...,
        description=(
            "Código Python: diagrama de blocos alinhado à descrição (matplotlib) + control/numpy quando houver valores"
        ),
    )
    diagramas_png_base64: List[str] = Field(
        default_factory=list,
        description="PNG em Base64 da execução automática (data:image/png;base64,... no cliente)",
    )
    execucao_diagrama_ok: bool = Field(
        False,
        description="True se a execução automática produziu ao menos uma imagem",
    )
    log_execucao_diagrama: Optional[str] = Field(
        None,
        description="Log truncado do subprocesso",
    )


# -----------------------------------------------------------------------------
# Error
# -----------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Resposta padrão de erro da API."""

    sucesso: bool = False
    erro: str = Field(..., description="Mensagem de erro")
    resposta_bruta: Optional[str] = Field(
        None,
        description="Resposta bruta do LLM em caso de falha no parsing"
    )
