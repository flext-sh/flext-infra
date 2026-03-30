# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Utilities package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit._utilities import (
        test_discovery_consolidated as test_discovery_consolidated,
        test_formatting as test_formatting,
        test_iteration as test_iteration,
        test_parsing as test_parsing,
        test_rope_hooks as test_rope_hooks,
        test_safety as test_safety,
        test_scanning as test_scanning,
    )
    from tests.unit._utilities.test_discovery_consolidated import (
        TestDiscoveryDiscoverProjects as TestDiscoveryDiscoverProjects,
        TestDiscoveryFindAllPyprojectFiles as TestDiscoveryFindAllPyprojectFiles,
        TestDiscoveryIterPythonFiles as TestDiscoveryIterPythonFiles,
        TestDiscoveryProjectRoots as TestDiscoveryProjectRoots,
    )
    from tests.unit._utilities.test_formatting import (
        TestFormattingRunRuffFix as TestFormattingRunRuffFix,
    )
    from tests.unit._utilities.test_iteration import (
        TestIterWorkspacePythonModules as TestIterWorkspacePythonModules,
    )
    from tests.unit._utilities.test_parsing import (
        TestParsingModuleAst as TestParsingModuleAst,
        TestParsingModuleCst as TestParsingModuleCst,
    )
    from tests.unit._utilities.test_rope_hooks import (
        test_run_rope_post_hooks_applies_mro_migration as test_run_rope_post_hooks_applies_mro_migration,
        test_run_rope_post_hooks_dry_run_is_non_mutating as test_run_rope_post_hooks_dry_run_is_non_mutating,
    )
    from tests.unit._utilities.test_safety import (
        TestSafetyCheckpoint as TestSafetyCheckpoint,
        TestSafetyRollback as TestSafetyRollback,
    )
    from tests.unit._utilities.test_scanning import TestScanModels as TestScanModels

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "TestDiscoveryDiscoverProjects": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryDiscoverProjects",
    ],
    "TestDiscoveryFindAllPyprojectFiles": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryFindAllPyprojectFiles",
    ],
    "TestDiscoveryIterPythonFiles": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryIterPythonFiles",
    ],
    "TestDiscoveryProjectRoots": [
        "tests.unit._utilities.test_discovery_consolidated",
        "TestDiscoveryProjectRoots",
    ],
    "TestFormattingRunRuffFix": [
        "tests.unit._utilities.test_formatting",
        "TestFormattingRunRuffFix",
    ],
    "TestIterWorkspacePythonModules": [
        "tests.unit._utilities.test_iteration",
        "TestIterWorkspacePythonModules",
    ],
    "TestParsingModuleAst": [
        "tests.unit._utilities.test_parsing",
        "TestParsingModuleAst",
    ],
    "TestParsingModuleCst": [
        "tests.unit._utilities.test_parsing",
        "TestParsingModuleCst",
    ],
    "TestSafetyCheckpoint": [
        "tests.unit._utilities.test_safety",
        "TestSafetyCheckpoint",
    ],
    "TestSafetyRollback": ["tests.unit._utilities.test_safety", "TestSafetyRollback"],
    "TestScanModels": ["tests.unit._utilities.test_scanning", "TestScanModels"],
    "test_discovery_consolidated": [
        "tests.unit._utilities.test_discovery_consolidated",
        "",
    ],
    "test_formatting": ["tests.unit._utilities.test_formatting", ""],
    "test_iteration": ["tests.unit._utilities.test_iteration", ""],
    "test_parsing": ["tests.unit._utilities.test_parsing", ""],
    "test_rope_hooks": ["tests.unit._utilities.test_rope_hooks", ""],
    "test_run_rope_post_hooks_applies_mro_migration": [
        "tests.unit._utilities.test_rope_hooks",
        "test_run_rope_post_hooks_applies_mro_migration",
    ],
    "test_run_rope_post_hooks_dry_run_is_non_mutating": [
        "tests.unit._utilities.test_rope_hooks",
        "test_run_rope_post_hooks_dry_run_is_non_mutating",
    ],
    "test_safety": ["tests.unit._utilities.test_safety", ""],
    "test_scanning": ["tests.unit._utilities.test_scanning", ""],
}

_EXPORTS: Sequence[str] = [
    "TestDiscoveryDiscoverProjects",
    "TestDiscoveryFindAllPyprojectFiles",
    "TestDiscoveryIterPythonFiles",
    "TestDiscoveryProjectRoots",
    "TestFormattingRunRuffFix",
    "TestIterWorkspacePythonModules",
    "TestParsingModuleAst",
    "TestParsingModuleCst",
    "TestSafetyCheckpoint",
    "TestSafetyRollback",
    "TestScanModels",
    "test_discovery_consolidated",
    "test_formatting",
    "test_iteration",
    "test_parsing",
    "test_rope_hooks",
    "test_run_rope_post_hooks_applies_mro_migration",
    "test_run_rope_post_hooks_dry_run_is_non_mutating",
    "test_safety",
    "test_scanning",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
