"""Contract tests for the ``--what`` phase selector on check/validate groups."""

from __future__ import annotations

from flext_infra.cli import main
from flext_tests import tm


class TestsFlextInfraCliWhatSelector:
    """``--what <phase>`` reuses the gate/validator selection machinery."""

    def test_check_what_loc_cap_runs_gate(self) -> None:
        """``check --what loc-cap`` runs the gate (0/1), never a usage error."""
        tm.that(
            {0, 1},
            has=main(["check", "--what", "loc-cap", "--projects", "flext-infra"]),
        )

    def test_check_what_boundary_runs_gate(self) -> None:
        """``check --what boundary`` maps to the boundary gate selection."""
        tm.that(
            {0, 1},
            has=main(["check", "--what", "boundary", "--projects", "flext-infra"]),
        )

    def test_check_what_unknown_is_usage_error(self) -> None:
        """An unrecognized gate phase returns ``ScriptExitCode.USAGE`` (2)."""
        tm.that(main(["check", "--what", "bogus"]), eq=2)

    def test_validate_what_manual_cmd_runs_validator(self) -> None:
        """``validate --what manual-cmd`` selects the manual-command validator."""
        tm.that({0, 1}, has=main(["validate", "--what", "manual-cmd"]))

    def test_validate_what_unknown_is_usage_error(self) -> None:
        """An unrecognized validator phase returns ``ScriptExitCode.USAGE`` (2)."""
        tm.that(main(["validate", "--what", "no-such-validator"]), eq=2)
