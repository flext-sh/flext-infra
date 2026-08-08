"""Safety-circuit behavior for the batch ast-grep ``mod`` verb."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import main as infra_main
from flext_infra import u
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_infra.codemod.batch_apply import (
    FlextInfraCodemodBatchApply,
    FlextInfraModGateSnapshot,
)
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

_CHECKPOINT_SUBJECT = "chore(git): checkpoint before ast-grep batch apply"


def _snapshot(ruff: int, pyrefly: int) -> FlextInfraModGateSnapshot:
    return FlextInfraModGateSnapshot(ruff_errors=ruff, pyrefly_errors=pyrefly)


def _git(root: Path, *args: str) -> str:
    result = u.Cli.run_raw(("git", *args), cwd=root)
    tm.that(result.success, eq=True)
    tm.that(result.value.exit_code, eq=0)
    return result.value.stdout.strip()


def _repo(tmp_path: Path, source: str) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "tmp"\nversion = "0.0.0"\n', encoding="utf-8"
    )
    (root / "sample.py").write_text(source, encoding="utf-8")
    _git(root, "add", "-A")
    _git(
        root,
        "-c",
        "user.name=Mod Test",
        "-c",
        "user.email=mod@example.com",
        "commit",
        "-m",
        "initial",
    )
    return root


def _rule(root: Path, *, pattern: str, fix: str | None) -> None:
    rules = root / "ast-grep-rules"
    rules.mkdir(exist_ok=True)
    fix_contract = (
        "fix: |-\n" + "".join(f"  {line}\n" for line in fix.splitlines())
        if fix is not None
        else ""
    )
    (rules / "mod-fix.yml").write_text(
        f"id: mod-fix\nlanguage: Python\nrule:\n  pattern: {pattern}\n"
        + fix_contract
        + "severity: warning\n",
        encoding="utf-8",
    )


class TestsFlextInfraModCircuitDecision:
    def test_equal_counts_keep_changes(self) -> None:
        tm.that(
            FlextInfraModGateEngine.circuit_broken(_snapshot(3, 2), _snapshot(3, 2)),
            eq=False,
        )

    def test_decreased_counts_keep_changes(self) -> None:
        tm.that(
            FlextInfraModGateEngine.circuit_broken(_snapshot(3, 2), _snapshot(1, 0)),
            eq=False,
        )

    def test_ruff_increase_breaks_circuit(self) -> None:
        tm.that(
            FlextInfraModGateEngine.circuit_broken(_snapshot(3, 2), _snapshot(4, 2)),
            eq=True,
        )

    def test_pyrefly_increase_breaks_circuit(self) -> None:
        tm.that(
            FlextInfraModGateEngine.circuit_broken(_snapshot(3, 2), _snapshot(3, 3)),
            eq=True,
        )


class TestsFlextInfraModCircuitApply:
    def test_apply_reports_exact_verified_fix_count(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = {}")
        _git(root, "add", "-A")
        _git(
            root,
            "-c",
            "user.name=Mod Test",
            "-c",
            "user.email=mod@example.com",
            "commit",
            "-m",
            "rules",
        )
        head_before = _git(root, "rev-parse", "HEAD")

        result = FlextInfraCodemodBatchApply(
            workspace_root=root, apply_changes=True
        ).execute()

        tm.that(result.success, eq=True)
        tm.that(capsys.readouterr().out, has="mod: applied 1 ast-grep fix(es)")
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = {}\n")
        tm.that(_git(root, "rev-parse", "HEAD"), eq=head_before)

    def test_detection_only_rule_is_not_pending_or_applied(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix=None)

        check_result = FlextInfraCodemodBatchApply(workspace_root=root).execute()
        apply_result = FlextInfraCodemodBatchApply(
            workspace_root=root, apply_changes=True
        ).execute()

        tm.that(check_result.success, eq=True)
        tm.that(apply_result.success, eq=True)
        tm.that(capsys.readouterr().out, has="mod: applied 0 ast-grep fix(es)")
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = dict()\n")

    def test_apply_fails_when_fixable_finding_remains(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = dict()")

        result = FlextInfraCodemodBatchApply(
            workspace_root=root, apply_changes=True
        ).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="remained after apply")

    def test_apply_rolls_back_when_ruff_regresses(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        dirty_source = "value = dict()\n# pending edit\n"
        (root / "sample.py").write_text(dirty_source, encoding="utf-8")
        _rule(root, pattern="value = dict()", fix="import os\nvalue = {}")

        result = FlextInfraCodemodBatchApply(
            workspace_root=root, apply_changes=True
        ).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="rolled back")
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq=dirty_source)
        tm.that(_git(root, "log", "-1", "--format=%s"), eq=_CHECKPOINT_SUBJECT)

    def test_check_mode_reports_pending_without_mutation(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = {}")

        result = FlextInfraCodemodBatchApply(workspace_root=root).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="pending ast-grep fix")
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = dict()\n")


class TestsFlextInfraModCliRoute:
    def test_refactor_mod_check_route(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = {}")

        exit_code = infra_main(["refactor", "mod", "--workspace", str(root)])

        tm.that(exit_code, ne=0)
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = dict()\n")
