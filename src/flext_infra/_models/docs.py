"""Domain models for the docs subpackage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, ClassVar

from flext_cli import m
from flext_infra.constants import c

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraModelsDocs:
    """Models for documentation services."""

    class DocsGenerateRequest(m.ContractModel):
        """Canonical docs generation request payload.

        Consolidates generate-call parameters into one typed contract so callers
        reuse the same validation rules and avoid ad-hoc multi-parameter calls.
        """

        workspace_root: Annotated[
            Path,
            m.Field(description="Workspace root for docs generation"),
        ]
        projects: Annotated[
            t.StrSequence | None,
            m.Field(description="Optional selected project names"),
        ] = None
        output_dir: Annotated[
            Path | str | None,
            m.Field(description="Optional docs output directory override"),
        ] = Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR)
        apply: Annotated[bool, m.Field(description="Apply writes to disk")] = False

    class DocsPhaseItemModel(m.BaseModel):
        """Unified item payload for docs phase reports."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            strict=True,
        )

        phase: Annotated[
            str,
            m.Field(description="Docs phase: audit, fix, build, generate, validate"),
        ]
        file: Annotated[str, m.Field(description="Relative file path")] = ""
        issue_type: Annotated[str, m.Field(description="Audit issue type")] = ""
        severity: Annotated[str, m.Field(description="Audit issue severity")] = ""
        message: Annotated[str, m.Field(description="Item detail message")] = ""
        links: Annotated[
            t.NonNegativeInt,
            m.Field(description="Applied link fixes"),
        ] = 0
        toc: Annotated[t.NonNegativeInt, m.Field(description="Applied TOC updates")] = 0
        codeblocks: Annotated[
            t.NonNegativeInt,
            m.Field(description="Applied python codeblock fixes"),
        ] = 0
        path: Annotated[str, m.Field(description="Generated file path")] = ""
        written: Annotated[bool, m.Field(description="Generated file write flag")] = (
            False
        )

    class DocScope(m.ArbitraryTypesModel):
        """Documentation scope targeting a project or workspace root."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Scope name")]
        path: Annotated[Path, m.Field(description="Absolute path to scope root")]
        report_dir: Annotated[
            Path,
            m.Field(description="Report output directory for scope"),
        ]
        project_class: Annotated[
            str,
            m.Field(description="Docs scope classification"),
        ] = "root"
        package_name: Annotated[
            str,
            m.Field(description="Primary package name for scope"),
        ] = ""

    class AuditIssue(m.ContractModel):
        """Single documentation audit finding."""

        file: Annotated[str, m.Field(description="File path relative to scope")]
        issue_type: Annotated[str, m.Field(description="Issue category")]
        severity: Annotated[str, m.Field(description="Issue severity")]
        message: Annotated[str, m.Field(description="Issue description")]

    class DocsProjectMeta(m.ContractModel):
        """Typed view over pyproject + docs metadata used to build public contracts.

        Single source of truth for the metadata bundle ``public_contract``
        passes between its own helpers; replaces the prior dict-of-Any
        approach so callers get strict typing for free. All payload fields
        are required — callers always populate them — so no mutable
        ``default_factory`` is needed.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            arbitrary_types_allowed=True,
        )

        project_meta: Annotated[
            t.Infra.ContainerDict,
            m.Field(description="Pyproject ``[project]`` table"),
        ]
        docs_meta: Annotated[
            t.Infra.ContainerDict,
            m.Field(description="Pyproject ``[tool.flext.docs]`` table"),
        ]
        exclude_docs: Annotated[
            t.StrSequence,
            m.Field(description="Docs paths excluded from generation"),
        ]
        site_title: Annotated[str, m.Field(description="Resolved site title")] = ""
        site_url: Annotated[str, m.Field(description="Resolved site URL")] = ""
        repo_url: Annotated[str, m.Field(description="Resolved repository URL")] = ""
        description: Annotated[str, m.Field(description="Project description")] = ""
        version: Annotated[str, m.Field(description="Project version")] = ""

    class GeneratedFile(m.ContractModel):
        """Record of a generated file operation."""

        path: Annotated[str, m.Field(description="File path")]
        written: Annotated[bool, m.Field(description="Whether file was written")] = (
            False
        )

    class AuditScopeParams(m.ContractModel):
        """Bundled parameters for a single audit scope run."""

        check: Annotated[str, m.Field(description="Comma-separated checks")] = "all"
        strict: Annotated[bool, m.Field(description="Strict mode")] = True
        budgets: Annotated[
            tuple[int | None, t.IntMapping] | None,
            m.Field(description="Budget tuple (default, by_scope)"),
        ] = None

    class DocsPhaseReport(m.ContractModel):
        """Unified report payload for docs phases."""

        @staticmethod
        def _items_default() -> list[FlextInfraModelsDocs.DocsPhaseItemModel]:
            """Items default."""
            return []

        phase: Annotated[
            str,
            m.Field(
                description="Docs phase: audit, fix, build, generate, validate",
            ),
        ]
        scope: Annotated[str, m.Field(description="Scope name")]
        result: Annotated[str, m.Field(description="Result status")] = ""
        reason: Annotated[str, m.Field(description="Result reason")] = ""
        message: Annotated[
            str,
            m.Field(description="Human-readable summary message"),
        ] = ""
        site_dir: Annotated[str, m.Field(description="Built site directory path")] = ""
        checks: Annotated[
            t.StrSequence,
            m.Field(description="Executed checks"),
        ] = m.Field(default_factory=tuple)
        strict: Annotated[bool, m.Field(description="Strict-mode flag")] = False
        passed: Annotated[bool, m.Field(description="Whether phase passed")] = False
        changed_files: Annotated[
            t.NonNegativeInt,
            m.Field(description="Changed files count"),
        ] = 0
        applied: Annotated[bool, m.Field(description="Apply mode flag")] = False
        generated: Annotated[
            t.NonNegativeInt,
            m.Field(description="Generated files count"),
        ] = 0
        source: Annotated[
            str,
            m.Field(
                description="Source marker for generated content",
            ),
        ] = ""
        missing_adr_skills: Annotated[
            t.StrSequence,
            m.Field(
                description="Missing ADR skill references",
            ),
        ] = m.Field(default_factory=tuple)
        todo_written: Annotated[
            bool,
            m.Field(
                description="Whether TODOS.md was written",
            ),
        ] = False
        items: Annotated[
            t.SequenceOf[FlextInfraModelsDocs.DocsPhaseItemModel],
            m.Field(
                description="Phase-specific item payloads",
            ),
        ] = m.Field(default_factory=_items_default)


__all__: list[str] = ["FlextInfraModelsDocs"]
