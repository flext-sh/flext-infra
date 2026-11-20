"""Publish bootstrap protocol sources for every declared owning package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from flext_infra import p, r, t
from flext_infra._utilities import FlextInfraUtilitiesWorkspaceSnapshot
from flext_infra._utilities._protocol_models.bootstrap_admission import (
    FlextInfraUtilitiesModelsProtocolBootstrapAdmission,
)


class FlextInfraUtilitiesModelsProtocolBootstrapSources(
    FlextInfraUtilitiesModelsProtocolBootstrapAdmission,
):
    """Own the source-bootstrap entry point and prepared-package planning."""

    @classmethod
    def bootstrap_protocol_model_sources(
        cls, repository_root: Path, *, ports: p.Infra.CodegenConformPorts
    ) -> p.Result[bool]:
        """Publish bootstrap sources for every declared package owning models.

        Every package prepares its sources in one source view and the candidate
        is admitted once, so the fresh-import gate sees the complete projection.

        Returns:
            Whether the authenticated, normalized candidate changed live sources.

        """
        root = repository_root.expanduser().resolve()
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            root
        ) as binding:
            project = binding[0]
            projection = cls._ModelProtocolProjection(root, project)
            primary = projection.source_layout()
            # Only the source-bootstrap owner (flext-infra's own protocol family)
            # projects ahead of the surfaces: its engine imports those holders.
            # A consumer's projection is planned by the lazy-init surface, in the
            # same ordered candidate as its regenerated initializers. A repository
            # without a primary package (a consumer) owns no source bootstrap.
            if primary is None or not cls._is_bootstrap_owned_protocol_package(
                primary[0]
            ):
                return r[bool].ok(value=False)
            prepared = cls._bootstrap_prepared_packages(
                root,
                project,
                (
                    *(
                        (layout[2], True)
                        for layout in projection.namespacesource_layouts()
                    ),
                    (primary[2], False),
                ),
            )
            if prepared.failure:
                return r[bool].from_failure(prepared)
            if not prepared.value:
                return r[bool].ok(value=False)
            return cls._bootstrap_publish_prepared(root, project, ports, prepared.value)

    @classmethod
    def _bootstrap_prepared_packages(
        cls,
        root: Path,
        project: p.Infra.RopeProject,
        packages: Sequence[tuple[str, bool]],
    ) -> p.Result[Sequence[t.Infra.BootstrapProtocolPackage]]:
        """Prepare every declared package's bootstrap sources in one source view.

        Returns:
            The prepared packages declaring a projection, or the first failure.

        """
        prepared: list[t.Infra.BootstrapProtocolPackage] = []
        for package_name, namespace_package in packages:
            part = cls._bootstrap_package_sources(
                root,
                project,
                package_name=package_name,
                namespace_package=namespace_package,
            )
            if part.failure:
                return r[Sequence[t.Infra.BootstrapProtocolPackage]].from_failure(part)
            if part.value is not None:
                prepared.append(part.value)
        return r[Sequence[t.Infra.BootstrapProtocolPackage]].ok(prepared)


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocolBootstrapSources"]
