# AUTO-GENERATED FILE — Regenerate with: make gen
"""Gates package."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base_gate": ("FlextInfraGate",),
        ".bandit": ("FlextInfraBanditGate",),
        ".go": ("FlextInfraGoGate",),
        ".markdown": ("FlextInfraMarkdownGate",),
        ".mypy": ("FlextInfraMypyGate",),
        ".pyrefly": ("FlextInfraPyreflyGate",),
        ".pyright": ("FlextInfraPyrightGate",),
        ".ruff_format": ("FlextInfraRuffFormatGate",),
        ".ruff_lint": ("FlextInfraRuffLintGate",),
        ".silent_failure": ("FlextInfraSilentFailureGate",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
