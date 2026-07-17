"""Base.mk freshness validation service.

Checks that the canonical base.mk owner matches the output from the template
generator, detecting template drift in workspace and standalone modes.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.base import s
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator


class FlextInfraBaseMkValidator(s[bool]):
    """Validate canonical base.mk freshness against the template generator."""

    generator: Annotated[
        FlextInfraBaseMkGenerator | None,
        m.Field(
            exclude=True, description="Optional generator for freshness comparison"
        ),
    ] = None

    def build_report(self, workspace_root: Path) -> p.Result[p.Infra.ValidationReport]:
        """Validate that canonical base.mk matches generated template output.

        Args:
            workspace_root: Root directory of the workspace.

        Returns:
            r with ValidationReport indicating freshness status.

        """
        try:
            source = self._canonical_source(workspace_root)
        except OSError as exc:
            return r[p.Infra.ValidationReport].fail_op("base.mk validation", exc)
        if not source.exists():
            return r[p.Infra.ValidationReport].ok(self._missing_source_report(source))
        return self._compare_with_generated(source)

    @staticmethod
    def _canonical_source(workspace_root: Path) -> Path:
        """Return the base.mk path owned by the detected execution mode."""
        # mro-wkii.17.26: Validate the same sole owner selected by workspace sync.
        infra_project = workspace_root / c.Infra.PACKAGE_IMPORT_NAME.replace("_", "-")
        owner = (
            infra_project
            if (infra_project / c.PYPROJECT_FILENAME).is_file()
            else workspace_root
        )
        return owner / c.Infra.BASE_MK

    @staticmethod
    def _missing_source_report(source: Path) -> p.Infra.ValidationReport:
        """Return the canonical missing-base.mk report."""
        violation = f"missing canonical base.mk: {source}"
        return m.Infra.ValidationReport(
            passed=False, violations=[violation], summary=violation
        )

    def _compare_with_generated(
        self, source: Path
    ) -> p.Result[p.Infra.ValidationReport]:
        """Compare source base.mk with freshly generated content."""
        generator = self.generator or FlextInfraBaseMkGenerator()
        gen_result = generator.generate_basemk()
        if gen_result.failure:
            return r[p.Infra.ValidationReport].ok(
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
            return r[p.Infra.ValidationReport].fail_op("base.mk validation", exc)
        return r[p.Infra.ValidationReport].ok(
            self._build_freshness_report(existing_hash, generated_hash)
        )

    @staticmethod
    def _base_mk_hash_pair(source: Path, generated: str) -> t.StrPair:
        """Return existing/generated SHA256 pair for base.mk freshness checks."""
        return u.Cli.sha256_file(source), u.Cli.sha256_content(generated)

    @staticmethod
    def _build_freshness_report(
        existing_hash: str, generated_hash: str
    ) -> p.Infra.ValidationReport:
        """Build freshness validation report from hash comparison."""
        violations: t.MutableSequenceOf[str] = []
        if generated_hash != existing_hash:
            violations.append(
                "canonical base.mk is stale (does not match generated template)"
            )
        passed = not violations
        summary = (
            "canonical base.mk matches generated template"
            if passed
            else "canonical base.mk is out of sync with templates"
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
