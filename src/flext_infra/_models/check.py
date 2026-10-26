"""Domain models for the check subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsMixins
from flext_infra._models._git.identity import FlextInfraModelsGitIdentity


class FlextInfraModelsCheck:
    """Quality-gate check domain models."""

    class BanditFinding(m.ExternalContractModel):
        """Required fields consumed from one native Bandit finding."""

        filename: Annotated[t.NonEmptyStr, m.Field(description="Audited source path")]
        line_number: Annotated[
            t.NonNegativeInt,
            m.Field(description="Native finding line"),
        ]
        test_id: Annotated[t.NonEmptyStr, m.Field(description="Bandit test identifier")]
        issue_text: Annotated[
            t.NonEmptyStr,
            m.Field(description="Native security diagnostic"),
        ]

    class BanditScanError(m.ExternalContractModel):
        """A source file Bandit could not audit."""

        filename: Annotated[t.NonEmptyStr, m.Field(description="Unaudited source path")]
        reason: Annotated[t.NonEmptyStr, m.Field(description="Native scan failure")]

    class BanditReport(m.ExternalContractModel):
        """Required Bandit JSON arrays, including a clean pair of empty arrays."""

        results: Annotated[
            t.SequenceOf[FlextInfraModelsCheck.BanditFinding],
            m.Field(description="Native security findings"),
        ]
        errors: Annotated[
            t.SequenceOf[FlextInfraModelsCheck.BanditScanError],
            m.Field(description="Source files that were not audited"),
        ]

    class RunCommand(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra check run``.

        Inherits canonical ``repository_root`` (``--repository-root``),
        ``gates`` (parsed to ``t.StrSequence``), ``apply``/``dry_run``,
        ``projects`` and ``verbose`` from ``WriteMixin``; the scope
        root has exactly one owner so an unmapped option can never fall back
        to the current directory.
        """

        fail_fast: Annotated[
            bool,
            m.Field(description="Stop check gates after the first failure"),
        ] = c.Infra.CHECK_FAIL_FAST_DEFAULT
        gate_set: Annotated[
            c.Infra.CheckGateSet,
            m.Field(
                alias="gate-set",
                description=(
                    "Gate inventory resolved at runtime when --gates is empty: "
                    "check (CI or local partition), fix, or fmt"
                ),
            ),
        ] = c.Infra.CheckGateSet.CHECK
        phase: Annotated[
            c.Infra.CheckPhase,
            m.Field(description="Primary source admission or complete checker phase"),
        ] = c.Infra.CheckPhase.COMPLETE
        scope: Annotated[
            c.Infra.CodegenConformScope,
            m.Field(
                description=(
                    "Omitted-project selection: self checks the invoked "
                    "repository; all adds every governed workspace member, "
                    "and multi-root tools run once over their union"
                ),
            ),
        ] = c.Infra.CodegenConformScope.SELF
        reports_dir: Annotated[
            str,
            m.Field(
                alias="reports-dir",
                description="Base directory for unique invocation check reports",
            ),
        ] = f"{c.Infra.REPORTS_DIR_NAME}/check"
        check_only: Annotated[
            bool,
            m.Field(
                alias="check-only",
                description="Enable check-only mode for supported tools",
            ),
        ] = False
        ruff_args: Annotated[
            str | None,
            m.Field(alias="ruff-args", description="Extra arguments forwarded to Ruff"),
        ] = None
        pyright_args: Annotated[
            str | None,
            m.Field(
                alias="pyright-args",
                description="Extra arguments forwarded to Pyright",
            ),
        ] = None
        file: Annotated[
            str | None,
            m.Field(
                description="One literal repository-relative file; read-only gates"
            ),
        ] = None
        report_output: Annotated[
            Path | None,
            m.Field(
                alias="report-output",
                description="Absent invocation-owned typed summary destination",
            ),
        ] = None

        @property
        def reports_dir_path(self) -> Path:
            """Resolve the requested base; the checker owns its unique run leaf."""
            reports_dir = Path(self.reports_dir).expanduser()
            if reports_dir.is_absolute():
                return reports_dir.resolve()
            return (self.repository_root / reports_dir).resolve()

    class CheckProjectTarget(m.ArbitraryTypesModel):
        """Resolved target and its original pre-gate Git identity, when captured.

        Coverage planning never invents source identity. Global currentness
        requires the producer's identity for each actual target, including root.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            frozen=True,
            validate_default=False,
        )

        name: Annotated[str, m.Field(description="Display/project name")]
        path: Annotated[Path, m.Field(description="Resolved project root path")]
        applicable_gates: Annotated[
            t.StrSequence,
            m.Field(description="Requested gates elected for this project's inputs"),
        ] = ()
        source_identity: Annotated[
            FlextInfraModelsGitIdentity.GitIdentityReport | None,
            m.Field(description="Original exact repository identity before gates"),
        ] = None

    class MypyResourceLimit(m.ContractModel):
        """Validated memory and wall-time limits for every Mypy process."""

        memory_limit_mb: Annotated[
            int,
            m.Field(
                gt=0,
                le=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
                description="Positive Mypy memory limit in MiB (Linux AS; Darwin RSS)",
            ),
        ] = c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT
        timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                description=(
                    "Positive Mypy wall-time limit in seconds, resolved from"
                    " tools.mypy.timeout_seconds in tooling.yaml or the env"
                    " override"
                ),
            ),
        ]

        @m.computed_field
        @property
        def memory_limit_bytes(self) -> int:
            """Validated memory limit converted to bytes for the platform owner.

            Returns:
                The resulting ``int``.

            """
            return self.memory_limit_mb * c.Infra.BYTES_PER_MIB

    class MypyInvocation(m.ContractModel):
        """Checker inputs; callers cannot select an executable or Python program."""

        targets: Annotated[
            t.VariadicTuple[Path],
            m.Field(min_length=1, description="Files or directories to check"),
        ]
        workspace: Annotated[
            Path | None,
            m.Field(description="Workspace owning the checker environment"),
        ] = None
        config_file: Annotated[
            Path | None,
            m.Field(description="Owned Mypy configuration"),
        ] = None
        report_json: Annotated[
            bool,
            m.Field(description="Emit native JSON diagnostics"),
        ] = False
        verbose: Annotated[bool, m.Field(description="Emit Mypy progress")] = False
        profile_output: Annotated[
            Path | None,
            m.Field(description="Optional cProfile output destination"),
        ] = None

    class FixPyreflyConfigCommand(FlextInfraModelsMixins.WriteMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra check fix-pyrefly-settings``."""

    class SarifLocation(m.ContractModel):
        """Native SARIF location, including the optional end of its source span."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(validate_by_name=True)

        uri: str = m.Field(
            validation_alias=m.AliasPath("physicalLocation", "artifactLocation", "uri"),
            description="Artifact URI",
        )
        start_line: int | None = m.Field(
            None,
            validation_alias=m.AliasPath("physicalLocation", "region", "startLine"),
            description="Start line (1-based)",
        )
        start_column: int | None = m.Field(
            None,
            validation_alias=m.AliasPath("physicalLocation", "region", "startColumn"),
            description="Native start column",
        )
        end_line: int | None = m.Field(
            None,
            validation_alias=m.AliasPath("physicalLocation", "region", "endLine"),
            description="Native end line when supplied by the scanner",
        )
        end_column: int | None = m.Field(
            None,
            validation_alias=m.AliasPath("physicalLocation", "region", "endColumn"),
            description="Native end column when supplied by the scanner",
        )
        uri_base_id: str = m.Field(
            "%SRCROOT%",
            validation_alias=m.AliasPath(
                "physicalLocation",
                "artifactLocation",
                "uriBaseId",
            ),
            description="URI base identifier",
            validate_default=True,
        )

        @m.model_serializer
        def _serialize(self) -> t.JsonMapping:
            """Emit native optional span coordinates only when present.

            Returns:
                The resulting ``t.JsonMapping``.

            """
            region: t.JsonDict = {}
            if self.start_line is not None:
                region["startLine"] = self.start_line
            if self.start_column is not None:
                region["startColumn"] = self.start_column
            if self.end_line is not None:
                region["endLine"] = self.end_line
            if self.end_column is not None:
                region["endColumn"] = self.end_column
            return {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": self.uri,
                        "uriBaseId": self.uri_base_id,
                    },
                    "region": region,
                },
            }

    class LineWrapLiteral(m.ContractModel):
        """One single-line string literal the line-length repair may split."""

        start: Annotated[int, m.Field(ge=0, description="Start column of the literal")]
        end: Annotated[int, m.Field(ge=0, description="End column of the literal")]
        prefix: Annotated[str, m.Field(description="String prefix such as f or r")]
        quote: Annotated[str, m.Field(description="Single-character quote")]
        bracketed: Annotated[
            bool,
            m.Field(description="Whether the literal already sits inside brackets"),
        ]

    class Issue(m.ContractModel):
        """Single issue reported by a quality gate tool."""

        file: Annotated[str, m.Field(description="Source file path")]
        line: Annotated[int, m.Field(description="Line number")]
        column: Annotated[int, m.Field(description="Column number")]
        code: Annotated[str, m.Field(description="Rule or error code")]
        message: Annotated[str, m.Field(description="Human-readable issue description")]
        severity: Annotated[str, m.Field(description="Issue severity level")] = (
            c.Infra.ERROR
        )
        locations: t.VariadicTuple[SarifLocation] = m.Field(
            default=(),
            description="Native primary source spans when supplied by the scanner",
            validate_default=True,
        )
        related_locations: t.VariadicTuple[SarifLocation] = m.Field(
            default=(),
            description="All native comparison locations, including other projects",
            validate_default=True,
        )

        @m.field_validator(
            "locations",
            "related_locations",
            mode="before",
        )
        @classmethod
        def _coerce_declared_sequences(
            cls, value: t.JsonValue
        ) -> t.JsonValue | t.VariadicTuple[t.JsonValue]:
            """Coerce scanner JSON arrays into the strict tuple form.

            Args:
                value: The raw declared value.

            Returns:
                The coerced tuple.

            """
            return tuple(value) if isinstance(value, list) else value

        @m.computed_field
        @property
        def formatted(self) -> str:
            """Format issue as ``file:line:col [code] message``.

            Returns:
                The resulting ``str``.

            """
            code_part = f"[{self.code}] " if self.code else ""
            return (
                f"{self.file}:{self.line}:{self.column} {code_part}{self.message}"
            ).strip()

    class GateResult(FlextInfraModelsMixins.ProjectNameMixin, m.ArbitraryTypesModel):
        """Result summary for a single quality gate execution."""

        gate: Annotated[str, m.Field(description="Gate name")]
        passed: Annotated[bool, m.Field(description="Gate execution status")]
        errors: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Gate error messages",
        )
        duration: float = m.Field(
            0.0,
            description="Duration in seconds",
            validate_default=True,
        )

    class GateOutputReceipt(m.ContractModel):
        """Exact native output paired with its atomically published runtime path."""

        raw_output: Annotated[str, t.StringConstraints(strip_whitespace=False)] = (
            m.Field(description="Unmodified native output", exclude=True)
        )
        path: Path = m.Field(description="Durably published native output receipt")

    class GateExecutionParams(m.ContractModel):
        """Validated assembly inputs keeping native outcome apart from acceptance."""

        project_dir: Path = m.Field(description="Project whose gate was executed")
        verdict: bool = m.Field(description="Acceptance decided by the caller")
        outcome: c.Infra.ToolOutcome | None = m.Field(
            default=None,
            description="Declared native tool outcome; absent derives it from findings",
        )
        issues: t.VariadicTuple[Issue] = m.Field(
            description="Complete native diagnostics",
        )
        raw_output: Annotated[str, t.StringConstraints(strip_whitespace=False)] = (
            m.Field(description="Unmodified native output")
        )
        started: float = m.Field(description="Monotonic execution start time")

    class GateExecution(m.ArbitraryTypesModel):
        """Execution result for a single quality gate."""

        result: FlextInfraModelsCheck.GateResult = m.Field(
            description="Gate result model",
        )
        issues: t.VariadicTuple[Issue] = m.Field(
            default_factory=tuple,
            description=(
                "Complete native gate diagnostics, including informative findings"
            ),
        )
        raw_output: Annotated[str, t.StringConstraints(strip_whitespace=False)] = (
            m.Field(
                default="",
                description=(
                    "In-memory native output; persisted once at raw_receipt rather "
                    "than duplicated inside serialized execution summaries"
                ),
                exclude=True,
                validate_default=True,
            )
        )
        raw_receipt: Path | None = m.Field(
            None,
            description="Durable verbatim native output published by the checker",
            validate_default=True,
        )
        outcome: c.Infra.ToolOutcome = m.Field(
            description="Native process/report verdict, independent of findings policy",
        )
        process: Annotated[
            m.Cli.ProcessOutcome | None,
            m.Field(description="Original native process, when this gate invoked one"),
        ] = None
        components: Annotated[
            MutableMapping[str, FlextInfraModelsCheck.GateExecution],
            m.Field(description="Executions owned by a composite gate"),
        ] = m.Field(default_factory=dict)
        requested_components: Annotated[
            t.StrSequence,
            m.Field(description="Native component inventory elected before execution"),
        ] = ()

        @m.computed_field
        @property
        def complete(self) -> bool:
            """Every elected component has its actual execution record."""
            return (
                len(set(self.requested_components)) == len(self.requested_components)
                and set(self.components) == set(self.requested_components)
                and all(component.complete for component in self.components.values())
            )

        @m.computed_field
        @property
        def interrupted(self) -> bool:
            """Whether this execution or an owned component was interrupted."""
            process = self.process
            return (
                process is not None
                and (
                    process.timed_out
                    or process.forwarded_signal is not None
                    or process.raw_return_code < 0
                )
            ) or any(component.interrupted for component in self.components.values())

        @m.computed_field
        @property
        def finding_count(self) -> int:
            """Number of native findings, independent of approval blocking policy.

            Returns:
                The resulting ``int``.

            """
            return len(self.issues)

    class ProjectResult(FlextInfraModelsMixins.ProjectNameMixin, m.ArbitraryTypesModel):
        """Aggregated gate results for a single project.

        Enforcement exemption: ``gates`` is a ``MutableMapping`` populated
        incrementally as each gate completes; no shared state — one fresh
        dict per instance.
        """

        gates: MutableMapping[str, FlextInfraModelsCheck.GateExecution] = m.Field(
            default_factory=dict[str, "FlextInfraModelsCheck.GateExecution"],
            description="Gate name to execution mapping",
        )

        @m.computed_field
        @property
        def passed(self) -> bool:
            """Whether every gate passed.

            Returns:
                The resulting ``bool``.

            """
            return bool(self.gates) and all(
                v.result.passed for v in self.gates.values()
            )

        @m.computed_field
        @property
        def total_findings(self) -> int:
            """Total native findings across every executed gate.

            Returns:
                The resulting ``int``.

            """
            return sum(v.finding_count for v in self.gates.values())

    class LoopOutcome(m.ArbitraryTypesModel):
        """Bundled results from the project-checking loop."""

        # Why: owned by m.Infra; ArbitraryTypesModel keeps protocol field writability.

        results: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.ProjectResult],
            m.Field(description="Individual project execution results."),
        ]
        failed: Annotated[
            int,
            m.Field(description="Number of projects that failed one or more gates."),
        ]
        total_elapsed: Annotated[
            float,
            m.Field(description="Total time elapsed in seconds for the entire loop."),
        ]

    # -- SARIF 2.1.0 report models -----------------------------------------
    # Each model keeps flat fields; ``model_serializer`` emits the nested SARIF
    # shape and the matching ``AliasPath`` validation aliases read that same
    # shape back, so an emitted report validates into the model it came from.

    class SarifRule(m.ContractModel):
        """Compact SARIF rule descriptor."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(validate_by_name=True)

        id: Annotated[str, m.Field(description="Rule identifier")]
        short_description: Annotated[
            str,
            m.Field(
                validation_alias=m.AliasPath("shortDescription", "text"),
                description="Rule short description",
            ),
        ]
        help_uri: Annotated[
            str,
            m.Field(
                validation_alias="helpUri",
                description="Documentation URL of the tool behind the gate",
            ),
        ]

        @m.model_serializer
        def _serialize(self) -> t.JsonMapping:
            """Serialize.

            Returns:
                The resulting ``t.JsonMapping``.

            """
            return {
                "id": self.id,
                "shortDescription": {"text": self.short_description},
                "helpUri": self.help_uri,
            }

    class SarifResult(m.ContractModel):
        """SARIF result entry."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(validate_by_name=True)

        rule_id: Annotated[
            str,
            m.Field(validation_alias="ruleId", description="Rule identifier"),
        ]
        level: Annotated[str, m.Field(description="Result level (error/warning/note)")]
        message: Annotated[
            str,
            m.Field(
                validation_alias=m.AliasPath("message", "text"),
                description="Result message",
            ),
        ]
        locations: t.VariadicTuple[FlextInfraModelsCheck.SarifLocation] = m.Field(
            description="Result locations",
        )
        related_locations: t.VariadicTuple[FlextInfraModelsCheck.SarifLocation] = (
            m.Field(
                (),
                validation_alias="relatedLocations",
                description="Native related source spans",
                validate_default=True,
            )
        )

        @m.model_serializer
        def _serialize(self) -> t.JsonMapping:
            """Serialize.

            Returns:
                The resulting ``t.JsonMapping``.

            """
            result: t.MutableJsonMapping = {
                "ruleId": self.rule_id,
                "level": self.level,
                "message": {"text": self.message},
                "locations": [
                    location.model_dump(by_alias=True) for location in self.locations
                ],
            }
            if self.related_locations:
                result["relatedLocations"] = [
                    location.model_dump(by_alias=True)
                    for location in self.related_locations
                ]
            return result

    class SarifRun(m.ContractModel):
        """SARIF run entry."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(validate_by_name=True)

        tool_name: Annotated[
            str,
            m.Field(
                validation_alias=m.AliasPath("tool", "driver", "name"),
                description="Tool name",
            ),
        ]
        information_uri: str = m.Field(
            "",
            validation_alias=m.AliasPath("tool", "driver", "informationUri"),
            description="Tool documentation URL",
            validate_default=True,
        )
        rules: t.VariadicTuple[FlextInfraModelsCheck.SarifRule] = m.Field(
            default_factory=tuple,
            validation_alias=m.AliasPath("tool", "driver", "rules"),
            description="Rule descriptors",
        )
        results: t.VariadicTuple[FlextInfraModelsCheck.SarifResult] = m.Field(
            default_factory=tuple,
            description="Run results",
        )

        @m.model_serializer
        def _serialize(self) -> t.JsonMapping:
            """Serialize.

            Returns:
                The resulting ``t.JsonMapping``.

            """
            return {
                "tool": {
                    "driver": {
                        "name": self.tool_name,
                        "informationUri": self.information_uri,
                        "rules": [
                            rule.model_dump(by_alias=True) for rule in self.rules
                        ],
                    },
                },
                "results": [
                    result.model_dump(by_alias=True) for result in self.results
                ],
            }

    class CheckReportSummary(m.ContractModel):
        """Invocation-owned execution facts retained by the published SARIF.

        Global admission requires the producer's unfiltered topology and full
        applicable gate plan, not merely completion of the requested subset.
        Missing global coverage is unknown, never implicit whole-workspace proof.
        """

        phase: Annotated[
            c.Infra.CheckPhase,
            m.Field(
                description="Original checker phase; primary is never complete check proof"
            ),
        ] = c.Infra.CheckPhase.COMPLETE
        requested_gates: Annotated[
            t.StrSequence,
            m.Field(
                min_length=1,
                description="Resolved gate inventory requested before execution",
            ),
        ]
        pending_gates: Annotated[
            t.StrSequence,
            m.Field(
                description=(
                    "Requested gates whose project applicability is still pending"
                ),
            ),
        ] = ()
        targets: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.CheckProjectTarget],
            m.Field(description="Canonical project roots selected for this invocation"),
        ]
        results: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.ProjectResult],
            m.Field(description="Only executions reached by this invocation"),
        ]
        selected_files: Annotated[
            t.VariadicTuple[Path],
            m.Field(description="File selection; empty means full-project execution"),
        ]
        global_targets: Annotated[
            t.VariadicTuple[FlextInfraModelsCheck.CheckProjectTarget] | None,
            m.Field(
                min_length=1,
                description=(
                    "Producer's unfiltered canonical global project and gate plan; "
                    "absent for legacy, filtered or applicability-pending reports"
                ),
            ),
        ] = None

        @m.computed_field
        @property
        def complete(self) -> bool:
            """Every selected target executed its exact applicable inventory."""
            return (
                bool(self.targets)
                and not self.pending_gates
                and len(self.targets) == len(self.results)
                and len({target.path for target in self.targets}) == len(self.targets)
                and all(
                    target.name == result.project
                    and bool(target.applicable_gates)
                    and set(target.applicable_gates).issubset(self.requested_gates)
                    and set(result.gates) == set(target.applicable_gates)
                    and all(execution.complete for execution in result.gates.values())
                    for target, result in zip(self.targets, self.results, strict=True)
                )
            )

    class SarifReport(m.ArbitraryTypesModel):
        """Complete SARIF 2.1.0 report; serializes and validates the same JSON."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            validate_by_name=True,
            serialize_by_alias=True,
        )

        schema_uri: c.Infra.SarifSchema = m.Field(
            c.Infra.SarifSchema.V2_1_0,
            alias="$schema",
            description="SARIF schema URI",
            validate_default=True,
        )
        version: c.Infra.SarifVersion = m.Field(
            c.Infra.SarifVersion.V2_1_0,
            description="SARIF version",
            validate_default=True,
        )
        runs: t.VariadicTuple[FlextInfraModelsCheck.SarifRun] = m.Field(
            default_factory=tuple,
            description="SARIF runs",
        )
        properties: FlextInfraModelsCheck.CheckReportSummary | None = m.Field(
            None,
            description="Typed invocation targets and executions; absent is unknown",
        )


__all__: list[str] = ["FlextInfraModelsCheck"]


SarifLocation = FlextInfraModelsCheck.SarifLocation
Issue = FlextInfraModelsCheck.Issue
