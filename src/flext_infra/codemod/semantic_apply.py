"""Guarded semantic phase for detection-only ``make mod`` findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import keyword
import os
import re
from collections.abc import Callable, Generator, Mapping, MutableMapping, Sequence
from contextlib import AbstractContextManager, ExitStack, closing, contextmanager
from functools import partial
from pathlib import Path

from flext_cli import cli

from flext_infra import c, config, m, p, r, t, u
from flext_infra._utilities._rope import FlextInfraRopeProject
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod import FlextInfraCodemodRename
from flext_infra.codemod._rename import FlextInfraCodemodRenameSymbols
from flext_infra.transformers._semantic import FlextInfraTransformersSemanticPublication
from flext_infra.workspace import FlextInfraRopeWorkspace


class FlextInfraCodemodSemanticApply(
    FlextInfraCodemodRename,
):
    """Plan semantic cutovers, preflight the batch, then publish guarded files."""

    @classmethod
    def publish_rename_plan(
        cls,
        request: p.Infra.SemanticRenamePlanCommand,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[p.Infra.SemanticRenamePlan]:
        """Plan, authenticate and atomically publish an inventory-derived artifact.

        Returns:
            The published plan, or the original containment, planning or write failure.

        """
        root = request.repository_root.resolve()
        target = (root / request.output).resolve()
        if not target.is_relative_to(root):
            return r[p.Infra.SemanticRenamePlan].fail(
                "rename plan output escapes workspace"
            )
        observed = u.Cli.atomic_read_binary_file_state(root / request.output)
        if observed.failure:
            return r[p.Infra.SemanticRenamePlan].from_failure(observed)
        selections = m.Infra.SemanticRenameSelections.model_validate_json(
            request.decisions
        )
        members = tuple(
            dict.fromkeys(
                project
                for scope in (root, *selections.consumer_roots)
                for project in u.Infra.import_project_roots(scope)
            )
        )
        with (
            workspace_factory(root, None) as workspace,
            u.Infra.workspace_snapshot(
                Path(os.path.commonpath(members)), members
            ) as snapshot,
        ):
            planned = cls.build_rename_plan(
                root, workspace, selections, snapshot=snapshot
            )
        if planned.failure:
            return r[p.Infra.SemanticRenamePlan].from_failure(planned)
        return cls._publish_source_plan(
            root, target, planned.value, before=observed.value
        ).map(lambda _written: planned.value)

    @classmethod
    def _publish_source_plan(
        cls,
        root: Path,
        target: Path,
        planned: p.Infra.SemanticSourcePlan,
        *,
        before: p.Cli.AtomicFileState,
    ) -> p.Result[tuple[Path, ...]]:
        """Publish a captured source artifact through the existing guarded owner.

        The caller observes the destination before capturing its source epoch.
        Explicit rename artifacts retain their concrete model and validation.

        Returns:
            Published paths, or the original authenticity or publication failure.

        """
        outcome = r[tuple[Path, ...]]
        root = root.resolve()
        target = u.Infra.contained_write_targets(root, (target,))[0]
        content = cls._validated_source_plan_content(before, planned, target, root)
        if content.failure:
            return outcome.from_failure(content)
        lock = u.Infra.mutation_lock_path(root)
        if lock.failure:
            return outcome.from_failure(lock)
        return u.Cli.publish_file_changes(
            (
                m.Cli.FileChange(
                    path=target,
                    before=before,
                    desired_content=f"{content.value}\n".encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode
                    if before.content is not None
                    else config.Infra.codegen.modes.file_default,
                ),
            ),
            lock_path=lock.value,
        )

    @staticmethod
    def _validated_source_plan_content(
        before: p.Cli.AtomicFileState,
        planned: p.Infra.SemanticSourcePlan,
        target: Path,
        root: Path,
    ) -> p.Result[str]:
        """Reject input aliases, foreign artifacts and non-round-trip content.

        Returns:
            The exact serialized artifact, or its first authentication failure.

        """
        if any(
            state.path == target
            or (
                before.inode is not None
                and (state.device, state.inode) == (before.device, before.inode)
            )
            for state in planned.candidate.inputs
        ):
            return r[str].fail("source plan output aliases a governed candidate input")
        plan_type = type(planned)
        if before.content is not None:
            previous = plan_type.model_validate_json(before.content)
            if (previous.candidate.workspaces or (previous.candidate.workspace,))[
                0
            ] != u.Infra.import_project_roots(root)[0].resolve():
                return r[str].fail("source plan output belongs to another workspace")
        content = planned.model_dump_json(indent=2, round_trip=True)
        if (
            plan_type.model_validate_json(content).model_dump_json(
                indent=2, round_trip=True
            )
            != content
        ):
            return r[str].fail("source artifact did not round-trip exactly")
        return r[str].ok(value=content)

    @classmethod
    def build_rename_plan(
        cls,
        root: Path,
        workspace: p.Infra.RopeWorkspaceDsl,
        selections: p.Infra.SemanticRenameSelections,
        *,
        source_plan: p.Infra.SemanticSourcePlan | None = None,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[p.Infra.SemanticRenamePlan]:
        """Produce exact native edits and closure from explicit domain selections.

        Returns:
            A reversible authenticated artifact, without changing live sources.

        """
        if not selections.decisions:
            return r[p.Infra.SemanticRenamePlan].fail(
                "semantic rename requires an explicit naming decision"
            )
        elected = cls._source_scopes(root, selections.consumer_roots)
        if elected.failure:
            return r[p.Infra.SemanticRenamePlan].from_failure(elected)
        scopes = elected.value
        if source_plan is not None:
            if (
                source_plan.candidate.workspaces or (source_plan.candidate.workspace,)
            ) != scopes:
                return r[p.Infra.SemanticRenamePlan].fail(
                    "semantic rename source receipt belongs to another scope"
                )
            # A persisted plan is rebuilt only over the bytes it observed.
            current = u.Cli.atomic_verify_binary_file_states(
                source_plan.candidate.inputs
            )
            if current.failure:
                return r[p.Infra.SemanticRenamePlan].from_failure(current)
        return cls._build_native_rename_plan(workspace, selections, scopes, snapshot)

    @classmethod
    def build_source_plan(
        cls,
        root: Path,
        consumer_roots: tuple[Path, ...] = (),
        *,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Capture a native source campaign without creating a rename artifact.

        Returns:
            The complete authenticated source closure, without live effects.

        """
        return cls._source_scopes(root, consumer_roots).flat_map(
            lambda scopes: cls._source_closure(scopes, snapshot).map(
                lambda candidate: m.Infra.SemanticSourcePlan(
                    candidate=candidate,
                    consumer_roots=scopes[1:],
                )
            )
        )

    @classmethod
    def _build_rewire_plan(
        cls,
        root: Path,
        source_plan: p.Infra.SemanticSourcePlan,
        intents: Sequence[p.Infra.SemanticRewireIntent],
        *,
        pre_move_sources: Mapping[Path, str],
    ) -> p.Result[p.Infra.SemanticRenamePlan]:
        """Retain census identities with the existing authenticated source receipt.

        Supplier bytes stay in the candidate's original observations. Portable
        intent carries only relative ownership and native binding identities;
        external invocations derive their own edits instead of replaying this
        producer's paths or offsets.

        Returns:
            The existing rename artifact with its portable relocation intent.

        """
        if not intents:
            return r[p.Infra.SemanticRenamePlan].fail(
                "native census has no relocation intent"
            )
        supplier = root.resolve().relative_to(source_plan.candidate.workspace)
        if any(intent.supplier_root != supplier for intent in intents):
            return r[p.Infra.SemanticRenamePlan].fail(
                "native relocation supplier differs from its captured owner"
            )
        observed = {state.path: state.content for state in source_plan.candidate.inputs}
        overlays = {
            path.relative_to(source_plan.candidate.workspace): content
            for path, content in pre_move_sources.items()
            if observed.get(path) != content.encode(c.DEFAULT_ENCODING)
        }
        return r[p.Infra.SemanticRenamePlan].ok(
            m.Infra.SemanticRenamePlan(
                candidate=source_plan.candidate,
                consumer_roots=source_plan.consumer_roots,
                decisions=(),
                rewires=tuple(intents),
                rewire_sources=overlays,
                edits=cls._rename_edits(
                    u.Infra.candidate_python_sources(
                        source_plan.candidate, source_plan.candidate.inputs
                    ),
                    source_plan.candidate.updates,
                ),
            )
        )

    @classmethod
    def rewire_artifact_file_plans(
        cls,
        root: Path,
        source_plan: p.Infra.SemanticSourcePlan,
        intents: Sequence[p.Infra.SemanticRewireIntent],
        *,
        pre_move_sources: Mapping[Path, str],
        directory: Path,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan one immutable native artifact in the configured versioned directory.

        Returns:
            A file plan belonging to the same coherent source publication batch.

        """
        outcome = r[tuple[p.Infra.CodegenFilePlan, ...]]
        if not intents:
            return outcome.ok(())
        built = cls._build_rewire_plan(
            root,
            source_plan,
            intents,
            pre_move_sources=pre_move_sources,
        )
        if built.failure:
            return outcome.from_failure(built)
        return cls._plan_rewire_artifact(root, built.value, directory=directory)

    @classmethod
    def _plan_rewire_artifact(
        cls,
        root: Path,
        plan: p.Infra.SemanticRenamePlan,
        *,
        directory: Path,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan the immutable artifact for one authenticated rewire.

        Returns:
            The file plan, the unchanged outcome, or the first refusal.

        """
        outcome = r[tuple[p.Infra.CodegenFilePlan, ...]]
        root = root.resolve()
        fingerprint = u.Cli.sha256_content(
            plan.model_dump_json(indent=2, round_trip=True)
        )
        target = u.Infra.contained_write_targets(
            root, (root / directory / f"{fingerprint}.json",)
        )[0]
        before = u.Cli.atomic_read_binary_file_state(target)
        if before.failure:
            return outcome.from_failure(before)
        serialized = cls._validated_source_plan_content(
            before.value, plan, target, root
        )
        if serialized.failure:
            return outcome.from_failure(serialized)
        content = f"{serialized.value}\n".encode(c.DEFAULT_ENCODING)
        if before.value.content == content:
            return outcome.ok(())
        if before.value.content is not None:
            return outcome.fail("immutable native rewire artifact content conflicts")
        return outcome.ok((
            m.Infra.CodegenFilePlan(
                project=root,
                path=target,
                before=before.value,
                desired_content=content,
                desired_mode=config.Infra.codegen.modes.file_default,
            ),
        ))

    @staticmethod
    def _rewire_import_root(path: Path, module: str) -> Path:
        """Resolve a native module's import root without assuming a src layout.

        Returns:
            The source root serving the qualified module.

        Raises:
            ValueError: The module identity disagrees with its observed resource.

        """
        suffix = Path(*module.split("."))
        suffix = (
            suffix / c.Infra.INIT_PY
            if path.name == c.Infra.INIT_PY
            else suffix.with_suffix(c.Infra.EXT_PYTHON)
        )
        if path.parts[-len(suffix.parts) :] != suffix.parts:
            msg = f"supplier module identity disagrees with source path: {module}"
            raise ValueError(msg)
        return path.parents[len(suffix.parts) - 1]

    @classmethod
    def _rewire_supplier_sources(
        cls,
        artifact: p.Infra.SemanticRenamePlan,
        project: p.Infra.RopeProject,
    ) -> tuple[dict[Path, Path], dict[Path, str | None]]:
        """Rebase recorded supplier sources onto the current native installation.

        Returns:
            Recorded/current import roots and the original pre-move source view.

        Raises:
            ValueError: A destination is absent or supplier provenance conflicts.

        """
        roots: dict[Path, Path] = {}
        for intent in artifact.rewires:
            if (
                intent.source_scope.rsplit(".", 1)[-1]
                != intent.destination_scope.rsplit(".", 1)[-1]
            ):
                msg = (
                    "binding relocation preserves its name; naming is a preceding "
                    "native phase"
                )
                raise ValueError(msg)
            destination = project.find_module(intent.destination_module)
            if destination is None or destination.is_folder():
                msg = (
                    f"rewire supplier destination is absent: "
                    f"{intent.destination_module}"
                )
                raise ValueError(msg)
            if intent.kind != "module":
                u.Infra.qualified_name(
                    project,
                    intent.destination_scope,
                    module_name=intent.destination_module,
                )
            recorded = cls._rewire_import_root(
                artifact.candidate.workspace
                / intent.supplier_root
                / intent.destination_path,
                intent.destination_module,
            )
            current = cls._rewire_import_root(
                Path(destination.real_path), intent.destination_module
            )
            if roots.setdefault(recorded, current) != current:
                msg = (
                    "portable supplier source root resolves to conflicting "
                    "installations"
                )
                raise ValueError(msg)
        sources: dict[Path, str | None] = {}
        retained = {
            state.path: None
            if state.content is None
            else state.content.decode(c.DEFAULT_ENCODING)
            for state in artifact.candidate.inputs
            if state.path.suffix == c.Infra.EXT_PYTHON
        }
        retained.update({
            artifact.candidate.workspace / path: source
            for path, source in artifact.rewire_sources.items()
        })
        for original, source in retained.items():
            for recorded, current in roots.items():
                if original.is_relative_to(recorded):
                    sources[current / original.relative_to(recorded)] = source
        return roots, sources

    @staticmethod
    def _rewire_identifier_offset(
        project: p.Infra.RopeProject,
        module: str,
        scope: str,
        sources: Mapping[Path, str | None],
    ) -> int:
        """Read a binding's identifier position from its authenticated native source.

        Returns:
            The native declaration identifier offset in the current source view.

        Raises:
            ValueError: The identity lacks a source declaration or identifier.

        """
        binding = u.Infra.qualified_name(project, scope, module_name=module)
        source_module, line = binding.get_definition_location()
        resource = None if source_module is None else source_module.get_resource()
        if resource is None or line is None:
            msg = f"portable rewire binding has no native source: {module}.{scope}"
            raise ValueError(msg)
        source = sources[Path(resource.real_path)]
        if source is None:
            msg = f"portable rewire source is absent: {module}.{scope}"
            raise ValueError(msg)
        offset = u.Infra.find_identifier_offset_in_lines(
            source.splitlines(keepends=True),
            line=line,
            symbol=scope.rsplit(".", 1)[-1],
            pyname=binding,
        )
        if offset is None:
            msg = f"portable rewire binding has no native identifier: {module}.{scope}"
            raise ValueError(msg)
        return offset

    @classmethod
    def _rebuild_rewire_plan(
        cls,
        root: Path,
        artifact: p.Infra.SemanticRenamePlan,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Derive this consumer's native edits using the supplier's saved source view.

        Supplier overlays exist only in Rope. Native transfer effects on supplier
        files are discarded; the final candidate validates consumer edits against
        the actual installed destination, with fresh physical observations.

        Returns:
            This checkout's authenticated consumer candidate, never saved edits.

        """
        root = root.resolve()
        roots, sources = cls._rewire_supplier_sources(artifact, workspace.rope_project)
        originals = {
            state.path: state
            for project in u.Infra.import_project_roots(root)
            for path in u.Infra.ast_grep_scan_targets(project)
            for state in (
                u.Cli.atomic_read_binary_file_state(
                    project / path, required=True
                ).unwrap(),
            )
        }
        consumers = tuple(
            path for path in originals if path.suffix == c.Infra.EXT_PYTHON
        )
        sources.update({
            path: content.decode(c.DEFAULT_ENCODING)
            for path in consumers
            if (content := originals[path].content) is not None
        })
        for path in sources:
            if path not in originals:
                originals[path] = u.Cli.atomic_read_binary_file_state(path).unwrap()
        source_folders = tuple(
            dict.fromkeys((
                *(
                    Path(folder.real_path)
                    for folder in workspace.rope_project.get_source_folders()
                ),
                *roots.values(),
            ))
        )
        view_root = Path(os.path.commonpath((root, *source_folders)))
        with u.Infra.open_project(
            view_root,
            project_roots=u.Infra.import_project_roots(root),
            fscommands=FlextInfraRopeProject.OverlayFiles(()),
        ) as live:
            python_folders = workspace.rope_project.get_python_path_folders()
            election = cls._planning_election(
                live,
                tuple(
                    path.relative_to(view_root).as_posix() for path in source_folders
                ),
                tuple(
                    dict.fromkeys((
                        *(str(path) for path in source_folders),
                        *(folder.real_path for folder in python_folders),
                    ))
                ),
            )

            def planned(
                current_sources: Mapping[Path, str | None],
                selected: Sequence[Path] | None = None,
            ) -> tuple[
                tuple[p.Infra.CodegenFilePlan, ...],
                AbstractContextManager[p.Infra.RopeProject],
            ]:
                scope = set(current_sources) if selected is None else set(selected)
                plans = tuple(
                    m.Infra.CodegenFilePlan(
                        project=view_root,
                        path=path,
                        before=originals[path],
                        desired_content=None
                        if source is None
                        else source.encode(c.DEFAULT_ENCODING),
                        desired_mode=None
                        if source is None
                        else (
                            originals[path].mode
                            or config.Infra.codegen.modes.file_default
                        ),
                    )
                    for path, source in current_sources.items()
                    if path in scope
                )
                return plans, closing(
                    u.Infra.planned_project(
                        live,
                        election=election,
                        declared_files=plans,
                        observations=tuple(originals.values()),
                    )
                )

            cls._replay_native_rewires(planned, artifact, roots, sources, originals)
        updates = {
            path: source
            for path in consumers
            if (source := sources[path]) is not None
            and source.encode(c.DEFAULT_ENCODING) != originals[path].content
        }
        return FlextInfraStagedPackage.plan_sources(
            root,
            updates,
            options=m.Infra.StageSourceOptions.model_validate({
                "inputs": tuple(originals.values())
            }),
        ).map(lambda candidate: m.Infra.SemanticSourcePlan(candidate=candidate))

    @classmethod
    def _current_rewire_sites(
        cls,
        opened: AbstractContextManager[p.Infra.RopeProject],
        intent: p.Infra.SemanticRewireIntent,
        consumers: tuple[Path, ...],
    ) -> frozenset[tuple[Path, int]]:
        """Prove current-destination sites before restoring old supplier declarations.

        Returns:
            Exact native occurrence sites in the current consumer source epoch.

        """
        with opened as project:
            binding = u.Infra.qualified_name(
                project,
                intent.destination_scope or intent.destination_module,
                module_name=None
                if intent.kind == "module"
                else intent.destination_module,
            )
            finder = u.Infra.create_occurrence_finder(
                project,
                (intent.destination_scope or intent.destination_module).rsplit(".", 1)[
                    -1
                ],
                binding,
                imports=False,
                in_hierarchy=False,
            )
            return frozenset(
                (path, occurrence.offset)
                for path in consumers
                for occurrence in finder.find_occurrences(
                    resource=u.Infra.file_resource_at(project, path)
                )
            )

    @classmethod
    def _module_rewire_plans(
        cls,
        project: p.Infra.RopeProject,
        endpoints: tuple[Path, Path],
        sources: Mapping[Path, str | None],
        originals: Mapping[Path, p.Cli.AtomicFileState],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        """Return the native module move, preserving its authenticated source view.

        Returns:
            The native module move plans.

        """
        origin, target = endpoints
        return u.Infra.plan_module_move(
            project,
            origin,
            destination_file=target,
            inputs=u.Infra.NativeSourceView(
                {
                    path: source
                    for path, source in sources.items()
                    if source is not None
                },
                tuple(originals.values()),
            ),
        ).unwrap()

    @classmethod
    def _binding_rewire_changes(
        cls,
        project: p.Infra.RopeProject,
        intent: p.Infra.SemanticRewireIntent,
        endpoints: tuple[Path, Path],
        sources: Mapping[Path, str | None],
        selected: Callable[[p.Infra.RopeOccurrence], bool],
    ) -> p.Infra.RopeChangeSet | None:
        """Return the native binding transfer for one resolved declaration.

        Returns:
            Native unapplied changes retaining the source binding's kind, or None
            when a method transfer is already complete.

        """
        origin, target = endpoints
        destination_owner = intent.destination_scope.rpartition(".")[0]
        if intent.kind == "method":
            return u.Infra.method_transfer_changes(
                project,
                m.Infra.RopeMethodTransfer(
                    id=f"{intent.source_module}.{intent.source_scope}",
                    destination=(intent.destination_module, destination_owner),
                    methods=((intent.source_module, intent.source_scope),),
                    receiver_rewrites=intent.receiver_rewrites,
                ),
                tuple(path for path, source in sources.items() if source is not None),
                u.Infra.source_member_resolver(project, sources={}),
            )
        return u.Infra.move_binding_changes(
            project,
            u.Infra.file_resource_at(project, origin),
            cls._rewire_identifier_offset(
                project, intent.source_module, intent.source_scope, sources
            ),
            u.Infra.file_resource_at(project, target),
            options=m.Infra.RopeMoveOptions(
                resources=tuple(
                    u.Infra.file_resource_at(project, path)
                    for path in dict.fromkeys((
                        *(
                            path
                            for path in sources
                            if path.suffix == c.Infra.EXT_PYTHON
                        ),
                        origin,
                        target,
                    ))
                ),
                destination_offset=None
                if not destination_owner
                else cls._rewire_identifier_offset(
                    project,
                    intent.destination_module,
                    destination_owner,
                    sources,
                ),
                match_filter=selected,
            ),
        )

    @classmethod
    def _absorb_module_plans(
        cls,
        moved: tuple[p.Infra.CodegenFilePlan, ...],
        sources: MutableMapping[Path, str | None],
    ) -> None:
        """Apply native module move plans to the in-memory source overlay.

        Raises:
            ValueError: If a native module plan escapes the source view.

        """
        for plan in moved:
            if plan.path not in sources:
                msg = "native module rewire escaped its source view"
                raise ValueError(msg)
            sources[plan.path] = (
                None
                if plan.desired_content is None
                else plan.desired_content.decode(c.DEFAULT_ENCODING)
            )

    @classmethod
    def _absorb_rewire_changes(
        cls,
        project: p.Infra.RopeProject,
        changes: p.Infra.RopeChangeSet,
        sources: MutableMapping[Path, str | None],
    ) -> None:
        """Apply native content changes to the in-memory source overlay.

        Raises:
            TypeError: If a native binding rewire returned a non-content effect.
            ValueError: If a native binding rewire escaped the source view.

        """
        consumers = frozenset(
            path for path in sources if path.suffix == c.Infra.EXT_PYTHON
        )
        for change in changes.changes:
            if not isinstance(change, p.Infra.RopeChangeContents):
                msg = "native binding rewire returned a non-content effect"
                raise TypeError(msg)
            path = Path(change.resource.real_path)
            if path not in sources:
                msg = "native binding rewire escaped its authenticated source view"
                raise ValueError(msg)
            previous = sources[path]
            sources[path] = (
                u.Infra.remove_orphaned_imports(
                    project, change.resource, previous, change.new_contents
                )
                if path in consumers and previous is not None
                else change.new_contents
            )

    @classmethod
    def _replay_native_rewires(
        cls,
        planned: Callable[
            [Mapping[Path, str | None], Sequence[Path] | None],
            tuple[
                tuple[p.Infra.CodegenFilePlan, ...],
                AbstractContextManager[p.Infra.RopeProject],
            ],
        ],
        artifact: p.Infra.SemanticRenamePlan,
        roots: Mapping[Path, Path],
        sources: MutableMapping[Path, str | None],
        originals: Mapping[Path, p.Cli.AtomicFileState],
    ) -> None:
        """Replay native binding transfers over the source/scaffold overlay only."""
        consumers = tuple(path for path in sources if path.suffix == c.Infra.EXT_PYTHON)
        for intent in artifact.rewires:
            recorded = cls._rewire_import_root(
                artifact.candidate.workspace
                / intent.supplier_root
                / intent.source_path,
                intent.source_module,
            )
            current = roots[recorded]
            original = artifact.candidate.workspace / intent.supplier_root
            origin = current / (original / intent.source_path).relative_to(recorded)
            target = current / (original / intent.destination_path).relative_to(
                recorded
            )
            _plans, opened = planned(sources, None)
            with opened as project:
                if intent.kind == "module":
                    moved = cls._module_rewire_plans(
                        project, (origin, target), sources, originals
                    )
                    cls._absorb_module_plans(moved, sources)
                    continue
                retained = cls._current_rewire_sites(
                    planned(sources, consumers)[1], intent, consumers
                )
                public = u.Infra.preserved_receiver_reference_filter(
                    project, intent.public_routes
                )

                def selected(
                    occurrence: p.Infra.RopeOccurrence,
                    public: Callable[[p.Infra.RopeOccurrence], bool] = public,
                    retained: frozenset[tuple[Path, int]] = retained,
                ) -> bool:
                    resource = occurrence.resource
                    if (
                        resource is not None
                        and (Path(resource.real_path), occurrence.offset) in retained
                    ):
                        return False
                    return public(occurrence)

                changes = cls._binding_rewire_changes(
                    project, intent, (origin, target), sources, selected
                )
                if changes is None:
                    continue
                cls._absorb_rewire_changes(project, changes, sources)

    @classmethod
    def plan_module_names(
        cls,
        root: Path,
        source_plan: p.Infra.SemanticSourcePlan,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Derive one package or module naming wave from authenticated inventory.

        Package waves precede module waves and never select parent and child together.
        Special double-underscore modules stay intact.
        Explicit consumer roots participate in reference rewriting, not discovery.

        Returns:
            The unchanged source plan or its native cross-root rename candidate.

        """
        if source_plan.candidate.updates:
            return r[p.Infra.SemanticSourcePlan].fail(
                "module naming discovery requires the original source seed"
            )
        sources = u.Infra.candidate_python_sources(
            source_plan.candidate, source_plan.candidate.inputs
        )
        with FlextInfraRopeWorkspace.open_workspace(
            root, rope_repository_root=root
        ) as workspace:
            packages = cls._package_naming_candidates(root, sources, workspace)
            candidates = packages or cls._module_naming_candidates(
                root, sources, workspace
            )
            reason = (
                "Facade package removes split suffix"
                if packages
                else "Python module removes private prefix and split suffix"
            )
            selections = [
                cls._module_naming_selection(workspace, path, replacement, reason)
                for path, replacement in candidates
            ]
            if not selections:
                return r[p.Infra.SemanticSourcePlan].ok(source_plan)
            planned = cls.build_rename_plan(
                root,
                workspace,
                m.Infra.SemanticRenameSelections(
                    decisions=tuple(selections),
                    consumer_roots=source_plan.consumer_roots,
                ),
                source_plan=source_plan,
            )
            if planned.failure:
                return r[p.Infra.SemanticSourcePlan].from_failure(planned)
            return r[p.Infra.SemanticSourcePlan].ok(planned.value)

    @staticmethod
    def _module_naming_selection(
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        replacement: str,
        reason: str,
    ) -> p.Infra.SemanticRenameSelection:
        """Authenticate one naming candidate against its native module identity.

        The candidate must be an inventoried module whose declaration resolves to
        the same file, and its sibling destination must still be free.

        Returns:
            The explicit rename selection for the candidate module.

        Raises:
            ValueError: If the module is not inventoried, its identity resolves to
                another file, or the destination module is already occupied.

        """
        module = workspace.module(path)
        if module is None:
            msg = f"module naming requires an inventoried module: {path}"
            raise ValueError(msg)
        declaration = FlextInfraCodemodRenameSymbols.inventoried_declaration(
            workspace, module.module_name
        )
        if Path(declaration.file_path) != path:
            msg = f"module naming identity resolves to another file: {path}"
            raise ValueError(msg)
        destination = ".".join((
            *module.module_name.split(".")[:-1],
            replacement,
        ))
        if workspace.rope_project.find_module(destination) is not None:
            msg = f"module naming destination is occupied: {destination}"
            raise ValueError(msg)
        return m.Infra.SemanticRenameSelection(
            qualified_name=module.module_name,
            replacement_name=replacement,
            reason=reason,
        )

    @staticmethod
    def _skips_module_naming(
        path: Path,
        root: Path,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> bool:
        """Return whether a path owns no naming decision.

        Dunder modules and paths outside the checkout never rename; legacy
        federation trees outside the inventoried modules are left untouched.

        Returns:
            ``True`` when the path is not a candidatesource.

        """
        name = path.stem
        if not path.is_relative_to(root.resolve()) or (
            name.startswith("__") and name.endswith("__")
        ):
            return True
        return workspace.module(path) is None

    @classmethod
    def _module_naming_candidates(
        cls,
        root: Path,
        sources: Mapping[Path, str],
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> tuple[tuple[Path, str], ...]:
        """Select module names without changing the authenticated native sources.

        Directory-owned prefixes follow the native package chain. A remaining
        responsibility is preserved; the same prefix is not consumed repeatedly
        across successive naming waves.

        Returns:
            Introducing module paths and their unambiguous destination basenames.

        Raises:
            ValueError: If a stripped identifier or responsibility is invalid.

        """
        selected: list[tuple[Path, str]] = []
        for path in sorted(sources):
            if cls._skips_module_naming(path, root, workspace):
                continue
            name = path.stem
            replacement = name.lstrip("_")
            part = re.search(r"_parts?(?:_?\d+)?$", name)
            if part is not None:
                owner = name[: part.start()]
                replacement = (
                    cls._module_responsibility_name(workspace, path, owner)
                    if part.group()[-1].isdigit()
                    else owner.lstrip("_")
                )
            else:
                replacement = cls._directory_owned_module_name(
                    workspace, path, replacement
                )
            if replacement == name:
                continue
            # A sibling data directory (YAML/JSON resources, no Python source)
            # owns the public basename; the private module keeps its prefix.
            data_dir = path.parent / replacement
            if data_dir.is_dir() and not any(data_dir.rglob("*.py")):
                continue
            # A public name of the parent package (the `config`/`settings`
            # singletons) cannot also be a submodule: importing the submodule
            # rebinds the parent attribute and shadows the lazy export.
            parent_init = path.parent / c.Infra.INIT_PY
            parent_resource = workspace.rope_project.get_file(
                parent_init.relative_to(root).as_posix()
            )
            if parent_resource.exists() and replacement in (
                u.Infra.public_export_names_source(
                    u.Infra.require_source_module(
                        workspace.rope_project.get_pymodule(
                            parent_resource, force_errors=True
                        )
                    )
                )
            ):
                if part is not None or replacement != name.lstrip("_"):
                    msg = (
                        f"module naming destination shadows its parent publication: "
                        f"{path} -> {replacement}"
                    )
                    raise ValueError(msg)
                continue
            if not replacement.isidentifier() or keyword.iskeyword(replacement):
                msg = (
                    f"module naming has no valid public identifier: {path}; "
                    "unresolved semantic grouping requires an explicit responsibility"
                )
                raise ValueError(msg)
            collision = next(
                (
                    other
                    for other, name in selected
                    if other.parent == path.parent and name == replacement
                ),
                None,
            )
            if collision is not None:
                msg = (
                    f"unresolved semantic grouping: {path} and {collision} both "
                    f"derive `{replacement}`; one responsibility per module"
                )
                raise ValueError(msg)
            selected.append((path, replacement))
        return tuple(selected)

    @staticmethod
    def _directory_owned_module_name(
        workspace: p.Infra.RopeWorkspaceDsl, path: Path, name: str
    ) -> str:
        """Remove one unambiguous directory-owned prefix from a native module.

        Prefixes end at the containing package, so an ancestor word appearing
        alone in a deeper domain remains part of that module's responsibility.

        Returns:
            The remaining responsibility, or the original unprefixed basename.

        Raises:
            ValueError: If the module is not inventoried or its remaining name
                would repeat the same naming decision in another wave.

        """
        module = workspace.module(path)
        if module is None:
            msg = f"module naming requires an inventoried module: {path}"
            raise ValueError(msg)
        owners = tuple(part.lstrip("_") for part in module.module_name.split(".")[:-1])
        prefixes = tuple("_".join(owners[index:]) + "_" for index in range(len(owners)))
        for prefix in prefixes:
            if not name.startswith(prefix):
                continue
            replacement = name[len(prefix) :].lstrip("_")
            if any(replacement.startswith(other) for other in prefixes):
                msg = (
                    f"module naming has an ambiguous repeated responsibility: "
                    f"{path} -> {replacement}"
                )
                raise ValueError(msg)
            return replacement
        return name

    @classmethod
    def _module_responsibility_name(
        cls, workspace: p.Infra.RopeWorkspaceDsl, path: Path, owner: str
    ) -> str:
        """Derive a numbered fragment's responsibility from its native declaration.

        The introducing declaration names it when its name adds a word to the
        owner stem; a mechanical split class (``<Owner>Part01``) adds only the
        split marker, so its own public methods name it instead.

        Returns:
            The owner-relative snake-case responsibility of the fragment.

        Raises:
            ValueError: If the native source does not identify one responsibility.

        """
        objects = tuple(workspace.objects(path, include_references=False))
        declarations = tuple(
            item
            for item in objects
            if item.kind in {"class", "function"} and item.scope_path == item.name
        )
        responsibility = ""
        methods: Sequence[str] = ()
        nested_classes: Sequence[str] = ()
        if len(declarations) == 1:
            declared = declarations[0].name
            responsibility = cls._declared_responsibility(path, owner, declared)
            methods = tuple(
                item.name
                for item in objects
                if item.kind == "method"
                and item.scope_path == f"{declared}.{item.name}"
                and not item.name.startswith("_")
            )
            nested_classes = tuple(
                item.name
                for item in objects
                if item.kind == "class"
                and item.scope_path.startswith(f"{declared}.")
                and item.scope_path.count(".") == 1
                and not item.name.startswith("_")
            )
            if not responsibility and len(nested_classes) == 1:
                responsibility = cls._declared_responsibility(
                    path, owner, nested_classes[0]
                )
            if not responsibility:
                responsibility = cls._member_responsibility(
                    (*methods, *nested_classes), owner
                )
        if not responsibility:
            msg = (
                f"unresolved semantic grouping: {path}; numbered split requires "
                "one owner-relative responsibility from native source evidence "
                f"(public methods: {', '.join(methods) or 'none'}; "
                f"public nested classes: {', '.join(nested_classes) or 'none'})"
            )
            raise ValueError(msg)
        return responsibility

    @staticmethod
    def _declared_responsibility(path: Path, owner: str, declared: str) -> str:
        """Read the responsibility the introducing declaration's name adds.

        Returns:
            The owner-relative suffix, or empty when the name adds only the
            owner stem or the split marker.

        """
        words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", declared)
        stem = owner.lstrip("_").replace("_", "").lower()
        responsibility = ""
        prefix = ""
        for index, word in enumerate(words):
            prefix += word.lower()
            if not stem.startswith(prefix):
                if index:
                    responsibility = "_".join(words[index:]).lower()
                break
        else:
            # The declaration spells the whole module stem, so its
            # responsibility is what it adds to its family package
            # (``_container`` + ``FlextContainerTestingOps`` -> testing_ops).
            family = path.parent.name.lstrip("_").replace("_", "").lower()
            prefix = ""
            for position, part in enumerate(words[:-1]):
                prefix += part.lower()
                if prefix.endswith(family):
                    responsibility = "_".join(words[position + 1 :]).lower()
                    break
        if re.fullmatch(r"(?:part_?)?\d*", responsibility):
            return ""
        return responsibility

    @staticmethod
    def _member_responsibility(methods: Sequence[str], owner: str) -> str:
        """Name a split class by the word its own public methods share.

        A single public method names the fragment; otherwise the one word
        outside the owner stem that most method names repeat does. A tie, or
        no repeated word, leaves the fragment unresolved.

        Returns:
            The responsibility word, or empty when the methods name none.

        """
        if len(methods) == 1:
            return methods[0]
        stem = owner.lstrip("_").replace("_", "").lower()
        counts: dict[str, int] = {}
        for name in methods:
            for word in dict.fromkeys(name.split("_")):
                if word and word not in stem:
                    counts[word] = counts.get(word, 0) + 1
        if not counts:
            return ""
        top = max(counts.values())
        leaders = [word for word, count in counts.items() if count == top]
        return leaders[0] if top > 1 and len(leaders) == 1 else ""

    @staticmethod
    def _package_naming_candidates(
        root: Path,
        sources: Mapping[Path, str],
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> tuple[tuple[Path, str], ...]:
        """Select shallowest split packages with an authenticated semantic owner.

        Returns:
            Initializer paths and semantic destination basenames for one wave.

        Raises:
            ValueError: If split naming has no unambiguous semantic responsibility.

        """
        selected: list[tuple[Path, str]] = []
        families = u.Infra.facade_families()
        for path in sorted(sources, key=lambda item: (len(item.parts), item)):
            if path.name != c.Infra.INIT_PY or not path.is_relative_to(root.resolve()):
                continue
            directory = path.parent
            if any(directory.is_relative_to(owner.parent) for owner, _ in selected):
                continue
            part = re.search(r"_parts?(?:_?\d+)?$", directory.name)
            if part is None:
                continue
            basename = directory.name[: part.start()].lstrip("_")
            if (
                not basename.isidentifier()
                or keyword.iskeyword(basename)
                or part.group()[-1].isdigit()
            ):
                msg = (
                    f"unresolved semantic grouping: {directory}; split package "
                    "requires a responsibility name from semantic source evidence"
                )
                raise ValueError(msg)
            owned = any(
                letter
                in u.Infra.public_export_names_source(
                    u.Infra.require_source_module(
                        workspace.rope_project.get_pymodule(
                            u.Infra.file_resource_at(workspace.rope_project, facade),
                            force_errors=True,
                        )
                    )
                )
                for ancestor in (directory, *directory.parents)
                if ancestor.is_relative_to(root.resolve())
                for letter, family in families.items()
                if ancestor.name in family.directories
                or (
                    ancestor == directory
                    and basename in {family.module, family.directory.lstrip("_")}
                )
                for filename in family.file_names
                if (facade := ancestor.parent / filename) in sources
            )
            composition = (
                owned
                or FlextInfraCodemodSemanticApply._split_composition_owner(
                    directory, sources, workspace
                )
            )
            if not composition:
                msg = (
                    f"unresolved semantic grouping: {directory}; split package "
                    "has no authenticated declaration or composition owner"
                )
                raise ValueError(msg)
            selected.append((path, f"_{basename}"))
        return tuple(selected)

    @staticmethod
    def _split_composition_owner(
        directory: Path,
        sources: Mapping[Path, str],
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> bool:
        """Authenticate one exported native composition root for a split package.

        Returns:
            Whether exactly one local public class composes a captured provider.

        Raises:
            ValueError: If competing local public classes claim the split package.

        """
        project = workspace.rope_project
        owners: list[tuple[Path, str]] = []
        for source in sources:
            if (
                source.parent != directory.parent
                or source.suffix != c.Infra.EXT_PYTHON
                or source.name == c.Infra.INIT_PY
            ):
                continue
            resource = u.Infra.file_resource_at(project, source)
            module = u.Infra.require_source_module(
                project.get_pymodule(resource, force_errors=True)
            )
            package = module.get_name().rpartition(".")[0]
            target = f"{package}.{directory.name}"
            if not any(
                imported == target or imported.startswith(f"{target}.")
                for imported in u.Infra.resolve_declared_module_imports(
                    project, resource
                ).values()
            ):
                continue
            for scope in u.Infra.declared_class_scopes(
                module.get_scope(),
                names=frozenset(u.Infra.public_export_names_source(module)),
            ):
                owner = u.Infra.require_class_object(scope.pyobject, str(source))
                if any(
                    u.Infra.py_class(base)
                    and (resource := base.get_module().get_resource()) is not None
                    and Path(resource.real_path).is_relative_to(directory)
                    for base in owner.get_bases()
                ):
                    owners.append((source, owner.get_name()))
        if len(owners) > 1:
            msg = f"competing semantic composition roots for split package: {directory}"
            raise ValueError(msg)
        return bool(owners)

    @staticmethod
    def _source_scopes(
        root: Path,
        consumer_roots: tuple[Path, ...],
    ) -> p.Result[tuple[Path, ...]]:
        """Elect explicit non-overlapping native source scopes.

        Returns:
            The producer followed by its distinct declared consumer roots.

        """
        outcome = r[tuple[Path, ...]]
        if any(not path.is_absolute() or not path.is_dir() for path in consumer_roots):
            return outcome.fail(
                "consumer roots must be existing absolute checkout roots"
            )
        scopes = tuple(
            dict.fromkeys(
                u.Infra.rope_repository_root(path).resolve()
                for path in (root, *consumer_roots)
            )
        )
        if any(
            left != right and left.is_relative_to(right)
            for left in scopes
            for right in scopes
        ):
            return outcome.fail("rename scopes overlap")
        return outcome.ok(scopes)

    @classmethod
    def _source_closure(
        cls,
        scopes: tuple[Path, ...],
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[p.Infra.StageSourcePlan]:
        """Plan the source closure of the elected scopes without any update.

        Returns:
            The original source closure.

        """
        return FlextInfraStagedPackage.plan_sources(
            scopes[0],
            {},
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": scopes,
                "snapshot": (snapshot),
                "inputs": (
                    tuple(
                        cls._input_state(path, snapshot)
                        for path in dict.fromkeys(
                            project.resolve() / target
                            for scope in scopes
                            for project in (
                                u.Infra.import_project_roots(scope)
                                if (scope / c.Infra.GITMODULES).is_file()
                                else (scope,)
                            )
                            for target in u.Infra.ast_grep_scan_targets(
                                project.resolve()
                            )
                        )
                    )
                ),
            }),
        )

    @staticmethod
    def _input_state(
        path: Path, snapshot: p.Infra.WorkspaceSnapshot | None
    ) -> p.Cli.AtomicFileState:
        """Authenticate one scanned source once: the run's read, or a direct one.

        Returns:
            The authenticated state, shared with the snapshot for member sources.

        """
        if (
            snapshot is not None
            and path.suffix == c.Infra.EXT_PYTHON
            and not frozenset(snapshot.members).isdisjoint(path.parents)
        ):
            return u.Infra.workspace_source(snapshot, path).state
        return u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()

    @staticmethod
    def _planning_election(
        live: p.Infra.RopeProject,
        source_folders: tuple[str, ...],
        python_folders: tuple[str, ...],
    ) -> p.Infra.RopeProjectElection:
        """Elect the multiproject source and interpreter folders of one plan.

        Returns:
            The election the overlay project resolves imports through.

        """
        return u.Infra.native_election(live).model_copy(
            update={
                "source_folders": source_folders,
                "python_path_folders": python_folders,
            }
        )

    @classmethod
    def _build_native_rename_plan(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        selections: p.Infra.SemanticRenameSelections,
        scopes: tuple[Path, ...],
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[p.Infra.SemanticRenamePlan]:
        """Capture all elected sources before computing any native candidate.

        Returns:
            A single authenticated candidate spanning only the elected scopes.

        """
        decisions = tuple(
            m.Infra.SemanticRenameDecision(
                declaration=FlextInfraCodemodRenameSymbols.inventoried_declaration(
                    workspace, selection.qualified_name
                ),
                replacement_name=selection.replacement_name,
                reason=selection.reason,
                contracts=tuple(
                    FlextInfraCodemodRenameSymbols.inventoried_declaration(
                        workspace, identity
                    )
                    for identity in selection.contracts
                ),
            )
            for selection in selections.decisions
        )
        return cls._build_native_source_plan(scopes, decisions, snapshot).map(
            lambda planned: m.Infra.SemanticRenamePlan(
                decisions=decisions,
                edits=cls._rename_edits(
                    u.Infra.candidate_python_sources(
                        planned[0].candidate, planned[0].candidate.inputs
                    ),
                    planned[0].candidate.updates,
                ),
                candidate=planned[0].candidate,
                consumer_roots=planned[0].consumer_roots,
                moves=planned[1],
            )
        )

    @classmethod
    def _build_native_source_plan(
        cls,
        scopes: tuple[Path, ...],
        decisions: tuple[p.Infra.SemanticRenameDecision, ...],
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[tuple[p.Infra.SemanticSourcePlan, tuple[tuple[Path, Path], ...]]]:
        """Share native capture, planning and receipts across source campaigns.

        Returns:
            The authenticated candidate and its actual native module moves.

        """
        captured_sources = cls._source_closure(scopes, snapshot)
        if captured_sources.failure:
            return r[
                tuple[p.Infra.SemanticSourcePlan, tuple[tuple[Path, Path], ...]]
            ].from_failure(captured_sources)
        baseline = captured_sources.value
        captured = m.Infra.CodemodBindingSnapshot(states=baseline.inputs)
        original = u.Infra.candidate_python_sources(baseline, captured.states)
        with ExitStack() as stack:
            # One native project per repository; a module elects in its owner only.
            live = tuple(
                stack.enter_context(
                    u.Infra.open_project(
                        owner,
                        project_roots=u.Infra.discover_rope_project_roots(owner),
                        consumer_root=owner,
                    )
                )
                for owner in dict.fromkeys(
                    project.resolve()
                    for scope in scopes
                    for project in u.Infra.import_project_roots(scope)
                )
            )
            python_folders = tuple(
                dict.fromkeys(
                    folder.real_path
                    for project in live
                    for folder in (
                        *project.get_source_folders(),
                        *(
                            item
                            for item in project.get_python_path_folders()
                            if item.is_folder()
                        ),
                    )
                )
            )
            snapshots = tuple(
                stack.enter_context(
                    closing(
                        u.Infra.planned_project(
                            project,
                            election=cls._planning_election(
                                project,
                                tuple(
                                    folder.path
                                    for folder in project.get_source_folders()
                                ),
                                python_folders,
                            ),
                        )
                    )
                )
                for project in live
            )
            updates, moves = FlextInfraCodemodRenameSymbols.plan_native_candidates(
                snapshots, original, decisions
            )
        staged_inputs = cls._staged_inputs(moves, captured.states)
        if staged_inputs.failure:
            return r[
                tuple[p.Infra.SemanticSourcePlan, tuple[tuple[Path, Path], ...]]
            ].from_failure(staged_inputs)
        return FlextInfraStagedPackage.plan_sources(
            scopes[0],
            updates,
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": (scopes if len(scopes) > 1 else ()),
                "modes": ({
                    target: state.mode
                    for source, target in moves
                    for state in staged_inputs.value
                    if state.path == source and state.mode is not None
                }),
                "inputs": (staged_inputs.value),
                "snapshot": (snapshot),
            }),
        ).map(
            lambda candidate: (
                m.Infra.SemanticSourcePlan(
                    candidate=candidate,
                    consumer_roots=scopes[1:],
                ),
                moves,
            )
        )

    @staticmethod
    def _rename_edits(
        original: Mapping[Path, str],
        updates: Mapping[Path, str | None],
    ) -> tuple[p.Infra.SemanticMigrationEdit, ...]:
        """Render one migration edit per updated original source.

        Returns:
            The edits for every planned path that stays inside the originals.

        """
        return tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=original[path],
                updated_source=source,
                changes=("native multiproject semantic rename",),
            )
            for path, source in sorted(updates.items())
            if path in original and source is not None
        )

    @classmethod
    def _staged_inputs(
        cls,
        moves: Sequence[tuple[Path, Path]],
        base_states: tuple[p.Cli.AtomicFileState, ...],
    ) -> p.Result[tuple[p.Cli.AtomicFileState, ...]]:
        """Authenticate native module destinations as absent before staging.

        Returns:
            The staged input states including every move destination, or the
            first destination that appeared before staging.

        """
        result_type = r[tuple[p.Cli.AtomicFileState, ...]]
        destinations = tuple(
            u.Cli.atomic_read_binary_file_state(target).unwrap()
            for _origin, target in moves
        )
        if any(state.content is not None for state in destinations):
            return result_type.fail("native module destination appeared before staging")
        return result_type.ok(
            m.Infra.CodemodBindingSnapshot(states=(*base_states, *destinations)).states
        )

    @classmethod
    @contextmanager
    def planning_workspace(
        cls,
        root: Path,
        seed: p.Infra.SemanticSourcePlan,
        sources: Mapping[Path, str],
    ) -> Generator[p.Infra.RopeWorkspaceDsl]:
        """Elect a bounded native graph over the live tree and planned bytes.

        Yields:
            The existing workspace DSL with target selection separate from read scope.

        """
        candidate = seed.candidate
        scopes = candidate.workspaces or (candidate.workspace,)
        projects = tuple(
            dict.fromkeys(
                project
                for scope in scopes
                for project in (
                    u.Infra.import_project_roots(scope)
                    if (scope / c.Infra.GITMODULES).is_file()
                    else (scope,)
                )
            )
        )
        with ExitStack() as stack:
            native_projects = tuple(
                stack.enter_context(
                    u.Infra.open_project(
                        owner,
                        project_roots=u.Infra.discover_rope_project_roots(owner),
                        consumer_root=owner,
                    )
                )
                for owner in dict.fromkeys((root, *projects))
            )
            source_folders = tuple(
                dict.fromkeys(
                    folder.real_path
                    for native in native_projects
                    for folder in native.get_source_folders()
                )
            )
            python_folders = tuple(
                dict.fromkeys((
                    *source_folders,
                    *(
                        folder.real_path
                        for native in native_projects
                        for folder in native.get_python_path_folders()
                        if folder.is_folder()
                    ),
                ))
            )
            live = stack.enter_context(
                u.Infra.open_project(
                    candidate.workspace,
                    project_roots=projects,
                    fscommands=FlextInfraRopeProject.OverlayFiles(()),
                )
            )
            project = stack.enter_context(
                closing(
                    u.Infra.planned_project(
                        live,
                        election=cls._planning_election(
                            live,
                            tuple(
                                Path(folder).relative_to(candidate.workspace).as_posix()
                                for folder in source_folders
                            ),
                            python_folders,
                        ),
                        declared_files=cls.planning_file_plans(
                            root, candidate, sources
                        ),
                        observations=candidate.inputs,
                    )
                )
            )
            snapshot = stack.enter_context(
                u.Infra.workspace_snapshot(candidate.workspace, projects)
            )
            with FlextInfraRopeWorkspace.open_workspace(
                root,
                rope_repository_root=candidate.workspace,
                source_project=project,
                workspace_index=u.Infra.index_rope_workspace(
                    snapshot, root, project=project
                ),
                snapshot=snapshot,
            ) as workspace:
                yield workspace

    @staticmethod
    def planning_file_plans(
        root: Path,
        candidate: p.Infra.StageSourcePlan,
        sources: Mapping[Path, str],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        """Declare source deltas against the candidate's captured observations.

        Returns:
            One plan per planned addition, rewrite, or retirement.

        Raises:
            ValueError: A planned source has no authenticated physical witness.

        """
        states = {state.path: state for state in candidate.inputs}
        selected = {**candidate.updates, **sources}
        planned: list[p.Infra.CodegenFilePlan] = []
        for path, source in selected.items():
            before = states.get(path)
            if before is None:
                message = f"candidate source has no authenticated input witness: {path}"
                raise ValueError(message)
            desired = None if source is None else source.encode(c.DEFAULT_ENCODING)
            mode = (
                None
                if source is None
                else candidate.modes.get(
                    path,
                    before.mode
                    if before.content is not None
                    else config.Infra.codegen.modes.file_default,
                )
            )
            if before.content == desired and before.mode == mode:
                continue
            planned.append(
                m.Infra.CodegenFilePlan(
                    project=u.Infra.project_root(path) or root,
                    path=path,
                    before=before,
                    desired_content=desired,
                    desired_mode=mode,
                )
            )
        return tuple(planned)

    @classmethod
    def consume_rename_plan(
        cls,
        request: p.Infra.ModCommand,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Re-derive an artifact and validate its complete candidate before effects.

        Returns:
            The first authentication/runtime failure, or the accepted candidate.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        root = u.Infra.import_project_roots(root)[0]
        loaded = cls.load_rename_artifact(root, request)
        verified = loaded.flat_map(
            lambda pair: cls._verify_rename_artifact(
                request,
                workspace,
                pair,
            )
        )
        if verified.failure:
            return verified
        artifact = loaded.value[0]
        action = (
            "apply"
            if request.apply and not request.check and not request.dry_run_mode
            else "preview"
        )
        cli.display_text(
            f"semantic rename {action}: "
            f"decisions={len(artifact.decisions)} "
            f"rewires={len(artifact.rewires)} runtime=validated"
        )
        return r[bool].ok(value=True)

    @classmethod
    def publish_candidate(
        cls,
        root: Path,
        candidate: p.Infra.SemanticSourcePlan,
        *,
        publish: bool = True,
        validator: Callable[[Path], p.Result[bool]] | None = None,
    ) -> p.Result[tuple[Path, ...]]:
        """Publish one rule-composed native candidate.

        Returns:
            The canonical publisher's acknowledged paths or original failure.

        """
        return cls._publish_authenticated_source(
            root, candidate, publish=publish, validator=validator
        )

    @classmethod
    def load_rename_artifact(
        cls,
        root: Path,
        request: p.Infra.ModCommand,
    ) -> p.Result[tuple[p.Infra.SemanticRenamePlan, p.Cli.AtomicFileState]]:
        """Authenticate the semantic rename driver and parse its artifact.

        Returns:
            The first artifact failure, or the parsed plan with its driver state.

        """
        loaded = r[tuple[p.Infra.SemanticRenamePlan, m.Cli.AtomicFileState]]
        if request.rename_plan is None:
            return loaded.fail("semantic rename consumption requires an artifact")
        path = (root / request.rename_plan).resolve()
        driver = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
        if driver.content is None:
            return loaded.fail(f"semantic rename artifact disappeared: {path}")
        artifact = m.Infra.SemanticRenamePlan.model_validate_json(driver.content)
        if not path.is_relative_to(root) and not artifact.rewires:
            return loaded.fail("semantic rename artifact escapes workspace")
        return loaded.ok((
            artifact,
            driver,
        ))

    @classmethod
    def _verify_rename_artifact(
        cls,
        request: p.Infra.ModCommand,
        workspace: p.Infra.RopeWorkspaceDsl,
        pair: tuple[p.Infra.SemanticRenamePlan, p.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Re-derive, candidate-validate, and re-authenticate the artifact.

        Returns:
            The first verification failure, or the accepted candidate.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        root = u.Infra.import_project_roots(root)[0]
        artifact, driver = pair
        return cls.plan_rename_artifact(root, artifact, driver, workspace).flat_map(
            lambda seed: cls._publish_authenticated_source(
                root,
                seed,
                publish=request.apply
                and not request.check
                and not request.dry_run_mode,
            ).map(lambda _published: True)
        )

    @classmethod
    def plan_rename_artifact(
        cls,
        root: Path,
        artifact: p.Infra.SemanticRenamePlan,
        driver: p.Cli.AtomicFileState,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Admit native intent as this invocation's authenticated source seed.

        Returns:
            A fresh portable consumer candidate or the authenticated exact rename.

        """
        outcome = r[p.Infra.SemanticSourcePlan]
        if artifact.rewires:
            rebuilt = cls._rebuild_rewire_plan(root, artifact, workspace)
            if rebuilt.failure:
                return outcome.from_failure(rebuilt)
            if any(
                state.path == driver.path for state in rebuilt.value.candidate.inputs
            ):
                return outcome.fail(
                    "portable rewire driver aliases a governed source input"
                )
            observed = u.Cli.atomic_verify_binary_file_states((driver,))
            if observed.failure:
                return outcome.from_failure(observed)
            candidate = rebuilt.value.candidate.model_copy(
                update={
                    "inputs": (*rebuilt.value.candidate.inputs, driver),
                }
            )
            return outcome.ok(m.Infra.SemanticSourcePlan(candidate=candidate))
        verified = cls.authenticate_rename_candidate(root, artifact, driver, workspace)
        if verified.failure:
            return outcome.from_failure(verified)
        return outcome.ok(artifact)

    @classmethod
    def authenticate_rename_candidate(
        cls,
        root: Path,
        artifact: p.Infra.SemanticRenamePlan,
        driver: p.Cli.AtomicFileState,
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Authenticate and compare the complete persisted native artifact.

        Both standalone consumption and batch seeding require current identities
        and exact equivalence to the reconstructed native plan.

        Returns:
            The original authentication failure or exact persisted plan acceptance.

        """
        guarded = cls._authenticate_rename_inputs(root, artifact, driver)
        if guarded.failure:
            return guarded
        rebuilt = cls.build_rename_plan(
            root,
            workspace,
            cls.rename_selections(artifact),
            source_plan=artifact,
        )
        if rebuilt.failure:
            return r[bool].from_failure(rebuilt)
        current_fields = rebuilt.value.model_dump(mode="python")
        artifact_fields = artifact.model_dump(mode="python")
        if current_fields != artifact_fields:
            differences = [
                name
                for name in artifact_fields
                if current_fields[name] != artifact_fields[name]
            ]
            if "candidate" in differences:
                differences.remove("candidate")
                differences.extend(
                    cls._rename_candidate_differences(
                        artifact.candidate, rebuilt.value.candidate
                    )
                )
            return r[bool].fail(
                "semantic rename artifact differs from current native plan; fields="
                + ", ".join(differences)
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _rename_candidate_differences(
        original: p.Infra.StageSourcePlan,
        current: p.Infra.StageSourcePlan,
    ) -> tuple[str, ...]:
        """Describe exact candidate differences without emitting observed values.

        Returns:
            Candidate fields whose identities or recorded contents differ.

        """
        before = original.model_dump(mode="python")
        after = current.model_dump(mode="python")
        differences = [
            f"candidate.{name}" for name in before if before[name] != after[name]
        ]
        for name, original_records, current_records in (
            ("inputs", original.inputs, current.inputs),
            ("declared_files", original.declared_files, current.declared_files),
            ("layouts", original.layouts, current.layouts),
            (
                "candidate_layouts",
                original.candidate_layouts,
                current.candidate_layouts,
            ),
        ):
            if len(original_records) != len(current_records):
                differences.append(f"candidate.{name}.length")
            for index, (old, new) in enumerate(
                zip(original_records, current_records, strict=False)
            ):
                old_fields = old.model_dump(mode="python")
                new_fields = new.model_dump(mode="python")
                if old_fields != new_fields:
                    differences.extend(
                        f"candidate.{name}[{index}].{field}"
                        for field in old_fields
                        if old_fields[field] != new_fields[field]
                    )
                    break
        for name, old_paths, new_paths in (
            ("updates", original.updates, current.updates),
            ("modes", original.modes, current.modes),
        ):
            if old_paths.keys() != new_paths.keys():
                differences.append(f"candidate.{name}.keys")
            elif old_paths != new_paths:
                differences.append(f"candidate.{name}.values")
        return tuple(differences)

    @staticmethod
    def _authenticate_rename_inputs(
        root: Path,
        artifact: p.Infra.SemanticRenamePlan,
        driver: p.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Reject a foreign workspace, an aliased driver, or drifted identities.

        Returns:
            The first authentication failure, or the accepted candidate.

        """
        if (artifact.candidate.workspaces or (artifact.candidate.workspace,))[
            0
        ] != u.Infra.import_project_roots(root)[0].resolve():
            return r[bool].fail(
                "semantic rename candidate belongs to another workspace"
            )
        if any(state.path == driver.path for state in artifact.candidate.inputs):
            return r[bool].fail(
                "semantic rename driver aliases a governed source input"
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _publish_authenticated_source(
        root: Path,
        artifact: p.Infra.SemanticSourcePlan,
        *,
        publish: bool,
        validator: Callable[[Path], p.Result[bool]] | None = None,
    ) -> p.Result[tuple[Path, ...]]:
        """Publish the candidate's planned effects through the shared publisher.

        Returns:
            Actual published paths, or pending paths when publication is disabled.

        """
        originals = {state.path: state for state in artifact.candidate.inputs}
        updates = artifact.candidate.updates
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=max(
                    (
                        owner
                        for owner in artifact.candidate.roots
                        if path.is_relative_to(owner)
                    ),
                    key=lambda owner: len(owner.parts),
                ),
                path=path,
                before=originals[path],
                desired_content=None
                if source is None
                else source.encode(c.DEFAULT_ENCODING),
                desired_mode=(
                    None
                    if source is None
                    else artifact.candidate.modes.get(path, originals[path].mode)
                ),
            )
            for path, source in updates.items()
        )
        return (
            FlextInfraTransformersSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=u.Infra.import_project_roots(root)[0].resolve(),
                options=m.Infra.SemanticPublicationOptions(
                    inputs=artifact.candidate.inputs,
                    validator=validator,
                    projection_roots=tuple(
                        sorted({
                            root,
                            *(u.Infra.project_root(path) or root for path in updates),
                        })
                    ),
                ),
                publish=publish,
            )
        )

    @classmethod
    def census_constants(
        cls,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        apply: bool,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Compose declaration and constant consumers before census acceptance.

        Args:
            root: Repository root governing the census scope.
            rope_workspace: The native workspace DSL used for planning.
            apply: Whether the composed candidate is also published.
            workspace_factory: Validator workspace factory for staged candidates.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]``.

        """
        inventory: p.Infra.ModOccurrenceReport[p.Infra.ModOccurrence] = (
            m.Infra.ModOccurrenceReport(files=frozenset(), entries=())
        )
        original = cls.source_inventory(root, inventory)
        planned = cls.plan_census_constants(root, rope_workspace, sources=original)
        if planned.failure:
            return planned
        working = dict(original)
        changed: set[Path] = set()
        cls.apply_plan(working, planned.value, changed)
        if not apply:
            return planned
        # A no-op candidate still verifies its planned inventory. A nonempty
        # candidate keeps the exact union, even when normalization writes no bytes.
        project_roots = {u.Infra.project_root(path) for path in changed or original}
        if not project_roots or None in project_roots:
            return r[tuple[p.Infra.SemanticMigrationEdit, ...]].fail(
                "census corrective candidate has no complete governed project scope",
            )
        projects = tuple(
            sorted(
                project.relative_to(root).as_posix()
                for project in project_roots
                if project is not None
            ),
        )

        def verify(candidate_root: Path) -> p.Result[bool]:
            with workspace_factory(candidate_root, None) as candidate_workspace:
                fixed_point = cls.plan_census_constants(
                    candidate_root,
                    candidate_workspace,
                    sources=cls.source_inventory(candidate_root, inventory),
                )
            if fixed_point.failure:
                return r[bool].from_failure(fixed_point)
            if fixed_point.value:
                return r[bool].fail(
                    "constants census candidate retains corrective edits"
                )
            return FlextInfraWorkspaceChecker(
                repository_root=candidate_root,
            ).execute_payload(
                m.Infra.RunCommand(
                    repository_root=candidate_root,
                    projects=projects,
                    reports_dir=str(
                        m.Infra.RunCommand(repository_root=root).reports_dir_path
                    ),
                    gates=(c.Infra.LINT, c.Infra.PYREFLY, c.Infra.FRESH_IMPORT),
                ),
            )

        return cls._publish(
            root,
            original,
            {path: working[path] for path in changed},
            validator=verify,
        ).map(lambda _: planned.value)

    @classmethod
    def plan_census_constants(
        cls,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan both census owners against one original-to-final source candidate.

        Returns:
            Combined declaration and consumer edits, never just the last phase.

        """
        phases = (
            c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
            c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
        )
        working = dict(sources)
        changed: set[Path] = set()
        result_type = r[tuple[p.Infra.SemanticMigrationEdit, ...]]
        if rope_workspace.repository_root.resolve() != root.resolve():
            return result_type.fail(
                "constants planner target differs from workspace selection"
            )
        for phase in phases:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                import_normalizer=u.Infra.normalize_import_source,
                rope_workspace=rope_workspace,
                sources=working,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            cls.apply_plan(working, planned.value, changed)
        if changed:
            verified = cls._verify_phase_sequences(working, rope_workspace, phases)
            if verified.failure:
                return result_type.from_failure(verified)
        u.Infra.preflight_semantic_import_graph(rope_workspace, sources, working)
        return cls._check_definition_time(sources, working, changed).map(
            lambda _: tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=sources[path],
                    updated_source=working[path],
                    changes=("composed constants census",),
                )
                for path in sorted(changed)
                if sources[path] != working[path]
            )
        )

    @classmethod
    def _verify_phase_sequences(
        cls,
        sources: Mapping[Path, str],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        phases: Sequence[c.Infra.SemanticCutoverPhase],
    ) -> p.Result[bool]:
        """Verify both corrective phases against one proposed or published state.

        Returns:
            The first phase failure or the verified joint fixed point.

        """
        for phase in phases:
            fixed_point = cls._check_residue(
                phase,
                u.Infra.plan_semantic_cutover(
                    phase,
                    import_normalizer=u.Infra.normalize_import_source,
                    rope_workspace=rope_workspace,
                    sources=sources,
                ),
            )
            if fixed_point.failure:
                return fixed_point
        return r[bool].ok(value=True)

    @classmethod
    def source_fingerprint[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
    ) -> tuple[tuple[str, str], ...]:
        """Identify the complete governed source state between mod phases.

        Returns:
            The resulting ``tuple[tuple[str, str], ...]``.

        """
        return tuple(
            (path.as_posix(), u.Cli.sha256_bytes(source.encode(c.DEFAULT_ENCODING)))
            for path, source in sorted(cls.source_inventory(root, preflight).items())
        )

    @classmethod
    def relocation_findings[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> tuple[p.Infra.DeclarationRelocationFinding, ...]:
        """Return every payload declaration whose relocation owner is unresolved.

        Returns:
            One finding per unresolved declaration, naming its expected owner.

        """
        return u.Infra.declaration_relocation_findings(
            rope_workspace,
            cls.source_inventory(root, preflight),
        )

    @classmethod
    def publish_planned_edits(
        cls,
        root: Path,
        edits: Sequence[p.Infra.SemanticMigrationEdit],
        *,
        validator: Callable[[Path], p.Result[bool]] | None = None,
    ) -> p.Result[bool]:
        """Compose a complete edit batch and publish through the semantic owner.

        Args:
            root: Repository root governing the publication.
            edits: The complete validated edit batch to compose.
            validator: Optional staged-candidate validator.

        Returns:
            Whether the accepted batch contains source changes.

        """
        original: MutableMapping[Path, str | None] = {}
        for edit in edits:
            if edit.file_path not in original:
                original[edit.file_path] = edit.original_source
        # A creation (original None) starts absent from the working view.
        working: MutableMapping[Path, str] = {
            path: source for path, source in original.items() if source is not None
        }
        changed: set[Path] = set()
        retired: t.Infra.RopeMutablePaths = set()
        cls.apply_plan(working, edits, changed, retirements=retired)
        return cls._publish(
            root,
            original,
            {path: None if path in retired else working[path] for path in changed},
            validator=validator,
        ).map(lambda accepted: bool(changed) and accepted)

    @classmethod
    def apply[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[bool]:
        """Apply every semantic cutover selected by the canonical mod circuit.

        Every planner failure (per module) is returned as a failed Result so the
        mod circuit reports it without a traceback and publishes nothing.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        authority = Path(rope_workspace.rope_project.root.real_path)
        with (
            u.Infra.open_project(
                authority, project_roots=u.Infra.import_project_roots(root)
            ) as live,
            closing(
                u.Infra.planned_project(live, election=u.Infra.native_election(live))
            ) as source_project,
            FlextInfraRopeWorkspace.open_workspace(
                root, rope_repository_root=authority, source_project=source_project
            ) as captured,
        ):
            # Contract normalization admits model envelopes through the
            # composition-owned checker, which the captured graph must carry.
            captured.model_envelope_checker = rope_workspace.model_envelope_checker
            original = cls.source_inventory(
                root, preflight, source_project=source_project
            )
            planned = cls.plan_semantic_edits(root, preflight, captured, original)
            if planned.failure:
                return r[bool].from_failure(planned)
        return cls._publish(
            root,
            original,
            {
                edit.file_path: None if edit.retire_file else edit.updated_source
                for edit in planned.value
            },
            validator=partial(
                cls._validate_candidate,
                preflight=preflight,
                workspace_factory=workspace_factory,
                reports_root=root,
            ),
        )

    @classmethod
    def plan_semantic_edits[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        original: Mapping[Path, str],
        *,
        phases: frozenset[c.Infra.SemanticCutoverPhase] | None = None,
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Compose semantic phases on planned bytes without publishing originals.

        ``phases`` restricts the cutover loop to a selected theme's phases;
        ``None`` composes every phase of the complete catalog.

        Returns:
            Complete edits relative to the supplied planned input, or its first failure.

        """
        result_type = r[tuple[p.Infra.SemanticMigrationEdit, ...]]
        if not original:
            return result_type.fail("semantic cutover has no source inventory")
        rope_workspace.semantic_rename_planner = FlextInfraCodemodRenameSymbols
        working = dict(original)
        changed: set[Path] = set()
        retired: t.Infra.RopeMutablePaths = set()

        # Phase 0: Import alignment (rope-native; toggle in tooling.yaml).
        # The original authority remains physical; every phase sees the latest
        # planned bytes through the authenticated Rope overlay.
        alignment = cls._phase_import_alignment(
            root,
            {
                path: source
                for path, source in working.items()
                if path.is_relative_to(root)
            },
            rope_workspace,
        )
        if alignment.failure:
            return result_type.from_failure(alignment)
        cls.apply_plan(working, alignment.value, changed)

        # Phase 1: Future annotations
        future_annotations = cls._phase_future_annotations(root, preflight, working)
        cls.apply_plan(working, future_annotations, changed)
        counts: MutableMapping[str, int] = {
            "import_alignment_files": len(alignment.value),
            "future_annotations": len(future_annotations),
        }
        residue = cls._future_annotation_residue(
            root, preflight, working, changed=bool(future_annotations)
        )
        # Class nesting establishes declaration scopes before references are
        # normalized; aliases and private imports follow those owner changes.
        for phase in c.Infra.SemanticCutoverPhase:
            if residue.failure:
                return result_type.from_failure(residue)
            if phases is not None and phase not in phases:
                continue
            cli.display_text(f"mod: plan semantic phase {phase}")
            phase_sources = cls._semantic_phase_sources(root, phase, working)
            planned = u.Infra.plan_semantic_cutover(
                phase,
                import_normalizer=u.Infra.normalize_import_source,
                rope_workspace=rope_workspace,
                sources=phase_sources,
                findings=preflight.entries,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            cls.apply_plan(working, planned.value, changed, retirements=retired)
            counts[phase] = len(planned.value)
            if planned.value:
                residue = cls._check_residue(
                    phase,
                    u.Infra.plan_semantic_cutover(
                        phase,
                        import_normalizer=u.Infra.normalize_import_source,
                        rope_workspace=rope_workspace,
                        sources={path: working[path] for path in phase_sources},
                        findings=preflight.entries,
                    ),
                )
            if phase is c.Infra.SemanticCutoverPhase.CLASS_NESTING:
                residue = cls._deferred_phase_residue(root, working, changed, counts)
            if residue.failure:
                return result_type.from_failure(residue)
            cli.display_text(f"mod: semantic phase {phase} complete")
        cli.display_text(
            "mod: semantic cutover "
            + " ".join(f"{name}={count}" for name, count in counts.items()),
        )
        return cls._check_definition_time(original, working, changed).map(
            lambda _: tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=original[path],
                    updated_source=working[path],
                    retire_file=path in retired,
                    changes=("composed semantic cutover",),
                )
                for path in sorted(changed)
            )
        )

    @classmethod
    def _future_annotation_residue[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        working: MutableMapping[Path, str],
        *,
        changed: bool,
    ) -> p.Result[bool]:
        """Recheck annotations only when the first pass actually changed sources.

        Returns:
            The exact annotation-residue result.

        """
        if not changed:
            return r[bool].ok(value=True)
        return cls._check_residue(
            "future-annotations",
            r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(
                cls._phase_future_annotations(root, preflight, working)
            ),
        )

    @staticmethod
    def _semantic_phase_sources(
        root: Path,
        phase: c.Infra.SemanticCutoverPhase,
        working: Mapping[Path, str],
    ) -> Mapping[Path, str]:
        """Restrict local-only phases while retaining shared views for other phases.

        Returns:
            The phase's elected source view.

        """
        if phase in {
            # The model-field contract cure is owned by the repository being
            # modified: a consumer run must not plan edits in its siblings.
            c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
            c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
            c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT,
            c.Infra.SemanticCutoverPhase.MODULE_END,
            c.Infra.SemanticCutoverPhase.NOTICE_LAST,
        }:
            return {
                path: source
                for path, source in working.items()
                if path.is_relative_to(root)
            }
        return working

    @classmethod
    def _validate_candidate[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        *,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
        reports_root: Path,
    ) -> p.Result[bool]:
        """Check the same public contract in a staged or published workspace.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        with workspace_factory(root, None) as workspace:
            return cls._validate_published(root, preflight, workspace, reports_root)

    @classmethod
    def _validate_published[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        reports_root: Path,
    ) -> p.Result[bool]:
        """Re-read, refresh, and verify the fixed point of the published sources.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        published = dict(cls.source_inventory(root, preflight))
        rope_workspace.refresh()
        return (
            cls
            ._verify_fixed_point(
                root,
                published,
                preflight,
                rope_workspace,
            )
            .flat_map(
                lambda _: cls._check_residue(
                    "import-alignment",
                    cls._phase_import_alignment(root, published, rope_workspace),
                ),
            )
            .flat_map(
                lambda _: (
                    FlextInfraWorkspaceChecker(repository_root=root)
                    .execute_payload(
                        m.Infra.RunCommand(
                            repository_root=root,
                            reports_dir=str(
                                m.Infra.RunCommand(
                                    repository_root=reports_root
                                ).reports_dir_path
                            ),
                            projects=tuple(
                                str(project.relative_to(root))
                                for project in sorted(
                                    u.Infra.governed_project_roots(root)
                                )
                            ),
                            gates=(c.Infra.LINT, c.Infra.PYREFLY, c.Infra.FRESH_IMPORT),
                        ),
                    )
                    .map(lambda _: True)
                ),
            )
        )

    @classmethod
    def _phase_import_alignment(
        cls,
        root: Path,
        working: Mapping[Path, str],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan rope-native absolute import alignment when tooling enables it.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]``.

        """
        planned_edits = r[tuple[p.Infra.SemanticMigrationEdit, ...]]
        if not config.Infra.tooling.mod.phases.import_alignment:
            return planned_edits.ok(())
        planned = u.Infra.align_module_imports(
            rope_project=rope_workspace.rope_project,
            repository_root=root.resolve(),
            index=rope_workspace.workspace_index,
        )
        if planned.failure:
            return planned_edits.from_failure(planned)
        return planned_edits.ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=plan.path,
                    original_source=working[plan.path],
                    updated_source=(plan.desired_content or b"").decode(
                        c.DEFAULT_ENCODING,
                    ),
                )
                for plan in planned.value
                if plan.path in working
            ),
        )

    @staticmethod
    def _phase_future_annotations[FindingT: p.Infra.ModOccurrence](
        root: Path,
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        working: MutableMapping[Path, str],
    ) -> tuple[p.Infra.SemanticMigrationEdit, ...]:
        """Plan the future-annotations phase; the pipeline applies the edits.

        Returns:
            The resulting ``tuple[p.Infra.SemanticMigrationEdit, ...]``.

        Raises:
            ValueError: If authenticated source disappeared during mod preflight.

        """
        future_annotations: list[p.Infra.SemanticMigrationEdit] = []
        for file_path in sorted({
            (root / finding.file).resolve()
            for finding in preflight.entries
            if finding.rule_id == "require-future-annotations"
        }):
            original_source = working.get(file_path)
            if original_source is None:
                state = u.Cli.atomic_read_binary_file_state(
                    file_path,
                    required=True,
                ).unwrap()
                content = state.content
                if content is None:
                    msg = (
                        "authenticated source disappeared during mod preflight: "
                        f"{file_path}"
                    )
                    raise ValueError(msg)
                original_source = content.decode(c.DEFAULT_ENCODING)
                working[file_path] = original_source
            updated_source = u.Infra.ensure_future_annotations(original_source)
            if updated_source != original_source:
                future_annotations.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=file_path,
                        original_source=original_source,
                        updated_source=updated_source,
                        changes=("inserted canonical future annotations import",),
                    ),
                )
        return tuple(future_annotations)

    @staticmethod
    def _check_residue(
        phase: str,
        planned: p.ResultView[tuple[p.Infra.SemanticMigrationEdit, ...]],
    ) -> p.Result[bool]:
        """Reject a replan failure or edits replanned by a completed phase.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if planned.failure:
            return r[bool].from_failure(planned)
        if planned.value:
            files = ", ".join(edit.file_path.as_posix() for edit in planned.value)
            return r[bool].fail(
                f"{phase} phase left residue after application: {files}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _check_definition_time(
        original: Mapping[Path, str],
        working: Mapping[Path, str],
        changed: set[Path],
    ) -> p.Result[bool]:
        """Reject a plan whose class suites would raise NameError at import.

        A rewrite that names a class inside its own suite, or reads an
        enclosing class member from a nested suite, still parses and passes
        every replan, so the fixed point alone cannot see it. Only errors the
        original source did not already carry are attributed to the plan.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        broken: list[str] = []
        for path in sorted(changed):
            before = frozenset(u.Infra.definition_time_name_errors(original[path]))
            broken.extend(
                f"{path}: {error}"
                for error in u.Infra.definition_time_name_errors(working[path])
                if error not in before
            )
        if broken:
            return r[bool].fail(
                "semantic plan introduces definition-time NameError(s); nothing "
                f"published for mandatory owner repair: {'; '.join(broken)}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _verify_fixed_point[FindingT: p.Infra.ModOccurrence](
        cls,
        root: Path,
        working: MutableMapping[Path, str],
        preflight: p.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Replan every phase against the proposed or reread published sources.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        edits = r[tuple[p.Infra.SemanticMigrationEdit, ...]]
        verified = cls._check_residue(
            "future-annotations",
            edits.ok(cls._phase_future_annotations(root, preflight, working)),
        ).flat_map(
            lambda _: cls._check_residue(
                "deferred-models",
                edits.ok(cls._deferred_model_edits(working)),
            ),
        )
        for phase in c.Infra.SemanticCutoverPhase:
            if verified.failure:
                return verified
            verified = cls._check_residue(
                phase,
                u.Infra.plan_semantic_cutover(
                    phase,
                    import_normalizer=u.Infra.normalize_import_source,
                    rope_workspace=rope_workspace,
                    sources=working,
                    findings=preflight.entries,
                ),
            )
        return verified

    @staticmethod
    def source_inventory[FindingT: p.Infra.ModOccurrence](
        root: Path,
        _preflight: p.Infra.ModOccurrenceReport[FindingT],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> Mapping[Path, str]:
        """Read the canonical governed Python inventory used by native scanning.

        Returns:
            The resulting ``Mapping[Path, str]``.

        Raises:
            ValueError: If authenticated source disappeared during mod preflight.

        """
        del _preflight
        root = root.resolve()
        # Findings cannot introduce foreign or generated paths into semantic input.
        paths = {
            root / target
            for target in u.Infra.ast_grep_scan_targets(
                root, source_project=source_project
            )
        }
        sources: MutableMapping[Path, str] = {}
        for path in sorted(paths):
            state = (
                source_project.source_state(path, required=True)
                if source_project is not None
                else u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            )
            content = state.content
            if content is None:
                msg = f"authenticated source disappeared during mod preflight: {path}"
                raise ValueError(msg)
            sources[path] = content.decode(c.DEFAULT_ENCODING)
        return sources

    @classmethod
    def _deferred_phase_residue(
        cls,
        root: Path,
        working: MutableMapping[Path, str],
        changed: set[Path],
        counts: MutableMapping[str, int],
    ) -> p.Result[bool]:
        """Apply the deferred-model pass and prove it reached its fixed point.

        Args:
            root: Repository root scoping the deferred normalization.
            working: The planned bytes mutated in place by the deferred edits.
            changed: Accumulator receiving the paths the pass changed.
            counts: Phase counters updated with the deferred edit count.

        Returns:
            The deferred-model residue check, or acceptance when none apply.

        """
        deferred = cls._deferred_model_edits({
            path: source
            for path, source in working.items()
            if path.is_relative_to(root)
        })
        cls.apply_plan(working, deferred, changed)
        counts["deferred_models"] = len(deferred)
        if not deferred:
            return r[bool].ok(value=True)
        return cls._check_residue(
            "deferred-models",
            r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(
                cls._deferred_model_edits({
                    path: source
                    for path, source in working.items()
                    if path.is_relative_to(root)
                })
            ),
        )

    @staticmethod
    def _deferred_model_edits(
        sources: Mapping[Path, str],
    ) -> tuple[p.Infra.SemanticMigrationEdit, ...]:
        """Normalize every handwritten canonical model source from its AST.

        Returns:
            The resulting ``tuple[p.Infra.SemanticMigrationEdit, ...]``.

        """
        edits: list[p.Infra.SemanticMigrationEdit] = []
        models = u.Infra.facade_family_declared_by(c.Infra.MODELS_PY)
        for path, source in sorted(sources.items()):
            if source.startswith("# AUTO-GENERATED FILE"):
                continue
            if (
                path.name not in models.file_names
                and not models.directories.intersection(path.parts)
            ):
                continue
            updated = u.Infra.normalize_deferred_self_references(source)
            if updated != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=source,
                        updated_source=updated,
                        changes=("normalized definition-time model references",),
                    ),
                )
        return tuple(edits)

    @classmethod
    def _publish(
        cls,
        root: Path,
        original: Mapping[Path, str | None],
        updated: Mapping[Path, str | None],
        *,
        validator: Callable[[Path], p.Result[bool]] | None = None,
    ) -> p.Result[bool]:
        """Bind every update to its destination once and publish the batch.

        Args:
            root: Repository root governing the publication.
            original: The original sources the plan was derived from; ``None``
                declares a creation whose destination must be absent.
            updated: The desired bytes per path, or ``None`` to retire a file.
            validator: Optional acceptance gate over the published tree.

        Returns:
            Whether the batch was published, or the first failure.

        """
        if not updated:
            return r[bool].ok(value=False)
        plans: list[p.Infra.CodegenFilePlan] = []
        for path in sorted(updated, key=cls._path_key):
            project_root = u.Infra.project_root(path)
            if project_root is None:
                return r[bool].fail(f"semantic target has no governed project: {path}")
            before = u.Infra.codegen_target_snapshot(path)
            if before.failure:
                return r[bool].from_failure(before)
            state = before.value
            expected = original.get(path)
            if path in original and expected is None and state.content is not None:
                return r[bool].fail(f"semantic creation destination exists: {path}")
            if expected is not None and (
                state.content is None
                or state.content.decode(c.DEFAULT_ENCODING) != expected
            ):
                return r[bool].fail(f"source changed after semantic preflight: {path}")
            source = updated[path]
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=project_root.resolve(),
                    path=path.resolve(),
                    before=state,
                    desired_content=None
                    if source is None
                    else source.encode(c.DEFAULT_ENCODING),
                    desired_mode=None
                    if source is None
                    else state.mode
                    if state.mode is not None
                    else config.Infra.codegen.modes.file_default,
                )
            )
        return (
            FlextInfraTransformersSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=root,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=tuple(
                        sorted({
                            *u.Infra.governed_project_roots(root),
                            *(plan.project for plan in plans),
                        })
                    ),
                    validator=validator,
                ),
            ).map(lambda _: True)
        )

    @staticmethod
    def _path_key(path: Path) -> tuple[bool, str]:
        """Sort consumers before the public API owner in a typed key.

        Returns:
            The resulting ``tuple[bool, str]``.

        """
        return (path.name == c.Infra.API_PY, path.as_posix())


__all__: list[str] = ["FlextInfraCodemodSemanticApply"]
