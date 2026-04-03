# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Gates package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
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

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
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
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "go": "flext_infra.gates.go",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "markdown": "flext_infra.gates.markdown",
    "mypy": "flext_infra.gates.mypy",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pyrefly": "flext_infra.gates.pyrefly",
    "pyright": "flext_infra.gates.pyright",
    "r": ("flext_core.result", "FlextResult"),
    "ruff_format": "flext_infra.gates.ruff_format",
    "ruff_lint": "flext_infra.gates.ruff_lint",
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
