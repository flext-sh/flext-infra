from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path

import libcst as cst

from flext_infra import c
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class NamespaceFacadeScanner:
    """Scan projects for namespace facade class patterns."""

    @classmethod
    def scan_project(
        cls,
        *,
        project_root: Path,
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.FacadeStatus]:
        """Scan a project for namespace facade classes and return their status."""
        results: list[nem.FacadeStatus] = []
        class_stem = cls.project_class_stem(project_name=project_name)
        for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
            expected_class = f"{class_stem}{suffix}"
            found_class, found_file, symbol_count = cls._find_facade_class(
                project_root=project_root,
                family=family,
                expected_class=expected_class,
                suffix=suffix,
                _parse_failures=parse_failures,
            )
            results.append(
                nem.FacadeStatus.create(
                    family=family,
                    exists=bool(found_class),
                    class_name=found_class,
                    file=found_file,
                    symbol_count=symbol_count,
                ),
            )
        return results

    @classmethod
    def _find_facade_class(
        cls,
        *,
        project_root: Path,
        family: str,
        expected_class: str,
        suffix: str,
        _parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> tuple[str, str, int]:
        file_pattern = c.Infra.FAMILY_FILES[family]
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ("", "", 0)
        for file_path in src_dir.rglob(file_pattern):
            try:
                tree = cst.parse_module(file_path.read_text())
            except (OSError, cst.ParserSyntaxError):
                continue
            for node in cls._walk_classes(tree.body):
                class_name = node.name.value
                if class_name == expected_class or class_name.endswith(suffix):
                    symbol_count = cls._count_class_symbols(node)
                    return (class_name, str(file_path), symbol_count)
        return ("", "", 0)

    @classmethod
    def _count_class_symbols(cls, node: cst.ClassDef) -> int:
        if not isinstance(node.body, cst.IndentedBlock):
            return 0
        count = 0
        for child in node.body.body:
            if isinstance(child, (cst.FunctionDef, cst.ClassDef)):
                count += 1
                continue
            if isinstance(child, cst.SimpleStatementLine):
                for stmt in child.body:
                    if isinstance(stmt, (cst.Assign, cst.AnnAssign)):
                        count += 1
        return count

    @classmethod
    def _walk_classes(
        cls,
        body: Sequence[cst.BaseStatement | cst.BaseCompoundStatement],
    ) -> Iterator[cst.ClassDef]:
        for item in body:
            if isinstance(item, cst.ClassDef):
                yield item
                if isinstance(item.body, cst.IndentedBlock):
                    yield from cls._walk_classes(item.body.body)

    @staticmethod
    def _module_to_str(module: cst.BaseExpression | None) -> str:
        if module is None:
            return ""
        if isinstance(module, cst.Name):
            return module.value
        if isinstance(module, cst.Attribute):
            parts: list[str] = []
            current: cst.BaseExpression | cst.Attribute = module
            while isinstance(current, cst.Attribute):
                parts.append(current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.append(current.value)
            return ".".join(reversed(parts))
        return ""

    @staticmethod
    def project_class_stem(*, project_name: str) -> str:
        """Derive the class name stem from a project name."""
        normalized = project_name.strip().lower().replace("_", "-")
        if normalized == "flext-core":
            return "Flext"
        if normalized.startswith("flext-"):
            tail = normalized.removeprefix("flext-")
            parts = [p for p in tail.split("-") if p]
            return "Flext" + "".join(p.capitalize() for p in parts)
        parts = [p for p in normalized.split("-") if p]
        return "".join(p.capitalize() for p in parts) if parts else ""
