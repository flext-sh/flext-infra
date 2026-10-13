"""Consume the selected host's public workspace inventory through typed ingress.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u

from flext_infra import c, e, m, p, r, t
from flext_infra._models._config.vocabulary import FlextInfraConfigVocabulary
from flext_infra._utilities.dependencies import FlextInfraUtilitiesDependencies


class FlextInfraUtilitiesWorkspaceInventory:
    """Discover guest repositories without maintaining a participant catalogue."""

    @classmethod
    def discover_external_consumers(
        cls,
        root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[t.VariadicTuple[m.Infra.ExternalConsumerSpec]]:
        """Read selected host identities, retaining the first native failure."""
        result = r[t.VariadicTuple[m.Infra.ExternalConsumerSpec]]
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
            inventory = m.Infra.HostWorkspaceInventory.model_validate_json(executed.value.stdout)
            return cls._collect_consumers(root.resolve(strict=True), inventory)
        except (e.ValidationError, OSError) as exc:
            return result.fail(
                f"public host workspace inventory is invalid: {exc}",
                exception=exc,
            )

    @classmethod
    def _collect_consumers(
        cls, workspace_root: Path, inventory: m.Infra.HostWorkspaceInventory,
    ) -> p.Result[t.VariadicTuple[m.Infra.ExternalConsumerSpec]]:
        """Elect external governing checkouts in inventory order, rejecting duplicates."""
        result = r[t.VariadicTuple[m.Infra.ExternalConsumerSpec]]
        consumers: list[m.Infra.ExternalConsumerSpec] = []
        identities: set[str] = set()
        roots: set[Path] = set()
        for entry in inventory.entries:
            if entry.checkout_id != entry.governing_checkout_id:
                continue
            if not entry.path.is_absolute() or entry.path.is_symlink():
                return result.fail(f"host governing checkout is not a physical absolute root: {entry.path}")
            external_root = entry.path.resolve(strict=True)
            if external_root.is_relative_to(workspace_root):
                continue
            if entry.project_profile == "unclassified":
                return result.fail(f"host governing project has no declared governance profile: {entry.project_id}")
            if entry.project_id in identities or external_root in roots:
                return result.fail(f"host inventory repeats a governing checkout: {entry.project_id}")
            identities.add(entry.project_id)
            roots.add(external_root)
            if not external_root.is_dir():
                return result.fail(f"host governing checkout is not a directory: {external_root}")
            consumer = cls._consumer_contract(entry, external_root)
            if consumer.failure:
                return result.from_failure(consumer)
            consumers.append(consumer.value)
        return result.ok(tuple(consumers))

    @staticmethod
    def _consumer_contract(
        entry: m.Infra.HostWorkspaceInventoryEntry, root: Path,
    ) -> p.Result[m.Infra.ExternalConsumerSpec]:
        """Derive guest capabilities from its own dependency and governance declarations."""
        result = r[m.Infra.ExternalConsumerSpec]
        dependencies: t.StrSequence = ()
        project_file = root / c.PYPROJECT_FILENAME
        if project_file.is_file():
            loaded = u.Cli.toml_read_document(project_file)
            if loaded.failure:
                return result.from_failure(loaded)
            dependencies = FlextInfraUtilitiesDependencies.flext_dependency_namespaces(loaded.value)
        own_flext = entry.project_profile is FlextInfraConfigVocabulary.ProjectKind.INTERNAL_FLEXT and entry.upstream_project_id is None
        return result.ok(m.Infra.ExternalConsumerSpec(
            name=entry.project_id, root=root, integration_branch=entry.effective_ref,
            advance_locks=bool(dependencies), fix_namespace=own_flext, fix_accessors=own_flext,
        ))


__all__ = ["FlextInfraUtilitiesWorkspaceInventory"]
