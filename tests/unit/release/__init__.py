# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Release package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.release.flow_tests as _tests_unit_release_flow_tests

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
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
_LAZY_IMPORTS = {
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "flow_tests": "tests.unit.release.flow_tests",
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main_tests": "tests.unit.release.main_tests",
    "orchestrator_git_tests": "tests.unit.release.orchestrator_git_tests",
    "orchestrator_helpers_tests": "tests.unit.release.orchestrator_helpers_tests",
    "orchestrator_phases_tests": "tests.unit.release.orchestrator_phases_tests",
    "orchestrator_publish_tests": "tests.unit.release.orchestrator_publish_tests",
    "orchestrator_tests": "tests.unit.release.orchestrator_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "release_init_tests": "tests.unit.release.release_init_tests",
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_release_dag": "tests.unit.release.test_release_dag",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "version_resolution_tests": "tests.unit.release.version_resolution_tests",
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "c",
    "d",
    "e",
    "flow_tests",
    "h",
    "m",
    "main_tests",
    "orchestrator_git_tests",
    "orchestrator_helpers_tests",
    "orchestrator_phases_tests",
    "orchestrator_publish_tests",
    "orchestrator_tests",
    "p",
    "r",
    "release_init_tests",
    "s",
    "t",
    "test_release_dag",
    "u",
    "version_resolution_tests",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
