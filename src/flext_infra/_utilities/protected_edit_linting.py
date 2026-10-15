"""Lint snapshot support for protected edit workflows.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import concurrent.futures
import difflib
import os
import sys
import traceback
from collections import Counter
from collections.abc import Iterable, MutableMapping
from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import libcst as cst
from flext_cli import u
from libcst.codemod import CodemodContext
from libcst.codemod.visitors import RemoveImportsVisitor

from flext_infra import c, config, m, r, t
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.process import FlextInfraUtilitiesProcess
from flext_infra._utilities.resource_limits import FlextInfraUtilitiesResourceLimits

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesProtectedEditLinting:
    """Shared linting and path helpers for protected edit workflows."""

    @classmethod
    def normalize_source(
        cls,
        repository_root: Path,
        path: Path,
        source: str,
        *,
        before_source: str | None = None,
    ) -> p.Result[str]:
        """Normalize candidate imports and format with the destination's policy.

        Returns:
            Normalized source, or the original Ruff subprocess failure.

        """
        executable = cls._workspace_tool_command(c.Infra.RUFF)[0]
        project_root = cls._command_cwd(path, repository_root)
        if before_source is not None:
            source = cls.remove_orphaned_imports(before_source, source)
        checked = u.Cli.run(
            [
                executable,
                "check",
                *config.Infra.codegen.make.ruff.lint_fix,
                "--select",
                "I,W",
                "--stdin-filename",
                str(path),
                "-",
            ],
            cwd=project_root,
            options=m.Cli.ProcessOptions(
                input_data=source,
                env=cls._command_env(),
                remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
            ),
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        return checked.flat_map(
            lambda output: u.Cli.run(
                [
                    executable,
                    "format",
                    *config.Infra.codegen.make.ruff.format_apply,
                    "--stdin-filename",
                    str(path),
                    "-",
                ],
                cwd=project_root,
                options=m.Cli.ProcessOptions(
                    input_data=output.stdout,
                    env=cls._command_env(),
                    remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                ),
                timeout=c.Infra.TIMEOUT_SHORT,
            ).map(lambda formatted: formatted.stdout),
        )

    @staticmethod
    def remove_orphaned_imports(original: str, proposed: str) -> str:
        """Remove only imports whose last executable use the transformation removed.

        Returns:
            The candidate retaining existing unused, string, and exported bindings.

        """
        before = ast.parse(original)
        after = ast.parse(proposed)
        lost = {
            item.id
            for item in ast.walk(before)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        } - {
            item.id
            for item in ast.walk(after)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        }
        strings = tuple(
            item.value
            for item in ast.walk(after)
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
        lost = {name for name in lost if not any(name in value for value in strings)}
        context = CodemodContext()
        for imported in ast.walk(after):
            if not isinstance(imported, ast.Import | ast.ImportFrom):
                continue
            for alias in imported.names:
                if (alias.asname or alias.name.split(".")[0]) not in lost:
                    continue
                module = (
                    "." * imported.level + (imported.module or "")
                    if isinstance(imported, ast.ImportFrom)
                    else alias.name
                )
                RemoveImportsVisitor.remove_unused_import(
                    context,
                    module,
                    alias.name if isinstance(imported, ast.ImportFrom) else None,
                    alias.asname,
                )
        return (
            RemoveImportsVisitor(context)
            .transform_module(
                cst.parse_module(proposed),
            )
            .code
        )

    @classmethod
    def normalize_touched_files(
        cls,
        paths: Iterable[Path],
        repository_root: Path,
    ) -> None:
        """Normalize published imports and whitespace with each destination's policy.

        Published files retain unused imports: the removal planner owns their
        removal, not this formatting pass.

        Raises:
            RuntimeError: If a Ruff subprocess rejects the touched files.

        """
        grouped: MutableMapping[Path, list[str]] = {}
        for path in sorted({path.resolve() for path in paths if path.is_file()}):
            grouped.setdefault(cls._command_cwd(path, repository_root), []).append(
                str(path)
            )
        if not grouped:
            return
        executable = cls._workspace_tool_command(c.Infra.RUFF)[0]
        for project_root, existing in grouped.items():
            for arguments in (
                (
                    "check",
                    *config.Infra.codegen.make.ruff.lint_fix,
                    "--select",
                    "I,W",
                ),
                ("format", *config.Infra.codegen.make.ruff.format_apply),
            ):
                result = u.Cli.run_checked(
                    [executable, *arguments, *existing],
                    cwd=project_root,
                    options=m.Cli.ProcessOptions(
                        env=cls._command_env(),
                        remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                    ),
                    timeout=c.Infra.TIMEOUT_SHORT,
                )
                if result.failure:
                    msg = (
                        f"ruff {arguments[0]} failed for touched files: "
                        f"{result.error}; files={existing!r}"
                    )
                    raise RuntimeError(msg)

    @staticmethod
    def unified_diff_lines(
        before: str,
        after: str,
        *,
        fromfile: str,
        tofile: str,
        max_lines: int,
    ) -> t.StrSequence:
        """Return a bounded unified diff without materializing omitted lines.

        Returns:
            A bounded unified diff without materializing omitted lines.

        Raises:
            ValueError: If max_lines must be positive.

        """
        if max_lines < 1:
            msg = "max_lines must be positive"
            raise ValueError(msg)
        return tuple(
            islice(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=fromfile,
                    tofile=tofile,
                    n=3,
                ),
                max_lines,
            ),
        )

    @staticmethod
    def _workspace_tool_command(tool_name: str) -> t.StrSequence:
        """Resolve one fleet lint tool from the active runtime environment.

        The gate protects edits with the fleet's own tools, so it resolves
        them from the interpreter running the pipeline — never from the lint
        target, whose environment may not exist (a census target is an
        arbitrary repository, not necessarily a provisioned workspace).

        Returns:
            The resulting ``t.StrSequence``.

        Raises:
            FileNotFoundError: If the active environment lacks the tool.

        """
        environment = Path(sys.executable).parent
        executable = tool_name + (".exe" if os.name == "nt" else "")
        tool_path = environment / executable
        if not tool_path.is_file():
            msg = f"active runtime environment tool is missing: {tool_path}"
            raise FileNotFoundError(msg)
        return (str(tool_path),)

    @staticmethod
    def _normalize_lint_line(line: str) -> str:
        """Normalize lint line.

        Returns:
            The resulting ``str``.

        """
        if c.Infra.CODE_FRAME_RE.match(line) or c.Infra.CODE_FRAME_BODY_RE.match(line):
            return ""

        def normalize_unused_import(match: t.RegexMatch) -> str:
            imported_name = match.group(1).rsplit(".", maxsplit=1)[-1]
            return f"`{imported_name}` imported but unused"

        normalized_line: str = c.Infra.LINE_COL_RE.sub("", line)
        # The comparison pairs one logical file's before and after snapshots,
        # whose linted locations differ (live path vs staged source-view path):
        # the leading file-path token normalizes away so only the diagnostic
        # content itself can differ.
        head, separator, remainder = normalized_line.partition(" ")
        if separator and "/" in head:
            normalized_line = remainder
        normalized_without_unused_imports: str = c.Infra.UNUSED_IMPORT_RE.sub(
            normalize_unused_import,
            normalized_line,
        )
        if c.Infra.LINT_SUMMARY_RE.match(normalized_without_unused_imports):
            return ""
        return normalized_without_unused_imports.strip()

    @staticmethod
    def snapshot_lint_gates() -> t.StrSequence:
        """Return the lint gates a protected edit validates its snapshots with.

        One owner: ``make.check_gates_ci`` (config) — the active budgeted gate set
        whose strict complement is the slow whole-program checkers owned by
        ``make check CI=N``. A per-file snapshot validator never runs those.

        Returns:
            The lint gates a protected edit validates its snapshots with.

        """
        lint_tool_gates = {
            "lint" if entry[0] == "ruff" else entry[0] for entry in c.Infra.LINT_TOOLS
        }
        return tuple(
            gate
            for gate in config.Infra.codegen.make.check_gates_ci
            if gate in lint_tool_gates
        )

    @staticmethod
    def _selected_lint_tools(
        gates: t.StrSequence | None = None,
    ) -> t.StrSequencePairTuple:
        """Return the lint tools for the requested gates (SSOT gates when omitted).

        Returns:
            The lint tools for the requested gates (SSOT gates when omitted).

        Raises:
            ValueError: If lint snapshot gates select no lint tool.

        """
        requested = tuple(
            gate.strip().lower() for gate in (gates or ()) if gate.strip()
        )
        gate_names = set(
            requested or FlextInfraUtilitiesProtectedEditLinting.snapshot_lint_gates(),
        )
        selected = tuple(
            entry
            for entry in c.Infra.LINT_TOOLS
            if gate_names.intersection({
                "lint" if entry[0] == "ruff" else entry[0],
                entry[0],
            })
        )
        if not selected:
            msg = (
                "lint snapshot gates select no lint tool: "
                f"{sorted(gate_names)} (tools: "
                f"{', '.join(entry[0] for entry in c.Infra.LINT_TOOLS)})"
            )
            raise ValueError(msg)
        return selected

    @classmethod
    def selected_lint_tool_names(
        cls,
        gates: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Return the canonical lint tool names selected for a gate set.

        Returns:
            The canonical lint tool names selected for a gate set.

        """
        return tuple(entry[0] for entry in cls._selected_lint_tools(gates))

    @classmethod
    def ruff_fix_files(cls, paths: t.SequenceOf[Path], workspace: Path) -> None:
        """Run ``ruff check --fix`` on *paths* with snapshot-identical resolution.

        Same venv-resolved binary and same working directory as the lint
        snapshots, so the fix pass and the before/after diff always resolve
        the SAME Ruff configuration for the same file.

        Raises:
            RuntimeError: If ruff normalization failed for.

        """
        for py_file in paths:
            output = u.Cli.run_raw(
                [
                    *cls._workspace_tool_command("ruff"),
                    c.Infra.CHECK,
                    "--fix",
                    str(py_file),
                ],
                cwd=cls._command_cwd(py_file, workspace),
                options=m.Cli.ProcessOptions(
                    env=cls._command_env(),
                    remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                ),
                timeout=c.Infra.TIMEOUT_SHORT,
            ).unwrap()
            outcome = output.outcome
            # Ruff's exit 1 means remaining findings, which the delta judge owns.
            findings_remain = (
                outcome.raw_return_code == 1
                and not outcome.timed_out
                and outcome.forwarded_signal is None
            )
            if not u.Cli.process_succeeded(outcome) and not findings_remain:
                detail = (output.stderr or output.stdout).strip()
                msg = (
                    f"ruff normalization failed for {py_file}: "
                    f"exit={outcome.raw_return_code}, timed_out={outcome.timed_out}, "
                    f"signal={outcome.forwarded_signal}: {detail}"
                )
                raise RuntimeError(msg)

    @staticmethod
    def _relative_path(py_file: Path, workspace: Path) -> Path:
        """Return ``py_file`` relative to the workspace when it lies inside it.

        Returns:
            ``py_file`` relative to the workspace when it lies inside it.

        """
        if py_file.is_relative_to(workspace):
            return py_file.relative_to(workspace)
        return py_file

    @staticmethod
    def _command_cwd(py_file: Path, workspace: Path) -> Path:
        """Command cwd.

        Returns:
            The resulting ``Path``.

        """
        resolved_workspace = workspace.resolve()
        project_root: Path | None = FlextInfraUtilitiesDiscovery.project_root(py_file)
        if project_root is None:
            return resolved_workspace
        return project_root

    _COMMAND_ENV_REMOVE_KEYS: ClassVar[t.StrSequence] = (
        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH,
        c.Infra.ENV_VAR_FORCE_COLOR,
    )

    @staticmethod
    def _command_env() -> t.StrMapping:
        """Return subprocess env overrides for lint and validation commands.

        ``run_raw`` merges this mapping over ``os.environ``, so keys can only be
        dropped by passing ``_COMMAND_ENV_REMOVE_KEYS`` as ``remove_env_keys``.

        Returns:
            Subprocess env overrides for lint and validation commands.

        """
        return {c.Infra.ORCHESTRATOR_ENV_NO_COLOR: "1"}

    @classmethod
    def _lint_command(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        command_cwd: Path,
        tool_name: str,
        template: t.StrSequence,
    ) -> t.StrSequence:
        """Build one canonical protected-edit lint command.

        Returns:
            The resulting ``t.StrSequence``.

        """
        if tool_name == c.Infra.MYPY:
            return FlextInfraUtilitiesResourceLimits.mypy_limited_command(
                m.Infra.MypyInvocation(
                    targets=(py_file.resolve(),),
                    workspace=workspace,
                    report_json=True,
                ),
            )
        command: t.StrSequence = (
            *cls._workspace_tool_command(template[0]),
            *(item.replace("{file}", str(py_file)) for item in template[1:]),
        )
        if tool_name == c.Infra.RUFF:
            command = (*command, "--output-format", c.Infra.OUTPUT_JSON)
        elif tool_name == c.Infra.PYRIGHT:
            command = (*command, "--outputjson")
        elif tool_name == c.Infra.PYREFLY:
            command = (
                *command,
                "--output-format",
                c.Infra.OUTPUT_JSON,
                "-o",
                "-",
                "--summary=none",
            )
        if (
            tool_name == c.Infra.PYREFLY
            and (project_config := command_cwd / c.PYPROJECT_FILENAME).is_file()
        ):
            command = (*command, "--config", str(project_config))
        return command

    @classmethod
    def lint_commands(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> t.StrSequencePairTuple:
        """Return the exact public command plan used by protected linting.

        Returns:
            The exact public command plan used by protected linting.

        """
        command_cwd = cls._command_cwd(py_file, workspace)
        return tuple(
            (
                entry[0],
                cls._lint_command(
                    py_file,
                    workspace,
                    command_cwd=command_cwd,
                    tool_name=entry[0],
                    template=entry[1],
                ),
            )
            for entry in cls._selected_lint_tools(gates)
        )

    @classmethod
    def _execute_selected_lint_tools(
        cls,
        py_file: Path,
        workspace: Path,
        selected_tools: t.StrSequencePairTuple,
    ) -> t.Infra.LintSnapshot[m.Infra.LintGateResult]:
        """Execute selected lint tools.

        Returns:
            The resulting ``t.Infra.LintSnapshot``.

        """
        # Every gate is an independent subprocess -- _run_lint_gate
        # builds its own command and returns a value, touching no shared state.
        # Running any one of them ahead of the pool made a snapshot cost that
        # gate's full wall clock PLUS the slowest of the rest, instead of just
        # the slowest. Measured: 8 snapshots x 4 gates at 0.297s each.
        results: list[m.Infra.LintGateResult] = []
        if not selected_tools:
            return cls._lint_snapshot_from_results(())

        # The pool waits for the slowest DECLARED gate deadline (mypy owns a
        # resource-limited deadline of its own); a shorter pool budget cut the
        # gate short and reported the cut as lint errors, reverting valid edits.
        timeout_budget = (
            max(cls._gate_deadline(entry[0]) for entry in selected_tools) + 10
        )
        pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(
                1, min(config.Infra.codegen.lint_snapshot_workers, len(selected_tools))
            ),
        )
        futures_by_tool = {
            pool.submit(
                cls._run_lint_gate,
                py_file=py_file,
                workspace=workspace,
                tool_name=entry[0],
                template=entry[1],
            ): entry[0]
            for entry in selected_tools
        }
        try:
            done, not_done = concurrent.futures.wait(
                tuple(futures_by_tool),
                timeout=timeout_budget,
            )
            results.extend(
                future.result() for future in futures_by_tool if future in done
            )
            for future in not_done:
                tool_name = futures_by_tool[future]
                _ = future.cancel()
                results.append(
                    m.Infra.LintGateResult(
                        tool_name=tool_name,
                        execution_error=(
                            f"timeout {timeout_budget}s: lint gate "
                            f"'{tool_name}' did not finish; native outcome unavailable"
                        ),
                    ),
                )
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        return cls._lint_snapshot_from_results(tuple(results))

    @staticmethod
    def _gate_deadline(tool_name: str) -> int:
        """Return the one declared deadline for a lint gate subprocess.

        Returns:
            The one declared deadline for a lint gate subprocess.

        """
        if tool_name == c.Infra.MYPY:
            return FlextInfraUtilitiesResourceLimits.mypy_runner_timeout()
        return max(5, min(15, c.Infra.TIMEOUT_SHORT))

    @classmethod
    def _run_lint_gate(
        cls,
        *,
        py_file: Path,
        workspace: Path,
        tool_name: str,
        template: t.StrSequence,
        source: str | None = None,
    ) -> m.Infra.LintGateResult:
        """Run one lint gate and return a validated result model.

        Returns:
            The resulting ``m.Infra.LintGateResult``.

        """
        command_cwd = cls._command_cwd(py_file, workspace)
        cmd = cls._lint_command(
            py_file,
            workspace,
            command_cwd=command_cwd,
            tool_name=tool_name,
            template=template,
        )
        if source is not None:
            cmd = (
                *tuple(item for item in cmd if item != str(py_file)),
                "--stdin-filename",
                str(py_file),
                "-",
            )
        environment = dict(cls._command_env())
        if tool_name == c.Infra.RUFF:
            environment[c.Infra.RUFF_CACHE_ENVIRONMENT_VARIABLE] = str(
                FlextInfraUtilitiesResourceLimits.ruff_cache_directory(command_cwd)
            )
        run_result = u.Cli.run_raw(
            cmd,
            cwd=command_cwd,
            options=m.Cli.ProcessOptions(
                env=environment,
                remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                input_data=source,
            ),
            timeout=cls._gate_deadline(tool_name),
        )
        return cls.lint_gate_result(tool_name, run_result)

    @staticmethod
    def lint_gate_result(
        tool_name: str,
        executed: p.Result[p.Cli.CommandOutput],
    ) -> m.Infra.LintGateResult:
        """Retain the native receipt without turning an absent report into success.

        Returns:
            Diagnostic evidence and the independent first execution failure.

        """
        if executed.failure:
            return m.Infra.LintGateResult(
                tool_name=tool_name,
                execution_error=str(executed.error),
                error_code=executed.error_code,
                error_data=executed.error_data,
                error_traceback=(
                    "".join(traceback.format_exception(executed.exception))
                    if executed.exception is not None
                    else None
                ),
            )
        output = m.Cli.CommandOutput.model_validate(
            executed.value, from_attributes=True
        )
        parsed = FlextInfraUtilitiesProtectedEditLinting._lint_report_errors(
            tool_name, output.stdout
        )
        lines = parsed.value if parsed.success else ()
        classification = FlextInfraUtilitiesProcess.tool_outcome(
            output.outcome,
            findings=len(lines),
            findings_exit_codes=(
                config.Infra.tooling.tools.ruff.findings_exit_codes
                if tool_name == c.Infra.RUFF
                else (c.Cli.EXIT_CODE_FAILURE,)
            ),
        )
        resource_error = (
            FlextInfraUtilitiesResourceLimits.mypy_failure_diagnostic(output)
            if tool_name == c.Infra.MYPY
            else None
        )
        failure = resource_error
        if classification is c.Infra.ToolOutcome.ERROR:
            failure = failure or (
                f"{tool_name} execution failed: "
                f"exit={output.outcome.raw_return_code}, "
                f"timed_out={output.outcome.timed_out}, "
                f"forwarded_signal={output.outcome.forwarded_signal}: "
                f"{(output.stderr or output.stdout).strip()}"
            )
        failure = failure or (str(parsed.error) if parsed.failure else None)
        return m.Infra.LintGateResult(
            tool_name=tool_name,
            errors=lines,
            output=output,
            execution_error=failure,
        )

    @classmethod
    def _lint_report_errors(
        cls, tool_name: str, source: str
    ) -> p.Result[t.StrSequence]:
        """Validate the selected tool's native machine report before counting findings.

        Returns:
            Complete diagnostic lines, or the original malformed-report failure.

        """
        result = r[t.StrSequence]
        if tool_name == c.Infra.MYPY:
            return cls._mypy_report_errors(source)
        if tool_name == c.Infra.PYRIGHT:
            report = u.validate_value(
                m.Infra.PyrightReport, source, from_json=True, strict=True
            )
            return report.flat_map(
                lambda observed: (
                    result.ok(
                        tuple(
                            f"{entry.file}:"
                            f"{entry.range.start.line + 1 if entry.range else 0}:"
                            f"{entry.range.start.character + 1 if entry.range else 0}: "
                            f"{entry.severity}: {entry.message} [{entry.rule or ''}]"
                            for entry in observed.general_diagnostics
                            if entry.severity in {"error", "warning"}
                        )
                    )
                    if observed.summary.files_analyzed
                    else result.fail(
                        "pyright analyzed no files for the selected source"
                    )
                )
            )
        if tool_name == c.Infra.PYREFLY:
            pyrefly = u.validate_value(
                m.Infra.PyreflyReport, source, from_json=True, strict=True
            )
            return pyrefly.map(
                lambda observed: tuple(
                    f"{entry.path}:{entry.line}:{entry.column}: "
                    f"{entry.severity}: {entry.description} [{entry.name}]"
                    for entry in observed.errors
                    if entry.severity in {"error", "warn"}
                )
            )
        if tool_name != c.Infra.RUFF:
            return result.fail(f"unsupported lint report contract: {tool_name}")
        return cls._ruff_report_errors(source)

    @staticmethod
    def _mypy_report_errors(source: str) -> p.Result[t.StrSequence]:
        """Validate every native JSON-lines diagnostic, retaining hints and failures.

        Returns:
            Complete diagnostic lines, or the original malformed-report failure.

        """
        result = r[t.StrSequence]
        lines: list[str] = []
        for line in filter(str.strip, source.splitlines()):
            diagnostic = u.validate_value(
                m.Infra.MypyDiagnostic, line, from_json=True, strict=True
            )
            if diagnostic.failure:
                return result.from_failure(diagnostic)
            entry = diagnostic.value
            if entry.severity != "error":
                continue
            lines.append(
                f"{entry.file}:{entry.line}:{entry.column}: "
                f"{entry.severity}: {entry.message} [{entry.code or ''}]"
                + (f"\n{entry.hint}" if entry.hint else "")
            )
        return result.ok(tuple(lines))

    @staticmethod
    def _ruff_report_errors(source: str) -> p.Result[t.StrSequence]:
        """Validate Ruff's complete native finding list before projecting diagnostics.

        Returns:
            Complete diagnostic lines, or the original malformed-report failure.

        """
        result = r[t.StrSequence]
        loaded = u.Cli.json_parse(source)
        if loaded.failure or not isinstance(loaded.value, list):
            return (
                result.from_failure(loaded)
                if loaded.failure
                else result.fail("Ruff JSON report is not a list of findings")
            )
        errors: list[str] = []
        for finding in loaded.value:
            if not isinstance(finding, dict):
                return result.fail("Ruff JSON finding is not an object")
            location = finding.get("location")
            if not isinstance(location, dict):
                return result.fail("Ruff JSON finding lacks its native location")
            issue = u.validate_value(
                m.Infra.Issue,
                {
                    "file": finding.get("filename"),
                    "line": location.get("row"),
                    "column": location.get("column"),
                    "code": finding.get("code"),
                    "message": finding.get("message"),
                },
                strict=True,
            )
            if issue.failure:
                return result.from_failure(issue)
            if (
                not issue.value.file.strip()
                or not issue.value.code.strip()
                or not issue.value.message.strip()
                or issue.value.line < 1
                or issue.value.column < 1
            ):
                return result.fail(
                    "Ruff JSON finding has invalid native diagnostic fields"
                )
            errors.append(issue.value.formatted)
        return result.ok(tuple(errors))

    @staticmethod
    def lint_execution_errors(
        snapshot: t.Infra.LintSnapshot[m.Infra.LintGateResult],
    ) -> t.StrSequence:
        """Return execution failures independently of diagnostic occurrence deltas.

        Returns:
            Every native execution failure in declared tool order.

        """
        return tuple(
            result.execution_error
            for result in snapshot.values()
            if result.execution_error is not None
        )

    @staticmethod
    def _lint_snapshot_from_results(
        results: t.SequenceOf[m.Infra.LintGateResult],
    ) -> t.Infra.LintSnapshot[m.Infra.LintGateResult]:
        """Convert validated lint gate results into the public snapshot contract.

        Returns:
            The resulting ``t.Infra.LintSnapshot``.

        """
        return {result.tool_name: result for result in results}

    @classmethod
    def lint_snapshot(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
        source: str | None = None,
    ) -> t.Infra.LintSnapshot[m.Infra.LintGateResult]:
        """Run selected tools, or uncached Ruff on candidate source at *py_file*.

        Candidate stdin retains the destination's filename and configuration;
        it never materializes the proposed bytes on the live filesystem.
        Every call observes the native tool again. A file hash cannot authenticate
        configuration, runtime or imported dependency changes; only the native
        checker owns reuse of its complete analysis inputs.

        Returns:
            The resulting ``t.Infra.LintSnapshot``.

        Raises:
            ValueError: If source snapshots select a tool other than Ruff.

        """
        selected_tools = cls._selected_lint_tools(gates)
        if source is not None:
            if tuple(entry[0] for entry in selected_tools) != (c.Infra.RUFF,):
                msg = "source lint snapshots require the Ruff lint gate"
                raise ValueError(msg)
            return cls._lint_snapshot_from_results((
                cls._run_lint_gate(
                    py_file=py_file,
                    workspace=workspace,
                    tool_name=selected_tools[0][0],
                    template=selected_tools[0][1],
                    source=source,
                ),
            ))
        return cls._execute_selected_lint_tools(
            py_file=py_file,
            workspace=workspace,
            selected_tools=selected_tools,
        )

    @classmethod
    def lint_snapshots(
        cls,
        paths: t.SequenceOf[Path],
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> MutableMapping[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]]:
        """Validate files in order while each file runs its tools concurrently.

        Returns:
            The resulting ``MutableMapping[Path, t.Infra.LintSnapshot]``.

        """
        ordered_paths = tuple(paths)
        if not ordered_paths:
            return {}
        if len(ordered_paths) == 1:
            path = ordered_paths[0]
            return {path: cls.lint_snapshot(path, workspace, gates=gates)}

        snapshots_by_path: MutableMapping[
            Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]
        ] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(
                1, min(config.Infra.codegen.lint_snapshot_workers, len(ordered_paths))
            ),
        ) as pool:
            futures_by_path = {
                pool.submit(cls.lint_snapshot, path, workspace, gates=gates): path
                for path in ordered_paths
            }
            for future in concurrent.futures.as_completed(futures_by_path):
                snapshots_by_path[futures_by_path[future]] = future.result()

        return {path: snapshots_by_path[path] for path in ordered_paths}

    @staticmethod
    def lint_new_errors(
        before: t.Infra.LintSnapshot[m.Infra.LintGateResult],
        after: t.Infra.LintSnapshot[m.Infra.LintGateResult],
    ) -> t.Infra.LintSnapshot[t.StrSequence]:
        """Return introduced diagnostic occurrences, ignoring shifted coordinates.

        Matching consumes each baseline occurrence once; resolving another rule
        never compensates for a new message or an additional identical finding.

        Returns:
            Only lint errors introduced relative to *before*.

        """
        introduced: t.MutableMappingKV[str, t.StrSequence] = {}
        normalize = FlextInfraUtilitiesProtectedEditLinting._normalize_lint_line
        for tool, candidate in after.items():
            baseline = before.get(tool)
            remaining = (
                Counter(normalize(line) for line in baseline.errors)
                if baseline is not None
                else Counter[str]()
            )
            added: list[str] = []
            for line in candidate.errors:
                identity = normalize(line)
                if not identity:
                    continue
                if remaining[identity]:
                    remaining[identity] -= 1
                else:
                    added.append(line)
            if added:
                introduced[tool] = tuple(added)
        return introduced


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditLinting"]
