"""Domain models for the check subpackage."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field, computed_field, model_serializer

from flext_cli import m
from flext_infra import c, t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsCheck:
    """Quality-gate check domain models."""

    class RunCommand(FlextInfraModelsMixins.ProjectMixin, m.ContractModel):
        """Canonical CLI payload for ``flext-infra check run``."""

        gates: Annotated[
            str,
            Field(
                default=c.Infra.DEFAULT_CSV,
                description="Comma-separated quality gates to execute",
            ),
        ] = c.Infra.DEFAULT_CSV
        reports_dir: Annotated[
            str,
            Field(
                default=f"{c.Infra.REPORTS_DIR_NAME}/check",
                alias="reports-dir",
                description="Directory used to write check reports",
            ),
        ] = f"{c.Infra.REPORTS_DIR_NAME}/check"
        fix: Annotated[
            bool,
            Field(default=False, description="Apply supported gate fixes before run"),
        ] = False
        check_only: Annotated[
            bool,
            Field(
                default=False,
                alias="check-only",
                description="Enable check-only mode for supported tools",
            ),
        ] = False
        ruff_args: Annotated[
            str | None,
            Field(
                default=None,
                alias="ruff-args",
                description="Extra arguments forwarded to Ruff",
            ),
        ] = None
        pyright_args: Annotated[
            str | None,
            Field(
                default=None,
                alias="pyright-args",
                description="Extra arguments forwarded to Pyright",
            ),
        ] = None

        @property
        def reports_dir_path(self) -> Path:
            """Return the resolved reports directory path."""
            reports_dir = Path(self.reports_dir).expanduser()
            if reports_dir.is_absolute():
                return reports_dir.resolve()
            return (Path.cwd() / reports_dir).resolve()

    class FixPyreflyConfigCommand(
        FlextInfraModelsMixins.ProjectMixin,
        m.ContractModel,
    ):
        """Canonical CLI payload for ``flext-infra check fix-pyrefly-settings``."""

        apply: Annotated[
            bool,
            Field(
                default=False,
                description="Apply fixes in-place instead of dry-run mode",
                json_schema_extra={
                    "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS),
                },
            ),
        ] = False

        @computed_field  # type: ignore[prop-decorator]
        @property
        def dry_run(self) -> bool:
            """Whether pyrefly fixes should avoid writing to disk."""
            return not self.apply

    class Issue(m.ContractModel):
        """Single issue reported by a quality gate tool."""

        file: Annotated[str, Field(description="Source file path")]
        line: Annotated[int, Field(description="Line number")]
        column: Annotated[int, Field(description="Column number")]
        code: Annotated[str, Field(description="Rule or error code")]
        message: Annotated[str, Field(description="Human-readable issue description")]
        severity: Annotated[
            str,
            Field(
                default=c.Infra.ERROR,
                description="Issue severity level",
            ),
        ] = c.Infra.ERROR

        @computed_field
        @property
        def formatted(self) -> str:
            """Format issue as ``file:line:col [code] message``."""
            code_part = f"[{self.code}] " if self.code else ""
            return (
                f"{self.file}:{self.line}:{self.column} {code_part}{self.message}"
            ).strip()

    class GateResult(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Result summary for a single quality gate execution."""

        gate: Annotated[str, Field(description="Gate name")]
        passed: Annotated[bool, Field(description="Gate execution status")]
        errors: t.StrSequence = Field(
            default_factory=tuple,
            description="Gate error messages",
        )
        duration: float = Field(default=0.0, description="Duration in seconds")

    class GateExecution(m.ArbitraryTypesModel):
        """Execution result for a single quality gate."""

        result: FlextInfraModelsCheck.GateResult = Field(
            description="Gate result model",
        )
        issues: tuple[FlextInfraModelsCheck.Issue, ...] = Field(
            default_factory=tuple, description="Detected issues"
        )
        raw_output: str = Field(default="", description="Raw tool output")

    class ProjectResult(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Aggregated gate results for a single project."""

        gates: MutableMapping[str, FlextInfraModelsCheck.GateExecution] = Field(
            default_factory=dict,
            description="Gate name to execution mapping",
        )

        @computed_field
        @property
        def passed(self) -> bool:
            """Whether every gate passed."""
            return all(v.result.passed for v in self.gates.values())

        @computed_field
        @property
        def total_errors(self) -> int:
            """Total issue count across all gates."""
            return sum(len(v.issues) for v in self.gates.values())

    # -- SARIF 2.1.0 report models -----------------------------------------

    class SarifRule(m.ContractModel):
        """Compact SARIF rule descriptor."""

        id: Annotated[str, Field(description="Rule identifier")]
        short_description: Annotated[
            str,
            Field(description="Rule short description"),
        ]

        @model_serializer(mode="plain")
        def _serialize(self) -> t.Cli.JsonMapping:
            return {
                "id": self.id,
                "shortDescription": {"text": self.short_description},
            }

    class SarifLocation(m.ContractModel):
        """Compact SARIF location source span."""

        uri: Annotated[str, Field(description="Artifact URI")]
        start_line: Annotated[int, Field(description="Start line (1-based)")]
        start_column: Annotated[int, Field(description="Start column (1-based)")]
        uri_base_id: str = Field(
            default="%SRCROOT%",
            description="URI base identifier",
        )

        @model_serializer(mode="plain")
        def _serialize(self) -> t.Cli.JsonMapping:
            return {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": self.uri,
                        "uriBaseId": self.uri_base_id,
                    },
                    "region": {
                        "startLine": self.start_line,
                        "startColumn": self.start_column,
                    },
                },
            }

    class SarifResult(m.ContractModel):
        """SARIF result entry."""

        rule_id: Annotated[str, Field(description="Rule identifier")]
        level: Annotated[str, Field(description="Result level (error/warning)")]
        message: Annotated[str, Field(description="Result message")]
        locations: list[FlextInfraModelsCheck.SarifLocation] = Field(
            description="Result locations",
        )

        @model_serializer(mode="plain")
        def _serialize(self) -> t.Cli.JsonMapping:
            return {
                "ruleId": self.rule_id,
                "level": self.level,
                "message": {"text": self.message},
                "locations": [
                    location.model_dump(by_alias=True) for location in self.locations
                ],
            }

    class SarifRun(m.ContractModel):
        """SARIF run entry."""

        tool_name: Annotated[str, Field(description="Tool name")]
        information_uri: str = Field(
            default="",
            description="Tool documentation URL",
        )
        rules: tuple[FlextInfraModelsCheck.SarifRule, ...] = Field(
            default_factory=tuple, description="Rule descriptors"
        )
        results: tuple[FlextInfraModelsCheck.SarifResult, ...] = Field(
            default_factory=tuple, description="Run results"
        )

        @model_serializer(mode="plain")
        def _serialize(self) -> t.Cli.JsonMapping:
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

    class SarifReport(m.ArbitraryTypesModel):
        """Complete SARIF 2.1.0 report."""

        model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True)

        schema_uri: str = Field(
            default="https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/Schemata/sarif-schema-2.1.0.json",
            alias="$schema",
            description="SARIF schema URI",
        )
        version: str = Field(default="2.1.0", description="SARIF version")
        runs: tuple[FlextInfraModelsCheck.SarifRun, ...] = Field(
            default_factory=tuple, description="SARIF runs"
        )


__all__ = ["FlextInfraModelsCheck"]
