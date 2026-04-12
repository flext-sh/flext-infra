"""Refactor migration model mixins for rope-oriented orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from flext_core import m
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsRefactorGrep:
    """Mixin containing migration/reporting contracts for refactor orchestration."""

    class MROSymbolCandidate(
        m.ArbitraryTypesModel,
    ):
        """Unified symbol candidate used by MRO scan and rewrites."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        facade_name: Annotated[
            str,
            Field(default="", description="Facade alias/import name"),
        ] = ""
        symbol: Annotated[t.NonEmptyStr, Field(description="Symbol name")]
        line: Annotated[t.PositiveInt, Field(description="Source line number")]
        end_line: Annotated[
            int | None,
            Field(
                default=None,
                description="Inclusive end line for multi-line declarations",
            ),
        ] = None
        kind: Annotated[
            str,
            Field(default="constant", description="constant|typevar|typealias"),
        ] = "constant"
        class_name: Annotated[
            str,
            Field(default="", description="Target class name"),
        ] = ""

    class MROImportRewrite(
        m.ArbitraryTypesModel,
    ):
        """Unified import rewrite payload for MRO reference updates."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        facade_name: Annotated[
            str,
            Field(default="", description="Facade alias/import name"),
        ] = ""
        module: Annotated[t.NonEmptyStr, Field(description="Import module path")]
        import_name: Annotated[
            str,
            Field(description="Imported symbol name"),
        ]
        as_name: Annotated[
            str | None,
            Field(default=None, description="Optional alias"),
        ] = None
        symbol: Annotated[
            str,
            Field(default="", description="Resolved symbol in facade"),
        ] = ""

    class MROScanReport(m.ArbitraryTypesModel):
        """Scan result for one constants module candidate file."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, Field(description="Import module path")]
        constants_class: Annotated[
            str,
            Field(
                default="",
                description="First constants class name",
            ),
        ] = ""
        facade_alias: Annotated[
            str,
            Field(default="c", description="Facade alias letter"),
        ] = "c"
        candidates: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.MROSymbolCandidate
        ] = Field(default_factory=tuple, description="Module-level symbol candidates")

    class MROFileMigration(m.ArbitraryTypesModel):
        """Migration summary for one transformed file."""

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, Field(description="Import module path")]
        moved_symbols: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Symbols moved to facade class"
        )
        created_classes: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Facade classes created during migration"
        )

    class MRORewriteResult(m.ArbitraryTypesModel):
        """Reference rewrite summary for one file."""

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        replacements: Annotated[
            int,
            Field(description="Reference replacements applied"),
        ]

    class MROMigrationReport(
        FlextInfraModelsMixins.StashRefMixin,
        m.ArbitraryTypesModel,
    ):
        """End-to-end report for migrate-to-mro command execution."""

        workspace: Annotated[
            str,
            Field(description="Workspace root path"),
        ]
        target: Annotated[t.NonEmptyStr, Field(description="constants|typings|all")]
        dry_run: Annotated[bool, Field(description="Dry-run indicator")]
        files_scanned: Annotated[
            int,
            Field(description="Total scanned Python files"),
        ]
        files_with_candidates: Annotated[
            int,
            Field(
                ge=0,
                description="Files containing movable declarations",
            ),
        ]
        migrations: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.MROFileMigration
        ] = Field(default_factory=tuple, description="File migration summaries")
        rewrites: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.MRORewriteResult
        ] = Field(default_factory=tuple, description="Reference rewrite summaries")
        remaining_violations: Annotated[
            int,
            Field(
                ge=0,
                description="Loose declarations remaining after run",
            ),
        ]
        mro_failures: Annotated[
            t.NonNegativeInt,
            Field(description="MRO validation failures"),
        ]
        warnings: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Warnings"
        )
        errors: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Errors"
        )

    class EngineConfig(m.ContractModel):
        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        project_scan_dirs: t.StrSequence = Field(
            default_factory=lambda: [
                c.Infra.DEFAULT_SRC_DIR,
                c.Infra.DIR_TESTS,
                c.Infra.DIR_SCRIPTS,
                c.Infra.DIR_EXAMPLES,
            ],
            description="Relative directories scanned for candidate files",
        )
        ignore_patterns: t.StrSequence = Field(
            default_factory=list, description="Glob/file patterns ignored during scan"
        )
        file_extensions: t.StrSequence = Field(
            default_factory=list,
            description="Allowed file extensions (empty = all by pattern)",
        )

    class MethodOrderRule(m.ContractModel):
        """A declarative method ordering rule for class reconstruction."""

        model_config: ClassVar[ConfigDict] = ConfigDict()

        category: Annotated[
            str | None,
            Field(default=None, description="Method category"),
        ]
        visibility: Annotated[
            str | None,
            Field(
                default=None,
                description="Visibility filter",
            ),
        ]
        exclude_decorators: t.StrSequence = Field(
            default_factory=list, description="Decorators to exclude"
        )
        decorators: t.StrSequence = Field(
            default_factory=list, description="Decorators to match"
        )
        patterns: t.StrSequence = Field(
            default_factory=list, description="Pattern rules"
        )
        order: t.StrSequence = Field(
            default_factory=list, description="Explicit method order"
        )

    class SignatureMigration(m.ContractModel):
        """Declarative signature migration rule for callsite propagation."""

        id: Annotated[
            str,
            Field(default="signature-migration", description="Migration ID"),
        ]
        enabled: Annotated[
            bool,
            Field(
                default=True,
                description="Whether migration is active",
            ),
        ]
        target_qualified_names: t.StrSequence = Field(
            default_factory=list, description="Qualified names to match"
        )
        target_simple_names: t.StrSequence = Field(
            default_factory=list, description="Simple names to match"
        )
        keyword_renames: t.StrMapping = Field(
            default_factory=dict, description="Keyword rename mapping"
        )
        remove_keywords: t.StrSequence = Field(
            default_factory=list, description="Keywords to remove"
        )
        add_keywords: t.StrMapping = Field(
            default_factory=dict, description="Keywords to add"
        )

    class ImportModernizerRuleConfig(m.ContractModel):
        """Configuration for a single import modernizer rule."""

        module: Annotated[
            str,
            Field(default="", description="Module path to modernize"),
        ]
        symbol_mapping: t.StrMapping = Field(
            default_factory=dict, description="Symbol-to-alias mapping"
        )

    class AccessorMigrationRule(m.ContractModel):
        """Declarative symbol-rename rule for accessor migration."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        source_name: Annotated[
            t.NonEmptyStr,
            Field(description="Canonical symbol name to replace"),
        ]
        replacement_name: Annotated[
            t.NonEmptyStr,
            Field(description="Canonical symbol name used as replacement"),
        ]
        reason: Annotated[
            t.NonEmptyStr,
            Field(description="Human-readable explanation for the rename"),
        ]
        origin: Annotated[
            str,
            Field(
                default="",
                description="Canonical API origin this rewrite is tied to",
            ),
        ] = ""

    class AccessorMigrationChange(m.ArbitraryTypesModel):
        """Single automated rename or manual warning emitted by accessor migration."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        line: Annotated[
            t.NonNegativeInt,
            Field(description="1-based source line number when available"),
        ]
        original_name: Annotated[
            t.NonEmptyStr,
            Field(description="Original accessor or helper name"),
        ]
        replacement_name: Annotated[
            str,
            Field(default="", description="Suggested or applied replacement name"),
        ] = ""
        automated: Annotated[
            bool,
            Field(description="Whether the migration was performed automatically"),
        ]
        reason: Annotated[str, Field(description="Human-readable migration rationale")]

    class AccessorMigrationFile(m.ArbitraryTypesModel):
        """Per-file preview for accessor migration dry-runs and applies."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        lint_tools: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple,
            description="Selected lint tools used for preview rendering",
        )
        automated_changes: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange
        ] = Field(
            default_factory=tuple,
            description="Automated rewrites captured for this file",
        )
        warnings: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationChange
        ] = Field(
            default_factory=tuple,
            description="Manual follow-up warnings for this file",
        )
        diff: Annotated[
            str,
            Field(default="", description="Unified diff preview for the file"),
        ] = ""
        lint_before: Annotated[
            Mapping[str, t.StrSequence],
            Field(description="Lint output before the proposed rewrite"),
        ] = Field(default_factory=dict)
        lint_after: Annotated[
            Mapping[str, t.StrSequence],
            Field(description="Lint output after the proposed rewrite"),
        ] = Field(default_factory=dict)
        new_lint_errors: Annotated[
            Mapping[str, t.StrSequence],
            Field(description="Lint errors introduced by the proposed rewrite"),
        ] = Field(default_factory=dict)

    class AccessorMigrationReport(m.ArbitraryTypesModel):
        """Workspace-scale report for accessor migration orchestration."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        workspace: Annotated[t.NonEmptyStr, Field(description="Workspace root path")]
        dry_run: Annotated[bool, Field(description="Dry-run indicator")]
        files_scanned: Annotated[
            t.NonNegativeInt,
            Field(description="Total Python files scanned"),
        ]
        files_with_changes: Annotated[
            t.NonNegativeInt,
            Field(description="Files with automated rewrites"),
        ]
        automated_change_count: Annotated[
            t.NonNegativeInt,
            Field(description="Total automated rewrites detected"),
        ]
        warning_count: Annotated[
            t.NonNegativeInt,
            Field(description="Total manual follow-up warnings detected"),
        ]
        lint_tools: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple,
            description="Canonical lint tool list used by this run",
        )
        lint_before_totals: Annotated[
            Mapping[str, int],
            Field(description="Per-tool count of lint lines before rewrites"),
        ] = Field(default_factory=dict)
        lint_after_totals: Annotated[
            Mapping[str, int],
            Field(description="Per-tool count of lint lines after rewrites"),
        ] = Field(default_factory=dict)
        new_lint_error_totals: Annotated[
            Mapping[str, int],
            Field(description="Per-tool count of newly introduced lint lines"),
        ] = Field(default_factory=dict)
        files: t.Infra.VariadicTuple[
            FlextInfraModelsRefactorGrep.AccessorMigrationFile
        ] = Field(
            default_factory=tuple,
            description="Preview entries included in this report",
        )


__all__: list[str] = ["FlextInfraModelsRefactorGrep"]
