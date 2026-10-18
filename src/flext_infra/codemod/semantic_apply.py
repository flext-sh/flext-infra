"""Guarded semantic phase for detection-only ``make mod`` findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Generator, MutableMapping
from contextlib import ExitStack, closing, contextmanager
from functools import partial
from pathlib import Path

from flext_cli import cli

from flext_infra import c, config, m, p, r, t, u
from flext_infra._utilities._rope.project import FlextInfraRopeProject
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod._rename_symbols import FlextInfraRenameSymbols
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.workspace import FlextInfraRopeWorkspace


class FlextInfraCodemodSemanticApply:
    """Plan semantic cutovers, preflight the batch, then publish guarded files."""

    @classmethod
    def build_rename_plan(
        cls,
        root: Path,
        workspace: p.Infra.RopeWorkspaceDsl,
        selections: m.Infra.SemanticRenameSelections,
    ) -> p.Result[m.Infra.SemanticRenamePlan]:
        """Produce exact native edits and closure from explicit domain selections.

        Returns:
            A reversible authenticated artifact, without changing live sources.

        """
        scope = u.Infra.import_project_roots(root)[0].resolve()
        consumers = tuple(
            dict.fromkeys(
                u.Infra.import_project_roots(path.resolve())[0].resolve()
                for path in selections.consumer_roots
                if u.Infra.import_project_roots(path.resolve())[0].resolve() != scope
            )
        )
        scopes = tuple(dict.fromkeys((scope, *consumers)))
        if any(
            not path.is_absolute() or not path.is_dir()
            for path in selections.consumer_roots
        ):
            return r[m.Infra.SemanticRenamePlan].fail(
                "consumer roots must be existing absolute checkout roots"
            )
        if any(
            left != right and left.is_relative_to(right)
            for left in scopes
            for right in scopes
        ):
            return r[m.Infra.SemanticRenamePlan].fail("rename scopes overlap")
        with ExitStack() as stack:
            producer_workspace = (
                workspace
                if workspace.rope_repository_root.resolve() == scope
                else stack.enter_context(FlextInfraRopeWorkspace.open_workspace(scope))
            )
            return cls._build_native_rename_plan(
                producer_workspace, selections, scopes, consumers
            )

    @classmethod
    def _build_native_rename_plan(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        selections: m.Infra.SemanticRenameSelections,
        scopes: t.VariadicTuple[Path],
        consumers: t.VariadicTuple[Path],
    ) -> p.Result[m.Infra.SemanticRenamePlan]:
        """Capture all elected sources before computing any native candidate.

        Returns:
            A single authenticated candidate spanning only the elected scopes.

        """
        decisions = tuple(
            m.Infra.SemanticRenameDecision(
                declaration=FlextInfraRenameSymbols.inventoried_declaration(
                    workspace, selection.qualified_name
                ),
                replacement_name=selection.replacement_name,
                reason=selection.reason,
                contracts=tuple(
                    FlextInfraRenameSymbols.inventoried_declaration(workspace, identity)
                    for identity in selection.contracts
                ),
            )
            for selection in selections.decisions
        )
        project_roots = {scope: u.Infra.import_project_roots(scope) for scope in scopes}
        inventories = {
            scope: dict(
                cls.source_inventory(scope, FlextInfraModGateEngine.recounted(()))
            )
            for scope in scopes
        }
        original = dict(
            sorted(
                (path, source)
                for inventory in inventories.values()
                for path, source in inventory.items()
            )
        )
        inputs = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in original
        )
        if any(
            state.content != original[state.path].encode(c.DEFAULT_ENCODING)
            for state in inputs
        ):
            return r[m.Infra.SemanticRenamePlan].fail(
                "rename inventory changed during capture"
            )
        bounded = FlextInfraStagedPackage.plan_sources(
            scopes[0],
            {},
            inputs=inputs,
            workspaces=scopes if len(scopes) > 1 else (),
        )
        if bounded.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(bounded)
        inputs = bounded.value.inputs
        captured = m.Infra.CodemodBindingSnapshot(states=inputs)
        epoch = u.Infra.codemod_source_epoch(captured)
        original = dict(epoch.sources)
        with ExitStack() as stack:
            declared_projects = tuple(
                dict.fromkeys(
                    project
                    for projects in project_roots.values()
                    for project in projects
                )
            )
            live = tuple(
                stack.enter_context(
                    u.Infra.open_project(
                        project,
                        project_roots=tuple(
                            owner
                            for owner in declared_projects
                            if owner.is_relative_to(project)
                        ),
                        consumer_root=project,
                    )
                )
                for project in declared_projects
            )
            import_folders = tuple(
                dict.fromkeys(
                    folder.real_path
                    for project in live
                    for folder in project.get_source_folders()
                )
            )
            path_folders = tuple(
                dict.fromkeys(
                    folder.real_path
                    for project in live
                    for folder in project.get_python_path_folders()
                    if folder.is_folder()
                )
            )
            snapshots = tuple(
                stack.enter_context(
                    closing(
                        FlextInfraRopeProject.from_atomic_reads(
                            project,
                            captured.states,
                            election=m.Infra.RopeProjectElection(
                                source_folders=tuple(
                                    folder.path
                                    for folder in project.get_source_folders()
                                ),
                                ignored_resources=tuple(
                                    u.type_adapter(list[str]).validate_python(
                                        project.get_prefs().get("ignored_resources"),
                                        strict=True,
                                    )
                                ),
                                extension_modules=tuple(
                                    sorted(
                                        u.type_adapter(set[str]).validate_python(
                                            project.get_pycore().extension_modules,
                                            strict=True,
                                        )
                                    )
                                ),
                                python_path_folders=tuple(
                                    dict.fromkeys((
                                        *import_folders,
                                        *path_folders,
                                    ))
                                ),
                            ),
                            sources=epoch.sources,
                        )
                    )
                )
                for project in live
            )
            updates, moves = FlextInfraRenameSymbols.plan_native_candidates(
                snapshots, original, decisions
            )
            source_directories, source_query_topology = (
                u.Cli.atomic_merge_directory_query_receipts(
                    tuple(
                        item
                        for project in snapshots
                        for item in project.consumed_source_directories()
                    ),
                    tuple(
                        item
                        for project in snapshots
                        for item in project.consumed_source_topology()
                    ),
                )
            )
            source_states = tuple(
                sorted(
                    m.Infra.CodemodBindingSnapshot(
                        states=(
                            *captured.states,
                            *(
                                state
                                for project in snapshots
                                for state in project.consumed_source_states()
                            ),
                        )
                    ).states,
                    key=lambda state: state.path,
                )
            )
            for project in snapshots:
                project.verify_source_states()
        edits = tuple(
            m.Infra.SemanticMigrationEdit(
                file_path=path,
                original_source=original[path],
                updated_source=source,
                changes=("native multiproject semantic rename",),
            )
            for path, source in sorted(updates.items())
            if path in original and source is not None
        )
        destinations = tuple(
            u.Cli.atomic_read_binary_file_state(target).unwrap()
            for _origin, target in moves
        )
        if any(state.content is not None for state in destinations):
            return r[m.Infra.SemanticRenamePlan].fail(
                "native module destination appeared before staging"
            )
        inputs = m.Infra.CodemodBindingSnapshot(states=(*inputs, *destinations)).states
        staged = FlextInfraStagedPackage.plan_sources(
            scopes[0],
            updates,
            inputs=inputs,
            workspaces=scopes if len(scopes) > 1 else (),
        )
        return staged.map(
            lambda candidate: m.Infra.SemanticRenamePlan(
                decisions=decisions,
                edits=edits,
                candidate=candidate.model_copy(
                    update={
                        "modes": {
                            target: state.mode
                            for source, target in moves
                            for state in inputs
                            if state.path == source and state.mode is not None
                        }
                    }
                ),
                consumer_roots=consumers,
                source_states=source_states,
                source_directories=source_directories,
                source_query_topology=source_query_topology,
                moves=moves,
            )
        )

    @staticmethod
    @contextmanager
    def planning_workspace(
        root: Path,
        seed: m.Infra.SemanticRenamePlan,
        sources: t.MappingKV[Path, str],
    ) -> Generator[p.Infra.RopeWorkspaceDsl]:
        """Elect a bounded native graph over original inputs and planned bytes.

        Yields:
            The existing workspace DSL with target selection separate from read scope.

        """
        candidate = seed.candidate
        scopes = candidate.workspaces or (candidate.workspace,)
        projects = tuple(
            dict.fromkeys(
                project
                for scope in scopes
                for project in u.Infra.import_project_roots(scope)
            )
        )
        originals = m.Infra.CodemodBindingSnapshot(
            states=(
                *candidate.inputs,
                *seed.source_states,
            )
        )
        epoch = u.Infra.codemod_source_epoch(originals)
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
                )
            )
            project = stack.enter_context(
                closing(
                    FlextInfraRopeProject.from_atomic_reads(
                        live,
                        originals.states,
                        election=m.Infra.RopeProjectElection(
                            source_folders=tuple(
                                Path(folder).relative_to(candidate.workspace).as_posix()
                                for folder in source_folders
                            ),
                            ignored_resources=tuple(
                                u.type_adapter(list[str]).validate_python(
                                    live.get_prefs().get("ignored_resources"),
                                    strict=True,
                                )
                            ),
                            extension_modules=tuple(
                                sorted(
                                    u.type_adapter(set[str]).validate_python(
                                        live.get_pycore().extension_modules,
                                        strict=True,
                                    )
                                )
                            ),
                            python_path_folders=python_folders,
                        ),
                        sources={
                            **{
                                path: source
                                for path, source in epoch.sources.items()
                                if path not in candidate.updates
                                or candidate.updates[path] is not None
                            },
                            **sources,
                        },
                        declared_files=tuple(
                            m.Infra.CodegenFilePlan(
                                project=u.Infra.project_root(path) or root,
                                path=path,
                                before=next(
                                    state
                                    for state in candidate.inputs
                                    if state.path == path
                                ),
                                desired_content=None
                                if source is None
                                else source.encode(c.DEFAULT_ENCODING),
                                desired_mode=None
                                if source is None
                                else candidate.modes.get(
                                    path,
                                    next(
                                        state.mode
                                        for state in candidate.inputs
                                        if state.path == path
                                    ),
                                ),
                                source_states=seed.source_states,
                                source_directories=seed.source_directories,
                                source_query_topology=seed.source_query_topology,
                            )
                            for path, source in candidate.updates.items()
                        ),
                    )
                )
            )
            with project.source_consumption() as selected:
                index = u.Infra.index_rope_workspace(project, root)
            yield stack.enter_context(
                FlextInfraRopeWorkspace.open_workspace(
                    root,
                    rope_repository_root=candidate.workspace,
                    source_project=project,
                    workspace_index=index,
                    index_receipt=selected.receipt(),
                )
            )
            project.verify_source_states()

    @classmethod
    def consume_rename_plan(
        cls,
        request: m.Infra.ModCommand,
        workspace: p.Infra.RopeWorkspaceDsl,
        source_preview: p.Infra.SourcePreview,
    ) -> p.Result[bool]:
        """Re-derive an artifact and validate its complete candidate before effects.

        Returns:
            The first authentication/runtime failure, or the accepted candidate.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        root = u.Infra.import_project_roots(root)[0]
        loaded = cls._load_rename_artifact(root, request)
        verified = loaded.flat_map(
            lambda pair: cls._verify_rename_artifact(
                request,
                workspace,
                pair,
                source_preview=source_preview,
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
            f"files={len(artifact.candidate.updates)} runtime=validated"
        )
        return r[bool].ok(value=True)

    @staticmethod
    def rename_selections(
        artifact: m.Infra.SemanticRenamePlan,
    ) -> m.Infra.SemanticRenameSelections:
        """Reconstruct execution intent without treating artifacts as rule authority.

        Returns:
            The original typed native selections and elected consumers.

        """
        return m.Infra.SemanticRenameSelections(
            decisions=tuple(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{item.declaration.module_name}.{item.declaration.scope_path}".rstrip(
                        "."
                    ),
                    replacement_name=item.replacement_name,
                    reason=item.reason,
                    contracts=tuple(
                        f"{part.module_name}.{part.scope_path}"
                        for part in item.contracts
                    ),
                )
                for item in artifact.decisions
            ),
            consumer_roots=artifact.consumer_roots,
        )

    @classmethod
    def publish_candidate(
        cls,
        root: Path,
        candidate: m.Infra.SemanticRenamePlan,
        *,
        publish: bool = True,
        source_analysis: p.Infra.SemanticSourceAnalysis | None = None,
    ) -> p.Result[bool]:
        """Publish one rule-composed native candidate under its original source epoch.

        Returns:
            The shared semantic publication's actual acceptance or failure.

        """
        current = FlextInfraStagedPackage.source_inputs_current(candidate.candidate)
        if current.failure:
            return current
        authenticated = u.Cli.atomic_verify_binary_file_states(candidate.source_states)
        if authenticated.failure:
            return authenticated
        return cls._publish_authenticated_rename(
            root,
            candidate,
            None,
            publish=publish,
            source_analysis=source_analysis,
        )

    @staticmethod
    def compose_candidate(
        candidate: m.Infra.SemanticRenamePlan,
        analysis: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.SemanticRenamePlan]:
        """Fold an existing phase's effects without replacing its physical originals.

        Returns:
            The updated staged view with the union of original source witnesses.
            The first original planning exception escapes unchanged.

        """
        result_type = r[m.Infra.SemanticRenamePlan]
        if analysis.exception is not None:
            raise analysis.exception
        if analysis.issues:
            return result_type.fail(
                "; ".join(issue.message for issue in analysis.issues)
            )
        originals = {state.path: state for state in candidate.candidate.inputs}
        known = {
            state.path: state
            for state in m.Infra.CodemodBindingSnapshot(
                states=(
                    *candidate.candidate.inputs,
                    *candidate.source_states,
                )
            ).states
        }
        updates = dict(candidate.candidate.updates)
        modes = dict(candidate.candidate.modes)
        for effect in analysis.files:
            if effect.before != known.setdefault(effect.path, effect.before):
                return result_type.fail(
                    f"phase replaced original physical evidence: {effect.path}"
                )
            originals.setdefault(effect.path, effect.before)
            updates[effect.path] = (
                None
                if effect.desired_content is None
                else effect.desired_content.decode(c.DEFAULT_ENCODING)
            )
            if effect.desired_mode is None:
                modes.pop(effect.path, None)
            else:
                modes[effect.path] = effect.desired_mode
        captured = m.Infra.CodemodBindingSnapshot(
            states=(
                *candidate.source_states,
                *analysis.inputs,
                *(effect.before for effect in analysis.files),
                *(state for effect in analysis.files for state in effect.source_states),
            )
        )
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            (
                *candidate.source_directories,
                *analysis.source_directories,
                *(
                    item
                    for effect in analysis.files
                    for item in effect.source_directories
                ),
            ),
            (
                *candidate.source_query_topology,
                *analysis.source_query_topology,
                *(
                    item
                    for effect in analysis.files
                    for item in effect.source_query_topology
                ),
            ),
        )
        return FlextInfraStagedPackage.plan_sources(
            candidate.candidate.workspace,
            updates,
            inputs=tuple(originals.values()),
            workspaces=candidate.candidate.workspaces,
            modes=modes,
        ).map(
            lambda stage: candidate.model_copy(
                update={
                    "candidate": stage,
                    "source_states": captured.states,
                    "source_directories": directories,
                    "source_query_topology": topology,
                }
            )
        )

    @classmethod
    def _load_rename_artifact(
        cls,
        root: Path,
        request: m.Infra.ModCommand,
    ) -> p.Result[t.Pair[m.Infra.SemanticRenamePlan, m.Cli.AtomicFileState]]:
        """Authenticate the semantic rename driver and parse its artifact.

        Returns:
            The first artifact failure, or the parsed plan with its driver state.

        """
        loaded = r[t.Pair[m.Infra.SemanticRenamePlan, m.Cli.AtomicFileState]]
        if request.rename_plan is None:
            return loaded.fail("semantic rename consumption requires an artifact")
        path = (root / request.rename_plan).resolve()
        if not path.is_relative_to(root):
            return loaded.fail("semantic rename artifact escapes workspace")
        driver = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
        if driver.content is None:
            return loaded.fail(f"semantic rename artifact disappeared: {path}")
        return loaded.ok((
            m.Infra.SemanticRenamePlan.model_validate_json(driver.content),
            driver,
        ))

    @classmethod
    def _verify_rename_artifact(
        cls,
        request: m.Infra.ModCommand,
        workspace: p.Infra.RopeWorkspaceDsl,
        pair: t.Pair[m.Infra.SemanticRenamePlan, m.Cli.AtomicFileState],
        *,
        source_preview: p.Infra.SourcePreview,
    ) -> p.Result[bool]:
        """Re-derive, candidate-validate, and re-authenticate the artifact.

        Returns:
            The first verification failure, or the accepted candidate.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        root = u.Infra.import_project_roots(root)[0]
        artifact, driver = pair
        guarded = cls._authenticate_rename_candidate(root, artifact, driver)
        if guarded.failure:
            return guarded
        rebuilt = cls.build_rename_plan(
            root,
            workspace,
            cls.rename_selections(artifact),
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
            return r[bool].fail(
                "semantic rename artifact differs from current native plan; fields="
                + ", ".join(differences)
            )
        # The publication owner consumes the complete semantic/projection group.
        del source_preview
        authenticated = u.Cli.atomic_verify_binary_file_states((
            driver,
            *artifact.source_states,
        ))
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        return cls._publish_authenticated_rename(
            root,
            artifact,
            driver,
            publish=request.apply and not request.check and not request.dry_run_mode,
        )

    @staticmethod
    def _authenticate_rename_candidate(
        root: Path,
        artifact: m.Infra.SemanticRenamePlan,
        driver: m.Cli.AtomicFileState,
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
        authenticated = u.Cli.atomic_verify_binary_file_states((
            driver,
            *artifact.source_states,
        ))
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        current = FlextInfraStagedPackage.source_inputs_current(artifact.candidate)
        if current.failure:
            return r[bool].from_failure(current)
        return r[bool].ok(value=True)

    @staticmethod
    def _publish_authenticated_rename(
        root: Path,
        artifact: m.Infra.SemanticRenamePlan,
        driver: m.Cli.AtomicFileState | None,
        *,
        publish: bool,
        source_analysis: p.Infra.SemanticSourceAnalysis | None = None,
    ) -> p.Result[bool]:
        """Publish the authenticated candidate through the guarded transaction.

        Returns:
            The publication outcome mapped to the candidate acceptance.

        """
        originals = {state.path: state for state in artifact.candidate.inputs}
        updates = artifact.candidate.updates
        moved_from = {target: source for source, target in artifact.moves}
        dependencies = m.Infra.CodemodBindingSnapshot(
            states=(
                *artifact.candidate.inputs,
                *artifact.source_states,
                *((driver,) if driver is not None else ()),
                *(
                    tuple(
                        m.Cli.AtomicFileState.model_validate(
                            state, from_attributes=True
                        )
                        for state in source_analysis.inputs
                    )
                    if source_analysis is not None
                    else ()
                ),
            )
        ).states
        directories, topology = u.Cli.atomic_merge_directory_query_receipts(
            (
                *artifact.source_directories,
                *(
                    tuple(
                        m.Cli.AtomicDirectoryInventory.model_validate(
                            receipt, from_attributes=True
                        )
                        for receipt in source_analysis.source_directories
                    )
                    if source_analysis is not None
                    else ()
                ),
            ),
            (
                *artifact.source_query_topology,
                *(
                    tuple(
                        m.Cli.AtomicDirectoryChainPlan.model_validate(
                            receipt, from_attributes=True
                        )
                        for receipt in source_analysis.source_query_topology
                    )
                    if source_analysis is not None
                    else ()
                ),
            ),
        )
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
                    else originals[moved_from.get(path, path)].mode
                ),
                source_states=dependencies,
                source_directories=directories,
                source_query_topology=topology,
                dependency_group=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            )
            for path, source in updates.items()
        )
        return FlextInfraSemanticPublication.publish_semantic_artifact_plans(
            plans,
            repository_root=u.Infra.import_project_roots(root)[0].resolve(),
            projection_roots=tuple(
                sorted({
                    root,
                    *(u.Infra.project_root(path) or root for path in updates),
                })
            ),
            dependency_group=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            publish=publish,
        ).map(lambda _: True)

    @classmethod
    def census_constants(
        cls,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        apply: bool,
        source_preview: p.Infra.SourcePreview,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose declaration and constant consumers before census acceptance.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        inventory: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence] = (
            m.Infra.ModOccurrenceReport(files=frozenset(), entries=())
        )
        original = cls.source_inventory(root, inventory)
        planned = cls.plan_census_constants(root, rope_workspace, sources=original)
        if planned.failure:
            return planned
        working = dict(original)
        changed: set[Path] = set()
        cls._apply_plan(working, planned.value, changed)
        if not apply:
            return planned
        # A no-op candidate still verifies its planned inventory. A nonempty
        # candidate keeps the exact union, even when normalization writes no bytes.
        project_roots = {u.Infra.project_root(path) for path in changed or original}
        if not project_roots or None in project_roots:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].fail(
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
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
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
        result_type = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
        if rope_workspace.repository_root.resolve() != root.resolve():
            return result_type.fail(
                "constants planner target differs from workspace selection"
            )
        for phase in phases:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope_workspace,
                sources=working,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            cls._apply_plan(working, planned.value, changed)
        if changed:
            verified = cls._verify_census_phases(working, rope_workspace, phases)
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
    def _verify_census_phases(
        cls,
        sources: t.MappingKV[Path, str],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        phases: t.SequenceOf[c.Infra.SemanticCutoverPhase],
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
                    rope_workspace=rope_workspace,
                    sources=sources,
                ),
            )
            if fixed_point.failure:
                return fixed_point
        return r[bool].ok(value=True)

    @classmethod
    def source_fingerprint[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
    ) -> t.VariadicTuple[t.Pair[str, str]]:
        """Identify the complete governed source state between mod phases.

        Returns:
            The resulting ``t.VariadicTuple[t.Pair[str, str]]``.

        """
        return tuple(
            (path.as_posix(), u.Cli.sha256_bytes(source.encode(c.DEFAULT_ENCODING)))
            for path, source in sorted(cls.source_inventory(root, preflight).items())
        )

    @classmethod
    def relocation_findings[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> t.VariadicTuple[m.Infra.DeclarationRelocationFinding]:
        """Return every payload declaration whose relocation owner is unresolved.

        Returns:
            One finding per unresolved declaration, naming its expected owner.

        """
        return u.Infra.declaration_relocation_findings(
            rope_workspace,
            cls.source_inventory(root, preflight),
        )

    @classmethod
    def plan_transaction_paths[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Return one immutable Rope callback for the mod loop's progress identity.

        Returns:
            One immutable Rope callback for the mod loop's progress identity.

        """
        original = cls.source_inventory(root, preflight)

        return u.Infra.plan_transaction_path_cutover(
            rope_workspace=rope_workspace,
            sources=original,
        )

    @classmethod
    def apply_transaction_paths(
        cls,
        root: Path,
        edits: t.VariadicTuple[m.Infra.SemanticMigrationEdit],
        *,
        source_preview: p.Infra.SourcePreview,
    ) -> None:
        """Publish the exact callback included in the existing progress fingerprint."""
        cls.publish_planned_edits(root, edits, source_preview=source_preview).unwrap()
        cli.display_text(f"mod: Rope transaction paths changed_files={len(edits)}")

    @classmethod
    def publish_planned_edits(
        cls,
        root: Path,
        edits: t.SequenceOf[p.Infra.SemanticMigrationEdit],
        *,
        source_preview: p.Infra.SourcePreview,
        validator: Callable[[Path], p.Result[bool]] | None = None,
    ) -> p.Result[bool]:
        """Compose a complete edit batch and publish through the semantic owner.

        Returns:
            Whether the accepted batch contains source changes.

        """
        original: t.MutableMappingKV[Path, str] = {}
        for edit in edits:
            if edit.file_path not in original:
                original[edit.file_path] = edit.original_source
        working = dict(original)
        changed: set[Path] = set()
        retired: t.Infra.RopeMutablePaths = set()
        inputs: t.MutableMappingKV[Path, p.Infra.SemanticSourceState] = {}
        cls._apply_plan(working, edits, changed, retirements=retired, inputs=inputs)
        return cls._publish(
            root,
            original,
            {path: None if path in retired else working[path] for path in changed},
            validator=validator,
            source_states=tuple(inputs.values()),
        ).map(lambda accepted: bool(changed) and accepted)

    @classmethod
    def apply[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        source_preview: p.Infra.SourcePreview,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[bool]:
        """Apply every semantic cutover selected by the canonical mod circuit.

        Every planner failure (per module) is returned as a failed Result so the
        mod circuit reports it without a traceback and publishes nothing.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        authority = Path(rope_workspace.rope_project.root.real_path)
        with u.Infra.facade_source_project(
            authority, project_roots=u.Infra.import_project_roots(root)
        ) as (source_project, consumed, _sources):
            with FlextInfraRopeWorkspace.open_workspace(
                root, rope_repository_root=authority, source_project=source_project
            ) as captured:
                original = cls.source_inventory(
                    root, preflight, source_project=source_project
                )
                planned = cls.plan(root, preflight, captured, original)
                if planned.failure:
                    return r[bool].from_failure(planned)
                states, directories, topology = consumed()
        # Exit the original capture before effects; publication keeps the same
        # receipts and rejects any drift between this verification and mutation.
        # These are observations only; normalized file plans are assembled below.
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
            source_states=tuple(
                state for edit in planned.value for state in edit.source_states
            ),
            source_analysis=m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=(),
                inputs=states,
                source_directories=directories,
                source_query_topology=topology,
            ),
        )

    @classmethod
    def plan[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        original: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose semantic phases on planned bytes without publishing originals.

        Returns:
            Complete edits relative to the supplied planned input, or its first failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
        if not original:
            return result_type.fail("semantic cutover has no source inventory")
        working = dict(original)
        changed: set[Path] = set()
        retired: t.Infra.RopeMutablePaths = set()
        inputs: t.MutableMappingKV[Path, p.Infra.SemanticSourceState] = {}
        if rope_workspace.rope_project.authenticated_sources:
            inputs.update({
                path: rope_workspace.rope_project.source_state(path, required=True)
                for path in original
            })

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
        cls._apply_plan(working, alignment.value, changed)

        # Phase 1: Future annotations
        future_annotations = cls._phase_future_annotations(root, preflight, working)
        cls._apply_plan(working, future_annotations, changed)
        counts: MutableMapping[str, int] = {
            "import_alignment_files": len(alignment.value),
            "future_annotations": len(future_annotations),
        }
        residue = r[bool].ok(value=True)
        if future_annotations:
            residue = cls._check_residue(
                "future-annotations",
                r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
                    cls._phase_future_annotations(root, preflight, working),
                ),
            )
        # Class nesting establishes declaration scopes before references are
        # normalized; aliases and private imports follow those owner changes.
        for phase in c.Infra.SemanticCutoverPhase:
            if residue.failure:
                return result_type.from_failure(residue)
            cli.display_text(f"mod: plan semantic phase {phase}")
            phase_sources = working
            if phase in {
                c.Infra.SemanticCutoverPhase.MODEL_FIELDS,
                c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT,
                c.Infra.SemanticCutoverPhase.MODULE_END,
                c.Infra.SemanticCutoverPhase.NOTICE_LAST,
            }:
                phase_sources = {
                    path: source
                    for path, source in working.items()
                    if path.is_relative_to(root)
                }
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope_workspace,
                sources=phase_sources,
                findings=preflight.entries,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            cls._apply_plan(
                working, planned.value, changed, retirements=retired, inputs=inputs
            )
            counts[phase] = len(planned.value)
            if planned.value:
                residue = cls._check_residue(
                    phase,
                    u.Infra.plan_semantic_cutover(
                        phase,
                        rope_workspace=rope_workspace,
                        sources={path: working[path] for path in phase_sources},
                        findings=preflight.entries,
                    ),
                )
            if phase is c.Infra.SemanticCutoverPhase.CLASS_NESTING:
                deferred = cls._deferred_model_edits({
                    path: source
                    for path, source in working.items()
                    if path.is_relative_to(root)
                })
                cls._apply_plan(working, deferred, changed)
                counts["deferred_models"] = len(deferred)
                if deferred:
                    residue = cls._check_residue(
                        "deferred-models",
                        r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
                            cls._deferred_model_edits({
                                path: source
                                for path, source in working.items()
                                if path.is_relative_to(root)
                            })
                        ),
                    )
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
                    source_states=tuple(inputs.values()),
                    changes=("composed semantic cutover",),
                )
                for path in sorted(changed)
            )
        )

    @classmethod
    def _validate_candidate[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        *,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
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
    def _validate_published[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
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
        working: t.MappingKV[Path, str],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan rope-native absolute import alignment when tooling enables it.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        planned_edits = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
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
    def _phase_future_annotations[FindingT: m.Infra.ModOccurrence](
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        working: MutableMapping[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Plan the future-annotations phase; the pipeline applies the edits.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SemanticMigrationEdit]``.

        Raises:
            ValueError: If authenticated source disappeared during mod preflight.

        """
        future_annotations: list[m.Infra.SemanticMigrationEdit] = []
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
        planned: p.ResultView[t.VariadicTuple[p.Infra.SemanticMigrationEdit]],
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
        original: t.MappingKV[Path, str],
        working: t.MappingKV[Path, str],
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
    def _verify_fixed_point[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        working: MutableMapping[Path, str],
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Replan every phase against the proposed or reread published sources.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        edits = r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]
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
                    rope_workspace=rope_workspace,
                    sources=working,
                    findings=preflight.entries,
                ),
            )
        return verified

    @staticmethod
    def source_inventory[FindingT: m.Infra.ModOccurrence](
        root: Path,
        _preflight: m.Infra.ModOccurrenceReport[FindingT],
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> t.MappingKV[Path, str]:
        """Read the canonical governed Python inventory used by native scanning.

        Returns:
            The resulting ``t.MappingKV[Path, str]``.

        Raises:
            ValueError: If authenticated source disappeared during mod preflight.

        """
        root = root.resolve()
        # Findings cannot introduce foreign or generated paths into semantic input.
        paths = {
            member / target
            for member in u.Infra.import_project_roots(root)
            for target in u.Infra.ast_grep_scan_targets(
                member, source_project=source_project
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

    @staticmethod
    def _deferred_model_edits(
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
        """Normalize every handwritten canonical model source from its AST.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.SemanticMigrationEdit]``.

        """
        edits: list[m.Infra.SemanticMigrationEdit] = []
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

    @staticmethod
    def _apply_plan(
        sources: MutableMapping[Path, str],
        edits: t.SequenceOf[p.Infra.SemanticMigrationEdit],
        changed: set[Path],
        *,
        retirements: t.Infra.RopeMutablePaths | None = None,
        inputs: t.MutableMappingKV[Path, p.Infra.SemanticSourceState] | None = None,
    ) -> None:
        """Compose validated edit plans in memory without partial effects.

        Raises:
            ValueError: If semantic plans disagree for.

        """
        for edit in edits:
            if edit.retire_file:
                if retirements is None or edit.updated_source:
                    msg = f"semantic retirement has no effect carrier: {edit.file_path}"
                    raise ValueError(msg)
                retirements.add(edit.file_path)
            if inputs is not None:
                for state in edit.source_states:
                    previous = inputs.get(state.path)
                    if previous is not None and previous != state:
                        msg = f"semantic plan changed its original source receipt: {state.path}"
                        raise ValueError(msg)
                    inputs[state.path] = state
            current = sources.get(edit.file_path)
            if current != edit.original_source:
                msg = f"semantic plans disagree for {edit.file_path}"
                raise ValueError(msg)
            sources[edit.file_path] = edit.updated_source
            changed.add(edit.file_path)

    @classmethod
    def _publish(
        cls,
        root: Path,
        original: t.MappingKV[Path, str],
        updated: t.MappingKV[Path, str | None],
        *,
        validator: Callable[[Path], p.Result[bool]] | None = None,
        source_states: t.SequenceOf[p.Infra.SemanticSourceState] = (),
        source_analysis: p.Infra.SemanticSourceAnalysis | None = None,
    ) -> p.Result[bool]:
        """Normalize and preflight every source before journaled publication.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if not updated:
            return r[bool].ok(False)
        retirement = any(source is None for source in updated.values())
        if retirement and source_analysis is None:
            return r[bool].fail(
                "semantic retirement requires its original native topology"
            )
        supplied = (
            *source_states,
            *(source_analysis.inputs if source_analysis is not None else ()),
        )
        inputs = m.Infra.CodemodBindingSnapshot(
            states=tuple(
                m.Cli.AtomicFileState.model_validate(state, from_attributes=True)
                for state in supplied
            )
        ).states
        states = {state.path: state for state in inputs}
        if any(
            path not in states
            or states[path].content != source.encode(c.DEFAULT_ENCODING)
            for path, source in original.items()
        ):
            return r[bool].fail("source changed after semantic preflight")
        if retirement and (
            source_analysis is None or not source_analysis.source_directories
        ):
            return r[bool].fail("semantic retirement has no original inventory witness")
        prepared = u.Infra.normalize_sources(
            root,
            {path: source for path, source in updated.items() if source is not None},
            inputs=inputs,
        )
        if prepared.failure:
            return r[bool].from_failure(prepared)
        dependencies = m.Infra.CodemodBindingSnapshot(
            states=(*inputs, *prepared.value.inputs)
        ).states
        directories = tuple(
            m.Cli.AtomicDirectoryInventory.model_validate(receipt, from_attributes=True)
            for receipt in (
                source_analysis.source_directories
                if source_analysis is not None
                else ()
            )
        )
        topology = tuple(
            m.Cli.AtomicDirectoryChainPlan.model_validate(receipt, from_attributes=True)
            for receipt in (
                source_analysis.source_query_topology
                if source_analysis is not None
                else ()
            )
        )
        plans = []
        for path in sorted(updated, key=cls._path_key):
            state = states[path]
            project_root = u.Infra.project_root(path)
            if project_root is None:
                return r[bool].fail(f"semantic target has no governed project: {path}")
            proposed = (
                prepared.value.updates[path] if updated[path] is not None else None
            )
            if updated[path] is not None and proposed is None:
                return r[bool].fail(
                    f"normalizer cannot invent a semantic retirement: {path}"
                )
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=project_root.resolve(),
                    path=path.resolve(),
                    before=state,
                    desired_content=proposed.encode(c.DEFAULT_ENCODING)
                    if proposed is not None
                    else None,
                    desired_mode=state.mode if proposed is not None else None,
                    source_states=dependencies,
                    source_directories=directories,
                    source_query_topology=topology,
                ),
            )
        return FlextInfraSemanticPublication.publish_semantic_artifact_plans(
            plans,
            repository_root=root,
            projection_roots=tuple(
                sorted({
                    *u.Infra.governed_project_roots(root),
                    *(plan.project for plan in plans),
                })
            ),
            dependency_group=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            validator=validator,
        ).map(lambda _: True)

    @staticmethod
    def _path_key(path: Path) -> t.Pair[bool, str]:
        """Sort consumers before the public API owner in a typed key.

        Returns:
            The resulting ``t.Pair[bool, str]``.

        """
        return (path.name == c.Infra.API_PY, path.as_posix())


__all__: list[str] = ["FlextInfraCodemodSemanticApply"]
