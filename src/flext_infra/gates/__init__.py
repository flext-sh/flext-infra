# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Quality gate implementations for the check library."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from flext_infra.gates import (
        _base_gate,
        _gate_registry,
        _models,
        bandit,
        go,
        markdown,
        mypy,
        pyrefly,
        pyright,
        ruff_format,
        ruff_lint,
    )
    from flext_infra.gates._base_gate import FlextInfraGate
    from flext_infra.gates._gate_registry import FlextInfraGateRegistry
    from flext_infra.gates._models import FlextInfraGatesModels
    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.go import FlextInfraGoGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraBanditGate": "flext_infra.gates.bandit",
    "FlextInfraGate": "flext_infra.gates._base_gate",
    "FlextInfraGateRegistry": "flext_infra.gates._gate_registry",
    "FlextInfraGatesModels": "flext_infra.gates._models",
    "FlextInfraGoGate": "flext_infra.gates.go",
    "FlextInfraMarkdownGate": "flext_infra.gates.markdown",
    "FlextInfraMypyGate": "flext_infra.gates.mypy",
    "FlextInfraPyreflyGate": "flext_infra.gates.pyrefly",
    "FlextInfraPyrightGate": "flext_infra.gates.pyright",
    "FlextInfraRuffFormatGate": "flext_infra.gates.ruff_format",
    "FlextInfraRuffLintGate": "flext_infra.gates.ruff_lint",
    "_base_gate": "flext_infra.gates._base_gate",
    "_gate_registry": "flext_infra.gates._gate_registry",
    "_models": "flext_infra.gates._models",
    "bandit": "flext_infra.gates.bandit",
    "go": "flext_infra.gates.go",
    "markdown": "flext_infra.gates.markdown",
    "mypy": "flext_infra.gates.mypy",
    "pyrefly": "flext_infra.gates.pyrefly",
    "pyright": "flext_infra.gates.pyright",
    "ruff_format": "flext_infra.gates.ruff_format",
    "ruff_lint": "flext_infra.gates.ruff_lint",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
