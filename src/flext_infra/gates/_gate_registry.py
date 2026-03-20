"""Gate registry for dynamic gate lookup and management."""

from __future__ import annotations

from pathlib import Path

from flext_infra.gates._base_gate import FlextInfraGate
from flext_infra.gates.bandit import FlextInfraBanditGate
from flext_infra.gates.go import FlextInfraGoGate
from flext_infra.gates.markdown import FlextInfraMarkdownGate
from flext_infra.gates.mypy import FlextInfraMypyGate
from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
from flext_infra.gates.pyright import FlextInfraPyrightGate
from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate

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
