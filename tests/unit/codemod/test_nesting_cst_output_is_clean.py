"""The class-nesting mover emits source the canonical gates accept."""

from __future__ import annotations

import subprocess
from pathlib import Path

from flext_tests import tm

from flext_infra import u

_SOURCE = '''"""Module with one owner and one member to nest."""

from __future__ import annotations


class SampleOwner:
    """Canonical namespace owner."""


class SampleMember:
    """A member that belongs under the owner.

    The body is indented at module level and must be re-indented when the
    class moves inside the owner, or the docstring reports D207.
    """

    value: int = 1


__all__: list[str] = ["SampleMember", "SampleOwner"]
'''


class TestsFlextInfraNestingCstOutput:
    """A mover whose output fails the fleet's own gates is not a repair.

    The four defects this pins were reproduced verbatim in a committed module
    on a member branch: a blank line carrying the block indent (W293), the
    rebuilt export declaration losing its separation (E305), a docstring left
    at the old indentation (D207), and no formatter pass at publication.
    """

    @staticmethod
    def _nested() -> str:
        """Move the member under the owner through the mover's own entry."""
        from flext_infra._utilities._semantic_cutover.nesting_cst import (
            FlextInfraUtilitiesSemanticCutoverNestingCst as mover,
        )

        return mover._nest_definitions(_SOURCE, {"SampleMember": "SampleOwner"})

    @staticmethod
    def _ruff(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        """Run the canonical linter over one emitted module."""
        return subprocess.run(  # noqa: S603
            ["ruff", *args, str(path)],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )

    def test_emitted_source_carries_no_blank_line_with_indentation(self) -> None:
        """A separator line inside the owner block is empty, never indented."""
        emitted = self._nested()

        indented_blanks = [
            line for line in emitted.splitlines() if line.strip() == "" and line != ""
        ]

        tm.that(indented_blanks, empty=True)

    def test_emitted_export_declaration_keeps_its_separation(self) -> None:
        """The rebuilt declaration stays separated from the preceding block."""
        emitted = self._nested()
        lines = emitted.splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("__all__"))

        tm.that(lines[index - 1].strip(), eq="")
        tm.that(lines[index - 2].strip(), eq="")

    def test_emitted_source_passes_the_canonical_gates(self, tmp_path: Path) -> None:
        """Ruff accepts what the mover writes, format and lint alike."""
        module = tmp_path / "nested_module.py"
        tm.ok(u.Cli.atomic_write_text_file(module, self._nested()))

        formatted = self._ruff(module, "format", "--check")
        linted = self._ruff(
            module, "check", "--isolated", "--select", "W291,W293,E301,E303,E305,D207"
        )

        tm.that(formatted.returncode, eq=0)
        tm.that(linted.returncode, eq=0)


__all__: list[str] = ["TestsFlextInfraNestingCstOutput"]
