"""Package checks exercise actual environments through their managed checker.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from pathlib import Path

import pytest

from flext_infra.deps.detection import FlextInfraDependencyDetectionService
from tests import c, tm, u


class TestsFlextInfraDepsDetectionPipCheck:
    """A native UV verdict belongs to the selected physical environment."""

    @staticmethod
    @pytest.mark.parametrize("conflict", [False, True])
    def test_installed_package_requirements_determine_the_verdict(
        tmp_path: Path,
        *,
        conflict: bool,
    ) -> None:
        """Real installed metadata produces clean and missing-provider verdicts."""
        project = tmp_path / "package-check"
        distribution = "package-check-consumer"
        dependency = "package-check-missing-provider>=1"
        u.Tests.write_native_resolution_project(
            project,
            distribution,
            dependencies=(dependency,) if conflict else (),
        )
        u.Tests.initialize_git_repo(project)
        tm.ok(u.Tests.provision_python_project_environment(project))
        environment = u.Infra.runtime_environment_dir(project)
        lines, exit_code = tm.ok(
            FlextInfraDependencyDetectionService().run_pip_check(
                project,
                environment / Path(sys.executable).parent.name,
            ),
        )
        tm.that(exit_code, eq=int(conflict))
        tm.that(lines, empty=False)
        if conflict:
            tm.that("\n".join(lines), has=distribution)

    @staticmethod
    def test_missing_environment_is_a_failure(tmp_path: Path) -> None:
        """An absent environment cannot report no conflicts."""
        tm.fail(
            FlextInfraDependencyDetectionService().run_pip_check(
                tmp_path,
                tmp_path / "missing-environment" / Path(sys.executable).parent.name,
            ),
        )

    @staticmethod
    def test_unlaunchable_environment_is_a_failure(tmp_path: Path) -> None:
        """A broken interpreter preserves the native checker failure."""
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "python").write_text("", encoding=c.DEFAULT_ENCODING)

        tm.fail(
            FlextInfraDependencyDetectionService().run_pip_check(tmp_path, venv_bin),
        )
