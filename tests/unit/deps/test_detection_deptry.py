"""Dependency reports preserve native deptry and the production-source scope.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from tests import c, tm, u


class TestsFlextInfraDepsDetectionDeptry:
    """Exercise native deptry against real project declarations and sources."""

    @staticmethod
    @pytest.mark.parametrize("namespace", ["infra", "deployment_support"])
    def test_shipped_namespace_imports_establish_runtime_usage(
        tmp_path: Path,
        namespace: str,
    ) -> None:
        """Native deptry consumes every shipped namespace alongside source."""
        name = "namespace-consumer"
        project = u.Tests.mk_project(
            tmp_path,
            name,
            with_src=True,
            pyproject=(
                f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
                'dependencies = ["pydantic"]\n'
            ),
        )
        u.Tests.write_standalone_workspace_manifest(
            project,
            name,
            declaration=u.Tests.StandaloneManifestDeclaration(
                cli_module=False,
                repository_namespace_packages=(namespace,),
            ),
        )
        (project / c.Infra.DEFAULT_SRC_DIR / "consumer.py").write_text(
            "from pathlib import Path\n",
            encoding=c.DEFAULT_ENCODING,
        )
        source = project / namespace / "runtime.py"
        source.parent.mkdir()
        source.write_text(
            "from pydantic import BaseModel\n",
            encoding=c.DEFAULT_ENCODING,
        )
        service = FlextInfraDependencyDetectionService()

        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )

        tm.that(exit_code, eq=0)
        tm.that(issues, empty=True)
        source.write_text("from pathlib import Path\n", encoding=c.DEFAULT_ENCODING)

        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )

        tm.that(exit_code, eq=1)
        tm.that(
            service.build_project_report(project.name, issues).deptry.unused,
            has="pydantic",
        )

    @staticmethod
    def test_missing_shipped_namespace_is_a_failure(tmp_path: Path) -> None:
        """An absent declared production root cannot yield a partial green scan."""
        name = "missing-namespace"
        project = u.Tests.mk_project(
            tmp_path,
            name,
            with_src=True,
            pyproject=(
                f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
                "dependencies = []\n"
            ),
        )
        u.Tests.write_standalone_workspace_manifest(
            project,
            name,
            declaration=u.Tests.StandaloneManifestDeclaration(
                cli_module=False,
                repository_namespace_packages=("deployment_support",),
            ),
        )

        tm.fail(
            FlextInfraDependencyDetectionService().run_deptry(
                project,
                Path(sys.executable).parent,
            ),
        )

    @staticmethod
    def test_unused_requirement_remains_a_finding(tmp_path: Path) -> None:
        """No policy profile may discard an unused runtime requirement."""
        project = u.Tests.mk_project(
            tmp_path,
            "unused-consumer",
            with_src=True,
            pyproject=(
                '[project]\nname = "unused-consumer"\nversion = "0.1.0"\n'
                'dependencies = ["pydantic"]\n'
            ),
        )
        (project / c.Infra.DEFAULT_SRC_DIR / "consumer.py").write_text(
            "from pathlib import Path\n",
            encoding=c.DEFAULT_ENCODING,
        )
        service = FlextInfraDependencyDetectionService()
        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )
        report = service.build_project_report(project.name, issues)
        tm.that(exit_code, eq=1)
        tm.that(report.deptry.unused, has="pydantic")
        tm.that(report.deptry.raw_count, eq=len(issues))

    @staticmethod
    def test_source_usage_changes_the_native_verdict(tmp_path: Path) -> None:
        """Adding and removing actual imports changes dependency evidence."""
        project = u.Tests.mk_project(
            tmp_path,
            "source-consumer",
            with_src=True,
            pyproject=(
                '[project]\nname = "source-consumer"\nversion = "0.1.0"\n'
                'dependencies = ["pydantic"]\n'
            ),
        )
        source = project / c.Infra.DEFAULT_SRC_DIR / "consumer.py"
        source.write_text(
            "from pydantic import BaseModel\n",
            encoding=c.DEFAULT_ENCODING,
        )
        service = FlextInfraDependencyDetectionService()
        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )
        tm.that(exit_code, eq=0)
        tm.that(issues, empty=True)
        source.write_text("from pathlib import Path\n", encoding=c.DEFAULT_ENCODING)
        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )
        tm.that(exit_code, eq=1)
        tm.that(
            service.build_project_report(project.name, issues).deptry.unused,
            has="pydantic",
        )

    @staticmethod
    def test_test_only_import_does_not_justify_runtime_dependency(
        tmp_path: Path,
    ) -> None:
        """Production evidence excludes imports used only by tests."""
        project = u.Tests.mk_project(
            tmp_path,
            "test-consumer",
            with_src=True,
            pyproject=(
                '[project]\nname = "test-consumer"\nversion = "0.1.0"\n'
                'dependencies = ["pydantic"]\n'
            ),
        )
        (project / c.Infra.DEFAULT_SRC_DIR / "consumer.py").write_text(
            "from pathlib import Path\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tests = project / "tests"
        tests.mkdir()
        (tests / "test_consumer.py").write_text(
            "from pydantic import BaseModel\n",
            encoding=c.DEFAULT_ENCODING,
        )
        service = FlextInfraDependencyDetectionService()
        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )
        tm.that(exit_code, eq=1)
        tm.that(
            service.build_project_report(project.name, issues).deptry.unused,
            has="pydantic",
        )

    @staticmethod
    def test_dev_import_in_source_remains_a_finding(tmp_path: Path) -> None:
        """A dev declaration does not authorize its use in production."""
        project = u.Tests.mk_project(
            tmp_path,
            "dev-consumer",
            with_src=True,
            pyproject=(
                '[project]\nname = "dev-consumer"\nversion = "0.1.0"\n'
                'dependencies = []\n[dependency-groups]\ndev = ["pydantic"]\n'
            ),
        )
        (project / c.Infra.DEFAULT_SRC_DIR / "consumer.py").write_text(
            "from pydantic import BaseModel\n",
            encoding=c.DEFAULT_ENCODING,
        )
        service = FlextInfraDependencyDetectionService()
        issues, exit_code = tm.ok(
            service.run_deptry(project, Path(sys.executable).parent),
        )
        tm.that(exit_code, eq=1)
        tm.that(
            service.build_project_report(project.name, issues).deptry.dev_in_runtime,
            has="pydantic",
        )

    @staticmethod
    @pytest.mark.parametrize("with_src", [False, True])
    def test_missing_configuration_is_a_failure(tmp_path: Path, with_src: bool) -> None:
        """An absent declaration never becomes an empty successful report."""
        project = tmp_path / "missing-config"
        project.mkdir()
        if with_src:
            (project / c.Infra.DEFAULT_SRC_DIR).mkdir()
        tm.fail(
            FlextInfraDependencyDetectionService().run_deptry(
                project,
                Path(sys.executable).parent,
            ),
        )

    @staticmethod
    def test_missing_native_tool_is_a_failure(tmp_path: Path) -> None:
        """An unavailable tool cannot prove dependency correctness."""
        project = u.Tests.mk_project(
            tmp_path,
            "missing-tool",
            with_src=True,
            pyproject=(
                '[project]\nname = "missing-tool"\nversion = "0.1.0"\n'
                "dependencies = []\n"
            ),
        )
        (project / c.Infra.DEFAULT_SRC_DIR / "consumer.py").write_text(
            "from pathlib import Path\n",
            encoding=c.DEFAULT_ENCODING,
        )
        unavailable_bin = tmp_path / "unavailable-bin"
        unavailable_bin.mkdir()
        tm.fail(
            FlextInfraDependencyDetectionService().run_deptry(project, unavailable_bin),
        )

    @staticmethod
    def test_existing_report_cannot_be_reused(tmp_path: Path) -> None:
        """A stale artifact cannot become evidence for a new invocation."""
        project = u.Tests.mk_project(
            tmp_path,
            "stale-report",
            with_src=True,
            pyproject=(
                '[project]\nname = "stale-report"\nversion = "0.1.0"\n'
                "dependencies = []\n"
            ),
        )
        report = tmp_path / "deptry.json"
        report.write_text("[]", encoding=c.DEFAULT_ENCODING)
        tm.fail(
            FlextInfraDependencyDetectionService().run_deptry(
                project,
                Path(sys.executable).parent,
                json_output_path=report,
            ),
            has="already exists",
        )
        tm.that(report.read_text(encoding=c.DEFAULT_ENCODING), eq="[]")
