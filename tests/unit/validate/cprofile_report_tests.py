"""Focused cProfile report service contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import cProfile
import io
import pstats
import sys
from pathlib import Path

import pytest

from flext_infra import config, main, validate
from tests import c, m, t, tm, u


class TestsFlextInfraCProfileReport:
    """Prove real pstats artifacts render through the typed owner."""

    @staticmethod
    @pytest.mark.parametrize("exit_code", [0, 1])
    @pytest.mark.parametrize("stage", ["selection", "inventory"])
    def test_selection_profile_without_plan_requires_failed_receipt(
        tmp_path: Path,
        exit_code: int,
        stage: str,
    ) -> None:
        """Render failed selection evidence without accepting an incomplete success."""
        directory = tmp_path / c.Infra.REPORTS_DIR_NAME / "selection"
        directory.mkdir(parents=True)
        profile = directory / "parent.pstats"
        measured = cProfile.Profile()
        measured.runcall(sum, range(3))
        measured.dump_stats(str(profile))
        selection = directory / (
            c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME
            if stage == "inventory"
            else c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
        )
        selection.write_bytes(profile.read_bytes())
        context = m.Infra.PytestRunContext(
            execution_mode=c.Infra.PytestExecutionMode.INCREMENTAL,
            testmon_db=None,
            deadline_monotonic=None,
            report_directory=directory,
        )
        (directory / "run-context.json").write_text(
            context.model_dump_json(),
            encoding=c.DEFAULT_ENCODING,
        )
        receipt = context.model_copy(
            update={
                "profile_sha256": u.Cli.sha256_bytes(profile.read_bytes()),
            }
        )
        for artifact in (profile, selection):
            artifact.with_suffix(".pstats.json").write_text(
                receipt.model_dump_json(),
                encoding=c.DEFAULT_ENCODING,
            )
        process = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", f"raise SystemExit({exit_code})"),
                cwd=tmp_path,
            )
        )
        (directory / f"{stage}-outcome.json").write_text(
            process.outcome.model_dump_json(),
            encoding=c.DEFAULT_ENCODING,
        )
        if stage == "inventory":
            selected = tm.ok(
                u.Cli.run_raw(
                    (sys.executable, "-c", "raise SystemExit(0)"),
                    cwd=tmp_path,
                )
            )
            (directory / "selection-outcome.json").write_text(
                selected.outcome.model_dump_json(),
                encoding=c.DEFAULT_ENCODING,
            )
        output = directory / "profile.txt"
        result = validate.FlextInfraCProfileReport(
            repository_root=tmp_path,
            profile=profile,
            output=output,
            sort=config.Infra.tooling.tools.pytest.profile_sort,
            limit=config.Infra.tooling.tools.pytest.profile_limit,
            run_receipt=profile.with_suffix(".pstats.json"),
        ).execute()
        if exit_code:
            tm.ok(result)
            tm.that(output.read_text(encoding=c.DEFAULT_ENCODING), has=str(selection))
        else:
            tm.fail(result)

    @staticmethod
    def test_cli_profiles_retain_each_run_and_measure_startup(tmp_path: Path) -> None:
        """Repeated public CLI launches preserve raw runs including CLI imports."""
        output = tmp_path / "profile.pstats"
        original: bytes | None = None
        for _ in range(2):
            tm.ok(
                u.Cli.run_checked(
                    (
                        sys.executable,
                        "-m",
                        "flext_infra._profile_entry",
                        str(output),
                        "--help",
                    ),
                    cwd=tmp_path,
                )
            )
            profiles = sorted(tmp_path.glob("profile-*.pstats"))
            if original is None:
                tm.that(len(profiles), eq=1)
                original = profiles[0].read_bytes()
            else:
                tm.that(len(profiles), eq=2)
                tm.ok(original in (path.read_bytes() for path in profiles))
                previous = tuple(tmp_path.glob("profile.previous-*.pstats"))
                tm.that(len(previous), eq=1)
                tm.that(previous[0].read_bytes(), eq=original)
            tm.that(
                output.read_bytes() in (path.read_bytes() for path in profiles), eq=True
            )
            for profile in profiles:
                rendered = io.StringIO()
                pstats.Stats(str(profile), stream=rendered).print_stats(
                    r"/flext_infra/cli\.py:\d+\(<module>\)"
                )
                tm.that(rendered.getvalue(), has="(<module>)")

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
            tm.fail(u.Cli.process_succeeded(profiled.outcome))
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
        tm.fail(u.Cli.process_succeeded(reference.outcome))
        tm.that(
            profiled.outcome.raw_return_code,
            eq=reference.outcome.raw_return_code,
            msg=reference.stderr + profiled.stderr,
        )
        tm.that(reference.stderr, lacks="KeyboardInterrupt")
        for executed in (reference, profiled):
            tm.fail(executed.outcome.timed_out)
            tm.that(executed.outcome.forwarded_signal, eq=None)
        tm.that(reference.stderr, has="ValueError: I/O operation on closed file.")
        primary_trace, secondary_trace = profiled.stderr.split(
            "profile publication failed:\n", maxsplit=1
        )
        tm.that(primary_trace, has="ValueError: I/O operation on closed file.")
        tm.that(primary_trace, lacks="NotADirectoryError")
        tm.that(secondary_trace, has="NotADirectoryError")
        tm.that(secondary_trace, has=str(blocked))
        tm.that(secondary_trace, lacks="ValueError: I/O operation on closed file.")

    @staticmethod
    def test_source_view_filters_before_its_row_limit(tmp_path: Path) -> None:
        """A busy external caller cannot hide captured repository functions."""
        root = tmp_path / "project"
        root.mkdir()
        owned = root / "owned_workload.py"
        owned.write_text(
            "class OwnedWorkload:\n"
            "    @staticmethod\n"
            "    def run():\n"
            "        return 'owned'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        external = tmp_path / "external"
        external.mkdir()
        driver = external / "driver.py"
        driver.write_text(
            "import sys\n"
            f"sys.path.insert(0, {str(root)!r})\n"
            "from owned_workload import OwnedWorkload\n"
            "for _ in range(5):\n"
            "    sum(range(100_000))\n"
            "OwnedWorkload.run()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        reports = root / c.Infra.REPORTS_DIR_NAME
        reports.mkdir()
        profile = reports / "workload.pstats"
        output = profile.with_suffix(".txt")
        tm.ok(
            u.Cli.run_checked(
                [
                    sys.executable,
                    "-m",
                    "cProfile",
                    "-o",
                    str(profile),
                    str(driver),
                ],
                cwd=external,
            ),
        )
        tm.ok(
            validate.FlextInfraCProfileReport(
                repository_root=root,
                profile=profile,
                output=output,
                sort="cumulative",
                limit=1,
            ).execute(),
        )
        full, source_report = output.read_text(encoding=c.DEFAULT_ENCODING).split(
            "Repository source functions:\n",
        )
        focused, callers = source_report.split("Repository source callers:\n")
        tm.that(full, lacks=str(owned))
        tm.that(focused, has=str(owned))
        tm.that(focused, lacks=str(driver))
        tm.that(callers, has=str(owned))

    @staticmethod
    @pytest.mark.parametrize("absolute_profile", [False, True])
    def test_entry_renders_member_profile_from_workspace_root(
        tmp_path: Path,
        *,
        absolute_profile: bool,
    ) -> None:
        """The real transport elects the member owning its report artifact."""
        workspace_name = "flext-profile-workspace"
        workspace, _ = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name=workspace_name,
            package_name=workspace_name.replace("-", "_"),
        )
        u.Tests.write_workspace_manifest(
            workspace,
            workspace_name,
            role=c.Infra.MakeProfile.WORKSPACE,
        )
        member_name = "flext-profile-consumer"
        member, _ = u.Tests.create_lazy_init_workspace(
            workspace,
            project_name=member_name,
            package_name=member_name.replace("-", "_"),
        )
        u.Tests.write_workspace_manifest(member, member_name)
        u.Tests.declare_workspace_projects(workspace, (member_name,))
        policy = config.Infra.tooling.tools.pytest
        report_dir = member / c.Infra.REPORTS_DIR_NAME / "profiles"
        report_dir.mkdir(parents=True)
        profile_path = report_dir / policy.profile_suite_filename
        profile_target = member / "profile_target.py"
        profile_target.write_text(
            "_ = sum(range(10))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    sys.executable,
                    "-m",
                    "cProfile",
                    "-o",
                    str(profile_path),
                    str(profile_target),
                ],
                cwd=workspace,
            ),
        )
        selected_profile = (
            profile_path if absolute_profile else profile_path.relative_to(workspace)
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    sys.executable,
                    "-m",
                    "flext_infra._cprofile_entry",
                    str(selected_profile),
                ],
                cwd=workspace,
            ),
        )
        rendered = profile_path.with_suffix(".txt").read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(rendered, has="function calls")

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

        result = validate.FlextInfraCProfileReport(
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
    def test_validate_route_exposes_profile_input(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The public CLI exposes the report owner's actual profile option."""
        tm.that(main(["validate", "cprofile-report", "--help"]), eq=0)
        tm.that(capsys.readouterr().out, has="--profile")

    @staticmethod
    def test_profile_artifacts_cannot_escape_workspace_reports(
        tmp_path: Path,
    ) -> None:
        """Test profile artifacts cannot escape workspace reports."""
        policy = config.Infra.tooling.tools.pytest

        with pytest.raises(ValueError, match="cProfile path must stay under"):
            validate.FlextInfraCProfileReport(
                repository_root=tmp_path,
                profile=tmp_path / "outside.pstats",
                output=tmp_path / "outside.txt",
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            )
