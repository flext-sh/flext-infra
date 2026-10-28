"""Lazy-init ``__init__.py`` planning orchestrator (PEP 562).

Binds the run's source view, indexes each selected repository, and delegates
planning, letter election and rendering to the ``u.Infra.lazy_init_*``
owners; publication belongs to the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, override

from flext_cli import u

from flext_infra import FlextInfraUtilities, c, m, p, r
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesLazyInitPlan,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra.codegen import FlextInfraCodegenExecution
from flext_infra.deps.phases.tool_tables import FlextInfraToolTablesPhase


class FlextInfraCodegenLazyInit(
    FlextInfraCodegenExecution[bool],
    m.Infra.ModuleSelectionMixin,
    FlextInfraUtilities,
):
    """Plan every generated ``__init__.py`` of the selected repositories."""

    project_scope_roots: Annotated[
        Sequence[Path] | None,
        m.Field(
            description=(
                "Repository roots selected by conformance; None plans every "
                "package of the repository root"
            ),
        ),
    ] = None

    @classmethod
    def plan_candidate(
        cls,
        root: Path,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        snapshot: p.Infra.WorkspaceSnapshot,
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None = None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Plan this candidate's exports through the existing public initializer.

        A selected facade retains its package and private-family projections,
        plus initializer consumers already changed by authenticated native moves.
        A selected package retains its descendants and affected native consumers;
        its absent family does not select every family in the repository.
        None preserves the complete repository planning contract.
        The snapshot retains ownership of the native project; the candidate
        borrows it only for this scoped initializer binding.

        Returns:
            The same initializer cohort for conformance and source composition.

        """
        with FlextInfraUtilities.Infra.facade_source_project(
            root,
            declared_files=declared_files,
            source_project=snapshot.engine,
        ) as (
            project,
            sources,
        ):
            if selection is not None and selection[1] is None:
                destination = selection[0]
                consumers = {
                    plan.path.parent / c.Infra.INIT_PY
                    for plan in declared_files
                    if plan.project == root
                    and plan.path.suffix == c.Infra.EXT_PYTHON
                    and FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect(
                        plan
                    )
                    and plan.path.parent / c.Infra.INIT_PY in sources
                }
                files: dict[Path, m.Infra.CodegenFilePlan] = {}
                for target in sorted({destination, *consumers}):
                    module = FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                        target, project_root=root, source_project=project
                    )
                    if not module:
                        return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                            f"selected initializer has no native package: {target}"
                        )
                    planned = cls(
                        repository_root=root,
                        project_scope_roots=(root,),
                        module=module,
                    ).plan_files(source_project=project, snapshot=snapshot)
                    if planned.failure:
                        return planned
                    files.update(
                        (file.path, file)
                        for file in planned.value
                        if file.path.is_relative_to(destination.parent)
                        or file.path in consumers
                    )
                return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(
                    tuple(files[path] for path in sorted(files))
                )
            planned = cls(repository_root=root, project_scope_roots=(root,)).plan_files(
                source_project=project, snapshot=snapshot
            )
            if selection is None:
                return planned
            destination, family = selection
            family_root = (
                destination.parent
                if family is None
                else destination.parent
                / FlextInfraUtilities.Infra.facade_families()[family].directory
            )
            consumers = {
                plan.path
                for plan in declared_files
                if plan.path.name == c.Infra.INIT_PY
                and FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect(
                    plan
                )
            }

            def family_files(
                files: Sequence[m.Infra.CodegenFilePlan],
            ) -> Sequence[m.Infra.CodegenFilePlan]:
                return tuple(
                    file
                    for file in files
                    if file.path.is_relative_to(family_root)
                    or file.path == destination.parent / c.Infra.INIT_PY
                    or file.path in consumers
                )

            return planned.map(family_files)

    @override
    def execute(self) -> p.Result[bool]:
        """Check lazy-init drift; publication belongs to conform.

        Returns:
            Success when every planned initializer matches its source.

        """
        planned = self.plan_files()
        if planned.failure:
            return r[bool].from_failure(planned)
        if not self.effective_dry_run:
            return r[bool].fail(c.Infra.LazyInitMessage.PUBLICATION_OWNED_BY_CONFORM)
        changed = tuple(
            str(plan.path)
            for plan in planned.value
            if FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect(plan)
        )
        if changed:
            return r[bool].fail(
                c.Infra.LazyInitMessage.DRIFT.format(
                    count=len(changed), paths=", ".join(changed)
                )
            )
        return r[bool].ok(value=True)

    def plan_files(
        self,
        *,
        source_project: p.Infra.RopeProject | None = None,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Return the immutable initializer plans; publication belongs to conform.

        The index of every selected root is a view over the run snapshot's
        listing; a caller without a run snapshot gets one scoped to this plan.

        Returns:
            The initializer file plans sorted by path, or the first failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        message = c.Infra.LazyInitMessage
        workspace = self.repository_root.resolve()
        started = time.monotonic()
        u.Cli.info(f"stage=lazy-init state=start root={workspace}")
        scoped = self.project_scope_roots is not None
        roots = tuple(
            sorted({root.resolve() for root in self.project_scope_roots or ()})
        ) or (workspace,)
        if not (
            workspace.is_dir()
            if source_project is None
            else source_project.source_query(workspace, "isdir")
        ):
            return result_type.fail(
                message.WORKSPACE_NOT_DIR.format(workspace=workspace)
            )
        with (
            self._source_view(workspace, source_project, roots) as view,
            self._run_snapshot(workspace, roots, snapshot) as shared,
        ):
            invalid = next(
                (
                    root
                    for root in roots
                    if not root.is_relative_to(workspace)
                    or not view.source_query(root, "isdir")
                ),
                None,
            )
            if invalid is not None:
                return result_type.fail(
                    message.SCOPE_OUTSIDE.format(workspace=workspace, root=invalid)
                )
            indexes = {
                root: FlextInfraUtilitiesRopeAnalysisWorkspace.index_rope_workspace(
                    shared,
                    root,
                    project=None if view is shared.engine else view,
                    project_roots=(root,) if scoped else None,
                )
                for root in roots
            }
            targets = self._targets(indexes, scoped=scoped)
            if targets.failure:
                return result_type.from_failure(targets)
            by_path: dict[Path, m.Infra.CodegenFilePlan] = {}
            for root, target in targets.value.items():
                planned = self._plan_root(
                    FlextInfraUtilitiesLazyInitPlan.lazy_init_run(
                        view,
                        indexes[root],
                        root=root,
                        scoped=scoped,
                        snapshot=shared,
                    ),
                    target,
                )
                if planned.failure:
                    return planned
                for file_plan in planned.value:
                    if by_path.setdefault(file_plan.path, file_plan) != file_plan:
                        return result_type.fail(
                            message.CONFLICTING_PLANS.format(path=file_plan.path)
                        )
        files = tuple(by_path[path] for path in sorted(by_path))
        effects = sum(
            map(
                FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect,
                files,
            )
        )
        u.Cli.info(
            f"stage=lazy-init state=end root={workspace} "
            f"elapsed={time.monotonic() - started:.3f}s files={len(files)} "
            f"effects={effects}"
        )
        return result_type.ok(files)

    def _targets(
        self,
        indexes: Mapping[Path, m.Infra.RopeWorkspaceIndex],
        *,
        scoped: bool,
    ) -> p.Result[Mapping[Path, Path | None]]:
        """Select each root's target package; ``None`` plans the whole root.

        Returns:
            The planned roots with their target, or an unresolved selection.

        """
        result_type = r[Mapping[Path, Path | None]]
        if not self.module:
            return result_type.ok(dict.fromkeys(indexes))
        found = {
            root: FlextInfraUtilitiesLazyInitPlan.lazy_init_target_dirs(
                index, root, module=self.module, scoped=scoped
            )
            for root, index in indexes.items()
        }
        selected = {root: dirs[0] for root, dirs in found.items() if dirs}
        if sum(map(len, found.values())) != 1:
            template = (
                c.Infra.LazyInitMessage.TARGET_AMBIGUOUS
                if selected
                else c.Infra.LazyInitMessage.TARGET_NOT_FOUND
            )
            return result_type.fail(template.format(module=self.module))
        return result_type.ok(selected)

    @staticmethod
    def _plan_root(
        run: m.Infra.LazyInitRun,
        target: Path | None,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Plan and render one repository bottom-up from its source inventory.

        Returns:
            The repository's initializer file plans, or the first failure.

        """
        plans = FlextInfraUtilitiesLazyInitPlan.lazy_init_plan_root(run, target)
        if plans.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(plans)
        owners = {
            FlextInfraUtilitiesLazyInitRender.lazy_init_project_root(
                run.model, plan.context.pkg_dir
            )
            for plan in plans.value
        }
        return FlextInfraUtilitiesLazyInitPlan.lazy_init_file_plans(
            run,
            plans.value,
            first_party={
                owner: frozenset(
                    FlextInfraToolTablesPhase.first_party_namespaces(
                        path=owner, source_project=run.model.source_project
                    )
                )
                for owner in owners
            },
        )

    @staticmethod
    @contextmanager
    def _run_snapshot(
        workspace: Path,
        roots: tuple[Path, ...],
        snapshot: p.Infra.WorkspaceSnapshot | None,
    ) -> Generator[p.Infra.WorkspaceSnapshot]:
        """Bind the run's snapshot without replacing an injected one.

        Yields:
            The injected snapshot, or one scoped to this plan.

        """
        if snapshot is not None:
            yield snapshot
            return
        with FlextInfraUtilitiesWorkspaceSnapshot.workspace_snapshot(
            workspace, tuple(dict.fromkeys((workspace, *roots)))
        ) as scoped:
            yield scoped

    @staticmethod
    @contextmanager
    def _source_view(
        workspace: Path,
        source_project: p.Infra.RopeProject | None,
        roots: tuple[Path, ...],
    ) -> Generator[p.Infra.RopeProject]:
        """Bind the run's source view without replacing an injected one.

        Yields:
            The source view every source is read through.

        Raises:
            ValueError: When the injected view does not cover the workspace.

        """
        if source_project is not None:
            if not workspace.is_relative_to(Path(source_project.root.real_path)):
                raise ValueError(c.Infra.LazyInitMessage.VIEW_OUTSIDE)
            yield source_project
            return
        with FlextInfraUtilitiesCodegenFacades.facade_source_project(
            workspace,
            project_roots=tuple(
                root for root in roots if root.is_relative_to(workspace)
            ),
        ) as (project, _):
            yield project


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
