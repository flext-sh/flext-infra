"""Retire authenticated generation staging without undoing published files.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m
from flext_infra.codegen import (
    FlextInfraMiseArtifactsJournal as journal_io,
    FlextInfraMiseArtifactsState as state,
    FlextInfraMiseArtifactsVerification as verify,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseRecovery:
    """Preserve every live destination while retiring owned staging."""

    def execute(
        self,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        journal: m.Infra.CodegenTransactionJournal,
        journal_state: m.Cli.AtomicFileState,
    ) -> p.Result[bool]:
        """Clean authenticated staging without restoring any destination.

        Returns:
            The cleanup outcome, preserving its original failure.
        """
        topology = verify.journal_topology(layout, journal)
        if topology.failure:
            return topology
        authorized = state.validate_transaction_roots(layout, journal)
        if authorized.failure:
            return authorized
        return journal_io.cleanup(layout, journal, journal_state)


__all__: list[str] = ["FlextInfraMiseRecovery"]
