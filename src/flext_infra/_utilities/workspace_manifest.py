"""Single owner of the workspace manifest: its path, its load, its role.

Every consumer that needs the workspace manifest, or whether a checkout
declares itself a fleet umbrella, asks here. The workspace detector service
consumes this owner; no utility reaches back into the service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from functools import lru_cache
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, m, r
from flext_infra._utilities._pyproject.conform import (
    FlextInfraUtilitiesPyprojectConform,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesWorkspaceManifest:
    """Resolve, load and classify a checkout by its workspace manifest."""

    @staticmethod
    def repository_declaration_delta(
        legacy: m.Infra.WorkspaceManifestSpec,
    ) -> p.Result[m.Infra.RepositoryDeltaSpec]:
        """Extract only self-owned declarations for an explicit migration.

        This operation describes migration input. Runtime discovery must consume
        the resulting repository codegen declaration, never the legacy document.
        Composed members, exclusions, ledger copies and machine-local consumer
        paths cannot become repository declaration fields.

        Returns:
            The validated declaration belonging to the document's own repository.

        """
        result_type = r[m.Infra.RepositoryDeltaSpec]
        fields = set(m.Infra.RepositoryDeltaSpec.model_fields)
        values = legacy.model_dump(
            mode="json",
            include=fields.intersection(m.Infra.WorkspaceManifestSpec.model_fields),
            exclude_none=True,
            exclude_computed_fields=True,
        )
        values.update(
            legacy.repository.model_dump(
                mode="json",
                include=fields.intersection(m.Infra.RepositoryRef.model_fields),
                exclude_none=True,
                exclude_computed_fields=True,
            ),
        )
        for policy in legacy.repository_policy_overlays:
            if policy.project == legacy.repository.distribution:
                values.update(
                    policy.model_dump(
                        mode="json",
                        include=fields.intersection(
                            m.Infra.RepositoryPolicyOverlaySpec.model_fields,
                        ),
                        # Why: the overlay's ``project`` is the selector that
                        # matched this policy (the distribution name string);
                        # the delta's ``project`` is ProjectSpec metadata. The
                        # selector is admission, never delta content.
                        exclude={"project"},
                        exclude_computed_fields=True,
                    ),
                )
        validated = u.validate_value(m.Infra.RepositoryDeltaSpec, values)
        if validated.failure:
            return result_type.from_failure(validated)
        return result_type.ok(validated.value)

    @staticmethod
    def workspace_manifest_path(repository_root: Path) -> Path:
        """Return where the workspace manifest lives for one checkout.

        Returns:
            Where the workspace manifest lives for one checkout.

        """
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME

    @classmethod
    def load_workspace_manifest(
        cls,
        repository_root: Path,
    ) -> p.Result[Sequence[m.Infra.WorkspaceManifestSpec]]:
        """Load the checkout's own workspace manifest as a 0-or-1 sequence.

        Absence is an EMPTY sequence — success payloads are never ``None``.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.WorkspaceManifestSpec]]``.

        """
        manifest_path = cls.workspace_manifest_path(repository_root)
        if not manifest_path.is_file():
            return r[Sequence[m.Infra.WorkspaceManifestSpec]].ok(())
        text = u.Cli.files_read_text(manifest_path)
        if text.failure:
            return r[Sequence[m.Infra.WorkspaceManifestSpec]].fail(
                f"invalid workspace manifest ({manifest_path}): {text.error}",
            )
        return cls._parsed_workspace_manifest(text.value, str(manifest_path))

    @staticmethod
    @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
    def _parsed_workspace_manifest(
        text: str,
        manifest_path: str,
    ) -> p.Result[Sequence[m.Infra.WorkspaceManifestSpec]]:
        """Parse and validate one manifest text once per exact content.

        The key is the exact file text, so an edited manifest is a new key,
        never a stale spec.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.WorkspaceManifestSpec]]``.

        """
        loaded = u.Cli.yaml_parse(text)
        if loaded.failure:
            return r[Sequence[m.Infra.WorkspaceManifestSpec]].fail(
                f"invalid workspace manifest ({manifest_path}): {loaded.error}",
            )
        validated: p.Result[m.Infra.WorkspaceManifestSpec] = u.validate_value(
            m.Infra.WorkspaceManifestSpec,
            loaded.value,
        )
        if validated.failure:
            return r[Sequence[m.Infra.WorkspaceManifestSpec]].fail_op(
                f"workspace manifest model validation ({manifest_path})",
                validated.error,
            )
        return r[Sequence[m.Infra.WorkspaceManifestSpec]].ok((validated.value,))

    @classmethod
    def fleet_umbrella(cls, repository_root: Path) -> bool:
        """Whether this checkout declares governed participants in Git.

        Returns:
            The resulting ``bool``.

        """
        return bool(
            FlextInfraUtilitiesPyprojectConform.workspace_project_paths(
                repository_root
            ),
        )


__all__: list[str] = ["FlextInfraUtilitiesWorkspaceManifest"]
