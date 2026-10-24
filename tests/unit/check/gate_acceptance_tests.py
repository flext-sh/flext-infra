"""Native gate acceptance preserves failures, scope and execution evidence.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from difflib import unified_diff
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, infra, m, p
from flext_infra.check import FlextInfraGateRegistry, FlextInfraWorkspaceChecker
from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenStaging
from flext_infra.gates import (
    FlextInfraMarkdownGate,
    FlextInfraRuffFormatGate,
    FlextInfraRuffLintGate,
)
from tests import tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraGateAcceptance:
    """Observe acceptance through real checker and Ruff public boundaries."""

    @staticmethod
    def test_pyproject_generation_publishes_formatter_projection_at_fixed_point(
        infra_git_repo: Path,
    ) -> None:
        """The native atomic publisher creates the cold artifact with its metadata."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        declaration = u.Tests.toml_payload(
            (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        )
        project = u.Tests.toml_mapping(declaration["project"])
        distribution = config.Infra.codegen.infra_repository.distribution
        project["name"] = distribution
        declaration["project"] = project
        tool = u.Tests.toml_mapping(declaration.get("tool", {}))
        uv = u.Tests.toml_mapping(tool.get("uv", {}))
        uv["package"] = True
        tool["uv"] = uv
        declaration["tool"] = tool
        tm.ok(u.Cli.toml_write_mapping(root / c.PYPROJECT_FILENAME, declaration))
        u.Tests.initialize_git_repo(
            root, origin_url=u.Tests.repository_ref(distribution).url,
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        destination = root / config.Infra.codegen.make.ruff.format_config
        tm.that(destination.exists(), eq=False)
        generated = tm.ok(infra.codegen_conform(request))
        tm.that(generated.written_files, has=destination)
        tm.that(FlextInfraRuffFormatGate.configuration_path(root), eq=destination)
        metadata = (root / c.PYPROJECT_FILENAME).read_bytes()
        artifact = destination.read_bytes()
        lint = u.Tests.toml_table_at(metadata.decode("utf-8"), "tool", "ruff", "lint")
        policy = config.Infra.tooling.tools.ruff.lint
        tm.that(lint["select"], eq=sorted(policy.select))
        tm.that(lint["ignore"], eq=sorted(policy.ruling_disabled_rules))
        tm.that(lint["unfixable"], eq=sorted(policy.unfixable))
        repeated = tm.ok(infra.codegen_conform(request))
        after = (root / c.PYPROJECT_FILENAME).read_bytes()
        if after != metadata:
            pytest.fail("\n".join(unified_diff(
                metadata.decode("utf-8").splitlines(),
                after.decode("utf-8").splitlines(),
                fromfile="first-pyproject", tofile="second-pyproject",
            )))
        tm.that(repeated.written_files, eq=())
        tm.that(after, eq=metadata)
        tm.that(destination.read_bytes(), eq=artifact)

    @staticmethod
    @pytest.mark.parametrize("line_length,quote_style", [(61, "single"), (117, "double")])
    def test_native_formatter_projection_preserves_real_com812_lint(
        tmp_path: Path,
        line_length: int,
        quote_style: str,
    ) -> None:
        """Formatting uses its own view while ALL still reports real missing commas."""
        project, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "values.py"
        original = (
            '"""Values."""\n\nLABEL = "native formatter"\n\n'
            'VALUES = [\n    0,\n    1\n]\n'
        )
        source.write_text(original, encoding="utf-8")
        metadata = project / c.PYPROJECT_FILENAME
        document = tm.ok(u.Cli.toml_read_document(metadata))
        ruff = u.Cli.toml_ensure_path(document, ("tool", "ruff"))
        ruff["line-length"] = line_length
        formatting = u.Cli.toml_ensure_path(document, ("tool", "ruff", "format"))
        formatting["quote-style"] = quote_style
        metadata.write_text(u.Cli.toml_dumps(document), encoding="utf-8")
        before = metadata.read_bytes()
        policy_before = config.Infra.tooling.tools.ruff.lint.model_dump_json(
            by_alias=True, exclude_computed_fields=True,
        )
        configuration = u.Tests.write_ruff_format_projection(project)
        projected = tm.ok(u.Cli.toml_read_document(configuration))
        tm.that(projected, lacks="lint")
        context = m.Infra.GateContext(
            repository_root=tmp_path,
            reports_dir=tmp_path / "reports",
            apply_fixes=True,
            selected_files=(source,),
        )
        gate = FlextInfraRuffFormatGate(tmp_path)
        lint = FlextInfraRuffLintGate(tmp_path)
        findings = lint.check_files((source,), project, context)
        tm.that([issue.code for issue in findings.issues], has="missing-trailing-comma")
        check = gate.check_files((source,), project, context)
        tm.that(check.result.passed, eq=False)
        tm.that(check.raw_output, lacks="warning:")
        for execution in (
            gate.fix(project, context),
            gate.check_files((source,), project, context),
        ):
            tm.that(execution.result.passed, eq=True)
            tm.that(execution.raw_output, lacks="warning:")
        stable = source.read_bytes()
        quote = "'" if quote_style == "single" else '"'
        tm.that(stable.decode("utf-8"), has=f"LABEL = {quote}native formatter{quote}")
        source.write_text(original, encoding="utf-8")
        tm.ok(FlextInfraRuffFormatGate.format_files(project, (source,)))
        tm.that(source.read_bytes(), eq=stable)
        tm.that(metadata.read_bytes(), eq=before)
        tm.that(
            config.Infra.tooling.tools.ruff.lint.model_dump_json(
                by_alias=True, exclude_computed_fields=True,
            ),
            eq=policy_before,
        )
        source.write_text(original, encoding="utf-8")
        after = lint.check_files((source,), project, context)
        tm.that([issue.code for issue in after.issues], eq=[issue.code for issue in findings.issues])
        tm.that(metadata.read_bytes(), eq=before)

    @staticmethod
    def test_native_formatter_rejects_missing_stale_or_lint_bearing_projection(
        tmp_path: Path,
    ) -> None:
        """An absent or obsolete artifact cannot silently select the lint document."""
        project, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "values.py"
        source.write_text("VALUE = 1\n", encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="projection is missing"):
            FlextInfraRuffFormatGate.format_files(project, (source,))
        projection = u.Tests.write_ruff_format_projection(project)
        document = tm.ok(u.Cli.toml_read_document(projection))
        document["line-length"] = config.Infra.tooling.tools.ruff.line_length + 13
        projection.write_text(u.Cli.toml_dumps(document), encoding="utf-8")
        with pytest.raises(ValueError, match="projection is stale"):
            FlextInfraRuffFormatGate.format_files(project, (source,))
        u.Tests.write_ruff_format_projection(project)
        projection.write_text(
            projection.read_text(encoding="utf-8") + '\n[lint]\nselect = ["ALL"]\n',
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="lint"):
            FlextInfraRuffFormatGate.format_files(project, (source,))

    @staticmethod
    @pytest.mark.parametrize("stale", [False, True])
    def test_native_staged_formatting_prepares_cold_configuration_at_fixed_point(
        tmp_path: Path,
        *,
        stale: bool,
    ) -> None:
        """The native planner stages desired configuration before preparing Python."""
        project, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "values.py"
        source.write_text('"""Values."""\n\nVALUES = [0, 1]\n', encoding="utf-8")
        metadata = project / c.PYPROJECT_FILENAME
        before = metadata.read_bytes()
        destination = project / config.Infra.codegen.make.ruff.format_config
        if stale:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text('line-length = 1\n', encoding="utf-8")
        config_before = tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False))
        source_plan = tm.ok(FlextInfraCodegenConform.file_plan(
            project, source.relative_to(project).as_posix(),
            source.read_text(encoding="utf-8"),
        ))
        prepared = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(project, (source_plan,)))
        formatter = next(plan for plan in prepared if plan.path == destination)
        tm.that(formatter.desired_content is not None, eq=True)
        tm.that(formatter.before, eq=config_before)
        tm.that(metadata.read_bytes(), eq=before)
        tm.that(tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False)), eq=config_before)
        repeated = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(project, prepared))
        tm.that(
            tuple((plan.path, plan.desired_content) for plan in repeated),
            eq=tuple((plan.path, plan.desired_content) for plan in prepared),
        )

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
        location = m.Infra.SarifLocation.model_validate({
            "physicalLocation": {
                "artifactLocation": {"uri": "selected.py"},
                "region": {"startLine": 1, "endLine": 2},
            },
        })
        issue = m.Infra.Issue(
            file=location.uri,
            line=1,
            column=0,
            code="B101",
            message="assert used",
            locations=(location,),
            related_locations=(location,),
        )
        diagnostic: p.Infra.Issue = issue
        params = m.Infra.GateExecutionParams(
            project_dir=tmp_path,
            verdict=verdict,
            outcome=c.Infra.ToolOutcome.FINDINGS,
            issues=(diagnostic,),
            raw_output="native diagnostic\n",
            started=1.0,
        )
        restored = m.Infra.GateExecutionParams.model_validate_json(
            params.model_dump_json(round_trip=True),
        )
        boundary: p.Infra.GateExecutionParams = restored
        tm.that(restored.model_dump(), eq=params.model_dump())
        tm.that(boundary.verdict, eq=verdict)
        tm.that(boundary.outcome, eq=c.Infra.ToolOutcome.FINDINGS)
        tm.that(boundary.raw_output, eq=params.raw_output)
        tm.that(boundary.project_dir, eq=tmp_path)
        tm.that(boundary.started, eq=params.started)
        tm.that(tuple(boundary.issues), eq=params.issues)
        tm.that(params.issues[0] is issue, eq=True)
        tm.that(issue.locations[0] is location, eq=True)
        tm.that(boundary.issues[0].locations[0].end_line, eq=location.end_line)
        tm.that(
            boundary.issues[0].related_locations[0].model_dump(mode="json"),
            eq=location.model_dump(mode="json"),
        )
        execution = m.Infra.GateExecution(
            result=m.Infra.GateResult(
                project=tmp_path.name,
                gate=c.Infra.SECURITY,
                passed=verdict,
            ),
            issues=params.issues,
            outcome=params.outcome,
        )
        tm.that(execution.issues[0] is issue, eq=True)
        restored_execution = m.Infra.GateExecution.model_validate_json(
            execution.model_dump_json(exclude_computed_fields=True),
        )
        tm.that(
            restored_execution.issues[0].model_dump(mode="json"),
            eq=issue.model_dump(mode="json"),
        )
        for mode in ("validation", "serialization"):
            schema = m.Infra.GateExecution.model_json_schema(mode=mode)
            issue_schema = m.Infra.Issue.model_json_schema(mode=mode)
            tm.that(
                schema["$defs"][m.Infra.Issue.__name__]["properties"],
                eq=issue_schema["properties"],
            )
        payload = execution.model_dump(mode="json", exclude_computed_fields=True)
        payload["issues"] = [{**issue.model_dump(mode="json"), "line": "invalid"}]
        with pytest.raises(m.ValidationError, match="line"):
            m.Infra.GateExecution.model_validate_json(tm.ok(u.Cli.json_dumps(payload)))

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
        metadata = project / c.PYPROJECT_FILENAME
        metadata.write_text(
            metadata.read_text(encoding="utf-8") + u.Tests.ruff_policy_toml(project),
            encoding="utf-8",
        )
        u.Tests.write_ruff_format_projection(project)
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
        metadata = project / c.PYPROJECT_FILENAME
        metadata.write_text(
            metadata.read_text(encoding="utf-8") + u.Tests.ruff_policy_toml(project),
            encoding="utf-8",
        )
        u.Tests.write_ruff_format_projection(project)
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
            ruff_args=("--select", rule, "--line-length", str(limit)),
        )
        gate = FlextInfraRuffLintGate(tmp_path)
        execution = gate.fix(project, context)
        tm.that(execution.result.passed, eq=False)
        tm.that(
            execution.outcome,
            eq=c.Infra.ToolOutcome.FINDINGS,
            msg=execution.raw_output,
        )
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
