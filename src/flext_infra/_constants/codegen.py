"""Centralized constants for the codegen package.

All constants used across codegen modules are defined here to avoid
duplication and ensure single-source-of-truth for configuration values.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from typing import TYPE_CHECKING, Final

from flext_infra._constants.codegen_detection import FlextInfraConstantsCodegenDetection
from flext_infra._constants.codegen_lazy import FlextInfraConstantsCodegenLazy
from flext_infra._constants.codegen_render_names import (
    FlextInfraConstantsCodegenRenderNames,
)

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegen(
    FlextInfraConstantsCodegenLazy,
    FlextInfraConstantsCodegenDetection,
    FlextInfraConstantsCodegenRenderNames,
):
    """Namespace for all codegen-related constants."""

    # mro-wkii.17.26 (codex): protobuf source owns runtime modules; no .pyi output.
    GRPC_PROTO_GLOB: Final[str] = "*.proto"
    "Package-source glob compiled by canonical gRPC codegen."
    GRPC_GENERATED_MODULE_SUFFIXES: Final[t.StrSequence] = ("_pb2.py", "_pb2_grpc.py")
    "Python runtime modules emitted for each protobuf schema."
    GRPC_CODEGEN_TIMEOUT_SECONDS: Final[int] = 120
    "Maximum duration of one project's grpc_tools.protoc invocation."

    SRC_MODULES: Final[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
        ("constants.py", "Constants", "FlextConstants", "Constants"),
        ("typings.py", "Types", "FlextTypes", "Type aliases"),
        ("protocols.py", "Protocols", "FlextProtocols", "Protocol definitions"),
        ("models.py", "Models", "FlextModels", "Domain models"),
        ("utilities.py", "Utilities", "FlextUtilities", "Utility functions"),
    )
    "Base module definitions for src/: (filename, class_suffix, base_class, docstring)."
    TESTS_MODULES: Final[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
        ("constants.py", "Constants", "FlextTestsConstants", "Test constants"),
        ("typings.py", "Types", "FlextTestsTypes", "Test type aliases"),
        ("protocols.py", "Protocols", "FlextTestsProtocols", "Test protocols"),
        ("models.py", "Models", "FlextTestsModels", "Test models"),
        ("utilities.py", "Utilities", "FlextTestsUtilities", "Test utilities"),
    )
    "Base module definitions for tests/: (filename, class_suffix, base_class, docstring)."
    # mro-wkii.14 (agent: codegen) — par raiz config/settings (padrao cosmos-main:
    # modulo privado `_config.py`/`_settings.py` exportando o singleton). Consumido
    # pelo gerador de scaffold (mro-wkii.10); base flext-core em estabilizacao por
    # outro agente — nao tocar runtime config/settings aqui.
    RUNTIME_MODULES: Final[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
        ("_config.py", "Config", "FlextConfig", "Runtime config"),
        ("_settings.py", "Settings", "FlextSettings", "Runtime settings"),
    )
    "Runtime singleton modules for src/: (filename, class_suffix, base_class, docstring)."
    VIOLATION_PATTERN: Final[t.RegexPattern] = re.compile(
        r"\[(?P<rule>NS-\d{3})-\d{3}\]\s+(?P<module>[^:]+):(?P<line>\d+)\s+\u2014\s+(?P<message>.+)"
    )
    "Regex to parse violation strings: [NS-00X-NNN] path:line — message."

    # --- Pipeline stage StrEnum (was: class Pipeline plain strings) ---
    @unique
    class PipelineStage(StrEnum):
        """Canonical codegen pipeline stage identifiers."""

        DISCOVER = "discover"
        PY_TYPED = "py_typed"
        CENSUS_BEFORE = "census_before"
        SCAFFOLD = "scaffold"
        AUTO_FIX = "auto_fix"
        GRPC = "grpc"
        LAZY_INIT = "lazy_init"
        CENSUS_AFTER = "census_after"

    PIPELINE_STAGE_ORDER: Final[tuple[PipelineStage, ...]] = (
        PipelineStage.DISCOVER,
        PipelineStage.PY_TYPED,
        PipelineStage.CENSUS_BEFORE,
        PipelineStage.SCAFFOLD,
        PipelineStage.AUTO_FIX,
        PipelineStage.GRPC,
        PipelineStage.LAZY_INIT,
        PipelineStage.CENSUS_AFTER,
    )
    "Ordered sequence of pipeline stage identifiers."
    PIPELINE_KEY_DRY_RUN: Final[str] = "dry_run"
    "Config key for pipeline dry-run mode."

    # --- Quality gate constants (was: class QualityGate) ---
    QG_REPORT_DIR: Final[str] = ".reports/codegen/constants-quality-gate"
    "Report directory for constants quality gate."
    QG_CHECK_NAMESPACE_COMPLIANCE: Final[str] = "namespace_compliance"
    QG_CHECK_MRO_VALIDITY: Final[str] = "mro_validity"
    QG_CHECK_IMPORT_RESOLUTION: Final[str] = "import_resolution"
    QG_CHECK_LAYER_COMPLIANCE: Final[str] = "layer_compliance"
    QG_CHECK_DUPLICATION_REDUCTION: Final[str] = "duplication_reduction"
    QG_CHECK_TYPE_SAFETY: Final[str] = "type_safety"
    QG_CHECK_LINT_CLEAN: Final[str] = "lint_clean"


__all__: list[str] = ["FlextInfraConstantsCodegen"]
