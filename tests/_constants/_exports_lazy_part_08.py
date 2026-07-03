# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export map part."""

from __future__ import annotations

from flext_core.lazy import build_lazy_import_map

TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_08 = build_lazy_import_map(
    {
        ".base": ("s",),
        ".protocols": ("p",),
        ".refactor": ("refactor",),
        ".typings": ("t",),
        ".unit": ("unit",),
        ".unit.fixtures": (
            "real_docs_project",
            "real_makefile_project",
            "real_python_package",
            "real_toml_project",
            "real_workspace",
            "rope_workspace",
            "services_resource",
            "tool_config_document",
        ),
        ".unit.fixtures_git": ("real_git_repo",),
        ".utilities": ("u",),
        "flext_tests": (
            "r",
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "x",
        ),
    },
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_LAZY_IMPORTS_PART_08"]
