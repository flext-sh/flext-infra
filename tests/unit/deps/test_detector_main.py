"""Public dependency mutation against a real provisioned UV project."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import config, main
from tests import u

pytestmark = pytest.mark.slow


class TestsFlextInfraDepsDetectorMain:
    def test_run_without_typings_skips_typings_detection(
        self, real_detector_project: Path
    ) -> None:
        root = real_detector_project
        before = (root / "pyproject.toml").read_bytes()
        outcome = tm.ok(u.Tests.run_real_detector(root, "--no-pip-check"))
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True, msg=outcome.stderr)
        tm.that((root / "pyproject.toml").read_bytes(), eq=before)
        report = tm.ok(
            u.Cli.json_read(
                root / ".reports/dependencies/detect-runtime-dev-latest.json"
            )
        )
        project = u.Cli.json_as_mapping(
            u.Cli.json_as_mapping(u.Cli.json_as_mapping(report).get("projects")).get(
                root.name
            )
        )
        tm.that(project, lacks="typings")

    @pytest.mark.parametrize(
        "real_detector_project",
        [("requests",), ("requests", "dateutil", "yaml")],
        indirect=True,
    )
    def test_apply_typings_installs_and_preserves_custom_source(
        self, real_detector_project: Path
    ) -> None:
        root = real_detector_project
        before = u.Tests.toml_payload((root / "pyproject.toml").read_text())
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root, "--apply-typings", "--apply", "--no-pip-check"
            )
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True, msg=outcome.stderr)
        after = u.Tests.toml_payload((root / "pyproject.toml").read_text())
        expected = {
            "requests": "types-requests",
            "python-dateutil": "types-python-dateutil",
            "pyyaml": "types-pyyaml",
        }
        requirements = u.Infra.project_dependency_names_from_payload(before)
        tm.that(
            u.Tests.toml_mapping(
                u.Tests.toml_mapping(after["project"])["optional-dependencies"]
            ),
            has="typings",
            msg=(
                f"{outcome.outcome}\n{outcome.stdout}\n{outcome.stderr}\n"
                + (root / ".reports/dependencies/detect-runtime-dev-latest.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        typing_specs = u.Tests.toml_strings(
            u.Tests.toml_mapping(
                u.Tests.toml_mapping(after["project"])["optional-dependencies"]
            )["typings"]
        )
        tm.that(
            {u.Infra.dep_name(item) for item in typing_specs},
            eq={expected[item] for item in requirements},
        )
        tm.that(after["dependency-groups"], eq=before["dependency-groups"])
        original_project = u.Tests.toml_mapping(before["project"])
        updated_project = u.Tests.toml_mapping(after["project"])
        for key, value in original_project.items():
            if key != "optional-dependencies":
                tm.that(updated_project[key], eq=value)
        tm.that(
            u.Tests.toml_mapping(
                u.Tests.toml_mapping(after["project"])["optional-dependencies"]
            )["feature"],
            eq=["requests"],
        )
        installed = tm.ok(
            u.Cli.capture(
                [
                    str(root / ".venv/bin/python"),
                    "-c",
                    (
                        "import importlib.metadata,sys; "
                        "[print(importlib.metadata.version(name)) for name in sys.argv[1:]]"
                    ),
                    *sorted(expected[item] for item in requirements),
                ],
                cwd=root,
            )
        )
        tm.that(len(installed.splitlines()), eq=len(requirements))
        snapshot = (root / "pyproject.toml").read_bytes()
        repeated = tm.ok(
            u.Tests.run_real_detector(
                root, "--apply-typings", "--apply", "--no-pip-check"
            )
        )
        tm.that(u.Cli.process_succeeded(repeated.outcome), eq=True, msg=repeated.stderr)
        tm.that((root / "pyproject.toml").read_bytes(), eq=snapshot)

    def test_apply_typings_dry_run_preserves_source_and_lock(
        self, real_detector_project: Path
    ) -> None:
        root = real_detector_project
        paths = (root / "pyproject.toml", root / "uv.lock")
        before = tuple(path.read_bytes() for path in paths)
        outcome = tm.ok(
            u.Tests.run_real_detector(root, "--apply-typings", "--no-pip-check")
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True, msg=outcome.stderr)
        tm.that(tuple(path.read_bytes() for path in paths), eq=before)

    def test_unsatisfiable_typing_add_is_not_success_even_with_no_fail(
        self, real_detector_project: Path
    ) -> None:
        root = real_detector_project
        with (root / "pyproject.toml").open("a", encoding="utf-8") as stream:
            stream.write(
                '\n[tool.uv]\nconstraint-dependencies = ["types-requests<0"]\n'
            )
        before = (root / "pyproject.toml").read_bytes()
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root, "--apply-typings", "--apply", "--no-fail", "--no-pip-check"
            )
        )
        tm.that(
            u.Cli.process_succeeded(outcome.outcome),
            eq=False,
            msg=f"{outcome.outcome}\n{outcome.stdout}\n{outcome.stderr}",
        )
        tm.that(outcome.stdout + outcome.stderr, has="UV typing dependency add failed")
        tm.that((root / "pyproject.toml").read_bytes(), eq=before)
        tm.that(
            (root / ".reports/dependencies/detect-runtime-dev-latest.json").exists(),
            eq=False,
        )

    def test_missing_uv_launch_is_not_reported_as_success(
        self, real_detector_project: Path
    ) -> None:
        root = real_detector_project
        before = (root / "pyproject.toml").read_bytes()
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root,
                "--apply-typings",
                "--apply",
                "--no-pip-check",
                env={"UV": str(root / "missing-uv")},
            )
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=False)
        tm.that((root / "pyproject.toml").read_bytes(), eq=before)

    def test_main_returns_failure_code_on_run_failure(self) -> None:
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

    def test_member_add_keeps_authoritative_parent_environment(
        self, real_detector_project: Path
    ) -> None:
        root = real_detector_project
        member = u.Tests.mk_project(
            root,
            "member",
            with_src=True,
            pyproject=(
                '[project]\nname = "member"\nversion = "0.1.0"\n'
                f'requires-python = "{config.Infra.codegen.toolchain.python_required_version}"\n'
                'dependencies = ["requests"]\n'
                "[tool.mypy]\n"
            ),
        )
        (member / "src/member/__init__.py").write_text(
            "import requests\n", encoding="utf-8"
        )
        u.Tests.initialize_git_repo(member)
        parent_before = (root / "pyproject.toml").read_bytes()
        outcome = tm.ok(
            u.Tests.run_real_detector(
                root,
                "--apply-typings",
                "--apply",
                "--no-pip-check",
                repository_root=member,
            )
        )
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True, msg=outcome.stderr)
        tm.that((member / ".venv").exists(), eq=False)
        tm.that((root / "pyproject.toml").read_bytes(), eq=parent_before)
        tm.that(
            u.Tests.toml_strings_at(
                (member / "pyproject.toml").read_text(),
                "project",
                "optional-dependencies",
                "typings",
            ),
            empty=False,
        )
