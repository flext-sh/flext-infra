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
    @pytest.mark.parametrize("entrypoint", ["cli", "request"])
    def test_run_without_typings_skips_typings_detection(
        real_detector_project: Path,
        entrypoint: str,
    ) -> None:
        """CLI and typed service requests retain the same report behavior."""
        root = real_detector_project
        before = (root / "pyproject.toml").read_bytes()
        if entrypoint == "request":
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
        tm.that((root / "pyproject.toml").read_bytes(), eq=before)
        report = m.Infra.WorkspaceDependencyReport.model_validate_json(
            (
                root / ".reports/dependencies/detect-runtime-dev-latest.json"
            ).read_bytes(),
        )
        tm.that(report.projects[root.name].typings, eq=None)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.remote
    @pytest.mark.parametrize(
        "real_detector_project",
        c.Tests.DETECTOR_MODULE_SCENARIOS[1:],
        indirect=True,
    )
    def test_apply_typings_follows_governed_policy_and_preserves_source(
        real_detector_project: Path,
    ) -> None:
        """Test apply typings follows governed policy and preserves source."""
        root = real_detector_project
        before = u.Tests.toml_payload((root / "pyproject.toml").read_text())
        lock_before = (root / "uv.lock").read_bytes()
        expected = {"pytz": "types-pytz", "six": "types-six"}
        declared_dev = {
            u.Infra.dep_name(item)
            for item in u.Tests.toml_strings(
                u.Tests.toml_mapping(before["dependency-groups"])["dev"],
            )
        }
        tm.that(declared_dev & set(expected.values()), empty=True)
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root,
                "--apply-typings",
                "--apply",
                "--no-pip-check",
            ),
        )
        tm.that(
            u.Cli.process_succeeded(outcome.outcome),
            eq=True,
            msg=f"{outcome.stdout}\n{outcome.stderr}",
        )
        after = u.Tests.toml_payload((root / "pyproject.toml").read_text())
        requirements = [
            item
            for item in u.Infra.project_dependency_names_from_payload(before)
            if item in expected
        ]
        added = {expected[item] for item in requirements}
        typing_specs = u.Tests.toml_strings(
            u.Tests.toml_mapping(after["dependency-groups"])["dev"],
        )
        tm.that(
            {u.Infra.dep_name(item) for item in typing_specs},
            eq=declared_dev | added,
            msg=(
                f"{outcome.outcome}\n{outcome.stdout}\n{outcome.stderr}\n"
                + (
                    root / ".reports/dependencies/detect-runtime-dev-latest.json"
                ).read_text(encoding="utf-8")
            ),
        )
        tm.that(after["project"], eq=before["project"])
        tm.that((root / "uv.lock").read_bytes(), eq=lock_before)
        snapshot = (root / "pyproject.toml").read_bytes()
        repeated = tm.ok(
            u.Tests.run_real_detector(
                root,
                "--apply-typings",
                "--apply",
                "--no-pip-check",
            ),
        )
        tm.that(
            u.Cli.process_succeeded(repeated.outcome),
            eq=True,
            msg=f"{repeated.stdout}\n{repeated.stderr}",
        )
        tm.that((root / "pyproject.toml").read_bytes(), eq=snapshot)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.remote
    def test_apply_typings_dry_run_preserves_source_and_lock(
        real_detector_project: Path,
    ) -> None:
        """Test apply typings dry run preserves source and lock."""
        root = real_detector_project
        paths = (root / "pyproject.toml", root / "uv.lock")
        before = tuple(path.read_bytes() for path in paths)
        outcome = tm.ok(
            u.Tests.run_real_detector(root, "--apply-typings", "--no-pip-check"),
        )
        tm.that(
            u.Cli.process_succeeded(outcome.outcome),
            eq=True,
            msg=f"{outcome.stdout}\n{outcome.stderr}",
        )
        tm.that(tuple(path.read_bytes() for path in paths), eq=before)

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

    # Why: `requests` ships inline types now and never needs a stub add;
    # `pyyaml` still lacks inline types, so it is what actually exercises
    # the member's own typings-group installation below.
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
        parent_before = (root / "pyproject.toml").read_bytes()
        member_before = (member / "pyproject.toml").read_bytes()
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root,
                "--apply-typings",
                "--apply",
                "--no-pip-check",
                repository_root=member,
            ),
        )
        tm.fail(u.Cli.process_succeeded(outcome.outcome))
        tm.that(outcome.stdout + outcome.stderr, has="Deptry executable not found")
        tm.fail((member / ".venv").exists())
        tm.that((root / "pyproject.toml").read_bytes(), eq=parent_before)
        tm.that((member / "pyproject.toml").read_bytes(), eq=member_before)
