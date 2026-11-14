# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/provider
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_infra import c, t


class FlextInfraProtocolsConfigProvider:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class ProviderIdentitySpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Declared provider key."""
            ...

        @property
        def organization(self) -> t.NonEmptyStr:
            """Git organization detected from the declared URL."""
            ...

        @property
        def base_url(self) -> t.NonEmptyStr:
            """HTTPS base URL detected from the declared URL."""
            ...

    @runtime_checkable
    class RepositorySourceSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr:
            """Repository distribution name."""
            ...

        @property
        def provider(self) -> t.NonEmptyStr:
            """Provider key owning URL and branch."""
            ...

        @property
        def kind(self) -> c.Infra.ProjectKind:
            """Structural member projected from the owning model.

            Governance kind declared for this repository; never assumed by a
            consumer of the identity.
            """
            ...

        @property
        def internal_distribution_prefix(self) -> str:
            """Derive the internal distribution namespace from the owner name."""
            ...

    @runtime_checkable
    class BranchPolicySpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def lane_remote(self) -> t.NonEmptyStr:
            """Remote whose live integration tip governs lanes."""
            ...

        @property
        def lane_temporary_roots(self) -> tuple[Path, ...]:
            """Temporary roots requiring registered ownership."""
            ...

        @property
        def lane_pr_limit(self) -> int:
            """PR page bound; saturation fails the inventory."""
            ...

        @property
        def lane_governance_file(self) -> Path | None:
            """Explicit host coordination SSOT, unavailable when undeclared."""
            ...

        @property
        def ci_trigger_branches(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Branches whose pushes trigger the generated CI workflow. Config owns
            this list: the renderer adds only the repository's own integration
            branch, so no fleet name is hardcoded in code.
            """
            ...

        @property
        def preservation_ref_namespaces(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Full-ref prefixes (ending in a slash) that hold WIP preservation pushes.
            The generated pre-push hook runs no gate matrix when every pushed remote
            ref is inside one.
            """
            ...

        @property
        def integration_branch(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            The one versioned line this workspace's repositories integrate on.
            Baseline resolution checks exactly this line against published Git and
            fails loud otherwise: no conventional-name list is probed, and no
            release name is hardcoded in the package. A consumer may declare a
            recorded release tag (for example a ``v0.12.x`` ref) instead of a
            branch; a name published as both branch and tag fails loud as ambiguous.
            """
            ...

    @runtime_checkable
    class GithubActionPinSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr:
            """GitHub owner/repository action name."""
            ...

        @property
        def version(self) -> t.NonEmptyStr:
            """Upstream floating release tag the action rides."""
            ...

    @runtime_checkable
    class CiPrivateSubmoduleDeployKeySpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def secret(self) -> t.NonEmptyStr:
            """GitHub Actions secret name holding the deploy key PEM."""
            ...

        @property
        def submodule(self) -> t.NonEmptyStr:
            """Gitmodules submodule name (git config submodule.<name>.url)."""
            ...

        @property
        def path(self) -> t.NonEmptyStr:
            """Checkout-relative submodule path."""
            ...

        @property
        def remote(self) -> t.NonEmptyStr:
            """Canonical GitHub SSH clone URL without a Host alias."""
            ...

    @runtime_checkable
    class CiPrivateDependencyAuthSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def app_id_secret(self) -> t.NonEmptyStr:
            """CI secret holding the private-dependency App id."""
            ...

        @property
        def private_key_secret(self) -> t.NonEmptyStr:
            """CI secret holding the private-dependency App key."""
            ...

        @property
        def repositories(self) -> tuple[t.NonEmptyStr, ...]:
            """Selected repositories granted contents-read only."""
            ...

    @runtime_checkable
    class CiSuperprojectCheckoutSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def repository(self) -> t.NonEmptyStr:
            """GitHub owner/name of the containing workspace."""
            ...

        @property
        def ref(self) -> t.NonEmptyStr:
            """Integration branch of the containing workspace."""
            ...

        @property
        def path(self) -> t.NonEmptyStr:
            """Member checkout path below the workspace root."""
            ...

        @property
        def submodules(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Declared workspace member paths the authenticated checkout initializes;
            every other superproject submodule stays untouched.
            """
            ...

    @runtime_checkable
    class CiPrivateSubmodulesSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def known_hosts(self) -> tuple[t.NonEmptyStr, ...]:
            """Pinned official SSH host-key lines used only in runner temp."""
            ...

        @property
        def paths(self) -> tuple[t.NonEmptyStr, ...]:
            """Submodule paths to init before make setup."""
            ...

        @property
        def deploy_keys(
            self,
        ) -> tuple[
            FlextInfraProtocolsConfigProvider.CiPrivateSubmoduleDeployKeySpec, ...
        ]:
            """Ordered deploy-key materializations."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigProvider",
]
