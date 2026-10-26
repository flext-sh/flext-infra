"""Explicit generation, conformance observation and repair composition.

The generation executor remains private. Its public operation is inherited through
the owning Generate subfacade; conformance retains its distinct request contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u, workspace as workspace_services
from flext_infra.codegen._conform.execute import FlextInfraCodegenConformExecute


class FlextInfraCodegenConform:
    """Observe or repair declarations before the shared projection publication."""

    class Generate(FlextInfraCodegenConformExecute):
        """Expose the existing generation operation through its owning MRO."""

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
        bound = cls.Generate.from_request(
            admitted,
            execution_context=execution_context,
            repository_root=repository_root,
        )
        if bound.failure:
            return r[p.Infra.CodegenResult].from_failure(bound)
        executor = bound.value
        if admitted.mode is c.Infra.CodegenConformMode.CHECK:
            native = workspace_services.FlextInfraWorkspaceNativeReference
            with native.compilation_scope():
                return executor.check_managed(admitted)
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
        return cls._migrate_repository_declarations(executor, request)

    @classmethod
    def _migrate_repository_declarations(
        cls,
        executor: FlextInfraCodegenConformExecute,
        request: p.Infra.CodegenConformRequest,
    ) -> p.Result[bool]:
        """Publish declaration migrations before any runtime detector read.

        Returns:
            Success after publishing every selected target's migration.

        """
        targets = u.Infra.repository_operation_targets(request.root, request.scope)
        if targets.failure:
            return r[bool].from_failure(targets)
        kind = request.declaration_kind
        files: list[m.Infra.CodegenFilePlan] = []
        for target in targets.value:
            if target.managed is False or not (
                u.Infra.workspace_manifest_path(target.root).is_file()
                or (
                    request.declaration_kind is not None
                    and target.root.resolve() == request.root.resolve()
                )
            ):
                continue
            inputs = u.Infra.load_codegen_inputs(target.root)
            if inputs.failure:
                return r[bool].from_failure(inputs)
            planned = (
                executor.repository_kind_declaration_plans(
                    target.root, inputs.value, kind
                )
                if kind is not None
                else executor.repository_declaration_migration_plans(
                    target.root, inputs.value
                )
            )
            if planned.failure:
                return r[bool].from_failure(planned)
            files.extend(planned.value)
        ports = executor.state.ports
        if ports is None:
            return r[bool].fail("conformance requires facade-wired file publication")
        return ports.file_publisher.publish_codegen_plans(request.root, files).map(
            lambda _: True
        )

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
            workspace_result = (
                workspace_services.FlextInfraWorkspaceDetector.load_workspace_spec(root)
            )
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
