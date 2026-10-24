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

from flext_infra import c, d, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenExecutionBase
from flext_infra.deps.phases import FlextInfraToolTablesPhase


class FlextInfraCodegenLazyInit(
    FlextInfraCodegenExecutionBase[bool],
    m.Infra.ModuleSelectionMixin,
):
    """Plan every generated ``__init__.py`` of the selected repositories."""

    project_scope_roots: Annotated[
        t.VariadicTuple[Path] | None,
        m.Field(
            description=(
                "Repository roots selected by conformance; None plans every "
                "package of the repository root"
            ),
        ),
    ] = None

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
            if u.Infra.codegen_file_requires_effect(plan)
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
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Return the immutable initializer plans; publication belongs to conform.

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
        with self._source_view(workspace, source_project, roots) as view:
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
            indexes = {root: u.Infra.index_rope_workspace(view, root) for root in roots}
            targets = self._targets(indexes, scoped=scoped)
            if targets.failure:
                return result_type.from_failure(targets)
            by_path: dict[Path, m.Infra.CodegenFilePlan] = {}
            for root, target in targets.value.items():
                planned = self._plan_root(
                    view, indexes[root], root, target, scoped=scoped
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
                effects=sum(map(u.Infra.codegen_file_requires_effect, files))
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
            root: u.Infra.lazy_init_target_dirs(
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
        view: p.Infra.RopeProject,
        index: m.Infra.RopeWorkspaceIndex,
        root: Path,
        target: Path | None,
        *,
        scoped: bool,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan and render one repository bottom-up from its source inventory.

        Returns:
            The repository's initializer file plans, or the first failure.

        """
        run = u.Infra.lazy_init_run(view, index, root=root, scoped=scoped)
        plans = u.Infra.lazy_init_plan_root(run, target)
        if plans.failure:
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(plans)
        owners = {
            u.Infra.lazy_init_project_root(run.model, plan.context.pkg_dir)
            for plan in plans.value
        }
        return u.Infra.lazy_init_file_plans(
            run,
            plans.value,
            first_party={
                owner: frozenset(
                    FlextInfraToolTablesPhase.first_party_namespaces(
                        path=owner, source_project=view
                    )
                )
                for owner in owners
            },
        )

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
        with u.Infra.facade_source_project(
            workspace,
            project_roots=tuple(
                root for root in roots if root.is_relative_to(workspace)
            ),
        ) as (project, _):
            yield project


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
