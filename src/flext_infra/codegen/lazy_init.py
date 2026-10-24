"""Lazy-init ``__init__.py`` file planner (PEP 562).

Auto-discovers exports from sibling ``.py`` files and describes clean
lazy-loading ``__init__.py`` artifacts using ``flext_core``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_infra import c, config, d, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenLazyInitGenerationMixin,
    FlextInfraCodegenLazyInitPlanner,
    FlextInfraCodegenLazyInitProjectionManifest,
)
from flext_infra.workspace import FlextInfraRopeWorkspace

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInit(
    FlextInfraCodegenLazyInitGenerationMixin,
):
    """Plan ``__init__.py`` artifacts with PEP 562 lazy imports.

    Scans sibling ``.py`` files in each package directory, discovers their
    exports, and returns immutable file plans for the shared publisher.
    Processes bottom-up so child packages are generated before parents.
    """

    _modified_files: t.Infra.StrSet = m.PrivateAttr(default_factory=set)
    _source_indexes: t.MutableMappingKV[Path, m.Infra.RopeWorkspaceIndex] = (
        m.PrivateAttr(default_factory=dict[Path, m.Infra.RopeWorkspaceIndex])
    )
    project_scope_roots: Annotated[
        t.VariadicTuple[Path] | None,
        m.Field(
            default=...,
            description=(
                "Repository roots selected by conformance; None plans every "
                "package of the workspace"
            ),
        ),
    ] = None

    @property
    def modified_files(self) -> t.StrSequence:
        """Initializer artifacts whose immutable plans require an effect."""
        return tuple(sorted(self._modified_files))

    @override
    def execute(self) -> p.Result[bool]:
        """Check lazy-init drift; publication belongs to conform.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        planned = self.plan_files()
        if planned.failure:
            return r[bool].from_failure(planned)
        if not self.effective_dry_run:
            return r[bool].fail(
                "lazy-init publication is owned by codegen conform; "
                "conform must publish plan_files()",
            )
        changed = tuple(
            plan for plan in planned.value if u.Infra.codegen_file_requires_effect(plan)
        )
        if changed:
            drifted_files = ", ".join(str(plan.path) for plan in changed)
            return r[bool].fail(
                f"init drift detected in {len(changed)} "
                f"generated artifacts: {drifted_files}",
            )
        return r[bool].ok(value=True)

    @d.log_operation("lazy_init_plan", track_perf=True)
    def plan_files(
        self,
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Return the complete immutable lazy-init file plans.

        Planning is read-only; conform owns publication.

        Returns:
            The lazy-init file plans, or the first planning failure.

        """
        self._source_indexes.clear()
        self._modified_files.clear()
        if not (
            self.repository_root.is_dir()
            if source_project is None
            else source_project.source_query(self.repository_root, "isdir")
        ):
            return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].fail(
                f"lazy-init workspace is not a directory: {self.repository_root}",
            )
        roots = (
            (self.repository_root.resolve(),)
            if self.project_scope_roots is None
            else tuple(sorted({root.resolve() for root in self.project_scope_roots}))
        )
        with self._source_binding(
            self.repository_root.resolve(), source_project, roots
        ) as project:
            planned = self._plan_roots(roots, source_project=project)
        if planned.failure:
            return planned
        changed = tuple(
            plan for plan in planned.value if u.Infra.codegen_file_requires_effect(plan)
        )
        self._modified_files.update(str(plan.path) for plan in changed)
        u.Cli.info(f"Lazy-init plan: {len(changed)} effects")
        return planned

    def _plan_roots(
        self,
        roots: t.VariadicTuple[Path],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Compose explicitly selected repositories without widening their indexes.

        Returns:
            The file plans of every selected repository plus their manifests.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        candidates = self._target_repository_candidates(roots, source_project)
        target_roots = sum(len(paths) for paths in candidates.values())
        if self.module and target_roots > 1:
            return result_type.fail(
                f"lazy-init target module is ambiguous: {self.module}",
            )
        files: list[m.Infra.CodegenFilePlan] = []
        for root in roots:
            if root in candidates and not candidates[root]:
                continue
            if (
                not root.is_relative_to(self.repository_root.resolve())
                or not root.is_dir()
            ):
                return result_type.fail(
                    "lazy-init repository scope is missing or outside "
                    f"{self.repository_root.resolve()}: {root}",
                )
            with self._root_workspace(root, source_project) as rope:
                planned = self._plan_open_workspace(rope)
            if planned.failure:
                return planned
            files.extend(planned.value)
        if self.module and not target_roots:
            return result_type.fail(
                f"lazy-init target module not found: {self.module}",
            )
        manifests = (
            FlextInfraCodegenLazyInitProjectionManifest.projection_manifest_plans(
                files=tuple(files),
            )
        )
        if manifests.failure:
            return result_type.from_failure(manifests)
        return result_type.ok((*files, *manifests.value))

    @classmethod
    def plan_scope_root(
        cls, scope: t.Pair[Path, Path]
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Plan one selected repository of a workspace as an independent fleet task.

        The workspace authority binds only the selected repository, exactly as
        a one-root ``project_scope_roots`` invocation does, so fleet workers can
        plan the repositories of one generation concurrently.

        Args:
            scope: The workspace root and the selected repository root.

        Returns:
            The selected repository's lazy-init file plans.

        """
        return (
            cls(repository_root=scope[0], project_scope_roots=(scope[1],))
            .plan_files()
            .unwrap()
        )

    @staticmethod
    @contextmanager
    def _source_binding(
        root: Path,
        source_project: p.Infra.RopeProject | None,
        scope_roots: t.VariadicTuple[Path],
    ) -> Generator[p.Infra.RopeProject]:
        """Bind one Rope view without replacing an injected one.

        Yields:
            The shared Rope source view.

        Raises:
            ValueError: When the injected view does not cover the invocation root.

        """
        if source_project is None:
            # The view elects exactly the selected scope roots inside this
            # repository: unselected members stay installed libraries and are
            # never indexed here.
            with u.Infra.facade_source_project(
                root,
                project_roots=tuple(
                    scope for scope in scope_roots if scope.is_relative_to(root)
                ),
            ) as (project, _):
                yield project
            return
        if not root.is_relative_to(Path(source_project.root.real_path)):
            msg = "lazy-init consumer is outside its injected Rope view"
            raise ValueError(msg)
        yield source_project

    @contextmanager
    def _root_workspace(
        self,
        root: Path,
        source_project: p.Infra.RopeProject,
    ) -> Generator[FlextInfraRopeWorkspace]:
        """Open one root's indexed workspace over the shared Rope view.

        Yields:
            The root's indexed workspace.

        """
        with FlextInfraRopeWorkspace.open_workspace(
            root,
            rope_repository_root=Path(source_project.root.real_path),
            source_project=source_project,
            workspace_index=self._source_indexes.get(root),
        ) as rope:
            yield rope

    def _target_repository_candidates(
        self,
        roots: t.VariadicTuple[Path],
        source_project: p.Infra.RopeProject,
    ) -> t.MutableMappingKV[Path, t.VariadicTuple[Path]]:
        """Resolve the selected target packages before repository analysis.

        Returns:
            The target package directories of each selected repository.

        """
        candidates: t.MutableMappingKV[Path, t.VariadicTuple[Path]] = {}
        if self.module:
            for root in roots:
                if (
                    not root.is_relative_to(self.repository_root.resolve())
                    or not root.is_dir()
                ):
                    continue
                with self._root_workspace(root, source_project) as rope:
                    candidates[root] = self._target_package_dirs(
                        rope.workspace_index, root
                    )
                    self._source_indexes[root] = rope.workspace_index
        return candidates

    def _target_package_dirs(
        self,
        index: m.Infra.RopeWorkspaceIndex,
        root: Path,
    ) -> t.VariadicTuple[Path]:
        """Resolve the target through the current repository's index.

        Returns:
            The resulting ``t.VariadicTuple[Path]``.

        """
        if self.module is None:
            return ()
        mapped = index.package_dir_by_name.get(self.module)
        targets = {
            entry.package_dir.resolve()
            for entry in index.modules_by_path.values()
            if entry.module_name == self.module
            and (self.project_scope_roots is None or entry.project_root == root)
        }
        if mapped is not None and (
            self.project_scope_roots is None
            or index.packages_by_dir[str(mapped)].project_root == root
        ):
            targets.add(mapped.resolve())
        return tuple(sorted(targets))

    def _plan_open_workspace(
        self,
        rope: FlextInfraRopeWorkspace,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Build immutable plans from one stable Rope workspace snapshot.

        One writer per destination (render purity, v4 §2.1): templates own
        every generated surface; alignment is a semantic phase of ``make
        mod`` (codemod/semantic_apply.py phase 0), never a second writer
        inside generation.

        Returns:
            The repository's lazy-init file plans.

        """
        result_type = r[t.VariadicTuple[m.Infra.CodegenFilePlan]]
        self._source_project = rope.rope_project
        workspace_index = rope.workspace_index
        resolved_repository_root = rope.repository_root.resolve()
        candidate_entries = tuple(
            workspace_index.packages_by_dir[str(package_dir)]
            for package_dir in workspace_index.package_dirs
            if package_dir.is_relative_to(resolved_repository_root)
            and not frozenset(package_dir.relative_to(resolved_repository_root).parts)
            & c.Infra.OBSOLETE_ROOT_SUPPORT_NAMES
        )
        if self.project_scope_roots is not None:
            unowned = tuple(
                entry.package_dir
                for entry in candidate_entries
                if entry.project_root is None
            )
            if unowned:
                return result_type.fail(
                    f"lazy-init package has no repository owner: {unowned[0]}",
                )
            candidate_entries = tuple(
                entry
                for entry in candidate_entries
                if entry.project_root == resolved_repository_root
            )
        indexed_package_dirs = tuple(
            sorted(
                (entry.package_dir.resolve() for entry in candidate_entries),
                key=u.Infra.path_depth,
                reverse=True,
            ),
        )
        target = self._resolved_target_package_dir(
            workspace_index,
            indexed_package_dirs,
            resolved_repository_root,
        )
        if target.failure:
            return result_type.from_failure(target)
        package_dirs = self._package_dirs_for_target(
            indexed_package_dirs,
            target_package_dir=target.value,
        )
        u.Cli.info(f"lazy-init: planning {len(package_dirs)} package dirs")
        package_plans = FlextInfraCodegenLazyInitPlanner(
            rope_workspace=rope,
            lazy_init=config.Infra.tooling.lazy_init,
        ).plan_all_inits(
            package_dirs,
            target_package_dir=target.value,
        )
        if package_plans.failure:
            return result_type.from_failure(package_plans)
        return self._build_file_plans(package_plans.value, index=workspace_index)

    def _resolved_target_package_dir(
        self,
        workspace_index: m.Infra.RopeWorkspaceIndex,
        indexed_package_dirs: t.VariadicTuple[Path],
        repository_root: Path,
    ) -> p.Result[Path | None]:
        """Resolve the single target package dir when a target module is set.

        Returns:
            The target package directory, or ``None`` when no module is set.

        """
        result_type = r[Path | None]
        if not self.module:
            return result_type.ok(None)
        sorted_target_dirs = self._target_package_dirs(
            workspace_index,
            repository_root,
        )
        if not sorted_target_dirs:
            return result_type.fail(
                f"lazy-init target module not found: {self.module}",
            )
        if sorted_target_dirs[1:]:
            return result_type.fail(
                f"lazy-init target module is ambiguous: {self.module}",
            )
        target_package_dir = sorted_target_dirs[0]
        if target_package_dir not in indexed_package_dirs:
            return result_type.fail(
                f"lazy-init target belongs to retired support: {self.module}",
            )
        return result_type.ok(target_package_dir)

    @staticmethod
    def _package_dirs_for_target(
        indexed_package_dirs: t.SequenceOf[Path],
        *,
        target_package_dir: Path | None,
    ) -> t.VariadicTuple[Path]:
        """Plan only the target tree; native reads resolve external dependencies.

        Returns:
            The resulting ``t.VariadicTuple[Path]``.

        """
        if target_package_dir is None:
            return tuple(indexed_package_dirs)
        return tuple(
            package_dir
            for package_dir in indexed_package_dirs
            if package_dir.is_relative_to(target_package_dir)
        )


__all__: list[str] = ["FlextInfraCodegenLazyInit"]
