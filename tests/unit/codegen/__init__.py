# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.codegen.autofix_workspace_tests as _tests_unit_codegen_autofix_workspace_tests

    autofix_workspace_tests = _tests_unit_codegen_autofix_workspace_tests
    import tests.unit.codegen.census_models_tests as _tests_unit_codegen_census_models_tests

    census_models_tests = _tests_unit_codegen_census_models_tests
    import tests.unit.codegen.census_tests as _tests_unit_codegen_census_tests

    census_tests = _tests_unit_codegen_census_tests
    import tests.unit.codegen.consolidator_tests as _tests_unit_codegen_consolidator_tests

    consolidator_tests = _tests_unit_codegen_consolidator_tests
    import tests.unit.codegen.constants_quality_gate_tests as _tests_unit_codegen_constants_quality_gate_tests

    constants_quality_gate_tests = _tests_unit_codegen_constants_quality_gate_tests
    import tests.unit.codegen.init_tests as _tests_unit_codegen_init_tests

    init_tests = _tests_unit_codegen_init_tests
    import tests.unit.codegen.lazy_init_generation_tests as _tests_unit_codegen_lazy_init_generation_tests

    lazy_init_generation_tests = _tests_unit_codegen_lazy_init_generation_tests
    import tests.unit.codegen.lazy_init_helpers_tests as _tests_unit_codegen_lazy_init_helpers_tests

    lazy_init_helpers_tests = _tests_unit_codegen_lazy_init_helpers_tests
    import tests.unit.codegen.lazy_init_process_tests as _tests_unit_codegen_lazy_init_process_tests

    lazy_init_process_tests = _tests_unit_codegen_lazy_init_process_tests
    import tests.unit.codegen.lazy_init_service_tests as _tests_unit_codegen_lazy_init_service_tests

    lazy_init_service_tests = _tests_unit_codegen_lazy_init_service_tests
    import tests.unit.codegen.lazy_init_tests as _tests_unit_codegen_lazy_init_tests

    lazy_init_tests = _tests_unit_codegen_lazy_init_tests
    import tests.unit.codegen.lazy_init_transforms_tests as _tests_unit_codegen_lazy_init_transforms_tests

    lazy_init_transforms_tests = _tests_unit_codegen_lazy_init_transforms_tests
    import tests.unit.codegen.main_tests as _tests_unit_codegen_main_tests

    main_tests = _tests_unit_codegen_main_tests
    import tests.unit.codegen.pipeline_tests as _tests_unit_codegen_pipeline_tests

    pipeline_tests = _tests_unit_codegen_pipeline_tests
    import tests.unit.codegen.scaffolder_naming_tests as _tests_unit_codegen_scaffolder_naming_tests

    scaffolder_naming_tests = _tests_unit_codegen_scaffolder_naming_tests
    import tests.unit.codegen.scaffolder_tests as _tests_unit_codegen_scaffolder_tests

    scaffolder_tests = _tests_unit_codegen_scaffolder_tests
    import tests.unit.codegen.test_codegen_pipeline_dag as _tests_unit_codegen_test_codegen_pipeline_dag

    test_codegen_pipeline_dag = _tests_unit_codegen_test_codegen_pipeline_dag
    import tests.unit.codegen.test_violation_key as _tests_unit_codegen_test_violation_key

    test_violation_key = _tests_unit_codegen_test_violation_key
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
    "autofix_workspace_tests": "tests.unit.codegen.autofix_workspace_tests",
    "c": ("flext_core.constants", "FlextConstants"),
    "census_models_tests": "tests.unit.codegen.census_models_tests",
    "census_tests": "tests.unit.codegen.census_tests",
    "consolidator_tests": "tests.unit.codegen.consolidator_tests",
    "constants_quality_gate_tests": "tests.unit.codegen.constants_quality_gate_tests",
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "init_tests": "tests.unit.codegen.init_tests",
    "lazy_init_generation_tests": "tests.unit.codegen.lazy_init_generation_tests",
    "lazy_init_helpers_tests": "tests.unit.codegen.lazy_init_helpers_tests",
    "lazy_init_process_tests": "tests.unit.codegen.lazy_init_process_tests",
    "lazy_init_service_tests": "tests.unit.codegen.lazy_init_service_tests",
    "lazy_init_tests": "tests.unit.codegen.lazy_init_tests",
    "lazy_init_transforms_tests": "tests.unit.codegen.lazy_init_transforms_tests",
    "m": ("flext_core.models", "FlextModels"),
    "main_tests": "tests.unit.codegen.main_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "pipeline_tests": "tests.unit.codegen.pipeline_tests",
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "scaffolder_naming_tests": "tests.unit.codegen.scaffolder_naming_tests",
    "scaffolder_tests": "tests.unit.codegen.scaffolder_tests",
    "t": ("flext_core.typings", "FlextTypes"),
    "test_codegen_pipeline_dag": "tests.unit.codegen.test_codegen_pipeline_dag",
    "test_violation_key": "tests.unit.codegen.test_violation_key",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "autofix_workspace_tests",
    "c",
    "census_models_tests",
    "census_tests",
    "consolidator_tests",
    "constants_quality_gate_tests",
    "d",
    "e",
    "h",
    "init_tests",
    "lazy_init_generation_tests",
    "lazy_init_helpers_tests",
    "lazy_init_process_tests",
    "lazy_init_service_tests",
    "lazy_init_tests",
    "lazy_init_transforms_tests",
    "m",
    "main_tests",
    "p",
    "pipeline_tests",
    "r",
    "s",
    "scaffolder_naming_tests",
    "scaffolder_tests",
    "t",
    "test_codegen_pipeline_dag",
    "test_violation_key",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
