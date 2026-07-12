"""Domain models for the enforcement subpackage.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, ClassVar

from flext_cli import m
from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.protocols import p


class FlextInfraModelsEnforcement:
    """Models for enforcement collection — exposed through the ``m.Infra`` facade."""

    class EnforcementEvaluation(m.ArbitraryTypesModel):
        """Collected rule probes and collection failures for one project."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        violations: Annotated[
            tuple[tuple[me.EnforcementRuleSpec, p.AttributeProbe], ...],
            m.Field(description="Rule/probe pairs collected for the project"),
        ]
        failures: Annotated[
            tuple[fr.FailedFix, ...],
            m.Field(description="Structured collection/routing failures"),
        ]

    class EnforcementProbe(m.ArbitraryTypesModel):
        """Structural probe consumed by fixer adapters.

        Replaces the former ``SimpleNamespace`` probe: validated core fields
        plus ``extra="allow"`` for rule-specific attributes that adapters
        inspect via ``getattr``.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            extra="allow",
        )

        file_path: Annotated[str, m.Field(description="Target file path")]
        line: Annotated[
            int,
            m.Field(description="Line number of the violation"),
        ] = 0
        rule_id: Annotated[
            str,
            m.Field(description="Originating rule identifier"),
        ] = ""


__all__: list[str] = ["FlextInfraModelsEnforcement"]
