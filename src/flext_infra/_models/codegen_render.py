"""Render context models for codegen templates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsMiseToolchain
from flext_infra._models._config import (
    FlextInfraConfigModelsContexts,
    FlextInfraConfigModelsContract,
    FlextInfraConfigModelsMake,
    FlextInfraConfigModelsProvider,
    FlextInfraConfigModelsRender,
)


class FlextInfraModelsCodegenRender:
    """Typed render contexts for generated codegen artifacts."""

    class GithubWorkflowRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed by generated GitHub workflow templates."""

        publishes_release: Annotated[
            bool,
            m.Field(description="Repository explicitly owns the release protocol"),
        ] = False
        extra_verbs: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsMake.MakeVerbSpec],
            m.Field(description="Elected repository-owned public commands"),
        ] = ()
        publish_index: Annotated[
            bool,
            m.Field(
                description="Resolved release policy permits package index publication"
            ),
        ] = False
        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        gate_original_receipt_filename: Annotated[
            t.NonEmptyStr,
            m.Field(description="Public original native gate receipt filename"),
        ]
        setup_operations_report_directory: Annotated[
            Path,
            m.Field(description="Canonical setup operation report artifact directory"),
        ]
        docs_report_filenames: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Structured docs reports CI dumps and uploads"),
        ] = c.Infra.DOCS_STRUCTURED_REPORT_FILENAMES
        make_profile: Annotated[
            c.Infra.MakeProfile,
            m.Field(
                description=(
                    "Make/codegen profile; ci-matrix projected only for "
                    "workspace/standalone; standalone excluded "
                    "and orphan copies pruned"
                ),
            ),
        ]
        gascity_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Gas City runtime-contract participation; gates the Dolt "
                    "server mode the generated Beads policy script asserts."
                ),
            ),
        ] = True
        repository_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository integration branch"),
        ]
        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python major.minor line"),
        ]
        toolchain: Annotated[
            FlextInfraConfigModelsContract.ToolchainSpec,
            m.Field(description="Canonical toolchain consumed by CI bootstrap"),
        ]
        github_actions: Annotated[
            Mapping[str, FlextInfraConfigModelsProvider.GithubActionPinSpec],
            m.Field(description="Immutable GitHub Action catalog"),
        ]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
        ]
        workspace_repositories: Annotated[
            t.VariadicTuple[FlextInfraConfigModelsContexts.RepositoryRef],
            m.Field(
                description=(
                    "Governed subproject repositories consumed by workspace-scoped "
                    "workflow templates (docs paths, dependabot directories)"
                ),
            ),
        ] = ()
        ci_trigger_branches: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description="Ordered, deduplicated blocking CI branches",
            ),
        ] = ()
        has_devcontainer: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the rendered repository ships a .devcontainer "
                    "directory. Dependabot only accepts a devcontainers "
                    "ecosystem entry when one exists; declaring it for a "
                    "repository without that directory makes GitHub reject the "
                    "whole manifest, which silently disables EVERY ecosystem in "
                    "it, security updates included. Derived from the repository "
                    "on disk rather than declared, because the directory is the "
                    "fact and a second declaration could disagree with it"
                ),
            ),
        ] = False
        dependency_cooldown_days: Annotated[
            int,
            m.Field(
                ge=1,
                description=(
                    "Fleet supply-chain cooldown (codegen.toolchain SSOT) "
                    "rendered as default-days into every dependabot ecosystem "
                    "entry."
                ),
            ),
        ]
        cooldown_excluded_dependencies: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Requirement names the project takes by direct git "
                    "reference (forks and local projects): derived from its "
                    "pyproject, they never enter the cooldown."
                ),
            ),
        ] = ()
        checkout_submodules: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^(true|false|recursive)$",
                description="actions/checkout submodules mode resolved from config",
            ),
        ]
        custom_steps: Annotated[
            str,
            m.Field(
                default="",
                description=(
                    "Verbatim project-owned workflow steps injected before the "
                    "toolchain installer, read from the project's own "
                    "custom-steps file; empty when the project declares none"
                ),
            ),
        ] = ""
        custom_post_steps: Annotated[
            str,
            m.Field(
                default="",
                description=(
                    "Verbatim project-owned workflow steps injected after the "
                    "approval verbs (failure diagnostics), read from the "
                    "project's own custom-post-steps file; empty when absent"
                ),
            ),
        ] = ""
        private_submodules: Annotated[
            FlextInfraConfigModelsProvider.CiPrivateSubmodulesSpec | None,
            m.Field(
                default=None,
                description=(
                    "Optional private-subproject deploy-key init for this "
                    "distribution; None means the workflow skips the step"
                ),
            ),
        ] = None
        private_dependency_auth: Annotated[
            FlextInfraConfigModelsProvider.CiPrivateDependencyAuthSpec | None,
            m.Field(
                default=None,
                description=(
                    "Optional GitHub App token minting for private git "
                    "dependencies; None means the workflow skips the step"
                ),
            ),
        ] = None
        system_packages: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(),
                description=(
                    "Runner packages this distribution's tests need; empty "
                    "means the workflow renders no install step"
                ),
            ),
        ] = ()
        packages_read: Annotated[
            bool,
            m.Field(
                default=False,
                description=(
                    "Grant the ci job packages: read because this "
                    "distribution's gates resolve GitHub Packages; False keeps "
                    "the job contents-only"
                ),
            ),
        ] = False
        superproject: Annotated[
            FlextInfraConfigModelsProvider.CiSuperprojectCheckoutSpec | None,
            m.Field(
                default=None,
                description=(
                    "Containing workspace an attached member's CI checks out to "
                    "install the frozen root lock; None for a workspace root or "
                    "a standalone repository, whose CI checks out itself"
                ),
            ),
        ] = None

        @m.model_validator(mode="after")
        def require_elected_release_commands(self) -> Self:
            """Require the complete elected product protocol before rendering.

            Returns:
                Self: the validated render specification.

            Raises:
                ValueError: when an elected release phase command is missing.

            """
            if self.publishes_release:
                required = {f"release-{phase.value}" for phase in c.Infra.ReleasePhase}
                missing = required - {verb.name for verb in self.extra_verbs}
                if missing:
                    msg = "elected release protocol lacks phase commands: " + ", ".join(
                        sorted(missing)
                    )
                    raise ValueError(msg)
            return self

    class MakeWorkflowRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input shared by generated local workflow surfaces."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
        ]

    class GitHookRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed by the generated Git hook validator."""

        preservation_ref_namespaces: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Remote ref prefixes exempt from the pre-push matrix"),
        ]

    class DistroDockerRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed by generated distro Dockerfiles."""

        package_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python import package name"),
        ]
        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python major.minor line"),
        ]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical Make CI token contract for ENV CI=Y"),
        ]

    class EnvrcRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed only by the generated project ``.envrc``."""

        native_environment_unset: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Inherited selectors excluded by native activation"),
        ]
        toolchain: Annotated[
            FlextInfraConfigModelsContract.ToolchainSpec,
            m.Field(description="Governed native reader shared with Make"),
        ]
        repository_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project-relative owner of the runtime environment"),
        ] = "."
        environment_path_prepends: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Project-relative executable paths"),
        ]
        environment_directory: Annotated[
            t.NonEmptyStr,
            m.Field(description="Runtime-root-local development environment"),
        ] = c.Infra.ENVIRONMENT_DIRECTORY

    class SonarcloudRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed only by the generated ``.sonarcloud.properties``."""

        sonarcloud: Annotated[
            FlextInfraConfigModelsRender.SonarcloudSpec,
            m.Field(description="Fleet SonarCloud scope policy"),
        ]
        tests_dir: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Project-relative tests directory; conform always "
                    "materializes it (managed tests/fixtures/ci/docker "
                    "projections), so sonar.tests always names a real directory"
                ),
            ),
        ]
        workspace_subprojects: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Workspace-relative member checkout paths of a workspace "
                    "root; each member is its own repository with its own "
                    "SonarCloud project, so the root scope excludes them. "
                    "Empty for a standalone repository"
                ),
            ),
        ] = ()
        generated_source_globs: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Tracked generated-source trees derived from the codegen "
                    "artifact key; never governed source"
                ),
            ),
        ] = ()

    class UvResolutionSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Resolver keys conform owns in one project's ``[tool.uv]`` table.

        Every key is declared: an empty sequence removes it from the table.
        """

        link_mode: Annotated[str, m.Field(description="uv installation link mode")]
        constraint_dependencies: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Declared constraints, projected as declared"),
        ]
        override_dependencies: Annotated[
            t.VariadicTuple[str | FlextInfraModelsMiseToolchain.UvScopedOverride],
            m.Field(
                description=(
                    "SSOT-declared PEP 508 overrides resolving a transitive "
                    "graph's family pins to the declared integration line; "
                    "empty removes the key, so a standalone repository locks "
                    "exactly like a fleet member (no member-computed fallback)."
                ),
            ),
        ] = ()
        environments: Annotated[
            t.VariadicTuple[str],
            m.Field(description="Resolved environment markers uv resolves for"),
        ]

    class MarkdownLintRenderSpec(m.ContractModel):
        """Validated tooling-only context for Markdown lint projections."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            strict=True,
        )

        native_config: Annotated[
            str,
            m.Field(description="Native Markdown TOML derived from the shared policy."),
        ]
        exclude: Annotated[
            t.StrTuple,
            m.Field(description="Declared non-documentation path patterns."),
        ]

    class QltyRenderSpec(m.ContractModel):
        """Validated context for the generated qlty repository configuration."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            strict=True,
        )

        generated_projection_patterns: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Generated projection surface excluded from the smells "
                    "scan, from the one generated-projection owner."
                ),
            ),
        ] = ()

    # Keep the module-skeleton template boundary model-backed and immutable.
    class ModuleSkeletonRenderContext(m.ContractModel):
        """Validated context for one generated module skeleton."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            str_strip_whitespace=False,
        )

        class_name: t.NonEmptyStr = m.Field(description="Generated class name.")
        base_class: t.NonEmptyStr = m.Field(description="Generated base class name.")
        base_module: t.NonEmptyStr = m.Field(description="Module owning base_class.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")

    class TestModuleSkeletonRenderContext(m.ContractModel):
        """Validated context for one generated test facade skeleton."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            str_strip_whitespace=False,
        )

        class_name: t.NonEmptyStr = m.Field(description="Generated facade class name.")
        base_class: t.NonEmptyStr = m.Field(
            description="Shared flext-tests base class.",
        )
        project_module: t.NonEmptyStr = m.Field(
            description="Public project package owning the lowercase facade alias.",
        )
        alias: t.NonEmptyStr = m.Field(description="Canonical c/t/p/m/u facade alias.")
        namespace: t.NonEmptyStr = m.Field(
            description="Nested test namespace composed by the facade.",
        )
        project_namespace: t.NonEmptyStr = m.Field(
            description="Production namespace composed by the test namespace.",
        )
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")

    # The docs renderer sends one immutable model directly to the flext-cli boundary.
    class MkdocsRenderContext(m.ContractModel):
        """Validated common context for a generated MkDocs configuration."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            strict=True,
            str_strip_whitespace=False,
        )

        site_title: t.NonEmptyStr = m.Field(description="Rendered site title.")
        site_url: t.NonEmptyStr = m.Field(description="Published site URL.")
        repo_url: t.NonEmptyStr = m.Field(description="Source repository URL.")
        repo_name: t.NonEmptyStr = m.Field(description="Source repository name.")
        exclude_docs: t.StrSequence = m.Field(
            description="Gitignore-style docs exclusions."
        )
        exclude_plugin_patterns: t.StrSequence = m.Field(
            description="Translated physical-copy exclusion regular expressions.",
        )
        mkdocstrings_paths: t.StrSequence = m.Field(
            description="mkdocstrings source paths.",
        )
        documentation_language: t.Infra.DocumentationLanguage = m.Field(
            default="en", description="Project-local generated documentation language"
        )

        @m.computed_field
        @property
        def documentation_label(self) -> str:
            """The project documentation title label."""
            return c.Infra.DocumentationText.DOCUMENTATION.localized(
                self.documentation_language
            )

        @m.computed_field
        @property
        def site_description(self) -> str:
            """The root site presentation description."""
            return c.Infra.DocumentationText.ROOT_SITE_DESCRIPTION.localized(
                self.documentation_language
            )

        @m.computed_field
        @property
        def project_site_description(self) -> str:
            """The project site description prefix."""
            return c.Infra.DocumentationText.PROJECT_SITE_DESCRIPTION.localized(
                self.documentation_language
            )

        @m.computed_field
        @property
        def dark_mode_label(self) -> str:
            """The Material palette action for dark mode."""
            return c.Infra.DocumentationText.DARK_MODE.localized(
                self.documentation_language
            )

        @m.computed_field
        @property
        def light_mode_label(self) -> str:
            """The Material palette action for light mode."""
            return c.Infra.DocumentationText.LIGHT_MODE.localized(
                self.documentation_language
            )

    class MkdocsProjectRenderContext(MkdocsRenderContext):
        """Validated MkDocs context with a project edit scope."""

        scope_name: t.NonEmptyStr = m.Field(description="Workspace project scope.")

    class LazyInitRootRender(m.ArbitraryTypesModel):
        """Template context for one lazy public root ``__init__.py``."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        runtime_import_lines: t.NonEmptyStr = m.Field(
            description="Isort-ordered runtime imports of the lazy helpers.",
        )
        eager_binding_lines: str = m.Field(
            default_factory=str,
            description=(
                "Runtime-only eager dunder bindings emitted after the lazy "
                "installer, so the bound submodule may consume the package's "
                "own facades while its static contract stays in TYPE_CHECKING."
            ),
        )
        type_checking_lines: str = m.Field(
            default_factory=str,
            description="Static declarations for public lazy exports.",
        )
        exports_tuple: t.NonEmptyStr = m.Field(
            description="Canonical rendered root ``__all__`` tuple.",
        )
        lazy_export_mapping: t.NonEmptyStr = m.Field(
            description="Immutable elected export-to-target installer argument.",
        )


__all__: list[str] = ["FlextInfraModelsCodegenRender"]
