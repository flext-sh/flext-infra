# AUTO-GENERATED FILE — Regenerate with: make gen
"""Gates package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "FlextInfraBanditGate": ".bandit",
    "FlextInfraGate": "._base_gate",
    "FlextInfraGoGate": ".go",
    "FlextInfraMarkdownGate": ".markdown",
    "FlextInfraMypyGate": ".mypy",
    "FlextInfraPyreflyGate": ".pyrefly",
    "FlextInfraPyrightGate": ".pyright",
    "FlextInfraRuffFormatGate": ".ruff_format",
    "FlextInfraRuffLintGate": ".ruff_lint",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
