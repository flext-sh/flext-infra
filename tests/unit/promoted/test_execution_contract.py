"""Promoted commands execute their declared operation through the public API."""

from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_infra.promoted.invocation import validate_command_contract
from tests import u


class TestsFlextInfraPromotedExecutionContract:
    """Promoted contracts always execute without an effect selector."""

    class TestsFlextInfraPromotedAlwaysExecutes:
        """Validate commands with and without declared domain parameters."""

        def test_command_contract_accepts_mutating_command_without_parameters(
            self, tmp_path: Path
        ) -> None:
            """A mutating command can declare an operation without parameters."""
            command = u.Tests.promoted_command(
                path=tmp_path / "scripts" / "probe" / "all.py"
            )
            u.Infra.promoted_validate_command_contract(command)

        def test_command_contract_accepts_declared_domain_parameter(
            self, tmp_path: Path
        ) -> None:
            """A domain parameter remains part of the command's input contract."""
            param = m.Infra.Promoted.Param(
                name="TARGET", help="Destination", choices=("alpha", "beta")
            )
            command = u.Tests.promoted_command(
                path=tmp_path / "scripts" / "probe" / "all.py", params=(param,)
            )
            u.Infra.promoted_validate_command_contract(command)


__all__: list[str] = ["TestsFlextInfraPromotedExecutionContract"]
