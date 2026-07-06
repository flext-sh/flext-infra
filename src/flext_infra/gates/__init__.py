# AUTO-GENERATED FILE — Regenerate with: make gen
"""Gates package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.gates.abstraction_boundary import FlextInfraAbstractionBoundaryGate
    from flext_infra.gates.bandit import FlextInfraBanditGate
    from flext_infra.gates.base_gate import FlextInfraGate
    from flext_infra.gates.canonical_alias import FlextInfraCanonicalAliasGate
    from flext_infra.gates.loc_cap import FlextInfraLocCapGate
    from flext_infra.gates.markdown import FlextInfraMarkdownGate
    from flext_infra.gates.mypy import FlextInfraMypyGate
    from flext_infra.gates.namespace import FlextInfraNamespaceGate
    from flext_infra.gates.pyrefly import FlextInfraPyreflyGate
    from flext_infra.gates.pyright import FlextInfraPyrightGate
    from flext_infra.gates.ruff_format import FlextInfraRuffFormatGate
    from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate
    from flext_infra.gates.runtime_census import FlextInfraRuntimeCensusGate
    from flext_infra.gates.silent_failure import FlextInfraSilentFailureGate
    from flext_infra.gates.smells import FlextInfraSmellsGate
    from flext_infra.gates.tier_whitelist import FlextInfraTierWhitelistGate
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".abstraction_boundary": ("FlextInfraAbstractionBoundaryGate",),
        ".bandit": ("FlextInfraBanditGate",),
        ".base_gate": ("FlextInfraGate",),
        ".canonical_alias": ("FlextInfraCanonicalAliasGate",),
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
