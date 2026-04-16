"""Shared model mixins for flext-infra contracts and CLI payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import AliasChoices, ConfigDict, computed_field

from flext_core import m
from flext_infra import c, t


class FlextInfraModelsMixins:
    """Centralized reusable field and helper mixins for _models."""

    # ── Hierarchy: BaseMixin → ProjectMixin → ReadMixin / WriteMixin ──

    class BaseMixin:
        """Foundation for all CLI commands: workspace path and verbose flag."""

        model_config = ConfigDict(populate_by_name=True)

        workspace: Annotated[
            str,
            m.Field(
                alias="workspace",
                validation_alias=AliasChoices("workspace", "workspace_path"),
                description="Workspace root",
            ),
        ] = "."
        verbose: Annotated[bool, m.Field(description="Verbose output")] = False

        @property
        def workspace_path(self) -> Path:
            """Return the resolved workspace path for CLI execution."""
            return Path(self.workspace).resolve()

        @staticmethod
        def resolve_optional_path(value: str | None) -> Path | None:
            """Resolve an optional path string when present."""
            return Path(value).resolve() if value else None

        @staticmethod
        def split_csv_values(*values: str | None) -> t.StrSequence:
            """Normalize comma-separated CLI values into a compact list."""
            return [
                item.strip()
                for value in values
                for group in (value or "").split(",")
                for item in group.split()
                if item.strip()
            ]

    class ProjectMixin(BaseMixin):
        """Commands that operate on one or more projects."""

        projects: Annotated[
            t.StrSequence | None,
            m.Field(
                description="Projects to process; repeat --projects NAME as needed",
            ),
        ] = None
        fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = True

        @property
        def project_names(self) -> t.StrSequence | None:
            """Return normalized project names from repeated selectors."""
            names = FlextInfraModelsMixins.BaseMixin.split_csv_values(
                *(self.projects or ()),
            )
            return names or None

    class ReadMixin(ProjectMixin):
        """Read-only commands with output configuration."""

        check: Annotated[bool, m.Field(description="Enable check mode")] = False
        output_dir: Annotated[
            str | None, m.Field(description="Output directory for reports")
        ] = None
        report: Annotated[str | None, m.Field(description="Output report file")] = None
        json_output: Annotated[
            str | None, m.Field(description="Path to write JSON report")
        ] = None

        @property
        def output_dir_path(self) -> Path | None:
            """Return the resolved output directory when provided."""
            return self.resolve_optional_path(self.output_dir)

        @property
        def report_path(self) -> Path | None:
            """Return the resolved report path when provided."""
            return self.resolve_optional_path(self.report)

        @property
        def json_output_path(self) -> Path | None:
            """Return the resolved JSON export path when provided."""
            return self.resolve_optional_path(self.json_output)

    class WriteMixin(ProjectMixin):
        """Commands that modify files with safety and rollback support."""

        apply: Annotated[
            bool,
            m.Field(
                description="Apply changes",
                json_schema_extra={
                    "typer_param_decls": list(c.Infra.CLI_APPLY_OPTION_DECLS),
                },
            ),
        ] = False
        diff: Annotated[bool, m.Field(description="Show diff without applying")] = False
        rollback: Annotated[
            bool, m.Field(description="Enable automatic rollback on gate failure")
        ] = True
        gates: Annotated[
            str,
            m.Field(
                description="Comma-separated gate names for post-transform validation",
            ),
        ] = c.Infra.SAFE_EXECUTION_DEFAULT_GATES

        @computed_field
        @property
        def dry_run(self) -> bool:
            """Whether writes are disabled (inverse of apply)."""
            return not self.apply

        @computed_field
        @property
        def execution_mode(self) -> c.Infra.ExecutionMode:
            """Resolve execution mode from CLI flags."""
            if not self.apply:
                return c.Infra.ExecutionMode.DRY_RUN
            if self.rollback:
                return c.Infra.ExecutionMode.APPLY_SAFE
            return c.Infra.ExecutionMode.APPLY_FORCE

    # ── Specialized mixins that extend WriteMixin ──

    class AliasSelectionMixin(WriteMixin):
        """Comma-separated canonical alias selector."""

        aliases: Annotated[
            str,
            m.Field(
                description="Comma-separated canonical aliases to normalize to local MRO imports",
            ),
        ] = "r,s"

        @property
        def alias_names(self) -> t.StrSequence:
            """Return normalized runtime alias names."""
            return self.split_csv_values(self.aliases)

    class ReleasePhaseMixin(WriteMixin):
        """Release phase selector with normalized expansion."""

        phase: Annotated[str, m.Field(description="Release phase")] = "all"

        @property
        def phase_names(self) -> t.StrSequence:
            """Return the normalized phase sequence for release execution."""
            if self.phase == "all":
                return [
                    c.Infra.VERB_VALIDATE,
                    c.Infra.VERSION,
                    c.Infra.DIR_BUILD,
                    c.Infra.VERB_PUBLISH,
                ]
            return self.split_csv_values(self.phase)

    class MakeArgMixin(WriteMixin):
        """Repeated --make-arg option with normalized accessor."""

        make_arg: Annotated[
            t.StrSequence,
            m.Field(
                default_factory=list,
                description="Additional make arguments; repeat --make-arg KEY=VALUE",
            ),
        ] = m.Field(
            default_factory=list,
            description="Additional make arguments; repeat --make-arg KEY=VALUE",
        )

        @property
        def make_args(self) -> t.StrSequence:
            """Return normalized make arguments without blank entries."""
            return [make_arg.strip() for make_arg in self.make_arg if make_arg.strip()]

    class CanonicalRootMixin(WriteMixin):
        """Canonical root selector with resolved accessor."""

        canonical_root: Annotated[
            str, m.Field(description="Canonical workspace root")
        ] = ""

        @property
        def canonical_root_path(self) -> Path | None:
            """Return the resolved canonical root when provided."""
            return self.resolve_optional_path(self.canonical_root)

    class GithubWorkspaceRequestMixin:
        """Shared branch/checkpoint flags for workspace GitHub requests."""

        include_root: Annotated[bool, m.Field(description="Include root project")] = (
            True
        )
        branch: Annotated[str, m.Field(description="Branch name filter")] = ""
        checkpoint: Annotated[bool, m.Field(description="Enable checkpoints")] = True
        fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = False

    class GithubWorkspaceCliRequestMixin(GithubWorkspaceRequestMixin):
        """CLI-specific defaults for workspace GitHub requests."""

        include_root: Annotated[bool, m.Field(description="Include root project")] = (
            False
        )
        fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = True

    class GithubPullRequestFieldsMixin:
        """Shared pull-request fields used by single and workspace requests."""

        action: Annotated[str, m.Field(description="PR action")] = "status"
        base: Annotated[str, m.Field(description="Base branch")] = "main"
        head: Annotated[str | None, m.Field(description="Head branch")] = None
        number: Annotated[int | None, m.Field(description="PR number")] = None
        title: Annotated[str | None, m.Field(description="PR title")] = None
        body: Annotated[str | None, m.Field(description="PR body")] = None
        draft: Annotated[bool, m.Field(description="Draft PR")] = False
        merge_method: Annotated[str, m.Field(description="Merge method")] = "squash"
        auto: Annotated[bool, m.Field(description="Auto-merge")] = False
        delete_branch: Annotated[
            bool, m.Field(description="Delete branch on merge")
        ] = True
        checks_strict: Annotated[
            bool, m.Field(description="Strict checks required")
        ] = True
        release_on_merge: Annotated[bool, m.Field(description="Release on merge")] = (
            True
        )

    class FilePathMixin:
        """Shared required file path field."""

        file: Annotated[t.NonEmptyStr, m.Field(description="File path")]

    class AbsoluteFilePathTextMixin:
        """Shared absolute file-path text field."""

        file_path: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]

    class PositiveLineMixin:
        """Shared positive line-number field."""

        line: Annotated[t.PositiveInt, m.Field(description="Line number")]

    class RequiredNonNegativeLineMixin:
        """Shared required non-negative line-number field."""

        line: Annotated[t.NonNegativeInt, m.Field(description="Line number")]

    class NonNegativeLineMixin:
        """Shared non-negative line-number field with default zero."""

        line: Annotated[t.NonNegativeInt, m.Field(description="Line number")] = 0

    class NestedClassPathMixin:
        """Shared optional nested class-path field."""

        class_path: Annotated[str, m.Field(description="Nested class path")] = ""

    class FileLineViolationMixin(FilePathMixin, PositiveLineMixin):
        """Shared file plus positive line fields for violations."""

    class CurrentImportMixin:
        """Shared current import statement field."""

        current_import: Annotated[str, m.Field(description="Current import statement")]

    class ViolationDetailMixin:
        """Shared violation detail field."""

        detail: Annotated[str, m.Field(description="Violation detail")] = ""

    class ErrorDetailMixin:
        """Shared error detail field."""

        detail: Annotated[str, m.Field(description="Error detail")] = ""

    class ConfidenceLevelMixin:
        """Shared confidence field for refactor diagnostics."""

        confidence: Annotated[str, m.Field(description="Confidence level")] = "low"

    class RewriteScopeMixin:
        """Shared rewrite-scope field for refactor diagnostics."""

        rewrite_scope: Annotated[str, m.Field(description="Rewrite scope")] = "file"

    class ReleaseVersionTagMixin:
        """Shared release identity fields."""

        version: Annotated[str, m.Field(description="Version string")] = ""
        tag: Annotated[str, m.Field(description="Git tag (e.g. v1.0.0)")] = ""

    class ReleaseAutomationMixin:
        """Shared release automation toggles."""

        push: Annotated[bool, m.Field(description="Push to remote")] = False
        dev_suffix: Annotated[bool, m.Field(description="Add dev suffix")] = False

    class ProjectNameMixin:
        """Shared required project-name field."""

        project: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class ProjectEntryNameMixin:
        """Shared required project entry name field."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class ProjectNameFieldMixin:
        """Shared required project_name field."""

        project_name: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class OptionalProjectNameFieldMixin:
        """Shared optional project_name field."""

        project_name: Annotated[str | None, m.Field(description="Project name")] = None

    class WorkspaceRootPathMixin:
        """Shared workspace root path field."""

        workspace_root: Annotated[Path, m.Field(description="Workspace root path")]

    class StashRefMixin:
        """Shared git stash reference field."""

        stash_ref: Annotated[str, m.Field(description="Git stash reference")] = ""

    class ProjectNamesOptionalMixin:
        """Shared optional project-name collection."""

        project_names: Annotated[
            t.StrSequence | None, m.Field(description="Project names")
        ] = None

    class ProjectNamesListMixin:
        """Shared concrete project-name collection."""

        project_names: Annotated[
            t.StrSequence,
            m.Field(default_factory=list, description="Project names"),
        ] = m.Field(default_factory=list, description="Project names")


__all__: list[str] = ["FlextInfraModelsMixins"]
