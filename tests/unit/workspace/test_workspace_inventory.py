"""Public optional host inventory selection contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, e, m, u
from tests import c, tm


class TestsFlextInfraWorkspaceInventory:
    """Host selection and typed ingress retain native failures."""

    @staticmethod
    @pytest.mark.parametrize("text", [None, '{"entries":[]}', "{", "[]", ""])
    def test_host_selection_preserves_native_failures(
        tmp_path: Path,
        text: str | None,
    ) -> None:
        """Validate real host stdout and preserve native transport/ingress failures."""
        command = (
            ("printf", "%s", text)
            if text
            else (c.ParserBooleanToken.FALSE,)
            if text == ""
            else ()
        )
        inputs = m.Infra.CodegenInputs(
            spec=m.Infra.CodegenConfigSpec.model_validate(
                config.Infra.codegen.model_dump(
                    by_alias=True, exclude_computed_fields=True
                )
                | {"repository": {"workspace_inventory_command": command}},
            ),
        )

        discovered = u.Infra.discover_external_consumers(tmp_path, inputs)
        if text in {"{", "[]", ""}:
            tm.fail(discovered)
            if text:
                tm.that(discovered.exception, is_=e.PydanticValidationError)
        else:
            tm.that(tm.ok(discovered), empty=True)
