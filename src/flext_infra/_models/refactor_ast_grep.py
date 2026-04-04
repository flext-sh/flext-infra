"""Ast-grep and MRO migration model mixins for refactor."""

from __future__ import annotations

from typing import Annotated, ClassVar

from pydantic import AliasPath, ConfigDict, Field

from flext_core import FlextModels
from flext_infra import FlextInfraConstants as c, FlextInfraTypes as t


class FlextInfraRefactorGrepModels:
    """Mixin containing ast-grep and migration model contracts."""

    class GrepMatchEnvelope(FlextModels.ArbitraryTypesModel):
        """Compact ast-grep envelope carrying file, symbol and location."""

        model_config: ClassVar[ConfigDict] = ConfigDict(
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
        candidates: t.Infra.VariadicTuple[
            FlextInfraRefactorGrepModels.MROSymbolCandidate
        ] = Field(default_factory=tuple, description="Module-level symbol candidates")

    class MROFileMigration(FlextModels.ArbitraryTypesModel):
        """Migration summary for one transformed file."""

        file: Annotated[t.NonEmptyStr, Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, Field(description="Import module path")]
        moved_symbols: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Symbols moved to facade class"
        )
        created_classes: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Facade classes created during migration"
        )

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
        migrations: t.Infra.VariadicTuple[
            FlextInfraRefactorGrepModels.MROFileMigration
        ] = Field(default_factory=tuple, description="File migration summaries")
        rewrites: t.Infra.VariadicTuple[
            FlextInfraRefactorGrepModels.MRORewriteResult
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
        stash_ref: Annotated[
            str,
            Field(default="", description="Git stash rollback ref"),
        ]
        warnings: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Warnings"
        )
        errors: t.Infra.VariadicTuple[str] = Field(
            default_factory=tuple, description="Errors"
        )

    class EngineConfig(FlextModels.ContractModel):
        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        project_scan_dirs: t.StrSequence = Field(
            default_factory=lambda: [
                c.Infra.Paths.DEFAULT_SRC_DIR,
                c.Infra.Directories.TESTS,
                c.Infra.Directories.SCRIPTS,
                c.Infra.Directories.EXAMPLES,
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

    class MethodOrderRule(FlextModels.ContractModel):
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

    class SignatureMigration(FlextModels.ContractModel):
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

    class ImportModernizerRuleConfig(FlextModels.ContractModel):
        """Configuration for a single import modernizer rule."""

        module: Annotated[
            str,
            Field(default="", description="Module path to modernize"),
        ]
        symbol_mapping: t.StrMapping = Field(
            default_factory=dict, description="Symbol-to-alias mapping"
        )


__all__ = ["FlextInfraRefactorGrepModels"]
