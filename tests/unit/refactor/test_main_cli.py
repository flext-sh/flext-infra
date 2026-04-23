from __future__ import annotations

from pathlib import Path

import pytest

import flext_infra
from flext_infra import FlextInfraRefactorCensus, main as infra_main
from tests import u


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

    @staticmethod
    def _build_test_only_workspace(tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "service.py",
            "from __future__ import annotations\n\n"
            "def only_for_tests(value: int) -> int:\n"
            "    return value + 1\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "tests" / "test_service.py",
            "from __future__ import annotations\n\n"
            "from sample_pkg.service import only_for_tests\n\n"
            "def test_only_for_tests_returns_incremented_value() -> None:\n"
            "    assert only_for_tests(1) == 2\n",
        )
        return workspace

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

    def test_refactor_census_apply_fixes_missing_runtime_alias(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        module_path.write_text(
            (
                "from __future__ import annotations\n\n"
                '__all__: list[str] = ["FlextDemoModels"]\n\n'
                "class FlextDemoModels:\n"
                "    pass\n"
            ),
            encoding="utf-8",
        )

        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
            "--apply",
        )

        assert result == 0
        source = module_path.read_text(encoding="utf-8")
        assert '"m"' in source
        assert "m = FlextDemoModels" in source

    def test_refactor_census_no_longer_uses_legacy_visitors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        workspace, package_root = u.Infra.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        module_path = package_root / "models.py"
        u.Infra.Tests.write_lazy_init_namespace_module(
            module_path,
            class_name="FlextDemoModels",
            alias="m",
            docstring="Models.",
        )
        monkeypatch.setattr(
            flext_infra.FlextInfraCensusImportDiscoveryVisitor,
            "scan_source",
            lambda self, source: (_ for _ in ()).throw(RuntimeError("legacy visitor")),
        )
        monkeypatch.setattr(
            flext_infra.FlextInfraCensusUsageCollector,
            "scan_source",
            lambda self, source: (_ for _ in ()).throw(
                RuntimeError("legacy collector")
            ),
        )

        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
        )

        assert result == 0

    def test_refactor_census_flags_test_only_candidates(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_workspace(tmp_path)

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]

        assert report.test_only_count == 1
        assert report.removal_candidate_count >= report.test_only_count
        assert len(violations) == 1
        assert violations[0].kind == "test_only"
        assert violations[0].object_name == "only_for_tests"

        rendered = FlextInfraRefactorCensus.render_text(report)
        assert "Test-only: 1" in rendered
        assert "Removal candidates:" in rendered
