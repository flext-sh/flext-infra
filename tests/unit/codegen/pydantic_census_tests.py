"""Public behavior of the Pydantic census owner over one real Rope workspace.

The census classifies the authenticated inventory; this test proves the
classification rows and the delegated projector parity surface without
building a second inventory or parser.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPydanticCensus:
    """Validate the Pydantic census rows through the public owners."""

    @staticmethod
    def test_census_classifies_models_enums_and_full_domain_literals(
        tmp_path: Path,
    ) -> None:
        """Preset models, StrEnum owners and full-domain literals stay typed."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "sample.py"
        source = (
            "from enum import StrEnum\n"
            "from typing import Literal\n"
            "from flext_infra import m\n"
            "\n"
            "class Sample(m.BaseModel):\n"
            '    flag: Literal["a", "b"] = "a"\n'
            "\n"
            "class Colour(StrEnum):\n"
            '    RED = "red"\n'
        )
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            census = u.Infra.pydantic_census(
                workspace,
                sources={path: source},
            )
        tm.that(tuple(row.name for row in census.models), eq=("Sample",))
        tm.that(tuple(row.name for row in census.enums), eq=("Colour",))
        tm.that(len(census.literals), eq=1)
        tm.that(
            census.literals[0].kind,
            eq=c.Infra.PydanticLiteralKind.FULL_DOMAIN,
        )
        tm.that(census.literals[0].values, eq=("a", "b"))
        tm.that(census.parity, eq=())
