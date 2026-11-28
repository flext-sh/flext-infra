"""Filesystem and Git primitives for the layout engine apply path.

Moves retain their Git history. Retirement requires unchanged committed bytes,
and publishes captured deletions through the native file transaction. Divergent
destinations and content without Git preservation remain untouched.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import m, p, r, t, u


class FlextInfraCodegenLayoutFiles:
    """Move/retire primitives shared by the layout apply orchestration."""

    def _move_entry(
        self,
        project_dir: Path,
        source: Path,
        target: Path,
        inputs: Sequence[p.Cli.AtomicFileState],
    ) -> p.Result[tuple[t.Infra.LayoutStatus, str]]:
        """Move one entry or retire a Git-preserved identical duplicate.

        Returns:
            The resulting ``p.Result[tuple[t.Infra.LayoutStatus, str]]``.

        """
        if not target.exists() and not target.is_symlink():
            moved = self._move_path(project_dir, source, target)
            if moved.failure:
                return r[tuple[t.Infra.LayoutStatus, str]].from_failure(moved)
            applied_status: t.Infra.LayoutStatus = "applied"
            return r[tuple[t.Infra.LayoutStatus, str]].ok((
                applied_status,
                f"moved {source.name} -> {target.name}",
            ))
        before = u.Cli.atomic_read_binary_file_state(source, required=True)
        if before.failure:
            return r[tuple[t.Infra.LayoutStatus, str]].from_failure(before)
        destination = u.Cli.atomic_read_binary_file_state(target, required=True)
        if destination.failure:
            return r[tuple[t.Infra.LayoutStatus, str]].from_failure(destination)
        if (
            before.value.content != destination.value.content
            or before.value.mode != destination.value.mode
        ):
            return r[tuple[t.Infra.LayoutStatus, str]].fail(
                f"layout collision preserves divergent paths: {source} -> {target}",
            )
        retired = self._retire_path(
            project_dir, source, (*inputs, before.value, destination.value)
        )
        if retired.failure:
            return r[tuple[t.Infra.LayoutStatus, str]].from_failure(retired)
        status, message = retired.value
        return r[tuple[t.Infra.LayoutStatus, str]].ok((
            status,
            f"identical target kept; {message}",
        ))

    def _retire_path(
        self,
        project_dir: Path,
        source: Path,
        inputs: Sequence[p.Cli.AtomicFileState],
    ) -> p.Result[tuple[t.Infra.LayoutStatus, str]]:
        """Retire exact HEAD content through authenticated native publication.

        Returns:
            The resulting ``p.Result[tuple[t.Infra.LayoutStatus, str]]``.

        """
        result_type = r[tuple[t.Infra.LayoutStatus, str]]
        paths = (source,)
        if source.is_dir() and not source.is_symlink():
            inventoried = u.Cli.atomic_inventory_physical_tree(source)
            if inventoried.failure:
                return result_type.from_failure(inventoried)
            paths = tuple(
                entry.path
                for entry in inventoried.value.entries
                if entry.kind != "directory"
            )
            if not paths:
                pruned = self._prune_empty_dirs(source)
                if pruned.failure:
                    return result_type.from_failure(pruned)
                empty_status: t.Infra.LayoutStatus = "applied"
                return result_type.ok((empty_status, f"pruned empty {source.name}"))
        captured = u.Infra.git_snapshot_worktree_state(
            m.Infra.GitWorktreeStateRequest(
                repo_root=project_dir,
                paths=(source.relative_to(project_dir),),
            ),
        )
        if captured.failure:
            return result_type.from_failure(captured)
        snapshot = captured.value
        committed = {
            entry.path: (entry.oid, entry.mode) for entry in snapshot.head_entries
        }
        observed = {entry.path: (entry.oid, entry.mode) for entry in snapshot.files}
        if (
            snapshot.index_entries != snapshot.head_entries
            or observed != committed
            or set(committed) != {path.relative_to(project_dir) for path in paths}
        ):
            return result_type.fail(
                f"layout retirement requires unchanged content committed in Git: "
                f"{source.relative_to(project_dir)}",
            )
        plans: list[p.Infra.CodegenFilePlan] = []
        for path in paths:
            before = u.Cli.atomic_read_binary_file_state(path, required=True)
            if before.failure:
                return result_type.from_failure(before)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=project_dir,
                    path=path,
                    before=before.value,
                    desired_content=None,
                    desired_mode=None,
                    inputs=tuple(inputs),
                    owner="codegen",
                ),
            )
        verified = u.Infra.git_verify_worktree_state(snapshot, project_dir)
        if verified.failure:
            return result_type.from_failure(verified)
        if not verified.value:
            return result_type.fail(
                "layout source changed before Git-preserved retirement"
            )
        published = u.Infra.publish_codegen_plans(project_dir, plans)
        if published.failure:
            return result_type.from_failure(published)
        finalized = self._finalize_retirement(
            project_dir, source, snapshot.index_entries
        )
        if finalized.failure:
            return result_type.fail(
                finalized.error or "layout retirement finalization failed",
                error_code=finalized.error_code,
                error_data={
                    **(finalized.error_data or {}),
                    "written_files": [str(path) for path in published.value],
                },
                exception=finalized.exception,
            )
        applied_status: t.Infra.LayoutStatus = "applied"
        return result_type.ok((
            applied_status,
            f"retired {source.name}; preserved in Git {snapshot.head}",
        ))

    def _finalize_retirement(
        self,
        project_dir: Path,
        source: Path,
        entries: Sequence[p.Infra.GitWorktreeIndexEntry],
    ) -> p.Result[bool]:
        """Retire exact versioned index entries and prune emptied directories.

        Returns:
            Success after finalization, or the original Git or filesystem failure.

        """
        for entry in entries:
            retired = u.Infra.git_retire_index_file(
                m.Infra.GitIndexRetirementRequest.model_validate({
                    "repo_root": project_dir,
                    "entry": entry,
                }),
            )
            if retired.failure:
                return r[bool].from_failure(retired)
        if source.is_dir():
            return self._prune_empty_dirs(source)
        return r[bool].ok(value=True)

    def _move_path(
        self,
        project_dir: Path,
        source: Path,
        target: Path,
    ) -> p.Result[bool]:
        """Move tracked entries via Git and untracked entries without staging.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        source_rel = source.relative_to(project_dir).as_posix()
        target_rel = target.relative_to(project_dir).as_posix()
        tracked = u.Infra.git_is_tracked(
            m.Infra.GitRelativePathRequest(
                repo_root=project_dir, relative_path=source_rel
            ),
        )
        if tracked.failure:
            return r[bool].from_failure(tracked)
        target.parent.mkdir(parents=True, exist_ok=True)
        if tracked.value.value:
            moved = u.Infra.git_mv_path(
                m.Infra.GitPathPairRequest(
                    repo_root=project_dir,
                    source=source_rel,
                    target=target_rel,
                ),
            )
            if moved.failure:
                return r[bool].from_failure(moved)
            return r[bool].ok(value=True)
        source.rename(target)
        return r[bool].ok(value=True)

    @staticmethod
    def _prune_empty_dirs(root: Path) -> p.Result[bool]:
        """Remove only the captured empty directory tree left by moves.

        Returns:
            Success after guarded cleanup, or the original failure.

        """
        if not root.exists():
            return r[bool].ok(value=True)
        inventoried = u.Cli.atomic_inventory_physical_tree(root)
        if inventoried.failure:
            return r[bool].from_failure(inventoried)
        if any(entry.kind != "directory" for entry in inventoried.value.entries):
            return r[bool].fail(
                f"layout directory still contains preserved content: {root}"
            )
        return u.Cli.atomic_cleanup_physical_tree_guarded(inventoried.value)


__all__: list[str] = ["FlextInfraCodegenLayoutFiles"]
