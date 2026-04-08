# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Codegen package."""

from __future__ import annotations

from flext_core.lazy import install_lazy_exports

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


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
