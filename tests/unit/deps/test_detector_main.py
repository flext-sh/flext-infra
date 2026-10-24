"""Public dependency mutation against a real provisioned UV project.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, m, main
from flext_infra.deps import FlextInfraRuntimeDevDependencyDetector
from tests import c, tm, u

# The fixture resolves and installs a real consumer environment from Git/index
# sources; this is an external integration boundary owned by ``test-full``.
pytestmark = [pytest.mark.slow, pytest.mark.remote]


class TestsFlextInfraDepsDetectorMain:
    """Tests for ``FlextInfraDepsDetectorMain``."""

    @staticmethod
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
                tm.ok(FlextInfraRuntimeDevDependencyDetector.execute(params)), eq=True
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
        report = tm.ok(
            u.Cli.json_read(
                root / ".reports/dependencies/detect-runtime-dev-latest.json",
            ),
        )
        project = u.Cli.json_as_mapping(
            u.Cli.json_as_mapping(u.Cli.json_as_mapping(report).get("projects")).get(
                root.name,
            ),
        )
        tm.that(project, lacks="typings")

    # Why: current `requests` ships its own inline types (`py.typed`), so
    # mypy no longer reports a missing-stub hint for it and `types-requests`
    # is retired upstream. `requests` stays imported (it still exercises the
    # "already-typed import produces no stub requirement" path via the
    # `feature` extra assertion below) but the stub-detection assertions
    # here exercise only modules that still lack inline types today.
    # `requests` stays a listed module (not just the always-declared `feature`
    # extra) so deptry does not flag it as an unused runtime dependency.
    # A conformed consumer's dev group already carries every stub the scaffold
    # declares, so the scenario uses untyped libraries whose stubs it lacks.
    # Stub discovery remains active when normal checks follow untyped imports.
    @staticmethod
    def _installed_typings_snapshot(root: Path, added: set[str]) -> bytes:
        """Verify the real installed distributions and capture their declarations.

        Returns:
            The pyproject snapshot after UV installed the development requirements.

        """
        installed = tm.ok(
            u.Cli.capture(
                [
                    str(root / ".venv/bin/python"),
                    "-c",
                    (
                        "import importlib.metadata,sys; "
                        "[print(importlib.metadata.version(name))"
                        " for name in sys.argv[1:]]"
                    ),
                    *sorted(added),
                ],
                cwd=root,
            ),
        )
        tm.that(len(installed.splitlines()), eq=len(added))
        return (root / "pyproject.toml").read_bytes()

    @staticmethod
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
        # `requests` (when present) needs no stub package; only the
        # still-untyped requirements below drive the typings-group assertion.
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
        tm.that(
            {
                key: value
                for key, value in u.Tests.toml_mapping(
                    after["dependency-groups"]
                ).items()
                if key != "dev"
            },
            eq={
                key: value
                for key, value in u.Tests.toml_mapping(
                    before["dependency-groups"]
                ).items()
                if key != "dev"
            },
        )
        original_project = u.Tests.toml_mapping(before["project"])
        updated_project = u.Tests.toml_mapping(after["project"])
        for key, value in original_project.items():
            if key != "optional-dependencies":
                tm.that(updated_project[key], eq=value)
        tm.that(
            u.Tests.toml_mapping(
                u.Tests.toml_mapping(after["project"])["optional-dependencies"],
            )["feature"],
            eq=["requests"],
        )
        snapshot = TestsFlextInfraDepsDetectorMain._installed_typings_snapshot(
            root,
            added,
        )
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
    def test_main_returns_failure_code_on_run_failure() -> None:
        """Test main returns failure code on run failure."""
        tm.that(
            main([
                "deps",
                "detect",
                "--repository-root",
                "/nonexistent/path",
                "--no-pip-check",
            ]),
            eq=1,
        )

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
