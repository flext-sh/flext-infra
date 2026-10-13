"""Resolve a bounded candidate package from canonical pinned workspace sources.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codegen import FlextInfraMiseArtifactsVerification


class FlextInfraStagedPackage:
    """Plan one complete package view and its static workspace import closure."""

    @classmethod
    def plan_sources(
        cls,
        workspace: Path,
        updates: t.MappingKV[Path, str],
        *,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState] = (),
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Pin real project inputs for preview without writing live source.

        Args:
            workspace: The root of the Git workspace containing the projects.
            updates: A mapping from file paths to their desired content.
            inputs: Original caller snapshots, never replaced by a fresh observation.

        Returns:
            A result wrapping the planned stage source or the first failure encountered.
        """
        result_type = r[m.Infra.StageSourcePlan]
        workspace = workspace.resolve()
        if any(not before.path.is_relative_to(workspace) for before in inputs):
            return result_type.fail("candidate original source escapes workspace")
        destinations = cls._normalized_updates(workspace, updates)
        if destinations.failure:
            return result_type.from_failure(destinations)
        normalized = destinations.value
        discovered = cls._workspace_layouts(workspace)
        if discovered.failure:
            return result_type.from_failure(discovered)
        layouts = discovered.value
        selected: list[m.Infra.RopeProjectLayout] = []
        states: dict[Path, m.Cli.AtomicFileState] = {}
        source_paths = dict.fromkeys((
            *normalized,
            *(
                before.path
                for before in inputs
                if before.path.suffix in {".py", ".pyi"}
            ),
        ))
        for path in source_paths:
            resolved = cls._source_layout(path, layouts)
            if resolved.failure:
                return result_type.from_failure(resolved)
            local = resolved.value
            if not any(item.project_root == local.project_root for item in selected):
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
        for before in inputs:
            if states.get(before.path) != before:
                return result_type.fail(
                    f"candidate original source identity changed: {before.path}",
                )
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
    def _normalized_updates(
        workspace: Path,
        updates: t.MappingKV[Path, str],
    ) -> p.Result[dict[Path, str]]:
        """Elect one contained physical destination per desired source.

        Returns:
            Desired sources or the first ambiguous, foreign or symlinked path.
        """
        result_type = r[dict[Path, str]]
        normalized: dict[Path, str] = {}
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
        layouts: dict[str, m.Infra.RopeProjectLayout],
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
        actual.update(
            path
            for path in (
                plan.workspace / c.PYPROJECT_FILENAME,
                plan.workspace / ".gitmodules",
                plan.workspace / "uv.lock",
            )
            if path.is_file()
        )
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
        states: dict[Path, m.Cli.AtomicFileState] = {}
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
    ) -> p.Result[dict[str, m.Infra.RopeProjectLayout]]:

        declarations = u.Infra.git_submodule_declarations(workspace)
        if declarations.failure:
            return r[dict[str, m.Infra.RopeProjectLayout]].from_failure(declarations)
        layouts: dict[str, m.Infra.RopeProjectLayout] = {}
        for repository in (
            workspace,
            *(workspace / declaration.path for declaration in declarations.value),
        ):
            layout = u.Infra.layout(repository)
            if layout is not None:
                if layout.package_name in layouts:
                    return r[dict[str, m.Infra.RopeProjectLayout]].fail(
                        f"ambiguous candidate package: {layout.package_name}"
                    )
                layouts[layout.package_name] = layout
        return r[dict[str, m.Infra.RopeProjectLayout]].ok(layouts)

    @staticmethod
    def _source_paths(
        layout: m.Infra.RopeProjectLayout,
        *,
        governed: bool = False,
    ) -> p.Result[list[Path]]:
        paths = [layout.project_root / c.PYPROJECT_FILENAME]
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
        states: dict[Path, m.Cli.AtomicFileState],
        *,
        updates: t.MappingKV[Path, str] | None = None,
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
            content = (
                updates[path].encode(c.DEFAULT_ENCODING)
                if updates is not None and path in updates
                else state.content
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
        layouts: dict[str, m.Infra.RopeProjectLayout],
        selected: list[m.Infra.RopeProjectLayout],
        states: dict[Path, m.Cli.AtomicFileState],
        *,
        updates: t.MappingKV[Path, str] | None = None,
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
    def _pin_workspace_metadata(
        workspace: Path,
        states: dict[Path, m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        for path in (
            workspace / c.PYPROJECT_FILENAME,
            workspace / ".gitmodules",
            workspace / "uv.lock",
        ):
            if path in states:
                continue
            observed = u.Cli.atomic_read_binary_file_state(path, required=False)
            if observed.failure:
                return r[bool].from_failure(observed)
            states[path] = observed.value
        return r[bool].ok(value=True)

    @staticmethod
    def _absolute_imports(tree: ast.Module) -> dict[str, tuple[str, str]]:
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
        states: dict[Path, m.Cli.AtomicFileState],
        layouts: dict[str, m.Infra.RopeProjectLayout],
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
