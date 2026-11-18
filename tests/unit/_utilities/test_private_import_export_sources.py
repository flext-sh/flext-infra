"""Authoritative export declarations do not require a materialized module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import infra
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraPrivateImportExportSources:
    """Keep alias bindings and unknown export computations distinct."""

    @staticmethod
    @c.Tests.MARK.parametrize("materialized", [False, True])
    @c.Tests.MARK.parametrize("dynamic", [False, True])
    def test_supplied_alias_exports_preserve_physical_and_virtual_semantics(
        tmp_path: Path, *, materialized: bool, dynamic: bool
    ) -> None:
        """Only explicit exports are admitted; source is never executed or written."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = f"{package.name}.consumer"
        path = package / "consumer.py"
        source = (
            "from absent_provider import Actual as Published\n"
            + (
                "__all__ = choose_exports()\n"
                if dynamic
                else "__all__ = ['Published']\n"
            )
            + "raise AssertionError('declarations must not execute')\n"
        )
        if materialized:
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root) as workspace:
            bindings, exports = u.Infra.declared_exports(
                {module: (source, False)}, project=workspace.rope_project
            )
        tm.that(bindings[f"{module}.Published"], eq={"absent_provider.Actual"})
        tm.that(
            exports.get(package.name, set()),
            eq=set() if dynamic else {f"{module}.Published"},
        )
        tm.that(path.exists(), eq=materialized)
        if materialized:
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
