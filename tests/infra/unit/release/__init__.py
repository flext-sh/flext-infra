# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make codegen
#
"""Release package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import cleanup_submodule_namespace, lazy_getattr

if TYPE_CHECKING:
    from flext_core.typings import FlextTypes

    from .flow_tests import TestReleaseMainFlow
    from .main_tests import TestReleaseMainParsing
    from .orchestrator_git_tests import (
        TestCollectChanges,
        TestCreateBranches,
        TestCreateTag,
        TestPreviousTag,
        TestPushRelease,
    )
    from .orchestrator_helpers_tests import (
        TestBuildTargets,
        TestBumpNextDev,
        TestDispatchPhase,
        TestGenerateNotes,
        TestRunMake,
        TestUpdateChangelog,
        TestVersionFiles,
    )
    from .orchestrator_phases_tests import (
        TestPhaseBuild,
        TestPhaseValidate,
        TestPhaseVersion,
    )
    from .orchestrator_publish_tests import TestPhasePublish
    from .orchestrator_tests import TestReleaseOrchestratorExecute, workspace_root
    from .release_init_tests import TestReleaseInit
    from .version_resolution_tests import (
        TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution,
        TestResolveVersionInteractive,
    )

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TestBuildTargets": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestBuildTargets",
    ),
    "TestBumpNextDev": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestBumpNextDev",
    ),
    "TestCollectChanges": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestCollectChanges",
    ),
    "TestCreateBranches": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestCreateBranches",
    ),
    "TestCreateTag": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestCreateTag",
    ),
    "TestDispatchPhase": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestDispatchPhase",
    ),
    "TestGenerateNotes": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestGenerateNotes",
    ),
    "TestPhaseBuild": (
        "tests.infra.unit.release.orchestrator_phases_tests",
        "TestPhaseBuild",
    ),
    "TestPhasePublish": (
        "tests.infra.unit.release.orchestrator_publish_tests",
        "TestPhasePublish",
    ),
    "TestPhaseValidate": (
        "tests.infra.unit.release.orchestrator_phases_tests",
        "TestPhaseValidate",
    ),
    "TestPhaseVersion": (
        "tests.infra.unit.release.orchestrator_phases_tests",
        "TestPhaseVersion",
    ),
    "TestPreviousTag": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestPreviousTag",
    ),
    "TestPushRelease": (
        "tests.infra.unit.release.orchestrator_git_tests",
        "TestPushRelease",
    ),
    "TestReleaseInit": (
        "tests.infra.unit.release.release_init_tests",
        "TestReleaseInit",
    ),
    "TestReleaseMainFlow": (
        "tests.infra.unit.release.flow_tests",
        "TestReleaseMainFlow",
    ),
    "TestReleaseMainParsing": (
        "tests.infra.unit.release.main_tests",
        "TestReleaseMainParsing",
    ),
    "TestReleaseMainTagResolution": (
        "tests.infra.unit.release.version_resolution_tests",
        "TestReleaseMainTagResolution",
    ),
    "TestReleaseMainVersionResolution": (
        "tests.infra.unit.release.version_resolution_tests",
        "TestReleaseMainVersionResolution",
    ),
    "TestReleaseOrchestratorExecute": (
        "tests.infra.unit.release.orchestrator_tests",
        "TestReleaseOrchestratorExecute",
    ),
    "TestResolveVersionInteractive": (
        "tests.infra.unit.release.version_resolution_tests",
        "TestResolveVersionInteractive",
    ),
    "TestRunMake": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestRunMake",
    ),
    "TestUpdateChangelog": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestUpdateChangelog",
    ),
    "TestVersionFiles": (
        "tests.infra.unit.release.orchestrator_helpers_tests",
        "TestVersionFiles",
    ),
    "workspace_root": ("tests.infra.unit.release.orchestrator_tests", "workspace_root"),
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


_LAZY_CACHE: dict[str, FlextTypes.ModuleExport] = {}


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
