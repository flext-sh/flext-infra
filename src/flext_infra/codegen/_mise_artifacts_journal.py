"""Durable journal for one extensible workspace generation transaction."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

from flext_core import r
from flext_infra import c, m, u
from flext_infra.codegen import _mise_artifacts_files as files
from flext_infra.codegen import _mise_artifacts_process as process
from flext_infra.codegen import _mise_artifacts_state as state

if TYPE_CHECKING:
    from flext_infra import p


def begin(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    *,
    transaction_id: str,
    sources: tuple[tuple[str, m.Cli.AtomicFileState], ...] = (),
    directories: tuple[m.Infra.CodegenJournalDirectory, ...] = (),
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Build staging authority before any disposable transaction root exists."""
    physical_scope = files.physical_directory_identity(plan.layout.scope_root)
    if physical_scope.failure:
        return r[m.Infra.CodegenTransactionJournal].from_failure(physical_scope)
    projects: list[m.Infra.CodegenJournalProject] = []
    for project in plan.projects:
        physical_project = files.physical_directory_identity(project.layout.root)
        if physical_project.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(physical_project)
        projects.append(
            m.Infra.CodegenJournalProject(
                selector=project.layout.selector,
                device=physical_project.value[0],
                inode=physical_project.value[1],
            )
        )
    encoded_sources = _merge_sources((), sources)
    if encoded_sources.failure:
        return r[m.Infra.CodegenTransactionJournal].from_failure(encoded_sources)
    try:
        return r[m.Infra.CodegenTransactionJournal].ok(
            m.Infra.CodegenTransactionJournal(
                version=8,
                transaction_id=transaction_id,
                scope_device=physical_scope.value[0],
                scope_inode=physical_scope.value[1],
                state="staging",
                projects=tuple(projects),
                sources=encoded_sources.value,
                directories=directories,
                entries=(),
            )
        )
    except c.ValidationError as exc:
        return r[m.Infra.CodegenTransactionJournal].fail_op(
            "validate staging codegen journal", exc
        )


