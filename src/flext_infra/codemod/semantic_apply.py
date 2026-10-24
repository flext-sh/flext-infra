"""Guarded semantic phase for detection-only ``make mod`` findings.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import keyword
import operator
import re
from collections.abc import Callable, Generator, MutableMapping
from contextlib import ExitStack, closing, contextmanager
from functools import partial
from pathlib import Path

from flext_cli import cli

from flext_infra import c, config, m, p, r, t, u
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod._rename_sources import FlextInfraRenameSources
from flext_infra.codemod._rename_symbols import FlextInfraRenameSymbols
from flext_infra.refactor import FlextInfraImportNormalization
from flext_infra.transformers import FlextInfraSemanticPublication
from flext_infra.workspace import FlextInfraRopeWorkspace


class FlextInfraCodemodSemanticApply(FlextInfraRenameSources):
    """Plan semantic cutovers, preflight the batch, then publish guarded files."""

    @classmethod
    def publish_rename_plan(
        cls,
        request: m.Infra.SemanticRenamePlanCommand,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[m.Infra.SemanticRenamePlan]:
        """Plan, authenticate and atomically publish an inventory-derived artifact.

        Returns:
            The published plan, or the original containment, planning or write failure.

        """
        root = request.repository_root.resolve()
        target = (root / request.output).resolve()
        if not target.is_relative_to(root):
            return r[m.Infra.SemanticRenamePlan].fail(
                "rename plan output escapes workspace"
            )
        observed = u.Cli.atomic_read_binary_file_state(root / request.output)
        if observed.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(observed)
        selections = m.Infra.SemanticRenameSelections.model_validate_json(
            request.decisions
        )
        with workspace_factory(root, None) as workspace:
            planned = cls.build_rename_plan(root, workspace, selections)
        if planned.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(planned)
        content = cls._validated_rename_content(
            observed.value, planned.value, target, root
        )
        if content.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(content)
        lock = u.Infra.mutation_lock_path(root)
        if lock.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(lock)
        return u.Cli.publish_file_changes(
            (
                m.Cli.FileChange(
                    path=target,
                    before=observed.value,
                    desired_content=f"{content.value}\n".encode(c.DEFAULT_ENCODING),
                    desired_mode=observed.value.mode
                    if observed.value.content is not None
                    else config.Infra.codegen.modes.file_default,
                ),
            ),
            lock_path=lock.value,
        ).map(lambda _written: planned.value)

    @staticmethod
    def _validated_rename_content(
        before: m.Cli.AtomicFileState,
        planned: m.Infra.SemanticRenamePlan,
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
            return r[str].fail("rename plan output aliases a governed candidate input")
        if before.content is not None:
            previous = m.Infra.SemanticRenamePlan.model_validate_json(before.content)
            if (previous.candidate.workspaces or (previous.candidate.workspace,))[
                0
            ] != u.Infra.import_project_roots(root)[0].resolve():
                return r[str].fail("rename plan output belongs to another workspace")
        content = planned.model_dump_json(indent=2, round_trip=True)
        if (
            m.Infra.SemanticRenamePlan.model_validate_json(content).model_dump_json(
                indent=2, round_trip=True
            )
            != content
        ):
            return r[str].fail("rename artifact did not round-trip exactly")
        return r[str].ok(value=content)

    @classmethod
    def build_rename_plan(
        cls,
        root: Path,
        workspace: p.Infra.RopeWorkspaceDsl,
        selections: m.Infra.SemanticRenameSelections,
        *,
        source_plan: m.Infra.SemanticSourcePlan | None = None,
    ) -> p.Result[m.Infra.SemanticRenamePlan]:
        """Produce exact native edits and closure from explicit domain selections.

        Returns:
            A reversible authenticated artifact, without changing live sources.

        """
        if not selections.decisions:
            return r[m.Infra.SemanticRenamePlan].fail(
                "semantic rename requires an explicit naming decision"
            )
        elected = cls._source_scopes(root, selections.consumer_roots)
        if elected.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(elected)
        scopes = elected.value
        if source_plan is not None:
            if (
                source_plan.candidate.workspaces or (source_plan.candidate.workspace,)
            ) != scopes:
                return r[m.Infra.SemanticRenamePlan].fail(
                    "semantic rename source receipt belongs to another scope"
                )
            # A persisted plan is rebuilt only over the bytes it observed.
            current = u.Cli.atomic_verify_binary_file_states(
                source_plan.candidate.inputs
            )
            if current.failure:
                return r[m.Infra.SemanticRenamePlan].from_failure(current)
        return cls._build_native_rename_plan(workspace, selections, scopes)

    @classmethod
    def build_source_plan(
        cls,
        root: Path,
        consumer_roots: t.VariadicTuple[Path] = (),
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Capture a native source campaign without creating a rename artifact.

        Returns:
            The complete authenticated source closure, without live effects.

        """
        return cls._source_scopes(root, consumer_roots).flat_map(
            lambda scopes: cls._build_native_source_plan(scopes, ()).map(
                operator.itemgetter(0)
            )
        )

    @classmethod
    def plan_module_names(
        cls,
        root: Path,
        source_plan: m.Infra.SemanticSourcePlan,
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Derive one package or module naming wave from authenticated inventory.

        Package waves precede module waves and never select parent and child together.
        Special double-underscore modules stay intact.
        Explicit consumer roots participate in reference rewriting, not discovery.

        Returns:
            The unchanged source plan or its native cross-root rename candidate.

        """
        if source_plan.candidate.updates:
            return r[m.Infra.SemanticSourcePlan].fail(
                "module naming discovery requires the original source seed"
            )
        sources = u.Infra.candidate_python_sources(
            source_plan.candidate, source_plan.candidate.inputs
        )
        with FlextInfraRopeWorkspace.open_workspace(
            root, rope_repository_root=root
        ) as workspace:
            packages = cls._package_naming_candidates(root, sources)
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
                return r[m.Infra.SemanticSourcePlan].ok(source_plan)
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
                return r[m.Infra.SemanticSourcePlan].from_failure(planned)
            return r[m.Infra.SemanticSourcePlan].ok(planned.value)

    @staticmethod
    def _module_naming_selection(
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        replacement: str,
        reason: str,
    ) -> m.Infra.SemanticRenameSelection:
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
        declaration = FlextInfraRenameSymbols.inventoried_declaration(
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

    @classmethod
    def _module_naming_candidates(
        cls,
        root: Path,
        sources: t.MappingKV[Path, str],
        workspace: p.Infra.RopeWorkspaceDsl,
    ) -> t.VariadicTuple[t.Pair[Path, str]]:
        """Select module names without changing the authenticated native sources.

        Returns:
            Introducing module paths and their unambiguous destination basenames.

        Raises:
            ValueError: If a stripped identifier or responsibility is invalid.

        """
        selected: list[t.Pair[Path, str]] = []
        for path in sorted(sources):
            name = path.stem
            if not path.is_relative_to(root.resolve()) or (
                name.startswith("__") and name.endswith("__")
            ):
                continue
            replacement = name.lstrip("_")
            part = re.search(r"_parts?(?:_?\d+)?$", name)
            if part is not None:
                owner = name[: part.start()]
                replacement = (
                    cls._module_responsibility_name(workspace, path, owner)
                    if part.group()[-1].isdigit()
                    else owner.lstrip("_")
                )
            if replacement == name:
                continue
            if not replacement.isidentifier() or keyword.iskeyword(replacement):
                msg = (
                    f"module naming has no valid public identifier: {path}; "
                    "unresolved semantic grouping requires an explicit responsibility"
                )
                raise ValueError(msg)
            selected.append((path, replacement))
        return tuple(selected)

    @staticmethod
    def _module_responsibility_name(
        workspace: p.Infra.RopeWorkspaceDsl, path: Path, owner: str
    ) -> str:
        """Derive a numbered fragment's responsibility from its native declaration.

        Returns:
            The introducing declaration's owner-relative snake-case suffix.

        Raises:
            ValueError: If the native source does not identify one responsibility.

        """
        declarations = tuple(
            item
            for item in workspace.objects(path, include_references=False)
            if item.kind in {"class", "function"} and item.scope_path == item.name
        )
        responsibility = ""
        if len(declarations) == 1:
            words = re.findall(
                r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+",
                declarations[0].name,
            )
            prefix = ""
            for index, word in enumerate(words):
                prefix += word.lower()
                if not owner.lstrip("_").replace("_", "").lower().startswith(prefix):
                    if index:
                        responsibility = "_".join(words[index:]).lower()
                    break
        if not responsibility:
            msg = (
                f"unresolved semantic grouping: {path}; numbered split requires "
                "one owner-relative responsibility from native source evidence"
            )
            raise ValueError(msg)
        return responsibility

    @staticmethod
    def _package_naming_candidates(
        root: Path,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[t.Pair[Path, str]]:
        """Select shallowest split packages owned by an actual facade declaration.

        Returns:
            Initializer paths and semantic destination basenames for one wave.

        Raises:
            ValueError: If split naming has no unambiguous facade responsibility.

        """
        selected: list[t.Pair[Path, str]] = []
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
                letter in u.Infra.public_export_names_source(sources[facade])
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
            if not owned:
                msg = (
                    f"unresolved semantic grouping: {directory}; split package "
                    "has no authenticated facade declaration owner"
                )
                raise ValueError(msg)
            selected.append((path, f"_{basename}"))
        return tuple(selected)

    @staticmethod
    def _source_scopes(
        root: Path,
        consumer_roots: t.VariadicTuple[Path],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Elect explicit non-overlapping native source scopes.

        Returns:
            The producer followed by its distinct declared consumer roots.

        """
        outcome = r[t.VariadicTuple[Path]]
        if any(not path.is_absolute() or not path.is_dir() for path in consumer_roots):
            return outcome.fail(
                "consumer roots must be existing absolute checkout roots"
            )
        scopes = tuple(
            dict.fromkeys(
                u.Infra.import_project_roots(path)[0].resolve()
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
        scopes: t.VariadicTuple[Path],
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Plan the source closure of the elected scopes without any update.

        Returns:
            The original source closure.

        """
        return FlextInfraStagedPackage.plan_sources(
            scopes[0],
            {},
            options=m.Infra.StageSourceOptions(
                workspaces=scopes if len(scopes) > 1 else (),
                inputs=tuple(
                    u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                    for path in dict.fromkeys(
                        project.resolve() / target
                        for scope in scopes
                        for project in u.Infra.import_project_roots(scope)
                        for target in u.Infra.ast_grep_scan_targets(project.resolve())
                    )
                ),
            ),
        )

    @staticmethod
    def _planning_election(
        live: p.Infra.RopeProject,
        source_folders: t.VariadicTuple[str],
        python_folders: t.VariadicTuple[str],
    ) -> m.Infra.RopeProjectElection:
        """Elect the multiproject source and interpreter folders of one plan.

        Returns:
            The election the overlay project resolves imports through.

        """
        return m.Infra.RopeProjectElection(
            source_folders=source_folders,
            ignored_resources=tuple(sorted(config.Infra.codegen.source_scan_ignored)),
            extension_modules=u.Infra.extension_module_names(live),
            python_path_folders=python_folders,
        )

    @classmethod
    def _build_native_rename_plan(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        selections: m.Infra.SemanticRenameSelections,
        scopes: t.VariadicTuple[Path],
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
        return cls._build_native_source_plan(scopes, decisions).map(
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
        scopes: t.VariadicTuple[Path],
        decisions: t.VariadicTuple[m.Infra.SemanticRenameDecision],
    ) -> p.Result[
        t.Pair[m.Infra.SemanticSourcePlan, t.VariadicTuple[t.Pair[Path, Path]]]
    ]:
        """Share native capture, planning and receipts across source campaigns.

        Returns:
            The authenticated candidate and its actual native module moves.

        """
        captured_sources = cls._source_closure(scopes)
        if captured_sources.failure:
            return r[
                t.Pair[m.Infra.SemanticSourcePlan, t.VariadicTuple[t.Pair[Path, Path]]]
            ].from_failure(captured_sources)
        baseline = captured_sources.value
        captured = m.Infra.CodemodBindingSnapshot(states=baseline.inputs)
        original = u.Infra.candidate_python_sources(baseline, captured.states)
        with ExitStack() as stack:
            declared_projects = tuple(
                dict.fromkeys(
                    project
                    for scope in scopes
                    for project in u.Infra.import_project_roots(scope)
                )
            )
            live = (
                stack.enter_context(
                    u.Infra.open_project(
                        baseline.workspace,
                        project_roots=declared_projects,
                    )
                ),
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
            updates, moves = FlextInfraRenameSymbols.plan_native_candidates(
                snapshots, original, decisions
            )
        staged_inputs = cls._staged_inputs(moves, captured.states)
        if staged_inputs.failure:
            return r[
                t.Pair[m.Infra.SemanticSourcePlan, t.VariadicTuple[t.Pair[Path, Path]]]
            ].from_failure(staged_inputs)
        return FlextInfraStagedPackage.plan_sources(
            scopes[0],
            updates,
            options=m.Infra.StageSourceOptions(
                workspaces=scopes if len(scopes) > 1 else (),
                modes={
                    target: state.mode
                    for source, target in moves
                    for state in staged_inputs.value
                    if state.path == source and state.mode is not None
                },
                inputs=staged_inputs.value,
            ),
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
        original: t.MappingKV[Path, str],
        updates: t.MappingKV[Path, str | None],
    ) -> t.VariadicTuple[m.Infra.SemanticMigrationEdit]:
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
        moves: t.SequenceOf[t.Pair[Path, Path]],
        base_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Authenticate native module destinations as absent before staging.

        Returns:
            The staged input states including every move destination, or the
            first destination that appeared before staging.

        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileState]]
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
        seed: m.Infra.SemanticSourcePlan,
        sources: t.MappingKV[Path, str],
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
                for project in u.Infra.import_project_roots(scope)
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
                u.Infra.open_project(candidate.workspace, project_roots=projects)
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
                        declared_files=cls._planned_files(root, candidate, sources),
                    )
                )
            )
            with FlextInfraRopeWorkspace.open_workspace(
                root,
                rope_repository_root=candidate.workspace,
                source_project=project,
                workspace_index=u.Infra.index_rope_workspace(project, root),
            ) as workspace:
                yield workspace

    @staticmethod
    def _planned_files(
        root: Path,
        candidate: m.Infra.StageSourcePlan,
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Declare every planned source that differs from its live destination.

        Returns:
            One plan per planned addition, rewrite, or retirement.

        """
        planned: list[m.Infra.CodegenFilePlan] = []
        for path, source in {**candidate.updates, **sources}.items():
            before = u.Infra.codegen_target_snapshot(path).unwrap()
            desired = None if source is None else source.encode(c.DEFAULT_ENCODING)
            if before.content == desired:
                continue
            planned.append(
                m.Infra.CodegenFilePlan(
                    project=u.Infra.project_root(path) or root,
                    path=path,
                    before=before,
                    desired_content=desired,
                    desired_mode=None
                    if desired is None
                    else candidate.modes.get(
                        path,
                        before.mode
                        if before.content is not None
                        else config.Infra.codegen.modes.file_default,
                    ),
                )
            )
        return tuple(planned)

    @classmethod
    def consume_rename_plan(
        cls,
        request: m.Infra.ModCommand,
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
            f"files={len(artifact.candidate.updates)} runtime=validated"
        )
        return r[bool].ok(value=True)

    @classmethod
    def publish_candidate(
        cls,
        root: Path,
        candidate: m.Infra.SemanticSourcePlan,
        *,
        publish: bool = True,
    ) -> p.Result[bool]:
        """Publish one rule-composed native candidate.

        Returns:
            The shared semantic publication's actual acceptance or failure.

        """
        return cls._publish_authenticated_source(root, candidate, publish=publish)

    @classmethod
    def load_rename_artifact(
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
    ) -> p.Result[bool]:
        """Re-derive, candidate-validate, and re-authenticate the artifact.

        Returns:
            The first verification failure, or the accepted candidate.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        root = u.Infra.import_project_roots(root)[0]
        artifact, driver = pair
        verified = cls.authenticate_rename_candidate(root, artifact, driver, workspace)
        if verified.failure:
            return verified
        return cls._publish_authenticated_source(
            root,
            artifact,
            publish=request.apply and not request.check and not request.dry_run_mode,
        )

    @classmethod
    def authenticate_rename_candidate(
        cls,
        root: Path,
        artifact: m.Infra.SemanticRenamePlan,
        driver: m.Cli.AtomicFileState,
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
            return r[bool].fail(
                "semantic rename artifact differs from current native plan; fields="
                + ", ".join(differences)
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _authenticate_rename_inputs(
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
        return r[bool].ok(value=True)

    @staticmethod
    def _publish_authenticated_source(
        root: Path,
        artifact: m.Infra.SemanticSourcePlan,
        *,
        publish: bool,
    ) -> p.Result[bool]:
        """Publish the candidate's planned effects through the shared publisher.

        Returns:
            The publication outcome mapped to the candidate acceptance.

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
        return FlextInfraSemanticPublication.publish_semantic_artifact_plans(
            plans,
            repository_root=u.Infra.import_project_roots(root)[0].resolve(),
            options=m.Infra.SemanticPublicationOptions(
                projection_roots=tuple(
                    sorted({
                        root,
                        *(u.Infra.project_root(path) or root for path in updates),
                    })
                ),
            ),
            publish=publish,
        ).map(lambda _: True)

    @classmethod
    def census_constants(
        cls,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        apply: bool,
        workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Compose declaration and constant consumers before census acceptance.

        Args:
            root: Repository root governing the census scope.
            rope_workspace: The native workspace DSL used for planning.
            apply: Whether the composed candidate is also published.
            workspace_factory: Validator workspace factory for staged candidates.

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
        cls.apply_plan(working, planned.value, changed)
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
                import_normalizer=FlextInfraImportNormalization.normalize_source,
                rope_workspace=rope_workspace,
                sources=working,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            cls.apply_plan(working, planned.value, changed)
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
                    import_normalizer=FlextInfraImportNormalization.normalize_source,
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
    def publish_planned_edits(
        cls,
        root: Path,
        edits: t.SequenceOf[p.Infra.SemanticMigrationEdit],
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
        original: t.MutableMappingKV[Path, str] = {}
        for edit in edits:
            if edit.file_path not in original:
                original[edit.file_path] = edit.original_source
        working = dict(original)
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
    def apply[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
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
            original = cls.source_inventory(
                root, preflight, source_project=source_project
            )
            planned = cls.plan(root, preflight, captured, original)
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
            cli.display_text(f"mod: plan semantic phase {phase}")
            phase_sources = cls._semantic_phase_sources(root, phase, working)
            planned = u.Infra.plan_semantic_cutover(
                phase,
                import_normalizer=FlextInfraImportNormalization.normalize_source,
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
                        import_normalizer=FlextInfraImportNormalization.normalize_source,
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
    def _future_annotation_residue[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        preflight: m.Infra.ModOccurrenceReport[FindingT],
        working: t.MutableMappingKV[Path, str],
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
            r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
                cls._phase_future_annotations(root, preflight, working)
            ),
        )

    @staticmethod
    def _semantic_phase_sources(
        root: Path,
        phase: c.Infra.SemanticCutoverPhase,
        working: t.MappingKV[Path, str],
    ) -> t.MappingKV[Path, str]:
        """Restrict local-only phases while retaining shared views for other phases.

        Returns:
            The phase's elected source view.

        """
        if phase in {
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
                    import_normalizer=FlextInfraImportNormalization.normalize_source,
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
            r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(
                cls._deferred_model_edits({
                    path: source
                    for path, source in working.items()
                    if path.is_relative_to(root)
                })
            ),
        )

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
    def apply_plan(
        sources: MutableMapping[Path, str],
        edits: t.SequenceOf[p.Infra.SemanticMigrationEdit],
        changed: set[Path],
        *,
        retirements: t.Infra.RopeMutablePaths | None = None,
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
    ) -> p.Result[bool]:
        """Bind every update to its destination once and publish the batch.

        Args:
            root: Repository root governing the publication.
            original: The original sources the plan was derived from.
            updated: The desired bytes per path, or ``None`` to retire a file.
            validator: Optional acceptance gate over the published tree.

        Returns:
            Whether the batch was published, or the first failure.

        """
        if not updated:
            return r[bool].ok(value=False)
        plans: list[m.Infra.CodegenFilePlan] = []
        for path in sorted(updated, key=cls._path_key):
            project_root = u.Infra.project_root(path)
            if project_root is None:
                return r[bool].fail(f"semantic target has no governed project: {path}")
            before = u.Infra.codegen_target_snapshot(path)
            if before.failure:
                return r[bool].from_failure(before)
            state = before.value
            if path in original and (
                state.content is None
                or state.content.decode(c.DEFAULT_ENCODING) != original[path]
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
                    desired_mode=None if source is None else state.mode,
                )
            )
        return FlextInfraSemanticPublication.publish_semantic_artifact_plans(
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

    @staticmethod
    def _path_key(path: Path) -> t.Pair[bool, str]:
        """Sort consumers before the public API owner in a typed key.

        Returns:
            The resulting ``t.Pair[bool, str]``.

        """
        return (path.name == c.Infra.API_PY, path.as_posix())


__all__: list[str] = ["FlextInfraCodemodSemanticApply"]
