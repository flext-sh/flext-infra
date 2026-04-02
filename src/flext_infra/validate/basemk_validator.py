"""Base.mk freshness validation service.

Checks that the workspace root base.mk matches the output from the
canonical template generator, detecting template drift.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

from flext_infra import FlextInfraBaseMkGenerator, c, m, r, u


class FlextInfraBaseMkValidator:
    """Validates root base.mk freshness against the template generator."""

    def __init__(
        self,
        generator: FlextInfraBaseMkGenerator | None = None,
    ) -> None:
        """Initialize with optional generator for freshness comparison."""
        self._generator = generator or FlextInfraBaseMkGenerator()

    _sha256 = staticmethod(u.Infra.sha256_content)
    _sha256_file = staticmethod(u.Infra.sha256_file)

    def validate(self, workspace_root: Path) -> r[m.Infra.ValidationReport]:
        """Validate root base.mk exists and matches generated template output.

        Args:
            workspace_root: Root directory of the workspace.

        Returns:
            r with ValidationReport indicating freshness status.

        """
        try:
            source = workspace_root / c.Infra.Files.BASE_MK
            if not source.exists():
                return r[m.Infra.ValidationReport].ok(
                    m.Infra.ValidationReport(
                        passed=False,
                        violations=["missing root base.mk"],
                        summary="missing root base.mk",
                    ),
                )
            gen_result = self._generator.generate_basemk()
            if gen_result.is_failure:
                return r[m.Infra.ValidationReport].ok(
                    m.Infra.ValidationReport(
                        passed=False,
                        violations=[
                            gen_result.error or "base.mk generation failed",
                        ],
                        summary="base.mk template generation failed",
                    ),
                )
            generated_hash = self._sha256(gen_result.value)
            existing_hash = self._sha256_file(source)
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


__all__ = ["FlextInfraBaseMkValidator"]
