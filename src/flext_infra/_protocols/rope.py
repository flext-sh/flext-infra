"""Application-level protocols for Rope-backed infra utilities.

Concrete Rope objects are typed in ``t.Infra.Rope*``. This module keeps only
FLEXT callback contracts that do not have a concrete Rope class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from flext_infra import m, p, t


class FlextInfraProtocolsRope(Protocol):
    """Application contracts layered around the concrete Rope boundary."""

    @runtime_checkable
    class RopeScopeDsl(Protocol):
        """Public scope contract for Rope semantic traversal."""

        def get_scopes(self) -> Sequence[FlextInfraProtocolsRope.RopeScopeDsl]: ...

        def get_names(self) -> Mapping[str, t.Infra.RopePyName]: ...

        def get_start(self) -> int: ...

        def get_end(self) -> int: ...

    class RopeWorkspaceDsl(Protocol):
        """Public DSL contract for one shared Rope workspace session."""

        workspace_root: Path

        @property
        def rope_workspace_root(self) -> Path: ...

        @property
        def rope_project(self) -> t.Infra.RopeProject: ...

        @property
        def workspace_index(self) -> m.Infra.RopeWorkspaceIndex: ...

        def reload(self) -> m.Infra.RopeWorkspaceSession: ...

        def __enter__(self) -> Self: ...

        def __exit__(
            self,
            _exc_type: type[BaseException] | None,
            _exc: BaseException | None,
            _tb: TracebackType | None,
        ) -> None: ...

        def close(self) -> None: ...

        def resource(
            self,
            file_path: Path,
        ) -> t.Infra.RopeResource | None: ...

        def module(
            self,
            file_path: Path,
        ) -> m.Infra.RopeModuleIndexEntry | None: ...

        def package(
            self,
            package_dir: Path,
        ) -> m.Infra.RopePackageIndexEntry | None: ...

        def modules(
            self,
            *,
            project_names: t.StrSequence | None = None,
        ) -> t.SequenceOf[m.Infra.RopeModuleIndexEntry]: ...

        def source(self, file_path: Path) -> str: ...

        def objects(
            self,
            file_path: Path,
            *,
            include_local_scopes: bool = True,
        ) -> t.SequenceOf[m.Infra.Census.Object]: ...

        def projects(self) -> t.SequenceOf[p.Infra.ProjectInfo]: ...

        def layout(
            self,
            project_root: Path,
        ) -> m.Infra.RopeProjectLayout | None: ...

        def context(
            self,
            package_dir: Path,
        ) -> m.Infra.LazyInitPackageContext: ...

        def policy(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
            current_pkg: str = "",
        ) -> m.Infra.NamespaceModulePolicy: ...

        def convention(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
        ) -> m.Infra.RopeModuleConvention: ...

        def semantic(
            self,
            file_path: Path,
        ) -> m.Infra.ModuleSemanticState: ...

        def exports(
            self,
            file_path: Path,
            *,
            include_dunder: bool = False,
            allow_main: bool = False,
            allow_assignments: bool = False,
            allow_functions: bool = False,
            require_explicit_all: bool = False,
        ) -> t.StrSequence: ...

    class RopePostHook(Protocol):
        """Contract for post-processing hooks invoked after Rope refactoring."""

        def __call__(
            self,
            path: Path,
            *,
            dry_run: bool,
        ) -> t.SequenceOf[m.Infra.Result]:
            """Execute the hook and return results."""
            ...

    class RopeAnalysisMethods(Protocol):
        """Class contract shared by the Rope analysis mixins."""

        @staticmethod
        def get_module_classes(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
        ) -> t.StrSequence: ...

        @staticmethod
        def get_class_methods(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
            class_name: str,
            *,
            include_private: bool = False,
        ) -> t.StrMapping: ...

        @staticmethod
        def project_root(file_path: Path) -> Path | None: ...

        @staticmethod
        def init_rope_project(
            workspace_root: Path,
            *,
            project_prefix: str = "",
            src_dir: str = "",
            ignored_resources: t.VariadicTuple[str] = (),
        ) -> t.Infra.RopeProject: ...

        @staticmethod
        def get_resource_from_path(
            rope_project: t.Infra.RopeProject,
            file_path: Path,
        ) -> t.Infra.RopeResource | None: ...


__all__: list[str] = ["FlextInfraProtocolsRope"]
