"""Namespace validation service.

AST-based validator enforcing namespace rules 0-2 for flext projects.
Detection-only -- does not auto-fix any files.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import FlextInfraNamespaceRules, c, m, t, u

__all__ = ["FlextInfraNamespaceValidator"]


class FlextInfraNamespaceValidator(FlextInfraNamespaceRules):
    """AST-based namespace validator for flext projects (Rules 0-2).

    Validates that each module follows the one-namespace-class-per-file
    convention, constants are centralized in ``constants.py``, and type
    definitions are centralized in ``typings.py``.
    """

    @staticmethod
    def _derive_prefix(project_root: Path) -> str:
        """Derive the expected class name prefix from the package directory."""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                return "".join(part.title() for part in child.name.split("_"))
        return ""

    @staticmethod
    def derive_prefix(project_root: Path) -> str:
        """Public wrapper for deriving the class name prefix from a project."""
        return FlextInfraNamespaceValidator._derive_prefix(project_root)

    def validate(
        self,
        project_root: Path,
        *,
        scan_tests: bool = False,
    ) -> r[m.Infra.ValidationReport]:
        """Validate namespace rules 0-2 for all discovered Python files."""
        try:
            files = self._discover_files(project_root, scan_tests=scan_tests)
            prefix = self._derive_prefix(project_root)
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

    def _discover_files(
        self,
        workspace_root: Path,
        *,
        scan_tests: bool,
    ) -> Sequence[Path]:
        """Walk ``src/`` (and optionally ``tests/``) for non-exempt .py files."""
        result: MutableSequence[Path] = []
        dirs_to_scan = [workspace_root / c.Infra.Paths.DEFAULT_SRC_DIR]
        if scan_tests:
            dirs_to_scan.append(workspace_root / c.Infra.Directories.TESTS)
        for base_dir in dirs_to_scan:
            if not base_dir.is_dir():
                continue
            result.extend(
                py_file
                for py_file in u.Infra.iter_directory_python_files(base_dir)
                if not self._is_exempt_file(py_file)
            )
        return sorted(result)

    def _is_exempt_file(self, filepath: Path) -> bool:
        """Check whether a file should be skipped from validation."""
        name = filepath.name
        if name in c.Infra.EXEMPT_FILENAMES:
            return True
        return any(name.startswith(pfx) for pfx in c.Infra.EXEMPT_PREFIXES)

    def _parse_file(self, path: Path) -> t.Infra.AstModule | None:
        """Parse a Python file into an AST, returning None on failure."""
        return u.Infra.parse_module_ast(path)
