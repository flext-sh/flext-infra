"""Focused public-route E2E for portable cProfile supervision."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, main as infra_main
from flext_tests import tm


def test_cprofile_run_creates_real_bounded_artifacts(tmp_path: Path) -> None:
    """Route config-owned defaults through a real supervised subprocess."""
    policy = config.Infra.codegen.make.cprofile
    report_root = tmp_path / ".reports" / "cprofile"
    profile = report_root / "e2e.prof"
    report = report_root / "e2e.txt"
    arguments = tuple(f"--arguments={argument}" for argument in policy.default_args)

    exit_code = infra_main([
        "validate",
        "cprofile-run",
        "--workspace",
        str(tmp_path),
        "--profile-module",
        policy.target,
        *arguments,
        "--profile",
        str(profile),
        "--output",
        str(report),
        "--sort",
        policy.sort_by,
        "--limit",
        "5",
        "--timeout-seconds",
        str(policy.timeout_seconds),
    ])

    tm.that(exit_code, eq=0)
    tm.that(profile.is_file(), eq=True)
    tm.that(profile.stat().st_size, gt=0)
    rendered = report.read_text(encoding="utf-8")
    tm.that(rendered, has="function calls")
    tm.that(rendered, has="Ordered by:")
