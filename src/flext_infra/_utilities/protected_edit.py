"""Protected file edit helpers with lint delta validation and .bak support."""

from __future__ import annotations

import concurrent.futures
import difflib
import hashlib
import shutil
from collections.abc import (
    Callable,
    MutableMapping,
)
from pathlib import Path
from typing import ClassVar

from flext_cli import u
from flext_infra import FlextInfraUtilitiesDiscovery, c, m, p, r, t


class FlextInfraUtilitiesProtectedEdit:
    """Shared safety helpers for protected file edits in refactor workflows."""

    _NO_TESTS_EXIT_CODE = 5

    @staticmethod
    def _normalize_lint_line(line: str) -> str:
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
        try:
            return py_file.relative_to(workspace)
        except ValueError:
            return py_file

    @staticmethod
    def _command_cwd(py_file: Path, workspace: Path) -> Path:
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
        return u.Cli.process_env(remove_keys=("PYTHONPATH",))

    @classmethod
    def _new_file_lint_baseline(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.LintSnapshot:
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

    @classmethod
    def lint_snapshot(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.LintSnapshot:
        """Run selected lint tools on *py_file*, concurrent and content-cached.

        Each gate tool spawns an independent subprocess; they are dispatched
        through a thread pool so that wall-clock time is bounded by the
        slowest tool rather than the sum of all tools. Results are cached
        by ``(resolved_path, content_sha256, gate_set)`` so that repeated
        snapshots of the same file content reuse prior subprocess output —
        a common pattern when the census measures a baseline before each
        candidate write.
        """
        selected_tools = cls._selected_lint_tools(gates)
        result: t.Infra.LintSnapshot
        if not selected_tools:
            result = {}
        else:
            gate_key = tuple(tool for tool, _ in selected_tools)
            cache_key: tuple[str, str, tuple[str, ...]] | None = None
            try:
                raw_bytes = py_file.read_bytes()
            except OSError:
                raw_bytes = None
            if raw_bytes is not None:
                cache_key = (
                    str(py_file.resolve()),
                    hashlib.sha256(raw_bytes).hexdigest(),
                    gate_key,
                )
                cached = cls._snapshot_cache.get(cache_key)
            else:
                cached = None

            if cached is not None:
                result = cached
            else:
                errors: MutableMapping[str, t.StrSequence] = {}
                command_cwd = cls._command_cwd(py_file, workspace)
                command_env = cls._command_env()
                gate_timeout = max(5, min(15, c.Infra.TIMEOUT_SHORT))

                def _run_gate(
                    tool_name: str, tmpl: tuple[str, ...]
                ) -> tuple[str, t.StrSequence]:
                    cmd = [item.replace("{file}", str(py_file)) for item in tmpl]
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
                        output = (
                            run_result.value.stdout + run_result.value.stderr
                        ).strip()
                        gate_errors = [
                            line for line in output.splitlines() if line.strip()
                        ]
                    else:
                        gate_errors = ()
                    return tool_name, gate_errors

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
                if remaining_tools:
                    with concurrent.futures.ThreadPoolExecutor(
                        max_workers=max(1, len(remaining_tools)),
                    ) as pool:
                        futures_by_tool = {
                            pool.submit(_run_gate, tool, tmpl): tool
                            for tool, tmpl in remaining_tools
                        }
                        timeout_budget = max(1, gate_timeout + 10)
                        try:
                            for future in concurrent.futures.as_completed(
                                tuple(futures_by_tool),
                                timeout=timeout_budget,
                            ):
                                tool_name, lines = future.result()
                                if lines:
                                    errors[tool_name] = lines
                        except concurrent.futures.TimeoutError:
                            for future, tool_name in futures_by_tool.items():
                                if future.done():
                                    continue
                                _ = future.cancel()
                                errors[tool_name] = [
                                    f"timeout {timeout_budget}s: lint gate '{tool_name}' did not finish"
                                ]
                if cache_key is not None:
                    cls._snapshot_cache[cache_key] = dict(errors)
                result = errors
        return result

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
                        := FlextInfraUtilitiesProtectedEdit._normalize_lint_line(
                            line,
                        )
                    )
                    and normalized
                    not in {
                        FlextInfraUtilitiesProtectedEdit._normalize_lint_line(item)
                        for item in before.get(tool, [])
                        if FlextInfraUtilitiesProtectedEdit._normalize_lint_line(item)
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
        before = FlextInfraUtilitiesProtectedEdit.lint_snapshot(
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
            after = FlextInfraUtilitiesProtectedEdit.lint_snapshot(
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

    @staticmethod
    def preview_source_writes(
        updates: t.MappingKV[Path, str],
        *,
        workspace: Path,
        gates: t.StrSequence | None = None,
        post_write: Callable[[], None] | None = None,
    ) -> t.Infra.EditResult:
        """Preview multiple file writes transactionally and always restore sources."""
        if not updates:
            return (True, [])

        normalized_updates = {
            path.resolve(): content
            for path, content in sorted(updates.items(), key=lambda item: str(item[0]))
        }
        before_sources: MutableMapping[Path, str | None] = {}
        before_lints: MutableMapping[Path, t.Infra.LintSnapshot] = {}
        for path in normalized_updates:
            if path.exists():
                before_sources[path] = path.read_text(
                    encoding=c.Cli.ENCODING_DEFAULT,
                )
                before_lints[path] = FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                    path,
                    workspace,
                    gates=gates,
                )
                continue
            before_sources[path] = None
            before_lints[path] = (
                FlextInfraUtilitiesProtectedEdit._new_file_lint_baseline(
                    path,
                    workspace,
                    gates=gates,
                )
            )

        def _restore() -> None:
            for path, original_source in before_sources.items():
                if original_source is None:
                    if path.exists():
                        path.unlink()
                    continue
                path.write_text(
                    original_source,
                    encoding=c.Cli.ENCODING_DEFAULT,
                )

        try:
            for path, updated_source in normalized_updates.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    updated_source,
                    encoding=c.Cli.ENCODING_DEFAULT,
                )
            if post_write is not None:
                post_write()

            reports: t.MutableSequenceOf[str] = []
            failed = False
            for path in normalized_updates:
                new_errors = FlextInfraUtilitiesProtectedEdit.lint_new_errors(
                    before_lints[path],
                    FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                        path,
                        workspace,
                        gates=gates,
                    ),
                )
                if not new_errors:
                    continue
                failed = True
                rel = FlextInfraUtilitiesProtectedEdit._relative_path(path, workspace)
                before_source = before_sources[path] or ""
                modified = path.read_text(
                    encoding=c.Cli.ENCODING_DEFAULT,
                )
                diff = list(
                    difflib.unified_diff(
                        before_source.splitlines(keepends=True),
                        modified.splitlines(keepends=True),
                        fromfile=f"a/{rel}",
                        tofile=f"b/{rel}",
                        n=3,
                    )
                )
                reports.append(f"  REVERTED {rel}:")
                reports.extend(f"    {line.rstrip()}" for line in diff[:30])
                for tool, messages in new_errors.items():
                    reports.extend((
                        f"    NEW {tool} errors:",
                        *(f"      {message}" for message in messages[:5]),
                    ))
            return (not failed, list(reports))
        finally:
            _restore()

    _NO_TESTS_MARKERS: ClassVar[frozenset[str]] = frozenset({
        "no tests collected",
        "no tests ran",
    })

    @classmethod
    def _has_no_tests_marker(cls, text: str) -> bool:
        """Return whether *text* contains any pytest "no tests" marker."""
        lowered = text.lower()
        return any(marker in lowered for marker in cls._NO_TESTS_MARKERS)

    @classmethod
    def _pytest_failure(cls, py_file: Path, workspace: Path) -> p.Result[bool]:
        """Run pytest for a single file and surface a failure message via ``r``.

        ``r.ok(True)`` for non-test files or when pytest passed (or
        legitimately collected no tests). ``r.fail(error_message)`` when
        pytest reported a real failure — the error message is the
        truncated (300-char) stdout/stderr or driver error.
        """
        if "tests" not in py_file.parts and not py_file.name.startswith("test_"):
            return r[bool].ok(True)
        run_result = u.Cli.run_raw(
            ["pytest", str(py_file), "-x", "--tb=short", "-q"],
            cwd=cls._command_cwd(py_file, workspace),
            env=cls._command_env(),
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if run_result.failure:
            error = (run_result.error or "pytest execution failed")[:300]
            return (
                r[bool].ok(True)
                if cls._has_no_tests_marker(error)
                else r[bool].fail(error)
            )
        output = (run_result.value.stdout + run_result.value.stderr)[:300]
        passed_or_no_tests = run_result.value.exit_code == 0 or (
            run_result.value.exit_code == cls._NO_TESTS_EXIT_CODE
            and cls._has_no_tests_marker(output)
        )
        return r[bool].ok(True) if passed_or_no_tests else r[bool].fail(output)

    @staticmethod
    def _preserve_backup(py_file: Path) -> Path | None:
        if not py_file.exists():
            return None
        backup_path = py_file.with_suffix(
            py_file.suffix + c.Infra.SAFE_EXECUTION_BAK_SUFFIX,
        )
        if not backup_path.exists():
            shutil.copy2(py_file, backup_path)
        return backup_path

    @classmethod
    def protected_file_edit(
        cls,
        py_file: Path,
        *,
        workspace: Path,
        before_source: str,
        edit_fn: Callable[[], None],
        restore_fn: Callable[[], None] | None = None,
        keep_backup: bool = False,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.EditResult:
        """Apply one edit, validate lint deltas, and restore on failure."""
        rel = cls._relative_path(py_file, workspace)
        before = cls.lint_snapshot(py_file, workspace, gates=gates)
        backup_path = cls._preserve_backup(py_file) if keep_backup else None

        def _restore() -> None:
            if restore_fn is not None:
                restore_fn()
                return
            py_file.write_text(
                before_source,
                encoding=c.Cli.ENCODING_DEFAULT,
            )

        edit_completed = False
        try:
            edit_fn()
            edit_completed = True
        finally:
            if not edit_completed:
                _restore()

        new_errors = cls.lint_new_errors(
            before,
            cls.lint_snapshot(py_file, workspace, gates=gates),
        )
        test_fail: str | None = (
            None
            if new_errors
            else cls._pytest_failure(py_file, workspace).fold(
                on_failure=lambda msg: msg,
                on_success=lambda _: None,
            )
        )
        if not new_errors and not test_fail:
            if backup_path is None:
                return (True, [])
            return (True, [f"  BACKUP {rel} -> {backup_path.name}"])

        modified = py_file.read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        diff = list(
            difflib.unified_diff(
                before_source.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
                n=3,
            )
        )
        _restore()
        report: t.MutableSequenceOf[str] = [f"  REVERTED {rel}:"]
        report.extend(f"    {line.rstrip()}" for line in diff[:30])
        for tool, messages in new_errors.items():
            report.extend((
                f"    NEW {tool} errors:",
                *(f"      {message}" for message in messages[:5]),
            ))
        if test_fail:
            report.append(f"    pytest failure: {test_fail}")
        return (False, report)

    @staticmethod
    def protected_source_write(
        py_file: Path,
        *,
        request: m.Infra.ProtectedSourceWriteRequest,
    ) -> t.Infra.EditResult:
        """Write validated source content with protected validation and rollback."""
        original_source = py_file.read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        if request.updated_source == original_source:
            return (True, [])

        def _write_updated() -> None:
            py_file.write_text(
                request.updated_source,
                encoding=c.Cli.ENCODING_DEFAULT,
            )

        def _restore_original() -> None:
            py_file.write_text(
                original_source,
                encoding=c.Cli.ENCODING_DEFAULT,
            )

        return FlextInfraUtilitiesProtectedEdit.protected_file_edit(
            py_file,
            workspace=request.workspace,
            before_source=original_source,
            edit_fn=_write_updated,
            restore_fn=_restore_original,
            keep_backup=request.keep_backup,
            gates=request.gates,
        )

    @staticmethod
    def protected_source_writes(
        updates: t.MappingKV[Path, str],
        *,
        request: m.Infra.ProtectedSourceWritesRequest,
    ) -> t.Infra.EditResult:
        """Write multiple files transactionally with lint delta validation.

        ``request.skip_pytest=True`` bypasses the per-file pytest invocation
        performed after the lint delta check. Callers that only remove code
        (e.g. the census apply path) can opt out because pytest on the shrunk
        file is guaranteed to collect no tests and return exit code 5 — a ~5s
        per-file no-op that dominates the wall-clock time in monorepo scale.
        """
        if not updates:
            return (True, [])

        normalized_updates = {
            path.resolve(): content
            for path, content in sorted(updates.items(), key=lambda item: str(item[0]))
        }
        before_sources: MutableMapping[Path, str | None] = {}
        before_lints: MutableMapping[Path, t.Infra.LintSnapshot] = {}
        backup_paths: MutableMapping[Path, Path] = {}
        for path in normalized_updates:
            if path.exists():
                before_sources[path] = path.read_text(
                    encoding=c.Cli.ENCODING_DEFAULT,
                )
                before_lints[path] = FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                    path,
                    request.workspace,
                    gates=request.gates,
                )
                if (
                    request.keep_backup
                    and (
                        backup_path
                        := FlextInfraUtilitiesProtectedEdit._preserve_backup(
                            path,
                        )
                    )
                    is not None
                ):
                    backup_paths[path] = backup_path
                continue
            before_sources[path] = None
            before_lints[path] = (
                FlextInfraUtilitiesProtectedEdit._new_file_lint_baseline(
                    path,
                    request.workspace,
                    gates=request.gates,
                )
            )

        def _restore() -> None:
            for path, original_source in before_sources.items():
                if original_source is None:
                    if path.exists():
                        path.unlink()
                    continue
                path.write_text(
                    original_source,
                    encoding=c.Cli.ENCODING_DEFAULT,
                )

        write_completed = False
        try:
            for path, updated_source in normalized_updates.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    updated_source,
                    encoding=c.Cli.ENCODING_DEFAULT,
                )
            if request.post_write is not None:
                request.post_write()
            write_completed = True
        finally:
            if not write_completed:
                _restore()

        reports: t.MutableSequenceOf[str] = []
        failed = False
        for path in normalized_updates:
            new_errors = FlextInfraUtilitiesProtectedEdit.lint_new_errors(
                before_lints[path],
                FlextInfraUtilitiesProtectedEdit.lint_snapshot(
                    path,
                    request.workspace,
                    gates=request.gates,
                ),
            )
            if new_errors or request.skip_pytest:
                test_fail: str | None = None
            else:
                test_fail = FlextInfraUtilitiesProtectedEdit._pytest_failure(
                    path,
                    request.workspace,
                ).fold(
                    on_failure=lambda msg: msg,
                    on_success=lambda _: None,
                )
            if not new_errors and not test_fail:
                continue
            failed = True
            rel = FlextInfraUtilitiesProtectedEdit._relative_path(
                path,
                request.workspace,
            )
            before_source = before_sources[path] or ""
            modified = path.read_text(
                encoding=c.Cli.ENCODING_DEFAULT,
            )
            diff = list(
                difflib.unified_diff(
                    before_source.splitlines(keepends=True),
                    modified.splitlines(keepends=True),
                    fromfile=f"a/{rel}",
                    tofile=f"b/{rel}",
                    n=3,
                )
            )
            reports.append(f"  REVERTED {rel}:")
            reports.extend(f"    {line.rstrip()}" for line in diff[:30])
            for tool, messages in new_errors.items():
                reports.extend((
                    f"    NEW {tool} errors:",
                    *(f"      {message}" for message in messages[:5]),
                ))
            if test_fail:
                reports.append(f"    pytest failure: {test_fail}")
        if failed:
            _restore()
            return (False, list(reports))

        if not backup_paths:
            return (True, [])
        return (
            True,
            [
                "  BACKUP "
                f"{FlextInfraUtilitiesProtectedEdit._relative_path(path, request.workspace)}"
                f" -> {backup.name}"
                for path, backup in backup_paths.items()
            ],
        )


__all__: list[str] = ["FlextInfraUtilitiesProtectedEdit"]
