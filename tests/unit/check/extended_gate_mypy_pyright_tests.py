"""Public checker acceptance against real tools and native report schemas.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraCli, check, config, gates
from tests import c, m, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraTypeGates:
    """The selected project's actual findings determine acceptance."""

    @staticmethod
    def test_omitted_ruff_policy_is_rejected() -> None:
        """A governed Make policy requires an explicit typed Ruff cache."""
        configured = config.Infra.codegen.make
        with pytest.raises(ValueError, match="ruff_cache"):
            m.Infra.MakeSpec.model_validate(
                configured.model_dump(
                    exclude={"ruff_cache"},
                    exclude_computed_fields=True,
                ),
            )

    @staticmethod
    @pytest.mark.parametrize(
        "field",
        ["data_home_environment_variable", "user_home_environment_variable"],
    )
    def test_required_cache_environment_fields_do_not_inherit_defaults(
        field: str,
    ) -> None:
        """Testmon keeps its explicitly required YAML environment contract."""
        configured = config.Infra.codegen.make
        policy = configured.testmon_cache
        payload = policy.model_dump(
            exclude={field},
            exclude_computed_fields=True,
        )
        with pytest.raises(ValueError, match=field):
            type(policy).model_validate(payload)

    @staticmethod
    @pytest.mark.slow
    def test_mypy_cache_is_project_keyed_across_checkouts_and_relocks(
        tmp_path: Path,
    ) -> None:
        """One environment shares one external cache per declared project name."""
        spec = config.Infra.codegen.make.mypy_cache
        cache_home = tmp_path / "cache"
        shared_root = cache_home / spec.external_storage_directory
        with tm.scope(env={str(spec.data_home_environment_variable): str(cache_home)}):
            for checkout, project in (
                ("lane", "fixture-alpha"),
                ("primary", "fixture-alpha"),
                ("other", "fixture-beta"),
            ):
                root = tmp_path / checkout
                root.mkdir()
                (root / c.PYPROJECT_FILENAME).write_text(
                    f"[project]\nname = '{project}'\nversion = '0.0.0'\n[tool.mypy]\n",
                    encoding="utf-8",
                )
                (root / "sample.py").write_text("value: int = 1\n", encoding="utf-8")
                lock = root / c.Infra.UV_LOCK_FILENAME
                context = m.Infra.GateContext(
                    repository_root=root,
                    reports_dir=root / ".reports",
                )
                gate = gates.FlextInfraMypyGate(root)
                cache = shared_root / project / u.Infra.environment_cache_identity()
                for revision in (1, 2):
                    lock.write_text(
                        f"version = 1\nrevision = {revision}\n",
                        encoding="utf-8",
                    )
                    execution = gate.check(root, context)
                    tm.ok(execution.result.passed)
                    tm.that(
                        [
                            line.partition("Cache Dir:")[2].strip()
                            for line in execution.raw_output.splitlines()
                            if line.startswith("LOG:") and "Cache Dir:" in line
                        ],
                        eq=[str(cache)],
                    )
                    tm.ok(cache.is_dir())
                    tm.ok(any(path.is_file() for path in cache.rglob("*")))
                tm.fail((root / ".mypy_cache").exists())
            tm.that(
                {path.name for path in shared_root.iterdir()},
                eq={"fixture-alpha", "fixture-beta"},
            )

    @pytest.fixture
    def checker_context(self: Path) -> m.Infra.GateContext:
        """Configure the existing real package for native checker execution.

        Returns:
            The resulting ``m.Infra.GateContext``.

        """
        pyproject = self / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8")
            + '\n[tool.mypy]\n[tool.pyright]\ninclude = ["src"]\n'
            + '[tool.pyrefly]\nproject-includes = ["src"]\n',
            encoding="utf-8",
        )
        reports = self / ".reports"
        reports.mkdir()
        return m.Infra.GateContext(
            repository_root=self,
            reports_dir=reports,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "plugin_output",
        ["native-plugin-output", "    native-plugin-output", "Deferral trace:"],
    )
    def test_mypy_preserves_malformed_native_output(
        checker_context: m.Infra.GateContext,
        plugin_output: str,
    ) -> None:
        """Unexpected plugin output remains a causal, visible tool failure."""
        project = checker_context.repository_root
        plugin = project / "plugin.py"
        plugin.write_text(
            "from mypy.plugin import Plugin\n"
            "def plugin(version: str) -> type[Plugin]:\n"
            f"    print({plugin_output!r})\n"
            "    return Plugin\n",
            encoding="utf-8",
        )
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8").replace(
                "[tool.mypy]\n",
                '[tool.mypy]\nplugins = ["plugin.py"]\n',
            ),
            encoding="utf-8",
        )

        result = gates.FlextInfraMypyGate(project).check(project, checker_context)

        tm.fail(result.result.passed)
        tm.that(
            tuple(issue.code for issue in result.issues),
            has=c.Infra.ToolOutcome.ERROR,
        )
        tm.that(
            "\n".join(issue.message for issue in result.issues),
            has=plugin_output,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "gate",
        sorted(c.Infra.TYPE_CHECKER_GATES),
    )
    def test_public_literal_file_checker_preserves_native_findings_policy(
        checker_context: m.Infra.GateContext,
        gate: str,
    ) -> None:
        """Native findings survive while acceptance follows the typed SSOT policy."""
        project = checker_context.repository_root
        source_root = project / config.Infra.source_scan.roots[0]
        source_root.mkdir(exist_ok=True)
        selected = source_root / "literal_file.py"
        selected.write_text("value: int = 'incorrect'\n", encoding="utf-8")
        sibling = source_root / "unselected_file.py"
        sibling.write_text("def :\n", encoding="utf-8")
        reports = checker_context.reports_dir / "literal-file"
        code = FlextInfraCli.infra_main([
            "check",
            "run",
            "--repository-root",
            str(project),
            "--file",
            str(selected.relative_to(project)),
            "--gates",
            gate,
            "--reports-dir",
            str(reports),
        ])
        tm.that(code, eq=1)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        findings = tm.ok(
            u.Infra.check_report_findings(project, reports_dir=report_path.parent),
        )
        tm.that(findings, empty=False)
        tm.that(
            any(
                location.uri.endswith(str(selected.relative_to(project)))
                for finding in findings
                for location in finding.locations
            ),
            eq=True,
        )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("module", "service"),
        [
            ("flext_infra", "FlextInfraServiceBase"),
            ("flext_infra", "FlextInfraProjectSelectionServiceBase"),
            ("flext_infra.codegen", "FlextInfraCodegenExecution"),
        ],
    )
    def test_mypy_public_service_payload_bound(
        checker_context: m.Infra.GateContext,
        module: str,
        service: str,
    ) -> None:
        """Public execution preserves payloads; only selection has a JSON bound."""
        project = checker_context.repository_root
        pyproject = project / c.PYPROJECT_FILENAME
        tooling = tm.ok(u.Infra.load_tooling_inputs(project)).document
        plugins = u.Infra.native_tool_setting(tooling, "mypy", "plugins", list[str])
        pyproject.write_text(
            pyproject.read_text(encoding=c.DEFAULT_ENCODING).replace(
                "[tool.mypy]\n",
                f"[tool.mypy]\nplugins = {list(plugins)!r}\n",
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        source = project / "src" / "test_pkg" / "payload_bound.py"
        selection = service == "FlextInfraProjectSelectionServiceBase"
        payload = "str" if selection else "set[int]"
        valid_source = (
            f"from {module} import {service}\n\n"
            f"def consume(value: {service}[{payload}]) -> {payload}:\n"
            "    return value.execute().unwrap()\n"
        )
        source.write_text(valid_source, encoding=c.DEFAULT_ENCODING)
        gate = gates.FlextInfraMypyGate(project)

        accepted = gate.check(project, checker_context)

        tm.that(accepted.result.passed, truth=True, msg=accepted.raw_output)
        tm.that(accepted.issues, truth=False, msg=accepted.raw_output)
        invalid_source = (
            valid_source.replace(f"{service}[str]", f"{service}[set[int]]")
            if selection
            else valid_source.replace(f"-> {payload}:", "-> int:")
        )
        if selection:
            invalid_source = invalid_source.replace("-> str:", "-> set[int]:")
        source.write_text(invalid_source, encoding=c.DEFAULT_ENCODING)

        rejected = gate.check(project, checker_context)

        tm.that(rejected.result.passed, truth=False, msg=rejected.raw_output)
        tm.that(len(rejected.issues), eq=1, msg=rejected.raw_output)
        (issue,) = rejected.issues
        tm.that(
            issue.code,
            eq="type-var" if selection else "return-value",
            msg=rejected.raw_output,
        )
        tm.that(issue.severity, eq=c.Infra.ERROR, msg=rejected.raw_output)
        diagnostic_path = project / issue.file
        tm.that(diagnostic_path.resolve(), eq=source.resolve(), msg=rejected.raw_output)
        tm.that(issue.line, eq=3 if selection else 4, msg=rejected.raw_output)
        if selection:
            annotation = invalid_source.splitlines()[2]
            tm.that(
                issue.column,
                eq=annotation.index("set[int]"),
                msg=rejected.raw_output,
            )
            tm.that(issue.message, has=service, msg=rejected.raw_output)
        else:
            tm.that(issue.message, has=["set[int]", "int"], msg=rejected.raw_output)

    @staticmethod
    @pytest.mark.slow
    def test_mypy_preserves_protocol_member_diagnostics(
        checker_context: m.Infra.GateContext,
    ) -> None:
        """Native protocol conflict details remain visible in reported issues."""
        project = checker_context.repository_root
        source = project / "src" / "test_pkg" / "contract.py"
        source.write_text(
            "from typing import Protocol\n"
            "class Expected(Protocol):\n"
            "    def size(self) -> int: ...\n"
            "class Actual:\n"
            "    def size(self) -> str:\n"
            "        return 'incorrect'\n"
            "value: Expected = Actual()\n",
            encoding="utf-8",
        )

        result = gates.FlextInfraMypyGate(project).check(project, checker_context)

        tm.fail(result.result.passed)
        messages = "\n".join(issue.message for issue in result.issues)
        tm.that(messages, has=["Expected", "Actual", "def size", "int", "str"])

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "gate_class",
        [
            gates.FlextInfraMypyGate,
            gates.FlextInfraPyrightGate,
            gates.FlextInfraPyreflyGate,
        ],
    )
    def test_real_check_and_repair(
        checker_context: m.Infra.GateContext,
        gate_class: type[gates.FlextInfraGate],
    ) -> None:
        """Test real check and repair."""
        project = checker_context.repository_root
        reports = checker_context.reports_dir
        ctx = m.Infra.GateContext(repository_root=project, reports_dir=reports)
        gate = gate_class(project)
        source = project / "src" / "test_pkg" / "contract.py"
        source.write_text('value: int = "incorrect"\n', encoding="utf-8")
        failed = gate.check(project, ctx)
        tm.that(failed.result.passed, eq=False)
        tm.that(failed.issues, truth=True)
        tm.that(failed.result.errors, truth=True)
        tm.that(
            any(issue.severity.lower() == "error" for issue in failed.issues),
            truth=True,
        )

        source.write_text("value: int = 1\n", encoding="utf-8")
        repaired = gate.check(project, ctx)
        tm.that(repaired.result.passed, truth=True, msg=repaired.raw_output)
        tm.that(repaired.issues, truth=False)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        ("gate_class", "config_text"),
        [
            (
                gates.FlextInfraPyrightGate,
                '[tool.pyright]\ninclude = ["src"]\nreportAssignmentType = "warning"\n',
            ),
            (
                gates.FlextInfraPyreflyGate,
                (
                    '[tool.pyrefly]\nproject-includes = ["src"]\n'
                    '[tool.pyrefly.errors]\nbad-assignment = "warn"\n'
                ),
            ),
        ],
    )
    def test_real_warning_is_red(
        real_python_package: Path,
        gate_class: type[gates.FlextInfraGate],
        config_text: str,
    ) -> None:
        """Test real warning is red."""
        project = real_python_package
        pyproject = project / c.PYPROJECT_FILENAME
        pyproject.write_text(
            pyproject.read_text(encoding="utf-8") + "\n" + config_text,
            encoding="utf-8",
        )
        (project / "src" / "test_pkg" / "warning.py").write_text(
            'value: int = "incorrect"\n',
            encoding="utf-8",
        )
        reports = project / ".reports"
        reports.mkdir()
        result = gate_class(project).check(
            project,
            m.Infra.GateContext(repository_root=project, reports_dir=reports),
        )
        tm.that(result.result.passed, eq=False)
        tm.that(
            any(issue.severity in {"warn", "warning"} for issue in result.issues),
            truth=True,
        )

    @staticmethod
    @pytest.mark.slow
    def test_failed_pyrefly_cannot_reuse_previous_report(
        checker_context: m.Infra.GateContext,
    ) -> None:
        """Test failed pyrefly cannot reuse previous report."""
        project = checker_context.repository_root
        pyproject = project / c.PYPROJECT_FILENAME
        reports = checker_context.reports_dir
        gate = gates.FlextInfraPyreflyGate(project)
        first = gate.check(project, checker_context)
        tm.that(first.result.passed, truth=True, msg=first.raw_output)
        native_reports = tuple(reports.glob("*-pyrefly.json"))
        tm.that(len(native_reports) == 1, truth=True)
        tm.that(
            m.Infra.PyreflyReport.model_validate_json(
                native_reports[0].read_text(encoding="utf-8"), strict=True
            ).errors,
            truth=False,
        )
        pyproject.write_text("[tool.pyrefly\n", encoding="utf-8")
        failed = gate.check(project, checker_context)
        tm.that(failed.result.passed, eq=False)
        tm.that(failed.raw_output, truth=True)
        # The gate's declared report path is replaced per run: the passing
        # run's report is removed before the failing run, never reused.
        tm.that(native_reports[0].exists(), truth=False)

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "gate_class",
        [
            gates.FlextInfraMypyGate,
            gates.FlextInfraPyrightGate,
            gates.FlextInfraPyreflyGate,
        ],
    )
    def test_explicit_files_keep_selected_scope(
        checker_context: m.Infra.GateContext,
        gate_class: type[gates.FlextInfraGate],
    ) -> None:
        """Test explicit files keep selected scope."""
        project = checker_context.repository_root
        package = project / "src" / "test_pkg"
        unselected = package / "unselected.py"
        unselected.write_text('value: int = "incorrect"\n', encoding="utf-8")
        gate = gate_class(project)
        result = gate.check_files([package / "identity.py"], project, checker_context)
        tm.that(result.result.passed, truth=True, msg=result.raw_output)
        tm.that(result.issues, truth=False)

        selected_error = gate.check_files([unselected], project, checker_context)
        tm.that(selected_error.result.passed, eq=False, msg=str(selected_error))
        tm.that(
            any(
                issue.file.endswith(unselected.name) for issue in selected_error.issues
            ),
            truth=True,
        )

        full_project = gate.check(project, checker_context)
        tm.that(full_project.result.passed, eq=False, msg=str(full_project))
        tm.that(
            any(issue.file.endswith(unselected.name) for issue in full_project.issues),
            truth=True,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "gate_class",
        [
            gates.FlextInfraMypyGate,
            gates.FlextInfraPyrightGate,
            gates.FlextInfraPyreflyGate,
        ],
    )
    def test_empty_source_is_not_passed(
        tmp_path: Path,
        gate_class: type[gates.FlextInfraGate],
    ) -> None:
        """A checker invoked without inputs never reads as a clean pass."""
        result = gate_class(tmp_path).check(
            tmp_path,
            m.Infra.GateContext(repository_root=tmp_path, reports_dir=tmp_path),
        )
        tm.that(result.result.passed, eq=False)
        # An empty source must never read as a clean pass: the skipped state
        # stays visible in the execution errors for every gate posture.
        tm.that(result.result.errors, truth=True)

    @staticmethod
    @pytest.mark.parametrize(
        "gate_class",
        [gates.FlextInfraPyrightGate, gates.FlextInfraPyreflyGate],
    )
    def test_python_analysis_gates_follow_detected_content(
        tmp_path: Path,
        real_python_package: Path,
        gate_class: type[gates.FlextInfraGate],
    ) -> None:
        """Detected Python content, not a pass receipt, selects the type gates."""
        tm.fail(
            gate_class(tmp_path).selected_for(tmp_path, u.Tests.gate_context(tmp_path))
        )
        tm.that(
            gate_class(real_python_package).selected_for(
                real_python_package, u.Tests.gate_context(real_python_package)
            ),
            eq=True,
        )

    @staticmethod
    @pytest.mark.parametrize("payload", ["", " ", "not JSON", "{}", "[]", "null"])
    @pytest.mark.parametrize(
        "report_model",
        [m.Infra.MypyDiagnostic, m.Infra.PyrightReport, m.Infra.PyreflyReport],
    )
    def test_invalid_native_report(
        report_model: type[
            m.Infra.MypyDiagnostic | m.Infra.PyrightReport | m.Infra.PyreflyReport
        ],
        payload: str,
    ) -> None:
        """Test invalid native report."""
        with pytest.raises(c.ValidationError):
            report_model.model_validate_json(payload, strict=True)

    @staticmethod
    def test_pyright_incomplete_counts() -> None:
        """Test pyright incomplete counts."""
        payload = (
            '{"version":"1.1.411","time":"1","generalDiagnostics":[], '
            '"summary":{"filesAnalyzed":1,"errorCount":0,"warningCount":1,'
            '"informationCount":0,"timeInSec":0.1}}'
        )
        with pytest.raises(c.ValidationError, match="warning count"):
            m.Infra.PyrightReport.model_validate_json(payload, strict=True)

    @staticmethod
    def test_pyrefly_empty_native_report() -> None:
        """Test pyrefly empty native report."""
        report = m.Infra.PyreflyReport.model_validate_json('{"errors":[]}', strict=True)
        tm.that(report.errors, truth=False)

    @staticmethod
    def test_pyright_information_without_location() -> None:
        """Test pyright information without location."""
        report = m.Infra.PyrightReport.model_validate_json(
            '{"version":"1.1.411","time":"1","generalDiagnostics":['
            '{"file":"source.py","severity":"information","message":"type info"}],'
            '"summary":{"filesAnalyzed":1,"errorCount":0,"warningCount":0,'
            '"informationCount":1,"timeInSec":0.1}}',
            strict=True,
        )
        tm.that(report.general_diagnostics[0].range, none=True)
        tm.that(report.summary.information_count == 1, truth=True)

    @staticmethod
    def test_pyright_zero_collection() -> None:
        """filesAnalyzed=0 parses; the gate, not the model, judges it."""
        report = m.Infra.PyrightReport.model_validate_json(
            '{"version":"1.1.411","time":"1","generalDiagnostics":[], '
            '"summary":{"filesAnalyzed":0,"errorCount":0,"warningCount":0,'
            '"informationCount":0,"timeInSec":0.1}}',
            strict=True,
        )
        tm.that(report.summary.files_analyzed == 0, truth=True)
        tm.that(report.general_diagnostics, truth=False)

    @staticmethod
    def test_checker_does_not_run_type_gates_on_content_only_project(
        real_python_package: Path,
    ) -> None:
        """A project without Python targets gets no type-gate row at all."""
        for module in (real_python_package / "src").rglob("*.py"):
            module.unlink()
        reports = real_python_package / ".reports"

        results = tm.ok(
            check.FlextInfraWorkspaceChecker(
                repository_root=real_python_package.parent,
            ).run_projects(
                [real_python_package.name],
                [
                    gates.FlextInfraPyrightGate.gate_id,
                    gates.FlextInfraPyreflyGate.gate_id,
                ],
                u.Tests.gate_context(real_python_package.parent, reports),
            ),
        )

        tm.that(results[0].gates, empty=True)
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_MARKDOWN_FILENAME}")
        markdown = report_path.read_text(
            encoding="utf-8",
        )
        tm.that(markdown, lacks=f"- {gates.FlextInfraPyrightGate.gate_id}:")
        tm.that(markdown, lacks=f"- {gates.FlextInfraPyreflyGate.gate_id}:")
