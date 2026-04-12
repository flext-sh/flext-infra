"""Public Rope workspace DSL and facade mixin."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from types import TracebackType
from typing import TYPE_CHECKING, Annotated, Self, override

from pydantic import Field, PrivateAttr

from flext_core import r
from flext_infra import c, m, s, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraRopeWorkspace(s[m.Infra.RopeWorkspaceSession]):
    """Open one shared Rope workspace with cached public DSL methods."""

    project_prefix: Annotated[
        str,
        Field(
            default=c.Infra.PKG_PREFIX_HYPHEN,
            description="Project prefix used when bootstrapping Rope",
        ),
    ]
    src_dir: Annotated[
        str,
        Field(
            default=c.Infra.DEFAULT_SRC_DIR,
            description="Primary source directory hint used by Rope bootstrap",
        ),
    ]
    ignored_resources: Annotated[
        tuple[str, ...],
        Field(
            default=c.Infra.ROPE_IGNORED_RESOURCES,
            description="Ignored Rope resource patterns for this session",
        ),
    ]

    _rope_workspace_root: Path = PrivateAttr()
    _rope_project: t.Infra.RopeProject | None = PrivateAttr(default=None)
    _workspace_index: m.Infra.RopeWorkspaceIndex | None = PrivateAttr(default=None)
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
    def execute(self) -> r[m.Infra.RopeWorkspaceSession]:
        """Materialize the public Rope session snapshot."""
        return r[m.Infra.RopeWorkspaceSession].ok(self.session_snapshot())

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

    def resource(self, file_path: Path) -> t.Infra.RopeResource | None:
        """Return one cached Rope resource for the requested file path."""
        cache_key = str(file_path.resolve())
        cached = self._resource_cache.get(cache_key)
        if cache_key in self._resource_cache:
            return cached
        resource = u.Infra.get_resource_from_path(self.rope_project, file_path)
        self._resource_cache[cache_key] = resource
        return resource

    def module_entry(
        self,
        file_path: Path,
    ) -> m.Infra.RopeModuleIndexEntry | None:
        """Return one indexed module entry for the requested file path."""
        return self.workspace_index.modules_by_path.get(str(file_path.resolve()))

    def package_entry(
        self,
        package_dir: Path,
    ) -> m.Infra.RopePackageIndexEntry | None:
        """Return one indexed package entry for the requested directory."""
        return self.workspace_index.packages_by_dir.get(str(package_dir.resolve()))

    def module_semantic_state(
        self,
        file_path: Path,
    ) -> m.Infra.ModuleSemanticState:
        """Return one cached semantic snapshot for a module path."""
        return u.Infra.get_module_semantic_state(
            self.rope_project,
            self._resource_for(file_path),
        )

    def module_export_names(
        self,
        file_path: Path,
        *,
        include_dunder: bool = False,
        allow_main: bool = False,
        allow_assignments: bool = False,
    ) -> t.StrSequence:
        """Return public export names for one module path."""
        return u.Infra.get_module_export_names(
            self.rope_project,
            self._resource_for(file_path),
            include_dunder=include_dunder,
            allow_main=allow_main,
            allow_assignments=allow_assignments,
        )

    def close(self) -> None:
        """Close the shared Rope project and clear transient caches."""
        if self._rope_project is not None:
            self._rope_project.close()
            self._rope_project = None
        self._workspace_index = None
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
