"""Contract tests for the ``--what`` phase selector on check/validate groups."""

from __future__ import annotations

from flext_infra.cli import main


class TestsFlextInfraCliWhatSelector:
    """``--what <phase>`` reuses the gate/validator selection machinery."""

    def test_check_what_loc_cap_runs_gate(self) -> None:
        """``check --what loc-cap`` runs the gate (0/1), never a usage error."""
        assert main(["check", "--what", "loc-cap", "--projects", "flext-infra"]) in {
            0,
            1,
        }

    def test_check_what_boundary_runs_gate(self) -> None:
        """``check --what boundary`` maps to the boundary gate selection."""
        assert main(["check", "--what", "boundary", "--projects", "flext-infra"]) in {
            0,
            1,
        }

    def test_check_what_unknown_is_usage_error(self) -> None:
        """An unrecognized gate phase returns ``ScriptExitCode.USAGE`` (2)."""
        assert main(["check", "--what", "bogus"]) == 2

    def test_validate_what_manual_cmd_runs_validator(self) -> None:
        """``validate --what manual-cmd`` selects the manual-command validator."""
        assert main(["validate", "--what", "manual-cmd"]) in {0, 1}

    def test_validate_what_unknown_is_usage_error(self) -> None:
        """An unrecognized validator phase returns ``ScriptExitCode.USAGE`` (2)."""
        assert main(["validate", "--what", "no-such-validator"]) == 2
