"""Estados formais da máquina de estados do workflow IPA.
Espelha o diagrama BPMN da arquitetura TO-BE.
"""
from __future__ import annotations

from enum import Enum


class EstadoWorkflow(str, Enum):
    """Estados do ciclo de vida de processamento de um documento."""

    INICIADO = "INICIADO"
    EXTRACAO_IA = "EXTRACAO_IA"
    REGRAS_TRIAGEM = "REGRAS_TRIAGEM"
    EXECUTOR_RPA = "EXECUTOR_RPA"
    REVISAO_HUMANA = "REVISAO_HUMANA"
    REJEITADO = "REJEITADO"
    CONCLUIDO = "CONCLUIDO"
    FALHA = "FALHA"


# Mapa de transições permitidas para garantir rigor operacional
TRANSIÇÕES_VALIDAS: dict[EstadoWorkflow, list[EstadoWorkflow]] = {
    EstadoWorkflow.INICIADO: [EstadoWorkflow.EXTRACAO_IA, EstadoWorkflow.FALHA],
    EstadoWorkflow.EXTRACAO_IA: [EstadoWorkflow.REGRAS_TRIAGEM, EstadoWorkflow.FALHA],
    EstadoWorkflow.REGRAS_TRIAGEM: [
        EstadoWorkflow.EXECUTOR_RPA,
        EstadoWorkflow.REVISAO_HUMANA,
        EstadoWorkflow.REJEITADO,
        EstadoWorkflow.FALHA,
    ],
    EstadoWorkflow.EXECUTOR_RPA: [EstadoWorkflow.CONCLUIDO, EstadoWorkflow.FALHA],
    EstadoWorkflow.REVISAO_HUMANA: [
        EstadoWorkflow.EXECUTOR_RPA,
        EstadoWorkflow.REJEITADO,
        EstadoWorkflow.CONCLUIDO,
        EstadoWorkflow.FALHA,
    ],
    EstadoWorkflow.REJEITADO: [],
    EstadoWorkflow.CONCLUIDO: [],
    EstadoWorkflow.FALHA: [],
}


def validar_transicao(origem: EstadoWorkflow, destino: EstadoWorkflow) -> bool:
    """Verifica se a transição entre estados é permitida pelo modelo formal."""
    return destino in TRANSIÇÕES_VALIDAS.get(origem, [])
