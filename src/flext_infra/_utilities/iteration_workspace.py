"""Workspace-scoped Python file iteration utility facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import multiprocessing
import os
import shlex
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from flext_cli import u as cli_u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import FlextInfraUtilitiesIterationDirectory
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.refactor import FlextInfraUtilitiesRefactor


class FlextInfraUtilitiesIterationWorkspace(FlextInfraUtilitiesIterationDirectory):
    """Static helpers for discovering Python files across workspace projects."""

    @staticmethod
    def bootstrap_operation_report_shell_literal() -> str:
        """Project the elected report schema for the interpreter-free Make boundary.

        Roots are relative to the repository containing the published report.
        Only closed stage/outcome labels, a validated Git OID and native scalar
        completion facts replace tokens in the original shell's EXIT handler.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If bootstrap report requires one elected scalar field.

        """
        report = m.Infra.WorkspaceOperationReport(
            root=Path(),
            operation="tool-bootstrap",
            scope=(Path(),),
            receipts=(
                m.Infra.WorkspaceOperationReceipt(
                    root=Path(),
                    executed=True,
                    outcome=None,
                ),
            ),
        )
        serialized = report.model_dump_json(round_trip=True)
        replacements = (
            ('"candidate_sha":null', '"candidate_sha":@@SHA@@'),
            (
                '"candidate_read_exit_code":null',
                '"candidate_read_exit_code":@@GIT_EXIT@@',
            ),
            ('"native_exit_code":null', '"native_exit_code":@@EXIT@@'),
            ('"stage":null', '"stage":"@@STAGE@@"'),
            ('"completed":null', '"completed":@@COMPLETE@@'),
        )
        for original, replacement in replacements:
            if serialized.count(original) != 1:
                msg = f"bootstrap report requires one elected scalar field: {original}"
                raise ValueError(msg)
            serialized = serialized.replace(original, replacement, 1)
        return shlex.quote(serialized)

    @staticmethod
    def repository_operation_batch(
        root: Path,
        scope: c.Infra.CodegenConformScope,
        operation: str,
        task: Callable[[Path], p.Result[t.SequenceOf[Path]]],
        *,
        mutating: bool = False,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Attempt a discovered repository scope serially through its original owner.

        Returns:
            Original returned paths, or the first causal failure after reporting.

        """
        resolved = root.expanduser().resolve()
        discovered = FlextInfraUtilitiesProjectDiscovery.repository_operation_targets(
            resolved,
            scope,
        )
        if discovered.failure:
            return r[t.SequenceOf[Path]].from_failure(discovered)
        roots = tuple(target.root for target in discovered.value)
        receipts: list[m.Infra.WorkspaceOperationReceipt] = []
        files: list[Path] = []
        first_failure: p.Result[t.SequenceOf[Path]] | None = None
        for target in discovered.value:
            receipt, observed, failure = (
                FlextInfraUtilitiesIterationWorkspace._operation_target_outcome(
                    target,
                    operation,
                    task,
                    mutating=mutating,
                )
            )
            receipts.append(receipt)
            files.extend(observed)
            if failure is not None and first_failure is None:
                first_failure = failure
        published = FlextInfraUtilitiesRefactor.publish_refactor_report_evidence(
            resolved,
            m.Infra.WorkspaceOperationReport(
                root=resolved,
                operation=operation,
                scope=roots,
                receipts=tuple(receipts),
            ),
            relative_path=(
                c.Infra.WORKSPACE_OPERATION_REPORT_DIRECTORY / f"{operation}.json"
            ),
        )
        if published.failure:
            if first_failure is not None:
                cli_u.Cli.error(
                    f"{operation} receipt publication failed: {published.error}",
                )
                return r[t.SequenceOf[Path]].from_failure(first_failure)
            return r[t.SequenceOf[Path]].from_failure(published)
        if first_failure is not None:
            return r[t.SequenceOf[Path]].from_failure(first_failure)
        if not any(receipt.executed for receipt in receipts):
            return r[t.SequenceOf[Path]].fail(
                f"{operation} executed no applicable repository operation",
            )
        return r[t.SequenceOf[Path]].ok(tuple(files))

    @staticmethod
    def _operation_target_outcome(
        target: m.Infra.WorkspaceOperationTarget,
        operation: str,
        task: Callable[[Path], p.Result[t.SequenceOf[Path]]],
        *,
        mutating: bool,
    ) -> tuple[
        m.Infra.WorkspaceOperationReceipt,
        tuple[Path, ...],
        p.Result[t.SequenceOf[Path]] | None,
    ]:
        """Run one discovered target through its original owner and report it.

        Returns:
            The receipt, the observed files, and the original failure if any.

        Raises:
            ValueError: If the original operation failed without its native error.

        """
        repository_root = target.root
        start = time.monotonic()
        applicability = (
            FlextInfraUtilitiesProjectDiscovery.repository_operation_applicability(
                target,
                mutating=mutating,
            )
        )
        if applicability.success and not applicability.value.applicable:
            cli_u.Cli.info(
                f"{operation} {repository_root}: NOT APPLICABLE: "
                f"{applicability.value.reason}",
            )
            return (
                m.Infra.WorkspaceOperationReceipt(
                    root=repository_root,
                    executed=False,
                    outcome=None,
                    applicability=applicability.value.reason,
                ),
                (),
                None,
            )
        executed = applicability.success
        result = (
            task(repository_root)
            if executed
            else r[t.SequenceOf[Path]].from_failure(applicability)
        )
        if result.failure:
            error = result.error
            if error is None:
                msg = f"{operation} failed without its native error: {repository_root}"
                raise ValueError(msg)
            issues = (
                m.Infra.Issue(
                    file=str(repository_root),
                    line=0,
                    column=0,
                    code=c.Infra.ToolOutcome.ERROR.value,
                    message=error,
                    severity="error",
                ),
            )
        else:
            issues = ()
        observed = () if result.failure else tuple(result.value)
        cli_u.Cli.status(
            operation,
            repository_root.name,
            result=result.success,
            elapsed=time.monotonic() - start,
        )
        receipt = m.Infra.WorkspaceOperationReceipt(
            root=repository_root,
            executed=executed,
            outcome=(
                c.Infra.ToolOutcome.ERROR
                if result.failure
                else c.Infra.ToolOutcome.CLEAN
            ),
            files=observed,
            issues=issues,
        )
        return receipt, observed, (result if result.failure else None)

    @staticmethod
    def machine_worker_capacity(worker_memory_gb: int) -> int:
        """Derive how many workers this process's CPUs and physical memory hold.

        CPU capacity is the process-scoped count (the cgroup affinity the
        process actually gets); memory capacity divides physical memory by the
        declared per-worker budget.

        Args:
            worker_memory_gb: Physical memory one worker needs, in GiB.

        Returns:
            The smaller of the CPU and memory capacities.

        Raises:
            ValueError: If CPU or physical memory capacity is unavailable, or if
                physical memory cannot hold one worker.

        """
        cpu_count = os.process_cpu_count()
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        if cpu_count is None or cpu_count <= 0 or page_size <= 0 or pages <= 0:
            msg = "CPU or physical memory capacity is unavailable"
            raise ValueError(msg)
        memory_workers = (
            (page_size * pages) // c.Infra.BYTES_PER_GIB // worker_memory_gb
        )
        if memory_workers <= 0:
            msg = f"physical memory cannot hold one {worker_memory_gb} GiB worker"
            raise ValueError(msg)
        return min(cpu_count, memory_workers)

    @staticmethod
    def fleet_map[TPayload, TResult](
        task: Callable[[TPayload], TResult],
        payloads: t.SequenceOf[TPayload],
    ) -> tuple[TResult, ...]:
        """Run one read-only task per payload across the configured workers.

        ``task`` must be importable by qualified name and every payload and
        result picklable: workers start from a clean interpreter (forkserver),
        so no parent lock, thread, or lease crosses the process boundary. The
        results keep the payload order, and the first worker exception escapes
        unchanged. One configured worker or one payload runs in this process.

        Returns:
            The task results in payload order.

        """
        workers = min(
            FlextInfraUtilitiesIterationWorkspace.machine_worker_capacity(
                config.Infra.codegen.fleet_worker_memory_gb
            ),
            len(payloads),
        )
        if workers <= 1:
            return tuple(task(payload) for payload in payloads)
        context = multiprocessing.get_context("forkserver")
        started = time.monotonic()
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            results = tuple(pool.map(task, payloads))
            mapped = time.monotonic()
        finished = time.monotonic()
        cli_u.Cli.info(
            f"stage=fleet-map payloads={len(payloads)} workers={workers} "
            f"map_elapsed={mapped - started:.3f}s "
            f"shutdown_elapsed={finished - mapped:.3f}s",
        )
        return results

    @classmethod
    def iter_python_files(
        cls,
        request: p.Infra.SourceScanRequest,
    ) -> p.Result[t.SequenceOf[Path]]:
        """Return Python files from the exact production roots in ``request``.

        Args:
            request: Field-only request containing already-resolved project roots.

        Returns:
            Result[t.SequenceOf[Path]] - Success contains sorted unique file paths.
            Failure if: workspace inaccessible, discovery fails, or OSError.

        """
        invalid_root = next(
            (root for root in request.project_roots if not root.is_dir()),
            None,
        )
        if invalid_root is not None:
            return r[t.SequenceOf[Path]].fail(
                f"python file iteration failed: project root "
                f"is not a directory: {invalid_root}",
            )
        try:
            files = {
                file_path
                for project_root in request.project_roots
                for file_path in cls._project_python_files(project_root)
            }
            return r[t.SequenceOf[Path]].ok(tuple(sorted(files)))
        except OSError as exc:
            return r[t.SequenceOf[Path]].fail_op("python file iteration", exc)

    @classmethod
    def _project_python_files(cls, project_root: Path) -> t.SequenceOf[Path]:
        """Return every active Python source owned by this project.

        Returns:
            Python sources from the canonical discovery inventory.

        """
        return tuple(
            file_path
            for file_path in FlextInfraUtilitiesProjectDiscovery.discover_python_files(
                project_root, workspace_excluded_top_dirs=frozenset()
            )
            if file_path.suffixes == [c.Infra.EXT_PYTHON]
        )


__all__: list[str] = ["FlextInfraUtilitiesIterationWorkspace"]
