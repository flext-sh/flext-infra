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

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsCodegenRender:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ModelProtocolConformanceRenderContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def header(self) -> str: ...
        @property
        def copyright_notice(self) -> str: ...
        @property
        def package_name(self) -> t.NonEmptyStr: ...
        @property
        def imports(self) -> tuple[str, ...]: ...
        @property
        def checks(
            self,
        ) -> tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...]: ...

    @runtime_checkable
    class ModelProtocolRenderContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def header(self) -> str: ...
        @property
        def copyright_notice(self) -> str: ...
        @property
        def imports(self) -> tuple[str, ...]: ...
        @property
        def sibling_import_lines(self) -> tuple[str, ...]: ...
        @property
        def owner(self) -> t.NonEmptyStr: ...
        @property
        def bases(self) -> tuple[str, ...]: ...
        @property
        def contracts(
            self,
        ) -> tuple[p.Infra.ModelProtocolRenderContext.ModelProtocolContract, ...]: ...

        @runtime_checkable
        class ModelProtocolContract(Protocol):
            """Structural data contract projected from the owning model."""

            @property
            def name(self) -> t.NonEmptyStr: ...
            @property
            def depth(self) -> int: ...
            @property
            def type_parameters(self) -> tuple[str, ...]: ...
            @property
            def declarations(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class GithubWorkflowRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def publishes_release(self) -> bool: ...
        @property
        def extra_verbs(self) -> tuple[p.Infra.MakeVerbSpec, ...]: ...
        @property
        def publish_index(self) -> bool: ...
        @property
        def dist(self) -> t.NonEmptyStr: ...
        @property
        def gate_original_receipt_filename(self) -> t.NonEmptyStr: ...
        @property
        def setup_operations_report_directory(self) -> Path: ...
        @property
        def docs_report_filenames(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def make_profile(self) -> c.Infra.MakeProfile: ...
        @property
        def gascity_enabled(self) -> bool: ...
        @property
        def repository_branch(self) -> t.NonEmptyStr: ...
        @property
        def python_version(self) -> t.NonEmptyStr: ...
        @property
        def toolchain(self) -> p.Infra.ToolchainSpec: ...
        @property
        def github_actions(self) -> Mapping[str, p.Infra.GithubActionPinSpec]: ...
        @property
        def make(self) -> p.Infra.MakeSpec: ...
        @property
        def workspace_repositories(self) -> tuple[p.Infra.RepositoryRef, ...]: ...
        @property
        def ci_trigger_branches(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def has_devcontainer(self) -> bool: ...
        @property
        def dependency_cooldown_days(self) -> int: ...
        @property
        def cooldown_excluded_dependencies(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def checkout_submodules(self) -> t.NonEmptyStr: ...
        @property
        def custom_steps(self) -> str: ...
        @property
        def custom_post_steps(self) -> str: ...
        @property
        def private_submodules(self) -> p.Infra.CiPrivateSubmodulesSpec | None: ...
        @property
        def private_dependency_auth(
            self,
        ) -> p.Infra.CiPrivateDependencyAuthSpec | None: ...
        @property
        def system_packages(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def packages_read(self) -> bool: ...
        @property
        def superproject(self) -> p.Infra.CiSuperprojectCheckoutSpec | None: ...

    @runtime_checkable
    class MakeWorkflowRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dist(self) -> t.NonEmptyStr: ...
        @property
        def make(self) -> p.Infra.MakeSpec: ...

    @runtime_checkable
    class GitHookRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def preservation_ref_namespaces(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class DistroDockerRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package_name(self) -> t.NonEmptyStr: ...
        @property
        def python_version(self) -> t.NonEmptyStr: ...
        @property
        def make(self) -> p.Infra.MakeSpec: ...

    @runtime_checkable
    class EnvrcRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_environment_unset(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def toolchain(self) -> p.Infra.ToolchainSpec: ...
        @property
        def repository_root_rel(self) -> t.NonEmptyStr: ...
        @property
        def environment_path_prepends(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def environment_directory(self) -> t.NonEmptyStr: ...
        @property
        def environment_metadata(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class SonarcloudRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def sonarcloud(self) -> p.Infra.SonarcloudSpec: ...
        @property
        def tests_dir(self) -> t.NonEmptyStr: ...
        @property
        def workspace_subprojects(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class UvResolutionSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def link_mode(self) -> str: ...
        @property
        def constraint_dependencies(self) -> tuple[str, ...]: ...
        @property
        def override_dependencies(
            self,
        ) -> tuple[str | p.Infra.UvScopedOverride, ...]: ...
        @property
        def environments(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class MarkdownLintRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_config(self) -> str: ...
        @property
        def exclude(self) -> t.StrTuple: ...

    @runtime_checkable
    class QltyRenderSpec(Protocol):
        """Structural data contract projected from the owning model."""

    @runtime_checkable
    class ModuleSkeletonRenderContext(Protocol):
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
        body_source: tuple[str | tuple[str, str], ...] | None
        publications: Mapping[str, str]
        exports: tuple[str, ...] | None
        managed_header: str | None

    @runtime_checkable
    class TestModuleSkeletonRenderContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def class_name(self) -> t.NonEmptyStr: ...
        @property
        def base_class(self) -> t.NonEmptyStr: ...
        @property
        def project_module(self) -> t.NonEmptyStr: ...
        @property
        def alias(self) -> t.NonEmptyStr: ...
        @property
        def namespace(self) -> t.NonEmptyStr: ...
        @property
        def project_namespace(self) -> t.NonEmptyStr: ...
        @property
        def docstring(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class MkdocsRenderContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def site_title(self) -> t.NonEmptyStr: ...
        @property
        def site_url(self) -> t.NonEmptyStr: ...
        @property
        def repo_url(self) -> t.NonEmptyStr: ...
        @property
        def repo_name(self) -> t.NonEmptyStr: ...
        @property
        def exclude_docs(self) -> Sequence[str]: ...
        @property
        def exclude_plugin_patterns(self) -> Sequence[str]: ...
        @property
        def mkdocstrings_paths(self) -> Sequence[str]: ...
        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage: ...
        @property
        def documentation_label(self) -> str: ...
        @property
        def site_description(self) -> str: ...
        @property
        def project_site_description(self) -> str: ...
        @property
        def dark_mode_label(self) -> str: ...
        @property
        def light_mode_label(self) -> str: ...

    @runtime_checkable
    class MkdocsProjectRenderContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def site_title(self) -> t.NonEmptyStr: ...
        @property
        def site_url(self) -> t.NonEmptyStr: ...
        @property
        def repo_url(self) -> t.NonEmptyStr: ...
        @property
        def repo_name(self) -> t.NonEmptyStr: ...
        @property
        def exclude_docs(self) -> Sequence[str]: ...
        @property
        def exclude_plugin_patterns(self) -> Sequence[str]: ...
        @property
        def mkdocstrings_paths(self) -> Sequence[str]: ...
        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage: ...
        @property
        def documentation_label(self) -> str: ...
        @property
        def site_description(self) -> str: ...
        @property
        def project_site_description(self) -> str: ...
        @property
        def dark_mode_label(self) -> str: ...
        @property
        def light_mode_label(self) -> str: ...
        @property
        def scope_name(self) -> t.NonEmptyStr: ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenRender",
]
