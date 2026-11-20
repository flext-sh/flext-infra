"""Admit and publish every prepared bootstrap protocol package once.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, config, m, p, r, t
from flext_infra.protocols_bootstrap import consolidate_protocol_owners

if TYPE_CHECKING:
    from flext_infra._utilities.protocol_models import (
        FlextInfraUtilitiesModelsProtocol,
    )


class FlextInfraUtilitiesModelsProtocolBootstrapAdmission:
    """Own the guarded admission and publication of prepared package sources."""

    @classmethod
    def _bootstrap_publish_prepared(
        cls: "FlextInfraUtilitiesModelsProtocol",
        root: Path,
        project: p.Infra.RopeProject,
        ports: p.Infra.CodegenConformPorts,
        prepared: Sequence[t.Infra.BootstrapProtocolPackage],
    ) -> p.Result[bool]:
        """Admit the merged prepared packages once and publish the candidate.

        Returns:
            Whether the authenticated, normalized candidate changed live sources.

        """
        packages = tuple(part[0] for part in prepared)
        planned: dict[Path, str] = {}
        updates: dict[Path, str] = {}
        originals: dict[Path, p.Cli.AtomicFileState] = {}
        inputs: dict[Path, p.Cli.AtomicFileState] = {}
        members: list[tuple[str, str, tuple[str, ...]]] = []
        for (
            _package,
            part_planned,
            part_updates,
            part_originals,
            part_inputs,
            part_members,
        ) in prepared:
            planned.update(part_planned)
            updates.update(part_updates)
            originals.update(part_originals)
            inputs.update(part_inputs)
            members.extend(part_members)
        manifest = root / c.PYPROJECT_FILENAME
        merged = (packages, planned, originals, inputs, members)
        preview = ports.source_preview.preview_sources(
            root,
            {manifest: project.source_text(manifest), **updates},
            lambda candidate, paths: cls._bootstrap_admit_candidate(
                (root, ports), merged, candidate, paths
            ),
            options=m.Infra.StageSourceOptions.model_validate({
                "inputs": (tuple(inputs.values()))
            }),
        ).flat_map(lambda outcome: outcome)
        if preview.failure:
            return r[bool].from_failure(preview)
        plans, changes = preview.value
        published = ports.file_publisher.publish_normalized_codegen_plans(
            root, plans, changes
        )
        if published.failure:
            return r[bool].from_failure(published)
        cls._install_bootstrap_facade_members(members, root)
        return r[bool].ok(value=bool(published.value))

    @classmethod
    def _bootstrap_admit_candidate(
        cls: "FlextInfraUtilitiesModelsProtocol",
        owner: tuple[Path, p.Infra.CodegenConformPorts],
        merged: tuple[
            tuple[Path, ...],
            dict[Path, str],
            Mapping[Path, p.Cli.AtomicFileState],
            Mapping[Path, p.Cli.AtomicFileState],
            list[tuple[str, str, tuple[str, ...]]],
        ],
        candidate: Path,
        paths: Mapping[Path, Path],
    ) -> p.Result[
        tuple[tuple[p.Infra.CodegenFilePlan, ...], tuple[p.Cli.FileChange, ...]]
    ]:
        """Consolidate, normalize and validate one staged bootstrap candidate.

        Returns:
            The publication plans and normalized changes, or the first failure.

        """
        root, ports = owner
        packages, planned, originals, inputs, members = merged
        target = paths[root / c.PYPROJECT_FILENAME].parent
        consolidate_protocol_owners(target, planned)
        # Only the source-bootstrap protocol owner (flext-infra's own
        # family) republishes its bootstrap facade; consumers carry the
        # generated lazy init instead.
        exported = (
            cls._publish_bootstrap_protocol_facades(target, members)
            if any(
                cls._is_bootstrap_owned_protocol_package(
                    target / package.relative_to(root)
                )
                for package in packages
            )
            else r[bool].ok(value=False)
        )
        if exported.failure:
            return r[
                tuple[
                    tuple[p.Infra.CodegenFilePlan, ...],
                    tuple[p.Cli.FileChange, ...],
                ]
            ].from_failure(exported)
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=before,
                desired_content=(target / path.relative_to(root)).read_bytes(),
                desired_mode=before.mode
                if before.mode is not None
                else config.Infra.codegen.modes.file_default,
                inputs=tuple(inputs.values()),
            )
            for path, before in originals.items()
        )
        repaired = ports.file_publisher.normalized_codegen_changes(plans)
        if repaired.failure:
            return r[
                tuple[
                    tuple[p.Infra.CodegenFilePlan, ...],
                    tuple[p.Cli.FileChange, ...],
                ]
            ].from_failure(repaired)
        for change in repaired.value:
            destination = target / change.path.relative_to(root)
            if change.desired_content is None:
                destination.unlink()
            else:
                destination.write_bytes(change.desired_content)
        validated = ports.candidate_validator(root, candidate, (root,))
        if validated.failure:
            return r[
                tuple[
                    tuple[p.Infra.CodegenFilePlan, ...],
                    tuple[p.Cli.FileChange, ...],
                ]
            ].from_failure(validated)
        if not validated.value:
            return r[
                tuple[
                    tuple[p.Infra.CodegenFilePlan, ...],
                    tuple[p.Cli.FileChange, ...],
                ]
            ].fail("bootstrap candidate admission returned no acceptance")
        return r[
            tuple[
                tuple[p.Infra.CodegenFilePlan, ...],
                tuple[p.Cli.FileChange, ...],
            ]
        ].ok((plans, repaired.value))


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocolBootstrapAdmission"]