def append_prepared(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    journal: m.Infra.CodegenTransactionJournal,
    publications: tuple[m.Infra.CodegenStagedFile, ...],
    *,
    sources: tuple[tuple[str, m.Cli.AtomicFileState], ...] = (),
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Back up one complete phase and return its extended prepared authority."""
    if journal.state not in {"staging", "prepared"}:
        return r[m.Infra.CodegenTransactionJournal].fail(
            "only staging or prepared codegen journal accepts a phase"
        )
    topology = _validate_physical_topology(plan, journal)
    if topology.failure:
        return r[m.Infra.CodegenTransactionJournal].from_failure(topology)
    existing_paths = {entry.path for entry in journal.entries}
    entries = list(journal.entries)
    recovery_roots: set[Path] = set()
    for offset, publication in enumerate(publications, start=len(entries)):
        target = files.workspace_relative(
            plan.layout.scope_root, publication.before.path
        )
        if target.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(target)
        if target.value in existing_paths:
            return r[m.Infra.CodegenTransactionJournal].fail(
                f"multiple generation phases own one destination: {target.value}"
            )
        entry = _journal_entry(
            plan, publication, index=offset, recovery_roots=recovery_roots
        )
        if entry.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(entry)
        entries.append(entry.value)
        existing_paths.add(entry.value.path)
    encoded_sources = _merge_sources(journal.sources, sources)
    if encoded_sources.failure:
        return r[m.Infra.CodegenTransactionJournal].from_failure(encoded_sources)
    try:
        return r[m.Infra.CodegenTransactionJournal].ok(
            m.Infra.CodegenTransactionJournal(
                version=8,
                transaction_id=journal.transaction_id,
                scope_device=journal.scope_device,
                scope_inode=journal.scope_inode,
                state="prepared",
                projects=journal.projects,
                sources=encoded_sources.value,
                directories=journal.directories,
                entries=tuple(entries),
            )
        )
    except c.ValidationError as exc:
        return r[m.Infra.CodegenTransactionJournal].fail_op(
            "validate prepared codegen journal", exc
        )


def append_directories(
    journal: m.Infra.CodegenTransactionJournal,
    directories: tuple[m.Infra.CodegenJournalDirectory, ...],
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Extend durable directory authority before materializing any new path."""
    if journal.state not in {"staging", "prepared"}:
        return r[m.Infra.CodegenTransactionJournal].fail(
            "only staging or prepared codegen journal accepts directories"
        )
    existing = {directory.path for directory in journal.directories}
    duplicate = next(
        (directory.path for directory in directories if directory.path in existing),
        None,
    )
    if duplicate is not None:
        return r[m.Infra.CodegenTransactionJournal].fail(
            f"generation directory already has an owner: {duplicate}"
        )
    try:
        return r[m.Infra.CodegenTransactionJournal].ok(
            m.Infra.CodegenTransactionJournal(
                version=8,
                transaction_id=journal.transaction_id,
                scope_device=journal.scope_device,
                scope_inode=journal.scope_inode,
                state=journal.state,
                projects=journal.projects,
                sources=journal.sources,
                directories=(*journal.directories, *directories),
                entries=journal.entries,
            )
        )
    except c.ValidationError as exc:
        return r[m.Infra.CodegenTransactionJournal].fail_op(
            "validate extended codegen directory journal", exc
        )


def record_directories(
    journal: m.Infra.CodegenTransactionJournal,
    directories: tuple[m.Infra.CodegenJournalDirectory, ...],
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Advance physical directory evidence without changing its durable intent."""
    result_type = r[m.Infra.CodegenTransactionJournal]
    if tuple(directory.path for directory in directories) != tuple(
        directory.path for directory in journal.directories
    ):
        return result_type.fail("recorded directory topology differs from journal")
    for previous, current in zip(journal.directories, directories, strict=True):
        stable_previous = previous.model_dump(exclude={"before", "created", "manifest"})
        stable_current = current.model_dump(exclude={"before", "created", "manifest"})
        if stable_current != stable_previous:
            return result_type.fail(
                f"recorded directory intent changed: {previous.path}"
            )
        if previous.before is not None and current.before != previous.before:
            return result_type.fail(
                f"recorded directory parent binding changed: {previous.path}"
            )
        if previous.before is None and current.before is None and current.created:
            return result_type.fail(
                f"created directory lacks parent binding: {previous.path}"
            )
        if previous.created is not None and current.created != previous.created:
            return result_type.fail(
                f"recorded directory physical identity changed: {previous.path}"
            )
        if previous.manifest is not None and current.manifest is None:
            return result_type.fail(
                f"recorded directory manifest disappeared: {previous.path}"
            )
    try:
        return result_type.ok(
            m.Infra.CodegenTransactionJournal(
                version=8,
                transaction_id=journal.transaction_id,
                scope_device=journal.scope_device,
                scope_inode=journal.scope_inode,
                state=journal.state,
                projects=journal.projects,
                sources=journal.sources,
                directories=directories,
                entries=journal.entries,
            )
        )
    except c.ValidationError as exc:
        return result_type.fail_op("validate recorded directory evidence", exc)


def commit(
    journal: m.Infra.CodegenTransactionJournal,
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Validate the sole prepared-to-committed transition."""
    if journal.state != "prepared":
        return r[m.Infra.CodegenTransactionJournal].fail(
            "only a prepared codegen journal can be committed"
        )
    try:
        return r[m.Infra.CodegenTransactionJournal].ok(
            m.Infra.CodegenTransactionJournal(
                version=8,
                transaction_id=journal.transaction_id,
                scope_device=journal.scope_device,
                scope_inode=journal.scope_inode,
                state="committed",
                projects=journal.projects,
                sources=journal.sources,
                directories=journal.directories,
                entries=journal.entries,
            )
        )
    except c.ValidationError as exc:
        return r[m.Infra.CodegenTransactionJournal].fail_op(
            "validate committed codegen journal", exc
        )


def begin_recovery(
    journal: m.Infra.CodegenTransactionJournal,
    candidates: tuple[m.Infra.CodegenStagedFile | None, ...],
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Persist every rollback replacement identity before the first restore."""
    if journal.state != "prepared" or len(candidates) != len(journal.entries):
        return r[m.Infra.CodegenTransactionJournal].fail(
            "codegen recovery candidates differ from prepared journal"
        )
    entries: list[m.Infra.CodegenJournalEntry] = []
    for entry, candidate in zip(journal.entries, candidates, strict=True):
        replacement = None if candidate is None else candidate.replacement
        if entry.original_exists and (
            replacement is None or replacement.content is None
        ):
            return r[m.Infra.CodegenTransactionJournal].fail(
                f"codegen rollback candidate is incomplete: {entry.path}"
            )
        entry_data = entry.model_dump()
        entry_data.update({
            "rollback_exists": entry.original_exists,
            "rollback_parent_device": entry.original_parent_device,
            "rollback_parent_inode": entry.original_parent_inode,
            "rollback_sha256": (
                None
                if replacement is None or replacement.content is None
                else files.digest(replacement.content)
            ),
            "rollback_mode": None if replacement is None else replacement.mode,
            "rollback_device": None if replacement is None else replacement.device,
            "rollback_inode": None if replacement is None else replacement.inode,
            "rollback_link_count": (
                None if replacement is None else replacement.link_count
            ),
            "rollback_file_attributes": (
                None if replacement is None else replacement.file_attributes
            ),
            "rollback_reparse_tag": (
                None if replacement is None else replacement.reparse_tag
            ),
            "rollback_staging": (
                None
                if replacement is None or entry.original_backup is None
                else Path(entry.original_backup).with_suffix(".restore").as_posix()
            ),
        })
        try:
            entries.append(m.Infra.CodegenJournalEntry.model_validate(entry_data))
        except c.ValidationError as exc:
            return r[m.Infra.CodegenTransactionJournal].fail_op(
                "validate recovering codegen journal entry", exc
            )
    try:
        return r[m.Infra.CodegenTransactionJournal].ok(
            m.Infra.CodegenTransactionJournal(
                version=8,
                transaction_id=journal.transaction_id,
                scope_device=journal.scope_device,
                scope_inode=journal.scope_inode,
                state="recovering",
                projects=journal.projects,
                sources=journal.sources,
                directories=journal.directories,
                entries=tuple(entries),
            )
        )
    except c.ValidationError as exc:
        return r[m.Infra.CodegenTransactionJournal].fail_op(
            "validate recovering codegen journal", exc
        )


def write(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
    *,
    expected: tuple[m.Cli.AtomicFileState, ...],
) -> p.Result[m.Cli.AtomicFileState]:
    """Create or transition the common journal with full-state CAS."""
    content = journal.model_dump_json(indent=2).encode(c.Cli.ENCODING_DEFAULT)
    if expected.path != layout.journal_path:
        return r[m.Cli.AtomicFileState].fail(
            "codegen journal expected state belongs to another path"
        )
    written = u.Cli.atomic_write_binary_file_guarded(
        expected, content, permission_mode=files.JOURNAL_MODE
    )
    if written.failure:
        return r[m.Cli.AtomicFileState].fail(
            written.error or "cannot publish codegen transaction journal"
        )
    observed = state.journal_state(layout)
    if observed.failure:
        return r[m.Cli.AtomicFileState].from_failure(observed)
    observed_snapshot = state.journal_snapshot(observed.value)
    if observed_snapshot is None:
        return r[m.Cli.AtomicFileState].fail(
            "published codegen journal parent disappeared"
        )
    if (
        observed_snapshot.content != content
        or observed_snapshot.mode != files.JOURNAL_MODE
    ):
        return r[m.Cli.AtomicFileState].fail(
            "published codegen journal differs from exact bytes or mode"
        )
    return r[m.Cli.AtomicFileState].ok(observed_snapshot)


def read(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
) -> p.Result[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
    """Parse the typed v8 journal without deriving a second filesystem path."""
    snapshot = state.journal_state(layout)
    result_type = r[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]
    if snapshot.failure:
        return result_type.from_failure(snapshot)
    journal_snapshot = state.journal_snapshot(snapshot.value)
    if journal_snapshot is None or journal_snapshot.content is None:
        return result_type.fail("codegen transaction journal is absent")
    if journal_snapshot.mode != files.JOURNAL_MODE:
        return result_type.fail("codegen transaction journal mode is not 0600")
    try:
        journal = m.Infra.CodegenTransactionJournal.model_validate_json(
            journal_snapshot.content
        )
    except c.ValidationError as exc:
        return result_type.fail_op("validate codegen transaction journal", exc)
    relocated = _relocate_journal(layout, journal)
    if relocated.failure:
        return result_type.from_failure(relocated)
    return result_type.ok((relocated.value, journal_snapshot))


def cleanup(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
    journal_state: m.Cli.AtomicFileState,
) -> p.Result[bool]:
    """Retain journal authority until all journal-authorized cleanup completes."""
    directories = state.cleanup_journaled_directories(
        layout, journal, include_generated=journal.state != "committed"
    )
    if directories.failure:
        return directories
    removed = files.delete_state(journal_state)
    if removed.failure:
        return r[bool].fail(removed.error or "cannot remove codegen journal")
    return r[bool].ok(True)


def _relocate_journal(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
) -> p.Result[m.Infra.CodegenTransactionJournal]:
    """Rebind authenticated paths when the same physical worktree was moved."""
    result_type = r[m.Infra.CodegenTransactionJournal]
    identity = files.physical_directory_identity(layout.scope_root)
    if identity.failure:
        return result_type.from_failure(identity)
    if identity.value != (journal.scope_device, journal.scope_inode):
        return result_type.fail("generation journal belongs to another physical scope")
    recorded_root = _recorded_scope_root(journal)
    if recorded_root.failure:
        return result_type.from_failure(recorded_root)
    if recorded_root.value == layout.scope_root:
        return result_type.ok(journal)
    sources: list[m.Infra.CodegenJournalSource] = []
    directories: list[m.Infra.CodegenJournalDirectory] = []
    for source in journal.sources:
        rebound = _relocated_path(source.path, recorded_root.value, layout.scope_root)
        if rebound.failure:
            return result_type.from_failure(rebound)
        sources.append(source.model_copy(update={"path": rebound.value}))
    for directory in journal.directories:
        before: m.Cli.AtomicDirectoryState | None = None
        if directory.before is not None:
            relocated_before = _relocate_directory_state(
                directory.before, recorded_root.value, layout.scope_root
            )
            if relocated_before.failure:
                return result_type.from_failure(relocated_before)
            before = relocated_before.value
        created: m.Cli.AtomicDirectoryState | None = None
        if directory.created is not None:
            relocated_created = _relocate_directory_state(
                directory.created, recorded_root.value, layout.scope_root
            )
            if relocated_created.failure:
                return result_type.from_failure(relocated_created)
            created = relocated_created.value
        manifest: m.Cli.AtomicPhysicalTreeManifest | None = None
        if directory.manifest is not None:
            relocated_manifest = _relocate_manifest(
                directory.manifest, recorded_root.value, layout.scope_root
            )
            if relocated_manifest.failure:
                return result_type.from_failure(relocated_manifest)
            manifest = relocated_manifest.value
        try:
            directories.append(
                m.Infra.CodegenJournalDirectory.model_validate({
                    **directory.model_dump(),
                    "before": before,
                    "created": created,
                    "manifest": manifest,
                })
            )
        except c.ValidationError as exc:
            return result_type.fail_op("relocate generation directory", exc)
    try:
        return result_type.ok(
            m.Infra.CodegenTransactionJournal.model_validate({
                **journal.model_dump(),
                "sources": tuple(sources),
                "directories": tuple(directories),
            })
        )
    except c.ValidationError as exc:
        return result_type.fail_op("relocate generation journal", exc)


def _recorded_scope_root(journal: m.Infra.CodegenTransactionJournal) -> p.Result[Path]:
    candidates: set[Path] = set()
    for directory in journal.directories:
        relative = Path(directory.path)
        for directory_state in (directory.before, directory.created):
            if directory_state is None:
                continue
            candidate = directory_state.path
            for _part in relative.parts:
                candidate = candidate.parent
            if candidate / relative != directory_state.path:
                return r[Path].fail(
                    f"generation directory path is inconsistent: {directory.path}"
                )
            candidates.add(candidate)
    if len(candidates) != 1:
        return r[Path].fail("generation journal has no single recorded scope path")
    return r[Path].ok(candidates.pop())


def _relocated_path(
    path: Path, previous_root: Path, current_root: Path
) -> p.Result[Path]:
    if not path.is_relative_to(previous_root):
        return r[Path].fail(f"generation journal path escapes recorded scope: {path}")
    return r[Path].ok(current_root / path.relative_to(previous_root))


def _relocate_directory_state(
    directory_state: m.Cli.AtomicDirectoryState, previous_root: Path, current_root: Path
) -> p.Result[m.Cli.AtomicDirectoryState]:
    rebound = _relocated_path(directory_state.path, previous_root, current_root)
    if rebound.failure:
        return r[m.Cli.AtomicDirectoryState].from_failure(rebound)
    return r[m.Cli.AtomicDirectoryState].ok(
        directory_state.model_copy(update={"path": rebound.value})
    )


def _relocate_manifest(
    manifest: m.Cli.AtomicPhysicalTreeManifest, previous_root: Path, current_root: Path
) -> p.Result[m.Cli.AtomicPhysicalTreeManifest]:
    result_type = r[m.Cli.AtomicPhysicalTreeManifest]
    relocated: list[m.Cli.AtomicPhysicalTreeEntry] = []
    for entry in (manifest.root, *manifest.entries):
        rebound = _relocated_path(entry.path, previous_root, current_root)
        if rebound.failure:
            return result_type.from_failure(rebound)
        relocated.append(entry.model_copy(update={"path": rebound.value}))
    try:
        return result_type.ok(
            m.Cli.AtomicPhysicalTreeManifest(
                root=relocated[0], entries=tuple(relocated[1:])
            )
        )
    except c.ValidationError as exc:
        return result_type.fail_op("relocate generation tree manifest", exc)


def _journal_source(
    phase: str, source: m.Cli.AtomicFileState
) -> p.Result[m.Infra.CodegenJournalSource]:
    if (
        source.content is None
        or source.mode is None
        or source.device is None
        or source.inode is None
        or source.link_count != 1
    ):
        return r[m.Infra.CodegenJournalSource].fail(
            f"generation source is absent or incomplete: {source.path}"
        )
    return r[m.Infra.CodegenJournalSource].ok(
        m.Infra.CodegenJournalSource(
            phase=phase,
            path=source.path,
            parent_device=source.parent_device,
            parent_inode=source.parent_inode,
            sha256=files.digest(source.content),
            mode=source.mode,
            device=source.device,
            inode=source.inode,
            link_count=source.link_count,
            file_attributes=source.file_attributes,
            reparse_tag=source.reparse_tag,
        )
    )


def _merge_sources(
    existing: tuple[m.Infra.CodegenJournalSource, ...],
    sources: tuple[tuple[str, m.Cli.AtomicFileState], ...],
) -> p.Result[tuple[m.Infra.CodegenJournalSource, ...]]:
    result_type = r[tuple[m.Infra.CodegenJournalSource, ...]]
    by_key = {(source.phase, source.path): source for source in existing}
    order = [(source.phase, source.path) for source in existing]
    for phase, source in sources:
        encoded = _journal_source(phase, source)
        if encoded.failure:
            return result_type.from_failure(encoded)
        key = (encoded.value.phase, encoded.value.path)
        previous = by_key.get(key)
        if previous is not None and previous != encoded.value:
            return result_type.fail(
                f"generation source changed between phases: {encoded.value.path}"
            )
        if previous is None:
            by_key[key] = encoded.value
            order.append(key)
    return result_type.ok(tuple(by_key[key] for key in order))


def _journal_entry(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    publication: m.Infra.CodegenStagedFile,
    *,
    index: int,
    recovery_roots: set[Path],
) -> p.Result[m.Infra.CodegenJournalEntry]:
    before = publication.before
    project = next(
        (item for item in plan.projects if item.layout.root == publication.project),
        None,
    )
    if project is None or project.layout.transaction_root is None:
        return r[m.Infra.CodegenJournalEntry].fail(
            f"generation publication has no transaction participant: {before.path}"
        )
    selector = files.workspace_relative(plan.layout.scope_root, before.path)
    if selector.failure:
        return r[m.Infra.CodegenJournalEntry].from_failure(selector)
    backup_selector: str | None = None
    original_sha: str | None = None
    if before.content is not None:
        if (
            before.mode is None
            or before.device is None
            or before.inode is None
            or before.link_count != 1
        ):
            return r[m.Infra.CodegenJournalEntry].fail(
                f"generation original identity is incomplete: {before.path}"
            )
        recovery_root = project.layout.transaction_root / "recovery"
        if recovery_root not in recovery_roots:
            if recovery_root.exists() or recovery_root.is_symlink():
                inventory = u.Cli.atomic_inventory_physical_tree(recovery_root)
                if inventory.failure:
                    return r[m.Infra.CodegenJournalEntry].from_failure(inventory)
            else:
                directory_before = u.Cli.atomic_read_empty_directory_state(
                    recovery_root, required=False
                )
                if directory_before.failure:
                    return r[m.Infra.CodegenJournalEntry].from_failure(directory_before)
                created = u.Cli.atomic_create_empty_directory_guarded(
                    directory_before.value, permission_mode=0o700
                )
                if created.failure:
                    return r[m.Infra.CodegenJournalEntry].from_failure(created)
            recovery_roots.add(recovery_root)
        backup = recovery_root / f"{index:06d}.original"
        written = process.write_new(backup, before.content, files.JOURNAL_MODE)
        if written.failure:
            return r[m.Infra.CodegenJournalEntry].fail(
                written.error or f"cannot back up generated file: {before.path}"
            )
        relative_backup = files.workspace_relative(plan.layout.scope_root, backup)
        if relative_backup.failure:
            return r[m.Infra.CodegenJournalEntry].from_failure(relative_backup)
        backup_selector = relative_backup.value
        original_sha = files.digest(before.content)
    replacement = publication.replacement
    desired_exists = replacement is not None
    incomplete_replacement = replacement is not None and any((
        replacement.content is None,
        replacement.mode is None,
        replacement.device is None,
        replacement.inode is None,
        replacement.link_count != 1,
    ))
    if incomplete_replacement:
        return r[m.Infra.CodegenJournalEntry].fail(
            f"generation staged identity is incomplete: {before.path}"
        )
    desired_staging: str | None = None
    if replacement is not None:
        relative_staging = files.workspace_relative(
            plan.layout.scope_root, replacement.path
        )
        if relative_staging.failure:
            return r[m.Infra.CodegenJournalEntry].from_failure(relative_staging)
        desired_staging = relative_staging.value
    return r[m.Infra.CodegenJournalEntry].ok(
        m.Infra.CodegenJournalEntry(
            phase=publication.phase,
            project=project.layout.selector,
            path=selector.value,
            desired_staging=desired_staging,
            original_exists=before.content is not None,
            original_parent_device=before.parent_device,
            original_parent_inode=before.parent_inode,
            original_backup=backup_selector,
            original_sha256=original_sha,
            original_mode=before.mode,
            original_device=before.device,
            original_inode=before.inode,
            original_link_count=cast("Literal[1] | None", before.link_count),
            original_file_attributes=before.file_attributes,
            original_reparse_tag=before.reparse_tag,
            desired_exists=desired_exists,
            desired_parent_device=before.parent_device,
            desired_parent_inode=before.parent_inode,
            desired_sha256=(
                files.digest(replacement.content)
                if replacement is not None and replacement.content is not None
                else None
            ),
            desired_mode=None if replacement is None else replacement.mode,
            desired_device=None if replacement is None else replacement.device,
            desired_inode=None if replacement is None else replacement.inode,
            desired_link_count=(
                None
                if replacement is None
                else cast("Literal[1]", replacement.link_count)
            ),
            desired_file_attributes=(
                None if replacement is None else replacement.file_attributes
            ),
            desired_reparse_tag=(
                None if replacement is None else replacement.reparse_tag
            ),
        )
    )


def _validate_physical_topology(
    plan: m.Infra.MiseToolchainWorkspacePlan, journal: m.Infra.CodegenTransactionJournal
) -> p.Result[bool]:
    scope = files.physical_directory_identity(plan.layout.scope_root)
    if scope.failure:
        return r[bool].from_failure(scope)
    if scope.value != (journal.scope_device, journal.scope_inode):
        return r[bool].fail("generation scope changed during transaction")
    expected = tuple(project.layout.selector for project in plan.projects)
    observed = tuple(project.selector for project in journal.projects)
    if observed != expected:
        return r[bool].fail("generation project topology changed during transaction")
    for planned, recorded in zip(plan.projects, journal.projects, strict=True):
        identity = files.physical_directory_identity(planned.layout.root)
        if identity.failure:
            return r[bool].from_failure(identity)
        if identity.value != (recorded.device, recorded.inode):
            return r[bool].fail(
                f"generation project changed during transaction: {recorded.selector}"
            )
    return r[bool].ok(True)


__all__: list[str] = [
    "append_directories",
    "append_prepared",
    "begin",
    "begin_recovery",
    "cleanup",
    "commit",
    "read",
    "record_directories",
    "write",
]
