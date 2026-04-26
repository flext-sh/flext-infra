"""Shared model mixins for flext-infra contracts and CLI payloads."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from flext_cli import m, u
from flext_infra import (
    FlextInfraUtilitiesBase as ub,
    c,
    t,
)


class FlextInfraModelsMixins:
    """Centralized reusable field and helper mixins for models.

    Structure (flat — no sub-namespaces): CLI parameter mixins, field
    contract mixins, violation/detail mixins, release mixins, github
    mixins, and project-name variants. All exposed directly under
    ``mm.<Mixin>`` for consumers.
    """

    # ═══════════════════ CLI PARAMETER MIXINS ═══════════════════

    class ScopeMixin:
        """Canonical CLI scope contract — workspace + project selection.

        Consolidates the former ``BaseMixin`` and ``ProjectMixin``
        surfaces into a single flat mixin used by every read/write
        command.
        """

        model_config = m.ConfigDict(populate_by_name=True)

        workspace: Annotated[
            str,
            m.Field(
                alias="workspace",
                validation_alias=t.AliasChoices("workspace", "workspace_path"),
                description="Workspace root",
            ),
        ] = "."
        projects: Annotated[
            t.StrSequence | None,
            m.Field(
                description="Projects to process; repeat --projects NAME as needed",
            ),
        ] = None
        module: Annotated[
            str | None,
            m.Field(
                description=(
                    "Dotted module path to scope verb to a single module "
                    "(e.g. flext_core.result). Mutually compatible with "
                    "--projects/--workspace; narrows the run."
                ),
            ),
        ] = None
        namespace: Annotated[
            str | None,
            m.Field(
                description=(
                    "Alias namespace (c|m|p|t|u|r|e|h|s|x[.<Domain>]) to scope "
                    "the verb to a single facade slot."
                ),
            ),
        ] = None
        fail_fast: Annotated[bool, m.Field(description="Stop on first failure")] = True
        verbose: Annotated[bool, m.Field(description="Verbose output")] = False

        @property
        def workspace_path(self) -> Path:
            """Return the resolved workspace path for CLI execution."""
            return Path(self.workspace).resolve()

        @property
        def project_names(self) -> t.StrSequence | None:
            """Return normalized project names from repeated selectors."""
            return ub.normalize_sequence_values(self.projects)

    class ReadMixin(ScopeMixin):
        """Read-only commands — report file + output directory only.

        Previous ``check`` and ``json_output`` fields removed (YAGNI —
        single canonical report path and a directory for multi-file
        outputs).
        """

        report: Annotated[
            str | None, m.Field(description="Output report file path")
        ] = None
        output_dir: Annotated[
            str | None, m.Field(description="Output directory for reports")
        ] = None

        @property
        def report_path(self) -> Path | None:
            """Return the resolved report path when provided."""
            return ub.normalize_optional_path(self.report)

        @property
        def output_dir_path(self) -> Path | None:
            """Return the resolved output directory when provided."""
            return ub.normalize_optional_path(self.output_dir)

    class WriteMixin(ScopeMixin):
        """Canonical write contract — apply/dry-run + safety gates.

        Gates are stored as ``t.StrSequence`` — CSV strings are parsed
        by ``@field_validator`` so downstream consumers always see a
        normalized list.
        """

        apply: Annotated[
            bool,
            m.Field(
                description="Apply changes instead of running in dry-run mode",
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
            t.StrSequence,
            m.Field(
                default_factory=lambda: tuple(
                    gate.strip()
                    for gate in c.Infra.SAFE_EXECUTION_DEFAULT_GATES.split(",")
                    if gate.strip()
                ),
                description="Gate names for post-transform validation",
            ),
        ]

        @u.field_validator("gates", mode="before")
        @classmethod
        def _parse_gates(
            cls,
            value: str | Sequence[str] | None,
        ) -> t.StrSequence:
            """Accept CSV string, sequence, or None; normalize to StrSequence."""
            if value is None:
                return ()
            if isinstance(value, str):
                return tuple(part.strip() for part in value.split(",") if part.strip())
            normalized: list[str] = []
            for part in value:
                if not part:
                    continue
                normalized.extend(
                    token.strip() for token in part.split(",") if token.strip()
                )
            return tuple(normalized)

        @u.computed_field()
        @property
        def dry_run(self) -> bool:
            """Whether writes are disabled (inverse of apply)."""
            return not self.apply

        @u.computed_field()
        @property
        def execution_mode(self) -> c.Infra.ExecutionMode:
            """Resolve execution mode from CLI flags."""
            if not self.apply:
                return c.Infra.ExecutionMode.DRY_RUN
            if self.rollback:
                return c.Infra.ExecutionMode.APPLY_SAFE
            return c.Infra.ExecutionMode.APPLY_FORCE

    # ═══════════════════ RELEASE MIXINS ═══════════════════

    class VersionTagMixin:
        """Shared release identity fields."""

        version: Annotated[str, m.Field(description="Version string")] = ""
        tag: Annotated[str, m.Field(description="Git tag (e.g. v1.0.0)")] = ""

    class AutomationMixin:
        """Shared release automation toggles."""

        push: Annotated[bool, m.Field(description="Push to remote")] = False
        dev_suffix: Annotated[bool, m.Field(description="Add dev suffix")] = False

    # ═══════════════════ GITHUB REQUEST MIXINS ═══════════════════

    class WorkspaceCliRequestMixin:
        """CLI workspace request fields — branch/checkpoint + canonical fail-fast.

        Merged surface of the former ``GithubWorkspaceRequestMixin`` +
        ``GithubWorkspaceCliRequestMixin``. ``fail_fast`` default aligned
        to the canonical ``ScopeMixin`` value (``True``); commands that
        need the legacy ``False`` declare it locally.
        """

        include_root: Annotated[bool, m.Field(description="Include root project")] = (
            False
        )
        branch: Annotated[str, m.Field(description="Branch name filter")] = ""
        checkpoint: Annotated[bool, m.Field(description="Enable checkpoints")] = True
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

    # ═══════════════════ FIELD CONTRACT MIXINS ═══════════════════

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

    # ═══════════════════ VIOLATION/DETAIL MIXINS ═══════════════════

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

    # ═══════════════════ PROJECT NAME / PATH VARIANTS ═══════════════════

    class ProjectNameMixin:
        """Shared required project-name field."""

        project: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class ProjectEntryNameMixin:
        """Shared required project entry name field."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class ProjectNameFieldMixin:
        """Shared required project_name field."""

        project_name: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

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
            m.Field(default_factory=tuple),
        ] = m.Field(default_factory=tuple)


__all__: list[str] = ["FlextInfraModelsMixins"]
