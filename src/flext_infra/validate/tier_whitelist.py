"""Guard 5 — tier / abstraction-boundary enforcer.

Enforces AGENTS.md §2.7 and §4 abstraction-boundary rules: flext-core is
the sole owner of pydantic, structlog, returns, orjson, pyyaml, and
dependency_injector. Any runtime import of these outside
``flext-core/src/`` is a violation.

Uses rope's semantic import resolution so ``if TYPE_CHECKING:`` imports
are automatically exempt (they live in conditional blocks that rope
skips when collecting runtime imports).

Mandate: 100% ROPE-based per the flext-infra detector mandate — no raw
``ast``/``libcst`` source analysis. Uses
``u.Infra`` Rope boundary helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p, r, s, t, u


class FlextInfraValidateTierWhitelist(s[bool]):
    """Enforces the flext-core abstraction boundary at runtime-import level.

    Banned-lib set and canonical-wrapper allowlist are sourced from
    ``c.Infra.BANNED_RUNTIME_LIBS`` and
    ``c.Infra.TIER_WHITELIST_ALLOWLIST_MARKERS`` (SSOT) — no parallel lists
    inside the validator.
    """

    NON_RUNTIME_DIR_PARTS: ClassVar[frozenset[str]] = frozenset({
        c.Infra.DIR_TESTS,
        c.Infra.DIR_EXAMPLES,
        c.Infra.DIR_SCRIPTS,
    })

    def build_report(
        self,
        workspace_root: Path,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Scan ``workspace_root`` for runtime imports of banned libs outside flext-core.

        Args:
            workspace_root: Path under which to open a rope Project.

        Returns:
            r with ValidationReport listing each boundary-breaking import.

        """
        try:
            violations = self._collect_violations(workspace_root)
        except OSError as exc:
            return r[m.Infra.ValidationReport].fail(
                f"tier-whitelist scan failed: {exc}",
            )
        passed = not violations
        summary = (
            "abstraction boundary respected (flext-core-only libs not imported elsewhere)"
            if passed
            else f"{len(violations)} abstraction-boundary violation(s)"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=list(violations),
                summary=summary,
            ),
        )

    def _collect_violations(
        self,
        workspace_root: Path,
    ) -> t.StrSequence:
        """Traverse the rope project and accumulate boundary breaks."""
        violations: MutableSequence[str] = []
        with u.Infra.open_project(workspace_root) as project:
            for resource in u.Infra.python_resources(project):
                file_path = u.Infra.resource_file_path(
                    project,
                    resource,
                )
                if file_path is None or self._is_allowlisted(file_path):
                    continue
                module_imports = u.Infra.get_module_imports(
                    project,
                    resource,
                )
                if module_imports is None:
                    continue
                violations.extend(
                    self._violations_for_module(file_path, module_imports),
                )
        return tuple(violations)

    def _is_allowlisted(self, file_path: Path) -> bool:
        """Return True iff ``file_path`` is a canonical wrapper or non-runtime surface.

        Sources the canonical-wrapper marker list from
        ``c.Infra.TIER_WHITELIST_ALLOWLIST_MARKERS`` (SSOT). Also exempts
        ``tests/``, ``examples/``, and ``scripts/`` directories — only
        runtime ``src/`` modules are gated by the abstraction boundary.
        """
        posix = file_path.as_posix()
        if any(marker in posix for marker in c.Infra.TIER_WHITELIST_ALLOWLIST_MARKERS):
            return True
        return any(part in self.NON_RUNTIME_DIR_PARTS for part in file_path.parts)

    def _violations_for_module(
        self,
        file_path: Path,
        module_imports: t.Infra.RopeModuleImports,
    ) -> t.StrSequence:
        """Return violation strings for a single module's rope ImportInfo set."""
        out: MutableSequence[str] = []
        for import_statement in u.Infra.import_statements(module_imports):
            module_name = u.Infra.import_statement_module_name(import_statement)
            if module_name is not None:
                top = self._top_module(module_name)
                if top in c.Infra.BANNED_RUNTIME_LIBS:
                    out.append(
                        f"{file_path}: bare import of {module_name!r} "
                        "— use flext_core facades (c/m/p/t/u)",
                    )
                continue
            for imported, _alias in u.Infra.import_statement_names_and_aliases(
                import_statement,
            ):
                top = self._top_module(imported)
                if top in c.Infra.BANNED_RUNTIME_LIBS:
                    out.append(
                        f"{file_path}: bare import of {imported!r} "
                        "— use flext_core facades (c/m/p/t/u)",
                    )
        return tuple(out)

    @staticmethod
    def _top_module(module_name: str | None) -> str:
        """Return the top-level package name for an import path (``a.b.c`` → ``a``)."""
        if not module_name:
            return ""
        return module_name.split(".", maxsplit=1)[0]

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the tier-whitelist validation using ``self.workspace_root``."""
        report_result = self.build_report(self.workspace_root)
        if report_result.failure:
            return r[bool].fail(
                report_result.error or "tier-whitelist validation failed",
            )
        report = report_result.unwrap()
        return r[bool].ok(True) if report.passed else r[bool].fail(report.summary)


__all__: t.StrSequence = ["FlextInfraValidateTierWhitelist"]
