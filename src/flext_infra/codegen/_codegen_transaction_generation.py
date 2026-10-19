"""Shared journal preparation for native file publication phases.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, r, t
from flext_infra.codegen._codegen_transaction_phases import (
    FlextInfraCodegenTransactionPhases,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenTransactionGeneration(FlextInfraCodegenTransactionPhases):
    """Materialize the journal used by the single file-phase publisher."""

    def __init__(
        self,
        owner: p.Infra.MiseArtifactsOwner,
        *,
        participant_policy: p.Infra.CodegenParticipantPolicy | None = None,
        producer: m.Infra.CodegenPhaseAnalysis | None = None,
        source_authority: m.Infra.CodegenSourceAuthority | None = None,
        prior_publications: t.VariadicTuple[m.Infra.CodegenPhaseOutcome] = (),
    ) -> None:
        """Retain the configured consumer used by explicit runtime validation."""
        super().__init__(
            owner,
            participant_policy=participant_policy,
            producer=producer,
            source_authority=source_authority,
            prior_publications=prior_publications,
        )
        self._owner = owner

    def _materialize_journal(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        *,
        expected: m.Cli.AtomicFileState,
    ) -> p.Result[t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]]:
        """Persist one journal revision, then materialize its planned directories.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.CodegenTransactionJournal,
                m.Cli.AtomicFileState]]``.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenTransactionJournal, m.Cli.AtomicFileState]
        ]
        persisted = self._write_journal(layout, journal, expected=expected)
        if persisted.failure:
            return result_type.from_failure(persisted)
        materialized = self._materialize_directories(layout, journal, persisted.value)
        if materialized.failure:
            return result_type.from_failure(materialized)
        recorded, recorded_state = materialized.value
        return result_type.ok((recorded, recorded_state))


__all__: list[str] = ["FlextInfraCodegenTransactionGeneration"]
