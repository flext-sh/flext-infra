"""Shared lazy-package project fixtures for the import-law engine contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalizationSupport:
    """Build real lazy-package projects and normalize sources through the engine."""

    @staticmethod
    def _lazy_init(package_dir: Path, exports: t.StrMapping) -> None:
        """Write one generated-shape lazy ``__init__`` publishing ``exports``."""
        package_dir.mkdir(parents=True, exist_ok=True)
        entries = "".join(
            f"    {name!r}: {module!r},\n" for name, module in exports.items()
        )
        (package_dir / "__init__.py").write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            "from flext_core.lazy import install_lazy_exports\n"
            "\n"
            "install_lazy_exports(\n"
            "    __name__,\n"
            "    globals(),\n"
            "    {\n"
            f"{entries}"
            "    },\n"
            ")\n",
            encoding="utf-8",
        )

    @classmethod
    def _project(cls, tmp_path: Path) -> tuple[Path, Path]:
        """Materialize ``demo_pkg`` with a lazy root and lazy family inits.

        Returns:
            The project root and the package directory.

        """
        project = tmp_path / "project"
        package: Path = u.Tests.src_package(
            project,
            "demo_pkg",
            pyproject="[project]\nname='demo'\nversion='1.0.0'\n",
        )
        families = u.Infra.facade_families()
        cls._lazy_init(
            package,
            {
                **{
                    letter: f".{families[letter].module}"
                    for letter in ("c", "t", "m", "u")
                },
                "r": "flext_core",
                "DemoApi": ".api",
            },
        )
        cls._lazy_init(package / "_utilities", {"DemoHelper": ".helper"})
        cls._lazy_init(package / "_models", {"DemoRecord": ".record"})
        cls._lazy_init(package / "services", {"DemoRunner": ".runner"})
        for letter, family in families.items():
            (package / f"{family.module}.py").write_text(
                f"from flext_cli import {letter}\n__all__ = ['{letter}']\n",
                encoding="utf-8",
            )
        return project, package

    @staticmethod
    def _normalize(project: Path, file_path: Path, source: str) -> str:
        """Normalize one module and require a rewrite.

        Returns:
            The rewritten source.

        """
        normalized = u.Infra.normalize_import_source(
            project_root=project,
            file_path=file_path,
            source=source,
        )
        tm.ok(normalized is not None)
        return normalized or ""

    @classmethod
    def _inherited_project(
        cls, tmp_path: Path, *, override_member: bool = False
    ) -> tuple[Path, Path]:
        """Build real upstream and consumer facades with inherited members.

        Returns:
            The project root and consumer package directory.

        """
        project, package = cls._project(tmp_path)
        families = u.Infra.facade_families()
        upstream = package.parent / "upstream_pkg"
        cls._lazy_init(
            upstream,
            {letter: f".{families[letter].module}" for letter in ("c", "m", "u")},
        )
        for letter in ("c", "m", "u"):
            module = families[letter].module
            (upstream / f"{module}.py").write_text(
                f"class {letter}:\n"
                "    @staticmethod\n"
                "    def render(value: str) -> str:\n"
                "        return value\n"
                f"__all__ = [{letter!r}]\n",
                encoding=c.DEFAULT_ENCODING,
            )
            replacement = (
                "    @staticmethod\n"
                "    def render(value: str) -> str:\n"
                "        return value.upper()\n"
                if override_member and letter == "m"
                else "    pass\n"
            )
            (package / f"{module}.py").write_text(
                f"from upstream_pkg import {letter} as upstream_{letter}\n"
                f"class {letter}(upstream_{letter}):\n"
                f"{replacement}"
                f"__all__ = [{letter!r}]\n",
                encoding=c.DEFAULT_ENCODING,
            )
        return project, package
