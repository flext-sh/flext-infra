"""Public dependency mutation against a real provisioned UV project.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, deps, m, main
from tests import c, tm, u


class TestsFlextInfraDepsDetectorMain:
    """Tests for ``FlextInfraDepsDetectorMain``."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.remote
    @pytest.mark.parametrize("entrypoint", ["cli", c.ContextScope.REQUEST])
    def test_run_reports_without_mutating_the_project(
        real_detector_project: Path,
        entrypoint: str,
    ) -> None:
        """CLI and typed service requests retain the same report behavior."""
        root = real_detector_project
        before = (root / c.PYPROJECT_FILENAME).read_bytes()
        if entrypoint == c.ContextScope.REQUEST:
            params = m.Infra.DetectCommand(repository_root=root, no_pip_check=True)
            before_request = params.model_dump()
            tm.that(
                tm.ok(deps.FlextInfraRuntimeDevDependencyDetector.execute(params)),
                eq=True,
            )
            tm.that(params.model_dump(), eq=before_request)
        else:
            outcome = tm.ok(u.Tests.run_real_detector(root, "--no-pip-check"))
            tm.that(
                u.Cli.process_succeeded(outcome.outcome),
                eq=True,
                msg=f"{outcome.stdout}\n{outcome.stderr}",
            )
        tm.that((root / c.PYPROJECT_FILENAME).read_bytes(), eq=before)
        report = m.Infra.WorkspaceDependencyReport.model_validate_json(
            (
                root / ".reports/dependencies/detect-runtime-dev-latest.json"
            ).read_bytes(),
        )
        tm.that(root.name in report.projects, eq=True)

    @staticmethod
    def test_main_preserves_repository_failure(tmp_path: Path) -> None:
        """Preserve the native repository error at the public CLI boundary."""
        with pytest.raises(OSError, match="cannot open git repository"):
            main([
                "deps",
                "detect",
                "--repository-root",
                str(tmp_path / "missing"),
                "--no-pip-check",
            ])

    # Why: commit ec3b159c7 (bead X-17, "detector venv from root") retired
    # ambient `UV_PROJECT_ENVIRONMENT`/`VIRTUAL_ENV` resolution from
    # `detector_runtime.run` on purpose — "an ambient UV_PROJECT_ENVIRONMENT
    # would silently redirect detection elsewhere" — and now resolves
    # `venv_bin` deterministically from `--repository-root` alone. A member
    # with no `.venv` of its own therefore no longer inherits the invoking
    # parent's environment; it fails closed with a clear missing-deptry
    # diagnostic instead of silently scanning under a different project's
    # binaries. This rewrites the retired "authoritative parent environment"
    # expectation to the current, intentional contract.
    @staticmethod
    @pytest.mark.slow
    @pytest.mark.remote
    def test_member_without_own_venv_fails_closed_not_parent_environment(
        real_detector_project: Path,
    ) -> None:
        """Test member without own venv fails closed not parent environment."""
        root = real_detector_project
        python_required = config.Infra.codegen.toolchain.python_required_version
        member = u.Tests.mk_project(
            root,
            "member",
            with_src=True,
            pyproject=(
                '[project]\nname = "member"\nversion = "0.1.0"\n'
                f'requires-python = "{python_required}"\n'
                'dependencies = ["pyyaml"]\n'
                "[tool.mypy]\n"
            ),
        )
        (member / "src/member/__init__.py").write_text(
            "import yaml\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(member)
        parent_before = (root / c.PYPROJECT_FILENAME).read_bytes()
        member_before = (member / c.PYPROJECT_FILENAME).read_bytes()
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root,
                "--apply",
                "--no-pip-check",
                repository_root=member,
            ),
        )
        tm.fail(u.Cli.process_succeeded(outcome.outcome))
        tm.that(outcome.stdout + outcome.stderr, has="Deptry executable not found")
        tm.fail((member / ".venv").exists())
        tm.that((root / c.PYPROJECT_FILENAME).read_bytes(), eq=parent_before)
        tm.that((member / c.PYPROJECT_FILENAME).read_bytes(), eq=member_before)
