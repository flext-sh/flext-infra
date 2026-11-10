"""A promoted command's file stem is its interpreter's name for the public WHAT.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from flext_infra import FlextInfraPromoted
from tests import c, config, tm, u


class TestsFlextInfraPromotedCommandStem:
    """Discovery maps a kebab-case WHAT onto a valid Python module name.

    A Python command is a module the fleet's Ruff policy names like any other
    (N999), so ``what = "krr-sizing"`` lives in ``krr_sizing.py``; a shell
    command keeps the WHAT exactly. The scenario mirrors the cosmos-main
    ``scripts/finops`` directory, where both kinds share one verb.
    """

    VERB: Final = "finops"
    PYTHON_WHAT: Final = "krr-sizing"
    SHELL_WHAT: Final = "reconcile-oci-usage"
    WIDTH: Final[int] = u.Infra.native_tool_setting(
        config.Infra.tooling, "ruff", "line-length", int
    )

    @classmethod
    def _write_command(cls, root: Path, name: str, what: str) -> Path:
        """Write one command whose canonical header declares ``what``.

        Returns:
            The command file path.

        """
        header = u.Infra.promoted_render_header(
            {
                "verb": cls.VERB,
                "what": what,
                "domain": "finops",
                "summary": f"Run {what}",
                "description": f"Run the read-only {what} report.",
                "example": f"make {cls.VERB} WHAT={what}",
                "mutates": False,
            },
            width=cls.WIDTH,
        )
        path = root / c.Infra.DIR_SCRIPTS / cls.VERB / name
        shebang = (
            "#!/usr/bin/env python3"
            if path.suffix == c.Infra.EXT_PYTHON
            else "#!/usr/bin/env bash"
        )
        tm.ok(u.Cli.atomic_write_text_file(path, f"{shebang}\n{header}\n"))
        return path

    @staticmethod
    def _discover(root: Path) -> FlextInfraPromoted:
        """Discover the registry of one repository's own script root.

        Returns:
            The validated registry.

        """
        u.Tests.initialize_git_repo(root)
        return FlextInfraPromoted.discover(
            script_roots=(root / c.Infra.DIR_SCRIPTS,),
            spec=u.Infra.promoted_workspace_spec(root),
        )

    @classmethod
    def test_unrelated_scripts_contribute_no_promoted_commands(
        cls,
        tmp_path: Path,
    ) -> None:
        """An empty discovery does not invalidate another declared dispatcher."""
        source = tmp_path / c.Infra.DIR_SCRIPTS / "run" / "report.py"
        tm.ok(u.Cli.atomic_write_text_file(source, 'print("report")\n'))
        original = source.read_bytes()
        registry = cls._discover(tmp_path)
        tm.that(registry.verbs(), length=0)
        tm.that(source.read_bytes(), eq=original)

    @classmethod
    def test_each_command_file_declares_its_public_what(
        cls,
        tmp_path: Path,
    ) -> None:
        """A ``.py`` stem replaces ``-`` with ``_``; a ``.sh`` stem is WHAT."""
        python = cls._write_command(tmp_path, "krr_sizing.py", cls.PYTHON_WHAT)
        shell = cls._write_command(tmp_path, f"{cls.SHELL_WHAT}.sh", cls.SHELL_WHAT)
        registry = cls._discover(tmp_path)
        tm.that(registry.command(cls.VERB, cls.PYTHON_WHAT).path, eq=python)
        tm.that(registry.command(cls.VERB, cls.SHELL_WHAT).path, eq=shell)

    @classmethod
    @c.Tests.MARK.parametrize(
        ("name", "what", "expected"),
        [
            ("krr-sizing.py", PYTHON_WHAT, "krr_sizing"),
            ("reconcile_oci_usage.sh", SHELL_WHAT, SHELL_WHAT),
        ],
    )
    def test_command_file_with_another_stem_fails_loud(
        cls,
        tmp_path: Path,
        name: str,
        what: str,
        expected: str,
    ) -> None:
        """Any other stem is a defect naming the one stem WHAT selects."""
        path = cls._write_command(tmp_path, name, what)
        with u.Tests.raises(
            c.Infra.PromotedRegistryError,
            match=re.escape(
                f"{path}: header what={what} requires the file stem {expected}"
            ),
        ):
            cls._discover(tmp_path)


__all__: list[str] = ["TestsFlextInfraPromotedCommandStem"]
