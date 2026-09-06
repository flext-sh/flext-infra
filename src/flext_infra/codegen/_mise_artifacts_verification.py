"""Physical topology, source, destination, and real-consumer verification."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from flext_core import r
from flext_infra import c, m, u
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra.codegen import _mise_artifacts_files as files

if TYPE_CHECKING:
    from flext_infra import p

type _JournalFileRole = Literal["desired", "backup", "rollback"]


def register_transaction_manifests(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
) -> p.Result[tuple[m.Infra.CodegenJournalDirectory, ...]]:
    """Register exact transaction trees after validating any prior authority."""
    result_type = r[tuple[m.Infra.CodegenJournalDirectory, ...]]
    registered: list[m.Infra.CodegenJournalDirectory] = []
    for directory in journal.directories:
        project = next(
            item for item in layout.projects if item.selector == directory.project
        )
        target = files.resolve_relative(
            layout.scope_root, directory.path, purpose="temporary tree manifest"
        )
        if target.failure:
            return result_type.from_failure(target)
        if (
            directory.disposition != "temporary"
            or target.value != project.transaction_root
        ):
            registered.append(directory)
            continue
        if directory.created is None:
            return result_type.fail(
                f"temporary tree has no created identity: {directory.path}"
            )
        observed = u.Cli.atomic_inventory_physical_tree(target.value)
        if observed.failure:
            return result_type.from_failure(observed)
        physical = _manifest_root_matches_created(directory, observed.value)
        if physical.failure:
            return result_type.from_failure(physical)
        if any(entry.kind == "symlink" for entry in observed.value.entries):
            return result_type.fail(
                f"temporary tree contains an alias: {directory.path}"
            )
        if directory.manifest is not None:
            transition = _validate_manifest_transition(
                layout,
                journal,
                directory.manifest,
                observed.value,
                allow_registered_additions=True,
            )
            if transition.failure:
                return result_type.from_failure(transition)
        try:
            registered.append(
                m.Infra.CodegenJournalDirectory.model_validate({
                    **directory.model_dump(),
                    "manifest": observed.value,
                })
            )
        except c.ValidationError as exc:
            return result_type.fail_op("validate temporary-tree manifest", exc)
    return result_type.ok(tuple(registered))


def authorized_cleanup_manifest(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
    directory: m.Infra.CodegenJournalDirectory,
) -> p.Result[m.Cli.AtomicPhysicalTreeManifest]:
    """Observe a tree, prove it is a journal-authorized projection, then return it."""
    result_type = r[m.Cli.AtomicPhysicalTreeManifest]
    if directory.manifest is None:
        return result_type.fail(
            f"temporary tree has no authorized manifest: {directory.path}"
        )
    observed = u.Cli.atomic_inventory_physical_tree(directory.manifest.root.path)
    if observed.failure:
        return result_type.from_failure(observed)
    if any(entry.kind == "symlink" for entry in observed.value.entries):
        return result_type.fail(
            f"temporary tree contains an unregistered alias: {directory.path}"
        )
    transition = _validate_manifest_transition(
        layout,
        journal,
        directory.manifest,
        observed.value,
        allow_registered_additions=False,
    )
    if transition.failure:
        return result_type.from_failure(transition)
    return result_type.ok(observed.value)


def journal_topology(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
) -> p.Result[bool]:
    """Bind every journal selector and physical identity to the locked layout."""
    if layout.transaction_id != journal.transaction_id:
        return r[bool].fail("generation journal transaction id differs from layout")
    scope = _directory_identity(layout.scope_root)
    if scope.failure:
        return r[bool].from_failure(scope)
    if scope.value != (journal.scope_device, journal.scope_inode):
        return r[bool].fail("generation journal scope identity differs from layout")
    if tuple(project.selector for project in journal.projects) != tuple(
        project.selector for project in layout.projects
    ):
        return r[bool].fail("generation journal project topology differs from layout")
    by_selector = {project.selector: project for project in layout.projects}
    directory_targets: dict[Path, m.Infra.CodegenJournalDirectory] = {}
    for directory in journal.directories:
        target = files.resolve_relative(
            layout.scope_root, directory.path, purpose="journaled generation directory"
        )
        if target.failure:
            return r[bool].from_failure(target)
        directory_targets[target.value] = directory
    for recorded in journal.projects:
        project = by_selector[recorded.selector]
        identity = _directory_identity(project.root)
        if identity.failure:
            return r[bool].from_failure(identity)
        if identity.value != (recorded.device, recorded.inode):
            return r[bool].fail(
                f"generation project identity changed: {recorded.selector}"
            )
    for directory in journal.directories:
        project = by_selector[directory.project]
        target = next(
            path for path, candidate in directory_targets.items() if candidate == directory
        )
        if target == project.root or not target.is_relative_to(project.root):
            return r[bool].fail(
                f"generation directory escapes its project: {directory.path}"
            )
        if directory.before is not None and directory.before.path != target:
            return r[bool].fail(
                f"generation directory preflight path differs: {directory.path}"
            )
        if directory.created is not None:
            if directory.created.path != target:
                return r[bool].fail(
                    f"generation created directory path differs: {directory.path}"
                )
            parent = directory_targets.get(target.parent)
            expected_parent = (
                (
                    directory.before.parent_device,
                    directory.before.parent_inode,
                )
                if directory.before is not None
                else (
                    None
                    if parent is None or parent.created is None
                    else (parent.created.device, parent.created.inode)
                )
            )
            if expected_parent is None or (
                directory.created.parent_device,
                directory.created.parent_inode,
            ) != expected_parent:
                return r[bool].fail(
                    f"generation directory parent binding differs: {directory.path}"
                )
        if directory.disposition == "temporary":
            transaction_root = project.transaction_root
            if (
                directory.phase != "transaction"
                or transaction_root is None
                or not transaction_root.is_relative_to(target)
            ):
                return r[bool].fail(
                    f"temporary directory escapes transaction root: {directory.path}"
                )
    for entry in journal.entries:
        project = by_selector[entry.project]
        target = files.resolve_relative(
            layout.scope_root, entry.path, purpose="generated destination"
        )
        if target.failure:
            return r[bool].from_failure(target)
        if not target.value.is_relative_to(project.root):
            return r[bool].fail(f"generation entry escapes its project: {entry.path}")
        staging_paths: list[tuple[str, str]] = []
        if entry.original_backup is not None:
            staging_paths.append(("backup", entry.original_backup))
        if entry.desired_staging is not None:
            staging_paths.append(("desired", entry.desired_staging))
        if entry.rollback_staging is not None:
            staging_paths.append(("rollback", entry.rollback_staging))
        transaction_root = project.transaction_root
        if staging_paths and transaction_root is None:
            return r[bool].fail("generation recovery layout has no transaction root")
        for role, selector in staging_paths:
            staging = files.resolve_relative(
                layout.scope_root, selector, purpose=f"generation {role} staging"
            )
            if staging.failure:
                return r[bool].from_failure(staging)
            if transaction_root is None or not staging.value.is_relative_to(
                transaction_root
            ):
                return r[bool].fail(
                    f"generation {role} staging escapes transaction root: {entry.path}"
                )
        if entry.original_backup is not None:
            backup = files.resolve_relative(
                layout.scope_root,
                entry.original_backup,
                purpose="generation recovery backup",
            )
            if backup.failure:
                return r[bool].from_failure(backup)
            if transaction_root is None or backup.value.parent != (
                transaction_root / "recovery"
            ):
                return r[bool].fail(
                    f"generation backup escapes its recovery root: {entry.path}"
                )
    return r[bool].ok(True)


def states_current(states: tuple[m.Cli.AtomicFileState, ...]) -> p.Result[bool]:
    """Prove every full file state still equals its authenticated snapshot."""
    for expected in states:
        observed = files.read_state(
            expected.path, required=expected.content is not None
        )
        if observed.failure:
            return r[bool].from_failure(observed)
        if observed.value != expected:
            return r[bool].fail(f"generation state changed: {expected.path}")
    return r[bool].ok(True)


def sources(plan: m.Infra.MiseToolchainWorkspacePlan) -> p.Result[bool]:
    """Prove every Mise config source still equals its full snapshot."""
    for project in plan.projects:
        current = FlextInfraUtilitiesProjectManagedArtifacts.snapshot_config_sources(
            project.layout.root
        )
        if current.failure:
            return r[bool].from_failure(current)
        if current.value != project.config.sources:
            return r[bool].fail(f"Mise sources changed: {project.layout.selector}")
    return r[bool].ok(True)


def destinations(plan: m.Infra.MiseToolchainWorkspacePlan) -> p.Result[bool]:
    """Prove all Mise destinations still equal the locked preflight snapshot."""
    for project in plan.projects:
        expected_states = (
            project.config.before,
            project.artifacts.unix_launcher,
            project.artifacts.windows_launcher,
            project.artifacts.lock,
        )
        current = states_current(expected_states)
        if current.failure:
            return current
    return r[bool].ok(True)


def publications_live(
    publications: tuple[m.Infra.CodegenStagedFile, ...],
) -> p.Result[bool]:
    """Prove live destinations have the exact staged inode or planned absence."""
    for publication in publications:
        observed = files.read_state(publication.before.path, required=False)
        if observed.failure:
            return r[bool].from_failure(observed)
        replacement = publication.replacement
        if replacement is None:
            if (
                observed.value.content is not None
                or observed.value.parent_device != publication.before.parent_device
                or observed.value.parent_inode != publication.before.parent_inode
            ):
                return r[bool].fail(
                    "deleted generation destination or its parent changed: "
                    f"{publication.before.path}"
                )
            continue
        current = observed.value
        if _file_identity(
            current,
            parent_device=current.parent_device,
            parent_inode=current.parent_inode,
        ) != _file_identity(
            replacement,
            parent_device=publication.before.parent_device,
            parent_inode=publication.before.parent_inode,
        ):
            return r[bool].fail(
                f"live generation destination differs from staged identity: {current.path}"
            )
    return r[bool].ok(True)


def live(
    owner: p.Infra.MiseArtifactsOwner,
    plan: m.Infra.MiseToolchainWorkspacePlan,
    publications: tuple[m.Infra.CodegenStagedFile, ...] | None = None,
) -> p.Result[bool]:
    """Exercise every real Mise consumer while guarding sources and live bytes."""
    source_before = sources(plan)
    if source_before.failure:
        return source_before
    replacements: dict[Path, tuple[bytes, int | None]] = {}
    for publication in publications or ():
        replacement = publication.replacement
        if replacement is None or replacement.content is None:
            return r[bool].fail(
                f"Mise replacement is absent: {publication.before.path}"
            )
        replacements[publication.before.path] = (replacement.content, replacement.mode)
    artifact_before = _artifact_snapshot(plan, replacements)
    if artifact_before.failure:
        return r[bool].from_failure(artifact_before)
    for project in plan.projects:
        validated = owner.validate_artifacts(
            project.layout.root, config_sources=project.config.sources
        )
        if validated.failure:
            return r[bool].fail(
                validated.error
                or f"published Mise validation failed for {project.layout.selector}"
            )
    artifact_after = _artifact_snapshot(plan, replacements)
    if artifact_after.failure:
        return r[bool].from_failure(artifact_after)
    if artifact_after.value != artifact_before.value:
        return r[bool].fail("published Mise artifacts changed during validation")
    source_after = sources(plan)
    if source_after.failure:
        return source_after
    return r[bool].ok(True)


def _validate_manifest_transition(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
    authorized: m.Cli.AtomicPhysicalTreeManifest,
    observed: m.Cli.AtomicPhysicalTreeManifest,
    *,
    allow_registered_additions: bool,
) -> p.Result[bool]:
    """Accept only stable objects and explicitly journaled file transitions."""
    if not _same_directory_identity(authorized.root, observed.root):
        return r[bool].fail(
            f"temporary tree root identity changed: {authorized.root.path}"
        )
    expected = {entry.path: entry for entry in authorized.entries}
    current = {entry.path: entry for entry in observed.entries}
    file_specs = _journal_file_specs(layout, journal)
    if file_specs.failure:
        return r[bool].from_failure(file_specs)
    consumable = {
        path
        for path, (role, _entry) in file_specs.value.items()
        if role in {"desired", "rollback"}
    }
    for path, entry in expected.items():
        current_entry = current.get(path)
        if current_entry is None:
            if entry.kind == "file" and path in consumable:
                continue
            return r[bool].fail(
                f"journaled temporary-tree entry is missing: {path}"
            )
        if entry.kind == "directory":
            if not _same_directory_identity(entry, current_entry):
                return r[bool].fail(
                    f"temporary-tree directory identity changed: {path}"
                )
        elif current_entry != entry:
            return r[bool].fail(f"temporary-tree file identity changed: {path}")
    additions = tuple(
        entry for path, entry in current.items() if path not in expected
    )
    if additions and not allow_registered_additions:
        return r[bool].fail(
            f"unregistered temporary-tree entry exists: {additions[0].path}"
        )
    authorized_files = set(file_specs.value)
    for entry in additions:
        if entry.kind == "directory":
            if not any(entry.path in path.parents for path in authorized_files):
                return r[bool].fail(
                    f"unregistered temporary-tree directory exists: {entry.path}"
                )
            continue
        spec = file_specs.value.get(entry.path)
        if spec is None or not _matches_journal_file(entry, *spec):
            return r[bool].fail(
                f"unregistered temporary-tree file exists: {entry.path}"
            )
    return r[bool].ok(True)


def _journal_file_specs(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.CodegenTransactionJournal,
) -> p.Result[dict[Path, tuple[_JournalFileRole, m.Infra.CodegenJournalEntry]]]:
    result_type = r[
        dict[Path, tuple[_JournalFileRole, m.Infra.CodegenJournalEntry]]
    ]
    specs: dict[
        Path, tuple[_JournalFileRole, m.Infra.CodegenJournalEntry]
    ] = {}
    for entry in journal.entries:
        selectors: tuple[tuple[_JournalFileRole, str | None], ...] = (
            ("desired", entry.desired_staging),
            ("backup", entry.original_backup),
            ("rollback", entry.rollback_staging),
        )
        for role, selector in selectors:
            if selector is None:
                continue
            resolved = files.resolve_relative(
                layout.scope_root, selector, purpose=f"{role} staging file"
            )
            if resolved.failure:
                return result_type.from_failure(resolved)
            previous = specs.get(resolved.value)
            if previous is not None and previous != (role, entry):
                return result_type.fail(
                    f"temporary file has multiple journal owners: {selector}"
                )
            specs[resolved.value] = (role, entry)
    return result_type.ok(specs)


def _matches_journal_file(
    observed: m.Cli.AtomicPhysicalTreeEntry,
    role: _JournalFileRole,
    entry: m.Infra.CodegenJournalEntry,
) -> bool:
    if observed.kind != "file":
        return False
    if role == "desired":
        expected = (
            entry.desired_sha256,
            entry.desired_mode,
            entry.desired_device,
            entry.desired_inode,
            entry.desired_link_count,
            entry.desired_file_attributes,
            entry.desired_reparse_tag,
        )
    elif role == "rollback":
        expected = (
            entry.rollback_sha256,
            entry.rollback_mode,
            entry.rollback_device,
            entry.rollback_inode,
            entry.rollback_link_count,
            entry.rollback_file_attributes,
            entry.rollback_reparse_tag,
        )
    else:
        expected = (
            entry.original_sha256,
            files.JOURNAL_MODE,
            observed.device,
            observed.inode,
            1,
            observed.file_attributes,
            observed.reparse_tag,
        )
    actual = (
        observed.sha256,
        observed.mode,
        observed.device,
        observed.inode,
        observed.link_count,
        observed.file_attributes,
        observed.reparse_tag,
    )
    return actual == expected


def _same_directory_identity(
    expected: m.Cli.AtomicPhysicalTreeEntry,
    observed: m.Cli.AtomicPhysicalTreeEntry,
) -> bool:
    return (
        expected.path,
        expected.kind,
        expected.parent_device,
        expected.parent_inode,
        expected.parent_mount_id,
        expected.mode,
        expected.device,
        expected.inode,
        expected.mount_id,
        expected.uid,
        expected.gid,
        expected.file_attributes,
        expected.reparse_tag,
    ) == (
        observed.path,
        observed.kind,
        observed.parent_device,
        observed.parent_inode,
        observed.parent_mount_id,
        observed.mode,
        observed.device,
        observed.inode,
        observed.mount_id,
        observed.uid,
        observed.gid,
        observed.file_attributes,
        observed.reparse_tag,
    )


def _manifest_root_matches_created(
    directory: m.Infra.CodegenJournalDirectory,
    manifest: m.Cli.AtomicPhysicalTreeManifest,
) -> p.Result[bool]:
    created = directory.created
    if created is None:
        return r[bool].fail(
            f"temporary tree has no created identity: {directory.path}"
        )
    root = manifest.root
    if (
        root.path,
        root.parent_device,
        root.parent_inode,
        root.mode,
        root.device,
        root.inode,
        root.file_attributes,
        root.reparse_tag,
    ) != (
        created.path,
        created.parent_device,
        created.parent_inode,
        created.mode,
        created.device,
        created.inode,
        created.file_attributes,
        created.reparse_tag,
    ):
        return r[bool].fail(
            f"temporary tree differs from created identity: {directory.path}"
        )
    return r[bool].ok(True)


def _artifact_snapshot(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    replacements: dict[Path, tuple[bytes, int | None]],
) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
    root_launchers: tuple[bytes, bytes] | None = None
    states: list[m.Cli.AtomicFileState] = []
    for project in plan.projects:
        artifacts = (
            project.config.before,
            project.artifacts.unix_launcher,
            project.artifacts.windows_launcher,
            project.artifacts.lock,
        )
        observed: list[bytes] = []
        for expected, (_name, required_mode) in zip(
            artifacts, files.PUBLICATION_SPECS, strict=True
        ):
            current = files.read_state(expected.path, required=True)
            if current.failure or current.value.content is None:
                return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                    current.error
                    or f"published Mise artifact is absent: {expected.path}"
                )
            expected_state = replacements.get(
                expected.path, (expected.content, expected.mode)
            )
            if (current.value.content, current.value.mode) != expected_state:
                return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                    f"published Mise artifact differs from plan: {expected.path}"
                )
            if current.value.mode != required_mode:
                return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                    f"published Mise artifact mode is noncanonical: {expected.path}"
                )
            observed.append(current.value.content)
            states.append(current.value)
        launchers = (observed[1], observed[2])
        if root_launchers is None:
            root_launchers = launchers
        elif launchers != root_launchers:
            return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                f"published Mise launchers differ in {project.layout.selector}"
            )
    return r[tuple[m.Cli.AtomicFileState, ...]].ok(tuple(states))


def _file_identity(
    value: m.Cli.AtomicFileState, *, parent_device: int, parent_inode: int
) -> tuple[
    int,
    int,
    bytes | None,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
    int | None,
]:
    """Return every physical and byte field except the intentionally moved path."""
    return (
        parent_device,
        parent_inode,
        value.content,
        value.mode,
        value.device,
        value.inode,
        value.link_count,
        value.file_attributes,
        value.reparse_tag,
    )


def _directory_identity(path: Path) -> p.Result[tuple[int, int]]:
    try:
        observed = path.lstat()
    except OSError as exc:
        return r[tuple[int, int]].fail_op("inspect generation directory", exc)
    reparse = getattr(observed, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
    )
    if not stat.S_ISDIR(observed.st_mode) or reparse:
        return r[tuple[int, int]].fail(f"generation directory is not physical: {path}")
    return r[tuple[int, int]].ok((observed.st_dev, observed.st_ino))


__all__: list[str] = [
    "authorized_cleanup_manifest",
    "destinations",
    "journal_topology",
    "live",
    "publications_live",
    "register_transaction_manifests",
    "sources",
    "states_current",
]
