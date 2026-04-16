"""Public Rope workspace DSL and facade mixin."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from types import TracebackType
from typing import TYPE_CHECKING, Annotated, Self, override

from pydantic import PrivateAttr

from flext_infra import FlextInfraUtilitiesRopeInventory, c, m, r, s, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraRopeWorkspace(s[m.Infra.RopeWorkspaceSession]):
    """Open one shared Rope workspace with cached public DSL methods."""

    project_prefix: Annotated[
        str,
        m.Field(
            description="Project prefix used when bootstrapping Rope",
        ),
    ] = c.Infra.PKG_PREFIX_HYPHEN
    src_dir: Annotated[
        str,
        m.Field(
            description="Primary source directory hint used by Rope bootstrap",
        ),
    ] = c.Infra.DEFAULT_SRC_DIR
    ignored_resources: Annotated[
        tuple[str, ...],
        m.Field(
            description="Ignored Rope resource patterns for this session",
        ),
    ] = c.Infra.ROPE_IGNORED_RESOURCES

    _rope_workspace_root: Path = PrivateAttr()
    _rope_project: t.Infra.RopeProject | None = PrivateAttr(default=None)
    _workspace_index: m.Infra.RopeWorkspaceIndex | None = PrivateAttr(default=None)
    _codegen_projects: tuple[p.Infra.ProjectInfo, ...] | None = PrivateAttr(
        default=None,
    )
    _project_layout_cache: dict[str, m.Infra.RopeProjectLayout | None] = PrivateAttr(
        default_factory=dict,
    )
    _package_context_cache: dict[str, m.Infra.LazyInitPackageContext] = PrivateAttr(
        default_factory=dict,
    )
    _module_policy_cache: dict[tuple[str, str, str], m.Infra.NamespaceModulePolicy] = (
        PrivateAttr(default_factory=dict)
    )
    _module_convention_cache: dict[str, m.Infra.RopeModuleConvention] = PrivateAttr(
        default_factory=dict,
    )
    _module_object_cache: dict[tuple[str, bool], tuple[m.Infra.Census.Object, ...]] = (
        PrivateAttr(default_factory=dict)
    )
    _resource_cache: dict[str, t.Infra.RopeResource | None] = PrivateAttr(
        default_factory=dict,
    )

    @override
    def model_post_init(self, __context: t.ScalarMapping | None, /) -> None:
        """Resolve the canonical Rope root once for the full session."""
        super().model_post_init(__context)
        self._rope_workspace_root = u.Infra.rope_workspace_root(self.workspace_root)

    @classmethod
    def open_workspace(
        cls,
        workspace_root: Path,
        *,
        project_prefix: str = c.Infra.PKG_PREFIX_HYPHEN,
        src_dir: str = c.Infra.DEFAULT_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> Self:
        """Create one ready-to-use Rope workspace session."""
        workspace = cls(
            workspace=workspace_root,
            project_prefix=project_prefix,
            src_dir=src_dir,
            ignored_resources=ignored_resources,
        )
        _ = workspace.rope_project
        return workspace

    @property
    def rope_workspace_root(self) -> Path:
        """Return the canonical root used for the shared Rope project."""
        return self._rope_workspace_root

    @property
    def rope_project(self) -> t.Infra.RopeProject:
        """Return the shared Rope project, opening it lazily once."""
        rope_project = self._rope_project
        if rope_project is None:
            started_at = perf_counter()
            u.Infra.info(
                f"rope: opening workspace at {self._rope_workspace_root}",
            )
            rope_project = u.Infra.init_rope_project(
                self._rope_workspace_root,
                project_prefix=self.project_prefix,
                src_dir=self.src_dir,
                ignored_resources=self.ignored_resources,
            )
            self._rope_project = rope_project
            u.Infra.info(
                f"rope: workspace ready in {perf_counter() - started_at:.2f}s",
            )
        return rope_project

    @property
    def workspace_index(self) -> m.Infra.RopeWorkspaceIndex:
        """Return the cached workspace index for the shared Rope project."""
        workspace_index = self._workspace_index
        if workspace_index is None:
            started_at = perf_counter()
            u.Infra.info(
                f"rope: indexing python workspace at {self._rope_workspace_root}",
            )
            workspace_index = u.Infra.index_rope_workspace(
                self.rope_project,
                self._rope_workspace_root,
            )
            self._workspace_index = workspace_index
            u.Infra.info(
                "rope: indexed "
                f"{len(workspace_index.package_dirs)} package dirs and "
                f"{len(workspace_index.modules_by_path)} modules in "
                f"{perf_counter() - started_at:.2f}s",
            )
        return workspace_index

    @override
    def execute(self) -> p.Result[m.Infra.RopeWorkspaceSession]:
        """Materialize the public Rope session snapshot."""
        snapshot: m.Infra.RopeWorkspaceSession = self.session_snapshot()
        return r[m.Infra.RopeWorkspaceSession].ok(snapshot)

    def session_snapshot(self) -> m.Infra.RopeWorkspaceSession:
        """Return the current public Rope session state."""
        return m.Infra.RopeWorkspaceSession(
            workspace_root=self.workspace_root,
            rope_workspace_root=self._rope_workspace_root,
            project_prefix=self.project_prefix,
            src_dir=self.src_dir,
            ignored_resources=self.ignored_resources,
            workspace_index=self.workspace_index,
        )

    def reload(self) -> m.Infra.RopeWorkspaceSession:
        """Reopen the shared Rope project and drop all transient caches."""
        self.close()
        _ = self.rope_project
        return self.session_snapshot()

    def resource(self, file_path: Path) -> t.Infra.RopeResource | None:
        """Return one cached Rope resource for the requested file path."""
        cache_key = str(file_path.resolve())
        cached = self._resource_cache.get(cache_key)
        if cache_key in self._resource_cache:
            return cached
        resource = u.Infra.get_resource_from_path(self.rope_project, file_path)
        self._resource_cache[cache_key] = resource
        return resource

    def module(
        self,
        file_path: Path,
    ) -> m.Infra.RopeModuleIndexEntry | None:
        """Return one indexed module entry for the requested file path."""
        return self.workspace_index.modules_by_path.get(str(file_path.resolve()))

    def package(
        self,
        package_dir: Path,
    ) -> m.Infra.RopePackageIndexEntry | None:
        """Return one indexed package entry for the requested directory."""
        return self.workspace_index.packages_by_dir.get(str(package_dir.resolve()))

    def modules(
        self,
        *,
        project_names: t.StrSequence | None = None,
    ) -> t.SequenceOf[m.Infra.RopeModuleIndexEntry]:
        """Return sorted module entries, optionally filtered by project names."""
        modules = tuple(
            sorted(
                self.workspace_index.modules_by_path.values(),
                key=lambda entry: entry.file_path.as_posix(),
            )
        )
        if not project_names:
            return modules
        project_filter = frozenset(project_names)
        return tuple(
            entry
            for entry in modules
            if entry.project_root is not None
            and entry.project_root.name in project_filter
        )

    def source(self, file_path: Path) -> str:
        """Return one module source snapshot from the active Rope workspace."""
        return self._resource_for(file_path).read()

    def objects(
        self,
        file_path: Path,
        *,
        include_local_scopes: bool = True,
    ) -> t.SequenceOf[m.Infra.Census.Object]:
        """Return Rope-only discovered objects for one module path."""
        resolved_file = file_path.resolve()
        cache_key = (str(resolved_file), include_local_scopes)
        cached = self._module_object_cache.get(cache_key)
        if cached is not None:
            return cached
        objects = FlextInfraUtilitiesRopeInventory.objects(
            self.rope_project,
            self._resource_for(resolved_file),
            module_entry=self.module(resolved_file),
            convention=self.convention(resolved_file),
            include_local_scopes=include_local_scopes,
        )
        self._module_object_cache[cache_key] = objects
        return objects

    def projects(self) -> t.SequenceOf[p.Infra.ProjectInfo]:
        """Return the canonical codegen project selection for this workspace."""
        if self._codegen_projects is None:
            projects_result = u.Infra.projects(self.workspace_root)
            if projects_result.failure:
                self._codegen_projects = ()
            else:
                discovered_projects: t.SequenceOf[p.Infra.ProjectInfo] = (
                    projects_result.unwrap()
                )
                self._codegen_projects = tuple(discovered_projects)
        return self._codegen_projects

    def layout(
        self,
        project_root: Path,
    ) -> m.Infra.RopeProjectLayout | None:
        """Return one centralized project layout contract for codegen pipelines."""
        resolved_root = project_root.resolve()
        cache_key = str(resolved_root)
        if cache_key in self._project_layout_cache:
            return self._project_layout_cache[cache_key]
        project_info = next(
            (
                project
                for project in self.projects()
                if project.path.resolve() == resolved_root
            ),
            None,
        )
        layout = u.Infra.layout(
            resolved_root,
            project=project_info,
        )
        self._project_layout_cache[cache_key] = layout
        return layout

    @override
    def context(
        self,
        package_dir: Path,
    ) -> m.Infra.LazyInitPackageContext:
        """Return one centralized lazy-init package context for a package dir."""
        resolved_dir = package_dir.resolve()
        cache_key = str(resolved_dir)
        cached = self._package_context_cache.get(cache_key)
        if cached is not None:
            return cached
        package_entry = self.package(resolved_dir)
        init_path = resolved_dir / c.Infra.INIT_PY
        current_pkg = package_entry.package_name if package_entry is not None else ""
        generated_init = init_path.is_file() and init_path.read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        ).startswith(c.Infra.AUTOGEN_HEADER)
        context = m.Infra.LazyInitPackageContext(
            pkg_dir=resolved_dir,
            init_path=init_path,
            current_pkg=current_pkg,
            surface=current_pkg.split(".", maxsplit=1)[0] if current_pkg else "",
            generated_init=generated_init,
            importable=bool(current_pkg),
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
        """Return the centralized naming policy for one module path."""
        resolved_file = file_path.resolve()
        resolved_rel_path = (
            rel_path if rel_path is not None else Path(resolved_file.name)
        )
        cache_key = (str(resolved_file), str(resolved_rel_path), current_pkg)
        cached = self._module_policy_cache.get(cache_key)
        if cached is not None:
            return cached
        policy = u.Infra.policy(
            resolved_file,
            rel_path=resolved_rel_path,
            current_pkg=current_pkg,
        )
        self._module_policy_cache[cache_key] = policy
        return policy

    def convention(
        self,
        file_path: Path,
        *,
        rel_path: Path | None = None,
    ) -> m.Infra.RopeModuleConvention:
        """Return one unified project/package/module convention contract."""
        resolved_file = file_path.resolve()
        cache_key = f"{resolved_file}::{rel_path or ''}"
        cached = self._module_convention_cache.get(cache_key)
        if cached is not None:
            return cached
        module_entry = self.module(resolved_file)
        package_dir = (
            module_entry.package_dir.resolve()
            if module_entry is not None
            else resolved_file.parent.resolve()
        )
        resolved_rel_path = (
            rel_path
            if rel_path is not None
            else resolved_file.relative_to(package_dir)
            if resolved_file.is_relative_to(package_dir)
            else Path(resolved_file.name)
        )
        package_context = self.context(package_dir)
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

    def semantic(
        self,
        file_path: Path,
    ) -> m.Infra.ModuleSemanticState:
        """Return one cached semantic snapshot for a module path."""
        return u.Infra.get_module_semantic_state(
            self.rope_project,
            self._resource_for(file_path),
        )

    def exports(
        self,
        file_path: Path,
        *,
        include_dunder: bool = False,
        allow_main: bool = False,
        allow_assignments: bool = False,
        allow_functions: bool = False,
        require_explicit_all: bool = False,
    ) -> t.StrSequence:
        """Return public export names for one module path."""
        return u.Infra.get_module_export_names(
            self.rope_project,
            self._resource_for(file_path),
            include_dunder=include_dunder,
            allow_main=allow_main,
            allow_assignments=allow_assignments,
            allow_functions=allow_functions,
            require_explicit_all=require_explicit_all,
        )

    def close(self) -> None:
        """Close the shared Rope project and clear transient caches."""
        if self._rope_project is not None:
            self._rope_project.close()
            self._rope_project = None
        self._workspace_index = None
        self._codegen_projects = None
        self._project_layout_cache.clear()
        self._package_context_cache.clear()
        self._module_policy_cache.clear()
        self._module_convention_cache.clear()
        self._module_object_cache.clear()
        self._resource_cache.clear()

    def __enter__(self) -> Self:
        """Open the Rope project on context-manager entry."""
        _ = self.rope_project
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        """Close the Rope project on context-manager exit."""
        self.close()

    def _resource_for(self, file_path: Path) -> t.Infra.RopeResource:
        """Require a resource inside the active Rope workspace."""
        resource = self.resource(file_path)
        if resource is not None:
            return resource
        msg = f"path is outside the active rope workspace: {file_path}"
        raise ValueError(msg)


class FlextInfraServiceRopeMixin:
    """Expose the public Rope DSL through the infra API facade."""

    def rope_workspace(
        self,
        workspace_root: Path,
        *,
        project_prefix: str = c.Infra.PKG_PREFIX_HYPHEN,
        src_dir: str = c.Infra.DEFAULT_SRC_DIR,
        ignored_resources: tuple[str, ...] = c.Infra.ROPE_IGNORED_RESOURCES,
    ) -> p.Infra.RopeWorkspaceDsl:
        """Open one public Rope workspace session through the facade."""
        return FlextInfraRopeWorkspace.open_workspace(
            workspace_root,
            project_prefix=project_prefix,
            src_dir=src_dir,
            ignored_resources=ignored_resources,
        )


__all__: tuple[str, ...] = (
    "FlextInfraRopeWorkspace",
    "FlextInfraServiceRopeMixin",
)
