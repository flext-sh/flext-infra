"""Render context models for codegen templates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, ClassVar

from flext_cli import m

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsDepsToolConfig
from flext_infra._models._config.contexts import FlextInfraConfigModelsContexts
from flext_infra._models._config.contract import FlextInfraConfigModelsContract
from flext_infra._models._config.make import FlextInfraConfigModelsMake
from flext_infra._models._config.provider import FlextInfraConfigModelsProvider
from flext_infra._models._config.render import FlextInfraConfigModelsRender


class FlextInfraModelsCodegenRender:
    """Typed render contexts for generated codegen artifacts."""

    class GithubWorkflowRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed by generated GitHub workflow templates."""

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

    class MakeWorkflowRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input shared by generated local workflow surfaces."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
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
            m.Field(description="Declared constraints; the uv pin is never kept"),
        ]
<<<<<<< HEAD
        override_dependencies: Annotated[
            t.VariadicTuple[str],
            m.Field(
                description=(
                    "SSOT-declared PEP 508 overrides resolving a transitive "
                    "graph's family pins to the declared integration line; "
                    "empty leaves the member-computed staging behavior."
                ),
            ),
        ] = ()
        exclude_dependencies: Annotated[
            t.VariadicTuple[
                FlextInfraConfigModelsRender.UvScopedDependencyExclusionSpec
            ],
            m.Field(description="Scoped dependency exclusions routed to the project"),
        ]
=======
>>>>>>> 734b15fc8230b9b36ab8e161e9a40ed2957ae92d
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

        tooling: Annotated[
            FlextInfraModelsDepsToolConfig.ToolConfigDocument,
            m.Field(description="Canonical validated tooling policy."),
        ]

    class QltyRenderSpec(m.ContractModel):
        """Validated context for the generated qlty repository configuration."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            strict=True,
        )

        generated_source_globs: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                description=(
                    "Tracked generated-source trees excluded from the smells "
                    "scan, derived from the codegen artifact key."
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
        exclude_docs_block: str = m.Field(description="Rendered docs exclusions.")
        exclude_plugin_block: str = m.Field(description="Rendered plugin exclusions.")
        mkdocstrings_paths_block: str = m.Field(
            description="Rendered mkdocstrings source paths.",
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
            description=(
                "Isort-ordered runtime imports: the lazy helpers plus any "
                "eager or wildcard reexports."
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
