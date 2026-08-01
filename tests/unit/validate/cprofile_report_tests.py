"""Focused cProfile report service contracts."""

from __future__ import annotations

import marshal
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.services.cli_routes_validate_commands import ValidationCommandRoutes
from flext_infra.validate.cprofile_report import FlextInfraCProfileReport
from flext_tests import tm


class TestsFlextInfraCProfileReport:
    """Prove real pstats artifacts render through the typed owner."""

    def test_real_profile_renders_bounded_text(self, tmp_path: Path) -> None:
        policy = config.Infra.tooling.tools.pytest
        report_dir = tmp_path / ".reports" / "tests" / "profile"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / "profile.pstats"
        output_path = report_dir / "profile.txt"
        callers: dict[tuple[str, int, str], tuple[int, int, float, float]] = {}
        stats = {("tests/sample.py", 1, "sample"): (1, 1, 0.001, 0.001, callers)}
        profile_path.write_bytes(marshal.dumps(stats))

        result = FlextInfraCProfileReport(
            workspace_root=tmp_path,
            profile=profile_path,
            output=output_path,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        ).execute()

        tm.ok(result)
        tm.that(output_path.read_text(encoding="utf-8"), has="function calls")

    def test_validate_route_uses_typed_profile_owner(self) -> None:
        routes = {
            route.name: route.model_cls
            for route in ValidationCommandRoutes.validate_command_routes
        }

        tm.that(routes["cprofile-report"], eq=FlextInfraCProfileReport)

    def test_truncated_profile_returns_typed_failure(self, tmp_path: Path) -> None:
        policy = config.Infra.tooling.tools.pytest
        report_dir = tmp_path / ".reports" / "tests" / "profile"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / "profile.pstats.pending"
        output_path = report_dir / "profile.txt"
        profile_path.write_bytes(b"")

        result = FlextInfraCProfileReport(
            workspace_root=tmp_path,
            profile=profile_path,
            output=output_path,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        ).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="render cProfile report")
        tm.that(output_path.exists(), eq=False)

    def test_profile_artifacts_cannot_escape_workspace_reports(
        self, tmp_path: Path
    ) -> None:
        policy = config.Infra.tooling.tools.pytest

        with pytest.raises(ValueError, match="cProfile path must stay under"):
            FlextInfraCProfileReport(
                workspace_root=tmp_path,
                profile=tmp_path / "outside.pstats",
                output=tmp_path / "outside.txt",
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            )
