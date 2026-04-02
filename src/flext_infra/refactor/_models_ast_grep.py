"""Ast-grep and MRO migration model mixins for refactor."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import AliasPath, ConfigDict, Field

from flext_core import FlextModels
from flext_infra import FlextInfraTypes as t


class FlextInfraRefactorAstGrepModels:
    """Mixin containing ast-grep and migration model contracts."""

    class AstGrepMatchEnvelope(FlextModels.ArbitraryTypesModel):
        """Compact ast-grep envelope carrying file, symbol and location."""

        model_config: ClassVar[ConfigDict] = ConfigDict(
            extra="ignore",
            populate_by_name=True,
        )

        file: Annotated[t.NonEmptyStr, Field(description="Matched file path")]
        symbol_name: Annotated[
            str | None,
            Field(
                default=None,
                validation_alias=AliasPath("metaVariables", "single", "NAME", "text"),
                description="Captured symbol name from ast-grep metadata",
            ),
        ]
        start_line: Annotated[
            int | None,
            Field(
                default=None,
                validation_alias=AliasPath("range", "start", "line"),
                description="Start line from ast-grep range",
            ),
        ]

    class MROSymbolCandidate(FlextModels.ArbitraryTypesModel):
        """Unified symbol candidate used by MRO scan and rewrites."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        symbol: Annotated[t.NonEmptyStr, Field(description="Symbol name")]
        line: Annotated[t.PositiveInt, Field(description="Source line number")]
        kind: Annotated[
            str,
            Field(default="constant", description="constant|typevar|typealias"),
        ] = "constant"
        class_name: Annotated[
            str,
            Field(default="", description="Target class name"),
        ] = ""
        facade_name: Annotated[
            str,
            Field(default="", description="Facade alias/import name"),
        ] = ""

    class MROImportRewrite(FlextModels.ArbitraryTypesModel):
        """Unified import rewrite payload for MRO reference updates."""

        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

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
        facade_name: Annotated[
            str,
            Field(default="", description="Facade alias/import name"),
        ] = ""

    class MROScanReport(FlextModels.ArbitraryTypesModel):
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
        candidates: Annotated[
            t.Infra.VariadicTuple[FlextInfraRefactorAstGrepModels.MROSymbolCandidate],
            Field(
                description="Module-level symbol candidates",
            ),
        ] = Field(default_factory=tuple)

    class MROFileMigration(FlextModels.ArbitraryTypesModel):
        """Migration summary for one transformed file."""

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, Field(description="Import module path")]
        moved_symbols: Annotated[
            t.Infra.VariadicTuple[str],
            Field(
                description="Symbols moved to facade class",
            ),
        ] = Field(default_factory=tuple)
        created_classes: Annotated[
            t.Infra.VariadicTuple[str],
            Field(
                description="Facade classes created during migration",
            ),
        ] = Field(default_factory=tuple)

    class MRORewriteResult(FlextModels.ArbitraryTypesModel):
        """Reference rewrite summary for one file."""

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        replacements: Annotated[
            int,
            Field(description="Reference replacements applied"),
        ]

    class MROMigrationReport(FlextModels.ArbitraryTypesModel):
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
        migrations: Annotated[
            t.Infra.VariadicTuple[FlextInfraRefactorAstGrepModels.MROFileMigration],
            Field(
                description="File migration summaries",
            ),
        ] = Field(default_factory=tuple)
        rewrites: Annotated[
            t.Infra.VariadicTuple[FlextInfraRefactorAstGrepModels.MRORewriteResult],
            Field(
                description="Reference rewrite summaries",
            ),
        ] = Field(default_factory=tuple)
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
        stash_ref: Annotated[
            str,
            Field(default="", description="Git stash rollback ref"),
        ]
        warnings: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Warnings"),
        ] = Field(default_factory=tuple)
        errors: Annotated[
            t.Infra.VariadicTuple[str],
            Field(description="Errors"),
        ] = Field(default_factory=tuple)

    class EngineConfig(FlextModels.FrozenStrictModel):
        model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

        project_scan_dirs: Annotated[
            t.StrSequence,
            Field(
                description="Relative directories scanned for candidate files",
            ),
        ] = Field(default_factory=lambda: ["src", "tests", "scripts", "examples"])
        ignore_patterns: Annotated[
            t.StrSequence,
            Field(
                description="Glob/file patterns ignored during scan",
            ),
        ] = Field(default_factory=list)
        file_extensions: Annotated[
            t.StrSequence,
            Field(
                description="Allowed file extensions (empty = all by pattern)",
            ),
        ] = Field(default_factory=list)

    class MethodOrderRule(FlextModels.FrozenStrictModel):
        """A declarative method ordering rule for class reconstruction."""

        model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

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
        exclude_decorators: Annotated[
            t.StrSequence,
            Field(
                description="Decorators to exclude",
            ),
        ] = Field(default_factory=list)
        decorators: Annotated[
            t.StrSequence,
            Field(
                description="Decorators to match",
            ),
        ] = Field(default_factory=list)
        patterns: Annotated[
            t.StrSequence,
            Field(
                description="Pattern rules",
            ),
        ] = Field(default_factory=list)
        order: Annotated[
            t.StrSequence,
            Field(
                description="Explicit method order",
            ),
        ] = Field(default_factory=list)

    class SignatureMigration(FlextModels.FrozenStrictModel):
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
        target_qualified_names: Annotated[
            t.StrSequence,
            Field(
                description="Qualified names to match",
            ),
        ] = Field(default_factory=list)
        target_simple_names: Annotated[
            t.StrSequence,
            Field(
                description="Simple names to match",
            ),
        ] = Field(default_factory=list)
        keyword_renames: Annotated[
            t.StrMapping,
            Field(
                description="Keyword rename mapping",
            ),
        ] = Field(default_factory=dict)
        remove_keywords: Annotated[
            t.StrSequence,
            Field(
                description="Keywords to remove",
            ),
        ] = Field(default_factory=list)
        add_keywords: Annotated[
            t.StrMapping,
            Field(
                description="Keywords to add",
            ),
        ] = Field(default_factory=dict)

    class ImportModernizerRuleConfig(FlextModels.FrozenStrictModel):
        """Configuration for a single import modernizer rule."""

        module: Annotated[
            str,
            Field(default="", description="Module path to modernize"),
        ]
        symbol_mapping: Annotated[
            t.StrMapping,
            Field(
                description="Symbol-to-alias mapping",
            ),
        ] = Field(default_factory=dict)


__all__ = ["FlextInfraRefactorAstGrepModels"]
