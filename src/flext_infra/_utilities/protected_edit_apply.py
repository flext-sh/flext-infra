"""Apply and validate protected edits while retaining written source.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import secrets
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r, settings, t
from flext_infra._utilities import FlextInfraUtilitiesProtectedEditPreview


class FlextInfraUtilitiesProtectedEditApply(FlextInfraUtilitiesProtectedEditPreview):
    """Apply, report validation failures, and retain protected edits."""

    @staticmethod
    def _protected_write_test_failure(
        path: Path,
        request: m.Infra.ProtectedSourceWritesRequest,
        new_errors: t.Infra.LintSnapshot[t.StrSequence],
    ) -> str | None:
        """Protected write test failure.

        Returns:
            The resulting ``str | None``.

        """
        if new_errors or request.skip_pytest:
            return None
        pytest_result = FlextInfraUtilitiesProtectedEditApply._pytest_failure(
            path,
            request.workspace,
        )
        if pytest_result.failure:
            error_message = pytest_result.error
            return error_message if isinstance(error_message, str) else None
        return None

    @staticmethod
    def _protected_write_reports(
        updates: t.MappingKV[Path, str],
        before_sources: t.MappingKV[Path, str | None],
        before_lints: t.MappingKV[Path, t.Infra.LintSnapshot[m.Infra.LintGateResult]],
        request: m.Infra.ProtectedSourceWritesRequest,
    ) -> t.Infra.EditResult:
        """Protected write reports.

        Returns:
            The resulting ``t.Infra.EditResult``.

        """
        reports: list[str] = []
        failed = False
        after_lints = FlextInfraUtilitiesProtectedEditApply.lint_snapshots(
            tuple(updates),
            request.workspace,
            gates=request.gates,
        )
        for path in updates:
            new_errors = FlextInfraUtilitiesProtectedEditApply.lint_new_errors(
                before_lints[path],
                after_lints[path],
            )
            execution_errors = tuple(
                error
                for snapshot in (before_lints[path], after_lints[path])
                for error in (
                    FlextInfraUtilitiesProtectedEditApply.lint_execution_errors(
                        snapshot
                    )
                )
            )
            test_fail = (
                None
                if execution_errors
                else (
                    FlextInfraUtilitiesProtectedEditApply._protected_write_test_failure(
                        path,
                        request,
                        new_errors,
                    )
                )
            )
            if not new_errors and not test_fail and not execution_errors:
                continue
            failed = True
            reports.extend(
                FlextInfraUtilitiesProtectedEditApply._validation_failure_report_lines(
                    path,
                    request.workspace,
                    before_sources[path] or "",
                    new_errors,
                    execution_errors=execution_errors,
                ),
            )
            if test_fail:
                reports.append(f"    pytest failure: {test_fail}")
        return (not failed, reports)

    @classmethod
    def _file_contains_tests(cls, py_file: Path) -> bool:
        """Return whether *py_file* defines pytest-collectable tests.

        Returns:
            Whether *py_file* defines pytest-collectable tests.

        """
        tree = ast.parse(py_file.read_text(encoding=c.DEFAULT_ENCODING))
        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.FunctionDef | ast.AsyncFunctionDef,
            ) and node.name.startswith("test_"):
                return True
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                return True
        return False

    @classmethod
    def _pytest_failure(cls, py_file: Path, workspace: Path) -> p.Result[bool]:
        """Run pytest for a single file and surface a failure message via ``r``.

        Returns:
            The resulting ``p.Result[bool]``.

        Raises:
            ValueError: If the profile declares no canonical process directory.
            NotADirectoryError: If the resolved profile path is not a directory.

        """
        if "tests" not in py_file.parts and not py_file.name.startswith("test_"):
            return r[bool].ok(value=True)
        if not cls._file_contains_tests(py_file):
            compile_result = u.Cli.run_raw(
                [
                    *cls._workspace_tool_command(c.Infra.PYTHON),
                    "-m",
                    "py_compile",
                    str(py_file),
                ],
                cwd=cls._command_cwd(py_file, workspace),
                options=m.Cli.ProcessOptions(
                    env=cls._command_env(),
                    remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
                ),
                timeout=c.Infra.TIMEOUT_SHORT,
            )
            if compile_result.failure:
                return r[bool].from_failure(compile_result)
            if not u.Cli.process_succeeded(compile_result.value.outcome):
                return r[bool].fail(
                    compile_result.value.stdout + compile_result.value.stderr,
                )
            return r[bool].ok(value=True)
        arguments = (str(py_file), "-x", "--tb=short", "-q")
        profile_root = settings.env_lookup(c.Infra.PYTEST_PROFILE_CHILD_ROOT_ENV)
        if profile_root is not None:
            if not profile_root or not settings.env_lookup(
                c.Infra.PYTEST_PROFILE_PROCESS_DIRECTORY_ENV,
            ):
                msg = "protected pytest profile has no canonical process directory"
                raise ValueError(msg)
            directory = Path(profile_root).resolve(strict=True)
            if not directory.is_dir():
                raise NotADirectoryError(directory)
            command = (
                *cls._workspace_tool_command(c.Infra.PYTHON),
                "-c",
                c.Infra.PYTEST_PROFILE_LAUNCHER,
                str(directory / f"{secrets.token_hex(16)}.pstats"),
                *arguments,
            )
        else:
            command = (*cls._workspace_tool_command("pytest"), *arguments)
        run_result = u.Cli.run_raw(
            command,
            cwd=cls._command_cwd(py_file, workspace),
            options=m.Cli.ProcessOptions(
                env=cls._command_env(),
                remove_env_keys=cls._COMMAND_ENV_REMOVE_KEYS,
            ),
            timeout=c.Infra.TIMEOUT_MEDIUM,
        )
        if run_result.failure:
            return r[bool].from_failure(run_result)
        output = run_result.value.stdout + run_result.value.stderr
        return (
            r[bool].ok(value=True)
            if u.Cli.process_succeeded(run_result.value.outcome)
            else r[bool].fail(output)
        )

    @staticmethod
    def protected_file_edit(
        py_file: Path,
        *,
        request: m.Infra.ProtectedFileEditRequest,
    ) -> t.Infra.EditResult:
        """Apply one edit and report lint/test failures without undoing writes.

        Returns:
            The resulting ``t.Infra.EditResult``.

        """
        before = FlextInfraUtilitiesProtectedEditApply.lint_snapshot(
            py_file,
            request.workspace,
            gates=request.gates,
        )

        request.edit_fn()
        after = FlextInfraUtilitiesProtectedEditApply.lint_snapshot(
            py_file,
            request.workspace,
            gates=request.gates,
        )
        new_errors = FlextInfraUtilitiesProtectedEditApply.lint_new_errors(
            before, after
        )
        execution_errors = tuple(
            error
            for snapshot in (before, after)
            for error in FlextInfraUtilitiesProtectedEditApply.lint_execution_errors(
                snapshot
            )
        )

        test_fail: str | None = (
            None
            if new_errors or execution_errors
            else FlextInfraUtilitiesProtectedEditApply._pytest_failure(
                py_file,
                request.workspace,
            ).fold(on_failure=lambda msg: msg, on_success=lambda _: None)
        )
        if not new_errors and not test_fail and not execution_errors:
            return (True, [])

        report = FlextInfraUtilitiesProtectedEditApply._validation_failure_report_lines(
            py_file,
            request.workspace,
            request.before_source,
            new_errors,
            execution_errors=execution_errors,
        )
        if test_fail:
            report.append(f"    pytest failure: {test_fail}")
        return (False, report)

    @staticmethod
    def protected_source_write(
        py_file: Path,
        *,
        request: m.Infra.ProtectedSourceWriteRequest,
    ) -> t.Infra.EditResult:
        """Write source content and retain it with its validation result.

        Returns:
            The resulting ``t.Infra.EditResult``.

        Raises:
            ValueError: If the protected source has no authenticated bytes or mode.

        """
        before_state = u.Cli.atomic_read_binary_file_state(
            py_file, required=True
        ).unwrap()
        if before_state.content is None or before_state.mode is None:
            msg = f"protected source has no authenticated bytes or mode: {py_file}"
            raise ValueError(msg)
        original_source = before_state.content.decode(c.DEFAULT_ENCODING)
        permission_mode = before_state.mode
        if request.updated_source == original_source:
            return (True, [])

        def _write_updated() -> None:
            """Write updated."""
            u.Cli.atomic_write_binary_file_guarded(
                before_state,
                request.updated_source.encode(c.DEFAULT_ENCODING),
                permission_mode=permission_mode,
            ).unwrap()

        return FlextInfraUtilitiesProtectedEditApply.protected_file_edit(
            py_file,
            request=m.Infra.ProtectedFileEditRequest(
                workspace=request.workspace,
                before_source=original_source,
                edit_fn=_write_updated,
                gates=request.gates,
            ),
        )

    @staticmethod
    def protected_source_writes(
        updates: t.MappingKV[Path, str],
        *,
        request: m.Infra.ProtectedSourceWritesRequest,
    ) -> t.Infra.EditResult:
        """Write multiple files and retain each write with validation evidence.

        Returns:
            The resulting ``t.Infra.EditResult``.

        """
        if not updates:
            return (True, [])

        normalized_updates = (
            FlextInfraUtilitiesProtectedEditApply._normalized_source_updates(updates)
        )
        expected_sources = {
            path.resolve(): content
            for path, content in request.expected_sources.items()
        }
        for path, expected_source in expected_sources.items():
            current_source = (
                path.read_text(encoding=c.DEFAULT_ENCODING) if path.is_file() else None
            )
            if current_source != expected_source:
                return (
                    False,
                    [
                        (
                            "CAS failed before protected source writes: "
                            f"source changed for {path}"
                        ),
                    ],
                )
        before_sources, before_lints = (
            FlextInfraUtilitiesProtectedEditApply._preview_write_baselines(
                normalized_updates,
                request.workspace,
                gates=request.gates,
            )
        )
        before_states: dict[Path, m.Cli.AtomicFileState] = {}
        for path in normalized_updates:
            path.parent.mkdir(parents=True, exist_ok=True)
            observed = u.Cli.atomic_read_binary_file_state(
                path, required=False
            ).unwrap()
            observed_source = (
                observed.content.decode(c.DEFAULT_ENCODING)
                if observed.content is not None
                else None
            )
            if observed_source != before_sources[path]:
                return (
                    False,
                    [f"source changed during protected write planning: {path}"],
                )
            before_states[path] = observed
        publication_errors: list[str] = []
        written_updates: dict[Path, str] = {}
        for path, updated_source in normalized_updates.items():
            before_state = before_states[path]
            published = u.Cli.atomic_write_binary_file_guarded(
                before_state,
                updated_source.encode(c.DEFAULT_ENCODING),
                permission_mode=(
                    before_state.mode
                    if before_state.mode is not None
                    else c.Infra.CONFIG_SPEC[1]
                ),
            )
            if published.failure:
                publication_errors.append(
                    f"PUBLICATION FAILED {path}: {published.error}"
                )
                continue
            written_updates[path] = updated_source
        if request.post_write is not None and not publication_errors:
            request.post_write()
        valid, validation_reports = (
            FlextInfraUtilitiesProtectedEditApply._protected_write_reports(
                written_updates,
                before_sources,
                before_lints,
                request,
            )
        )
        return (
            valid and not publication_errors,
            [*publication_errors, *validation_reports],
        )


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditApply"]
