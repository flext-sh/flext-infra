"""Public census evidence for constants declared outside their owning family.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, infra
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraConstantsCensusOwnership:
    """The constants contract overrides a containing file's behavior family."""

    @pytest.mark.parametrize(
        "relative_module",
        [
            "_utilities/base.py",
            "_protocols/base.py",
            "_models/base.py",
            "service.py",
        ],
    )
    @pytest.mark.parametrize(
        ("typing_import", "name", "annotation"),
        [
            ("from typing import ClassVar", "PROTOCOL_TOKEN", "ClassVar[str]"),
            ("from typing import Final", "protocol_token", "Final[str]"),
            (
                "from typing import Final as Immutable",
                "protocol_token",
                "Immutable[str]",
            ),
            ("import typing as types", "protocol_token", "types.Final[str]"),
        ],
    )
    def test_constant_is_owned_by_constants_in_every_source_family(
        self,
        tmp_path: Path,
        relative_module: str,
        typing_import: str,
        name: str,
        annotation: str,
    ) -> None:
        """Observe the real Rope census without freezing configuration values."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        path = package / relative_module
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "from __future__ import annotations\n"
            f"{typing_import}\n"
            "class Declaration:\n"
            f"    {name}: {annotation} = 'fixture-token'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(root) as workspace:
            constants = tuple(
                item
                for item in workspace.objects(
                    path,
                    include_local_scopes=True,
                    include_references=False,
                )
                if item.name == name
            )
        tm.that(constants, none=False, empty=False)
        expected_family = u.Infra.facade_families()["c"].suffix
        for item in constants:
            tm.that(item.expected_tier, eq=expected_family)
            tm.that(item.actual_tier, ne=expected_family)

    def test_user_final_homonym_remains_an_attribute(self, tmp_path: Path) -> None:
        """A user-defined Final name does not prove an immutable declaration."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        path = package / "service.py"
        path.write_text(
            "from __future__ import annotations\n"
            "class Final:\n"
            "    pass\n"
            "class Declaration:\n"
            "    token: Final = 'fixture-token'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(root) as workspace:
            declaration = next(
                item
                for item in workspace.objects(
                    path,
                    include_local_scopes=True,
                    include_references=False,
                )
                if item.scope_path == "Declaration.token"
            )
        tm.that(declaration.kind, eq="attribute")
