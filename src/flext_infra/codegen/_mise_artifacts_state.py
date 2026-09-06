"""Persistent coordination-state lifecycle for Mise transactions."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from flext_core import r
from flext_infra import c, m, u
from flext_infra.codegen import _mise_artifacts_files as files
from flext_infra.codegen import _mise_artifacts_verification as verify

if TYPE_CHECKING:
    from flext_infra import p


def _project_depth(item: m.Infra.MiseToolchainProjectLayout) -> int:
    """Order the narrowest project owner before its ancestors."""
    return -len(item.root.parts)


def _directory_cleanup_order(item: m.Infra.CodegenJournalDirectory) -> tuple[int, str]:
    """Order journaled directory cleanup from descendants to ancestors."""
    return u.Infra.path_depth_then_text(Path(item.path))


def plan_transaction_directories(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[tuple[m.Infra.CodegenJournalDirectory, ...]]:
    """Prove every transaction path absent before journal publication."""
    roots: list[Path] = []
    for project in layout.projects:
        transaction_root = project.transaction_root
        if transaction_root is None:
            return r[tuple[m.Infra.CodegenJournalDirectory, ...]].fail(
                "Mise mutating layout has no transaction root"
            )
        destination_devices: set[int] = set()
        for artifact in (
            project.artifacts.config,
            project.artifacts.unix_launcher,
            project.artifacts.windows_launcher,
            project.artifacts.lock,
        ):
            parent_plan = u.Cli.atomic_plan_directory_chain(artifact.parent)
            if parent_plan.failure:
                return r[tuple[m.Infra.CodegenJournalDirectory, ...]].from_failure(
                    parent_plan
                )
            destination_devices.add(parent_plan.value.anchor_device)
        project_plan = u.Cli.atomic_plan_directory_chain(project.root)
        if project_plan.failure:
            return r[tuple[m.Infra.CodegenJournalDirectory, ...]].from_failure(
                project_plan
            )
        project_device = project_plan.value.anchor_device
        if destination_devices != {project_device}:
            return r[tuple[m.Infra.CodegenJournalDirectory, ...]].fail(
                f"Mise state is not on destination filesystem: {project.selector}"
            )
        roots.append(transaction_root)
    return plan_directories(
        layout, phase="transaction", requested=tuple(roots), disposition="temporary"
    )


def plan_directories(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    *,
    phase: str,
    requested: tuple[Path, ...],
    disposition: Literal["temporary", "generated"],
) -> p.Result[tuple[m.Infra.CodegenJournalDirectory, ...]]:
    """Return unique missing paths after descriptor-authenticated preflight."""
    result_type = r[tuple[m.Infra.CodegenJournalDirectory, ...]]
    if len(set(requested)) != len(requested):
        return result_type.fail(f"duplicate {phase} directory request")
    projects = tuple(sorted(layout.projects, key=_project_depth))
    planned: dict[Path, m.Infra.CodegenJournalDirectory] = {}
    for target in requested:
        path = target.expanduser().absolute()
        project = next(
            (item for item in projects if path.is_relative_to(item.root)), None
        )
        if project is None or path == project.root:
            return result_type.fail(f"{phase} directory escapes its project: {path}")
        chain = u.Cli.atomic_plan_directory_chain(path)
        if chain.failure:
            return result_type.from_failure(chain)
        for directory in chain.value.directories:
            owner = next(
                (item for item in projects if directory.is_relative_to(item.root)), None
            )
            if owner is None or directory == owner.root:
                return result_type.fail(
                    f"{phase} directory has no project owner: {directory}"
                )
            relative = files.workspace_relative(layout.scope_root, directory)
            if relative.failure:
                return result_type.from_failure(relative)
            before: m.Cli.AtomicDirectoryState | None = None
            if directory.parent == chain.value.anchor_path:
                observed = u.Cli.atomic_read_empty_directory_state(
                    directory, required=False
                )
                if observed.failure:
                    return result_type.from_failure(observed)
                if observed.value.exists or (
                    observed.value.parent_device,
                    observed.value.parent_inode,
                ) != (chain.value.anchor_device, chain.value.anchor_inode):
                    return result_type.fail(
                        f"{phase} directory anchor changed during planning: {directory}"
                    )
                before = observed.value
            entry = m.Infra.CodegenJournalDirectory(
                phase=phase,
                project=owner.selector,
                path=relative.value,
                disposition=disposition,
                before=before,
            )
            previous = planned.get(directory)
            if previous is not None and (
                previous.phase,
                previous.project,
                previous.disposition,
            ) != (entry.phase, entry.project, entry.disposition):
                return result_type.fail(
                    f"generation directory has conflicting owners: {directory}"
                )
            if previous is None or (previous.before is None and before is not None):
                planned[directory] = entry
    ordered = tuple(
        planned[path] for path in sorted(planned, key=u.Infra.path_depth_then_text)
    )
    return result_type.ok(ordered)


def create_journaled_directory(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    directories: tuple[m.Infra.CodegenJournalDirectory, ...],
    entry: m.Infra.CodegenJournalDirectory,
) -> p.Result[m.Infra.CodegenJournalDirectory]:
    """Create one durable intent and return its exact physical identity."""
    result_type = r[m.Infra.CodegenJournalDirectory]
    if entry.created is not None or entry not in directories:
        return result_type.fail(f"invalid directory creation cursor: {entry.path}")
    target = files.resolve_relative(
        layout.scope_root, entry.path, purpose="journaled generation directory"
    )
    if target.failure:
        return result_type.from_failure(target)
    project = next(
        (item for item in layout.projects if item.selector == entry.project), None
    )
    if project is None or not target.value.is_relative_to(project.root):
        return result_type.fail(
            f"journaled directory differs from its project: {entry.path}"
        )
    before = entry.before
    if before is None:
        parent_entry = next(
            (
                candidate
                for candidate in directories
                if (layout.scope_root / candidate.path).absolute()
                == target.value.parent
            ),
            None,
        )
        if (
            parent_entry is None
            or parent_entry.created is None
            or parent_entry.created.device is None
            or parent_entry.created.inode is None
        ):
            return result_type.fail(
                f"journaled directory parent has no durable identity: {entry.path}"
            )
        observed = u.Cli.atomic_read_empty_directory_state(target.value, required=False)
        if observed.failure:
            return result_type.from_failure(observed)
        before = observed.value
        if before.exists or (before.parent_device, before.parent_inode) != (
            parent_entry.created.device,
            parent_entry.created.inode,
        ):
            return result_type.fail(
                f"journaled directory parent changed before creation: {entry.path}"
            )
    elif before.path != target.value:
        return result_type.fail(
            f"journaled absent state belongs to another path: {entry.path}"
        )
    created = u.Cli.atomic_create_empty_directory_guarded(
        before, permission_mode=0o700 if entry.disposition == "temporary" else 0o755
    )
    if created.failure:
        return result_type.from_failure(created)
    try:
        return result_type.ok(
            m.Infra.CodegenJournalDirectory.model_validate({
                **entry.model_dump(),
                "before": before,
                "created": created.value,
            })
        )
    except c.ValidationError as exc:
        rolled_back = u.Cli.atomic_delete_empty_directory_guarded(created.value)
        if rolled_back.failure:
            return result_type.fail(
                f"validate created directory identity failed: {exc}; "
                f"compensation failed: {rolled_back.error}"
            )
        return result_type.fail_op("validate created directory identity", exc)


def compensate_created_directory(
    entry: m.Infra.CodegenJournalDirectory,
) -> p.Result[bool]:
    """Remove only the exact empty directory returned by this invocation."""
    if entry.created is None:
        return r[bool].fail(f"directory has no created identity: {entry.path}")
    return u.Cli.atomic_delete_empty_directory_guarded(entry.created)


def journal_state(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
    """Read the typed Git-owned journal without creating filesystem state."""
    result_type = r[tuple[m.Cli.AtomicFileState, ...]]
    snapshot = files.read_state(layout.journal_path, required=False)
    if snapshot.failure:
        return result_type.from_failure(snapshot)
    return result_type.ok((snapshot.value,))


def journal_snapshot(
    states: tuple[m.Cli.AtomicFileState, ...],
) -> m.Cli.AtomicFileState | None:
    """Return the optional journal snapshot from its non-null result payload."""
    return states[0] if states else None


def transaction_residue(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> tuple[Path, ...]:
    """Return every transaction-prefixed child or unsafe state-root alias."""
    residue: list[Path] = []
    for project in layout.projects:
        state_root = project.root / files.STATE_DIRECTORY
        if not state_root.exists() and not state_root.is_symlink():
            continue
        if state_root.is_symlink():
            residue.append(state_root)
            continue
        try:
            root_state = state_root.lstat()
            if not stat.S_ISDIR(root_state.st_mode) or _is_reparse(root_state):
                residue.append(state_root)
                continue
            children = tuple(state_root.iterdir())
        except OSError:
            residue.append(state_root)
            continue
        residue.extend(
            child
            for child in children
            if child.name.startswith(files.TRANSACTION_DIR_PREFIX)
        )
    return tuple(sorted(set(residue)))


def cleanup_journaled_directories(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
    *,
    include_generated: bool,
) -> p.Result[bool]:
    """Remove authenticated temporary trees and authorized empty directories."""
    validated = validate_transaction_roots(layout, journal)
    if validated.failure:
        return validated
    removed_temporary_roots: set[str] = set()
    for project in layout.projects:
        transaction_root = project.transaction_root
        if transaction_root is None:
            return r[bool].fail("Mise recovery layout has no transaction root")
        if not transaction_root.exists() and not transaction_root.is_symlink():
            continue
        relative = files.workspace_relative(layout.scope_root, transaction_root)
        if relative.failure:
            return r[bool].from_failure(relative)
        entry = next(
            (item for item in journal.directories if item.path == relative.value), None
        )
        if entry is None or entry.created is None:
            return r[bool].fail(
                f"transaction root has no durable physical identity: {relative.value}"
            )
        if entry.manifest is None:
            observed = u.Cli.atomic_inventory_physical_tree(transaction_root)
            if observed.failure:
                return r[bool].from_failure(observed)
            try:
                m.Infra.CodegenJournalDirectory.model_validate({
                    **entry.model_dump(),
                    "manifest": observed.value,
                })
            except c.ValidationError as exc:
                return r[bool].fail_op("validate recovery temporary-tree manifest", exc)
            removed = u.Cli.atomic_cleanup_physical_tree_guarded(observed.value)
        else:
            observed = verify.authorized_cleanup_manifest(layout, journal, entry)
            if observed.failure:
                return r[bool].from_failure(observed)
            removed = u.Cli.atomic_cleanup_physical_tree_guarded(observed.value)
        if removed.failure:
            return removed
        removed_temporary_roots.add(entry.path)
    removable = tuple(
        directory
        for directory in journal.directories
        if (
            directory.path not in removed_temporary_roots
            and (directory.disposition == "temporary" or include_generated)
        )
    )
    for entry in sorted(removable, key=_directory_cleanup_order, reverse=True):
        target = files.resolve_relative(
            layout.scope_root, entry.path, purpose="journaled cleanup directory"
        )
        if target.failure:
            return r[bool].from_failure(target)
        if not target.value.exists() and not target.value.is_symlink():
            continue
        if entry.created is None:
            return r[bool].fail(
                f"journaled directory exists without durable identity: {entry.path}"
            )
        removed = u.Cli.atomic_delete_empty_directory_guarded(entry.created)
        if removed.failure:
            return r[bool].fail(
                removed.error
                or f"journaled directory is not safely empty: {entry.path}"
            )
    return r[bool].ok(True)


def validate_transaction_roots(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
) -> p.Result[bool]:
    """Authenticate the sole journal-derived staging root in every project."""
    expected = {
        project.transaction_root
        for project in layout.projects
        if project.transaction_root is not None
    }
    unexpected = sorted(set(transaction_residue(layout)) - expected)
    if unexpected:
        return r[bool].fail(
            f"foreign generation transaction residue exists: {unexpected[0]}"
        )
    for project in layout.projects:
        transaction_root = project.transaction_root
        if transaction_root is None:
            return r[bool].fail("Mise recovery layout has no transaction root")
        transaction = _validate_transaction_root(transaction_root)
        if transaction.failure:
            return r[bool].from_failure(transaction)
        if not transaction.value:
            continue
        transaction_identity = transaction.value[0]
        relative = files.workspace_relative(layout.scope_root, transaction_root)
        if relative.failure:
            return r[bool].from_failure(relative)
        recorded = next(
            (item for item in journal.directories if item.path == relative.value), None
        )
        if (
            recorded is None
            or recorded.created is None
            or (recorded.created.device, recorded.created.inode) != transaction_identity
        ):
            return r[bool].fail(
                f"Mise transaction root identity is not journaled: {relative.value}"
            )
    return r[bool].ok(True)


def _validate_transaction_root(target: Path) -> p.Result[tuple[tuple[int, int], ...]]:
    if not target.exists() and not target.is_symlink():
        return r[tuple[tuple[int, int], ...]].ok(())
    identifier = target.name.removeprefix(files.TRANSACTION_DIR_PREFIX)
    if (
        not target.name.startswith(files.TRANSACTION_DIR_PREFIX)
        or len(identifier) != files.TRANSACTION_ID_LENGTH
        or any(character not in "0123456789abcdef" for character in identifier)
        or target.is_symlink()
    ):
        return r[tuple[tuple[int, int], ...]].fail(
            f"refusing invalid Mise transaction target: {target}"
        )
    try:
        state = target.lstat()
    except OSError as exc:
        return r[tuple[tuple[int, int], ...]].fail_op(
            "inspect Mise transaction target", exc
        )
    if not stat.S_ISDIR(state.st_mode) or _is_reparse(state):
        return r[tuple[tuple[int, int], ...]].fail(
            f"Mise transaction target is not physical: {target}"
        )
    return r[tuple[tuple[int, int], ...]].ok(((state.st_dev, state.st_ino),))


def _is_reparse(state: os.stat_result) -> bool:
    attributes = getattr(state, "st_file_attributes", 0)
    marker = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & marker)


__all__: list[str] = [
    "cleanup_journaled_directories",
    "compensate_created_directory",
    "create_journaled_directory",
    "journal_state",
    "plan_directories",
    "plan_transaction_directories",
    "transaction_residue",
    "validate_transaction_roots",
]
