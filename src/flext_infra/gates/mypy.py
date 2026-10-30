"""FLEXT mypy quality gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, t, u
from flext_infra.gates import FlextInfraGates

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraGatesMypy(FlextInfraGates):
    """Gate for Mypy type checking."""

    gate_id: ClassVar[str] = c.Infra.MYPY
    gate_name: ClassVar[str] = "Mypy"
    can_fix: ClassVar[bool] = False
    checker_info_prefixes: ClassVar[Sequence[str]] = (
        "LOG:",
        "TRACE:",
        "[pydantic-mypy]:",
    )

    def __init__(
        self,
        repository_root: Path,
        *,
        runner: p.Cli.CommandRunner = u.Cli,
    ) -> None:
        """Keep one effective resource policy for each admitted analysis."""
        super().__init__(repository_root, runner=runner)
        self._resource_limits: MutableMapping[Path, m.Infra.MypyResourceLimit] = {}

    def _project_limit(self, project_dir: Path) -> m.Infra.MypyResourceLimit:
        """Return the admitted policy shared by the child, runner and receipt.

        Returns:
            The effective project resource limit.

        """
        if project_dir not in self._resource_limits:
            self._resource_limits[project_dir] = (
                u.Infra.mypy_resource_limit_for_project(project_dir)
            )
        return self._resource_limits[project_dir]

    @staticmethod
    def _config_exclude(config_path: Path) -> t.RegexPattern | None:
        """Return the compiled [tool.mypy].exclude regex, if configured.

        Returns:
            The compiled [tool.mypy].exclude regex, if configured.

        """
        doc = u.Cli.toml_read(config_path)
        if doc is None:
            return None
        tool_table = u.Cli.toml_table_child(doc, c.Infra.TOOL)
        if tool_table is None:
            return None
        mypy_table = u.Cli.toml_table_child(tool_table, c.Infra.MYPY)
        if mypy_table is None:
            return None
        exclude = u.Cli.toml_value(mypy_table, "exclude")
        if not isinstance(exclude, str) or not exclude:
            return None
        return re.compile(exclude)

    @staticmethod
    def _has_real_module(directory: Path) -> bool:
        """True when the dir holds a Python module other than __init__.py.

        Returns:
            The resulting ``bool``.

        """
        for py_file in directory.rglob(c.Infra.EXT_PYTHON_GLOB):
            if py_file.name != c.Infra.INIT_PY:
                return True
        return any(directory.rglob("*.pyi"))

    @override
    def _get_check_dirs(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Sequence[str]:
        """Check local Python roots directly instead of recursively scanning ``.``.

        Returns:
            The resulting ``Sequence[str]``.

        """
        # Empty or explicitly excluded roots are omitted because Mypy aborts
        # when they are passed positionally.
        exclude = self._config_exclude(self._resolve_config(project_dir, ctx))
        return [
            target
            for target in self._python_targets(project_dir)
            if (project_dir / target).is_file()
            or (
                self._has_real_module(project_dir / target)
                and (exclude is None or not exclude.match(f"{target}/"))
            )
        ]

    @staticmethod
    def _resolve_config(project_dir: Path, ctx: m.Infra.GateContext) -> Path:
        """Resolve Mypy settings from the project, then the workspace.

        Returns:
            The resulting ``Path``.

        """
        pyproject_name: str = c.PYPROJECT_FILENAME
        proj_py = project_dir / pyproject_name
        doc = u.Cli.toml_read(proj_py)
        if doc is not None:
            tool_table = u.Cli.toml_table_child(doc, c.Infra.TOOL)
            if (
                tool_table is not None
                and u.Cli.toml_table_child(tool_table, c.Infra.MYPY) is not None
            ):
                return proj_py
        repository_root: Path = ctx.repository_root
        return repository_root / pyproject_name

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: Sequence[str],
    ) -> Sequence[str]:
        """Run the resource-limited Mypy invocation with its JSON report.

        Returns:
            The limited Mypy command over the resolved settings owner.

        Raises:
            ValueError: If Mypy profile output requires an absolute path in an existing
                directory.

        """
        cfg = self._resolve_config(project_dir, ctx)
        self._resource_limits[project_dir] = u.Infra.mypy_resource_limit_for_project(
            project_dir,
        )
        profile_output = u.Cli.process_env().get(c.Infra.MYPY_PROFILE_OUTPUT_ENV)
        destination = None
        if profile_output is not None:
            destination = Path(profile_output)
            if not destination.is_absolute() or not destination.parent.is_dir():
                msg = (
                    "Mypy profile output requires an absolute path "
                    "in an existing directory"
                )
                raise ValueError(msg)
        return u.Infra.mypy_limited_command(
            m.Infra.MypyInvocation(
                targets=tuple(project_dir / target for target in check_dirs),
                workspace=ctx.runtime_root,
                config_file=cfg,
                report_json=True,
                verbose=True,
                profile_output=destination,
            ),
            self._project_limit(project_dir),
        )

    @override
    def _parsed_gate_execution(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        result: p.Cli.CommandOutput,
        started: float,
    ) -> m.Infra.GateExecution:
        """Publish the admitted budget alongside untouched checker streams.

        Returns:
            The native gate execution and durable budget evidence.

        """
        limit = self._project_limit(project_dir)
        recorded = m.Cli.CommandOutput(
            stdout=result.stdout,
            stderr=(
                "LOG:  Mypy resource budget: "
                f"timeout_seconds={limit.timeout_seconds} "
                f"memory_limit_mb={limit.memory_limit_mb} "
                f"runner_timeout_seconds={u.Infra.mypy_runner_timeout(limit)}\n"
                f"{result.stderr}"
            ),
            outcome=result.outcome,
        )
        return super()._parsed_gate_execution(project_dir, ctx, recorded, started)

    @override
    def _validate_check_report(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        targets: Sequence[str],
    ) -> None:
        """Account for every submitted target from Mypy's native build trace.

        The trace itself is read by ``u.Infra.mypy_build_sources``.

        Raises:
            ValueError: If Mypy native report did not account for a target; or if
                Mypy native report contains an unsubmitted source.

        """
        del ctx
        sources = u.Infra.mypy_build_sources(result.stderr, project_dir)
        submitted = tuple((project_dir / target).resolve() for target in targets)
        for target in submitted:
            if not any(
                source == target or (target.is_dir() and source.is_relative_to(target))
                for source in sources
            ):
                msg = f"Mypy native report did not account for target: {target}"
                raise ValueError(msg)
        for source in sources:
            if not any(
                source == target or (target.is_dir() and source.is_relative_to(target))
                for target in submitted
            ):
                msg = f"Mypy native report contains an unsubmitted source: {source}"
                raise ValueError(msg)

    @staticmethod
    @override
    def _runner_limits(
        timeout: int,
    ) -> tuple[int | None, p.Cli.ProcessDeadline | None]:
        """Leave the child's analysis and forced-kill windows uninterrupted.

        Returns:
            No plain timeout, and a deadline whose soft boundary follows the
            inner forced-kill window.

        """
        return None, u.Infra.mypy_runner_deadline(timeout)

    @override
    def _check_timeout(self, project_dir: Path, ctx: m.Infra.GateContext) -> int:
        """Keep the outer runner alive through the controlled Mypy deadline.

        Returns:
            The resulting ``int``.

        """
        del ctx
        return u.Infra.mypy_runner_timeout(self._project_limit(project_dir))

    @override
    def _check_env(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> Mapping[str, str] | None:
        """Run Mypy against the project's shared analysis cache.

        Returns:
            The resulting ``Mapping[str, str] | None``.

        """
        del ctx
        overrides = {
            c.Infra.MypyCacheEnvironment.CACHE_DIR.value: str(
                u.Infra.mypy_cache_directory(project_dir),
            ),
        }
        return u.Cli.process_env(overrides=overrides)

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, Sequence[p.Infra.Issue]]:
        """Validate Mypy's one-JSON-object-per-line report into findings.

        Returns:
            The run's verdict and its diagnostics, stderr failures or limit hit.

        """
        del ctx
        diagnostics: MutableSequence[p.Infra.Issue] = []
        if resource_diagnostic := u.Infra.mypy_failure_diagnostic(
            result,
            self._project_limit(project_dir),
        ):
            return (
                False,
                (
                    m.Infra.Issue(
                        file=c.PYPROJECT_FILENAME,
                        line=1,
                        column=1,
                        code="mypy-resource-limit",
                        message=resource_diagnostic,
                        severity=c.Infra.ERROR,
                    ),
                ),
            )
        for raw_line in result.stdout.splitlines():
            if not raw_line.strip():
                continue
            if raw_line.startswith("LOG:"):
                # Mypy verbose progress channel (--verbose runs). LOG lines are
                # the tool's own human stream, never diagnostics; the machine
                # contract of this gate is one JSON object per line.
                continue
            validated: p.Result[m.Infra.MypyDiagnostic] = u.validate_value(
                m.Infra.MypyDiagnostic,
                raw_line,
                from_json=True,
                strict=True,
            )
            if validated.failure:
                return False, (
                    self._malformed_report_issue(
                        f"{validated.error}\n"
                        f"mypy exited with code {result.outcome.raw_return_code}\n"
                        f"stdout: {result.stdout}\n"
                        f"stderr: {result.stderr}",
                        tool=c.Infra.MYPY,
                        file=str(project_dir),
                    ),
                )
            diagnostic = validated.value
            diagnostics.append(
                m.Infra.Issue(
                    file=diagnostic.file,
                    line=diagnostic.line,
                    column=diagnostic.column,
                    code=diagnostic.code or "",
                    message=(
                        f"{diagnostic.message}\n{diagnostic.hint}"
                        if diagnostic.hint
                        else diagnostic.message
                    ),
                    severity=diagnostic.severity,
                ),
            )
        issues = self._checker_issues(result, project_dir, diagnostics)
        return (
            u.Cli.process_succeeded(result.outcome)
            and not any(issue.severity.lower() == "error" for issue in issues),
            issues,
        )


__all__: list[str] = ["FlextInfraGatesMypy"]
