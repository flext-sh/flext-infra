"""Provider, repository source, and CI private-submodule models."""

from __future__ import annotations

from typing import Annotated, ClassVar, Self

from flext_cli import m, u

from ... import t
from ..._constants import FlextInfraConstantsSharedInfra
from .contract import FlextInfraConfigModelsContract


class FlextInfraConfigModelsProvider:
    """Provider, repository source, and CI private-submodule models."""

    class ProviderSpec(FlextInfraConfigModelsContract._ConfigContract):
        """One GitHub organization and its mandatory branch policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Provider key")]
        organization: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub organization")
        ]
        base_url: Annotated[t.NonEmptyStr, m.Field(description="GitHub HTTPS base URL")]
        branch: Annotated[t.NonEmptyStr, m.Field(description="Provider branch")]

    class RepositorySourceSpec(FlextInfraConfigModelsContract._ConfigContract):
        """Portable repository identity derived through one declared provider."""

        distribution: Annotated[
            t.NonEmptyStr, m.Field(description="Repository distribution name")
        ]
        provider: Annotated[
            t.NonEmptyStr, m.Field(description="Provider key owning URL and branch")
        ]

        @m.computed_field
        @property
        def internal_distribution_prefix(self) -> str:
            """Derive the internal distribution namespace from the owner name."""
            namespace, _, _ = self.distribution.partition("-")
            return f"{namespace}-"

    class BranchPolicySpec(FlextInfraConfigModelsContract._ConfigContract):
        """Global branch policy shared by every provider."""

        ci_trigger_branches: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description=(
                    "Branches whose pushes trigger the generated CI workflow. "
                    "Config owns this list: the renderer adds only the repository's "
                    "own integration branch, so no fleet name is hardcoded in code."
                ),
            ),
        ]
        integration_branch_preference: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                default=FlextInfraConstantsSharedInfra.INTEGRATION_BRANCH_PREFERENCE,
                min_length=1,
                description=(
                    "Ordered names tried against live Git to derive one "
                    "repository's integration baseline. A workspace that "
                    "integrates on a versioned line declares it here, so a "
                    "release name never has to be hardcoded in the package. "
                    "The provider default stays the last-resort fallback, "
                    "never the answer."
                ),
            ),
        ] = FlextInfraConstantsSharedInfra.INTEGRATION_BRANCH_PREFERENCE

    class GithubActionPinSpec(FlextInfraConfigModelsContract._ConfigContract):
        """One GitHub Action reference from the codegen catalog."""

        repository: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub owner/repository action name")
        ]
        version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Upstream floating release tag the action rides"),
        ]

    class CiPrivateSubmoduleDeployKeySpec(
        FlextInfraConfigModelsContract._ConfigContract
    ):
        """One read-only deploy key that unlocks a private workspace subproject in CI."""

        secret: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="GitHub Actions secret name holding the deploy key PEM"
            ),
        ]
        submodule: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="gitmodules submodule name (git config submodule.<name>.url)"
            ),
        ]
        path: Annotated[
            t.NonEmptyStr, m.Field(description="Checkout-relative submodule path")
        ]
        remote: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$",
                description="Canonical GitHub SSH clone URL without a Host alias",
            ),
        ]

    class CiPrivateDependencyAuthSpec(FlextInfraConfigModelsContract._ConfigContract):
        """GitHub App identity minting installation tokens for private deps."""

        app_id_secret: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[A-Z][A-Z0-9_]*$",
                description="CI secret holding the private-dependency App id",
            ),
        ]
        private_key_secret: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[A-Z][A-Z0-9_]*$",
                description="CI secret holding the private-dependency App key",
            ),
        ]

    class CiPrivateSubmodulesSpec(FlextInfraConfigModelsContract._ConfigContract):
        """Per-distribution private submodule init contract for generated CI."""

        _KNOWN_HOSTS_FIELD_COUNT: ClassVar[int] = 3

        known_hosts: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1,
                description="Pinned official SSH host-key lines used only in runner temp",
            ),
        ]

        paths: Annotated[
            t.VariadicTuple[t.NonEmptyStr],
            m.Field(
                min_length=1, description="Submodule paths to init before make setup"
            ),
        ]
        deploy_keys: Annotated[
            t.VariadicTuple[
                FlextInfraConfigModelsProvider.CiPrivateSubmoduleDeployKeySpec
            ],
            m.Field(min_length=1, description="Ordered deploy-key materializations"),
        ]

        @u.model_validator(mode="after")
        def _validate_private_submodule_identity(self) -> Self:
            """Keep path, key, and host identities complete and unambiguous."""
            key_paths = tuple(key.path for key in self.deploy_keys)
            if key_paths != self.paths:
                msg = "private submodule deploy-key paths must exactly match paths"
                raise ValueError(msg)
            for field, values in (
                ("secret", tuple(key.secret for key in self.deploy_keys)),
                ("submodule", tuple(key.submodule for key in self.deploy_keys)),
                ("remote", tuple(key.remote for key in self.deploy_keys)),
                ("known_hosts", self.known_hosts),
            ):
                if len(set(values)) != len(values):
                    msg = f"private submodule {field} values must be unique"
                    raise ValueError(msg)
            for line in self.known_hosts:
                fields = line.split()
                if (
                    len(fields) != self._KNOWN_HOSTS_FIELD_COUNT
                    or fields[0] != "github.com"
                    or fields[1] != "ssh-ed25519"
                ):
                    msg = (
                        "private submodule known_hosts must pin github.com ssh-ed25519"
                    )
                    raise ValueError(msg)
            return self
