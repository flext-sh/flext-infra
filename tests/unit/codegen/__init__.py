# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

# mro-i6nq.10: The package consumes its manifest's public-export contract.
from tests.unit.codegen.__unit__ import (
    LAZY_ALIAS_GROUPS as _LAZY_ALIAS_GROUPS,
    LAZY_MODULES as _LAZY_MODULES,
    PUBLIC_EXPORTS as _PUBLIC_EXPORTS,
)

if TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u,
        x as x,
    )

    from tests.unit.codegen import (
        autofix_workspace_tests as autofix_workspace_tests,
        census_models_tests as census_models_tests,
        census_tests as census_tests,
        consolidator_tests as consolidator_tests,
        constants_quality_gate_tests as constants_quality_gate_tests,
        init_tests as init_tests,
        main_tests as main_tests,
        pipeline_tests as pipeline_tests,
        scaffolder_tests as scaffolder_tests,
        test_codegen_conform as test_codegen_conform,
        test_codegen_py_typed as test_codegen_py_typed,
        test_codegen_version_file as test_codegen_version_file,
        test_violation_key as test_violation_key,
    )
    from tests.unit.codegen.lazy_init_fixture_settings_tests import (
        TestsFlextInfraLazyInitFixtureSettingsCollision as TestsFlextInfraLazyInitFixtureSettingsCollision,
    )
    from tests.unit.codegen.lazy_init_generation_tests import (
        TestsFlextInfraCodegenGeneration as TestsFlextInfraCodegenGeneration,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestsFlextInfraLazyInitHelpers as TestsFlextInfraLazyInitHelpers,
    )
    from tests.unit.codegen.lazy_init_process_tests import (
        TestsFlextInfraLazyInitProcessing as TestsFlextInfraLazyInitProcessing,
    )
    from tests.unit.codegen.lazy_init_registry_wrapper_tests import (
        TestsFlextInfraLazyInitCleanup as TestsFlextInfraLazyInitCleanup,
    )
    from tests.unit.codegen.lazy_init_service_tests import (
        TestsFlextInfraCodegenLazyInitService as TestsFlextInfraCodegenLazyInitService,
    )
    from tests.unit.codegen.lazy_init_tests import (
        TestAllDirectoriesScanned as TestAllDirectoriesScanned,
        TestCheckOnlyMode as TestCheckOnlyMode,
        TestEdgeCases as TestEdgeCases,
        TestExcludedDirectories as TestExcludedDirectories,
    )
    from tests.unit.codegen.lazy_init_transforms_tests import (
        TestsFlextInfraLazyInitTransforms as TestsFlextInfraLazyInitTransforms,
    )
    from tests.unit.codegen.scaffolder_naming_tests import (
        TestGeneratedClassNamingConvention as TestGeneratedClassNamingConvention,
        TestGeneratedFilesAreValidPython as TestGeneratedFilesAreValidPython,
    )
    from tests.unit.codegen.test_codegen_pyproject_conform import (
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
