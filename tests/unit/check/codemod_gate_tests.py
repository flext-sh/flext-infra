"""Public codemod gate evidence against the real ast-grep scanner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from re import escape

import pytest

from flext_infra import config
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_infra.cli import FlextInfraCli
from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.gates.codemod import FlextInfraCodemodGate
from tests import c, m, t, tm, u


class TestsFlextInfraCodemodGate:
    """Block on every policy finding and on every native scanner failure."""

    @staticmethod
    def _project(
        tmp_path: Path,
        installed_dependency_path: Path,
        *,
        severity: str = "error",
    ) -> Path:
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        tm.ok(u.Cli.run_checked(["mise", "trust", str(tmp_path / ".mise.toml")]))
        project = installed_dependency_path / "scanner_contract"
        (project / "src").mkdir(parents=True)
        package = project / "src" / "scanner_contract"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        metadata = installed_dependency_path / "scanner_contract-1.0.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: scanner-contract\nVersion: 1.0.0\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (project / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "scanner-contract"\nversion = "1.0.0"\n'
            "dependencies = []\n"
            '[tool.uv.build-backend]\nmodule-root = "src"\n'
            'module-name = "scanner_contract"\n',
            encoding="utf-8",
        )
        u.Tests.declare_codemod_rules(
            project,
            {
                name: (
                    f"id: contract-{name}\nlanguage: Python\nseverity: {severity}\n"
                    f"message: Observed {name}\nrule:\n  pattern: {name}($VALUE)\n"
                )
                for name in ("first", "second")
            },
        )
        return project

    @pytest.mark.parametrize("severity", ["error", "warning", "info", "hint"])
    def test_policy_findings_block_at_every_severity(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        severity: str,
    ) -> None:
        """Test policy findings block at every severity."""
        project = self._project(tmp_path, installed_dependency_path, severity=severity)
        source = project / "src" / "subject.py"
        source.write_text("\nsecond(1)\n", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)

        tm.fail(execution.result.passed)
        policy_findings = tuple(
            issue for issue in execution.issues if issue.code == "contract-second"
        )
        tm.that(len(policy_findings), eq=1, msg=execution.raw_output)
        finding = policy_findings[0]
        tm.ok(finding.file.endswith("src/subject.py"))
        tm.that((finding.line, finding.column), eq=(2, 1))
        tm.that(finding.severity, eq=severity)
        tm.that(
            tuple(execution.result.errors),
            eq=tuple(issue.formatted for issue in execution.issues),
        )
        tm.that(
            execution.finding_count,
            eq=len(execution.issues),
        )
        if severity == "error":
            tm.that(execution.raw_output, has="exit=1")
            tm.that(execution.raw_output, has="error(s) found in code")

    def test_clean_native_scan_has_no_findings(
        self, tmp_path: Path, installed_dependency_path: Path
    ) -> None:
        """Test clean native scan has no findings."""
        project = self._project(tmp_path, installed_dependency_path)
        (project / "src" / "subject.py").write_text("", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)

        tm.that(execution.result.passed, eq=True, msg=execution.raw_output)
        tm.that(execution.issues, empty=True)
        tm.that(execution.raw_output, has="exit=0")

    @staticmethod
    def _rule_files(
        project: Path,
        rule_id: str,
        tmp_path: Path,
    ) -> Sequence[str]:
        """Project-relative files the bundled rule ``rule_id`` reports.

        Returns:
            The sorted project-relative files the real scan reported.

        """
        execution = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)
        return sorted(
            (project / issue.file).resolve().relative_to(project.resolve()).as_posix()
            for issue in execution.issues
            if issue.code == rule_id
        )

    def test_flext_tests_import_is_banned_only_in_the_infra_package(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """The project-root scan reports flext_tests only inside flext_infra.

        Premise (operator-ruling-2026-10-08-subprocess-test-imports, item 2):
        the rule fires when flext-infra scans itself (``src/...`` paths), not
        only from the workspace root, and never binds another package.
        """
        project = self._project(tmp_path, installed_dependency_path)
        for relative in ("src/flext_infra/leak.py", "src/flext_tests/tier.py"):
            module = project / relative
            module.parent.mkdir(parents=True)
            module.write_text("import flext_tests\n", encoding="utf-8")

        tm.that(
            self._rule_files(project, "ban-infra-runtime-flext-tests-import", tmp_path),
            eq=["src/flext_infra/leak.py"],
        )

    def test_subprocess_is_banned_in_a_consumer(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """A consumer routes processes through the public execution owner."""
        project = self._project(tmp_path, installed_dependency_path)
        consumer = "src/consumer/spawn.py"
        module = project / consumer
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("import subprocess\n", encoding="utf-8")

        tm.that(
            self._rule_files(project, "ban-subprocess-outside-run-owner", tmp_path),
            eq=[consumer],
        )

    def test_generated_source_tree_is_outside_the_scan(
        self, tmp_path: Path, installed_dependency_path: Path
    ) -> None:
        """A tracked generated-source module never reaches the policy scan.

        Premise (flext-gknfx): generated trees are tracked, so Git ignore rules
        no longer hide them from ast-grep; the codegen artifact key does.
        """
        names = config.Infra.codegen.generated_sources
        tm.that(names, empty=False)
        project = self._project(tmp_path, installed_dependency_path)
        tree = project / "src" / "pkg" / names[0]
        tree.mkdir(parents=True)
        (tree / "wire_pb2.py").write_text("\nsecond(1)\n", encoding="utf-8")
        (project / "src" / "pkg" / "subject.py").write_text("", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)

        tm.that(execution.result.passed, eq=True, msg=str(execution.issues))
        tm.that(execution.issues, empty=True)

    def test_owned_stub_paths_share_mod_and_check_admission(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Empty, invalid, ignored and generated stubs fail without an AST match."""
        project = self._project(tmp_path, installed_dependency_path)
        retired = next(
            artifact.name
            for artifact in config.Infra.codegen.artifacts
            if artifact.retired_typing_root
        )
        generated = config.Infra.codegen.generated_sources[0]
        owned = {
            "root.pyi": b"",
            "tests/boundary.pyi": b"invalid [\n",
            "examples/boundary.pyi": b"def load() -> bytes: ...\n",
            "scripts/boundary.pyi": f"{c.Infra.AUTOGEN_HEADER}\n".encode(),
            "infra/contracts/boundary.pyi": b"\xff\n",
            "src/pkg/.typecache/boundary.pyi": b"",
            f"src/pkg/{generated}/boundary.pyi": b"",
            f"{retired}/owned-stubs/package/__init__.pyi": b"",
        }
        excluded = (
            ".venv/lib/site-packages/dependency/__init__.pyi",
            "src/pkg/.venv/lib/site-packages/dependency/__init__.pyi",
            f"{retired}/foreign/__init__.pyi",
            "foreign/__init__.pyi",
        )
        for relative, content in owned.items():
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        for relative in excluded:
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"")
        for root in (project / retired / "foreign", project / "foreign"):
            (root / c.Infra.GIT_DIR).mkdir()
        (project / retired / "owned-stubs" / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "owned-stubs"\nversion = "1.0.0"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        gate = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)
        observed = {
            Path(issue.file).as_posix()
            for issue in gate.issues
            if issue.code == "ban-stub-file"
        }
        tm.that(observed, eq=set(owned))
        tm.fail(gate.result.passed)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                project, fix=False, selection=("ban-stub-file",)
            )
        )
        tm.that({entry.file.as_posix() for entry in report.entries}, eq=set(owned))
        tm.that(report.detection_only, eq=len(owned))
        tm.that(report.actionable, eq=0)
        tm.ok(all(entry.origin == "owned-path" for entry in report.entries))
        tm.ok(all(entry.source_state is not None for entry in report.entries))
        for relative, content in owned.items():
            tm.that((project / relative).read_bytes(), eq=content)

    def test_custom_analysis_exclusion_keeps_stub_and_python_scope_distinct(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Authored exclusions hide ordinary Python, never owned stub policy paths."""
        project = self._project(tmp_path, installed_dependency_path)
        custom = m.Infra.CodegenArtifactSpec(
            name="arbitrary_contract_exclusion",
            analysis_exclude=True,
        )
        declared = config.Infra.codegen.model_copy(
            update={"artifacts": (*config.Infra.codegen.artifacts, custom)},
        )
        delta: t.JsonValue = {
            "codegen": declared.model_dump(mode="json", include={"artifacts"}),
        }
        prefix = type(config).model_config.get("env_prefix")
        if prefix is None:
            tm.reject("The config owner must declare its environment prefix")
        try:
            with u.Tests.env_vars_context({
                f"{prefix}Infra": tm.ok(
                    u.Cli.json_dumps(delta),
                ),
            }):
                type(config).reset_for_testing()
                elected = next(
                    artifact
                    for artifact in config.Infra.codegen.artifacts
                    if artifact.name == custom.name
                )
                source_root = project / config.Infra.source_scan.roots[0]
                excluded = source_root / elected.name
                excluded.mkdir(parents=True)
                stub = excluded / "boundary.pyi"
                stub.write_bytes(b"")
                ordinary = excluded / "ordinary.py"
                ordinary.write_text("second(1)\n", encoding=c.DEFAULT_ENCODING)
                active = source_root / "active.py"
                active.write_text("second(2)\n", encoding=c.DEFAULT_ENCODING)
                before = tuple(
                    tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                    for path in (stub, ordinary, active)
                )
                expected = {
                    ("ban-stub-file", stub.relative_to(project).as_posix()),
                    ("contract-second", active.relative_to(project).as_posix()),
                }
                gate = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)
                tm.fail(gate.result.passed)
                tm.that(
                    {
                        (issue.code, Path(issue.file).as_posix())
                        for issue in gate.issues
                        if issue.code in {rule for rule, _ in expected}
                    },
                    eq=expected,
                )
                report = tm.ok(
                    FlextInfraModGateEngine.scan(
                        project,
                        fix=False,
                        selection=("ban-stub-file", "contract-second"),
                    ),
                )
                tm.that(
                    {
                        (entry.rule_id, entry.file.as_posix())
                        for entry in report.entries
                    },
                    eq=expected,
                )
                tm.ok(u.Cli.atomic_verify_binary_file_states(before))
        finally:
            type(config).reset_for_testing()

    @pytest.mark.parametrize("target_scope", ["in_tree", "foreign", "broken"])
    def test_stub_symlink_keeps_the_owned_path_name(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        target_scope: str,
    ) -> None:
        """Check observes the stub name; Mod preserves the original physical guard."""
        project = self._project(tmp_path, installed_dependency_path)
        source_root = (
            project / "src" if target_scope == "in_tree" else tmp_path / "foreign"
        )
        source_root.mkdir(parents=True, exist_ok=True)
        source = source_root / "boundary.py"
        if target_scope != "broken":
            source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        source_before = tm.ok(u.Cli.atomic_read_binary_file_state(source))
        stub = project / "src" / "boundary.pyi"
        stub.symlink_to(source.name if target_scope == "in_tree" else source)
        link_before = stub.readlink()
        identity_before = stub.lstat()
        tm.that(
            u.Infra.ast_grep_scan_targets(project, source_files=(stub,)),
            eq=(stub.relative_to(project).as_posix(),),
        )
        gate = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)
        tm.that(
            [issue.file for issue in gate.issues if issue.code == "ban-stub-file"],
            eq=[stub.relative_to(project).as_posix()],
        )
        with pytest.raises(OSError, match=escape(str(stub))) as original_guard:
            u.Cli.atomic_read_binary_file_state(stub, required=True).unwrap()
        with pytest.raises(type(original_guard.value)) as mod_guard:
            FlextInfraModGateEngine.scan(
                project,
                fix=False,
                selection=("ban-stub-file",),
                source_files=(stub,),
            )
        tm.that(mod_guard.value.args, eq=original_guard.value.args)
        tm.that(mod_guard.value.filename, eq=original_guard.value.filename)
        tm.that(stub.is_symlink(), eq=True)
        tm.that(stub.readlink(), eq=link_before)
        identity_after = stub.lstat()
        tm.that(
            (identity_after.st_dev, identity_after.st_ino),
            eq=(identity_before.st_dev, identity_before.st_ino),
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((source_before,)))

    def test_runtime_typing_contracts_are_not_stub_paths(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Protocol, ABC and overload ellipses in .py remain legitimate declarations."""
        project = self._project(tmp_path, installed_dependency_path)
        (project / "typings.py").write_text(
            "from abc import ABC, abstractmethod\n"
            "from typing import Protocol, overload\n"
            "class Port(Protocol):\n"
            "    def load(self) -> bytes: ...\n"
            "class Base(ABC):\n"
            "    @abstractmethod\n"
            "    def load(self) -> bytes: ...\n"
            "@overload\n"
            "def identity(value: int) -> int: ...\n"
            "@overload\n"
            "def identity(value: str) -> str: ...\n"
            "def identity(value: int | str) -> int | str:\n"
            "    return value\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (project / "py.typed").write_bytes(b"")
        gate = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)
        tm.that(any(issue.code == "ban-stub-file" for issue in gate.issues), eq=False)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                project, fix=False, selection=("ban-stub-file",)
            )
        )
        tm.that(report.findings, eq=0)

    def test_unmanaged_git_submodule_does_not_hide_owned_sibling(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Git excludes its foreign subtree while the sibling stays enforced."""
        project = self._project(tmp_path, installed_dependency_path)
        declaration = u.Tests.declare_workspace_projects(
            project,
            ("src/vendor",),
        )
        tm.ok(
            u.Cli.run_checked(
                (
                    "git",
                    "config",
                    "--file",
                    str(declaration),
                    f"submodule.src/vendor.{c.Infra.GITMODULE_MANAGED_KEY}",
                    c.ParserBooleanToken.FALSE,
                ),
                cwd=project,
            ),
        )
        vendor = project / "src" / "vendor"
        vendor.mkdir()
        (vendor / "subject.py").write_text("second(1)\n", encoding="utf-8")
        (project / "src" / "vendor_owned.py").write_text(
            "second(2)\n",
            encoding="utf-8",
        )

        execution = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)

        tm.fail(execution.result.passed)
        findings = tuple(
            issue for issue in execution.issues if issue.code == "contract-second"
        )
        tm.that(len(findings), eq=1)
        tm.ok(findings[0].file.endswith("src/vendor_owned.py"))

    def test_check_files_uses_every_rule_and_only_requested_files(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """Test check files uses every rule and only requested files."""
        project = self._project(tmp_path, installed_dependency_path)
        selected = project / "src" / "selected.py"
        selected.write_text("second(1)\n", encoding="utf-8")
        other = project / "src" / "other.py"
        other.write_text("second(2)\n", encoding="utf-8")

        execution = FlextInfraCodemodGate(tmp_path).check_files(
            (selected,),
            project,
            u.Tests.gate_context(tmp_path),
        )

        tm.fail(execution.result.passed)
        policy_findings = tuple(
            issue for issue in execution.issues if issue.code == "contract-second"
        )
        tm.that(len(policy_findings), eq=1, msg=execution.raw_output)
        tm.ok(policy_findings[0].file.endswith("src/selected.py"))

    def test_missing_requested_file_cannot_be_deselected(
        self, tmp_path: Path, installed_dependency_path: Path
    ) -> None:
        """Test missing requested file cannot be deselected."""
        project = self._project(tmp_path, installed_dependency_path)
        missing = project / "src" / "missing.py"
        gate = FlextInfraCodemodGate(tmp_path)
        context = u.Tests.gate_context(tmp_path)

        with pytest.raises(FileNotFoundError):
            gate.check_files((missing,), project, context)

    @pytest.mark.parametrize("finding", [False, True])
    def test_public_file_check_reuses_elected_scanner_scope(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        *,
        finding: bool,
    ) -> None:
        """Public check uses the native configured scanner for exactly one file."""
        project = self._project(tmp_path, installed_dependency_path)
        source_root = project / config.Infra.source_scan.roots[0]
        source_root.mkdir(exist_ok=True)
        selected = source_root / "literal.py"
        selected.write_text("second(1)\n" if finding else "", encoding="utf-8")
        sibling = source_root / "other.py"
        sibling.write_text("second(2)\n", encoding="utf-8")
        before = (selected.read_bytes(), sibling.read_bytes())
        reports = tmp_path / "reports"
        code = FlextInfraCli.infra_main([
            "check",
            "run",
            "--repository-root",
            str(project),
            "--file",
            str(selected.relative_to(project)),
            "--gates",
            "codemod",
            "--reports-dir",
            str(reports),
        ])
        tm.that(code, eq=1 if finding else 0)
        # Each invocation owns one report directory below the base.
        (report_path,) = reports.glob(f"*/{c.Infra.CHECK_REPORT_SARIF_FILENAME}")
        findings = tm.ok(
            u.Infra.check_report_findings(project, reports_dir=report_path.parent),
        )
        # The bundled policy rules also scan the selected file; the fixture
        # rule proves the scope, because the unselected sibling matches it too.
        tm.that(
            [row.rule_id for row in findings].count("contract-second"),
            eq=1 if finding else 0,
        )
        tm.that((selected.read_bytes(), sibling.read_bytes()), eq=before)

    @pytest.mark.parametrize("severity", ["error", "warning", "info", "hint"])
    def test_workspace_pipeline_fails_the_project_on_policy_findings(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        severity: str,
    ) -> None:
        """The public check facade fails the project on any rule finding.

        The gate line, the report row and the SARIF run carry the same finding
        that fails the gate, whatever its native severity.
        """
        project = self._project(tmp_path, installed_dependency_path, severity=severity)
        (project / "src" / "subject.py").write_text("second(1)\n", encoding="utf-8")
        reports = tmp_path / "reports"

        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                [project.relative_to(tmp_path).as_posix()],
                ["codemod"],
                u.Tests.gate_context(tmp_path, reports),
            ),
        )

        result = results[0]
        tm.fail(result.passed)
        receipt = result.gates["codemod"].raw_receipt
        if receipt is None:
            msg = "A failed codemod gate must retain its native receipt"
            tm.reject(msg)
        reports = receipt.parents[len(project.relative_to(tmp_path).parts)]
        markdown = (reports / c.Infra.CHECK_REPORT_MARKDOWN_FILENAME).read_text(
            encoding="utf-8",
        )
        tm.that(markdown, has=f"| {project.name} | FAIL |")
        tm.that(markdown, has="contract-second")
        sarif = m.Infra.SarifReport.model_validate_json(
            (reports / c.Infra.CHECK_REPORT_SARIF_FILENAME).read_text(encoding="utf-8"),
        )
        observed = tuple(
            finding
            for run in sarif.runs
            for finding in run.results
            if finding.rule_id == "contract-second"
        )
        tm.that(len(observed), eq=1)
        tm.that(observed[0].message, has="Observed second")

    def test_invalid_rule_is_a_native_failure(
        self, tmp_path: Path, installed_dependency_path: Path
    ) -> None:
        """Test invalid rule is a native failure."""
        project = self._project(tmp_path, installed_dependency_path)
        rules = (project / c.Infra.CODEMOD_CONFIG_RELPATH).parent / c.Cli.RULES_DIR_NAME
        (rules / "second.yml").write_text(
            "id: contract-second\nlanguage: invalid-language\n"
            "rule:\n  pattern: second($VALUE)\n",
            encoding="utf-8",
        )
        (project / "src" / "subject.py").write_text("second(1)\n", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)

        tm.fail(execution.result.passed)
        tm.that(
            any(issue.code == c.Infra.ToolOutcome.ERROR for issue in execution.issues),
            eq=True,
        )
        # The native ast-grep diagnostic names the rule file it cannot parse;
        # its wording for the bad field is the tool's, not this contract's.
        tm.that(execution.raw_output, has="Cannot parse rule")
        tm.that(execution.raw_output, has="second.yml")

    def test_native_traversal_error_cannot_be_hidden_by_a_policy_finding(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
    ) -> None:
        """A partial walk remains red even when another file has an error match."""
        project = self._project(tmp_path, installed_dependency_path)
        (project / "src" / "subject.py").write_text("second(1)\n", encoding="utf-8")
        blocked = project / "src" / "unreadable"
        blocked.mkdir()
        (blocked / "hidden.py").write_text("second(2)\n", encoding="utf-8")
        original_mode = blocked.stat().st_mode
        blocked.chmod(0)
        try:
            with pytest.raises(PermissionError):
                tuple(blocked.iterdir())
            with pytest.raises(PermissionError):
                u.Tests.run_gate_check(FlextInfraCodemodGate, tmp_path, project)
        finally:
            blocked.chmod(original_mode)

    @staticmethod
    @pytest.mark.parametrize("payload", ["", "[", "{}", "[{}]", "[null]"])
    def test_native_json_contract_rejects_malformed_output(payload: str) -> None:
        """An empty stream or malformed finding cannot be a clean native scan."""
        with pytest.raises(m.ValidationError):
            m.Infra.AstGrepReport.model_validate_json(payload)

    @staticmethod
    @pytest.mark.parametrize("severity", c.Infra.NativeRuleSeverity)
    def test_native_severity_preserves_wire_literals(
        severity: c.Infra.NativeRuleSeverity,
    ) -> None:
        """Native strings validate to the domain while JSON keeps native values."""
        payload = (
            '[{"file":"subject.py","ruleId":"native-wire","severity":"'
            + severity.value
            + '","message":"match","text":"x","lines":"x",'
            '"range":{"start":{"line":0,"column":0},'
            '"end":{"line":0,"column":1},"byteOffset":{"start":0,"end":1}}}]'
        )
        report = m.Infra.AstGrepReport.model_validate_json(payload)
        diagnostic = report.root[0]
        tm.that(diagnostic.severity, eq=severity.value)
        tm.that(type(diagnostic.severity), eq=str)
        tm.that(diagnostic.model_dump(mode="json")["severity"], eq=severity.value)
        for mode in ("python", "json"):
            with pytest.raises(m.ValidationError, match="is_instance_of"):
                m.Infra.AstGrepDiagnostic.model_validate(
                    diagnostic.model_dump(mode=mode)
                )
        tm.that(
            m.Infra.AstGrepDiagnostic.model_validate(diagnostic) is diagnostic,
            eq=True,
        )
        tm.that(
            m.Infra.AstGrepDiagnostic.model_validate({
                **diagnostic.model_dump(),
                "severity": severity,
            }).severity,
            eq=diagnostic.severity,
        )

    @staticmethod
    @pytest.mark.parametrize("severity", ["fatal", "ERROR", "", b"error"])
    def test_native_severity_rejects_non_wire_values(severity: str | bytes) -> None:
        """Unknown values and Python bytes retain literal rejection semantics."""
        with pytest.raises(m.ValidationError):
            m.Infra.AstGrepDiagnostic.model_validate({
                "file": "subject.py",
                "ruleId": "native-wire",
                "severity": severity,
                "message": "match",
                "text": "x",
                "lines": "x",
                "range": {
                    "start": {"line": 0, "column": 0},
                    "end": {"line": 0, "column": 1},
                    "byteOffset": {"start": 0, "end": 1},
                },
            })
