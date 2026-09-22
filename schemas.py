"""
Modelos de entrada e saída da API (Pydantic v2).
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from graph_validation import DiagramGraph


class ProblemaRequest(BaseModel):
    """Requisição: descrição do sistema a ser modelado."""

    descricao: str = Field(
        ...,
        description="Descrição em linguagem natural do sistema dinâmico a ser modelado",
        min_length=10,
        examples=[
            "Um sistema é composto por um bloco de massa 'M' e uma mola 'K'. Encontre a função de transferência G(s) = X(s)/F(s)."
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "descricao": "Um sistema é composto por um bloco de massa 'M' e uma mola 'K'. Encontre a função de transferência G(s) = X(s)/F(s)."
                },
                {
                    "descricao": "Um circuito elétrico é composto por um resistor 'R' e um capacitor 'C' em série. A saída é a tensão no capacitor. Encontre G(s) = Vc(s)/Vin(s)."
                },
            ]
        }
    }


class ProviderRespostaSchema(BaseModel):
    """Resultado de um único provedor de LLM dentro do ensemble."""

    provedor: str = Field(..., description="Nome do provedor: google, anthropic, groq ou openai")
    modelo: str = Field(..., description="Modelo efetivamente usado nesse provedor")
    sucesso: bool = Field(..., description="False se a chamada falhou (rede, quota, etc.)")
    funcao_transferencia: Optional[str] = Field(
        None, description="FT retornada por esse provedor, quando bem-sucedido"
    )
    erro: Optional[str] = Field(None, description="Mensagem de erro quando sucesso=False")


class AnaliseCompletaResponse(BaseModel):
    """Resposta da análise completa: texto didático do vencedor do ensemble + checagens."""

    lei_aplicada: str = Field(
        ...,
        description="Lei física fundamental aplicada (ex: Segunda Lei de Newton, Lei de Kirchhoff)",
    )
    equacao_diferencial: str = Field(
        ...,
        description="Equação diferencial ordinária (EDO) do sistema",
    )
    passos_laplace: str = Field(
        ...,
        description="Passo a passo da aplicação da Transformada de Laplace",
    )
    funcao_transferencia: str = Field(
        ...,
        description="Função de transferência final G(s) — a mais votada no ensemble",
    )
    analise_resultado: str = Field(
        ...,
        description="Análise e interpretação do resultado obtido",
    )
    codigo_diagrama: Optional[str] = Field(
        None,
        description=(
            "Opcional/legado: código Python de plotagem. O fluxo atual não solicita "
            "isso ao LLM — o diagrama vem do grafo_diagrama + render determinístico."
        ),
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
    ensemble_executado: bool = Field(
        False,
        description="True se pelo menos 2 provedores geraram análise e o voto escolheu o resultado",
    )
    ensemble_concordancia: Optional[str] = Field(
        None,
        description='Fração "n/total" de provedores que concordaram com a FT vencedora',
    )
    ensemble_consenso_ft: Optional[str] = Field(
        None,
        description="FT mais votada (a mesma exibida em funcao_transferencia quando o ensemble rodou)",
    )
    ensemble_provedor_vencedor: Optional[str] = Field(
        None,
        description="Provedor cuja análise completa foi escolhida pelo voto",
    )
    ensemble_mensagem: Optional[str] = Field(
        None,
        description="Detalhes quando o ensemble não roda ou não há consenso parseável",
    )
    ensemble_respostas: List[ProviderRespostaSchema] = Field(
        default_factory=list,
        description="FT (ou erro) de cada provedor consultado",
    )
    grafo_diagrama: Optional[DiagramGraph] = Field(
        None,
        description=(
            "Estrutura do diagrama como grafo, usada para validar por redução algébrica "
            "(Fórmula de Ganho de Mason) que o diagrama reduz à FT."
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
        description="Detalhes quando a validação por grafo falha",
    )
    ft_derivada_grafo: Optional[str] = Field(
        None,
        description="FT obtida reduzindo o grafo (Mason)",
    )
    diagramas_png_base64: List[str] = Field(
        default_factory=list,
        description=(
            "PNG em Base64: render determinístico do grafo e, se habilitado, "
            "figuras da execução de codigo_diagrama"
        ),
    )
    execucao_diagrama_ok: bool = Field(
        False,
        description="True se a execução automática de codigo_diagrama (legado) produziu PNG",
    )
    log_execucao_diagrama: Optional[str] = Field(
        None,
        description="Log da execução do diagrama (quando falha ou DEBUG)",
    )
    diagramas_arquivos: List[str] = Field(
        default_factory=list,
        description="Caminhos relativos dos PNG gravados em diagrams/",
    )


class ErrorResponse(BaseModel):
    """Resposta padrão de erro da API."""

    sucesso: bool = False
    erro: str = Field(..., description="Mensagem de erro")
    resposta_bruta: Optional[str] = Field(
        None,
        description="Resposta bruta do LLM em caso de falha no parsing",
    )
