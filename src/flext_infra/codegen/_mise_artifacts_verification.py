"""Physical topology, source, destination, and real-consumer verification."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra.codegen import _mise_artifacts_files as files

if TYPE_CHECKING:
    from flext_infra import p


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
        target = files.resolve_relative(
            layout.scope_root,
            directory.path,
            purpose="journaled generation directory",
        )
        if target.failure:
            return r[bool].from_failure(target)
        if (
            target.value == project.root
            or not target.value.is_relative_to(project.root)
        ):
            return r[bool].fail(
                f"generation directory escapes its project: {directory.path}"
            )
        if directory.disposition == "temporary":
            transaction_root = project.transaction_root
            if (
                directory.phase != "transaction"
                or transaction_root is None
                or not transaction_root.is_relative_to(target.value)
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
        if entry.original_backup is None:
            continue
        if project.transaction_root is None:
            return r[bool].fail("generation recovery layout has no transaction root")
        backup = files.resolve_relative(
            layout.scope_root,
            entry.original_backup,
            purpose="generation recovery backup",
        )
        if backup.failure:
            return r[bool].from_failure(backup)
        if backup.value.parent != project.transaction_root / "recovery":
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
    "destinations",
    "journal_topology",
    "live",
    "publications_live",
    "sources",
    "states_current",
]
