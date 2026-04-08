# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Gates package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.gates._base_gate as _flext_infra_gates__base_gate

    _base_gate = _flext_infra_gates__base_gate
    import flext_infra.gates.bandit as _flext_infra_gates_bandit
    from flext_infra.gates._base_gate import FlextInfraGate

    bandit = _flext_infra_gates_bandit
    import flext_infra.gates.go as _flext_infra_gates_go
    from flext_infra.gates.bandit import FlextInfraBanditGate

    go = _flext_infra_gates_go
    import flext_infra.gates.markdown as _flext_infra_gates_markdown
    from flext_infra.gates.go import FlextInfraGoGate

    markdown = _flext_infra_gates_markdown
    import flext_infra.gates.mypy as _flext_infra_gates_mypy
    from flext_infra.gates.markdown import FlextInfraMarkdownGate

    mypy = _flext_infra_gates_mypy
    import flext_infra.gates.pyrefly as _flext_infra_gates_pyrefly
    from flext_infra.gates.mypy import FlextInfraMypyGate

    pyrefly = _flext_infra_gates_pyrefly
    import flext_infra.gates.pyright as _flext_infra_gates_pyright
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate

    pyright = _flext_infra_gates_pyright
    import flext_infra.gates.ruff_format as _flext_infra_gates_ruff_format
    from flext_infra.gates.pyright import FlextInfraPyrightGate

    ruff_format = _flext_infra_gates_ruff_format
    import flext_infra.gates.ruff_lint as _flext_infra_gates_ruff_lint
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate

    ruff_lint = _flext_infra_gates_ruff_lint
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
_LAZY_IMPORTS = {
    "FlextInfraBanditGate": ("flext_infra.gates.bandit", "FlextInfraBanditGate"),
    "FlextInfraGate": ("flext_infra.gates._base_gate", "FlextInfraGate"),
    "FlextInfraGoGate": ("flext_infra.gates.go", "FlextInfraGoGate"),
    "FlextInfraMarkdownGate": ("flext_infra.gates.markdown", "FlextInfraMarkdownGate"),
    "FlextInfraMypyGate": ("flext_infra.gates.mypy", "FlextInfraMypyGate"),
    "FlextInfraPyreflyGate": ("flext_infra.gates.pyrefly", "FlextInfraPyreflyGate"),
    "FlextInfraPyrightGate": ("flext_infra.gates.pyright", "FlextInfraPyrightGate"),
    "FlextInfraRuffFormatGate": (
        "flext_infra.gates.ruff_format",
        "FlextInfraRuffFormatGate",
    ),
    "FlextInfraRuffLintGate": ("flext_infra.gates.ruff_lint", "FlextInfraRuffLintGate"),
    "_base_gate": "flext_infra.gates._base_gate",
    "bandit": "flext_infra.gates.bandit",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "go": "flext_infra.gates.go",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "markdown": "flext_infra.gates.markdown",
    "mypy": "flext_infra.gates.mypy",
    "pyrefly": "flext_infra.gates.pyrefly",
    "pyright": "flext_infra.gates.pyright",
    "r": ("flext_core.result", "FlextResult"),
    "ruff_format": "flext_infra.gates.ruff_format",
    "ruff_lint": "flext_infra.gates.ruff_lint",
    "s": ("flext_core.service", "FlextService"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraBanditGate",
    "FlextInfraGate",
    "FlextInfraGoGate",
    "FlextInfraMarkdownGate",
    "FlextInfraMypyGate",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "_base_gate",
    "bandit",
    "d",
    "e",
    "go",
    "h",
    "markdown",
    "mypy",
    "pyrefly",
    "pyright",
    "r",
    "ruff_format",
    "ruff_lint",
    "s",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
