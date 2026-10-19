"""Executores de pedido: Stub (Robô Simulado para testes rápidos) e RPA (Playwright Real).
"""
from __future__ import annotations

import time
from typing import Any, Mapping

from src.ipa.contracts import ExecutorPedido


class StubExecutor:
    """Robô simulado em memória para validação da máquina de estados e testes de alta velocidade."""

    def __init__(self, latencia_s: float = 0.05) -> None:
        self.latencia_s = latencia_s
        self.pedidos_armazenados: dict[str, int] = {}
        self._contador_sequencial = 1000

    def reset(self) -> None:
        """Limpa a memória do simulador."""
        self.pedidos_armazenados.clear()
        self._contador_sequencial = 1000

    def executar(self, pedido: Mapping[str, Any]) -> dict[str, Any]:
        """Simula a execução do robô com checagem de duplicidade idempotente."""
        inicio = time.perf_counter()
        if self.latencia_s > 0:
            time.sleep(self.latencia_s)

        ref_id = str(pedido.get("ref_id") or "SEM_REF").strip()

        # Checagem de idempotência simulada
        if ref_id in self.pedidos_armazenados:
            numero = self.pedidos_armazenados[ref_id]
            duracao = time.perf_counter() - inicio
            return {
                "ref_id": ref_id,
                "status": "duplicado",
                "numero_pedido": numero,
                "duracao_s": round(duracao, 3),
                "tentativas": 1,
                "screenshot": f"stub/evidencias/{ref_id}_duplicado.png",
                "erro": None,
                "modo": "STUB",
            }

        # Criação de novo pedido simulado
        self._contador_sequencial += 1
        numero = self._contador_sequencial
        self.pedidos_armazenados[ref_id] = numero
        duracao = time.perf_counter() - inicio

        return {
            "ref_id": ref_id,
            "status": "sucesso",
            "numero_pedido": numero,
            "duracao_s": round(duracao, 3),
            "tentativas": 1,
            "screenshot": f"stub/evidencias/{ref_id}.png",
            "erro": None,
            "modo": "STUB",
        }


class RpaExecutor:
    """Executa a inserção real através do robô Playwright no ERP Simulado."""

    def executar(self, pedido: Mapping[str, Any]) -> dict[str, Any]:
        from rpa.bot import executar as bot_executar
        resultado = bot_executar(pedido)
        resultado["modo"] = "RPA"
        return resultado


def obter_executor(tipo: str = "stub", **kwargs: Any) -> ExecutorPedido:
    """Fábrica de executores."""
    tipo_norm = str(tipo or "stub").strip().lower()
    if tipo_norm == "rpa":
        return RpaExecutor()
    return StubExecutor(**kwargs)
