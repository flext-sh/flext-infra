"""Strict process lifecycle for the canonical pytest runner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shlex
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, override

from typing_extensions import TypeForm

from flext_infra import c, m, p, r, t, u
from flext_infra.validate import FlextInfraTestmonDbInspector
from flext_infra.validate._pytest_runner import (
    FlextInfraPytestRunnerCommand,
    FlextInfraPytestRunnerReports,
)


class FlextInfraPytestRunnerExecution(
    FlextInfraPytestRunnerCommand,
    FlextInfraPytestRunnerReports,
):
    """Execute pytest once and reject incomplete evidence."""

    def _inspect_cache(
        self,
        *,
        database: Path,
        digest: str | None,
    ) -> p.Result[p.Infra.TestmonCacheState]:
        """Run the SQLite integrity owner for the testmon database.

        Returns:
            The resulting ``p.Result[p.Infra.TestmonCacheState]``.

        """
        return FlextInfraTestmonDbInspector(
            repository_root=self.repository_root,
            db_path=database,
            pre_run_digest=digest,
        ).execute()

    def _run_pytest_process(
        self,
        command: tuple[str, ...],
        stdout_file: Path,
        *,
        execution_mode: c.Infra.PytestExecutionMode,
        phase: Literal["selection", "suite"],
        selection_manifest: Path | None = None,
    ) -> tuple[p.Result[p.Cli.ProcessOutcome], p.Cli.AtomicPhysicalTreeEntry | None]:
        """Launch one pytest child at the checkout with its process policy.

        Testmon children receive the checkout database the parent inspects.
        An inherited database location never controls a child.

        Returns:
            The process outcome and the original fixture output directory identity.

        Raises:
            ValueError: If test target has no declared project owner.

        """
        source_root = self.repository_root
        if self.target_file is not None:
            target_root = u.Infra.nearest_project_root(
                self.repository_root, self.repository_root / self.target_file
            )
            if target_root is None:
                msg = "test target has no declared project owner"
                raise ValueError(msg)
            source_root = target_root
        overrides: t.MutableStrMapping = {}
        if not self.ci_context:
            if self.fixture is None:
                inherited_path = u.Cli.process_env().get(
                    c.Infra.ORCHESTRATOR_ENV_PYTHONPATH, ""
                )
            else:
                inherited_path = ""
                source_root = self.fixture.checkout_root / source_root.relative_to(
                    self.repository_root,
                )
            overrides[c.Infra.ORCHESTRATOR_ENV_PYTHONPATH] = os.pathsep.join(
                path
                for path in (
                    str(source_root / c.Infra.DEFAULT_SRC_DIR),
                    inherited_path,
                )
                if path
            )
        if self.profile_enabled or self.collection_command_prefix:
            overrides[c.Infra.PYTEST_PROFILE_PROCESS_DIRECTORY_ENV] = (
                self.pytest_policy().profile_process_directory
            )
        if execution_mode.records_testmon and self.testmon_db is not None:
            overrides[c.Infra.PYTEST_ENV_TESTMON_DATAFILE] = str(self.testmon_db)
        inherited_keys = (
            *c.Infra.PYTEST_INHERITED_ENV_REMOVE_KEYS,
            c.Infra.PYTEST_ENV_TESTMON_DATAFILE,
        )
        options = m.Cli.ProcessOptions(
            env=overrides,
            remove_env_keys=tuple(
                key for key in inherited_keys if key not in overrides
            ),
            live=phase == "suite",
            deadline=self._process_deadline(execution_mode=execution_mode),
        )
        if self.fixture is not None:
            if not execution_mode.records_testmon:
                msg = "isolated pytest child requires Testmon"
                raise ValueError(msg)
            return self._run_fixture_process(
                command,
                stdout_file,
                options,
                output=self._pytest_child_reports(stdout_file.parent, phase),
                selection_manifest=selection_manifest,
            )
        return (
            u.Cli.run_to_file(
                command,
                stdout_file,
                cwd=self.repository_root,
                options=options,
            ),
            None,
        )

    def _run_fixture_process(
        self,
        command: tuple[str, ...],
        stdout_file: Path,
        options: m.Cli.ProcessOptions,
        *,
        output: Path,
        selection_manifest: Path | None,
    ) -> tuple[p.Result[p.Cli.ProcessOutcome], p.Cli.AtomicPhysicalTreeEntry]:
        """Launch pytest against the locked checkout with writable phase output.

        Returns:
            The native result and the identity of the directory mounted by the child.

        Raises:
            ValueError: If this launch is missing the elected Testmon state.

        """
        fixture = self.fixture
        database = self.testmon_db
        config_receipts = self.config_receipts
        if fixture is None or database is None or config_receipts is None:
            msg = "isolated pytest child has no elected Testmon state"
            raise ValueError(msg)
        u.Cli.ensure_dir(output).unwrap()
        admitted = fixture.isolation
        environment = dict(admitted.environment)
        for key in options.remove_env_keys:
            environment.pop(key, None)
        environment.update(options.env or {})
        environment.update({
            "HOME": str(output),
            c.Infra.TEMPORARY_DIRECTORY_VARIABLE: str(output),
            c.Infra.PYTEST_ENV_PYCACHE_PREFIX: str(output / c.Infra.DUNDER_PYCACHE),
        })
        inputs = admitted.runtime_files
        if selection_manifest is not None:
            inputs = (
                *inputs,
                m.Cli.AtomicFileState.model_validate(
                    u.Cli.atomic_read_binary_file_state(
                        selection_manifest, required=True
                    ).unwrap(),
                    from_attributes=True,
                ),
            )
        checkout = fixture.checkout_root
        output_inventory = m.Cli.AtomicPhysicalTreeManifest.model_validate(
            u.Cli.atomic_inventory_physical_tree(output).unwrap(),
            from_attributes=True,
        )
        isolation = m.Cli.ProcessFixtureIsolation(
            platform=admitted.platform,
            architecture=admitted.architecture,
            launcher=admitted.launcher,
            launcher_declaration=admitted.launcher_declaration,
            policy_compiler=admitted.policy_compiler,
            compiler_declaration=admitted.compiler_declaration,
            sources=admitted.sources,
            runtime_trees=admitted.runtime_trees,
            runtime_tree_roots=self.fixture_runtime_tree_roots,
            runtime_files=inputs,
            environment=tuple(environment.items()),
            output_directory=output_inventory,
            persistent_directory=m.Cli.AtomicPhysicalTreeManifest.model_validate(
                u.Cli.atomic_inventory_physical_tree(config_receipts).unwrap(),
                from_attributes=True,
            ),
            private_checkout=m.Cli.ProcessFixtureCheckout(
                backing=self._fixture_backing(database),
                source_root=self.repository_root,
                persistent_filenames=self._fixture_database_names(database),
                persistent_directory_suffix=c.Infra.PYTEST_CONFIG_RECEIPT_SUFFIX,
            ),
        )
        return (
            u.Cli.run_to_file(
                command,
                stdout_file,
                cwd=checkout,
                options=m.Cli.ProcessOptions(
                    live=options.live,
                    deadline=options.deadline,
                    isolation=isolation,
                ),
            ),
            output_inventory.root,
        )

    @staticmethod
    def _fixture_database_names(database: Path) -> t.StrTuple:
        return (
            database.name,
            *(
                f"{database.name}{suffix}"
                for suffix in c.Infra.SQLITE_DATABASE_SIDECAR_SUFFIXES
            ),
        )

    def _fixture_backing(self, database: Path) -> m.Cli.AtomicPhysicalTreeManifest:
        """Authenticate the database family before native SQLite opens it.

        Returns:
            The backing inventory admitted for the database and its sidecars.

        Raises:
            ValueError: If a database-family path is not an owned regular file.

        """
        checkout = database.parent
        inventory = m.Cli.AtomicPhysicalTreeManifest.model_validate(
            u.Cli.atomic_inventory_physical_tree(checkout).unwrap(),
            from_attributes=True,
        )
        names = self._fixture_database_names(database)
        uid = os.getuid()
        if (
            inventory.root.uid != uid
            or inventory.root.mode & 0o022
            or any(
                entry.path.parent == checkout
                and entry.path.name in names
                and (
                    entry.kind != "file"
                    or entry.link_count != 1
                    or entry.uid != uid
                    or entry.mode & 0o022
                )
                for entry in inventory.entries
            )
        ):
            msg = "pytest fixture database and sidecars require owned regular files"
            raise ValueError(msg)
        return inventory

    def _collect_selection(
        self,
        report_dir: Path,
        *,
        execution_mode: c.Infra.PytestExecutionMode,
        complete: bool = False,
    ) -> p.Infra.PytestSelectionPlan | p.Cli.ProcessOutcome:
        """Run the one read-only collection and publish its manifest artifacts.

        The collection is one deadline-bound child of the flext-cli process
        owner. An incremental one records the selection and the complete
        inventory in the same manifest; a declared file or a coverage run
        collects its complete inventory directly.

        Returns:
            The selection plan or original failed collection outcome.

        Raises:
            RuntimeError: If the incremental selection or coverage inventory
                process fails natively.

        """
        complete = complete or self.target_file is not None
        artifact = "testmon-inventory" if complete else "testmon-selection"
        selection_log = report_dir / f"{artifact}.log"
        manifest_path = report_dir / f"{artifact}.json"
        report_log = report_dir / f"{artifact}.events.jsonl"
        command = self._build_collection_launch(
            report_log,
            manifest_path,
            complete=complete,
            execution_mode=execution_mode,
        )
        if self.profile_enabled or self.collection_command_prefix:
            sys.stdout.write(
                f"pytest {artifact} profile: {manifest_path.with_suffix('.pstats')}\n",
            )
        outcome, published = self._record_process_outcome(
            report_dir,
            "inventory" if complete else "selection",
            self._run_pytest_process(
                command,
                selection_log,
                execution_mode=execution_mode,
                phase="selection",
            ),
            report_log=report_log,
            raw_log=selection_log,
        )
        if not published:
            return outcome
        # Exit code 5 is pytest's "no tests ran": testmon selected nothing.
        # For a zero-test project (no test module under the config-owned
        # roots) rc=5 is the DECLARED inventory outcome in both phases.
        owns_no_tests = (
            outcome.raw_return_code == c.Infra.PytestExitCode.NO_TESTS_COLLECTED
            and self._owns_no_tests()
        )
        # A slow phase may own no slow item, a harness scope may own no harness
        # gate, and a declared file may sit entirely outside this phase's
        # marker. All are empty scopes; the harness caller fails a run that
        # executes no harness item at all. A whole-suite budgeted inventory
        # that collects nothing stays a failure.
        scope_may_be_empty = self._scope_may_be_empty(execution_mode)
        # The selection pass executes the collected items only to fingerprint
        # their dependencies. An item failure is the suite's outcome, not a
        # failed collection: the manifest is still complete, and the real suite
        # run must follow and report it. Collection errors remain fatal.
        accepted: set[c.Infra.PytestExitCode] = {
            c.Infra.PytestExitCode.OK,
            c.Infra.PytestExitCode.TESTS_FAILED,
        } | (
            set()
            if complete and not scope_may_be_empty
            else {c.Infra.PytestExitCode.NO_TESTS_COLLECTED}
        )
        if owns_no_tests:
            accepted = {
                c.Infra.PytestExitCode.OK,
                c.Infra.PytestExitCode.NO_TESTS_COLLECTED,
            }
        if (
            outcome.raw_return_code not in accepted
            or outcome.timed_out
            or outcome.forwarded_signal is not None
        ):
            if (
                not outcome.timed_out
                and outcome.forwarded_signal is None
                and outcome.raw_return_code >= 0
            ):
                self._write_collection_failure(
                    report_dir,
                    phase="inventory" if complete else "selection",
                    report_log=report_log,
                    raw_log=selection_log,
                    outcome=outcome,
                )
                if (
                    not complete
                    or execution_mode == c.Infra.PytestExecutionMode.COVERAGE
                ):
                    detail = selection_log.read_text(
                        encoding=c.DEFAULT_ENCODING,
                    ).strip()
                    msg = (
                        f"testmon selection failed "
                        f"({outcome.raw_return_code}): {detail}"
                    )
                    raise RuntimeError(msg)
            return outcome
        if self.profile_enabled or self.collection_command_prefix:
            self._bind_child_profile(report_dir, manifest_path.with_suffix(".pstats"))
        if not owns_no_tests:
            self._collection_diagnostics(report_log)
        if (
            owns_no_tests
            and outcome.raw_return_code == c.Infra.PytestExitCode.NO_TESTS_COLLECTED
        ):
            # No manifest artifact is produced for an empty declared suite.
            return m.Infra.PytestSelectionPlan(
                manifest_path=manifest_path,
                node_ids=(),
                whole_target=True,
                inventory_collected=complete,
                owns_no_tests=True,
            )
        manifest = m.Infra.PytestCollectionManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8"),
        )
        inventory = self._manifest_inventory(
            manifest,
            no_tests_collected=(
                outcome.raw_return_code == c.Infra.PytestExitCode.NO_TESTS_COLLECTED
            ),
            empty_allowed=owns_no_tests or scope_may_be_empty,
        )
        u.Cli.atomic_write_text_file(
            report_dir / f"{artifact}.txt",
            "\n".join(manifest.node_ids) + "\n",
        ).unwrap()
        return m.Infra.PytestSelectionPlan(
            manifest_path=manifest_path,
            node_ids=manifest.node_ids,
            whole_target=set(manifest.node_ids) == set(inventory),
            inventory_collected=complete,
            # An empty complete inventory in an allowed scope owns no in-scope
            # test. Collection diagnostics already ran, so a collection failure
            # never becomes this receipt.
            owns_no_tests=owns_no_tests or (not inventory and scope_may_be_empty),
        )

    def _build_collection_launch(
        self,
        report_log: Path,
        manifest_path: Path,
        *,
        complete: bool,
        execution_mode: c.Infra.PytestExecutionMode,
    ) -> tuple[str, ...]:
        """Build collection argv with its independently owned child outputs.

        Returns:
            The exact argv for the collection subprocess.

        """
        output = self._pytest_child_reports(report_log.parent, "selection")
        return self._pytest_child_argv(
            self.build_selection_command(
                report_log=output / report_log.name,
                manifest_path=output / manifest_path.name,
                complete=complete,
                execution_mode=execution_mode,
            ),
            output,
        )

    @staticmethod
    def _manifest_inventory(
        manifest: p.Infra.PytestCollectionManifest,
        *,
        no_tests_collected: bool,
        empty_allowed: bool,
    ) -> t.StrTuple:
        """Return the complete inventory the one manifest selected from.

        An incremental collection records it beside the selection; every other
        manifest is its own complete collection.

        Returns:
            The complete inventory node IDs.

        Raises:
            RuntimeError: If pytest reports no collection with a nonempty
                manifest; if the complete inventory holds no test outside an
                allowed empty scope; or if the selection lies outside it.

        """
        if no_tests_collected and manifest.node_ids:
            msg = "pytest reported no collection with a nonempty manifest"
            raise RuntimeError(msg)
        inventory = manifest.inventory_node_ids or manifest.node_ids
        if not inventory and not empty_allowed:
            msg = "complete pytest inventory must contain at least one test"
            raise RuntimeError(msg)
        if not set(manifest.node_ids).issubset(inventory):
            msg = "testmon selected node IDs outside the complete collection inventory"
            raise RuntimeError(msg)
        return inventory

    def _owns_no_tests(self) -> bool:
        """Return whether the project owns zero test files by design.

        The config-owned collection roots (``pytest.test-paths`` SSOT) contain
        no test module at all: an empty suite is the declared topology (a
        content-only workspace shell), not a broken collection. A project that
        DOES own test files but collects nothing keeps the loud failure —
        zero-execution of an existing suite is never a silent pass (law 14).

        Returns:
            Whether the project owns zero test files by design.

        """
        # The module patterns are the pytest SSOT's own python-files: a
        # project whose suites use another declared form (``*_tests.py``)
        # still owns its tests, and a hardcoded copy of the list here would
        # answer "owns no tests" for a live suite again.
        tool_config = self.tooling
        patterns = u.Infra.native_tool_setting(
            tool_config, "pytest.ini_options", "python_files", TypeForm(Sequence[str])
        )
        roots = u.Infra.native_tool_setting(
            tool_config, "pytest.ini_options", "testpaths", TypeForm(Sequence[str])
        )
        for root in roots:
            base = self.repository_root / root
            if not base.is_dir():
                continue
            for pattern in patterns:
                if any(base.rglob(pattern)):
                    return False
        return True

    def _scope_may_be_empty(self, execution_mode: c.Infra.PytestExecutionMode) -> bool:
        return (
            self.slow_phase
            or self.target_file is not None
            or execution_mode == c.Infra.PytestExecutionMode.HARNESS
        )

    def _process_deadline(
        self, *, execution_mode: c.Infra.PytestExecutionMode
    ) -> p.Cli.ProcessDeadline | None:
        """Use the suite clock for selection, execution, and cleanup.

        Returns:
            The absolute deadline shared by every phase of this operation;
            FULL owns none.

        """
        expires = self._deadline_monotonic(execution_mode=execution_mode)
        if expires is None:
            return None
        return m.Cli.ProcessDeadline(
            expires_at_monotonic=expires,
            termination_grace_seconds=self.termination_grace_seconds,
        )

    def _pytest_child_argv(
        self,
        command: tuple[str, ...],
        child_reports: Path,
    ) -> tuple[str, ...]:
        if self.fixture is None:
            return command
        cache = child_reports / c.Infra.PYTEST_CACHE_DIRECTORY
        return (
            *command,
            "-o",
            f"cache_dir={cache}",
            c.Infra.PYTEST_BENCHMARK_STORAGE_OPTION,
            f"file://{child_reports}",
        )

    def _run_suite(
        self,
        command: tuple[str, ...],
        report_dir: Path,
        *,
        execution_mode: c.Infra.PytestExecutionMode,
        selection_manifest: Path | None = None,
    ) -> tuple[p.Cli.ProcessOutcome, bool]:
        """Execute one suite argv under the shared deadline and environment.

        Returns:
            The native outcome and the result of report publication.

        """
        child_reports = self._pytest_child_reports(report_dir, "suite")
        command = self._pytest_child_argv(command, child_reports)
        u.Cli.atomic_write_text_file(
            report_dir / "command.txt",
            f"{shlex.join(command)}\n",
        ).unwrap()
        capture = u.Infra.git_begin_gate_capture(
            m.Infra.GateCaptureBeginRequest(
                repository_root=self.repository_root,
                gate=c.Infra.VERB_TEST,
                command=command,
                intent=m.Infra.GateExecutionIntent(
                    test_selection=m.Infra.GateTestIntent(
                        execution_mode=execution_mode,
                        target=self.target,
                        target_file=self.target_file,
                        ci_context=self.ci_context,
                        slow_phase=self.slow_phase,
                        profile_enabled=self.profile_enabled,
                    ),
                ),
                runtime_identity=self.testmon_environment(execution_mode),
            ),
            inputs=u.Infra.load_codegen_inputs(self.repository_root).unwrap(),
        )
        u.Cli.atomic_write_text_file(
            report_dir / c.Infra.GATE_CAPTURE_START_FILENAME,
            capture.model_dump_json(round_trip=True) + "\n",
        ).unwrap()
        outcome, published = self._record_process_outcome(
            report_dir,
            "suite",
            self._run_pytest_process(
                command,
                report_dir / "pytest.log",
                execution_mode=execution_mode,
                phase="suite",
                selection_manifest=selection_manifest,
            ),
            report_log=report_dir / "events.jsonl",
            raw_log=report_dir / "pytest.log",
        )
        if published and self.profile_enabled:
            policy = self.pytest_policy()
            suite_profile = report_dir / policy.profile_suite_filename
            # The process owner has reaped the child before binding its native
            # checkpoints. An interrupted run retains its failure and real data.
            if (
                suite_profile.is_file()
                or u.Cli.process_succeeded(outcome)
                or self._completed_failure(outcome, report_dir)
            ):
                self._bind_child_profile(report_dir, suite_profile)
            for profile in sorted(
                (report_dir / policy.profile_process_directory).glob("*.pstats")
            ):
                self._bind_child_profile(report_dir, profile)
        return outcome, published

    def _record_process_outcome(
        self,
        report_dir: Path,
        phase: str,
        process: tuple[
            p.Result[p.Cli.ProcessOutcome],
            p.Cli.AtomicPhysicalTreeEntry | None,
        ],
        *,
        report_log: Path,
        raw_log: Path,
    ) -> tuple[p.Cli.ProcessOutcome, bool]:
        """Preserve the process owner's causal fields even when JUnit is absent.

        A failed process cleanup still carries the observed exit, timeout and
        forwarded signal in ``error_data``; that outcome is recorded like any
        other, so a timed-out suite keeps its receipt.

        Returns:
            The recorded process outcome and the result of report publication.

        Raises:
            OSError: If a successful child left an inaccessible report.
            RuntimeError: If the process reported no outcome, if a zero return
                code follows an interrupted lifecycle, or if a successful
                process left a cleanup failure.
            ValueError: If a successful child left an invalid report identity.

        """
        run, output_identity = process
        if run.success:
            outcome = run.value
        else:
            data = run.error_data or {}
            exit_code = data.get(c.Cli.PROCESS_EXIT_CODE_KEY)
            if not isinstance(exit_code, int):
                msg = f"pytest {phase} process reported no outcome: {run.error}"
                raise RuntimeError(msg)
            signal = data.get(c.Cli.PROCESS_FORWARDED_SIGNAL_KEY)
            outcome = m.Cli.ProcessOutcome(
                raw_return_code=exit_code,
                timed_out=data.get(c.Cli.PROCESS_TIMED_OUT_KEY) is True,
                forwarded_signal=signal if isinstance(signal, int) else None,
            )
            sys.stderr.write(f"pytest {phase} process cleanup: {run.error}\n")
        recorded = m.Cli.ProcessOutcome.model_validate(outcome, from_attributes=True)
        receipt = report_dir / f"{phase}-outcome.json"
        u.Cli.atomic_write_text_file(
            receipt,
            recorded.model_dump_json(indent=2) + "\n",
        ).unwrap()
        if output_identity is not None:
            try:
                self._publish_fixture_reports(
                    report_dir, output_identity, phase, report_log.name
                )
            except (OSError, RuntimeError, ValueError) as error:
                sys.stderr.write(f"pytest {phase} report publication: {error}\n")
                if outcome.raw_return_code in {
                    c.Infra.PytestExitCode.OK,
                    c.Infra.PytestExitCode.NO_TESTS_COLLECTED,
                }:
                    raise
                return outcome, False
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code < 0
        ):
            self._write_collection_failure(
                report_dir,
                phase=phase,
                report_log=report_log,
                raw_log=raw_log,
                outcome=outcome,
            )
        if not u.Cli.process_succeeded(outcome):
            sys.stderr.write(
                f"pytest {phase}: raw_return_code={outcome.raw_return_code} "
                f"timed_out={outcome.timed_out} "
                f"forwarded_signal={outcome.forwarded_signal}; receipt={receipt}\n",
            )
        if outcome.raw_return_code == 0 and not u.Cli.process_succeeded(outcome):
            msg = (
                f"pytest {phase} reported zero after an interrupted "
                f"lifecycle: {receipt}"
            )
            raise RuntimeError(msg)
        if run.failure and u.Cli.process_succeeded(outcome):
            msg = f"pytest {phase} succeeded but its cleanup failed: {run.error}"
            raise RuntimeError(msg)
        return outcome, True

    @staticmethod
    def _interrupted_suite(outcome: p.Cli.ProcessOutcome) -> bool:
        """Return whether the suite lifecycle ended before its natural end.

        An interrupted suite may leave its last dispatched item in setup with
        no call or teardown report; diagnostics retain that tail as reported
        but not executed so the accounting publishes the executed prefix as
        incomplete instead of rejecting the whole run.

        Returns:
            Whether the suite lifecycle was interrupted.

        """
        return (
            outcome.timed_out
            or outcome.raw_return_code < 0
            or outcome.raw_return_code == c.Infra.PytestExitCode.INTERRUPTED
        )

    @staticmethod
    def _completed_failure(outcome: p.Cli.ProcessOutcome, report_dir: Path) -> bool:
        """Return whether a failing suite still finished its lifecycle.

        Under xdist the declared max-failures stop exits as Interrupted, not
        TestsFailed; it is still one completed suite lifecycle whose bounded
        evidence must be published. The process deadline's interruption
        unwinds the suite through pytest's own handlers, so a timed-out
        suite that wrote its final JUnit report also finished its lifecycle
        and publishes its executed prefix, including when the remaining
        termination escalation records the native signal exit. A timed-out
        suite whose JUnit holds no testcase has no prefix: it is the
        unfinished timeout. An operator signal keeps forwarded_signal set and
        never qualifies. A startup interruption has no final JUnit report and
        must retain its native failure without suite finalization.

        Returns:
            Whether a failing suite still finished its lifecycle.

        """
        junit = report_dir / "junit.xml"
        # An empty file is a report pytest never wrote: the deadline cut the
        # suite before its final JUnit, so the native timeout stays the cause.
        if (
            outcome.forwarded_signal is not None
            or not junit.is_file()
            or not junit.stat().st_size
        ):
            return False
        if outcome.raw_return_code in c.Infra.PYTEST_COMPLETED_FAILURES:
            return True
        root = u.Infra.junit_report_root(junit)
        return (
            outcome.raw_return_code < 0
            and root is not None
            and next(root.iter("testcase"), None) is not None
        )

    @staticmethod
    def _record_cache_state(
        report_dir: Path,
        name: str,
        state: p.Infra.TestmonCacheState,
    ) -> None:
        """Persist one testmon integrity decision before it is acted upon."""
        u.Cli.atomic_write_text_file(
            report_dir / f"{name}.json",
            state.model_dump_json(indent=2) + "\n",
        ).unwrap()

    def _finalize(
        self,
        report_dir: Path,
        *,
        cache_restored: bool = False,
        raw_return_code: int = 0,
        cache_hit: bool = False,
        interrupted: bool,
    ) -> p.Result[int]:
        """Reject incomplete evidence and publish one bounded summary.

        Args:
            report_dir: The report directory of the run.
            cache_restored: Whether a testmon cache was restored.
            raw_return_code: The native process exit status.
            cache_hit: Whether the run was a verified incremental cache hit.
            interrupted: Whether the suite ended before its natural end.

        Returns:
            The resulting ``p.Result[int]``.

        Raises:
            RuntimeError: If zero execution is accepted only for a verified incremental
                cache hit; or if a testmon cache hit cannot contain executed tests.

        """
        diagnostics = self._diagnostics(
            report_dir,
            interrupted=interrupted,
        ).unwrap()
        accounting = self._accounting(
            report_dir / "junit.xml",
            report_dir / "pytest.log",
            cache_restored=cache_restored,
            reported_count=len(diagnostics.reported_node_ids),
        ).unwrap()
        context = m.Infra.PytestRunContext.model_validate_json(
            (report_dir / "run-context.json").read_text(encoding="utf-8"),
        )
        # The zero-test receipt travels on the typed accounting the reports
        # owner parsed from the durable selection plan.
        if (
            not accounting.executed_count
            and not accounting.owns_no_tests
            and not (
                cache_hit
                and context.execution_mode.is_incremental
                and raw_return_code
                in {
                    c.Infra.PytestExitCode.OK,
                    c.Infra.PytestExitCode.NO_TESTS_COLLECTED,
                }
            )
        ):
            msg = "zero execution is accepted only for a verified incremental cache hit"
            raise RuntimeError(msg)
        if cache_hit and accounting.executed_count:
            msg = "a testmon cache hit cannot contain executed tests"
            raise RuntimeError(msg)
        phases = self._phase_diagnostics(report_dir, context=context, suite=diagnostics)
        self._write_diagnostics(report_dir, diagnostics, phases=phases)
        warnings = sum(item.warning_count for _, item in phases)
        accounting_complete = (
            accounting.executed_count == accounting.reported_count
            and (
                accounting.inventory_count is None
                or accounting.executed_count + accounting.deselected_count
                == accounting.inventory_count
            )
        )
        markdown_complete = (
            True
            if context.execution_mode == c.Infra.PytestExecutionMode.COVERAGE
            else self._reconcile_markdown(
                report_dir,
                diagnostics,
                cache_hit=cache_hit,
            )
        )
        rejected = any((
            diagnostics.failed_count,
            diagnostics.error_count,
            warnings,
            # A connectivity prerequisite skip reports its unmet external
            # service as not executed; every other skip stays red (operator
            # decision 2026-11-08, AGENTS.md connectivity rule 2026-10-10).
            diagnostics.skipped_count > len(diagnostics.connectivity_skip_cases),
            diagnostics.collection_failed_count,
            diagnostics.collection_skipped_count,
            not accounting_complete,
            not markdown_complete,
        ))
        accepted_cache_hit = cache_hit and not rejected and not accounting.owns_no_tests
        selected_count = (
            None
            if accounting.inventory_count is None
            else accounting.inventory_count - accounting.deselected_count
        )
        final_exit = (
            0
            if accepted_cache_hit
            else raw_return_code or int(rejected or accounting.owns_no_tests)
        )
        # A graceful stop at the suite stop instant publishes the executed
        # prefix and remains red: the unexecuted remainder is the next run's
        # testmon selection.
        if final_exit and (
            selected_count is not None
            and accounting.executed_count < selected_count
            and not (diagnostics.failed_count or diagnostics.error_count)
        ):
            result = "incomplete"
        elif final_exit:
            result = "failed"
        elif accepted_cache_hit:
            result = "cache_hit"
        else:
            result = "executed"
        summary = (
            f"outcome={result}\n"
            f"selected={selected_count}\n"
            f"executed={accounting.executed_count}\n"
            f"reported={accounting.reported_count}\n"
            f"accounting_complete={accounting_complete}\n"
            f"deselected={accounting.deselected_count}\n"
            f"inventory={accounting.inventory_count}\n"
            f"not_executed_external_gates={self._external_gate_markers(context)}\n"
            f"not_executed_ci_markers={self._ci_marker_list(context)}\n"
            f"cache_restored={cache_restored}\n"
            f"failed={diagnostics.failed_count}\nerrors={diagnostics.error_count}\n"
            f"warnings={warnings}\n"
            f"{self._phase_warning_lines(phases)}"
            f"skipped={diagnostics.skipped_count}\n"
            f"connectivity_prerequisite_skips={len(diagnostics.connectivity_skip_cases)}\n"
            f"collection_errors={diagnostics.collection_failed_count}\n"
            f"collection_skips={diagnostics.collection_skipped_count}\n"
            f"exit={final_exit}\n"
        )
        u.Cli.atomic_write_text_file(
            report_dir / "run-accounting.json",
            accounting.model_dump_json(indent=2) + "\n",
        ).unwrap()
        u.Cli.atomic_write_text_file(report_dir / "summary.txt", summary).unwrap()
        self._capture_original_suite(report_dir)
        sys.stderr.write(f"Reports: {report_dir}\n")
        if (
            self.target_file is not None
            and rejected
            and final_exit == c.Infra.PytestExitCode.NO_TESTS_COLLECTED
        ):
            msg = f"empty file phase has rejected evidence: {report_dir}"
            raise RuntimeError(msg)
        return r.ok(final_exit)

    def _capture_original_suite(self, report_dir: Path) -> None:
        """Bind the already executed suite to its original typed reports.

        Args:
            report_dir: The directory containing the report files.

        Raises:
            ValueError: If the original suite checkpoint has no native test selection.

        """
        start = m.Infra.GateCaptureStart.model_validate_json(
            u.Cli.files_read_binary(
                report_dir / c.Infra.GATE_CAPTURE_START_FILENAME,
            ).unwrap(),
        )
        outcome = m.Cli.ProcessOutcome.model_validate_json(
            u.Cli.files_read_binary(report_dir / "suite-outcome.json").unwrap(),
        )
        reports = u.Infra.git_capture_report_bindings(
            start.repository_root,
            (
                (
                    report_dir / "suite-outcome.json",
                    c.Infra.GateEvidenceReportKind.PYTEST_PROCESS,
                ),
                (
                    report_dir / "run-accounting.json",
                    c.Infra.GateEvidenceReportKind.PYTEST_ACCOUNTING,
                ),
                (
                    report_dir / "diagnostics.json",
                    c.Infra.GateEvidenceReportKind.PYTEST_DIAGNOSTICS,
                ),
                (
                    report_dir / "run-context.json",
                    c.Infra.GateEvidenceReportKind.PYTEST_CONTEXT,
                ),
            ),
        ).unwrap()
        selection = start.intent.test_selection
        if selection is None:
            msg = "original suite checkpoint has no native test selection"
            raise ValueError(msg)
        u.Infra.git_finish_gate_capture(
            m.Infra.GateCaptureFinishRequest.model_validate({
                "started": start,
                "process": outcome,
                "reports": reports,
                "report_root": report_dir,
                "runtime_identity": self.testmon_environment(selection.execution_mode),
            }),
            inputs=u.Infra.load_codegen_inputs(self.repository_root),
        ).unwrap()

    def _external_gate_markers(self, context: p.Infra.PytestRunContext) -> str:
        """Return the not-executed external gate marker list of one run.

        Returns:
            The not-executed external gate marker list of one run.

        """
        return ",".join(
            self.not_executed_external_gates(execution_mode=context.execution_mode),
        )

    def _ci_marker_list(self, context: p.Infra.PytestRunContext) -> str:
        """Return the CI-excluded marker list of one run.

        Returns:
            The CI-excluded marker list of one run.

        """
        return ",".join(
            self.ci_excluded_markers(
                execution_mode=context.execution_mode,
            ),
        )

    @staticmethod
    def _phase_warning_lines(
        phases: Sequence[tuple[str, p.Infra.PytestDiagnostics]],
    ) -> str:
        """Return one warnings line per phase.

        Returns:
            One warnings line per phase.

        """
        return "".join(
            f"{phase}_warnings={item.warning_count}\n" for phase, item in phases
        )

    @override
    def execute(self) -> p.Result[int]:
        """Execute applicable Testmon impact selection independently of checks.

        Slow items remain eligible without replaying unchanged cases.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return self.execute_global()

    @classmethod
    def execute_project_context(
        cls,
        context: p.Infra.WorkspaceProjectContext,
        *,
        started_at_monotonic: float,
        target_file: Path | None = None,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
        harness_marker: str | None = None,
    ) -> int:
        """Execute the project's global suite; pytest owns its basetemp.

        Returns:
            The unchanged native status.

        Raises:
            ValueError: Rejects nonglobal modes or changed inputs between suites.

        """
        if not execution_mode.is_global:
            msg = f"project context requires a global pytest mode: {execution_mode}"
            raise ValueError(msg)
        runner = cls.from_project_context(
            context,
            started_at_monotonic=started_at_monotonic,
            target_file=target_file,
            execution_mode=execution_mode,
            harness_marker=harness_marker,
        )
        if execution_mode == c.Infra.PytestExecutionMode.HARNESS:
            # Reject an undeclared narrowing marker before any collection.
            runner.harness_markers()
        return runner.execute_global(execution_mode=execution_mode).unwrap()

    def execute_full(self) -> p.Result[int]:
        """Run the complete suite once independently of quality-check receipts.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return self.execute_global(execution_mode=c.Infra.PytestExecutionMode.FULL)

    def execute_global(
        self,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
    ) -> p.Result[int]:
        """Select impacted global cases independently of quality checks.

        Explicit FULL executes its complete inventory once and records it
        under its own Testmon environment, which locally is the global
        incremental one, so one FULL run warms a cold lane. Both operations
        retain the same marker inventory and native execution evidence.

        Returns:
            The native status with selection, inventory and execution evidence.

        Raises:
            ValueError: If the requested mode does not own the global inventory.

        """
        if not execution_mode.is_global:
            msg = f"global pytest operation requires a global mode: {execution_mode}"
            raise ValueError(msg)
        runner = self._fixture_runner_for_mode(execution_mode)
        return FlextInfraPytestRunnerExecution._execute_testmon(
            runner, execution_mode=execution_mode
        )

    def execute_file(self) -> p.Result[int]:
        """Run and record the complete declared file once.

        Returns:
            The native status of the complete file execution.

        Raises:
            ValueError: If no single-file target was declared.

        """
        if self.target_file is None:
            msg = "complete file execution requires a declared target file"
            raise ValueError(msg)
        return self.execute_full()

    def _execute_complete_suite(
        self, *, report_dir: Path, database: Path
    ) -> p.Result[int]:
        """Run, record and account for one complete suite.

        Testmon selects nothing; it records every executed item in its native
        database, so the incremental run of the same marker scope starts warm.

        Returns:
            The original suite status after its complete-inventory evidence.

        """
        mode = c.Infra.PytestExecutionMode.FULL
        pre_digest = (
            None
            if self.fixture is None
            else FlextInfraTestmonDbInspector.digest_file(database)
        )
        outcome, published = self._run_suite(
            self.build_command(
                self._pytest_child_reports(report_dir, "suite"),
                execution_mode=mode,
            ),
            report_dir,
            execution_mode=mode,
        )
        if not published:
            return self._unfinished_result(outcome, report_dir)
        selection = self._selection_from_suite(report_dir, outcome)
        if isinstance(selection, p.Cli.ProcessOutcome):
            return r.ok(selection.raw_return_code)
        self._record_selection_plan(selection, report_dir, cache_restored=False)
        if not u.Cli.process_succeeded(outcome) and not self._completed_failure(
            outcome, report_dir
        ):
            return self._unfinished_result(outcome, report_dir)
        if self.fixture is not None:
            state = self._inspect_cache(database=database, digest=pre_digest).unwrap()
            self._record_cache_state(report_dir, "cache-after", state)
        return self._finalize(
            report_dir,
            raw_return_code=outcome.raw_return_code,
            interrupted=self._interrupted_suite(outcome),
        )

    def _execute_testmon(
        self,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.INCREMENTAL
        ),
    ) -> p.Result[int]:
        """Execute one Testmon phase, selected or FULL, on the native database.

        Returns:
            The resulting ``p.Result[int]``.

        Raises:
            ValueError: If incremental pytest has no Testmon database.

        """
        database = self.testmon_db
        if database is None:
            msg = "incremental pytest requires its Testmon database"
            raise ValueError(msg)
        slow_marker = self.pytest_policy().slow_marker
        if self.slow_phase and slow_marker in self.ci_excluded_markers(
            execution_mode=execution_mode,
        ):
            # The CI context deselects the slow marker by declaration, so its
            # phase is typed NOT EXECUTED here, never a selection of nothing.
            sys.stderr.write(
                f"pytest slow phase NOT EXECUTED: ci-excluded-markers declares "
                f"{slow_marker!r}\n",
            )
            return r.ok(
                int(c.Infra.PytestExitCode.NO_TESTS_COLLECTED)
                if self.target_file is not None
                else 0,
            )
        if self.fixture is not None:
            return self._execute_testmon_fixture(database, execution_mode)
        return self._execute_testmon_checkout(database, execution_mode)

    def _execute_testmon_fixture(
        self, database: Path, execution_mode: c.Infra.PytestExecutionMode
    ) -> p.Result[int]:
        """Own the checkout lease through process settlement and SQLite inspection.

        Returns:
            The original Testmon phase status.

        Raises:
            ValueError: If the checkout does not have a private lease authority.

        """
        checkout = database.parent
        authority = checkout.parent
        config_receipts = self.config_receipts
        status = authority.stat()
        lease_path = authority / f"{checkout.name}.testmon.lock"
        if (
            status.st_uid != os.getuid()
            or status.st_mode & 0o077
            or lease_path.is_symlink()
            or config_receipts is None
            or config_receipts.is_symlink()
        ):
            msg = "pytest fixture requires a private checkout lease directory"
            raise ValueError(msg)
        deadline = self._deadline_monotonic(execution_mode=execution_mode)
        remaining = None if deadline is None else max(0.0, deadline - time.monotonic())
        with u.Cli.file_changes_lock(lease_path).acquire(timeout=remaining):
            self._fixture_backing(database)
            u.Cli.ensure_dir(config_receipts).unwrap()
            return self._execute_testmon_checkout(database, execution_mode)

    def _execute_testmon_checkout(
        self, database: Path, execution_mode: c.Infra.PytestExecutionMode
    ) -> p.Result[int]:
        """Run every phase and its evidence against the elected Testmon database.

        Returns:
            The original Testmon phase status.

        """
        report_dir = self._report_directory()
        self._write_run_context(
            report_dir,
            m.Infra.PytestRunContext(
                execution_mode=execution_mode,
                isolated_fixture=self.fixture is not None,
                testmon_db=database,
                deadline_monotonic=self._deadline_monotonic(
                    execution_mode=execution_mode,
                ),
                report_directory=report_dir,
            ),
        )
        if execution_mode == c.Infra.PytestExecutionMode.FULL:
            return self._execute_complete_suite(
                report_dir=report_dir,
                database=database,
            )
        return self._execute_incremental(
            database=database,
            execution_mode=execution_mode,
            report_dir=report_dir,
        )

    def _execute_incremental(
        self,
        *,
        database: Path,
        execution_mode: c.Infra.PytestExecutionMode,
        report_dir: Path,
    ) -> p.Result[int]:
        """Run incremental pytest on its native database.

        A qualified fixture observes native selection in the suite itself.
        The same checkout database remains authoritative through finalization.

        Returns:
            The resulting ``p.Result[int]``.

        """
        pre_digest = FlextInfraTestmonDbInspector.digest_file(database)
        cache_restored = self._preflight_cache(pre_digest, report_dir, database)
        selection_plan: p.Infra.PytestSelectionPlan | None = None
        if not self._native_fixture_dispatch:
            observed = self._collect_selection(
                report_dir, execution_mode=execution_mode
            )
            if isinstance(observed, p.Cli.ProcessOutcome):
                return r.ok(observed.raw_return_code)
            selection_plan = observed
            self._record_selection_plan(
                selection_plan, report_dir, cache_restored=cache_restored
            )
        command = self.build_command(
            self._pytest_child_reports(report_dir, "suite"),
            selection_plan,
            execution_mode=execution_mode,
        )
        outcome, published = self._run_suite(
            command,
            report_dir,
            execution_mode=execution_mode,
            selection_manifest=(
                selection_plan.manifest_path
                if selection_plan is not None
                and (
                    not selection_plan.owns_no_tests
                    or selection_plan.manifest_path.is_file()
                )
                else None
            ),
        )
        if not published:
            return self._unfinished_result(outcome, report_dir)
        if selection_plan is None:
            observed = self._selection_from_suite(
                report_dir, outcome, execution_mode=execution_mode
            )
            if isinstance(observed, p.Cli.ProcessOutcome):
                return self._unfinished_result(observed, report_dir)
            selection_plan = observed
            self._record_selection_plan(
                selection_plan, report_dir, cache_restored=cache_restored
            )
        selection = selection_plan.node_ids
        # A declared file executes its complete collected inventory, so an empty
        # incremental suite selection never grants a cache hit to a file request.
        cache_hit = (
            self.target_file is None
            and outcome.raw_return_code
            in {c.Infra.PytestExitCode.OK, c.Infra.PytestExitCode.NO_TESTS_COLLECTED}
            and not outcome.timed_out
            and outcome.forwarded_signal is None
            and not selection
            and cache_restored
            and not selection_plan.owns_no_tests
        )
        # A zero-test project (empty suite by declared design) completes its
        # lifecycle with pytest's NO_TESTS_COLLECTED: the run must reach the
        # finalizer so the typed receipt is published instead of a bare rc=5.
        completed_zero_tests = (
            selection_plan.owns_no_tests
            and outcome.raw_return_code
            in {c.Infra.PytestExitCode.OK, c.Infra.PytestExitCode.NO_TESTS_COLLECTED}
            and not outcome.timed_out
            and outcome.forwarded_signal is None
        )
        if (
            not u.Cli.process_succeeded(outcome)
            and not cache_hit
            and not completed_zero_tests
            and not self._completed_failure(outcome, report_dir)
        ):
            return self._unfinished_result(outcome, report_dir)
        state = self._inspect_cache(database=database, digest=pre_digest).unwrap()
        self._record_cache_state(report_dir, "cache-after", state)
        return self._finalize(
            report_dir,
            cache_restored=cache_restored,
            raw_return_code=outcome.raw_return_code,
            cache_hit=cache_hit,
            interrupted=self._interrupted_suite(outcome),
        )

    def _preflight_cache(
        self, pre_digest: str | None, report_dir: Path, database: Path
    ) -> bool:
        """Require a restored cache whenever a testmon database already exists.

        Returns:
            True when an existing database was inspected and accepted.

        Raises:
            RuntimeError: If testmon preflight rejected the cache.

        """
        if pre_digest is None:
            return False
        pre_state = self._inspect_cache(database=database, digest=pre_digest).unwrap()
        self._record_cache_state(report_dir, "cache-before", pre_state)
        if not pre_state.restored_accepted:
            msg = f"testmon preflight rejected cache: {pre_state.reason}"
            raise RuntimeError(msg)
        return True

    def _record_selection_plan(
        self,
        selection_plan: p.Infra.PytestSelectionPlan,
        report_dir: Path,
        *,
        cache_restored: bool,
    ) -> None:
        """Persist the resolved plan and require a cache for an empty selection.

        A declared file executes its complete collected scope even when
        incremental selection would be empty.

        Raises:
            RuntimeError: If empty incremental selection requires an integrity-checked
                cache.

        """
        u.Cli.atomic_write_text_file(
            report_dir / "selection-plan.json",
            selection_plan.model_dump_json(indent=2) + "\n",
        ).unwrap()
        if (
            not selection_plan.node_ids
            and not cache_restored
            and not selection_plan.owns_no_tests
            and not (
                self.target_file is not None and selection_plan.inventory_collected
            )
        ):
            msg = "empty incremental selection requires an integrity-checked cache"
            raise RuntimeError(msg)

    def _unfinished_result(
        self,
        outcome: p.Cli.ProcessOutcome,
        report_dir: Path,
    ) -> p.Result[int]:
        """Return the native exit of a suite that did not reach its finalizer.

        Returns:
            The original native return code.

        Raises:
            RuntimeError: If a file phase exited 5 without a completed empty scope.

        """
        if (
            self.target_file is not None
            and outcome.raw_return_code == c.Infra.PytestExitCode.NO_TESTS_COLLECTED
        ):
            msg = f"file phase exited 5 without a completed empty scope: {report_dir}"
            raise RuntimeError(msg)
        return r.ok(outcome.raw_return_code)

    def _selection_from_suite(
        self,
        report_dir: Path,
        outcome: p.Cli.ProcessOutcome,
        *,
        execution_mode: c.Infra.PytestExecutionMode = c.Infra.PytestExecutionMode.FULL,
    ) -> p.Infra.PytestSelectionPlan | p.Cli.ProcessOutcome:
        """Bind the plan to the suite's actual collection and selection.

        Interrupted processes retain their recorded native outcome before any
        potentially partial manifest or diagnostic event can be consumed.

        Returns:
            The observed plan or original interrupted or failed process outcome.

        Raises:
            FileNotFoundError: If a successful suite produced no manifest.
            RuntimeError: If a successful FULL suite collected no tests.

        """
        if (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code < 0
        ):
            return outcome
        manifest_path = report_dir / "testmon-inventory.json"
        manifest = (
            m.Infra.PytestCollectionManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8"),
            )
            if manifest_path.exists() or manifest_path.is_symlink()
            else None
        )
        if manifest is None or (
            not manifest.node_ids and not execution_mode.is_incremental
        ):
            if u.Cli.process_succeeded(outcome):
                if manifest is None:
                    raise FileNotFoundError(manifest_path)
                msg = "complete pytest inventory must contain at least one test"
                raise RuntimeError(msg)
            self._write_collection_failure(
                report_dir,
                phase="suite",
                report_log=report_dir / "events.jsonl",
                raw_log=report_dir / "pytest.log",
                outcome=outcome,
            )
            return outcome
        inventory = manifest.node_ids
        if execution_mode.is_incremental:
            empty_allowed = self._scope_may_be_empty(execution_mode) or (
                not manifest.inventory_node_ids and self._owns_no_tests()
            )
            if not manifest.inventory_node_ids and (
                manifest.node_ids or not empty_allowed
            ):
                msg = "native Testmon suite did not record its complete inventory"
                raise RuntimeError(msg)
            inventory = self._manifest_inventory(
                manifest,
                no_tests_collected=(
                    outcome.raw_return_code == c.Infra.PytestExitCode.NO_TESTS_COLLECTED
                ),
                empty_allowed=empty_allowed,
            )
        plan = m.Infra.PytestSelectionPlan(
            manifest_path=manifest_path,
            node_ids=manifest.node_ids,
            whole_target=set(manifest.node_ids) == set(inventory),
            inventory_collected=True,
            owns_no_tests=not inventory,
        )
        u.Cli.atomic_write_text_file(
            report_dir / "testmon-inventory.txt",
            "\n".join(inventory) + "\n",
        ).unwrap()
        return plan

    def execute_coverage(self) -> p.Result[int]:
        """Execute the whole suite under the coverage plugin (never testmon).

        testmon 2.x refuses branch coverage through the cov plugin, so the
        coverage pass is its own process: no selection pass, no cache traffic.
        The coverage artifact is validated here; coverage is reported, never gated.
        A completed failing suite writes no coverage artifact but still
        publishes its accounting and diagnostics with the original exit code.

        Returns:
            The resulting ``p.Result[int]``.

        """
        execution_mode = c.Infra.PytestExecutionMode.COVERAGE
        report_dir = self._report_directory()
        self._write_run_context(
            report_dir,
            m.Infra.PytestRunContext(
                execution_mode=execution_mode,
                testmon_db=None,
                deadline_monotonic=self._deadline_monotonic(
                    execution_mode=execution_mode,
                ),
                report_directory=report_dir,
            ),
        )
        # The inventory pass enforces the same collection policy before coverage.
        selection = self._collect_selection(
            report_dir,
            complete=True,
            execution_mode=execution_mode,
        )
        if isinstance(selection, p.Cli.ProcessOutcome):
            return r.ok(selection.raw_return_code)
        command = self.build_coverage_command(report_dir)
        outcome, _published = self._run_suite(
            command,
            report_dir,
            execution_mode=execution_mode,
        )
        if self._completed_failure(outcome, report_dir):
            return self._finalize(
                report_dir,
                raw_return_code=outcome.raw_return_code,
                interrupted=self._interrupted_suite(outcome),
            )
        if not u.Cli.process_succeeded(outcome):
            return r.ok(outcome.raw_return_code)
        self._validate_coverage(report_dir).unwrap()
        return self._finalize(report_dir, interrupted=False)


__all__: list[str] = ["FlextInfraPytestRunnerExecution"]
