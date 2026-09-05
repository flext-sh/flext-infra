"""Safety-circuit behavior for the batch ast-grep ``mod`` verb."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, main as infra_main, u
from flext_infra.codemod.batch_apply import FlextInfraCodemodBatchApply
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine
from flext_tests import tm

if TYPE_CHECKING:
    import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MAKE_SERIALIZATION_RULE = (
    _PROJECT_ROOT
    / "src"
    / "flext_infra"
    / "codemod"
    / "rules"
    / "automation-infrastructure"
    / "ban-make-serialization.yml"
)


def _git(root: Path, *args: str) -> str:
    result = u.Cli.run_raw(("git", *args), cwd=root)
    tm.that(result.success, eq=True)
    tm.that(result.value.exit_code, eq=0)
    return result.value.stdout.strip()


def _repo(tmp_path: Path, source: str, *, project_name: str = "tmp") -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init")
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "{project_name}"\nversion = "0.0.0"\n', encoding="utf-8"
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


def _rule(root: Path, *, pattern: str, fix: str | None) -> Path:
    rules = root / "ast-grep-rules"
    rules.mkdir(exist_ok=True)
    rule = rules / "mod-fix.yml"
    fix_contract = (
        "fix: |-\n" + "".join(f"  {line}\n" for line in fix.splitlines())
        if fix is not None
        else ""
    )
    rule.write_text(
        f"id: mod-fix\nlanguage: Python\nrule:\n  pattern: {pattern}\n"
        + fix_contract
        + "severity: warning\n",
        encoding="utf-8",
    )
    return rule


class TestsFlextInfraModCircuitApply:
    def test_make_serialization_guard_is_detection_only(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "u.Infra.serialization_lock_execute(paths, timeout)\n")

        detection = tm.ok(
            u.Cli.run_raw(
                [
                    c.Infra.SG,
                    c.Infra.SCAN,
                    "--rule",
                    str(_MAKE_SERIALIZATION_RULE),
                    "--json=stream",
                    ".",
                ],
                cwd=root,
            )
        )

        report = tm.ok(
            FlextInfraModGateEngine.scan(root, (_MAKE_SERIALIZATION_RULE,), fix=False)
        )

        tm.that(detection.exit_code, ne=0)
        tm.that(
            (detection.stdout or "") + (detection.stderr or ""),
            has='"ruleId":"ban-make-serialization"',
        )
        tm.that(report.nodes, eq=0)
        tm.that(report.files, eq=frozenset())

    def test_apply_reports_verified_node_and_file_counts(
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
            repository_root=root, apply_changes=True
        ).execute()

        tm.that(result.success, eq=True)
        tm.that(capsys.readouterr().out, has="applied 1 node(s) across 1 file(s)")
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = {}\n")
        tm.that(_git(root, "rev-parse", "HEAD"), eq=head_before)

    def test_detection_only_rule_blocks_check_and_apply(self, tmp_path: Path) -> None:
        """Detection-only findings stay visible until a semantic fix removes them."""
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix=None)

        check_result = FlextInfraCodemodBatchApply(repository_root=root).execute()
        apply_result = FlextInfraCodemodBatchApply(
            repository_root=root, apply_changes=True
        ).execute()

        tm.that(check_result.failure, eq=True)
        tm.that(
            check_result.error or "", has="1 pending ast-grep finding(s), 0 actionable"
        )
        tm.that(apply_result.failure, eq=True)
        tm.that(
            apply_result.error or "", has="detection-only findings require fix-forward"
        )
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = dict()\n")

    def test_byte_identical_fix_is_not_pending(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = dict()")

        result = FlextInfraCodemodBatchApply(repository_root=root).execute()

        tm.that(result.success, eq=True)

    def test_actionable_fix_remains_pending(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = {}")

        result = FlextInfraCodemodBatchApply(repository_root=root).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="1 pending actionable ast-grep fix")

    def test_discovered_rule_without_id_fails_explicitly(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        rule = _rule(root, pattern="value = dict()", fix="value = {}")
        rule.write_text(
            "language: Python\nrule:\n  pattern: value = dict()\nfix: value = {}\n",
            encoding="utf-8",
        )

        result = FlextInfraCodemodBatchApply(repository_root=root).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="missing required id")

    def test_check_mode_reports_pending_without_mutation(self, tmp_path: Path) -> None:
        root = _repo(tmp_path, "value = dict()\n")
        _rule(root, pattern="value = dict()", fix="value = {}")

        result = FlextInfraCodemodBatchApply(repository_root=root).execute()

        tm.that(result.failure, eq=True)
        tm.that(result.error or "", has="pending actionable ast-grep fix")
        tm.that((root / "sample.py").read_text(encoding="utf-8"), eq="value = dict()\n")


class TestsFlextInfraModCliRoute:
    def test_refactor_mod_check_route(self, tmp_path: Path) -> None:
        project = tm.ok(u.read_project_metadata(_PROJECT_ROOT))
        root = _repo(
            tmp_path,
            "u.Infra.serialization_lock_execute(paths, timeout)\n",
            project_name=project.name,
        )

        exit_code = infra_main(["refactor", "mod", "--workspace", str(root)])

        tm.that(exit_code, ne=0)
        tm.that(
            (root / "sample.py").read_text(encoding="utf-8"),
            eq="u.Infra.serialization_lock_execute(paths, timeout)\n",
        )
