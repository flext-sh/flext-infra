"""Tests for catalog-driven enforcement fixer orchestration."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, ClassVar, override

import pytest

from flext_cli import cli
from flext_core import FlextUtilitiesEnforcement, r
from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra import m, p, t, u
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.gate_fixer import FlextInfraGateFixerAdapter
from flext_infra.fixers.manual_fixer import FlextInfraManualFixerAdapter
from flext_infra.fixers.orchestrator import FlextInfraEnforcementFixerOrchestrator
from flext_infra.fixers.rope_fixer import FlextInfraRopeFixerAdapter
from tests import c
from flext_tests import tm

if TYPE_CHECKING:
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
            workspace_root=workspace, selected_projects=("demo",)
        )

    def test_validator_import_failure_is_failed_fix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
            project_dir, self._rule("ENFORCE-016")
        )

        tm.that(violations, eq=[])
        tm.that(len(failures), eq=1)
        tm.that(failures[0].error, has="unable to import flext_tests.validator")

    def test_python_file_enumeration_failure_is_failed_fix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
            u.Infra, "iter_python_files", staticmethod(fake_iter_python_files)
        )
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_python_file_violations(
            tmp_path / "demo", self._rule("ENFORCE-045")
        )

        tm.that(violations, eq=[])
        tm.that(len(failures), eq=1)
        tm.that(failures[0].error, eq="enumeration failed")

    def test_beartype_rules_collect_real_python_file_probes(
        self, tmp_path: Path
    ) -> None:
        """Beartype-backed deterministic fixers receive concrete file probes."""
        project_dir = tmp_path / "demo"
        source_file = project_dir / "src" / "demo" / "sample.py"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("from __future__ import annotations\n", encoding="utf-8")
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_violations(
            project_dir, (self._rule("ENFORCE-045"),)
        )

        tm.that(failures, eq=[])
        assert any(
            getattr(probe, "file_path", "") == str(source_file)
            for _rule, probe in violations
        )

    def test_stub_file_rule_collects_pyi_probes(self, tmp_path: Path) -> None:
        """Stub-file enforcement receives concrete ``.pyi`` probes."""
        project_dir = tmp_path / "demo"
        stub_file = project_dir / "src" / "demo" / "__init__.pyi"
        excluded_stub = project_dir / ".venv" / "ignored.pyi"
        stub_file.parent.mkdir(parents=True)
        excluded_stub.parent.mkdir(parents=True)
        stub_file.write_text("from demo import x as x\n", encoding="utf-8")
        excluded_stub.write_text("x: int\n", encoding="utf-8")
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_violations(
            project_dir, (self._rule("ENFORCE-090"),)
        )

        tm.that(failures, eq=[])
        tm.that(
            [Path(str(getattr(probe, "file_path", ""))) for _rule, probe in violations],
            eq=[stub_file.resolve()],
        )

    def test_remove_stub_file_dry_run_does_not_unlink(self, tmp_path: Path) -> None:
        """The remove-stub adapter previews deletion in dry-run."""
        project_dir = tmp_path / "demo"
        stub_file = project_dir / "src" / "demo" / "__init__.pyi"
        stub_file.parent.mkdir(parents=True)
        stub_file.write_text("from demo import x as x\n", encoding="utf-8")
        adapter = FlextInfraRopeFixerAdapter(tmp_path)
        ctx = m.Infra.FixEnforcementCommand(
            workspace=str(tmp_path), projects=("demo",), apply=False
        )

        result = adapter.fix_project(
            project_dir,
            ((self._rule("ENFORCE-090"), SimpleNamespace(file_path=str(stub_file))),),
            ctx,
        )

        assert stub_file.exists()
        tm.that(len(result.previewed), eq=1)
        assert not result.fixed
        assert not result.failed

    def test_remove_stub_file_apply_unlinks_only_stub(self, tmp_path: Path) -> None:
        """The remove-stub adapter deletes the reported ``.pyi`` in apply mode."""
        project_dir = tmp_path / "demo"
        stub_file = project_dir / "src" / "demo" / "__init__.pyi"
        stub_file.parent.mkdir(parents=True)
        stub_file.write_text("from demo import x as x\n", encoding="utf-8")
        adapter = FlextInfraRopeFixerAdapter(tmp_path)
        ctx = m.Infra.FixEnforcementCommand(
            workspace=str(tmp_path), projects=("demo",), apply=True
        )

        result = adapter.fix_project(
            project_dir,
            ((self._rule("ENFORCE-090"), SimpleNamespace(file_path=str(stub_file))),),
            ctx,
        )

        assert not stub_file.exists()
        tm.that(len(result.fixed), eq=1)
        tm.that(result.files_modified, eq=(str(stub_file),))
        assert not result.failed

    def test_manual_fix_dry_run_previews_without_mutation(self, tmp_path: Path) -> None:
        """Manual fix actions produce explicit previews in dry-run."""
        rule = self._rule("ENFORCE-097")
        tm.that(rule.fix_action, none=False)
        adapter = FlextInfraManualFixerAdapter(tmp_path)
        assert adapter.can_fix(rule.fix_action)
        source_file = tmp_path / "demo" / "src" / "demo" / "sample.py"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("VALUE = 42\n", encoding="utf-8")

        result = adapter.fix_project(
            tmp_path / "demo",
            (
                (
                    rule,
                    SimpleNamespace(file_path=str(source_file), line=1, literal="42"),
                ),
            ),
            m.Infra.FixEnforcementCommand(
                workspace=str(tmp_path), projects=("demo",), apply=False
            ),
        )

        tm.that(source_file.read_text(encoding="utf-8"), eq="VALUE = 42\n")
        tm.that(len(result.previewed), eq=1)
        tm.that(result.previewed[0].message, has="magic literal 42")
        tm.that(result.fixed, eq=())
        tm.that(result.failed, eq=())

    def test_manual_fix_apply_fails_loudly(self, tmp_path: Path) -> None:
        """Manual fix actions cannot be reported as applied automatically."""
        rule = self._rule("ENFORCE-097")
        adapter = FlextInfraManualFixerAdapter(tmp_path)

        result = adapter.fix_project(
            tmp_path / "demo",
            (
                (
                    rule,
                    SimpleNamespace(
                        file_path=str(tmp_path / "demo" / "sample.py"),
                        line=7,
                        literal="42",
                    ),
                ),
            ),
            m.Infra.FixEnforcementCommand(
                workspace=str(tmp_path), projects=("demo",), apply=True
            ),
        )

        tm.that(result.previewed, eq=())
        tm.that(len(result.failed), eq=1)
        tm.that(result.failed[0].error, has="manual fix required for ENFORCE-097")

    def test_code_smell_gate_collects_project_probe(self, tmp_path: Path) -> None:
        """Gate-backed smell fixes get an explicit project-level probe."""
        project_dir = tmp_path / "demo"
        orchestrator = self._orchestrator(tmp_path)

        violations, failures = orchestrator._collect_violations(
            project_dir, (self._rule("ENFORCE-074"),)
        )

        tm.that(failures, eq=[])
        tm.that(len(violations), eq=1)
        tm.that(getattr(violations[0][1], "file_path", ""), eq=str(project_dir))

    def test_missing_selected_project_fails_resolution(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
            workspace_root=tmp_path, selected_projects=("missing",)
        )

        result = orchestrator._resolve_projects()

        tm.fail(result)
        tm.that((result.error or ""), has="missing")

    def test_explicit_unsafe_rule_fails_under_safe_only(self) -> None:
        """Explicit unsafe fix requests must fail instead of becoming no-op success."""
        catalog = FlextUtilitiesEnforcement.build_canonical_catalog()
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace_root=Path("/tmp"),
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
            workspace_root=tmp_path, selected_projects=("demo",), safe_only=False
        )
        unsupported_rule = me.EnforcementRuleSpec(
            id="ENFORCE-999",
            description="Unsupported fix action",
            severity=me.EnforcementRuleSeverity.HIGH,
            source=me.EnforcementRuntimeWarningSource(category="UserWarning"),
            fix_action=me.EnforcementFixAction(
                kind="transformer", target="unregistered"
            ),
        )

        results = orchestrator._fix_project(project, (unsupported_rule,))

        tm.that(len(results), eq=1)
        tm.that(len(results[0].failed), eq=1)
        tm.that(results[0].failed[0].error, has="no registered fixer adapter")

    def test_adapter_exception_is_failed_fix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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

        tm.that(len(results), eq=1)
        tm.that(len(results[0].failed), eq=1)
        tm.that(results[0].failed[0].error, has="adapter exploded")

    def test_gate_dry_run_uses_non_mutating_check_preview(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gate dry-run uses the non-mutating check path."""

        class FakeGate:
            can_fix: ClassVar[bool] = True
            checked: ClassVar[bool] = False
            fixed: ClassVar[bool] = False

            def __init__(self, workspace_root: Path) -> None:
                self.workspace_root = workspace_root

            def check(
                self, project_dir: Path, ctx: m.Infra.GateContext
            ) -> m.Infra.GateExecution:
                _ = self.workspace_root
                tm.that(ctx.check_only, eq=True)
                tm.that(ctx.apply_fixes, eq=False)
                FakeGate.checked = True
                return m.Infra.GateExecution(
                    result=m.Infra.GateResult(
                        gate="smells", project=project_dir.name, passed=True
                    ),
                    issues=(
                        m.Infra.Issue(
                            file=str(project_dir / "src" / "demo.py"),
                            line=1,
                            column=1,
                            code="boolean-logic",
                            message="boolean logic",
                            severity="error",
                        ),
                    ),
                    raw_output="check only",
                )

            def fix(
                self, project_dir: Path, ctx: m.Infra.GateContext
            ) -> m.Infra.GateExecution:
                _ = project_dir, ctx
                FakeGate.fixed = True
                msg = "dry-run must not execute gate fixes"
                raise AssertionError(msg)

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
                workspace=str(tmp_path), projects=("demo",), apply=False
            ),
        )

        tm.that(FakeGate.checked, eq=True)
        tm.that(FakeGate.fixed, eq=False)
        tm.that(len(result.previewed), eq=1)
        tm.that(result.failed, eq=())

    def test_command_ctx_forces_check_after_false_in_dry_run(self) -> None:
        """Dry-run must not request post-fix checks that could rewrite files."""
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace_root=Path("/tmp"),
            selected_projects=("demo",),
            apply=False,
            check_after=True,
        )

        ctx = orchestrator._command_ctx()

        tm.that(ctx.apply, eq=False)
        tm.that(ctx.check_after, eq=False)

    def test_command_ctx_preserves_check_after_when_applying(self) -> None:
        """Apply mode may still request post-fix checks."""
        orchestrator = FlextInfraEnforcementFixerOrchestrator(
            workspace_root=Path("/tmp"),
            selected_projects=("demo",),
            apply=True,
            check_after=True,
        )

        ctx = orchestrator._command_ctx()

        tm.that(ctx.apply, eq=True)
        tm.that(ctx.check_after, eq=True)

    def test_fix_enforcement_dry_run_leaves_worktree_unchanged(self) -> None:
        """Running fix-enforcement in dry-run must not modify the worktree.

        This is a real-process guard: it executes the CLI against the
        flext-infra project and asserts ``git status --short`` is identical
        before and after the run.
        """
        project_dir = Path(__file__).parents[3]
        workspace_root = project_dir.parent

        def git_status() -> str:
            capture_result: p.Result[str] = cli.capture(
                [c.Infra.GIT, "-C", str(project_dir), "status", "--short"],
                cwd=workspace_root,
            )
            stdout: str = capture_result.value
            return stdout

        pre_status = git_status()
        result = cli.run_raw(
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
            cwd=workspace_root,
        ).value
        post_status = git_status()
        tm.that(result.exit_code, eq=0)
        tm.that(pre_status, eq=post_status)
