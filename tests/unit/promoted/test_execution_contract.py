"""Promoted commands execute their declared operation through the public API."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import m
from flext_infra.promoted.dispatcher import dispatch
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

    class TestsFlextInfraPromotedDispatchAlwaysExecutes:
        """Exercise dispatch()'s execution and verb-help routing through real commands."""

        @staticmethod
        def _write_registry(
            tmp_path: Path, what: str
        ) -> t.Pair[p.Infra.Promoted.Registry, Path]:
            (tmp_path / c.Infra.PYPROJECT_FILENAME).write_text(
                "[project]\nname = 'probe'\n", encoding="utf-8"
            )
            command_path = tmp_path / c.Infra.DIR_SCRIPTS / "probe" / f"{what}.py"
            command_path.parent.mkdir(parents=True)
            marker = tmp_path / "EXECUTED"
            command_path.write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('1')\n",
                encoding="utf-8",
            )
            registry = Registry()
            registry.add(u.Tests.promoted_command(path=command_path))
            return registry, marker

        @staticmethod
        def _write_discoverable_command(tmp_path: Path) -> Path:
            """Write one header-bearing command discoverable by the dispatcher."""
            (tmp_path / c.Infra.PYPROJECT_FILENAME).write_text(
                "[project]\nname = 'probe'\n", encoding="utf-8"
            )
            command_path = (
                tmp_path
                / c.Infra.DIR_SCRIPTS
                / "probe"
                / f"{c.Infra.PromotedSelector.ALL}.py"
            )
            command_path.parent.mkdir(parents=True)
            marker = tmp_path / "EXECUTED"
            header = "\n".join(
                f"# {key} = {value}"
                for key, value in (
                    ("verb", "'probe'"),
                    ("what", f"'{c.Infra.PromotedSelector.ALL}'"),
                    ("domain", "'probe'"),
                    ("summary", "'Probe command'"),
                    ("description", "'Writes one marker file when executed.'"),
                    ("example", "'make probe'"),
                    ("mutates", "true"),
                )
            )
            command_path.write_text(
                f"# {c.Infra.PromotedHeader.START}\n"
                f"{header}\n"
                f"# {c.Infra.PromotedHeader.END}\n"
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('1')\n",
                encoding="utf-8",
            )
            return marker

        @pytest.mark.parametrize("ambient_value", [None, "arbitrary"])
        def test_dispatch_executes_declared_operation(
            self, tmp_path: Path, ambient_value: str | None
        ) -> None:
            """Unrelated ambient input never changes the declared operation."""
            registry, marker = self._write_registry(
                tmp_path, c.Infra.PromotedSelector.ALL
            )
            environment = (
                {} if ambient_value is None else {"UNDECLARED_INPUT": ambient_value}
            )
            with tm.scope(
                env=environment, remove_env_keys=("HELP", "OPTIONS", "UNDECLARED_INPUT")
            ):
                exit_code = FlextInfraPromoted.dispatch(
                    registry, "probe", c.Infra.PromotedSelector.ALL
                )
            tm.that(exit_code, eq=0)
            tm.that(marker.exists(), eq=True)

        @pytest.mark.parametrize("ambient_value", [None, "arbitrary"])
        def test_dispatch_executes_settings_declared_operation(
            self, tmp_path: Path, ambient_value: str | None
        ) -> None:
            """WHAT declared through the live settings singleton reaches dispatch."""
            marker = self._write_discoverable_command(tmp_path)
            settings_cls = type(settings)
            settings_cls.update_global(Infra={"WHAT": c.Infra.PromotedSelector.ALL})
            try:
                environment = (
                    {} if ambient_value is None else {"UNDECLARED_INPUT": ambient_value}
                )
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
