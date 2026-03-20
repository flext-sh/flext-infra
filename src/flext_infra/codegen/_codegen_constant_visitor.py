from __future__ import annotations

import re
from pathlib import Path
from typing import Final, override

import libcst as cst

from flext_infra.codegen._codegen_governance import FlextInfraCodegenGovernance
from flext_infra.models import m


class FlextInfraCodegenConstantDetection:
    MIN_QUOTED_LITERAL_LEN: Final[int] = 2
    MIN_DIRECT_REFERENCE_CHAIN: Final[int] = 3

    class RenderContext:
        def __init__(self, source: str) -> None:
            self._render_module = cst.parse_module("")
            self._source = source
            self._search_offset = 0

        def node_code(self, node: cst.CSTNode) -> str:
            return self._render_module.code_for_node(node)

        def line_for_node(self, node: cst.CSTNode) -> int:
            snippet = self.node_code(node)
            if not snippet:
                return 1
            index = self._source.find(snippet, self._search_offset)
            if index < 0:
                index = self._source.find(snippet)
            if index < 0:
                return 1
            self._search_offset = index + len(snippet)
            return self._source.count("\n", 0, index) + 1

    class DeclarationVisitor(cst.CSTVisitor):
        def __init__(self, *, project: str, file_path: str) -> None:
            super().__init__()
            self._project = project
            self._file_path = file_path
            self._render = FlextInfraCodegenConstantDetection.RenderContext(
                Path(file_path).read_text("utf-8"),
            )
            self._class_stack: list[str] = []
            self.definitions: list[m.Infra.ConstantDefinition] = []

        @override
        def visit_ClassDef(self, node: cst.ClassDef) -> None:
            self._class_stack.append(node.name.value)

        @override
        def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
            del original_node
            if self._class_stack:
                self._class_stack.pop()

        @override
        def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
            if not isinstance(node.target, cst.Name) or node.value is None:
                return
            type_annotation = self._render.node_code(node.annotation.annotation)
            if "Final" not in type_annotation:
                return
            self.definitions.append(
                m.Infra.ConstantDefinition(
                    name=node.target.value,
                    value_repr=self._render.node_code(node.value),
                    type_annotation=type_annotation,
                    file_path=self._file_path,
                    class_path=".".join(self._class_stack),
                    project=self._project,
                    line=self._render.line_for_node(node),
                ),
            )

    class UsageVisitor(cst.CSTVisitor):
        def __init__(
            self,
            *,
            project: str,
            file_path: str,
            target_class: str = "",
        ) -> None:
            super().__init__()
            self._project = project
            self._file_path = file_path
            self._target_class = target_class
            self._render = FlextInfraCodegenConstantDetection.RenderContext(
                Path(file_path).read_text("utf-8"),
            )
            self.used_constants: set[str] = set()
            self.direct_refs: list[m.Infra.DirectConstantRef] = []

        @override
        def visit_Attribute(self, node: cst.Attribute) -> None:
            det = FlextInfraCodegenConstantDetection
            if (
                isinstance(node.value, cst.Attribute)
                and det.root_name(node.value) == "c"
            ):
                self.used_constants.add(node.attr.value)

            chain = det.attribute_chain(node)
            if (
                len(chain)
                < FlextInfraCodegenConstantDetection.MIN_DIRECT_REFERENCE_CHAIN
            ):
                return
            if not re.fullmatch(
                FlextInfraCodegenGovernance.get_constants_class_pattern(),
                chain[0],
            ):
                return
            if self._target_class and chain[0] != self._target_class:
                return

            self.direct_refs.append(
                m.Infra.DirectConstantRef(
                    full_ref=".".join(chain),
                    alias_ref=".".join(["c", *chain[1:]]),
                    file_path=self._file_path,
                    project=self._project,
                    line=self._render.line_for_node(node),
                ),
            )

    @staticmethod
    def attribute_chain(expr: cst.BaseExpression) -> list[str]:
        if isinstance(expr, cst.Name):
            return [expr.value]
        if isinstance(expr, cst.Attribute):
            return [
                *FlextInfraCodegenConstantDetection.attribute_chain(expr.value),
                expr.attr.value,
            ]
        return []

    @staticmethod
    def root_name(expr: cst.BaseExpression) -> str:
        parts = FlextInfraCodegenConstantDetection.attribute_chain(expr)
        return parts[0] if parts else ""

    @staticmethod
    def int_literal(value_repr: str) -> int | None:
        if re.fullmatch(r"-?\d+", value_repr) is None:
            return None
        return int(value_repr)

    @staticmethod
    def str_literal(value_repr: str) -> str | None:
        if len(value_repr) < FlextInfraCodegenConstantDetection.MIN_QUOTED_LITERAL_LEN:
            return None
        if value_repr[0] != value_repr[-1]:
            return None
        if value_repr[0] not in {'"', "'"}:
            return None
        return value_repr[1:-1]

    @staticmethod
    def semantic_name_matches(name: str, canonical_ref: str) -> bool:
        if not canonical_ref:
            return False
        semantic_names = FlextInfraCodegenGovernance.get_semantic_names(canonical_ref)
        return name in semantic_names

    @staticmethod
    def canonical_reference_for(name: str, value_repr: str) -> str:
        det = FlextInfraCodegenConstantDetection
        int_value = det.int_literal(value_repr)
        if int_value is not None:
            candidate = FlextInfraCodegenGovernance.get_canonical_int_values().get(
                int_value,
                "",
            )
            return candidate if det.semantic_name_matches(name, candidate) else ""

        str_value = det.str_literal(value_repr)
        if str_value is not None:
            candidate = FlextInfraCodegenGovernance.get_canonical_str_values().get(
                str_value,
                "",
            )
            return candidate if det.semantic_name_matches(name, candidate) else ""

        return ""

    @staticmethod
    def is_mro_passthrough(value_repr: str) -> bool:
        return bool(re.match(r"Flext\w*Constants\.", value_repr))

    @staticmethod
    def extract_constant_definitions(
        file_path: Path,
        project: str,
    ) -> list[m.Infra.ConstantDefinition]:
        try:
            source = file_path.read_text("utf-8")
            tree = cst.parse_module(source)
        except (cst.ParserSyntaxError, UnicodeDecodeError):
            return []
        visitor = FlextInfraCodegenConstantDetection.DeclarationVisitor(
            project=project,
            file_path=str(file_path),
        )
        tree.visit(visitor)
        return visitor.definitions

    @staticmethod
    def scan_constant_usages(
        file_path: Path,
        project: str,
        *,
        target_class: str = "",
    ) -> tuple[set[str], list[m.Infra.DirectConstantRef]]:
        try:
            source = file_path.read_text("utf-8")
            tree = cst.parse_module(source)
        except (cst.ParserSyntaxError, UnicodeDecodeError):
            return set(), []
        if not target_class:
            pkg_name = file_path.parent.name
            while pkg_name.startswith("_") and file_path.parent.parent.name != "src":
                pkg_name = file_path.parent.parent.name
            target_class = (
                "".join(part.capitalize() for part in pkg_name.split("_")) + "Constants"
            )
        visitor = FlextInfraCodegenConstantDetection.UsageVisitor(
            project=project,
            file_path=str(file_path),
            target_class=target_class,
        )
        tree.visit(visitor)
        return visitor.used_constants, visitor.direct_refs

    @staticmethod
    def detect_hardcoded_canonicals(
        definitions: list[m.Infra.ConstantDefinition],
    ) -> list[m.Infra.ConstantDefinition]:
        return [
            definition
            for definition in definitions
            if FlextInfraCodegenConstantDetection.canonical_reference_for(
                definition.name,
                definition.value_repr,
            )
        ]

    @staticmethod
    def detect_unused_constants(
        definitions: list[m.Infra.ConstantDefinition],
        all_used_names: set[str],
    ) -> list[m.Infra.UnusedConstant]:
        return [
            m.Infra.UnusedConstant(
                name=definition.name,
                file_path=definition.file_path,
                class_path=definition.class_path,
                project=definition.project,
                line=definition.line,
            )
            for definition in definitions
            if definition.name not in all_used_names
            and not FlextInfraCodegenConstantDetection.is_mro_passthrough(
                definition.value_repr,
            )
        ]

    @staticmethod
    def build_self_import_graph(pkg_dir: Path) -> dict[str, set[str]]:
        """Scans ``from pkg.module import X`` only (real cycle risk).

        Lazy-safe ``from pkg import X`` via ``__getattr__`` excluded (AGENTS.md §2.2).
        """
        package_name = pkg_dir.name
        module_stems = {
            py_file.stem
            for py_file in pkg_dir.glob("*.py")
            if py_file.name != "__init__.py"
        }
        graph: dict[str, set[str]] = {}
        for py_file in pkg_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            stem = py_file.stem
            deps: set[str] = set()
            try:
                source = py_file.read_text("utf-8")
                tree = cst.parse_module(source)
            except (cst.ParserSyntaxError, UnicodeDecodeError):
                continue
            for stmt in tree.body:
                if not isinstance(stmt, cst.SimpleStatementLine):
                    continue
                for small in stmt.body:
                    if not isinstance(small, cst.ImportFrom):
                        continue
                    if isinstance(small.names, cst.ImportStar):
                        continue
                    mod = tree.code_for_node(small.module) if small.module else ""
                    if not mod.startswith(f"{package_name}."):
                        continue
                    target_mod = mod.split(".")[-1]
                    if target_mod in module_stems and target_mod != stem:
                        deps.add(target_mod)
            if deps:
                graph[stem] = deps
        return graph

    @staticmethod
    def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
        cycles: list[list[str]] = []
        visited: set[str] = set()
        path: list[str] = []
        path_set: set[str] = set()

        def _dfs(node: str) -> None:
            if node in path_set:
                idx = path.index(node)
                cycles.append([*path[idx:], node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            path_set.add(node)
            for neighbor in graph.get(node, set()):
                _dfs(neighbor)
            path.pop()
            path_set.remove(node)

        for start in graph:
            _dfs(start)
        return cycles

    @staticmethod
    def detect_import_cycles(pkg_dir: Path) -> list[list[str]]:
        det = FlextInfraCodegenConstantDetection
        return det.find_cycles(det.build_self_import_graph(pkg_dir))

    @staticmethod
    def resolve_parent_package(pkg_dir: Path) -> str:
        constants_file = pkg_dir / "constants.py"
        if not constants_file.is_file():
            return "flext_core"
        try:
            source = constants_file.read_text("utf-8")
            tree = cst.parse_module(source)
        except (cst.ParserSyntaxError, UnicodeDecodeError):
            return "flext_core"
        for stmt in tree.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            for small in stmt.body:
                if not isinstance(small, cst.ImportFrom):
                    continue
                if isinstance(small.names, cst.ImportStar):
                    continue
                mod = tree.code_for_node(small.module) if small.module else ""
                for alias in small.names:
                    name = alias.name.value if isinstance(alias.name, cst.Name) else ""
                    if "Constants" in name and name.startswith("Flext"):
                        return mod
        return "flext_core"


__all__ = ["FlextInfraCodegenConstantDetection"]
