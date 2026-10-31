"""Shared model mixins for flext-infra contracts and CLI payloads.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m, t

from flext_infra import c


class FlextInfraModelsMixins:
    """Centralized reusable field and helper mixins for models.

    Structure (flat — no sub-namespaces): CLI parameter mixins, field
    contract mixins, violation/detail mixins, release mixins, github
    mixins, and project-name variants. All exposed directly under
    ``FlextInfraModelsMixins.<Mixin>`` for consumers.
    """

    # ═══════════════════ CLI PARAMETER MIXINS ═══════════════════

    class ModuleSelectionMixin(m.BaseModel):
        """Optional module selection consumed by a scoped operation."""

        module: Annotated[
            str | None,
            m.Field(
                description=(
                    "Dotted module path to scope verb to a single module "
                    "(e.g. flext_core.result). Mutually compatible with "
                    "--projects/--repository-root; narrows the run."
                ),
            ),
        ] = None

    class NamespaceSelectionMixin(m.BaseModel):
        """Optional facade namespace selection consumed by a scoped operation."""

        namespace: Annotated[
            str | None,
            m.Field(
                description=(
                    "Alias namespace (c|m|p|t|u|r|e|h|s|x[.<Domain>]) to scope "
                    "the verb to a single facade slot."
                ),
            ),
        ] = None

    class ScopeMixin(m.BaseModel):
        """Canonical CLI scope contract — workspace + project selection.

        Consolidates the former ``BaseMixin`` and ``ProjectMixin``
        surfaces into a single flat mixin used by every read/write
        command.
        """

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(populate_by_name=True)

        repository_root: Annotated[
            Path,
            m.BeforeValidator(lambda value: Path(value).resolve()),
            m.Field(description="Repository root"),
        ] = Path()
        projects: Annotated[
            Sequence[str] | None,
            m.BeforeValidator(
                lambda value: (value,) if isinstance(value, str) else value
            ),
            m.Field(
                description="Projects to process; repeat --projects NAME as needed",
            ),
        ] = None
        verbose: Annotated[bool, m.Field(description="Verbose output")] = False

    class ReadMixin(ScopeMixin):
        """Read-only commands — report file + output directory only.

        Previous ``check`` and ``json_output`` fields removed (YAGNI —
        single canonical report path and a directory for multi-file
        outputs).
        """

        report: Annotated[
            str | None,
            m.Field(description="Output report file path"),
        ] = None
        output_dir: Annotated[
            str | None,
            m.Field(description="Output directory for reports"),
        ] = None

    class WriteMixin(ScopeMixin):
        """Canonical write contract — apply/dry-run + safety gates.

        Gates are stored as ``Sequence[str]`` — CSV strings are parsed
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
        gates: Sequence[str] = m.Field(
            default=(),
            description=(
                "Gate names for post-transform validation; empty resolves the"
                " requested gate set from the typed Make spec at runtime."
            ),
        )

        @m.field_validator("gates", mode="before")
        @classmethod
        def _parse_gates(cls, value: str | Sequence[str] | None) -> Sequence[str]:
            """Accept CSV string, sequence, or None; normalize to Sequence[str].

            Returns:
                The resulting ``Sequence[str]``.

            """
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

        @m.computed_field
        @property
        def dry_run(self) -> bool:
            """Whether writes are disabled (inverse of apply).

            Returns:
                The resulting ``bool``.

            """
            return not self.apply

    # ═══════════════════ RELEASE MIXINS ═══════════════════

    class VersionTagMixin(m.BaseModel):
        """Shared release identity fields."""

        version: Annotated[str, m.Field(description="Version string")] = ""
        tag: Annotated[str, m.Field(description="Git tag (e.g. v1.0.0)")] = ""

    # ═══════════════════ FIELD CONTRACT MIXINS ═══════════════════

    class FilePathMixin(m.BaseModel):
        """Shared required file path field."""

        file: Annotated[t.NonEmptyStr, m.Field(description="File path")]

    class AbsoluteFilePathTextMixin(m.BaseModel):
        """Shared absolute file-path text field."""

        file_path: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]

    class PositiveLineMixin(m.BaseModel):
        """Shared positive line-number field."""

        line: Annotated[t.PositiveInt, m.Field(description="Line number")]

    class RequiredNonNegativeLineMixin(m.BaseModel):
        """Shared required non-negative line-number field."""

        line: Annotated[t.NonNegativeInt, m.Field(description="Line number")]

    class NonNegativeLineMixin(m.BaseModel):
        """Shared non-negative line-number field with default zero."""

        line: Annotated[t.NonNegativeInt, m.Field(description="Line number")] = 0

    class NestedClassPathMixin(m.BaseModel):
        """Shared optional nested class-path field."""

        class_path: Annotated[str, m.Field(description="Nested class path")] = ""

    class FileLineViolationMixin(FilePathMixin, PositiveLineMixin):
        """Shared file plus positive line fields for violations."""

    class CurrentImportMixin(m.BaseModel):
        """Shared current import statement field."""

        current_import: Annotated[str, m.Field(description="Current import statement")]

    # ═══════════════════ VIOLATION/DETAIL MIXINS ═══════════════════

    class ErrorDetailMixin(m.BaseModel):
        """Shared error detail field."""

        detail: Annotated[str, m.Field(description="Error detail")] = ""

    # ═══════════════════ PROJECT NAME / PATH VARIANTS ═══════════════════

    class ProjectNameMixin(m.BaseModel):
        """Shared required project-name field."""

        project: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class ProjectEntryNameMixin(m.BaseModel):
        """Shared required project entry name field."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project name")]

    class RepositoryRootPathMixin(m.BaseModel):
        """Shared repository root path field."""

        repository_root: Annotated[Path, m.Field(description="Repository root path")]

    class ProjectNamesOptionalMixin(m.BaseModel):
        """Shared optional project-name collection."""

        project_names: Annotated[
            Sequence[str] | None,
            m.Field(description="Project names"),
        ] = None

    class ProjectNamesListMixin(m.BaseModel):
        """Shared concrete project-name collection."""

        project_names: Sequence[str] = m.Field(
            default_factory=tuple, description="Project names"
        )


__all__: list[str] = ["FlextInfraModelsMixins"]
