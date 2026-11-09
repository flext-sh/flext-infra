"""Conformance planning for existing repositories and governed artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Generator, Mapping, MutableMapping, Sequence
from contextlib import ExitStack, contextmanager
from functools import partial
from pathlib import Path

from flext_infra import (
    c,
    deps as dependency_services,
    m,
    p,
    r,
    u,
    workspace as workspace_services,
)
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.codegen._conform import FlextInfraCodegenConformEditor


class FlextInfraCodegenConformExistingPlan(FlextInfraCodegenConformEditor):
    """Conformance planning for existing repositories and governed artifacts."""

    _source_views: (
        tuple[ExitStack, MutableMapping[Path, p.Infra.RopeProject]] | None
    ) = m.PrivateAttr(default=None)

    @contextmanager
    def shared_source_views(self) -> Generator[None]:
        """Keep the elected native project of each repository plan open once.

        Candidate bindings evolve and restore this project's overlay through
        native resource invalidation, rather than constructing another project
        for every distinct tuple of planned bytes.

        Yields:
            Nothing; the scope is active until the repository plan completes.

        """
        try:
            with ExitStack() as stack:
                self._source_views = (stack, {})
                yield
        finally:
            self._source_views = None

    @contextmanager
    def _source_view(
        self,
        root: Path,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...] = (),
    ) -> Generator[tuple[p.Infra.RopeProject, Mapping[Path, str]]]:
        """Bind candidate bytes for the lifetime of one native source consumer.

        Exiting restores the entry overlay, preserving observed ownership for
        the next phase. Every binding gets its own source mapping; native
        resource identity and inference remain owned by the elected project.

        Yields:
            The shared native project and its planned sources.

        Raises:
            RuntimeError: If no repository planning scope is open.

        """
        if self._source_views is None:
            msg = "source views require an open repository planning scope"
            raise RuntimeError(msg)
        stack, opened = self._source_views
        if root not in opened:
            engine = u.Infra.snapshot_engine(self.state.snapshot, root)
            opened[root] = (
                engine
                if engine is not None
                else stack.enter_context(u.Infra.facade_source_project(root))[0]
            )
        with u.Infra.facade_source_project(
            root,
            declared_files=declared_files,
            source_project=opened[root],
        ) as binding:
            yield binding

    def _plan_existing_repository(
        self,
        *,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Conform every declared managed surface in an existing repository.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.CodegenFilePlan]]``.

        """
        root = target.root
        surface_plans = self._plan_existing_contract_surface(
            target,
            workspace,
            codegen,
            contract,
        )
        if surface_plans is not None:
            return surface_plans
        pyproject = root / c.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[Sequence[p.Infra.CodegenFilePlan]].fail(
                f"existing repository has no pyproject.toml: {root}; "
                "scaffold templates are available only through codegen new",
            )
        identity = self._validated_existing_identity(target, workspace, codegen)
        if identity.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(identity)
        docs_config = (Path(c.Infra.DIR_DOCS) / c.Infra.DOCS_CONFIG_FILENAME).as_posix()
        if contract.destinations == frozenset({docs_config}):
            return self._plan_existing_docs_config(
                target,
                workspace,
                codegen,
                docs_config,
            )
        return self._plan_existing_managed(
            target,
            workspace,
            codegen,
            contract,
            identity.value,
        )

    def _validated_existing_identity(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
    ) -> p.Result[tuple[p.Infra.ProjectSpec, p.ProjectMetadata]]:
        """Resolve the project identity and prove it matches the live PEP 621.

        Existing checkouts declare no scaffold metadata: the tooling identity
        derives from live PEP 621 metadata (same rule as the render pass)
        instead of referencing an undefined name.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.ProjectSpec,
                p.ProjectMetadata]]``.

        """
        result_type = r[tuple[p.Infra.ProjectSpec, p.ProjectMetadata]]
        root = target.root
        repository = target.repository
        u.Cli.info(f"  stage=pyproject repository={repository.name}")
        metadata = u.Infra.read_project_metadata_result(root)
        if metadata.failure:
            return result_type.from_failure(metadata)
        project = workspace.project
        if project is None:
            derived = self._project_spec_from_existing(repository, root, codegen)
            if derived.failure:
                return result_type.from_failure(derived)
            project = derived.value
        dist = metadata.value.project.name
        if dist != repository.distribution:
            return result_type.fail(
                "PEP 621 project name does not match catalog distribution: "
                f"{dist} != {repository.distribution}",
            )
        return result_type.ok((project, metadata.value))

    def _plan_existing_contract_surface(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]] | None:
        """Plan recovery surfaces before consumers parse existing projections.

        Returns:
            The resulting plans for a single-artifact surface, or None when
            the contract does not select one.

        """
        if contract.destinations == self._editor_destinations(codegen):
            return self._plan_existing_editor(target, workspace, codegen)
        destinations = contract.destinations
        if destinations is None or destinations not in {
            frozenset({c.Infra.ENVRC_FILENAME}),
            frozenset({c.Infra.GITIGNORE}),
            frozenset({c.Infra.MISE_TOML_FILENAME}),
            c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS,
        }:
            return None
        return self._plan_existing_bootstrap(
            target, workspace, codegen, destinations=destinations
        )

    def _plan_existing_managed(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
        identity: tuple[p.Infra.ProjectSpec, p.ProjectMetadata],
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Plan the managed templates (and custom content) for an existing tree.

        One original source epoch serves the whole plan. Failures return as
        data; only a source cohort that passed verification is recorded as
        completed, so a later failure retains exactly that verified output.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.CodegenFilePlan]]``.

        """
        result_type = r[Sequence[p.Infra.CodegenFilePlan]]
        managed_artifacts = u.Infra.snapshot_project_managed_artifacts(target.root)
        if managed_artifacts.failure:
            return result_type.from_failure(managed_artifacts)
        if not (contract.tooling or contract.custom):
            untooled_runtime = self._existing_untooled_runtime(
                target, codegen, contract, identity, managed_artifacts.value
            )
            return (
                result_type.from_failure(untooled_runtime)
                if untooled_runtime is not None and untooled_runtime.failure
                else self._plan_existing_templates(
                    render_inputs=self.resolve_render_inputs(
                        target=target,
                        workspace=workspace,
                        codegen=codegen,
                        tooling_runtime=(
                            None if untooled_runtime is None else untooled_runtime.value
                        ),
                        managed_artifacts=managed_artifacts.value,
                    ),
                    contract=contract,
                )
            )
        sources = self._existing_managed_sources(target, codegen, contract)
        if sources.failure:
            return result_type.from_failure(sources)
        custom, initializers = sources.value[1], sources.value[2]
        with self._source_view(
            target.root,
            declared_files=sources.value[0],
        ) as binding:
            tooling_runtime = None
            if contract.tooling:
                tooling_context = self._existing_tooling_context(
                    self._existing_tooling_request(
                        target, identity, codegen, (*initializers, *custom)
                    ),
                    managed_artifacts.value.resolution,
                    source_project=binding[0],
                )
                if tooling_context.failure:
                    return result_type.from_failure(tooling_context)
                tooling_runtime = tooling_context.value
            render_inputs = self.resolve_render_inputs(
                target=target,
                workspace=workspace,
                codegen=codegen,
                tooling_runtime=tooling_runtime,
                managed_artifacts=managed_artifacts.value,
            )
            return self._render_existing_managed(
                render_inputs,
                contract,
                initializers,
                custom,
                source_project=binding[0],
            )

    def _existing_untooled_runtime(
        self,
        target: p.Infra.RepositoryConformTarget,
        codegen: p.Infra.CodegenConfigSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
        identity: tuple[p.Infra.ProjectSpec, p.ProjectMetadata],
        managed_artifacts: p.Infra.ProjectManagedArtifactsSnapshot,
    ) -> p.Result[p.Infra.ToolingRuntimeContext] | None:
        """Resolve the full live-source runtime consumed by a scoped pyproject.

        Returns:
            The elected pyproject runtime, no runtime, or its original failure.

        """
        if contract.pyproject:
            return dependency_services.FlextInfraPyprojectModernizer(
                repository_root=target.root,
                skip_check=True,
                managed_artifacts=managed_artifacts.resolution,
            ).resolve_tooling_context(
                self._existing_tooling_request(target, identity, codegen, ()),
            )
        return None

    def _existing_managed_sources(
        self,
        target: p.Infra.RepositoryConformTarget,
        codegen: p.Infra.CodegenConfigSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[
        tuple[
            tuple[p.Infra.CodegenFilePlan, ...],
            Sequence[p.Infra.CodegenFilePlan],
            tuple[p.Infra.CodegenFilePlan, ...],
        ]
    ]:
        """Compose custom declarations and exports over the projected sources.

        Returns:
            Projected files, custom files and initializers.

        """
        result_type = r[
            tuple[
                tuple[p.Infra.CodegenFilePlan, ...],
                Sequence[p.Infra.CodegenFilePlan],
                tuple[p.Infra.CodegenFilePlan, ...],
            ]
        ]
        root = target.root
        metadata_only = (
            contract.destinations is not None
            and contract.destinations <= self._pyproject_destinations(codegen)
        )
        # Custom convergence seeds exports before resolving its facade imports.
        # The planned initializers are always seeded, including custom
        # contracts: a stale on-disk initializer otherwise breaks rope
        # resolution of facade imports before the convergence loop can heal
        # it (a stale initializer never blocks its own regeneration).
        lazy_result = (
            r[Sequence[p.Infra.CodegenFilePlan]].ok(())
            if metadata_only
            else self._existing_lazy_sources(root)
        )
        if lazy_result.failure:
            return result_type.from_failure(lazy_result)
        # Custom facades resolve their owners through the provided initializers
        # of this repository too; the initializers re-planned over the projected
        # facades below supersede them by path.
        cohort = tuple(
            {
                plan.path: plan
                for plan in (
                    *(
                        plan
                        for plan in self.state.provider_plans or ()
                        if plan.project != root or contract.custom
                    ),
                    *lazy_result.value,
                )
            }.values()
        )
        if not contract.custom:
            if not metadata_only:
                return result_type.ok((cohort, (), tuple(lazy_result.value)))
            return self._projected_exports(root, cohort).map(
                lambda exported: ((*cohort, *exported), (), tuple(exported))
            )
        return self._projected_custom_sources(
            root, (codegen, target.make_profile.value), cohort=cohort
        )

    def _projected_custom_sources(
        self,
        root: Path,
        configuration: tuple[p.Infra.CodegenConfigSpec, str],
        *,
        cohort: tuple[p.Infra.CodegenFilePlan, ...],
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None = None,
    ) -> p.Result[
        tuple[
            tuple[p.Infra.CodegenFilePlan, ...],
            Sequence[p.Infra.CodegenFilePlan],
            tuple[p.Infra.CodegenFilePlan, ...],
        ]
    ]:
        """Project a repository's custom artifacts in one ordered pass.

        Generation projects authored declarations and never edits them: the
        model protocol data contracts first, then the lazy exports over them,
        then the family facades, then the exports over the facades. Each step
        reads only what the earlier steps declared, so one pass is the fixed
        point. Repairs, module moves, consumer rewiring and import
        normalization transform authored sources and belong to ``make mod``.

        Returns:
            Projected files, custom files and initializers, or the first failure.

        """
        result_type = r[
            tuple[
                tuple[p.Infra.CodegenFilePlan, ...],
                Sequence[p.Infra.CodegenFilePlan],
                tuple[p.Infra.CodegenFilePlan, ...],
            ]
        ]
        protocols = (
            self._model_protocol_sources(root, cohort)
            if selection is None
            else r[tuple[p.Infra.CodegenFilePlan, ...]].ok(())
        )
        if protocols.failure:
            return result_type.from_failure(protocols)
        staged = u.Infra.codegen_compose_file_plans(
            (*cohort, *protocols.value), ordered=True
        )
        exported = self._custom_export_seed(root, staged, selection=selection)
        if exported.failure:
            return result_type.from_failure(exported)
        staged = u.Infra.codegen_compose_file_plans(
            (*staged, *exported.value), ordered=True
        )
        facades = self._custom_candidate_sources(
            root, configuration, staged, selection=selection
        )
        if facades.failure:
            return result_type.from_failure(facades)
        staged = u.Infra.codegen_compose_file_plans(
            (*staged, *facades.value), ordered=True
        )
        initializers = self._projected_exports(root, staged, selection=selection)
        if initializers.failure:
            return result_type.from_failure(initializers)
        return result_type.ok((
            u.Infra.codegen_compose_file_plans(
                (*staged, *initializers.value), ordered=True
            ),
            (*protocols.value, *facades.value),
            initializers.value,
        ))

    def _model_protocol_sources(
        self,
        root: Path,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Restore model data projection inside the existing source candidate.

        Returns:
            File plans for admitted protocol sources, or the producer's failure.
            Failed inventory never reaches generated-file retirement.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        snapshot = self.state.snapshot
        if snapshot is None:
            return result_type.fail(
                "model protocol projection requires the authenticated run snapshot"
            )
        with self._source_view(root, declared_files=declared_files) as binding:
            rendered_sources: dict[Path, str] = {}
            for package_name in u.Infra.protocol_model_package_names(root, binding[0]):
                rendered = u.Infra.protocol_model_sources_from_source(
                    root, binding[0], package_name=package_name
                )
                if rendered.failure:
                    return result_type.from_failure(rendered)
                rendered_sources.update(rendered.value)
            plans: list[p.Infra.CodegenFilePlan] = []
            for path, content in rendered_sources.items():
                planned = self.file_plan(root, path.as_posix(), content)
                if planned.failure:
                    return result_type.from_failure(planned)
                plans.append(planned.value)
            # Legacy route files may still have live imports. A filename and a
            # general generation header do not authenticate projection ownership
            # or prove consumer rewiring; retirement belongs to that cutover plan.
        return result_type.ok(tuple(plans))

    def _custom_export_seed(
        self,
        root: Path,
        cohort: tuple[p.Infra.CodegenFilePlan, ...],
        *,
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Reuse the complete lazy plan only while its candidate is unchanged.

        Returns:
            Initial exports over the admitted source cohort.

        """
        if (
            selection is not None
            and self.state.provider_plans is not None
            and cohort == self.state.provider_plans
            and all(plan.project == root for plan in cohort)
        ):
            return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(cohort)
        if (
            selection is None
            and self.state.provider_plans is not None
            and not any(
                (plan.project != root or plan.path.name != c.Infra.INIT_PY)
                and u.Infra.codegen_file_requires_effect(plan)
                for plan in cohort
            )
        ):
            return self._existing_lazy_sources(root).map(tuple)
        return self._projected_exports(root, cohort, selection=selection)

    def _custom_candidate_sources(
        self,
        root: Path,
        configuration: tuple[p.Infra.CodegenConfigSpec, str],
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
        *,
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Dispatch the same custom planner for a complete or selected candidate.

        Returns:
            Custom plans, or the original planning admission failure.

        """
        if selection is None:
            return self._plan_existing_custom(
                root,
                configuration[0],
                profile=configuration[1],
                declared_files=declared_files,
            )
        ports, snapshot = self.state.ports, self.state.snapshot
        if ports is None or snapshot is None:
            return r[Sequence[p.Infra.CodegenFilePlan]].fail(
                "selected family composition requires caller-bound planning "
                "and an authenticated repository snapshot"
            )
        return self._component_projection(root, declared_files, selection=selection)

    def _component_projection(
        self,
        root: Path,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
        *,
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Borrow the existing engine; its first planning failure propagates raw.

        Returns:
            The complete source cohort, or the missing-ports refusal.

        """
        ports, snapshot = self.state.ports, self.state.snapshot
        if ports is None or snapshot is None:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].fail(
                "Facade planning requires its invocation ports and source snapshot"
            )
        with (
            self._source_view(root, declared_files=declared_files) as binding,
            workspace_services.FlextInfraRopeWorkspace.open_workspace(
                root,
                rope_repository_root=Path(binding[0].root.real_path),
                source_project=binding[0],
                snapshot=snapshot,
            ) as workspace,
        ):
            outcome = ports.component_planner(
                workspace,
                declared_files=declared_files,
                selection=selection,
            )
        return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(outcome.files)

    def _projected_exports(
        self,
        root: Path,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
        *,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None = None,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Re-plan initializers over one repository's projected sources.

        Returns:
            The export plans.

        Raises:
            ValueError: If the supplied snapshot belongs to another invocation.
            RuntimeError: If the invocation has no authenticated snapshot.

        """
        if snapshot is not None and snapshot is not self.state.snapshot:
            message = "component initializer snapshot differs from the run"
            raise ValueError(message)
        active = self.state.snapshot
        if active is None:
            message = "projected exports require the run snapshot"
            raise RuntimeError(message)
        return FlextInfraCodegenLazyInit.plan_candidate(
            root, declared_files=declared_files, snapshot=active, selection=selection
        )

    def _existing_lazy_sources(
        self,
        root: Path,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Elect the repository's planned or provided initializers.

        Returns:
            Planned initializers of the repository.

        """
        if self.state.provider_plans is None:
            return self._planned_lazy_init_files(root)
        return r[Sequence[p.Infra.CodegenFilePlan]].ok(
            tuple(plan for plan in self.state.provider_plans if plan.project == root)
        )

    def _render_existing_managed(
        self,
        render_inputs: m.Infra.CodegenRenderInputs,
        contract: p.Infra.CodegenConformSurfaceContract,
        initializers: Sequence[p.Infra.CodegenFilePlan],
        custom: Sequence[p.Infra.CodegenFilePlan],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Render both template passes through the same native source project.

        Returns:
            Final templates and their dependent facade publication groups.

        """
        managed = self._plan_existing_templates(
            render_inputs=render_inputs,
            contract=contract,
        )
        if managed.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(managed)
        tooling = render_inputs.tooling_runtime
        if contract.pyproject:
            try:
                render_inputs.tooling_runtime = self.planned_source_tooling(
                    render_inputs,
                    [*initializers, *managed.value, *custom],
                    source_project=source_project,
                )
            except u.Infra.rope_unresolved_error_types() as exception:
                notes = tuple(getattr(exception, "__notes__", ()))
                return r[Sequence[p.Infra.CodegenFilePlan]].fail(
                    f"planned-source tooling derivation failed for "
                    f"{render_inputs.target.root}: "
                    f"{type(exception).__name__}: {exception}; notes={notes}",
                )
        templates = (
            self._plan_existing_templates(
                render_inputs=render_inputs,
                contract=contract,
            )
            if render_inputs.tooling_runtime is not tooling
            else managed
        )
        if templates.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(templates)
        return self._facade_runtime_plans(
            (*templates.value, *custom),
            custom,
            initializers,
            complete_governed=contract.complete_governed,
        )

    @staticmethod
    def _facade_runtime_plans(
        planned: Sequence[p.Infra.CodegenFilePlan],
        custom: Sequence[p.Infra.CodegenFilePlan],
        initializers: Sequence[p.Infra.CodegenFilePlan],
        *,
        complete_governed: bool,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Compose the projections consumed by the publication's native checks.

        Complete generation retains every initializer. Facade consumers share
        their declared source group; other outputs retain their own native
        own plans.

        Returns:
            Original plans grouped with the generated sources their checks consume.

        """
        result_type = r[Sequence[p.Infra.CodegenFilePlan]]
        facades = tuple(
            item for item in custom if item.path.suffix == c.Infra.EXT_PYTHON
        )
        packages = {item.path.parent for item in facades}
        if not packages and not complete_governed:
            return result_type.ok(tuple(planned))
        families = tuple(
            package / family.directory
            for package in packages
            for family in u.Infra.facade_families().values()
        )
        barrels = tuple(
            item
            for item in initializers
            if (
                complete_governed
                or item.path.name != c.Infra.INIT_PY
                or item.path.parent in packages
                or any(item.path.is_relative_to(family) for family in families)
            )
        )
        by_path = {item.path: item for item in planned}
        for barrel in barrels:
            existing = by_path.get(barrel.path)
            # Lazy-init owns every initializer. A protocol mirror package's
            # seed exists only so the package is enumerable and importable;
            # it yields to the initializer planned for the same path.
            if (
                existing is not None
                and existing != barrel
                and not u.Infra.is_mirror_package_seed(existing)
            ):
                return result_type.fail(
                    f"runtime barrel has competing bootstrap plans: {barrel.path}"
                )
        by_path.update(
            (item.path, item)
            for item in (barrels if complete_governed else (*barrels, *facades))
        )
        return result_type.ok(tuple(by_path.values()))

    def _planned_lazy_init_files(
        self,
        root: Path,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Plan the lazy-init projection the declarations determine, read-only.

        Facades import family owners in package form, which resolves only
        through the package initializer the declaring modules' ``__all__``
        project. Tooling derivations therefore read the planned initializers,
        never the previous projection on disk: a stale initializer otherwise
        blocks its own regeneration, on every conform surface (a partial
        surface such as ``dependencies`` derives tooling too). Required runtime
        barrels join their facade consumers in the bootstrap dependency group.
        Complete generation stages every initializer before its project-wide
        admission; narrower surfaces retain their declared publication scope.

        Planning reads the run snapshot's one Rope project, so every
        repository and stage shares its parsed modules and inference.

        Returns:
            The repository's planned lazy-init file plans, or the planning failure.

        Raises:
            RuntimeError: If lazy-init planning requires the run's workspace snapshot.

        """
        snapshot = self.state.snapshot
        if snapshot is None:
            msg = "lazy-init planning requires the run's workspace snapshot"
            raise RuntimeError(msg)
        return FlextInfraCodegenLazyInit(
            repository_root=root,
            project_scope_roots=(root,),
        ).plan_files(source_project=snapshot.engine, snapshot=snapshot)

    @staticmethod
    def _existing_tooling_context(
        request: p.Infra.ToolingContextRequest,
        managed_resolution: p.Infra.ProjectManagedArtifactsResolution,
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[p.Infra.ToolingRuntimeContext]:
        """Resolve tooling through its canonical request and captured artifacts.

        Returns:
            The modernizer's tooling context or its original failure.

        """
        modernizer = dependency_services.FlextInfraPyprojectModernizer(
            repository_root=request.path.parent,
            skip_check=True,
            managed_artifacts=managed_resolution,
        )
        return modernizer.resolve_tooling_context(
            request,
            source_project=source_project,
        )

    def _existing_tooling_request(
        self,
        target: p.Infra.RepositoryConformTarget,
        identity: tuple[p.Infra.ProjectSpec, p.ProjectMetadata],
        codegen: p.Infra.CodegenConfigSpec,
        planned: Sequence[p.Infra.CodegenFilePlan],
    ) -> p.Infra.ToolingContextRequest:
        """Declare tooling inputs from the existing repository's native identity.

        Returns:
            The canonical request consumed by the modernizer.

        """
        root = target.root
        repository = target.repository
        project, metadata = identity
        return m.Infra.ToolingContextRequest(
            # Attached members resolve through the canonical workspace runtime
            # owner: runtime_environment_dir derives the superproject root when
            # the checkout is a submodule, and the checkout's own root otherwise.
            environment_dir=u.Infra.runtime_environment_dir(root),
            planned_sources={
                plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                for plan in planned
                if plan.path.suffix == c.Infra.EXT_PYTHON
                and plan.desired_content is not None
            },
            project_name=repository.distribution,
            package_name=metadata.package_name,
            path=root / c.PYPROJECT_FILENAME,
            codegen=codegen,
            runtime_dependency_overlay=project.runtime_dependency_overlay,
            declared_project_dependencies=metadata.project.dependencies,
            topology=self._existing_topology(target, codegen),
        )

    def _plan_existing_control(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.CodegenRepositoryPlanOutcome]:
        """Plan metadata and its bootstrap closure before Python source analysis.

        Returns:
            The existing repository outcome, or the original planning failure.

        """
        result_type = r[p.Infra.CodegenRepositoryPlanOutcome]
        root, codegen = target.root, inputs.spec
        manifest = next(
            (
                state
                for state in workspace.inputs
                if state.path == root / c.PYPROJECT_FILENAME
            ),
            None,
        )
        if manifest is None or manifest.content is None:
            if workspace.flext_source is not None:
                return self._plan_scaffold_control(target, workspace, inputs)
            return result_type.fail(
                f"control requires original project metadata: {root}"
            )
        managed = u.Infra.snapshot_project_managed_artifacts(root)
        if managed.failure:
            return result_type.from_failure(managed)
        render_inputs = self.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=None,
            managed_artifacts=managed.value,
        )
        formatted = self._control_metadata_source(
            target,
            workspace,
            render_inputs,
            manifest.path,
            manifest.content.decode(c.DEFAULT_ENCODING),
        )
        if formatted.failure:
            return result_type.from_failure(formatted)
        metadata = self._control_metadata_plan(
            target, workspace, inputs, formatted.value
        )
        if metadata.failure:
            return result_type.from_failure(metadata)
        return self._control_bootstrap_outcome(
            target, workspace, inputs, metadata.value
        )

    def _control_metadata_source(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        render_inputs: p.Infra.CodegenRenderInputs,
        manifest_path: Path,
        original_source: str,
    ) -> p.Result[str]:
        """Recover, overlay, conform, and format the control project metadata.

        The control candidate carries the same final form as the repository
        plan (``published_pyproject_source``); the run's one composed
        publication writes it once.

        Returns:
            The published conformed metadata source, or the first failure.

        """
        result_type = r[str]
        recovered = u.Infra.recover_live_pyproject_text(original_source)
        if recovered.failure:
            return result_type.from_failure(recovered)
        source = recovered.value
        project = workspace.project
        if project is not None and project.runtime_dependency_overlay:
            overlaid = self._control_dependency_overlay(
                target.root, project, manifest_path, original_source, source
            )
            if overlaid.failure:
                return overlaid
            source = overlaid.value
        conformed = self.conformed_pyproject_source(source, render_inputs)
        if conformed.failure:
            return result_type.from_failure(conformed)
        return u.Infra.format_toml_source(
            conformed.value, path=manifest_path, toolchain_root=target.toolchain_root
        ).map(self.published_pyproject_source)

    def _control_dependency_overlay(
        self,
        root: Path,
        project: p.Infra.ProjectSpec,
        manifest_path: Path,
        original_source: str,
        source: str,
    ) -> p.Result[str]:
        """Sync the declared runtime dependencies into the control metadata.

        Returns:
            The metadata source carrying the declared dependencies, or the
            first failure.

        """
        result_type = r[str]
        dependencies = self._declared_dependency_facts(
            root, project, manifest_source=original_source
        )
        if dependencies.failure:
            return result_type.from_failure(dependencies)
        document = u.Cli.toml_parse_text(source)
        if document is None:
            return result_type.fail(
                f"control project metadata is invalid: {manifest_path}"
            )
        project_table = u.Cli.toml_table_child(document, c.Infra.PROJECT)
        if project_table is None:
            return result_type.fail(f"control project table is absent: {manifest_path}")
        u.Cli.toml_sync_string_list(
            project_table, c.Infra.DEPENDENCIES, dependencies.value[0]
        )
        return result_type.ok(u.Cli.toml_dumps(document))

    def _control_metadata_plan(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        inputs: p.Infra.CodegenInputs,
        formatted: str,
    ) -> p.Result[p.Infra.CodegenFilePlan]:
        """Plan the formatted control metadata under its bootstrap ownership.

        Returns:
            The metadata file plan, or the binding or planning failure.

        """
        binding = self._bootstrap_template_binding(
            target, inputs.spec, c.PYPROJECT_FILENAME
        )
        if binding.failure:
            return r[p.Infra.CodegenFilePlan].from_failure(binding)
        return self.owned_file_plan(
            target.root,
            c.PYPROJECT_FILENAME,
            formatted,
            ownership=binding.value[1],
            inputs=(*workspace.inputs, *inputs.sources),
        )

    def _plan_scaffold_control(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        inputs: p.Infra.CodegenInputs,
    ) -> p.Result[p.Infra.CodegenRepositoryPlanOutcome]:
        """Use the native scaffold metadata context without a Python snapshot.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenRepositoryPlanOutcome]``.

        """
        result_type = r[p.Infra.CodegenRepositoryPlanOutcome]
        root, codegen, project = target.root, inputs.spec, workspace.project
        if project is None:
            return result_type.fail(f"scaffold control has no declared project: {root}")
        absent = self._scaffold_absent_metadata(root)
        if absent.failure:
            return result_type.from_failure(absent)
        managed = u.Infra.snapshot_project_managed_artifacts(root)
        if managed.failure:
            return result_type.from_failure(managed)
        tooling = self._scaffold_control_tooling(
            target, project, codegen, managed.value
        )
        if tooling.failure:
            return result_type.from_failure(tooling)
        render_inputs = self.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=tooling.value,
            managed_artifacts=managed.value,
        )
        metadata = self._scaffold_metadata_plan(
            target,
            codegen,
            render_inputs,
            (
                absent.value,
                *workspace.inputs,
                *inputs.sources,
                *tooling.value.sources,
            ),
        )
        if metadata.failure:
            return result_type.from_failure(metadata)
        return self._control_bootstrap_outcome(
            target, workspace, inputs, metadata.value
        )

    def _scaffold_metadata_plan(
        self,
        target: p.Infra.RepositoryConformTarget,
        codegen: p.Infra.CodegenConfigSpec,
        render_inputs: p.Infra.CodegenRenderInputs,
        observed: tuple[p.Cli.AtomicFileState, ...],
    ) -> p.Result[p.Infra.CodegenFilePlan]:
        """Render the scaffold project metadata through its bootstrap binding.

        Returns:
            The rendered metadata file plan, or the binding or render failure.

        """
        binding = self._bootstrap_template_binding(
            target, codegen, c.PYPROJECT_FILENAME
        )
        if binding.failure:
            return r[p.Infra.CodegenFilePlan].from_failure(binding)
        entry, managed = binding.value
        return self._rendered_managed_plan(
            render_inputs,
            managed,
            m.Infra.ArtifactRenderRoute.model_validate({
                "entry": (entry),
                "destination": (entry.destination),
                "failure_prefix": (""),
                "project_context": (None),
            }),
            target.root / c.PYPROJECT_FILENAME,
            inputs=observed,
        )

    @staticmethod
    def _scaffold_absent_metadata(root: Path) -> p.Result[p.Cli.AtomicFileState]:
        """Observe that scaffold project metadata is still absent.

        Returns:
            The absent metadata observation, or the failure when it was read
            unsuccessfully or appeared after election.

        """
        absent = u.Cli.atomic_read_binary_file_state(
            root / c.PYPROJECT_FILENAME, required=False
        )
        if absent.success and absent.value.content is not None:
            return r[p.Cli.AtomicFileState].fail(
                f"scaffold metadata changed after election: {root}"
            )
        return absent

    def _scaffold_control_tooling(
        self,
        target: p.Infra.RepositoryConformTarget,
        project: p.Infra.ProjectSpec,
        codegen: p.Infra.CodegenConfigSpec,
        managed: p.Infra.ProjectManagedArtifactsSnapshot,
    ) -> p.Result[p.Infra.ToolingRuntimeContext]:
        """Resolve the scaffold tooling context without deriving a runtime.

        Returns:
            The scaffold tooling context, or its resolution failure.

        """
        root = target.root
        return dependency_services.FlextInfraPyprojectModernizer(
            repository_root=root,
            skip_check=True,
            managed_artifacts=managed.resolution,
        ).resolve_tooling_context(
            m.Infra.ToolingContextRequest(
                environment_dir=u.Infra.runtime_environment_dir(
                    root, runtime_root=root
                ),
                planned_sources={},
                project_name=target.repository.distribution,
                package_name=project.package_name,
                path=root / c.PYPROJECT_FILENAME,
                codegen=codegen,
                runtime_dependency_overlay=project.runtime_dependency_overlay,
                declared_project_dependencies=(),
                topology=m.Infra.PyprojectDeclaredTopology(
                    root_modules=project.root_modules,
                    root_packages=project.root_packages,
                    repository_namespace_packages=project.repository_namespace_packages,
                    packaged_data_paths=project.packaged_data_paths,
                    declared_python_dirs=tuple(
                        self._scaffold_python_dirs(
                            codegen.templates.entries,
                            target.make_profile,
                            package=target.repository.package,
                        )
                    ),
                    declared_python_dirs_are_complete=(
                        target.make_profile is not c.Infra.MakeProfile.WORKSPACE
                    ),
                ),
            ),
        )

    def _control_bootstrap_outcome(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        inputs: p.Infra.CodegenInputs,
        metadata: p.Infra.CodegenFilePlan,
    ) -> p.Result[p.Infra.CodegenRepositoryPlanOutcome]:
        """Close bootstrap artifacts over the authenticated metadata candidate.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenRepositoryPlanOutcome]``.

        """
        result_type = r[p.Infra.CodegenRepositoryPlanOutcome]
        codegen = inputs.spec
        bootstrap_entry = codegen.templates.bootstrap_entry
        destinations = frozenset((
            *c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS,
            c.Infra.ENVRC_FILENAME,
            *(
                (bootstrap_entry.destination,)
                if u.Infra.codegen_bootstrap_provider_available(
                    bootstrap_entry, workspace
                )
                else ()
            ),
        ))
        previous = self.state.provider_plans
        self.state.provider_plans = u.Infra.codegen_compose_file_plans(
            (*(previous or ()), metadata), ordered=True
        )
        try:
            bootstrap = self._plan_existing_bootstrap(
                target, workspace, codegen, destinations=destinations
            )
        finally:
            self.state.provider_plans = previous
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        return result_type.ok(
            m.Infra.CodegenRepositoryPlanOutcome(
                repository=target.repository.name,
                files=u.Infra.codegen_compose_file_plans((metadata, *bootstrap.value)),
            )
        )

    def _plan_existing_bootstrap(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
        *,
        destinations: frozenset[str] = c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Render the bootstrap Make surface before sibling checkouts exist.

        The existing renderer elects each entry's context in native dependency
        order. Public surface roots retain their declared destinations.

        Returns:
            One authenticated file plan per destination, dependencies first.

        """
        result_type = r[Sequence[p.Infra.CodegenFilePlan]]
        graph = codegen.templates.artifact_requirements
        ordered = u.Cli.dag_closure(graph, destinations).flat_map(
            lambda closed: u.Cli.dag_order({name: graph[name] for name in closed})
        )
        if ordered.failure:
            return result_type.from_failure(ordered)
        # A dependency whose template declares no entry for the running
        # profile is not part of this profile's contract (a workspace-only
        # bootstrap requirement never applies to a standalone member): the
        # branch election skips it instead of failing the closure.
        ordered = ordered.map(
            lambda names: tuple(
                name
                for name in names
                if any(
                    entry.destination == name and target.make_profile in entry.profiles
                    for entry in codegen.templates.entries
                    if entry.source is not None
                )
            )
        )
        managed = u.Infra.snapshot_project_managed_artifacts(target.root)
        if managed.failure:
            return result_type.from_failure(managed)
        render_inputs = self.resolve_render_inputs(
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=None,
            managed_artifacts=managed.value,
        )
        plans: list[p.Infra.CodegenFilePlan] = []
        for destination in ordered.value:
            planned = self._bootstrap_destination_plan(
                render_inputs,
                destination,
                planned=plans,
            )
            if planned.failure:
                return result_type.from_failure(planned)
            plans.append(planned.value)
        return self._artifact_dependency_plans(codegen, target.root, plans)

    def _bootstrap_destination_plan(
        self,
        render_inputs: p.Infra.CodegenRenderInputs,
        destination: str,
        *,
        planned: Sequence[p.Infra.CodegenFilePlan] = (),
    ) -> p.Result[p.Infra.CodegenFilePlan]:
        """Render and plan exactly one bootstrap destination.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenFilePlan]``.

        """
        result_type = r[p.Infra.CodegenFilePlan]
        target = render_inputs.target
        codegen = render_inputs.codegen
        binding = self._bootstrap_template_binding(target, codegen, destination)
        if binding.failure:
            return result_type.from_failure(binding)
        entry, managed_spec = binding.value
        if not u.Infra.codegen_bootstrap_provider_available(
            entry, render_inputs.workspace
        ):
            return result_type.fail(
                f"bootstrap artifact provider is not declared: {destination}"
            )
        manifests = (
            self._candidate_manifests(planned)
            if entry.bootstrap_distribution is not None
            else ()
        )
        rendered = self._rendered_artifact_source(
            render_inputs,
            m.Infra.ArtifactRenderRoute.model_validate({
                "entry": (entry),
                "destination": (destination),
                "failure_prefix": (""),
                "project_context": (None),
                "planned_manifests": (manifests),
            }),
        )
        if rendered.failure:
            return result_type.from_failure(rendered)
        content = rendered.value.rendered
        conflict_marker = u.Infra.first_merge_conflict_marker(content)
        if conflict_marker is not None:
            return result_type.fail(
                f"rendered {destination} contains a merge conflict marker: "
                f"{conflict_marker}",
            )
        if destination == c.Infra.MISE_TOML_FILENAME:
            composed = self._composed_mise_overlay(target.root, content, render_inputs)
            if composed.failure:
                return result_type.from_failure(composed)
            content = composed.value
        return self.owned_file_plan(
            target.root,
            destination,
            content,
            ownership=managed_spec,
            inputs=(
                *rendered.value.source_states,
                *render_inputs.workspace.inputs,
                *render_inputs.managed_artifacts.sources,
                *(state for plan in manifests for state in (plan.before, *plan.inputs)),
            ),
        )

    @classmethod
    def _bootstrap_template_binding(
        cls,
        target: p.Infra.RepositoryConformTarget,
        codegen: p.Infra.CodegenConfigSpec,
        destination: str,
    ) -> p.Result[tuple[p.Infra.TemplateEntrySpec, p.Infra.ManagedFileSpec]]:
        """Resolve the single render template and managed spec of a destination.

        Args:
            target: The conform target whose profile selects templates.
            codegen: The codegen configuration owning template entries.
            destination: The bootstrap destination being planned.

        Returns:
            The original selected entry with its managed-file spec, or a failure
            when the destination lacks a unique binding.

        """
        result_type = r[tuple[p.Infra.TemplateEntrySpec, m.Infra.ManagedFileSpec]]
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == destination
            and entry.source is not None
            and target.make_profile in entry.profiles
        )
        if len(entries) != 1 or entries[0].source is None:
            return result_type.fail(
                f"{destination} requires exactly one render template for its profile",
            )
        managed = tuple(
            item
            for item in codegen.managed_file_specs
            if item.path == Path(destination)
        )
        if len(managed) != 1:
            return result_type.fail(
                f"{destination} requires exactly one managed-file declaration",
            )
        return result_type.ok((entries[0], managed[0]))

    def _plan_existing_docs_config(
        self,
        target: p.Infra.RepositoryConformTarget,
        workspace: p.Infra.WorkspaceSpec,
        codegen: p.Infra.CodegenConfigSpec,
        destination: str,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Render the declared docs policy before consumers parse its projection.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.CodegenFilePlan]]``.

        """
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == destination
            and entry.source is not None
            and target.make_profile in entry.profiles
        )
        managed = tuple(
            item
            for item in codegen.managed_file_specs
            if item.path == Path(destination)
        )
        if len(entries) != 1 or entries[0].source is None or len(managed) != 1:
            return r[Sequence[p.Infra.CodegenFilePlan]].fail(
                f"docs config requires one declared render template "
                f"and owner: {destination}",
            )
        template = u.Infra.codegen_templates_root(codegen) / entries[0].source
        rendered = u.Cli.template_render_authenticated(template, workspace)
        if rendered.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(rendered)
        parsed = u.Cli.json_loads(rendered.value.rendered)
        if parsed.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(parsed)
        plan = self.file_plan(
            target.root,
            destination,
            rendered.value.rendered,
            mode=managed[0].mode,
        )
        if plan.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(plan)
        return r[Sequence[p.Infra.CodegenFilePlan]].ok((plan.value,))

    def _plan_existing_templates(
        self,
        *,
        render_inputs: p.Infra.CodegenRenderInputs,
        contract: p.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Render the managed-file templates of one pass from one project context.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.CodegenFilePlan]]``.

        """
        with self.project_render_scope():
            return self._planned_existing_templates(
                render_inputs=render_inputs, contract=contract
            )

    def _planned_existing_templates(
        self,
        *,
        render_inputs: p.Infra.CodegenRenderInputs,
        contract: p.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Render the managed-file templates for an existing tree.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.CodegenFilePlan]]``.

        """
        target = render_inputs.target
        workspace = render_inputs.workspace
        codegen = render_inputs.codegen
        root = target.root
        u.Cli.info(f"  stage=templates repository={target.repository.name}")
        profile = target.make_profile
        planned: list[p.Infra.CodegenFilePlan] = []
        # The pyproject plans first: renders that derive from its requirements
        # (the dependabot cooldown exclusion) read the planned bytes.
        for managed in sorted(
            codegen.managed_file_specs,
            key=lambda item: item.path != Path(c.PYPROJECT_FILENAME),
        ):
            if self._managed_file_skipped(
                render_inputs,
                contract,
                managed,
            ):
                continue
            resolved = self._managed_render_entry(codegen, workspace, root, managed)
            if resolved.failure:
                u.Infra.codegen_raise_failure(root / managed.path, resolved)
            (entry, path), present = resolved.value
            if not present or entry is None or path is None:
                continue
            if (
                profile not in entry.profiles
                or (entry.requires_release_protocol and not target.publishes_release)
                or not u.Infra.codegen_bootstrap_provider_available(entry, workspace)
            ):
                if managed.policy != c.Infra.MANAGED_FILE_POLICY_FULL:
                    continue
                # Profile- and capability-excluded workflows must not keep firing.
                # Conform, rather than a user, retires the generated orphan.
                orphan = self._retired_workflow_orphan(
                    render_inputs,
                    managed,
                    entry,
                    path,
                )
                if orphan.failure:
                    u.Infra.codegen_raise_failure(path, orphan)
                planned.extend(orphan.value)
                continue
            rendered = self._rendered_managed_plan(
                render_inputs,
                managed,
                m.Infra.ArtifactRenderRoute.model_validate({
                    "entry": (entry),
                    "destination": (entry.destination),
                    "failure_prefix": (""),
                    "project_context": (None),
                    "planned_manifests": (self._candidate_manifests(planned)),
                }),
                path,
            )
            if rendered.failure:
                u.Infra.codegen_raise_failure(path, rendered)
            planned.append(rendered.value)
        return self._artifact_dependency_plans(codegen, root, planned)

    @staticmethod
    def _managed_file_skipped(
        render_inputs: p.Infra.CodegenRenderInputs,
        contract: p.Infra.CodegenConformSurfaceContract,
        managed: p.Infra.ManagedFileSpec,
    ) -> bool:
        """Whether this managed file is out of scope for the current surface.

        Returns:
            True when the file is skipped before any template resolution.

        """
        target = render_inputs.target
        codegen = render_inputs.codegen
        if target.beads is None and managed.path.parts[:1] == (".beads",):
            return True
        if not target.ci_enabled and managed.path.parts[:2] == (
            ".github",
            "workflows",
        ):
            return True
        if (
            contract.destinations is not None
            and managed.path.as_posix()
            not in u.Cli.dag_closure(
                codegen.templates.artifact_requirements,
                contract.destinations,
            ).unwrap()
        ):
            return True
        return managed.path == Path(c.PYPROJECT_FILENAME) and not contract.pyproject

    @staticmethod
    def _managed_render_entry(
        codegen: p.Infra.CodegenConfigSpec,
        workspace: p.Infra.WorkspaceSpec,
        root: Path,
        managed: p.Infra.ManagedFileSpec,
    ) -> p.Result[tuple[tuple[p.Infra.TemplateEntrySpec | None, Path | None], bool]]:
        """Resolve the single render template entry and its physical target path.

        Returns:
            The resulting ``p.Result[tuple[tuple[p.Infra.TemplateEntrySpec |
            None, Path | None], bool]]`` where the boolean selects template
            rendering rather than an absent capability or specialized owner.

        """
        result_type = r[
            tuple[tuple[p.Infra.TemplateEntrySpec | None, Path | None], bool]
        ]
        entries = tuple(
            entry
            for entry in codegen.templates.entries
            if entry.destination == managed.path.as_posix()
        )
        if not entries:
            return result_type.fail(
                f"managed file has no artifact declaration: {managed.path}",
            )
        if len(entries) != 1:
            return result_type.fail(
                f"managed file requires exactly one render template: {managed.path}",
            )
        entry = entries[0]
        if entry.requires_beads and workspace.beads is None:
            return result_type.ok(((None, None), False))
        path = FlextInfraCodegenConformExistingPlan._managed_entry_path(root, entry)
        if path.failure:
            return result_type.from_failure(path)
        return result_type.ok(((entry, path.value), entry.source is not None))

    @staticmethod
    def _managed_entry_path(
        root: Path,
        entry: p.Infra.TemplateEntrySpec,
    ) -> p.Result[Path]:
        """Resolve and confine one managed destination inside the repository root.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        relative = Path(entry.destination)
        if relative.is_absolute() or ".." in relative.parts:
            return r[Path].fail(
                f"managed destination escapes repository root: {entry.destination}",
            )
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            return r[Path].fail(
                f"managed destination escapes repository root: {entry.destination}",
            )
        return r[Path].ok(path)

    @staticmethod
    def _retired_workflow_orphan(
        render_inputs: p.Infra.CodegenRenderInputs,
        managed: p.Infra.ManagedFileSpec,
        entry: p.Infra.TemplateEntrySpec,
        path: Path,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Retire one inapplicable full-owned artifact through its catalog owner.

        The same declaration authorizes updates and retirement; file headers
        are not ownership inputs.

        Returns:
            The owned retirement plan, or no effects for an absent destination.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan, ...]]
        if (
            entry.ownership is None
            or entry.ownership.policy != c.Infra.MANAGED_FILE_POLICY_FULL
            or managed.policy != c.Infra.MANAGED_FILE_POLICY_FULL
            or entry.source is None
        ):
            return result_type.fail(
                f"artifact retirement requires full template ownership: {path}",
            )
        target = render_inputs.target
        if (
            target.make_profile in entry.profiles
            and (not entry.requires_release_protocol or target.publishes_release)
            and u.Infra.codegen_bootstrap_provider_available(
                entry, render_inputs.workspace
            )
        ):
            return result_type.fail(
                f"applicable catalog artifact cannot be retired: {path}",
            )
        if not path.exists() and not path.is_symlink():
            return result_type.ok(())
        before = u.Cli.atomic_read_binary_file_state(path, required=True)
        if before.failure:
            return result_type.from_failure(before)
        return result_type.ok((
            m.Infra.CodegenFilePlan(
                project=render_inputs.target.root.expanduser().absolute(),
                path=path,
                before=before.value,
                desired_content=None,
                desired_mode=None,
                owner=managed.owner,
                policy=managed.policy,
                inputs=render_inputs.workspace.inputs,
            ),
        ))

    def _rendered_managed_plan(
        self,
        render_inputs: p.Infra.CodegenRenderInputs,
        managed: p.Infra.ManagedFileSpec,
        route: p.Infra.ArtifactRenderRoute,
        path: Path,
        *,
        inputs: tuple[p.Cli.AtomicFileState, ...] = (),
    ) -> p.Result[p.Infra.CodegenFilePlan]:
        """Render, compose, record, and plan one managed artifact.

        Returns:
            The finalized file plan using this operation's existing render state.

        """
        result_type = r[p.Infra.CodegenFilePlan]
        root = render_inputs.target.root
        entry, planned_manifests = route.entry, route.planned_manifests
        rendered = (
            r[p.Cli.AuthenticatedTemplateRender].fail(
                f"managed render entry has no template source: {entry.destination}",
            )
            if entry.source is None
            else self._rendered_artifact_source(render_inputs, route)
        )
        if rendered.failure:
            u.Cli.error(
                f"artifact render failed: {entry.destination}: {rendered.error}"
            )
            return result_type.from_failure(rendered)
        composed = (
            rendered.map(lambda payload: payload.rendered)
            if entry.source_kind == "resource"
            else self.compose_project_artifact(
                root,
                entry.destination,
                rendered.value.rendered,
                render_inputs=render_inputs,
            )
        )
        if composed.failure:
            u.Cli.error(
                f"artifact composition failed: {entry.destination}: {composed.error}"
            )
            return result_type.from_failure(composed)
        rendered_content = composed.value
        names = None
        if entry.destination == c.PYPROJECT_FILENAME:
            names = self.direct_sources(render_inputs, composed=rendered_content)
            if names.failure:
                return result_type.from_failure(names)
        conflict_marker = u.Infra.first_merge_conflict_marker(rendered_content)
        if conflict_marker is not None:
            return result_type.fail(
                "rendered template contains a merge conflict marker: "
                f"source={entry.source}; target={path}; root={root}; "
                f"marker={conflict_marker}",
            )
        planned = self.owned_file_plan(
            root,
            entry.destination,
            rendered_content,
            ownership=managed,
            inputs=(
                *inputs,
                *rendered.value.source_states,
                *(
                    ()
                    if entry.bootstrap_distribution is None
                    else (
                        *render_inputs.workspace.inputs,
                        *(
                            state
                            for plan in planned_manifests
                            for state in (plan.before, *plan.inputs)
                        ),
                    )
                ),
            ),
        )
        if planned.success and names is not None:
            render_inputs.planned_direct_sources = names.value
        return planned

    def _plan_existing_custom(
        self,
        root: Path,
        config: p.Infra.CodegenConfigSpec,
        *,
        profile: str | None = None,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Validate custom Make content and stage dependency-ordered family facades.

        Existing handwritten Make content is validated against the selected
        profile policy. The canonical source inventory contributes declared
        facade families from every owned package, including internal test and
        auxiliary namespaces. Each subsequent family binds the prior candidate.
        The component owner borrows this invocation's existing source views;
        identical epochs reuse inference and changed effects rebind before use.
        This method returns file plans; it does not publish their contents.

        Returns:
            The custom Make and facade plans, or a typed validation failure.

        """
        started = time.monotonic()
        u.Cli.info(f"stage=facades state=start root={root}")
        policy = config.make.custom_handler_policies.get(
            profile or "",
            config.make.custom_handler_policy,
        )
        plans: list[p.Infra.CodegenFilePlan] = []
        make_plan = self._validated_custom_make_plan(root, policy)
        if make_plan.failure:
            u.Infra.codegen_raise_failure(root / policy.filename, make_plan)
        make_plan_value, make_plan_present = make_plan.value
        if make_plan_present and make_plan_value is not None:
            plans.append(make_plan_value)
        if root.is_dir():
            snapshot = self.state.snapshot
            ports = self.state.ports
            if snapshot is None or ports is None:
                return r[Sequence[p.Infra.CodegenFilePlan]].fail(
                    "recursive family composition requires caller-bound "
                    "planning and an authenticated repository snapshot"
                )
            recursive = self._component_projection(root, declared_files, selection=None)
            if recursive.failure:
                return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(recursive)
            plans.extend(recursive.value)
        u.Cli.info(
            f"stage=facades state=end root={root} "
            f"elapsed={time.monotonic() - started:.3f}s files={len(plans)}"
        )
        return r[Sequence[p.Infra.CodegenFilePlan]].ok(tuple(plans))

    def _validated_custom_make_plan(
        self,
        root: Path,
        policy: p.Infra.CustomHandlerPolicy,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan | None, bool]]:
        """Validate and plan the existing custom Make content under its policy.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.CodegenFilePlan | None,
            bool]]`` where the boolean marks plan presence (False: an absent
            custom Make file).

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan | None, bool]]
        path = root / policy.filename
        if path.exists() and not path.is_file():
            return result_type.fail(
                f"custom Make destination is not a regular file: {path}",
            )
        if not path.is_file():
            return result_type.ok((None, False))
        read = u.Cli.files_read_text(path)
        if read.failure:
            return result_type.from_failure(read)
        validation = self.validate_custom_make(read.value, policy)
        if validation.failure:
            return result_type.from_failure(validation)
        planned = self.file_plan(root, policy.filename, read.value)
        if planned.failure:
            return result_type.from_failure(planned)
        return result_type.ok((planned.value, True))

    def _complete_governed_plans(
        self,
        target: p.Infra.RepositoryConformTarget,
        planned: Sequence[p.Infra.CodegenFilePlan],
        codegen: p.Infra.CodegenConfigSpec,
        contract: p.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[Sequence[p.Infra.CodegenFilePlan]]:
        """Attach ownership metadata and represent every governed root artifact.

        Only the ``ALL`` surface completes the full governed set; the
        pyproject-scoped surfaces (``DEPENDENCIES``/``PYPROJECT``) keep the plan
        restricted to what their own planners already produced.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.CodegenFilePlan]]``.

        """
        root = target.root
        governed_by_path = {
            item.path: item
            for item in codegen.managed_file_specs
            if target.beads is not None or item.path.parts[:1] != (".beads",)
        }
        bound = self._bind_governed_ownership(root, planned, governed_by_path)
        if bound.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(bound)
        completed, represented = bound.value
        if not contract.complete_governed:
            return r[Sequence[p.Infra.CodegenFilePlan]].ok(tuple(completed))
        pending_artifacts = {
            path: item
            for path, item in governed_by_path.items()
            if path not in represented
        }
        represented_set = self._represent_ungoverned_artifacts(
            target,
            codegen,
            pending_artifacts,
        )
        if represented_set.failure:
            return r[Sequence[p.Infra.CodegenFilePlan]].from_failure(
                represented_set,
            )
        completed.extend(represented_set.value)
        return r[Sequence[p.Infra.CodegenFilePlan]].ok(tuple(completed))

    @staticmethod
    def _bind_governed_ownership(
        root: Path,
        planned: Sequence[p.Infra.CodegenFilePlan],
        governed_by_path: Mapping[Path, p.Infra.ManagedFileSpec],
    ) -> p.Result[tuple[list[p.Infra.CodegenFilePlan], set[Path]]]:
        """Stamp governed ownership onto the planned files, first plan wins.

        Returns:
            The resulting ``p.Result[tuple[list[p.Infra.CodegenFilePlan],
                set[Path]]]`` with the bound plans and the represented paths.

        """
        completed: list[p.Infra.CodegenFilePlan] = []
        represented: set[Path] = set()
        represented_indexes: MutableMapping[Path, int] = {}
        for file in planned:
            relative = file.path.relative_to(root)
            governed = governed_by_path.get(relative)
            if governed is None:
                completed.append(file)
                continue
            represented.add(relative)
            governed_file = file.model_copy(
                update={
                    "owner": governed.owner,
                    "policy": governed.policy,
                    "desired_mode": (
                        governed.mode if file.desired_content is not None else None
                    ),
                },
            )
            if relative in represented_indexes:
                completed[represented_indexes[relative]] = governed_file
            else:
                represented_indexes[relative] = len(completed)
                completed.append(governed_file)
        return r[tuple[list[p.Infra.CodegenFilePlan], set[Path]]].ok(
            (completed, represented),
        )

    def _represent_ungoverned_artifacts(
        self,
        target: p.Infra.RepositoryConformTarget,
        codegen: p.Infra.CodegenConfigSpec,
        governed_by_path: Mapping[Path, p.Infra.ManagedFileSpec],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan every unrepresented governed artifact in the mapping.

        Args:
            target: The conform target whose root owns the artifacts.
            codegen: The codegen configuration governing the artifacts.
            governed_by_path: Governed artifacts keyed by repository-relative
                path.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.CodegenFilePlan, ...]]``
            carrying one plan per represented artifact.

        Raises:
            ValueError: When a governed artifact path is not a regular file.

        """
        plans: list[p.Infra.CodegenFilePlan] = []
        root = target.root
        vscode_spec = target.vscode_spec
        for relative, governed in governed_by_path.items():
            path = root / relative
            if path.exists() and not path.is_file():
                msg = f"governed artifact is not a regular file: {path}"
                raise ValueError(msg)
            if not self._governed_entry_reachable(codegen, target, relative):
                continue
            if not path.exists() and governed.policy != "merge":
                continue
            current = self._governed_current_text(path)
            if current.failure:
                u.Infra.codegen_raise_failure(path, current)
            request = m.Infra.CodegenGovernedPlanRequest.model_validate({
                "root": (root),
                "relative": (relative),
                "governed": (governed),
                "current": (current.value),
                "vscode_spec": (vscode_spec),
            })
            decided = self._decide_governed_plan(request)
            if decided.failure:
                u.Infra.codegen_raise_failure(path, decided)
            decided_value, decided_present = decided.value
            if decided_present and decided_value is not None:
                plans.append(decided_value)
        return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(tuple(plans))

    @staticmethod
    def _governed_entry_reachable(
        codegen: p.Infra.CodegenConfigSpec,
        target: p.Infra.RepositoryConformTarget,
        relative: Path,
    ) -> bool:
        """Whether the artifact admits this profile and its selected capabilities.

        Returns:
            True only for a declared artifact applicable to this target.

        """
        if (
            not target.ci_enabled and relative.parts[:2] == (".github", "workflows")
        ) or (
            relative == Path(c.PYPROJECT_FILENAME)
            and target.make_profile is c.Infra.MakeProfile.WORKSPACE
            and target.project is None
        ):
            return False
        return any(
            entry.destination == relative.as_posix()
            and target.make_profile in entry.profiles
            and (not entry.requires_beads or target.beads is not None)
            and (not entry.requires_release_protocol or target.publishes_release)
            for entry in codegen.templates.entries
        )

    @staticmethod
    def _governed_current_text(path: Path) -> p.Result[str]:
        """Read the current bytes of an existing governed artifact.

        Returns:
            The resulting ``p.Result[str]``, empty for a non-file path.

        """
        if not path.is_file():
            return r[str].ok("")
        read = u.Cli.atomic_read_binary_file_state(path, required=True)
        if read.failure:
            return r[str].from_failure(read)
        content = read.value.content
        if content is None:
            error = ValueError(f"governed artifact has no captured bytes: {path}")
            return r[str].fail(str(error), exception=error)
        return r[str].create_from_callable(partial(content.decode, c.DEFAULT_ENCODING))

    @classmethod
    def _decide_governed_plan(
        cls,
        request: p.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan | None, bool]]:
        """Require the existing specialized planner for an unrendered artifact.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        special = cls._special_governed_plan(request)
        if special.failure:
            return special
        if special.value[0] is not None:
            return special
        return r[tuple[p.Infra.CodegenFilePlan | None, bool]].fail(
            "managed artifact has no specialized projection owner: "
            f"{request.relative} (owner={request.governed.owner})",
        )

    @classmethod
    def _special_governed_plan(
        cls,
        request: p.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan | None, bool]]:
        """Plan owner-specific merge behavior for special governed artifacts.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.CodegenFilePlan | None,
            bool]]`` where the boolean identifies a declared rendering owner.

        """
        vscode_merge = request.governed.policy == "merge" and (
            request.governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
        )
        if vscode_merge:
            # Owner-merge dispatch: owners with a canonical document merge
            # (vscode settings today) produce their rendered content here.
            return cls._vscode_merged_plan(request)
        if request.governed.policy == "merge" and request.relative.as_posix() == (
            c.Infra.ENVRC_LOCAL_RELPATH
        ):
            # Local overrides never carry generated content: the merge strips
            # stale generated sections and deletes the file when nothing
            # custom remains, so `.envrc` stays the single beads owner.
            return cls._envrc_local_plan(request)
        return r[tuple[p.Infra.CodegenFilePlan, bool]].ok((None, False))

    @classmethod
    def _vscode_merged_plan(
        cls,
        request: p.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan | None, bool]]:
        """Render the canonical vscode settings merge when it diverges.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan | None, bool]]
        spec = request.vscode_spec
        if spec is None:
            loaded = u.Infra.load_codegen_inputs(request.root)
            if loaded.failure:
                return result_type.from_failure(loaded)
            spec = loaded.value.spec.vscode
        merged = cls.render_vscode_settings(
            request.root,
            spec=spec,
        )
        if merged.failure:
            return result_type.from_failure(merged)
        return cls.owned_file_plan(
            request.root,
            request.relative.as_posix(),
            merged.value,
            ownership=request.governed,
        ).map(lambda plan: (plan, True))

    @classmethod
    def _envrc_local_plan(
        cls,
        request: p.Infra.CodegenGovernedPlanRequest,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan | None, bool]]:
        """Normalize the local envrc overrides or plan the file's deletion.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.CodegenFilePlan | None,
            bool]]`` with its presence flag.

        """
        result_type = r[tuple[p.Infra.CodegenFilePlan | None, bool]]
        root = request.root
        relative = request.relative
        path = root / relative
        normalized = (
            workspace_services.FlextInfraWorkspaceEnvironmentContracts.envrc_local_normalized
        )(
            request.current,
        )
        if normalized and normalized == request.current:
            return cls.owned_file_plan(
                root,
                relative.as_posix(),
                request.current,
                ownership=request.governed,
            ).map(lambda plan: (plan, True))
        if not normalized:
            before = u.Cli.atomic_read_binary_file_state(path, required=False)
            if before.failure:
                return result_type.from_failure(before)
            return result_type.ok(
                (
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=before.value,
                        desired_content=None,
                        desired_mode=None,
                        owner=request.governed.owner,
                        policy=request.governed.policy,
                    ),
                    True,
                ),
            )
        return cls.owned_file_plan(
            root,
            relative.as_posix(),
            normalized,
            ownership=request.governed,
        ).map(lambda plan: (plan, True))


__all__: list[str] = ["FlextInfraCodegenConformExistingPlan"]
