"""AST parent-package resolution for lazy-init planning."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra.constants import c

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.typings import t


class FlextInfraCodegenLazyInitPlannerParentAstMixin:
    """Private AST helpers for constants parent discovery."""

    if TYPE_CHECKING:

        def _module_file(self, module_path: str) -> Path | None: ...

        @staticmethod
        def _module_path_from_target(target: str) -> str: ...

        def _parents_from_constants_module(
            self,
            module_path: Path,
            current_pkg: str,
            visited: set[str] | None = None,
        ) -> t.StrSequence: ...

        def _package_name_from_target(self, target: str) -> str: ...

    def _parents_from_constants_ast(
        self,
        module_path: Path,
        current_pkg: str,
        visited: set[str],
    ) -> t.StrSequence:
        """Extract parent packages from the constants module AST."""
        tree = ast.parse(
            module_path.read_text(encoding=c.Cli.ENCODING_DEFAULT),
            filename=str(module_path),
        )
        imports = self._ast_import_targets(tree)
        base_packages = tuple(
            package_name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and "Constants" in node.name
            for base in node.bases
            if (
                package_name := self._package_name_from_target(
                    imports.get(self._ast_dotted_name(base), ""),
                )
            )
        )
        declared_packages = tuple(
            package_name
            for target in imports.values()
            if (package_name := self._package_name_from_target(target))
            and package_name != current_pkg
        )
        same_package_parents = tuple(
            parent
            for target in imports.values()
            if target.startswith(f"{current_pkg}.")
            and (
                module_file := self._module_file(self._module_path_from_target(target))
            )
            is not None
            and str(module_file.resolve()) not in visited
            for parent in self._parents_from_constants_module(
                module_file,
                current_pkg,
                visited,
            )
        )
        return tuple(
            dict.fromkeys(
                package_name
                for package_name in (
                    *base_packages,
                    *declared_packages,
                    *same_package_parents,
                )
                if package_name and package_name != current_pkg
            ),
        )

    @staticmethod
    def _ast_import_targets(tree: ast.AST) -> t.StrMapping:
        """Return local import-name targets from one parsed module AST."""
        targets: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    targets[local_name] = f"{node.module}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    local_name = alias.asname or alias.name.partition(".")[0]
                    targets[local_name] = alias.name
        return targets

    @classmethod
    def _ast_dotted_name(cls, node: ast.AST) -> str:
        """Return the dotted name represented by an AST expression."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = cls._ast_dotted_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerParentAstMixin"]
