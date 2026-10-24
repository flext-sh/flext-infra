"""Pyrefly distinguishes admitted literal files from discovered targets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config, gates, m, u
from tests import c, tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPyreflyExplicitTargets:
    """Literal files retain native scope; discovery retains artifact exclusions."""

    @staticmethod
    @pytest.mark.slow
    def test_literal_excluded_stub_preserves_native_scope_and_config(
        real_python_package: Path,
    ) -> None:
        """A selected excluded stub is checked without admitting its sibling."""
        project = real_python_package
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + '\n[tool.pyrefly]\nproject-excludes = ["**/excluded/**"]\n',
            encoding="utf-8",
        )
        tree = project / "excluded"
        tree.mkdir()
        selected = tree / "contract.pyi"
        selected.write_text("value: int = 1\n", encoding="utf-8")
        (tree / "sibling.pyi").write_text("def :\n", encoding="utf-8")
        (project / "pyrefly.toml").write_text(
            'project-excludes = ["**/*"]\npython-version = "invalid"\n',
            encoding="utf-8",
        )
        reports = project / ".reports"
        reports.mkdir()
        context = m.Infra.GateContext(
            repository_root=project,
            reports_dir=reports,
            selected_files=(selected,),
        )
        targets = (str(selected.relative_to(project)),)
        tm.that(
            u.Infra.pyrefly_target_args(
                project,
                targets,
                selected_files=context.selected_files,
            ),
            eq=targets,
        )
        tm.that(
            u.Infra.pyrefly_target_args(project, targets, selected_files=()),
            eq=(*targets, c.Infra.PYREFLY_PROJECT_EXCLUDES_FLAG, "**/excluded/**"),
        )
        gate = gates.FlextInfraPyreflyGate(project)
        valid = gate.check_files((selected,), project, context)
        tm.that(valid.result.passed, eq=True, msg=str(valid.issues))
        selected.write_text('value: int = "incorrect"\n', encoding="utf-8")
        invalid = gate.check_files((selected,), project, context)
        tm.fail(invalid.result.passed)
        tm.that(invalid.issues, empty=False)
        tm.that(
            all(
                issue.file.endswith(selected.name) and issue.line > 0
                for issue in invalid.issues
            ),
            eq=True,
            msg=str(invalid.issues),
        )
        discovery = m.Infra.GateContext(repository_root=project, reports_dir=reports)
        empty = gate.check_files((selected,), project, discovery)
        tm.fail(empty.result.passed)
        tm.that(empty.issues, empty=False)
        tm.that(
            "\n".join(issue.message for issue in empty.issues),
            has="No Python files matched",
        )

    @staticmethod
    @pytest.mark.slow
    def test_explicit_targets_keep_configured_excludes(
        real_python_package: Path,
    ) -> None:
        """The real gate excludes a generated tree yet still checks governed code.

        Premise (flext-gknfx): a root-level module switches the gate to
        explicit targets, and Pyrefly ignores the configured project-excludes
        for explicit files, so flext-grpc's generated protos were checked.
        """
        names = config.Infra.codegen.generated_sources
        tm.that(names, empty=False)
        project = real_python_package
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + '\n[tool.pyrefly]\nproject-includes = ["src/**/*.py*"]\n'
            + f'project-excludes = ["**/{names[0]}/**"]\n',
            encoding="utf-8",
        )
        (project / "conftest.py").write_text('"""Root module."""\n', encoding="utf-8")
        tree = project / "src" / "test_pkg" / names[0]
        tree.mkdir()
        (tree / "wire_pb2.py").write_text('value: int = "wire"\n', encoding="utf-8")
        reports = project / ".reports"
        reports.mkdir()
        context = m.Infra.GateContext(repository_root=project, reports_dir=reports)
        gate = gates.FlextInfraPyreflyGate(project)

        excluded = gate.check(project, context)

        tm.that(excluded.result.passed, eq=True, msg=str(excluded.issues))
        governed_module = project / "src" / "test_pkg" / "contract.py"
        governed_module.write_text('value: int = "governed"\n', encoding="utf-8")
        governed = gate.check(project, context)
        tm.fail(governed.result.passed)
        tm.that(
            all(issue.file.endswith(governed_module.name) for issue in governed.issues),
            eq=True,
            msg=str(governed.issues),
        )
