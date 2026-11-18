"""Line wrapping never edits a ``# /// <type>`` structured comment block.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from flext_infra import gates
from tests import c, config, tm, u


class TestsFlextInfraWrapStructuredBlocks:
    """Wrapping a comment reflows prose; a structured block carries TOML.

    Reflowing one key of a PEP 723 block splits its string across lines and
    leaves invalid TOML, while the module AST, which drops comments, stays
    equal. The block text itself therefore guards the repair.
    """

    LIMIT: Final[int] = u.Infra.native_tool_setting(
        config.Infra.tooling, "ruff", "line-length", int
    )
    WIDTH_RULE: Final = next(
        rule
        for rule, recipe in config.Infra.tooling.tools.ruff.lint.fix_recipes.items()
        if recipe is c.Infra.LintFixRecipe.WRAP_LONG_LINE
    )

    @classmethod
    def test_fix_keeps_a_long_block_line_and_its_finding(cls, tmp_path: Path) -> None:
        """``make fix`` leaves block lines byte for byte and reports them."""
        project = u.Tests.mk_project(
            tmp_path,
            "block-wrap",
            pyproject='[project]\nname = "block-wrap"\nversion = "0.1.0"\n',
            with_src=True,
        )
        prose = " ".join(["palavra"] * cls.LIMIT)
        content = (
            "# /// script\n"
            "# [tool.probe]\n"
            f'# description = "{prose}"\n'
            "# ///\n"
            '"""Probe module."""\n'
        )
        source = project / "src" / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(source, content))
        context = u.Tests.gate_context(tmp_path, tmp_path / "reports").model_copy(
            update={
                "apply_fixes": True,
                "ruff_args": (
                    "--select",
                    cls.WIDTH_RULE,
                    "--line-length",
                    str(cls.LIMIT),
                ),
            },
        )
        gate = gates.FlextInfraGatesRuffLint(tmp_path)
        execution = gate.fix(project, context)
        tm.fail(execution.result.passed)
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
        tm.that([issue.code for issue in execution.issues], eq=[cls.WIDTH_RULE])
        tm.that(execution.issues, eq=gate.check(project, context).issues)

    @classmethod
    def test_wrap_refuses_a_repair_that_changes_block_text(cls) -> None:
        """A reflow that would open a new block fails instead of publishing it."""
        opening = " /// script"
        words = "x" * (cls.LIMIT - 2)
        source = f"# {words}{opening}\n# [tool.probe]\n# ///\nvalue = 1\n"
        with u.Tests.raises(ValueError, match="structured comment block"):
            u.Infra.wrap_long_lines(source, (1,), limit=cls.LIMIT)


class TestsFlextInfraWrapTrailingComment:
    """A trailing comment moves to its own line when the code part fits."""

    LIMIT: Final[int] = u.Infra.native_tool_setting(
        config.Infra.tooling, "ruff", "line-length", int
    )

    @classmethod
    def test_moves_a_trailing_comment_above_its_code(cls) -> None:
        """The code keeps its bytes and the comment keeps its text."""
        comment = "# " + "palavra " * cls.LIMIT
        line = f"tm.that(len(meses), eq=2)  {comment}\n"
        repaired = u.Infra.wrap_long_lines(line, (1,), limit=cls.LIMIT)
        tm.that(repaired, eq=f"{comment}\ntm.that(len(meses), eq=2)\n")

    @classmethod
    def test_keeps_a_line_binding_directive_in_place(cls) -> None:
        """``type:`` and similar directives keep their line association."""
        line = f"tm.that(value, eq=1)  # type: ignore[{'x' * cls.LIMIT}]\n"
        tm.that(u.Infra.wrap_long_lines(line, (1,), limit=cls.LIMIT), eq=line)


__all__: list[str] = [
    "TestsFlextInfraWrapStructuredBlocks",
    "TestsFlextInfraWrapTrailingComment",
]
