"""R28 (operator decision A, 2026-09-12) promoted-command APPLY contract tests.

Mutation is the default for every promoted command; ``APPLY=N`` selects
check/dry-run mode where the command mutates; any other ``APPLY`` value — in
particular the legacy ``APPLY=Y`` — is a hard, named error. These tests
exercise the public ``flext_infra.promoted`` surface directly, with no mocks
or patched internals: real ``Command``/``Param`` models, a real ``Registry``,
and a real child process for the dispatch-level cases.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import m
from flext_infra.promoted.base import RegistryError
from flext_infra.promoted.dispatcher import dispatch
from flext_infra.promoted.invocation import (
    validate_apply_env,
    validate_command_contract,
)
from flext_infra.promoted.registry import Registry

if TYPE_CHECKING:
    from flext_infra import p


def _command(
    *,
    path: Path,
    mutates: bool = True,
    params: tuple[p.Infra.Promoted.Param, ...] = (),
    verb: str = "probe",
    what: str = "all",
) -> p.Infra.Promoted.Command:
    return m.Infra.Promoted.Command(
        verb=verb,
        what=what,
        domain="probe",
        summary="probe",
        description="probe",
        example=f"make {verb} WHAT={what}",
        path=path,
        mutates=mutates,
        aliases=(),
        params=params,
        rules=(),
    )


class TestsFlextInfraPromotedApplyEnvValidation:
    """Validate the ambient ``APPLY`` value against the R28 contract."""

    def test_absent_apply_selects_mutation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unset APPLY resolves to "" — mutation is the default."""
        monkeypatch.delenv("APPLY", raising=False)
        command = _command(path=tmp_path / "scripts" / "probe" / "all.py")
        assert validate_apply_env(command) == ""

    def test_apply_n_selects_check_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """APPLY=N is the only accepted opt-in to check/dry-run mode."""
        monkeypatch.setenv("APPLY", "N")
        command = _command(path=tmp_path / "scripts" / "probe" / "all.py")
        assert validate_apply_env(command) == "N"

    def test_apply_y_is_a_named_hard_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The legacy APPLY=Y raises, naming the violator and the fix."""
        monkeypatch.setenv("APPLY", "Y")
        command_path = tmp_path / "scripts" / "probe" / "all.py"
        command = _command(path=command_path)
        with pytest.raises(RegistryError) as excinfo:
            validate_apply_env(command)
        message = str(excinfo.value)
        assert "[PROMOTED-APPLY] unsupported APPLY value 'Y'" in message
        assert str(command_path) in message
        assert "APPLY=N" in message

    def test_arbitrary_apply_value_is_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any value outside {"", "N"} is rejected, not only "Y"."""
        monkeypatch.setenv("APPLY", "maybe")
        command = _command(path=tmp_path / "scripts" / "probe" / "all.py")
        with pytest.raises(RegistryError, match=r"unsupported APPLY value 'maybe'"):
            validate_apply_env(command)


class TestsFlextInfraPromotedApplyCommandContract:
    """Validate the static header contract for a declared APPLY parameter."""

    def test_command_may_omit_apply_entirely(self, tmp_path: Path) -> None:
        """A mutating command need not declare APPLY (mutation is default)."""
        command = _command(path=tmp_path / "scripts" / "probe" / "all.py")
        validate_command_contract(command)

    def test_declared_apply_choices_n_only_is_valid(self, tmp_path: Path) -> None:
        """APPLY choices restricted to ("N",) is the only valid declaration."""
        param = m.Infra.Promoted.Param(name="APPLY", help="check mode", choices=("N",))
        command = _command(
            path=tmp_path / "scripts" / "probe" / "all.py", params=(param,)
        )
        validate_command_contract(command)

    def test_declared_apply_choices_containing_y_is_rejected(
        self, tmp_path: Path
    ) -> None:
        """A header declaring APPLY choices with "Y" fails discovery-time validation."""
        param = m.Infra.Promoted.Param(name="APPLY", help="apply", choices=("N", "Y"))
        command_path = tmp_path / "scripts" / "probe" / "all.py"
        command = _command(path=command_path, params=(param,))
        with pytest.raises(RegistryError) as excinfo:
            validate_command_contract(command)
        message = str(excinfo.value)
        assert "[PROMOTED-APPLY]" in message
        assert str(command_path) in message


class TestsFlextInfraPromotedDispatchApplyBehavior:
    """Exercise dispatch()'s mutate/check/error branches through a real command."""

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
        registry.add(_command(path=command_path))
        return registry, marker

    def test_dispatch_mutates_by_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No ambient APPLY: the mutating command actually executes."""
        registry, marker = self._write_registry(tmp_path)
        monkeypatch.setenv("WHAT", "all")
        monkeypatch.delenv("APPLY", raising=False)
        monkeypatch.delenv("HELP", raising=False)
        monkeypatch.delenv("OPTIONS", raising=False)
        exit_code = dispatch(registry, "probe")
        assert exit_code == 0
        assert marker.exists()

    def test_dispatch_check_mode_does_not_execute(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """APPLY=N renders the dry-run report and never runs the command."""
        registry, marker = self._write_registry(tmp_path)
        monkeypatch.setenv("WHAT", "all")
        monkeypatch.setenv("APPLY", "N")
        monkeypatch.delenv("HELP", raising=False)
        monkeypatch.delenv("OPTIONS", raising=False)
        exit_code = dispatch(registry, "probe")
        assert exit_code == 0
        assert not marker.exists()
        assert "DRY-RUN" in capsys.readouterr().out

    def test_dispatch_rejects_legacy_apply_y_before_executing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """APPLY=Y raises the R28 error and never reaches execution."""
        registry, marker = self._write_registry(tmp_path)
        monkeypatch.setenv("WHAT", "all")
        monkeypatch.setenv("APPLY", "Y")
        monkeypatch.delenv("HELP", raising=False)
        monkeypatch.delenv("OPTIONS", raising=False)
        with pytest.raises(RegistryError, match=r"\[PROMOTED-APPLY\]"):
            dispatch(registry, "probe")
        assert not marker.exists()
