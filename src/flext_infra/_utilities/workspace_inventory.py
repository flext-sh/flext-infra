"""Consume the selected host's public workspace inventory through typed ingress.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u

from flext_infra import c, e, m, p, r


class FlextInfraUtilitiesWorkspaceInventory:
    """Discover guest repositories without maintaining a participant catalogue."""

    @classmethod
    def discover_external_consumers(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[tuple[m.Infra.ExternalConsumerSpec], ...]:
        """Read selected host identities, retaining the first native failure.

        Returns:
            Governing guests, or the first transport or inventory failure.

        """
        result = (r[tuple[m.Infra.ExternalConsumerSpec], ...],)
        command = inputs.spec.repository.workspace_inventory_command
        if not command:
            return result.ok(())
        executed = u.Cli.run(
            command,
            cwd=root,
            options=m.Cli.ProcessOptions(
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            ),
        )
        if executed.failure:
            return result.from_failure(executed)
        try:
            return cls._collect_consumers(root, executed.value.stdout)
        except (e.PydanticValidationError, OSError) as exc:
            return result.fail(
                f"public host workspace inventory is invalid: {exc}",
                exception=exc,
            )

    @staticmethod
    def _collect_consumers(
        root: Path,
        payload: str,
    ) -> p.Result[tuple[m.Infra.ExternalConsumerSpec], ...]:
        """Parse host ingress once and elect governing guests in inventory order.

        Returns:
            Ordered guest contracts, or the first rejected entry.

        """
        result = (r[tuple[m.Infra.ExternalConsumerSpec], ...],)
        inventory = m.Infra.HostWorkspaceInventory.model_validate_json(payload)
        workspace_root = root.resolve(strict=True)
        consumers: list[m.Infra.ExternalConsumerSpec] = []
        identities: set[str | Path] = set()
        for entry in inventory.entries:
            if entry.checkout_id != entry.governing_checkout_id:
                continue
            if not entry.path.is_absolute() or entry.path.is_symlink():
                return result.fail(
                    "host governing checkout is not a physical absolute root: "
                    f"{entry.path}"
                )
            external_root = entry.path.resolve(strict=True)
            if external_root.is_relative_to(workspace_root):
                continue
            if entry.project_profile == "unclassified":
                return result.fail(
                    "host governing project has no declared governance profile: "
                    f"{entry.project_id}"
                )
            if entry.project_id in identities or external_root in identities:
                return result.fail(
                    f"host inventory repeats a governing checkout: {entry.project_id}"
                )
            identities.update((entry.project_id, external_root))
            if not external_root.is_dir():
                return result.fail(
                    f"host governing checkout is not a directory: {external_root}"
                )
            own_flext = (
                entry.project_profile is c.Infra.ProjectKind.INTERNAL_FLEXT
                and entry.upstream_project_id is None
            )
            consumers.append(
                m.Infra.ExternalConsumerSpec(
                    name=entry.project_id,
                    root=external_root,
                    integration_branch=entry.effective_ref,
                    fix_namespace=own_flext,
                    fix_accessors=own_flext,
                )
            )
        return result.ok(tuple(consumers))


__all__ = ["FlextInfraUtilitiesWorkspaceInventory"]
