# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.release._stubs as _tests_unit_release__stubs

    _stubs = _tests_unit_release__stubs
    import tests.unit.release.flow_tests as _tests_unit_release_flow_tests
    from tests.unit.release._stubs import (
        FakeReporting,
        FakeSelection,
        FakeSubprocess,
        FakeUtilsNamespace,
        FakeVersioning,
    )

    flow_tests = _tests_unit_release_flow_tests
    import tests.unit.release.main_tests as _tests_unit_release_main_tests
    from tests.unit.release.flow_tests import TestReleaseMainFlow, main

    main_tests = _tests_unit_release_main_tests
    import tests.unit.release.orchestrator_git_tests as _tests_unit_release_orchestrator_git_tests
    from tests.unit.release.main_tests import TestReleaseMainParsing

    orchestrator_git_tests = _tests_unit_release_orchestrator_git_tests
    import tests.unit.release.orchestrator_helpers_tests as _tests_unit_release_orchestrator_helpers_tests
    from tests.unit.release.orchestrator_git_tests import (
        TestCollectChanges,
        TestCreateBranches,
        TestCreateTag,
        TestPreviousTag,
        TestPushRelease,
    )

    orchestrator_helpers_tests = _tests_unit_release_orchestrator_helpers_tests
    import tests.unit.release.orchestrator_phases_tests as _tests_unit_release_orchestrator_phases_tests
    from tests.unit.release.orchestrator_helpers_tests import (
        TestBuildTargets,
        TestBumpNextDev,
        TestDispatchPhase,
        TestGenerateNotes,
        TestRunMake,
        TestUpdateChangelog,
        TestVersionFiles,
    )

    orchestrator_phases_tests = _tests_unit_release_orchestrator_phases_tests
    import tests.unit.release.orchestrator_publish_tests as _tests_unit_release_orchestrator_publish_tests
    from tests.unit.release.orchestrator_phases_tests import (
        TestPhaseBuild,
        TestPhaseValidate,
        TestPhaseVersion,
    )

    orchestrator_publish_tests = _tests_unit_release_orchestrator_publish_tests
    import tests.unit.release.orchestrator_tests as _tests_unit_release_orchestrator_tests
    from tests.unit.release.orchestrator_publish_tests import TestPhasePublish

    orchestrator_tests = _tests_unit_release_orchestrator_tests
    import tests.unit.release.release_init_tests as _tests_unit_release_release_init_tests
    from tests.unit.release.orchestrator_tests import (
        TestReleaseOrchestratorExecute,
        workspace_root,
    )

    release_init_tests = _tests_unit_release_release_init_tests
    import tests.unit.release.version_resolution_tests as _tests_unit_release_version_resolution_tests
    from tests.unit.release.release_init_tests import TestReleaseInit

    version_resolution_tests = _tests_unit_release_version_resolution_tests
    from tests.unit.release.version_resolution_tests import (
        TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution,
        TestResolveVersionInteractive,
    )

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "FakeReporting": "tests.unit.release._stubs",
    "FakeSelection": "tests.unit.release._stubs",
    "FakeSubprocess": "tests.unit.release._stubs",
    "FakeUtilsNamespace": "tests.unit.release._stubs",
    "FakeVersioning": "tests.unit.release._stubs",
    "TestBuildTargets": "tests.unit.release.orchestrator_helpers_tests",
    "TestBumpNextDev": "tests.unit.release.orchestrator_helpers_tests",
    "TestCollectChanges": "tests.unit.release.orchestrator_git_tests",
    "TestCreateBranches": "tests.unit.release.orchestrator_git_tests",
    "TestCreateTag": "tests.unit.release.orchestrator_git_tests",
    "TestDispatchPhase": "tests.unit.release.orchestrator_helpers_tests",
    "TestGenerateNotes": "tests.unit.release.orchestrator_helpers_tests",
    "TestPhaseBuild": "tests.unit.release.orchestrator_phases_tests",
    "TestPhasePublish": "tests.unit.release.orchestrator_publish_tests",
    "TestPhaseValidate": "tests.unit.release.orchestrator_phases_tests",
    "TestPhaseVersion": "tests.unit.release.orchestrator_phases_tests",
    "TestPreviousTag": "tests.unit.release.orchestrator_git_tests",
    "TestPushRelease": "tests.unit.release.orchestrator_git_tests",
    "TestReleaseInit": "tests.unit.release.release_init_tests",
    "TestReleaseMainFlow": "tests.unit.release.flow_tests",
    "TestReleaseMainParsing": "tests.unit.release.main_tests",
    "TestReleaseMainTagResolution": "tests.unit.release.version_resolution_tests",
    "TestReleaseMainVersionResolution": "tests.unit.release.version_resolution_tests",
    "TestReleaseOrchestratorExecute": "tests.unit.release.orchestrator_tests",
    "TestResolveVersionInteractive": "tests.unit.release.version_resolution_tests",
    "TestRunMake": "tests.unit.release.orchestrator_helpers_tests",
    "TestUpdateChangelog": "tests.unit.release.orchestrator_helpers_tests",
    "TestVersionFiles": "tests.unit.release.orchestrator_helpers_tests",
    "_stubs": "tests.unit.release._stubs",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "flow_tests": "tests.unit.release.flow_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "main": "tests.unit.release.flow_tests",
    "main_tests": "tests.unit.release.main_tests",
    "orchestrator_git_tests": "tests.unit.release.orchestrator_git_tests",
    "orchestrator_helpers_tests": "tests.unit.release.orchestrator_helpers_tests",
    "orchestrator_phases_tests": "tests.unit.release.orchestrator_phases_tests",
    "orchestrator_publish_tests": "tests.unit.release.orchestrator_publish_tests",
    "orchestrator_tests": "tests.unit.release.orchestrator_tests",
    "r": ("flext_core.result", "FlextResult"),
    "release_init_tests": "tests.unit.release.release_init_tests",
    "s": ("flext_core.service", "FlextService"),
    "version_resolution_tests": "tests.unit.release.version_resolution_tests",
    "workspace_root": "tests.unit.release.orchestrator_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
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
    "_stubs",
    "d",
    "e",
    "flow_tests",
    "h",
    "main",
    "main_tests",
    "orchestrator_git_tests",
    "orchestrator_helpers_tests",
    "orchestrator_phases_tests",
    "orchestrator_publish_tests",
    "orchestrator_tests",
    "r",
    "release_init_tests",
    "s",
    "version_resolution_tests",
    "workspace_root",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
