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
        flow_tests,
        main_tests,
        orchestrator_git_tests,
        orchestrator_helpers_tests,
        orchestrator_phases_tests,
        orchestrator_publish_tests,
        orchestrator_tests,
        release_init_tests,
        version_resolution_tests,
    )
    from tests.unit.release.flow_tests import *
    from tests.unit.release.main_tests import *
    from tests.unit.release.orchestrator_git_tests import *
    from tests.unit.release.orchestrator_helpers_tests import *
    from tests.unit.release.orchestrator_phases_tests import *
    from tests.unit.release.orchestrator_publish_tests import *
    from tests.unit.release.orchestrator_tests import *
    from tests.unit.release.release_init_tests import *
    from tests.unit.release.version_resolution_tests import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
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
    "flow_tests": "tests.unit.release.flow_tests",
    "main": "tests.unit.release.flow_tests",
    "main_tests": "tests.unit.release.main_tests",
    "orchestrator_git_tests": "tests.unit.release.orchestrator_git_tests",
    "orchestrator_helpers_tests": "tests.unit.release.orchestrator_helpers_tests",
    "orchestrator_phases_tests": "tests.unit.release.orchestrator_phases_tests",
    "orchestrator_publish_tests": "tests.unit.release.orchestrator_publish_tests",
    "orchestrator_tests": "tests.unit.release.orchestrator_tests",
    "release_init_tests": "tests.unit.release.release_init_tests",
    "version_resolution_tests": "tests.unit.release.version_resolution_tests",
    "workspace_root": "tests.unit.release.orchestrator_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, sorted(_LAZY_IMPORTS))
