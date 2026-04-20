"""Refactor migration model mixins for rope-oriented orchestration."""

from __future__ import annotations

from collections.abc import (
    Mapping,
)
from types import MappingProxyType
from typing import Annotated, ClassVar

from flext_core import m

from flext_infra import FlextInfraModelsMixins, c, t


class FlextInfraModelsRefactorGrep:
    """Mixin containing migration/reporting contracts for refactor orchestration."""

    class MROSymbolCandidate(
        m.ArbitraryTypesModel,
    ):
        """Unified symbol candidate used by MRO scan and rewrites."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        facade_name: Annotated[str, m.Field(description="Facade alias/import name")] = (
            ""
        )
        symbol: Annotated[t.NonEmptyStr, m.Field(description="Symbol name")]
        line: Annotated[t.PositiveInt, m.Field(description="Source line number")]
        end_line: Annotated[
            int | None,
            m.Field(
                description="Inclusive end line for multi-line declarations",
            ),
        ] = None
        kind: Annotated[str, m.Field(description="constant|typevar|typealias")] = (
            "constant"
        )
        class_name: Annotated[str, m.Field(description="Target class name")] = ""

    class MROImportRewrite(
        m.ArbitraryTypesModel,
    ):
        """Unified import rewrite payload for MRO reference updates."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        facade_name: Annotated[str, m.Field(description="Facade alias/import name")] = (
            ""
        )
        module: Annotated[t.NonEmptyStr, m.Field(description="Import module path")]
        import_name: Annotated[
            str,
            m.Field(description="Imported symbol name"),
        ]
        as_name: Annotated[str | None, m.Field(description="Optional alias")] = None
        symbol: Annotated[str, m.Field(description="Resolved symbol in facade")] = ""

    class MROScanReport(m.ArbitraryTypesModel):
        """Scan result for one constants module candidate file."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, m.Field(description="Import module path")]
        constants_class: Annotated[
            str,
            m.Field(
                description="First constants class name",
            ),
        ] = ""
        facade_alias: Annotated[str, m.Field(description="Facade alias letter")] = "c"
        candidates: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.MROSymbolCandidate
        ] = m.Field(default_factory=tuple, description="Module-level symbol candidates")

    class MROFileMigration(m.ArbitraryTypesModel):
        """Migration summary for one transformed file."""

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, m.Field(description="Import module path")]
        moved_symbols: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple, description="Symbols moved to facade class"
        )
        created_classes: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple, description="Facade classes created during migration"
        )

    class MRORewriteResult(m.ArbitraryTypesModel):
        """Reference rewrite summary for one file."""

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        replacements: Annotated[
            int,
            m.Field(description="Reference replacements applied"),
        ]

    class MROMigrationReport(
        FlextInfraModelsMixins.StashRefMixin,
        m.ArbitraryTypesModel,
    ):
        """End-to-end report for migrate-to-mro command execution."""

        workspace: Annotated[
            str,
            m.Field(description="Workspace root path"),
        ]
        target: Annotated[t.NonEmptyStr, m.Field(description="constants|typings|all")]
        selected_projects: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple,
            description="Project scope used for the run; empty means whole workspace",
        )
        dry_run: Annotated[bool, m.Field(description="Dry-run indicator")]
        validation_mode: Annotated[
            str,
            m.Field(
                description="Validation strategy used for remaining violation counts",
            ),
        ] = "post-apply-rescan"
        files_scanned: Annotated[
            int,
            m.Field(description="Total scanned Python files"),
        ]
        files_with_candidates: Annotated[
            int,
            m.Field(
                ge=0,
                description="Files containing movable declarations",
            ),
        ]
        migrations: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.MROFileMigration
        ] = m.Field(default_factory=tuple, description="File migration summaries")
        rewrites: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.MRORewriteResult
        ] = m.Field(default_factory=tuple, description="Reference rewrite summaries")
        remaining_violations: Annotated[
            int,
            m.Field(
                ge=0,
                description="Loose declarations remaining after run",
            ),
        ]
        mro_failures: Annotated[
            t.NonNegativeInt,
            m.Field(description="MRO validation failures"),
        ]
        scan_duration_seconds: Annotated[
            float, m.Field(ge=0.0, description="Scan phase duration in seconds")
        ] = 0.0
        rewrite_duration_seconds: Annotated[
            float,
            m.Field(
                ge=0.0,
                description="Rewrite phase duration in seconds",
            ),
        ] = 0.0
        validation_duration_seconds: Annotated[
            float,
            m.Field(
                ge=0.0,
                description="Validation phase duration in seconds",
            ),
        ] = 0.0
        total_duration_seconds: Annotated[
            float, m.Field(ge=0.0, description="Total run duration in seconds")
        ] = 0.0
        warnings: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple, description="Warnings"
        )
        errors: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple, description="Errors"
        )

    class EngineConfig(m.ContractModel):
        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        project_scan_dirs: t.StrSequence = m.Field(
            default_factory=lambda: [
                c.Infra.DEFAULT_SRC_DIR,
                c.Infra.DIR_TESTS,
                c.Infra.DIR_SCRIPTS,
                c.Infra.DIR_EXAMPLES,
            ],
            description="Relative directories scanned for candidate files",
        )
        ignore_patterns: t.StrSequence = m.Field(
            default_factory=tuple, description="Glob/file patterns ignored during scan"
        )
        file_extensions: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Allowed file extensions (empty = all by pattern)",
        )

    class MethodOrderRule(m.ContractModel):
        """A declarative method ordering rule for class reconstruction.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        _flext_enforcement_exempt: ClassVar[bool] = True

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict()

        category: Annotated[str | None, m.Field(description="Method category")] = None
        visibility: Annotated[
            str | None,
            m.Field(
                description="Visibility filter",
            ),
        ] = None
        exclude_decorators: t.StrSequence = m.Field(default_factory=tuple)
        decorators: t.StrSequence = m.Field(default_factory=tuple)
        patterns: t.StrSequence = m.Field(default_factory=tuple)
        order: t.StrSequence = m.Field(default_factory=tuple)

    class SignatureMigration(m.ContractModel):
        """Declarative signature migration rule for callsite propagation.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        _flext_enforcement_exempt: ClassVar[bool] = True

        id: Annotated[str, m.Field(description="Migration ID")] = "signature-migration"
        enabled: Annotated[
            bool,
            m.Field(
                description="Whether migration is active",
            ),
        ] = True
        target_qualified_names: t.StrSequence = m.Field(default_factory=tuple)
        target_simple_names: t.StrSequence = m.Field(default_factory=tuple)
        keyword_renames: t.StrMapping = m.Field(
            default_factory=lambda: MappingProxyType({}),
            description="Keyword rename mapping",
        )
        remove_keywords: t.StrSequence = m.Field(default_factory=tuple)
        add_keywords: t.StrMapping = m.Field(
            default_factory=lambda: MappingProxyType({}),
            description="Keywords to add",
        )

    class ImportModernizerRuleConfig(m.ContractModel):
        """Configuration for a single import modernizer rule.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        _flext_enforcement_exempt: ClassVar[bool] = True

        module: Annotated[str, m.Field(description="Module path to modernize")] = ""
        symbol_mapping: t.StrMapping = m.Field(
            default_factory=lambda: MappingProxyType({}),
            description="Symbol-to-alias mapping",
        )

    class AccessorMigrationRule(m.ContractModel):
        """Declarative symbol-rename rule for accessor migration."""

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
            m.Field(
                description="Canonical API origin this rewrite is tied to",
            ),
        ] = ""

    class AccessorMigrationChange(m.ArbitraryTypesModel):
        """Single automated rename or manual warning emitted by accessor migration."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

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
            str, m.Field(description="Suggested or applied replacement name")
        ] = ""
        automated: Annotated[
            bool,
            m.Field(description="Whether the migration was performed automatically"),
        ]
        reason: Annotated[
            str, m.Field(description="Human-readable migration rationale")
        ]

    class AccessorMigrationFile(m.ArbitraryTypesModel):
        """Per-file preview for accessor migration dry-runs and applies.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        _flext_enforcement_exempt: ClassVar[bool] = True

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        lint_tools: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple,
            description="Selected lint tools used for preview rendering",
        )
        automated_changes: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange
        ] = m.Field(
            default_factory=tuple,
            description="Automated rewrites captured for this file",
        )
        warnings: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange
        ] = m.Field(
            default_factory=tuple,
            description="Manual follow-up warnings for this file",
        )
        diff: Annotated[
            str, m.Field(description="Unified diff preview for the file")
        ] = ""
        lint_before: Annotated[
            Mapping[str, t.StrSequence],
            m.Field(description="Lint output before the proposed rewrite"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))
        lint_after: Annotated[
            Mapping[str, t.StrSequence],
            m.Field(description="Lint output after the proposed rewrite"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))
        new_lint_errors: Annotated[
            Mapping[str, t.StrSequence],
            m.Field(description="Lint errors introduced by the proposed rewrite"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))

    class AccessorMigrationReport(m.ArbitraryTypesModel):
        """Workspace-scale report for accessor migration orchestration.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        _flext_enforcement_exempt: ClassVar[bool] = True

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        workspace: Annotated[t.NonEmptyStr, m.Field(description="Workspace root path")]
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
        lint_tools: t.Infra.VariadicTuple[str] = m.Field(
            default_factory=tuple,
            description="Canonical lint tool list used by this run",
        )
        lint_before_totals: Annotated[
            Mapping[str, int],
            m.Field(description="Per-tool count of lint lines before rewrites"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))
        lint_after_totals: Annotated[
            Mapping[str, int],
            m.Field(description="Per-tool count of lint lines after rewrites"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))
        new_lint_error_totals: Annotated[
            Mapping[str, int],
            m.Field(description="Per-tool count of newly introduced lint lines"),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))
        files: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationFile
        ] = m.Field(
            default_factory=tuple,
            description="Preview entries included in this report",
        )


__all__: list[str] = ["FlextInfraModelsRefactorGrep"]
