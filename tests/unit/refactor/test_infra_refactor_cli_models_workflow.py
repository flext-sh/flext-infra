"""CLI workflow tests for refactor namespace automation."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from flext_infra import main as infra_main


class TestsFlextInfraRefactorInfraRefactorCliModelsWorkflow:
    """Behavior contract for test_infra_refactor_cli_models_workflow."""

    def test_namespace_enforce_cli_fails_on_manual_protocol_violation(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = tmp_path / "workspace"
        project = workspace / "sample-project"
        module_dir = project / "src" / "sample_pkg"
        module_dir.mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            "[project]\nname='sample'\n",
            encoding="utf-8",
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
        cli_args = [
            "namespace-enforce",
            f"--workspace={workspace!s}",
            "--dry-run",
        ]
        with redirect_stdout(buffer):
            result = infra_main(["refactor"] + cli_args)
        assert result != 0
