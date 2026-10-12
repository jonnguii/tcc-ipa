"""Instrumentação de telemetria, cronometragem precisa (perf_counter) e auditoria de eventos.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventoEtapa(BaseModel):
    """Registro individual de uma etapa executada no ciclo de vida do workflow."""

    etapa: str
    inicio_ts: float = Field(default_factory=time.time)
    duracao_s: float
    resultado: str = "OK"  # "OK", "ERRO", "ALERTA"
    detalhes: dict[str, Any] = Field(default_factory=dict)


class CronometroEtapa:
    """Context manager para cronometrar a duração de blocos de código com time.perf_counter()."""

    def __init__(self, etapa: str) -> None:
        self.etapa = etapa
        self.inicio: float = 0.0
        self.duracao_s: float = 0.0
        self.resultado: str = "OK"
        self.detalhes: dict[str, Any] = {}

    def __enter__(self) -> CronometroEtapa:
        self.inicio = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.duracao_s = round(time.perf_counter() - self.inicio, 4)
        if exc_type is not None:
            self.resultado = "ERRO"
            self.detalhes["erro"] = str(exc_val)

    def to_evento(self) -> EventoEtapa:
        return EventoEtapa(
            etapa=self.etapa,
            duracao_s=self.duracao_s,
            resultado=self.resultado,
            detalhes=self.detalhes,
        )


class RelatorioMetricasExecucao(BaseModel):
    """Consolidado de métricas de uma execução de workflow."""

    doc_id: str
    run_id: str
    tempo_total_s: float
    eventos: list[EventoEtapa] = Field(default_factory=list)
    sucesso: bool = True
    rota_decidida: str | None = None
    status_final: str = "CONCLUIDO"
