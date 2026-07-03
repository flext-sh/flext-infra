"""Tests for catalog-driven enforcement fixer orchestration."""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import ClassVar, override

import pytest

from flext_core import FlextUtilitiesEnforcement, r
from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra import m, p, t, u
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.gate_fixer import FlextInfraGateFixerAdapter
from flext_infra.fixers.orchestrator import (
    FlextInfraEnforcementFixerOrchestrator,
)
from flext_infra.fixers.result import FlextInfraFixersResult as fr


class TestsEnforcementFixerOrchestrator:
    """Root-cause guardrails for fixer collection and routing."""

    @staticmethod
    def _rule(rule_id: str) -> me.EnforcementRuleSpec:
        catalog = FlextUtilitiesEnforcement.build_canonical_catalog()
        return next(rule for rule in catalog.enabled_rules() if rule.id == rule_id)

    @staticmethod
    def _orchestrator(workspace: Path) -> FlextInfraEnforcementFixerOrchestrator:
        return FlextInfraEnforcementFixerOrchestrator(
            workspace=workspace,
            selected_projects=("demo",),
        )

    def test_validator_import_failure_is_failed_fix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Validator import failure is not reported as an empty violation set."""
        original_import = importlib.import_module

        def fake_import(name: str, package: str | None = None) -> ModuleType:
            if name == "flext_tests.validator":
                msg = "validator unavailable"
                raise ImportError(msg)
            return original_import(name, package)

        monkeypatch.setattr(importlib, "import_module", fake_import)
        project_dir = tmp_path / "demo"
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_tests_validator_violations(
            project_dir,
            self._rule("ENFORCE-016"),
        )

        assert violations == []
        assert len(failures) == 1
        assert "unable to import flext_tests.validator" in failures[0].error

    def test_python_file_enumeration_failure_is_failed_fix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Project file enumeration failure is not hidden as zero work."""

        def fake_iter_python_files(
            *,
            workspace_root: Path,
            project_roots: t.SequenceOf[Path],
            include_tests: bool,
            include_examples: bool,
            include_scripts: bool,
            include_dynamic_dirs: bool,
        ) -> p.Result[t.SequenceOf[Path]]:
            _ = (
                workspace_root,
                project_roots,
                include_tests,
                include_examples,
                include_scripts,
                include_dynamic_dirs,
            )
            return r[t.SequenceOf[Path]].fail("enumeration failed")

        monkeypatch.setattr(
            u.Infra,
            "iter_python_files",
            staticmethod(fake_iter_python_files),
        )
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_python_file_violations(
            tmp_path / "demo",
            self._rule("ENFORCE-045"),
        )

        assert violations == []
        assert len(failures) == 1
        assert failures[0].error == "enumeration failed"

    def test_beartype_rules_collect_real_python_file_probes(
        self,
        tmp_path: Path,
    ) -> None:
        """Beartype-backed deterministic fixers receive concrete file probes."""
        project_dir = tmp_path / "demo"
        source_file = project_dir / "src" / "demo" / "sample.py"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("from __future__ import annotations\n", encoding="utf-8")
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_violations(
            project_dir,
            (self._rule("ENFORCE-045"),),
        )

        assert failures == []
        assert any(
            getattr(probe, "file_path", "") == str(source_file)
            for _rule, probe in violations
        )

    def test_code_smell_gate_collects_project_probe(self, tmp_path: Path) -> None:
        """Gate-backed smell fixes get an explicit project-level probe."""
        project_dir = tmp_path / "demo"
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_violations(
            project_dir,
            (self._rule("ENFORCE-074"),),
        )

        assert failures == []
        assert len(violations) == 1
        assert getattr(violations[0][1], "file_path", "") == str(project_dir)

    def test_missing_selected_project_fails_resolution(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A typoed project filter is a hard failure, not a zero-project success."""
        demo = m.Infra.ProjectInfo(name="demo", path=tmp_path / "demo", stack="python")

        def fake_projects(
            workspace_root: Path,
        ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
            _ = workspace_root
            return r[t.SequenceOf[p.Infra.ProjectInfo]].ok((demo,))

        monkeypatch.setattr(u.Infra, "projects", staticmethod(fake_projects))
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace=tmp_path,
            selected_projects=("missing",),
        )

        result = orchestrator._resolve_projects()

        assert result.failure
        assert "missing" in (result.error or "")

    def test_explicit_unsafe_rule_fails_under_safe_only(self) -> None:
        """Explicit unsafe fix requests must fail instead of becoming no-op success."""
        catalog = FlextUtilitiesEnforcement.build_canonical_catalog()
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace=Path("/tmp"),
            selected_projects=("demo",),
            rules=("ENFORCE-067",),
            safe_only=True,
        )

        with pytest.raises(ValueError, match="unsafe under --safe-only"):
            orchestrator._selected_rules(catalog)

    def test_unhandled_fix_action_fails_project(self, tmp_path: Path) -> None:
        """Adapterless selected rules are explicit failures, not dropped work."""
        project_dir = tmp_path / "demo"
        project = m.Infra.ProjectInfo(name="demo", path=project_dir, stack="python")
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace=tmp_path,
            selected_projects=("demo",),
            safe_only=False,
        )

        results = orchestrator._fix_project(project, (self._rule("ENFORCE-069"),))

        assert len(results) == 1
        assert len(results[0].failed) == 1
        assert "no registered fixer adapter" in results[0].failed[0].error

    def test_adapter_exception_is_failed_fix(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Adapter exceptions are structured failures, never orchestrator crashes."""

        class ExplodingAdapter(FlextInfraFixerAdapter):
            kind: ClassVar[str] = "transformer"

            @override
            def can_fix(self, fix_action: me.EnforcementFixAction) -> bool:
                return fix_action.kind == self.kind

            @override
            def fix_project(
                self,
                project_dir: Path,
                violations: t.SequenceOf[
                    tuple[me.EnforcementRuleSpec, p.AttributeProbe]
                ],
                ctx: m.Infra.FixEnforcementCommand,
            ) -> fr.ProjectFixResult:
                _ = project_dir, violations, ctx
                msg = "adapter exploded"
                raise RuntimeError(msg)

        monkeypatch.setattr(
            FlextInfraEnforcementFixerOrchestrator,
            "_ADAPTER_CLASSES",
            (ExplodingAdapter,),
        )
        project_dir = tmp_path / "demo"
        source_file = project_dir / "src" / "demo" / "sample.py"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("from __future__ import annotations\n", encoding="utf-8")
        project = m.Infra.ProjectInfo(name="demo", path=project_dir, stack="python")
        orchestrator = self._orchestrator(tmp_path)
        monkeypatch.setattr(
            orchestrator,
            "_collect_violations",
            lambda project_dir, rules: (
                [(rules[0], SimpleNamespace(file_path=str(source_file)))],
                [],
            ),
        )

        results = orchestrator._fix_project(project, (self._rule("ENFORCE-008"),))

        assert len(results) == 1
        assert len(results[0].failed) == 1
        assert "adapter exploded" in results[0].failed[0].error

    def test_gate_dry_run_uses_non_mutating_fix_preview(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Gate dry-run uses the non-mutating fix preview path."""

        class FakeGate:
            can_fix: ClassVar[bool] = True
            checked: ClassVar[bool] = False
            previewed: ClassVar[bool] = False

            def __init__(self, workspace_root: Path) -> None:
                self.workspace_root = workspace_root

            def check(
                self,
                project_dir: Path,
                ctx: m.Infra.GateContext,
            ) -> m.Infra.GateExecution:
                _ = self.workspace_root, ctx
                msg = "dry-run must not execute gate checks"
                raise AssertionError(msg)

            def fix(
                self,
                project_dir: Path,
                ctx: m.Infra.GateContext,
            ) -> m.Infra.GateExecution:
                assert ctx.check_only is True
                assert ctx.apply_fixes is False
                FakeGate.previewed = True
                return m.Infra.GateExecution(
                    result=m.Infra.GateResult(
                        gate="smells",
                        project=project_dir.name,
                        passed=True,
                    ),
                    issues=(),
                    raw_output="preview only",
                )

        class FakeRegistry:
            def get(self, target: str) -> type[FakeGate] | None:
                return FakeGate if target == "smells" else None

        def fake_registry(self: FlextInfraGateFixerAdapter) -> FakeRegistry:
            _ = self
            return FakeRegistry()

        monkeypatch.setattr(FlextInfraGateFixerAdapter, "_registry", fake_registry)
        adapter = FlextInfraGateFixerAdapter(tmp_path)
        project_dir = tmp_path / "demo"

        result = adapter.fix_project(
            project_dir,
            ((self._rule("ENFORCE-074"), SimpleNamespace(file_path=str(project_dir))),),
            m.Infra.FixEnforcementCommand(
                workspace=str(tmp_path),
                projects=("demo",),
                apply=False,
            ),
        )

        assert FakeGate.checked is False
        assert FakeGate.previewed is True
        assert len(result.previewed) == 1
        assert result.failed == ()

    def test_command_ctx_forces_check_after_false_in_dry_run(self) -> None:
        """Dry-run must not request post-fix checks that could rewrite files."""
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace=Path("/tmp"),
            selected_projects=("demo",),
            apply=False,
            check_after=True,
        )

        ctx = orchestrator._command_ctx()

        assert ctx.apply is False
        assert ctx.check_after is False

    def test_command_ctx_preserves_check_after_when_applying(self) -> None:
        """Apply mode may still request post-fix checks."""
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace=Path("/tmp"),
            selected_projects=("demo",),
            apply=True,
            check_after=True,
        )

        ctx = orchestrator._command_ctx()

        assert ctx.apply is True
        assert ctx.check_after is True

    def test_fix_enforcement_dry_run_leaves_worktree_unchanged(self) -> None:
        """Running fix-enforcement in dry-run must not modify the worktree.

        This is a real-process guard: it executes the CLI against the
        flext-infra project and asserts ``git status --short`` is identical
        before and after the run.
        """
        project_dir = Path(__file__).parents[3]
        workspace_root = project_dir.parent

        def git_status() -> str:
            result = subprocess.run(
                ["git", "-C", str(project_dir), "status", "--short"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout

        pre_status = git_status()
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "flext_infra",
                "check",
                "fix-enforcement",
                "--workspace",
                str(workspace_root),
                "--projects",
                project_dir.name,
                "--rules",
                "ENFORCE-079",
                "--no-check-after",
            ],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            check=False,
        )
        post_status = git_status()
        assert result.returncode == 0, (
            f"dry-run failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert pre_status == post_status, (
            f"dry-run mutated the worktree\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}\n"
            f"exit: {result.returncode}"
        )
