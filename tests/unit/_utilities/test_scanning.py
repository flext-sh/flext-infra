from __future__ import annotations

from pathlib import Path

from flext_infra import c, m


class TestScanModels:
    def test_scan_violation_model_fields(self) -> None:
        violation = m.Infra.ScanViolation(
            line=42,
            message="forbidden import",
            severity="high",
            rule_id="FLEXT001",
        )

        assert violation.line == 42
        assert violation.message == "forbidden import"
        assert violation.severity == "high"
        assert violation.rule_id == "FLEXT001"

    def test_scan_result_model_fields_and_defaults(self, tmp_path: Path) -> None:
        result = m.Infra.ScanResult(
            file_path=tmp_path / "sample.py",
            detector_name="scanner-x",
            violations=[],
        )
        payload = result.model_dump()

        assert result.file_path == tmp_path / "sample.py"
        assert result.detector_name == "scanner-x"
        assert payload["violations"] == []

    def test_scan_result_with_violations(self, tmp_path: Path) -> None:
        violation = m.Infra.ScanViolation(
            line=7,
            message="rule hit",
            severity="medium",
            rule_id=None,
        )
        result = m.Infra.ScanResult(
            file_path=tmp_path / "violating.py",
            detector_name="scanner-y",
            violations=[violation],
        )
        payload = result.model_dump()

        violations = payload["violations"]
        assert len(violations) == 1
        assert violations[0]["message"] == "rule hit"
        assert violations[0]["rule_id"] is None
        assert c.Cli.GIT == "git"
