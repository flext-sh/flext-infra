"""Behavior tests for the canonical ``flext-infra deps`` CLI group."""

from __future__ import annotations

from flext_tests import tm

from flext_infra import FlextInfraCliDeps, main as infra_main


class TestDepsGroupEntry:
    @staticmethod
    def subcommands() -> list[str]:
        return ["detect", "extra-paths", "internal-sync", "modernize", "path-sync"]

    def test_subcommand_help_is_available(self) -> None:
        for subcommand in self.subcommands():
            tm.that(infra_main(["deps", subcommand, "--help"]), eq=0)

    def test_group_help_is_available(self) -> None:
        tm.that(FlextInfraCliDeps.run(["--help"]), eq=0)

    def test_group_without_subcommand_returns_usage_error(self) -> None:
        tm.that(FlextInfraCliDeps.run([]), eq=1)

    def test_unknown_subcommand_returns_usage_error(self) -> None:
        tm.that(FlextInfraCliDeps.run(["unknown"]), eq=2)
