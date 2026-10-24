"""Durable diagnostics and execution accounting for pytest.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from defusedxml import ElementTree as DefusedET

from flext_infra import c, config, m, r, u
from flext_infra.validate._pytest_runner import FlextInfraPytestRunnerBase
from flext_infra.validate.pytest_diag import FlextInfraPytestDiagExtractor

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraPytestRunnerReports(FlextInfraPytestRunnerBase):
    """Validate and persist pytest evidence."""

    @staticmethod
    def _reconcile_markdown(
        report_dir: Path,
        diagnostics: m.Infra.PytestDiagnostics,
        *,
        cache_hit: bool,
    ) -> bool:
        """Reconcile the existing collection manifest with real phase evidence.

        Returns:
            The resulting ``bool``.

        """
        plan = m.Infra.PytestSelectionPlan.model_validate_json(
            (report_dir / "selection-plan.json").read_text(encoding="utf-8"),
        )
        if plan.owns_no_tests:
            return True
        manifest = m.Infra.PytestCollectionManifest.model_validate_json(
            plan.manifest_path.read_text(encoding="utf-8"),
        )
        selected = tuple(
            item
            for item in manifest.markdown_collected
            if item.node_id in manifest.node_ids
        )
        deselected = tuple(
            item
            for item in manifest.markdown_collected
            if item.node_id not in manifest.node_ids
        )
        violations: t.MutableSequenceOf[str] = []
        if not cache_hit and set(diagnostics.reported_node_ids) != set(
            manifest.node_ids,
        ):
            violations.append("selected node IDs differ from executed node IDs")
        if cache_hit and (
            diagnostics.reported_node_ids or diagnostics.markdown_attempts
        ):
            violations.append("incremental cache hit contains execution evidence")
        if not cache_hit and set(diagnostics.markdown_items) != set(selected):
            violations.append(
                "selected Markdown definitions differ from executed origins",
            )
        violations.extend(
            ("duplicate Markdown executed origin",)
            if len(set(diagnostics.markdown_items)) != len(diagnostics.markdown_items)
            else (),
        )
        proofs = {proof.node_id: proof for proof in diagnostics.markdown_attempts}
        if len(proofs) != len(diagnostics.markdown_attempts):
            violations.append("duplicate Markdown attempt proof")
        if not cache_hit and set(proofs) != {item.node_id for item in selected}:
            violations.append("missing or unexpected Markdown attempt proof")
        expected_phases = {"setup", "call", "teardown"}
        for item in selected:
            phases = tuple(
                phase
                for phase in diagnostics.phase_outcomes
                if phase.node_id == item.node_id
            )
            if not cache_hit and (
                {phase.phase for phase in phases} != expected_phases
                or len(phases) != len(expected_phases)
                or any(phase.outcome != "passed" for phase in phases)
            ):
                violations.append(f"Markdown lifecycle did not pass: {item.node_id}")
            proof = proofs.get(item.node_id)
            if proof is not None and (
                proof.attempts != 1 or proof.first_exception_type is not None
            ):
                violations.append(
                    f"Markdown first-attempt execution failed: {item.node_id}",
                )
        receipt = m.Infra.PytestMarkdownReconciliation(
            eligible=manifest.markdown_eligible,
            selected=selected,
            deselected=deselected,
            diagnostics=diagnostics,
            cache_hit=cache_hit,
            violations=tuple(violations),
        )
        u.Cli.atomic_write_text_file(
            report_dir / "markdown-reconciliation.json",
            receipt.model_dump_json(indent=2) + "\n",
        ).unwrap()
        return not violations

    @staticmethod
    def _write_run_context(report_dir: Path, context: m.Infra.PytestRunContext) -> None:
        """Name the mode and database before any subprocess can fail."""
        u.Cli.atomic_write_text_file(
            report_dir / "run-context.json",
            context.model_dump_json(indent=2) + "\n",
        ).unwrap()
        latest = report_dir.parent / "latest.txt"
        wait_seconds = max(
            0.0,
            context.deadline_monotonic
            - config.Infra.tooling.tools.pytest.termination_grace_seconds
            - time.monotonic(),
        )
        # This publication runs both before and inside the separate cache lease.
        with u.Cli.file_changes_lock(
            latest.with_name(f"{latest.name}.lock"),
        ).acquire(timeout=wait_seconds):
            u.Cli.atomic_write_text_file(latest, f"{report_dir.name}\n").unwrap()

    @staticmethod
    def _bind_child_profile(report_dir: Path, profile: Path) -> None:
        """Bind one reaped child's native profile to this run by digest.

        A checkpoint from an interrupted child is diagnostic evidence; binding
        it never changes the separately recorded native process outcome.
        """
        context = m.Infra.PytestRunContext.model_validate_json(
            (report_dir / "run-context.json").read_text(encoding="utf-8"),
        )
        receipt = context.model_copy(
            update={"profile_sha256": u.Cli.sha256_bytes(profile.read_bytes())},
        )
        u.Cli.atomic_write_text_file(
            profile.with_suffix(".pstats.json"),
            receipt.model_dump_json(indent=2) + "\n",
        ).unwrap()

    @staticmethod
    def _failure_detail(message: str, pytest_log: Path) -> str:
        """Attach the bounded log tail to an artifact failure.

        Returns:
            The resulting ``str``.

        """
        tail = "\n".join(pytest_log.read_text(encoding="utf-8").splitlines()[-40:])
        return f"{message}\n--- pytest.log (tail) ---\n{tail}" if tail else message

    def _accounting(
        self,
        junit: Path,
        log: Path,
        *,
        cache_restored: bool,
        reported_count: int,
    ) -> p.Result[m.Infra.TestmonRunAccounting]:
        """Parse typed executed/deselected accounting from durable artifacts.

        Returns:
            The resulting ``p.Result[m.Infra.TestmonRunAccounting]``.

        Raises:
            FileNotFoundError: If ``not junit.exists()``.
            RuntimeError: Always; or if testmon accounting requires the durable
                selection plan; or if testmon selected node IDs outside the complete
                collection inventory.
            ValueError: If JUnit must be a regular file; or if ``junit.stat().st_size ==
                0``; or if ``root is None``.

        """
        if not junit.exists():
            raise FileNotFoundError(junit)
        if not junit.is_file():
            msg = f"JUnit must be a regular file: {junit}"
            raise ValueError(msg)
        if junit.stat().st_size == 0:
            msg = self._failure_detail(f"empty JUnit: {junit}", log)
            raise ValueError(msg)
        root = DefusedET.parse(junit).getroot()
        if root is None:
            msg = self._failure_detail(f"JUnit has no document root: {junit}", log)
            raise ValueError(msg)
        executed = sum(1 for _ in root.iter("testcase"))
        context = m.Infra.PytestRunContext.model_validate_json(
            (log.parent / "run-context.json").read_text(encoding="utf-8"),
        )
        deselected = 0
        inventory_count = None
        owns_no_tests = False
        selection_plan: m.Infra.PytestSelectionPlan | None = None
        # Testmon operations publish a plan bound to their observed inventory.
        # Coverage owns no Testmon selection or database.
        if context.testmon_db is not None:
            selection_plan = m.Infra.PytestSelectionPlan.model_validate_json(
                (log.parent / "selection-plan.json").read_text(encoding="utf-8"),
            )
            owns_no_tests = selection_plan.owns_no_tests
        if owns_no_tests and selection_plan is not None:
            # The declared empty suite produces no manifest artifacts: zero
            # execution with typed accounting IS the receipt.
            accounting = m.Infra.TestmonRunAccounting(
                executed_count=executed,
                reported_count=reported_count,
                deselected_count=0,
                inventory_count=0,
                cache_restored=cache_restored,
                owns_no_tests=True,
            )
            return r.ok(accounting)
        deselected, inventory_count = self._selected_inventory(
            log,
            context,
            selection_plan,
        )
        accounting = m.Infra.TestmonRunAccounting(
            executed_count=executed,
            reported_count=reported_count,
            deselected_count=deselected,
            inventory_count=inventory_count,
            cache_restored=cache_restored,
            owns_no_tests=owns_no_tests,
        )
        if executed:
            return r.ok(accounting)
        if cache_restored and deselected:
            return r.ok(accounting)
        msg = self._failure_detail("pytest executed zero tests", log)
        raise RuntimeError(msg)

    @staticmethod
    def _selected_inventory(
        log: Path,
        context: m.Infra.PytestRunContext,
        selection_plan: m.Infra.PytestSelectionPlan | None,
    ) -> t.Pair[int, int | None]:
        """Reconcile the executed selection against the collection inventory.

        Returns:
            The resulting ``(deselected, inventory_count)`` pair; the inventory
            count stays unset for a run without testmon (coverage).

        Raises:
            RuntimeError: If testmon accounting requires the durable selection
                plan; or if testmon selected node IDs outside the complete
                collection inventory.

        """
        if context.testmon_db is None:
            return (0, None)
        if selection_plan is None:
            msg = (
                "testmon accounting requires the durable selection plan: "
                f"{log.parent / 'selection-plan.json'}"
            )
            raise RuntimeError(msg)
        selected = (
            m.Infra.PytestCollectionManifest.model_validate_json(
                selection_plan.manifest_path.read_text(encoding="utf-8"),
            )
            if (
                context.execution_mode == c.Infra.PytestExecutionMode.FULL
                # Full runs and declared single-file selections use the
                # centrally enforced manifest as the executed selection.
                or selection_plan.whole_target
            )
            else m.Infra.PytestCollectionManifest.model_validate_json(
                (log.parent / "testmon-selection.json").read_text(encoding="utf-8"),
            )
        )
        inventory = (
            selected
            if not selection_plan.inventory_collected
            else m.Infra.PytestCollectionManifest.model_validate_json(
                (log.parent / "testmon-inventory.json").read_text(encoding="utf-8"),
            )
        )
        if not set(selected.node_ids).issubset(inventory.node_ids):
            msg = "testmon selected node IDs outside the complete collection inventory"
            raise RuntimeError(msg)
        inventory_count = len(inventory.node_ids)
        # Deselection follows the centrally enforced manifest. An empty
        # incremental suite selection deselects the complete inventory; declared
        # file and full requests execute their complete in-scope inventory.
        return (inventory_count - len(selected.node_ids), inventory_count)

    def _diagnostics(self, report_dir: Path) -> p.Result[m.Infra.PytestDiagnostics]:
        """Extract diagnostics through the canonical typed service.

        Returns:
            The resulting ``p.Result[m.Infra.PytestDiagnostics]``.

        """
        extractor = FlextInfraPytestDiagExtractor(
            repository_root=self.repository_root,
            junit=report_dir / "junit.xml",
            log_path=report_dir / "pytest.log",
            report_log=report_dir / "events.jsonl",
        )
        return extractor.extract(
            extractor.junit,
            extractor.log_path,
            report_log=extractor.report_log,
        )

    @staticmethod
    def _read_collection_diagnostics(
        report_log: Path,
    ) -> m.Infra.PytestDiagnostics:
        """Read and retain the collection's native typed evidence.

        Returns:
            Observed collection outcomes and warning events for this child.

        """
        diagnostics = FlextInfraPytestDiagExtractor.extract_report_log(
            report_log,
        ).unwrap()
        receipt = report_log.with_suffix(".diagnostics.json")
        u.Cli.atomic_write_text_file(
            receipt,
            diagnostics.model_dump_json(indent=2) + "\n",
        ).unwrap()
        return diagnostics

    @classmethod
    def _collection_diagnostics(cls, report_log: Path) -> None:
        """Require complete collection evidence before accepting a selection.

        Raises:
            RuntimeError: If pytest collection contains blocking findings.

        """
        diagnostics = cls._read_collection_diagnostics(report_log)
        receipt = report_log.with_suffix(".diagnostics.json")
        if any((
            diagnostics.collection_failed_count,
            diagnostics.collection_skipped_count,
            diagnostics.warning_count,
        )):
            msg = f"pytest collection contains blocking findings: {receipt}"
            raise RuntimeError(msg)

    def _write_collection_failure(
        self,
        report_dir: Path,
        *,
        phase: str,
        report_log: Path,
        raw_log: Path,
        outcome: p.Cli.ProcessOutcome,
    ) -> None:
        """Retain failed collection or incomplete suite evidence without a plan.

        A suite process may have reported tests before its inventory was lost;
        an absent inventory cannot turn that observation into zero execution.
        """
        required_reports = (
            report_log,
            report_log.with_suffix(c.Infra.PYTEST_WARNING_EVENTS_SUFFIX),
        )
        interrupted = (
            outcome.timed_out
            or outcome.forwarded_signal is not None
            or outcome.raw_return_code < 0
        )
        diagnostics: m.Infra.PytestDiagnostics | None = None
        if interrupted:
            diagnostic_summary = "diagnostics=incomplete\n"
        else:
            missing_reports = tuple(
                path
                for path in required_reports
                if not path.exists() and not path.is_symlink()
            )
            if missing_reports:
                diagnostic_summary = "diagnostics=not_produced\n" + "".join(
                    f"missing_report={path}\n" for path in missing_reports
                )
            else:
                diagnostics = self._read_collection_diagnostics(report_log)
                self._write_diagnostics(
                    report_dir,
                    diagnostics,
                    phases=((phase, diagnostics),),
                )
                diagnostic_summary = (
                    f"collection_errors={diagnostics.collection_failed_count}\n"
                    f"collection_skips={diagnostics.collection_skipped_count}\n"
                    f"warnings={diagnostics.warning_count}\n"
                )
        reported = (
            len(diagnostics.reported_node_ids) if diagnostics is not None else "unknown"
        )
        execution_summary = (
            f"suite=incomplete\nexecuted=unknown\nreported={reported}\n"
            if phase == "suite"
            else "suite=not_executed\nexecuted=0\n"
        )
        status = (
            "interrupted"
            if interrupted
            else "incomplete"
            if phase == "suite"
            else "collection_failed"
        )
        summary = (
            f"outcome={status}\n"
            f"phase={phase}\n"
            f"{execution_summary}"
            f"inventory_complete={'unknown' if interrupted else 'false'}\n"
            f"{diagnostic_summary}"
            f"exit={outcome.raw_return_code}\n"
            f"timed_out={outcome.timed_out}\n"
            f"forwarded_signal={outcome.forwarded_signal}\n"
            f"raw_log={raw_log}\n"
        )
        u.Cli.atomic_write_text_file(report_dir / "summary.txt", summary).unwrap()
        sys.stderr.write(
            f"Pytest {phase}: outcome={status}; reports={report_dir}; log={raw_log}\n",
        )

    def _phase_diagnostics(
        self,
        report_dir: Path,
        *,
        context: m.Infra.PytestRunContext,
        suite: m.Infra.PytestDiagnostics,
    ) -> t.VariadicTuple[t.Pair[str, m.Infra.PytestDiagnostics]]:
        """Read each subprocess receipt once in execution order.

        Whole-project FULL collection belongs to the suite process. Declared
        file and incremental requests retain their separate collection phases.

        Returns:
            The resulting ``t.VariadicTuple[t.Pair[str, m.Infra.PytestDiagnostics]]``.

        """
        if (
            context.execution_mode == c.Infra.PytestExecutionMode.FULL
            and self.target_file is None
        ):
            return (("suite", suite),)
        phases: t.MutableSequenceOf[t.Pair[str, m.Infra.PytestDiagnostics]] = []
        if context.testmon_db is not None:
            selection_plan = m.Infra.PytestSelectionPlan.model_validate_json(
                (report_dir / "selection-plan.json").read_text(encoding="utf-8"),
            )
            if selection_plan.owns_no_tests:
                # The declared empty suite ran no collection subprocess, so no
                # per-phase receipt exists: only the suite diagnostics.
                return (("suite", suite),)
            # A phase receipt exists only for a subprocess that ran, and
            # ``inventory_collected`` is that contract. ``whole_target`` alone
            # cannot imply one: the cold-cache selection-only plan also
            # returns whole_target=True (its single selection collection spans
            # the whole target) without ever running an inventory subprocess,
            # and demanding the inventory receipt then crashed the report
            # phase of every fresh-environment CI run after an all-green
            # suite.
            names = (
                ("inventory",)
                # A whole-target run (the declared single file) collects its
                # inventory directly and never runs a separate selection
                # collection, so only the inventory receipt exists.
                if selection_plan.whole_target and selection_plan.inventory_collected
                else (
                    (
                        ("selection", "inventory")
                        if selection_plan.inventory_collected
                        else ("selection",)
                    )
                    if context.execution_mode == c.Infra.PytestExecutionMode.INCREMENTAL
                    else ("inventory",)
                )
            )
            for phase in names:
                receipt = report_dir / f"testmon-{phase}.events.diagnostics.json"
                phases.append((
                    phase,
                    m.Infra.PytestDiagnostics.model_validate_json(
                        receipt.read_text(encoding="utf-8"),
                    ),
                ))
        return (*phases, ("suite", suite))

    def _validate_coverage(self, report_dir: Path) -> p.Result[bool]:
        """Require a non-empty coverage report; the percentage is never a gate.

        Returns:
            The resulting ``p.Result[bool]``.

        Raises:
            FileNotFoundError: If ``not coverage.exists()``.
            ValueError: If coverage artifact must be a regular file; or if
                ``coverage.stat().st_size == 0``.

        """
        coverage = report_dir / "coverage.xml"
        if not coverage.exists():
            raise FileNotFoundError(coverage)
        if not coverage.is_file():
            msg = f"coverage artifact must be a regular file: {coverage}"
            raise ValueError(msg)
        if coverage.stat().st_size == 0:
            msg = self._failure_detail(
                f"empty coverage artifact: {coverage}",
                report_dir / "pytest.log",
            )
            raise ValueError(msg)
        return r.ok(value=True)

    @staticmethod
    def _write_diagnostics(
        report_dir: Path,
        diagnostics: m.Infra.PytestDiagnostics,
        *,
        phases: t.VariadicTuple[t.Pair[str, m.Infra.PytestDiagnostics]],
    ) -> None:
        """Persist each typed diagnostics channel."""
        u.Cli.atomic_write_text_file(
            report_dir / "diagnostics.json",
            diagnostics.model_dump_json(indent=2) + "\n",
        ).unwrap()
        outputs: t.VariadicTuple[t.Triple[str, t.StrSequence, str]] = (
            ("failed-tests.txt", diagnostics.failed_cases, "\n\n"),
            ("errors.txt", diagnostics.error_traces, "\n\n"),
            (
                "warnings.txt",
                tuple(
                    f"{phase}: {line}"
                    for phase, item in phases
                    for line in item.warning_lines
                ),
                "\n",
            ),
            ("skipped-tests.txt", diagnostics.skip_cases, "\n"),
            ("slowest-tests.txt", diagnostics.slow_entries, "\n"),
        )
        for filename, values, separator in outputs:
            body = separator.join(values) + ("\n" if values else "")
            u.Cli.atomic_write_text_file(report_dir / filename, body).unwrap()


__all__: list[str] = ["FlextInfraPytestRunnerReports"]
