# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra.codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
)

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from flext_infra.codegen.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_infra.codegen.census import (
        FlextInfraCodegenCensus as FlextInfraCodegenCensus,
    )
    from flext_infra.codegen.codegen_generation import (
        FlextInfraCodegenGeneration as FlextInfraCodegenGeneration,
    )
    from flext_infra.codegen.conform import (
        FlextInfraCodegenConform as FlextInfraCodegenConform,
    )
    from flext_infra.codegen.consolidator import (
        FlextInfraCodegenConsolidator as FlextInfraCodegenConsolidator,
    )
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenQualityGate as FlextInfraCodegenQualityGate,
    )
    from flext_infra.codegen.fixer import (
        FlextInfraCodegenFixer as FlextInfraCodegenFixer,
    )
    from flext_infra.codegen.lazy_init import (
        FlextInfraCodegenLazyInit as FlextInfraCodegenLazyInit,
    )
    from flext_infra.codegen.lazy_init_planner import (
        FlextInfraCodegenLazyInitPlanner as FlextInfraCodegenLazyInitPlanner,
    )
    from flext_infra.codegen.pipeline import (
        FlextInfraCodegenPipeline as FlextInfraCodegenPipeline,
    )
    from flext_infra.codegen.project_new import (
        FlextInfraCodegenProjectNew as FlextInfraCodegenProjectNew,
    )
    from flext_infra.codegen.py_typed import (
        FlextInfraCodegenPyTyped as FlextInfraCodegenPyTyped,
    )
    from flext_infra.codegen.pyproject_keys import (
        FlextInfraCodegenPyprojectKeys as FlextInfraCodegenPyprojectKeys,
    )
    from flext_infra.codegen.scaffolder import (
        FlextInfraCodegenScaffolder as FlextInfraCodegenScaffolder,
    )
    from flext_infra.codegen.version_file import (
        FlextInfraCodegenVersionFile as FlextInfraCodegenVersionFile,
    )

    # mro-i6nq.10: Static declaration mirrors the installer-owned runtime binding.
    __all__: tuple[str, ...]

_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES,
    alias_groups=_LAZY_ALIAS_GROUPS,
    sort_keys=False,
)

# mro-i6nq.10: The installer publishes __all__ from the manifest's literal ABI.
install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    public_exports=_PUBLIC_EXPORTS,
)
