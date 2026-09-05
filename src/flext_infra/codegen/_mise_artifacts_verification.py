"""Topology, source, and live-state verification for Mise transactions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import _mise_artifacts_files as files

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


def journal_topology(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.MiseToolchainJournal,
    publications: tuple[m.Cli.AtomicFilePublication, ...] | None = None,
) -> p.Result[bool]:
    """Bind every untrusted journal entry to the stable workspace layout."""
    if journal.projects != tuple(project.selector for project in layout.projects):
        return r[bool].fail("Mise journal project topology differs from layout")
    source_topology = _journal_source_topology(layout, journal.sources)
    if source_topology.failure:
        return source_topology
    directories = _journal_directory_topology(layout, journal, publications)
    if directories.failure:
        return directories
    if journal.state == "staging":
        return r[bool].ok(True)
    observed_paths = tuple(entry.path for entry in journal.entries)
    if len(set(observed_paths)) != len(observed_paths):
        return r[bool].fail("codegen journal destination paths are not unique")
    if publications is not None:
        expected_entries: list[tuple[str, str | None, int | None]] = []
        for item in publications:
            selector = files.workspace_relative(layout.scope_root, item.before.path)
            if selector.failure:
                return r[bool].from_failure(selector)
            expected_entries.append((
                selector.value,
                None
                if item.replacement.content is None
                else u.Cli.sha256_bytes(item.replacement.content),
                item.replacement.mode,
            ))
        observed_entries = tuple(
            (entry.path, entry.replacement_sha256, entry.replacement_mode)
            for entry in journal.entries
        )
        if observed_entries != tuple(expected_entries):
            return r[bool].fail(
                "codegen journal entries differ from staged publications"
            )
    for index, entry in enumerate(journal.entries):
        target = files.resolve_relative(
            layout.scope_root, entry.path, purpose="codegen journal destination"
        )
        if target.failure:
            return r[bool].from_failure(target)
        project = files.project_for_path(layout, target.value)
        if project.failure:
            return r[bool].from_failure(project)
        expected_backup: str | None = None
        if entry.original_exists:
            relative = files.workspace_relative(
                layout.state_root,
                project.value.transaction_root / "recovery" / f"{index:04d}.original",
            )
            if relative.failure:
                return r[bool].from_failure(relative)
            expected_backup = relative.value
        if entry.original_backup != expected_backup:
            return r[bool].fail(
                "Mise journal backup topology differs from runtime state"
            )
    return r[bool].ok(True)


def _journal_directory_topology(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    journal: m.Infra.MiseToolchainJournal,
    publications: tuple[m.Cli.AtomicFilePublication, ...] | None,
) -> p.Result[bool]:
    """Authenticate created-directory ownership, order, and preflight state."""
    selectors = journal.created_directories
    if len(set(selectors)) != len(selectors):
        return r[bool].fail("codegen journal directory paths are not unique")
    resolved_paths: list[Path] = []
    for selector in selectors:
        resolved = files.resolve_relative(
            layout.scope_root, selector, purpose="codegen destination directory"
        )
        if resolved.failure:
            return r[bool].from_failure(resolved)
        owner = files.project_for_path(layout, resolved.value)
        if owner.failure:
            return r[bool].from_failure(owner)
        if resolved.value == owner.value.root.absolute():
            return r[bool].fail("codegen journal cannot create a project root")
        resolved_paths.append(resolved.value)
    canonical = tuple(
        sorted(resolved_paths, key=lambda path: (len(path.parts), str(path)))
    )
    if tuple(resolved_paths) != canonical:
        return r[bool].fail("codegen journal directory order differs from topology")
    if publications is None:
        return r[bool].ok(True)
    targets = tuple(
        item.before.path
        for item in publications
        if item.replacement.content is not None
    )
    for directory in resolved_paths:
        if not directory.is_dir() or directory.is_symlink():
            return r[bool].fail(
                f"journaled codegen destination directory is invalid: {directory}"
            )
        if not any(directory in target.parents for target in targets):
            return r[bool].fail(
                f"journaled codegen directory owns no publication: {directory}"
            )
    if any(
        not target.parent.is_dir() or target.parent.is_symlink() for target in targets
    ):
        return r[bool].fail("codegen publication has an invalid destination parent")
    return r[bool].ok(True)


def sources(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    journal: m.Infra.MiseToolchainJournal | None = None,
    source_plans: tuple[m.Infra.CodegenFilePlan, ...] = (),
) -> p.Result[bool]:
    """Prove source topology, bytes, and modes still equal one snapshot."""
    for project in plan.projects:
        config_sources = u.Infra.snapshot_config_sources(project.layout.root)
        if config_sources.failure:
            return r[bool].from_failure(config_sources)
        expected = project.config.sources
        current = config_sources.value
        if current != expected:
            return r[bool].fail(f"Mise sources changed: {project.layout.selector}")
    expected_states = files.transaction_sources(plan, source_plans)
    if expected_states.failure:
        return r[bool].from_failure(expected_states)
    verified = u.Cli.atomic_verify_binary_file_states(expected_states.value)
    if verified.failure:
        return r[bool].fail(
            "codegen source verification failed: "
            f"{verified.error or 'physical state changed'}"
        )
    if journal is None:
        return r[bool].ok(True)
    topology = _journal_source_topology(plan.layout, journal.sources)
    if topology.failure:
        return topology
    if len(journal.sources) != len(expected_states.value):
        return r[bool].fail("codegen journal source count differs from snapshot")
    for expected, recorded in zip(expected_states.value, journal.sources, strict=True):
        selector = files.source_selector(plan.layout.scope_root, expected.path)
        if selector.failure:
            return r[bool].from_failure(selector)
        if (
            expected.content is None
            or expected.mode is None
            or recorded.path != selector.value
            or u.Cli.sha256_bytes(expected.content) != recorded.sha256
            or expected.mode != recorded.mode
        ):
            return r[bool].fail(f"Mise source differs from journal: {expected.path}")
    return r[bool].ok(True)


def destinations(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    publications: tuple[m.Cli.AtomicFilePublication, ...] = (),
) -> p.Result[bool]:
    """Prove every live destination still equals the locked preflight snapshot."""
    expected_by_path: dict[Path, m.Cli.AtomicFileState] = {}
    expected_states = (
        *(
            state
            for project in plan.projects
            for state in (
                project.config.before,
                project.artifacts.unix_launcher,
                project.artifacts.windows_launcher,
                project.artifacts.lock,
            )
        ),
        *(publication.before for publication in publications),
    )
    for expected in expected_states:
        prior = expected_by_path.get(expected.path)
        if prior is not None and prior != expected:
            return r[bool].fail(
                f"codegen destination has conflicting snapshots: {expected.path}"
            )
        expected_by_path[expected.path] = expected
    for expected in expected_by_path.values():
        observed = u.Cli.atomic_read_binary_file_state(expected.path, required=False)
        if observed.failure:
            return r[bool].from_failure(observed)
        if observed.value != expected:
            return r[bool].fail(
                f"codegen destination changed after preflight: {expected.path}"
            )
    return r[bool].ok(True)


def published(publications: tuple[m.Cli.AtomicFilePublication, ...]) -> p.Result[bool]:
    """Prove every live destination equals its staged replacement."""
    for publication in publications:
        expected = publication.replacement
        observed = u.Cli.atomic_read_binary_file_state(
            publication.before.path, required=expected.content is not None
        )
        if observed.failure:
            return r[bool].from_failure(observed)
        if (observed.value.content, observed.value.mode) != (
            expected.content,
            expected.mode,
        ):
            return r[bool].fail(
                f"published codegen destination differs: {publication.before.path}"
            )
    return r[bool].ok(True)


def live(
    owner: p.Infra.MiseArtifactsOwner,
    plan: m.Infra.MiseToolchainWorkspacePlan,
    publications: tuple[m.Cli.AtomicFilePublication, ...] | None = None,
) -> p.Result[bool]:
    """Exercise each real artifact consumer and compare exact bytes plus modes."""
    source_before = sources(plan)
    if source_before.failure:
        return source_before
    replacements = {
        publication.before.path: (
            publication.replacement.content,
            publication.replacement.mode,
        )
        for publication in publications or ()
    }
    artifact_before = _artifact_snapshot(plan, replacements)
    if artifact_before.failure:
        return r[bool].from_failure(artifact_before)
    for project in plan.projects:
        validated = owner.validate_artifacts(
            project.layout.root, config_sources=project.config.sources
        )
        if validated.failure:
            return r[bool].from_failure(validated)
    artifact_after = _artifact_snapshot(plan, replacements)
    if artifact_after.failure:
        return r[bool].from_failure(artifact_after)
    if artifact_after.value != artifact_before.value:
        return r[bool].fail("published Mise artifacts changed during validation")
    source_after = sources(plan)
    if source_after.failure:
        return source_after
    artifact_final = _artifact_snapshot(plan, replacements)
    if artifact_final.failure:
        return r[bool].from_failure(artifact_final)
    if artifact_final.value != artifact_after.value:
        return r[bool].fail("published Mise artifacts changed after validation")
    return r[bool].ok(True)


def _artifact_snapshot(
    plan: m.Infra.MiseToolchainWorkspacePlan,
    replacements: dict[Path, tuple[bytes | None, int | None]],
) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
    """Capture and validate one complete ordered artifact-state barrier."""
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
            current = u.Cli.atomic_read_binary_file_state(expected.path, required=True)
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


def _journal_source_topology(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    sources_to_validate: tuple[m.Infra.MiseToolchainJournalSource, ...],
) -> p.Result[bool]:
    seen: set[str] = set()
    for source in sources_to_validate:
        if source.path in seen:
            return r[bool].fail(f"duplicate Mise journal source: {source.path}")
        seen.add(source.path)
        resolved = files.resolve_source(layout.scope_root, source.path)
        if resolved.failure:
            return r[bool].from_failure(resolved)
        if resolved.value.is_relative_to(layout.state_root.absolute()):
            return r[bool].fail(
                f"Mise journal source enters transaction state: {source.path}"
            )
        if resolved.value.is_relative_to(layout.scope_root.absolute()):
            owner = files.project_for_path(layout, resolved.value)
            if owner.failure:
                return r[bool].from_failure(owner)
    observed_order = tuple(source.path for source in sources_to_validate)
    if observed_order != tuple(sorted(observed_order)):
        return r[bool].fail("codegen journal source order differs from workspace")
    return r[bool].ok(True)


__all__: list[str] = [
    "destinations",
    "journal_topology",
    "live",
    "published",
    "sources",
]
