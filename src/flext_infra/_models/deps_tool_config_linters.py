"""Ruff and Mypy tool configuration models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from keyword import iskeyword
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsDepsToolConfigProject


class FlextInfraModelsDepsToolConfigLinters(FlextInfraModelsDepsToolConfigProject):
    """Linters tool configuration models."""

    class RuffTypeCheckingConfig(m.ArbitraryTypesModel):
        """Ruff flake8-type-checking settings loaded from YAML."""

        runtime_evaluated_roots: Annotated[
            t.SequenceOf[t.NonEmptyStr],
            m.Field(
                alias="runtime-evaluated-roots",
                min_length=1,
                description=(
                    "Qualified base classes whose subclasses evaluate their "
                    "annotations at runtime; codegen derives every project "
                    "base inheriting one into runtime-evaluated-base-classes."
                ),
            ),
        ]

    class RuffReadonlyNamespaceOccurrence(m.ArbitraryTypesModel):
        """Identify one readonly namespace, never a name-wide lint exemption.

        These are declaration identities. Source authentication, producer typing,
        and complete native lint coverage must precede any Ruff adaptation.
        """

        path: t.NonEmptyStr = m.Field(
            description="Exact project-relative getter source path, without globs.",
        )
        qualname: t.NonEmptyStr = m.Field(
            description="Getter declaration qualified within its source module.",
        )
        role: Literal["protocol-instance-readonly-namespace"] = m.Field(
            description="Readonly instance Protocol getter role to authenticate.",
        )
        return_type_owner: t.NonEmptyStr = m.Field(
            alias="return-type-owner",
            description="Fully qualified declared return contract owner.",
        )
        producer_qualname: t.NonEmptyStr = m.Field(
            alias="producer-qualname",
            description="Fully qualified real producer namespace member.",
        )

        @m.field_validator("path")
        @classmethod
        def require_exact_project_path(cls, value: str) -> str:
            """Reject glob, escaping, and normalized spellings of source paths.

            Returns:
                The exact project-relative Python source identity.

            Raises:
                ValueError: If the path is not an exact relative source path.

            """
            path = PurePosixPath(value)
            if (
                path.is_absolute()
                or path.as_posix() != value
                or ".." in path.parts
                or path.suffix not in {".py", ".pyi"}
                or any(character in value for character in "\\*?[]{}:\x00\n\r")
            ):
                msg = (
                    "readonly namespace requires an exact project-relative Python path"
                )
                raise ValueError(msg)
            return value

        @m.field_validator("qualname", "return_type_owner", "producer_qualname")
        @classmethod
        def require_declaration_identity(cls, value: str) -> str:
            """Accept qualified Python identities, not expressions or patterns.

            Returns:
                The unchanged qualified declaration identity.

            Raises:
                ValueError: If the value cannot name a qualified declaration.

            """
            parts = value.split(".")
            if "." not in value or any(
                not part.isascii() or not part.isidentifier() or iskeyword(part)
                for part in parts
            ):
                msg = "readonly namespace requires a qualified declaration identity"
                raise ValueError(msg)
            return value

        @m.model_validator(mode="after")
        def require_paired_namespace(self) -> Self:
            """Require the producer to expose the same PascalCase namespace.

            Returns:
                The identity pair, without granting a semantic exemption.

            Raises:
                ValueError: If the declared namespace and producer disagree.

            """
            name = self.qualname.rsplit(".", 1)[1]
            if (
                not name[0].isupper()
                or not any(character.islower() for character in name)
                or self.producer_qualname.rsplit(".", 1)[1] != name
            ):
                msg = "readonly namespace requires a paired PascalCase producer member"
                raise ValueError(msg)
            return self

    class RuffLintConfig(m.ArbitraryTypesModel):
        """Ruff lint settings loaded from YAML."""

        rule_owners: Annotated[
            t.MappingKV[t.Infra.RuffRule, t.NonEmptyStr],
            m.Field(
                alias="rule-owners",
                description=(
                    "Rules enforced by another registered canonical gate, never "
                    "waived; projection verifies its complete check/repair election."
                ),
            ),
        ]

        @m.field_validator("rule_owners")
        @classmethod
        def require_distinct_registered_rule_owners(
            cls,
            owners: t.StrMapping,
        ) -> t.StrMapping:
            """Reject unknown owners and delegation back to the lint gate.

            Returns:
                The declared ownership mapping without introducing defaults.

            Raises:
                ValueError: If any rule has an unknown or self-owned gate.

            """
            invalid = sorted(
                f"{rule}: {owner}"
                for rule, owner in owners.items()
                if owner == c.Infra.LINT or owner not in c.Infra.ALLOWED_GATES
            )
            if invalid:
                msg = "Ruff rules require distinct registered owners: " + ", ".join(
                    invalid
                )
                raise ValueError(msg)
            return owners

        ruling_disabled_rules: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="ruling-disabled-rules",
                strict=False,
                description=(
                    "Operator-ruled rules disabled at the SSOT because the "
                    "lazy facade architecture requires what they forbid; "
                    "projected into lint ignore, never silenced by manual "
                    "hints."
                ),
            ),
        ] = ()
        enforce: Annotated[
            t.MappingKV[t.Infra.RuffRule, t.Infra.EnforcementIds],
            m.Field(
                description=(
                    "Ruff rule name -> enforcement law ids the rule claims; a "
                    "claim is active only while the lint selection enables it."
                ),
            ),
        ]
        fix_recipes: Annotated[
            t.MappingKV[t.Infra.RuffRule, c.Infra.LintFixRecipe],
            m.Field(
                alias="fix-recipes",
                description=(
                    "Ruff rule name -> repair make fix applies to the findings "
                    "Ruff reports without a fix of its own."
                ),
            ),
        ]
        fix_recipe_phases: Annotated[
            t.VariadicTuple[t.VariadicTuple[c.Infra.LintFixRecipe]],
            m.Field(
                alias="fix-recipe-phases",
                description=(
                    "Recipe phases make fix applies in order; Ruff re-reads "
                    "the tree after each phase so a later phase sees the "
                    "findings an earlier one created or cured."
                ),
            ),
        ]
        flake8_type_checking: Annotated[
            FlextInfraModelsDepsToolConfigLinters.RuffTypeCheckingConfig,
            m.Field(
                alias="flake8-type-checking",
                description="Ruff flake8-type-checking configuration",
            ),
        ]

    class RuffConfig(m.ArbitraryTypesModel):
        """Ruff top-level settings loaded from YAML."""

        findings_exit_codes: Annotated[
            tuple[int, ...],
            m.Field(
                alias="findings-exit-codes",
                strict=False,
                description="Exit statuses with which Ruff reports its findings.",
            ),
        ]
        lint: FlextInfraModelsDepsToolConfigLinters.RuffLintConfig = m.Field(
            description="Ruff lint configuration",
        )

    class MypyOverrideConfig(m.ArbitraryTypesModel):
        """Single [[tool.mypy.overrides]] entry."""

        modules: Annotated[
            t.StrSequence,
            m.Field(description="Module patterns for this override."),
        ]
        settings: Annotated[
            t.Infra.SettingsPairs,
            m.Field(description="Native override options as ordered key/value pairs."),
        ] = ()
        justification: Annotated[
            str,
            m.Field(
                description=(
                    "Required citation (GitHub issue / PEP / mypy docs) justifying "
                    "this override. AGENTS.md:319 forbids suppressions without "
                    "evidence; leave empty only for strictly transitional overrides "
                    "with a TODO in the module comment."
                ),
            ),
        ] = ""

    class MypyConfig(m.ArbitraryTypesModel):
        """Execution budget and ownership policy for native Mypy options."""

        timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                strict=True,
                description="Default Mypy wall-time budget in seconds.",
            ),
        ]
        max_timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                strict=True,
                description="Finite project budget ceiling in seconds.",
            ),
        ]

        @m.model_validator(mode="after")
        def validate_timeout_ceiling(self) -> Self:
            """Keep the default inside the declared finite ceiling.

            Returns:
                The validated policy.

            Raises:
                ValueError: If the default exceeds the ceiling.

            """
            if self.timeout_seconds > self.max_timeout_seconds:
                msg = "Mypy default timeout exceeds max_timeout_seconds"
                raise ValueError(msg)
            return self

        ruling_disable_error_codes: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                alias="ruling-disable-error-codes",
                strict=False,
                description="Operator-authorized suspended diagnostics.",
            ),
        ] = ()
        overrides: Annotated[
            t.VariadicTuple[FlextInfraModelsDepsToolConfigLinters.MypyOverrideConfig],
            m.Field(description="Module scopes and justified native option pairs."),
        ] = ()


__all__: list[str] = ["FlextInfraModelsDepsToolConfigLinters"]
