"""Canonical pytest argv for incremental and complete-suite execution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import c, p, t, u
from flext_infra._pytest import FlextInfraPytestCollection
from flext_infra.validate._pytest_runner import FlextInfraPytestRunnerBase
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance


class FlextInfraPytestRunnerCommand(FlextInfraPytestRunnerBase):
    """Build the single supported pytest command family.

    One suite builder owns every flag. Global incremental and explicit FULL
    share the same inventory scope; incremental execution selects through
    Testmon, FULL only records into it.
    Local/slow callers retain their marker partitions. Coverage owns its
    separate measurement plugin. Every operation shares its entrypoint
    deadline across collection and execution.
    """

    _NO_COVERAGE: ClassVar[tuple[str, ...]] = ("--no-cov",)
    _COLLECTION_TIMEOUT_OPTION: ClassVar[tuple[str, ...]] = (
        f"--timeout={c.Infra.PYTEST_CASE_TIMEOUT_DISABLED_SECONDS}",
    )

    def carries_slow_items(self, execution_mode: c.Infra.PytestExecutionMode) -> bool:
        """Whether this invocation may run slow-marked items.

        The budgeted incremental phase deselects the slow marker and the slow
        phase selects it: each is its own process on its own clock
        (gate-budget law). A declared file runs its slow items. The coverage
        operation and both global modes include slow items. One predicate
        drives both the marker expression and the stop reserve, so an in-flight
        slow item always has its slow drain. Under the Make CI token the global
        incremental run is the fast tier (operator decision 2026-11-22): CI
        runs the fast tests, so slow items stay out of it.

        Returns:
            The resulting ``bool``.

        """
        fast_ci = (
            self.ci_context
            and execution_mode == c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        )
        return (
            self.slow_phase
            or self.target_file is not None
            or (execution_mode.is_global and not fast_ci)
            or execution_mode == c.Infra.PytestExecutionMode.COVERAGE
        )

    def suite_stop_monotonic(
        self,
        *,
        serial: bool = False,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.INCREMENTAL
        ),
    ) -> float | None:
        """Derive the graceful suite stop instant from the entrypoint deadline.

        Selection and inventory consume the same clock, so the instant leaves
        the typed stop reserve before the process deadline. Slow items have a
        bounded drain; ordinary items do not. The process wall still terminates
        an unfinished item and preserves its causal timeout outcome rather than
        promising a synthetic unit completion window.

        Returns:
            The stop instant, or None when the run owns no deadline.

        """
        deadline = self._deadline_monotonic(execution_mode=execution_mode)
        if deadline is None:
            return None
        pytest = self.pytest_policy()
        if self.carries_slow_items(execution_mode):
            reserve = (
                pytest.slow_serial_suite_stop_reserve_seconds
                if serial
                else pytest.slow_suite_stop_reserve_seconds
            )
        else:
            reserve = self.termination_grace_seconds
        return deadline - reserve

    def ci_excluded_markers(
        self,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.INCREMENTAL
        ),
    ) -> t.StrTuple:
        """Use the same CI token as generated workflows and pre-commit hooks.

        Returns:
            The resulting ``t.StrTuple``.

        """
        if self.ci_context and not execution_mode.is_global:
            return self.pytest_policy().ci_excluded_markers
        return ()

    def not_executed_external_gates(
        self,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.INCREMENTAL
        ),
    ) -> t.StrTuple:
        """Return the external gate markers this run deselects as NOT EXECUTED.

        Offline scopes never run them. Under the Make CI token the incremental
        global scope deselects them too: CI provides neither Docker nor remote
        services, so those cases are reported as not executed instead of being
        skipped at setup. Local incremental and FULL runs execute the complete
        applicable population: both deselect the harness gates, whose suites
        run only under the harness that provides their inputs. The harness
        scope deselects every external gate it does not select.

        Returns:
            The external gate markers deselected by this run.

        """
        pytest = self.pytest_policy()
        if execution_mode == c.Infra.PytestExecutionMode.HARNESS:
            selected = self.harness_markers()
            return tuple(
                marker
                for marker in pytest.external_gate_markers
                if marker not in selected
            )
        if not execution_mode.is_global or (
            self.ci_context and execution_mode.is_incremental
        ):
            return pytest.external_gate_markers
        return pytest.harness_gate_markers

    def harness_markers(self) -> t.StrTuple:
        """Return the harness gate markers the harness scope selects.

        Returns:
            The narrowing marker, or every declared harness gate marker.

        Raises:
            ValueError: If the repository declares no harness gate marker, or
                the narrowing marker is not one of them.

        """
        declared = self.pytest_policy().harness_gate_markers
        if not declared:
            msg = "pytest harness scope requires declared harness-gate-markers"
            raise ValueError(msg)
        if self.harness_marker is None:
            return declared
        if self.harness_marker not in declared:
            msg = (
                f"pytest harness marker {self.harness_marker!r} is not a declared"
                f" harness-gate-marker: {', '.join(declared)}"
            )
            raise ValueError(msg)
        return (self.harness_marker,)

    def testmon_environment(self, execution_mode: c.Infra.PytestExecutionMode) -> str:
        """Name the testmon environment of one marker scope on this toolchain.

        Under xdist, testmon syncs its records from the ids the workers
        collected and deletes every changed test outside them. Phases that
        deselect each other's markers inside one environment therefore erase
        each other's executions — a failed slow test vanished after the next
        budgeted run, its file then read as stable, and the slow phase passed
        without running it. testmon's environment is its declared separation
        between run configurations, so each marker scope owns one.

        Config edits never name an environment: each test records the config
        files it opens and the typed config leaves it reads as Testmon file
        dependencies (``_config_receipt_args``), so an edited YAML selects
        only its consumers. Only the elected pytest policy, which shapes the
        run itself rather than any test's behavior, keys the environment.

        Returns:
            The resulting ``str``.

        """
        scope = hashlib.sha256(
            self._marker_expression(execution_mode).encode(),
        ).hexdigest()[:8]
        policy = hashlib.sha256(
            self.pytest_policy().model_dump_json().encode(),
        ).hexdigest()[:8]
        toolchain = (
            FlextInfraWorkspaceEnvironmentProvenance.installed_toolchain_identity()
        )
        return f"toolchain-{toolchain[:12]}-{policy}-{scope}"

    def _config_receipt_args(self) -> t.StrTuple:
        """Activate per-test config dependency recording for a Testmon process.

        Returns:
            The plugin option naming the receipts directory, or nothing.

        """
        if self.config_receipts is None:
            return ()
        return (f"{c.Infra.PYTEST_CONFIG_RECEIPTS_OPTION}={self.config_receipts}",)

    def _marker_expression(self, execution_mode: c.Infra.PytestExecutionMode) -> str:
        """Return the native pytest marker expression of one execution scope.

        The phase split is a marker expression: the budgeted phase deselects
        the slow marker, the slow phase selects only it, and the harness
        scope selects only its harness gate markers.

        Returns:
            The native pytest marker expression of one execution scope.

        """
        if self.target_file is not None:
            return ""
        pytest = self.pytest_policy()
        excluded = tuple(
            dict.fromkeys((
                *self.not_executed_external_gates(execution_mode=execution_mode),
                *self.ci_excluded_markers(execution_mode=execution_mode),
                *(
                    ()
                    if self.carries_slow_items(execution_mode)
                    else (pytest.slow_marker,)
                ),
            )),
        )
        if execution_mode == c.Infra.PytestExecutionMode.HARNESS:
            selected = f"({' or '.join(self.harness_markers())})"
        elif self.slow_phase:
            selected = pytest.slow_marker
        else:
            return f"not ({' or '.join(excluded)})" if excluded else ""
        return f"{selected} and not ({' or '.join(excluded)})" if excluded else selected

    def _plugin_policy_args(
        self,
        *,
        execution_mode: c.Infra.PytestExecutionMode,
    ) -> tuple[str, ...]:
        """Apply the same configured plugin contract to collection and execution.

        Returns:
            The resulting ``tuple[str, ...],``.

        """
        expression = self._marker_expression(execution_mode)
        tool_config = self.tooling
        pytest = self.pytest_policy()
        fixture_scope = u.Infra.native_tool_setting(
            tool_config, "pytest.ini_options", "asyncio_default_fixture_loop_scope", str
        )
        return (
            "-p",
            pytest.enforcement_plugin,
            f"--timeout={pytest.ordinary_timeout_seconds}",
            "-p",
            "no:metadata",
            "-o",
            f"{c.Infra.ASYNCIO_DEFAULT_FIXTURE_LOOP_SCOPE}={fixture_scope}",
            "-o",
            f"{c.Infra.FLEXT_SLOW_TIMEOUT_SECONDS}={pytest.slow_timeout_seconds}",
            *(
                ("-o", "timeout_func_only=true")
                if pytest.item_deadline_call_only
                else ()
            ),
            *(("-m", expression) if expression else ()),
        )

    def _node_targets(self) -> t.StrTuple:
        """Return the pytest node targets of this invocation.

        A declared single-file target replaces the suite directory as the
        only node target; the default remains the configured test root.

        Returns:
            The resulting ``t.StrTuple``.

        """
        return (
            (str(self.target_file),)
            if self.target_file is not None
            else (str(self.target),)
        )

    def build_selection_command(
        self,
        *,
        report_log: Path,
        manifest_path: Path,
        complete: bool = False,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.INCREMENTAL
        ),
    ) -> tuple[str, ...]:
        """Build the read-only argv that resolves the testmon selection once.

        Every xdist worker otherwise resolves the selection itself, and two
        workers reading the database while a third writes it collect different
        sets, which xdist aborts with "Different tests were collected". This
        pass runs no test and records its collection and warning evidence.
        FULL collects in its suite and coverage owns no Testmon plugin, so
        neither runs this pass.

        Returns:
            The resulting ``tuple[str, ...],``.

        """
        testmon = (
            ()
            if not execution_mode.is_incremental
            else (
                "--testmon",
                "--testmon-nocollect",
                # Why: the external-gate deselection is a ``-m`` expression, and
                # testmon deactivates its selection whenever ``-m`` is present;
                # ``--testmon-forceselect`` is testmon's declared override for
                # exactly that case (never combined with ``--testmon-noselect``).
                *(("--testmon-noselect",) if complete else ("--testmon-forceselect",)),
                "--testmon-env",
                self.testmon_environment(execution_mode),
                *self._config_receipt_args(),
            )
        )
        pytest_arguments = (
            *self._node_targets(),
            *testmon,
            "--collect-only",
            f"{c.Infra.PYTEST_COLLECTION_MANIFEST_OPTION}={manifest_path}",
            f"--report-log={report_log}",
            "-q",
            *self._plugin_policy_args(execution_mode=execution_mode),
            "--benchmark-disable",
            "--strict-markers",
            *self._COLLECTION_TIMEOUT_OPTION,
            "-o",
            "filterwarnings=",
            "-p",
            "no:randomly",
            "-n",
            c.ParserBooleanToken.ZERO,
            "--no-cov",
        )
        if self.profile_enabled or self.collection_command_prefix:
            return (
                *(
                    self.collection_command_prefix
                    or (sys.executable, "-c", c.Infra.PYTEST_PROFILE_LAUNCHER)
                ),
                str(manifest_path.with_suffix(".pstats")),
                *pytest_arguments,
            )
        return (sys.executable, "-m", "pytest", *pytest_arguments)

    def build_command(
        self,
        report_dir: Path,
        selection_plan: p.Infra.PytestSelectionPlan | None = None,
        *,
        serialize: bool = False,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.INCREMENTAL
        ),
    ) -> tuple[str, ...]:
        """Build incremental or complete-suite argv without the coverage plugin.

        A resolved plan carries the selected IDs and their manifest together.
        Workers record dependencies without selecting those IDs a second time.
        Their ``--testmon-noselect`` freezes only the accepted selection, never
        elects the global inventory for regular incremental execution.
        A qualified fixture publishes the inventory and native selection from
        this suite's collection. FULL publishes its own inventory and records
        every item without selecting.

        Returns:
            The resulting ``tuple[str, ...],``.

        """
        pytest = self.pytest_policy()
        selection = selection_plan.node_ids if selection_plan is not None else None
        # An empty selection needs no workers, and a selection smaller than the
        # worker budget never needs more workers than items: every extra worker
        # only pays startup cost for an empty queue. Explicit serial execution
        # remains available to callers; cold and warm cache runs share the same
        # manifest.
        budget = self.parallel_worker_budget(pytest)
        if serialize or selection == ():
            workers = c.ParserBooleanToken.ZERO
        elif selection:
            workers = str(min(budget, len(selection)))
        else:
            workers = str(budget)
        # A serial dispatch keeps one item in flight, so its drain reserve is
        # the single-item budget instead of the xdist two-deep worst case.
        serial = workers in {c.ParserBooleanToken.ZERO, c.ParserBooleanToken.ONE}
        if serial:
            workers = c.ParserBooleanToken.ZERO
        manifest_args: t.StrTuple = ()
        if selection_plan is not None:
            manifest_args = (
                "-p",
                FlextInfraPytestCollection.__module__,
                (
                    f"{c.Infra.PYTEST_SELECTED_COLLECTION_OPTION}="
                    f"{selection_plan.manifest_path}"
                ),
            )
        elif execution_mode == c.Infra.PytestExecutionMode.FULL or (
            self._native_fixture_dispatch and execution_mode.is_incremental
        ):
            manifest_args = (
                "-p",
                FlextInfraPytestCollection.__module__,
                (
                    f"{c.Infra.PYTEST_COLLECTION_MANIFEST_OPTION}="
                    f"{report_dir / 'testmon-inventory.json'}"
                ),
            )
        return self._suite_argv(
            report_dir,
            limits=self._bounded_limits(workers, execution_mode=execution_mode),
            targets=(
                self._node_targets()
                if (
                    selection_plan is None
                    or selection_plan.whole_target
                    or not selection
                )
                else tuple(selection)
            ),
            workers=workers,
            trailing=(
                *self._plugin_policy_args(execution_mode=execution_mode),
                *manifest_args,
                *(
                    (
                        "--testmon",
                        *(
                            ("--testmon-noselect",)
                            if bool(selection)
                            or execution_mode == c.Infra.PytestExecutionMode.FULL
                            else ("--testmon-forceselect",)
                        ),
                        *(
                            ("--testmon-env", self.testmon_environment(execution_mode))
                            if not self._native_fixture_dispatch
                            else ()
                        ),
                        *self._config_receipt_args(),
                    )
                    if execution_mode.records_testmon
                    else ()
                ),
                *self._NO_COVERAGE,
            ),
        )

    def build_coverage_command(
        self,
        report_dir: Path,
        *,
        serialize: bool = False,
    ) -> tuple[str, ...]:
        """Build the whole-suite coverage argv (never the testmon plugin).

        The measurement source is the declared package source directory — the
        same boundary every fleet coverage config declares — so imported
        third-party/Cython modules can never emit parse warnings.

        Returns:
            The resulting ``tuple[str, ...],``.

        """
        pytest = self.pytest_policy()
        workers = (
            c.ParserBooleanToken.ZERO
            if serialize
            else str(self.parallel_worker_budget(pytest))
        )
        return self._suite_argv(
            report_dir,
            limits=self._bounded_limits(
                workers,
                execution_mode=c.Infra.PytestExecutionMode.COVERAGE,
            ),
            targets=self._node_targets(),
            workers=workers,
            trailing=(
                *self._plugin_policy_args(
                    execution_mode=c.Infra.PytestExecutionMode.COVERAGE,
                ),
                f"--cov={self.repository_root / c.Infra.DEFAULT_SRC_DIR}",
                f"--cov-report=xml:{report_dir / 'coverage.xml'}",
                "--no-cov-on-fail",
            ),
        )

    def _bounded_limits(
        self,
        workers: str,
        *,
        execution_mode: c.Infra.PytestExecutionMode,
    ) -> t.StrTuple:
        """Return the aggregate graceful suite stop deadline.

        Returns:
            The bounded suite's time-limit arguments; none for an unbounded run.

        """
        suite_stop = self.suite_stop_monotonic(
            serial=workers == c.ParserBooleanToken.ZERO,
            execution_mode=execution_mode,
        )
        return (
            ()
            if suite_stop is None
            else (f"{c.Infra.PYTEST_SUITE_STOP_OPTION}={suite_stop!r}",)
        )

    def _suite_argv(
        self,
        report_dir: Path,
        *,
        limits: Sequence[str],
        targets: Sequence[str],
        workers: str,
        trailing: Sequence[str],
    ) -> tuple[str, ...]:
        """Assemble one suite invocation; ``trailing`` owns the plugin split.

        ``limits`` carries the aggregate stop instant for this operation.

        Returns:
            The resulting ``tuple[str, ...],``.

        """
        pytest = self.pytest_policy()
        return (
            sys.executable,
            *(
                (
                    "-c",
                    c.Infra.PYTEST_PROFILE_LAUNCHER,
                    str(report_dir / pytest.profile_suite_filename),
                )
                if self.profile_enabled
                else ("-m", "pytest")
            ),
            *targets,
            *pytest.progress_args,
            *pytest.report_args,
            *limits,
            f"--maxfail={pytest.max_failures}",
            f"--junitxml={report_dir / 'junit.xml'}",
            f"--report-log={report_dir / 'events.jsonl'}",
            *trailing,
            "-n",
            workers,
            "--max-worker-restart",
            str(c.Infra.PYTEST_WORKER_RESTARTS_DISABLED),
            # Why: xdist queues the shutdown marker behind each worker's
            # pre-dispatched chunk, so the declared max-failures stop only took
            # effect after every worker drained its assigned items at fleet
            # scale. A one-item dispatch step makes that stop immediate.
            *pytest.parallel_arguments,
            "--benchmark-disable",
        )


__all__: list[str] = ["FlextInfraPytestRunnerCommand"]
