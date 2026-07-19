"""Shared Rope lifecycle helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING

from flext_infra import config, t

# mro-wkii.17.26 (codex): compose Rope core from its private domain package.
from flext_infra._utilities._rope.core_pymodule import (
    FlextInfraUtilitiesRopeCorePyModuleMixin,
)
from flext_infra._utilities._rope.core_resources import (
    FlextInfraUtilitiesRopeCoreResourcesMixin,
)
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery
from flext_infra._utilities.rope_patch.pep695_patch import (
    FlextInfraUtilitiesRopePep695Patch,
)
from flext_infra._utilities.rope_runtime import FlextInfraUtilitiesRopeRuntime

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


class FlextInfraUtilitiesRopeCore(
    FlextInfraUtilitiesRopeCoreResourcesMixin, FlextInfraUtilitiesRopeCorePyModuleMixin
):
    """Core Rope lifecycle helpers."""

    @staticmethod
    def init_rope_project(workspace_root: Path) -> t.Infra.RopeProject:
        """Create a rope Project over workspace_root with no disk artifacts."""
        FlextInfraUtilitiesRopePep695Patch.apply()
        resolved_root = workspace_root.resolve()
        discovered_roots = FlextInfraUtilitiesProjectDiscovery.discover_project_roots(
            resolved_root
        )
        project_roots = tuple(
            project_root
            for project_root in discovered_roots
            if project_root.resolve().is_relative_to(resolved_root)
        )
        # mro-wkii.17.26 (codex): one Rope project indexes every declared
        # consumer surface across the enclosing workspace.
        source_folders = sorted({
            str(scan_path.relative_to(resolved_root))
            for project_root in project_roots
            for dir_name in config.Infra.rope_index.roots
            if (scan_path := project_root / dir_name).is_dir()
            and scan_path.resolve().is_relative_to(resolved_root)
        })
        with warnings.catch_warnings():
            # Why: rope's own Project.__init__ emits this DeprecationWarning
            # internally; upstream noise we cannot fix, scoped to this call
            # only via catch_warnings (auto-restored, never process-global).
            warnings.filterwarnings(
                "ignore",
                message="Delete once deprecated functions are gone",
                category=DeprecationWarning,
            )
            project: t.Infra.RopeProject = FlextInfraUtilitiesRopeRuntime.new_project(
                str(resolved_root),
                ropefolder="",
                save_objectdb=False,
                ignored_resources=sorted(config.Infra.rope_index.ignored_resources),
                source_folders=source_folders,
            )
            return project

    @staticmethod
    @contextmanager
    def open_project(workspace_root: Path) -> Generator[t.Infra.RopeProject]:
        """Open one Rope project and always close it through the core boundary."""
        rope_project = FlextInfraUtilitiesRopeCore.init_rope_project(workspace_root)
        try:
            yield rope_project
        finally:
            rope_project.close()


__all__: list[str] = ["FlextInfraUtilitiesRopeCore"]
