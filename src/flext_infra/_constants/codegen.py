"""Centralized constants for the codegen package.

All constants used across codegen modules are defined here to avoid
duplication and ensure single-source-of-truth for configuration values.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from enum import StrEnum, unique
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from flext_infra._constants import (
    FlextInfraConstantsCodegenDetection,
    FlextInfraConstantsCodegenLazy,
    FlextInfraConstantsCodegenRenderNames,
    FlextInfraConstantsWorkspace,
)
from flext_infra._constants.config import FlextInfraConstantsConfig

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraConstantsCodegen(
    FlextInfraConstantsCodegenLazy,
    FlextInfraConstantsCodegenDetection,
    FlextInfraConstantsCodegenRenderNames,
):
    """Namespace for all codegen-related constants."""

    FILE_ONLY_SURFACES: ClassVar[
        frozenset[FlextInfraConstantsConfig.CodegenConformSurface]
    ] = frozenset((
        FlextInfraConstantsConfig.CodegenConformSurface.LAZY_INIT,
        FlextInfraConstantsConfig.CodegenConformSurface.FACADES,
    ))
    "Surfaces planned for one exact module destination, never repository fans."

    SELF_SCOPE_SURFACES: ClassVar[
        frozenset[FlextInfraConstantsConfig.CodegenConformSurface]
    ] = frozenset((
        FlextInfraConstantsConfig.CodegenConformSurface.ENVRC,
        FlextInfraConstantsConfig.CodegenConformSurface.MISE_CONFIG,
    ))
    "Surfaces restricted to the self repository scope."

    DECLARED_TARGET_SURFACES: ClassVar[
        frozenset[FlextInfraConstantsConfig.CodegenConformSurface]
    ] = SELF_SCOPE_SURFACES | frozenset((
        FlextInfraConstantsConfig.CodegenConformSurface.MAKEFILE,
        FlextInfraConstantsConfig.CodegenConformSurface.PYPROJECT,
        FlextInfraConstantsConfig.CodegenConformSurface.EDITOR,
    ))
    "Self-owned configuration is planned against the declared repository target."

    ALLOW_UNPROVISIONED_SURFACES: ClassVar[
        frozenset[FlextInfraConstantsConfig.CodegenConformSurface]
    ] = DECLARED_TARGET_SURFACES | frozenset((
        FlextInfraConstantsConfig.CodegenConformSurface.DOCS_CONFIG,
    ))
    "Declared configuration and docs can be rendered before member provisioning."

    PARTIAL_PLAN_SURFACES: ClassVar[
        frozenset[FlextInfraConstantsConfig.CodegenConformSurface]
    ] = ALLOW_UNPROVISIONED_SURFACES | frozenset((
        FlextInfraConstantsConfig.CodegenConformSurface.WORKFLOWS,
    ))
    "Partial rendering also includes provisioned workflow bindings."

    MISE_ARTIFACTS_STATE_DIRECTORY: ClassVar[Path] = Path(".state") / "mise-artifacts"

    MISE_BOOTSTRAP_STORAGE_ROOT_VARIABLE: ClassVar[str] = "MISE_DATA_DIR"
    """Env key routing the packaged mise bootstrap to its storage root."""

    CONFIG_SPEC: ClassVar[t.Pair[str, int]] = (
        FlextInfraConstantsWorkspace.MISE_TOML_FILENAME,
        0o644,
    )

    JOURNAL_NAME: ClassVar[str] = "flext-infra-codegen-transaction-journal.json"

    JOURNAL_MODE: ClassVar[int] = 0o600

    JOURNAL_LEASE_WAIT_SECONDS: ClassVar[float] = 1800.0
    """Bounded polite wait for a held lease before failing loud.

    A legitimate fleet ``make gen`` holds the lease for minutes; an immediate
    non-blocking refusal turned ordinary concurrent traffic into a spurious
    ``JournalLeaseTimeoutError``. The wait is bounded so a truly
    wedged holder still fails loud instead of hanging forever.
    """

    JOURNAL_LEASE_POLL_SECONDS: ClassVar[float] = 1.0
    """Polling interval while waiting for a held journal lease."""

    TRANSACTION_DIR_PREFIX: ClassVar[str] = "transaction-"

    TRANSACTION_ID_LENGTH: ClassVar[int] = 32

    FACADE_MODULE_PARTS: ClassVar[int] = 2
    """Dotted parts of the ``package.module`` a type facade destination names."""

    SRC_MODULES: ClassVar[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
        ("constants.py", "Constants", "FlextConstants", "Constants"),
        ("typings.py", "Types", "FlextTypes", "Type aliases"),
        ("protocols.py", "Protocols", "FlextProtocols", "Protocol definitions"),
        ("models.py", "Models", "FlextModels", "Domain models"),
        ("utilities.py", "Utilities", "FlextUtilities", "Utility functions"),
    )
    "Base module definitions for src/: (filename, class_suffix, base_class, docstring)."
    TESTS_MODULES: ClassVar[t.VariadicTuple[t.Quad[str, str, str, str]]] = tuple(
        (
            filename,
            suffix,
            base_class.replace("Flext", "FlextTests", 1),
            f"Test {description.lower()}",
        )
        for filename, suffix, base_class, description in SRC_MODULES
    )
    "Test modules inherit the source family shape through the test foundation."
    # Canonical root config/settings pair: a
    # private `_config.py`/`_settings.py` module exporting the singleton.
    # Consumed by the scaffold generator.
    RUNTIME_MODULES: ClassVar[t.VariadicTuple[t.Quad[str, str, str, str]]] = (
        ("_config.py", "Config", "FlextConfig", "Runtime config"),
        ("_settings.py", "Settings", "FlextSettings", "Runtime settings"),
    )
    "Runtime singleton modules for src/: (filename, class_suffix, base_class, doc)."
    VIOLATION_PATTERN: ClassVar[t.RegexPattern] = re.compile(
        r"\[(?P<rule>[a-z0-9][a-z0-9-]*)\]\s+"
        r"(?P<module>[^:]+):(?P<line>\d+)\s+\u2014\s+(?P<message>.+)",
    )
    "Regex to parse violation strings: [rule-id] path:line — message."
    PROTOCOL_MODEL_MINIMAL_BODY_LINES: ClassVar[int] = 3
    "Header lines of a generated protocol class; at or below it the body is empty."
    MISE_RELEASE_COMPONENT_COUNT: ClassVar[int] = 3
    "Number of numeric components in a generated Mise release version."
    MISE_RELEASE_PATTERN: ClassVar[str] = (
        rf"[0-9]+(\.[0-9]+){{{MISE_RELEASE_COMPONENT_COUNT - 1}}}"
    )
    "Resolved-release grammar consumed by Python and generated shell boundaries."
    CODEGEN_TRANSACTION_LOCK_FILENAME: ClassVar[str] = "flext-infra-codegen.lock"
    "Worktree-specific administrative lock for complete generation."
    CODEGEN_TRANSACTION_LOCK_MODE: ClassVar[int] = 0o600
    "Owner-private mode required for the generation lock."

    # --- Pipeline stage StrEnum (was: class Pipeline plain strings) ---
    @unique
    class PipelineStage(StrEnum):
        """Canonical codegen pipeline stage identifiers."""

        DISCOVER = "discover"
        TOOLCHAIN = "toolchain"
        PY_TYPED = "py_typed"
        CENSUS_BEFORE = "census_before"
        SCAFFOLD = "scaffold"
        AUTO_FIX = "auto_fix"
        DEPS = "deps"
        LAZY_INIT = "lazy_init"
        CENSUS_AFTER = "census_after"

    PIPELINE_STAGE_ORDER: ClassVar[t.VariadicTuple[PipelineStage]] = tuple(
        PipelineStage
    )
    "Stage execution follows the canonical enumeration's declaration order."
    PIPELINE_KEY_DRY_RUN: ClassVar[str] = "dry_run"
    "Config key for pipeline dry-run mode."

    # --- Quality gate constants (was: class QualityGate) ---
    QG_REPORT_DIR: ClassVar[str] = ".reports/codegen/constants-quality-gate"
    "Report directory for constants quality gate."
    QG_CHECK_NAMESPACE_COMPLIANCE: ClassVar[str] = "namespace_compliance"
    QG_CHECK_DUPLICATION_REDUCTION: ClassVar[str] = "duplication_reduction"
    QG_CHECK_TYPE_SAFETY: ClassVar[str] = "type_safety"
    QG_CHECK_LINT_CLEAN: ClassVar[str] = "lint_clean"


__all__: list[str] = ["FlextInfraConstantsCodegen"]
