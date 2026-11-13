# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/templates
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols._config import FlextInfraProtocolsConfigScaffold


class FlextInfraProtocolsConfigTemplates:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenVscodeSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def settings(self) -> t.Infra.SettingsPairs:
            """Ordered VS Code key/value pairs; the last key wins."""
            ...

        @property
        def runtime_environment_token(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Declared generation token replaced by the topology-owned environment
            path, relative to the opened workspace folder.
            """
            ...

        @property
        def map_union_settings(self) -> Mapping[str, t.JsonMapping]:
            """VS Code objects union-merged over project settings."""
            ...

        @property
        def stripped_keys(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            VS Code keys actively stripped from the settings projection because they
            conflict with a pyrightconfig.json/pyproject.toml owner (Pylance
            settingsNotOverridable).
            """
            ...

        @property
        def stripped_map_keys(self) -> Mapping[str, tuple[str, ...]]:
            """Retired keys inside language-specific setting maps."""
            ...

    @runtime_checkable
    class CodegenVscodeDeclarationDelta(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def values(self) -> t.JsonMapping:
            """Minimal typed codegen.vscode declaration overrides."""
            ...

    @runtime_checkable
    class CodegenLayerProjection(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Exact target config layer."""
            ...

        @property
        def values(self) -> t.JsonMapping:
            """JSON-compatible declaration fragment."""
            ...

    @runtime_checkable
    class ConfigDocumentInputs(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def values(self) -> t.JsonMapping:
            """Strictly parsed and ordered configuration document."""
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Exact physical files consulted by this document."""
            ...

    @runtime_checkable
    class ManagedFileOwnership(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def owner(self) -> t.NonEmptyStr:
            """Canonical owner."""
            ...

        @property
        def tracking(self) -> Literal["versioned", "runtime-local"]:
            """Versioned declaration or checkout-local projection."""
            ...

        @property
        def policy(self) -> Literal["full", "merge"]:
            """Structural member projected from the owning model.

            Full renders the whole file; merge keeps content outside the owner's
            declared sections.
            """
            ...

        @property
        def mode(self) -> int:
            """Exact permission bits owned by generated publication."""
            ...

        @property
        def conflict_sections(self) -> tuple[t.NonEmptyStr, ...]:
            """Dotted sections rendered by the canonical owner."""
            ...

        @property
        def preserve_project_keys(self) -> tuple[t.NonEmptyStr, ...]:
            """Authored PEP 621 project keys retained on merge."""
            ...

        @property
        def overwrite_project_keys(self) -> tuple[t.NonEmptyStr, ...]:
            """PEP 621 project keys replaced by generation."""
            ...

        @property
        def managed_tool_tables(self) -> tuple[str, ...]:
            """Derive tool-relative table paths from the owner's sections."""
            ...

    @runtime_checkable
    class TemplateDeclarationSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def source(self) -> Path | None:
            """Source relative to the selected template or package root."""
            ...

        @property
        def source_kind(self) -> Literal["template", "resource"]:
            """Render a template or project the original package asset."""
            ...

        @property
        def source_package(self) -> t.NonEmptyStr | None:
            """Explicit original package owner of a resource declaration."""
            ...

        @property
        def source_closure(self) -> tuple[Path, ...]:
            """Complete package-relative resource source closure."""
            ...

        @property
        def enforce(self) -> t.Infra.EnforcementIds:
            """Enforcement law ids the generated projection itself enforces."""
            ...

        @property
        def requires_artifacts(self) -> tuple[t.NonEmptyStr, ...]:
            """Catalog destination keys required by this artifact."""
            ...

        @property
        def profiles(self) -> tuple[c.Infra.MakeProfile, ...]:
            """Profiles that consume the artifact."""
            ...

        @property
        def ownership(
            self,
        ) -> FlextInfraProtocolsConfigTemplates.ManagedFileOwnership | None:
            """Structural member projected from the owning model.

            Explicit generated-file ownership, or null for an authored project-
            creation seed.
            """
            ...

        @property
        def requires_release_protocol(self) -> bool:
            """Structural member projected from the owning model.

            Whether this projection requires the repository's explicit release-
            protocol opt-in.
            """
            ...

        @property
        def requires_beads(self) -> bool:
            """Whether the projection requires Beads participation."""
            ...

        @property
        def requires_package(self) -> bool:
            """Structural member projected from the owning model.

            Whether the seed belongs to the repository's own import package; a
            consumer repository owns none.
            """
            ...

        @property
        def bootstrap_distribution(self) -> t.NonEmptyStr | None:
            """Executor whose local dependency closure this artifact binds."""
            ...

    @runtime_checkable
    class TemplateEntrySpec(TemplateDeclarationSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def destination(self) -> t.NonEmptyStr:
            """Tokenized repository-relative destination."""
            ...

    @runtime_checkable
    class TemplatesSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Package-relative template root."""
            ...

        @property
        def catalog(
            self,
        ) -> Mapping[
            t.NonEmptyStr, FlextInfraProtocolsConfigTemplates.TemplateDeclarationSpec
        ]:
            """Ordered template bodies keyed by destination."""
            ...

        @cached_property
        def entries(
            self,
        ) -> tuple[FlextInfraProtocolsConfigTemplates.TemplateEntrySpec, ...]:
            """Structural member projected from the owning model.

            Expose the typed consumer view, validated once per catalog instance.
            """
            ...

        @property
        def artifact_requirements(self) -> Mapping[str, Sequence[str]]:
            """Expose each catalog key's declared artifact dependencies."""
            ...

        @cached_property
        def artifact_order(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Order every artifact dependencies-first, proving the graph acyclic.
            """
            ...

        def artifact_closure(self, destinations: frozenset[str]) -> frozenset[str]:
            """Structural member projected from the owning model.

            Return the destinations with every artifact they transitively require.
            """
            ...

        @property
        def bootstrap_entry(
            self,
        ) -> FlextInfraProtocolsConfigTemplates.TemplateEntrySpec:
            """Require the single declared executor bootstrap artifact."""
            ...

    @runtime_checkable
    class ManagedFileSpec(ManagedFileOwnership, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Repository-relative file path."""
            ...

    @runtime_checkable
    class GitignoreRenderContext(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraProtocolsConfigScaffold.ScaffoldGitignoreSectionSpec, ...]:
            """Applicable Git ignore sections."""
            ...

    @runtime_checkable
    class GitignoreRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraProtocolsConfigScaffold.ScaffoldGitignoreSectionSpec, ...]:
            """Canonical ignore sections applicable to one profile."""
            ...

    @runtime_checkable
    class StaticTextRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""


__all__: list[str] = [
    "FlextInfraProtocolsConfigTemplates",
]
