"""Render specification models for generated workflow and env surfaces."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from flext_cli import m

from ... import t
from ..._constants import FlextInfraConstantsCodegenProject
from ..deps_tool_config import FlextInfraModelsDepsToolConfig
from .beads import FlextInfraConfigModelsBeads
from .contexts import FlextInfraConfigModelsContexts
from .contract import FlextInfraConfigModelsContract
from .make import FlextInfraConfigModelsMake
from .provider import FlextInfraConfigModelsProvider


class FlextInfraConfigModelsRender:
    """Render specification models for generated workflow and env surfaces."""

    class GithubWorkflowRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed by generated GitHub workflow templates."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        make_profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(
                description=(
                    "Make/codegen profile; ci-matrix projected only for "
                    "workspace/standalone; standalone excluded "
                    "and orphan copies pruned"
                )
            ),
        ]
        gascity_enabled: Annotated[
            bool,
            m.Field(
                description=(
                    "Gas City runtime-contract participation; gates the Dolt "
                    "server mode the generated Beads policy script asserts."
                )
            ),
        ] = True
        repository_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Repository integration branch")
        ]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor line")
        ]
        state_directory_name: Annotated[
            t.NonEmptyStr, m.Field(description="External runtime state directory name")
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
                default=(),
                description=(
                    "Governed subproject repositories consumed by workspace-scoped "
                    "workflow templates (docs paths, dependabot directories)"
                ),
            ),
        ]
        ci_trigger_branches: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=(), description="Ordered, deduplicated blocking CI branches"
            ),
        ] = ()
        has_devcontainer: Annotated[
            bool,
            m.Field(
                default=False,
                description=(
                    "Whether the rendered repository ships a .devcontainer "
                    "directory. Dependabot only accepts a devcontainers "
                    "ecosystem entry when one exists; declaring it for a "
                    "repository without that directory makes GitHub reject the "
                    "whole manifest, which silently disables EVERY ecosystem in "
                    "it, security updates included. Derived from the repository "
                    "on disk rather than declared, because the directory is the "
                    "fact and a second declaration could disagree with it "
                    "(hq-36xk)"
                ),
            ),
        ] = False
        checkout_submodules: Annotated[
            t.NonEmptyStr,
            m.Field(
                default="false",
                pattern=r"^(true|false|recursive)$",
                description=(
                    "actions/checkout submodules mode. Defaults to 'false' "
                    "because the default GITHUB_TOKEN cannot clone sibling "
                    "private repositories: 'recursive' aborts the job at "
                    "checkout with 'Repository not found'. Projects whose "
                    "submodules are public, or that provide a PAT, override "
                    "it per project in codegen.yaml"
                ),
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

    class MakeWorkflowRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input shared by generated local workflow surfaces."""

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical workflow command contract"),
        ]

    class ToolingRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input for project-independent generated tooling surfaces."""

        tooling: Annotated[
            FlextInfraModelsDepsToolConfig.ToolConfigDocument,
            m.Field(description="Canonical validated tooling policy"),
        ]

    class DistroDockerRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed by generated distro Dockerfiles."""

        package_name: Annotated[
            t.NonEmptyStr, m.Field(description="Python import package name")
        ]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor line")
        ]
        make: Annotated[
            FlextInfraConfigModelsMake.MakeSpec,
            m.Field(description="Canonical Make CI token contract for ENV CI=Y"),
        ]
        mise_bootstrap: Annotated[
            FlextInfraConfigModelsContract.MiseBootstrapEnvironmentSpec,
            m.Field(description="Strict Mise environment projected into containers"),
        ]

    class EnvrcRenderSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Typed input consumed only by the generated project ``.envrc``."""

        state_directory_name: Annotated[
            t.NonEmptyStr, m.Field(description="External runtime state directory")
        ]
        scratch_namespace: Annotated[
            t.NonEmptyStr, m.Field(description="External scratch namespace")
        ]
        scratch_home_relative: Annotated[
            t.NonEmptyStr, m.Field(description="Home-relative scratch root")
        ]
        pycache_namespace: Annotated[
            t.NonEmptyStr, m.Field(description="External bytecode cache namespace")
        ]

        environment_path_prepends: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(description="Project-relative executable paths"),
        ]
        mise_bootstrap: Annotated[
            FlextInfraConfigModelsContract.MiseBootstrapEnvironmentSpec,
            m.Field(description="Strict persistent Mise storage contract"),
        ]
        gascity: Annotated[
            FlextInfraConfigModelsBeads.BeadsWorkspaceEnvironmentSpec | None,
            m.Field(
                description=(
                    "Gas City Beads projection present only when the repository "
                    "declares gascity_enabled"
                )
            ),
        ] = None

    class UvPackageSelectorSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Package selector for one official uv scoped dependency exclusion."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Selected package name")]
        version: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional selected package version expression"),
        ] = None

    class UvScopedDependencyExclusionSpec(
        FlextInfraConfigModelsContract.ConfigContract
    ):
        """Project-routed official uv scoped dependency exclusion."""

        project: Annotated[
            t.NonEmptyStr,
            m.Field(exclude=True, description="Owning project distribution route"),
        ]
        package: Annotated[
            FlextInfraConfigModelsRender.UvPackageSelectorSpec,
            m.Field(description="Package whose transitive edge is scoped"),
        ]
        dependencies: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(min_length=1, description="Excluded transitive dependency names"),
        ]
