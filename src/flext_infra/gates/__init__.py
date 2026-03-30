# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Quality gate implementations for the check library."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.gates import (
        bandit as bandit,
        go as go,
        markdown as markdown,
        mypy as mypy,
        pyrefly as pyrefly,
        pyright as pyright,
        ruff_format as ruff_format,
        ruff_lint as ruff_lint,
    )
    from flext_infra.gates.bandit import FlextInfraBanditGate as FlextInfraBanditGate
    from flext_infra.gates.go import FlextInfraGoGate as FlextInfraGoGate
    from flext_infra.gates.markdown import (
        FlextInfraMarkdownGate as FlextInfraMarkdownGate,
    )
    from flext_infra.gates.mypy import FlextInfraMypyGate as FlextInfraMypyGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate as FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate as FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import (
        FlextInfraRuffFormatGate as FlextInfraRuffFormatGate,
    )
    from flext_infra.gates.ruff_lint import (
        FlextInfraRuffLintGate as FlextInfraRuffLintGate,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "FlextInfraBanditGate": ["flext_infra.gates.bandit", "FlextInfraBanditGate"],
    "FlextInfraGoGate": ["flext_infra.gates.go", "FlextInfraGoGate"],
    "FlextInfraMarkdownGate": ["flext_infra.gates.markdown", "FlextInfraMarkdownGate"],
    "FlextInfraMypyGate": ["flext_infra.gates.mypy", "FlextInfraMypyGate"],
    "FlextInfraPyreflyGate": ["flext_infra.gates.pyrefly", "FlextInfraPyreflyGate"],
    "FlextInfraPyrightGate": ["flext_infra.gates.pyright", "FlextInfraPyrightGate"],
    "FlextInfraRuffFormatGate": [
        "flext_infra.gates.ruff_format",
        "FlextInfraRuffFormatGate",
    ],
    "FlextInfraRuffLintGate": ["flext_infra.gates.ruff_lint", "FlextInfraRuffLintGate"],
    "bandit": ["flext_infra.gates.bandit", ""],
    "go": ["flext_infra.gates.go", ""],
    "markdown": ["flext_infra.gates.markdown", ""],
    "mypy": ["flext_infra.gates.mypy", ""],
    "pyrefly": ["flext_infra.gates.pyrefly", ""],
    "pyright": ["flext_infra.gates.pyright", ""],
    "ruff_format": ["flext_infra.gates.ruff_format", ""],
    "ruff_lint": ["flext_infra.gates.ruff_lint", ""],
}

_EXPORTS: Sequence[str] = [
    "FlextInfraBanditGate",
    "FlextInfraGoGate",
    "FlextInfraMarkdownGate",
    "FlextInfraMypyGate",
    "FlextInfraPyreflyGate",
    "FlextInfraPyrightGate",
    "FlextInfraRuffFormatGate",
    "FlextInfraRuffLintGate",
    "bandit",
    "go",
    "markdown",
    "mypy",
    "pyrefly",
    "pyright",
    "ruff_format",
    "ruff_lint",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
