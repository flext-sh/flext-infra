"""Provider, repository source, and CI private-submodule models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, ClassVar, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models._config.contract import FlextInfraModelsConfigContract


class FlextInfraModelsConfigProvider:
    """Provider, repository source, and CI private-submodule models."""

    class ProviderIdentitySpec(FlextInfraModelsConfigContract.ConfigContract):
        """Git provider identity detected from one repository's own declarations.

        flext-infra ships no provider registry: the name is the key the
        repository's own ``config/workspace.yaml`` declares, and the
        organization and base URL are read from that same declaration's
        canonical URL. No branch lives here — a branch is detected from live
        Git or declared by an explicit caller, never invented from policy.
        """

        name: Annotated[t.NonEmptyStr, m.Field(description="Declared provider key")]
        organization: Annotated[
            t.NonEmptyStr,
            m.Field(description="Git organization detected from the declared URL"),
        ]
        base_url: Annotated[
            t.NonEmptyStr,
            m.Field(description="HTTPS base URL detected from the declared URL"),
        ]

    class RepositorySourceSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Portable repository identity derived through one declared provider."""

        distribution: Annotated[
            t.NonEmptyStr,
            m.Field(description="Repository distribution name"),
        ]
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key owning URL and branch"),
        ]

        @m.computed_field
        @property
        def internal_distribution_prefix(self) -> str:
            """Derive the internal distribution namespace from the owner name.

            Returns:
                The resulting ``str``.

            """
            namespace, _, _ = self.distribution.partition("-")
            return f"{namespace}-"

    class BranchPolicySpec(FlextInfraModelsConfigContract.ConfigContract):
        """Global branch policy shared by every provider."""

        lane_remote: Annotated[
            t.NonEmptyStr,
            m.Field(description="Remote whose live integration tip governs lanes"),
        ]
        lane_temporary_roots: Annotated[
            tuple[Path, ...],
            m.Field(description="Temporary roots requiring registered ownership"),
        ]
        lane_pr_limit: Annotated[
            int,
            m.Field(gt=0, description="PR page bound; saturation fails the inventory"),
        ]
        lane_governance_file: Annotated[
            Path | None,
            m.Field(
                description="Explicit host coordination SSOT, unavailable when "
                "undeclared",
            ),
        ] = None
        ci_trigger_branches: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Branches whose pushes trigger the generated CI workflow. "
                    "Config owns this list: the renderer adds only the repository's "
                    "own integration branch, so no fleet name is hardcoded in code."
                ),
            ),
        ]
        preservation_ref_namespaces: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Full-ref prefixes (ending in a slash) that hold WIP "
                    "preservation pushes. The generated pre-push hook runs no "
                    "gate matrix when every pushed remote ref is inside one."
                ),
            ),
        ]
        integration_branch: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "The one versioned line this workspace's repositories "
                    "integrate on. Baseline resolution checks exactly this "
                    "line against published Git and fails loud otherwise: "
                    "no conventional-name list is probed, and no release "
                    "name is hardcoded in the package. A consumer may "
                    "declare a recorded release tag (for example a "
                    "``v0.12.x`` ref) instead of a branch; a name published "
                    "as both branch and tag fails loud as ambiguous."
                ),
            ),
        ]

    class GithubActionPinSpec(FlextInfraModelsConfigContract.ConfigContract):
        """One GitHub Action reference from the codegen catalog."""

        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="GitHub owner/repository action name"),
        ]
        version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Upstream floating release tag the action rides"),
        ]

    class CiPrivateSubmoduleDeployKeySpec(
        FlextInfraModelsConfigContract.ConfigContract,
    ):
        """One read-only deploy key unlocking a private subproject in CI."""

        secret: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="GitHub Actions secret name holding the deploy key PEM",
            ),
        ]
        submodule: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "gitmodules submodule name (git config submodule.<name>.url)"
                ),
            ),
        ]
        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Checkout-relative submodule path"),
        ]
        remote: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^git@github\.com:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git$",
                description="Canonical GitHub SSH clone URL without a Host alias",
            ),
        ]

    class CiPrivateDependencyAuthSpec(FlextInfraModelsConfigContract.ConfigContract):
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
        repositories: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Selected repositories granted contents-read only",
            ),
        ]

    class CiSuperprojectCheckoutSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Containing workspace a member's CI checks out to install the root lock.

        A workspace member tracks no lock of its own: its CI checks out the
        containing workspace at its integration branch with the submodules,
        pins the member at the tested commit and runs the member verbs there.
        """

        repository: Annotated[
            t.NonEmptyStr,
            m.Field(
                pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$",
                description="GitHub owner/name of the containing workspace",
            ),
        ]
        ref: Annotated[
            t.NonEmptyStr,
            m.Field(description="Integration branch of the containing workspace"),
        ]
        path: Annotated[
            t.NonEmptyStr,
            m.Field(description="Member checkout path below the workspace root"),
        ]

    class CiPrivateSubmodulesSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Per-distribution private submodule init contract for generated CI."""

        _KNOWN_HOSTS_FIELD_COUNT: ClassVar[int] = 3

        known_hosts: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Pinned official SSH host-key lines used only in runner temp"
                ),
            ),
        ]

        paths: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description="Submodule paths to init before make setup",
            ),
        ]
        deploy_keys: Annotated[
            tuple[FlextInfraModelsConfigProvider.CiPrivateSubmoduleDeployKeySpec, ...],
            m.Field(min_length=1, description="Ordered deploy-key materializations"),
        ]

        @m.model_validator(mode="after")
        def _validate_private_submodule_identity(self) -> Self:
            """Keep path, key, and host identities complete and unambiguous.

            Returns:
                The resulting ``Self``.

            Raises:
                ValueError: If private submodule deploy-key paths must exactly match
                    paths; or if private submodule; or if private submodule known_hosts
                    must pin github.com ssh-ed25519.

            """
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


__all__: list[str] = ["FlextInfraModelsConfigProvider"]
