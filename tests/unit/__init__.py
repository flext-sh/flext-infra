# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Unit package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

_LAZY_IMPORTS = merge_lazy_imports(
    (
        "tests.unit._utilities",
        "tests.unit.basemk",
        "tests.unit.check",
        "tests.unit.codegen",
        "tests.unit.container",
        "tests.unit.deps",
        "tests.unit.discovery",
        "tests.unit.docs",
        "tests.unit.github",
        "tests.unit.io",
        "tests.unit.refactor",
        "tests.unit.release",
        "tests.unit.transformers",
        "tests.unit.validate",
        "tests.unit.workspace",
    ),
    {
        "_utilities": "tests.unit._utilities",
        "basemk": "tests.unit.basemk",
        "c": ("flext_core.constants", "FlextConstants"),
        "check": "tests.unit.check",
        "codegen": "tests.unit.codegen",
        "container": "tests.unit.container",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "deps": "tests.unit.deps",
        "discovery": "tests.unit.discovery",
        "docs": "tests.unit.docs",
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "github": "tests.unit.github",
        "h": ("flext_core.handlers", "FlextHandlers"),
        "io": "tests.unit.io",
        "m": ("flext_core.models", "FlextModels"),
        "p": ("flext_core.protocols", "FlextProtocols"),
        "r": ("flext_core.result", "FlextResult"),
        "refactor": "tests.unit.refactor",
        "release": "tests.unit.release",
        "s": ("flext_core.service", "FlextService"),
        "t": ("flext_core.typings", "FlextTypes"),
        "test_infra_constants_core": "tests.unit.test_infra_constants_core",
        "test_infra_constants_extra": "tests.unit.test_infra_constants_extra",
        "test_infra_git": "tests.unit.test_infra_git",
        "test_infra_init_lazy_core": "tests.unit.test_infra_init_lazy_core",
        "test_infra_init_lazy_submodules": "tests.unit.test_infra_init_lazy_submodules",
        "test_infra_main": "tests.unit.test_infra_main",
        "test_infra_maintenance_cli": "tests.unit.test_infra_maintenance_cli",
        "test_infra_maintenance_init": "tests.unit.test_infra_maintenance_init",
        "test_infra_maintenance_main": "tests.unit.test_infra_maintenance_main",
        "test_infra_maintenance_python_version": "tests.unit.test_infra_maintenance_python_version",
        "test_infra_paths": "tests.unit.test_infra_paths",
        "test_infra_patterns_core": "tests.unit.test_infra_patterns_core",
        "test_infra_patterns_extra": "tests.unit.test_infra_patterns_extra",
        "test_infra_protocols": "tests.unit.test_infra_protocols",
        "test_infra_reporting_core": "tests.unit.test_infra_reporting_core",
        "test_infra_reporting_extra": "tests.unit.test_infra_reporting_extra",
        "test_infra_selection": "tests.unit.test_infra_selection",
        "test_infra_typings": "tests.unit.test_infra_typings",
        "test_infra_utilities": "tests.unit.test_infra_utilities",
        "test_infra_version_core": "tests.unit.test_infra_version_core",
        "test_infra_version_extra": "tests.unit.test_infra_version_extra",
        "test_infra_versioning": "tests.unit.test_infra_versioning",
        "test_infra_workspace_cli": "tests.unit.test_infra_workspace_cli",
        "test_infra_workspace_detector": "tests.unit.test_infra_workspace_detector",
        "test_infra_workspace_init": "tests.unit.test_infra_workspace_init",
        "test_infra_workspace_main": "tests.unit.test_infra_workspace_main",
        "test_infra_workspace_migrator": "tests.unit.test_infra_workspace_migrator",
        "test_infra_workspace_migrator_deps": "tests.unit.test_infra_workspace_migrator_deps",
        "test_infra_workspace_migrator_dryrun": "tests.unit.test_infra_workspace_migrator_dryrun",
        "test_infra_workspace_migrator_errors": "tests.unit.test_infra_workspace_migrator_errors",
        "test_infra_workspace_migrator_internal": "tests.unit.test_infra_workspace_migrator_internal",
        "test_infra_workspace_migrator_pyproject": "tests.unit.test_infra_workspace_migrator_pyproject",
        "test_infra_workspace_orchestrator": "tests.unit.test_infra_workspace_orchestrator",
        "test_infra_workspace_sync": "tests.unit.test_infra_workspace_sync",
        "test_ssot_enforcement": "tests.unit.test_ssot_enforcement",
        "transformers": "tests.unit.transformers",
        "u": ("flext_core.utilities", "FlextUtilities"),
        "validate": "tests.unit.validate",
        "workspace": "tests.unit.workspace",
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)
_ = _LAZY_IMPORTS.pop("cleanup_submodule_namespace", None)
_ = _LAZY_IMPORTS.pop("install_lazy_exports", None)
_ = _LAZY_IMPORTS.pop("lazy_getattr", None)
_ = _LAZY_IMPORTS.pop("logger", None)
_ = _LAZY_IMPORTS.pop("merge_lazy_imports", None)
_ = _LAZY_IMPORTS.pop("output", None)
_ = _LAZY_IMPORTS.pop("output_reporting", None)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
