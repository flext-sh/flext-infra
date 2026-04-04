# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit._utilities.test_discovery_consolidated as _tests_unit__utilities_test_discovery_consolidated

    test_discovery_consolidated = _tests_unit__utilities_test_discovery_consolidated
    import tests.unit._utilities.test_formatting as _tests_unit__utilities_test_formatting
    from tests.unit._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots,
    )

    test_formatting = _tests_unit__utilities_test_formatting
    import tests.unit._utilities.test_iteration as _tests_unit__utilities_test_iteration
    from tests.unit._utilities.test_formatting import TestFormattingRunRuffFix

    test_iteration = _tests_unit__utilities_test_iteration
    import tests.unit._utilities.test_rope_hooks as _tests_unit__utilities_test_rope_hooks

    test_rope_hooks = _tests_unit__utilities_test_rope_hooks
    import tests.unit._utilities.test_safety as _tests_unit__utilities_test_safety
    from tests.unit._utilities.test_rope_hooks import (
        test_run_rope_post_hooks_applies_mro_migration,
        test_run_rope_post_hooks_dry_run_is_non_mutating,
    )

    test_safety = _tests_unit__utilities_test_safety
    import tests.unit._utilities.test_scanning as _tests_unit__utilities_test_scanning
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
    )

    test_scanning = _tests_unit__utilities_test_scanning
    from tests.unit._utilities.test_scanning import TestScanModels
_LAZY_IMPORTS = {
    "TestDiscoveryDiscoverProjects": "tests.unit._utilities.test_discovery_consolidated",
    "TestDiscoveryFindAllPyprojectFiles": "tests.unit._utilities.test_discovery_consolidated",
    "TestDiscoveryIterPythonFiles": "tests.unit._utilities.test_discovery_consolidated",
    "TestDiscoveryProjectRoots": "tests.unit._utilities.test_discovery_consolidated",
    "TestFormattingRunRuffFix": "tests.unit._utilities.test_formatting",
    "TestSafetyCheckpoint": "tests.unit._utilities.test_safety",
    "TestSafetyRollback": "tests.unit._utilities.test_safety",
    "TestScanModels": "tests.unit._utilities.test_scanning",
    "test_discovery_consolidated": "tests.unit._utilities.test_discovery_consolidated",
    "test_formatting": "tests.unit._utilities.test_formatting",
    "test_iteration": "tests.unit._utilities.test_iteration",
    "test_rope_hooks": "tests.unit._utilities.test_rope_hooks",
    "test_run_rope_post_hooks_applies_mro_migration": "tests.unit._utilities.test_rope_hooks",
    "test_run_rope_post_hooks_dry_run_is_non_mutating": "tests.unit._utilities.test_rope_hooks",
    "test_safety": "tests.unit._utilities.test_safety",
    "test_scanning": "tests.unit._utilities.test_scanning",
}

__all__ = [
    "TestDiscoveryDiscoverProjects",
    "TestDiscoveryFindAllPyprojectFiles",
    "TestDiscoveryIterPythonFiles",
    "TestDiscoveryProjectRoots",
    "TestFormattingRunRuffFix",
    "TestSafetyCheckpoint",
    "TestSafetyRollback",
    "TestScanModels",
    "test_discovery_consolidated",
    "test_formatting",
    "test_iteration",
    "test_rope_hooks",
    "test_run_rope_post_hooks_applies_mro_migration",
    "test_run_rope_post_hooks_dry_run_is_non_mutating",
    "test_safety",
    "test_scanning",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
