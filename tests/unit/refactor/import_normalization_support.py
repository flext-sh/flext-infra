"""Shared lazy-package project fixtures for the import-law engine contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.refactor import FlextInfraImportNormalization
from tests import t, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


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
        cls._lazy_init(
            package,
            {
                "c": ".constants",
                "t": ".typings",
                "m": ".models",
                "u": ".utilities",
                "r": "flext_core",
                "DemoApi": ".api",
            },
        )
        cls._lazy_init(package / "_utilities", {"DemoHelper": ".helper"})
        cls._lazy_init(package / "_models", {"DemoRecord": ".record"})
        cls._lazy_init(package / "services", {"DemoRunner": ".runner"})
        return project, package

    @staticmethod
    def _normalize(project: Path, file_path: Path, source: str) -> str:
        """Normalize one module and require a rewrite.

        Returns:
            The rewritten source.

        """
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=file_path,
            source=source,
        )
        tm.that(normalized is not None, eq=True)
        return normalized or ""

    @staticmethod
    def _publish(project: Path, module: Path, source: str) -> str:
        """Write the normalized module, or its source when already normal.

        Returns:
            The text written to ``module``.

        """
        normalized = FlextInfraImportNormalization.normalize_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        text = source if normalized is None else normalized
        module.write_text(text, encoding="utf-8")
        return text

    @staticmethod
    def _assert_fixed_point(project: Path, module: Path) -> None:
        """Require a second normalization pass over ``module`` to change nothing."""
        tm.that(
            FlextInfraImportNormalization.normalize_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )

    @staticmethod
    def _run_python(
        project: Path,
        *arguments: str,
        pythonpath: Path | None = None,
    ) -> p.Cli.CommandOutput:
        """Run the interpreter in ``project`` and require a successful process.

        Returns:
            The captured command output.

        """
        result = tm.ok(
            u.Cli.run(
                (sys.executable, *arguments),
                cwd=project,
                options=(
                    None
                    if pythonpath is None
                    else m.Cli.ProcessOptions(env={"PYTHONPATH": str(pythonpath)})
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        return result
