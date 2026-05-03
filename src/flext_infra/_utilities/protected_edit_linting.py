"""Lint snapshot support for protected edit workflows."""

from __future__ import annotations

import concurrent.futures
import hashlib
from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar

from flext_cli import u
from flext_infra import FlextInfraUtilitiesDiscovery, c, t


class FlextInfraUtilitiesProtectedEditLinting:
    """Shared linting and path helpers for protected edit workflows."""

    _SNAPSHOT_MAX_WORKERS: ClassVar[int] = 4

    @staticmethod
    def _workspace_tool_command(
        workspace: Path,
        tool_name: str,
    ) -> tuple[str, ...]:
        """Resolve one tool against the workspace venv before falling back to PATH."""
        tool_path = (workspace.resolve() / c.Infra.VENV_BIN_REL / tool_name).resolve()
        if tool_path.is_file():
            return (str(tool_path),)
        return (tool_name,)

    @staticmethod
    def _normalize_lint_line(line: str) -> str:
        """Normalize lint line."""
        if c.Infra.CODE_FRAME_RE.match(line) or c.Infra.CODE_FRAME_BODY_RE.match(line):
            return ""
        normalized_line: str = c.Infra.LINE_COL_RE.sub("", line)
        normalized_without_unused_imports: str = c.Infra.UNUSED_IMPORT_RE.sub(
            lambda match: (
                f"`{match.group(1).rsplit('.', maxsplit=1)[-1]}` imported but unused"
            ),
            normalized_line,
        )
        if c.Infra.LINT_SUMMARY_RE.match(normalized_without_unused_imports):
            return ""
        return normalized_without_unused_imports.strip()

    @staticmethod
    def _selected_lint_tools(
        gates: t.StrSequence | None = None,
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Selected lint tools."""
        resolved_gates = gates or tuple(
            gate.strip()
            for gate in c.Infra.SAFE_EXECUTION_DEFAULT_GATES.split(",")
            if gate.strip()
        )
        gate_names = {gate.strip().lower() for gate in resolved_gates if gate.strip()}
        selected = [
            (tool, tmpl)
            for tool, tmpl in c.Infra.LINT_TOOLS
            if gate_names.intersection({"lint" if tool == "ruff" else tool, tool})
        ]
        return tuple(selected) or c.Infra.LINT_TOOLS

    @classmethod
    def selected_lint_tool_names(
        cls,
        gates: t.StrSequence | None = None,
    ) -> t.StrSequence:
        """Return the canonical lint tool names selected for a gate set."""
        return tuple(tool for tool, _ in cls._selected_lint_tools(gates))

    @staticmethod
    def _relative_path(py_file: Path, workspace: Path) -> Path:
        """Relative path."""
        try:
            return py_file.relative_to(workspace)
        except ValueError:
            return py_file

    @staticmethod
    def _command_cwd(py_file: Path, workspace: Path) -> Path:
        """Command cwd."""
        resolved_workspace = workspace.resolve()
        project_root = FlextInfraUtilitiesDiscovery.project_root(
            py_file,
        )
        if project_root is None:
            return resolved_workspace
        try:
            project_root.relative_to(resolved_workspace)
        except ValueError:
            return resolved_workspace
        return project_root

    @staticmethod
    def _command_env() -> t.StrMapping:
        """Command env."""
        return u.Cli.process_env(remove_keys=("PYTHONPATH",))

    @classmethod
    def _new_file_lint_baseline(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.LintSnapshot:
        """New file lint baseline."""
        py_file.parent.mkdir(parents=True, exist_ok=True)
        py_file.write_text(
            f"{c.Infra.FUTURE_ANNOTATIONS}\n",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        try:
            return cls.lint_snapshot(py_file, workspace, gates=gates)
        finally:
            if py_file.exists():
                py_file.unlink()

    _snapshot_cache: ClassVar[
        MutableMapping[tuple[str, str, tuple[str, ...]], t.Infra.LintSnapshot]
    ] = {}

    @classmethod
    def clear_snapshot_cache(cls) -> None:
        """Reset the content-hash keyed lint snapshot cache."""
        cls._snapshot_cache.clear()

    @staticmethod
    def _lint_snapshot_cache_key(
        py_file: Path,
        gate_key: tuple[str, ...],
    ) -> tuple[str, str, tuple[str, ...]] | None:
        """Lint snapshot cache key."""
        try:
            raw_bytes = py_file.read_bytes()
        except OSError:
            return None
        return (
            str(py_file.resolve()),
            hashlib.sha256(raw_bytes).hexdigest(),
            gate_key,
        )

    @classmethod
    def _execute_selected_lint_tools(
        cls,
        py_file: Path,
        workspace: Path,
        selected_tools: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> t.Infra.LintSnapshot:
        """Execute selected lint tools."""
        command_cwd = cls._command_cwd(py_file, workspace)
        command_env = cls._command_env()
        gate_timeout = max(5, min(15, c.Infra.TIMEOUT_SHORT))

        def _run_gate(
            tool_name: str,
            tmpl: tuple[str, ...],
        ) -> tuple[str, t.StrSequence]:
            """Run gate."""
            cmd = [
                *cls._workspace_tool_command(workspace, tmpl[0]),
                *(item.replace("{file}", str(py_file)) for item in tmpl[1:]),
            ]
            run_result = u.Cli.run_raw(
                cmd,
                cwd=command_cwd,
                env=command_env,
                timeout=gate_timeout,
            )
            gate_errors: t.StrSequence
            if run_result.failure:
                gate_errors = [run_result.error or f"{tool_name} failed"]
            elif run_result.success and run_result.value.exit_code != 0:
                output = (run_result.value.stdout + run_result.value.stderr).strip()
                gate_errors = [line for line in output.splitlines() if line.strip()]
            else:
                gate_errors = ()
            return tool_name, gate_errors

        errors: MutableMapping[str, t.StrSequence] = {}
        ruff_template = next(
            (tmpl for tool, tmpl in selected_tools if tool == "ruff"),
            None,
        )
        if ruff_template is not None:
            ruff_tool, ruff_lines = _run_gate("ruff", ruff_template)
            if ruff_lines:
                errors[ruff_tool] = ruff_lines

        remaining_tools = tuple(
            (tool, tmpl) for tool, tmpl in selected_tools if tool != "ruff"
        )
        if not remaining_tools:
            return dict(errors)

        timeout_budget = max(1, gate_timeout + 10)
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, len(remaining_tools)),
        ) as pool:
            futures_by_tool = {
                pool.submit(_run_gate, tool, tmpl): tool
                for tool, tmpl in remaining_tools
            }
            done, not_done = concurrent.futures.wait(
                tuple(futures_by_tool),
                timeout=timeout_budget,
            )

        for future in done:
            tool_name, lines = future.result()
            if lines:
                errors[tool_name] = lines
        for future in not_done:
            tool_name = futures_by_tool[future]
            _ = future.cancel()
            errors[tool_name] = [
                f"timeout {timeout_budget}s: lint gate '{tool_name}' did not finish"
            ]
        return dict(errors)

    @classmethod
    def lint_snapshot(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.LintSnapshot:
        """Run selected lint tools on *py_file*, concurrent and content-cached."""
        selected_tools = cls._selected_lint_tools(gates)
        if not selected_tools:
            return {}

        gate_key = tuple(tool for tool, _ in selected_tools)
        cache_key = cls._lint_snapshot_cache_key(py_file, gate_key)
        if (
            cache_key is not None
            and (cached := cls._snapshot_cache.get(cache_key)) is not None
        ):
            return cached

        result = cls._execute_selected_lint_tools(
            py_file=py_file,
            workspace=workspace,
            selected_tools=selected_tools,
        )
        if cache_key is not None:
            cls._snapshot_cache[cache_key] = dict(result)
        return result

    @classmethod
    def lint_snapshots(
        cls,
        paths: t.SequenceOf[Path],
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> MutableMapping[Path, t.Infra.LintSnapshot]:
        """Run lint snapshots for multiple files concurrently."""
        ordered_paths = tuple(paths)
        if not ordered_paths:
            return {}
        if len(ordered_paths) == 1:
            path = ordered_paths[0]
            return {path: cls.lint_snapshot(path, workspace, gates=gates)}

        snapshots_by_path: MutableMapping[Path, t.Infra.LintSnapshot] = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max(
                1,
                min(cls._SNAPSHOT_MAX_WORKERS, len(ordered_paths)),
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
        before: t.Infra.LintSnapshot,
        after: t.Infra.LintSnapshot,
    ) -> t.Infra.LintSnapshot:
        """Return only lint errors introduced relative to *before*."""
        return {
            tool: added
            for tool, lines in after.items()
            if (
                added := [
                    line
                    for line in lines
                    if (
                        normalized
                        := FlextInfraUtilitiesProtectedEditLinting._normalize_lint_line(
                            line,
                        )
                    )
                    and normalized
                    not in {
                        FlextInfraUtilitiesProtectedEditLinting._normalize_lint_line(
                            item
                        )
                        for item in before.get(tool, [])
                        if FlextInfraUtilitiesProtectedEditLinting._normalize_lint_line(
                            item
                        )
                    }
                ]
            )
        }

    @staticmethod
    def preview_source_lint(
        py_file: Path,
        workspace: Path,
        *,
        updated_source: str,
        gates: t.StrSequence | None = None,
    ) -> tuple[t.Infra.LintSnapshot, t.Infra.LintSnapshot]:
        """Preview lint output for ``updated_source`` while restoring the file."""
        original_source = py_file.read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        before = FlextInfraUtilitiesProtectedEditLinting.lint_snapshot(
            py_file,
            workspace,
            gates=gates,
        )
        if updated_source == original_source:
            return before, before
        py_file.write_text(
            updated_source,
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        try:
            after = FlextInfraUtilitiesProtectedEditLinting.lint_snapshot(
                py_file,
                workspace,
                gates=gates,
            )
        finally:
            py_file.write_text(
                original_source,
                encoding=c.Cli.ENCODING_DEFAULT,
            )
        return before, after


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditLinting"]
