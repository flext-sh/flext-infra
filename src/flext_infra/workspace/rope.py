"""Public Rope workspace DSL and facade mixin.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from keyword import iskeyword
from pathlib import Path
from types import TracebackType
from typing import Annotated, Self, override

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import FlextInfraRopeQueryMixin


class FlextInfraRopeWorkspace(FlextInfraRopeQueryMixin):
    """Open one shared Rope workspace with cached public DSL methods."""

    rope_repository_root_override: Annotated[
        Path | None,
        m.Field(description="Optional Rope project root; defaults to repository_root"),
    ] = None

    _query_receipts: MutableMapping[str, m.Infra.CodegenPhaseAnalysis] = m.PrivateAttr(
        default_factory=dict[str, m.Infra.CodegenPhaseAnalysis],
    )
    _codegen_projects: t.VariadicTuple[p.Infra.ProjectInfo] | None = m.PrivateAttr(
        default_factory=lambda: None,
    )
    _project_layout_cache: MutableMapping[str, m.Infra.RopeProjectLayout | None] = (
        m.PrivateAttr(default_factory=dict[str, m.Infra.RopeProjectLayout | None])
    )
    _package_context_cache: MutableMapping[str, m.Infra.LazyInitPackageContext] = (
        m.PrivateAttr(default_factory=dict[str, m.Infra.LazyInitPackageContext])
    )
    _module_policy_cache: MutableMapping[
        t.Triple[str, str, str],
        m.Infra.NamespaceModulePolicy,
    ] = m.PrivateAttr(
        default_factory=dict[t.Triple[str, str, str], m.Infra.NamespaceModulePolicy]
    )
    _module_convention_cache: MutableMapping[str, m.Infra.RopeModuleConvention] = (
        m.PrivateAttr(default_factory=dict[str, m.Infra.RopeModuleConvention])
    )
    _module_object_cache: MutableMapping[
        t.Triple[str, bool, bool],
        t.VariadicTuple[m.Infra.Object],
    ] = m.PrivateAttr(
        default_factory=dict[t.Triple[str, bool, bool], t.VariadicTuple[m.Infra.Object]]
    )

    @override
    def model_post_init(self, __context: t.ScalarMapping | None, /) -> None:
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
        index_receipt: m.Infra.CodegenPhaseAnalysis | None = None,
    ) -> Self:
        """Create one ready-to-use Rope workspace session.

        The caller owns this session's lifetime. Explicitly supplied projects
        and indexes are borrowed; independent invocations never share state.

        Returns:
            The resulting ``Self``.

        Raises:
            ValueError: If an explicit source project does not match the
                declared workspace root.

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
            if Path(source_project.root.real_path) != resolved_rope_root.resolve():
                msg = "Rope source project does not match the declared workspace root"
                raise ValueError(msg)
            workspace._rope_project = source_project
            workspace._owns_rope_project = False
        if workspace_index is not None:
            if source_project is None or index_receipt is None:
                msg = "Rope structural index reuse requires its original source receipt"
                raise ValueError(msg)
            workspace._workspace_index = workspace_index
            workspace._index_receipt = index_receipt
            workspace._reused_index = True
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

    def refresh(
        self,
        *,
        preserve_indexes: bool = False,
        validate_project: bool = True,
    ) -> m.Infra.RopeWorkspaceSession:
        """Invalidate Rope caches without reopening the Rope project.

        ``preserve_indexes=True`` is reserved for flows that temporarily wrote
        files and already restored the original on-disk content before the
        refresh runs. ``validate_project=False`` is reserved for those reverted
        preview flows so cleanup does not rescan an already-restored project.
        Normal refresh also invalidates module inventory and project discovery;
        reverted previews retain those unchanged indexes. Layouts always
        invalidate with their query receipts.

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
        self._query_receipts.clear()
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

    def projects(self) -> t.SequenceOf[p.Infra.ProjectInfo]:
        """Return the canonical codegen project selection for this workspace.

        Returns:
            The canonical codegen project selection for this workspace.

        """
        if self._codegen_projects is None:
            projects_result = u.Infra.projects(self.repository_root)
            self._codegen_projects = tuple(projects_result.unwrap())
        return self._codegen_projects

    def layout(self, project_root: Path) -> m.Infra.RopeProjectLayout | None:
        """Return one centralized project layout contract for codegen pipelines.

        Returns:
            One centralized project layout contract for codegen pipelines.

        """
        resolved_root = project_root.resolve()
        cache_key = str(resolved_root)
        if self.rope_project.authenticated_sources:
            with u.Infra.cached_source_query(
                self.rope_project,
                self._project_layout_cache,
                cache_key,
                self._query_receipts,
                f"layout:{cache_key}",
            ) as cached:
                if not cached:
                    self._project_layout_cache[cache_key] = u.Infra.layout(
                        resolved_root, rope_project=self.rope_project
                    )
                return self._project_layout_cache[cache_key]
        if not self._owns_rope_project:
            return u.Infra.layout(resolved_root, rope_project=self.rope_project)
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
        layout = u.Infra.layout(resolved_root, project=project_info)
        self._project_layout_cache[cache_key] = layout
        return layout

    def package_context(self, package_dir: Path) -> m.Infra.LazyInitPackageContext:
        """Return one centralized lazy-init package context for a package dir.

        Returns:
            One centralized lazy-init package context for a package dir.

        """
        resolved_dir = package_dir.resolve()
        cache_key = str(resolved_dir)
        with u.Infra.cached_source_query(
            self.rope_project,
            self._package_context_cache,
            cache_key,
            self._query_receipts,
            f"context:{cache_key}",
        ) as cached:
            if cached:
                return self._package_context_cache[cache_key]
            package_entry = self.package(resolved_dir)
            init_path = resolved_dir / c.Infra.INIT_PY
            current_pkg = (
                package_entry.package_name if package_entry is not None else ""
            )
            init_resource = self.resource(init_path)
            generated_init = (
                init_resource is not None
                and init_resource.read().startswith(
                    c.Infra.AUTOGEN_HEADERS,
                )
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
        resolved_file = file_path.resolve()
        resolved_rel_path = (
            rel_path if rel_path is not None else Path(resolved_file.name)
        )
        cache_key = (str(resolved_file), str(resolved_rel_path), current_pkg)
        with u.Infra.cached_source_query(
            self.rope_project,
            self._module_policy_cache,
            cache_key,
            self._query_receipts,
            f"policy:{cache_key}",
        ) as cached:
            if cached:
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
        resolved_file = file_path.resolve()
        cache_key = f"{resolved_file}::{rel_path or ''}"
        with u.Infra.cached_source_query(
            self.rope_project,
            self._module_convention_cache,
            cache_key,
            self._query_receipts,
            f"convention:{cache_key}",
        ) as cached:
            if cached:
                return self._module_convention_cache[cache_key]
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
            project_layout = (
                self.layout(project_root) if project_root is not None else None
            )
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
    ) -> t.StrSequence:
        """Return public export names for one module path.

        Returns:
            Public export names for one module path.

        """
        resolved_export_options = export_options or m.Infra.ExportOptions()
        return u.Infra.resolve_module_export_names(
            self.rope_project,
            self._resource_for(file_path),
            export_options=resolved_export_options,
        )

    def close(self) -> None:
        """Close the shared Rope project and clear transient caches."""
        if self._rope_project is not None:
            if self._owns_rope_project:
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
        self._query_receipts.clear()
        self._name_index = None
        self._import_dependents_index = None

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
        del _exc_type, _exc, _tb
        self.close()

    def objects(
        self,
        file_path: Path,
        *,
        include_local_scopes: bool = True,
        include_references: bool = True,
    ) -> t.SequenceOf[m.Infra.Object]:
        """Return Rope-only discovered objects for one module path.

        Returns:
            Rope-only discovered objects for one module path.

        """
        resolved_file = file_path.resolve()
        cache_key = (str(resolved_file), include_local_scopes, include_references)
        with u.Infra.cached_source_query(
            self.rope_project,
            self._module_object_cache,
            cache_key,
            self._query_receipts,
            f"objects:{cache_key}",
        ) as cached:
            if cached:
                return self._module_object_cache[cache_key]
            objects = u.Infra.objects(
                self,
                resolved_file,
                include_local_scopes=include_local_scopes,
                include_references=include_references,
            )
            self._module_object_cache[cache_key] = objects
            return objects


__all__: t.StrSequence = ("FlextInfraRopeWorkspace",)
