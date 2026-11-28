"""cubic AI-review gate: branch AI review as a native `make check` gate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, p, r, u
from flext_infra.gates import FlextInfraGates

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraGatesCubic(FlextInfraGates):
    """Run one headless cubic branch review and map its findings to issues.

    The gate is applicable only when the host exports ``CUBIC_API_KEY``; without
    it the gate is simply not selected, so it never runs, never passes, and never
    blocks an offline gate. FLEXT reads the variable once at this boundary and
    never stores, logs or sources it.
    """

    gate_id: ClassVar[str] = c.Infra.CUBIC
    gate_name: ClassVar[str] = "cubic AI Review"
    scanner_binary: ClassVar[str] = c.Infra.CUBIC_BINARY
    check_timeout: ClassVar[int] = c.Infra.TIMEOUT_LONG
    union_capable: ClassVar[bool] = True

    @override
    def selected_for(self, project_dir: Path, ctx: p.Infra.GateContext) -> bool:
        """Select the gate only when its headless credential is exported.

        Returns:
            Whether ``CUBIC_API_KEY`` is present in the process environment.

        """
        del project_dir, ctx
        return bool(os.environ.get(c.Infra.CUBIC_API_KEY_ENV))

    @override
    def check(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> p.Infra.GateExecution:
        """Review the project's branch diff once and grade its findings.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        started = time.monotonic()
        binary = self.resolve_binary()
        if binary is None:
            return self._build_project_error_gate_result(
                project_dir,
                (f"{c.Infra.CUBIC_BINARY} binary not found on PATH",),
                ctx,
                started,
                outcome=c.Infra.ToolOutcome.ERROR,
            )
        scan = self._run(
            (binary, *c.Infra.CUBIC_REVIEW_ARGS),
            project_dir,
            ctx,
        )
        return self._parsed_gate_execution(project_dir, ctx, scan, started)

    @override
    def _parse_check_output(
        self,
        result: p.Cli.CommandOutput,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> tuple[bool, Sequence[p.Infra.Issue]]:
        """Parse a JSON review into per-project issues (file-scoped path).

        Returns:
            The resulting ``tuple[bool, Sequence[p.Infra.Issue]]``.

        """
        del project_dir, ctx
        issues = self._report_issues(result)
        return not issues, issues

    @override
    def _check_env(
        self,
        project_dir: Path,
        ctx: p.Infra.GateContext,
    ) -> Mapping[str, str]:
        """Pass the credential and the deterministic headless flags.

        Returns:
            The child environment overlay for this review invocation.

        """
        del project_dir, ctx
        env = dict(c.Infra.CUBIC_HEADLESS_ENV)
        key = os.environ.get(c.Infra.CUBIC_API_KEY_ENV)
        if key:
            env[c.Infra.CUBIC_API_KEY_ENV] = key
        return env

    @staticmethod
    @override
    def _findings_exit_codes() -> tuple[int, ...]:
        """Cubic reports findings with exit status 1.

        Returns:
            The findings statuses cubic declares.

        """
        return (c.Infra.CUBIC_FINDINGS_EXIT_CODE,)

    def _report_issues(
        self,
        scan: p.Cli.CommandOutput,
    ) -> Sequence[p.Infra.Issue]:
        """Grade one review run, keeping tool faults distinct from findings.

        Returns:
            The findings the review reported, or one blocking fault issue.

        """
        if not scan.stdout.strip():
            if u.Cli.process_succeeded(scan.outcome):
                return ()
            return (self._tool_failure_issue(scan),)
        parsed = self._issues_from_report(scan.stdout)
        if parsed.failure:
            return (self._failure_issue(parsed.error),)
        if parsed.value:
            return parsed.value
        if u.Cli.process_succeeded(scan.outcome):
            return ()
        return (self._tool_failure_issue(scan),)

    @classmethod
    def _issues_from_report(cls, text: str) -> p.Result[tuple[p.Infra.Issue, ...]]:
        """Map a cubic ``--json`` review document to canonical issues.

        Returns:
            The resulting ``p.Result[tuple[p.Infra.Issue, ...]]``.

        """
        result_type = r[tuple[p.Infra.Issue, ...]]
        parsed = u.Cli.json_loads(text)
        if parsed.failure:
            return result_type.from_failure(parsed)
        document = u.Cli.json_as_mapping(parsed.value)
        return result_type.ok(
            tuple(
                cls._issue_from_item(item)
                for item in u.Cli.json_deep_mapping_list(document, "issues")
                if item
            ),
        )

    @classmethod
    def _issue_from_item(cls, item: t.JsonMapping) -> p.Infra.Issue:
        """Map one tolerant cubic issue object to a canonical issue.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        location = u.Cli.json_deep_mapping(item, "location")
        return m.Infra.Issue(
            file=cls._first_str(item, location, ("file", "path", "filename"))
            or c.PYPROJECT_FILENAME,
            line=cls._first_int(item, location, ("line", "startLine"), default=1),
            column=cls._first_int(item, location, ("column", "startColumn"), default=0),
            code=cls._first_str(item, location, ("rule", "ruleId", "code", "category"))
            or cls.gate_id,
            message=cls._first_str(
                item, location, ("message", "title", "description", "summary")
            )
            or cls.gate_id,
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )

    @staticmethod
    def _first_str(
        item: t.JsonMapping,
        location: t.JsonMapping,
        keys: Sequence[str],
    ) -> str:
        """First non-empty string among ``keys`` on the item, then its location.

        Returns:
            The first non-empty value, or an empty string.

        """
        for source in (item, location):
            for key in keys:
                value = u.Cli.json_pick_str(source, key)
                if value:
                    return value
        return ""

    @staticmethod
    def _first_int(
        item: t.JsonMapping,
        location: t.JsonMapping,
        keys: Sequence[str],
        *,
        default: int,
    ) -> int:
        """First positive integer among ``keys`` on the item, then its location.

        Returns:
            The first positive value, or ``default``.

        """
        for source in (item, location):
            for key in keys:
                value = u.Cli.json_pick_int(source, key)
                if value > 0:
                    return value
        return default

    def _failure_issue(self, message: str | None) -> p.Infra.Issue:
        """Represent malformed or absent review output as a blocking issue.

        Returns:
            The resulting ``m.Infra.Issue``.

        """
        return m.Infra.Issue(
            file=c.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=c.Infra.ToolOutcome.ERROR.value,
            message=message or "cubic returned no parseable JSON review output",
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )


__all__: list[str] = ["FlextInfraGatesCubic"]
