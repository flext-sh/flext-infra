# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

from .lazy_init_fixture_settings_tests import (
    TestsFlextInfraLazyInitFixtureSettingsCollision as TestsFlextInfraLazyInitFixtureSettingsCollision,
)
from .lazy_init_generation_tests import (
    TestsFlextInfraCodegenGeneration as TestsFlextInfraCodegenGeneration,
)
from .lazy_init_helpers_tests import (
    TestsFlextInfraLazyInitHelpers as TestsFlextInfraLazyInitHelpers,
)
from .lazy_init_process_tests import (
    TestsFlextInfraLazyInitProcessing as TestsFlextInfraLazyInitProcessing,
)
from .lazy_init_registry_wrapper_tests import (
    TestsFlextInfraLazyInitCleanup as TestsFlextInfraLazyInitCleanup,
)
from .lazy_init_service_tests import (
    TestsFlextInfraCodegenLazyInitService as TestsFlextInfraCodegenLazyInitService,
)
from .lazy_init_tests import (
    TestAllDirectoriesScanned as TestAllDirectoriesScanned,
    TestCheckOnlyMode as TestCheckOnlyMode,
    TestEdgeCases as TestEdgeCases,
    TestExcludedDirectories as TestExcludedDirectories,
)
from .lazy_init_transforms_tests import (
    TestsFlextInfraLazyInitTransforms as TestsFlextInfraLazyInitTransforms,
)
from .scaffolder_naming_tests import (
    TestGeneratedClassNamingConvention as TestGeneratedClassNamingConvention,
    TestGeneratedFilesAreValidPython as TestGeneratedFilesAreValidPython,
)
from .test_codegen_pyproject_conform import (
    TestsFlextInfraCodegenPyprojectConform as TestsFlextInfraCodegenPyprojectConform,
)

__all__: tuple[str, ...] = (
    "TestAllDirectoriesScanned",
    "TestCheckOnlyMode",
    "TestEdgeCases",
    "TestExcludedDirectories",
    "TestGeneratedClassNamingConvention",
    "TestGeneratedFilesAreValidPython",
    "TestsFlextInfraCodegenGeneration",
    "TestsFlextInfraCodegenLazyInitService",
    "TestsFlextInfraCodegenPyprojectConform",
    "TestsFlextInfraLazyInitCleanup",
    "TestsFlextInfraLazyInitFixtureSettingsCollision",
    "TestsFlextInfraLazyInitHelpers",
    "TestsFlextInfraLazyInitProcessing",
    "TestsFlextInfraLazyInitTransforms",
)
