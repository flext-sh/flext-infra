from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main


class TestFlextInfraRefactorMainCli:
    @staticmethod
    def _refactor_main(*args: str) -> int:
        return infra_main(["refactor", *args])

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _build_basic_workspace(tmp_path: Path) -> tuple[Path, Path]:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        service_file = workspace / "src" / "sample_pkg" / "service.py"
        TestFlextInfraRefactorMainCli._write(
            service_file,
            "from __future__ import annotations\n"
            "from collections.abc import Mapping\n"
            "from typing import TypeAlias\n\n"
            "PayloadMap: TypeAlias = t.StrMapping\n"
            "def consume(payload: PayloadMap) -> PayloadMap:\n"
            "    return payload\n",
        )
        return workspace, service_file

    def test_refactor_census_accepts_workspace_before_subcommand(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, _service_file = self._build_basic_workspace(tmp_path)
        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
        )
        assert result == 0
