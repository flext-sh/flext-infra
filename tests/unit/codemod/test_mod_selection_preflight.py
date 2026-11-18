"""A mod selection is validated before the route queues (ADR-032 fail early).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import infra
from tests import m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraModSelectionPreflight:
    """Unknown authored rule IDs fail at once; catalog IDs are accepted."""

    @staticmethod
    def _project(tmp_path: Path) -> Path:
        return u.Tests.mk_project(
            tmp_path,
            "preflight",
            pyproject='[project]\nname = "preflight"\nversion = "0.1.0"\n',
            with_src=True,
        )

    @classmethod
    def test_unknown_rule_id_fails_before_any_run(cls, tmp_path: Path) -> None:
        """A rule ID no governed catalog declares is refused by name."""
        root = cls._project(tmp_path)

        result = infra.mod_selection(
            m.Infra.ModCommand(repository_root=root, rule_ids=("no-such-rule-id",))
        )

        tm.fail(result, has="unknown codemod rule IDs: no-such-rule-id")

    @classmethod
    def test_authored_rule_id_is_accepted(cls, tmp_path: Path) -> None:
        """A rule ID from the repository's authored catalog passes the preflight."""
        root = cls._project(tmp_path)
        authored = tm.ok(u.Infra.codemod_compose_rule_plan(root, {root: None}))

        result = infra.mod_selection(
            m.Infra.ModCommand(repository_root=root, rule_ids=(authored.rules[0].id,))
        )

        tm.ok(result)


__all__: list[str] = ["TestsFlextInfraModSelectionPreflight"]
