"""Single-file pytest target contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from typing_extensions import TypeForm

from flext_infra import config
from tests import c, m, tm, u


@pytest.mark.unit
class TestsFlextInfraPytestTargetFile:
    """A declared file replaces the suite directory as the only node target."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("budgeted", "slow", "failure"),
        [
            (True, False, ""),
            (False, True, ""),
            (True, True, ""),
            (False, False, ""),
            (True, True, "budgeted"),
            (True, True, "slow"),
            (True, True, "collection"),
        ],
    )
    def test_public_runner_runs_complete_requested_file_once(
        cached_runner_project: Path,
        *,
        budgeted: bool,
        slow: bool,
        failure: str,
    ) -> None:
        """The public file operation runs one bounded phase with causal failure."""
        root = cached_runner_project
        make = config.Infra.codegen.make
        probe = f"file_phase_probe_{budgeted}_{slow}_{failure or 'passed'}"
        relative = Path(make.testmon_cache.target_directory) / (
            u.Infra.native_tool_setting(
                config.Infra.tooling,
                "pytest.ini_options",
                "python_files",
                TypeForm(Sequence[str]),
            )[0].replace("*", probe)
        )
        proof = root / f"{probe}.log"
        source, expected = TestsFlextInfraPytestTargetFile._probe_source(
            proof,
            budgeted=budgeted,
            slow=slow,
            failure=failure,
        )
        (root / relative).write_text(source, encoding=c.Infra.ENCODING_DEFAULT)
        # An unrelated failing module proves FILE remains the complete scope.
        (
            root / relative.with_name(relative.name.replace("probe", "unrelated"))
        ).write_text(
            "def test_unrelated() -> None:\n    assert False\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        reports = root / make.testmon_cache.reports_directory
        before = set(reports.glob("*/run-context.json"))
        runner = u.Tests.PytestRunner.runner_for(root, target_file=relative)

        status = tm.ok(runner.execute_file())

        tm.that(
            status == pytest.ExitCode.OK.value,
            eq=bool(expected) and not failure,
        )
        if failure == "collection" or not expected:
            tm.fail(proof.exists())
        else:
            observed = proof.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()
            tm.that(
                all(observed.count(item) <= expected.count(item) for item in observed),
                eq=True,
            )
            if not failure:
                tm.that(sorted(observed), eq=sorted(expected))
        receipts = [
            m.Infra.PytestRunContext.model_validate_json(path.read_text())
            for path in sorted(
                set(reports.glob("*/run-context.json")) - before,
                key=lambda path: path.stat().st_mtime_ns,
            )
        ]
        modes = [c.Infra.PytestExecutionMode.FULL]
        tm.that([receipt.execution_mode for receipt in receipts], eq=modes)
        tm.that(len({receipt.testmon_db for receipt in receipts}), eq=1)
        tm.that(
            {receipt.deadline_monotonic for receipt in receipts},
            eq={
                runner.started_at_monotonic
                + config.Infra.tooling.tools.pytest.run_timeout_seconds,
            },
        )
        if expected and not failure:
            TestsFlextInfraPytestTargetFile._assert_rerun_executes_again(
                root,
                relative,
                proof,
                expected,
            )

    @staticmethod
    def _probe_source(
        proof: Path,
        *,
        budgeted: bool,
        slow: bool,
        failure: str,
    ) -> tuple[str, list[str]]:
        """Render the probe module and the phases it must record.

        Returns:
            The probe module source and the phases it must record, in order.

        """
        slow_marker = config.Infra.tooling.tools.pytest.slow_marker
        source = "import pytest\nfrom pathlib import Path\n\n"
        if failure == "collection":
            source += "raise RuntimeError('file-phase-collection-failure')\n"
        expected: list[str] = []
        for phase, enabled in (("budgeted", budgeted), ("slow", slow)):
            if not enabled:
                continue
            if phase == "slow":
                source += f"@pytest.mark.{slow_marker}\n"
            source += (
                f"def test_{phase}() -> None:\n"
                f"    with Path({str(proof)!r}).open('a') as stream:\n"
                f"        stream.write('{phase}\\n')\n"
                + ("    assert False\n" if failure == phase else "")
                + "\n"
            )
            if failure != "collection":
                expected.append(phase)
        return source, expected

    @staticmethod
    def _assert_rerun_executes_again(
        root: Path,
        relative: Path,
        proof: Path,
        expected: list[str],
    ) -> None:
        """A green public file operation reruns and records every selected item."""
        before = proof.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()
        runner = u.Tests.PytestRunner.runner_for(root, target_file=relative)

        tm.that(tm.ok(runner.execute_file()), eq=pytest.ExitCode.OK.value)

        after = proof.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()
        tm.that(after[: len(before)], eq=before)
        tm.that(sorted(after[len(before) :]), eq=sorted(expected))

    @staticmethod
    def test_declared_file_replaces_the_suite_directory(
        cached_runner_project: Path,
    ) -> None:
        """Selection and suite argv both name the declared file."""
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "declared_case.py"
        declared = cached_runner_project / relative
        declared.write_text(
            "def test_declared() -> None:\n    return None\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=relative
        )
        report = cached_runner_project / cache.reports_directory
        suite = runner.build_command(report)
        selection = runner.build_selection_command(
            report_log=report / "selection.jsonl",
            manifest_path=report / "selection.json",
        )
        expected = relative.as_posix()
        tm.that(suite[3], eq=expected)
        tm.that(selection[3], eq=expected)

    @staticmethod
    def test_missing_target_file_fails(cached_runner_project: Path) -> None:
        """An absent declared file fails before pytest starts."""
        outcome = "raised"
        try:
            u.Tests.PytestRunner.runner_for(
                cached_runner_project,
                target_file=Path("tests/missing_declared_case.py"),
            )
        except ValueError as exc:
            tm.ok("existing file" in str(exc))
            outcome = "value-error"
        tm.that(outcome, eq="value-error")

    @staticmethod
    @pytest.mark.slow
    def test_declared_file_operation_executes_fresh_tests(
        cached_runner_project: Path,
    ) -> None:
        """A fresh declared file runs through the real persistent-cache owner."""
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "fresh_case.py"
        declared = cached_runner_project / relative
        declared.write_text(
            "from pathlib import Path\n\n"
            "def test_fresh() -> None:\n"
            "    Path(__file__).with_suffix('.executed').write_text("
            "'executed', encoding='utf-8')\n",
            encoding="utf-8",
        )
        runner = u.Tests.PytestRunner.runner_for(
            cached_runner_project, target_file=relative
        )
        outcome = tm.ok(runner.execute_file())
        tm.that(outcome, eq=pytest.ExitCode.OK.value)
        tm.that(
            declared.with_suffix(".executed").read_text(encoding="utf-8"),
            eq="executed",
        )

    @staticmethod
    @pytest.mark.slow
    def test_declared_file_rerun_over_a_warm_cache_executes_again(
        cached_runner_project: Path,
    ) -> None:
        """An unchanged declared file reruns green, never as a cache hit."""
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "rerun_case.py"
        (cached_runner_project / relative).write_text(
            "def test_rerun() -> None:\n    return None\n",
            encoding="utf-8",
        )
        for _ in range(2):
            runner = u.Tests.PytestRunner.runner_for(
                cached_runner_project, target_file=relative
            )
            tm.that(tm.ok(runner.execute_file()), eq=pytest.ExitCode.OK.value)
            report = u.Tests.PytestRunner.summary(
                cached_runner_project / cache.reports_directory
            )
            tm.that(report, has="executed=1\n")

    @staticmethod
    @pytest.mark.slow
    def test_declared_file_edit_reruns_the_complete_file(
        cached_runner_project: Path,
    ) -> None:
        """A partly edited declared file stays green and runs every test.

        One invocation selects the complete file on the persistent cache,
        so an edit touching one test still verifies both tests of the file.
        """
        cache = config.Infra.codegen.make.testmon_cache
        relative = Path(cache.target_directory) / "partial_case.py"
        declared = cached_runner_project / relative
        kept = "def test_kept() -> None:\n    return None\n\n\n"
        for value in (1, 2):
            declared.write_text(
                kept + f"def test_edited() -> None:\n    assert {value}\n",
                encoding="utf-8",
            )
            runner = u.Tests.PytestRunner.runner_for(
                cached_runner_project, target_file=relative
            )
            tm.that(tm.ok(runner.execute_file()), eq=pytest.ExitCode.OK.value)
            report = u.Tests.PytestRunner.summary(
                cached_runner_project / cache.reports_directory
            )
            tm.that(report, has="executed=2\n")
