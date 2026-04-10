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
    def _build_centralize_workspace(tmp_path: Path) -> tuple[Path, Path]:
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
            "PayloadMap: TypeAlias = Mapping[str, str]\n"
            "def consume(payload: PayloadMap) -> PayloadMap:\n"
            "    return payload\n",
        )
        return workspace, service_file

    @staticmethod
    def _build_runtime_alias_workspace(tmp_path: Path) -> tuple[Path, Path]:
        workspace = tmp_path / "workspace"
        project_root = workspace / "flext-demo"
        TestFlextInfraRefactorMainCli._write(
            project_root / "Makefile",
            "check:\n\t@true\n",
        )
        TestFlextInfraRefactorMainCli._write(
            project_root / "pyproject.toml",
            '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
        )
        TestFlextInfraRefactorMainCli._write(
            project_root / "src" / "flext_demo" / "__init__.py",
            "from __future__ import annotations\n\n"
            "_LAZY_IMPORTS: dict[str, tuple[str, str]] = {\n"
            '    "FlextDemoCodegenGeneration": (\n'
            '        "flext_demo.codegen.generation",\n'
            '        "FlextDemoCodegenGeneration",\n'
            "    ),\n"
            '    "c": ("flext_demo.constants", "c"),\n'
            '    "r": ("flext_core.result", "r"),\n'
            '    "s": ("flext_core.service", "s"),\n'
            '    "t": ("flext_demo.typings", "t"),\n'
            '    "u": ("flext_demo.utilities", "u"),\n'
            "}\n"
            "FlextDemoCodegenGeneration = object()\n"
            "c = object()\n"
            "r = object()\n"
            "s = object()\n"
            "t = object()\n"
            "u = object()\n",
        )
        TestFlextInfraRefactorMainCli._write(
            project_root / "src" / "flext_demo" / "constants.py",
            "from __future__ import annotations\n\n"
            "class FlextDemoConstants:\n"
            "    pass\n\n"
            "c = FlextDemoConstants\n",
        )
        TestFlextInfraRefactorMainCli._write(
            project_root / "src" / "flext_demo" / "typings.py",
            "from __future__ import annotations\n\n"
            "class FlextDemoTypes:\n"
            "    pass\n\n"
            "t = FlextDemoTypes\n",
        )
        TestFlextInfraRefactorMainCli._write(
            project_root / "src" / "flext_demo" / "utilities.py",
            "from __future__ import annotations\n\n"
            "class FlextDemoUtilities:\n"
            "    pass\n\n"
            "u = FlextDemoUtilities\n",
        )
        TestFlextInfraRefactorMainCli._write(
            project_root / "src" / "flext_demo" / "codegen" / "generation.py",
            "from __future__ import annotations\n\n"
            "class FlextDemoCodegenGeneration:\n"
            "    pass\n",
        )
        target = project_root / "src" / "flext_demo" / "codegen" / "lazy_init.py"
        TestFlextInfraRefactorMainCli._write(
            target,
            "from __future__ import annotations\n\n"
            "from flext_core import r, s\n"
            "from flext_demo import (\n"
            "    FlextDemoCodegenGeneration,\n"
            "    c,\n"
            "    t,\n"
            "    u,\n"
            ")\n",
        )
        return workspace, target

    def test_refactor_census_accepts_workspace_before_subcommand(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, _service_file = self._build_centralize_workspace(tmp_path)
        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
        )
        assert result == 0

    def test_refactor_centralize_accepts_shared_flags_before_subcommand(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, service_file = self._build_centralize_workspace(tmp_path)
        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "--apply",
            "centralize-pydantic",
        )
        assert result == 0
        assert service_file.with_name("_models.py").exists()
        assert service_file.with_suffix(".py.bak").exists()

    def test_refactor_runtime_alias_imports_accepts_shared_flags_before_subcommand(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, target = self._build_runtime_alias_workspace(tmp_path)
        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "--projects",
            "flext-demo",
            "--apply",
            "migrate-runtime-alias-imports",
            "--aliases",
            "r,s",
        )
        assert result == 0
        rewritten = target.read_text(encoding="utf-8")
        assert "from flext_core import r, s" not in rewritten
        assert rewritten.count("from flext_demo import") == 1
        assert target.with_suffix(".py.bak").exists()
