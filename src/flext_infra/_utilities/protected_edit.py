"""Protected file edit helpers with lint delta validation and .bak support."""

from __future__ import annotations

import difflib
import os
import re
import shutil
from collections.abc import Callable, Mapping, MutableMapping, MutableSequence
from pathlib import Path

from flext_cli import u
from flext_infra import FlextInfraUtilitiesDiscovery, c, t


class FlextInfraUtilitiesProtectedEdit:
    """Shared safety helpers for protected file edits in refactor workflows."""

    _NO_TESTS_EXIT_CODE = 5
    _LINE_COL_RE = re.compile(r":\d+(?::\d+)?")
    _CODE_FRAME_RE = re.compile(r"^\s*\d+\s+\|")
    _CODE_FRAME_BODY_RE = re.compile(r"^\s*\|")
    _UNUSED_IMPORT_RE = re.compile(r"`([^`]+)` imported but unused")

    @staticmethod
    def _normalize_lint_line(line: str) -> str:
        if FlextInfraUtilitiesProtectedEdit._CODE_FRAME_RE.match(
            line
        ) or FlextInfraUtilitiesProtectedEdit._CODE_FRAME_BODY_RE.match(line):
            return ""
        normalized = FlextInfraUtilitiesProtectedEdit._LINE_COL_RE.sub("", line)
        normalized = FlextInfraUtilitiesProtectedEdit._UNUSED_IMPORT_RE.sub(
            lambda match: (
                f"`{match.group(1).rsplit('.', maxsplit=1)[-1]}` imported but unused"
            ),
            normalized,
        )
        return normalized.strip()

    @staticmethod
    def _selected_lint_tools(
        gates: t.StrSequence | None = None,
    ) -> tuple[tuple[str, tuple[str, ...]], ...]:
        if not gates:
            gates = tuple(
                gate.strip()
                for gate in c.Infra.SAFE_EXECUTION_DEFAULT_GATES.split(",")
                if gate.strip()
            )
        gate_names = {gate.strip().lower() for gate in gates if gate.strip()}
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
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
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
        env = dict(os.environ)
        _ = env.pop("PYTHONPATH", None)
        return env

    @classmethod
    def lint_snapshot(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.LintSnapshot:
        """Run selected lint tools on *py_file* and return failing output lines."""
        errors: MutableMapping[str, t.StrSequence] = {}
        command_cwd = cls._command_cwd(py_file, workspace)
        for tool, tmpl in cls._selected_lint_tools(gates):
            cmd = [item.replace("{file}", str(py_file)) for item in tmpl]
            result = u.Cli.run_raw(
                cmd,
                cwd=command_cwd,
                env=cls._command_env(),
                timeout=c.Infra.TIMEOUT_SHORT,
            )
            if result.success and result.value.exit_code != 0:
                output = (result.value.stdout + result.value.stderr).strip()
                errors[tool] = [line for line in output.splitlines() if line.strip()]
        return errors

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

    @classmethod
    def preview_source_lint(
        cls,
        py_file: Path,
        workspace: Path,
        *,
        updated_source: str,
        gates: t.StrSequence | None = None,
    ) -> tuple[t.Infra.LintSnapshot, t.Infra.LintSnapshot]:
        """Preview lint output for ``updated_source`` while restoring the file."""
        original_source = py_file.read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        before = cls.lint_snapshot(py_file, workspace, gates=gates)
        if updated_source == original_source:
            return before, before
        py_file.write_text(
            updated_source,
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        try:
            after = cls.lint_snapshot(py_file, workspace, gates=gates)
        finally:
            py_file.write_text(
                original_source,
                encoding=c.Infra.ENCODING_DEFAULT,
            )
        return before, after

    @staticmethod
    def _pytest_failure(py_file: Path, workspace: Path) -> str | None:
        if "tests" not in py_file.parts and not py_file.name.startswith("test_"):
            return None
        command_cwd = FlextInfraUtilitiesProtectedEdit._command_cwd(py_file, workspace)
        result = u.Cli.run_raw(
            ["pytest", str(py_file), "-x", "--tb=short", "-q"],
            cwd=command_cwd,
            env=FlextInfraUtilitiesProtectedEdit._command_env(),
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if result.failure:
            error = (result.error or "pytest execution failed")[:300]
            if "no tests collected" in error.lower() or "no tests ran" in error.lower():
                return None
            return error
        output = (result.value.stdout + result.value.stderr)[:300]
        if (
            result.value.exit_code
            == FlextInfraUtilitiesProtectedEdit._NO_TESTS_EXIT_CODE
            and (
                "no tests collected" in output.lower()
                or "no tests ran" in output.lower()
            )
        ):
            return None
        if result.value.exit_code != 0:
            return output
        return None

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
                encoding=c.Infra.ENCODING_DEFAULT,
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
        test_fail = None if new_errors else cls._pytest_failure(py_file, workspace)
        if not new_errors and not test_fail:
            if backup_path is None:
                return (True, [])
            return (True, [f"  BACKUP {rel} -> {backup_path.name}"])

        modified = py_file.read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
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
        report: MutableSequence[str] = [f"  REVERTED {rel}:"]
        report.extend(f"    {line.rstrip()}" for line in diff[:30])
        for tool, messages in new_errors.items():
            report.extend((
                f"    NEW {tool} errors:",
                *(f"      {message}" for message in messages[:5]),
            ))
        if test_fail:
            report.append(f"    pytest failure: {test_fail}")
        return (False, report)

    @classmethod
    def protected_source_write(
        cls,
        py_file: Path,
        *,
        workspace: Path,
        updated_source: str,
        keep_backup: bool = False,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.EditResult:
        """Write *updated_source* with protected validation and rollback."""
        original_source = py_file.read_text(
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        if updated_source == original_source:
            return (True, [])

        def _write_updated() -> None:
            py_file.write_text(
                updated_source,
                encoding=c.Infra.ENCODING_DEFAULT,
            )

        def _restore_original() -> None:
            py_file.write_text(
                original_source,
                encoding=c.Infra.ENCODING_DEFAULT,
            )

        return cls.protected_file_edit(
            py_file,
            workspace=workspace,
            before_source=original_source,
            edit_fn=_write_updated,
            restore_fn=_restore_original,
            keep_backup=keep_backup,
            gates=gates,
        )

    @classmethod
    def protected_source_writes(
        cls,
        updates: Mapping[Path, str],
        *,
        workspace: Path,
        keep_backup: bool = False,
        gates: t.StrSequence | None = None,
        post_write: Callable[[], None] | None = None,
    ) -> t.Infra.EditResult:
        """Write multiple files transactionally with lint delta validation."""
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
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                before_lints[path] = cls.lint_snapshot(path, workspace, gates=gates)
                if (
                    keep_backup
                    and (backup_path := cls._preserve_backup(path)) is not None
                ):
                    backup_paths[path] = backup_path
                continue
            before_sources[path] = None
            before_lints[path] = {}

        def _restore() -> None:
            for path, original_source in before_sources.items():
                if original_source is None:
                    if path.exists():
                        path.unlink()
                    continue
                path.write_text(
                    original_source,
                    encoding=c.Infra.ENCODING_DEFAULT,
                )

        write_completed = False
        try:
            for path, updated_source in normalized_updates.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    updated_source,
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
            if post_write is not None:
                post_write()
            write_completed = True
        finally:
            if not write_completed:
                _restore()

        reports: MutableSequence[str] = []
        failed = False
        for path in normalized_updates:
            new_errors = cls.lint_new_errors(
                before_lints[path],
                cls.lint_snapshot(path, workspace, gates=gates),
            )
            test_fail = None if new_errors else cls._pytest_failure(path, workspace)
            if not new_errors and not test_fail:
                continue
            failed = True
            rel = cls._relative_path(path, workspace)
            before_source = before_sources[path] or ""
            modified = path.read_text(
                encoding=c.Infra.ENCODING_DEFAULT,
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
                f"  BACKUP {cls._relative_path(path, workspace)} -> {backup.name}"
                for path, backup in backup_paths.items()
            ],
        )


__all__: list[str] = ["FlextInfraUtilitiesProtectedEdit"]
