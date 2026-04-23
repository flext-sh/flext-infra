"""Guard 2/3 — lazy-init map freshness validator.

Drives the existing ROPE-backed ``FlextInfraCodegenLazyInit`` generator
in check-only mode. Any ``__init__.py`` whose rendered content differs
from the current on-disk content is a stale lazy-map violation. This
closes the recurring failure mode where developers add ``models/x.py``
(or similar) but skip ``make gen``, leaving the lazy map incomplete
until first attribute access trips a cycle.

Mandate: 100% ROPE-based per flext-infra detector mandate — the check
delegates to the existing codegen pipeline which uses rope internally
via the ``u.Infra`` boundary.

Architecture: flext-infra validate layer — wraps flext-infra codegen.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from pathlib import Path
from typing import override

from flext_infra import FlextInfraCodegenLazyInit, m, p, r, s, t


class FlextInfraValidateLazyMapFreshness(s[bool]):
    """Flags ``__init__.py`` files whose lazy maps are out of sync with siblings."""

    def build_report(
        self,
        workspace_root: Path,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Run the lazy-init generator in check-only mode, collect stale inits.

        Args:
            workspace_root: Root directory under which to scan packages.

        Returns:
            r with ValidationReport listing each stale ``__init__.py`` as a violation.

        """
        generator = FlextInfraCodegenLazyInit.model_validate(
            {"workspace_root": workspace_root},
        )
        try:
            errors = generator.generate_inits(check_only=True)
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail(
                f"lazy-map freshness scan failed: {exc}",
            )
        if errors > 0:
            return r[m.Infra.ValidationReport].fail(
                f"lazy-map freshness scan errored in {errors} package(s)",
            )
        modified = tuple(generator.modified_files)
        violations: MutableSequence[str] = [
            f"stale lazy map: {path}" for path in modified
        ]
        passed = not violations
        summary = (
            "all __init__.py files are fresh (lazy maps in sync with siblings)"
            if passed
            else f"{len(violations)} stale __init__.py file(s) — run 'make gen'"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=violations,
                summary=summary,
            ),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the freshness validation using ``self.workspace_root``."""
        report_result = self.build_report(self.workspace_root)
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "lazy-map freshness validation failed",
            )
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)


__all__: t.StrSequence = ["FlextInfraValidateLazyMapFreshness"]
