"""Static enforcement catalog contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Self

from flext_cli import m

from flext_infra import c, t


class FlextInfraModelsEnforcementCatalog:
    """Declarations of ``config/rules/catalog.yaml``."""

    class EnforcementRuleRef(m.FrozenModel):
        """One owner that detects a catalog law: an engine and its rule id."""

        engine: Annotated[
            c.Infra.EnforcementEngine,
            m.Field(description="Engine that owns the detection"),
        ]
        id: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Rule identity inside the engine: ast-grep rule id, Ruff "
                    "rule name, gate id or codegen template entry"
                ),
            ),
        ]
        code: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description="Finding code the gate reports for this law",
            ),
        ] = None

    class RuleSpec(m.FrozenModel):
        """One enforcement law and every owner that detects it."""

        id: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=c.Infra.ENFORCEMENT_RULE_ID_PATTERN,
                description="Stable catalog identity (ENFORCE-NNN)",
            ),
        ]
        severity: Annotated[
            c.Infra.EnforcementSeverity,
            m.Field(description="Declared severity of a violation"),
        ]
        description: Annotated[
            t.NonEmptyStr,
            m.Field(description="The law the row enforces"),
        ]
        agents_md_anchor: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="AGENTS.md section that states the law"),
        ] = None
        skills: Annotated[
            t.SequenceOf[t.NonEmptyStr],
            m.Field(description="Skills that teach the law"),
        ] = ()
        rules: Annotated[
            t.SequenceOf[FlextInfraModelsEnforcementCatalog.EnforcementRuleRef],
            m.Field(min_length=1, description="Owners that detect the law"),
        ]

    class EnforcementCatalog(m.FrozenModel):
        """The complete static enforcement catalog."""

        version: Annotated[
            int,
            m.Field(ge=1, description="Catalog schema version"),
        ]
        rules: Annotated[
            t.SequenceOf[FlextInfraModelsEnforcementCatalog.RuleSpec],
            m.Field(min_length=1, description="Enforcement laws"),
        ]

        @m.model_validator(mode="after")
        def _unique_rule_ids(self) -> Self:
            """Reject a catalog that declares one law twice.

            Returns:
                The validated catalog.

            Raises:
                ValueError: If two rows share one catalog identity.

            """
            ids = [rule.id for rule in self.rules]
            duplicates = sorted({rule_id for rule_id in ids if ids.count(rule_id) > 1})
            if duplicates:
                msg = f"enforcement catalog declares duplicate ids: {duplicates}"
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsEnforcementCatalog"]
