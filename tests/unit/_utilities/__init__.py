# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes
    from tests.unit._utilities import (
        test_discovery_consolidated,
        test_formatting,
        test_iteration,
        test_parsing,
        test_rope_hooks,
        test_safety,
        test_scanning,
    )
    from tests.unit._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots,
    )
    from tests.unit._utilities.test_formatting import TestFormattingRunRuffFix
    from tests.unit._utilities.test_iteration import TestIterWorkspacePythonModules
    from tests.unit._utilities.test_parsing import (
        TestParsingModuleAst,
        TestParsingModuleCst,
    )
    from tests.unit._utilities.test_rope_hooks import (
        test_run_rope_post_hooks_applies_mro_migration,
        test_run_rope_post_hooks_dry_run_is_non_mutating,
    )
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint,
        TestSafetyRollback,
    )
    from tests.unit._utilities.test_scanning import TestScanModels

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
    "TestDiscoveryDiscoverProjects": "tests.unit._utilities.test_discovery_consolidated",
    "TestDiscoveryFindAllPyprojectFiles": "tests.unit._utilities.test_discovery_consolidated",
    "TestDiscoveryIterPythonFiles": "tests.unit._utilities.test_discovery_consolidated",
    "TestDiscoveryProjectRoots": "tests.unit._utilities.test_discovery_consolidated",
    "TestFormattingRunRuffFix": "tests.unit._utilities.test_formatting",
    "TestIterWorkspacePythonModules": "tests.unit._utilities.test_iteration",
    "TestParsingModuleAst": "tests.unit._utilities.test_parsing",
    "TestParsingModuleCst": "tests.unit._utilities.test_parsing",
    "TestSafetyCheckpoint": "tests.unit._utilities.test_safety",
    "TestSafetyRollback": "tests.unit._utilities.test_safety",
    "TestScanModels": "tests.unit._utilities.test_scanning",
    "test_discovery_consolidated": "tests.unit._utilities.test_discovery_consolidated",
    "test_formatting": "tests.unit._utilities.test_formatting",
    "test_iteration": "tests.unit._utilities.test_iteration",
    "test_parsing": "tests.unit._utilities.test_parsing",
    "test_rope_hooks": "tests.unit._utilities.test_rope_hooks",
    "test_run_rope_post_hooks_applies_mro_migration": "tests.unit._utilities.test_rope_hooks",
    "test_run_rope_post_hooks_dry_run_is_non_mutating": "tests.unit._utilities.test_rope_hooks",
    "test_safety": "tests.unit._utilities.test_safety",
    "test_scanning": "tests.unit._utilities.test_scanning",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
