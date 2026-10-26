"""Lazy-init ``__init__.py`` planning orchestrator (PEP 562).

Binds the run's source view, indexes each selected repository, and delegates
planning, letter election and rendering to the ``u.Infra.lazy_init_*``
owners; publication belongs to the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, override

from flext_cli import u

from flext_infra import c, d, m, p, r, t
from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities.codegen_facades import FlextInfraUtilitiesCodegenFacades
from flext_infra._utilities.codegen_file_plan import FlextInfraUtilitiesCodegenFilePlan
from flext_infra._utilities.lazy_init_plan import FlextInfraUtilitiesLazyInitPlan
from flext_infra._utilities.lazy_init_render import FlextInfraUtilitiesLazyInitRender
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra.codegen._execution import FlextInfraCodegenExecutionBase
from flext_infra.deps.phases.tool_tables import FlextInfraToolTablesPhase


class FlextInfraCodegenLazyInit(
    FlextInfraCodegenExecutionBase[bool],
    m.Infra.ModuleSelectionMixin,
    FlextInfraUtilitiesCodegenFacades,
):
    """Plan every generated ``__init__.py`` of the selected repositories."""

    project_scope_roots: Annotated[
        t.SequenceOf[Path] | None,
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
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        snapshot: p.Infra.WorkspaceSnapshot,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan this candidate's exports through the existing public initializer.

        Returns:
            The same initializer cohort for conformance and source composition.

        """
        with cls.facade_source_project(root, declared_files=declared_files) as (
            project,
            _sources,
        ):
            return cls(repository_root=root, project_scope_roots=(root,)).plan_files(
                source_project=project, snapshot=snapshot
            )

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

    @d.log_operation("lazy_init_plan", track_perf=True)
    def plan_files(
        self,
        *,
        source_project: p.Infra.RopeProject | None = None,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Return the immutable initializer plans; publication belongs to conform.

        The index of every selected root is a view over the run snapshot's
        listing; a caller without a run snapshot gets one scoped to this plan.

        Returns:
            The initializer file plans sorted by path, or the first failure.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        message = c.Infra.LazyInitMessage
        workspace = self.repository_root.resolve()
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
        u.Cli.info(
            message.PLAN_SUMMARY.format(
                effects=sum(
                    map(
                        FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect,
                        files,
                    )
                )
            )
        )
        return result_type.ok(files)

    def _targets(
        self,
        indexes: t.MappingKV[Path, m.Infra.RopeWorkspaceIndex],
        *,
        scoped: bool,
    ) -> p.Result[t.MappingKV[Path, Path | None]]:
        """Select each root's target package; ``None`` plans the whole root.

        Returns:
            The planned roots with their target, or an unresolved selection.

        """
        result_type = r[t.MappingKV[Path, Path | None]]
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
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan and render one repository bottom-up from its source inventory.

        Returns:
            The repository's initializer file plans, or the first failure.

        """
        plans = FlextInfraUtilitiesLazyInitPlan.lazy_init_plan_root(run, target)
        if plans.failure:
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(plans)
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
        roots: t.VariadicTuple[Path],
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
        roots: t.VariadicTuple[Path],
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
