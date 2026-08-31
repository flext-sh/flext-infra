"""Public direnv gate behavior: static contracts plus activation smoke."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.gates.direnv import FlextInfraDirenvGate
from flext_infra.workspace.environment_contracts import envrc_contract_violations
from flext_tests import tm
from tests import TestsFlextInfraUtilities as u

if TYPE_CHECKING:
    from pathlib import Path


def make_ctx(root: Path) -> m.Infra.GateContext:
    """Build the minimal typed gate context for one workspace."""
    return m.Infra.GateContext(workspace=root, reports_dir=root)


class TestsDirenvContractLint:
    """Pure-lint contracts for managed environment files."""

    def test_unguarded_direnv_dir_reads_fail(self, tmp_path: Path) -> None:
        """strict_env does not export DIRENV_DIR; unguarded reads violate."""
        violations = envrc_contract_violations(
            'checkout_root="${DIRENV_DIR#-}"\n'
            'other="${DIRENV_DIR}"\n'
            "bare=$DIRENV_DIR\n",
            root=tmp_path,
        )
        tm.that(len(violations), eq=3)

    def test_guarded_direnv_dir_reads_pass(self, tmp_path: Path) -> None:
        """Guarded reads keep working under strict_env."""
        violations = envrc_contract_violations(
            'fallback="${DIRENV_DIR:-missing}"\noptional="${DIRENV_DIR-}"\n',
            root=tmp_path,
        )
        tm.that(violations, eq=())

    def test_missing_literal_target_fails(self, tmp_path: Path) -> None:
        """Literal source_env and watch_file targets must exist."""
        (tmp_path / "present.envrc").write_text("export OK=1\n", encoding="utf-8")
        violations = envrc_contract_violations(
            'source_env "present.envrc"\nwatch_file "absent.envrc"\n', root=tmp_path
        )
        tm.that(len(violations), eq=1)
        tm.that("absent.envrc" in violations[0], eq=True)

    def test_dynamic_targets_are_skipped(self, tmp_path: Path) -> None:
        """Runtime-derived targets cannot be validated statically."""
        violations = envrc_contract_violations(
            'watch_file "$some_var/relstate.json"\n', root=tmp_path
        )
        tm.that(violations, eq=())

    def test_home_targets_validated_only_when_resolving(self, tmp_path: Path) -> None:
        """resolve_home=False skips $HOME targets (generation-time lint)."""
        violations = envrc_contract_violations(
            'source_env "$HOME/.config/environment.d/projects/absent.envrc"\n',
            root=tmp_path,
            resolve_home=False,
        )
        tm.that(violations, eq=())


class TestsDirenvGate:
    """Fail-closed gate behavior over the two enforcement stages."""

    def test_workspace_without_envrc_skips(self, tmp_path: Path) -> None:
        """No .envrc means nothing to enforce."""
        gate = FlextInfraDirenvGate(tmp_path)
        execution = gate.check(tmp_path, make_ctx(tmp_path))
        tm.that(execution.result.passed, eq=True)

    def test_contract_violation_fails_before_smoke(self, tmp_path: Path) -> None:
        """The static lint fires without consuming any runner command."""
        _ = (tmp_path / c.Infra.ENVRC_FILENAME).write_text(
            'checkout_root="${DIRENV_DIR#-}"\n', encoding="utf-8"
        )
        sentinel = "SENTINEL_SMOKE_RAN"
        gate = FlextInfraDirenvGate(
            tmp_path, runner=u.Tests.command_runner(returncode=99, stderr=sentinel)
        )
        execution = gate.check(tmp_path, make_ctx(tmp_path))
        tm.that(execution.result.passed, eq=False)
        tm.that(
            any("DIRENV_CONTRACT" in error for error in execution.result.errors),
            eq=True,
        )
        tm.that(any(sentinel in error for error in execution.result.errors), eq=False)

    def test_activation_smoke_passes(self, tmp_path: Path) -> None:
        """A clean envrc passes through a zero-exit direnv exec."""
        _ = (tmp_path / c.Infra.ENVRC_FILENAME).write_text(
            "export OK=1\n", encoding="utf-8"
        )
        gate = FlextInfraDirenvGate(
            tmp_path, runner=u.Tests.command_runner(stdout="direnv: loading\n")
        )
        execution = gate.check(tmp_path, make_ctx(tmp_path))
        tm.that(execution.result.passed, eq=True)

    def test_activation_smoke_fails_loud(self, tmp_path: Path) -> None:
        """A failing activation fails the gate with the direnv error."""
        _ = (tmp_path / c.Infra.ENVRC_FILENAME).write_text(
            "export OK=1\n", encoding="utf-8"
        )
        gate = FlextInfraDirenvGate(
            tmp_path,
            runner=u.Tests.command_runner(
                returncode=1, stderr="direnv: error unbound variable\n"
            ),
        )
        execution = gate.check(tmp_path, make_ctx(tmp_path))
        tm.that(execution.result.passed, eq=False)
        tm.that(
            any("unbound variable" in error for error in execution.result.errors),
            eq=True,
        )
