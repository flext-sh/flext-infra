"""Focused cProfile report service contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import signal
import sys
from pathlib import Path

import pytest

from flext_infra import config, main, validate
from tests import c, m, tm, u


class TestsFlextInfraCProfileReport:
    """Prove real pstats artifacts render through the typed owner."""

    @staticmethod
    @pytest.mark.parametrize("suite_state", ["absent", "published", "stale"])
    def test_interrupted_suite_reports_native_outcome_before_artifacts(
        tmp_path: Path,
        native_cprofile: Path,
        capsys: pytest.CaptureFixture[str],
        suite_state: str,
    ) -> None:
        """Missing snapshots stay incomplete; present snapshots still require identity."""
        directory = tmp_path / c.Infra.REPORTS_DIR_NAME / "interrupted"
        directory.mkdir(parents=True)
        policy = config.Infra.tooling.tools.pytest
        profile = native_cprofile
        selection = directory / c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
        selection.write_bytes(profile.read_bytes())
        context = m.Infra.PytestRunContext(
            execution_mode=c.Infra.PytestExecutionMode.INCREMENTAL,
            testmon_db=tmp_path / "testmon",
            testmon_lease_acquired=True,
            deadline_monotonic=None,
            report_directory=directory,
        )
        (directory / "run-context.json").write_text(
            context.model_dump_json(), encoding=c.DEFAULT_ENCODING
        )
        receipt = context.model_copy(
            update={"profile_sha256": u.Cli.sha256_bytes(profile.read_bytes())}
        )
        for artifact in (profile, selection):
            artifact.with_suffix(".pstats.json").write_text(
                receipt.model_dump_json(), encoding=c.DEFAULT_ENCODING
            )
        plan = m.Infra.PytestSelectionPlan(
            manifest_path=selection.with_suffix(".json"),
            node_ids=("tests/test_workload.py::test_workload",),
            whole_target=True,
            inventory_collected=False,
        )
        (directory / "selection-plan.json").write_text(
            plan.model_dump_json(), encoding=c.DEFAULT_ENCODING
        )
        terminated = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "import os, signal; os.kill(os.getpid(), signal.SIGTERM)",
                ),
                cwd=tmp_path,
            )
        )
        tm.that(terminated.outcome.raw_return_code, eq=-signal.SIGTERM)
        (directory / "suite-outcome.json").write_text(
            terminated.outcome.model_dump_json(), encoding=c.DEFAULT_ENCODING
        )
        suite = directory / policy.profile_suite_filename
        if suite_state != "absent":
            suite.write_bytes(profile.read_bytes())
            suite.with_suffix(".pstats.json").write_text(
                (
                    receipt.model_copy(update={"profile_sha256": "0" * 64})
                    if suite_state == "stale"
                    else receipt
                ).model_dump_json(),
                encoding=c.DEFAULT_ENCODING,
            )
        output = directory / "profile.txt"
        result = validate.FlextInfraCProfileReport(
            repository_root=tmp_path,
            profile=profile,
            output=output,
            sort=policy.profile_sort,
            limit=policy.profile_limit,
            run_receipt=profile.with_suffix(".pstats.json"),
        ).execute()
        tm.that(capsys.readouterr().err, has=f"raw_return_code={-signal.SIGTERM}")
        if suite_state == "stale":
            tm.fail(result)
            tm.that(result.error, has="stale or mismatched")
        else:
            tm.ok(result)
            tm.that(output.read_text(encoding=c.DEFAULT_ENCODING), has=str(selection))

    @staticmethod
    @pytest.mark.parametrize("execution_artifact", [False, True])
    def test_waiting_lease_profile_has_no_child_execution(
        tmp_path: Path, native_cprofile: Path, *, execution_artifact: bool
    ) -> None:
        """A profiled lease wait renders only authenticated parent evidence."""
        reports = tmp_path / c.Infra.REPORTS_DIR_NAME
        directory = reports / "waiting"
        directory.mkdir(parents=True)
        profile = native_cprofile
        context = m.Infra.PytestRunContext(
            execution_mode=c.Infra.PytestExecutionMode.INCREMENTAL,
            testmon_db=tmp_path / "testmon",
            testmon_lease_acquired=False,
            deadline_monotonic=None,
            report_directory=directory,
        )
        (directory / "run-context.json").write_text(
            context.model_dump_json(), encoding=c.DEFAULT_ENCODING
        )
        profile.with_suffix(".pstats.json").write_text(
            context.model_copy(
                update={"profile_sha256": u.Cli.sha256_bytes(profile.read_bytes())}
            ).model_dump_json(),
            encoding=c.DEFAULT_ENCODING,
        )
        if execution_artifact:
            (directory / "suite-outcome.json").write_text(
                "{}\n", encoding=c.DEFAULT_ENCODING
            )
        result = validate.FlextInfraCProfileReport(
            repository_root=tmp_path,
            profile=profile,
            output=reports / "profile.txt",
            sort=config.Infra.tooling.tools.pytest.profile_sort,
            limit=config.Infra.tooling.tools.pytest.profile_limit,
            run_receipt=profile.with_suffix(".pstats.json"),
        ).execute()
        if execution_artifact:
            tm.fail(result)
        else:
            tm.ok(result)

    @staticmethod
    @pytest.mark.parametrize("exit_code", [0, 1])
    @pytest.mark.parametrize("stage", ["selection", "inventory"])
    def test_selection_profile_without_plan_requires_failed_receipt(
        tmp_path: Path,
        native_cprofile: Path,
        exit_code: int,
        stage: str,
    ) -> None:
        """Render failed selection evidence without accepting an incomplete success."""
        directory = tmp_path / c.Infra.REPORTS_DIR_NAME / "selection"
        directory.mkdir(parents=True)
        profile = native_cprofile
        selection = directory / (
            c.Infra.PYTEST_INVENTORY_PROFILE_FILENAME
            if stage == "inventory"
            else c.Infra.PYTEST_SELECTION_PROFILE_FILENAME
        )
        selection.write_bytes(profile.read_bytes())
        context = m.Infra.PytestRunContext(
            execution_mode=c.Infra.PytestExecutionMode.INCREMENTAL,
            testmon_db=tmp_path / "testmon",
            testmon_lease_acquired=True,
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
            testmon_db=tmp_path / "testmon",
            testmon_lease_acquired=True,
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
