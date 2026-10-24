"""FULL execution observes its own collection and preserves native failures.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import signal
import sys
import time
from typing import TYPE_CHECKING

import pytest

from flext_infra import config, validate
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPytestFullInventory:
    """Exercise real consumers, worker lifecycles and the public profile reader."""

    @staticmethod
    def _consumer(
        root: Path,
        *,
        distributed: bool = False,
        markdown: bool = False,
        with_tests: bool = True,
    ) -> Path:
        """Create a consumer with explicit storage and measurement-only hooks.

        Returns:
            The physical consumer root.

        """
        project = u.Tests.mk_project(root, "full-consumer", with_src=True)
        cache = config.Infra.codegen.make.testmon_cache
        target = project / cache.target_directory
        target.mkdir(parents=True)
        (project / "observations").mkdir()
        tm.ok(
            u.Cli.toml_write_mapping(
                project / c.PYPROJECT_FILENAME,
                {
                    "tool": {
                        "pytest": {
                            "ini_options": {
                                "pythonpath": [c.Infra.DEFAULT_SRC_DIR],
                                "markers": list(
                                    config.Infra.tooling.tools.pytest.standard_markers,
                                ),
                                "addopts": (
                                    ["--markdown-docs", "-k", "kept"]
                                    if markdown
                                    else []
                                ),
                            },
                        },
                    },
                },
            ),
        )
        if distributed:
            u.Tests.PytestRunner.declare_parallel_project(project)
        (project / "conftest.py").write_text(
            "import json\n"
            "import os\n"
            "from pathlib import Path\n"
            "import pytest\n\n"
            "configuration: pytest.Config\n\n"
            "def pytest_configure(config):\n"
            "    global configuration\n"
            "    configuration = config\n"
            "    if not hasattr(config, 'workerinput'):\n"
            "        directory = Path(config.rootpath) / 'observations'\n"
            "        (directory / 'admissions.jsonl').write_text("
            "'', encoding='utf-8')\n"
            "        (directory / 'controller-collections.jsonl').write_text("
            "'', encoding='utf-8')\n\n"
            "@pytest.hookimpl(optionalhook=True)\n"
            "def pytest_configure_node(node):\n"
            "    path = Path(node.config.rootpath) / 'observations' / "
            "'admissions.jsonl'\n"
            "    with path.open('a', encoding='utf-8') as stream:\n"
            "        stream.write(json.dumps(node.gateway.id) + '\\n')\n\n"
            "@pytest.hookimpl(optionalhook=True)\n"
            "def pytest_xdist_node_collection_finished(node, ids):\n"
            "    path = (Path(node.config.rootpath) / 'observations'\n"
            "            / 'controller-collections.jsonl')\n"
            "    with path.open('a', encoding='utf-8') as stream:\n"
            "        stream.write(json.dumps({'worker': node.gateway.id,\n"
            "                                 'node_ids': list(ids)}) + '\\n')\n\n"
            "def pytest_collection_finish(session):\n"
            "    config = session.config\n"
            "    worker = (config.workerinput['workerid']\n"
            "              if hasattr(config, 'workerinput') else None)\n"
            "    path = Path(config.rootpath) / 'observations' / "
            "f'collection-{os.getpid()}.jsonl'\n"
            "    with path.open('a', encoding='utf-8') as stream:\n"
            "        stream.write(json.dumps({'pid': os.getpid(), 'worker': worker,\n"
            "            'collect_only': config.getoption('collectonly'),\n"
            "            'node_ids': [item.nodeid for item in "
            "session.items]}) + '\\n')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (project / c.Infra.DEFAULT_SRC_DIR / "full_pipeline.py").write_text(
            "from pathlib import Path\n\n"
            "def normalize(source: Path, destination: Path) -> None:\n"
            "    records = source.read_text(encoding='utf-8').splitlines()\n"
            "    values = [record.strip().upper() for record in records "
            "if record.strip()]\n"
            "    destination.write_text('\\n'.join(values), encoding='utf-8')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (project / "input.txt").write_text(
            " alpha \n\n beta\n",
            encoding=c.DEFAULT_ENCODING,
        )
        if with_tests:
            (target / "test_kept_pipeline.py").write_text(
                "from pathlib import Path\n"
                "from full_pipeline import normalize\n\n"
                "def test_kept_pipeline() -> None:\n"
                "    normalize(Path('input.txt'), Path('python-output.txt'))\n",
                encoding=c.DEFAULT_ENCODING,
            )
        if markdown:
            (target / "kept.md").write_text(
                "```python\nfrom pathlib import Path\n"
                "from full_pipeline import normalize\n"
                "normalize(Path('input.txt'), Path('markdown-output.txt'))\n```\n",
                encoding=c.DEFAULT_ENCODING,
            )
            (target / "excluded.md").write_text(
                "```python\nfrom pathlib import Path\n"
                "Path('excluded-output.txt').write_text("
                "'unexpected', encoding='utf-8')\n"
                "```\n",
                encoding=c.DEFAULT_ENCODING,
            )
        return project

    @staticmethod
    def _report_directory(project: Path) -> Path:
        """Select the only invocation created by this fresh consumer.

        Returns:
            The observed invocation report directory.

        """
        reports = project / config.Infra.codegen.make.testmon_cache.reports_directory
        (context,) = reports.glob("*/run-context.json")
        return context.parent

    @staticmethod
    def _events(path: Path) -> tuple[dict[str, t.JsonValue], ...]:
        """Read the observer's original JSON events without synthesizing entries.

        Returns:
            The events actually written by the native hooks.

        """
        adapter = u.type_adapter(dict[str, t.JsonValue])
        return tuple(
            adapter.validate_json(line)
            for line in path.read_text(encoding=c.DEFAULT_ENCODING).splitlines()
        )

    @staticmethod
    def _admissions(project: Path) -> tuple[str, ...]:
        """Read actual native worker admissions in their observed order.

        Returns:
            The identities reported by xdist.

        """
        return tuple(
            u.type_adapter(str).validate_json(line)
            for line in (project / "observations" / "admissions.jsonl")
            .read_text(encoding=c.DEFAULT_ENCODING)
            .splitlines()
        )

    @staticmethod
    def _assert_single_collection(
        project: Path,
        expected_processes: int,
    ) -> tuple[dict[str, t.JsonValue], ...]:
        """Require exactly one native collection per executing interpreter.

        Returns:
            The independently observed collection events.

        """
        paths = tuple((project / "observations").glob("collection-*.jsonl"))
        tm.that(paths, length=expected_processes)
        events: list[dict[str, t.JsonValue]] = []
        for path in paths:
            (event,) = TestsFlextInfraPytestFullInventory._events(path)
            tm.that(event["collect_only"], eq=False)
            events.append(event)
        return tuple(events)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "distributed",
        [False, True],
        ids=["default", "declared-xdist"],
    )
    def test_full_observes_one_collection_and_markdown_selection(
        tmp_path: Path,
        *,
        distributed: bool,
    ) -> None:
        """The executed suite supplies inventory and Markdown deselection facts."""
        project = TestsFlextInfraPytestFullInventory._consumer(
            tmp_path,
            distributed=distributed,
            markdown=True,
        )
        runner = u.Tests.PytestRunner.runner_for(project)
        budget = runner.parallel_worker_budget(config.Infra.tooling.tools.pytest)
        uses_workers = budget > 1
        if distributed:
            tm.that(budget, gt=1)

        tm.that(tm.ok(runner.execute_full()), eq=pytest.ExitCode.OK)

        directory = TestsFlextInfraPytestFullInventory._report_directory(project)
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            (directory / "selection-plan.json").read_bytes(),
        )
        manifest = m.Infra.PytestCollectionManifest.model_validate_json(
            plan.manifest_path.read_bytes(),
        )
        observations = TestsFlextInfraPytestFullInventory._assert_single_collection(
            project,
            budget,
        )
        for observation in observations:
            tm.that(observation["node_ids"], eq=list(manifest.node_ids))
        admissions = TestsFlextInfraPytestFullInventory._admissions(project)
        tm.that(admissions, length=budget if uses_workers else 0)
        if uses_workers:
            tm.that(
                {
                    u.type_adapter(str).validate_python(event["worker"])
                    for event in observations
                },
                eq=set(admissions),
            )
        tm.ok(plan.whole_target)
        tm.ok(plan.inventory_collected)
        tm.that(plan.node_ids, eq=manifest.node_ids)
        tm.fail(plan.owns_no_tests)
        tm.ok((directory / "suite-outcome.json").is_file())
        for phase in ("inventory", "selection"):
            tm.fail((directory / f"{phase}-outcome.json").exists())
        accounting = m.Infra.TestmonRunAccounting.model_validate_json(
            (directory / "run-accounting.json").read_bytes(),
        )
        tm.that(accounting.inventory_count, eq=len(manifest.node_ids))
        tm.that(accounting.executed_count, eq=len(manifest.node_ids))
        tm.that(accounting.reported_count, eq=len(manifest.node_ids))
        tm.that(accounting.deselected_count, eq=0)
        reconciliation = m.Infra.PytestMarkdownReconciliation.model_validate_json(
            (directory / "markdown-reconciliation.json").read_bytes(),
        )
        tm.that(reconciliation.violations, empty=True)
        tm.fail(reconciliation.cache_hit)
        expected_sources = {
            (runner.target / name).as_posix() for name in ("kept.md", "excluded.md")
        }
        tm.that(
            {origin.source_path for origin in manifest.markdown_eligible},
            eq=expected_sources,
        )
        tm.that(
            {item.origin for item in manifest.markdown_collected},
            eq=set(manifest.markdown_eligible),
        )
        excluded = tuple(
            item.node_id
            for item in manifest.markdown_collected
            if item.origin.source_path == (runner.target / "excluded.md").as_posix()
        )
        tm.that(excluded, length=1)
        tm.that(manifest.markdown_deselected, eq=excluded)
        for filename in ("python-output.txt", "markdown-output.txt"):
            tm.that(
                (project / filename).read_text(encoding=c.DEFAULT_ENCODING),
                eq="ALPHA\nBETA",
            )
        tm.fail((project / "excluded-output.txt").exists())

    @staticmethod
    @pytest.mark.slow
    def test_full_worker_crash_keeps_native_failure_without_restart(
        tmp_path: Path,
    ) -> None:
        """A real worker exit remains red with its native crash phase intact."""
        project = TestsFlextInfraPytestFullInventory._consumer(
            tmp_path,
            distributed=True,
            with_tests=False,
        )
        runner = u.Tests.PytestRunner.runner_for(project)
        budget = runner.parallel_worker_budget(config.Infra.tooling.tools.pytest)
        tm.that(budget, gt=1)
        source = project / runner.target / "test_worker_crash.py"
        source.write_text(
            "import os\nfrom pathlib import Path\n\n"
            "def test_worker_crash() -> None:\n"
            "    Path('crash-attempt.txt').write_text("
            "str(os.getpid()), encoding='utf-8')\n"
            "    os._exit(os.EX_SOFTWARE)\n",
            encoding=c.DEFAULT_ENCODING,
        )

        status = tm.ok(runner.execute_full())

        tm.that(status, ne=pytest.ExitCode.OK)
        directory = TestsFlextInfraPytestFullInventory._report_directory(project)
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (directory / "suite-outcome.json").read_bytes(),
        )
        tm.that(outcome.raw_return_code, eq=status)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        tm.that(
            TestsFlextInfraPytestFullInventory._admissions(project),
            length=budget,
        )
        TestsFlextInfraPytestFullInventory._assert_single_collection(project, budget)
        tm.that(
            int((project / "crash-attempt.txt").read_text(encoding=c.DEFAULT_ENCODING)),
            gt=0,
        )
        tm.fail((directory / "selection-plan.json").exists())
        tm.fail((directory / "testmon-inventory.json").exists())
        diagnostics = m.Infra.PytestDiagnostics.model_validate_json(
            (directory / "diagnostics.json").read_bytes(),
        )
        (crash,) = (
            phase for phase in diagnostics.phase_outcomes if phase.phase == "???"
        )
        tm.that(
            crash.node_id,
            eq=f"{source.relative_to(project).as_posix()}::test_worker_crash",
        )
        tm.that(crash.outcome, eq="failed")
        tm.that(diagnostics.error_count, eq=1)
        tm.that(
            (directory / "pytest.log").read_text(encoding=c.DEFAULT_ENCODING),
            has="crashed while running",
            lacks="ValidationError",
        )

    @staticmethod
    @pytest.mark.slow
    def test_full_shutdown_does_not_promote_late_worker_output(
        tmp_path: Path,
    ) -> None:
        """A real failed collector precedes a successful peer's late inventory."""
        project = TestsFlextInfraPytestFullInventory._consumer(
            tmp_path,
            distributed=True,
            with_tests=False,
        )
        runner = u.Tests.PytestRunner.runner_for(project)
        policy = config.Infra.tooling.tools.pytest
        budget = runner.parallel_worker_budget(policy)
        required_failures = policy.max_failures
        tm.that(budget, gt=required_failures)
        os.mkfifo(project / "late-collection.pipe")
        conftest = project / "conftest.py"
        with conftest.open("a", encoding=c.DEFAULT_ENCODING) as stream:
            stream.write(
                f"\nrequired_failures = {required_failures!r}\n"
                "collection_failures = 0\nreleased = set()\n\n"
                "def pytest_collectreport(report):\n"
                "    global collection_failures\n"
                "    if not hasattr(configuration, 'workerinput') and report.failed:\n"
                "        collection_failures += 1\n\n"
                "@pytest.hookimpl(optionalhook=True)\n"
                "def pytest_testnodedown(node, error):\n"
                "    if error is not None or collection_failures < required_failures:\n"
                "        return\n"
                "    root = Path(node.config.rootpath)\n"
                "    admissions = [json.loads(line) for line in\n"
                "        (root / 'observations' / 'admissions.jsonl')"
                ".read_text(encoding='utf-8').splitlines()]\n"
                "    identity = node.gateway.id\n"
                "    if identity not in admissions[:required_failures] or released:\n"
                "        return\n"
                "    released.add(identity)\n"
                "    with (root / 'late-collection.pipe').open('wb') as signal:\n"
                "        signal.write(b'native worker finished')\n"
                "    (root / 'observations' / 'released-worker.txt')"
                ".write_text(identity, encoding='utf-8')\n\n"
                "@pytest.hookimpl(wrapper=True, tryfirst=True,\n"
                "                 specname='pytest_collection_finish')\n"
                "def pytest_delay_peer_collection(session):\n"
                "    config = session.config\n"
                "    if hasattr(config, 'workerinput'):\n"
                "        root = Path(config.rootpath)\n"
                "        admissions = [json.loads(line) for line in\n"
                "            (root / 'observations' / 'admissions.jsonl')"
                ".read_text(encoding='utf-8').splitlines()]\n"
                "        identity = config.workerinput['workerid']\n"
                "        if identity == admissions[required_failures]:\n"
                "            with (root / 'late-collection.pipe').open('rb') "
                "as signal:\n"
                "                signal.read()\n"
                "            (root / 'observations' / 'late-worker.txt')"
                ".write_text(identity, encoding='utf-8')\n"
                "    yield\n",
            )
        message = "original consumer collection failure"
        (project / runner.target / "test_collection.py").write_text(
            "import json\nimport os\nfrom pathlib import Path\n"
            "from full_pipeline import normalize\n\n"
            "admissions = [json.loads(line) for line in\n"
            "    Path('observations/admissions.jsonl')"
            ".read_text(encoding='utf-8').splitlines()]\n"
            "identity = os.environ['PYTEST_XDIST_WORKER']\n"
            f"if identity in admissions[:{required_failures!r}]:\n"
            f"    raise RuntimeError({message!r} + ': ' + identity)\n\n"
            "def test_pipeline() -> None:\n"
            "    normalize(Path('input.txt'), Path('unexpected-output.txt'))\n",
            encoding=c.DEFAULT_ENCODING,
        )

        status = tm.ok(runner.execute_full())

        tm.that(status, eq=pytest.ExitCode.INTERRUPTED)
        directory = TestsFlextInfraPytestFullInventory._report_directory(project)
        admissions = TestsFlextInfraPytestFullInventory._admissions(project)
        tm.that(admissions, length=budget)
        tm.ok(
            (project / "observations" / "released-worker.txt").read_text(
                encoding=c.DEFAULT_ENCODING,
            )
            in admissions[:required_failures],
        )
        late = (project / "observations" / "late-worker.txt").read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(late, eq=admissions[required_failures])
        observations = TestsFlextInfraPytestFullInventory._assert_single_collection(
            project,
            budget,
        )
        tm.ok(any(event["worker"] == late for event in observations))
        observed = TestsFlextInfraPytestFullInventory._events(
            project / "observations" / "controller-collections.jsonl",
        )
        tm.fail(any(event["worker"] == late for event in observed))
        tm.fail((directory / "testmon-inventory.json").exists())
        tm.fail((directory / "selection-plan.json").exists())
        tm.fail((project / "unexpected-output.txt").exists())
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (directory / "suite-outcome.json").read_bytes(),
        )
        tm.that(outcome.raw_return_code, eq=status)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        diagnostics = m.Infra.PytestDiagnostics.model_validate_json(
            (directory / "diagnostics.json").read_bytes(),
        )
        tm.that(diagnostics.collection_failed_count, gt=0)
        tm.that(diagnostics.reported_node_ids, empty=True)
        tm.that(
            (directory / "pytest.log").read_text(encoding=c.DEFAULT_ENCODING),
            has=message,
        )

    @staticmethod
    @pytest.mark.slow
    def test_full_empty_inventory_is_not_promoted_to_success(tmp_path: Path) -> None:
        """An actually empty whole target keeps pytest's native zero-test failure."""
        project = TestsFlextInfraPytestFullInventory._consumer(
            tmp_path,
            with_tests=False,
        )
        runner = u.Tests.PytestRunner.runner_for(project)
        budget = runner.parallel_worker_budget(config.Infra.tooling.tools.pytest)

        status = tm.ok(runner.execute_full())

        tm.that(status, eq=pytest.ExitCode.NO_TESTS_COLLECTED)
        directory = TestsFlextInfraPytestFullInventory._report_directory(project)
        observations = TestsFlextInfraPytestFullInventory._assert_single_collection(
            project,
            budget,
        )
        for observation in observations:
            tm.that(observation["node_ids"], empty=True)
        tm.fail((directory / "selection-plan.json").exists())
        tm.fail((directory / "run-accounting.json").exists())
        diagnostics = m.Infra.PytestDiagnostics.model_validate_json(
            (directory / "diagnostics.json").read_bytes(),
        )
        tm.that(diagnostics.reported_node_ids, empty=True)
        tm.that(diagnostics.phase_outcomes, empty=True)
        tm.that(diagnostics.failed_count, eq=0)
        tm.that(diagnostics.error_count, eq=0)
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (directory / "suite-outcome.json").read_bytes(),
        )
        tm.that(outcome.raw_return_code, eq=status)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("execution_mode", "phase", "report_name"),
        [
            (c.Infra.PytestExecutionMode.FULL, "suite", "events.jsonl"),
            (
                c.Infra.PytestExecutionMode.INCREMENTAL,
                "selection",
                "testmon-selection.events.jsonl",
            ),
        ],
        ids=["full-suite", "incremental-selection"],
    )
    def test_native_sigterm_preserves_partial_events_and_interruption_summary(
        tmp_path: Path,
        execution_mode: c.Infra.PytestExecutionMode,
        phase: str,
        report_name: str,
    ) -> None:
        """A real controller signal retains its status without parsing partial JSONL."""
        project = TestsFlextInfraPytestFullInventory._consumer(tmp_path)
        partial = b'{"unfinished_event":'
        with (project / "conftest.py").open("a", encoding=c.DEFAULT_ENCODING) as stream:
            stream.write(
                "\nimport signal\n\n"
                "@pytest.hookimpl(tryfirst=True)\n"
                "def pytest_sessionstart(session):\n"
                "    if hasattr(session.config, 'workerinput'):\n"
                "        return\n"
                "    report = Path(session.config.getoption('report_log'))\n"
                "    with report.open('ab') as stream:\n"
                f"        stream.write({partial!r})\n"
                "    observation = (Path(session.config.rootpath) / 'observations'\n"
                "                   / 'interrupted-events.bin')\n"
                "    observation.write_bytes(report.read_bytes())\n"
                "    os.kill(os.getpid(), signal.SIGTERM)\n",
            )
        runner = u.Tests.PytestRunner.runner_for(project)

        status = tm.ok(
            runner.execute_full()
            if execution_mode is c.Infra.PytestExecutionMode.FULL
            else runner.execute(),
        )

        tm.that(status, eq=-signal.SIGTERM)
        directory = TestsFlextInfraPytestFullInventory._report_directory(project)
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            (directory / f"{phase}-outcome.json").read_bytes(),
        )
        tm.that(outcome.raw_return_code, eq=-signal.SIGTERM)
        tm.fail(outcome.timed_out)
        tm.that(outcome.forwarded_signal, none=True)
        summary = (directory / "summary.txt").read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(
            summary,
            has=[
                "outcome=interrupted\n",
                f"phase={phase}\n",
                "inventory_complete=unknown\n",
                "diagnostics=incomplete\n",
                f"exit={-signal.SIGTERM}\n",
                "timed_out=False\n",
                "forwarded_signal=None\n",
            ],
        )
        tm.that(
            summary,
            has=(
                "suite=incomplete\nexecuted=unknown\nreported=unknown\n"
                if execution_mode is c.Infra.PytestExecutionMode.FULL
                else "suite=not_executed\nexecuted=0\n"
            ),
        )
        observed = (project / "observations" / "interrupted-events.bin").read_bytes()
        tm.ok(observed.endswith(partial))
        tm.that((directory / report_name).read_bytes(), eq=observed)
        for filename in (
            c.Infra.GATE_CAPTURE_RESULT_FILENAME,
            "run-accounting.json",
            "selection-plan.json",
            "testmon-inventory.json",
            "diagnostics.json",
            "junit.xml",
        ):
            tm.fail((directory / filename).exists())
        tm.fail((project / "python-output.txt").exists())

    @staticmethod
    @pytest.mark.slow
    def test_profile_setting_keeps_full_operation_and_native_suite_profile(
        tmp_path: Path,
    ) -> None:
        """The FULL entrypoint profiles its actual suite and renders that evidence."""
        project = TestsFlextInfraPytestFullInventory._consumer(tmp_path)
        runner = u.Tests.PytestRunner.runner_for(project)
        policy = config.Infra.tooling.tools.pytest
        cache = config.Infra.codegen.make.testmon_cache

        process = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-m", "flext_infra._pytest_entry", "full"),
                cwd=project,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.PYTEST_ENV_REPOSITORY_ROOT: str(project),
                        c.Infra.PYTEST_ENV_TARGET: str(runner.target),
                        c.Infra.PYTEST_ENV_TARGET_FILE: "",
                        c.Infra.PYTEST_ENV_REPORTS: str(runner.reports),
                        cache.database_environment_variable: str(runner.testmon_db),
                        "FLEXT_INFRA_PROFILE": "true",
                    },
                    deadline=m.Cli.ProcessDeadline(
                        expires_at_monotonic=(
                            runner.started_at_monotonic + policy.run_timeout_seconds
                        ),
                        termination_grace_seconds=policy.termination_grace_seconds,
                    ),
                ),
            ),
        )

        tm.that(process.outcome.raw_return_code, eq=pytest.ExitCode.OK)
        tm.fail(process.outcome.timed_out)
        tm.that(process.outcome.forwarded_signal, none=True)
        directory = TestsFlextInfraPytestFullInventory._report_directory(project)
        context = m.Infra.PytestRunContext.model_validate_json(
            (directory / "run-context.json").read_bytes(),
        )
        tm.that(context.execution_mode, eq=c.Infra.PytestExecutionMode.FULL)
        tm.that(
            context.deadline_monotonic - policy.run_timeout_seconds,
            gte=runner.started_at_monotonic,
            lte=time.monotonic(),
        )
        capture = m.Infra.GateCaptureStart.model_validate_json(
            (directory / c.Infra.GATE_CAPTURE_START_FILENAME).read_bytes(),
        )
        intent = tm.not_none(capture.intent.test_selection)
        tm.that(intent.execution_mode, eq=c.Infra.PytestExecutionMode.FULL)
        tm.that(intent.target_file, none=True)
        tm.ok(intent.profile_enabled)
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            (directory / "selection-plan.json").read_bytes(),
        )
        tm.ok(plan.whole_target)
        tm.ok(plan.inventory_collected)
        for phase in ("inventory", "selection"):
            tm.fail((directory / f"{phase}-outcome.json").exists())
        profile = directory / policy.profile_suite_filename
        output = directory / "full-profile.txt"
        tm.ok(
            validate.FlextInfraCProfileReport(
                repository_root=project,
                profile=profile,
                output=output,
                run_receipt=profile.with_suffix(".pstats.json"),
                sort=policy.profile_sort,
                limit=policy.profile_limit,
            ).execute(),
        )
        tm.that(
            output.read_text(encoding=c.DEFAULT_ENCODING),
            has="normalize",
            lacks="testmon-inventory.pstats",
        )
        tm.that(
            (project / "python-output.txt").read_text(encoding=c.DEFAULT_ENCODING),
            eq="ALPHA\nBETA",
        )
