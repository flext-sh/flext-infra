from __future__ import annotations

import ast
from collections.abc import Mapping, MutableMapping, MutableSequence
from pathlib import Path

from flext_infra import FlextInfraCodegenSnapshot, t


class FlextInfraUtilitiesCodegenAstParsing(FlextInfraCodegenSnapshot):
    @staticmethod
    def infer_package(path: Path) -> str:
        root_markers = {"examples", "scripts", "src", "tests"}
        abs_parts = path.absolute().parts
        for index, part in enumerate(abs_parts):
            if part not in root_markers:
                continue
            pkg_parts = abs_parts[index + 1 : -1]
            if part == "src":
                return ".".join(pkg_parts)
            return ".".join([part, *pkg_parts]) if pkg_parts else part
        return ""

    @staticmethod
    def extract_exports(tree: ast.Module) -> t.Infra.Pair[bool, t.StrSequence]:
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
