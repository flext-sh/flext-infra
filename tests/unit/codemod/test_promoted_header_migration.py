"""The promoted-header migration rule rewrites retired blocks exactly once.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from tests import FlextInfraCli, c, p, tm, u


@c.Tests.MARK.slow
class TestsFlextInfraPromotedHeaderMigration:
    """Drive the packaged text rule through ``refactor mod --rule-ids``.

    That route is what ``make mod RULES=<id>`` invokes. The scenario tree
    holds consumer-shaped commands, one Python and one
    shell, so the rule meets the headers consumers actually carry.
    """

    RULE: Final = "promoted-command-header-pep723"
    SCENARIO: Final = "promoted-header"
    COMMANDS: Final = (("charts", "adopt.py"), ("check", "docs.sh"))

    @staticmethod
    def _run(root: Path, *arguments: str) -> int:
        return FlextInfraCli.infra_main([
            "refactor",
            "mod",
            "--repository-root",
            str(root),
            *arguments,
        ])

    @classmethod
    def test_rule_rewrites_every_retired_header_once(
        cls,
        mod_workspace: Path,
        fixture_tree: p.Tests.FixtureTree,
    ) -> None:
        """Check is red, apply renders the header, and a rerun changes nothing."""
        fixture_tree(cls.SCENARIO, destination=mod_workspace)
        commands = [
            mod_workspace / "scripts" / verb / name for verb, name in cls.COMMANDS
        ]
        width: int = u.Infra.native_tool_setting(
            tm.ok(u.Infra.load_tooling_inputs(mod_workspace)).document,
            "ruff",
            "line-length",
            int,
        )
        before = {
            path: path.read_text(encoding=c.DEFAULT_ENCODING) for path in commands
        }
        declared = {
            path: u.Tests.promoted_legacy_header(source)
            for path, source in before.items()
        }

        tm.that(cls._run(mod_workspace, "--check", "--rule-ids", cls.RULE), ne=0)
        for path, source in before.items():
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

        tm.that(cls._run(mod_workspace, "--rule-ids", cls.RULE), eq=0)
        migrated: dict[Path, bytes] = {}
        for path, (block, command) in declared.items():
            header = u.Infra.promoted_render_header(command, width=width)
            tm.that(
                path.read_text(encoding=c.DEFAULT_ENCODING),
                eq=before[path].replace(block, f"{header}\n", 1),
            )
            tm.that(u.Infra.promoted_command_headers(path.parent)[path], eq=command)
            migrated[path] = path.read_bytes()

        tm.that(cls._run(mod_workspace, "--rule-ids", cls.RULE), eq=0)
        tm.that(cls._run(mod_workspace, "--check", "--rule-ids", cls.RULE), eq=0)
        tm.that({path: path.read_bytes() for path in commands}, eq=migrated)


__all__: list[str] = ["TestsFlextInfraPromotedHeaderMigration"]
