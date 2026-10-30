"""Public Rope workspace DSL and facade mixin.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from keyword import iskeyword
from pathlib import Path
from types import TracebackType
from typing import Annotated, Self, override

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceRopeQuery


class FlextInfraRopeWorkspace(FlextInfraWorkspaceRopeQuery):
    """Open one shared Rope workspace with cached public DSL methods."""

    def facade_projection(
        self,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        planners: tuple[p.Infra.SourceInitializerPlanner, p.Infra.SourceViewProvider],
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
    ) -> m.Infra.CodegenRepositoryPlanOutcome:
        """Compose facade, native consumer and lazy-export effects in this session.

        Every family is planned against the same native source candidate. A failed
        family retains its original exception and contributes no incomplete effects.
        Publication and admission remain owned by the injected operation callbacks.

        Args:
            declared_files: The set of declared file plans to consider.
            planners: The source initializer and view provider planners.
            selection: Optional selection of a specific path and facade family.

        Returns:
            Complete candidate cohorts and the first causal planning diagnostics.

        Raises:
            ValueError: If the selection is invalid.

        """
        root, project = self.repository_root, self.rope_project
        initializer, _source_view = planners
        staged = {plan.path: plan for plan in declared_files}
        completed: dict[Path, m.Infra.CodegenFilePlan] = {}
        issues: list[m.Infra.Issue] = []
        failure: BaseException | None = None
        self.bind_candidate(declared_files=declared_files)
        sources = {
            Path(resource.real_path): project.source_text(Path(resource.real_path))
            for resource in project.get_python_files()
            if Path(resource.real_path).is_relative_to(root)
        }
        packages = sorted({
            path.parent
            for path in sources
            if path.name == c.Infra.INIT_PY
            and (selection is None or path.parent.is_relative_to(selection[0].parent))
        })
        families = u.Infra.facade_families()
        for package in packages:
            for letter, family in families.items():
                selected = c.Infra.FacadeFamily(letter)
                if (
                    selection is not None
                    and selection[1] is not None
                    and (package != selection[0].parent or selected is not selection[1])
                ):
                    continue
                directory = package / family.directory
                if not project.source_query(directory, "isdir"):
                    continue
                baseline = tuple(staged.values())
                cohort: dict[Path, m.Infra.CodegenFilePlan] = {}

                def stage(plans: Sequence[m.Infra.CodegenFilePlan]) -> None:
                    """Advance authenticated plans without replacing their witnesses."""
                    u.Infra.codegen_stage_file_plans(cohort, plans, ordered=True)
                    u.Infra.codegen_stage_file_plans(staged, plans, ordered=True)
                    self.bind_candidate(declared_files=tuple(staged.values()))

                def source(path: Path, text: str) -> None:
                    """Bind a source result through the existing file-plan owner."""
                    planned = u.Infra.workspace_declared_sources(
                        Path(project.root.real_path),
                        (),
                        {path: text},
                        source_project=project,
                    )
                    stage(tuple(plan for plan in planned if plan.path == path))

                try:
                    destination = u.Infra.facade_module_path(
                        package, letter, project=project, sources=sources
                    )
                    if destination is None:
                        if u.Infra.facade_component_declarations(project, directory):
                            message = f"Family declarations have no facade: {directory}"
                            raise ValueError(message)
                        continue
                    domains = sorted(
                        {
                            parent
                            for path in sources
                            if path.is_relative_to(directory)
                            for parent in path.parents
                            if parent != directory
                            and parent.is_relative_to(directory)
                            and all(
                                part.startswith("_")
                                for part in parent.relative_to(directory).parts
                            )
                        },
                        key=lambda path: (-len(path.parts), path),
                    )
                    for domain in domains:
                        owners = u.Infra.family_subfacade_owners(project, domain)
                        if len(owners) > 1:
                            message = (
                                f"Competing native domain owners: {domain}: {owners}"
                            )
                            raise ValueError(message)
                        target = domain.parent / f"{domain.name.lstrip('_')}.py"
                        if owners:
                            original, name = owners[0]
                            if (
                                original
                                == directory / c.Infra.IMPORT_LAW_FAMILY_BASE_FILE
                                and original != target
                            ):
                                message = (
                                    f"Root family base cannot move to a domain: "
                                    f"{domain}"
                                )
                                raise ValueError(message)
                            if original != target:
                                captured = {
                                    Path(resource.real_path): project.source_text(
                                        Path(resource.real_path)
                                    )
                                    for resource in project.get_python_files()
                                }
                                stage(
                                    u.Infra.plan_module_move(
                                        project,
                                        original,
                                        destination_file=target,
                                        inputs=u.Infra.NativeSourceView(
                                            captured,
                                            tuple(
                                                project.source_state(
                                                    path, required=False
                                                )
                                                for path in captured
                                            ),
                                            declared_files=tuple(staged.values()),
                                        ),
                                    )
                                )
                        else:
                            if project.source_query(target, "exists"):
                                message = (
                                    f"Domain destination has unrelated "
                                    f"ownership: {target}"
                                )
                                raise ValueError(message)
                            declarations = u.Infra.facade_component_declarations(
                                project, domain
                            )
                            if not declarations:
                                continue
                            prefix = u.Infra.project_prefix(
                                target, source_project=project
                            )
                            if not prefix:
                                message = (
                                    f"Domain has no native project identity: {domain}"
                                )
                                raise ValueError(message)
                            name = (
                                prefix
                                + family.suffix
                                + u.derive_class_stem(
                                    "-".join(
                                        part.lstrip("_").replace("_", "-")
                                        for part in domain.relative_to(directory).parts
                                    )
                                )
                            )
                            domain_module = project.get_pymodule(
                                project.get_folder(
                                    domain.relative_to(
                                        Path(project.root.real_path)
                                    ).as_posix()
                                )
                            )
                            documentation = domain_module.get_doc()
                            if not documentation:
                                message = (
                                    f"Domain has no declared documentation: {domain}"
                                )
                                raise ValueError(message)
                            source(
                                target,
                                u.Infra.generate_module_skeleton(
                                    class_name=name,
                                    base_class=None,
                                    base_module=None,
                                    docstring=documentation,
                                ),
                            )
                        exports = initializer(
                            root,
                            declared_files=tuple(staged.values()),
                            snapshot=self.snapshot,
                            selection=selection,
                        )
                        if exports.failure:
                            raise exports.exception or ValueError(exports.error)
                        stage(exports.value)
                        source(
                            target,
                            u.Infra.facade_component_source(
                                project,
                                target,
                                domain,
                                family=selected,
                                owner_name=name,
                            ),
                        )
                    rendered = (
                        u.Infra.render_type_facade(
                            package, destination, sources, project=project
                        )
                        if selected is c.Infra.FacadeFamily.T
                        else u.Infra.render_utility_facade(
                            package, family=selected, project=project, sources=sources
                        )
                    )
                    if rendered is not None:
                        source(destination, rendered)
                    stage(
                        u.Infra.plan_component_consumers(
                            root,
                            source_project=project,
                            declared_files=tuple(staged.values()),
                        )
                    )
                    if selected is c.Infra.FacadeFamily.U:
                        stage(
                            u.Infra.facade_component_retirements(
                                project,
                                tuple(
                                    path
                                    for path in cohort
                                    if path.suffix == c.Infra.EXT_PYTHON
                                ),
                                declared_files=tuple(staged.values()),
                            )
                        )
                    exports = initializer(
                        root,
                        declared_files=tuple(staged.values()),
                        snapshot=self.snapshot,
                        selection=selection,
                    )
                    if exports.failure:
                        raise exports.exception or ValueError(exports.error)
                    stage(exports.value)
                except (ValueError, OSError, *u.Infra.rope_hierarchy_errors()) as error:
                    error.add_note(f"facade cohort={directory}; repository={root}")
                    if failure is None:
                        failure = error
                    issues.append(
                        m.Infra.Issue(
                            file=str(directory),
                            line=0,
                            column=0,
                            code=c.Infra.ToolOutcome.ERROR.value,
                            message=str(error),
                        )
                    )
                    staged = {plan.path: plan for plan in baseline}
                    self.bind_candidate(declared_files=baseline)
                else:
                    u.Infra.codegen_stage_file_plans(
                        completed, tuple(cohort.values()), ordered=True
                    )
        return m.Infra.CodegenRepositoryPlanOutcome(
            repository=root.name,
            files=tuple(completed.values()),
            issues=tuple(issues),
            exception=failure,
            error=str(failure) if failure is not None else "",
            error_type=(
                f"{type(failure).__module__}.{type(failure).__qualname__}"
                if failure is not None
                else ""
            ),
        )

    rope_repository_root_override: Annotated[
        Path | None,
        m.Field(description="Optional Rope project root; defaults to repository_root"),
    ] = None

    _codegen_projects: tuple[p.Infra.ProjectInfo, ...] | None = m.PrivateAttr(
        default_factory=lambda: None,
    )
    _candidate_scope: ExitStack | None = m.PrivateAttr(default=None)
    _candidate_files: tuple[m.Infra.CodegenFilePlan, ...] = m.PrivateAttr(default=())
    _candidate_source_folders: t.StrTuple | None = m.PrivateAttr(default=None)
    _project_layout_cache: MutableMapping[str, m.Infra.RopeProjectLayout | None] = (
        m.PrivateAttr(default_factory=dict[str, m.Infra.RopeProjectLayout | None])
    )
    _package_context_cache: MutableMapping[str, m.Infra.LazyInitPackageContext] = (
        m.PrivateAttr(default_factory=dict[str, m.Infra.LazyInitPackageContext])
    )
    _module_policy_cache: MutableMapping[
        tuple[str, str, str],
        m.Infra.NamespaceModulePolicy,
    ] = m.PrivateAttr(
        default_factory=dict[tuple[str, str, str], m.Infra.NamespaceModulePolicy]
    )
    _module_convention_cache: MutableMapping[str, m.Infra.RopeModuleConvention] = (
        m.PrivateAttr(default_factory=dict[str, m.Infra.RopeModuleConvention])
    )
    _module_object_cache: MutableMapping[
        tuple[str, bool, bool],
        tuple[m.Infra.Object, ...],
    ] = m.PrivateAttr(
        default_factory=dict[tuple[str, bool, bool], tuple[m.Infra.Object, ...]]
    )

    @override
    def model_post_init(self, __context: Mapping[str, t.Scalar] | None, /) -> None:
        """Resolve the canonical Rope root once for the full session."""
        super().model_post_init(__context)
        self._rope_repository_root = (
            self.rope_repository_root_override
            or u.Infra.rope_repository_root(self.repository_root)
        )

    @classmethod
    def open_workspace(
        cls,
        repository_root: Path,
        *,
        rope_repository_root: Path | None = None,
        source_project: p.Infra.RopeProject | None = None,
        workspace_index: m.Infra.RopeWorkspaceIndex | None = None,
        snapshot: p.Infra.WorkspaceSnapshot | None = None,
    ) -> Self:
        """Create one ready-to-use Rope workspace session.

        The caller owns this session's lifetime. Explicitly supplied projects
        and indexes are borrowed; independent invocations never share state.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If an explicit source project does not match the
                declared workspace root, or an index is reused without it.

        """
        # Scan policy is owned only by the
        # validated config singleton, never copied into a session.
        resolved_rope_root = rope_repository_root or u.Infra.rope_repository_root(
            repository_root,
        )
        workspace = cls(
            repository_root=repository_root,
            rope_repository_root_override=resolved_rope_root,
        )
        if source_project is not None:
            if Path(source_project.root.real_path) != Path(
                source_project.fscommands.realpath(str(resolved_rope_root))
            ):
                msg = "Rope source project does not match the declared workspace root"
                raise ValueError(msg)
            workspace._rope_project = source_project
            workspace._view_project = source_project
            workspace._owns_rope_project = False
        if snapshot is not None:
            workspace._snapshot = snapshot
        if workspace_index is not None:
            if source_project is None:
                msg = "Rope structural index reuse requires its source project"
                raise ValueError(msg)
            workspace._workspace_index = workspace_index
        _ = workspace.rope_project
        return workspace

    @override
    def execute(self) -> p.Result[m.Infra.RopeWorkspaceSession]:
        """Materialize the public Rope session snapshot.

        Returns:
            The resulting ``p.Result[m.Infra.RopeWorkspaceSession]``.

        """
        snapshot: m.Infra.RopeWorkspaceSession = self.session_snapshot()
        return r[m.Infra.RopeWorkspaceSession].ok(snapshot)

    def session_snapshot(self) -> m.Infra.RopeWorkspaceSession:
        """Return the current public Rope session state.

        Returns:
            The current public Rope session state.

        """
        return m.Infra.RopeWorkspaceSession(
            repository_root=self.repository_root,
            rope_repository_root=self._rope_repository_root,
            workspace_index=self.workspace_index,
        )

    def bind_candidate(
        self,
        *,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...],
        additional_source_folders: t.StrTuple | None = None,
    ) -> None:
        """Advance this session to authenticated planned bytes without disk effects.

        Native source views remain bound until the session closes, so the next
        phase evolves the current candidate rather than reopening the original
        project. The native project owns resource notifications and inference
        invalidation; this method updates the DSL's derived query state. Callers
        re-elect native objects after binding rather than retaining an earlier
        view's inference objects as current declarations.

        Args:
            declared_files: Complete file declarations of the next candidate.
            additional_source_folders: Explicit roots, or the currently elected roots.

        Raises:
            ValueError: More than one declaration targets the same resource.

        """
        project = self.rope_project
        current_folders = tuple(folder.path for folder in project.get_source_folders())
        folders = (
            current_folders
            if additional_source_folders is None
            else additional_source_folders
        )
        if (
            self._candidate_scope is not None
            and declared_files == self._candidate_files
            and folders == self._candidate_source_folders
        ):
            return
        previous = {plan.path: plan for plan in self._candidate_files}
        prospective = {plan.path: plan for plan in declared_files}
        if len(prospective) != len(declared_files):
            message = "candidate contains multiple declarations for one resource"
            raise ValueError(message)
        changed = tuple(
            sorted(
                path
                for path in previous.keys() | prospective.keys()
                if previous.get(path) != prospective.get(path)
            )
        )
        index = self._workspace_index
        if (
            index is not None
            and changed
            and (self._module_object_cache or self._module_policy_cache)
        ):
            first = next(
                (
                    entry.module_name
                    for entry in index.modules_by_path.values()
                    if entry.module_name
                ),
                "",
            )
            if first:
                self.import_dependents(first)
        imports = dict(self._import_dependents_index or {})
        affected = self._candidate_dependents(index, changed, imports)
        scope = self._candidate_scope
        if scope is None:
            scope = ExitStack()
        scope.enter_context(
            project.source_view(
                declared_files=declared_files,
                additional_source_folders=folders,
            )
        )
        self._candidate_scope = scope
        self._candidate_files = declared_files
        self._candidate_source_folders = folders
        self._view_project = project
        if current_folders != tuple(
            folder.path for folder in project.get_source_folders()
        ):
            # A new native import-root election affects every namespace query.
            # The source-view owner has already notified its observers.
            self.refresh(validate_project=False)
            return
        if index is not None:
            self._workspace_index = u.Infra.index_rope_workspace(
                self.snapshot,
                self.repository_root,
                project=project,
                refresh=(index, changed),
            )
        if self._import_dependents_index is not None:
            self._refresh_candidate_imports(changed)
            affected.update(
                self._candidate_dependents(
                    self._workspace_index,
                    changed,
                    self._import_dependents_index,
                )
            )
        self._invalidate_candidate_queries(affected, changed, previous_index=index)

    @staticmethod
    def _candidate_dependents(
        index: m.Infra.RopeWorkspaceIndex | None,
        changed: Sequence[Path],
        imports: Mapping[str, tuple[Path, ...]],
    ) -> set[Path]:
        """Close source changes through the existing native import query index.

        Returns:
            Changed resources and consumers of their elected namespaces.

        """
        affected = set(changed)
        pending = list(changed)
        while pending and index is not None:
            path = pending.pop()
            entry = index.modules_by_path.get(str(path))
            if entry is None or not entry.module_name:
                continue
            namespace = entry.module_name.partition(".")[0]
            for target, consumers in imports.items():
                if target != namespace and not target.startswith(f"{namespace}."):
                    continue
                for consumer in consumers:
                    if consumer not in affected:
                        affected.add(consumer)
                        pending.append(consumer)
        return affected

    def _refresh_candidate_imports(self, changed: Sequence[Path]) -> None:
        """Replace only changed sources in the existing native import index."""
        index = self._import_dependents_index
        if index is None:
            return
        selected = frozenset(changed)
        updated = {
            target: {path for path in consumers if path not in selected}
            for target, consumers in index.items()
        }
        for path in changed:
            if self.module(path) is None or self.resource(path) is None:
                continue
            for target in self.semantic(path).semantic_imports.values():
                if target:
                    updated.setdefault(target, set()).add(path)
        self._import_dependents_index = {
            target: tuple(sorted(consumers))
            for target, consumers in updated.items()
            if consumers
        }

    def _invalidate_candidate_queries(
        self,
        affected: set[Path],
        changed: Sequence[Path],
        *,
        previous_index: m.Infra.RopeWorkspaceIndex | None,
    ) -> None:
        """Discard per-view facts while retaining unchanged structural entries."""
        affected_names = {str(path) for path in affected}
        metadata_roots = {
            path.parent for path in changed if path.name == c.PYPROJECT_FILENAME
        }
        affected_names.update(
            str(entry.file_path)
            for index in (previous_index, self._workspace_index)
            if index is not None
            for entry in index.modules_by_path.values()
            if entry.project_root in metadata_roots
        )
        roots = self._invalidation_roots(affected_names, previous_index)
        roots.update(metadata_roots)
        for root in roots:
            self._project_layout_cache.pop(str(root), None)
        if affected and not roots:
            self._project_layout_cache.clear()
        self._invalidate_module_caches(affected_names)
        self._invalidate_package_contexts(changed, metadata_roots)
        for path in affected_names:
            self._resource_cache.pop(path, None)
        if changed:
            # This legacy query is global. Its owner must rebuild its derived
            # occurrence facts; it is not the native structural/module index.
            self._name_index = None
        if self._codegen_projects_stale(changed, previous_index):
            self._codegen_projects = None

    def _invalidation_roots(
        self,
        affected_names: set[str],
        previous_index: m.Infra.RopeWorkspaceIndex | None,
    ) -> set[Path]:
        """Collect project roots owning any affected module.

        Returns:
            The project roots whose layout facts are stale.

        """
        roots: set[Path] = set()
        for index in (previous_index, self._workspace_index):
            if index is None:
                continue
            roots.update(
                entry.project_root
                for path in affected_names
                if (entry := index.modules_by_path.get(path)) is not None
                and entry.project_root is not None
            )
        return roots

    def _invalidate_module_caches(self, affected_names: set[str]) -> None:
        """Drop module-object, policy and convention facts of affected modules."""
        for key in tuple(self._module_object_cache):
            # Reference counts/sites are workspace-wide facts: a changed use
            # affects a provider even when its own declaration is unchanged.
            if key[0] in affected_names or key[2]:
                del self._module_object_cache[key]
        for key in tuple(self._module_policy_cache):
            if key[0] in affected_names:
                del self._module_policy_cache[key]
        for key in tuple(self._module_convention_cache):
            if any(key.startswith(f"{path}::") for path in affected_names):
                del self._module_convention_cache[key]

    def _invalidate_package_contexts(
        self,
        changed: Sequence[Path],
        metadata_roots: set[Path],
    ) -> None:
        """Drop package-context facts under changed directories or metadata roots."""
        directories = {path.parent for path in changed}
        for key in tuple(self._package_context_cache):
            package = Path(key)
            if any(
                directory.is_relative_to(package) for directory in directories
            ) or any(package.is_relative_to(root) for root in metadata_roots):
                del self._package_context_cache[key]

    def _codegen_projects_stale(
        self,
        changed: Sequence[Path],
        previous_index: m.Infra.RopeWorkspaceIndex | None,
    ) -> bool:
        """Decide whether derived codegen projects must be rebuilt.

        Returns:
            Whether the codegen project cache is stale.

        """
        return bool(changed) and (
            previous_index is None
            or self._workspace_index is not previous_index
            or any(
                path.suffix not in c.Infra.PYTHON_SOURCE_SUFFIXES for path in changed
            )
        )

    def refresh(
        self,
        *,
        preserve_indexes: bool = False,
        validate_project: bool = True,
    ) -> m.Infra.RopeWorkspaceSession:
        """Invalidate Rope caches without reopening the Rope project.

        ``preserve_indexes=True`` is reserved for flows that temporarily wrote
        files and already restored the original on-disk content before the
        refresh runs. ``validate_project=False`` is used after those reverted
        previews or an authenticated native source-view transition whose own
        resource observers already ran; neither needs another physical rescan.
        Normal refresh also invalidates module inventory and project discovery;
        reverted previews retain those unchanged indexes. Layouts always
        invalidate.

        Returns:
            The resulting ``m.Infra.RopeWorkspaceSession``.

        """
        if validate_project and self._rope_project is not None:
            self._rope_project.validate()
        self._package_context_cache.clear()
        self._module_policy_cache.clear()
        self._module_convention_cache.clear()
        self._module_object_cache.clear()
        self._resource_cache.clear()
        self._project_layout_cache.clear()
        if not preserve_indexes:
            self._workspace_index = None
            self._codegen_projects = None
            self._name_index = None
            self._import_dependents_index = None
        return self.session_snapshot()

    def reload(self) -> m.Infra.RopeWorkspaceSession:
        """Reopen the shared Rope project and drop all transient caches.

        Returns:
            The resulting ``m.Infra.RopeWorkspaceSession``.

        """
        self.close()
        _ = self.rope_project
        return self.session_snapshot()

    def projects(self) -> Sequence[p.Infra.ProjectInfo]:
        """Return the canonical codegen project selection for this workspace.

        Returns:
            The canonical codegen project selection for this workspace.

        """
        if self._codegen_projects is None:
            projects_result = u.Infra.projects(
                self.repository_root, source_project=self.rope_project
            )
            self._codegen_projects = tuple(projects_result.unwrap())
        return self._codegen_projects

    def layout(self, project_root: Path) -> m.Infra.RopeProjectLayout | None:
        """Return one centralized project layout contract for codegen pipelines.

        Returns:
            One centralized project layout contract for codegen pipelines.

        """
        resolved_root = self._source_path(project_root)
        cache_key = str(resolved_root)
        if cache_key not in self._project_layout_cache:
            self._project_layout_cache[cache_key] = u.Infra.layout(
                resolved_root, rope_project=self.rope_project
            )
        return self._project_layout_cache[cache_key]

    def package_context(self, package_dir: Path) -> m.Infra.LazyInitPackageContext:
        """Return one centralized lazy-init package context for a package dir.

        Returns:
            One centralized lazy-init package context for a package dir.

        """
        resolved_dir = self._source_path(package_dir)
        cache_key = str(resolved_dir)
        if cache_key in self._package_context_cache:
            return self._package_context_cache[cache_key]
        package_entry = self.package(resolved_dir)
        init_path = resolved_dir / c.Infra.INIT_PY
        current_pkg = package_entry.package_name if package_entry is not None else ""
        init_resource = self.resource(init_path)
        generated_init = init_resource is not None and init_resource.read().startswith(
            c.Infra.AUTOGEN_HEADER,
        )
        context = m.Infra.LazyInitPackageContext(
            pkg_dir=resolved_dir,
            init_path=init_path,
            current_pkg=current_pkg,
            surface=current_pkg.split(".", maxsplit=1)[0] if current_pkg else "",
            generated_init=generated_init,
            importable=bool(current_pkg)
            and all(
                part.isidentifier() and not iskeyword(part)
                for part in current_pkg.split(".")
            ),
        )
        self._package_context_cache[cache_key] = context
        return context

    def policy(
        self,
        file_path: Path,
        *,
        rel_path: Path | None = None,
        current_pkg: str = "",
    ) -> m.Infra.NamespaceModulePolicy:
        """Return the centralized naming policy for one module path.

        Returns:
            The centralized naming policy for one module path.

        """
        resolved_file = self._source_path(file_path)
        resolved_rel_path = (
            rel_path if rel_path is not None else Path(resolved_file.name)
        )
        cache_key = (str(resolved_file), str(resolved_rel_path), current_pkg)
        if cache_key in self._module_policy_cache:
            return self._module_policy_cache[cache_key]
        module_entry = self.module(resolved_file)
        project_root = (
            module_entry.project_root
            if module_entry is not None and module_entry.project_root is not None
            else u.Infra.project_root(resolved_file)
        )
        policy: m.Infra.NamespaceModulePolicy = u.Infra.policy(
            resolved_file,
            rope_project=self.rope_project,
            rel_path=resolved_rel_path,
            current_pkg=current_pkg,
            project_layout=self.layout(project_root)
            if project_root is not None
            else None,
        )
        self._module_policy_cache[cache_key] = policy
        return policy

    def convention(
        self,
        file_path: Path,
        *,
        rel_path: Path | None = None,
    ) -> m.Infra.RopeModuleConvention:
        """Return one unified project/package/module convention contract.

        Returns:
            One unified project/package/module convention contract.

        """
        resolved_file = self._source_path(file_path)
        cache_key = f"{resolved_file}::{rel_path or ''}"
        if cache_key in self._module_convention_cache:
            return self._module_convention_cache[cache_key]
        module_entry = self.module(resolved_file)
        package_dir = (
            self._source_path(module_entry.package_dir)
            if module_entry is not None
            else resolved_file.parent
        )
        resolved_rel_path = (
            rel_path
            if rel_path is not None
            else resolved_file.relative_to(package_dir)
            if resolved_file.is_relative_to(package_dir)
            else Path(resolved_file.name)
        )
        package_context = self.package_context(package_dir)
        policy = self.policy(
            resolved_file,
            rel_path=resolved_rel_path,
            current_pkg=package_context.current_pkg,
        )
        project_root = (
            module_entry.project_root
            if module_entry is not None and module_entry.project_root is not None
            else u.Infra.project_root(resolved_file)
        )
        project_layout = self.layout(project_root) if project_root is not None else None
        convention = m.Infra.RopeModuleConvention(
            file_path=resolved_file,
            relative_path=resolved_rel_path,
            module_name=module_entry.module_name
            if module_entry is not None
            else resolved_file.stem,
            package_name=package_context.current_pkg,
            package_dir=package_dir,
            package_context=package_context,
            module_policy=policy,
            project_layout=project_layout,
        )
        self._module_convention_cache[cache_key] = convention
        return convention

    def exports(
        self,
        file_path: Path,
        *,
        export_options: m.Infra.ExportOptions | None = None,
    ) -> Sequence[str]:
        """Return public export names for one module path from its parsed source.

        Returns:
            Public export names for one module path.

        """
        return u.Infra.module_export_names_source(
            u.Infra.resolve_pymodule(
                self.rope_project,
                u.Infra.require_file_resource(self.resource(file_path), file_path),
            ),
            export_options=export_options,
        )

    def close(self) -> None:
        """Close the shared Rope project and clear transient caches."""
        self._close_candidate_views(None, None, None)
        if self._rope_project is not None:
            if self._owns_rope_project:
                self._rope_project.close()
            self._rope_project = None
        self._view_project = None
        if self._snapshot_scope is not None:
            self._snapshot_scope.close()
            self._snapshot_scope = None
            self._snapshot = None
        self._workspace_index = None
        self._codegen_projects = None
        self._project_layout_cache.clear()
        self._package_context_cache.clear()
        self._module_policy_cache.clear()
        self._module_convention_cache.clear()
        self._module_object_cache.clear()
        self._resource_cache.clear()
        self._name_index = None
        self._import_dependents_index = None

    def _close_candidate_views(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Restore nested candidate bindings before their source owner closes."""
        scope = self._candidate_scope
        self._candidate_scope = None
        self._candidate_files = ()
        self._candidate_source_folders = None
        if scope is not None:
            scope.__exit__(exc_type, exc, traceback)

    def __enter__(self) -> Self:
        """Open the Rope project on context-manager entry.

        Returns:
            The resulting ``Self``.

        """
        _ = self.rope_project
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        """Close the Rope project on context-manager exit."""
        self._close_candidate_views(_exc_type, _exc, _tb)
        self.close()

    def objects(
        self,
        file_path: Path,
        *,
        include_local_scopes: bool = True,
        include_references: bool = True,
    ) -> Sequence[m.Infra.Object]:
        """Return Rope-only discovered objects for one module path.

        Returns:
            Rope-only discovered objects for one module path.

        """
        resolved_file = self._source_path(file_path)
        cache_key = (str(resolved_file), include_local_scopes, include_references)
        if cache_key in self._module_object_cache:
            return self._module_object_cache[cache_key]
        objects = u.Infra.objects(
            self,
            resolved_file,
            include_local_scopes=include_local_scopes,
            include_references=include_references,
        )
        self._module_object_cache[cache_key] = objects
        return objects


__all__: Sequence[str] = ("FlextInfraRopeWorkspace",)
