"""Domain models for the docs subpackage."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, Field

from flext_core import FlextModels
from flext_infra import t


def _docs_phase_items() -> Sequence[FlextInfraDocsModels.DocsPhaseItemModel]:
    return []


class FlextInfraDocsModels:
    """Models for documentation services."""

    class DocsPhaseItemModel(BaseModel):
        """Unified item payload for docs phase reports."""

        model_config: ClassVar[ConfigDict] = ConfigDict(
            extra="forbid",
            frozen=True,
            strict=True,
        )

        phase: Annotated[
            str,
            Field(description="Docs phase: audit, fix, build, generate, validate"),
        ]
        file: Annotated[str, Field(default="", description="Relative file path")] = ""
        issue_type: Annotated[
            str,
            Field(default="", description="Audit issue type"),
        ] = ""
        severity: Annotated[
            str,
            Field(default="", description="Audit issue severity"),
        ] = ""
        message: Annotated[
            str,
            Field(default="", description="Item detail message"),
        ] = ""
        links: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Applied link fixes"),
        ] = 0
        toc: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Applied TOC updates"),
        ] = 0
        path: Annotated[
            str,
            Field(default="", description="Generated file path"),
        ] = ""
        written: Annotated[
            bool,
            Field(default=False, description="Generated file write flag"),
        ] = False

    class DocScope(FlextModels.ArbitraryTypesModel):
        """Documentation scope targeting a project or workspace root."""

        name: Annotated[t.NonEmptyStr, Field(description="Scope name")]
        path: Annotated[Path, Field(description="Absolute path to scope root")]
        report_dir: Annotated[
            Path,
            Field(description="Report output directory for scope"),
        ]
        project_class: Annotated[
            str,
            Field(default="root", description="Docs scope classification"),
        ] = "root"
        package_name: Annotated[
            str,
            Field(default="", description="Primary package name for scope"),
        ] = ""

    class AuditIssue(FlextModels.ContractModel):
        """Single documentation audit finding."""

        file: Annotated[str, Field(description="File path relative to scope")]
        issue_type: Annotated[str, Field(description="Issue category")]
        severity: Annotated[str, Field(description="Issue severity")]
        message: Annotated[str, Field(description="Issue description")]

    class GeneratedFile(FlextModels.ContractModel):
        """Record of a generated file operation."""

        path: Annotated[str, Field(description="File path")]
        written: Annotated[
            bool,
            Field(default=False, description="Whether file was written"),
        ] = False

    class AuditScopeParams(FlextModels.ContractModel):
        """Bundled parameters for a single audit scope run."""

        check: Annotated[
            str, Field(default="all", description="Comma-separated checks")
        ]
        strict: Annotated[bool, Field(default=True, description="Strict mode")]
        budgets: Annotated[
            t.Infra.Pair[int | None, t.IntMapping] | None,
            Field(default=None, description="Budget tuple (default, by_scope)"),
        ] = None

    class DocsPhaseReport(FlextModels.ContractModel):
        """Unified report payload for docs phases."""

        phase: Annotated[
            str,
            Field(
                description="Docs phase: audit, fix, build, generate, validate",
            ),
        ]
        scope: Annotated[str, Field(description="Scope name")]
        result: Annotated[str, Field(default="", description="Result status")] = ""
        reason: Annotated[str, Field(default="", description="Result reason")] = ""
        message: Annotated[
            str,
            Field(default="", description="Human-readable summary message"),
        ] = ""
        site_dir: Annotated[
            str,
            Field(default="", description="Built site directory path"),
        ] = ""
        checks: Annotated[
            t.StrSequence,
            Field(description="Executed checks"),
        ] = Field(default_factory=list)
        strict: Annotated[
            bool,
            Field(default=False, description="Strict-mode flag"),
        ] = False
        passed: Annotated[
            bool,
            Field(default=False, description="Whether phase passed"),
        ] = False
        changed_files: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Changed files count"),
        ] = 0
        applied: Annotated[
            bool,
            Field(default=False, description="Apply mode flag"),
        ] = False
        generated: Annotated[
            t.NonNegativeInt,
            Field(default=0, description="Generated files count"),
        ] = 0
        source: Annotated[
            str,
            Field(
                default="",
                description="Source marker for generated content",
            ),
        ] = ""
        missing_adr_skills: Annotated[
            t.StrSequence,
            Field(
                description="Missing ADR skill references",
            ),
        ] = Field(default_factory=list)
        todo_written: Annotated[
            bool,
            Field(
                default=False,
                description="Whether TODOS.md was written",
            ),
        ] = False
        items: Annotated[
            Sequence[FlextInfraDocsModels.DocsPhaseItemModel],
            Field(description="Phase-specific item payloads"),
        ] = Field(
            default_factory=_docs_phase_items,
            description="Phase-specific item payloads",
        )


__all__ = ["FlextInfraDocsModels"]
