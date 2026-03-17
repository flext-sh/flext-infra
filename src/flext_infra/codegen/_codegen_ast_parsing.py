from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c
from flext_infra.codegen._codegen_snapshot import FlextInfraCodegenSnapshot


class FlextInfraCodegenAstParsing(FlextInfraCodegenSnapshot):
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
    def extract_docstring_source(tree: ast.Module, content: str) -> str:
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            ds = tree.body[0]
            return "\n".join(content.splitlines()[ds.lineno - 1 : ds.end_lineno])
        return ""

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

    @staticmethod
    def derive_lazy_map(
        tree: ast.Module,
        current_pkg: str,
    ) -> dict[str, tuple[str, str]]:
        lazy_map: dict[str, tuple[str, str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                raw_module = node.module or ""
                if raw_module in c.Infra.Codegen.SKIP_MODULES:
                    continue
                module_path = FlextInfraCodegenAstParsing.resolve_module(
                    raw_module,
                    node.level,
                    current_pkg,
                )
                if module_path == current_pkg:
                    continue
                for alias in node.names:
                    name = alias.name
                    asname = alias.asname or name
                    lazy_map[asname] = (module_path, name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    asname = alias.asname or name
                    if name in c.Infra.Codegen.SKIP_STDLIB:
                        continue
                    lazy_map[asname] = (name, "")
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name):
                rhs = node.value.id
                if rhs in lazy_map:
                    mod, attr = lazy_map[rhs]
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            lazy_map[target.id] = (mod, attr)
        for a_name, suffix in c.Infra.Codegen.ALIAS_TO_SUFFIX.items():
            if a_name not in lazy_map:
                continue
            alias_mod, alias_attr = lazy_map[a_name]
            if alias_attr == a_name:
                for name, (mod, _) in lazy_map.items():
                    if mod == alias_mod and name.endswith(suffix) and (len(name) > 1):
                        lazy_map[a_name] = (mod, name)
                        break
        return lazy_map


__all__ = ["FlextInfraCodegenAstParsing"]
