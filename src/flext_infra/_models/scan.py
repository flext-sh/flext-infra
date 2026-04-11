"""Domain models for the shared utilities subpackage.

Scan violation and result models used by infrastructure scanning utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import (
    FlextInfraModelsNamespaceEnforcer,
    t,
)
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsScan:
    """Shared utility domain models for scanning and analysis."""

    class DetectorContext(m.ArbitraryTypesModel):
        """Bundles common parameters passed to every detect_file classmethod."""

        file_path: Path = Field(
            description="Filesystem path of the file being scanned.",
        )
        rope_project: t.Infra.RopeProject = Field(
            description="Initialized Rope project for semantic metadata.",
        )
        parse_failures: (
            MutableSequence[FlextInfraModelsNamespaceEnforcer.ParseFailureViolation]
            | None
        ) = Field(
            default=None,
            description="Shared parse-failure collector across detector passes.",
        )
        project_name: str = Field(
            default="",
            description="Optional project name for the scanned file.",
        )
        project_root: Path | None = Field(
            default=None,
            description="Optional project root containing the scanned file.",
        )

    class ScanViolation(
        FlextInfraModelsMixins.PositiveLineMixin,
        m.ContractModel,
    ):
        """A single violation found during file scanning."""

        message: Annotated[
            str,
            Field(description="Human-readable violation description"),
        ]
        severity: Annotated[str, Field(description="Violation severity level")]
        rule_id: Annotated[
            str | None,
            Field(default=None, description="Optional rule identifier"),
        ]

    class ScanResult(m.ArbitraryTypesModel):
        """Result of scanning a single file."""

        @staticmethod
        def _violations_default() -> list[FlextInfraModelsScan.ScanViolation]:
            return []

        file_path: Annotated[Path, Field(description="Path to the scanned file")]
        violations: Annotated[
            list[FlextInfraModelsScan.ScanViolation],
            Field(
                default_factory=_violations_default,
                description="Violations found in the file",
            ),
        ]
        detector_name: Annotated[
            str,
            Field(description="Name of the detector that produced this result"),
        ]


__all__ = ["FlextInfraModelsScan"]
