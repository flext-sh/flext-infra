"""Observable public profiling contract for the cached-pytest runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pstats
import signal
import sys
from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.validate import FlextInfraCProfileReport, FlextInfraPytestRunner
from tests import c, m, t, tm, u


class TestsFlextInfraPytestProfile:
    """Exercise the real profiling child transport and its receipt binding."""

    @staticmethod
    def test_interrupted_publication_preserves_the_previous_readable_profile(
        tmp_path: Path,
    ) -> None:
        """A real SIGINT during serialization cannot truncate an earlier profile."""
        output = tmp_path / "checkpoint.pstats"
        script = (
            c.Infra.PYTEST_PROFILE_BOOTSTRAP + "import os, signal, sys, pstats\n"
            "output = Path(sys.argv[1])\n"
            "profile.runcall(sum, range(10))\n"
            "clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "before = output.read_bytes()\n"
            "before_modified = output.stat().st_mtime_ns\n"
            "def interrupt(event, arguments):\n"
            "    if event == 'marshal.dumps':\n"
            "        assert output.read_bytes() == before\n"
            "        os.kill(os.getpid(), signal.SIGINT)\n"
            "sys.addaudithook(interrupt)\n"
            "try:\n"
            "    clock.FlextInfraPytestClock.publish_profile(profile, output)\n"
            "except KeyboardInterrupt:\n"
            "    pass\n"
            "else:\n"
            "    raise AssertionError('native SIGINT did not escape publication')\n"
            "assert output.read_bytes() == before\n"
            "assert output.stat().st_mtime_ns == before_modified\n"
            "assert pstats.Stats(str(output)).get_stats_profile().func_profiles\n"
        )
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script, str(output)),
                cwd=tmp_path,
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stdout + result.stderr,
        )

    @staticmethod
    @pytest.mark.parametrize("interruption", ["signal", "timeout"])
    def test_native_termination_keeps_a_readable_profile_checkpoint(
        tmp_path: Path,
        interruption: str,
    ) -> None:
        """Preserve native SIGTERM and timeout outcomes alongside measured progress."""
        deadline = config.Infra.tooling.tools.pytest.termination_grace_seconds
        probe = tmp_path / "termination_probe.py"
        action = (
            "os.kill(os.getpid(), signal.SIGTERM)"
            if interruption == "signal"
            else f"time.sleep({deadline * 2!r})"
        )
        probe.write_text(
            "import os\nimport signal\nimport time\n"
            "def interrupt_import():\n"
            f"    {action}\n"
            "interrupt_import()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        output = tmp_path / "terminated.pstats"
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    c.Infra.PYTEST_PROFILE_LAUNCHER,
                    str(output),
                    "-p",
                    probe.stem,
                    "--version",
                ),
                cwd=tmp_path,
                timeout=deadline,
            ),
        )
        tm.that(result.outcome.raw_return_code, eq=-signal.SIGTERM)
        tm.that(result.outcome.timed_out, eq=interruption == "timeout")
        tm.that(result.outcome.forwarded_signal, eq=None)
        measured = pstats.Stats(str(output)).get_stats_profile().func_profiles
        tm.that(
            any(Path(function.file_name) == probe for function in measured.values()),
            eq=True,
        )

    @staticmethod
    @pytest.mark.slow
    def test_interrupted_profile_preserves_the_child_process_failure(
        cached_runner_project: Path,
    ) -> None:
        """A killed real child keeps its signal instead of a missing-profile error."""
        cache = config.Infra.codegen.make.testmon_cache
        target = Path(cache.target_directory) / "test_runtime.py"
        (cached_runner_project / target).write_text(
            "import os\n"
            "import signal\n"
            "def test_runtime():\n"
            "    os.kill(os.getpid(), signal.SIGKILL)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        ).model_copy(update={"profile_enabled": True})
        tm.that(tm.ok(runner.execute()), eq=-signal.SIGKILL)
        reports = cached_runner_project / runner.reports
        contexts = tuple(reports.glob("*/run-context.json"))
        tm.that(len(contexts), eq=1)
        directory = contexts[0].parent
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (directory / "suite-outcome.json").read_text(encoding=c.DEFAULT_ENCODING)
        )
        tm.that(outcome.raw_return_code, eq=-signal.SIGKILL)
        tm.that(outcome.timed_out, eq=False)
        tm.that(outcome.forwarded_signal, eq=None)
        profile = directory / config.Infra.tooling.tools.pytest.profile_suite_filename
        tm.that(profile.exists(), eq=False)
        tm.that((directory / "run-accounting.json").exists(), eq=False)

    @staticmethod
    @pytest.mark.slow
    def test_focused_profile_keeps_one_run_and_excludes_other_files(
        cached_runner_project: Path,
    ) -> None:
        """The fresh entry profiles one declared file on the persistent database."""
        cache = config.Infra.codegen.make.testmon_cache
        target = Path(cache.target_directory) / "test_runtime.py"
        unselected = (
            cached_runner_project / cache.target_directory / "test_unselected.py"
        )
        unselected.write_text(
            "def test_unselected():\n    raise RuntimeError('unselected file ran')\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        )
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / config.Infra.tooling.tools.pytest.profile_suite_filename
        )
        tm.that(
            u.Tests.PytestRunner.profile_parent(runner, output), eq=pytest.ExitCode.OK
        )
        reports = cached_runner_project / runner.reports
        contexts = list(reports.glob("*/run-context.json"))
        tm.that(len(contexts), eq=1)
        context = m.Infra.PytestRunContext.model_validate_json(
            contexts[0].read_text(encoding="utf-8"),
        )
        tm.that(context.testmon_db, eq=runner.testmon_db)
        tm.that(context.deadline_monotonic is not None, eq=True)
        command = (contexts[0].parent / "command.txt").read_text(encoding="utf-8")
        tm.that(command, has=str(target))
        tm.that(command, lacks="test_unselected.py")
        tm.that(runner.testmon_db.is_file(), eq=True)
        stats = pstats.Stats(str(output)).get_stats_profile().func_profiles
        tm.that(FlextInfraPytestRunner.__name__ in stats, eq=True)
        tm.that("FlextInfraPytestProfile" in stats, eq=True)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("target_file", [Path("../outside.py"), Path("missing.py")])
    def test_profile_entry_rejects_invalid_focused_targets(
        cached_runner_project: Path,
        target_file: Path,
    ) -> None:
        """Invalid input fails through the real entry before publishing a run."""
        runner = u.Tests.PytestRunner.runner_for(cached_runner_project)
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / config.Infra.tooling.tools.pytest.profile_suite_filename
        )
        with pytest.raises(RuntimeError, match=r"target_file|test target file"):
            u.Tests.PytestRunner.profile_parent(runner, output, target_file=target_file)
        tm.that(
            list((cached_runner_project / runner.reports).glob("*/run-context.json")),
            eq=[],
        )

    @staticmethod
    @pytest.mark.slow
    def test_pytester_children_profile_startup_and_preserve_native_exits(
        cached_runner_project: Path,
    ) -> None:
        """Real pytester children retain imports, site customization and exits."""
        cache = config.Infra.codegen.make.testmon_cache
        policy = config.Infra.tooling.tools.pytest
        customization = (
            cached_runner_project / c.Infra.DEFAULT_SRC_DIR / "sitecustomize.py"
        )
        customization.write_text(
            "class ProfiledSiteCustomization:\n    pass\n",
            encoding="utf-8",
        )
        target = Path(cache.target_directory) / "test_runtime.py"
        (cached_runner_project / target).write_text(
            "import pytest\n"
            "pytest_plugins = ['pytester']\n"
            f"@pytest.mark.{policy.slow_marker}\n"
            "def test_runtime(pytester):\n"
            "    result = pytester.runpytest_subprocess('--version')\n"
            "    assert result.ret == pytest.ExitCode.OK\n"
            "    result = pytester.runpytest_subprocess('--invalid-profile-probe')\n"
            "    assert result.ret == pytest.ExitCode.USAGE_ERROR\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=target
        )
        output = (
            cached_runner_project
            / ".reports"
            / "profiles"
            / policy.profile_suite_filename
        )
        tm.that(
            u.Tests.PytestRunner.profile_parent(runner, output), eq=pytest.ExitCode.OK
        )
        receipt = m.Infra.PytestRunContext.model_validate_json(
            output.with_suffix(".pstats.json").read_text(encoding="utf-8"),
        )
        directory = receipt.report_directory
        if directory is None:
            pytest.fail("profile did not bind its run directory")
        processes = directory / policy.profile_process_directory
        profiles = list(processes.glob("*.pstats"))
        tm.that(len(profiles) >= 2, eq=True)
        for child in profiles:
            functions = pstats.Stats(str(child)).get_stats_profile().func_profiles
            startup_functions = tuple(
                (name, function.file_name)
                for name, function in functions.items()
                if function.file_name.endswith("sitecustomize.py")
            )
            tm.that(
                "ProfiledSiteCustomization" in functions,
                eq=True,
                msg=f"site customization absent from {child}: {startup_functions}",
            )
            tm.that(
                any("_pytest" in function.file_name for function in functions.values()),
                eq=True,
            )
        report = FlextInfraCProfileReport(
            repository_root=cached_runner_project,
            profile=output,
            output=output.with_suffix(".txt"),
            run_receipt=output.with_suffix(".pstats.json"),
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        )
        tm.ok(report.execute())
        text = report.output.read_text(encoding="utf-8")
        for child in profiles:
            tm.that(text, has=str(child))
        child = profiles[0]
        child.write_bytes(child.read_bytes() + b"changed")
        tm.that(report.execute().failure, eq=True)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("arguments", "expected_exit"),
        [
            (("--version",), pytest.ExitCode.OK),
            (("--flext-invalid-profile-option",), pytest.ExitCode.USAGE_ERROR),
        ],
    )
    def test_profile_child_preserves_exit_status_and_arguments(
        tmp_path: Path,
        arguments: t.StrTuple,
        expected_exit: int,
    ) -> None:
        """The real pytest module exits natively and leaves its raw profile."""
        profile = tmp_path / "collection.pstats"
        result = u.Tests.PytestRunner.profile_collection(profile, arguments)
        assert result.outcome.raw_return_code == expected_exit
        assert not result.outcome.timed_out
        assert result.outcome.forwarded_signal is None
        if expected_exit == pytest.ExitCode.USAGE_ERROR:
            assert arguments[0] in result.stderr
        assert pstats.Stats(str(profile)).get_stats_profile().func_profiles

    @staticmethod
    @pytest.mark.slow
    def test_profile_failure_exposes_the_write_error(tmp_path: Path) -> None:
        """A real profile I/O failure remains visible rather than becoming success."""
        output = tmp_path / "collection.pstats"
        output.mkdir()
        result = u.Tests.PytestRunner.profile_collection(output, ("--version",))
        assert result.outcome.raw_return_code != 0
        assert not result.outcome.timed_out
        assert result.outcome.forwarded_signal is None
        assert "IsADirectoryError" in result.stderr

    @staticmethod
    @pytest.mark.parametrize("complete", [False, True])
    def test_collection_profile_preserves_pytest_arguments(
        cached_runner_project: Path,
        *,
        complete: bool,
    ) -> None:
        """Only the interpreter prefix changes; suite execution is not profiled."""
        plain = u.Tests.PytestRunner.runner_for(cached_runner_project)
        profiled = u.Tests.PytestRunner.runner_for(
            cached_runner_project, profile_collection=True
        )
        report = cached_runner_project / plain.reports
        manifest = report / "collection.json"
        plain_command = plain.build_selection_command(
            report_log=report / "collection.jsonl",
            manifest_path=manifest,
            complete=complete,
        )
        profiled_command = profiled.build_selection_command(
            report_log=report / "collection.jsonl",
            manifest_path=manifest,
            complete=complete,
        )
        assert profiled_command == (
            *profiled.collection_command_prefix,
            str(manifest.with_suffix(".pstats")),
            *plain_command[3:],
        )
        assert c.Infra.PYTEST_PROFILE_LAUNCHER not in profiled.build_command(report)

    @staticmethod
    def _assert_parent_profile_evidence(
        project: Path,
        reports_root: Path,
        latest_name: str,
    ) -> None:
        """Prove the parent profiler captured the public runner import.

        The profiled run's parent profile names pytest internals and the
        runner class, its report pairs only this run, and every tampered
        receipt input fails the report loudly.

        """
        parent_profile = project / ".reports" / "profiles" / "pytest.pstats"
        profile = reports_root / latest_name / "testmon-selection.pstats"
        stats = pstats.Stats(str(profile))
        directory = reports_root / latest_name
        policy = config.Infra.tooling.tools.pytest
        suite = pstats.Stats(
            *(
                str(path)
                for path in (
                    directory / policy.profile_suite_filename,
                    *sorted(
                        (directory / policy.profile_process_directory).glob("*.pstats")
                    ),
                )
            )
        ).get_stats_profile()
        tm.that(
            any(
                name == "test_runtime"
                and Path(function.file_name)
                == project
                / config.Infra.codegen.make.testmon_cache.target_directory
                / "test_runtime.py"
                for name, function in suite.func_profiles.items()
            ),
            eq=True,
        )
        assert any(
            "_pytest" in function.file_name
            for function in stats.get_stats_profile().func_profiles.values()
        )
        parent_stats = pstats.Stats(str(parent_profile)).get_stats_profile()
        # The class body runs on import, unlike its methods: this proves the
        # public runner was first imported while the parent profiler was active.
        assert FlextInfraPytestRunner.__name__ in parent_stats.func_profiles
        report = FlextInfraCProfileReport(
            repository_root=project,
            profile=parent_profile,
            output=parent_profile.with_suffix(".txt"),
            run_receipt=parent_profile.with_suffix(".pstats.json"),
            sort=policy.profile_sort,
            limit=policy.profile_limit,
        )
        # An unrelated latest pointer must never pair this parent with another run.
        latest = reports_root / "latest.txt"
        latest.write_text("unrelated-run\n", encoding="utf-8")
        tm.ok(report.execute())
        latest.write_text(latest_name + "\n", encoding="utf-8")
        text = report.output.read_text(encoding="utf-8")
        assert str(parent_profile) in text
        assert str(profile) in text
        receipt_path = profile.with_suffix(".pstats.json")
        original = receipt_path.read_text(encoding="utf-8")
        receipt = m.Infra.PytestRunContext.model_validate_json(original)
        # The profiled incremental operation is bounded, so its receipt names
        # a deadline.
        deadline = receipt.deadline_monotonic
        assert deadline is not None
        receipt_path.write_text(
            receipt.model_copy(
                update={"deadline_monotonic": deadline + 1},
            ).model_dump_json(),
            encoding="utf-8",
        )
        assert report.execute().failure
        receipt_path.write_text("{", encoding="utf-8")
        assert report.execute().failure
        receipt_path.unlink()
        assert report.execute().failure
        receipt_path.write_text(original, encoding="utf-8")
        parent_profile.write_bytes(parent_profile.read_bytes() + b"stale")
        assert report.execute().failure

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("profile_collection", [False, True])
    def test_complete_suite_persists_cache_and_zero_diagnostic_evidence(
        cached_runner_project: Path,
        *,
        profile_collection: bool,
    ) -> None:
        """One public execution collects every test and publishes real evidence.

        The profiled run loads ``flext_infra`` as a plugin package, as consumer
        projects do: a child that imported it before pytest makes pytest warn
        that it cannot rewrite it, and the collection gate rejects warnings.
        """
        cache = config.Infra.codegen.make.testmon_cache
        if profile_collection:
            pyproject = cached_runner_project / c.PYPROJECT_FILENAME
            pyproject.write_text(
                pyproject.read_text(encoding="utf-8") + 'addopts = "-p flext_infra"\n',
                encoding="utf-8",
            )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project,
            profile_collection=profile_collection,
        )
        testmon_db = runner.testmon_db

        parent_profile = (
            cached_runner_project / ".reports" / "profiles" / "pytest.pstats"
        )
        exit_code = (
            u.Tests.PytestRunner.profile_parent(runner, parent_profile)
            if profile_collection
            else tm.ok(runner.execute())
        )

        tm.that(exit_code, eq=0)
        tm.that(testmon_db.is_file(), eq=True)
        tm.that(testmon_db.is_relative_to(cached_runner_project), eq=False)
        tm.that((cached_runner_project / cache.database_filename).exists(), eq=False)
        reports_root = cached_runner_project / cache.reports_directory
        latest_name = tm.ok(u.Cli.files_read_text(reports_root / "latest.txt")).strip()
        profile = reports_root / latest_name / "testmon-selection.pstats"
        assert profile.is_file() == profile_collection
        if profile_collection:
            TestsFlextInfraPytestProfile._assert_parent_profile_evidence(
                cached_runner_project,
                reports_root,
                latest_name,
            )
        assert not (reports_root / latest_name / "testmon-inventory.pstats").exists()
        summary = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "summary.txt"),
        )
        tm.that(
            summary,
            has=[
                "executed=1",
                "failed=0",
                "errors=0",
                "warnings=0",
                "skipped=0",
                "exit=0",
            ],
        )
        tm.that((reports_root / latest_name / "junit.xml").is_file(), eq=True)
        # The testmon verb owns no coverage plugin (testmon 2.x refuses branch
        # coverage through the cov plugin), so its command carries --no-cov and
        # the coverage artifact belongs to the coverage verb alone.
        selection = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "testmon-selection.txt"),
        )
        command = tm.ok(
            u.Cli.files_read_text(reports_root / latest_name / "command.txt"),
        )
        # Selection runs once before workers record dependencies; the collection
        # plugin enforces exactly the selected node ids in the recorded order.
        tm.that(selection.splitlines(), has="tests/test_runtime.py::test_runtime")
        tm.that(command, has=c.Infra.PYTEST_SELECTED_COLLECTION_OPTION)
        tm.that(command, has="--no-cov")
        tm.that(command, has="--testmon --testmon-noselect")
        tm.that((reports_root / latest_name / "coverage.xml").is_file(), eq=False)
        # A cold run has no database to inspect before pytest; its only cache
        # receipt is the post-run seed decision.
        tm.that((reports_root / latest_name / "cache-before.json").exists(), eq=False)
        seeded = m.Infra.TestmonCacheState.model_validate_json(
            tm.ok(
                u.Cli.files_read_text(reports_root / latest_name / "cache-after.json"),
            ),
        )
        tm.that(seeded.seed_needed, eq=True)
        tm.that(seeded.saveable, eq=True)
