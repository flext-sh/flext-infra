# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_07 = build_lazy_import_map(
    {
        ".codegen": ("codegen",),
        ".container": ("container",),
        ".deps": ("deps",),
        ".discovery": ("discovery",),
        ".docs": ("docs",),
        ".fixtures": (
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
            "services_resource",
            "tool_config_document",
        ),
        ".fixtures_git": ("real_git_repo",),
        ".github": ("github",),
        ".io": ("io",),
        ".refactor": ("refactor",),
        ".release": ("release",),
        ".test_infra_workspace_migrator_errors": (
            "test_infra_workspace_migrator_errors",
        ),
        ".test_infra_workspace_migrator_pyproject": (
            "test_infra_workspace_migrator_pyproject",
        ),
        ".test_mro_service_base_alias": ("test_mro_service_base_alias",),
        ".test_version_diag": ("test_version_diag",),
        ".test_version_diag2": ("test_version_diag2",),
        ".transformers": ("transformers",),
        ".validate": ("validate",),
        ".workspace": ("workspace",),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_07"]
