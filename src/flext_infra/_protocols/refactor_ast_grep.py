# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/refactor_ast_grep
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsRefactorAstGrep:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodemodRule(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def id(self) -> t.NonEmptyStr:
            """Canonical ast-grep rule ID."""
            ...

        @property
        def digest(self) -> t.NonEmptyStr:
            """SHA-256 of the canonical rule document."""
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Distribution or local rule provider."""
            ...

        @property
        def resource(self) -> Path:
            """Rule document resource containing this ID."""
            ...

        @property
        def fixable(self) -> bool:
            """Whether the rule declares an automated fix."""
            ...

        @property
        def owned_path_suffix(self) -> Literal[".pyi"] | None:
            """Owned path admission independent of syntax or content."""
            ...

        @property
        def message(self) -> str:
            """Canonical rule diagnostic."""
            ...

        @property
        def module_absence(self) -> bool:
            """Native predicate is exclusively absence at module root."""
            ...

        @property
        def expected(self) -> int | None:
            """Structural member projected from the owning model.

            Declared finding-count receipt from the rule's metadata; absent when the
            rule declares none.
            """
            ...

        @property
        def owner(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Canonical distribution name whose own plan drops the rule; absent when
            the rule applies to every project.
            """
            ...

        @property
        def consumers_of(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Canonical distribution name whose runtime consumers alone elect the
            rule; absent when the rule applies to every project.
            """
            ...

        @property
        def enforce(self) -> t.Infra.EnforcementIds:
            """Structural member projected from the owning model.

            Enforcement law ids the rule claims under its metadata; empty when the
            rule enforces no catalog law.
            """
            ...

        @property
        def disabled(self) -> bool:
            """Whether ast-grep's own severity switches it off."""
            ...

        @property
        def partitioned(self) -> bool:
            """Structural member projected from the owning model.

            Whether metadata.scope partitions the rule per file group: each
            project's generated provider renders it, so a plan never elects the
            authored document.
            """
            ...

        @property
        def partition_of(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Catalog rule this generated partition renders; retained for finding
            provenance, never selector aliasing.
            """
            ...

        @property
        def relocation(self) -> c.Infra.CodemodRelocation | None:
            """Structural member projected from the owning model.

            Rope relocation that repairs the rule's findings over the captured
            $NAME; absent for token-fix and plain detection rules.
            """
            ...

    @runtime_checkable
    class CodemodRuleset(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def provider(self) -> t.NonEmptyStr:
            """Distribution or local rule provider."""
            ...

        @property
        def config(self) -> Path:
            """Provider-owned ast-grep sgconfig path."""
            ...

        @property
        def rule_ids(self) -> Sequence[str]:
            """Rule IDs elected from this provider."""
            ...

        @property
        def fixable_rule_ids(self) -> Sequence[str]:
            """Elected rule IDs that declare an automated fix."""
            ...

    @runtime_checkable
    class CodemodRulePlan(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def provider_order(self) -> Sequence[str]:
            """Dependency-first provider precedence."""
            ...

        @property
        def rules(self) -> tuple[FlextInfraProtocolsRefactorAstGrep.CodemodRule, ...]:
            """Unique semantic rules with their elected owner."""
            ...

        @property
        def rulesets(
            self,
        ) -> tuple[FlextInfraProtocolsRefactorAstGrep.CodemodRuleset, ...]:
            """Executable provider configs in precedence order."""
            ...

        @property
        def project_rule_ids(self) -> Mapping[Path, Sequence[str]]:
            """Absolute governed roots and their applicable rule IDs."""
            ...

        @property
        def selected_rule_ids(self) -> tuple[str, ...] | None:
            """Structural member projected from the owning model.

            Exact focused selection; every other planned rule is a binding stage
            scanned only on the files the selection matches. None plans the complete
            catalog.
            """
            ...

    @runtime_checkable
    class CodemodPackageExportsFacts(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def exports(self) -> Mapping[str, t.StrTuple]:
            """Structural member projected from the owning model.

            Dotted package to the exact names its initializer __all__ declares, read
            statically.
            """
            ...

        @property
        def directories(self) -> Mapping[str, str]:
            """Structural member projected from the owning model.

            Dotted project package to its directory, relative to the project root in
            POSIX form; an installed provider package has none.
            """
            ...

        @property
        def modules(self) -> Mapping[str, t.StrTuple]:
            """Structural member projected from the owning model.

            Dotted package to the leaf names of its direct child modules and child
            packages, read from the source index.
            """
            ...

    @runtime_checkable
    class CodemodNativeGenerated(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def utilities(self) -> Mapping[str, t.JsonMapping]:
            """Generated utility documents keyed by utility id."""
            ...

        @property
        def rules(self) -> Mapping[str, t.JsonMapping]:
            """Generated rule documents keyed by rule id."""
            ...

        @property
        def scopes(self) -> Mapping[str, t.StrTuple]:
            """Structural member projected from the owning model.

            Project-relative file sets keyed by the scope selector a catalog rule
            names under metadata.scope.
            """
            ...

    @runtime_checkable
    class CodemodPrimitiveOwner(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def arg(self) -> tuple[str, str]:
            """The primitive's module and public expression."""
            ...

    @runtime_checkable
    class CodemodScopePartition(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def rule_id(self) -> t.NonEmptyStr:
            """Catalog rule declaring the partition."""
            ...

        @property
        def variable(self) -> t.NonEmptyStr:
            """Metavariable each copy constrains."""
            ...

        @property
        def holds(self) -> bool:
            """Whether a copy keeps (true) or ignores its group."""
            ...

        @property
        def selectors(self) -> t.NonEmptyStr:
            """Published file-scope selector prefix."""
            ...

        @property
        def pattern(self) -> t.NonEmptyStr:
            """Regex template instantiated with each key."""
            ...

        @property
        def keys(self) -> Mapping[str, str]:
            """Explicit key regexes; derived from scopes when empty."""
            ...

        @property
        def matching(self) -> bool:
            """False constrains each copy away from its key."""
            ...

    @runtime_checkable
    class CodemodScopeFacts(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scopes(self) -> Mapping[str, t.StrTuple]:
            """Project-relative file sets keyed by scope selector."""
            ...

    @runtime_checkable
    class AccessorMigrationRule(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_name(self) -> t.NonEmptyStr:
            """Canonical symbol name to replace."""
            ...

        @property
        def replacement_name(self) -> t.NonEmptyStr:
            """Canonical symbol name used as replacement."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Human-readable explanation for the rename."""
            ...

        @property
        def origin(self) -> str:
            """Canonical API origin this rewrite is tied to."""
            ...

        @property
        def operation(self) -> Literal["rename", "normalize-field"]:
            """Transformation applied to proven owned references."""
            ...

        @property
        def declaring_class(self) -> t.NonEmptyStr | None:
            """Qualified class that declares the accessor and field."""
            ...

        @property
        def field(self) -> t.NonEmptyStr | None:
            """Backing field passed to the public normalizer."""
            ...

    @runtime_checkable
    class AccessorMigrationChange(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> t.NonEmptyStr:
            """Absolute file path."""
            ...

        @property
        def line(self) -> t.NonNegativeInt:
            """1-based source line number when available."""
            ...

        @property
        def original_name(self) -> t.NonEmptyStr:
            """Original accessor or helper name."""
            ...

        @property
        def replacement_name(self) -> str:
            """Suggested or applied replacement name."""
            ...

        @property
        def automated(self) -> bool:
            """Whether the migration was performed automatically."""
            ...

        @property
        def reason(self) -> str:
            """Human-readable migration rationale."""
            ...

    @runtime_checkable
    class AccessorMigrationFile(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> t.NonEmptyStr:
            """Absolute file path."""
            ...

        @property
        def lint_tools(self) -> tuple[str, ...]:
            """Selected lint tools used for preview rendering."""
            ...

        @property
        def automated_changes(
            self,
        ) -> tuple[FlextInfraProtocolsRefactorAstGrep.AccessorMigrationChange, ...]:
            """Automated rewrites captured for this file."""
            ...

        @property
        def warnings(
            self,
        ) -> tuple[FlextInfraProtocolsRefactorAstGrep.AccessorMigrationChange, ...]:
            """Manual follow-up warnings for this file."""
            ...

        @property
        def diff(self) -> str:
            """Unified diff preview for the file."""
            ...

        @property
        def lint_before(
            self,
        ) -> t.Infra.LintSnapshot[FlextInfraProtocolsBase.LintGateResult]:
            """Lint output before the proposed rewrite."""
            ...

        @property
        def lint_after(
            self,
        ) -> t.Infra.LintSnapshot[FlextInfraProtocolsBase.LintGateResult]:
            """Lint output after the proposed rewrite."""
            ...

        @property
        def new_lint_errors(self) -> Mapping[str, Sequence[str]]:
            """Lint errors introduced by the proposed rewrite."""
            ...

    @runtime_checkable
    class AccessorMigrationReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace(self) -> t.NonEmptyStr:
            """Repository root path."""
            ...

        @property
        def dry_run(self) -> bool:
            """Dry-run indicator."""
            ...

        @property
        def files_scanned(self) -> t.NonNegativeInt:
            """Total Python files scanned."""
            ...

        @property
        def files_with_changes(self) -> t.NonNegativeInt:
            """Files with automated rewrites."""
            ...

        @property
        def automated_change_count(self) -> t.NonNegativeInt:
            """Total automated rewrites detected."""
            ...

        @property
        def warning_count(self) -> t.NonNegativeInt:
            """Total manual follow-up warnings detected."""
            ...

        @property
        def lint_tools(self) -> tuple[str, ...]:
            """Canonical lint tool list used by this run."""
            ...

        @property
        def lint_before_totals(self) -> t.IntMapping:
            """Per-tool count of lint lines before rewrites."""
            ...

        @property
        def lint_after_totals(self) -> t.IntMapping:
            """Per-tool count of lint lines after rewrites."""
            ...

        @property
        def new_lint_error_totals(self) -> t.IntMapping:
            """Per-tool count of newly introduced lint lines."""
            ...

        @property
        def files(
            self,
        ) -> tuple[FlextInfraProtocolsRefactorAstGrep.AccessorMigrationFile, ...]:
            """Preview entries included in this report."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsRefactorAstGrep",
]
