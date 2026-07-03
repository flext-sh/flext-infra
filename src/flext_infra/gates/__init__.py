# AUTO-GENERATED FILE — Regenerate with: make gen
"""Gates package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.gates.abstraction_boundary import (
        FlextInfraAbstractionBoundaryGate as FlextInfraAbstractionBoundaryGate,
    )
    from flext_infra.gates.bandit import FlextInfraBanditGate as FlextInfraBanditGate
    from flext_infra.gates.base_gate import FlextInfraGate as FlextInfraGate
    from flext_infra.gates.loc_cap import FlextInfraLocCapGate as FlextInfraLocCapGate
    from flext_infra.gates.markdown import (
        FlextInfraMarkdownGate as FlextInfraMarkdownGate,
    )
    from flext_infra.gates.mypy import FlextInfraMypyGate as FlextInfraMypyGate
    from flext_infra.gates.namespace import (
        FlextInfraNamespaceGate as FlextInfraNamespaceGate,
    )
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate as FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate as FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import (
        FlextInfraRuffFormatGate as FlextInfraRuffFormatGate,
    )
    from flext_infra.gates.ruff_lint import (
        FlextInfraRuffLintGate as FlextInfraRuffLintGate,
    )
    from flext_infra.gates.runtime_census import (
        FlextInfraRuntimeCensusGate as FlextInfraRuntimeCensusGate,
    )
    from flext_infra.gates.silent_failure import (
        FlextInfraSilentFailureGate as FlextInfraSilentFailureGate,
    )
    from flext_infra.gates.smells import FlextInfraSmellsGate as FlextInfraSmellsGate
    from flext_infra.gates.tier_whitelist import (
        FlextInfraTierWhitelistGate as FlextInfraTierWhitelistGate,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".abstraction_boundary": ("FlextInfraAbstractionBoundaryGate",),
        ".bandit": ("FlextInfraBanditGate",),
        ".base_gate": ("FlextInfraGate",),
        ".loc_cap": ("FlextInfraLocCapGate",),
        ".markdown": ("FlextInfraMarkdownGate",),
        ".mypy": ("FlextInfraMypyGate",),
        ".namespace": ("FlextInfraNamespaceGate",),
        ".pyrefly": ("FlextInfraPyreflyGate",),
        ".pyright": ("FlextInfraPyrightGate",),
        ".ruff_format": ("FlextInfraRuffFormatGate",),
        ".ruff_lint": ("FlextInfraRuffLintGate",),
        ".runtime_census": ("FlextInfraRuntimeCensusGate",),
        ".silent_failure": ("FlextInfraSilentFailureGate",),
        ".smells": ("FlextInfraSmellsGate",),
        ".tier_whitelist": ("FlextInfraTierWhitelistGate",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
