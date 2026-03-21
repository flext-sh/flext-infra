"""Gate registry for dynamic gate lookup and management."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    FlextInfraBanditGate,
    FlextInfraGate,
    FlextInfraGoGate,
    FlextInfraMarkdownGate,
    FlextInfraMypyGate,
    FlextInfraPyreflyGate,
    FlextInfraPyrightGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
)

_GATES: tuple[type[FlextInfraGate], ...] = (
    FlextInfraRuffLintGate,
    FlextInfraRuffFormatGate,
    FlextInfraPyreflyGate,
    FlextInfraMypyGate,
    FlextInfraPyrightGate,
    FlextInfraBanditGate,
    FlextInfraMarkdownGate,
    FlextInfraGoGate,
)


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    def __init__(self) -> None:
        self._gates: dict[str, type[FlextInfraGate]] = {g.gate_id: g for g in _GATES}

    def get(self, gate_id: str) -> type[FlextInfraGate] | None:
        return self._gates.get(gate_id)

    def available_gates(self) -> frozenset[str]:
        return frozenset(self._gates)

    def create(self, gate_id: str, workspace_root: Path) -> FlextInfraGate | None:
        gate_cls = self._gates.get(gate_id)
        return gate_cls(workspace_root) if gate_cls else None

    @classmethod
    def default(cls) -> FlextInfraGateRegistry:
        return cls()


__all__ = ["FlextInfraGateRegistry"]
