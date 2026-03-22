"""Tier-0 import fix rule — enforces canonical alias import ordering."""

from __future__ import annotations

from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import (
    FlextInfraRefactorRule,
    Tier0ImportAnalyzer,
    Tier0ImportFixer,
    c,
    u,
)


class FlextInfraRefactorTier0ImportFixRule(FlextInfraRefactorRule):
    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> tuple[cst.Module, list[str]]:
        if _file_path is None:
            return (tree, [])
        analyzer = Tier0ImportAnalyzer(
            file_path=_file_path,
            tier0_modules=self._tier0_modules(),
            core_aliases=self._core_aliases(),
        )
        tree.visit(analyzer)
        analysis = analyzer.build_analysis()
        if not analysis.has_violations:
            return (tree, [])

        project_root = u.Infra.discover_project_root_from_file(_file_path)
        core_package = (
            u.Infra.discover_core_package(project_root)
            if project_root
            else self._core_package()
        )

        fixer = Tier0ImportFixer(
            analysis=analysis,
            alias_to_submodule=self._alias_to_submodule(),
            core_package=core_package,
        )
        updated = tree.visit(fixer)
        return (updated, fixer.changes)

    def _tier0_modules(self) -> tuple[str, ...]:
        value = self.config.get("tier0_modules", [])
        if not isinstance(value, list):
            return ("constants.py", "typings.py", "protocols.py")
        return tuple(str(item) for item in value)

    def _core_aliases(self) -> tuple[str, ...]:
        value = self.config.get("core_aliases", [])
        if not isinstance(value, list):
            return tuple(c.Infra.NAMESPACE_SOURCE_UNIVERSAL_ALIASES)
        return tuple(str(item) for item in value)

    def _core_package(self) -> str:
        return str(self.config.get("core_package", "flext_core"))

    def _alias_to_submodule(self) -> dict[str, str]:
        value = self.config.get("alias_to_submodule", {})
        if not isinstance(value, dict):
            return {}
        return {str(key): str(item) for key, item in value.items()}


__all__ = ["FlextInfraRefactorTier0ImportFixRule"]
