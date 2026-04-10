"""Behavior tests for the canonical ``flext-infra deps`` CLI group."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import FlextInfraCliDeps, main as infra_main
from tests import r


class TestDepsGroupEntry:
    @pytest.mark.parametrize(
        "subcommand",
        ["detect", "extra-paths", "internal-sync", "modernize", "path-sync"],
    )
    def test_subcommand_help_is_available(self, subcommand: str) -> None:
        tm.that(infra_main(["deps", subcommand, "--help"]), eq=0)

    def test_group_help_is_available(self) -> None:
        tm.that(FlextInfraCliDeps.run(["--help"]), eq=0)

    def test_group_without_subcommand_returns_usage_error(self) -> None:
        tm.that(FlextInfraCliDeps.run([]), eq=1)

    def test_unknown_subcommand_returns_usage_error(self) -> None:
        tm.that(FlextInfraCliDeps.run(["unknown"]), eq=2)


def test_shared_flags_before_subcommand_are_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []

    def _fake_detect(self: FlextInfraCliDeps, params: object) -> r[bool]:
        del self
        captured.append(params)
        return r[bool].ok(True)

    monkeypatch.setattr(FlextInfraCliDeps, "detect_dependencies", _fake_detect)
    exit_code = infra_main([
        "deps",
        "--workspace",
        ".",
        "--projects",
        "flext-core",
        "detect",
        "--typings",
    ])
    tm.that(exit_code, eq=0)
    params = captured[0]
    tm.that(getattr(params, "project_names"), eq=["flext-core"])
    tm.that(getattr(params, "typings"), eq=True)
