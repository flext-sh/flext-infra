"""Workspace-scoped Python file iteration utility facet.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import multiprocessing
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from flext_cli import u as cli_u

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGitScopeMixin,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesRefactor,
)


class FlextInfraUtilitiesIterationWorkspace(FlextInfraUtilitiesIterationDirectory):
    """Static helpers for discovering Python files across workspace projects."""

    @staticmethod
    def repository_operation_batch(
        root: Path,
        scope: c.Infra.CodegenConformScope,
        operation: str,
        task: Callable[[Path], p.Result[t.SequenceOf[Path]]],
    ) -> p.Result[t.SequenceOf[Path]]:
        """Attempt a discovered repository scope serially through its original owner.

        Returns:
            Original returned paths, or the first causal failure after reporting.
        """
        resolved = root.expanduser().resolve()
        if scope == c.Infra.CodegenConformScope.SELF:
            roots = (resolved,)
        elif scope == c.Infra.CodegenConformScope.ALL:
            declared = FlextInfraUtilitiesGit.git_submodule_declarations(resolved)
            if declared.failure:
                return r[t.SequenceOf[Path]].from_failure(declared)
            roots = (
                resolved,
                *(resolved / declaration.path for declaration in declared.value),
            )
        else:
            return r[t.SequenceOf[Path]].fail(
                f"{operation} scope must be self or all, received {scope}",
            )
        receipts: list[m.Infra.WorkspaceOperationReceipt] = []
        files: list[Path] = []
        first_failure: p.Result[t.SequenceOf[Path]] | None = None
        for repository_root in roots:
            result = task(repository_root)
            issues = (
                (
                    m.Infra.Issue(
                        file=str(repository_root),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=result.error or f"{operation} failed",
                        severity="error",
                    ),
                )
                if result.failure
                else ()
            )
            observed = () if result.failure else tuple(result.value)
            files.extend(observed)
            receipts.append(
                m.Infra.WorkspaceOperationReceipt(
                    root=repository_root,
                    executed=True,
                    outcome=(
                        c.Infra.ToolOutcome.ERROR
                        if result.failure
                        else c.Infra.ToolOutcome.CLEAN
                    ),
                    files=observed,
                    issues=issues,
                ),
            )
            cli_u.Cli.status(operation, repository_root.name, result=result.success)
            if result.failure and first_failure is None:
                first_failure = result
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
        return r[t.SequenceOf[Path]].ok(tuple(files))

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
        workers = min(config.Infra.codegen.fleet_workers, len(payloads))
        if workers <= 1:
            return tuple(task(payload) for payload in payloads)
        context = multiprocessing.get_context("forkserver")
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            return tuple(pool.map(task, payloads))

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
        """Return configured Python sources with one Git inventory per project.

        Returns:
            Configured Python sources with one Git inventory per project.

        """
        source_roots = tuple(
            path
            for directory_name in config.Infra.source_scan.roots
            if (path := (project_root / directory_name).resolve()).is_dir()
        )
        tracked_files = FlextInfraUtilitiesGitScopeMixin.git_tracked_scope_paths(
            project_root,
        )
        if tracked_files is None:
            return tuple(
                file_path
                for source_root in source_roots
                for file_path in (
                    FlextInfraUtilitiesIterationDirectory.iter_directory_python_files
                )(
                    source_root,
                )
            )
        ignored = frozenset(config.Infra.codegen.source_scan_ignored)
        return tuple(
            file_path
            for file_path in tracked_files
            if file_path.suffixes == [c.Infra.EXT_PYTHON]
            and any(
                file_path.is_relative_to(source_root) for source_root in source_roots
            )
            and not ignored.intersection(file_path.relative_to(project_root).parts)
        )


__all__: list[str] = ["FlextInfraUtilitiesIterationWorkspace"]
