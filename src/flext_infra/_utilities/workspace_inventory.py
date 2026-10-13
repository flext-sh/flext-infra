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

    @staticmethod
    def discover_external_consumers(
        root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[t.VariadicTuple[m.Infra.ExternalConsumerSpec]]:
        """Read selected host identities and retain each guest's own contract.

        Returns:
            Governing external checkouts, or the first native transport or input
            failure. An unselected host contributes no external participants.
        """
        result = r[t.VariadicTuple[m.Infra.ExternalConsumerSpec]]
        declaration = inputs.spec.repository
        if declaration is None:
            return result.ok(())
        command = declaration.workspace_inventory_command
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
            inventory = m.Infra.HostWorkspaceInventory.model_validate_json(
                executed.value.stdout,
            )
            workspace_root = root.resolve(strict=True)
            consumers: list[m.Infra.ExternalConsumerSpec] = []
            identities: set[str] = set()
            roots: set[Path] = set()
            for entry in inventory.entries:
                if entry.checkout_id != entry.governing_checkout_id:
                    continue
                if not entry.path.is_absolute() or entry.path.is_symlink():
                    return result.fail(
                        f"host governing checkout is not a physical absolute root: "
                        f"{entry.path}",
                    )
                external_root = entry.path.resolve(strict=True)
                if external_root.is_relative_to(workspace_root):
                    continue
                if entry.project_profile == "unclassified":
                    return result.fail(
                        f"host governing project has no declared governance profile: "
                        f"{entry.project_id}",
                    )
                if entry.project_id in identities or external_root in roots:
                    return result.fail(
                        f"host inventory repeats a governing checkout: "
                        f"{entry.project_id}",
                    )
                identities.add(entry.project_id)
                roots.add(external_root)
                if not external_root.is_dir():
                    return result.fail(
                        f"host governing checkout is not a directory: {external_root}",
                    )
                project_file = external_root / c.PYPROJECT_FILENAME
                flext_dependencies: t.StrSequence = ()
                if project_file.is_file():
                    loaded = u.Cli.toml_read_document(project_file)
                    if loaded.failure:
                        return result.from_failure(loaded)
                    flext_dependencies = (
                        FlextInfraUtilitiesDependencies.flext_dependency_namespaces(
                            loaded.value,
                        )
                    )
                own_flext = (
                    entry.project_profile
                    is FlextInfraConfigVocabulary.ProjectKind.INTERNAL_FLEXT
                    and entry.upstream_project_id is None
                )
                consumers.append(
                    m.Infra.ExternalConsumerSpec(
                        name=entry.project_id,
                        root=external_root,
                        integration_branch=entry.effective_ref,
                        advance_locks=bool(flext_dependencies),
                        fix_namespace=own_flext,
                        fix_accessors=own_flext,
                    ),
                )
            return result.ok(tuple(consumers))
        except (e.ValidationError, OSError) as exc:
            return result.fail(
                f"public host workspace inventory is invalid: {exc}",
                exception=exc,
            )


__all__ = ["FlextInfraUtilitiesWorkspaceInventory"]
