"""Contratos e interfaces para o orquestrador e executores de pedidos."""
from __future__ import annotations

from typing import Any, Mapping, Protocol


class ExecutorPedido(Protocol):
    """Protocolo que define a interface comum para executores de pedido (Stub e RPA)."""

    def executar(self, pedido: Mapping[str, Any]) -> dict[str, Any]:
        """Recebe o dicionário do pedido e executa a inserção no ERP."""
        ...
