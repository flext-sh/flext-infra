from __future__ import annotations

from pathlib import Path

import pytest

import flext_infra
from flext_infra import FlextInfraRefactorCensus, main as infra_main
from tests import t, u


def _mapping(value: t.JsonValue | t.JsonMapping) -> t.JsonMapping:
    return t.Cli.JSON_MAPPING_ADAPTER.validate_python(value)


def _strings(value: t.JsonValue) -> t.StrSequence:
    return t.Infra.STR_SEQ_ADAPTER.validate_python(value)


class TestFlextInfraRefactorMainCli:
    @staticmethod
    def _refactor_main(*args: str) -> int:
        return infra_main(["refactor", *args])

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _write_workspace_pyproject(workspace: Path) -> None:
        TestFlextInfraRefactorMainCli._write(
            workspace / "pyproject.toml",
            "[project]\n"
            'name = "sample-pkg"\n'
            'version = "0.1.0"\n\n'
            "[tool.pyrefly]\n"
            "disable-project-excludes-heuristics = true\n"
            "project-excludes = []\n"
            'search-path = [".", "src"]\n',
        )

    @staticmethod
    def _build_basic_workspace(tmp_path: Path) -> tuple[Path, Path]:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
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
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
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

    @staticmethod
    def _build_lazy_init_cascade_workspace(
        tmp_path: Path,
    ) -> tuple[Path, Path, Path]:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
        init_path = workspace / "src" / "sample_pkg" / "__init__.py"
        TestFlextInfraRefactorMainCli._write(
            init_path,
            "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
            '"""Sample package."""\n\n'
            "from __future__ import annotations\n\n"
            "import typing as _t\n\n"
            "from flext_core.lazy import build_lazy_import_map, install_lazy_exports\n\n"
            "if _t.TYPE_CHECKING:\n"
            "    from sample_pkg.keep import keep_me\n"
            "    from sample_pkg.service import only_for_tests\n"
            "_LAZY_IMPORTS = build_lazy_import_map(\n"
            "    {\n"
            '        ".keep": ("keep_me",),\n'
            '        ".service": ("only_for_tests",),\n'
            "    },\n"
            ")\n\n"
            "install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)\n\n"
            "__all__: list[str] = [\n"
            '    "keep_me",\n'
            '    "only_for_tests",\n'
            "]\n",
        )
        service_file = workspace / "src" / "sample_pkg" / "service.py"
        TestFlextInfraRefactorMainCli._write(
            service_file,
            "from __future__ import annotations\n\n"
            '__all__: list[str] = ["only_for_tests"]\n\n'
            "def only_for_tests(value: int) -> int:\n"
            "    return value + 1\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "keep.py",
            "from __future__ import annotations\n\n"
            '__all__: list[str] = ["keep_me"]\n\n'
            "def keep_me(value: int) -> int:\n"
            "    return value\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "tests" / "test_service.py",
            "from __future__ import annotations\n\n"
            "from sample_pkg.service import only_for_tests\n\n"
            "def test_only_for_tests_returns_incremented_value() -> None:\n"
            "    assert only_for_tests(1) == 2\n",
        )
        return workspace, service_file, init_path

    @staticmethod
    def _build_test_only_workspace_with_source_import(
        tmp_path: Path,
    ) -> tuple[Path, Path]:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        service_file = workspace / "src" / "sample_pkg" / "service.py"
        TestFlextInfraRefactorMainCli._write(
            service_file,
            "from __future__ import annotations\n"
            "from collections.abc import Sequence\n\n"
            "def only_for_tests(values: Sequence[int]) -> int:\n"
            "    return len(values)\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "tests" / "test_service.py",
            "from __future__ import annotations\n\n"
            "from sample_pkg.service import only_for_tests\n\n"
            "def test_only_for_tests_uses_sequence_signature() -> None:\n"
            "    assert only_for_tests([1, 2]) == 2\n",
        )
        return workspace, service_file

    @staticmethod
    def _build_test_only_method_workspace(tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "service.py",
            "from __future__ import annotations\n\n"
            "class Service:\n"
            "    def only_for_tests(self, value: int) -> int:\n"
            "        return value + 1\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "tests" / "test_service.py",
            "from __future__ import annotations\n\n"
            "from sample_pkg.service import Service\n\n"
            "def test_only_for_tests_method_returns_incremented_value() -> None:\n"
            "    assert Service().only_for_tests(1) == 2\n",
        )
        return workspace

    @staticmethod
    def _build_unused_nested_function_workspace(tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "service.py",
            "from __future__ import annotations\n\n"
            "def outer(value: int) -> int:\n"
            "    def only_for_cleanup(inner: int) -> int:\n"
            "        return inner + 1\n\n"
            "    return value\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "tests" / "test_service.py",
            "from __future__ import annotations\n\n"
            "from sample_pkg.service import outer\n\n"
            "OBSERVED_VALUE = outer(1)\n"
            "assert OBSERVED_VALUE == 1\n",
        )
        return workspace

    @staticmethod
    def _build_unused_top_level_workspace_with_source_import(
        tmp_path: Path,
    ) -> tuple[Path, Path]:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        service_file = workspace / "src" / "sample_pkg" / "service.py"
        TestFlextInfraRefactorMainCli._write(
            service_file,
            "from __future__ import annotations\n"
            "from collections.abc import Sequence\n\n"
            "def only_for_cleanup(values: Sequence[int]) -> int:\n"
            "    return len(values)\n",
        )
        return workspace, service_file

    @staticmethod
    def _build_unused_local_workspace(tmp_path: Path) -> Path:
        workspace = tmp_path / "workspace"
        TestFlextInfraRefactorMainCli._write_workspace_pyproject(workspace)
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "__init__.py",
            "from __future__ import annotations\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "src" / "sample_pkg" / "service.py",
            "from __future__ import annotations\n\n"
            "def outer(value: int) -> int:\n"
            "    only_for_cleanup = value + 1\n"
            "    return value\n",
        )
        TestFlextInfraRefactorMainCli._write(
            workspace / "tests" / "test_service.py",
            "from __future__ import annotations\n\n"
            "from sample_pkg.service import outer\n\n"
            "assert outer(1) == 1\n",
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

        assert report.unused_count == 0
        assert report.test_only_count == 1
        assert report.removal_candidate_count == 1
        assert len(report.removal_candidates) == 1
        assert len(violations) == 1
        assert violations[0].kind == "test_only"
        assert violations[0].object_name == "only_for_tests"
        candidate = report.removal_candidates[0]
        assert candidate.reason == "test_only"
        assert candidate.suggested_action == "delete_object_and_test_references"
        assert len(candidate.test_reference_sites) == 2
        assert sorted(site.line for site in candidate.test_reference_sites) == [3, 6]

        rendered = FlextInfraRefactorCensus.render_text(report)
        assert "Test-only: 1" in rendered
        assert "Removal candidates:" in rendered
        assert "Candidate preview:" in rendered

    def test_refactor_census_apply_removes_simple_test_only_candidate(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_workspace(tmp_path)
        service_file = workspace / "src" / "sample_pkg" / "service.py"
        test_file = workspace / "tests" / "test_service.py"

        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
            "--apply",
            "--rules",
            "test_only",
            "--kinds",
            "function",
        )

        assert result == 0
        service_source = service_file.read_text(encoding="utf-8")
        test_source = test_file.read_text(encoding="utf-8")
        assert "only_for_tests" not in service_source
        assert "only_for_tests" not in test_source
        assert u.Infra.parse_source_ast(service_source) is not None
        assert u.Infra.parse_source_ast(test_source) is not None

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.test_only_count == 0
        assert report.removal_candidate_count == 0

    def test_refactor_census_apply_cascades_through_init_lazy_map_and_all(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, service_file, init_path = self._build_lazy_init_cascade_workspace(
            tmp_path,
        )
        test_file = workspace / "tests" / "test_service.py"

        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
            "--apply",
            "--rules",
            "test_only",
            "--kinds",
            "function",
        )

        assert result == 0
        init_source = init_path.read_text(encoding="utf-8")
        service_source = service_file.read_text(encoding="utf-8")
        test_source = test_file.read_text(encoding="utf-8")

        assert "only_for_tests" not in init_source
        assert "only_for_tests" not in service_source
        assert "only_for_tests" not in test_source
        assert "keep_me" in init_source
        assert ".service" not in init_source
        assert u.Infra.parse_source_ast(init_source) is not None
        assert u.Infra.parse_source_ast(service_source) is not None
        assert u.Infra.parse_source_ast(test_source) is not None

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.test_only_count == 0
        assert report.removal_candidate_count == 0

    def test_refactor_census_apply_removes_unused_top_level_and_cleans_imports(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, service_file = (
            self._build_unused_top_level_workspace_with_source_import(tmp_path)
        )

        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
            "--apply",
            "--rules",
            "unused",
            "--kinds",
            "function",
        )

        assert result == 0
        service_source = service_file.read_text(encoding="utf-8")
        assert "def only_for_cleanup" not in service_source
        assert "from collections.abc import Sequence" not in service_source
        assert u.Infra.parse_source_ast(service_source) is not None

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            include_local_scopes=False,
            kinds=("function",),
            rules=("unused",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.unused_count == 0
        assert report.removal_candidate_count == 0

    def test_refactor_census_dry_run_validates_candidate_after_import_cleanup(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, service_file = self._build_test_only_workspace_with_source_import(
            tmp_path,
        )

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.test_only_count == 1
        assert report.removal_candidate_count == 1
        assert report.removal_candidates[0].object_name == "only_for_tests"
        service_source = service_file.read_text(encoding="utf-8")
        assert "from collections.abc import Sequence" in service_source
        assert "def only_for_tests" in service_source

    def test_refactor_census_apply_dry_run_does_not_mutate_files(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_workspace(tmp_path)
        service_file = workspace / "src" / "sample_pkg" / "service.py"
        test_file = workspace / "tests" / "test_service.py"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            apply_changes=True,
            dry_run=True,
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.test_only_count == 1
        assert report.removal_candidate_count == 1
        assert "only_for_tests" in service_file.read_text(encoding="utf-8")
        assert "only_for_tests" in test_file.read_text(encoding="utf-8")

    def test_refactor_census_dry_run_excludes_unsupported_method_candidate(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_method_workspace(tmp_path)
        impact_map_path = tmp_path / "method-impact-map.json"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            impact_map_output=str(impact_map_path),
            include_local_scopes=True,
            kinds=("method",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert report.test_only_count == 1
        assert report.removal_candidate_count == 0
        assert len(report.removal_candidates) == 0
        assert len(violations) == 1
        assert violations[0].kind == "test_only"
        assert violations[0].object_kind == "method"
        assert violations[0].object_name == "only_for_tests"

        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        assert len(files) == 0

    def test_refactor_census_dry_run_excludes_unsupported_nested_unused_function(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_unused_nested_function_workspace(tmp_path)
        impact_map_path = tmp_path / "nested-unused-impact-map.json"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            impact_map_output=str(impact_map_path),
            include_local_scopes=True,
            kinds=("function",),
            rules=("unused",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert report.unused_count == 1
        assert report.removal_candidate_count == 0
        assert len(report.removal_candidates) == 0
        assert len(violations) == 1
        assert violations[0].kind == "unused"
        assert violations[0].object_kind == "function"
        assert violations[0].object_name == "only_for_cleanup"

        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        assert len(files) == 0

    def test_refactor_census_dry_run_validates_unused_candidate_after_import_cleanup(
        self,
        tmp_path: Path,
    ) -> None:
        workspace, service_file = (
            self._build_unused_top_level_workspace_with_source_import(tmp_path)
        )
        impact_map_path = tmp_path / "unused-impact-map.json"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            impact_map_output=str(impact_map_path),
            include_local_scopes=False,
            kinds=("function",),
            rules=("unused",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.unused_count == 1
        assert report.removal_candidate_count == 1
        candidate = report.removal_candidates[0]
        assert candidate.object_name == "only_for_cleanup"
        assert candidate.reason == "unused"
        assert candidate.suggested_action == "delete_object_definition"
        service_source = service_file.read_text(encoding="utf-8")
        assert "from collections.abc import Sequence" in service_source
        assert "def only_for_cleanup" in service_source

        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        entries = [_mapping(item) for item in files]

        assert len(entries) == 1
        service_entry = entries[0]
        assert service_entry["modified"] is True
        assert service_entry["success"] is True
        assert list(_strings(service_entry["changes"])) == [
            "delete_object_definition: only_for_cleanup (unused)"
        ]

    def test_refactor_census_dry_run_excludes_unsupported_local_unused_object(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_unused_local_workspace(tmp_path)
        impact_map_path = tmp_path / "local-unused-impact-map.json"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            impact_map_output=str(impact_map_path),
            include_local_scopes=True,
            kinds=("local",),
            rules=("unused",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert report.unused_count == 1
        assert report.removal_candidate_count == 0
        assert len(report.removal_candidates) == 0
        assert len(violations) == 1
        assert violations[0].kind == "unused"
        assert violations[0].object_kind == "local"
        assert violations[0].object_name == "only_for_cleanup"

        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        assert len(files) == 0

    def test_refactor_census_writes_impact_map_for_removal_candidates(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_workspace(tmp_path)
        impact_map_path = tmp_path / "impact-map.json"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            impact_map_output=str(impact_map_path),
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        entries = [_mapping(item) for item in files]

        assert len(entries) == 2
        service_path = str((workspace / "src" / "sample_pkg" / "service.py").resolve())
        test_path = str((workspace / "tests" / "test_service.py").resolve())
        service_entry = next(item for item in entries if item["path"] == service_path)
        test_entry = next(item for item in entries if item["path"] == test_path)

        assert service_entry["modified"] is True
        assert service_entry["success"] is True
        assert list(_strings(service_entry["changes"])) == [
            "delete_object_and_test_references: only_for_tests (test_only)"
        ]
        assert test_entry["modified"] is True
        assert test_entry["success"] is True
        assert list(_strings(test_entry["changes"])) == [
            "remove reference to only_for_tests at line 3 (tests)",
            "remove reference to only_for_tests at line 6 (tests)",
        ]

    def test_refactor_census_cli_writes_impact_map_for_removal_candidates(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_workspace(tmp_path)
        impact_map_path = tmp_path / "cli-impact-map.json"

        result = self._refactor_main(
            "--workspace",
            str(workspace),
            "census",
            "--rules",
            "test_only",
            "--kinds",
            "function",
            "--impact-map-output",
            str(impact_map_path),
        )

        assert result == 0
        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        entries = [_mapping(item) for item in files]

        assert len(entries) == 2

    def test_refactor_census_apply_preserves_impact_map_plan(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._build_test_only_workspace(tmp_path)
        impact_map_path = tmp_path / "apply-impact-map.json"

        report_result = FlextInfraRefactorCensus(
            workspace=workspace,
            impact_map_output=str(impact_map_path),
            apply_changes=True,
            include_local_scopes=False,
            kinds=("function",),
            rules=("test_only",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        assert report.test_only_count == 0
        assert report.removal_candidate_count == 0

        payload_result = u.Cli.json_read(impact_map_path)
        assert payload_result.success, payload_result.error
        payload = _mapping(payload_result.unwrap())
        files = t.Cli.JSON_LIST_ADAPTER.validate_python(payload["files"])
        entries = [_mapping(item) for item in files]

        assert len(entries) == 2
