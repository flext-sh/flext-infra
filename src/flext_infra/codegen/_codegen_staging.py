"""Destination-local staging for generic generated-file plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import stat
from collections.abc import MutableMapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, check, codegen, m, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsFiles as files,
    FlextInfraMiseArtifactsProcess as process,
)
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions
from flext_infra.codegen.staged_package import FlextInfraStagedPackage

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenStaging:
    """Stage generated-file plans beside their live destinations."""

    _phases: ClassVar[frozenset[str]] = frozenset(c.Infra.CodegenStagedFilePhase)

    @classmethod
    def prepare_python_plans(
        cls,
        workspace: Path,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Prepare each owning project's joint bytes against its planned policy.

        Each project consumes its own complete Python and metadata plans. Shared
        read-only workspace context does not join independent publication groups.
        The publisher must keep each project's prepared metadata and Python in
        one component, preserving any explicitly declared cross-project groups.

        Returns:
            Prepared plans retaining their original authority and topology.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        projects = tuple(dict.fromkeys(plan.project for plan in plans))
        if len(projects) > 1:
            return cls._prepare_split_project_plans(workspace, plans, projects)
        if not any(
            plan.path.suffix in {".py", ".pyi"} and plan.desired_content is not None
            for plan in plans
        ):
            return result_type.ok(plans)
        return cls._prepare_single_project_plans(workspace, plans, projects[0])

    @classmethod
    def _prepare_split_project_plans(
        cls,
        workspace: Path,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        projects: t.VariadicTuple[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Prepare one independent component per declared owning project.

        Args:
            workspace: Shared read-only workspace root of every plan.
            plans: Plans of all components in their original order.
            projects: Distinct owning project roots in declaration order.

        Returns:
            Prepared plans joined back into their original order.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        prepared_by_path: MutableMapping[Path, m.Infra.CodegenFilePlan] = {}
        for project in projects:
            local = cls.prepare_python_plans(
                workspace, tuple(plan for plan in plans if plan.project == project)
            )
            if local.failure:
                return result_type.from_failure(local)
            prepared_by_path.update((plan.path, plan) for plan in local.value)
        return result_type.ok(tuple(prepared_by_path[plan.path] for plan in plans))

    @classmethod
    def _prepare_single_project_plans(
        cls,
        workspace: Path,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        project: Path,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Prepare one project's joint Python and metadata bytes together.

        Args:
            workspace: Shared read-only workspace root of the plans.
            plans: Plans of the single owning project.
            project: The one distinct owning project root.

        Returns:
            Prepared plans with their composed source states.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        sources = FlextInfraCodegenPreconditions.unique_states((
            *(state for plan in plans for state in plan.source_states),
            *(
                plan.before
                for plan in plans
                if isinstance(plan.before, m.Cli.AtomicFileState)
            ),
        ))
        if sources.failure:
            return result_type.from_failure(sources)
        prepared = u.Infra.normalize_sources(
            workspace,
            {
                plan.path: (
                    None
                    if plan.desired_content is None
                    else plan.desired_content.decode(c.DEFAULT_ENCODING)
                )
                for plan in plans
            },
            inputs=sources.value,
            workspaces=(project,) if not project.is_relative_to(workspace) else (),
        )
        if prepared.failure:
            return result_type.from_failure(prepared)
        inputs = FlextInfraCodegenPreconditions.unique_states((
            *sources.value,
            *prepared.value.inputs,
        ))
        if inputs.failure:
            return result_type.from_failure(inputs)
        return result_type.ok(
            tuple(
                plan.model_copy(
                    update={
                        "desired_content": (
                            None
                            if (content := prepared.value.updates[plan.path.resolve()])
                            is None
                            else content.encode(c.DEFAULT_ENCODING)
                        ),
                        "source_states": inputs.value,
                    }
                )
                for plan in plans
            )
        )

    @staticmethod
    def validate_python_plans(
        session: m.Infra.CodegenTransactionSession,
        staged_files: t.VariadicTuple[m.Infra.CodegenStagedFile],
        *,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        workspace: Path,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Admit exact composed staged bytes with every native default gate.

        Unchanged outputs enter the same runtime and read-only checker.
        Preparation never occurs inside this authenticated consumer.

        Returns:
            The original session, or the original runtime/checker failure.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        if not plans:
            return result_type.ok(session)
        planned = FlextInfraCodegenStaging._planned_candidate_sources(
            workspace,
            staged_files,
            plans,
            session,
        )
        if planned.failure:
            return result_type.from_failure(planned)
        projects = tuple(dict.fromkeys(plan.project for plan in plans))
        consume_source_runtime = (
            codegen.FlextInfraCodegenTransaction.consume_source_runtime
        )
        with TemporaryDirectory(prefix="flext-source-admission-reports-") as directory:

            def validate(root: Path) -> p.Result[bool]:
                for project in projects:
                    runtime_root = u.Infra.runtime_environment_dir(project).parent
                    consumed = consume_source_runtime(
                        planned.value,
                        root,
                        runtime_root,
                        project_root=project,
                    )
                    if consumed.failure:
                        return r[bool].from_failure(consumed)
                    relative = project.relative_to(planned.value.workspace)
                    candidate = root / relative
                    checked = check.FlextInfraWorkspaceChecker(
                        repository_root=candidate
                    ).execute_candidate(
                        m.Infra.RunCommand(
                            repository_root=candidate,
                            reports_dir=str(Path(directory) / relative),
                            check_only=True,
                        ),
                        planned.value,
                        project_root=project,
                    )
                    if checked.failure:
                        return r[bool].from_failure(checked)
                    if not checked.value:
                        return r[bool].fail(f"candidate check rejected: {project}")
                return r[bool].ok(value=True)

            checked = FlextInfraStagedPackage.consume_sources(planned.value, validate)
        if checked.failure:
            return result_type.from_failure(checked)
        return result_type.ok(session)

    @classmethod
    def _planned_candidate_sources(
        cls,
        workspace: Path,
        staged_files: t.VariadicTuple[m.Infra.CodegenStagedFile],
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        session: m.Infra.CodegenTransactionSession,
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Plan the composed candidate view consumed by native admission.

        Args:
            workspace: Shared read-only workspace root of the plans.
            staged_files: Already staged replacements to bind into the view.
            plans: Declared file effects of the prepared publication.

        Returns:
            The planned candidate sources, or the first planning failure.

        """
        result_type = r[m.Infra.StageSourcePlan]
        updates = cls._composed_candidate_updates(staged_files, plans)
        inputs = FlextInfraCodegenPreconditions.unique_states(
            tuple(state for plan in plans for state in plan.source_states)
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        current_inputs = (
            codegen.FlextInfraMiseArtifactsVerification.session_input_states(
                inputs.value, session
            )
        )
        if current_inputs.failure:
            return result_type.from_failure(current_inputs)
        projects = tuple(dict.fromkeys(plan.project for plan in plans))
        scopes: list[Path] = []
        for project in projects:
            scope = FlextInfraStagedPackage.workspace_root(project)
            if scope.failure:
                return result_type.from_failure(scope)
            if scope.value not in scopes:
                scopes.append(scope.value)
        planned = FlextInfraStagedPackage.plan_sources(
            workspace,
            updates,
            inputs=current_inputs.value,
            workspaces=tuple(
                scope
                for scope in scopes
                if not any(
                    scope != parent and scope.is_relative_to(parent)
                    for parent in scopes
                )
            ),
        )
        if planned.failure:
            return result_type.from_failure(planned)
        return planned

    @staticmethod
    def _composed_candidate_updates(
        staged_files: t.VariadicTuple[m.Infra.CodegenStagedFile],
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> dict[Path, str | None]:
        """Compose desired sources from declared effects and staged replacements.

        Args:
            staged_files: Already staged replacements to bind into the view.
            plans: Declared file effects of the prepared publication.

        Returns:
            Desired candidate sources keyed by live destination path.

        """
        updates = {
            plan.path: (
                None
                if plan.desired_content is None
                else plan.desired_content.decode(c.DEFAULT_ENCODING)
            )
            for plan in plans
            # A directory-chain preimage owns no staged bytes; only real file
            # effects (create/replace/retire) enter the composed source view.
            if not isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
            or plan.desired_content is not None
        }
        for staged in staged_files:
            replacement = staged.replacement
            if replacement is not None and replacement.content is not None:
                updates[staged.before.path] = replacement.content.decode(
                    c.DEFAULT_ENCODING
                )
        return updates

    @classmethod
    def stage_file_plans(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        phase: str,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        directories: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
        intents: t.VariadicTuple[m.Infra.CodegenStagingIntent] = (),
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]:
        """Stage one exact phase without changing any live destination.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]``.

        """
        result_type = r[tuple[m.Infra.CodegenStagedFile, ...]]
        if phase not in FlextInfraCodegenStaging._phases:
            return result_type.fail(f"unsupported generation phase: {phase}")
        changed = tuple(
            plan for plan in plans if u.Infra.codegen_file_requires_effect(plan)
        )
        paths = tuple(plan.path for plan in changed)
        if len(set(paths)) != len(paths):
            return result_type.fail(f"duplicate {phase} generation destination")
        verified = cls.plan_file_staging(
            layout,
            phase,
            changed,
            directories=directories,
        )
        if verified.failure:
            return result_type.from_failure(verified)
        prepared, phase_roots = verified.value
        # Reject every invalid destination before creating any phase artifact.
        # Recovery cannot authorize partial staging absent from the durable
        # journal.
        for phase_root_state in phase_roots.values():
            if phase_root_state.exists:
                continue
            created = u.Cli.atomic_create_empty_directory_guarded(
                phase_root_state,
                permission_mode=0o700,
            )
            if created.failure:
                return result_type.from_failure(created)
        return cls._write_staged_publications(phase, prepared, intents=intents)

    @classmethod
    def plan_file_staging(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        phase: str,
        changed: t.VariadicTuple[m.Infra.CodegenFilePlan],
        *,
        directories: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[
                tuple[
                    m.Infra.CodegenFilePlan,
                    m.Cli.AtomicFileState,
                    tuple[Path, bytes, int],
                    bool,
                ]
            ],
            t.MappingKV[Path, m.Cli.AtomicDirectoryState],
        ]
    ]:
        """Prove every changed plan is stageable and collect its inputs.

        Returns:
            The resulting ``p.Result[t.Pair[t.VariadicTuple[tuple[
                m.Infra.CodegenFilePlan, m.Cli.AtomicFileState, tuple[Path,
                bytes, int], bool]], t.MappingKV[Path,
                m.Cli.AtomicDirectoryState]]]``.

        """
        result_type = r[
            t.Pair[
                t.VariadicTuple[
                    tuple[
                        m.Infra.CodegenFilePlan,
                        m.Cli.AtomicFileState,
                        tuple[Path, bytes, int],
                        bool,
                    ]
                ],
                t.MappingKV[Path, m.Cli.AtomicDirectoryState],
            ]
        ]
        prepared: list[
            tuple[
                m.Infra.CodegenFilePlan,
                m.Cli.AtomicFileState,
                tuple[Path, bytes, int],
                bool,
            ]
        ] = []
        phase_roots: MutableMapping[Path, m.Cli.AtomicDirectoryState] = {}
        for file_plan in changed:
            project = next(
                (
                    item
                    for item in files.transaction_participants(layout)
                    if item.root == file_plan.project
                ),
                None,
            )
            if project is None or project.transaction_root is None:
                return result_type.fail(
                    f"{phase} file has no transaction participant: {file_plan.path}",
                )
            current = files.read_state(file_plan.path, required=False)
            if current.failure:
                return result_type.from_failure(current)
            before = current.value
            planned = cls._verified_planned_state(phase, file_plan, before)
            if planned.failure:
                return result_type.from_failure(planned)
            physical = cls._verified_staging_filesystem(
                phase,
                file_plan,
                project.transaction_root,
            )
            if physical.failure:
                return result_type.from_failure(physical)
            replacement_input = cls._staged_replacement_input(
                phase,
                file_plan,
                project.transaction_root,
                phase_roots,
                directories,
            )
            if replacement_input.failure:
                return result_type.from_failure(replacement_input)
            prepared.append((
                file_plan,
                before,
                replacement_input.value[0],
                replacement_input.value[1],
            ))
        return result_type.ok((tuple(prepared), phase_roots))

    @staticmethod
    def _verified_planned_state(
        phase: str,
        file_plan: m.Infra.CodegenFilePlan,
        before: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Prove the live destination still matches its planned state.

        A plan captured before its parent chain existed carries no parent
        identity (chain plan, or file state with ``parent_device`` None); the
        parent may legitimately appear before staging, and the journal owns
        its identity check. Staging only proves the file itself stayed absent.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        planned_before = file_plan.before
        if (
            isinstance(planned_before, m.Cli.AtomicDirectoryChainPlan)
            or planned_before.parent_device is None
        ):
            if before.content is not None:
                return result_type.fail(
                    f"{phase} destination appeared after planning: {file_plan.path}",
                )
            return result_type.ok(value=True)
        if before != planned_before:
            return result_type.fail(
                f"{phase} destination changed after planning: {file_plan.path}",
            )
        return result_type.ok(value=True)

    @staticmethod
    def _verified_staging_filesystem(
        phase: str,
        file_plan: m.Infra.CodegenFilePlan,
        transaction_root: Path,
    ) -> p.Result[bool]:
        """Prove the destination parent is physical and on the staging device.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        if not file_plan.path.parent.is_dir() or file_plan.path.parent.is_symlink():
            return result_type.fail(
                f"{phase} destination parent is not physical: {file_plan.path.parent}",
            )
        try:
            parent_state = file_plan.path.parent.lstat()
            transaction_parent = transaction_root.parent.lstat()
        except OSError as exc:
            return result_type.fail_op(f"inspect {phase} staging filesystem", exc)
        reparse = getattr(parent_state, "st_file_attributes", 0) & getattr(
            stat,
            "FILE_ATTRIBUTE_REPARSE_POINT",
            0,
        )
        if (
            not stat.S_ISDIR(parent_state.st_mode)
            or reparse
            or parent_state.st_dev != transaction_parent.st_dev
        ):
            return result_type.fail(
                f"{phase} staging is not on destination filesystem: {file_plan.path}",
            )
        return result_type.ok(value=True)

    @staticmethod
    def _staged_replacement_input(
        phase: str,
        file_plan: m.Infra.CodegenFilePlan,
        transaction_root: Path,
        phase_roots: MutableMapping[Path, m.Cli.AtomicDirectoryState],
        directories: t.VariadicTuple[m.Cli.AtomicDirectoryState] = (),
    ) -> p.Result[t.Pair[tuple[Path, bytes, int], bool]]:
        """Reserve the phase staging root for a content-bearing plan.

        Returns:
            The resulting ``p.Result[t.Pair[tuple[Path, bytes, int],
            bool]]`` where the boolean marks staging presence (False marks a
            deletion-only plan).

        """
        result_type = r[t.Pair[tuple[Path, bytes, int], bool]]
        desired_mode = file_plan.desired_mode
        if file_plan.desired_content is None and file_plan.dependency_group is None:
            return result_type.ok(((Path(), b"", 0), False))
        if file_plan.desired_content is None:
            desired_mode = (
                file_plan.before.mode
                if isinstance(file_plan.before, m.Cli.AtomicFileState)
                else None
            )
        if desired_mode is None:
            return result_type.fail(f"{phase} desired mode is absent: {file_plan.path}")
        phase_root = transaction_root / f"phase-{phase}"
        if phase_root not in phase_roots:
            # Distinct name: the plan's `before` is this file's
            # AtomicFileState and is published below; reusing it here bound a
            # Result and the staged-file model rejected it.
            phase_root_before = u.Cli.atomic_read_empty_directory_state(
                phase_root,
                required=False,
            )
            if phase_root_before.failure:
                return result_type.from_failure(phase_root_before)
            if (
                phase_root_before.value.exists
                and phase_root_before.value not in directories
            ):
                return result_type.fail(
                    f"{phase} staging root already exists: {phase_root}",
                )
            phase_roots[phase_root] = phase_root_before.value
        return result_type.ok((
            (phase_root, file_plan.desired_content or b"", desired_mode),
            file_plan.desired_content is not None,
        ))

    @staticmethod
    def _write_staged_publications(
        phase: str,
        prepared: t.VariadicTuple[
            tuple[
                m.Infra.CodegenFilePlan,
                m.Cli.AtomicFileState,
                tuple[Path, bytes, int],
                bool,
            ]
        ],
        *,
        intents: t.VariadicTuple[m.Infra.CodegenStagingIntent] = (),
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]:
        """Write every staged replacement and bind the staged-file models.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]
            ``.

        """
        result_type = r[tuple[m.Infra.CodegenStagedFile, ...]]
        publications: list[m.Infra.CodegenStagedFile] = []
        for index, (file_plan, before, replacement_input, staged_present) in enumerate(
            prepared,
        ):
            replacement: m.Cli.AtomicFileState | None = None
            original_replacement: m.Cli.AtomicFileState | None = None
            if file_plan.dependency_group is not None and before.content is not None:
                original = FlextInfraCodegenStaging._write_group_preimage(
                    index,
                    replacement_input,
                    before.content,
                    before.mode,
                    intents,
                )
                if original.failure:
                    return result_type.from_failure(original)
                original_replacement = original.value
            if staged_present:
                staged = FlextInfraCodegenStaging._write_staged_replacement(
                    index,
                    replacement_input,
                    intents,
                )
                if staged.failure:
                    return result_type.from_failure(staged)
                replacement = staged.value
            publications.append(
                m.Infra.CodegenStagedFile(
                    dependency_group=file_plan.dependency_group,
                    original_replacement=original_replacement,
                    phase=c.Infra.CodegenStagedFilePhase(phase),
                    project=file_plan.project,
                    before=before,
                    replacement=replacement,
                    source_states=file_plan.source_states,
                    source_directories=file_plan.source_directories,
                    source_query_topology=file_plan.source_query_topology,
                    tracking=file_plan.tracking,
                    index_before=file_plan.index_before,
                    tracking_dependencies=file_plan.tracking_dependencies,
                ),
            )
        return result_type.ok(tuple(publications))

    @staticmethod
    def _write_group_preimage(
        index: int,
        replacement_input: tuple[Path, bytes, int],
        content: bytes,
        mode: int | None,
        intents: t.VariadicTuple[m.Infra.CodegenStagingIntent] = (),
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Write the dependency-group preimage and read back its state.

        Args:
            index: Staged-file index used to derive the preimage path.
            replacement_input: Staged replacement tuple carrying the phase root.
            content: Pre-staging content bytes to preserve as the preimage.
            mode: Pre-staging permission bits, or None when absent.
            intents: Durable staging intents consulted for the write.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        result_type = r[m.Cli.AtomicFileState]
        original_path = replacement_input[0] / f"{index:06d}.original"
        intent = next(
            (item for item in intents if item.before.path == original_path),
            None,
        )
        if intent is None or mode is None:
            return result_type.fail("group preimage has no durable intention")
        original = process.write_new(
            original_path,
            content,
            mode,
            intent=intent,
        )
        if original.failure:
            return result_type.from_failure(original)
        observed = files.read_state(original_path, required=True)
        if observed.failure:
            return result_type.from_failure(observed)
        return result_type.ok(observed.value)

    @staticmethod
    def _write_staged_replacement(
        index: int,
        replacement_input: tuple[Path, bytes, int],
        intents: t.VariadicTuple[m.Infra.CodegenStagingIntent] = (),
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Write the staged replacement file and read back its state.

        Args:
            index: Staged-file index used to derive the replacement path.
            replacement_input: Staged replacement tuple with phase root, content,
                and mode.
            intents: Durable staging intents consulted for the write.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        result_type = r[m.Cli.AtomicFileState]
        phase_root, desired_content, desired_mode = replacement_input
        staged_path = phase_root / f"{index:06d}.replacement"
        intent = next(
            (item for item in intents if item.before.path == staged_path),
            None,
        )
        if intents and intent is None:
            return result_type.fail(
                f"replacement has no durable intention: {staged_path}",
            )
        staged = process.write_new(
            staged_path,
            desired_content,
            desired_mode,
            intent=intent,
        )
        if staged.failure:
            return result_type.from_failure(staged)
        staged_state = files.read_state(staged_path, required=True)
        if staged_state.failure:
            return result_type.from_failure(staged_state)
        return result_type.ok(staged_state.value)


__all__: list[str] = ["FlextInfraCodegenStaging"]
