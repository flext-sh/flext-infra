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


def _variables(
    apply_token: str,
    *,
    workspace_root: Path | None = None,
    verb: str = "test",
    selector_value: str = "",
) -> p.Result[t.StrMapping]:
    """Resolve the Make variables one read-only invocation would export."""
    root = workspace_root or Path.cwd()
    service = FlextInfraMakeSerializationService(
        workspace_root=root,
        makefile=root / "Makefile",
        verb=verb,
        selector_value=selector_value,
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


def test_custom_what_from_custom_mk_is_accepted(tmp_path: Path) -> None:
    """Serialized verbs accept `_custom_<verb>_<what>` the same way _dispatch does."""
    (tmp_path / "Makefile").write_text("# test makefile\n", encoding="utf-8")
    custom_body = "_custom_test_unit:" + chr(10) + chr(9) + "@true" + chr(10)
    (tmp_path / "custom.mk").write_text(custom_body, encoding="utf-8")
    resolved = _variables(
        config.Infra.codegen.make.apply_absent_value,
        workspace_root=tmp_path,
        selector_value="unit",
    )
    assert resolved.success, resolved.error
    assert resolved.value[config.Infra.codegen.make.selector] == "unit"


def test_unknown_what_without_custom_target_still_fails(tmp_path: Path) -> None:
    """Invented WHATs without a custom.mk target remain fail-closed."""
    (tmp_path / "Makefile").write_text("# test makefile\n", encoding="utf-8")
    custom_body = "_custom_test_unit:" + chr(10) + chr(9) + "@true" + chr(10)
    (tmp_path / "custom.mk").write_text(custom_body, encoding="utf-8")
    resolved = _variables(
        config.Infra.codegen.make.apply_absent_value,
        workspace_root=tmp_path,
        selector_value="invented",
    )
    assert resolved.failure
    assert "unsupported test" in (resolved.error or "")
