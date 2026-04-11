"""Base.mk freshness validation service.

Checks that the workspace root base.mk matches the output from the
canonical template generator, detecting template drift.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path
from typing import Annotated, override

from pydantic import Field

from flext_infra import FlextInfraBaseMkGenerator, c, m, r, s, u


class FlextInfraBaseMkValidator(s[bool]):
    """Validates root base.mk freshness against the template generator."""

    generator: Annotated[
        FlextInfraBaseMkGenerator | None,
        Field(
            default=None,
            exclude=True,
            description="Optional generator for freshness comparison",
        ),
    ] = None

    def build_report(self, workspace_root: Path) -> r[m.Infra.ValidationReport]:
        """Validate root base.mk exists and matches generated template output.

        Args:
            workspace_root: Root directory of the workspace.

        Returns:
            r with ValidationReport indicating freshness status.

        """
        try:
            source = workspace_root / c.Infra.BASE_MK
            if not source.exists():
                return r[m.Infra.ValidationReport].ok(
                    m.Infra.ValidationReport(
                        passed=False,
                        violations=["missing root base.mk"],
                        summary="missing root base.mk",
                    ),
                )
            generator = self.generator or FlextInfraBaseMkGenerator()
            gen_result = generator.generate_basemk()
            if gen_result.failure:
                return r[m.Infra.ValidationReport].ok(
                    m.Infra.ValidationReport(
                        passed=False,
                        violations=[
                            gen_result.error or "base.mk generation failed",
                        ],
                        summary="base.mk template generation failed",
                    ),
                )
            generated_hash = u.Cli.sha256_content(gen_result.value)
            existing_hash = u.Cli.sha256_file(source)
            violations: MutableSequence[str] = []
            if generated_hash != existing_hash:
                violations.append(
                    "root base.mk is stale (does not match generated template)",
                )
            passed = not violations
            summary = (
                "root base.mk matches generated template"
                if passed
                else "root base.mk is out of sync with templates"
            )
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=passed,
                    violations=violations,
                    summary=summary,
                ),
            )
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail(
                f"base.mk validation failed: {exc}",
            )

    @override
    def execute(self) -> r[bool]:
        """Execute the basemk validation CLI flow."""
        return self.build_report(self.workspace_root).flat_map(
            lambda report: (
                r[bool].ok(True) if report.passed else r[bool].fail(report.summary)
            )
        )


__all__ = ["FlextInfraBaseMkValidator"]
