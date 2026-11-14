"""Public codemod gate evidence against the real ast-grep scanner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from re import escape
from typing import ClassVar, override

from flext_infra import FlextInfraCli, config, r, u as infra_u
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.gates import FlextInfraGatesCodemod
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodemodGate:
    """Block on every policy finding and on every native scanner failure."""

    @staticmethod
    def _project(
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        severity: str = "error",
    ) -> Path:
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        tm.ok(u.Cli.run_checked(["mise", "trust", str(tmp_path / ".mise.toml")]))
        project = installed_dependency_path / "scanner_contract"
        u.Tests.write_native_resolution_project(project, "scanner-contract")
        # The scanned package itself is clean: only each case's own source may
        # produce findings.
        (project / "src" / "scanner_contract" / c.Infra.INIT_PY).write_text(
            "", encoding=c.DEFAULT_ENCODING
        )
        u.Tests.declare_rules(
            project,
            {
                name: (
                    f"id: contract-{name}\nlanguage: Python\nseverity: {severity}\n"
                    f"message: Observed {name}\nrule:\n  pattern: {name}($VALUE)\n"
                )
                for name in ("first", "second")
            },
        )
        # The rule plan reads the target checkout's own runtime, never the
        # invoking interpreter, so the scanned project owns a provisioned one.
        u.Tests.initialize_git_repo(project)
        tm.ok(
            u.Tests.provision_scan_workspace(project, session_runtime=session_runtime)
        )
        return project

    @c.Tests.MARK.parametrize("severity", ["error", "warning", "info", "hint"])
    def test_policy_findings_block_at_every_severity(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        severity: str,
    ) -> None:
        """Test policy findings block at every severity."""
        project = self._project(
            tmp_path, installed_dependency_path, session_runtime, severity=severity
        )
        source = project / "src" / "subject.py"
        source.write_text("\nsecond(1)\n", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)

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
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Test clean native scan has no findings."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        (project / "src" / "subject.py").write_text("", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)

        tm.that(execution.result.passed, eq=True, msg=execution.raw_output)
        tm.that(execution.issues, empty=True)
        tm.that(execution.raw_output, has="exit=0")

    @c.Tests.MARK.parametrize("truncated", [False, True])
    def test_timed_out_scan_reports_every_published_finding(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        truncated: bool,
    ) -> None:
        """Measure the JSON a stopped scan published instead of counting it once.

        A scanner that reaches its deadline after emitting its final
        ``--json=compact`` array must report each published rule/file and the
        true policy-finding total, while the native timeout stays blocking.
        A killed scanner can also leave the array without its closing bracket;
        the complete records before the cut are still the native measurement.
        """
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        diagnostics = tuple(
            m.Infra.AstGrepDiagnostic.model_validate({
                "file": path,
                "ruleId": rule,
                "severity": c.Infra.NativeRuleSeverity.ERROR,
                "message": f"Observed {rule}",
                "text": "call",
                "lines": "call",
                "range": {
                    "start": {"line": 0, "column": 0},
                    "end": {"line": 0, "column": 4},
                    "byteOffset": {"start": 0, "end": 4},
                },
            })
            for path, rule in (
                ("src/first.py", "contract-first"),
                ("src/second.py", "contract-second"),
            )
        )
        payload = tm.ok(
            u.Cli.json_dumps(
                m.Infra.AstGrepReport(root=diagnostics).model_dump(mode="json")
            )
        )

        class _TimedOutScan(infra_u.Cli):
            """A native scan that published its final report before its deadline."""

            published: ClassVar[str] = ""

            @classmethod
            @override
            def run_raw(
                cls,
                cmd: Sequence[str],
                cwd: t.Cli.TextPath | None = None,
                timeout: int | None = None,
                *,
                options: p.Cli.ProcessOptions | None = None,
                capture: bool = True,
                env: Mapping[str, str] | None = None,
                remove_env_keys: Sequence[str] | None = None,
            ) -> p.Result[p.Cli.CommandOutput]:
                _ = cmd, cwd, timeout, options, capture, env, remove_env_keys
                return r[p.Cli.CommandOutput].ok(
                    m.Cli.CommandOutput.model_validate({
                        "stdout": cls.published,
                        "stderr": "",
                        "outcome": m.Cli.ProcessOutcome(
                            raw_return_code=-2,
                            timed_out=True,
                            forwarded_signal=None,
                        ),
                    })
                )

        _TimedOutScan.published = payload.rstrip()[:-1] if truncated else payload
        execution = FlextInfraGatesCodemod(tmp_path, runner=_TimedOutScan).check(
            project, u.Tests.gate_context(tmp_path)
        )

        tm.fail(execution.result.passed)
        published = tuple(
            (issue.code, Path(issue.file).as_posix())
            for issue in execution.issues
            if issue.code.startswith("contract-")
        )
        tm.that(
            published,
            eq=(
                ("contract-first", "src/first.py"),
                ("contract-second", "src/second.py"),
            ),
        )
        tm.that(execution.raw_output, has="2 policy findings; 1 native failures")
        tm.that(
            tuple(
                issue.message
                for issue in execution.issues
                if issue.code == c.Infra.ToolOutcome.ERROR.value
            ),
            eq=("ast-grep exited with code -2: timed_out=True; forwarded_signal=None",),
        )
        tm.ok(execution.raw_receipt is not None)

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
        execution = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
        return sorted(
            (project / issue.file).resolve().relative_to(project.resolve()).as_posix()
            for issue in execution.issues
            if issue.code == rule_id
        )

    def test_flext_tests_import_is_banned_only_in_the_infra_package(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """The project-root scan reports flext_tests only inside flext_infra.

        Premise (operator-ruling-2026-10-08-subprocess-test-imports, item 2):
        the rule fires when flext-infra scans itself (``src/...`` paths), not
        only from the workspace root, and never binds another package.
        """
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """A consumer routes processes through the public execution owner."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        consumer = "src/consumer/spawn.py"
        module = project / consumer
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("import subprocess\n", encoding="utf-8")

        tm.that(
            self._rule_files(project, "ban-subprocess-outside-run-owner", tmp_path),
            eq=[consumer],
        )

    def test_generated_source_tree_is_inside_the_scan(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """A tracked generated-source module reaches the policy scan.

        The ``generated_source`` flag owns tracked generation and the package
        initializer only; it never feeds native source-scan exclusions, so
        owned generated Python is admitted like authored Python.
        """
        names = config.Infra.codegen.generated_sources
        tm.that(names, empty=False)
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        tree = project / "src" / "pkg" / names[0]
        tree.mkdir(parents=True)
        (tree / "wire_pb2.py").write_text("\nsecond(1)\n", encoding="utf-8")
        (project / "src" / "pkg" / "subject.py").write_text("", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)

        tm.fail(execution.result.passed)
        tm.that(
            (f"src/pkg/{names[0]}/wire_pb2.py", "contract-second")
            in {(issue.file, issue.code) for issue in execution.issues},
            eq=True,
        )

    def test_owned_stub_paths_share_mod_and_check_admission(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Empty, invalid, ignored and generated stubs fail without an AST match."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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
        gate = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
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
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Authored exclusions hide ordinary Python, never owned stub policy paths."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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
                gate = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
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

    @c.Tests.MARK.parametrize("target_scope", ["in_tree", "foreign", "broken"])
    def test_stub_symlink_keeps_the_owned_path_name(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        target_scope: str,
    ) -> None:
        """Check observes the stub name; Mod preserves the original physical guard."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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
        gate = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
        tm.that(
            [issue.file for issue in gate.issues if issue.code == "ban-stub-file"],
            eq=[stub.relative_to(project).as_posix()],
        )
        with u.Tests.raises(OSError, match=escape(str(stub))) as original_guard:
            u.Cli.atomic_read_binary_file_state(stub, required=True).unwrap()
        with u.Tests.raises(type(original_guard.value)) as mod_guard:
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
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Protocol, ABC and overload ellipses in .py remain legitimate declarations."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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
        gate = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
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
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Git excludes its foreign subtree while the sibling stays enforced."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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

        execution = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)

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
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Test check files uses every rule and only requested files."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        selected = project / "src" / "selected.py"
        selected.write_text("second(1)\n", encoding="utf-8")
        other = project / "src" / "other.py"
        other.write_text("second(2)\n", encoding="utf-8")

        execution = FlextInfraGatesCodemod(tmp_path).check_files(
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
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Test missing requested file cannot be deselected."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        missing = project / "src" / "missing.py"
        gate = FlextInfraGatesCodemod(tmp_path)
        context = u.Tests.gate_context(tmp_path)

        with u.Tests.raises(FileNotFoundError):
            gate.check_files((missing,), project, context)

    @c.Tests.MARK.parametrize("finding", [False, True])
    def test_public_file_check_reuses_elected_scanner_scope(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        finding: bool,
    ) -> None:
        """Public check uses the native configured scanner for exactly one file."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
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

    @c.Tests.MARK.parametrize("severity", ["error", "warning", "info", "hint"])
    def test_workspace_pipeline_fails_the_project_on_policy_findings(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        severity: str,
    ) -> None:
        """The public check facade fails the project on any rule finding.

        The gate line, the report row and the SARIF run carry the same finding
        that fails the gate, whatever its native severity.
        """
        project = self._project(
            tmp_path, installed_dependency_path, session_runtime, severity=severity
        )
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
        # Reports live at the invocation directory; receipts nest below it.
        (reports,) = tuple(reports.iterdir())
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

    def test_failed_prerequisite_ends_check_before_later_phases(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """A prerequisite finding ends the verb; later gates are not executed."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        (project / "src" / "subject.py").write_text(
            "import os\nsecond(1)\n", encoding="utf-8"
        )

        results = tm.ok(
            FlextInfraWorkspaceChecker(repository_root=tmp_path).run_projects(
                [project.relative_to(tmp_path).as_posix()],
                ["lint", "codemod"],
                u.Tests.gate_context(tmp_path, tmp_path / "reports"),
            ),
        )

        tm.fail(results[0].passed)
        tm.that(set(results[0].gates), eq={"lint"})

    def test_invalid_rule_is_a_native_failure(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """Test invalid rule is a native failure."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        rules = (project / c.Infra.CODEMOD_CONFIG_RELPATH).parent / c.Cli.RULES_DIR_NAME
        (rules / "second.yml").write_text(
            "id: contract-second\nlanguage: invalid-language\n"
            "rule:\n  pattern: second($VALUE)\n",
            encoding="utf-8",
        )
        (project / "src" / "subject.py").write_text("second(1)\n", encoding="utf-8")

        execution = u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)

        tm.fail(execution.result.passed)
        tm.that(
            any(issue.code == c.Infra.ToolOutcome.ERROR for issue in execution.issues),
            eq=True,
        )
        # Authored catalogs are composed into one staged native provider
        # (docs/guides/codemod-rules.md): the native ast-grep diagnostic names
        # the staged bundle and quotes the refused rule document; its wording
        # for the bad field is the tool's, not this contract's.
        tm.that(execution.raw_output, has="Cannot parse rule")
        tm.that(execution.raw_output, has=c.Infra.CODEMOD_NATIVE_RULE_BUNDLE_FILENAME)
        tm.that(execution.raw_output, has="contract-second")

    def test_native_traversal_error_cannot_be_hidden_by_a_policy_finding(
        self,
        tmp_path: Path,
        installed_dependency_path: Path,
        session_runtime: p.Tests.SessionRuntime,
    ) -> None:
        """A partial walk remains red even when another file has an error match."""
        project = self._project(tmp_path, installed_dependency_path, session_runtime)
        (project / "src" / "subject.py").write_text("second(1)\n", encoding="utf-8")
        blocked = project / "src" / "unreadable"
        blocked.mkdir()
        (blocked / "hidden.py").write_text("second(2)\n", encoding="utf-8")
        original_mode = blocked.stat().st_mode
        blocked.chmod(0)
        try:
            with u.Tests.raises(PermissionError):
                tuple(blocked.iterdir())
            with u.Tests.raises(PermissionError):
                u.Tests.run_gate_check(FlextInfraGatesCodemod, tmp_path, project)
        finally:
            blocked.chmod(original_mode)

    @staticmethod
    @c.Tests.MARK.parametrize("payload", ["", "[", "{}", "[{}]", "[null]"])
    def test_native_json_contract_rejects_malformed_output(payload: str) -> None:
        """An empty stream or malformed finding cannot be a clean native scan."""
        with u.Tests.raises(m.ValidationError):
            m.Infra.AstGrepReport.model_validate_json(payload)

    @staticmethod
    @c.Tests.MARK.parametrize("severity", c.Infra.NativeRuleSeverity)
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
        tm.that(diagnostic.severity is severity, eq=True)
        tm.that(type(diagnostic.severity), eq=c.Infra.NativeRuleSeverity)
        tm.that(diagnostic.model_dump()["severity"] is severity, eq=True)
        tm.that(diagnostic.model_dump(mode="json")["severity"], eq=severity.value)
        with u.Tests.raises(m.ValidationError, match="is_instance_of"):
            m.Infra.AstGrepDiagnostic.model_validate(diagnostic.model_dump(mode="json"))
        tm.that(
            m.Infra.AstGrepDiagnostic.model_validate(diagnostic) is diagnostic,
            eq=True,
        )
        tm.that(
            m.Infra.AstGrepDiagnostic.model_validate(diagnostic.model_dump()).severity,
            eq=diagnostic.severity,
        )

    @staticmethod
    @c.Tests.MARK.parametrize("severity", ["fatal", "ERROR", "", b"error"])
    def test_native_severity_rejects_non_wire_values(severity: str | bytes) -> None:
        """Unknown values and Python bytes retain literal rejection semantics."""
        with u.Tests.raises(m.ValidationError):
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
