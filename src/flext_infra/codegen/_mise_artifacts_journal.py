"""Durable journal for one extensible workspace generation transaction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Literal

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles as files,
    FlextInfraMiseArtifactsJournalRelocation,
    FlextInfraMiseArtifactsState as journal_state,
    FlextInfraMiseArtifactsVerification,
)


class FlextInfraMiseArtifactsJournal(FlextInfraMiseArtifactsJournalRelocation):
    """Durable transaction journal for Mise artifact generation."""

    @classmethod
    def observed_outcome(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        admission: m.Infra.CodegenPhaseOutcome,
        *,
        producer: m.Infra.CodegenPhaseAnalysis | m.Infra.CodegenSourceAuthority,
    ) -> p.Result[m.Infra.CodegenPhaseOutcome]:
        """Encode an admitted observation without materializing a transaction.

        Returns:
            The actual scope receipt carrying admitted outputs and producer inputs.

        """
        result_type = r[m.Infra.CodegenPhaseOutcome]
        analysis = admission.analysis
        if analysis is None or layout.transaction_id is None:
            return result_type.fail("observed publication lacks its admitted identity")
        if (
            not analysis.files
            or analysis.issues
            or analysis.exception is not None
            or any(
                u.Infra.codegen_file_requires_effect(file) for file in analysis.files
            )
        ):
            return result_type.fail(
                "observed publication requires an unchanged complete batch",
                exception=analysis.exception,
            )
        destinations = FlextInfraMiseArtifactsVerification.plans_current(analysis.files)
        if destinations.failure:
            return result_type.from_failure(destinations)
        sources = cls._merge_sources(
            (),
            tuple((analysis.phase, source) for source in analysis.inputs),
        )
        if sources.failure:
            return result_type.from_failure(sources)
        generator = cls._generator_source_records(producer)
        if generator.failure:
            return result_type.from_failure(generator)
        return result_type.ok(
            admission.model_copy(
                update={
                    "analysis": None,
                    "admitted_states": (),
                    "root": layout.scope_root,
                    "transaction_id": layout.transaction_id,
                    "completed": True,
                    "sources": sources.value,
                    "generator_sources": generator.value,
                    "generator_trees": analysis.generator_trees,
                    "generator_modules": analysis.generator_modules,
                    "generator_reference": analysis.generator_reference,
                    "scope_roots": admission.scope_roots
                    or tuple(dict.fromkeys(file.project for file in analysis.files)),
                },
            )
        )

    @classmethod
    def _generator_source_records(
        cls,
        producer: m.Infra.CodegenPhaseAnalysis | m.Infra.CodegenSourceAuthority | None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalSource]]:
        """Encode one producer's generator inputs with their module roles.

        A source inside one generator tree is a ``resource``; a Python source
        inside it is graded further by its importable module role. Anything
        outside every tree ships as a ``distribution`` input.

        Args:
            producer: Producer analysis whose inputs are encoded, or ``None``.

        Returns:
            The encoded generator sources, or the first encoding failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenJournalSource]]
        if producer is None:
            return result_type.ok(value=())
        if isinstance(producer, m.Infra.CodegenSourceAuthority):
            from flext_infra.codegen.codegen_preconditions import (
                FlextInfraCodegenPreconditions,
            )

            pinned = FlextInfraCodegenPreconditions.authority_inputs(producer)
            if pinned.failure:
                return result_type.from_failure(pinned)
            source_inputs = pinned.value
        else:
            source_inputs = producer.inputs
        generator_sources: list[m.Infra.CodegenJournalSource] = []
        for source in source_inputs:
            role: Literal[
                "layer0", "family", "consumer", "resource", "distribution"
            ] = "distribution"
            for tree in producer.generator_trees:
                if tree.root.path.name.endswith(
                    ".dist-info"
                ) or not source.path.is_relative_to(tree.root.path):
                    continue
                role = "resource"
                if source.path.suffix == c.Infra.EXT_PYTHON:
                    module = ".".join((
                        tree.root.path.name,
                        *source.path.relative_to(tree.root.path).with_suffix("").parts,
                    ))
                    role = u.Infra.import_module_role(module)
                break
            encoded = cls.source_record("generator", source)
            if encoded.failure:
                return result_type.from_failure(encoded)
            generator_sources.append(encoded.value.model_copy(update={"role": role}))
        return result_type.ok(value=tuple(generator_sources))

    @classmethod
    def begin(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan | m.Infra.CodegenFileSessionPlan,
        *,
        transaction_id: str,
        sources: t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]] = (),
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory] = (),
        producer: m.Infra.CodegenPhaseAnalysis
        | m.Infra.CodegenSourceAuthority
        | None = None,
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Build staging authority before any disposable transaction root exists.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionJournal]``.

        """
        reference = producer.generator_reference if producer is not None else None
        if reference is not None:
            metrics = {
                "bindings": len(reference.bindings),
                "binding_bytes": sum(
                    len(item.binding.encode(c.DEFAULT_ENCODING))
                    for item in reference.bindings
                ),
                "code_bytes": sum(
                    len((item.code or "").encode(c.DEFAULT_ENCODING))
                    for item in reference.bindings
                ),
                "operand_bytes": sum(
                    len(value.encode(c.DEFAULT_ENCODING))
                    for item in reference.bindings
                    for _name, value in item.operands
                ),
                "operational_bytes": sum(
                    len(value.encode(c.DEFAULT_ENCODING))
                    for item in reference.bindings
                    for _name, value in item.operational
                ),
            }
            u.Cli.info(
                "native authority "
                + " ".join(f"{name}={size}" for name, size in metrics.items())
            )
        physical_scope = files.physical_directory_identity(plan.layout.scope_root)
        if physical_scope.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(physical_scope)
        projects: list[m.Infra.CodegenJournalProject] = []
        for project in plan.layout.projects:
            physical_project = files.physical_directory_identity(project.root)
            if physical_project.failure:
                return r[m.Infra.CodegenTransactionJournal].from_failure(
                    physical_project,
                )
            projects.append(
                m.Infra.CodegenJournalProject(
                    selector=project.selector,
                    device=physical_project.value[0],
                    inode=physical_project.value[1],
                ),
            )
        encoded_sources = cls._merge_sources((), sources)
        if encoded_sources.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(encoded_sources)
        generator_sources = cls._generator_source_records(producer)
        if generator_sources.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(
                generator_sources,
            )
        generator_trees = producer.generator_trees if producer is not None else ()
        generator_modules = producer.generator_modules if producer is not None else ()
        return r[m.Infra.CodegenTransactionJournal].ok(
            m.Infra.CodegenTransactionJournal(
                version=9,
                transaction_id=transaction_id,
                scope_device=physical_scope.value[0],
                scope_inode=physical_scope.value[1],
                state="staging",
                projects=tuple(projects),
                file_participants=plan.layout.file_participants,
                sources=encoded_sources.value,
                generator_sources=generator_sources.value,
                generator_trees=generator_trees,
                generator_modules=generator_modules,
                generator_reference=(
                    producer.generator_reference if producer is not None else None
                ),
                directories=directories,
                entries=(),
            ),
        )

    @classmethod
    def append_prepared(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan | m.Infra.CodegenFileSessionPlan,
        journal: m.Infra.CodegenTransactionJournal,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        sources: t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]] = (),
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Back up one complete phase and return its extended prepared authority.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionJournal]``.

        """
        if journal.state not in {"staging", "prepared"}:
            return r[m.Infra.CodegenTransactionJournal].fail(
                "only staging or prepared codegen journal accepts a phase",
            )
        topology = cls._validate_physical_topology(plan, journal)
        if topology.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(topology)
        prepared_entries = cls._prepared_phase_entries(plan, journal, publications)
        if prepared_entries.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(prepared_entries)
        entries = list(journal.entries)
        entries.extend(prepared_entries.value)
        encoded_sources = cls._merge_sources(journal.sources, sources)
        if encoded_sources.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(encoded_sources)
        candidate = journal.model_copy(
            update={
                "state": "prepared",
                "sources": encoded_sources.value,
                "entries": tuple(entries),
            }
        )
        validated = r[m.Infra.CodegenTransactionJournal].create_from_callable(
            lambda: m.Infra.CodegenTransactionJournal.model_validate_json(
                candidate.model_dump_json()
            )
        )
        if validated.failure:
            return r[m.Infra.CodegenTransactionJournal].fail_op(
                "validate prepared codegen journal",
                validated.error,
            )
        return r[m.Infra.CodegenTransactionJournal].ok(validated.value)

    @classmethod
    def _prepared_phase_entries(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan | m.Infra.CodegenFileSessionPlan,
        journal: m.Infra.CodegenTransactionJournal,
        publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalEntry]]:
        """Build one journal entry per staged publication, rejecting collisions.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenJournalEntry]]
            ``.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenJournalEntry]]
        existing_paths = {entry.path for entry in journal.entries}
        entries: list[m.Infra.CodegenJournalEntry] = []
        for publication in publications:
            target = files.transaction_relative(plan.layout, publication.before.path)
            if target.failure:
                return result_type.from_failure(target)
            if target.value in existing_paths:
                return result_type.fail(
                    f"multiple generation phases own one destination: {target.value}",
                )
            entry = cls._journal_entry(
                plan,
                publication,
            )
            if entry.failure:
                return result_type.from_failure(entry)
            entries.append(entry.value)
            existing_paths.add(entry.value.path)
        return result_type.ok(tuple(entries))

    @classmethod
    def append_directories(
        cls,
        journal: m.Infra.CodegenTransactionJournal,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Extend durable directory authority before materializing any new path.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionJournal]``.

        """
        if journal.state not in {"staging", "prepared"}:
            return r[m.Infra.CodegenTransactionJournal].fail(
                "only staging or prepared codegen journal accepts directories",
            )
        existing = {directory.path for directory in journal.directories}
        duplicate = next(
            (directory.path for directory in directories if directory.path in existing),
            None,
        )
        if duplicate is not None:
            return r[m.Infra.CodegenTransactionJournal].fail(
                f"generation directory already has an owner: {duplicate}",
            )
        extended = journal.model_copy(
            update={"directories": (*journal.directories, *directories)},
        )
        return r[m.Infra.CodegenTransactionJournal].ok(extended)

    @classmethod
    def record_transaction_manifests(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        created: t.VariadicTuple[
            m.Cli.AtomicFileState | m.Cli.AtomicDirectoryState
        ] = (),
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Validate physical manifests and retain them in the transaction journal.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionJournal]``.

        """
        inventory_for_parent = cache(u.Cli.atomic_inventory_physical_tree)
        finalized: list[m.Infra.CodegenStagingIntent] = []
        for intent in journal.staging_intents:
            observed = files.read_state(intent.before.path, required=False)
            if observed.failure:
                return r[m.Infra.CodegenTransactionJournal].from_failure(observed)
            current = observed.value
            if current.content is None:
                finalized.append(intent)
                continue
            if (
                current.parent_device != intent.before.parent_device
                or current.parent_inode != intent.before.parent_inode
                or current.mode != intent.mode
                or files.digest(current.content) != intent.sha256
            ):
                return r[m.Infra.CodegenTransactionJournal].fail(
                    f"staging bytes differ from durable intention: {current.path}",
                )
            inventory = inventory_for_parent(current.path.parent)
            if inventory.failure:
                return r[m.Infra.CodegenTransactionJournal].from_failure(inventory)
            receipt = next(
                (
                    entry
                    for entry in inventory.value.entries
                    if entry.path == current.path
                ),
                None,
            )
            if receipt is None or (
                intent.created is not None and receipt != intent.created
            ):
                return r[m.Infra.CodegenTransactionJournal].fail(
                    f"staging physical identity changed: {current.path}",
                )
            finalized.append(
                intent.model_copy(update={"created": receipt}),
            )
        journal = journal.model_copy(update={"staging_intents": tuple(finalized)})
        registered = FlextInfraMiseArtifactsVerification.register_transaction_manifests(
            layout,
            journal,
            created=created,
        )
        if registered.failure:
            return r[m.Infra.CodegenTransactionJournal].from_failure(registered)
        return cls.record_directories(journal, registered.value)

    @classmethod
    def record_directories(
        cls,
        journal: m.Infra.CodegenTransactionJournal,
        directories: t.VariadicTuple[m.Infra.CodegenJournalDirectory],
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Advance physical directory evidence without changing its durable intent.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionJournal]``.

        """
        result_type = r[m.Infra.CodegenTransactionJournal]
        if tuple(directory.path for directory in directories) != tuple(
            directory.path for directory in journal.directories
        ):
            return result_type.fail("recorded directory topology differs from journal")
        for previous, current in zip(journal.directories, directories, strict=True):
            compared = cls._validated_recorded_directory(previous, current)
            if compared.failure:
                return result_type.from_failure(compared)
        return result_type.ok(journal.model_copy(update={"directories": directories}))

    @staticmethod
    def _validated_recorded_directory(
        previous: m.Infra.CodegenJournalDirectory,
        current: m.Infra.CodegenJournalDirectory,
    ) -> p.Result[bool]:
        """Prove one recorded directory kept its durable intent and evidence.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        stable_previous = previous.model_dump(
            exclude={"before", "created", "manifest"},
        )
        stable_current = current.model_dump(
            exclude={"before", "created", "manifest"},
        )
        if stable_current != stable_previous:
            return result_type.fail(
                f"recorded directory intent changed: {previous.path}",
            )
        if previous.before is not None and current.before != previous.before:
            return result_type.fail(
                f"recorded directory parent binding changed: {previous.path}",
            )
        if previous.before is None and current.before is None and current.created:
            return result_type.fail(
                f"created directory lacks parent binding: {previous.path}",
            )
        if previous.created is not None and current.created != previous.created:
            return result_type.fail(
                f"recorded directory physical identity changed: {previous.path}",
            )
        if previous.manifest is not None and current.manifest is None:
            return result_type.fail(
                f"recorded directory manifest disappeared: {previous.path}",
            )
        return result_type.ok(value=True)

    @classmethod
    def commit(
        cls,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[m.Infra.CodegenTransactionJournal]:
        """Validate the sole prepared-to-committed transition.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionJournal]``.

        """
        if journal.state != "prepared":
            return r[m.Infra.CodegenTransactionJournal].fail(
                "only a prepared codegen journal can be committed",
            )
        return r[m.Infra.CodegenTransactionJournal].ok(
            journal.model_copy(update={"state": "committed"}),
        )

    @classmethod
    def write(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        expected: m.Cli.AtomicFileState,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Create or transition the common journal with full-state CAS.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        content = journal.model_dump_json().encode(c.DEFAULT_ENCODING)
        u.Cli.info(
            f"codegen journal state={journal.state} bytes={len(content)} "
            f"entries={len(journal.entries)} intents={len(journal.staging_intents)}"
        )
        if expected.path != layout.journal_path:
            return r[m.Cli.AtomicFileState].fail(
                "codegen journal expected state belongs to another path",
            )
        written = u.Cli.atomic_write_binary_file_guarded(
            expected,
            content,
            permission_mode=c.Infra.JOURNAL_MODE,
        )
        if written.failure:
            return r[m.Cli.AtomicFileState].from_failure(written)
        observed = journal_state.journal_state(layout)
        if observed.failure:
            return r[m.Cli.AtomicFileState].from_failure(observed)
        observed_snapshot = journal_state.journal_snapshot(observed.value)
        if observed_snapshot is None:
            return r[m.Cli.AtomicFileState].fail(
                "published codegen journal parent disappeared",
            )
        if (
            observed_snapshot.content != content
            or observed_snapshot.mode != c.Infra.JOURNAL_MODE
        ):
            return r[m.Cli.AtomicFileState].fail(
                "published codegen journal differs from exact bytes or mode",
            )
        return r[m.Cli.AtomicFileState].ok(observed_snapshot)

    @classmethod
    def read(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Parse the typed v8 journal without deriving a second filesystem path.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        snapshot = journal_state.journal_state(layout)
        result_type = r[tuple[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]
        if snapshot.failure:
            return result_type.from_failure(snapshot)
        journal_snapshot = journal_state.journal_snapshot(snapshot.value)
        if journal_snapshot is None or journal_snapshot.content is None:
            return result_type.fail("codegen transaction journal is absent")
        if journal_snapshot.mode != c.Infra.JOURNAL_MODE:
            return result_type.fail("codegen transaction journal mode is not 0600")
        u.Cli.info(f"codegen journal read bytes={len(journal_snapshot.content)}")
        validated = m.Infra.CodegenTransactionJournal.model_validate_json(
            journal_snapshot.content,
        )
        relocated = cls._relocate_journal(layout, validated)
        if relocated.failure:
            return result_type.from_failure(relocated)
        return result_type.ok((relocated.value, journal_snapshot))

    @classmethod
    def cleanup(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_snapshot: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Retain journal authority until all journal-authorized cleanup completes.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        directories = journal_state.cleanup_journaled_directories(
            layout,
            journal,
            include_generated=False,
        )
        if directories.failure:
            return directories
        removed = files.delete_state(journal_snapshot)
        if removed.failure:
            return r[bool].from_failure(removed)
        return r[bool].ok(value=True)

    @classmethod
    def _merge_sources(
        cls,
        existing: t.VariadicTuple[m.Infra.CodegenJournalSource],
        sources: t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenJournalSource]]:
        result_type = r[tuple[m.Infra.CodegenJournalSource, ...]]
        by_key = {(source.phase, source.path): source for source in existing}
        order = [(source.phase, source.path) for source in existing]
        for phase, source in sources:
            key = (phase, source.path)
            previous = by_key.get(key)
            encoded = cls.source_record(phase, source, previous)
            if encoded.failure:
                return result_type.from_failure(encoded)
            if previous is not None and previous != encoded.value:
                return result_type.fail(
                    f"generation source changed between phases: {encoded.value.path}",
                )
            if previous is None:
                by_key[key] = encoded.value
                order.append(key)
        return result_type.ok(tuple(by_key[key] for key in order))

    @staticmethod
    def _entry_project(
        plan: m.Infra.MiseToolchainWorkspacePlan | m.Infra.CodegenFileSessionPlan,
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[
        t.Pair[
            m.Infra.MiseToolchainProjectLayout | m.Infra.CodegenFileParticipant,
            str,
        ]
    ]:
        """Resolve the transaction participant and relative selector of a target.

        Returns:
            The registered Mise or file participant and relative selector.

        """
        result_type = r[
            t.Pair[
                m.Infra.MiseToolchainProjectLayout | m.Infra.CodegenFileParticipant,
                str,
            ]
        ]
        before = publication.before
        if before.parent_device is None or before.parent_inode is None:
            return result_type.fail(
                f"generation destination parent identity is incomplete: {before.path}",
            )
        project = next(
            (
                item
                for item in files.transaction_participants(plan.layout)
                if item.root == publication.project
            ),
            None,
        )
        if project is None or project.transaction_root is None:
            return result_type.fail(
                f"generation publication has no transaction participant: {before.path}",
            )
        selector = files.transaction_relative(plan.layout, before.path)
        if selector.failure:
            return result_type.from_failure(
                selector,
            )
        return result_type.ok(
            (project, selector.value),
        )

    @classmethod
    def _desired_staging_selector(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        replacement: m.Cli.AtomicFileState,
        destination: Path,
    ) -> p.Result[str]:
        """Prove a replacement's complete identity before encoding its path.

        Returns:
            The staging selector for an authenticated replacement.

        """
        incomplete = any((
            replacement.content is None,
            replacement.mode is None,
            replacement.device is None,
            replacement.inode is None,
            replacement.link_count != 1,
        ))
        if incomplete:
            return r[str].fail(
                f"generation staged identity is incomplete: {destination}",
            )
        relative_staging = files.transaction_relative(layout, replacement.path)
        if relative_staging.failure:
            return r[str].from_failure(relative_staging)
        return r[str].ok(relative_staging.value)

    @classmethod
    def _journal_entry(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan | m.Infra.CodegenFileSessionPlan,
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[m.Infra.CodegenJournalEntry]:
        before = publication.before
        if before.parent_device is None or before.parent_inode is None:
            return r[m.Infra.CodegenJournalEntry].fail(
                f"generation destination parent identity is incomplete: {before.path}",
            )
        located = cls._entry_project(plan, publication)
        if located.failure:
            return r[m.Infra.CodegenJournalEntry].from_failure(located)
        project, selector = located.value
        original_sha = (
            files.digest(before.content) if before.content is not None else None
        )
        replacement = publication.replacement
        desired_exists = replacement is not None
        desired_staging: str | None = None
        if replacement is not None:
            staging = cls._desired_staging_selector(
                plan.layout,
                replacement,
                before.path,
            )
            if staging.failure:
                return r[m.Infra.CodegenJournalEntry].from_failure(staging)
            desired_staging = staging.value
        return r[m.Infra.CodegenJournalEntry].ok(
            m.Infra.CodegenJournalEntry(
                dependency_group=publication.dependency_group,
                original_staging=(
                    files.transaction_relative(
                        plan.layout, publication.original_replacement.path
                    ).unwrap()
                    if publication.original_replacement is not None
                    else None
                ),
                original_content_hex=(
                    before.content.hex()
                    if publication.dependency_group is not None
                    and before.content is not None
                    else None
                ),
                phase=publication.phase,
                project=project.selector,
                path=selector,
                desired_staging=desired_staging,
                source_paths=tuple(source.path for source in publication.source_states),
                tracking=publication.tracking,
                index_before=publication.index_before,
                tracking_dependencies=publication.tracking_dependencies,
                original_exists=before.content is not None,
                original_parent_device=before.parent_device,
                original_parent_inode=before.parent_inode,
                original_sha256=original_sha,
                original_mode=before.mode,
                original_device=before.device,
                original_inode=before.inode,
                original_link_count=1 if before.content is not None else None,
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
                desired_link_count=1 if replacement is not None else None,
                desired_file_attributes=(
                    None if replacement is None else replacement.file_attributes
                ),
                desired_reparse_tag=(
                    None if replacement is None else replacement.reparse_tag
                ),
            ),
        )

    @classmethod
    def _validate_physical_topology(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan | m.Infra.CodegenFileSessionPlan,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[bool]:
        """Use the same capability and physical topology proof as recovery.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return FlextInfraMiseArtifactsVerification.journal_topology(
            plan.layout,
            journal,
        )


__all__: list[str] = ["FlextInfraMiseArtifactsJournal"]
