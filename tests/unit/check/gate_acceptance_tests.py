"""Native gate acceptance preserves failures, scope and execution evidence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, m, p
from flext_infra.check import FlextInfraGateRegistry, FlextInfraWorkspaceChecker
from flext_infra.gates import (
    FlextInfraMarkdownGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
)
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraGateAcceptance:
    """Observe acceptance through real checker and Ruff public boundaries."""

    @staticmethod
    def test_tooling_contract_rejects_retired_residual_policy() -> None:
        """The live typed owner round-trips without accepting residual exemptions."""
        lint = config.Infra.tooling.tools.ruff.lint
        restored = type(lint).model_validate_json(
            lint.model_dump_json(by_alias=True, exclude_computed_fields=True),
        )
        tm.that(restored.model_dump(), eq=lint.model_dump())
        with pytest.raises(ValueError, match="fix-recipe-residual"):
            type(lint).model_validate_json(
                tm.ok(
                    u.Cli.json_dumps({
                        **lint.model_dump(
                            mode="json",
                            by_alias=True,
                            exclude_computed_fields=True,
                        ),
                        "fix-recipe-residual": [],
                    }),
                ),
            )

    @staticmethod
    def test_tooling_contract_rejects_retired_bandit_catalog() -> None:
        """An owner-specific security exemption cannot return through config."""
        tools = config.Infra.tooling.tools
        payload = tools.model_dump(
            mode="json",
            by_alias=True,
            exclude_computed_fields=True,
        )
        payload["bandit"] = {"authorized-exceptions": []}
        with pytest.raises(m.ValidationError, match="bandit"):
            type(tools).model_validate_json(tm.ok(u.Cli.json_dumps(payload)))

    @staticmethod
    @pytest.mark.parametrize("verdict", [False, True])
    def test_execution_params_round_trip_preserves_independent_verdict(
        tmp_path: Path,
        *,
        verdict: bool,
    ) -> None:
        """The facade model validates and implements the structural boundary."""
        params = m.Infra.GateExecutionParams(
            project_dir=tmp_path,
            verdict=verdict,
            outcome=c.Infra.ToolOutcome.FINDINGS,
            issues=(),
            raw_output="native diagnostic\n",
            started=1.0,
        )
        restored = m.Infra.GateExecutionParams.model_validate_json(
            params.model_dump_json(),
        )
        boundary: p.Infra.GateExecutionParams = restored
        tm.that(restored.model_dump(), eq=params.model_dump())
        tm.that(boundary.verdict, eq=verdict)
        tm.that(boundary.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(boundary.raw_output, eq=params.raw_output)
        tm.that(boundary.project_dir, eq=tmp_path)
        tm.that(boundary.started, eq=params.started)
        tm.that(tuple(boundary.issues), eq=params.issues)

    @staticmethod
    def test_execution_params_rejects_invalid_native_outcome(tmp_path: Path) -> None:
        """An unknown native outcome cannot cross the validated model boundary."""
        with pytest.raises(ValueError, match="outcome"):
            m.Infra.GateExecutionParams.model_validate({
                "project_dir": tmp_path,
                "verdict": True,
                "outcome": "not-a-native-outcome",
                "issues": (),
                "raw_output": "",
                "started": 1.0,
            })

    @staticmethod
    @pytest.mark.parametrize("broken", [False, True])
    def test_generic_fix_preserves_native_clean_or_error(
        tmp_path: Path,
        *,
        broken: bool,
    ) -> None:
        """Real Ruff formatting exercises the shared assembly contract."""
        project = u.Tests.mk_project(tmp_path, "format-contract", with_src=True)
        source = project / "src" / "sample.py"
        source.write_text(
            "def broken(:\n" if broken else "value=1\n",
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project)
        execution = FlextInfraRuffFormatGate(tmp_path).fix(
            project,
            m.Infra.GateContext(
                repository_root=tmp_path,
                reports_dir=tmp_path / "reports",
                apply_fixes=True,
            ),
        )
        tm.that(execution.result.passed, eq=not broken)
        tm.that(
            execution.outcome,
            eq=c.Infra.ToolOutcome.ERROR if broken else c.Infra.ToolOutcome.CLEAN,
        )
        tm.that(bool(execution.issues), eq=broken)
        tm.that(execution.raw_output.strip() != "", eq=True)
        tm.that(
            source.read_text(encoding="utf-8"),
            eq="def broken(:\n" if broken else "value = 1\n",
        )

    @staticmethod
    @pytest.mark.parametrize("fail_fast", [False, True])
    def test_failed_gate_preserves_only_executed_native_verdicts(
        tmp_path: Path,
        *,
        fail_fast: bool,
    ) -> None:
        """Real Ruff failures remain red without inventing dependent executions."""
        project: Path = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        (project / "src" / "broken.py").write_text(
            "missing_name( 1 )\n",
            encoding="utf-8",
        )
        requested = (c.Infra.LINT, c.Infra.FORMAT)
        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                (project.name,),
                requested,
                fail_fast=fail_fast,
            ),
        )
        tm.that(len(results), eq=1)
        verdict = results[0]
        tm.that(verdict.passed, eq=False)
        tm.that(
            tuple(verdict.gates),
            eq=requested[:1] if fail_fast else requested,
        )
        for execution in verdict.gates.values():
            tm.that(execution.result.passed, eq=False)
            tm.that(execution.finding_count > 0, eq=True)
            receipt = execution.raw_receipt
            tm.that(receipt is not None, eq=True)
            if receipt is None:
                pytest.fail("Every executed gate must retain its native receipt")
            tm.that(receipt.read_text(encoding="utf-8").strip() != "", eq=True)

    @staticmethod
    @pytest.mark.parametrize("residual", [False, True])
    def test_native_fix_accepts_only_postrepair_clean_state(
        tmp_path: Path,
        *,
        residual: bool,
    ) -> None:
        """Native repair applies safe effects but remaining findings stay red."""
        project: Path = u.Tests.mk_project(tmp_path, "p1", with_src=True)
        source = project / "src" / "broken.py"
        source.write_text(
            "import os\n" + ("missing_name()\n" if residual else ""),
            encoding="utf-8",
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            ruff_args=("--select", "F401,F821"),
        )
        before = gate.check(project, context)
        execution = gate.fix(project, context)
        after = gate.check(project, context)
        tm.that(before.result.passed, eq=False)
        tm.that(execution.result.passed, eq=not residual)
        tm.that(execution.issues, eq=after.issues)
        tm.that(execution.finding_count > 0, eq=residual)
        tm.that(
            execution.outcome,
            eq=c.Infra.ToolOutcome.FINDINGS if residual else c.Infra.ToolOutcome.CLEAN,
        )
        tm.that(source.read_text(encoding="utf-8"), lacks="import os")
        tm.that(execution.raw_output.strip() != "", eq=True)

    @staticmethod
    def test_native_fix_does_not_reject_already_fixed_diagnostics(
        tmp_path: Path,
    ) -> None:
        """Ruff can report a findings exit even after every violation was fixed."""
        project = u.Tests.mk_project(tmp_path, "repaired", with_src=True)
        source = project / "src" / "sample.py"
        source.write_text("import os\n", encoding="utf-8")
        gate = FlextInfraRuffLintGate(tmp_path)
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            ruff_args=("--select", "F401", "--exit-non-zero-on-fix"),
        )
        execution = gate.fix(project, context)
        tm.that(execution.result.passed, eq=True)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.CLEAN)
        tm.that(execution.issues, empty=True)
        tm.that(source.read_text(encoding="utf-8"), lacks="import os")
        tm.that(gate.check(project, context).result.passed, eq=True)

    @staticmethod
    def test_native_fix_rejects_unrepairable_recipe_residue(tmp_path: Path) -> None:
        """An unsplittable identifier retains its native diagnostic, never a waiver."""
        project = u.Tests.mk_project(tmp_path, "recipe-residue", with_src=True)
        limit = config.Infra.tooling.tools.ruff.line_length
        source = project / "src" / "sample.py"
        content = f"value_{'x' * (limit * 2)} = 1\n"
        source.write_text(content, encoding="utf-8")
        rule = next(
            rule
            for rule, recipe in config.Infra.tooling.tools.ruff.lint.fix_recipes.items()
            if recipe is c.Infra.LintFixRecipe.WRAP_LONG_LINE
        )
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            ruff_args=("--preview", "--select", rule, "--line-length", str(limit)),
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        execution = gate.fix(project, context)
        tm.that(execution.result.passed, eq=False)
        tm.that(execution.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(execution.issues, eq=gate.check(project, context).issues)
        tm.that([issue.code for issue in execution.issues], has=rule)
        tm.that(source.read_text(encoding="utf-8"), eq=content)
        tm.that(execution.raw_output.strip() != "", eq=True)

    @staticmethod
    @pytest.mark.parametrize("residual", [False, True])
    def test_markdown_fix_verifies_remaining_native_diagnostics(
        tmp_path: Path,
        *,
        residual: bool,
    ) -> None:
        """Already-fixed Markdown records do not fail a clean postrepair check."""
        project = u.Tests.mk_project(tmp_path, "markdown-repair")
        source = project / "README.md"
        source.write_text(
            "# Title   \n" + ("\n[Target](missing.md)\n" if residual else ""),
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(project)
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
        )
        gate = FlextInfraMarkdownGate(tmp_path)
        execution = gate.fix(project, context)
        tm.that(execution.result.passed, eq=not residual)
        tm.that(execution.issues, eq=gate.check(project, context).issues)
        tm.that(source.read_text(encoding="utf-8"), lacks="# Title   ")

    @staticmethod
    @pytest.mark.parametrize("check_only", [False, True])
    @pytest.mark.parametrize("residual", [False, True])
    def test_fix_literal_selection_preserves_unselected_source(
        tmp_path: Path,
        *,
        check_only: bool,
        residual: bool,
    ) -> None:
        """Public checker dispatch repairs only selected files unless check-only."""
        project = u.Tests.mk_project(tmp_path, "selected-repair", with_src=True)
        selected = project / "src" / "selected.py"
        unselected = selected.with_name("unselected.py")
        selected.write_text(
            "import os\n" + ("missing_name()\n" if residual else ""),
            encoding="utf-8",
        )
        unselected.write_text("import os\n", encoding="utf-8")
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            check_only=check_only,
            ruff_args=("--select", "F401,F821"),
            selected_files=(selected,),
        )
        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                (project.name,),
                (c.Infra.LINT,),
                ctx=context,
            ),
        )
        execution = results[0].gates[c.Infra.LINT]
        tm.that(execution.result.passed, eq=not (check_only or residual))
        tm.that("import os" in selected.read_text(encoding="utf-8"), eq=check_only)
        tm.that(unselected.read_text(encoding="utf-8"), eq="import os\n")
        gate = FlextInfraRuffLintGate(tmp_path)
        tm.that(
            execution.issues,
            eq=gate.check_files((selected,), project, context).issues,
        )
        tm.that(gate.check(project, context).result.passed, eq=False)

    @staticmethod
    @pytest.mark.parametrize(
        "gate_id",
        sorted(
            gate_id
            for gate_id in c.Infra.TYPE_CHECKER_GATES
            for gate_type in (FlextInfraGateRegistry().get(gate_id),)
            if gate_type is not None and gate_type.requires_python_targets
        ),
    )
    def test_project_without_an_executed_gate_is_not_accepted(
        tmp_path: Path,
        gate_id: str,
    ) -> None:
        """Content-selected checkers have no execution without Python sources."""
        project: Path = u.Tests.mk_project(tmp_path, "p1")
        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                (project.name,),
                (gate_id,),
            ),
        )
        tm.that(len(results), eq=1)
        tm.that(results[0].gates, empty=True)
        tm.that(results[0].passed, eq=False)
