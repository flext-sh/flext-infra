# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/codegen_render
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import c, t
    from flext_infra._protocols import FlextInfraProtocolsMiseToolchain
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigMake,
        FlextInfraProtocolsConfigProvider,
        FlextInfraProtocolsConfigRender,
        FlextInfraProtocolsConfigRepository,
    )


class FlextInfraProtocolsCodegenRender:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModelProtocolRenderContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def header(self) -> str:
            """Existing generated-source ownership header."""
            ...

        @property
        def copyright_notice(self) -> str:
            """The owning project's legal notice."""
            ...

        @property
        def imports(self) -> tuple[str, ...]:
            """Ordered declaration imports."""
            ...

        @property
        def sibling_import_lines(self) -> tuple[str, ...]:
            """Canonical import lines for referenced protocol owners."""
            ...

        @property
        def owner(self) -> t.NonEmptyStr:
            """The declaring protocol namespace."""
            ...

        @property
        def bases(self) -> tuple[str, ...]:
            """Native source-derived facade composition bases."""
            ...

        @property
        def contracts(
            self,
        ) -> tuple[
            FlextInfraProtocolsCodegenRender.ModelProtocolRenderContextModelProtocolContract,
            ...,
        ]:
            """All data contracts declared by the corresponding model module."""
            ...

        @property
        def aliases(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Structural mirrors of the model namespace's type aliases whose value
            names projected models, as complete ``type`` statements.
            """
            ...

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """Project-local generated documentation language."""
            ...

        @property
        def module_description(self) -> str:
            """The projected module's structural responsibility."""
            ...

        @property
        def owner_description(self) -> str:
            """The declaring holder's structural responsibility."""
            ...

        @property
        def contract_description(self) -> str:
            """The generated value contract's responsibility."""
            ...

    @runtime_checkable
    class ModelProtocolRenderContextModelProtocolContract(
        FlextCliProtocols.BaseModel, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """The nested structural contract."""
            ...

        @property
        def depth(self) -> int:
            """The contract's nesting depth beneath its owner."""
            ...

        @property
        def type_parameters(self) -> tuple[str, ...]:
            """Complete parameter declarations with bounds and defaults."""
            ...

        @property
        def bases(self) -> tuple[str, ...]:
            """Authenticated structural capabilities of the contract."""
            ...

        @property
        def declarations(self) -> tuple[str, ...]:
            """Field declarations retaining their annotation metadata."""
            ...

    @runtime_checkable
    class GithubWorkflowProjectRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def publishes_release(self) -> bool:
            """Repository explicitly owns the release protocol."""
            ...

        @property
        def extra_verbs(self) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Elected repository-owned public commands."""
            ...

        @property
        def publish_index(self) -> bool:
            """Resolved release policy permits package index publication."""
            ...

        @property
        def dist(self) -> t.NonEmptyStr:
            """Distribution name."""
            ...

        @property
        def gate_original_receipt_filename(self) -> t.NonEmptyStr:
            """Public original native gate receipt filename."""
            ...

        @property
        def setup_operations_report_directory(self) -> Path:
            """Canonical setup operation report artifact directory."""
            ...

        @property
        def docs_report_filenames(self) -> tuple[t.NonEmptyStr, ...]:
            """Structured docs reports CI dumps and uploads."""
            ...

        @property
        def make_profile(self) -> c.Infra.MakeProfile:
            """Structural member projected from the owning model.

            Make/codegen profile; ci-matrix projected only for workspace/standalone;
            standalone excluded and orphan copies pruned.
            """
            ...

        @property
        def gascity_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Gas City runtime-contract participation; gates the Dolt server mode the
            generated Beads policy script asserts.
            """
            ...

        @property
        def repository_branch(self) -> t.NonEmptyStr:
            """Repository integration branch."""
            ...

        @property
        def python_version(self) -> t.NonEmptyStr:
            """Python major.minor line."""
            ...

        @property
        def toolchain(self) -> FlextInfraProtocolsMiseToolchain.ToolchainSpec:
            """Canonical toolchain consumed by CI bootstrap."""
            ...

        @property
        def github_actions(
            self,
        ) -> Mapping[str, FlextInfraProtocolsConfigProvider.GithubActionPinSpec]:
            """Immutable GitHub Action catalog."""
            ...

        @property
        def make(self) -> FlextInfraProtocolsConfigMake.MakeSpec:
            """Canonical workflow command contract."""
            ...

    @runtime_checkable
    class GithubWorkflowRenderSpec(GithubWorkflowProjectRenderSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_repositories(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.RepositoryRef, ...]:
            """Structural member projected from the owning model.

            Governed subproject repositories consumed by workspace-scoped workflow
            templates (docs paths, dependabot directories).
            """
            ...

        @property
        def ci_trigger_branches(self) -> tuple[t.NonEmptyStr, ...]:
            """Ordered, deduplicated blocking CI branches."""
            ...

        @property
        def has_devcontainer(self) -> bool:
            """Structural member projected from the owning model.

            Whether the rendered repository ships a .devcontainer directory.
            Dependabot only accepts a devcontainers ecosystem entry when one exists;
            declaring it for a repository without that directory makes GitHub reject
            the whole manifest, which silently disables EVERY ecosystem in it,
            security updates included. Derived from the repository on disk rather
            than declared, because the directory is the fact and a second
            declaration could disagree with it.
            """
            ...

        @property
        def dependency_cooldown_days(self) -> int:
            """Structural member projected from the owning model.

            Fleet supply-chain cooldown (codegen.toolchain SSOT) rendered as
            default-days into every dependabot ecosystem entry.
            """
            ...

        @property
        def cooldown_excluded_dependencies(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Requirement names the project takes by direct git reference (forks and
            local projects): derived from its pyproject, they never enter the
            cooldown.
            """
            ...

        @property
        def checkout_submodules(self) -> t.NonEmptyStr:
            """actions/checkout submodules mode resolved from config."""
            ...

        @property
        def custom_steps(self) -> str:
            """Structural member projected from the owning model.

            Verbatim project-owned workflow steps injected before the toolchain
            installer, read from the project's own custom-steps file; empty when the
            project declares none.
            """
            ...

        @property
        def custom_post_steps(self) -> str:
            """Structural member projected from the owning model.

            Verbatim project-owned workflow steps injected after the approval verbs
            (failure diagnostics), read from the project's own custom-post-steps
            file; empty when absent.
            """
            ...

        @property
        def private_submodules(
            self,
        ) -> FlextInfraProtocolsConfigProvider.CiPrivateSubmodulesSpec | None:
            """Structural member projected from the owning model.

            Optional private-subproject deploy-key init for this distribution; None
            means the workflow skips the step.
            """
            ...

        @property
        def private_dependency_auth(
            self,
        ) -> FlextInfraProtocolsConfigProvider.CiPrivateDependencyAuthSpec | None:
            """Structural member projected from the owning model.

            Optional GitHub App token minting for private git dependencies; None
            means the workflow skips the step.
            """
            ...

        @property
        def system_packages(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Runner packages this distribution's tests need; empty means the workflow
            renders no install step.
            """
            ...

        @property
        def packages_read(self) -> bool:
            """Structural member projected from the owning model.

            Grant the ci job packages: read because this distribution's gates
            resolve GitHub Packages; False keeps the job contents-only.
            """
            ...

        @property
        def superproject(
            self,
        ) -> FlextInfraProtocolsConfigProvider.CiSuperprojectCheckoutSpec | None:
            """Structural member projected from the owning model.

            Containing workspace an attached member's CI checks out to install the
            frozen root lock; None for a workspace root or a standalone repository,
            whose CI checks out itself.
            """
            ...

    @runtime_checkable
    class MakeWorkflowRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def dist(self) -> t.NonEmptyStr:
            """Distribution name."""
            ...

        @property
        def make(self) -> FlextInfraProtocolsConfigMake.MakeSpec:
            """Canonical workflow command contract."""
            ...

        @property
        def scenario_data_roots(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Scenario-data roots the staged-file hook never hands to a gate
            (codegen.exclusions.scenario_data_roots).
            """
            ...

    @runtime_checkable
    class GitHookRenderSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def preservation_ref_namespaces(self) -> tuple[t.NonEmptyStr, ...]:
            """Remote ref prefixes exempt from the pre-push matrix."""
            ...

    @runtime_checkable
    class DistroDockerRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def package_name(self) -> t.NonEmptyStr:
            """Python import package name."""
            ...

        @property
        def python_version(self) -> t.NonEmptyStr:
            """Python major.minor line."""
            ...

        @property
        def make(self) -> FlextInfraProtocolsConfigMake.MakeSpec:
            """Canonical Make CI token contract for ENV CI=Y."""
            ...

    @runtime_checkable
    class EnvrcRenderSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_environment_unset(self) -> tuple[t.NonEmptyStr, ...]:
            """Inherited selectors excluded by native activation."""
            ...

        @property
        def toolchain(self) -> FlextInfraProtocolsMiseToolchain.ToolchainSpec:
            """Governed native reader shared with Make."""
            ...

        @property
        def repository_root_rel(self) -> t.NonEmptyStr:
            """Project-relative owner of the runtime environment."""
            ...

        @property
        def mise_config_filename(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Only project Mise config the activation loads; a machine-local override
            never enters the governed shell.
            """
            ...

        @property
        def environment_path_prepends(self) -> tuple[t.NonEmptyStr, ...]:
            """Project-relative executable paths."""
            ...

        @property
        def environment_directory(self) -> t.NonEmptyStr:
            """Runtime-root-local development environment."""
            ...

        @property
        def environment_metadata(self) -> t.NonEmptyStr:
            """Native environment marker required before publication."""
            ...

    @runtime_checkable
    class SonarcloudRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def sonarcloud(self) -> FlextInfraProtocolsConfigRender.SonarcloudSpec:
            """Fleet SonarCloud scope policy."""
            ...

        @property
        def tests_dir(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Project-relative tests directory; conform always materializes it
            (managed tests/fixtures/ci/docker projections), so sonar.tests always
            names a real directory.
            """
            ...

        @property
        def workspace_subprojects(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Workspace-relative member checkout paths of a workspace root; each
            member is its own repository with its own SonarCloud project, so the
            root scope excludes them. Empty for a standalone repository.
            """
            ...

    @runtime_checkable
    class UvResolutionSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def link_mode(self) -> str:
            """Uv installation link mode."""
            ...

        @property
        def cooldown_days(self) -> int:
            """Structural member projected from the owning model.

            Fleet supply-chain cooldown rendered as the relative exclude-newer span
            every uv resolution honours.
            """
            ...

        @property
        def cooldown_exceptions(self) -> tuple[str, ...]:
            """Structural member projected from the owning model.

            Declared CVE or critical-fix packages exempt from the cooldown; empty
            removes exclude-newer-package.
            """
            ...

        @property
        def constraint_dependencies(self) -> tuple[str, ...]:
            """Declared constraints, projected as declared."""
            ...

        @property
        def override_dependencies(
            self,
        ) -> tuple[str | FlextInfraProtocolsMiseToolchain.UvScopedOverride, ...]:
            """Structural member projected from the owning model.

            SSOT-declared PEP 508 overrides resolving a transitive graph's family
            pins to the declared integration line; empty removes the key, so a
            standalone repository locks exactly like a fleet member (no member-
            computed fallback).
            """
            ...

        @property
        def environments(self) -> tuple[str, ...]:
            """Resolved environment markers uv resolves for."""
            ...

    @runtime_checkable
    class MarkdownRenderSpec(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_config(self) -> str:
            """Native Markdown TOML derived from the shared policy."""
            ...

    @runtime_checkable
    class QltyRenderSpec(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def facade_modules(self) -> tuple[str, ...]:
            """Facade module stems the generator projects (c, t, p, m, u)."""
            ...

    @runtime_checkable
    class ModuleSkeletonRenderContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        class_name: t.NonEmptyStr
        base_class: t.NonEmptyStr | None
        base_module: t.NonEmptyStr | None
        docstring: str | None
        module_prefix: str | None
        module_suffix: str
        class_bases: tuple[str, ...]
        class_keywords: tuple[str, ...]
        type_parameters_source: str
        header_source: str | None
        header_comments: tuple[str, ...]
        class_indent: str
        indentation: str
        body_source: str | None
        exports: tuple[str, ...] | None
        managed_header: str | None

    @runtime_checkable
    class TestModuleSkeletonRenderContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def class_name(self) -> t.NonEmptyStr:
            """Generated facade class name."""
            ...

        @property
        def base_class(self) -> t.NonEmptyStr:
            """Shared flext-tests base class."""
            ...

        @property
        def project_module(self) -> t.NonEmptyStr:
            """Public project package owning the lowercase facade alias."""
            ...

        @property
        def alias(self) -> t.NonEmptyStr:
            """Canonical c/t/p/m/u facade alias."""
            ...

        @property
        def namespace(self) -> t.NonEmptyStr:
            """Nested test namespace composed by the facade."""
            ...

        @property
        def project_namespace(self) -> t.NonEmptyStr:
            """Production namespace composed by the test namespace."""
            ...

        @property
        def docstring(self) -> t.NonEmptyStr:
            """Generated module docstring."""
            ...

    @runtime_checkable
    class MkdocsRenderContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def site_title(self) -> t.NonEmptyStr:
            """Rendered site title."""
            ...

        @property
        def site_url(self) -> t.NonEmptyStr:
            """Published site URL."""
            ...

        @property
        def repo_url(self) -> t.NonEmptyStr:
            """Source repository URL."""
            ...

        @property
        def repo_name(self) -> t.NonEmptyStr:
            """Source repository name."""
            ...

        @property
        def exclude_docs(self) -> Sequence[str]:
            """Gitignore-style docs exclusions."""
            ...

        @property
        def exclude_plugin_patterns(self) -> Sequence[str]:
            """Translated physical-copy exclusion regular expressions."""
            ...

        @property
        def mkdocstrings_paths(self) -> Sequence[str]:
            """Mkdocstrings source paths."""
            ...

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """Project-local generated documentation language."""
            ...

        @property
        def documentation_label(self) -> str:
            """The project documentation title label."""
            ...

        @property
        def site_description(self) -> str:
            """The root site presentation description."""
            ...

        @property
        def project_site_description(self) -> str:
            """The project site description prefix."""
            ...

        @property
        def dark_mode_label(self) -> str:
            """The Material palette action for dark mode."""
            ...

        @property
        def light_mode_label(self) -> str:
            """The Material palette action for light mode."""
            ...

    @runtime_checkable
    class MkdocsProjectRenderContext(MkdocsRenderContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scope_name(self) -> t.NonEmptyStr:
            """Workspace project scope."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenRender",
]
