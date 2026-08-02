"""Prove generated Make handlers derive from the typed verb registry."""

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


def _template_text() -> str:
    """Return the generated-Makefile template source."""
    return _TEMPLATE.read_text(encoding="utf-8")


def _routed_handlers() -> set[str]:
    """Return handlers derived from each generated selector declaration."""
    return {
        f"_builtin_{verb}_{what}"
        for verb, whats in re.findall(
            r"_ALLOWED_WHATS_([a-z_]+) :=([^\n]*)", _template_text()
        )
        for what in whats.split()
        if not what.startswith("{")
    }


def _defined_handlers() -> set[str]:
    """Return every handler the template actually defines as a target."""
    return set(re.findall(r"^(_builtin_[a-z_]+):", _template_text(), re.MULTILINE))


def _invoked_handlers() -> set[str]:
    """Return every handler a recipe dispatches to through ``$(SELF_MAKE)``."""
    return set(re.findall(r"\$\(SELF_MAKE\)\s+(_builtin_[a-z_]+)", _template_text()))


def _ssot_handlers() -> set[str]:
    """Return the handler names the codegen SSOT declares through verb whats."""
    return {
        f"_builtin_{verb.name}_{what}"
        for verb in config.Infra.codegen.make.verbs
        for what in verb.whats
    }


def test_every_invoked_handler_is_declared_in_the_ssot() -> None:
    """A recipe never calls a handler the SSOT does not declare.

    The routing list is rendered from ``make.verbs[].whats``, so a handler that
    a recipe invokes but the SSOT never declares can never be routed.
    """
    missing = sorted(_invoked_handlers() - _ssot_handlers())

    assert not missing, f"invoked but absent from make.verbs[].whats: {missing}"


def test_every_routed_handler_is_defined() -> None:
    """The routing list never names a handler that does not exist."""
    routed = {name for name in _routed_handlers() if not name.endswith("_")}
    missing = sorted(routed - _defined_handlers())

    assert not missing, f"routed but never defined: {missing}"


def test_routing_declares_one_allowed_whats_per_verb() -> None:
    """Each verb owns exactly one ``_ALLOWED_WHATS_`` assignment.

    The dispatcher validates the selector against the per-verb variable before
    naming the target. A missing or repeated assignment would make routing
    incomplete or ambiguous.
    """
    assignments = re.findall(
        r"^_ALLOWED_WHATS_([a-z_]+) :=", _template_text(), re.MULTILINE
    )
    templated = re.findall(r"_ALLOWED_WHATS_\{\{ verb\.name \}\}", _template_text())

    assert templated, "routing must be generated from the verb catalogue"
    assert len(assignments) == len(set(assignments)), assignments
