"""Canonical file-plan composition for generated package initializers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenGeneration,
    FlextInfraCodegenLazyInitGenerationRegistryMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInitGenerationFilePlanMixin(
    FlextInfraCodegenLazyInitGenerationRegistryMixin,
):
    """Convert resolved lazy-init decisions into immutable file plans."""

    @staticmethod
    def _generated_source_dirs(
        package_dir: Path,
        *,
        source_project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[Path]:
        """Return the generated source trees directly inside one package.

        The names come from the codegen artifact SSOT (``generated_source``).
        Rope never indexes these trees, so their package initializer is
        planned from the indexed parent that contains them.

        Returns:
            The resolved generated source directories, sorted.

        """
        names = frozenset(config.Infra.codegen.generated_sources)
        if not names or not source_project.source_query(package_dir, "isdir"):
            return ()
        return tuple(
            sorted(
                child.resolve()
                for child in source_project.source_children(package_dir)
                if child.name in names and source_project.source_query(child, "isdir")
            )
        )

    @staticmethod
    def _generated_source_modules(
        generated_dir: Path,
        *,
        source_project: p.Infra.RopeProject,
    ) -> t.VariadicTuple[Path]:
        """Return the generator-owned Python modules of one generated tree.

        Returns:
            Every module other than the package initializer, sorted.

        """
        return tuple(
            sorted(
                module.resolve()
                for module in source_project.source_children(generated_dir)
                if module.suffix == c.Infra.EXT_PYTHON
                and module.name != c.Infra.INIT_PY
                and source_project.source_query(module, "isfile")
            )
        )

    def _file_plan(
        self,
        *,
        project: Path,
        path: Path,
        desired_content: bytes | None,
    ) -> m.Infra.CodegenFilePlan:
        """Bind one target's live state to its desired initializer state.

        Returns:
            The resulting ``m.Infra.CodegenFilePlan``.

        """
        return m.Infra.CodegenFilePlan(
            project=project,
            path=path,
            before=self.source_project.source_state(path, required=False),
            desired_content=desired_content,
            desired_mode=(
                config.Infra.codegen.modes.file_default
                if desired_content is not None
                else None
            ),
        )

    def _artifact_file_plans(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        project: Path,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Describe the initializer effect for one package.

        Returns:
            The initializer plan, or none when the package is skipped or retained.

        """
        if plan.action in {
            c.Infra.LazyInitAction.SKIP,
            c.Infra.LazyInitAction.RETAIN,
        }:
            return ()
        return (
            self._file_plan(
                project=project,
                path=plan.context.init_path.resolve(),
                desired_content=(
                    None
                    if plan.action == c.Infra.LazyInitAction.REMOVE
                    else FlextInfraCodegenGeneration.render_init(
                        plan,
                        source_project=self.source_project,
                    ).encode(c.DEFAULT_ENCODING)
                ),
            ),
        )

    def _generated_source_file_plans(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        project: Path,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Plan the static initializer of each generated source tree.

        A tree that holds generator modules is a regular package with a
        generated static initializer; a tree left without modules loses the
        initializer generation wrote for it. A foreign initializer in an
        empty tree is not generation's to remove.

        Returns:
            The generated-source initializer plans.

        """
        plans: list[m.Infra.CodegenFilePlan] = []
        for generated_dir in self._generated_source_dirs(
            plan.context.pkg_dir,
            source_project=self.source_project,
        ):
            init_path = generated_dir / c.Infra.INIT_PY
            selected = (
                self.source_project.source_text(init_path).encode(c.DEFAULT_ENCODING)
                if self.source_project.source_query(init_path, "isfile")
                else None
            )
            if u.Infra.codegen_initializer_is_authored(selected):
                u.Cli.info(
                    f"ownership=authored disposition=retained target={init_path}",
                )
                continue
            if self._generated_source_modules(
                generated_dir, source_project=self.source_project
            ):
                generated_plan = m.Infra.LazyInitPlan(
                    context=m.Infra.LazyInitPackageContext(
                        pkg_dir=generated_dir,
                        init_path=init_path,
                        current_pkg=f"{plan.context.current_pkg}.{generated_dir.name}",
                        surface=plan.context.surface,
                        generated_init=self._is_generated(selected),
                        importable=True,
                    ),
                    action=c.Infra.LazyInitAction.WRITE,
                    lazy_map={},
                    eager_dunders={},
                )
                desired: bytes | None = FlextInfraCodegenGeneration.render_init(
                    generated_plan,
                    source_project=self.source_project,
                ).encode(c.DEFAULT_ENCODING)
            elif self._is_generated(selected):
                desired = None
            else:
                continue
            plans.append(
                self._file_plan(
                    project=project,
                    path=init_path,
                    desired_content=desired,
                ),
            )
        return tuple(plans)

    def _build_file_plans(
        self,
        plans: t.SequenceOf[m.Infra.LazyInitPlan],
        *,
        index: m.Infra.RopeWorkspaceIndex,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Build and deduplicate every lazy-init file plan.

        Returns:
            The file plans sorted by destination path.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        by_path: MutableMapping[Path, m.Infra.CodegenFilePlan] = {}
        projects: MutableMapping[Path, Path] = {}
        for plan in plans:
            package_entry = index.packages_by_dir.get(
                str(plan.context.pkg_dir.resolve())
            )
            if package_entry is None or package_entry.project_root is None:
                return result_type.fail(
                    "lazy-init package has no physical project owner: "
                    f"{plan.context.pkg_dir}",
                )
            projects[plan.context.pkg_dir] = package_entry.project_root.resolve()
            if plan.action in {
                c.Infra.LazyInitAction.SKIP,
                c.Infra.LazyInitAction.RETAIN,
            }:
                continue
            support_states = self._cleanup_generated_support_file_states(plan)
            if support_states.failure:
                return result_type.from_failure(support_states)
            for state in support_states.value:
                by_path[state.path] = self._file_plan(
                    project=projects[plan.context.pkg_dir],
                    path=state.path,
                    desired_content=None,
                )
        retired = frozenset(by_path)
        for plan in plans:
            project = projects[plan.context.pkg_dir]
            artifact_plans = (
                ()
                if plan.context.init_path.resolve() in retired
                else self._artifact_file_plans(plan, project=project)
            )
            for artifact_plan in (
                *artifact_plans,
                *self._generated_source_file_plans(plan, project=project),
            ):
                existing = by_path.get(artifact_plan.path)
                if existing is not None and existing != artifact_plan:
                    return result_type.fail(
                        f"conflicting lazy-init plans for {artifact_plan.path}",
                    )
                by_path[artifact_plan.path] = artifact_plan
        return result_type.ok(tuple(by_path[path] for path in sorted(by_path)))


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationFilePlanMixin"]
