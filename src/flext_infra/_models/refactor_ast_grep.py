"""Refactor migration model mixins for rope-oriented orchestration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsBase, FlextInfraModelsCodemod


class FlextInfraModelsRefactorGrep:
    """Mixin containing migration/reporting contracts for refactor orchestration."""

    class CodemodContextCondition(FlextInfraModelsBase.FrozenArbitrary):
        """One project-context condition over a captured metavariable."""

        variable: Annotated[
            t.NonEmptyStr,
            m.Field(description="Captured single metavariable name"),
        ]
        predicate: Annotated[
            c.Infra.CodemodContextPredicate,
            m.Field(description="Project-context predicate derived from an SSOT"),
        ]
        holds: Annotated[
            bool,
            m.Field(description="Whether the predicate must hold (is) or fail (not)"),
        ]
        of: Annotated[
            t.NonEmptyStr | None,
            m.Field(
                description=(
                    "Captured metavariable naming the module the predicate is "
                    "evaluated against; absent for predicates of the project "
                    "or of the finding's own module"
                ),
            ),
        ] = None
        arg: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Literal operands the rule passes to the predicate (layer "
                    "names, for the layer predicates); empty when it takes none"
                ),
            ),
        ] = ()
        as_: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Layer the predicate assumes for a captured name that is "
                    "not itself a layer; empty when the rule assumes none"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_native_owner_reference(self) -> Self:
            """Require one qualified primitive, never a module waiver table.

            Returns:
                The validated model instance.

            Raises:
                ValueError: If the native predicate lacks its module/producer pair.

            """
            if (
                self.predicate
                is c.Infra.CodemodContextPredicate.CANONICAL_STATIC_PUBLICATION
                and (self.of is None or self.arg or self.as_)
            ):
                msg = (
                    "canonical-static-publication requires of and accepts no arg or as"
                )
                raise ValueError(msg)
            if self.predicate in {
                c.Infra.CodemodContextPredicate.DECLARATION_DECORATOR,
                c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
                c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION,
            } and (
                len(self.arg) != c.Infra.PAIRED_CONTEXT_PREDICATE_ARG_COUNT
                or any(
                    not all(part.isidentifier() for part in value.split("."))
                    for value in self.arg
                )
            ):
                msg = f"{self.predicate} requires one module and native producer"
                raise ValueError(msg)
            if (
                self.predicate is c.Infra.CodemodContextPredicate.FOREIGN_FACADE_MEMBER
                and (
                    len(self.arg) != 1
                    or self.arg[0] not in set(c.Infra.FacadeMemberPlacement)
                    or bool(self.as_)
                    or self.of is not None
                )
            ):
                msg = (
                    "foreign-facade-member requires exactly one placement arg: "
                    f"{sorted(c.Infra.FacadeMemberPlacement)}"
                )
                raise ValueError(msg)
            if (
                self.predicate is c.Infra.CodemodContextPredicate.FACADE_MEMBER_OWNER
                and any((
                    self.of is None,
                    len(self.arg) != 1,
                    not all(value.isidentifier() for value in self.arg),
                    bool(self.as_),
                    not self.holds,
                ))
            ):
                msg = (
                    "facade-member-owner requires of (the member capture) and "
                    "exactly one owner letter arg"
                )
                raise ValueError(msg)
            if (
                self.predicate is c.Infra.CodemodContextPredicate.MEMBER_RELOCATION
                and any((
                    self.of is None,
                    len(self.arg) != c.Infra.MEMBER_RELOCATION_CONTEXT_ARG_COUNT,
                    bool(self.as_),
                    not self.holds,
                    any(
                        not all(part.isidentifier() for part in value.split("."))
                        for value in self.arg
                    ),
                ))
            ):
                msg = (
                    "member-relocation requires of and five qualified operands: "
                    "receiver module, receiver, emitted expression, "
                    "target module, target"
                )
                raise ValueError(msg)
            return self

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
        relocation: Annotated[
            c.Infra.CodemodRelocation | None,
            m.Field(
                description=(
                    "Rope relocation that repairs the rule's findings over the "
                    "captured $NAME; absent for token-fix and plain detection rules"
                ),
            ),
        ] = None
        context: Annotated[
            t.VariadicTuple[FlextInfraModelsRefactorGrep.CodemodContextCondition],
            m.Field(
                description=(
                    "Project-context conditions a finding must satisfy; empty "
                    "when the syntactic match alone is the finding"
                ),
            ),
        ] = ()

        @m.model_validator(mode="after")
        def _validate_owned_path_rule(self) -> Self:
            """Require unconditional detection with a nonblank path diagnostic.

            Owned paths cannot depend on context, ownership, consumers, relocation,
            or module absence, and cannot declare an automated fix.

            Returns:
                The original unexempted rule.

            Raises:
                ValueError: If a path rule rewrites, exempts, or lacks a diagnostic.

            """
            if self.owned_path_suffix is not None and any((
                self.fixable,
                self.context,
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
            t.StrSequence,
            m.Field(description="Rule IDs elected from this provider"),
        ]
        fixable_rule_ids: Annotated[
            t.StrSequence,
            m.Field(description="Elected rule IDs that declare an automated fix"),
        ]

    class CodemodRulePlan(FlextInfraModelsBase.FrozenArbitrary):
        """Topologically composed dependency rules followed by the local delta."""

        provider_order: Annotated[
            t.StrSequence,
            m.Field(description="Dependency-first provider precedence"),
        ]
        rules: Annotated[
            t.VariadicTuple[FlextInfraModelsRefactorGrep.CodemodRule],
            m.Field(description="Unique semantic rules with their elected owner"),
        ]
        rulesets: Annotated[
            t.VariadicTuple[FlextInfraModelsRefactorGrep.CodemodRuleset],
            m.Field(description="Executable provider configs in precedence order"),
        ]
        project_rule_ids: Annotated[
            t.MappingKV[Path, t.StrSequence],
            m.Field(
                description="Absolute governed roots and their applicable rule IDs"
            ),
        ]

    class CodemodProjectFacts(m.ArbitraryTypesModel):
        """Project facts one admission pass reads, built from the current tree.

        A pass builds only the facts its rules' predicates ask for, so a
        project rewritten between passes is always read as it now is.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        own_package: Annotated[
            str | None,
            m.Field(
                description="Declared namespace when package predicates require it",
            ),
        ]
        predicates: Annotated[
            frozenset[c.Infra.CodemodContextPredicate],
            m.Field(description="Context predicates these facts were built for"),
        ]
        binding_rule_ids: Annotated[
            frozenset[str],
            m.Field(description="Elected rules requiring occurrence source proof"),
        ]
        binding_modules: Annotated[
            t.StrSequence,
            m.Field(description="Elected semantic owner modules"),
        ]
        import_graph: Annotated[
            t.MappingKV[str, frozenset[str]],
            m.Field(
                description="Runtime import edges of each project module",
            ),
        ]
        import_modules: Annotated[
            t.MappingKV[Path, str],
            m.Field(
                description="Module name of each project source file",
            ),
        ]
        import_cycles: Annotated[
            t.MappingKV[str, frozenset[str]],
            m.Field(
                description="Members of the runtime import cycle of each module",
            ),
        ]
        runtime_modules: Annotated[
            frozenset[str],
            m.Field(description="Import packages of the runtime dependency closure"),
        ]

    class CodemodAdmission(FlextInfraModelsBase.FrozenArbitrary):
        """One finding's admission inputs against its rule's project context."""

        root: Annotated[
            Path,
            m.Field(description="Project root the finding was scanned under"),
        ]
        rule: Annotated[
            FlextInfraModelsRefactorGrep.CodemodRule,
            m.Field(description="Elected rule whose project context is evaluated"),
        ]
        file_path: Annotated[
            Path,
            m.Field(description="Finding file path, absolute or root-relative"),
        ]
        captures: Annotated[
            t.JsonMapping,
            m.Field(description="Captured metavariables of the finding"),
        ]
        facts: Annotated[
            FlextInfraModelsRefactorGrep.CodemodProjectFacts,
            m.Field(description="Project snapshot built for the rule's predicates"),
        ]
        snapshot: Annotated[
            FlextInfraModelsCodemod.CodemodBindingSnapshot | None,
            m.Field(
                description=(
                    "Captured binding snapshot, required for binding predicates"
                ),
            ),
        ] = None

    class MethodOrderRule(m.ContractModel):
        """A declarative method ordering rule for class reconstruction.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict()

        category: Annotated[str | None, m.Field(description="Method category")] = None
        visibility: Annotated[str | None, m.Field(description="Visibility filter")] = (
            None
        )
        exclude_decorators: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Decorators excluded from the ordering rule",
        )
        decorators: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Decorators required by the ordering rule",
        )
        patterns: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Method name patterns included by the ordering rule",
        )
        order: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Expected method-category order for matching methods",
        )

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
        lint_tools: t.VariadicTuple[str] = m.Field(
            default_factory=tuple,
            description="Selected lint tools used for preview rendering",
        )
        automated_changes: t.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange
        ] = m.Field(
            default_factory=tuple,
            description="Automated rewrites captured for this file",
        )
        warnings: t.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange
        ] = m.Field(
            default_factory=tuple,
            description="Manual follow-up warnings for this file",
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
            t.MappingKV[str, t.StrSequence],
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
        lint_tools: t.VariadicTuple[str] = m.Field(
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
        files: t.VariadicTuple[FlextInfraModelsRefactorGrep.AccessorMigrationFile] = (
            m.Field(
                default_factory=tuple,
                description="Preview entries included in this report",
            )
        )


__all__ = ("FlextInfraModelsRefactorGrep",)
