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
    Sequence,
)
from pathlib import Path

from flext_infra import (
    FlextInfraConstantsSharedInfra,
    FlextInfraModelsCore,
    FlextInfraNamespaceRules,
    FlextInfraUtilitiesParsing,
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

    @staticmethod
    def derive_prefix(project_root: Path) -> str:
        """Public wrapper for deriving the class name prefix from a project."""
        layout = u.Infra.layout(project_root)
        return layout.class_stem if layout is not None else ""

    def validate(
        self,
        project_root: Path,
        *,
        scan_tests: bool = False,
    ) -> p.Result[FlextInfraModelsCore.ValidationReport]:
        """Validate namespace rules 0-2 for all discovered Python files."""
        try:
            files = self._discover_files(project_root, scan_tests=scan_tests)
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
            return r[FlextInfraModelsCore.ValidationReport].ok(
                FlextInfraModelsCore.ValidationReport(
                    passed=passed,
                    violations=violations,
                    summary=summary,
                ),
            )
        except (OSError, TypeError, ValueError, RuntimeError) as exc:
            return r[FlextInfraModelsCore.ValidationReport].fail(
                f"Namespace validation failed: {exc}",
            )

    def _discover_files(
        self,
        workspace_root: Path,
        *,
        scan_tests: bool,
    ) -> Sequence[Path]:
        """Walk ``src/`` (and optionally ``tests/``) for non-exempt .py files."""
        result: MutableSequence[Path] = []
        dirs_to_scan = [
            workspace_root / FlextInfraConstantsSharedInfra.DEFAULT_SRC_DIR,
        ]
        if scan_tests:
            dirs_to_scan.append(
                workspace_root / FlextInfraConstantsSharedInfra.DIR_TESTS,
            )
        for base_dir in dirs_to_scan:
            if not base_dir.is_dir():
                continue
            result.extend(
                py_file
                for py_file in u.Infra.iter_directory_python_files(
                    base_dir,
                )
                if not self._is_exempt_file(py_file)
            )
        return sorted(result)

    def _is_exempt_file(self, filepath: Path) -> bool:
        """Check whether a file should be skipped from validation."""
        name = filepath.name
        if name in FlextInfraConstantsSharedInfra.EXEMPT_FILENAMES:
            return True
        return any(
            name.startswith(prefix)
            for prefix in FlextInfraConstantsSharedInfra.EXEMPT_PREFIXES
        )

    def _parse_file(self, path: Path) -> ast.Module | None:
        """Parse a Python file into an AST, returning None on failure."""
        return FlextInfraUtilitiesParsing.parse_module_ast(path)


__all__: list[str] = ["FlextInfraNamespaceValidator"]
