"""
Modelos de entrada e saída da API (Pydantic v2).
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from graph_validation import DiagramGraph


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
        description="Função de transferência no formato G(s) = numerador / denominador",
    )
    verificacao_executada: bool = Field(
        False,
        description="True se o verificador simbólico (SymPy + gabaritos canônicos) foi executado",
    )
    verificacao_ft_ok: bool = Field(
        True,
        description="False se falhou parsing ou inconsistência contra gabarito canônico quando aplicável",
    )
    mensagem_verificacao: Optional[str] = Field(
        None,
        description="Detalhes quando a verificação falha ou modo debug",
    )
    nova_tentativa_pos_verificacao: bool = Field(
        False,
        description="True se houve segunda chamada ao LLM com prompt de correção curta",
    )
    verificacao_ensemble_executada: bool = Field(
        False,
        description="True se pelo menos 2 provedores de LLM (Google/Anthropic/Groq/OpenAI) estavam configurados e o ensemble rodou",
    )
    verificacao_ensemble_ok: bool = Field(
        True,
        description="False se a FT retornada não é equivalente ao consenso do ensemble entre provedores",
    )
    mensagem_verificacao_ensemble: Optional[str] = Field(
        None,
        description="Detalhes quando a verificação por ensemble falha ou não pôde ser executada",
    )
    ensemble_concordancia: Optional[str] = Field(
        None,
        description='Fração "n/total" de provedores que concordaram entre si no ensemble',
    )
    ensemble_consenso_ft: Optional[str] = Field(
        None,
        description="FT de consenso do ensemble, para comparação/depuração",
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
    verificacao_executada: bool = Field(
        False,
        description="True se o verificador simbólico (SymPy + gabaritos canônicos) foi executado",
    )
    verificacao_ft_ok: bool = Field(
        True,
        description="False se falhou parsing ou inconsistência contra gabarito canônico quando aplicável",
    )
    mensagem_verificacao: Optional[str] = Field(
        None,
        description="Detalhes quando a verificação falha ou modo debug",
    )
    nova_tentativa_pos_verificacao: bool = Field(
        False,
        description=(
            "Sempre False neste endpoint: a análise completa não tem prompt de correção "
            "dedicado (custaria uma segunda chamada completa ao LLM), então falhas ficam "
            "só sinalizadas em verificacao_ft_ok/mensagem_verificacao"
        ),
    )
    verificacao_ensemble_executada: bool = Field(
        False,
        description="True se pelo menos 2 provedores de LLM (Google/Anthropic/Groq/OpenAI) estavam configurados e o ensemble rodou",
    )
    verificacao_ensemble_ok: bool = Field(
        True,
        description="False se a FT retornada não é equivalente ao consenso do ensemble entre provedores",
    )
    mensagem_verificacao_ensemble: Optional[str] = Field(
        None,
        description="Detalhes quando a verificação por ensemble falha ou não pôde ser executada",
    )
    ensemble_concordancia: Optional[str] = Field(
        None,
        description='Fração "n/total" de provedores que concordaram entre si no ensemble',
    )
    ensemble_consenso_ft: Optional[str] = Field(
        None,
        description="FT de consenso do ensemble, para comparação/depuração",
    )
    grafo_diagrama: Optional[DiagramGraph] = Field(
        None,
        description=(
            "Estrutura do diagrama como grafo (blocos com ganho, somadores, arestas com sinal), "
            "usada para validar por redução algébrica (Fórmula de Ganho de Mason) que o diagrama "
            "realmente reduz à FT. Opcional: quando ausente ou malformada, a validação por grafo "
            "simplesmente não roda (verificacao_grafo_executada=False)."
        ),
    )
    verificacao_grafo_executada: bool = Field(
        False,
        description="True se um grafo válido foi recebido e a redução de Mason foi executada",
    )
    verificacao_grafo_ok: bool = Field(
        True,
        description="False se o grafo não reduz à FT, ou se o grafo é malformado",
    )
    mensagem_verificacao_grafo: Optional[str] = Field(
        None,
        description="Detalhes quando a validação por grafo falha ou não pôde ser executada",
    )
    ft_derivada_grafo: Optional[str] = Field(
        None,
        description="FT obtida reduzindo o grafo (Mason), para depuração/transparência",
    )
    diagramas_png_base64: List[str] = Field(
        default_factory=list,
        description="PNG em Base64 quando codigo_diagrama é executado automaticamente",
    )
    execucao_diagrama_ok: bool = Field(
        False,
        description="True se a execução automática do codigo_diagrama produziu PNG",
    )
    log_execucao_diagrama: Optional[str] = Field(
        None,
        description="Log da execução do diagrama (quando falha ou DEBUG)",
    )
    diagramas_arquivos: List[str] = Field(
        default_factory=list,
        description="Caminhos relativos dos PNG gravados em diagrams/",
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
    verificacao_executada: bool = Field(
        False,
        description="Verificação do texto da FT de entrada (parse racional em s)",
    )
    verificacao_ft_ok: bool = Field(
        True,
        description="False se a FT textual da requisição não pôde ser interpretada simbolicamente",
    )
    mensagem_verificacao: Optional[str] = Field(None, description="Detalhes do verificador")
    nova_tentativa_pos_verificacao: bool = Field(
        False,
        description="Reservado; usualmente False neste endpoint",
    )
    grafo_diagrama: Optional[DiagramGraph] = Field(
        None,
        description=(
            "Estrutura do diagrama como grafo (blocos com ganho, somadores, arestas com sinal), "
            "usada para validar por redução algébrica (Fórmula de Ganho de Mason) que o diagrama "
            "realmente reduz à FT informada. Opcional: quando ausente ou malformada, a validação "
            "por grafo simplesmente não roda (verificacao_grafo_executada=False)."
        ),
    )
    verificacao_grafo_executada: bool = Field(
        False,
        description="True se um grafo válido foi recebido e a redução de Mason foi executada",
    )
    verificacao_grafo_ok: bool = Field(
        True,
        description="False se o grafo não reduz à FT informada, ou se o grafo é malformado",
    )
    mensagem_verificacao_grafo: Optional[str] = Field(
        None,
        description="Detalhes quando a validação por grafo falha ou não pôde ser executada",
    )
    ft_derivada_grafo: Optional[str] = Field(
        None,
        description="FT obtida reduzindo o grafo (Mason), para depuração/transparência",
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
    diagramas_arquivos: List[str] = Field(
        default_factory=list,
        description="Caminhos relativos dos PNG gravados em disco (ex.: diagrams/diagrama_rota3_ex1.png)",
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
    verificacao_executada: bool = Field(
        False,
        description="True se rodou SymPy/canônicos e heurística de layout físico quando aplicável",
    )
    verificacao_ft_ok: bool = Field(
        True,
        description="False se FT ou código falhou parte verificável do pipeline",
    )
    verificacao_layout_fisico_ok: Optional[bool] = Field(
        None,
        description="None se N/A; False se esperava esquema mecânico 1×2 e não detectado no código",
    )
    mensagem_verificacao: Optional[str] = Field(None)
    nova_tentativa_pos_verificacao: bool = Field(False)
    grafo_diagrama: Optional[DiagramGraph] = Field(
        None,
        description=(
            "Estrutura do diagrama como grafo (blocos com ganho, somadores, arestas com sinal), "
            "usada para validar por redução algébrica (Fórmula de Ganho de Mason) que o diagrama "
            "realmente reduz à FT declarada. Opcional: quando ausente ou malformada, a validação "
            "por grafo simplesmente não roda (verificacao_grafo_executada=False)."
        ),
    )
    verificacao_grafo_executada: bool = Field(
        False,
        description="True se um grafo válido foi recebido e a redução de Mason foi executada",
    )
    verificacao_grafo_ok: bool = Field(
        True,
        description="False se o grafo não reduz à FT declarada, ou se o grafo é malformado",
    )
    mensagem_verificacao_grafo: Optional[str] = Field(
        None,
        description="Detalhes quando a validação por grafo falha ou não pôde ser executada",
    )
    ft_derivada_grafo: Optional[str] = Field(
        None,
        description="FT obtida reduzindo o grafo (Mason), para depuração/transparência",
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
    diagramas_arquivos: List[str] = Field(
        default_factory=list,
        description="Caminhos relativos dos PNG gravados em diagrams/",
    )


# -----------------------------------------------------------------------------
# Ensemble
# -----------------------------------------------------------------------------


class ProviderRespostaSchema(BaseModel):
    """Resultado de um único provedor de LLM dentro do ensemble."""

    provedor: str = Field(..., description="Nome do provedor: google, openai ou anthropic")
    modelo: str = Field(..., description="Modelo efetivamente usado nesse provedor")
    sucesso: bool = Field(..., description="False se a chamada falhou (rede, quota, etc.)")
    funcao_transferencia: Optional[str] = Field(
        None, description="FT retornada por esse provedor, quando bem-sucedido"
    )
    erro: Optional[str] = Field(None, description="Mensagem de erro quando sucesso=False")


class EnsembleFTResponse(BaseModel):
    """Resposta: consenso entre múltiplos provedores de LLM para a função de transferência."""

    ensemble_executado: bool = Field(
        False,
        description="False quando menos de 2 provedores têm chave de API configurada",
    )
    respostas: List[ProviderRespostaSchema] = Field(
        default_factory=list,
        description="Resposta individual de cada provedor consultado",
    )
    consenso_ft: Optional[str] = Field(
        None,
        description="FT do maior grupo de respostas simbolicamente equivalentes (SymPy, não string)",
    )
    concordancia: Optional[str] = Field(
        None,
        description='Fração "n/total" de provedores bem-sucedidos que concordaram com o consenso',
    )
    mensagem: Optional[str] = Field(
        None,
        description="Detalhes quando o ensemble não roda ou nenhum provedor produz FT parseável",
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
