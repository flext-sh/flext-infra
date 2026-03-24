from __future__ import annotations

import operator
import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Final, override

import libcst as cst

from flext_infra import (
    FlextInfraUtilitiesCodegenGovernance,
    FlextInfraUtilitiesParsing,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCodegenConstantDetection:
    MIN_QUOTED_LITERAL_LEN: Final[int] = 2
    MIN_DIRECT_REFERENCE_CHAIN: Final[int] = 2

    @staticmethod
    def _infer_project_name(py_file: Path, root_path: Path) -> str:
        """Extract project name from file path (src/PROJECT_NAME/...)."""
        try:
            parts = py_file.relative_to(root_path).parts
            if "src" in parts:
                src_idx = parts.index("src")
                if src_idx + 1 < len(parts):
                    return parts[src_idx + 1].replace("_", "-")
            return "unknown"
        except ValueError:
            return "unknown"

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
            self._render = FlextInfraUtilitiesCodegenConstantDetection.RenderContext(
                Path(file_path).read_text(c.Infra.Encoding.DEFAULT),
            )
            self._class_stack: MutableSequence[str] = []
            self.definitions: MutableSequence[m.Infra.ConstantDefinition] = []

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
            collect_all_refs: bool = False,
        ) -> None:
            super().__init__()
            self._project = project
            self._file_path = file_path
            self._target_class = target_class
            self._collect_all_refs = collect_all_refs
            self._render = FlextInfraUtilitiesCodegenConstantDetection.RenderContext(
                Path(file_path).read_text(c.Infra.Encoding.DEFAULT),
            )
            self.used_constants: set[str] = set()
            self.direct_refs: MutableSequence[m.Infra.DirectConstantRef] = []
            self.all_constant_refs: MutableSequence[
                tuple[str, int]
            ] = []  # (name, line)

        @override
        def visit_Attribute(self, node: cst.Attribute) -> None:
            det = FlextInfraUtilitiesCodegenConstantDetection
            root = det.root_name(node)

            # Track all c.* usage (generic) - both c.X and c.X.Y
            if root == "c":
                constant_name = node.attr.value
                self.used_constants.add(constant_name)
                if self._collect_all_refs:
                    line = self._render.line_for_node(node)
                    self.all_constant_refs.append((constant_name, line))

            # Track FlextXxxConstants.* patterns (direct refs)
            chain = det.attribute_chain(node)
            if (
                len(chain)
                < FlextInfraUtilitiesCodegenConstantDetection.MIN_DIRECT_REFERENCE_CHAIN
            ):
                return
            if not re.fullmatch(
                FlextInfraUtilitiesCodegenGovernance.get_constants_class_pattern(),
                chain[0],
            ):
                return
            if (
                self._target_class
                and chain[0] != self._target_class
                and not self._collect_all_refs
            ):
                return

            line = self._render.line_for_node(node)
            ref = m.Infra.DirectConstantRef(
                full_ref=".".join(chain),
                alias_ref=".".join(["c", *chain[1:]]),
                file_path=self._file_path,
                project=self._project,
                line=line,
            )
            self.direct_refs.append(ref)

            if self._collect_all_refs:
                # Also track the attribute name for duplicates analysis
                constant_name = chain[-1]
                self.all_constant_refs.append((constant_name, line))

    @staticmethod
    def attribute_chain(expr: cst.BaseExpression) -> t.StrSequence:
        if isinstance(expr, cst.Name):
            return [expr.value]
        if isinstance(expr, cst.Attribute):
            return [
                *FlextInfraUtilitiesCodegenConstantDetection.attribute_chain(
                    expr.value,
                ),
                expr.attr.value,
            ]
        return []

    @staticmethod
    def root_name(expr: cst.BaseExpression) -> str:
        parts = FlextInfraUtilitiesCodegenConstantDetection.attribute_chain(expr)
        return parts[0] if parts else ""

    @staticmethod
    def int_literal(value_repr: str) -> int | None:
        if re.fullmatch(r"-?\d+", value_repr) is None:
            return None
        return int(value_repr)

    @staticmethod
    def str_literal(value_repr: str) -> str | None:
        if (
            len(value_repr)
            < FlextInfraUtilitiesCodegenConstantDetection.MIN_QUOTED_LITERAL_LEN
        ):
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
        semantic_names = FlextInfraUtilitiesCodegenGovernance.get_semantic_names(
            canonical_ref,
        )
        return name in semantic_names

    @staticmethod
    def canonical_reference_for(name: str, value_repr: str) -> str:
        det = FlextInfraUtilitiesCodegenConstantDetection
        int_value = det.int_literal(value_repr)
        if int_value is not None:
            candidate = (
                FlextInfraUtilitiesCodegenGovernance.get_canonical_int_values().get(
                    int_value,
                    "",
                )
            )
            return candidate if det.semantic_name_matches(name, candidate) else ""

        str_value = det.str_literal(value_repr)
        if str_value is not None:
            candidate = (
                FlextInfraUtilitiesCodegenGovernance.get_canonical_str_values().get(
                    str_value,
                    "",
                )
            )
            return candidate if det.semantic_name_matches(name, candidate) else ""

        return ""

    @staticmethod
    def extract_constant_definitions(
        file_path: Path,
        project: str,
    ) -> Sequence[m.Infra.ConstantDefinition]:
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if tree is None:
            return []
        visitor = FlextInfraUtilitiesCodegenConstantDetection.DeclarationVisitor(
            project=project,
            file_path=str(file_path),
        )
        tree.visit(visitor)
        return visitor.definitions

    @staticmethod
    def extract_all_constant_definitions(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[m.Infra.ConstantDefinition]]:
        """Extract all constant definitions from all Python files (generic).

        Scans recursively for files named constants.py or any class with Final attrs.

        Args:
            root_path: Root directory to scan
            exclude_packages: Package names to skip

        Returns:
            Dict mapping project_name -> list of ConstantDefinitions

        """
        if exclude_packages is None:
            exclude_packages = frozenset()

        all_defs: MutableMapping[str, MutableSequence[m.Infra.ConstantDefinition]] = {}

        for py_file in root_path.rglob("*.py"):
            # Skip excluded packages
            if any(excl in py_file.parts for excl in exclude_packages):
                continue

            project_name = (
                FlextInfraUtilitiesCodegenConstantDetection._infer_project_name(
                    py_file,
                    root_path,
                )
            )

            defs = FlextInfraUtilitiesCodegenConstantDetection.extract_constant_definitions(
                py_file,
                project_name,
            )
            if defs:
                if project_name not in all_defs:
                    all_defs[project_name] = []
                all_defs[project_name].extend(defs)

        return all_defs

    @staticmethod
    def scan_constant_usages(
        file_path: Path,
        project: str,
        *,
        target_class: str = "",
        collect_all_refs: bool = False,
    ) -> tuple[
        set[str],
        Sequence[m.Infra.DirectConstantRef],
        Sequence[tuple[str, int]],
    ]:
        """Scan constant usages in a file.

        Args:
            file_path: File to scan
            project: Project name
            target_class: Optional target class (e.g., 'FlextAuthConstants')
            collect_all_refs: If True, collect all refs regardless of target_class

        Returns:
            Tuple of (used_names_set, direct_refs, all_refs_with_lines)

        """
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if tree is None:
            return set(), [], []

        if not target_class and not collect_all_refs:
            pkg_name = file_path.parent.name
            while pkg_name.startswith("_") and file_path.parent.parent.name != "src":
                pkg_name = file_path.parent.parent.name
            target_class = (
                "".join(part.capitalize() for part in pkg_name.split("_")) + "Constants"
            )

        visitor = FlextInfraUtilitiesCodegenConstantDetection.UsageVisitor(
            project=project,
            file_path=str(file_path),
            target_class=target_class,
            collect_all_refs=collect_all_refs,
        )
        tree.visit(visitor)
        return visitor.used_constants, visitor.direct_refs, visitor.all_constant_refs

    @staticmethod
    def scan_all_constant_usages(
        root_path: Path,
        exclude_packages: frozenset[str] | None = None,
    ) -> Mapping[str, Sequence[tuple[str, int]]]:
        """Scan all constant usages across workspace (generic).

        Args:
            root_path: Root directory to scan
            exclude_packages: Package names to skip

        Returns:
            Dict mapping constant_name -> [(file_path, line_number), ...]

        """
        if exclude_packages is None:
            exclude_packages = frozenset()

        usage_map: MutableMapping[str, MutableSequence[tuple[str, int]]] = {}

        for py_file in root_path.rglob("*.py"):
            if any(excl in py_file.parts for excl in exclude_packages):
                continue

            project_name = (
                FlextInfraUtilitiesCodegenConstantDetection._infer_project_name(
                    py_file,
                    root_path,
                )
            )

            _, _, all_refs = (
                FlextInfraUtilitiesCodegenConstantDetection.scan_constant_usages(
                    py_file,
                    project_name,
                    collect_all_refs=True,
                )
            )

            for constant_name, line_num in all_refs:
                if constant_name not in usage_map:
                    usage_map[constant_name] = []
                usage_map[constant_name].append((str(py_file), line_num))

        return usage_map

    @staticmethod
    def detect_hardcoded_canonicals(
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> Sequence[m.Infra.ConstantDefinition]:
        return [
            definition
            for definition in definitions
            if FlextInfraUtilitiesCodegenConstantDetection.canonical_reference_for(
                definition.name,
                definition.value_repr,
            )
        ]

    @staticmethod
    def detect_unused_constants(
        definitions: Sequence[m.Infra.ConstantDefinition],
        all_used_names: set[str],
    ) -> Sequence[m.Infra.UnusedConstant]:
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
            and not re.match(r"Flext\w*Constants\.", definition.value_repr)
        ]

    @staticmethod
    def detect_duplicate_constants(
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        """Detect duplicate constants by name and value across projects.

        Groups constants that have:
        - Same name (semantic duplicates)
        - Same value (potential consolidation candidates)
        """
        # Group by name
        by_name: MutableMapping[str, MutableSequence[m.Infra.ConstantDefinition]] = {}
        for defn in definitions:
            if defn.name not in by_name:
                by_name[defn.name] = []
            by_name[defn.name].append(defn)

        # Group by value (for value duplicates)
        by_value: MutableMapping[str, MutableSequence[m.Infra.ConstantDefinition]] = {}
        for defn in definitions:
            value_key = defn.value_repr
            if value_key not in by_value:
                by_value[value_key] = []
            by_value[value_key].append(defn)

        duplicates: MutableSequence[m.Infra.DuplicateConstantGroup] = []

        # Name-based duplicates (at least 2 definitions)
        for name, defs in by_name.items():
            if len(defs) > 1:
                values = {d.value_repr for d in defs}
                duplicates.append(
                    m.Infra.DuplicateConstantGroup(
                        constant_name=name,
                        definitions=defs,
                        is_value_identical=len(values) == 1,
                        canonical_ref="",
                    ),
                )

        # Value-based duplicates (different names, same value)
        for value_key, defs in by_value.items():
            if len(defs) > 1:
                # Check if already captured by name
                unique_names = {d.name for d in defs}
                if len(unique_names) > 1:
                    duplicates.append(
                        m.Infra.DuplicateConstantGroup(
                            constant_name=f"[value: {value_key}]",
                            definitions=defs,
                            is_value_identical=True,
                            canonical_ref="",
                        ),
                    )

        return duplicates

    @staticmethod
    def resolve_parent_package(pkg_dir: Path) -> str:
        constants_file = pkg_dir / "constants.py"
        if not constants_file.is_file():
            return "flext_core"
        tree = FlextInfraUtilitiesParsing.parse_module_cst(constants_file)
        if tree is None:
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

    @staticmethod
    def extract_class_attributes_with_mro(
        class_path: str,
    ) -> Mapping[str, m.Infra.ConstantDefinition]:
        """Extract all attributes from a class including MRO inheritance.

        Includes: constants, enums, classes, types, and other public attributes.

        Args:
            class_path: Full class path like 'flext_core.FlextConstants'

        Returns:
            Dict mapping attribute name to ConstantDefinition (with type info)

        """
        module_part_count = 2
        try:
            parts = class_path.rsplit(".", 1)
            if len(parts) != module_part_count:
                return {}
            module_name, class_name = parts
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
        except (ImportError, AttributeError, ValueError):
            return {}

        result: MutableMapping[str, m.Infra.ConstantDefinition] = {}
        seen_names: set[str] = set()

        # Walk MRO to get all attributes (constants, enums, classes, types)
        for base_cls in cls.__mro__[:-1]:  # Exclude t.NormalizedValue
            for attr_name in dir(base_cls):
                if attr_name.startswith("_") or attr_name in seen_names:
                    continue
                try:
                    attr_value = getattr(cls, attr_name)
                    # Skip only instance methods, not type definitions or constants
                    if (
                        callable(attr_value)
                        and not isinstance(attr_value, type)
                        and hasattr(attr_value, "__self__")
                    ):
                        continue
                    # Include: constants (str, int, bool), enums, classes, types
                    attr_type = type(attr_value).__name__
                    result[attr_name] = m.Infra.ConstantDefinition(
                        name=attr_name,
                        value_repr=repr(attr_value)[:100],
                        type_annotation=attr_type,
                        file_path="<dynamic>",
                        class_path=class_name,
                        project="flext-core",
                        line=1,
                    )
                    seen_names.add(attr_name)
                except (AttributeError, ValueError, TypeError, RecursionError):
                    continue
        return result

    @staticmethod
    def scan_class_attribute_usages(
        root_path: Path,
        class_name: str,
        exclude_patterns: frozenset[str] = frozenset({".mypy_cache", "__pycache__"}),
        max_files: int = 10000,
    ) -> tuple[set[str], Mapping[str, Sequence[tuple[str, int]]]]:
        """Scan workspace for usages of a specific class's attributes.

        Args:
            root_path: Root directory to scan
            class_name: Class name to search for (e.g., 'FlextConstants')
            exclude_patterns: Directory patterns to exclude
            max_files: Maximum files to scan (default 10000)

        Returns:
            Tuple of (used_attribute_names, usage_map with file+line)

        """
        used_names: set[str] = set()
        usage_map: MutableMapping[str, MutableSequence[tuple[str, int]]] = {}

        # Fast lookup for class usages
        search_prefix = f"{class_name}."
        files_scanned = 0

        for py_file in root_path.rglob("*.py"):
            if files_scanned >= max_files:
                break
            if any(excl in py_file.parts for excl in exclude_patterns):
                continue
            try:
                source = py_file.read_text(c.Infra.Encoding.DEFAULT)
            except (UnicodeDecodeError, OSError):
                continue

            # Quick check: does file contain the class name at all?
            if search_prefix not in source:
                continue

            files_scanned += 1
            lines = source.split("\n")
            for line_num, line in enumerate(lines, 1):
                # Find all occurrences of CLASS_NAME.ATTR
                idx = 0
                while True:
                    pos = line.find(search_prefix, idx)
                    if pos == -1:
                        break
                    # Extract attribute name (word characters after the dot)
                    after_dot = pos + len(search_prefix)
                    end_pos = after_dot
                    while end_pos < len(line) and (
                        line[end_pos].isalnum() or line[end_pos] == "_"
                    ):
                        end_pos += 1
                    if end_pos > after_dot:
                        attr_name = line[after_dot:end_pos]
                        used_names.add(attr_name)
                        if attr_name not in usage_map:
                            usage_map[attr_name] = []
                        usage_map[attr_name].append((str(py_file), line_num))
                    idx = pos + 1

        return used_names, usage_map

    @staticmethod
    def _analyze_class_internal(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str],
        max_files: int,
    ) -> tuple[
        Mapping[str, m.Infra.ConstantDefinition],
        set[str],
        Mapping[str, Sequence[tuple[str, int]]],
    ]:
        """Shared logic: extract attributes and usages for a class."""
        attrs = FlextInfraUtilitiesCodegenConstantDetection.extract_class_attributes_with_mro(
            class_path,
        )
        if not attrs:
            return {}, set(), {}
        simple_class_name = class_path.rsplit(".", 1)[-1]
        used_attrs, usage_map = (
            FlextInfraUtilitiesCodegenConstantDetection.scan_class_attribute_usages(
                root_path,
                simple_class_name,
                exclude_patterns,
                max_files,
            )
        )
        return attrs, used_attrs, usage_map

    @staticmethod
    def analyze_class_object_census(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str] = frozenset({".mypy_cache", "__pycache__"}),
        max_files: int = 5000,
    ) -> Mapping[
        str,
        int
        | Mapping[str, int | Mapping[str, int]]
        | Mapping[str, Mapping[str, int]]
        | Mapping[str, Sequence[tuple[str, int]]],
    ]:
        """Comprehensive census of all objects in a class."""
        attrs, used_attrs, usage_map = (
            FlextInfraUtilitiesCodegenConstantDetection._analyze_class_internal(
                class_path,
                root_path,
                exclude_patterns,
                max_files,
            )
        )
        if not attrs:
            return {}

        by_type: MutableMapping[str, MutableMapping[str, int]] = {}
        for attr_name, attr_def in attrs.items():
            attr_type = attr_def.type_annotation
            if attr_type not in by_type:
                by_type[attr_type] = {"total": 0, "used": 0, "unused": 0}
            by_type[attr_type]["total"] += 1
            if attr_name in used_attrs:
                by_type[attr_type]["used"] += 1
            else:
                by_type[attr_type]["unused"] += 1

        return {
            "total_objects": len(attrs),
            "total_used": len(used_attrs),
            "total_unused": len(attrs) - len(used_attrs),
            "by_type": by_type,
            "usage_map": usage_map,
        }

    @staticmethod
    def propose_deduplication_fixes(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str] = frozenset({".mypy_cache", "__pycache__"}),
        max_files: int = 2000,
    ) -> Sequence[Mapping[str, str | int | Sequence[Mapping[str, str | int]]]]:
        """Propose fixes to deduplicate constant values across a class."""
        attrs, _, usage_map = (
            FlextInfraUtilitiesCodegenConstantDetection._analyze_class_internal(
                class_path,
                root_path,
                exclude_patterns,
                max_files,
            )
        )
        if not attrs:
            return []

        # Group by value
        by_value: MutableMapping[str, MutableSequence[Mapping[str, str | int]]] = {}
        for name, defn in attrs.items():
            value_key = defn.value_repr[:100]
            if value_key not in by_value:
                by_value[value_key] = []
            by_value[value_key].append({
                "name": name,
                "type": defn.type_annotation,
                "usages": len(usage_map.get(name, [])),
            })

        # Create fix proposals for duplicates
        fixes: MutableSequence[
            Mapping[str, str | int | Sequence[Mapping[str, str | int]]]
        ] = []
        for value, names_list in by_value.items():
            if len(names_list) <= 1:
                continue  # Not a duplicate

            # Find most-used
            canonical = max(names_list, key=operator.itemgetter("usages"))
            duplicates = [n for n in names_list if n["name"] != canonical["name"]]

            fixes.append({
                "value": value,
                "canonical_name": canonical["name"],
                "canonical_usages": canonical["usages"],
                "duplicates": duplicates,
                "total_occurrences": len(names_list),
            })

        # Sort by impact (total usages × duplicates)
        def _sort_key(
            x: Mapping[str, str | int | Sequence[Mapping[str, str | int]]],
        ) -> int:
            usages_val = x.get("canonical_usages", 0)
            usages = usages_val if isinstance(usages_val, int) else 0
            dups_val = x.get("duplicates", [])
            dups_len = len(dups_val) if isinstance(dups_val, (list, tuple)) else 0
            return usages * dups_len

        return sorted(fixes, key=_sort_key, reverse=True)

    @staticmethod
    def apply_deduplication_fix(
        fix_proposal: Mapping[str, str | int | Sequence[Mapping[str, str | int]]],
        root_path: Path,
        class_path: str,
        *,
        dry_run: bool = True,
    ) -> Mapping[str, str | int | t.StrSequence | Sequence[Mapping[str, str | int]]]:
        """Apply a single deduplication fix.

        Returns dict with: status, canonical, replaced, files_modified
        """
        canonical_name = str(fix_proposal.get("canonical_name", ""))
        simple_class_name = class_path.rsplit(".", 1)[-1]

        # Determine access pattern
        access_pattern = (
            f"c.Infra.{canonical_name}"
            if "Infra" in simple_class_name
            else f"c.{canonical_name}"
        )

        files_modified = 0
        replaced_names: MutableSequence[str] = []
        replaced_details: MutableSequence[
            Mapping[str, str | int]
        ] = []  # Track file, line, old_name for each replacement

        # Replace each duplicate
        duplicates_val = fix_proposal.get("duplicates", [])
        duplicates = duplicates_val if isinstance(duplicates_val, list) else []
        for dup in duplicates:
            if isinstance(dup, dict):
                dup_name = str(dup.get("name", ""))
                replaced_names.append(dup_name)
            else:
                continue

            # Patterns to find and replace
            patterns = [
                (f"{simple_class_name}.{dup_name}", access_pattern),
                (f"c.{dup_name}", access_pattern),
            ]

            # Scan and replace files
            for py_file in root_path.rglob("*.py"):
                if any(
                    excl in py_file.parts for excl in (".mypy_cache", "__pycache__")
                ):
                    continue
                try:
                    content = py_file.read_text(c.Infra.Encoding.DEFAULT)
                except (UnicodeDecodeError, OSError):
                    continue

                modified = False
                new_content = content
                lines = content.split("\n")

                for old_pattern, new_pattern in patterns:
                    if old_pattern not in new_content:
                        continue

                    # Find all occurrences with line numbers
                    for line_idx, line in enumerate(lines, 1):
                        if old_pattern in line:
                            # Track this replacement
                            replaced_details.append({
                                "file": str(py_file),
                                "line": line_idx,
                                "old_name": dup_name,
                            })
                            # Do the replacement
                            new_content = new_content.replace(old_pattern, new_pattern)
                            modified = True

                if modified and not dry_run:
                    py_file.write_text(new_content, encoding=c.Infra.Encoding.DEFAULT)
                    files_modified += 1

        return {
            "status": "success",
            "canonical": canonical_name,
            "replaced": replaced_names,
            "replaced_details": replaced_details,
            "files_modified": files_modified,
        }


__all__ = ["FlextInfraUtilitiesCodegenConstantDetection"]
