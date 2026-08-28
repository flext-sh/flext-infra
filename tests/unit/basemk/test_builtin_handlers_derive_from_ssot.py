"""Every builtin handler the dispatcher routes to is declared exactly once.

``_BUILTIN_HANDLERS`` is the list the generated Makefile scans to decide whether
a verb is served in-process or shelled out to the dispatch script. It was
hand-written beside ``make.verbs``, so the two lists were free to drift: a verb
could be declared in the SSOT, render a recipe that calls ``_builtin_<verb>_*``,
and still be missing from the routing list.

That drift is not hypothetical. ``setup`` is declared in ``make.verbs`` and its
recipe calls ``_builtin_setup_environment``, but that handler was absent from
``_BUILTIN_HANDLERS``, so consumers regenerated from this template had no
working ``make setup``.

These tests pin the invariant: no handler the template defines may be missing
from the routing list, and no routed handler may be undefined.
"""

from __future__ import annotations

import re
from pathlib import Path

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
    """Return every handler the dispatcher can route to.

    Routing moved from the literal ``_BUILTIN_HANDLERS`` list to per-verb
    ``_ALLOWED_WHATS_<verb>``, which the dispatcher validates the selector
    against before building the ``_builtin_<verb>_<what>`` target name.
    """
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


def test_every_direct_private_invocation_is_defined() -> None:
    """Every literal private helper invoked through recursive Make exists.

    Direct helpers such as ``_builtin_setup_lifecycle`` are deliberately not a
    public ``WHAT``. Public route coverage is proven separately from the SSOT.
    """
    missing = sorted(_invoked_handlers() - _defined_handlers())

    assert not missing, f"invoked but never defined: {missing}"


def test_every_routed_handler_is_defined() -> None:
    """The routing list never names a handler that does not exist."""
    routed = {name for name in _routed_handlers() if not name.endswith("_")}
    missing = sorted(routed - _defined_handlers())

    assert not missing, f"routed but never defined: {missing}"


def test_routing_declares_one_allowed_whats_per_verb() -> None:
    """Each verb owns exactly one ``_ALLOWED_WHATS_`` assignment.

    Routing no longer uses a continuation-joined list; the dispatcher validates
    the selector against the per-verb variable before naming the target. A verb
    missing its assignment makes every WHAT fail as unsupported, and a verb
    declared twice silently keeps only the last set of selectors.
    """
    assignments = re.findall(
        r"^_ALLOWED_WHATS_([a-z_]+) :=", _template_text(), re.MULTILINE
    )
    templated = re.findall(r"_ALLOWED_WHATS_\{\{ verb\.name \}\}", _template_text())

    assert templated, "routing must be generated from the verb catalogue"
    assert len(assignments) == len(set(assignments)), assignments
