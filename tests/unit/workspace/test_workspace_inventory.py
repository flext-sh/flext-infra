"""Public optional host inventory selection contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, m, u
from tests import tm


class TestsFlextInfraWorkspaceInventory:
    """An unselected host has no transport or external participant contract."""

    def test_unselected_host_returns_no_external_participants(
        self,
        tmp_path: Path,
    ) -> None:
        """An empty inventory command leaves the host unselected."""
        inputs = m.Infra.CodegenInputs(
            spec=m.Infra.CodegenConfigSpec.model_validate(
                config.Infra.codegen.model_dump(
                    by_alias=True, exclude_computed_fields=True
                )
                | {"repository": {"workspace_inventory_command": []}},
            ),
        )

        participants = tm.ok(
            u.Infra.discover_external_consumers(
                tmp_path,
                inputs,
            ),
        )

        tm.that(participants, empty=True)
