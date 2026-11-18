"""Project namespace validation through the one rule engine.

The namespace laws are rule data (the ast-grep rule catalog and the
project's generated utilities and file scopes); this service reports one
project's findings of that catalog in the declared namespace scope. It owns
no rule.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from flext_infra import m, p, r, s, u
from flext_infra.codemod import FlextInfraModGateEngine


class FlextInfraNamespaceValidator(s[bool]):
    """Report one project's rule-catalog findings in its namespace scope."""

    @override
    def execute(self) -> p.Result[bool]:
        """Execute namespace validation for the configured repository root.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        report_result = self.build_report()
        if report_result.failure:
            return r[bool].from_failure(report_result)
        return r[bool].ok(report_result.value.passed)

    def build_report(self) -> p.Result[p.Infra.ValidationReport]:
        """Scan the project with the rule engine and report its findings.

        Each violation reads ``[<rule-id>] <file>:<line> — <message>``. The
        scope is the canonical governed source inventory. Configured directory
        declarations never suppress findings in other active Python sources.

        Returns:
            The resulting ``p.Result[p.Infra.ValidationReport]``.

        """
        project_root = self.repository_root.resolve()
        scanned = FlextInfraModGateEngine.scan(project_root, fix=False)
        if scanned.failure:
            return r[p.Infra.ValidationReport].from_failure(scanned)
        violations = tuple(
            f"[{entry.rule_id}] {entry.file.as_posix()}:"
            f"{u.Infra.codemod_finding_start(entry)[0] + 1} — {self._message(entry)}"
            for entry in scanned.value.entries
        )
        passed = not violations
        return r[p.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=violations,
                summary=(
                    "namespace validation passed"
                    if passed
                    else f"{len(violations)} namespace violation(s) found"
                ),
            ),
        )

    @staticmethod
    def _message(entry: p.Infra.ModScanFinding) -> str:
        """Return the rule's message for one finding.

        Returns:
            The rule's message for one finding.

        Raises:
            TypeError: If ast-grep finding without a message.

        """
        message = entry.message
        if message is None:
            msg = f"ast-grep finding without a message: {entry.rule_id}"
            raise TypeError(msg)
        return " ".join(message.split())


__all__: Sequence[str] = ("FlextInfraNamespaceValidator",)
