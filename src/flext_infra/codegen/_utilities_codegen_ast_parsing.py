from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import FlextInfraCodegenSnapshot


class FlextInfraUtilitiesCodegenAstParsing(FlextInfraCodegenSnapshot):
    @staticmethod
    def infer_package(path: Path) -> str:
        abs_path = str(path.absolute())
        for root_dir in ("/src/", "/tests/", "/examples/", "/scripts/"):
            idx = abs_path.rfind(root_dir)
            if idx != -1:
                rel = abs_path[idx + len(root_dir) :]
                pkg_parts = rel.split("/")[:-1]
                if root_dir == "/src/":
                    return ".".join(pkg_parts)
                root_name = root_dir.strip("/")
                return ".".join([root_name, *pkg_parts]) if pkg_parts else root_name
        return ""

    @staticmethod
    def resolve_module(raw_module: str, level: int, current_pkg: str) -> str:
        if level == 0:
            return raw_module
        if not current_pkg:
            return raw_module
        parts = current_pkg.split(".")
        base = parts[: len(parts) - level + 1]
        if not base:
            return raw_module
        return ".".join(base) + ("." + raw_module if raw_module else "")

    @staticmethod
    def extract_exports(tree: ast.Module) -> tuple[bool, list[str]]:
        exports: list[str] = []
        has_all = False
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        has_all = True
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            exports.extend(
                                elt.value
                                for elt in node.value.elts
                                if isinstance(elt, ast.Constant)
                                and isinstance(elt.value, str)
                            )
        return (has_all, exports)

    @staticmethod
    def extract_inline_constants(tree: ast.Module) -> dict[str, str]:
        constants: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if (
                    isinstance(target, ast.Name)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    constants[target.id] = node.value.value
        return constants

    @staticmethod
    def parse_existing_lazy_imports(tree: ast.Module) -> dict[str, tuple[str, str]]:
        result: dict[str, tuple[str, str]] = {}
        lazy_import_pair_size = 2

        def _extract(d: ast.expr) -> None:
            if not isinstance(d, ast.Dict):
                return
            for key, val in zip(d.keys, d.values, strict=False):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(val, ast.Tuple)
                    and (len(val.elts) == lazy_import_pair_size)
                    and isinstance(val.elts[0], ast.Constant)
                    and isinstance(val.elts[1], ast.Constant)
                ):
                    result[str(key.value)] = (
                        str(val.elts[0].value),
                        str(val.elts[1].value),
                    )

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_LAZY_IMPORTS":
                        _extract(node.value)
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and (node.target.id == "_LAZY_IMPORTS")
                and (node.value is not None)
            ):
                _extract(node.value)
        return result


__all__ = ["FlextInfraUtilitiesCodegenAstParsing"]
