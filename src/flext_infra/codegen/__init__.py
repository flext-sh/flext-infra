# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra.codegen._codegen_generation as _flext_infra_codegen__codegen_generation

    _codegen_generation = _flext_infra_codegen__codegen_generation
    import flext_infra.codegen._codegen_generation_helpers as _flext_infra_codegen__codegen_generation_helpers
    from flext_infra.codegen._codegen_generation import FlextInfraCodegenGeneration

    _codegen_generation_helpers = _flext_infra_codegen__codegen_generation_helpers
    import flext_infra.codegen._codegen_snapshot as _flext_infra_codegen__codegen_snapshot
    from flext_infra.codegen._codegen_generation_helpers import (
        _build_lazy_entries,
        _collapse_to_children,
        _emit_type_checking_module,
        _format_import,
        _format_module_alias_import,
        _format_type_checking_module_alias_import,
        _group_imports,
        _has_flext_types,
        _is_local_module,
    )

    _codegen_snapshot = _flext_infra_codegen__codegen_snapshot
    import flext_infra.codegen._constants as _flext_infra_codegen__constants
    from flext_infra.codegen._codegen_snapshot import FlextInfraCodegenSnapshot

    _constants = _flext_infra_codegen__constants
    import flext_infra.codegen._models as _flext_infra_codegen__models
    from flext_infra.codegen._constants import FlextInfraCodegenConstants

    _models = _flext_infra_codegen__models
    import flext_infra.codegen._utilities as _flext_infra_codegen__utilities
    from flext_infra.codegen._models import FlextInfraCodegenModels

    _utilities = _flext_infra_codegen__utilities
    import flext_infra.codegen.census as _flext_infra_codegen_census
    from flext_infra.codegen._utilities import FlextInfraUtilitiesCodegen

    census = _flext_infra_codegen_census
    import flext_infra.codegen.cli as _flext_infra_codegen_cli
    from flext_infra.codegen.census import FlextInfraCodegenCensus

    cli = _flext_infra_codegen_cli
    import flext_infra.codegen.constants_quality_gate as _flext_infra_codegen_constants_quality_gate
    from flext_infra.codegen.cli import FlextInfraCliCodegen

    constants_quality_gate = _flext_infra_codegen_constants_quality_gate
    import flext_infra.codegen.fixer as _flext_infra_codegen_fixer
    from flext_infra.codegen.constants_quality_gate import (
        FlextInfraCodegenConstantsQualityGate,
    )

    fixer = _flext_infra_codegen_fixer
    import flext_infra.codegen.lazy_init as _flext_infra_codegen_lazy_init
    from flext_infra.codegen.fixer import FlextInfraCodegenFixer

    lazy_init = _flext_infra_codegen_lazy_init
    import flext_infra.codegen.py_typed as _flext_infra_codegen_py_typed
    from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit

    py_typed = _flext_infra_codegen_py_typed
    import flext_infra.codegen.scaffolder as _flext_infra_codegen_scaffolder
    from flext_infra.codegen.py_typed import FlextInfraCodegenPyTyped

    scaffolder = _flext_infra_codegen_scaffolder
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
    from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
_LAZY_IMPORTS = {
    "FlextInfraCliCodegen": "flext_infra.codegen.cli",
    "FlextInfraCodegenCensus": "flext_infra.codegen.census",
    "FlextInfraCodegenConstants": "flext_infra.codegen._constants",
    "FlextInfraCodegenConstantsQualityGate": "flext_infra.codegen.constants_quality_gate",
    "FlextInfraCodegenFixer": "flext_infra.codegen.fixer",
    "FlextInfraCodegenGeneration": "flext_infra.codegen._codegen_generation",
    "FlextInfraCodegenLazyInit": "flext_infra.codegen.lazy_init",
    "FlextInfraCodegenModels": "flext_infra.codegen._models",
    "FlextInfraCodegenPyTyped": "flext_infra.codegen.py_typed",
    "FlextInfraCodegenScaffolder": "flext_infra.codegen.scaffolder",
    "FlextInfraCodegenSnapshot": "flext_infra.codegen._codegen_snapshot",
    "FlextInfraUtilitiesCodegen": "flext_infra.codegen._utilities",
    "_build_lazy_entries": "flext_infra.codegen._codegen_generation_helpers",
    "_codegen_generation": "flext_infra.codegen._codegen_generation",
    "_codegen_generation_helpers": "flext_infra.codegen._codegen_generation_helpers",
    "_codegen_snapshot": "flext_infra.codegen._codegen_snapshot",
    "_collapse_to_children": "flext_infra.codegen._codegen_generation_helpers",
    "_constants": "flext_infra.codegen._constants",
    "_emit_type_checking_module": "flext_infra.codegen._codegen_generation_helpers",
    "_format_import": "flext_infra.codegen._codegen_generation_helpers",
    "_format_module_alias_import": "flext_infra.codegen._codegen_generation_helpers",
    "_format_type_checking_module_alias_import": "flext_infra.codegen._codegen_generation_helpers",
    "_group_imports": "flext_infra.codegen._codegen_generation_helpers",
    "_has_flext_types": "flext_infra.codegen._codegen_generation_helpers",
    "_is_local_module": "flext_infra.codegen._codegen_generation_helpers",
    "_models": "flext_infra.codegen._models",
    "_utilities": "flext_infra.codegen._utilities",
    "c": ("flext_core.constants", "FlextConstants"),
    "census": "flext_infra.codegen.census",
    "cli": "flext_infra.codegen.cli",
    "constants_quality_gate": "flext_infra.codegen.constants_quality_gate",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "fixer": "flext_infra.codegen.fixer",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "lazy_init": "flext_infra.codegen.lazy_init",
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "py_typed": "flext_infra.codegen.py_typed",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scaffolder": "flext_infra.codegen.scaffolder",
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FlextInfraCliCodegen",
    "FlextInfraCodegenCensus",
    "FlextInfraCodegenConstants",
    "FlextInfraCodegenConstantsQualityGate",
    "FlextInfraCodegenFixer",
    "FlextInfraCodegenGeneration",
    "FlextInfraCodegenLazyInit",
    "FlextInfraCodegenModels",
    "FlextInfraCodegenPyTyped",
    "FlextInfraCodegenScaffolder",
    "FlextInfraCodegenSnapshot",
    "FlextInfraUtilitiesCodegen",
    "_build_lazy_entries",
    "_codegen_generation",
    "_codegen_generation_helpers",
    "_codegen_snapshot",
    "_collapse_to_children",
    "_constants",
    "_emit_type_checking_module",
    "_format_import",
    "_format_module_alias_import",
    "_format_type_checking_module_alias_import",
    "_group_imports",
    "_has_flext_types",
    "_is_local_module",
    "_models",
    "_utilities",
    "c",
    "census",
    "cli",
    "constants_quality_gate",
    "d",
    "e",
    "fixer",
    "h",
    "lazy_init",
    "m",
    "p",
    "py_typed",
    "r",
    "s",
    "scaffolder",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
