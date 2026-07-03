# AUTO-GENERATED FILE — Regenerate with: make gen
"""Workspace package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.tests.unit.workspace.test_main import (
        TestsFlextInfraWorkspaceMain as TestsFlextInfraWorkspaceMain,
    )
    from flext_infra.tests.unit.workspace.test_makefile_dry_run import (
        TestsFlextInfraWorkspaceMakefileDryRun as TestsFlextInfraWorkspaceMakefileDryRun,
    )
    from flext_infra.tests.unit.workspace.test_makefile_generator import (
        TestsFlextInfraWorkspaceMakefileGenerator as TestsFlextInfraWorkspaceMakefileGenerator,
    )
    from flext_infra.tests.unit.workspace.test_sync import (
        TestsFlextInfraWorkspaceSync as TestsFlextInfraWorkspaceSync,
    )
    from flext_infra.tests.unit.workspace.test_sync_environment import (
        TestsFlextInfraWorkspaceSyncEnvironment as TestsFlextInfraWorkspaceSyncEnvironment,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".make_constants_tests": ("make_constants_tests",),
        ".resolve_what_tests": ("resolve_what_tests",),
        ".test_main": ("TestsFlextInfraWorkspaceMain",),
        ".test_makefile_dry_run": ("TestsFlextInfraWorkspaceMakefileDryRun",),
        ".test_makefile_generator": ("TestsFlextInfraWorkspaceMakefileGenerator",),
        ".test_sync": ("TestsFlextInfraWorkspaceSync",),
        ".test_sync_environment": ("TestsFlextInfraWorkspaceSyncEnvironment",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
