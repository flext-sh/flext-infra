"""Focused cProfile report service contracts."""

from __future__ import annotations

import cProfile
import sys
from pathlib import Path

import pytest

from flext_infra import c, config, p, r, t, u
from flext_infra.services.cli_routes_validate_commands import ValidationCommandRoutes
from flext_infra.validate.cprofile_report import (
    FlextInfraCProfileReport,
    FlextInfraCProfileRun,
)
from flext_tests import tm


class TestsFlextInfraCProfileReport:
    """Prove real pstats artifacts render through the typed owner."""

    def test_real_profile_renders_bounded_text(self, tmp_path: Path) -> None:
        policy = config.Infra.tooling.tools.pytest
        report_dir = tmp_path / ".reports" / "tests" / "profile"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / "profile.pstats"
        output_path = report_dir / "profile.txt"
        profiler = cProfile.Profile()
        profiler.enable()
        _ = sum(range(10))
        profiler.disable()
        profiler.dump_stats(profile_path)
        service = FlextInfraCProfileReport(
            workspace=tmp_path,
            profile=profile_path,
            output=output_path,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        )

        tm.ok(service.execute())

        tm.that(output_path.read_text(encoding="utf-8"), has="function calls")

    def test_validate_route_uses_typed_profile_owner(self) -> None:
        routes = {
            route.name: route.model_cls
            for route in ValidationCommandRoutes.validate_command_routes
        }

        tm.that(routes["cprofile-report"], eq=FlextInfraCProfileReport)
        tm.that(routes["cprofile-run"], eq=FlextInfraCProfileRun)

    def test_run_profiles_exact_module_argv_including_imports(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        policy = config.Infra.tooling.tools.pytest
        report_dir = tmp_path / ".reports" / "tests" / "profile"
        profile_path = report_dir / "profile.pstats"
        output_path = report_dir / "profile.txt"
        log_path = report_dir / "profile.log"
        observed: list[tuple[str, ...]] = []

        def fake_run_to_file(
            command: t.StrSequence,
            output_file: t.Cli.TextPath,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            live: bool = False,
            deadline: p.Cli.ProcessDeadline | None = None,
        ) -> p.Result[int]:
            _ = (
                cwd,
                timeout,
                env,
                remove_env_keys,
                input_data,
                live,
                deadline,
            )
            observed.append(tuple(command))
            Path(output_file).write_text("profiled\n", encoding="utf-8")
            profiler = cProfile.Profile()
            profiler.enable()
            _ = sum(range(10))
            profiler.disable()
            profiler.dump_stats(profile_path)
            return r[int].ok(0)

        monkeypatch.setattr(u.Cli, "run_to_file", staticmethod(fake_run_to_file))
        service = FlextInfraCProfileRun(
            workspace=tmp_path,
            profile=profile_path,
            output=output_path,
            log=log_path,
            module="flext_infra",
            argument=("codegen", "conform", "--workspace", "."),
            timeout_seconds=policy.run_timeout_seconds,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        )

        tm.ok(service.execute())

        tm.that(
            observed,
            eq=[
                (
                    sys.executable,
                    "-m",
                    "cProfile",
                    "-o",
                    str(profile_path),
                    "-m",
                    "flext_infra",
                    "codegen",
                    "conform",
                    "--workspace",
                    ".",
                )
            ],
        )
        tm.that(output_path.read_text(encoding="utf-8"), has="function calls")

    def test_profile_artifacts_cannot_escape_workspace_reports(
        self, tmp_path: Path
    ) -> None:
        policy = config.Infra.tooling.tools.pytest

        with pytest.raises(c.ValidationError, match="cProfile path must stay under"):
            FlextInfraCProfileReport(
                workspace=tmp_path,
                profile=tmp_path / "outside.pstats",
                output=tmp_path / "outside.txt",
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            )
