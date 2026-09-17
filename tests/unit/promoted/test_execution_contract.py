"""Promoted commands execute their declared operation through the public API."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m
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
            settings_module = importlib.import_module("flext_infra._settings")
            base_module = importlib.import_module("flext_infra.promoted.base")
            dispatcher_module = importlib.import_module(
                "flext_infra.promoted.dispatcher"
            )
            # Build a settings instance with the desired WHAT value through the
            # public models namespace (the settings class itself stays private).
            test_settings = settings_module.settings.model_copy(
                update={
                    "Infra": m.FlextInfraSettingsModels.Infra.model_validate(
                        {"WHAT": "all"}
                    )
                }
            )

            original_settings = settings_module.settings
            original_dispatcher_settings = dispatcher_module.settings
            original_base_settings = base_module.settings

            try:
                settings_module.settings = test_settings
                dispatcher_module.settings = test_settings
                base_module.settings = test_settings

                environment = {"WHAT": "all"}
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
                settings_module.settings = original_settings
                dispatcher_module.settings = original_dispatcher_settings
                base_module.settings = original_base_settings


__all__: list[str] = ["TestsFlextInfraPromotedExecutionContract"]
