"""CLI contract tests for the centralized validate CLI group."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import main as infra_main


class TestValidateCli:
    """Exercise the public validate CLI entrypoints."""

    def test_stub_validate_accepts_all_flag(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        tm.that(
            infra_main([
                "validate",
                "stub-validate",
                "--workspace",
                str(workspace),
                "--all",
            ]),
            eq=0,
        )

    def test_stub_validate_help_returns_zero(self) -> None:
        tm.that(infra_main(["validate", "stub-validate", "--help"]), eq=0)
