"""Namespace validation service.

AST-based validator enforcing namespace rules 0-2 for flext projects.
Detection-only -- does not auto-fix any files.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import (
    MutableSequence,
)
from pathlib import Path

from flext_infra import (
    FlextInfraNamespaceRules,
    c,
    m,
    p,
    r,
    u,
)


class FlextInfraNamespaceValidator(FlextInfraNamespaceRules):
    """AST-based namespace validator for flext projects (Rules 0-2).

    Validates that each module follows the one-namespace-class-per-file
    convention, constants are centralized in ``constants.py``, and type
    definitions are centralized in ``typings.py``.
    """

    def validate(
        self,
        project_root: Path,
        *,
        scan_tests: bool = False,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate namespace rules 0-2 for all discovered Python files."""
        try:
            files_result = u.Infra.iter_python_files(
                workspace_root=project_root,
                project_roots=[project_root],
                include_tests=scan_tests,
                include_examples=False,
                include_scripts=False,
                include_dynamic_dirs=False,
            )
            if files_result.failure:
                return r[m.Infra.ValidationReport].fail(
                    files_result.error
                    or "Namespace validation failed: discovery failed",
                )
            files = [
                py_file
                for py_file in files_result.value
                if not self._is_exempt_file(py_file)
            ]
            layout = u.Infra.layout(project_root)
            prefix = layout.class_stem if layout is not None else ""
            violations: MutableSequence[str] = []
            for filepath in files:
                tree = self._parse_file(filepath)
                if tree is None:
                    continue
                rel = filepath.relative_to(project_root)
                violations.extend(self.check_rule_0(tree, rel, prefix))
                violations.extend(self.check_rule_1(tree, rel))
                violations.extend(self.check_rule_2(tree, rel))
            passed = not violations
            summary = (
                f"namespace validation passed ({len(files)} files checked)"
                if passed
                else f"{len(violations)} namespace violation(s) found ({len(files)} files checked)"
            )
            return r[m.Infra.ValidationReport].ok(
                m.Infra.ValidationReport(
                    passed=passed,
                    violations=violations,
                    summary=summary,
                ),
            )
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            return r[m.Infra.ValidationReport].fail(
                f"Namespace validation failed: {exc}",
            )

    def _is_exempt_file(self, filepath: Path) -> bool:
        """Check whether a file should be skipped from validation."""
        name = filepath.name
        if name in c.Infra.EXEMPT_FILENAMES:
            return True
        return any(name.startswith(prefix) for prefix in c.Infra.EXEMPT_PREFIXES)

    def _parse_file(self, path: Path) -> ast.Module | None:
        """Parse a Python file into an AST, returning None on failure."""
        try:
            return ast.parse(path.read_text(encoding=c.Infra.ENCODING_DEFAULT))
        except (OSError, SyntaxError):
            return None


__all__: list[str] = ["FlextInfraNamespaceValidator"]
