"""Deterministic projection lock emitted beside the lazy-init projections.

``.agents/projections.lock.json`` (v1) is derived entirely from the composed
lazy-init file plans: one entry per projected ``.agents``/``.codex`` file with
its sha256 digest and byte length, ordered by path. Being just another plan
entry, the conform fixed-point gate owns its convergence, and workspace
consumers gain the machine-checkable contract their post-generation
projection synchronization verifies. The path deliberately avoids the
ai-hub-owned ``.agents/projection.json`` (the projection INPUT manifest);
this file is the projected OUTPUT state, owned by the generator alone.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenLazyInitProjectionManifest:
    """Derive the per-project projection manifest from composed file plans."""

    @staticmethod
    def projection_manifest_plans(
        *,
        files: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Append one manifest plan per project that owns projected files.

        Entries derive only from the other plans' desired states, so the
        manifest bytes are a pure function of the phase plan: stable order,
        stable digests, no self-reference.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]``.

        """
        projected: MutableMapping[
            Path, list[t.Pair[Path, p.Infra.ProjectionManifestEntry]]
        ] = {}
        for plan in files:
            if plan.desired_content is None:
                continue
            relative = plan.path.relative_to(plan.project)
            if relative.parts[0] not in c.Infra.PROJECTED_ROOTS:
                continue
            if relative.name == c.Infra.MANIFEST_FILENAME:
                continue
            projected.setdefault(plan.project, []).append((
                plan.path,
                m.Infra.ProjectionManifestEntry(
                    path=relative.as_posix(),
                    sha256=hashlib.sha256(plan.desired_content).hexdigest(),
                    bytes=len(plan.desired_content),
                ),
            ))
        plans: t.MutableSequenceOf[m.Infra.CodegenFilePlan] = []
        for project in sorted(projected):
            payload = m.Infra.ProjectionManifest.model_validate({
                "apiVersion": c.Infra.MANIFEST_API_VERSION,
                "entries": tuple(
                    sorted(
                        (entry for _, entry in projected[project]),
                        key=lambda entry: entry.path,
                    ),
                ),
            })
            serialized = u.Cli.json_dumps(
                payload.model_dump(mode="json", by_alias=True),
                indent=2,
            )
            if serialized.failure:
                return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(
                    serialized,
                )
            content = f"{serialized.value}\n".encode(c.DEFAULT_ENCODING)
            manifest_path = project / ".agents" / c.Infra.MANIFEST_FILENAME
            state = u.Cli.atomic_read_binary_file_state(manifest_path, required=False)
            if state.failure:
                return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].from_failure(state)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=project,
                    path=manifest_path,
                    before=state.value,
                    desired_content=content,
                    desired_mode=config.Infra.codegen.modes.file_default,
                    tracking_dependencies=tuple(
                        sorted(path for path, _ in projected[project])
                    ),
                ),
            )
        return r[t.VariadicTuple[m.Infra.CodegenFilePlan]].ok(tuple(plans))


__all__: tuple[str, ...] = ("FlextInfraCodegenLazyInitProjectionManifest",)
