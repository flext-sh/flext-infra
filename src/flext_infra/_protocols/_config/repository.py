# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/repository
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigBeads,
        FlextInfraProtocolsConfigMake,
        FlextInfraProtocolsConfigTemplates,
    )


class FlextInfraProtocolsConfigRepository:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProjectIdentitySpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def flext_source(self) -> t.NonEmptyStr | None:
            """Direct Git infrastructure requirement declared for scaffolding."""
            ...

        @property
        def hatch_build_hook_path(self) -> Path | None:
            """Project-relative Hatch custom build hook module."""
            ...

        @property
        def package_name(self) -> t.NonEmptyStr:
            """Import package name."""
            ...

        @property
        def class_stem(self) -> t.NonEmptyStr:
            """Canonical public facade class stem."""
            ...

        @property
        def namespace(self) -> t.NonEmptyStr:
            """Nested c/t/p/m/u namespace."""
            ...

        @property
        def constant_name(self) -> t.NonEmptyStr:
            """Configured project name exposed through constants."""
            ...

        @property
        def namespace_attribute(self) -> t.NonEmptyStr:
            """Private module namespace token."""
            ...

        @property
        def alias(self) -> t.NonEmptyStr:
            """Canonical public instance alias."""
            ...

        @property
        def environment_prefix(self) -> t.NonEmptyStr:
            """Project settings environment prefix."""
            ...

        @property
        def description(self) -> t.NonEmptyStr:
            """Project description."""
            ...

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """Project-local generated documentation language."""
            ...

        @property
        def license(self) -> t.NonEmptyStr:
            """SPDX license id."""
            ...

        @property
        def author_name(self) -> t.NonEmptyStr:
            """Author display name."""
            ...

        @property
        def author_email(self) -> t.NonEmptyStr:
            """Author email."""
            ...

    @runtime_checkable
    class ProjectSpec(ProjectIdentitySpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def upstream(self) -> t.NonEmptyStr:
            """Upstream FLEXT facade module."""
            ...

        @property
        def namespace_scan_dirs(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Production source roots the namespace validator enforces; empty keeps
            every root in scope (previous behavior).
            """
            ...

        @property
        def inherited_facets(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Upstream facets re-exported by the project root. The lazy-init public-
            root planner reads this to decide which upstream namespace names the
            generated root __init__ may re-export: a facet is inherited when
            declared here or actually imported from source. Without the field the
            planner cannot honour a manifest declaration and re-exports only what
            source imports prove -- which silently drops manifest-declared facets.
            """
            ...

        @property
        def root_packages(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Additional top-level packages under the source directory that the
            distribution must ship beyond the primary package. Declared per
            repository because the layout is a fact of that repository, not of its
            upstream profile.
            """
            ...

        @property
        def repository_namespace_packages(self) -> tuple[t.NonEmptyStr, ...]:
            """Implicit namespace directories shipped from the repository root."""
            ...

        @property
        def root_modules(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Top-level single-file modules under the source directory shipped
            alongside the packages; see the root_packages namesake for why the
            declaration is per repository.
            """
            ...

        @property
        def packaged_data_paths(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Repository-relative data files and directories shipped with the package.
            """
            ...

        @property
        def packaged_data_excludes(self) -> tuple[t.NonEmptyStr, ...]:
            """Repository-relative files omitted from declared data directories."""
            ...

        @property
        def cli_module(self) -> bool:
            """Structural member projected from the owning model.

            Whether the package ships its cli entry module. A scaffold renders the
            cli seed in the same plan; an existing checkout derives the fact from
            its source tree. The default console script is declared only then,
            because conform loads every declared entry point in its fresh-import
            stage.
            """
            ...

        @property
        def console_scripts(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.ConsoleScriptSpec, ...]:
            """Structural member projected from the owning model.

            Console scripts this repository ships beside the default cli script,
            each rendered into [project.scripts].
            """
            ...

        @property
        def runtime_dependency_overlay(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Runtime requirements this repository adds ahead of its dependency
            profile's runtime set. The profile states what every project on that
            upstream needs; the overlay states what this one additionally needs, so
            neither owner has to encode the other's scope.
            """
            ...

        @property
        def homepage(self) -> t.NonEmptyStr:
            """Project homepage."""
            ...

        @property
        def documentation(self) -> t.NonEmptyStr:
            """Project documentation URL."""
            ...

        @property
        def repository_root_rel(self) -> t.NonEmptyStr:
            """Declared relative path to the workspace root."""
            ...

        @property
        def year(self) -> int:
            """Copyright year."""
            ...

    @runtime_checkable
    class WorkspaceIntegrationSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def provider(self) -> t.NonEmptyStr:
            """Configured provider key."""
            ...

        @property
        def branch(self) -> t.NonEmptyStr:
            """Workspace integration branch."""
            ...

        @property
        def organization(self) -> t.NonEmptyStr | None:
            """Optional provider organization override."""
            ...

        @property
        def base_url(self) -> t.NonEmptyStr | None:
            """Optional provider base URL override."""
            ...

    @runtime_checkable
    class RepositoryRefIdentity(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Original identity and policy observations."""
            ...

        @property
        def name(self) -> t.NonEmptyStr:
            """Catalog key."""
            ...

        @property
        def distribution(self) -> t.NonEmptyStr:
            """Python distribution or repository name."""
            ...

        @property
        def url(self) -> t.NonEmptyStr:
            """Canonical GitHub clone URL ending in .git."""
            ...

        @property
        def path(self) -> Path:
            """POSIX path relative to its workspace root."""
            ...

        @property
        def role(self) -> c.Infra.MakeProfile:
            """Repository role in the declared topology."""
            ...

        @property
        def state(self) -> c.Infra.RepositoryState:
            """Repository lifecycle state."""
            ...

        @property
        def checkout(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Physical checkout topology of the declared tree; 'root' marks the
            workspace's own primary checkout.
            """
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Provider key the declaring repository's own manifest carries."""
            ...

        @property
        def kind(self) -> c.Infra.ProjectKind:
            """Structural member projected from the owning model.

            Governance kind detected from native dependency and workspace-
            composition facts.
            """
            ...

    @runtime_checkable
    class RepositoryRef(RepositoryRefIdentity, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def codegen(self) -> c.Infra.CodegenKind:
            """Repository code-generation policy."""
            ...

        @property
        def package(self) -> bool:
            """Repository publishes a Python package."""
            ...

        @property
        def publishes_release(self) -> bool:
            """Structural member projected from the owning model.

            Whether this distribution explicitly opts into the generated release
            protocol.
            """
            ...

        @property
        def editable(self) -> bool:
            """Overlay repository as an editable dependency."""
            ...

        @property
        def read_only(self) -> bool:
            """Repository rejects generated mutations."""
            ...

        @property
        def uv_link_mode(
            self,
        ) -> Literal["clone", "copy", "hardlink", "symlink"] | None:
            """Structural member projected from the owning model.

            Repository-specific uv installation link mode; absent uses the fleet
            toolchain default.
            """
            ...

        @property
        def duplication_trees(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Project-relative directory trees the duplication gate must scan besides
            the canonical src/tests scope (e.g. declared Helm charts).
            """
            ...

        @property
        def examples_module(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Explicit dotted examples module with a repository-relative Python source
            file; absence does not select an entrypoint.
            """
            ...

        @property
        def extra_verbs(self) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Structural member projected from the owning model.

            Additional public Make verbs this repository dispatches beyond the
            canonical set (e.g. a script command framework).
            """
            ...

        @property
        def script_dispatch(
            self,
        ) -> FlextInfraProtocolsConfigRepository.ScriptDispatchSpec | None:
            """Structural member projected from the owning model.

            Opt-in script command-framework routing for non-builtin verbs and WHAT
            selectors; None keeps builtin-only dispatch.
            """
            ...

        @property
        def verb_groups(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbGroupSpec, ...]:
            """Structural member projected from the owning model.

            Ordered `make help` sections; empty keeps one flat listing and then no
            verb may name a section.
            """
            ...

    @runtime_checkable
    class RepositoryConformTarget(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> FlextInfraProtocolsConfigRepository.RepositoryRef:
            """Declared immutable repository identity."""
            ...

        @property
        def root(self) -> Path:
            """Resolved repository root receiving conformance."""
            ...

        @property
        def toolchain_root(self) -> Path:
            """Composition root owning the active generation toolchain."""
            ...

        @property
        def vscode_spec(
            self,
        ) -> FlextInfraProtocolsConfigTemplates.CodegenVscodeSpec | None:
            """Repository-rooted resolved editor declarations."""
            ...

        @property
        def vscode_sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Exact consulted editor declaration inputs."""
            ...

        @property
        def make_profile(self) -> c.Infra.MakeProfile:
            """Make profile inferred from live Git topology."""
            ...

        @property
        def beads(self) -> FlextInfraProtocolsConfigBeads.BeadsProjectSpec | None:
            """Repository-local Beads identity when enabled."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsConfigRepository.ProjectSpec | None:
            """Structural member projected from the owning model.

            Declared project metadata of the manifest, when the repository declares
            one; carries the distribution roots the packaging phase must prove
            present.
            """
            ...

        @property
        def canonical_project_name(self) -> t.NonEmptyStr:
            """Canonical PEP 621 project name."""
            ...

        @property
        def ci_enabled(self) -> bool:
            """Whether conform owns the CI projection."""
            ...

        @property
        def publishes_release(self) -> bool:
            """Whether conform renders release-protocol artifacts."""
            ...

        @property
        def gascity_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Whether the repository consumes the Gas City runtime contract; gates the
            gc tool projection and the inherited Dolt endpoint keys at render time.
            """
            ...

        @property
        def external_dependency_paths(self) -> tuple[Path, ...]:
            """Observed external or fork Git submodule paths."""
            ...

    @runtime_checkable
    class ConsoleScriptSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Console script name in [project.scripts]."""
            ...

        @property
        def target(self) -> t.NonEmptyStr:
            """Entry point reference module:attribute."""
            ...

    @runtime_checkable
    class ScriptDispatchSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def dispatcher(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Repository-relative dispatcher entrypoint that resolves
            scripts/<verb>/<what>.{py,sh} commands.
            """
            ...

        @property
        def roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Repository-relative script roots scanned for a matching <verb>/<what>
            command before falling back to a builtin.
            """
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigRepository",
]
