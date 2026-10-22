"""Canonical file-plan composition for generated package initializers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra._config import FlextInfraConfig
from flext_infra.codegen import FlextInfraCodegenGeneration

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from flext_infra import p


class FlextInfraCodegenLazyInitGenerationFilePlanMixin:
    """Convert resolved lazy-init decisions into immutable publication plans."""

    if TYPE_CHECKING:
        _publication_receipts: t.MutableMappingKV[str, m.Infra.CodegenPhaseAnalysis]

        @property
        def source_project(self) -> p.Infra.RopeProject: ...

        def _cleanup_generated_support_file_states(
            self,
            plan: m.Infra.LazyInitPlan,
        ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
            del plan
            raise NotImplementedError(type(self).__qualname__)

    @staticmethod
    def _snapshot_paths(
        required_paths: AbstractSet[Path],
        optional_paths: AbstractSet[Path],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[MutableMapping[Path, m.Cli.AtomicFileState]]:
        """Capture one descriptor-authenticated state for every planner input.

        Returns:
            The resulting ``p.Result[MutableMapping[Path, m.Cli.AtomicFileState]]``.

        Raises:
            FileNotFoundError: When a required source path is absent.

        """
        snapshots: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        paths = sorted(required_paths | optional_paths)
        progress_interval = max(1, len(paths) // 20)
        for index, path in enumerate(paths, start=1):
            if index == 1 or index == len(paths) or index % progress_interval == 0:
                u.Cli.info(f"lazy-init: snapshot inputs {index}/{len(paths)} — {path}")
            snapshots[path] = source_project.source_state(
                path,
                required=False,
            )
            if path in required_paths and not source_project.source_query(
                path, "isfile"
            ):
                msg = f"lazy-init required source is absent: {path}"
                raise FileNotFoundError(msg)
        return r[MutableMapping[Path, m.Cli.AtomicFileState]].ok(snapshots)

    @classmethod
    def _snapshot_planner_inputs(
        cls,
        index: m.Infra.RopeWorkspaceIndex,
        package_dirs: t.SequenceOf[Path],
        *,
        source_project: p.Infra.RopeProject,
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
        template_paths = set(
            FlextInfraCodegenGeneration.init_template_paths(
                source_project=source_project
            )
        )
        for root in {path.parent for path in tuple(template_paths)}:
            for directory, _, names in source_project.source_walk(root):
                template_paths.update(
                    directory / name
                    for name in names
                    if source_project.source_query(directory / name, "isfile")
                )
        project_metadata_paths = {
            entry.project_root.resolve() / c.PYPROJECT_FILENAME
            for entry in index.packages_by_dir.values()
            if entry.project_root is not None and entry.package_dir in selected_dirs
        }
        declaration_paths = {
            path
            for root in {path.parent for path in project_metadata_paths}
            for path in FlextInfraConfig.config_layer_paths_for_repository(
                root,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )
        }
        init_paths = {
            entry.init_path.resolve()
            for entry in index.packages_by_dir.values()
            if entry.package_dir in selected_dirs
        }
        generated_dirs = tuple(
            generated_dir
            for package_dir in selected_dirs
            for generated_dir in cls._generated_source_dirs(
                package_dir, source_project=source_project
            )
        )
        generated_modules = {
            module
            for generated_dir in generated_dirs
            for module in cls._generated_source_modules(
                generated_dir, source_project=source_project
            )
        }
        generated_inits = {
            generated_dir / c.Infra.INIT_PY for generated_dir in generated_dirs
        }
        return cls._snapshot_paths(
            module_paths | template_paths | generated_modules,
            init_paths | project_metadata_paths | generated_inits | declaration_paths,
            source_project=source_project,
        )

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
        with source_project.source_selection():
            if not names or not source_project.source_query(package_dir, "isdir"):
                return ()
            return tuple(
                sorted(
                    child.resolve()
                    for child in source_project.source_children(package_dir)
                    if child.name in names
                    and source_project.source_query(child, "isdir")
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
        with source_project.source_selection():
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
        before: m.Cli.AtomicFileState,
        desired_content: bytes | None,
    ) -> m.Infra.CodegenFilePlan:
        """Bind one exact target state to its desired initializer state.

        Returns:
            The resulting ``m.Infra.CodegenFilePlan``.

        Raises:
            ValueError: When the target has no original parent absence witness.

        """
        original: m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan = before
        if before.parent_inode is None:
            parent = next(
                (
                    witness
                    for witness in self.source_project.consumed_source_topology()
                    if witness.target == before.path.parent and witness.directories
                ),
                None,
            )
            if parent is None:
                msg = (
                    f"lazy-init target has no original parent "
                    f"absence witness: {before.path}"
                )
                raise ValueError(msg)
            original = parent.model_copy(
                update={"queries": (), "membership_queried": False}
            )
        return m.Infra.CodegenFilePlan(
            project=project,
            path=before.path,
            before=original,
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
        }:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(())
        if plan.action == c.Infra.LazyInitAction.REMOVE:
            init_plan = self._file_plan(
                project=project,
                before=init_before,
                desired_content=None,
            )
        else:
            rendered = FlextInfraCodegenGeneration.render_init(
                plan,
                source_project=self.source_project,
            ).encode(
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
        for generated_dir in self._generated_source_dirs(
            plan.context.pkg_dir,
            source_project=self.source_project,
        ):
            init_path = generated_dir / c.Infra.INIT_PY
            self.source_project.source_state(init_path, required=False)
            init_before = snapshots.get(init_path)
            if init_before is None:
                return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                    f"lazy-init target was not snapshotted: {init_path}",
                )
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
                    inline_constants={},
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
        source_receipts: t.MappingKV[str, m.Infra.CodegenPhaseAnalysis],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Build, deduplicate, and source-bind every lazy-init file plan.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        cleanup_receipts: MutableMapping[str, m.Infra.CodegenPhaseAnalysis] = {}
        retired = self._retired_support_plans(
            plans,
            index,
            source_receipts,
            cleanup_receipts=cleanup_receipts,
        )
        if retired.failure:
            return result_type.from_failure(retired)
        by_path: MutableMapping[Path, m.Infra.CodegenFilePlan] = dict(retired.value)
        for plan in plans:
            key = str(plan.context.pkg_dir.resolve())
            with self.source_project.source_consumption() as consumption:
                self.source_project.replay_source_consumption(source_receipts[key])
                cleanup = cleanup_receipts.get(key)
                if cleanup is not None:
                    self.source_project.replay_source_consumption(cleanup)
                artifact_plans = self._package_file_plans(
                    plan,
                    index,
                    snapshots,
                    frozenset(by_path),
                )
            if artifact_plans.failure:
                return result_type.from_failure(artifact_plans)
            receipt = consumption.receipt()
            self._publication_receipts[key] = receipt
            for artifact_plan in self._bound_file_plans(artifact_plans.value, receipt):
                existing = by_path.get(artifact_plan.path)
                if existing is not None and existing != artifact_plan:
                    return result_type.fail(
                        f"conflicting lazy-init plans for {artifact_plan.path}",
                    )
                by_path[artifact_plan.path] = artifact_plan
        return result_type.ok(tuple(by_path[path] for path in sorted(by_path)))

    def _retired_support_plans(
        self,
        plans: t.SequenceOf[m.Infra.LazyInitPlan],
        index: m.Infra.RopeWorkspaceIndex,
        source_receipts: t.MappingKV[str, m.Infra.CodegenPhaseAnalysis],
        *,
        cleanup_receipts: MutableMapping[str, m.Infra.CodegenPhaseAnalysis],
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
            with self.source_project.source_consumption() as consumption:
                self.source_project.replay_source_consumption(
                    source_receipts[str(plan.context.pkg_dir.resolve())],
                )
                support_states = self._cleanup_generated_support_file_states(plan)
            cleanup_receipts[str(plan.context.pkg_dir.resolve())] = (
                consumption.receipt()
            )
            if support_states.failure:
                return r[MutableMapping[Path, m.Infra.CodegenFilePlan]].from_failure(
                    support_states,
                )
            for state in support_states.value:
                file = self._file_plan(
                    project=package_entry.project_root.resolve(),
                    before=state,
                    desired_content=None,
                )
                by_path[state.path] = self._bound_file_plans(
                    (file,), consumption.receipt()
                )[0]
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
        self.source_project.source_state(init_path, required=False)
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
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
        receipt: m.Infra.CodegenPhaseAnalysis,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Bind the sealed genuine native consumption without inferring dependencies.

        Returns:
            The planned files with their shared source states bound.

        Raises:
            ValueError: When the receipt carries no original source
                consumption evidence.

        """
        if not (
            receipt.inputs
            or receipt.source_directories
            or receipt.source_query_topology
        ):
            msg = "lazy-init artifact has no original source consumption evidence"
            raise ValueError(msg)
        return tuple(
            file.model_copy(
                update={
                    "source_states": receipt.inputs,
                    "source_directories": receipt.source_directories,
                    "source_query_topology": receipt.source_query_topology,
                }
            )
            for file in files
        )


__all__: list[str] = ["FlextInfraCodegenLazyInitGenerationFilePlanMixin"]
