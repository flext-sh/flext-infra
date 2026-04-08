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
        workspace_root,
    )

    flow_tests = _tests_unit_release_flow_tests
    import tests.unit.release.main_tests as _tests_unit_release_main_tests

    main_tests = _tests_unit_release_main_tests
    import tests.unit.release.orchestrator_git_tests as _tests_unit_release_orchestrator_git_tests

    orchestrator_git_tests = _tests_unit_release_orchestrator_git_tests
    import tests.unit.release.orchestrator_helpers_tests as _tests_unit_release_orchestrator_helpers_tests

    orchestrator_helpers_tests = _tests_unit_release_orchestrator_helpers_tests
    import tests.unit.release.orchestrator_phases_tests as _tests_unit_release_orchestrator_phases_tests

    orchestrator_phases_tests = _tests_unit_release_orchestrator_phases_tests
    import tests.unit.release.orchestrator_publish_tests as _tests_unit_release_orchestrator_publish_tests

    orchestrator_publish_tests = _tests_unit_release_orchestrator_publish_tests
    import tests.unit.release.orchestrator_tests as _tests_unit_release_orchestrator_tests

    orchestrator_tests = _tests_unit_release_orchestrator_tests
    import tests.unit.release.release_init_tests as _tests_unit_release_release_init_tests

    release_init_tests = _tests_unit_release_release_init_tests
    import tests.unit.release.test_release_dag as _tests_unit_release_test_release_dag

    test_release_dag = _tests_unit_release_test_release_dag
    import tests.unit.release.version_resolution_tests as _tests_unit_release_version_resolution_tests

    version_resolution_tests = _tests_unit_release_version_resolution_tests
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = {
    "FakeReporting": ("tests.unit.release._stubs", "FakeReporting"),
    "FakeSelection": ("tests.unit.release._stubs", "FakeSelection"),
    "FakeSubprocess": ("tests.unit.release._stubs", "FakeSubprocess"),
    "FakeUtilsNamespace": ("tests.unit.release._stubs", "FakeUtilsNamespace"),
    "FakeVersioning": ("tests.unit.release._stubs", "FakeVersioning"),
    "_stubs": "tests.unit.release._stubs",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "flow_tests": "tests.unit.release.flow_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "main_tests": "tests.unit.release.main_tests",
    "orchestrator_git_tests": "tests.unit.release.orchestrator_git_tests",
    "orchestrator_helpers_tests": "tests.unit.release.orchestrator_helpers_tests",
    "orchestrator_phases_tests": "tests.unit.release.orchestrator_phases_tests",
    "orchestrator_publish_tests": "tests.unit.release.orchestrator_publish_tests",
    "orchestrator_tests": "tests.unit.release.orchestrator_tests",
    "r": ("flext_core.result", "FlextResult"),
    "release_init_tests": "tests.unit.release.release_init_tests",
    "s": ("flext_core.service", "FlextService"),
    "test_release_dag": "tests.unit.release.test_release_dag",
    "version_resolution_tests": "tests.unit.release.version_resolution_tests",
    "workspace_root": ("tests.unit.release._stubs", "workspace_root"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "FakeReporting",
    "FakeSelection",
    "FakeSubprocess",
    "FakeUtilsNamespace",
    "FakeVersioning",
    "_stubs",
    "d",
    "e",
    "flow_tests",
    "h",
    "main_tests",
    "orchestrator_git_tests",
    "orchestrator_helpers_tests",
    "orchestrator_phases_tests",
    "orchestrator_publish_tests",
    "orchestrator_tests",
    "r",
    "release_init_tests",
    "s",
    "test_release_dag",
    "version_resolution_tests",
    "workspace_root",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
