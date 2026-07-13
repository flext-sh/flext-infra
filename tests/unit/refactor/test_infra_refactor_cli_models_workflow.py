"""CLI workflow tests for refactor namespace automation."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING

from flext_infra import main as infra_main
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow:
    """Behavior contract for test_infra_refactor_cli_models_workflow."""

    def test_namespace_enforce_cli_fails_on_manual_protocol_violation(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-project"
        module_dir = project / "src" / "sample_pkg"
        module_dir.mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        (module_dir / "service.py").write_text(
            "from __future__ import annotations\n"
            "from typing import Protocol\n\n"
            "class External(Protocol):\n"
            "    def call(self) -> str:\n"
            "        ...\n",
            encoding="utf-8",
        )
        buffer = StringIO()
        cli_args = ["namespace-enforce", f"--workspace={workspace!s}", "--dry-run"]
        with redirect_stdout(buffer):
            result = infra_main(["refactor", *cli_args])
        tm.that(result, ne=0)

    def test_wrapper_root_namespace_cli_dry_run_succeeds(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-project"
        tests_dir = project / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        source_file = tests_dir / "test_sample.py"
        source_file.write_text(
            "from tests import c\n"
            "\n"
            "def test_contract() -> None:\n"
            "    _ = c.Core.Tests.ERR_OK_FAILED\n",
            encoding="utf-8",
        )

        with redirect_stdout(StringIO()):
            result = infra_main([
                "refactor",
                "wrapper-root-namespace",
                f"--workspace={workspace!s}",
                "--dry-run",
            ])

        tm.that(result, eq=0)
        tm.that(source_file.read_text(encoding="utf-8"), has="c.Core.Tests")

    def test_wrapper_root_namespace_cli_check_fails_when_changes_are_needed(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-project"
        tests_dir = project / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        (tests_dir / "test_sample.py").write_text(
            "from tests import m\n"
            "\n"
            "def test_contract() -> None:\n"
            "    _ = m.Core.Tests.Testobject\n",
            encoding="utf-8",
        )

        result = infra_main([
            "refactor",
            "wrapper-root-namespace",
            f"--workspace={workspace!s}",
            "--check",
        ])

        tm.that(result, ne=0)

    def test_wrapper_root_namespace_cli_apply_rewrites_file(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-project"
        tests_dir = project / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        (project / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        source_file = tests_dir / "test_sample.py"
        source_file.write_text(
            "from tests import t\n"
            "\n"
            "def test_contract() -> None:\n"
            "    _ = t.Core.Tests.Testobject\n",
            encoding="utf-8",
        )

        result = infra_main([
            "refactor",
            "wrapper-root-namespace",
            f"--workspace={workspace!s}",
            "--apply",
        ])

        tm.that(result, eq=0)
        updated = source_file.read_text(encoding="utf-8")
        tm.that(updated, has="from tests import t")
        tm.that(updated, has="t.Tests.Testobject")
        tm.that(updated, lacks="Core.Tests")
