"""Domain models for the shared utilities subpackage.

Scan violation and result models used by infrastructure scanning utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, ClassVar, Literal, Self

from flext_cli import m, p

from flext_infra import c, t
from flext_infra._models import (
    FlextInfraModelsCodemod,
    FlextInfraModelsMixins,
    FlextInfraModelsNamespaceEnforcer,
)


class FlextInfraModelsScan:
    """Shared utility domain models for scanning and analysis."""

    class ModScanPublication(m.ContractModel):
        """Typed invocation metadata for the existing scan evidence publisher."""

        command: Annotated[
            c.Infra.ModScanCommand, m.Field(description="Actual native scan operation")
        ]
        scope: Annotated[
            t.StrSequence, m.Field(description="Actual governed scan scope")
        ]
        relative_path: Annotated[
            Path, m.Field(description="Invocation evidence destination under root")
        ] = c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH
        repositories: Annotated[
            t.StrSequence, m.Field(description="Observed repository inventory")
        ] = ()
        rule_ids: Annotated[
            t.StrSequence, m.Field(description="Actual elected rule inventory")
        ] = ()

    class DetectorContext(m.ArbitraryTypesModel):
        """Bundles common parameters passed to every detect_file classmethod."""

        file_path: Path = m.Field(
            description="Filesystem path of the file being scanned.",
        )
        rope_project: t.Infra.RopeProject = m.Field(
            description="Initialized Rope project for semantic metadata.",
        )
        parse_failures: Annotated[
            (
                t.MutableSequenceOf[
                    FlextInfraModelsNamespaceEnforcer.ParseFailureViolation
                ]
                | None
            ),
            m.SkipValidation,
            m.Field(
                description="Shared parse-failure collector across detector passes.",
            ),
        ] = None
        project_name: Annotated[
            str,
            m.Field(description="Optional project name for the scanned file."),
        ] = ""
        project_root: Annotated[
            Path | None,
            m.Field(description="Optional project root containing the scanned file."),
        ] = None

    class ScanViolation(FlextInfraModelsMixins.PositiveLineMixin, m.ContractModel):
        """A single violation found during file scanning."""

        message: Annotated[
            str,
            m.Field(description="Human-readable violation description"),
        ]
        severity: Annotated[str, m.Field(description="Violation severity level")]
        rule_id: Annotated[
            str | None,
            m.Field(description="Optional rule identifier"),
        ] = None

    class ScanResult(m.ArbitraryTypesModel):
        """Result of scanning a single file."""

        file_path: Annotated[Path, m.Field(description="Path to the scanned file")]
        violations: Annotated[
            t.SequenceOf[FlextInfraModelsScan.ScanViolation],
            m.Field(description="Violations found in the file"),
        ] = m.Field(default_factory=tuple)
        detector_name: Annotated[
            str,
            m.Field(description="Name of the detector that produced this result"),
        ]

    class ModScanFinding(m.ArbitraryTypesModel):
        """One complete ast-grep JSONL finding with canonical evidence keys."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        rule_file: Annotated[
            t.NonEmptyStr,
            m.Field(description="Rule document file producing the finding"),
        ]
        rule_id: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact ast-grep rule identifier"),
        ]
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Workspace repository owning the file"),
        ]
        catalog_digest: Annotated[
            str | None, m.Field(description="Authenticated native rule document digest")
        ] = None
        module_absence: Annotated[
            bool,
            m.Field(
                description="Occurrence anchored by native module absence predicate"
            ),
        ] = False
        file: Annotated[Path, m.Field(description="Workspace-relative finding path")]
        source_owner: Annotated[
            Literal["authored", "generator"],
            m.Field(description="Writable authority for the finding source"),
        ] = "authored"
        source_state: Annotated[
            m.Cli.AtomicFileState | None,
            m.Field(
                exclude=True,
                description="Live source snapshot; evidence stores its input once",
            ),
        ] = None
        binding_states: Annotated[
            tuple[m.Cli.AtomicFileState, ...],
            m.Field(
                exclude=True,
                description="Live binding inputs; evidence stores their inventory once",
            ),
        ] = m.Field(default_factory=tuple)
        range: Annotated[
            t.JsonMapping,
            m.Field(description="Exact ast-grep source range payload"),
        ]
        text: Annotated[str, m.Field(description="Exact matched source text")]
        replacement: Annotated[
            str | None,
            m.Field(description="Exact replacement when the rule provides one"),
        ] = None
        actionable: Annotated[
            bool,
            m.Field(description="Whether applying the rule changes source bytes"),
        ]
        classification: Annotated[
            c.Infra.ModScanFindingClass,
            m.Field(description="Rule mutability and byte-change classification"),
        ]
        payload: Annotated[
            t.JsonMapping,
            m.Field(
                description="Complete validated ast-grep finding without field loss",
            ),
        ]

    class ModScanSourceContext(m.ArbitraryTypesModel):
        """One scan's per-file authentication and ownership indexes."""

        source_states: Annotated[
            t.MappingKV[Path, m.Cli.AtomicFileState],
            m.Field(description="Exact sources captured before the native scan"),
        ]
        repository_roots: Annotated[
            tuple[Path, ...],
            m.Field(description="Governed roots in nearest-owner precedence"),
        ]
        authenticated: Annotated[
            t.MutableMappingKV[str, p.Result[t.Pair[Path, m.Cli.AtomicFileState]]],
            m.Field(default_factory=dict, description="One authentication per file"),
        ]
        repositories: Annotated[
            t.MutableMappingKV[Path, str],
            m.Field(
                default_factory=dict, description="One ownership election per file"
            ),
        ]

    class ModScanFindingReference(ModScanFinding):
        """Serialized occurrence referencing the report's authenticated inventory."""

        source_path: Annotated[
            Path | None,
            m.Field(
                description="Authenticated source input, or absent on source drift"
            ),
        ]
        binding_graph: Annotated[
            int,
            m.Field(
                ge=0,
                strict=True,
                description="Index of this occurrence's authenticated binding graph",
            ),
        ]

    class ModReplacementOffsets(m.ContractModel):
        """UTF-8 byte coordinates supplied by the ast-grep JSON contract."""

        start: Annotated[
            int,
            m.Field(ge=0, strict=True, description="Inclusive start byte"),
        ]
        end: Annotated[
            int,
            m.Field(ge=0, strict=True, description="Exclusive end byte"),
        ]

    class ModScanCounts[FindingT: ModScanFinding](m.ArbitraryTypesModel):
        """Authenticated findings are the sole source of serialized scan counts."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        entries: Annotated[
            t.VariadicTuple[FindingT],
            m.Field(description="Every validated ast-grep finding in stable order"),
        ]

        @m.computed_field
        @property
        def findings(self) -> t.NonNegativeInt:
            """Complete native occurrence count, including source drift."""
            return len(self.entries)

        @m.computed_field
        @property
        def actionable(self) -> t.NonNegativeInt:
            """Native occurrences whose admitted fix changes source bytes."""
            return sum(
                entry.classification == c.Infra.ModScanFindingClass.ACTIONABLE
                for entry in self.entries
            )

        @m.computed_field
        @property
        def detection_only(self) -> t.NonNegativeInt:
            """Native occurrences produced by rules without a fix."""
            return sum(
                entry.classification == c.Infra.ModScanFindingClass.DETECTION_ONLY
                for entry in self.entries
            )

        @m.computed_field
        @property
        def non_actionable_with_fix(self) -> t.NonNegativeInt:
            """Native occurrences whose declared fix leaves identical bytes."""
            return sum(
                entry.classification
                == c.Infra.ModScanFindingClass.NON_ACTIONABLE_WITH_FIX
                for entry in self.entries
            )

        @m.computed_field
        @property
        def deferred(self) -> t.NonNegativeInt:
            """Drifted native occurrences retained as evidence, never admitted edits."""
            return sum(
                entry.classification
                == c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT
                for entry in self.entries
            )

    class ModScanReport(ModScanCounts[ModScanFinding]):
        """Verified structural findings and actionable rewrite targets."""

        source_states: Annotated[
            tuple[m.Cli.AtomicFileState, ...] | None,
            m.Field(
                description="Complete authenticated scan inventory, including zero "
                "findings"
            ),
        ] = None
        files: Annotated[
            frozenset[Path],
            m.Field(description="Files containing findings"),
        ]

    class ModTextRule(m.ArbitraryTypesModel):
        """One declarative sed-by-list entry with its exact rewrite receipt."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        rule_id: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact unique text-rule identifier"),
        ]
        description: Annotated[
            str,
            m.Field(description="Human-readable rewrite intent"),
        ] = ""
        include: Annotated[
            t.StrSequence,
            m.Field(description="fnmatch globs a target path must match"),
        ] = ()
        exclude: Annotated[
            t.StrSequence,
            m.Field(description="fnmatch globs a target path must not match"),
        ] = ()
        distributions: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Declared project distributions selected "
                    "for this rule; empty selects all"
                ),
            ),
        ] = ()
        find: Annotated[
            t.NonEmptyStr,
            m.Field(description="Regex source pattern to locate"),
        ]
        replace: Annotated[
            str,
            m.Field(description="Expansion template replacing each match"),
        ] = ""
        flags: Annotated[
            t.StrSequence,
            m.Field(description="Regex flag names from the SSOT map"),
        ] = ()
        capture_equals: Annotated[
            t.MappingKV[str, str],
            m.Field(description="Named regex captures and their required exact values"),
        ] = m.Field(default_factory=lambda: MappingProxyType[str, str]({}))
        expected: Annotated[
            int | None,
            m.Field(
                ge=0,
                description="Exact finding count the rule must produce when set",
            ),
        ] = None

    class ModTextFinding(m.ArbitraryTypesModel):
        """One text-rule match with its computed replacement."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        rule_id: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact text-rule identifier"),
        ]
        file: Annotated[Path, m.Field(description="Workspace-relative target path")]
        line: Annotated[t.NonNegativeInt, m.Field(description="One-based match line")]
        text: Annotated[str, m.Field(description="Exact matched source text")]
        replacement: Annotated[
            str,
            m.Field(description="Expanded replacement for the match"),
        ]

    class ModTextReport(m.ArbitraryTypesModel):
        """Complete text-rule findings for one fixed-point pass."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        findings: Annotated[
            t.NonNegativeInt,
            m.Field(description="Complete finding count"),
        ]
        actionable: Annotated[
            t.NonNegativeInt,
            m.Field(description="Matches whose replacement differs from the text"),
        ]
        files: Annotated[
            frozenset[Path],
            m.Field(description="Files containing findings"),
        ]
        entries: Annotated[
            t.VariadicTuple[FlextInfraModelsScan.ModTextFinding],
            m.Field(description="Every validated text finding in stable order"),
        ]

    class ModScanEvidence(ModScanCounts[ModScanFindingReference]):
        """Complete replace-on-run evidence for one public mod scan."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        schema_version: Annotated[
            int,
            m.Field(
                strict=True,
                ge=c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
                le=c.Infra.MOD_SCAN_REPORT_SCHEMA_VERSION,
                description="Exact structured evidence schema",
            ),
        ]
        inputs: Annotated[
            FlextInfraModelsCodemod.CodemodBindingSnapshot,
            m.Field(description="Single authenticated inventory for all occurrences"),
        ]
        binding_graphs: Annotated[
            tuple[tuple[Path, ...], ...],
            m.Field(
                description="Closed binding graphs stored once, retaining input order "
                "and multiplicity",
            ),
        ]
        command: Annotated[
            c.Infra.ModScanCommand,
            m.Field(description="Public mod scan mode"),
        ]
        root: Annotated[Path, m.Field(description="Absolute scanned workspace root")]
        scope: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(min_length=1, description="Exact ast-grep target scope"),
        ]
        totals_by_class: Annotated[
            t.MappingKV[c.Infra.ModScanFindingClass, t.NonNegativeInt],
            m.Field(description="Complete finding totals by mutability class"),
        ]
        totals_by_repository: Annotated[
            t.MappingKV[str, t.NonNegativeInt],
            m.Field(description="Complete finding totals by repository"),
        ]
        totals_by_rule: Annotated[
            t.MappingKV[str, t.NonNegativeInt],
            m.Field(description="Complete finding totals by rule identifier"),
        ]

        @m.model_validator(mode="after")
        def hydrate_occurrence_inputs(self) -> Self:
            """Resolve persisted references through the typed closed inventory.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If mod scan classification inventory is incomplete; or if
                    mod scan.
            """
            if set(self.totals_by_class) != set(c.Infra.MOD_SCAN_CLASS_COUNT_FIELDS):
                msg = "mod scan classification inventory is incomplete"
                raise ValueError(msg)
            for classification, field in c.Infra.MOD_SCAN_CLASS_COUNT_FIELDS.items():
                if self.totals_by_class[classification] != getattr(self, field):
                    msg = f"mod scan {field} differs from authenticated entries"
                    raise ValueError(msg)
            for field, totals in (
                ("repository", self.totals_by_repository),
                ("rule_id", self.totals_by_rule),
            ):
                counted = Counter(dict.fromkeys(totals, 0))
                counted.update(getattr(entry, field) for entry in self.entries)
                if dict(counted) != dict(totals):
                    msg = f"mod scan {field} totals differ from authenticated entries"
                    raise ValueError(msg)
            indexed = {state.path: state for state in self.inputs.states}
            bindings = tuple(
                tuple(indexed[path] for path in paths) for paths in self.binding_graphs
            )
            entries = []
            for entry in self.entries:
                source = (
                    None if entry.source_path is None else indexed[entry.source_path]
                )
                if entry.binding_graph >= len(bindings):
                    msg = f"mod scan binding graph is missing: {entry.binding_graph}"
                    raise ValueError(msg)
                entries.append(
                    entry.model_copy(
                        update={
                            "source_state": source,
                            "binding_states": bindings[entry.binding_graph],
                        }
                    )
                )
            return self.model_copy(update={"entries": tuple(entries)})

    class ModScanEvidenceReceipt(m.ArbitraryTypesModel):
        """Authenticated publication identity and its exact evidence payload."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        path: Annotated[Path, m.Field(description="Published evidence destination")]
        sha256: Annotated[t.NonEmptyStr, m.Field(description="Published byte digest")]
        evidence: Annotated[
            FlextInfraModelsScan.ModScanEvidence,
            m.Field(description="Exact structured evidence that was published"),
        ]


__all__: list[str] = ["FlextInfraModelsScan"]
