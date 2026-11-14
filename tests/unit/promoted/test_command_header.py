"""Promoted command headers are PEP 723 script blocks within the lint width.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from flext_infra import gates
from tests import c, config, p, tm, u


class TestsFlextInfraPromotedCommandHeader:
    """Read and render the ``[tool.flext.command]`` table of a script block.

    The scenario tree holds consumer-shaped commands
    whose headers still use the retired ``flext-command`` block, so every
    expectation is derived from what those consumers declared.
    """

    SCENARIO: Final = "promoted-header"
    COMMANDS: Final = (("charts", "adopt.py"), ("check", "docs.sh"))
    # Ruff names of the findings the retired block produced on consumers.
    COMMENT_CODE_RULE: Final = "commented-out-code"
    WIDTH: Final[int] = u.Infra.native_tool_setting(
        config.Infra.tooling, "ruff", "line-length", int
    )

    @classmethod
    def _commands(cls, fixture_tree: p.Tests.FixtureTree, root: Path) -> list[Path]:
        scripts = fixture_tree(cls.SCENARIO, destination=root)
        return [scripts / "scripts" / verb / name for verb, name in cls.COMMANDS]

    @classmethod
    def _rendered(cls, path: Path, width: int) -> str:
        """Return ``path`` with its legacy block replaced by the rendered header.

        Returns:
            The command source carrying the canonical header.

        """
        source = path.read_text(encoding=c.DEFAULT_ENCODING)
        block, command = u.Tests.promoted_legacy_header(source)
        header = u.Infra.promoted_render_header(command, width=width)
        return source.replace(block, f"{header}\n", 1)

    @classmethod
    def test_legacy_block_is_not_a_command_header(
        cls, fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> None:
        """The parser reads only the script block; the retired block is absent."""
        for path in cls._commands(fixture_tree, tmp_path):
            tm.instance(
                u.Infra.promoted_command_headers(path.parent)[path],
                c.Infra.PromotedMissingHeaderError,
            )

    @classmethod
    @c.Tests.MARK.parametrize("width", [WIDTH, 40, 200])
    def test_rendered_header_round_trips_within_width(
        cls,
        fixture_tree: p.Tests.FixtureTree,
        tmp_path: Path,
        width: int,
    ) -> None:
        """The rendered block parses back to the declared command, line by line."""
        for path in cls._commands(fixture_tree, tmp_path):
            _block, command = u.Tests.promoted_legacy_header(
                path.read_text(encoding=c.DEFAULT_ENCODING)
            )
            header = u.Infra.promoted_render_header(command, width=width)
            tm.that(max(len(line) for line in header.splitlines()), lte=width)
            tm.ok(
                u.Cli.atomic_write_text_file(path, cls._rendered(path, width)),
            )
            parsed = u.Infra.promoted_command_headers(path.parent)[path]
            tm.that(parsed, eq=command)
            if isinstance(parsed, c.Infra.PromotedRegistryError):
                raise parsed
            loaded = u.Infra.promoted_load_command(path, path.parent.name, parsed)
            tm.that(loaded.what, eq=path.stem)

    @classmethod
    def test_rendered_header_clears_comment_and_width_findings(
        cls, fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> None:
        """Ruff reports the retired block and accepts the rendered script block."""
        project = u.Tests.mk_project(
            tmp_path,
            "promoted-lint",
            pyproject='[project]\nname = "promoted-lint"\nversion = "0.1.0"\n',
        )
        python_command = next(
            path
            for path in cls._commands(fixture_tree, project)
            if path.suffix == c.Infra.EXT_PYTHON
        )
        width_rule = next(
            rule
            for rule, recipe in config.Infra.tooling.tools.ruff.lint.fix_recipes.items()
            if recipe is c.Infra.LintFixRecipe.WRAP_LONG_LINE
        )
        context = u.Tests.gate_context(tmp_path, tmp_path / "reports").model_copy(
            update={
                "ruff_args": (
                    "--select",
                    f"{cls.COMMENT_CODE_RULE},{width_rule}",
                    "--line-length",
                    str(cls.WIDTH),
                ),
            },
        )
        gate = gates.FlextInfraGatesRuffLint(tmp_path)
        legacy = gate.check(project, context)
        tm.fail(legacy.result.passed)
        tm.that(
            {issue.code for issue in legacy.issues},
            eq={cls.COMMENT_CODE_RULE, width_rule},
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                python_command, cls._rendered(python_command, cls.WIDTH)
            ),
        )
        rendered = gate.check(project, context)
        tm.ok(rendered.result.passed, msg=rendered.raw_output)
        tm.that(rendered.issues, empty=True)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("header", "missing"),
        [
            ("# /// script\n# dependencies = []\n# ///\n", True),
            ("# /// script\n# [tool.flext.command\n# ///\n", False),
            ("# /// script\n# [tool.flext.command]\n# ///\n" * 2, False),
        ],
        ids=["no-command-table", "invalid-toml", "two-script-blocks"],
    )
    def test_script_block_defects_keep_their_error_class(
        tmp_path: Path,
        header: str,
        *,
        missing: bool,
    ) -> None:
        """A block without the table is no command; a broken block is a defect."""
        path = tmp_path / "scripts" / "probe" / "probe.sh"
        tm.ok(u.Cli.atomic_write_text_file(path, f"#!/usr/bin/env bash\n{header}"))
        error = tm.instance(
            u.Infra.promoted_command_headers(path.parent)[path],
            c.Infra.PromotedRegistryError,
        )
        tm.that(
            isinstance(error, c.Infra.PromotedMissingHeaderError),
            eq=missing,
        )


__all__: list[str] = ["TestsFlextInfraPromotedCommandHeader"]
