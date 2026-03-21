# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Release package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .flow import TestReleaseMainFlow
    from .main import TestReleaseMainParsing
    from .orchestrator import TestReleaseOrchestratorExecute
    from .orchestrator_git import (
        TestCollectChanges,
        TestCreateBranches,
        TestCreateTag,
        TestPreviousTag,
        TestPushRelease,
    )
    from .orchestrator_helpers import (
        TestBuildTargets,
        TestBumpNextDev,
        TestDispatchPhase,
        TestGenerateNotes,
        TestRunMake,
        TestUpdateChangelog,
        TestVersionFiles,
    )
    from .orchestrator_phases import TestPhaseBuild, TestPhaseValidate, TestPhaseVersion
    from .orchestrator_publish import TestPhasePublish, workspace_root
    from .release_init import TestReleaseInit
    from .version_resolution import (
        TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution,
        TestResolveVersionInteractive,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestBuildTargets": (
        "tests.infra.unit.release.orchestrator_helpers",
        "TestBuildTargets",
    ),
    "TestBumpNextDev": (
        "tests.infra.unit.release.orchestrator_helpers",
        "TestBumpNextDev",
    ),
    "TestCollectChanges": (
        "tests.infra.unit.release.orchestrator_git",
        "TestCollectChanges",
    ),
    "TestCreateBranches": (
        "tests.infra.unit.release.orchestrator_git",
        "TestCreateBranches",
    ),
    "TestCreateTag": ("tests.infra.unit.release.orchestrator_git", "TestCreateTag"),
    "TestDispatchPhase": (
        "tests.infra.unit.release.orchestrator_helpers",
        "TestDispatchPhase",
    ),
    "TestGenerateNotes": (
        "tests.infra.unit.release.orchestrator_helpers",
        "TestGenerateNotes",
    ),
    "TestPhaseBuild": (
        "tests.infra.unit.release.orchestrator_phases",
        "TestPhaseBuild",
    ),
    "TestPhasePublish": (
        "tests.infra.unit.release.orchestrator_publish",
        "TestPhasePublish",
    ),
    "TestPhaseValidate": (
        "tests.infra.unit.release.orchestrator_phases",
        "TestPhaseValidate",
    ),
    "TestPhaseVersion": (
        "tests.infra.unit.release.orchestrator_phases",
        "TestPhaseVersion",
    ),
    "TestPreviousTag": ("tests.infra.unit.release.orchestrator_git", "TestPreviousTag"),
    "TestPushRelease": ("tests.infra.unit.release.orchestrator_git", "TestPushRelease"),
    "TestReleaseInit": ("tests.infra.unit.release.release_init", "TestReleaseInit"),
    "TestReleaseMainFlow": ("tests.infra.unit.release.flow", "TestReleaseMainFlow"),
    "TestReleaseMainParsing": (
        "tests.infra.unit.release.main",
        "TestReleaseMainParsing",
    ),
    "TestReleaseMainTagResolution": (
        "tests.infra.unit.release.version_resolution",
        "TestReleaseMainTagResolution",
    ),
    "TestReleaseMainVersionResolution": (
        "tests.infra.unit.release.version_resolution",
        "TestReleaseMainVersionResolution",
    ),
    "TestReleaseOrchestratorExecute": (
        "tests.infra.unit.release.orchestrator",
        "TestReleaseOrchestratorExecute",
    ),
    "TestResolveVersionInteractive": (
        "tests.infra.unit.release.version_resolution",
        "TestResolveVersionInteractive",
    ),
    "TestRunMake": ("tests.infra.unit.release.orchestrator_helpers", "TestRunMake"),
    "TestUpdateChangelog": (
        "tests.infra.unit.release.orchestrator_helpers",
        "TestUpdateChangelog",
    ),
    "TestVersionFiles": (
        "tests.infra.unit.release.orchestrator_helpers",
        "TestVersionFiles",
    ),
    "workspace_root": (
        "tests.infra.unit.release.orchestrator_publish",
        "workspace_root",
    ),
}

__all__ = [
    "TestBuildTargets",
    "TestBumpNextDev",
    "TestCollectChanges",
    "TestCreateBranches",
    "TestCreateTag",
    "TestDispatchPhase",
    "TestGenerateNotes",
    "TestPhaseBuild",
    "TestPhasePublish",
    "TestPhaseValidate",
    "TestPhaseVersion",
    "TestPreviousTag",
    "TestPushRelease",
    "TestReleaseInit",
    "TestReleaseMainFlow",
    "TestReleaseMainParsing",
    "TestReleaseMainTagResolution",
    "TestReleaseMainVersionResolution",
    "TestReleaseOrchestratorExecute",
    "TestResolveVersionInteractive",
    "TestRunMake",
    "TestUpdateChangelog",
    "TestVersionFiles",
    "workspace_root",
]


_LAZY_CACHE: dict[str, object] = {}


def __getattr__(name: str) -> FlextTypes.ModuleExport:
    """Lazy-load module attributes on first access (PEP 562).

    A local cache ``_LAZY_CACHE`` persists resolved objects across repeated
    accesses during process lifetime.

    Args:
        name: Attribute name requested by dir()/import.

    Returns:
        Lazy-loaded module export type.

    Raises:
        AttributeError: If attribute not registered.

    """
    if name in _LAZY_CACHE:
        return _LAZY_CACHE[name]

    value = lazy_getattr(name, _LAZY_IMPORTS, globals(), __name__)
    _LAZY_CACHE[name] = value
    return value


def __dir__() -> list[str]:
    """Return list of available attributes for dir() and autocomplete.

    Returns:
        List of public names from module exports.

    """
    return sorted(__all__)


cleanup_submodule_namespace(__name__, _LAZY_IMPORTS)
