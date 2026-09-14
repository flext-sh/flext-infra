"""Promoted-command always-executes contract tests.

S1 (2026-09-14): mutation is unconditional for every promoted command; there
is no ``APPLY``/check/dry-run selector anywhere in the promoted framework.
``dispatch()`` always runs the selected command, and an ambient ``APPLY``
value of any kind — including the legacy ``APPLY=N`` — is inert: it is never
read by the promoted framework and never changes execution. These tests
exercise the public ``flext_infra.promoted`` surface directly, with no mocks
or patched internals: real ``Command``/``Param`` models, a real ``Registry``,
and a real child process for the dispatch-level cases.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import m
from flext_infra.promoted.dispatcher import dispatch
from flext_infra.promoted.invocation import validate_command_contract
from flext_infra.promoted.registry import Registry
from tests import u


class TestsFlextInfraPromotedApplyContract:
    """Promoted contracts always execute without an effect selector."""

    class TestsFlextInfraPromotedAlwaysExecutes:
        """Validate the static header contract carries no APPLY special-casing."""

        def test_command_contract_accepts_mutating_command_without_apply(
            self, tmp_path: Path
        ) -> None:
            """A mutating command declaring no APPLY parameter is a valid contract."""
            command = u.Tests.promoted_command(path=tmp_path / "scripts" / "probe" / "all.py")
            validate_command_contract(command)

        def test_command_contract_accepts_mutating_command_with_apply(
            self, tmp_path: Path
        ) -> None:
            """A mutating command that still declares an APPLY parameter is equally valid.

            The promoted framework no longer special-cases the name ``APPLY``: a
            declared parameter by that name is an ordinary parameter, not a
            check-mode selector.
            """
            param = m.Infra.Promoted.Param(name="APPLY", help="ignored", choices=("N", "Y"))
            command = u.Tests.promoted_command(
                path=tmp_path / "scripts" / "probe" / "all.py", params=(param,)
            )
            validate_command_contract(command)

    class TestsFlextInfraPromotedDispatchAlwaysExecutes:
        """Exercise dispatch()'s unconditional execution through a real command."""

        @staticmethod
        def _write_registry(tmp_path: Path) -> tuple[Registry, Path]:
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

        def test_dispatch_executes_with_no_ambient_apply(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
        ) -> None:
            """No ambient APPLY: the mutating command executes."""
            registry, marker = self._write_registry(tmp_path)
            monkeypatch.setenv("WHAT", "all")
            monkeypatch.delenv("APPLY", raising=False)
            monkeypatch.delenv("HELP", raising=False)
            monkeypatch.delenv("OPTIONS", raising=False)
            exit_code = dispatch(registry, "probe")
            assert exit_code == 0
            assert marker.exists()

        def test_dispatch_executes_even_with_apply_n_set(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
        ) -> None:
            """APPLY=N in the environment is ignored: the command still executes.

            There is no check/dry-run mode left in the promoted framework, so a
            caller-set APPLY value never suppresses mutation.
            """
            registry, marker = self._write_registry(tmp_path)
            monkeypatch.setenv("WHAT", "all")
            monkeypatch.setenv("APPLY", "N")
            monkeypatch.delenv("HELP", raising=False)
            monkeypatch.delenv("OPTIONS", raising=False)
            exit_code = dispatch(registry, "probe")
            assert exit_code == 0
            assert marker.exists()


__all__: list[str] = ["TestsFlextInfraPromotedApplyContract"]
