"""Builtin Make routing is derived from the typed handler registry."""

from __future__ import annotations

import re
from pathlib import Path

from flext_infra import config

_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
    / "Makefile.j2"
)
_GENERATED_MAKEFILE = Path(__file__).resolve().parents[3] / "Makefile"


def _template_text() -> str:
    """Return the generated-Makefile template source."""
    return _TEMPLATE.read_text(encoding="utf-8")


def _registry_handlers() -> set[str]:
    """Return private targets derived from the typed production SSOT."""
    return {
        f"_builtin_{verb.name}_{handler.target}"
        for verb in config.Infra.codegen.make.verbs
        for handler in verb.handlers.values()
    }


def _defined_handlers() -> set[str]:
    """Return every concrete handler from the generated consumer projection."""
    generated = _GENERATED_MAKEFILE.read_text(encoding="utf-8")
    return set(re.findall(r"^(_builtin_[a-z_]+):", generated, re.MULTILINE))


def _invoked_handlers() -> set[str]:
    """Return every private handler invoked directly by another recipe."""
    return set(re.findall(r"\$\(SELF_MAKE\)\s+(_builtin_[a-z_]+)", _template_text()))


def test_every_invoked_handler_is_declared_in_the_registry() -> None:
    """A recipe never invokes a private target absent from the typed registry."""
    missing = sorted(_invoked_handlers() - _registry_handlers())

    assert not missing, f"invoked but absent from make.verbs handlers: {missing}"


def test_every_registry_handler_is_defined() -> None:
    """Every registry-owned builtin target has a concrete implementation."""
    missing = sorted(_registry_handlers() - _defined_handlers())

    assert not missing, f"registered but never defined: {missing}"


def test_template_renders_handler_and_mutation_maps_from_one_registry() -> None:
    """Routing and APPLY policy consume the same typed handler records."""
    template = _template_text()

    assert "_HANDLER_MAP_{{ verb.name }}" in template
    assert "{{ selector }}:{{ handler.target }}" in template
    assert "_MUTATING_WHATS_{{ verb.name }}" in template
    assert "if handler.mutating" in template
    assert "_ALLOWED_WHATS_" not in template
