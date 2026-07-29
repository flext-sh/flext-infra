"""Declarative descriptors for codegen-family CLI routes."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar


class CodegenRouteDescriptors:
    """Own public descriptions for basemk, check, codegen, and deps."""

    descriptions: ClassVar[Mapping[str, Mapping[str, str]]] = MappingProxyType({
        "basemk": MappingProxyType({
            "generate": "Generate base.mk content from the canonical template"
        }),
        "check": MappingProxyType({
            "run": "Run workspace quality gates",
            "fix-pyrefly-settings": "Repair [tool.pyrefly] blocks",
            "fix-enforcement": "Auto-fix enforcement-catalog violations",
        }),
        "codegen": MappingProxyType({
            "conform": "Conform generated project and workspace files",
            "new": "Create a new FLEXT project from the canonical templates",
            "init": "Generate/refresh PEP 562 lazy-import __init__.py files",
            "census": "Count namespace violations across workspace projects",
            "scaffold": "Generate missing base modules in src/ and tests/",
            "auto-fix": "Auto-fix namespace violations (move Finals/TypeVars)",
            "py-typed": "Create/remove PEP 561 py.typed markers",
            "pipeline": "Run full codegen pipeline",
            "constants-quality-gate": "Run constants migration quality gate",
            "consolidate": "Consolidate inline constants into c.Infra.* references",
            "version-file": "Generate __version__.py from project-metadata SSOT",
        }),
        "deps": MappingProxyType({
            "detect": "Detect runtime vs dev dependencies",
            "extra-paths": "Synchronize pyright/mypy extraPaths",
            "modernize": "Modernize workspace pyproject files",
        }),
    })

    @classmethod
    def command_descriptions(cls, group: str) -> Mapping[str, str]:
        """Return this route family's declarative command descriptors."""
        return cls.descriptions[group]


__all__: list[str] = ["CodegenRouteDescriptors"]
