"""Resolve a bounded candidate package from canonical pinned workspace sources.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsProcess,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraStagedPackage:
    """Plan one complete package view and its static workspace import closure."""

    @staticmethod
    def source_writes(
        plan: m.Infra.StageSourcePlan,
        view_root: Path,
    ) -> t.VariadicTuple[tuple[Path, bytes, int]]:
        """Materialize the same pinned composition for preparation and admission.

        Returns:
            Exact candidate paths, bytes and permissions, excluding retirements.

        """
        writes: list[tuple[Path, bytes, int]] = []
        for before in plan.inputs:
            if not before.path.is_relative_to(plan.workspace):
                continue
            content = before.content
            if before.path in plan.updates:
                desired = plan.updates[before.path]
                content = (
                    None if desired is None else desired.encode(c.DEFAULT_ENCODING)
                )
            if content is not None:
                writes.append((
                    view_root / before.path.relative_to(plan.workspace),
                    content,
                    before.mode if before.mode is not None else c.Infra.CONFIG_SPEC[1],
                ))
        return tuple(writes)

    @classmethod
    def prepare_sources(
        cls,
        plan: m.Infra.StageSourcePlan,
        preparer: Callable[[Path, t.MappingKV[Path, Path]], p.Result[bool]],
    ) -> p.Result[t.MappingKV[Path, str | None]]:
        """Prepare producer bytes before any publication identity is sealed.

        The preparation tree owns no runtime environment. Only desired source
        bytes leave it; admission subsequently builds a fresh read-only view.

        Returns:
            Prepared updates, or the original repair or source-identity failure.

        """
        result_type = r[t.MappingKV[Path, str | None]]
        current = cls.source_inputs_current(plan)
        if current.failure:
            return result_type.from_failure(current)
        with TemporaryDirectory(prefix="flext-source-prepare-") as directory:
            root = Path(directory)
            writes = cls.source_writes(plan, root)
            materialized = cls.materialize_sources(plan, root)
            if materialized.failure:
                return result_type.from_failure(materialized)
            candidates = {
                path: root / path.relative_to(plan.workspace)
                for path, content in plan.updates.items()
                if content is not None and path.suffix in {".py", ".pyi"}
            }
            prepared = preparer(root, candidates)
            if prepared.failure:
                return result_type.from_failure(prepared)
            if not prepared.value:
                return result_type.fail("source preparation returned no acceptance")
            selected = frozenset(candidates.values())
            for path, content, mode in writes:
                if path in selected:
                    continue
                observed = u.Cli.atomic_read_binary_file_state(path, required=True)
                if observed.failure:
                    return result_type.from_failure(observed)
                if observed.value.content != content or observed.value.mode != mode:
                    return result_type.fail(
                        f"source preparation changed an unselected input: {path}"
                    )
            updates = dict(plan.updates)
            for destination, candidate in candidates.items():
                observed = u.Cli.atomic_read_binary_file_state(candidate, required=True)
                if observed.failure:
                    return result_type.from_failure(observed)
                content = observed.value.content
                if content is None:
                    return result_type.fail(
                        f"prepared source disappeared: {destination}"
                    )
                updates[destination] = content.decode(c.DEFAULT_ENCODING)
            return cls.source_inputs_current(plan).map(lambda _: updates)

    @classmethod
    def materialize_sources(
        cls,
        plan: m.Infra.StageSourcePlan,
        root: Path,
    ) -> p.Result[bool]:
        """Write a pinned composition into an exclusively owned empty stage.

        Returns:
            Success after guarded writes, or their first original failure.

        """
        for path, content, mode in cls.source_writes(plan, root):
            created = u.Cli.ensure_dir(path.parent)
            if created.failure:
                return r[bool].from_failure(created)
            written = FlextInfraMiseArtifactsProcess.write_new(path, content, mode)
            if written.failure:
                return r[bool].from_failure(written)
        return r[bool].ok(value=True)

    @classmethod
    def consume_sources(
        cls,
        plan: m.Infra.StageSourcePlan,
        consumer: Callable[[Path], p.Result[bool]],
    ) -> p.Result[bool]:
        """Consume exact candidates read-only without nesting a live journal.

        Returns:
            The original consumer result while candidate and source guards hold.

        """
        current = cls.source_inputs_current(plan)
        if current.failure:
            return r[bool].from_failure(current)
        with TemporaryDirectory(prefix="flext-source-admit-") as directory:
            root = Path(directory)
            materialized = cls.materialize_sources(plan, root)
            if materialized.failure:
                return r[bool].from_failure(materialized)
            manifest = u.Cli.atomic_inventory_physical_tree(root)
            if manifest.failure:
                return r[bool].from_failure(manifest)
            consumed = consumer(root)
            if consumed.failure:
                return r[bool].from_failure(consumed)
            if not consumed.value:
                return r[bool].fail("candidate consumer returned no acceptance")
            observed = u.Cli.atomic_inventory_physical_tree(root)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != manifest.value:
                return r[bool].fail(
                    "source candidate changed during read-only admission"
                )
            return cls.source_inputs_current(plan)

    @classmethod
    def plan_sources(
        cls,
        workspace: Path,
        updates: t.MappingKV[Path, str | None],
        *,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Pin real project inputs for preview without writing live source.

        Args:
            workspace: The root of the Git workspace containing the projects.
            updates: Desired content by live path; None retires an artifact.
            inputs: Original caller snapshots, never replaced by a fresh observation.

        Returns:
            A result wrapping the planned stage source or the first failure encountered.

        """
        result_type = r[m.Infra.StageSourcePlan]
        workspace = workspace.resolve()
        discovered = cls._normalized_updates(
            workspace,
            updates,
        ).flat_map(
            lambda normalized: cls._workspace_layouts(workspace).map(
                lambda layouts: (normalized, layouts),
            )
        )
        if discovered.failure:
            return result_type.from_failure(discovered)
        normalized, layouts = discovered.value
        selected: list[m.Infra.RopeProjectLayout] = []
        states: dict[Path, m.Cli.AtomicFileState] = {}
        source_paths = dict.fromkeys((
            *normalized,
            *(
                before.path
                for before in inputs
                if before.path.suffix in {".py", ".pyi"}
                # Read-only evidence needs no pinned rope layout: the
                # rule-fixture scratch lives outside the workspace, and a
                # standalone consumer's venv lives INSIDE its checkout —
                # installed packages are exactly the site-packages segment
                # (platform convention, not a declared list).
                and before.path.is_relative_to(workspace)
                and "site-packages" not in before.path.parts
            ),
        ))
        for path in source_paths:
            root = u.Infra.project_root(path)
            if any(item.project_root == root for item in selected):
                continue
            resolved = cls._source_layout(path, layouts)
            if resolved.failure:
                if path in normalized:
                    return result_type.from_failure(resolved)
                # Evidence-only inputs (an installed family package inside a
                # standalone consumer's venv, the rule-fixture scratch) are
                # read outside any rope layout; only rewrite targets need one.
                continue
            local = resolved.value
            pinned = cls._pin_closure(
                local,
                layouts,
                selected,
                states,
                updates=normalized,
            )
            if pinned.failure:
                return result_type.from_failure(pinned)
        metadata = cls._pin_workspace_metadata(workspace, states)
        if metadata.failure:
            return result_type.from_failure(metadata)
        verified = cls._verified_input_originals(states, inputs, normalized)
        if verified.failure:
            return result_type.from_failure(verified)
        return result_type.ok(
            m.Infra.StageSourcePlan(
                workspace=workspace,
                roots=tuple(
                    dict.fromkeys((
                        workspace,
                        *(item.project_root for item in selected),
                    ))
                ),
                inputs=tuple(states.values()),
                updates=normalized,
                layouts=tuple(selected),
                workspace_packages=tuple(sorted(layouts)),
            )
        )

    @staticmethod
    def _verified_input_originals(
        states: t.MappingKV[Path, m.Cli.AtomicFileState],
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
        normalized: t.MappingKV[Path, str | None],
    ) -> p.Result[bool]:
        """Verify every caller input kept its pinned original identity.

        Args:
            states: Freshly pinned states keyed by path.
            inputs: Original caller snapshots to verify.
            normalized: Rewrite targets of the candidate.

        Returns:
            Whether every original input kept its identity, or the first
            identity failure.

        """
        for before in inputs:
            observed = states.get(before.path)
            if observed is None:
                # Evidence-only input: never pinned (installed packages and
                # scratch views live outside every rope layout), so it owns
                # no fresh observation. A rewrite target always has one.
                if before.path in normalized:
                    return r[bool].fail(
                        f"candidate original source identity changed: {before.path}",
                    )
                continue
            if observed != before:
                return r[bool].fail(
                    f"candidate original source identity changed: {before.path}",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _normalized_updates(
        workspace: Path,
        updates: t.MappingKV[Path, str | None],
    ) -> p.Result[dict[Path, str | None]]:
        """Elect one contained physical destination per desired source.

        Every desired destination must be a contained, physical, unambiguous
        workspace path.

        Returns:
            Desired sources or the first ambiguous, foreign or symlinked path.

        """
        result_type = r[dict[Path, str | None]]
        normalized: dict[Path, str | None] = {}
        for path, content in updates.items():
            if any(item.is_symlink() for item in (path, *path.parents)):
                return result_type.fail(f"candidate source is a symlink: {path}")
            destination = path.resolve()
            if not destination.is_relative_to(workspace):
                return result_type.fail(f"candidate source escapes workspace: {path}")
            if destination in normalized and normalized[destination] != content:
                return result_type.fail(f"conflicting candidate source: {destination}")
            normalized[destination] = content
        return result_type.ok(normalized)

    @staticmethod
    def _source_layout(
        path: Path,
        layouts: t.MutableMappingKV[str, m.Infra.RopeProjectLayout],
    ) -> p.Result[m.Infra.RopeProjectLayout]:
        """Resolve a source owner without replacing another package's identity.

        Returns:
            The unique source layout or the first ownership failure.

        """
        result_type = r[m.Infra.RopeProjectLayout]
        root = u.Infra.project_root(path)
        local = u.Infra.layout(root) if root is not None else None
        if local is None:
            return result_type.fail(f"preview source has no project layout: {path}")
        existing = layouts.get(local.package_name)
        if existing is not None and existing.project_root != local.project_root:
            return result_type.fail(
                f"ambiguous candidate package: {local.package_name}"
            )
        layouts[local.package_name] = local
        return result_type.ok(local)

    @classmethod
    def source_inputs_current(cls, plan: m.Infra.StageSourcePlan) -> p.Result[bool]:
        """Reject additions as well as changes to the pinned governed inventory.

        Returns:
            Success only while every original source path remains in the closure.

        """
        current = FlextInfraMiseArtifactsVerification.states_current(plan.inputs)
        if current.failure:
            return current
        actual: set[Path] = set()
        for layout in plan.layouts:
            paths = cls._source_paths(layout, governed=True)
            if paths.failure:
                return r[bool].from_failure(paths)
            actual.update(path for path in paths.value if path.is_file())
        actual.update(path for path in plan.updates if path.is_file())
        metadata = cls._workspace_metadata_paths(plan.workspace)
        if metadata.failure:
            return r[bool].from_failure(metadata)
        actual.update(path for path in metadata.value if path.is_file())
        expected = {item.path for item in plan.inputs if item.content is not None}
        if actual != expected:
            return r[bool].fail("candidate original source inventory changed")
        return r[bool].ok(value=True)

    @staticmethod
    def workspace_root(root: Path) -> p.Result[Path]:
        """Resolve the package's Git workspace identity.

        Returns:
            The superproject root or the standalone repository root.

        """
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=root))
        if identity.failure:
            return r[Path].from_failure(identity)
        return r[Path].ok(identity.value.superproject_root or identity.value.repo_root)

    @classmethod
    def plan(
        cls,
        root: Path,
        file: m.Infra.CodegenFilePlan,
    ) -> p.Result[m.Infra.StagePackagePlan]:
        """Pin the package closure and read its canonical facade contract.

        Returns:
            The immutable candidate plan or the first discovery failure.

        """
        result_type = r[m.Infra.StagePackagePlan]
        workspace = cls.workspace_root(root)
        if workspace.failure:
            return result_type.from_failure(workspace)
        discovered = cls._workspace_layouts(workspace.value)
        if discovered.failure:
            return result_type.from_failure(discovered)
        layouts = discovered.value
        local = u.Infra.layout(root)
        if local is None or file.desired_content is None:
            return result_type.fail(
                "staged facade requires an existing package and desired bytes"
            )
        layouts[local.package_name] = local
        selected: list[m.Infra.RopeProjectLayout] = []
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        pinned = cls._pin_closure(local, layouts, selected, states)
        if pinned.failure:
            return result_type.from_failure(pinned)
        metadata = cls._pin_workspace_metadata(workspace.value, states)
        if metadata.failure:
            return result_type.from_failure(metadata)
        return cls._facade_plan(file, local, selected, states, layouts)

    @staticmethod
    def _workspace_layouts(
        workspace: Path,
    ) -> p.Result[t.MutableMappingKV[str, m.Infra.RopeProjectLayout]]:
        """Retain Python providers independently of their generation participation.

        Returns:
            The mutable package-name to source-layout mapping of every
            retained provider, or the first applicability failure.

        """
        result_type = r[t.MutableMappingKV[str, m.Infra.RopeProjectLayout]]
        targets = u.Infra.repository_operation_targets(
            workspace,
            c.Infra.CodegenConformScope.ALL,
        )
        if targets.failure:
            return result_type.from_failure(targets)
        layouts: t.MutableMappingKV[str, m.Infra.RopeProjectLayout] = {}
        for target in targets.value:
            repository = target.root
            manifest = repository / c.PYPROJECT_FILENAME
            if not manifest.is_file():
                applicability = u.Infra.repository_operation_applicability(
                    target,
                    mutating=False,
                )
                if applicability.failure:
                    return result_type.from_failure(applicability)
                if not applicability.value.applicable:
                    continue
                required = u.Cli.atomic_read_binary_file_state(
                    manifest,
                    required=True,
                )
                if required.failure:
                    return result_type.from_failure(required)
            layout = u.Infra.layout(repository)
            if layout is not None:
                if layout.package_name in layouts:
                    return result_type.fail(
                        f"ambiguous candidate package: {layout.package_name}"
                    )
                layouts[layout.package_name] = layout
        return result_type.ok(layouts)

    @staticmethod
    def _source_paths(
        layout: m.Infra.RopeProjectLayout,
        *,
        governed: bool = False,
    ) -> p.Result[list[Path]]:
        paths = [layout.project_root / c.PYPROJECT_FILENAME]
        if governed:
            paths.extend(
                path
                for path in u.Infra.iter_matching_files(
                    layout.project_root, includes=()
                )
                if not c.Infra.CHECK_EXCLUDED_DIRS.intersection(
                    path.relative_to(layout.project_root).parts
                )
            )
        directories = (
            layout.package_dir,
            layout.project_root / c.Infra.CODEGEN_CONFIG_DIR,
        )
        if governed:
            directories = (
                *directories,
                *(
                    layout.project_root / target
                    for target in u.Infra.discover_python_targets(
                        layout.project_root,
                        workspace_excluded_top_dirs=frozenset(),
                    )
                ),
            )
        for directory in directories:
            if directory.is_symlink():
                return r[list[Path]].fail(
                    f"candidate source directory is a symlink: {directory}"
                )
            if directory.is_dir():
                if not governed:
                    paths.extend(
                        path
                        for path in directory.rglob("*")
                        if "__pycache__" not in path.parts
                    )
                    continue
                for parent, children, files in directory.walk():
                    for name in (*children, *files):
                        if (parent / name).is_symlink():
                            return r[list[Path]].fail(
                                f"candidate source is a symlink: {parent / name}",
                            )
                    children[:] = [
                        name
                        for name in children
                        if name not in c.Infra.PYTHON_DISCOVERY_SKIP_DIRS
                        and not name.startswith(".")
                        and not (parent / name / c.PYPROJECT_FILENAME).is_file()
                    ]
                    paths.extend(parent / name for name in files)
            elif directory.is_file():
                paths.append(directory)
        return r[list[Path]].ok(sorted(set(paths)))

    @staticmethod
    def _runtime_imports(
        path: Path,
        content: bytes,
        *,
        runtime_only: bool = True,
    ) -> tuple[str, ...]:
        tree = ast.parse(content.decode(c.DEFAULT_ENCODING), filename=str(path))
        excluded = {
            id(child)
            for guard in ast.walk(tree)
            if isinstance(guard, ast.If)
            and (
                (isinstance(guard.test, ast.Name) and guard.test.id == "TYPE_CHECKING")
                or (
                    isinstance(guard.test, ast.Attribute)
                    and guard.test.attr == "TYPE_CHECKING"
                )
            )
            for statement in guard.body
            for child in ast.walk(statement)
        }
        modules: list[str] = []
        for node in ast.walk(tree):
            if runtime_only and id(node) in excluded:
                continue
            if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                modules.append(node.module)
            elif isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
        return tuple(modules)

    @classmethod
    def _pin_layout(
        cls,
        layout: m.Infra.RopeProjectLayout,
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        *,
        updates: t.MappingKV[Path, str | None] | None = None,
    ) -> p.Result[tuple[str, ...]]:
        paths = cls._source_paths(layout, governed=updates is not None)
        if paths.failure:
            return r[tuple[str, ...]].from_failure(paths)
        modules: list[str] = []
        source_paths = set(paths.value)
        if updates is not None:
            source_paths.update(
                path
                for path in updates
                if u.Infra.project_root(path) == layout.project_root
            )
        for path in sorted(source_paths):
            if path.is_symlink():
                return r[tuple[str, ...]].fail(f"candidate source is a symlink: {path}")
            if not path.is_file() and (updates is None or path not in updates):
                continue
            observed = u.Cli.atomic_read_binary_file_state(
                path,
                required=updates is None or path not in updates,
            )
            if observed.failure:
                return r[tuple[str, ...]].from_failure(observed)
            state = observed.value
            states[path] = state
            content = state.content
            if updates is not None and path in updates:
                desired = updates[path]
                content = (
                    None if desired is None else desired.encode(c.DEFAULT_ENCODING)
                )
            if path.suffix in {c.Infra.EXT_PYTHON, ".pyi"} and content is not None:
                modules.extend(
                    cls._runtime_imports(
                        path,
                        content,
                        runtime_only=updates is None,
                    )
                )
        return r[tuple[str, ...]].ok(tuple(modules))

    @classmethod
    def _pin_closure(
        cls,
        local: m.Infra.RopeProjectLayout,
        layouts: t.MutableMappingKV[str, m.Infra.RopeProjectLayout],
        selected: list[m.Infra.RopeProjectLayout],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        *,
        updates: t.MappingKV[Path, str | None] | None = None,
    ) -> p.Result[bool]:
        queue = [local.package_name]
        while queue:
            name = queue.pop(0)
            layout = layouts[name]
            selected.append(layout)
            pinned = cls._pin_layout(layout, states, updates=updates)
            if pinned.failure:
                return r[bool].from_failure(pinned)
            for module in pinned.value:
                dependency = module.partition(".")[0]
                if (
                    dependency in layouts
                    and dependency not in queue
                    and not any(item.package_name == dependency for item in selected)
                ):
                    queue.append(dependency)
        return r[bool].ok(value=True)

    @staticmethod
    def _workspace_metadata_paths(
        workspace: Path,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Name the source and selected resolver metadata from physical ownership.

        Returns:
            The deduplicated resolver, manifest, lock and codegen source
            paths, or the first resolution failure.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(workspace)
        if context.failure:
            return r[t.VariadicTuple[Path]].from_failure(context)
        inputs = u.Infra.load_codegen_inputs(context.value.runtime_root)
        if inputs.failure:
            return r[t.VariadicTuple[Path]].from_failure(inputs)
        return r[t.VariadicTuple[Path]].ok(
            tuple(
                dict.fromkeys(
                    (
                        context.value.runtime_root / c.PYPROJECT_FILENAME,
                        context.value.runtime_root / c.Infra.GITMODULES,
                        context.value.pyproject_path,
                        context.value.lock_path,
                        *(state.path for state in inputs.value.sources),
                    ),
                ),
            ),
        )

    @staticmethod
    def _pin_workspace_metadata(
        workspace: Path,
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        paths = FlextInfraStagedPackage._workspace_metadata_paths(workspace)
        if paths.failure:
            return r[bool].from_failure(paths)
        for path in paths.value:
            if path in states:
                continue
            observed = u.Cli.atomic_read_binary_file_state(path, required=False)
            if observed.failure:
                return r[bool].from_failure(observed)
            states[path] = observed.value
        return r[bool].ok(value=True)

    @staticmethod
    def _absolute_imports(tree: ast.Module) -> t.MappingKV[str, t.StrPair]:
        return {
            alias.asname or alias.name: (node.module, alias.name)
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and not node.level and node.module
            for alias in node.names
        }

    @classmethod
    def _facade_owner(
        cls,
        tree: ast.Module,
        local: m.Infra.RopeProjectLayout,
    ) -> p.Result[tuple[str, str]]:
        result_type = r[tuple[str, str]]
        classes = tuple(node for node in tree.body if isinstance(node, ast.ClassDef))
        if (
            len(classes) != 1
            or len(classes[0].bases) != 1
            or not isinstance(classes[0].bases[0], ast.Name)
        ):
            return result_type.fail(
                "staged t consumer requires one thin full-owner class"
            )
        public = classes[0]
        parent = public.bases[0]
        if not isinstance(parent, ast.Name):
            return result_type.fail("staged public class has no named full owner")
        imported = cls._absolute_imports(tree).get(parent.id)
        if (
            imported is None
            or imported[1] != public.name
            or not imported[0].startswith(f"{local.package_name}.")
        ):
            return result_type.fail(
                "staged facade must inherit its canonical local full owner"
            )
        return result_type.ok((imported[0], public.name))

    @classmethod
    def _owner_contract(
        cls,
        tree: ast.Module,
        classname: str,
    ) -> p.Result[tuple[tuple[tuple[str, str], ...], tuple[str, ...]]]:
        result_type = r[tuple[tuple[tuple[str, str], ...], tuple[str, ...]]]
        owner = next(
            (
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == classname
            ),
            None,
        )
        if owner is None:
            return result_type.fail("canonical owner class is absent")
        upstream_imports = cls._absolute_imports(tree)
        upstream: list[tuple[str, str]] = []
        for parent in owner.bases:
            if not isinstance(parent, ast.Name) or parent.id not in upstream_imports:
                return result_type.fail(
                    "full owner must declare an importable upstream base"
                )
            upstream.append(upstream_imports[parent.id])
        members = tuple(
            node.name if isinstance(node, ast.ClassDef) else node.name.id
            for node in owner.body
            if isinstance(node, ast.ClassDef | ast.TypeAlias)
        )
        return result_type.ok((tuple(upstream), members))

    @staticmethod
    def _facade_plan(
        file: m.Infra.CodegenFilePlan,
        local: m.Infra.RopeProjectLayout,
        selected: list[m.Infra.RopeProjectLayout],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        layouts: t.MutableMappingKV[str, m.Infra.RopeProjectLayout],
    ) -> p.Result[m.Infra.StagePackagePlan]:
        result_type = r[m.Infra.StagePackagePlan]
        if file.desired_content is None:
            return result_type.fail(
                "staged facade requires an existing package and desired bytes"
            )
        tree = ast.parse(
            file.desired_content.decode(c.DEFAULT_ENCODING),
            filename=str(file.path),
        )
        facade = FlextInfraStagedPackage._facade_owner(tree, local)
        if facade.failure:
            return result_type.from_failure(facade)
        owner_module, classname = facade.value
        owner_path = local.src_dir / Path(*owner_module.split(".")).with_suffix(
            c.Infra.EXT_PYTHON
        )
        owner_state = states.get(owner_path)
        if owner_state is None or owner_state.content is None:
            return result_type.fail(f"canonical owner was not pinned: {owner_path}")
        owner_tree = ast.parse(
            owner_state.content.decode(c.DEFAULT_ENCODING), filename=str(owner_path)
        )
        contract = FlextInfraStagedPackage._owner_contract(owner_tree, classname)
        if contract.failure:
            return result_type.from_failure(contract)
        upstream, members = contract.value
        return result_type.ok(
            m.Infra.StagePackagePlan(
                package=local.package_name,
                module=f"{local.package_name}.{file.path.stem}",
                classname=classname,
                owner_module=owner_module,
                upstream=upstream,
                members=members,
                layouts=tuple(selected),
                inputs=tuple(states.values()),
                workspace_packages=tuple(sorted(layouts)),
            )
        )


__all__ = ("FlextInfraStagedPackage",)
