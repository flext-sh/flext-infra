from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, MutableSequence
from pathlib import Path

from flext_core import FlextTypes as t

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
    def extract_exports(tree: ast.Module) -> tuple[bool, t.StrSequence]:
        exports: MutableSequence[str] = []
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
    def extract_inline_constants(tree: ast.Module) -> Mapping[str, str]:
        constants: MutableMapping[str, str] = {}
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


__all__ = ["FlextInfraUtilitiesCodegenAstParsing"]
