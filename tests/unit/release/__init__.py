# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

_LAZY_IMPORTS = {
    "flow_tests": "tests.unit.release.flow_tests",
    "main_tests": "tests.unit.release.main_tests",
    "orchestrator_git_tests": "tests.unit.release.orchestrator_git_tests",
    "orchestrator_helpers_tests": "tests.unit.release.orchestrator_helpers_tests",
    "orchestrator_phases_tests": "tests.unit.release.orchestrator_phases_tests",
    "orchestrator_publish_tests": "tests.unit.release.orchestrator_publish_tests",
    "orchestrator_tests": "tests.unit.release.orchestrator_tests",
    "release_init_tests": "tests.unit.release.release_init_tests",
    "test_release_dag": "tests.unit.release.test_release_dag",
    "version_resolution_tests": "tests.unit.release.version_resolution_tests",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
