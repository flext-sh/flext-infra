"""Plan a bounded candidate source tree from the live workspace and planned sources.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from os.path import commonpath
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from types import MappingProxyType

from flext_infra import c, config, m, p, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraStagedPackage:
    """Plan one complete candidate tree and its static workspace import closure."""

    @staticmethod
    def source_preparation_bootstrap() -> str:
        """Select SOURCE temporary storage and describe that same public operation.

        Source preparation uses ``TemporaryDirectory(dir=None)``. Its selected
        storage is therefore part of the prepared producer's runtime, not an
        expected cache value to copy into a cold interpreter.

        Returns:
            The SOURCE-only cold replay of the real stdlib directory selection.

        """
        gettempdir()
        return "from tempfile import gettempdir as _source_storage\n_source_storage()\n"

    def preview_sources[T](
        self,
        workspace: Path,
        updates: t.MappingKV[Path, str | None],
        validator: Callable[[Path, t.MappingKV[Path, Path]], T],
        *,
        options: m.Infra.CodegenSourcePreviewOptions | None = None,
    ) -> p.Result[T]:
        """Validate updates and retirements inside a candidate tree.

        The candidate tree lives beside the workspace's mutation lock, on the
        destination filesystem and outside the working tree, and is removed
        once the validator returns.

        Returns:
            The validator outcome, or the first planning or staging failure.

        """
        options = options or m.Infra.CodegenSourcePreviewOptions()
        planned = self.plan_sources(
            workspace,
            updates,
            options=m.Infra.StageSourceOptions(
                workspaces=options.workspaces, modes=options.modes
            ),
        )
        if planned.failure:
            return r[T].from_failure(planned)
        plan = planned.value
        lock = u.Infra.mutation_lock_path(plan.workspace)
        if lock.failure:
            return r[T].from_failure(lock)
        storage = u.Cli.ensure_dir(lock.value.parent)
        if storage.failure:
            return r[T].from_failure(storage)
        with TemporaryDirectory(
            prefix="flext-source-preview-", dir=lock.value.parent
        ) as directory:
            root = Path(directory)
            materialized = self.materialize_sources(plan, root)
            if materialized.failure:
                return r[T].from_failure(materialized)
            return r[T].ok(
                validator(
                    root,
                    {
                        path: root / path.relative_to(plan.workspace)
                        for path in plan.updates
                    },
                )
            )

    @staticmethod
    def source_writes(
        plan: m.Infra.StageSourcePlan,
        view_root: Path,
    ) -> t.VariadicTuple[tuple[Path, bytes, int]]:
        """Materialize the same composition for preparation and admission.

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
                    plan.modes.get(
                        before.path,
                        before.mode
                        if before.mode is not None
                        else c.Infra.CONFIG_SPEC[1],
                    ),
                ))
        return tuple(writes)

    @classmethod
    def prepare_sources(
        cls,
        plan: m.Infra.StageSourcePlan,
        preparer: Callable[[Path, t.MappingKV[Path, Path]], p.Result[bool]],
    ) -> p.Result[t.MappingKV[Path, str | None]]:
        """Prepare producer bytes in a temporary candidate tree.

        The preparation tree owns no runtime environment. Only desired source
        bytes leave it.

        Returns:
            Prepared updates, or the original staging or repair failure.

        """
        result_type = r[t.MappingKV[Path, str | None]]
        cls.source_preparation_bootstrap()
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
            return cls._verify_unselected_writes(
                writes, frozenset(candidates.values())
            ).flat_map(lambda _: cls._prepared_candidate_updates(plan, candidates))

    @staticmethod
    def _verify_unselected_writes(
        writes: t.VariadicTuple[tuple[Path, bytes, int]],
        selected: frozenset[Path],
    ) -> p.Result[bool]:
        """Prove the preparer left every unselected staged input unchanged.

        Args:
            writes: Exact staged destinations, bytes and permissions.
            selected: Candidate destinations the preparer may have rewritten.

        Returns:
            Acceptance while every unselected input keeps its staged identity.

        """
        for path, content, mode in writes:
            if path in selected:
                continue
            observed = u.Cli.atomic_read_binary_file_state(path, required=True)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value.content != content or observed.value.mode != mode:
                return r[bool].fail(
                    f"source preparation changed an unselected input: {path}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _prepared_candidate_updates(
        plan: m.Infra.StageSourcePlan,
        candidates: t.MappingKV[Path, Path],
    ) -> p.Result[t.MutableMappingKV[Path, str | None]]:
        """Read the prepared candidate bytes back as updated live sources.

        Args:
            plan: The planned candidate sources.
            candidates: Prepared candidate destinations keyed by live path.

        Returns:
            Prepared updates keyed by live destination, or the read failure.

        """
        updates = dict(plan.updates)
        for destination, candidate in candidates.items():
            observed = u.Cli.atomic_read_binary_file_state(candidate, required=True)
            if observed.failure:
                return r[dict[Path, str | None]].from_failure(observed)
            content = observed.value.content
            if content is None:
                return r[dict[Path, str | None]].fail(
                    f"prepared source disappeared: {destination}"
                )
            updates[destination] = content.decode(c.DEFAULT_ENCODING)
        return r[dict[Path, str | None]].ok(updates)

    @classmethod
    def materialize_sources(
        cls,
        plan: m.Infra.StageSourcePlan,
        root: Path,
    ) -> p.Result[bool]:
        """Write the planned composition into an exclusively owned empty tree.

        Returns:
            Success after the writes, or their first original failure.

        """
        for path, content, mode in cls.source_writes(plan, root):
            created = u.Cli.ensure_dir(path.parent)
            if created.failure:
                return r[bool].from_failure(created)
            before = u.Cli.atomic_read_binary_file_state(path)
            if before.failure:
                return r[bool].from_failure(before)
            written = u.Cli.atomic_write_binary_file_guarded(
                before.value, content, permission_mode=mode
            )
            if written.failure:
                return r[bool].from_failure(written)
        return r[bool].ok(value=True)

    @classmethod
    def plan_sources(
        cls,
        workspace: Path,
        updates: t.MappingKV[Path, str | None],
        *,
        options: m.Infra.StageSourceOptions | None = None,
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Elect the candidate closure of the desired sources.

        Args:
            workspace: The root of the Git workspace containing the projects.
            updates: Desired content by live path; None retires an artifact.
            options: Composition roots, file modes and declared file effects.

        Returns:
            A result wrapping the planned stage source or the first failure encountered.

        """
        options = options or m.Infra.StageSourceOptions()
        result_type = r[m.Infra.StageSourcePlan]
        modes = cls._validated_effect_modes(
            options.declared_files, updates, options.modes
        )
        if modes.failure:
            return result_type.from_failure(modes)
        if options.workspaces:
            return cls._composed_scope_plan(updates, options, modes.value)
        containing = cls.workspace_root(workspace.resolve())
        if containing.failure:
            return result_type.from_failure(containing)
        workspace = containing.value
        errors: t.VariadicTuple[type[Exception]] = (OSError, *c.EXC_BROAD_RUNTIME)
        try:
            with u.Infra.facade_source_project(
                workspace,
                declared_files=options.declared_files,
                planned_sources=updates,
                project_roots=tuple(
                    dict.fromkeys(
                        file.project
                        for file in options.declared_files
                        if file.project.is_relative_to(workspace)
                    )
                ),
            ) as (source_project, _):
                return cls._source_plan_project(
                    workspace,
                    updates,
                    options.declared_files,
                    modes.value,
                    source_project,
                )
        except errors as exc:
            return result_type.fail(str(exc), exception=exc)

    @classmethod
    def _source_plan_project(
        cls,
        workspace: Path,
        updates: t.MappingKV[Path, str | None],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        modes: t.MappingKV[Path, int],
        source_project: p.Infra.RopeProject,
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Build the candidate plan from one Rope view of the workspace.

        Returns:
            The complete candidate plan or the original source failure.

        """
        discovered = cls._normalized_updates(workspace, updates).flat_map(
            lambda normalized: cls.workspace_layouts(
                workspace, source_project=source_project
            ).map(lambda layouts: (normalized, layouts))
        )
        if discovered.failure:
            return r[m.Infra.StageSourcePlan].from_failure(discovered)
        normalized, layouts = discovered.value
        closure = cls._source_closure(workspace, normalized, layouts, source_project)
        if closure.failure:
            return r[m.Infra.StageSourcePlan].from_failure(closure)
        selected, states = closure.value
        introduced = frozenset(
            item.project_root
            for item in selected
            if item.project_root / c.PYPROJECT_FILENAME in normalized
            and states[item.project_root / c.PYPROJECT_FILENAME].content is None
        )
        return r[m.Infra.StageSourcePlan].ok(
            m.Infra.StageSourcePlan(
                workspace=workspace,
                roots=tuple(
                    dict.fromkeys((
                        workspace,
                        *(item.project_root for item in selected),
                    ))
                ),
                inputs=tuple(states.values()),
                updates=MappingProxyType(dict(normalized)),
                modes=MappingProxyType(dict(modes)),
                declared_files=cls._declared_source_effects(
                    workspace, normalized, states, modes, declared_files
                ),
                layouts=tuple(
                    item for item in selected if item.project_root not in introduced
                ),
                workspace_packages=tuple(
                    sorted(
                        name
                        for name, item in layouts.items()
                        if item.project_root not in introduced
                    )
                ),
                candidate_layouts=tuple(selected),
                candidate_workspace_packages=tuple(sorted(layouts)),
            )
        )

    @staticmethod
    def _validated_effect_modes(
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
        updates: t.MappingKV[Path, str | None],
        modes: t.MappingKV[Path, int] | None,
    ) -> p.Result[t.MutableMappingKV[Path, int]]:
        """Validate declared file effects and merge their modes.

        Args:
            declared_files: Declared file effects of the candidate.
            updates: Desired content by live path; None retires an artifact.
            modes: Desired file-effect modes supplied by the caller.

        Returns:
            The validated mode mapping covering every declared effect.

        """
        result_type = r[dict[Path, int]]
        if len({plan.path for plan in declared_files}) != len(declared_files):
            return result_type.fail("candidate has competing declared file effects")
        if any(plan.path not in updates for plan in declared_files):
            return result_type.fail("declared file has no desired source effect")
        effect_modes = {
            plan.path: plan.desired_mode
            for plan in declared_files
            if plan.desired_mode is not None
        }
        for path, mode in (modes or {}).items():
            if effect_modes.setdefault(path, mode) != mode:
                return result_type.fail(f"candidate mode competes: {path}")
        if not set(effect_modes).issubset(updates):
            return result_type.fail("candidate mode has no declared file effect")
        return result_type.ok(effect_modes)

    @classmethod
    def _composed_scope_plan(
        cls,
        updates: t.MappingKV[Path, str | None],
        options: m.Infra.StageSourceOptions,
        modes: t.MappingKV[Path, int],
    ) -> p.Result[m.Infra.StageSourcePlan]:
        """Compose one joint plan from explicit non-overlapping scope roots.

        Args:
            updates: Desired content by live path; None retires an artifact.
            options: Scopes and declared file effects.
            modes: Validated file-effect modes.

        Returns:
            The composed joint plan, or the first scope composition failure.

        """
        result_type = r[m.Infra.StageSourcePlan]
        scopes = tuple(dict.fromkeys(path.resolve() for path in options.workspaces))
        if any(
            left != right and left.is_relative_to(right)
            for left in scopes
            for right in scopes
        ) or any(
            not any(path.is_relative_to(root) for root in scopes) for path in updates
        ):
            return result_type.fail("candidate scopes overlap or omit a rewrite target")
        plans: list[m.Infra.StageSourcePlan] = []
        for root in scopes:
            planned = cls.plan_sources(
                root,
                {
                    path: source
                    for path, source in updates.items()
                    if path.is_relative_to(root)
                },
                options=m.Infra.StageSourceOptions(
                    modes={
                        path: mode
                        for path, mode in modes.items()
                        if path.is_relative_to(root)
                    },
                    declared_files=tuple(
                        file
                        for file in options.declared_files
                        if file.path.is_relative_to(root)
                    ),
                ),
            )
            if planned.failure:
                return result_type.from_failure(planned)
            plans.append(planned.value)
        packages: t.MutableMappingKV[str, Path] = {}
        for plan in plans:
            for layout in plan.candidate_layouts:
                if (
                    packages.setdefault(layout.package_name, layout.project_root)
                    != layout.project_root
                ):
                    return result_type.fail(
                        f"ambiguous elected candidate package: {layout.package_name}"
                    )
        return result_type.ok(
            m.Infra.StageSourcePlan(
                workspace=Path(commonpath(plan.workspace for plan in plans)),
                workspaces=scopes,
                roots=tuple(
                    dict.fromkeys(root for plan in plans for root in plan.roots)
                ),
                inputs=tuple({
                    state.path: state for plan in plans for state in plan.inputs
                }.values()),
                updates=MappingProxyType({
                    path: source
                    for plan in plans
                    for path, source in plan.updates.items()
                }),
                modes=MappingProxyType({
                    path: mode for plan in plans for path, mode in plan.modes.items()
                }),
                declared_files=tuple(
                    file for plan in plans for file in plan.declared_files
                ),
                layouts=tuple(layout for plan in plans for layout in plan.layouts),
                workspace_packages=tuple(
                    sorted({name for plan in plans for name in plan.workspace_packages})
                ),
                candidate_layouts=tuple(
                    layout for plan in plans for layout in plan.candidate_layouts
                ),
                candidate_workspace_packages=tuple(
                    sorted({
                        name
                        for plan in plans
                        for name in plan.candidate_workspace_packages
                    })
                ),
            )
        )

    @classmethod
    def _source_closure(
        cls,
        workspace: Path,
        normalized: t.MappingKV[Path, str | None],
        layouts: t.MutableMappingKV[str, m.Infra.RopeProjectLayout],
        source_project: p.Infra.RopeProject,
    ) -> p.Result[
        t.Pair[
            list[m.Infra.RopeProjectLayout],
            t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        ]
    ]:
        """Elect the layouts and file states of the candidate tree.

        Args:
            workspace: Resolved root of the Git workspace containing the projects.
            normalized: Elected physical destinations of the desired sources.
            layouts: Retained provider layouts keyed by package name.
            source_project: The Rope view of the workspace.

        Returns:
            The elected layouts with the file states of their sources.

        """
        result_type = r[
            t.Pair[
                list[m.Infra.RopeProjectLayout],
                dict[Path, m.Cli.AtomicFileState],
            ]
        ]
        selected: list[m.Infra.RopeProjectLayout] = []
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}

        def read_layout(
            provider: m.Infra.RopeProjectLayout,
            owned: t.MappingKV[Path, str | None] | None,
        ) -> p.Result[tuple[str, ...]]:
            return cls._layout_states(
                provider, states, source_project, updates=owned
            )

        roots: list[t.Pair[m.Infra.RopeProjectLayout, bool]] = []
        for path in normalized:
            resolved = cls._source_layout(path, layouts)
            if resolved.success:
                roots.append((resolved.value, True))
                continue
            # A common Python source outside every package needs only its
            # own original bytes: repair groups it by the workspace cwd.
            if path.is_symlink():
                return result_type.fail(f"candidate source is a symlink: {path}")
            states.setdefault(path, source_project.source_state(path, required=False))
        roots.extend(
            (layouts[name], False)
            for _, name in u.family_discovery_candidates()
            if name in layouts
        )
        for local, rewritten in roots:
            if any(item.project_root == local.project_root for item in selected):
                continue
            closure = cls._closure(
                local,
                layouts,
                read_layout,
                updates=normalized if rewritten else None,
            )
            if closure.failure:
                return result_type.from_failure(closure)
            selected.extend(item for item in closure.value if item not in selected)
        paths = cls._workspace_metadata_paths(workspace)
        if paths.failure:
            return result_type.from_failure(paths)
        for path in paths.value:
            states.setdefault(path, source_project.source_state(path, required=False))
        return result_type.ok((selected, states))

    @staticmethod
    def _declared_source_effects(
        workspace: Path,
        normalized: t.MappingKV[Path, str | None],
        states: t.MappingKV[Path, m.Cli.AtomicFileState],
        modes: t.MappingKV[Path, int],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Build one file effect per normalized desired source.

        A declared effect already carries the desired bytes and mode, so it is
        passed through unchanged.

        Args:
            workspace: Resolved root of the Git workspace containing the projects.
            normalized: Elected physical destinations of the desired sources.
            states: Live file states keyed by source path.
            modes: Validated file-effect modes covering every declared effect.
            declared_files: Declared file effects of the candidate.

        Returns:
            The file effects of the composed candidate.

        """
        declared = {plan.path: plan for plan in declared_files}
        effects: list[m.Infra.CodegenFilePlan] = []
        for path, source in normalized.items():
            if path in declared:
                effects.append(declared[path])
                continue
            content = None if source is None else source.encode(c.DEFAULT_ENCODING)
            effects.append(
                m.Infra.CodegenFilePlan(
                    project=u.Infra.project_root(path) or workspace,
                    path=path,
                    before=states[path],
                    desired_content=content,
                    desired_mode=(
                        None
                        if content is None
                        else modes.get(
                            path,
                            states[path].mode
                            if states[path].mode is not None
                            else c.Infra.CONFIG_SPEC[1],
                        )
                    ),
                )
            )
        return tuple(effects)

    @staticmethod
    def _normalized_updates(
        workspace: Path,
        updates: t.MappingKV[Path, str | None],
    ) -> p.Result[t.MutableMappingKV[Path, str | None]]:
        """Elect one contained physical destination per desired source.

        Every desired destination must be a contained, physical, unambiguous
        workspace path.

        Returns:
            Desired sources or the first ambiguous, foreign or symlinked path.

        """
        result_type = r[dict[Path, str | None]]
        normalized: t.MutableMappingKV[Path, str | None] = {}
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
        local = max(
            (
                layout
                for layout in layouts.values()
                if path.is_relative_to(layout.project_root)
            ),
            key=lambda layout: len(layout.project_root.parts),
            default=None,
        )
        if local is None:
            return result_type.fail(f"preview source has no project layout: {path}")
        return result_type.ok(local)

    @staticmethod
    def workspace_root(root: Path) -> p.Result[Path]:
        """Resolve the package's Git workspace identity.

        Returns:
            The superproject root or the standalone repository root.

        """
        request = m.Infra.GitRepoRequest(repo_root=root)
        inside = u.Infra.git_is_inside_work_tree(request)
        if inside.failure:
            return r[Path].from_failure(inside)
        if not inside.value.value:
            return r[Path].ok(root.resolve())
        return u.Infra.git_repository_root(request).map(
            lambda identity: identity.repository_root,
        )

    @staticmethod
    def workspace_layouts(
        workspace: Path,
        *,
        source_project: p.Infra.RopeProject | None = None,
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
            applicability = u.Infra.repository_operation_applicability(
                target,
                mutating=False,
            )
            if applicability.failure:
                return result_type.from_failure(applicability)
            layout = u.Infra.layout(repository, rope_project=source_project)
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
        source_project: p.Infra.RopeProject,
        *,
        governed: bool = False,
    ) -> p.Result[list[Path]]:
        """Collect declared resources and the complete applicable Python closure.

        Git membership alone does not make unrelated content a source input.

        Args:
            layout: The provider layout whose source paths are collected.
            source_project: The Rope view of the workspace.
            governed: Whether rewrite targets elect the governed closure walk.

        Returns:
            The collected physical paths, or the first symlink failure.

        """
        paths = [layout.project_root / c.PYPROJECT_FILENAME] if governed else []
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
                        source_project=source_project,
                    )
                ),
            )
        walked = FlextInfraStagedPackage._physical_directory_paths(
            directories, source_project, governed=governed
        )
        if walked.failure:
            return r[list[Path]].from_failure(walked)
        paths.extend(walked.value)
        return r[list[Path]].ok(sorted(set(paths)))

    @staticmethod
    def _physical_directory_paths(
        directories: t.VariadicTuple[Path],
        source_project: p.Infra.RopeProject,
        *,
        governed: bool,
    ) -> p.Result[list[Path]]:
        """Walk declared directories rejecting symlinks and excluded members.

        Args:
            directories: Physical directories admitted for the closure.
            source_project: The Rope view of the workspace.
            governed: Whether the governed walk applies exclusion pruning.

        Returns:
            The walked directory paths, or the first symlink failure.

        """
        paths: list[Path] = []
        for directory in directories:
            if directory.is_symlink():
                return r[list[Path]].fail(
                    f"candidate source directory is a symlink: {directory}"
                )
            if source_project.source_query(directory, "isdir"):
                for parent, children, files in source_project.source_walk(directory):
                    for name in (*children, *files):
                        if (parent / name).is_symlink():
                            return r[list[Path]].fail(
                                f"candidate source is a symlink: {parent / name}",
                            )
                    children[:] = [
                        name
                        for name in children
                        if (not governed and name != "__pycache__")
                        or (
                            governed
                            and name not in config.Infra.codegen.analysis_excluded_dirs
                            and not name.startswith(".")
                            and not source_project.source_query(
                                parent / name / c.PYPROJECT_FILENAME, "isfile"
                            )
                        )
                    ]
                    paths.extend(parent / name for name in files)
            elif directory.is_file():
                paths.append(directory)
        return r[list[Path]].ok(paths)

    @staticmethod
    def _runtime_imports(
        path: Path,
        content: bytes,
        *,
        runtime_only: bool = True,
    ) -> tuple[str, ...]:
        """Name the absolute modules imported by one source.

        Type-only guards are excluded when ``runtime_only`` is set.

        Returns:
            The imported module names in source order.

        """
        tree = ast.parse(content.decode(c.DEFAULT_ENCODING), filename=str(path))
        excluded = (
            {
                id(child)
                for guard in ast.walk(tree)
                if isinstance(guard, ast.If)
                and (
                    (
                        isinstance(guard.test, ast.Name)
                        and guard.test.id == "TYPE_CHECKING"
                    )
                    or (
                        isinstance(guard.test, ast.Attribute)
                        and guard.test.attr == "TYPE_CHECKING"
                    )
                )
                for statement in guard.body
                for child in ast.walk(statement)
            }
            if runtime_only
            else set[int]()
        )
        modules: list[str] = []
        for node in ast.walk(tree):
            if id(node) in excluded:
                continue
            if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                modules.append(node.module)
            elif isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
        return tuple(modules)

    @classmethod
    def _layout_states(
        cls,
        layout: m.Infra.RopeProjectLayout,
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        source_project: p.Infra.RopeProject,
        *,
        updates: t.MappingKV[Path, str | None] | None = None,
    ) -> p.Result[tuple[str, ...]]:
        """Read one layout's sources and collect their package dependencies.

        A rewritten project receives the full native checker, not a file gate,
        so its non-effect sources belong to the candidate tree too.

        Args:
            layout: The provider layout whose sources are read.
            states: File states extended by each source.
            source_project: The Rope view of the workspace.
            updates: Desired sources keyed by live path; None retires an artifact.

        Returns:
            The imports of the layout's sources.

        """
        paths = cls._source_paths(layout, source_project, governed=bool(updates))
        if paths.failure:
            return r[tuple[str, ...]].from_failure(paths)
        modules: list[str] = []
        source_paths = set(paths.value)
        if updates is not None:
            source_paths.update(updates)
        for path in sorted(source_paths):
            if path.is_symlink():
                return r[tuple[str, ...]].fail(f"candidate source is a symlink: {path}")
            if not path.is_file() and (updates is None or path not in updates):
                continue
            state = states.get(path)
            if state is None:
                state = source_project.source_state(
                    path, required=updates is None or path not in updates
                )
                states[path] = state
            content = state.content
            if updates is not None and path in updates:
                desired = updates[path]
                content = (
                    None if desired is None else desired.encode(c.DEFAULT_ENCODING)
                )
            if path.suffix in {c.Infra.EXT_PYTHON, ".pyi"} and content is not None:
                modules.extend(
                    cls._runtime_imports(path, content, runtime_only=not updates)
                )
        return r[tuple[str, ...]].ok(tuple(modules))

    @classmethod
    def _closure(
        cls,
        local: m.Infra.RopeProjectLayout,
        layouts: t.MutableMappingKV[str, m.Infra.RopeProjectLayout],
        read: Callable[
            [m.Infra.RopeProjectLayout, t.MappingKV[Path, str | None] | None],
            p.Result[tuple[str, ...]],
        ],
        *,
        updates: t.MappingKV[Path, str | None] | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.RopeProjectLayout]]:
        """Traverse one layout's import closure across the retained providers.

        Args:
            local: The layout whose closure is traversed first.
            layouts: Every retained provider layout keyed by package name.
            read: The source reader of each layout, returning its imports.
            updates: Desired sources keyed by live path; None retires an artifact.

        Returns:
            The elected layouts of the traversed dependency closure.

        """
        selected: list[m.Infra.RopeProjectLayout] = []
        queue = [local.package_name]
        while queue:
            name = queue.pop(0)
            layout = layouts[name]
            selected.append(layout)
            owned: t.MutableMappingKV[Path, str | None] | None = None
            if updates is not None:
                owned = {}
                for path, content in updates.items():
                    owner = cls._source_layout(path, layouts)
                    if owner.failure:
                        return r[
                            t.VariadicTuple[m.Infra.RopeProjectLayout]
                        ].from_failure(owner)
                    if owner.value.project_root == layout.project_root:
                        owned[path] = content
            imported = read(layout, owned)
            if imported.failure:
                return r[t.VariadicTuple[m.Infra.RopeProjectLayout]].from_failure(
                    imported,
                )
            for module in imported.value:
                dependency = module.partition(".")[0]
                if (
                    dependency in layouts
                    and dependency not in queue
                    and not any(item.package_name == dependency for item in selected)
                ):
                    queue.append(dependency)
        return r[t.VariadicTuple[m.Infra.RopeProjectLayout]].ok(tuple(selected))

    @staticmethod
    def _workspace_metadata_paths(
        workspace: Path,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Name the source and selected resolver metadata from physical ownership.

        Workspace metadata exists only inside a Git work tree: the resolver,
        manifest and lock belong to a git workspace, and a plain directory
        declares none of them.

        Returns:
            The deduplicated resolver, manifest, lock and codegen source
            paths, or the first resolution failure.

        """
        inside = u.Infra.git_is_inside_work_tree(
            m.Infra.GitRepoRequest(repo_root=workspace),
        )
        if inside.failure:
            return r[t.VariadicTuple[Path]].from_failure(inside)
        if not inside.value.value:
            return r[t.VariadicTuple[Path]].ok(())
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


__all__ = ("FlextInfraStagedPackage",)
