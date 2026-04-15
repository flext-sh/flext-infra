# AUTO-GENERATED FILE — Regenerate with: make gen
"""Unit package."""

from __future__ import annotations

from flext_core.lazy import (
    build_lazy_import_map,
    install_lazy_exports,
    merge_lazy_imports,
)

_LAZY_IMPORTS = merge_lazy_imports(
    (
        "._utilities",
        ".basemk",
        ".check",
        ".codegen",
        ".container",
        ".deps",
        ".discovery",
        ".docs",
        ".github",
        ".io",
        ".refactor",
        ".release",
        ".transformers",
        ".validate",
        ".workspace",
    ),
    build_lazy_import_map(
        {
            ".fixtures": ("fixtures",),
            ".fixtures_git": ("fixtures_git",),
            ".runner_service": ("runner_service",),
            ".scenarios": ("scenarios",),
            ".test_infra_constants_core": ("test_infra_constants_core",),
            ".test_infra_constants_extra": ("test_infra_constants_extra",),
            ".test_infra_init_lazy_core": ("test_infra_init_lazy_core",),
            ".test_infra_main": ("test_infra_main",),
            ".test_infra_maintenance_cli": ("test_infra_maintenance_cli",),
            ".test_infra_maintenance_init": ("test_infra_maintenance_init",),
            ".test_infra_maintenance_main": ("test_infra_maintenance_main",),
            ".test_infra_maintenance_python_version": (
                "test_infra_maintenance_python_version",
            ),
            ".test_infra_paths": ("test_infra_paths",),
            ".test_infra_patterns_core": ("test_infra_patterns_core",),
            ".test_infra_patterns_extra": ("test_infra_patterns_extra",),
            ".test_infra_protocols": ("test_infra_protocols",),
            ".test_infra_refactor_rope_migrations": (
                "test_infra_refactor_rope_migrations",
            ),
            ".test_infra_reporting_core": ("test_infra_reporting_core",),
            ".test_infra_reporting_extra": ("test_infra_reporting_extra",),
            ".test_infra_rope_service": ("test_infra_rope_service",),
            ".test_infra_selection": ("test_infra_selection",),
            ".test_infra_typings": ("test_infra_typings",),
            ".test_infra_utilities": ("test_infra_utilities",),
            ".test_infra_version_core": ("test_infra_version_core",),
            ".test_infra_version_extra": ("test_infra_version_extra",),
            ".test_infra_versioning": ("test_infra_versioning",),
            ".test_infra_workspace_detector": ("test_infra_workspace_detector",),
            ".test_infra_workspace_init": ("test_infra_workspace_init",),
            ".test_infra_workspace_migrator": ("test_infra_workspace_migrator",),
            ".test_infra_workspace_migrator_deps": (
                "test_infra_workspace_migrator_deps",
            ),
            ".test_infra_workspace_migrator_dryrun": (
                "test_infra_workspace_migrator_dryrun",
            ),
            ".test_infra_workspace_migrator_errors": (
                "test_infra_workspace_migrator_errors",
            ),
            ".test_infra_workspace_migrator_internal": (
                "test_infra_workspace_migrator_internal",
            ),
            ".test_infra_workspace_migrator_pyproject": (
                "test_infra_workspace_migrator_pyproject",
            ),
            ".test_infra_workspace_orchestrator": (
                "test_infra_workspace_orchestrator",
            ),
            ".test_ssot_enforcement": ("test_ssot_enforcement",),
            ".workspace_factory": ("workspace_factory",),
            ".workspace_scenarios": ("workspace_scenarios",),
            "flext_infra": (
                "c",
                "d",
                "e",
                "h",
                "m",
                "p",
                "r",
                "s",
                "t",
                "u",
                "x",
            ),
        },
    ),
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
    ),
    module_name=__name__,
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
