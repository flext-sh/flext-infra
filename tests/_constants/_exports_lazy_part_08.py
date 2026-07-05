# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_08 = build_lazy_import_map(
    {
        "._constants": ("_constants",),
        ".conftest": ("conftest",),
        ".constants": ("c",),
        ".integration": ("integration",),
        ".models": ("m",),
        ".protocols": ("p",),
        ".refactor": ("refactor",),
        ".unit._utilities.test_discovery_consolidated": (
            "TestsFlextInfraUtilitiesdiscoveryconsolidated",
        ),
        ".unit._utilities.test_formatting": ("TestsFlextInfraUtilitiesformatting",),
        ".unit._utilities.test_safety": ("TestsFlextInfraUtilitiessafety",),
        ".unit._utilities.test_scanning": ("TestsFlextInfraUtilitiesscanning",),
        ".unit.fixtures": (
            "deptry_report_payload",
            "models_resource",
            "modernizer_workspace",
            "modernizer_workspace_with_projects",
            "real_docs_project",
            "real_makefile_project",
            "real_python_package",
            "real_toml_project",
            "real_workspace",
            "rope_workspace",
        ),
        ".unit.fixtures_git": ("real_git_repo",),
        ".unit.workspace.test_main": ("TestsFlextInfraWorkspaceMain",),
        ".unit.workspace.test_makefile_dry_run": (
            "TestsFlextInfraWorkspaceMakefileDryRun",
        ),
        ".unit.workspace.test_makefile_generator": (
            "TestsFlextInfraWorkspaceMakefileGenerator",
        ),
        ".unit.workspace.test_sync": ("TestsFlextInfraWorkspaceSync",),
        ".unit.workspace.test_sync_environment": (
            "TestsFlextInfraWorkspaceSyncEnvironment",
        ),
        ".unit.workspace_factory": ("TestsFlextInfraWorkspaceFactory",),
        "flext_tests": (
            "d",
            "e",
            "h",
            "r",
        ),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_08"]
