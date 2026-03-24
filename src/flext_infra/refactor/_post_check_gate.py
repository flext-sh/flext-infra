from __future__ import annotations

import ast
import sys
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t, u


class PostCheckGate:
    def __init__(self) -> None:
        pass

    def validate(
        self,
        result: m.Infra.Result,
        expected: t.Infra.ContainerDict,
    ) -> tuple[bool, Sequence[str]]:
        errors: MutableSequence[str] = []
        if not result.success:
            if result.error:
                return (False, [result.error])
            return (False, ["transform_failed"])
        if not result.modified:
            return (True, [])
        file_path = result.file_path
        post_checks = u.Infra.string_list(
            expected.get(c.Infra.ReportKeys.POST_CHECKS),
        )
        quality_gates = u.Infra.string_list(expected.get("quality_gates"))
        if self._check_enabled("imports_resolve", post_checks):
            errors.extend(self._validate_imports(file_path))
        source_symbol_raw = expected.get(c.Infra.ReportKeys.SOURCE_SYMBOL, "")
        source_symbol = source_symbol_raw if isinstance(source_symbol_raw, str) else ""
        expected_chain = u.Infra.string_list(
            expected.get("expected_base_chain"),
        )
        if (
            source_symbol
            and expected_chain
            and self._check_enabled("mro_valid", post_checks)
        ):
            errors.extend(self._validate_mro(file_path, source_symbol, expected_chain))
        if self._check_enabled("lsp_diagnostics_clean", quality_gates):
            errors.extend(self._validate_types(file_path))
        return (not errors, errors)

    def _check_enabled(self, check_name: str, checks: Sequence[str]) -> bool:
        return check_name in checks

    def _validate_imports(self, file_path: Path) -> Sequence[str]:
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return [f"parse_error:{file_path}:parse_failed"]
        unresolved: Sequence[str] = [
            f"line_{node.lineno}:invalid_import_from"
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module is None
            and (node.level == 0)
        ]
        return unresolved

    def _validate_mro(
        self,
        file_path: Path,
        class_name: str,
        expected_bases: Sequence[str],
    ) -> Sequence[str]:
        tree = u.Infra.parse_module_ast(file_path)
        if tree is None:
            return [f"mro_parse_error:{file_path}:parse_failed"]
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                actual = [self._base_name(base) for base in node.bases]
                actual_clean = [name for name in actual if name]
                expected_prefix = list(expected_bases)[: len(actual_clean)]
                if actual_clean != expected_prefix:
                    return [
                        f"mro_mismatch:{class_name}:expected={expected_prefix}:actual={actual_clean}",
                    ]
                return []
        return [f"class_not_found:{class_name}"]

    def _validate_types(self, file_path: Path) -> Sequence[str]:
        cmd = [sys.executable, "-m", "py_compile", str(file_path)]
        result = u.Infra.capture(cmd)
        return result.fold(
            on_failure=lambda e: [f"lsp_diagnostics_clean_failed:{e or ''}"],
            on_success=lambda _: [],
        )

    def _base_name(self, base: ast.expr) -> str:
        return u.Infra.ast_extract_base_name(base)


__all__ = ["PostCheckGate"]
