"""Behavior tests for the canonical ``flext-infra deps`` CLI group."""

from __future__ import annotations

from flext_tests import tm

from flext_infra import main as infra_main


class TestsFlextInfraDepsMainDispatch:
    def test_subcommand_help_is_available(self) -> None:
        # NOTE (multi-agent, mro-wkii.17.9): deps exposes no conformance alias;
        # pyproject normalization is consumed only by the codegen owner.
        for subcommand in ("detect", "extra-paths", "internal-sync", "modernize"):
            tm.that(infra_main(["deps", subcommand, "--help"]), eq=0)
