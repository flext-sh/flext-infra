"""Public github CLI tests using real workspaces."""

from __future__ import annotations

from flext_infra import main as infra_main
from flext_tests import tm


def test_main_returns_zero_on_help() -> None:
    tm.that(infra_main(["github", "--help"]), eq=0)


def test_main_returns_one_without_subcommand() -> None:
    tm.that(infra_main(["github"]), eq=1)


def test_main_returns_nonzero_on_unknown() -> None:
    tm.that(infra_main(["github", "unknown-command"]), ne=0)
