"""Canonical file-plan composition for generated package initializers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen import FlextInfraCodegenGeneration

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from flext_infra import p


class FlextInfraCodegenLazyInitGenerationFilePlanMixin:
    """Convert resolved lazy-init decisions into immutable publication plans."""

    if TYPE_CHECKING:

        def _cleanup_generated_support_file_states(
            self,
            plan: m.Infra.LazyInitPlan,
        ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]: ...

    @staticmethod
    def _snapshot_paths(
        required_paths: AbstractSet[Path],
        optional_paths: AbstractSet[Path],
    ) -> p.Result[MutableMapping[Path, m.Cli.AtomicFileState]]:
        """Capture one descriptor-authenticated state for every planner input.

        Returns:
            The resulting ``p.Result[MutableMapping[Path, m.Cli.AtomicFileState]]``.

        """
        snapshots: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        paths = sorted(required_paths | optional_paths)
        progress_interval = max(1, len(paths) // 20)
        for index, path in enumerate(paths, start=1):
            if index == 1 or index == len(paths) or index % progress_interval == 0:
                u.Cli.info(f"lazy-init: snapshot inputs {index}/{len(paths)} — {path}")
            snapshot = u.Cli.atomic_read_binary_file_state(
                path,
                required=path in required_paths,
            )
            if snapshot.failure:
                return r[MutableMapping[Path, m.Cli.AtomicFileState]].from_failure(
                    snapshot,
                )
            snapshots[path] = snapshot.value
        return r[MutableMapping[Path, m.Cli.AtomicFileState]].ok(snapshots)

    @classmethod
    def _snapshot_planner_inputs(
        cls,
        index: m.Infra.RopeWorkspaceIndex,
        package_dirs: t.SequenceOf[Path],
    ) -> p.Result[MutableMapping[Path, m.Cli.AtomicFileState]]:
        """Snapshot Python, project, target, and template inputs before planning.

        Returns:
            The resulting ``p.Result[MutableMapping[Path, m.Cli.AtomicFileState]]``.

        """
        selected_dirs = frozenset(package_dirs)
        module_paths = {
            entry.file_path.resolve()
            for entry in index.modules_by_path.values()
            if entry.package_dir.resolve() in selected_dirs
        }
        template_paths = set(FlextInfraCodegenGeneration.init_template_paths())
        project_metadata_paths = {
            entry.project_root.resolve() / c.PYPROJECT_FILENAME
            for entry in index.packages_by_dir.values()
            if entry.project_root is not None and entry.package_dir in selected_dirs
        }
        init_paths = {
            entry.init_path.resolve()
            for entry in index.packages_by_dir.values()
            if entry.package_dir in selected_dirs
        }
        generated_dirs = tuple(
            generated_dir
            for package_dir in selected_dirs
            for generated_dir in cls._generated_source_dirs(package_dir)
        )
        generated_modules = {
            module
            for generated_dir in generated_dirs
            for module in cls._generated_source_modules(generated_dir)
        }
        generated_inits = {
            generated_dir / c.Infra.INIT_PY for generated_dir in generated_dirs
        }
        return cls._snapshot_paths(
            module_paths | template_paths | generated_modules,
            init_paths | project_metadata_paths | generated_inits,
        )

    @staticmethod
    def _generated_source_dirs(package_dir: Path) -> t.VariadicTuple[Path]:
        """Return the generated source trees directly inside one package.

        The names come from the codegen artifact SSOT (``generated_source``).
        Rope never indexes these trees, so their package initializer is
        planned from the indexed parent that contains them.

        Returns:
            The resolved generated source directories, sorted.

        """
        names = frozenset(config.Infra.codegen.generated_sources)
        if not names or not package_dir.is_dir():
            return ()
        return tuple(
            sorted(
                child.resolve()
                for child in package_dir.iterdir()
                if child.name in names and child.is_dir() and not child.is_symlink()
            ),
        )

    @staticmethod
    def _generated_source_modules(generated_dir: Path) -> t.VariadicTuple[Path]:
        """Return the generator-owned Python modules of one generated tree.

        Returns:
            Every module other than the package initializer, sorted.

        """
        return tuple(
            sorted(
                module.resolve()
                for module in generated_dir.glob(f"*{c.Infra.EXT_PYTHON}")
                if module.name != c.Infra.INIT_PY and module.is_file()
            ),
        )

    @staticmethod
    def _file_plan(
        *,
        project: Path,
        before: m.Cli.AtomicFileState,
        desired_content: bytes | None,
    ) -> m.Infra.CodegenFilePlan:
        """Bind one exact target state to its desired initializer state.

        Returns:
            The resulting ``m.Infra.CodegenFilePlan``.

        """
        return m.Infra.CodegenFilePlan(
            project=project,
            path=before.path,
            before=before,
            desired_content=desired_content,
            desired_mode=(
                config.Infra.codegen.modes.file_default
                if desired_content is not None
                else None
            ),
        )

    @staticmethod
    def _is_generated(content: bytes | None) -> bool:
        """Return whether bytes carry an accepted lazy-init owner marker.

        Returns:
            Whether bytes carry an accepted lazy-init owner marker.

        """
        return content is not None and content.startswith(
            tuple(
                header.encode(c.DEFAULT_ENCODING) for header in c.Infra.AUTOGEN_HEADERS
            ),
        )

    def _artifact_file_plans(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        project: Path,
        init_before: m.Cli.AtomicFileState,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Describe the initializer and every cleanup effect for one package.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        if plan.action in {
            c.Infra.LazyInitAction.SKIP,
            c.Infra.LazyInitAction.RETAIN,
        } or u.Infra.codegen_initializer_is_authored(init_before.content):
            return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(())
        if plan.action is c.Infra.LazyInitAction.REMOVE:
            init_plan = self._file_plan(
                project=project,
                before=init_before,
                desired_content=None,
            )
        else:
            rendered = FlextInfraCodegenGeneration.render_init(plan).encode(
                c.DEFAULT_ENCODING,
            )
            init_plan = self._file_plan(
                project=project,
                before=init_before,
                desired_content=rendered,
            )
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok((init_plan,))

    def _generated_source_file_plans(
        self,
        plan: m.Infra.LazyInitPlan,
        *,
        project: Path,
        snapshots: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan the static initializer of each generated source tree.

        A tree that holds generator modules is a regular package with a
        generated static initializer; a tree left without modules loses the
        initializer generation wrote for it. A foreign initializer in an
        empty tree is not generation's to remove.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        plans: list[m.Infra.CodegenFilePlan] = []
        for generated_dir in self._generated_source_dirs(plan.context.pkg_dir):
            init_path = generated_dir / c.Infra.INIT_PY
            init_before = snapshots.get(init_path)
            if init_before is None:
                return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                    f"lazy-init target was not snapshotted: {init_path}",
                )
            if u.Infra.codegen_initializer_is_authored(init_before.content):
                u.Cli.info(
                    f"ownership=authored disposition=retained target={init_path}",
                )
                continue
            if self._generated_source_modules(generated_dir):
                generated_plan = m.Infra.LazyInitPlan(
                    context=m.Infra.LazyInitPackageContext(
                        pkg_dir=generated_dir,
                        init_path=init_path,
                        current_pkg=f"{plan.context.current_pkg}.{generated_dir.name}",
                        surface=plan.context.surface,
                        generated_init=self._is_generated(init_before.content),
                        importable=True,
                    ),
                    action=c.Infra.LazyInitAction.WRITE,
                    lazy_map={},
                    eager_dunders={},
                    inline_constants={},
                )
                desired: bytes | None = FlextInfraCodegenGeneration.render_init(
                    generated_plan,
                ).encode(c.DEFAULT_ENCODING)
            elif self._is_generated(init_before.content):
                desired = None
            else:
                continue
            plans.append(
                self._file_plan(
                    project=project,
                    before=init_before,
                    desired_content=desired,
                ),
            )
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(tuple(plans))

    def _build_file_plans(
        self,
        plans: t.SequenceOf[m.Infra.LazyInitPlan],
        *,
        index: m.Infra.RopeWorkspaceIndex,
        snapshots: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Build, deduplicate, and source-bind every lazy-init file plan.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        retired = self._retired_support_plans(plans, index)
        if retired.failure:
            return result_type.from_failure(retired)
        by_path = retired.value
        for plan in plans:
            artifact_plans = self._package_file_plans(
                plan,
                index,
                snapshots,
                frozenset(by_path),
            )
            if artifact_plans.failure:
                return result_type.from_failure(artifact_plans)
            for artifact_plan in artifact_plans.value:
                existing = by_path.get(artifact_plan.path)
                if existing is not None and existing != artifact_plan:
                    return result_type.fail(
                        f"conflicting lazy-init plans for {artifact_plan.path}",
                    )
                by_path[artifact_plan.path] = artifact_plan
        return result_type.ok(self._bound_file_plans(by_path, snapshots))

    def _retired_support_plans(
        self,
        plans: t.SequenceOf[m.Infra.LazyInitPlan],
        index: m.Infra.RopeWorkspaceIndex,
    ) -> p.Result[MutableMapping[Path, m.Infra.CodegenFilePlan]]:
        """Plan the generator-owned support files retired before artifact plans.

        Returns:
            The retired support plans keyed by their destination path.

        """
        by_path: MutableMapping[Path, m.Infra.CodegenFilePlan] = {}
        for plan in plans:
            if plan.action in {
                c.Infra.LazyInitAction.SKIP,
                c.Infra.LazyInitAction.RETAIN,
            }:
                continue
            package_entry = index.packages_by_dir.get(
                str(plan.context.pkg_dir.resolve()),
            )
            if package_entry is None or package_entry.project_root is None:
                return r[MutableMapping[Path, m.Infra.CodegenFilePlan]].fail(
                    f"lazy-init package has no physical project owner: "
                    f"{plan.context.pkg_dir}",
                )
            support_states = self._cleanup_generated_support_file_states(plan)
            if support_states.failure:
                return r[MutableMapping[Path, m.Infra.CodegenFilePlan]].from_failure(
                    support_states,
                )
            for state in support_states.value:
                by_path[state.path] = self._file_plan(
                    project=package_entry.project_root.resolve(),
                    before=state,
                    desired_content=None,
                )
        return r[MutableMapping[Path, m.Infra.CodegenFilePlan]].ok(by_path)

    def _package_file_plans(
        self,
        plan: m.Infra.LazyInitPlan,
        index: m.Infra.RopeWorkspaceIndex,
        snapshots: t.MappingKV[Path, m.Cli.AtomicFileState],
        retired_paths: frozenset[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan one package's artifact and generated-source file changes.

        Returns:
            The concatenated artifact and generated-source plans.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        package_key = str(plan.context.pkg_dir.resolve())
        package_entry = index.packages_by_dir.get(package_key)
        if package_entry is None or package_entry.project_root is None:
            return result_type.fail(
                f"lazy-init package has no physical project owner: {package_key}",
            )
        project_root = package_entry.project_root.resolve()
        init_path = plan.context.init_path.resolve()
        init_before = snapshots.get(init_path)
        if init_before is None:
            return result_type.fail(
                f"lazy-init target was not snapshotted: {init_path}",
            )
        artifact_plans = (
            result_type.ok(())
            if init_path in retired_paths
            else self._artifact_file_plans(
                plan,
                project=project_root,
                init_before=init_before,
            )
        )
        if artifact_plans.failure:
            return result_type.from_failure(artifact_plans)
        generated_plans = self._generated_source_file_plans(
            plan,
            project=project_root,
            snapshots=snapshots,
        )
        if generated_plans.failure:
            return result_type.from_failure(generated_plans)
        return result_type.ok((*artifact_plans.value, *generated_plans.value))

    @staticmethod
    def _bound_file_plans(
        by_path: t.MappingKV[Path, m.Infra.CodegenFilePlan],
        snapshots: t.MappingKV[Path, m.Cli.AtomicFileState],
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Bind the shared source states onto every planned file.

        Returns:
            The planned files with their shared source states bound.

        """
        target_paths = frozenset(by_path)
        source_states = tuple(
            state
            for path in sorted(snapshots)
            for state in (snapshots[path],)
            if path not in target_paths and state.content is not None
        )
        return tuple(
            m.Infra.CodegenFilePlan(
                project=by_path[path].project,
                path=by_path[path].path,
                before=by_path[path].before,
                desired_content=by_path[path].desired_content,
                desired_mode=by_path[path].desired_mode,
                source_states=source_states,
                owner=by_path[path].owner,
                policy=by_path[path].policy,
            )
            for path in sorted(by_path)
        )


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationFilePlanMixin"]
