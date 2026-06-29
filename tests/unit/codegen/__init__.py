# AUTO-GENERATED FILE — Regenerate with: make gen
"""Codegen package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_tests import (
        c as c,
        d as d,
        e as e,
        h as h,
        m as m,
        p as p,
        r as r,
        s as s,
        t as t,
        td as td,
        tf as tf,
        tk as tk,
        tm as tm,
        tv as tv,
        u as u,
        x as x,
    )

    from tests.unit.codegen.lazy_init_generation_tests import (
        TestGenerateFile as TestGenerateFile,
        TestGenerateTypeChecking as TestGenerateTypeChecking,
        TestRunRuffFix as TestRunRuffFix,
    )
    from tests.unit.codegen.lazy_init_helpers_tests import (
        TestsFlextInfraLazyInitHelpers as TestsFlextInfraLazyInitHelpers,
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
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".autofix_workspace_tests": ("autofix_workspace_tests",),
        ".census_models_tests": ("census_models_tests",),
        ".census_tests": ("census_tests",),
        ".consolidator_tests": ("consolidator_tests",),
        ".constants_quality_gate_tests": ("constants_quality_gate_tests",),
        ".init_tests": ("init_tests",),
        ".lazy_init_generation_tests": (
            "TestGenerateFile",
            "TestGenerateTypeChecking",
            "TestRunRuffFix",
        ),
        ".lazy_init_helpers_tests": ("TestsFlextInfraLazyInitHelpers",),
        ".lazy_init_process_tests": ("lazy_init_process_tests",),
        ".lazy_init_service_tests": ("lazy_init_service_tests",),
        ".lazy_init_tests": (
            "TestAllDirectoriesScanned",
            "TestCheckOnlyMode",
            "TestEdgeCases",
            "TestExcludedDirectories",
        ),
        ".lazy_init_transforms_tests": ("TestsFlextInfraLazyInitTransforms",),
        ".main_tests": ("main_tests",),
        ".pipeline_tests": ("pipeline_tests",),
        ".scaffolder_naming_tests": (
            "TestGeneratedClassNamingConvention",
            "TestGeneratedFilesAreValidPython",
        ),
        ".scaffolder_tests": ("scaffolder_tests",),
        ".test_codegen_py_typed": ("test_codegen_py_typed",),
        ".test_codegen_version_file": ("test_codegen_version_file",),
        ".test_violation_key": ("test_violation_key",),
        "flext_tests": (
            "c",
            "d",
            "e",
            "h",
            "m",
            "p",
            "r",
            "s",
            "t",
            "td",
            "tf",
            "tk",
            "tm",
            "tv",
            "u",
            "x",
        ),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
