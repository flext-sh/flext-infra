"""Domain models for the codegen subpackage."""

from __future__ import annotations

from collections.abc import MutableSequence, MutableSet, Sequence
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import u
from flext_core import m
from flext_infra import (
    FlextInfraModelsMixins,
    p,
    t,
)


class FlextInfraModelsCodegen:
    """Models for codegen census, scaffold, and auto-fix pipelines."""

    class CensusViolation(
        FlextInfraModelsMixins.RequiredNonNegativeLineMixin,
        m.ArbitraryTypesModel,
    ):
        """A single namespace violation detected by the census service."""

        module: t.NonEmptyStr = m.Field(description="Module file path")
        rule: t.NonEmptyStr = m.Field(
            description="Violated rule identifier (e.g. NS-001)"
        )
        message: t.NonEmptyStr = m.Field(description="Human-readable violation message")
        fixable: bool = m.Field(description="Whether this violation can be auto-fixed")

    class CensusReport(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Aggregated census report for a single project."""

        @staticmethod
        def _violations_default() -> list[FlextInfraModelsCodegen.CensusViolation]:
            return []

        violations: Annotated[
            list[FlextInfraModelsCodegen.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="Detected violations",
            ),
        ]
        total: Annotated[t.NonNegativeInt, m.Field(description="Total violation count")]
        fixable: Annotated[
            t.NonNegativeInt,
            m.Field(description="Count of auto-fixable violations"),
        ]

    class ScaffoldResult(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Result of scaffolding base modules for a project."""

        files_created: t.StrSequence = m.Field(
            default_factory=list,
            description="Newly created file paths",
        )
        files_skipped: t.StrSequence = m.Field(
            default_factory=list,
            description="Skipped (already existing) file paths",
        )

    class AutoFixResult(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Result of auto-fixing namespace violations for a project."""

        @staticmethod
        def _violations_default() -> list[FlextInfraModelsCodegen.CensusViolation]:
            return []

        violations_fixed: Annotated[
            list[FlextInfraModelsCodegen.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="Fixed violations",
            ),
        ]
        violations_skipped: Annotated[
            list[FlextInfraModelsCodegen.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="Skipped violations (not auto-fixable)",
            ),
        ]
        files_modified: t.StrSequence = m.Field(
            default_factory=list,
            description="Modified file paths",
        )

    class NamespaceModulePolicy(m.ArbitraryTypesModel):
        """Derived gen-init policy for one governed module."""

        enforce_contract: Annotated[
            bool,
            m.Field(
                description="Whether gen-init must enforce namespace shape.",
            ),
        ] = False
        export_symbols: Annotated[
            bool,
            m.Field(
                description="Whether gen-init should discover public symbols.",
            ),
        ] = False
        include_in_lazy_init: Annotated[
            bool,
            m.Field(
                description="Whether lazy-init should index this module at all.",
            ),
        ] = True
        project_prefix: Annotated[
            str,
            m.Field(
                description="Canonical class prefix expected for the module.",
            ),
        ] = ""
        expected_alias: Annotated[
            str | None,
            m.Field(
                description="Canonical module-level alias allowed for the file.",
            ),
        ] = None
        expected_family: Annotated[
            str | None,
            m.Field(
                description="Canonical namespace family suffix for the file.",
            ),
        ] = None
        family_tokens: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Accepted family markers for private namespace modules.",
        )
        accepted_suffixes: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Accepted class suffixes for governed facade classes.",
        )
        allow_main_export: Annotated[
            bool,
            m.Field(
                description="Whether the file may export a module-level main().",
            ),
        ] = False
        allow_type_alias: Annotated[
            bool,
            m.Field(
                description="Whether the module may keep TypeAlias declarations.",
            ),
        ] = False
        is_fixture_module: Annotated[
            bool,
            m.Field(
                description="Whether the module belongs to a private fixtures package.",
            ),
        ] = False
        type_checking_imports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Canonical root names allowed inside TYPE_CHECKING imports.",
        )

    class LazyInitPackageContext(m.ArbitraryTypesModel):
        """Declarative package context for one lazy-init directory."""

        pkg_dir: Path = m.Field(description="Directory being processed.")
        init_path: Path = m.Field(description="Target __init__.py path.")
        current_pkg: str = m.Field(description="Importable package name.")
        surface: str = m.Field(description="Root surface for alias inheritance.")
        generated_init: Annotated[
            bool,
            m.Field(
                description="Whether the current __init__.py is generated by lazy-init.",
            ),
        ] = False
        importable: Annotated[
            bool,
            m.Field(
                description="Whether the directory resolves to an importable package.",
            ),
        ] = False

    class LazyInitPlan(m.ArbitraryTypesModel):
        """Fully resolved lazy-init action and render payload."""

        context: FlextInfraModelsCodegen.LazyInitPackageContext = m.Field(
            description="Discovered package context.",
        )
        action: Annotated[
            t.Infra.LazyInitAction,
            m.Field(
                description="Action selected for this package.",
            ),
        ] = "skip"
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Public exports for generated __init__.py.",
        )
        lazy_map: t.Infra.LazyImportMap = m.Field(
            default_factory=dict,
            description="Lazy import map: export name to module/attribute target.",
        )
        inline_constants: t.StrMapping = m.Field(
            default_factory=dict,
            description="Inline constants emitted directly into __init__.py.",
        )
        wildcard_runtime_modules: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Runtime wildcard import modules.",
        )
        child_packages_for_lazy: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Direct child package imports merged at runtime.",
        )
        child_packages_for_tc: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Descendant package imports available for type checking.",
        )

    class QualityGateCheck(m.ArbitraryTypesModel):
        """A single quality gate check result entry."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Check identifier")]
        passed: Annotated[bool, m.Field(description="Whether check passed")]
        detail: Annotated[str, m.Field(description="Human-readable check detail")] = ""
        critical: Annotated[bool, m.Field(description="Whether failure is critical")]

    class QualityGateProjectFinding(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Per-project quality gate findings."""

        violations_total: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total violations"),
        ]
        fixable_violations: Annotated[
            t.NonNegativeInt,
            m.Field(description="Auto-fixable violations"),
        ]
        validator_passed: Annotated[
            bool, m.Field(description="Whether validator passed")
        ]
        mro_failures: Annotated[
            t.NonNegativeInt,
            m.Field(description="MRO failure count"),
        ]
        layer_violations: Annotated[
            t.NonNegativeInt,
            m.Field(description="Layer violation count"),
        ]
        cross_project_reference_violations: Annotated[
            t.NonNegativeInt,
            m.Field(description="Cross-project reference violation count"),
        ]

    class BulkFixItem(
        FlextInfraModelsMixins.AbsoluteFilePathTextMixin,
        FlextInfraModelsMixins.PositiveLineMixin,
        m.ArbitraryTypesModel,
    ):
        """Shared line-addressable item used by bulk codegen fixes."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Item identifier")]

    class ConstantDefinition(
        FlextInfraModelsMixins.ProjectNameMixin,
        FlextInfraModelsMixins.NestedClassPathMixin,
        BulkFixItem,
    ):
        """A single constant extracted from a constants.py file."""

        value_repr: Annotated[
            str,
            m.Field(description="Source repr (e.g., '30', '\"localhost\"')"),
        ]
        type_annotation: Annotated[
            str, m.Field(description="Type annotation string")
        ] = ""

    class DuplicateConstantGroup(m.ArbitraryTypesModel):
        """Cross-project duplicate group with consolidation metadata."""

        constant_name: t.NonEmptyStr = m.Field(description="Constant identifier")
        definitions: list[FlextInfraModelsCodegen.ConstantDefinition] = m.Field(
            description="Definitions across projects",
        )
        is_value_identical: bool = m.Field(description="Whether all values match")
        canonical_ref: Annotated[
            str, m.Field(description="Canonical parent reference")
        ] = ""

    class DirectConstantRef(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Direct FlextXConstants.Y.Z reference that should use c.* alias."""

        full_ref: Annotated[
            t.NonEmptyStr,
            m.Field(description="e.g., FlextAuthConstants.Auth.DEFAULT_TIMEOUT"),
        ]
        alias_ref: Annotated[
            t.NonEmptyStr,
            m.Field(description="e.g., c.Auth.DEFAULT_TIMEOUT"),
        ]
        file_path: Annotated[
            t.NonEmptyStr,
            m.Field(description="File containing the reference"),
        ]
        line: Annotated[t.PositiveInt, m.Field(description="Line number")]

    class CanonicalValueRule(m.ArbitraryTypesModel):
        value: t.Infra.CanonicalValue = m.Field(description="Canonical value")
        type: str = m.Field(description="Canonical type")
        canonical_ref: str = m.Field(description="Canonical reference")
        semantic_names: t.StrSequence = m.Field(
            default_factory=list, description="semantic_names"
        )

    class NsRule(m.ArbitraryTypesModel):
        id: str = m.Field(description="Rule ID")
        description: str = m.Field(description="Rule description")
        fixable: bool = m.Field(description="Whether the rule is fixable")
        fixable_exclusion: Annotated[
            str | None, m.Field(description="Fixable exclusion reason")
        ] = None

    class ConstantsGovernanceConfig(m.ArbitraryTypesModel):
        version: str = m.Field(description="Config version")
        rules: list[FlextInfraModelsCodegen.NsRule] = m.Field(
            description="Governance rules"
        )
        canonical_values: list[FlextInfraModelsCodegen.CanonicalValueRule] = m.Field(
            description="Canonical values settings"
        )
        constants_class_pattern: str = m.Field(
            description="Constants class pattern regex"
        )

    class FixContext(m.ArbitraryTypesModel):
        """Mutable accumulation context for fix operations."""

        @staticmethod
        def _violations_default() -> list[FlextInfraModelsCodegen.CensusViolation]:
            return []

        violations_fixed: Annotated[
            MutableSequence[FlextInfraModelsCodegen.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="List of violations that were fixed",
            ),
        ]
        violations_skipped: Annotated[
            MutableSequence[FlextInfraModelsCodegen.CensusViolation],
            m.Field(
                default_factory=_violations_default,
                description="List of violations that were skipped",
            ),
        ]
        files_modified: Annotated[
            MutableSet[str],
            m.Field(
                default_factory=set,
                description="Set of unique modified file paths",
            ),
        ]

        def skip(self, *, module: str, rule: str, line: int, message: str) -> None:
            self.violations_skipped.append(
                FlextInfraModelsCodegen.CensusViolation(
                    module=module, rule=rule, line=line, message=message, fixable=False
                ),
            )

        def fix(self, *, module: str, rule: str, line: int, message: str) -> None:
            self.violations_fixed.append(
                FlextInfraModelsCodegen.CensusViolation(
                    module=module, rule=rule, line=line, message=message, fixable=True
                ),
            )

    class ViolationKey(m.ContractModel):
        """Content-stable violation identifier — resilient to line shifts."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            extra="forbid",
        )

        module: Annotated[str, m.Field(description="Module containing the violation")]
        rule: Annotated[str, m.Field(description="Rule that was violated")]
        content_hash: Annotated[
            str, m.Field(description="SHA256 of surrounding context lines")
        ]

        def __hash__(self) -> int:
            """Hash by stable business identity so keys work in sets and frozensets."""
            return hash((self.module, self.rule, self.content_hash))

        @staticmethod
        def from_violation(
            violation: FlextInfraModelsCodegen.CensusViolation,
            source_lines: t.StrSequence,
        ) -> FlextInfraModelsCodegen.ViolationKey:
            """Build key from violation and source context (+-2 lines)."""
            ctx_start = max(0, violation.line - 2)
            ctx_end = min(len(source_lines), violation.line + 3)
            context = "\n".join(source_lines[ctx_start:ctx_end])
            content_hash = u.Cli.sha256_content(context)
            return FlextInfraModelsCodegen.ViolationKey(
                module=violation.module,
                rule=violation.rule,
                content_hash=content_hash,
            )

    class CodegenPipelineState(m.ArbitraryTypesModel):
        """Typed inter-stage state for the codegen pipeline — Pydantic v2 model."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            arbitrary_types_allowed=True,
        )

        discovered_projects: Annotated[
            Sequence[p.Infra.ProjectInfo],
            m.Field(
                default_factory=tuple,
                description="Projects discovered at pipeline start",
            ),
        ]
        census_service: Annotated[
            p.Infra.CodegenCensusService | None,
            m.Field(
                description="Cached census service for reuse across stages",
            ),
        ] = None
        reports_before: Annotated[
            Sequence[FlextInfraModelsCodegen.CensusReport],
            m.Field(
                default_factory=tuple,
                description="Census reports collected before fixes",
            ),
        ]
        reports_after: Annotated[
            Sequence[FlextInfraModelsCodegen.CensusReport],
            m.Field(
                default_factory=tuple,
                description="Census reports collected after fixes",
            ),
        ]
        scaffold_results: Annotated[
            Sequence[FlextInfraModelsCodegen.ScaffoldResult],
            m.Field(default_factory=tuple, description="Scaffolding stage results"),
        ]
        fix_results: Annotated[
            Sequence[FlextInfraModelsCodegen.AutoFixResult],
            m.Field(default_factory=tuple, description="Auto-fix stage results"),
        ]


__all__: list[str] = ["FlextInfraModelsCodegen"]
