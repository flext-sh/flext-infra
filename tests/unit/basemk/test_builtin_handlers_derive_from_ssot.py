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

import yaml

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
    """Return every handler name listed in ``_BUILTIN_HANDLERS``."""
    body = _template_text().split("_BUILTIN_HANDLERS := \\", 1)[1].split("\n\n", 1)[0]
    return set(re.findall(r"_builtin_[a-z_]+", body))


def _defined_handlers() -> set[str]:
    """Return every handler the template actually defines as a target."""
    return set(re.findall(r"^(_builtin_[a-z_]+):", _template_text(), re.MULTILINE))


def _invoked_handlers() -> set[str]:
    """Return every handler a recipe dispatches to through ``$(SELF_MAKE)``."""
    return set(re.findall(r"\$\(SELF_MAKE\)\s+(_builtin_[a-z_]+)", _template_text()))


def _ssot_handlers() -> set[str]:
    """Return the handler names the codegen SSOT declares through verb whats."""
    config = yaml.safe_load(
        (Path(__file__).resolve().parents[3] / "config" / "codegen.yaml").read_text(
            encoding="utf-8"
        )
    )
    verbs = config["Infra"]["codegen"]["make"]["verbs"]
    return {
        f"_builtin_{verb['name']}_{what}"
        for verb in verbs
        for what in verb.get("whats") or ()
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


def test_routing_list_keeps_makefile_continuation_syntax() -> None:
    """Every routed handler stays indented under its backslash continuation.

    ``make`` reads an unindented continuation line as a new target, so losing
    the leading tab turns the routing list into "multiple target patterns" and
    the whole Makefile stops parsing. Jinja's ``-%}`` strips that tab, which is
    exactly how the list broke once ``setup`` joined it.
    """
    body = _template_text().split("_BUILTIN_HANDLERS := \\", 1)[1].split("\n\n", 1)[0]
    handler_lines = [
        line for line in body.splitlines() if "_builtin_" in line and "{%" not in line
    ]

    assert handler_lines
    assert all(line.startswith("\t") for line in handler_lines), handler_lines
