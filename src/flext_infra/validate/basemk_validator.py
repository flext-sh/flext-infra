"""Base.mk freshness validation service.

Checks that the workspace root base.mk matches the output from the
canonical template generator, detecting template drift.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, m, u
from flext_infra.base import s
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraBaseMkValidator(s[bool]):
    """Validates root base.mk freshness against the template generator."""

    generator: Annotated[
        FlextInfraBaseMkGenerator | None,
        m.Field(
            exclude=True, description="Optional generator for freshness comparison"
        ),
    ] = None

    def build_report(self, workspace_root: Path) -> p.Result[m.Infra.ValidationReport]:
        """Validate root base.mk exists and matches generated template output.

        Args:
            workspace_root: Root directory of the workspace.

        Returns:
            r with ValidationReport indicating freshness status.

        """
        try:
            source = workspace_root / c.Infra.BASE_MK
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail_op("base.mk validation", exc)
        if not source.exists():
            return r[m.Infra.ValidationReport].ok(self._missing_source_report())
        return self._compare_with_generated(source)

    @staticmethod
    def _missing_source_report() -> m.Infra.ValidationReport:
        """Return the canonical missing-root-base.mk report."""
        return m.Infra.ValidationReport(
            passed=False,
            violations=["missing root base.mk"],
            summary="missing root base.mk",
        )

    def _compare_with_generated(
        self, source: Path
    ) -> p.Result[m.Infra.ValidationReport]:
        """Compare source base.mk with freshly generated content."""
        generator = self.generator or FlextInfraBaseMkGenerator()
        gen_result = generator.generate_basemk()
        if gen_result.failure:
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=False,
                    violations=[gen_result.error or "base.mk generation failed"],
                    summary="base.mk template generation failed",
                )
            )
        try:
            existing_hash, generated_hash = self._base_mk_hash_pair(
                source, gen_result.value
            )
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail_op("base.mk validation", exc)
        return r[m.Infra.ValidationReport].ok(
            self._build_freshness_report(existing_hash, generated_hash)
        )

    @staticmethod
    def _base_mk_hash_pair(source: Path, generated: str) -> t.StrPair:
        """Return existing/generated SHA256 pair for base.mk freshness checks."""
        return u.Cli.sha256_file(source), u.Cli.sha256_content(generated)

    @staticmethod
    def _build_freshness_report(
        existing_hash: str, generated_hash: str
    ) -> m.Infra.ValidationReport:
        """Build freshness validation report from hash comparison."""
        violations: t.MutableSequenceOf[str] = []
        if generated_hash != existing_hash:
            violations.append(
                "root base.mk is stale (does not match generated template)"
            )
        passed = not violations
        summary = (
            "root base.mk matches generated template"
            if passed
            else "root base.mk is out of sync with templates"
        )
        return m.Infra.ValidationReport(
            passed=passed, violations=violations, summary=summary
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the basemk validation CLI flow."""
        report_result = self.build_report(self.workspace_root)
        if report_result.failure:
            return r[bool].fail(report_result.error or "base.mk validation failed")
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)


__all__: list[str] = ["FlextInfraBaseMkValidator"]
