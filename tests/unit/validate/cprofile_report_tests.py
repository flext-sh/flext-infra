"""Focused cProfile report service contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.services import FlextInfraValidationCommandRoutes
from flext_infra.validate import FlextInfraCProfileReport
from tests import c, m, t, tm, u


class TestsFlextInfraCProfileReport:
    """Prove real pstats artifacts render through the typed owner."""

    @staticmethod
    @pytest.mark.parametrize(
        "arguments",
        [("--help",), ("validate", "cprofile-report", "--invalid-profile-option")],
    )
    def test_profile_publication_failure_preserves_the_native_cli_status(
        tmp_path: Path, arguments: t.StrTuple
    ) -> None:
        """A real invalid parent cannot replace a failing CLI's returned status."""
        blocked = tmp_path / "blocked-parent"
        blocked.write_text("not a directory\n", encoding=c.DEFAULT_ENCODING)
        reference = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-m", "flext_infra", *arguments), cwd=tmp_path
            )
        )
        profiled = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra._profile_entry",
                    str(blocked / "profile.pstats"),
                    *arguments,
                ),
                cwd=tmp_path,
            )
        )
        tm.that(profiled.stdout, eq=reference.stdout)
        tm.that(profiled.stderr, has="NotADirectoryError")
        tm.that(profiled.stderr, has=str(blocked))
        if u.Cli.process_succeeded(reference.outcome):
            tm.that(u.Cli.process_succeeded(profiled.outcome), eq=False)
        else:
            tm.that(
                profiled.outcome.raw_return_code, eq=reference.outcome.raw_return_code
            )

    @staticmethod
    def test_profile_publication_failure_keeps_the_original_cli_exception(
        tmp_path: Path,
    ) -> None:
        """A closed native stdout raises first; a real flush failure remains a note."""
        blocked = tmp_path / "blocked-parent"
        blocked.write_text("not a directory\n", encoding=c.DEFAULT_ENCODING)
        consumer = (
            "import runpy, sys\n"
            "from flext_cli import cli\n"
            "from flext_infra import main\n"
            "sys.stdout.close()\n"
            "module = sys.argv[1]\n"
            "sys.argv = sys.argv[1:]\n"
            "runpy.run_module(module, run_name='__main__')\n"
        )
        reference = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", consumer, "flext_infra", "--help"),
                cwd=tmp_path,
            )
        )
        profiled = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    consumer,
                    "flext_infra._profile_entry",
                    str(blocked / "profile.pstats"),
                    "--help",
                ),
                cwd=tmp_path,
            )
        )
        tm.that(u.Cli.process_succeeded(reference.outcome), eq=False)
        tm.that(
            profiled.outcome.raw_return_code,
            eq=reference.outcome.raw_return_code,
            msg=reference.stderr + profiled.stderr,
        )
        tm.that(reference.stderr, lacks="KeyboardInterrupt")
        for executed in (reference, profiled):
            tm.that(executed.outcome.timed_out, eq=False)
            tm.that(executed.outcome.forwarded_signal, eq=None)
        tm.that(reference.stderr, has="ValueError: I/O operation on closed file.")
        primary_trace, secondary_trace = profiled.stderr.split(
            "profile publication failed:\n", maxsplit=1
        )
        tm.that(primary_trace, has="ValueError: I/O operation on closed file.")
        tm.that(primary_trace, lacks="NotADirectoryError")
        tm.that(secondary_trace, has="NotADirectoryError")
        tm.that(secondary_trace, has=str(blocked))

    @staticmethod
    @pytest.mark.parametrize("inventory_only", [False, True])
    def test_real_profile_renders_bounded_text(
        tmp_path: Path,
        *,
        inventory_only: bool,
    ) -> None:
        """Test real profile renders bounded text."""
        policy = config.Infra.tooling.tools.pytest
        repository_root = tmp_path / "project[scope]"
        report_dir = repository_root / ".reports" / "tests" / "profile"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / "profile.pstats"
        output_path = report_dir / "profile.txt"
        profile_target = repository_root / "profile_target.py"
        profile_target.write_text("_ = sum(range(10))\n", encoding="utf-8")
        profiled = u.Cli.run_checked(
            [
                sys.executable,
                "-m",
                "cProfile",
                "-o",
                str(profile_path),
                str(profile_target),
            ],
            cwd=repository_root,
        )
        tm.ok(profiled)
        context = m.Infra.PytestRunContext(
            execution_mode=c.Infra.PytestExecutionMode.INCREMENTAL,
            testmon_db=None,
            deadline_monotonic=None,
            report_directory=report_dir,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                report_dir / "run-context.json",
                context.model_dump_json(),
            ),
        )
        receipt = context.model_copy(
            update={"profile_sha256": u.Cli.sha256_bytes(profile_path.read_bytes())},
        )
        parent_receipt = profile_path.with_suffix(".pstats.json")
        tm.ok(u.Cli.atomic_write_text_file(parent_receipt, receipt.model_dump_json()))
        inventory = report_dir / c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME
        selection = report_dir / c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
        for collection in (inventory,) if inventory_only else (selection, inventory):
            collection.write_bytes(profile_path.read_bytes())
            tm.ok(
                u.Cli.atomic_write_text_file(
                    collection.with_suffix(".pstats.json"),
                    receipt.model_dump_json(),
                ),
            )
        plan = m.Infra.PytestSelectionPlan(
            manifest_path=(inventory if inventory_only else selection).with_suffix(
                ".json",
            ),
            node_ids=(),
            whole_target=True,
            inventory_collected=True,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                report_dir / "selection-plan.json",
                plan.model_dump_json(),
            ),
        )

        result = FlextInfraCProfileReport(
            repository_root=repository_root,
            profile=profile_path,
            output=output_path,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
            run_receipt=parent_receipt,
        ).execute()

        tm.ok(result)
        tm.that(output_path.read_text(encoding="utf-8"), has="function calls")
        rendered = output_path.read_text(encoding="utf-8")
        tm.that(rendered, has=f"{profile_target}:1(<module>)")
        tm.that(rendered.count(f"Profile: {inventory}\n"), eq=1)
        tm.that(
            rendered.count(f"Profile: {selection}\n"), eq=0 if inventory_only else 1
        )

    @staticmethod
    def test_validate_route_uses_typed_profile_owner() -> None:
        """Test validate route uses typed profile owner."""
        routes = {
            route.name: route.model_cls
            for route in FlextInfraValidationCommandRoutes.validate_command_routes
        }

        tm.that(routes["cprofile-report"], eq=FlextInfraCProfileReport)

    @staticmethod
    def test_profile_artifacts_cannot_escape_workspace_reports(
        tmp_path: Path,
    ) -> None:
        """Test profile artifacts cannot escape workspace reports."""
        policy = config.Infra.tooling.tools.pytest

        with pytest.raises(ValueError, match="cProfile path must stay under"):
            FlextInfraCProfileReport(
                repository_root=tmp_path,
                profile=tmp_path / "outside.pstats",
                output=tmp_path / "outside.txt",
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            )
