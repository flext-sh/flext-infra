"""Tests for the catalog-driven declarative enforcement engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_core import FlextModelsEnforcement, FlextUtilitiesEnforcement
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.detectors.class_placement_detector import (
    FlextInfraClassPlacementDetector,
)
from flext_infra.models import m
from flext_infra.refactor.declarative_enforcement import (
    FlextInfraRefactorDeclarativeEnforcement,
)
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

    def test_unsupported_source_fails_loud(self, tmp_path: Path) -> None:
        """Unsupported catalog wiring is a contract error, not an empty scan."""
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
        with FlextInfraUtilitiesRopeCore.open_project(tmp_path) as rope_project:
            with pytest.raises(ValueError, match="unsupported declarative"):
                FlextInfraRefactorDeclarativeEnforcement.detect(
                    rule,
                    self._ctx(rope_project, source),
                )
