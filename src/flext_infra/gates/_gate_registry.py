"""Gate registry for dynamic gate lookup and management."""

from __future__ import annotations

import importlib
from pathlib import Path

from flext_infra.gates._base_gate import FlextInfraGate

_BUILTIN_GATES: tuple[tuple[str, str], ...] = (
    ("flext_infra.gates.ruff_lint", "FlextInfraRuffLintGate"),
    ("flext_infra.gates.ruff_format", "FlextInfraRuffFormatGate"),
    ("flext_infra.gates.pyrefly", "FlextInfraPyreflyGate"),
    ("flext_infra.gates.mypy", "FlextInfraMypyGate"),
    ("flext_infra.gates.pyright", "FlextInfraPyrightGate"),
    ("flext_infra.gates.bandit", "FlextInfraBanditGate"),
    ("flext_infra.gates.markdown", "FlextInfraMarkdownGate"),
    ("flext_infra.gates.go", "FlextInfraGoGate"),
)


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    def __init__(self) -> None:
        self._gates: dict[str, type[FlextInfraGate]] = {}

    def register(self, gate_cls: type[FlextInfraGate]) -> None:
        self._gates[gate_cls.gate_id] = gate_cls

    def get(self, gate_id: str) -> type[FlextInfraGate] | None:
        return self._gates.get(gate_id)

    def available_gates(self) -> frozenset[str]:
        return frozenset(self._gates)

    def create(self, gate_id: str, workspace_root: Path) -> FlextInfraGate | None:
        gate_cls = self._gates.get(gate_id)
        if gate_cls is None:
            return None
        return gate_cls(workspace_root)

    @classmethod
    def default(cls) -> FlextInfraGateRegistry:
        registry = cls()
        for module_path, class_name in _BUILTIN_GATES:
            module = importlib.import_module(module_path)
            gate_cls: type[FlextInfraGate] = getattr(module, class_name)
            registry.register(gate_cls)
        return registry


__all__ = ["FlextInfraGateRegistry"]
