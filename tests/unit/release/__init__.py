# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.release import (
        flow_tests as flow_tests,
        main_tests as main_tests,
        orchestrator_git_tests as orchestrator_git_tests,
        orchestrator_helpers_tests as orchestrator_helpers_tests,
        orchestrator_phases_tests as orchestrator_phases_tests,
        orchestrator_publish_tests as orchestrator_publish_tests,
        orchestrator_tests as orchestrator_tests,
        release_init_tests as release_init_tests,
        version_resolution_tests as version_resolution_tests,
    )
    from tests.unit.release.flow_tests import (
        TestReleaseMainFlow as TestReleaseMainFlow,
        main as main,
    )
    from tests.unit.release.main_tests import (
        TestReleaseMainParsing as TestReleaseMainParsing,
    )
    from tests.unit.release.orchestrator_git_tests import (
        TestCollectChanges as TestCollectChanges,
        TestCreateBranches as TestCreateBranches,
        TestCreateTag as TestCreateTag,
        TestPreviousTag as TestPreviousTag,
        TestPushRelease as TestPushRelease,
    )
    from tests.unit.release.orchestrator_helpers_tests import (
        TestBuildTargets as TestBuildTargets,
        TestBumpNextDev as TestBumpNextDev,
        TestDispatchPhase as TestDispatchPhase,
        TestGenerateNotes as TestGenerateNotes,
        TestRunMake as TestRunMake,
        TestUpdateChangelog as TestUpdateChangelog,
        TestVersionFiles as TestVersionFiles,
    )
    from tests.unit.release.orchestrator_phases_tests import (
        TestPhaseBuild as TestPhaseBuild,
        TestPhaseValidate as TestPhaseValidate,
        TestPhaseVersion as TestPhaseVersion,
    )
    from tests.unit.release.orchestrator_publish_tests import (
        TestPhasePublish as TestPhasePublish,
    )
    from tests.unit.release.orchestrator_tests import (
        TestReleaseOrchestratorExecute as TestReleaseOrchestratorExecute,
        workspace_root as workspace_root,
    )
    from tests.unit.release.release_init_tests import TestReleaseInit as TestReleaseInit
    from tests.unit.release.version_resolution_tests import (
        TestReleaseMainTagResolution as TestReleaseMainTagResolution,
        TestReleaseMainVersionResolution as TestReleaseMainVersionResolution,
        TestResolveVersionInteractive as TestResolveVersionInteractive,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestBuildTargets": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestBuildTargets",
    ],
    "TestBumpNextDev": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestBumpNextDev",
    ],
    "TestCollectChanges": [
        "tests.unit.release.orchestrator_git_tests",
        "TestCollectChanges",
    ],
    "TestCreateBranches": [
        "tests.unit.release.orchestrator_git_tests",
        "TestCreateBranches",
    ],
    "TestCreateTag": ["tests.unit.release.orchestrator_git_tests", "TestCreateTag"],
    "TestDispatchPhase": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestDispatchPhase",
    ],
    "TestGenerateNotes": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestGenerateNotes",
    ],
    "TestPhaseBuild": [
        "tests.unit.release.orchestrator_phases_tests",
        "TestPhaseBuild",
    ],
    "TestPhasePublish": [
        "tests.unit.release.orchestrator_publish_tests",
        "TestPhasePublish",
    ],
    "TestPhaseValidate": [
        "tests.unit.release.orchestrator_phases_tests",
        "TestPhaseValidate",
    ],
    "TestPhaseVersion": [
        "tests.unit.release.orchestrator_phases_tests",
        "TestPhaseVersion",
    ],
    "TestPreviousTag": ["tests.unit.release.orchestrator_git_tests", "TestPreviousTag"],
    "TestPushRelease": ["tests.unit.release.orchestrator_git_tests", "TestPushRelease"],
    "TestReleaseInit": ["tests.unit.release.release_init_tests", "TestReleaseInit"],
    "TestReleaseMainFlow": ["tests.unit.release.flow_tests", "TestReleaseMainFlow"],
    "TestReleaseMainParsing": [
        "tests.unit.release.main_tests",
        "TestReleaseMainParsing",
    ],
    "TestReleaseMainTagResolution": [
        "tests.unit.release.version_resolution_tests",
        "TestReleaseMainTagResolution",
    ],
    "TestReleaseMainVersionResolution": [
        "tests.unit.release.version_resolution_tests",
        "TestReleaseMainVersionResolution",
    ],
    "TestReleaseOrchestratorExecute": [
        "tests.unit.release.orchestrator_tests",
        "TestReleaseOrchestratorExecute",
    ],
    "TestResolveVersionInteractive": [
        "tests.unit.release.version_resolution_tests",
        "TestResolveVersionInteractive",
    ],
    "TestRunMake": ["tests.unit.release.orchestrator_helpers_tests", "TestRunMake"],
    "TestUpdateChangelog": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestUpdateChangelog",
    ],
    "TestVersionFiles": [
        "tests.unit.release.orchestrator_helpers_tests",
        "TestVersionFiles",
    ],
    "flow_tests": ["tests.unit.release.flow_tests", ""],
    "main": ["tests.unit.release.flow_tests", "main"],
    "main_tests": ["tests.unit.release.main_tests", ""],
    "orchestrator_git_tests": ["tests.unit.release.orchestrator_git_tests", ""],
    "orchestrator_helpers_tests": ["tests.unit.release.orchestrator_helpers_tests", ""],
    "orchestrator_phases_tests": ["tests.unit.release.orchestrator_phases_tests", ""],
    "orchestrator_publish_tests": ["tests.unit.release.orchestrator_publish_tests", ""],
    "orchestrator_tests": ["tests.unit.release.orchestrator_tests", ""],
    "release_init_tests": ["tests.unit.release.release_init_tests", ""],
    "version_resolution_tests": ["tests.unit.release.version_resolution_tests", ""],
    "workspace_root": ["tests.unit.release.orchestrator_tests", "workspace_root"],
}

_EXPORTS: Sequence[str] = [
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
    "flow_tests",
    "main",
    "main_tests",
    "orchestrator_git_tests",
    "orchestrator_helpers_tests",
    "orchestrator_phases_tests",
    "orchestrator_publish_tests",
    "orchestrator_tests",
    "release_init_tests",
    "version_resolution_tests",
    "workspace_root",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
