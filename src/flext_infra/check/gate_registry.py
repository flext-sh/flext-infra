"""Explicit registry of the workspace check gates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, m, p, r, t
from flext_infra.gates import (
    FlextInfraBanditGate,
    FlextInfraConflictMarkersGate,
    FlextInfraDepsGate,
    FlextInfraDirenvGate,
    FlextInfraDuplicationGate,
    FlextInfraFreshImportGate,
    FlextInfraIndexDeclarationsGate,
    FlextInfraLayoutGate,
    FlextInfraLocCapGate,
    FlextInfraMarkdownCodeGate,
    FlextInfraMarkdownFormatGate,
    FlextInfraMarkdownGate,
    FlextInfraMypyGate,
    FlextInfraPyreflyGate,
    FlextInfraPyrightGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
    FlextInfraRuntimeCensusGate,
    FlextInfraSmellsGate,
)
from flext_infra.gates.codemod import FlextInfraCodemodGate
from flext_infra.gates.runtime_integrity import (
    FlextInfraProjectModuleGate,
    FlextInfraRuntimeIntegrityGate,
)

if TYPE_CHECKING:
    from flext_infra.gates import FlextInfraGate


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    def __init__(
        self,
        *,
        runners: t.MappingKV[str, p.Cli.CommandRunner] | None = None,
        project_gates: t.SequenceOf[m.Infra.MakeProjectCheckGateSpec] = (),
    ) -> None:
        """Build the gate-id to gate-class mapping used by check execution.

        ``c.Infra.GATE_TOOLS_BY_KIND`` owns built-in vocabulary; the repository's
        typed ``project_check_gates`` owns its native module extensions. The
        registry is their exact union and rejects collisions. Two classes
        claiming one id remain a registration defect that fails the registry
        before a single gate can run, never a gate that silently cannot be
        reached through ``make check``.

        Raises:
            ValueError: If gate registry declares duplicate gate ids.

        """
        classes = self._gate_classes()
        self._gates: MutableMapping[str, type[FlextInfraGate]] = {
            gate_cls.gate_id: gate_cls for gate_cls in classes
        }
        if len(self._gates) != len(classes):
            msg = "gate registry declares duplicate gate ids"
            raise ValueError(msg)
        for declaration in project_gates:
            if declaration.name in self._gates:
                msg = f"gate registry declares duplicate gate id: {declaration.name}"
                raise ValueError(msg)
            self._gates[declaration.name] = type(
                declaration.name,
                (FlextInfraProjectModuleGate,),
                {
                    "gate_id": declaration.name,
                    "gate_name": declaration.name,
                    "check_module_command_prefix": (
                        declaration.module,
                        *declaration.arguments,
                    ),
                    "check_timeout": declaration.timeout_seconds,
                },
            )
        self._runners = dict(runners or {})

    @property
    def gate_ids(self) -> t.StrTuple:
        """Exact built-in and repository-declared gate vocabulary."""
        return tuple(self._gates)

    def applicable_gate_ids(
        self, gate_ids: t.StrSequence, project_dir: Path
    ) -> t.StrTuple:
        """Elect applicability through each registered gate's existing owner.

        Returns:
            The gate identifiers selected for the project directory.

        """
        return tuple(
            gate_id
            for gate_id in gate_ids
            if self._gates[gate_id](project_dir).selected_for(project_dir)
        )

    @staticmethod
    def _gate_classes() -> t.VariadicTuple[type[FlextInfraGate]]:
        """Return the runtime gate classes registered for workspace checks.

        Returns:
            The runtime gate classes registered for workspace checks.

        """
        return (
            FlextInfraRuntimeIntegrityGate,
            FlextInfraRuffLintGate,
            FlextInfraConflictMarkersGate,
            FlextInfraDepsGate,
            FlextInfraRuffFormatGate,
            FlextInfraPyreflyGate,
            FlextInfraMypyGate,
            FlextInfraPyrightGate,
            FlextInfraBanditGate,
            FlextInfraMarkdownGate,
            FlextInfraMarkdownFormatGate,
            FlextInfraMarkdownCodeGate,
            FlextInfraLocCapGate,
            FlextInfraRuntimeCensusGate,
            FlextInfraFreshImportGate,
            FlextInfraLayoutGate,
            FlextInfraIndexDeclarationsGate,
            FlextInfraSmellsGate,
            FlextInfraCodemodGate,
            FlextInfraDirenvGate,
            FlextInfraDuplicationGate,
        )

    def get(self, gate_id: str) -> type[FlextInfraGate] | None:
        """Return the registered gate class for one gate id, when present.

        Returns:
            The registered gate class for one gate id, when present.

        """
        return self._gates.get(gate_id)

    def delegated_lint_rules(
        self,
        owners: t.StrMapping,
        *,
        check_gates: t.StrSequence,
        repair_gates: t.StrSequence,
    ) -> t.StrTuple:
        """Derive native delegation only for elected checking and repair owners.

        Returns:
            Declared rules whose registered owner remains in both contracts.

        Raises:
            ValueError: If an owner is unknown, self-owned, or not elected with
                a native checking and repair implementation.

        """
        for rule, owner in owners.items():
            gate = self.get(owner)
            native_owner = (
                owner != c.Infra.LINT
                and owner in c.Infra.ALLOWED_GATES
                and owner in c.Infra.CANONICAL_FILE_GATE_IDS
                and gate is not None
                and gate.can_fix
            )
            elected = owner in check_gates and owner in repair_gates
            if not (native_owner and elected):
                msg = (
                    f"Ruff rule {rule} requires an elected native check/repair "
                    f"owner: {owner}"
                )
                raise ValueError(msg)
        return tuple(sorted(owners))

    def runtime_identity(
        self,
        gate_ids: t.StrSequence,
        *,
        installed_identity: str,
    ) -> p.Result[str]:
        """Fingerprint selected provisioned scanners through their existing owners.

        Python module tools are bound by the shared installed-distribution owner.
        Only declared scanner binaries participate here; no project/tool roster
        is introduced.

        Returns:
            An opaque digest of actual selected external executable identities.

        """
        observed: list[str] = []
        for gate_id in gate_ids:
            gate = self.get(gate_id)
            if gate is None:
                return r[str].fail(
                    f"unregistered gate has no runtime identity: {gate_id}"
                )
            if not gate.scanner_binary:
                continue
            executable = gate.resolve_binary()
            if executable is None:
                return r[str].fail(
                    f"selected scanner is not provisioned: {gate.scanner_binary}",
                )
            content = u.Cli.files_read_binary(executable)
            if content.failure:
                return r[str].from_failure(content)
            observed.append(
                f"{gate_id}:{gate.scanner_binary}:{u.Cli.sha256_bytes(content.value)}",
            )
        return r[str].ok(
            u.Cli.sha256_content(
                "\n".join((installed_identity, *observed)),
            )
        )

    def create(self, gate_id: str, repository_root: Path) -> FlextInfraGate | None:
        """Instantiate one registered gate for ``repository_root`` when available.

        Returns:
            The resulting ``FlextInfraGate | None``.

        """
        gate_cls = self._gates.get(gate_id)
        return (
            gate_cls(repository_root, runner=self._runners.get(gate_id))
            if gate_cls
            else None
        )

    @classmethod
    def default(cls) -> FlextInfraGateRegistry:
        """Return the default registry instance for workspace checks.

        Returns:
            The default registry instance for workspace checks.

        """
        return cls()


__all__: list[str] = ["FlextInfraGateRegistry"]
