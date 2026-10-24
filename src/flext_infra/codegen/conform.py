"""Explicit conformance observation and repair composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u

from flext_infra.codegen._conform.execute import FlextInfraCodegenConformExecute
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceNativeReference,
)


class FlextInfraCodegenConform:
    """Observe or repair declarations before the shared projection publication."""

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.CodegenConformRequest,
        *,
        execution_context: p.Infra.CodegenExecutionContext | None,
        repository_root: t.Infra.Path | None = None,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Admit conformance once and compose its validated native instance.

        Returns:
            The observation or complete repair outcome with its original cause.

        """
        admitted = m.Infra.CodegenConformRequest.model_validate(
            request, from_attributes=True
        )
        if admitted.mode is c.Infra.CodegenConformMode.CHECK:
            with FlextInfraWorkspaceNativeReference.compilation_scope():
                return cls._observe_publication(admitted)
        bound = FlextInfraCodegenConformExecute.from_request(
            admitted,
            execution_context=execution_context,
            repository_root=repository_root,
        )
        if bound.failure:
            return r[p.Infra.CodegenResult].from_failure(bound)
        executor = bound.value
        governed = cls._migrate_governed_declarations(executor, admitted)
        if governed.failure:
            return r[p.Infra.CodegenResult].from_failure(governed)
        if admitted.what is not c.Infra.CodegenConformSurface.ALL:
            return executor.execute()
        seeded = cls._seed_declared_beads_identity(executor, admitted.root)
        if seeded.failure:
            return r[p.Infra.CodegenResult].from_failure(seeded)
        return executor.execute_managed(
            admitted,
            after_publication=(
                lambda written: cls.conform_workspace_beads_routes(
                    executor, admitted
                ).flat_map(lambda _: cls._allow_direnv_after_apply(written)),
            ),
        )

    @classmethod
    def _migrate_governed_declarations(
        cls,
        executor: FlextInfraCodegenConformExecute,
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[bool]:
        """Migrate declarations when the surface is governed or kind-declared.

        Returns:
            Success when no migration is due or its only failure is a retained
            planning issue, otherwise the migration failure.

        """
        inputs = u.Infra.load_codegen_inputs(request.root.expanduser().resolve())
        if inputs.failure:
            return r[bool].from_failure(inputs)
        contract = executor.surface_contract(request.what, codegen=inputs.value.spec)
        if not (contract.complete_governed or request.declaration_kind is not None):
            return r[bool].ok(value=True)
        migrated = cls._migrate_repository_declarations(executor, request)
        if migrated.failure and (
            migrated.error_code != c.Infra.ToolOutcome.ERROR.value
            or not executor.state.planning_issues
        ):
            return migrated
        return r[bool].ok(value=True)

    @staticmethod
    def _observe_publication(
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[p.Infra.CodegenResult]:
        """Observe physical publication evidence without a general code audit.

        Returns:
            The verified publication result, or the verification failure.

        """
        with u.Cli.file_changes_lock(u.Infra.mutation_lock_path(request.root).unwrap()):
            observed = FlextInfraMiseArtifactsVerification.publication_current(
                request,
            )
            if observed.failure:
                return r[p.Infra.CodegenResult].from_failure(observed)
            payload: p.Infra.CodegenResult = m.Infra.CodegenResult(
                verified_publication=observed.value,
            )
            return r[p.Infra.CodegenResult].ok(payload)

    @classmethod
    def _migrate_repository_declarations(
        cls,
        executor: FlextInfraCodegenConformExecute,
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[bool]:
        """Publish explicit input migration before any runtime detector read.

        Returns:
            A complete migration receipt, retaining per-file failures and gains.

        """
        targets = u.Infra.repository_operation_targets(
            request.root,
            request.scope,
        )
        if targets.failure:
            return r[bool].from_failure(targets)
        selected = tuple(
            target
            for target in targets.value
            if target.managed is not False
            and (
                u.Infra.workspace_manifest_path(target.root).is_file()
                or (
                    request.declaration_kind is not None
                    and target.root.resolve() == request.root.resolve()
                )
            )
        )
        if not selected:
            return r[bool].ok(value=True)
        roots = FlextInfraCodegenTransaction.capability_roots(
            "repository-declaration",
            tuple(target.root for target in selected),
        )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
        )

        def publish(scope_root: Path) -> p.Result[bool]:
            analysis = cls._collect_declaration_migration_plans(
                executor, request, selected
            )
            if analysis.failure:
                return r[bool].from_failure(analysis)
            if (
                not analysis.value.files
                and not analysis.value.issues
                and analysis.value.exception is None
            ):
                return r[bool].ok(value=True)
            published = transaction.publish_file_phase_locked(
                scope_root,
                roots,
                analysis.value,
                m.Infra.CodegenPhasePublicationPolicy(
                    directories=tuple(
                        sorted({
                            file.path.parent
                            for file in analysis.value.files
                            if not file.path.parent.is_dir()
                        }),
                    ),
                ),
            )
            if published.failure:
                if published.error_code == c.Infra.ToolOutcome.ERROR.value:
                    retained = cls._retain_completed_migration_issues(
                        executor, published
                    )
                    if retained.failure:
                        return retained
                return r[bool].from_failure(published)
            return r[bool].ok(value=True)

        return transaction.run_files_locked(roots, publish)

    @staticmethod
    def _collect_declaration_migration_plans(
        executor: FlextInfraCodegenConformExecute,
        request: p.Infra.CodegenConformRequest,
        selected: t.SequenceOf[m.Infra.WorkspaceOperationTarget],
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan every selected target's declaration migration into one analysis.

        Returns:
            The combined bootstrap-phase analysis, retaining per-file
            failures and gains.

        """
        files: list[m.Infra.CodegenFilePlan] = []
        inputs: list[m.Cli.AtomicFileState] = []
        issues: list[m.Infra.Issue] = []
        first_exception: BaseException | None = None
        for target in selected:
            captured = u.Infra.load_codegen_inputs(target.root)
            if captured.failure:
                planned: p.Result[m.Infra.CodegenPhaseAnalysis] = r[
                    m.Infra.CodegenPhaseAnalysis
                ].from_failure(captured)
            elif request.declaration_kind is not None:
                planned = executor.repository_kind_declaration_plans(
                    target.root,
                    captured.value,
                    request.declaration_kind,
                )
            else:
                planned = executor.repository_declaration_migration_plans(
                    target.root,
                    captured.value,
                )
            if planned.failure:
                issues.append(
                    m.Infra.Issue(
                        file=str(u.Infra.workspace_manifest_path(target.root)),
                        line=0,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=planned.error
                        or "repository declaration migration failed",
                    ),
                )
                if first_exception is None:
                    first_exception = planned.exception
                continue
            files.extend(planned.value.files)
            inputs.extend(planned.value.inputs)
            issues.extend(planned.value.issues)
            if first_exception is None:
                first_exception = planned.value.exception
        snapshots = u.Infra.unique_states(tuple(inputs))
        if snapshots.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(snapshots)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
                files=tuple(files),
                inputs=snapshots.value,
                issues=tuple(issues),
                exception=first_exception,
            ),
        )

    @staticmethod
    def _retain_completed_migration_issues(
        executor: FlextInfraCodegenConformExecute,
        published: p.Result[t.VariadicTuple[Path]],
    ) -> p.Result[bool]:
        """Carry a settled red publication into the existing final plan report.

        Returns:
            Typed residual issues retained with their original first cause.

        """
        metadata = published.error_data
        if metadata is None:
            return r[bool].fail(
                "completed migration failure has no structured publication receipt",
                exception=published.exception,
            )

        def parse() -> t.VariadicTuple[m.Infra.Issue]:
            serialized = u.Cli.json_dumps(metadata["issues"]).unwrap()
            wire = u.type_adapter(tuple[t.JsonMapping, ...]).validate_json(serialized)
            return tuple(
                m.Infra.Issue.model_validate_json(
                    u.Cli.json_dumps(
                        {
                            key: value
                            for key, value in issue.items()
                            if key not in m.Infra.Issue.model_computed_fields
                        },
                    ).unwrap(),
                )
                for issue in wire
            )

        parsed = r[t.VariadicTuple[m.Infra.Issue]].create_from_callable(parse)
        if parsed.failure:
            return r[bool].fail(
                parsed.error or "invalid completed migration issue receipt",
                exception=published.exception or parsed.exception,
            )
        if not parsed.value:
            return r[bool].fail(
                "completed migration failure has no residual issue",
                exception=published.exception,
            )
        executor.retain_diagnostics(published.exception, issues=parsed.value)
        return r[bool].ok(value=True)

    @staticmethod
    def _seed_declared_beads_identity(
        executor: FlextInfraCodegenConformExecute, root: Path
    ) -> p.Result[bool]:
        """Materialize the scaffold's declared Beads identity before governance.

        The participant-policy snapshot resolves repository governance through
        the workspace detector, which reads the repository-local Beads
        identity. A fresh scaffold root has no local history for the detector
        to read yet, while the declared workspace already carries the derived
        identity: writing it first makes the repository self-consistent from
        the first governed effect. The template render of the same identity
        follows later in the cycle and is byte-identical.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        workspace = executor.state.initial_workspace
        if workspace is None or workspace.beads is None:
            return r[bool].ok(value=True)
        beads = workspace.beads
        destination = root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME
        if destination.is_file():
            return r[bool].ok(value=True)
        quoted = tuple(
            u.Cli.json_dumps(value)
            for value in (beads.workspace, beads.database, beads.issue_prefix)
        )
        failed = next((item for item in quoted if item.failure), None)
        if failed is not None:
            return r[bool].from_failure(failed)
        workspace_name, database, issue_prefix = (item.value for item in quoted)
        payload = (
            f"version: {beads.version}\n"
            f"workspace: {workspace_name}\n"
            f"database: {database}\n"
            f"issue_prefix: {issue_prefix}\n"
        )
        written = u.Cli.atomic_write_text_file(destination, payload)
        if written.failure:
            return r[bool].from_failure(written)
        return r[bool].ok(value=True)

    @classmethod
    def conform_workspace_beads_routes(
        cls,
        executor: FlextInfraCodegenConformExecute,
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[bool]:
        """Reconcile private metadata directories without cross-project links.

        A composed project follows the workspace ledger through its own rendered
        ``.beads`` configuration, which every checkout resolves identically. It
        previously followed the ledger through ``.beads -> ../.beads``, a link
        escaping into another repository: a second owner of a fact the
        configuration already declares, resolvable only on one machine's exact
        layout, and invisible to review because it reads as a directory. This
        method used to create those links and delete the real directory first;
        now it proves none survive and enforces the client's private-directory
        contract after publication, for the root and its composed members.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = request.root.expanduser().resolve()
        workspace = executor.state.initial_workspace
        if workspace is None:
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(root)
            if workspace_result.failure:
                return r[bool].from_failure(workspace_result)
            workspace = workspace_result.value
        owner = root / c.Infra.BEADS_DIRNAME
        if workspace.beads is None:
            if owner.exists() or owner.is_symlink():
                return r[bool].fail(
                    f"Beads-disabled repository still has Beads state: {owner}",
                )
            return r[bool].ok(value=True)
        # The ledger directory is a conform projection: absent before the
        # first render is normal; a link, or a non-directory, is not physical.
        if owner.is_symlink() or (owner.exists() and not owner.is_dir()):
            return r[bool].fail(
                f"workspace Beads ledger owner is not physical: {owner}",
            )
        if owner.is_dir():
            owner.chmod(c.Infra.BEADS_DIRECTORY_MODE)
        for repository in workspace.subprojects:
            state = cls.beads_route_state((root / repository.path).resolve())
            if state.failure:
                return state
        return r[bool].ok(value=True)

    @staticmethod
    def beads_route_state(root: Path) -> p.Result[bool]:
        """Prove one repository reaches the ledger through its own directory.

        The route used to be a symlink into the workspace, so the directory
        always existed by the time anything rendered into it. Each repository
        now owns a real ``.beads`` holding its own generated configuration, and
        a generator owns the destination directory of the artifacts it
        declares: without it the first render fails reading a before-state
        whose parent is missing. The directory is created empty;
        ``.beads/config.yaml`` and ``.beads/metadata.json`` are rendered into
        it by generation, never copied and never linked.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        allowed_entries = (
            frozenset({
                Path(c.Infra.BEADS_CONFIG_RELPATH).name,
                Path(c.Infra.BEADS_METADATA_RELPATH).name,
                c.Infra.BEADS_LOCAL_VERSION_FILENAME,
                c.Infra.BEADS_LAST_TOUCHED_FILENAME,
                # Passive bd runtime exports: the bd client rewrites these from
                # the rig's Dolt ledger on every interaction, so they are
                # regenerable projections of ledger truth, never composed output.
                "issues.jsonl",
                "interactions.jsonl",
            })
            | c.Infra.BEADS_RUNTIME_ENTRY_NAMES
        )
        route = root / c.Infra.BEADS_DIRNAME
        if route.is_symlink():
            return r[bool].fail(
                "composed project reaches the workspace ledger through a "
                f"cross-project symbolic link: {route}",
            )
        if not route.exists():
            route.mkdir(mode=c.Infra.BEADS_DIRECTORY_MODE, parents=True)
            return r[bool].ok(value=True)
        if not route.is_dir():
            return r[bool].fail(
                f"composed project Beads route is not a directory: {route}",
            )
        unexpected = sorted(
            entry.name for entry in route.iterdir() if entry.name not in allowed_entries
        )
        if unexpected:
            return r[bool].fail(
                f"composed project has unmerged Beads state at {route}: "
                + ", ".join(unexpected),
            )
        route.chmod(c.Infra.BEADS_DIRECTORY_MODE)
        return r[bool].ok(value=True)

    @staticmethod
    def _allow_direnv_after_apply(
        written_files: t.VariadicTuple[Path],
    ) -> p.Result[bool]:
        """Heal the direnv allow for every ``.envrc`` this apply published.

        ``make setup`` authorizes the rendered ``.envrc`` once; a later conform
        apply legitimately rewrites it (content-hash changes) and every
        subsequent command blocks on direnv's stale-allow warning. The
        generator owns the file it renders, so apply heals the allow itself
        instead of leaving every environment stale until the operator re-runs
        setup.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        roots = {
            path.expanduser().resolve().parent
            for path in written_files
            if path.name == c.Infra.ENVRC_FILENAME
        }
        if not roots:
            return r[bool].ok(value=False)
        for root in sorted(roots):
            result = u.Cli.run_raw(
                (c.Infra.CLI_DIRENV, "allow", str(root)),
                cwd=root,
                timeout=c.Infra.TIMEOUT_SHORT,
            )
            if result.failure:
                return r[bool].from_failure(result)
            if not u.Cli.process_succeeded(result.value.outcome):
                return r[bool].fail(
                    f"direnv allow failed for {root}: "
                    f"{result.value.stderr.strip() or result.value.stdout.strip()}",
                )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraCodegenConform"]
