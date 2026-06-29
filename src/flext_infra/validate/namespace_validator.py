"""Namespace validation service.

Rope-backed validator enforcing namespace rules 0-3 for flext projects.
Detection-only — does not auto-fix any files. AST nodes are obtained via
``rope.get_pymodule(...).get_ast()`` per the flext-infra detector mandate
(no raw ``ast.parse`` source reads).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.validate.namespace_rules import FlextInfraNamespaceRules


class FlextInfraNamespaceValidator(FlextInfraNamespaceRules):
    """Rope-backed namespace validator for flext projects (Rules 0-3).

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
        """Validate namespace rules 0-3 for all discovered Python files."""
        try:
            return self._validate_project_namespace(
                project_root,
                scan_tests=scan_tests,
            )
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[m.Infra.ValidationReport].fail_op("Namespace validation", exc)

    def _validate_project_namespace(
        self,
        project_root: Path,
        *,
        scan_tests: bool,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate namespace rules inside one project."""
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
                files_result.error or "Namespace validation failed: discovery failed",
            )
        files = [
            py_file
            for py_file in files_result.value
            if not self._is_exempt_file(py_file)
        ]
        layout = u.Infra.layout(project_root)
        prefix = layout.class_stem if layout is not None else ""
        package_name = (
            layout.package_dir.name
            if layout is not None
            else project_root.name.replace("-", "_")
        )
        violations: t.MutableSequenceOf[str] = []
        with u.Infra.open_project(project_root) as rope_project:
            for filepath in files:
                tree_result = self._parse_file(rope_project, filepath)
                if tree_result.failure:
                    continue
                tree = tree_result.value
                rel = filepath.relative_to(project_root)
                if self._is_namespace_governed_file(rel):
                    violations.extend(self.check_rule_0(tree, rel, prefix))
                    violations.extend(self.check_rule_1(tree, rel))
                    violations.extend(self.check_rule_2(tree, rel))
                violations.extend(
                    self.check_rule_3(
                        tree,
                        rel,
                        class_stem=prefix,
                        package_name=package_name,
                    )
                )
        return self._validation_report(files=files, violations=violations)

    @staticmethod
    def _validation_report(
        *,
        files: t.SequenceOf[Path],
        violations: t.SequenceOf[str],
    ) -> p.Result[m.Infra.ValidationReport]:
        """Build the namespace validation report."""
        passed = not violations
        summary = (
            f"namespace validation passed ({len(files)} files checked)"
            if passed
            else f"{len(violations)} namespace violation(s) found ({len(files)} files checked)"
        )
        return r[m.Infra.ValidationReport].ok(
            m.Infra.ValidationReport(
                passed=passed,
                violations=tuple(violations),
                summary=summary,
            ),
        )

    def _is_exempt_file(self, filepath: Path) -> bool:
        """Check whether a file should be skipped from validation."""
        name = filepath.name
        if name in c.Infra.EXEMPT_FILENAMES:
            return True
        return any(name.startswith(prefix) for prefix in c.Infra.EXEMPT_PREFIXES)

    def _parse_file(
        self,
        rope_project: t.Infra.RopeProject,
        path: Path,
    ) -> p.Result[ast.AST]:
        """Return the AST module for ``path`` via rope.

        ``r.ok(module)`` on success. ``r.fail(reason)`` when the resource
        cannot be fetched, the module fails to parse, or rope returns no
        ``PyModule``. Callers that want "skip silently" can collapse with
        ``unwrap_or(None)`` or ``.failure``.
        """
        try:
            resource = u.Infra.fetch_python_resource(rope_project, path)
        except c.EXC_OS_SYNTAX as exc:
            return r[ast.AST].fail(f"fetch_python_resource raised: {exc!s}")
        if resource is None:
            return r[ast.AST].fail(f"no rope resource for {path}")
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
        except c.EXC_OS_SYNTAX as exc:
            return r[ast.AST].fail(f"get_pymodule raised: {exc!s}")
        ast_module = pymodule.get_ast()
        if ast_module is None:
            return r[ast.AST].fail(f"pymodule has no AST for {path}")
        return r[ast.AST].ok(ast_module)

    def _is_namespace_governed_file(self, rel_path: Path) -> bool:
        """Return whether NS-000/001/002 structural rules apply to this file."""
        if rel_path.name in {
            c.Infra.CONSTANTS_PY,
            c.Infra.MODELS_PY,
            c.Infra.PROTOCOLS_PY,
            c.Infra.TYPINGS_PY,
            c.Infra.UTILITIES_PY,
        }:
            return True
        return any(
            part
            in {
                "_constants",
                "_models",
                "_protocols",
                "_typings",
                "_utilities",
            }
            for part in rel_path.parts
        )


__all__: list[str] = ["FlextInfraNamespaceValidator"]
