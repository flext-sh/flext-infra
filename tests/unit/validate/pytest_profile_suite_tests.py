"""Observable public profiling contract for complete-suite profile evidence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import pstats
from math import isfinite
from pathlib import Path

import pytest

from flext_infra import config, validate
from tests import c, m, tm, u


class TestsFlextInfraPytestProfileSuite:
    """Exercise collection and complete-suite profile evidence."""

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
        tm.that(
            profiled_command
            == (
                *profiled.collection_command_prefix,
                str(manifest.with_suffix(".pstats")),
                *plain_command[3:],
            ),
            truth=True,
        )
        tm.that(
            c.Infra.PYTEST_PROFILE_LAUNCHER not in profiled.build_command(report),
            truth=True,
        )

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
        tm.that(
            any(
                "_pytest" in function.file_name
                for function in stats.get_stats_profile().func_profiles.values()
            ),
            truth=True,
        )
        parent_stats = pstats.Stats(str(parent_profile)).get_stats_profile()
        # The class body runs on import, unlike its methods: this proves the
        # public runner was first imported while the parent profiler was active.
        tm.that(
            validate.FlextInfraPytestRunner.__name__ in parent_stats.func_profiles,
            truth=True,
        )
        report = validate.FlextInfraCProfileReport(
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
        tm.that(str(parent_profile) in text, truth=True)
        tm.that(str(profile) in text, truth=True)
        receipt_path = profile.with_suffix(".pstats.json")
        original = receipt_path.read_text(encoding="utf-8")
        receipt = m.Infra.PytestRunContext.model_validate_json(original)
        # The profiled incremental operation is bounded, so its receipt names
        # a deadline.
        deadline = receipt.deadline_monotonic
        tm.ok(isfinite(deadline))
        tm.that(deadline, gt=0)
        receipt_path.write_text(
            receipt.model_copy(
                update={"deadline_monotonic": deadline + 1},
            ).model_dump_json(),
            encoding="utf-8",
        )
        tm.that(report.execute().failure, truth=True)
        receipt_path.write_text("{", encoding="utf-8")
        tm.that(report.execute().failure, truth=True)
        receipt_path.unlink()
        tm.that(report.execute().failure, truth=True)
        receipt_path.write_text(original, encoding="utf-8")
        parent_profile.write_bytes(parent_profile.read_bytes() + b"stale")
        tm.that(report.execute().failure, truth=True)

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
        tm.ok(testmon_db.is_file())
        tm.fail(testmon_db.is_relative_to(cached_runner_project))
        tm.fail((cached_runner_project / cache.database_filename).exists())
        reports_root = cached_runner_project / cache.reports_directory
        latest_name = tm.ok(u.Cli.files_read_text(reports_root / "latest.txt")).strip()
        profile = reports_root / latest_name / "testmon-selection.pstats"
        tm.that(profile.is_file() == profile_collection, truth=True)
        if profile_collection:
            TestsFlextInfraPytestProfileSuite._assert_parent_profile_evidence(
                cached_runner_project,
                reports_root,
                latest_name,
            )
        tm.that(
            (reports_root / latest_name / "testmon-inventory.pstats").exists(),
            truth=False,
        )
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
        tm.ok((reports_root / latest_name / "junit.xml").is_file())
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
        tm.fail((reports_root / latest_name / "coverage.xml").is_file())
        # A cold run has no database to inspect before pytest; its only cache
        # receipt is the post-run seed decision.
        tm.fail((reports_root / latest_name / "cache-before.json").exists())
        seeded = m.Infra.TestmonCacheState.model_validate_json(
            tm.ok(
                u.Cli.files_read_text(reports_root / latest_name / "cache-after.json"),
            ),
        )
        tm.ok(seeded.seed_needed)
        tm.ok(seeded.saveable)
