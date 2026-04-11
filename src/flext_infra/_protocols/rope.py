"""Application-level protocols for Rope-backed infra utilities.

Concrete Rope objects are typed in ``t.Infra.Rope*``. This module keeps only
FLEXT callback contracts that do not have a concrete Rope class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraProtocolsRope(Protocol):
    """Application contracts layered around the concrete Rope boundary."""

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
        def discover_project_root_from_file(file_path: Path) -> Path | None: ...

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


__all__ = ["FlextInfraProtocolsRope"]
