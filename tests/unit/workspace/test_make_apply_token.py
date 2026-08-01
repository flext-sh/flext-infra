"""The serialized boundary accepts the apply token the Makefile really sends.

The generated Makefile seeds ``APPLY ?= N`` and forwards it verbatim on every
invocation, so a plain ``make test`` / ``make check`` arrives carrying that
value. Accepting only ``""`` and the write-enable value made that default fail
closed with "APPLY must be Y when set", which broke both verbs for the ordinary
read-only run they exist for.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, p, t
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService


def _variables(apply_token: str) -> p.Result[t.StrMapping]:
    """Resolve the Make variables one read-only invocation would export."""
    service = FlextInfraMakeSerializationService(
        workspace_root=Path.cwd(),
        makefile=Path.cwd() / "Makefile",
        verb="test",
        selector_value="",
        apply_token=apply_token,
    )
    # The resolution is internal to the boundary and has no public reader.
    return service._make_variables(config.Infra.codegen.make)  # ruff: ignore[private-member-access]


def test_seeded_absent_token_reads_as_not_applying() -> None:
    """The value the Makefile seeds by default never trips the guard."""
    resolved = _variables(config.Infra.codegen.make.apply_absent_value)

    assert resolved.success, resolved.error


def test_empty_token_still_reads_as_not_applying() -> None:
    """An unset token keeps meaning the caller enabled nothing."""
    resolved = _variables("")

    assert resolved.success, resolved.error


def test_unknown_token_is_still_rejected() -> None:
    """Widening the absent value never accepts an arbitrary token."""
    resolved = _variables("X")

    assert resolved.failure
    assert config.Infra.codegen.make.apply_value in (resolved.error or "")
