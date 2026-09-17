"""Promoted commands execute their declared operation through the public API."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m, settings
from flext_infra.promoted.dispatcher import dispatch
from flext_infra.promoted.invocation import validate_command_contract
from flext_infra.promoted.registry import Registry
from tests import t, u


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
            validate_command_contract(command)

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
            validate_command_contract(command)

    class TestsFlextInfraPromotedDispatchAlwaysExecutes:
        """Exercise dispatch()'s unconditional execution through a real command."""

        @staticmethod
        def _write_registry(tmp_path: Path) -> t.Pair[Registry, Path]:
            (tmp_path / "pyproject.toml").write_text(
                "[project]\nname = 'probe'\n", encoding="utf-8"
            )
            command_path = tmp_path / "scripts" / "probe" / "all.py"
            command_path.parent.mkdir(parents=True)
            marker = tmp_path / "EXECUTED"
            command_path.write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('1')\n",
                encoding="utf-8",
            )
            registry = Registry()
            registry.add(u.Tests.promoted_command(path=command_path))
            return registry, marker

        @pytest.mark.parametrize("ambient_value", [None, "arbitrary"])
        def test_dispatch_executes_declared_operation(
            self, tmp_path: Path, ambient_value: str | None
        ) -> None:
            """Unrelated ambient input never changes the declared operation."""
            registry, marker = self._write_registry(tmp_path)
            settings_cls = type(settings)
            settings_cls.update_global(Infra={"WHAT": "all"})
            try:
                environment: dict[str, str] = {}
                if ambient_value is not None:
                    environment["UNDECLARED_INPUT"] = ambient_value
                with tm.scope(
                    env=environment,
                    remove_env_keys=("HELP", "OPTIONS", "UNDECLARED_INPUT"),
                ):
                    exit_code = dispatch(registry, "probe")
                    assert exit_code == 0
                    assert marker.exists()
            finally:
                settings_cls.reset_for_testing()


__all__: list[str] = ["TestsFlextInfraPromotedExecutionContract"]
