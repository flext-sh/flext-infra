"""Tests for the catalog-driven declarative enforcement engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_core import FlextModelsEnforcement, FlextUtilitiesEnforcement
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
)
from flext_infra.models import m
from flext_infra.refactor.census import FlextInfraRefactorCensus
from flext_infra.refactor.declarative_enforcement import (
    FlextInfraRefactorDeclarativeEnforcement,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.typings import t


class TestsFlextInfraRefactorDeclarativeEnforcement:
    """Root-cause coverage for declarative detection strategies."""

    @staticmethod
    def _rule(rule_id: str) -> FlextModelsEnforcement.EnforcementRuleSpec:
        catalog = FlextUtilitiesEnforcement.build_canonical_catalog()
        return next(rule for rule in catalog.enabled_rules() if rule.id == rule_id)

    @staticmethod
    def _ctx(
        rope_project: t.Infra.RopeProject,
        file_path: Path,
    ) -> m.Infra.DetectorContext:
        return m.Infra.DetectorContext(
            file_path=file_path,
            rope_project=rope_project,
            project_name="demo",
            project_root=file_path.parent,
        )

    def test_stub_file_detection(self, tmp_path: Path) -> None:
        """ENFORCE-090 probe is emitted for ``.pyi`` files."""
        stub = tmp_path / "demo.pyi"
        stub.write_text("x: int\n", encoding="utf-8")
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-090"),
                self._ctx(rope_project, stub),
            )
        assert len(probes) == 1
        assert getattr(probes[0], "file_path", "") == str(stub)
        assert getattr(probes[0], "rule_id", "") == "090"

    def test_supported_rules_are_selected_by_source_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """Declarative support is source-driven, not tied to catalog IDs."""
        rule = FlextModelsEnforcement.EnforcementRuleSpec(
            id="ENFORCE-999",
            description="Synthetic stub-file rule",
            severity=FlextModelsEnforcement.EnforcementRuleSeverity.HIGH,
            source=FlextModelsEnforcement.EnforcementInfraDetectorSource(
                violation_field="stub_file_violations",
            ),
        )
        stub = tmp_path / "demo.pyi"
        stub.write_text("x: int\n", encoding="utf-8")
        assert FlextInfraRefactorDeclarativeEnforcement.supports(rule)
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                rule,
                self._ctx(rope_project, stub),
            )
        assert len(probes) == 1
        assert getattr(probes[0], "file_path", "") == str(stub)

    def test_magic_literal_in_function_body(self, tmp_path: Path) -> None:
        """ENFORCE-097 detects a bare integer inside a function body."""
        source = tmp_path / "demo.py"
        source.write_text(
            "from __future__ import annotations\n\ndef f() -> int:\n    return 42\n",
            encoding="utf-8",
        )
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-097"),
                self._ctx(rope_project, source),
            )
        assert len(probes) == 1
        assert getattr(probes[0], "line", 0) == 4
        assert getattr(probes[0], "rule_id", "") == "097"

    def test_magic_literal_skips_default_arg(self, tmp_path: Path) -> None:
        """Default argument values are exempt from magic-literal detection."""
        source = tmp_path / "demo.py"
        source.write_text(
            "from __future__ import annotations\n\ndef f(x: int = 42) -> int:\n    return x\n",
            encoding="utf-8",
        )
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-097"),
                self._ctx(rope_project, source),
            )
        assert len(probes) == 0

    def test_magic_literal_skips_type_annotation(self, tmp_path: Path) -> None:
        """Type annotations are exempt from magic-literal detection."""
        source = tmp_path / "demo.py"
        source.write_text(
            "from __future__ import annotations\n\nLITERAL: str = 'ok'\n",
            encoding="utf-8",
        )
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-097"),
                self._ctx(rope_project, source),
            )
        assert len(probes) == 0

    def test_magic_literal_skips_module_level_assignment(self, tmp_path: Path) -> None:
        """Module-level assignments are the canonical constant location."""
        source = tmp_path / "demo.py"
        source.write_text(
            "from __future__ import annotations\n\nMAGIC = 42\n",
            encoding="utf-8",
        )
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-097"),
                self._ctx(rope_project, source),
            )
        assert len(probes) == 0

    def test_classvar_constant_detection(self, tmp_path: Path) -> None:
        """ENFORCE-079 delegates to the class-placement detector."""
        source = tmp_path / "consumer.py"
        source.write_text(
            "from typing import ClassVar\n"
            "class PlainClass:\n"
            "    GROUPS: ClassVar[frozenset[str]] = frozenset({'a'})\n",
            encoding="utf-8",
        )
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-079"),
                self._ctx(rope_project, source),
            )
        assert len(probes) == 1
        assert getattr(probes[0], "object_name", "") == "GROUPS"
        assert getattr(probes[0], "rule_id", "") == "079"

    def test_missing_rope_resource_fails_loud(self, tmp_path: Path) -> None:
        """Missing source resources are detector failures, not clean scans."""
        missing = tmp_path / "missing.py"
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            with pytest.raises(RuntimeError, match="unable to resolve rope resource"):
                FlextInfraRefactorDeclarativeEnforcement.detect(
                    self._rule("ENFORCE-097"),
                    self._ctx(rope_project, missing),
                )

    def test_classvar_detector_failure_fails_loud(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Class-placement detector failures propagate to the orchestrator."""
        source = tmp_path / "consumer.py"
        source.write_text("from typing import ClassVar\n", encoding="utf-8")

        def _fail(
            ctx: m.Infra.DetectorContext,
        ) -> t.SequenceOf[m.Infra.ClassPlacementViolation]:
            _ = ctx
            msg = "class placement exploded"
            raise RuntimeError(msg)

        monkeypatch.setattr(FlextInfraClassPlacementDetector, "detect_file", _fail)
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            with pytest.raises(RuntimeError, match="class placement detector failed"):
                FlextInfraRefactorDeclarativeEnforcement.detect(
                    self._rule("ENFORCE-079"),
                    self._ctx(rope_project, source),
                )

    def test_foreign_canonical_alias_detection(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ENFORCE-080 detects a canonical alias imported from flext_core."""
        source = tmp_path / "src" / "demo_pkg" / "consumer.py"
        source.parent.mkdir(parents=True)
        source.write_text(
            "from __future__ import annotations\nfrom flext_core import c\n",
            encoding="utf-8",
        )
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "demo_pkg"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "flext_infra.constants.c.ENFORCEMENT_PROJECT_ALIAS_OWNERS",
            {"demo_pkg": ("c", "m", "p", "t", "u")},
        )
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            ctx = self._ctx(rope_project, source)
            ctx.project_name = "demo_pkg"
            probes = FlextInfraRefactorDeclarativeEnforcement.detect(
                self._rule("ENFORCE-080"),
                ctx,
            )
        assert len(probes) == 1
        assert getattr(probes[0], "object_name", "") == "c"
        assert getattr(probes[0], "rule_id", "") == "080"

    def test_unsupported_source_fails_loud(self, tmp_path: Path) -> None:
        rule = FlextModelsEnforcement.EnforcementRuleSpec(
            id="ENFORCE-999",
            description="Unsupported declarative source",
            severity=FlextModelsEnforcement.EnforcementRuleSeverity.HIGH,
            source=FlextModelsEnforcement.EnforcementRuntimeWarningSource(
                category="UserWarning",
            ),
        )
        source = tmp_path / "consumer.py"
        source.write_text("", encoding="utf-8")
        assert not FlextInfraRefactorDeclarativeEnforcement.supports(rule)
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            with pytest.raises(ValueError, match="unsupported declarative"):
                FlextInfraRefactorDeclarativeEnforcement.detect(
                    rule,
                    self._ctx(rope_project, source),
                )


class TestsFlextInfraRefactorDeclarativeEnforcementInCensus:
    """Declarative rules surface in the census report."""

    @staticmethod
    def _build_workspace(tmp_path: Path, project_name: str) -> Path:
        workspace = tmp_path / "workspace"
        src = workspace / "src" / project_name
        src.mkdir(parents=True)
        (src / "__init__.py").write_text(
            "from __future__ import annotations\n",
            encoding="utf-8",
        )
        (workspace / "pyproject.toml").write_text(
            f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        return workspace

    def test_census_reports_enforce_079_classvar_constant(
        self,
        tmp_path: Path,
    ) -> None:
        """ENFORCE-079 appears in the census when classvar_constant is selected."""
        workspace = self._build_workspace(tmp_path, "demo_pkg")
        source = workspace / "src" / "demo_pkg" / "domain.py"
        source.write_text(
            "from __future__ import annotations\n"
            "from typing import ClassVar\n\n"
            "class DemoService:\n"
            "    GROUPS: ClassVar[frozenset[str]] = frozenset({'a'})\n",
            encoding="utf-8",
        )

        report_result = FlextInfraRefactorCensus(
            workspace_root=workspace,
            include_local_scopes=False,
            rules=("ENFORCE-079",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert len(violations) == 1
        assert violations[0].kind == "classvar_constant"
        assert violations[0].object_name == "GROUPS"
        assert violations[0].fix_action == "classvar_relocation"
        assert violations[0].fixable

    def test_census_reports_enforce_090_stub_file(
        self,
        tmp_path: Path,
    ) -> None:
        """ENFORCE-090 appears in the census for prohibited ``.pyi`` files."""
        workspace = self._build_workspace(tmp_path, "demo_pkg")
        stub = workspace / "src" / "demo_pkg" / "service.pyi"
        stub.write_text("x: int\n", encoding="utf-8")

        report_result = FlextInfraRefactorCensus(
            workspace_root=workspace,
            include_local_scopes=False,
            rules=("ENFORCE-090",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert len(violations) == 1
        assert violations[0].kind == "stub_file"
        assert violations[0].fix_action == "remove_stub_file"
        assert violations[0].fixable

    def test_census_apply_enforce_090_removes_stub_file(
        self,
        tmp_path: Path,
    ) -> None:
        """ENFORCE-090 apply removes the reported ``.pyi`` file."""
        workspace = self._build_workspace(tmp_path, "demo_pkg")
        stub = workspace / "src" / "demo_pkg" / "service.pyi"
        stub.write_text("x: int\n", encoding="utf-8")

        dry_run_result = FlextInfraRefactorCensus(
            workspace_root=workspace,
            apply_changes=True,
            dry_run=True,
            include_local_scopes=False,
            rules=("ENFORCE-090",),
        ).execute()

        assert dry_run_result.success, dry_run_result.error
        assert stub.exists()

        apply_result = FlextInfraRefactorCensus(
            workspace_root=workspace,
            apply_changes=True,
            include_local_scopes=False,
            rules=("ENFORCE-090",),
        ).execute()

        assert apply_result.success, apply_result.error
        assert not stub.exists()

    def test_census_reports_enforce_097_magic_literal(
        self,
        tmp_path: Path,
    ) -> None:
        """ENFORCE-097 appears in the census for magic literals."""
        workspace = self._build_workspace(tmp_path, "demo_pkg")
        source = workspace / "src" / "demo_pkg" / "service.py"
        source.write_text(
            "from __future__ import annotations\n\n"
            "def compute() -> int:\n"
            "    return 42\n",
            encoding="utf-8",
        )

        report_result = FlextInfraRefactorCensus(
            workspace_root=workspace,
            include_local_scopes=False,
            rules=("ENFORCE-097",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert len(violations) == 1
        assert violations[0].kind == "magic_literal"
        assert violations[0].fix_action == "extract_magic_literal"
        assert not violations[0].fixable

    def test_census_reports_enforce_080_foreign_canonical_alias(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ENFORCE-080 appears in the census for foreign canonical aliases."""
        workspace = self._build_workspace(tmp_path, "demo_pkg")
        source = workspace / "src" / "demo_pkg" / "service.py"
        source.write_text(
            "from __future__ import annotations\nfrom flext_core import c\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "flext_infra.constants.c.ENFORCEMENT_PROJECT_ALIAS_OWNERS",
            {"demo_pkg": ("c", "m", "p", "t", "u")},
        )

        report_result = FlextInfraRefactorCensus(
            workspace_root=workspace,
            include_local_scopes=False,
            rules=("ENFORCE-080",),
        ).execute()

        assert report_result.success, report_result.error
        report = report_result.unwrap()
        violations = [
            violation for project in report.projects for violation in project.violations
        ]
        assert len(violations) == 1
        assert violations[0].kind == "foreign_canonical_alias"
        assert violations[0].object_name == "c"
        assert violations[0].fix_action == "rewrite_foreign_canonical_alias"
        assert violations[0].fixable
