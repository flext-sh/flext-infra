# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Gates package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
