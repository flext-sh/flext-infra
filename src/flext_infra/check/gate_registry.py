"""Explicit registry of the workspace check gates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, p, r, t
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

if TYPE_CHECKING:
    from flext_infra.gates import FlextInfraGate


class FlextInfraGateRegistry:
    """Explicit gate registry mapping gate IDs to gate classes."""

    def __init__(
        self,
        *,
        runners: t.MappingKV[str, p.Cli.CommandRunner] | None = None,
    ) -> None:
        """Build the gate-id to gate-class mapping used by check execution.

        ``c.Infra.GATE_TOOLS_BY_KIND`` is the sole gate vocabulary: every
        registered class declares its ``gate_id`` from those same constants,
        and the SARIF tool identity, the allowed gate set, and the fixable
        vocabulary are all derived from that one declaration, so the
        registry and the vocabulary cannot name different gates. Two classes
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
        self._runners = dict(runners or {})

    @staticmethod
    def _gate_classes() -> t.VariadicTuple[type[FlextInfraGate]]:
        """Return the runtime gate classes registered for workspace checks.

        Returns:
            The runtime gate classes registered for workspace checks.

        """
        return (
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
            if (
                owner == c.Infra.LINT
                or owner not in c.Infra.ALLOWED_GATES
                or owner not in c.Infra.CANONICAL_FILE_GATE_IDS
                or gate is None
                or not gate.can_fix
                or owner not in check_gates
                or owner not in repair_gates
            ):
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
