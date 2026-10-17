"""Public optional host inventory selection contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, m
from flext_infra._utilities.workspace_inventory import (
    FlextInfraUtilitiesWorkspaceInventory,
)
from tests import tm


class TestsFlextInfraWorkspaceInventory:
    """An unselected host has no transport or external participant contract."""

    @pytest.mark.parametrize("declare_repository", [False, True])
    def test_unselected_host_returns_no_external_participants(
        self,
        tmp_path: Path,
        *,
        declare_repository: bool,
    ) -> None:
        """Both legitimate configuration absences remain usable standalone."""
        declaration = (
            m.Infra.RepositoryDeltaSpec(workspace_inventory_command=())
            if declare_repository
            else None
        )
        inputs = m.Infra.CodegenInputs(
            spec=config.Infra.codegen.model_copy(
                update={"repository": declaration},
            ),
        )

        participants = tm.ok(
            FlextInfraUtilitiesWorkspaceInventory.discover_external_consumers(
                tmp_path,
                inputs,
            ),
        )

        tm.that(participants, empty=True)
