"""Canonical alias quality gate (ENFORCE-080).

Flags imports of canonical short aliases (c/m/p/t/u) from ``flext_core`` inside
projects that re-export those aliases locally. Auto-fix rewrites them to the
project's own facade modules.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import ClassVar, override

from flext_infra.constants import c
from flext_infra.detectors.compatibility_alias_detector import (
    FlextInfraCompatibilityAliasDetector,
)
from flext_infra.gates.base_gate import FlextInfraGate
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraCanonicalAliasGate(FlextInfraGate):
    """Detect and fix foreign canonical alias imports (ENFORCE-080)."""

    gate_id: ClassVar[str] = "canonical-alias"
    gate_name: ClassVar[str] = "Canonical Alias"
    can_fix: ClassVar[bool] = True
    tool_name: ClassVar[str] = "Flext Canonical Alias Detector"
    tool_url: ClassVar[str] = "internal://flext-infra/canonical-alias"

    # Packages that define the canonical aliases themselves. Rewriting imports
    # inside them risks creating import cycles during package initialization.
    _ALIAS_SOURCE_PACKAGES: ClassVar[frozenset[str]] = frozenset({
        c.Infra.PKG_CORE_UNDERSCORE,
        "flext_cli",
    })

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Scan one project's Python sources for ENFORCE-080 violations."""
        _ = ctx
        started = time.monotonic()
        if project_dir.name in self._ALIAS_SOURCE_PACKAGES:
            return self._skip_result(project_dir, started)
        files_result = u.Infra.iter_python_files(
            project_dir,
            project_roots=[project_dir],
            include_tests=False,
        )
        if files_result.failure:
            issue = m.Infra.Issue(
                file=c.Infra.PYPROJECT_FILENAME,
                line=1,
                column=1,
                code=self.gate_id,
                message=files_result.error or "canonical-alias scan failed",
            )
            return self._build_gate_result(
                result=m.Infra.GateResult(
                    gate=self.gate_id,
                    project=project_dir.name,
                    passed=False,
                    errors=[issue.formatted],
                    duration=round(time.monotonic() - started, 3),
                ),
                issues=[issue],
                raw_output=issue.message,
                ctx=ctx,
            )

        rope_project = u.Infra.init_rope_project(project_dir)
        try:
            issues: list[m.Infra.Issue] = []
            for file_path in files_result.value:
                for violation in FlextInfraCompatibilityAliasDetector.detect_file(
                    m.Infra.DetectorContext(
                        file_path=file_path,
                        project_root=project_dir,
                        rope_project=rope_project,
                        project_name=project_dir.name,
                    )
                ):
                    if (
                        violation.module_name
                        != u.Infra.package_name(file_path).split(".", maxsplit=1)[0]
                    ):
                        continue
                    issues.append(
                        m.Infra.Issue(
                            file=str(file_path),
                            line=violation.line,
                            column=1,
                            code=self.gate_id,
                            message=(
                                f"canonical alias '{violation.alias_name}' "
                                f"imported from flext_core; use "
                                f"from {violation.module_name}.<facade> import "
                                f"{violation.alias_name}"
                            ),
                            severity="ERROR",
                        )
                    )
        finally:
            rope_project.close()

        return self._build_gate_result(
            result=m.Infra.GateResult(
                gate=self.gate_id,
                project=project_dir.name,
                passed=len(issues) == 0,
                errors=[issue.formatted for issue in issues],
                duration=round(time.monotonic() - started, 3),
            ),
            issues=issues,
            raw_output="\n".join(issue.formatted for issue in issues),
            ctx=ctx,
        )

    @override
    def fix(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Apply ENFORCE-080 rewrites for the selected project."""
        if ctx.check_only or not ctx.apply_fixes:
            return self._check_only_fix_result(project_dir)
        started = time.monotonic()
        if project_dir.name in self._ALIAS_SOURCE_PACKAGES:
            return self._skip_result(project_dir, started)
        files_result = u.Infra.iter_python_files(
            project_dir,
            project_roots=[project_dir],
            include_tests=False,
        )
        if files_result.failure:
            return self._build_gate_result(
                result=m.Infra.GateResult(
                    gate=self.gate_id,
                    project=project_dir.name,
                    passed=False,
                    errors=[files_result.error or "canonical-alias fix failed"],
                    duration=round(time.monotonic() - started, 3),
                ),
                issues=[],
                raw_output=files_result.error or "canonical-alias fix failed",
            )

        rope_project = u.Infra.init_rope_project(project_dir)
        try:
            violations: list[m.Infra.CompatibilityAliasViolation] = []
            for file_path in files_result.value:
                for violation in FlextInfraCompatibilityAliasDetector.detect_file(
                    m.Infra.DetectorContext(
                        file_path=file_path,
                        project_root=project_dir,
                        rope_project=rope_project,
                        project_name=project_dir.name,
                    )
                ):
                    if (
                        violation.module_name
                        != u.Infra.package_name(file_path).split(".", maxsplit=1)[0]
                    ):
                        continue
                    violations.append(violation)

            if violations:
                u.Infra.rewrite_foreign_canonical_alias_violations(
                    rope_project=rope_project,
                    violations=violations,
                    parse_failures=[],
                )
        finally:
            rope_project.close()

        return self.check(project_dir, ctx)

    @override
    def _build_check_command(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
        check_dirs: t.StrSequence,
    ) -> t.StrSequence:
        """No external tool — execution happens in ``check``."""
        _ = project_dir, ctx, check_dirs
        return []

    @override
    def _parse_check_output(
        self,
        result: m.Cli.CommandOutput,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> tuple[bool, t.SequenceOf[m.Infra.Issue]]:
        """Unused — ``check`` is overridden directly."""
        _ = result, project_dir, ctx
        return True, ()


__all__: list[str] = ["FlextInfraCanonicalAliasGate"]
