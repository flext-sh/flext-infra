"""Typed immutable inputs for one documentation generation pass.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Self

from flext_core import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsBase
from flext_infra._models._config import (
    FlextInfraModelsConfigArtifact,
    FlextInfraModelsConfigWorkspace,
)


class FlextInfraModelsDocsGeneration:
    """Declaration-only documentation generation contracts."""

    class DocsRootInputs(m.FrozenModel):
        """Workspace-level inputs shared by the aggregate root page rendering."""

        workspace_contract: t.JsonMapping = m.Field(
            description="Validated workspace contract of the repository",
        )
        markdown_width: int = m.Field(
            gt=0,
            description="Prose width elected once for the destination repository",
        )
        exclude_docs: t.StrSequence = m.Field(
            default=(),
            description="Repository-relative publication exclusion globs from codegen",
        )

    class DocScope(FlextInfraModelsBase.FrozenArbitrary):
        """Documentation scope targeting a project or workspace root."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Scope name")]
        path: Annotated[Path, m.Field(description="Absolute lexical scope root")]
        report_dir: Annotated[
            Path,
            m.Field(description="Absolute lexical report output directory"),
        ]
        project_class: Annotated[
            str,
            m.Field(description="Docs scope classification"),
        ] = "root"
        package_name: Annotated[
            str,
            m.Field(description="Primary package name for scope"),
        ] = ""
        documentation_language: t.Infra.DocumentationLanguage = m.Field(
            default="en", description="Project-local generated documentation language"
        )

        governance_source: (
            FlextInfraModelsConfigWorkspace.CodegenBootstrapSource | None
        ) = m.Field(
            default=None, description="Captured source and ref owning governance links"
        )
        # Why (docs_audit_policy root-cause fix): a member-project scope inside
        # a larger declared workspace does not own the physical repository
        # (its docs policy file lives at the workspace root, not under
        # `path`). This override is the declared physical repository root for
        # that case; a self-contained scope (standalone project, workspace
        # root scope) leaves it absent and `repository_root` resolves to
        # `path` itself. No consumer re-derives this value heuristically.
        repository_root_override: Annotated[
            Path | None,
            m.Field(
                description=(
                    "Physical repository root when it differs from `path` "
                    "(a member project scope inside a declared workspace); "
                    "absent for a scope that owns its own docs policy"
                ),
            ),
        ] = None

        def documentation_text(self, message: c.Infra.DocumentationText) -> str:
            """Resolve one finite presentation message without changing source prose.

            Returns:
                The project-local message in its selected language.

            """
            return message.localized(self.documentation_language)

        @m.field_validator("path", "report_dir")
        @classmethod
        def _validate_absolute_lexical_path(cls, value: Path) -> Path:
            if not value.is_absolute() or ".." in value.parts:
                msg = f"docs scope path must be absolute and lexical: {value}"
                raise ValueError(msg)
            return value

        @m.field_validator("repository_root_override")
        @classmethod
        def _validate_absolute_lexical_repository_root_override(
            cls,
            value: Path | None,
        ) -> Path | None:
            if value is None:
                return None
            if not value.is_absolute() or ".." in value.parts:
                msg = (
                    "docs scope repository root override must be absolute "
                    f"and lexical: {value}"
                )
                raise ValueError(msg)
            return value

        @m.computed_field
        @property
        def repository_root(self) -> Path:
            """The physical repository root owning this scope's docs policy.

            Returns:
                The resulting ``Path``.

            """
            return (
                self.path
                if self.repository_root_override is None
                else self.repository_root_override
            )

        @m.model_validator(mode="after")
        def _validate_report_owner(self) -> Self:
            if not self.report_dir.is_relative_to(self.path):
                msg = f"docs report directory escapes its scope: {self.report_dir}"
                raise ValueError(msg)
            return self

        @m.model_validator(mode="after")
        def _validate_repository_root_owns_path(self) -> Self:
            if not self.path.is_relative_to(self.repository_root):
                msg = f"docs scope path escapes its repository root: {self.path}"
                raise ValueError(msg)
            return self

    class DocsRenderedArtifact(FlextInfraModelsBase.FrozenArbitrary):
        """One immutable desired docs artifact relative to its owning scope."""

        relative_path: Annotated[
            Path,
            m.Field(description="Normalized scope-relative destination"),
        ]
        desired_content: Annotated[
            bytes | None,
            m.Field(description="Exact desired bytes, or absence"),
        ]
        desired_mode: Annotated[
            Literal[0o644] | None,
            m.Field(description="Exact desired mode, or absence"),
        ]

        @m.field_validator("relative_path")
        @classmethod
        def _validate_relative_path(cls, value: Path) -> Path:
            if (
                value.is_absolute()
                or not value.parts
                or value.as_posix() in {"", "."}
                or ".." in value.parts
            ):
                msg = f"unsafe docs artifact selector: {value}"
                raise ValueError(msg)
            return value

        @m.model_validator(mode="after")
        def _validate_desired_tuple(self) -> Self:
            if (self.desired_content is None) != (self.desired_mode is None):
                msg = "docs artifact content and mode must be present together"
                raise ValueError(msg)
            return self

    class DocsScopeArtifacts(FlextInfraModelsBase.FrozenArbitrary):
        """One scope paired with its complete rendered artifact inventory."""

        scope: Annotated[
            FlextInfraModelsDocsGeneration.DocScope,
            m.Field(description="Exact scope that owns every relative artifact"),
        ]
        artifacts: Annotated[
            tuple[FlextInfraModelsDocsGeneration.DocsRenderedArtifact, ...],
            m.Field(description="Complete ordered desired artifact inventory"),
        ]

    class DocsGenerationBundle(FlextInfraModelsBase.FrozenArbitrary):
        """Single render consumed through publication."""

        scopes: Annotated[
            tuple[FlextInfraModelsDocsGeneration.DocsScopeArtifacts, ...],
            m.Field(min_length=1, description="Ordered selected scope inventories"),
        ]
        metadata_files: t.VariadicTuple[
            FlextInfraModelsConfigArtifact.CodegenFilePlan
        ] = m.Field(default=(), description="Owned metadata published with this render")
        # The workspace root stays explicit: it may be excluded from `scopes`
        # (DECLARED conform scope), so it cannot be inferred from `scopes[0]`.
        repository_root: Annotated[
            Path,
            m.Field(description="Absolute lexical physical workspace root"),
        ]

        @m.field_validator("repository_root")
        @classmethod
        def _validate_absolute_repository_root(cls, value: Path) -> Path:
            if not value.is_absolute() or ".." in value.parts:
                msg = (
                    "docs generation repository root must "
                    f"be absolute and lexical: {value}"
                )
                raise ValueError(msg)
            return value

        @m.model_validator(mode="after")
        def _validate_unique_complete_inputs(self) -> Self:
            scope_names = tuple(item.scope.name for item in self.scopes)
            if len(set(scope_names)) != len(scope_names):
                msg = "docs generation scope names must be unique"
                raise ValueError(msg)
            destinations = tuple(
                item.scope.path / artifact.relative_path
                for item in self.scopes
                for artifact in item.artifacts
            )
            metadata_paths = tuple(plan.path for plan in self.metadata_files)
            allowed_metadata = {
                item.scope.path / c.PYPROJECT_FILENAME for item in self.scopes
            }
            if any(path not in allowed_metadata for path in metadata_paths):
                msg = "docs metadata target is outside its selected scope"
                raise ValueError(msg)
            destinations = (*destinations, *metadata_paths)
            if len(set(destinations)) != len(destinations):
                msg = "docs generation destinations must be unique"
                raise ValueError(msg)
            return self


__all__: list[str] = ["FlextInfraModelsDocsGeneration"]
