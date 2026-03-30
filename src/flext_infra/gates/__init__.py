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
        bandit,
        go,
        markdown,
        mypy,
        pyrefly,
        pyright,
        ruff_format,
        ruff_lint,
    )
    from flext_infra.gates.bandit import *
    from flext_infra.gates.go import *
    from flext_infra.gates.markdown import *
    from flext_infra.gates.mypy import *
    from flext_infra.gates.pyrefly import *
    from flext_infra.gates.pyright import *
    from flext_infra.gates.ruff_format import *
    from flext_infra.gates.ruff_lint import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "FlextInfraBanditGate": "flext_infra.gates.bandit",
    "FlextInfraGoGate": "flext_infra.gates.go",
    "FlextInfraMarkdownGate": "flext_infra.gates.markdown",
    "FlextInfraMypyGate": "flext_infra.gates.mypy",
    "FlextInfraPyreflyGate": "flext_infra.gates.pyrefly",
    "FlextInfraPyrightGate": "flext_infra.gates.pyright",
    "FlextInfraRuffFormatGate": "flext_infra.gates.ruff_format",
    "FlextInfraRuffLintGate": "flext_infra.gates.ruff_lint",
    "bandit": "flext_infra.gates.bandit",
    "go": "flext_infra.gates.go",
    "markdown": "flext_infra.gates.markdown",
    "mypy": "flext_infra.gates.mypy",
    "pyrefly": "flext_infra.gates.pyrefly",
    "pyright": "flext_infra.gates.pyright",
    "ruff_format": "flext_infra.gates.ruff_format",
    "ruff_lint": "flext_infra.gates.ruff_lint",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
