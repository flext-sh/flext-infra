# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export registry."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map, merge_lazy_imports

_LOCAL_LAZY_IMPORTS = build_lazy_import_map(
    {
        "._constants": ("_constants",),
        "._enforcement": ("_enforcement",),
        "._enforcement.collection_base": (
            "FlextInfraEnforcementCollectionBase",
            "FlextInfraEnforcementEvaluation",
        ),
        "._enforcement.collection_sources": ("FlextInfraEnforcementSourceCollectors",),
        "._enforcement.collection_tests": ("FlextInfraEnforcementTestsCollector",),
        "._enforcement.engine": ("FlextInfraEnforcementEngine",),
        "._enforcement.metadata": ("FlextInfraEnforcementMetadata",),
        "._enforcement.selection": ("FlextInfraEnforcementSelection",),
        "._fixtures.enforcement": ("FlextInfraEnforcementPytestPlugin",),
        "._models": ("_models",),
        "._protocols": ("_protocols",),
        "._typings": ("_typings",),
        "._utilities": ("_utilities",),
        ".api": (
            "FlextInfra",
            "infra",
        ),
        ".base": (
            "FlextInfraServiceBase",
            "s",
        ),
        ".base_selection": ("FlextInfraProjectSelectionServiceBase",),
        ".basemk": ("basemk",),
        ".check": ("check",),
        ".cli": (
            "FlextInfraCli",
            "main",
        ),
        ".codegen": ("codegen",),
        ".constants": (
            "FlextInfraConstants",
            "c",
        ),
        ".deps": ("deps",),
        ".detectors": ("detectors",),
        ".docs": ("docs",),
        ".fixers": ("fixers",),
        ".gates": ("gates",),
        ".maintenance": ("maintenance",),
        ".models": (
            "FlextInfraModels",
            "m",
        ),
        ".protocols": (
            "FlextInfraProtocols",
            "p",
        ),
        ".refactor": ("refactor",),
        ".release": ("release",),
        ".settings": ("FlextInfraSettings",),
        ".transformers": ("transformers",),
        ".typings": (
            "FlextInfraTypes",
            "t",
        ),
        ".utilities": (
            "FlextInfraUtilities",
            "u",
        ),
        ".validate": ("validate",),
        ".workspace": ("workspace",),
        "flext_core._root_typing_parts.facades": (
            "d",
            "e",
            "h",
            "r",
            "x",
        ),
    },
)

FLEXT_INFRA_LAZY_IMPORTS = merge_lazy_imports(
    ("._enforcement",),
    _LOCAL_LAZY_IMPORTS,
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name="flext_infra",
)

__all__: list[str] = ["FLEXT_INFRA_LAZY_IMPORTS"]
