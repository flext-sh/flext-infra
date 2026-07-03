# AUTO-GENERATED FILE — Regenerate with: make gen
"""Release package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.release.test_release_dag import (
        TestsFlextInfraReleaseDag as TestsFlextInfraReleaseDag,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".flow_tests": ("flow_tests",),
        ".main_tests": ("main_tests",),
        ".orchestrator_git_tests": ("orchestrator_git_tests",),
        ".orchestrator_helpers_tests": ("orchestrator_helpers_tests",),
        ".orchestrator_publish_tests": ("orchestrator_publish_tests",),
        ".orchestrator_tests": ("orchestrator_tests",),
        ".test_release_dag": ("TestsFlextInfraReleaseDag",),
        ".version_resolution_tests": ("version_resolution_tests",),
    },
)


install_lazy_exports(
    __name__,
    globals(),
    _LAZY_IMPORTS,
    publish_all=False,
)
