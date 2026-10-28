"""Refactor migration model mixins for rope-oriented orchestration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, u
from typing_extensions import TypeForm

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsBase


class FlextInfraModelsRefactorGrep:
    """Mixin containing migration/reporting contracts for refactor orchestration."""

    class CodemodRule(FlextInfraModelsBase.FrozenArbitrary):
        """One validated ast-grep rule document from a composed provider."""

        id: Annotated[t.NonEmptyStr, m.Field(description="Canonical ast-grep rule ID")]
        digest: Annotated[
            t.NonEmptyStr,
            m.Field(description="SHA-256 of the canonical rule document"),
        ]
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Distribution or local rule provider"),
        ]
        resource: Annotated[
            Path,
            m.Field(description="Rule document resource containing this ID"),
        ]
        fixable: Annotated[
            bool,
            m.Field(description="Whether the rule declares an automated fix"),
        ]
        owned_path_suffix: Annotated[
            Literal[".pyi"] | None,
            m.Field(
                description="Owned path admission independent of syntax or content"
            ),
        ] = None
        message: Annotated[str, m.Field(description="Canonical rule diagnostic")] = ""
        module_absence: Annotated[
            bool,
            m.Field(
                description="Native predicate is exclusively absence at module root"
            ),
        ] = False
        expected: Annotated[
            int | None,
            m.Field(
                ge=0,
                description=(
                    "Declared finding-count receipt from the rule's metadata; "
                    "absent when the rule declares none"
                ),
            ),
        ] = None
        owner: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Canonical distribution name whose own plan drops the rule; "
                    "absent when the rule applies to every project"
                ),
            ),
        ] = None
        consumers_of: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Canonical distribution name whose runtime consumers alone "
                    "elect the rule; absent when the rule applies to every project"
                ),
            ),
        ] = None
        enforce: Annotated[
            t.Infra.EnforcementIds,
            m.Field(
                description=(
                    "Enforcement law ids the rule claims under its metadata; "
                    "empty when the rule enforces no catalog law"
                ),
            ),
        ] = ()
        disabled: Annotated[
            bool,
            m.Field(description="Whether ast-grep's own severity switches it off"),
        ] = False
        partitioned: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether metadata.scope partitions the rule per file group: "
                    "each project's generated provider renders it, so a plan "
                    "never elects the authored document"
                ),
            ),
        ] = False
        partition_of: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Catalog rule this generated partition renders; selecting "
                    "that catalog id selects every partition of it"
                ),
            ),
        ] = None
        relocation: Annotated[
            c.Infra.CodemodRelocation | None,
            m.Field(
                description=(
                    "Rope relocation that repairs the rule's findings over the "
                    "captured $NAME; absent for token-fix and plain detection rules"
                ),
            ),
        ] = None

        @m.model_validator(mode="after")
        def _validate_owned_path_rule(self) -> Self:
            """Require unconditional detection with a nonblank path diagnostic.

            Owned paths cannot depend on ownership, consumers, relocation, or
            module absence, and cannot declare an automated fix.

            Returns:
                The original unexempted rule.

            Raises:
                ValueError: If a path rule rewrites, exempts, or lacks a diagnostic.

            """
            if self.owned_path_suffix is not None and any((
                self.fixable,
                self.owner,
                self.consumers_of,
                self.relocation,
                self.module_absence,
                not self.message.strip(),
            )):
                msg = "owned-path rules cannot rewrite or exempt owned paths"
                raise ValueError(msg)
            return self

    class CodemodRuleset(FlextInfraModelsBase.FrozenArbitrary):
        """One provider config and its elected, conflict-free rule IDs."""

        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Distribution or local rule provider"),
        ]
        config: Annotated[
            Path,
            m.Field(description="Provider-owned ast-grep sgconfig path"),
        ]
        rule_ids: Annotated[
            Sequence[str],
            m.Field(description="Rule IDs elected from this provider"),
        ]
        fixable_rule_ids: Annotated[
            Sequence[str],
            m.Field(description="Elected rule IDs that declare an automated fix"),
        ]

    class CodemodRulePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Topologically composed dependency rules followed by the local delta."""

        provider_order: Annotated[
            Sequence[str],
            m.Field(description="Dependency-first provider precedence"),
        ]
        rules: Annotated[
            tuple[FlextInfraModelsRefactorGrep.CodemodRule, ...],
            m.Field(description="Unique semantic rules with their elected owner"),
        ]
        rulesets: Annotated[
            tuple[FlextInfraModelsRefactorGrep.CodemodRuleset, ...],
            m.Field(description="Executable provider configs in precedence order"),
        ]
        project_rule_ids: Annotated[
            Mapping[Path, Sequence[str]],
            m.Field(
                description="Absolute governed roots and their applicable rule IDs"
            ),
        ]

    class CodemodPackageExportsFacts(FlextInfraModelsBase.FrozenArbitrary):
        """What each package of one project publishes, where it lives, what it holds."""

        exports: Annotated[
            Mapping[str, t.StrTuple],
            m.Field(
                description=(
                    "Dotted package to the exact names its initializer __all__ "
                    "declares, read statically"
                ),
            ),
        ]
        directories: Annotated[
            Mapping[str, str],
            m.Field(
                description=(
                    "Dotted package to its directory, relative to the project "
                    "root in POSIX form"
                ),
            ),
        ]
        modules: Annotated[
            Mapping[str, t.StrTuple],
            m.Field(
                description=(
                    "Dotted package to the leaf names of its direct child modules "
                    "and child packages, read from the source index"
                ),
            ),
        ]

    class CodemodNativeGenerated(FlextInfraModelsBase.FrozenArbitrary):
        """One project's generated native documents, rendered in memory."""

        utilities: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(description="Generated utility documents keyed by utility id"),
        ]
        rules: Annotated[
            Mapping[str, t.JsonMapping],
            m.Field(description="Generated rule documents keyed by rule id"),
        ]
        scopes: Annotated[
            Mapping[str, t.StrTuple],
            m.Field(
                description=(
                    "Project-relative file sets keyed by the scope selector a "
                    "catalog rule names under metadata.scope"
                ),
            ),
        ]

    class CodemodPrimitiveOwner(FlextInfraModelsBase.FrozenArbitrary):
        """One public primitive whose native implementation closure is asked."""

        arg: Annotated[
            tuple[str, str],
            m.Field(description="The primitive's module and public expression"),
        ]

    class CodemodScopePartition(FlextInfraModelsBase.FrozenArbitrary):
        """One catalog rule's ``metadata.scope.partition`` declaration."""

        rule_id: Annotated[
            t.NonEmptyStr, m.Field(description="Catalog rule declaring the partition")
        ]
        variable: Annotated[
            t.NonEmptyStr, m.Field(description="Metavariable each copy constrains")
        ]
        holds: Annotated[
            bool,
            m.Field(description="Whether a copy keeps (true) or ignores its group"),
        ]
        selectors: Annotated[
            t.NonEmptyStr, m.Field(description="Published file-scope selector prefix")
        ]
        pattern: Annotated[
            t.NonEmptyStr,
            m.Field(description="Regex template instantiated with each key"),
        ] = c.Infra.CODEMOD_PARTITION_DEFAULT_PATTERN
        keys: Mapping[str, str] = m.Field(
            default_factory=u.empty(TypeForm(Mapping[str, str])),
            description="Explicit key regexes; derived from scopes when empty",
        )
        matching: Annotated[
            bool,
            m.Field(description="False constrains each copy away from its key"),
        ] = True

        @m.model_validator(mode="after")
        def _require_held_negation(self) -> Self:
            """Allow a negated key only where the group holds.

            Returns:
                The validated partition.

            Raises:
                ValueError: If a negated partition does not hold its group.

            """
            if not self.matching and not self.holds:
                msg = f"{self.rule_id}: partition matching=false requires holds=true"
                raise ValueError(msg)
            return self

    class CodemodScopeFacts(FlextInfraModelsBase.FrozenArbitrary):
        """One project's file scopes, the facts of the scoped rule renderer."""

        scopes: Annotated[
            Mapping[str, t.StrTuple],
            m.Field(description="Project-relative file sets keyed by scope selector"),
        ]

    class AccessorMigrationRule(m.ContractModel):
        """Declarative origin-bound accessor transformation."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        source_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical symbol name to replace"),
        ]
        replacement_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical symbol name used as replacement"),
        ]
        reason: Annotated[
            t.NonEmptyStr,
            m.Field(description="Human-readable explanation for the rename"),
        ]
        origin: Annotated[
            str,
            m.Field(description="Canonical API origin this rewrite is tied to"),
        ] = ""
        operation: Annotated[
            Literal["rename", "normalize-field"],
            m.Field(description="Transformation applied to proven owned references"),
        ] = "rename"
        declaring_class: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Qualified class that declares the accessor and field"),
        ] = None
        field: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Backing field passed to the public normalizer"),
        ] = None

        @m.model_validator(mode="after")
        def _require_expression_owner(self) -> Self:
            """Reject expression rules without complete declaration identity.

            Returns:
                The complete typed migration rule.

            Raises:
                ValueError: If a field-normalization rule lacks its owner or field.

            """
            if self.operation == "normalize-field" and (
                self.declaring_class is None or self.field is None
            ):
                msg = "Field normalization requires declaring_class and field"
                raise ValueError(msg)
            return self

    class AccessorMigrationChange(FlextInfraModelsBase.FrozenArbitrary):
        """Single automated rename or manual warning emitted by accessor migration."""

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        line: Annotated[
            t.NonNegativeInt,
            m.Field(description="1-based source line number when available"),
        ]
        original_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Original accessor or helper name"),
        ]
        replacement_name: Annotated[
            str,
            m.Field(description="Suggested or applied replacement name"),
        ] = ""
        automated: Annotated[
            bool,
            m.Field(description="Whether the migration was performed automatically"),
        ]
        reason: Annotated[
            str,
            m.Field(description="Human-readable migration rationale"),
        ]

    class AccessorMigrationFile(m.ArbitraryTypesModel):
        """Per-file preview for accessor migration dry-runs and applies.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        lint_tools: tuple[str, ...] = m.Field(
            default_factory=tuple,
            description="Selected lint tools used for preview rendering",
        )
        automated_changes: tuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange, ...
        ] = m.Field(
            default_factory=tuple,
            description="Automated rewrites captured for this file",
        )
        warnings: tuple[FlextInfraModelsRefactorGrep.AccessorMigrationChange, ...] = (
            m.Field(
                default_factory=tuple,
                description="Manual follow-up warnings for this file",
            )
        )
        diff: Annotated[
            str,
            m.Field(description="Unified diff preview for the file"),
        ] = ""
        lint_before: Annotated[
            t.Infra.LintSnapshot[FlextInfraModelsBase.LintGateResult],
            m.Field(description="Lint output before the proposed rewrite"),
        ]
        lint_after: Annotated[
            t.Infra.LintSnapshot[FlextInfraModelsBase.LintGateResult],
            m.Field(description="Lint output after the proposed rewrite"),
        ]
        new_lint_errors: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(description="Lint errors introduced by the proposed rewrite"),
        ]

    class AccessorMigrationReport(m.ArbitraryTypesModel):
        """Workspace-scale report for accessor migration orchestration.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        workspace: Annotated[t.NonEmptyStr, m.Field(description="Repository root path")]
        dry_run: Annotated[bool, m.Field(description="Dry-run indicator")]
        files_scanned: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total Python files scanned"),
        ]
        files_with_changes: Annotated[
            t.NonNegativeInt,
            m.Field(description="Files with automated rewrites"),
        ]
        automated_change_count: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total automated rewrites detected"),
        ]
        warning_count: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total manual follow-up warnings detected"),
        ]
        lint_tools: tuple[str, ...] = m.Field(
            default_factory=tuple,
            description="Canonical lint tool list used by this run",
        )
        lint_before_totals: Annotated[
            t.IntMapping,
            m.Field(description="Per-tool count of lint lines before rewrites"),
        ]
        lint_after_totals: Annotated[
            t.IntMapping,
            m.Field(description="Per-tool count of lint lines after rewrites"),
        ]
        new_lint_error_totals: Annotated[
            t.IntMapping,
            m.Field(description="Per-tool count of newly introduced lint lines"),
        ]
        files: tuple[FlextInfraModelsRefactorGrep.AccessorMigrationFile, ...] = m.Field(
            default_factory=tuple,
            description="Preview entries included in this report",
        )


__all__ = ("FlextInfraModelsRefactorGrep",)
