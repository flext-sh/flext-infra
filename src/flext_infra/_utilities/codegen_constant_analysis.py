"""Constant census, deduplication, and class-level attribute analysis.

Extracted from ``_utilities_codegen_constant_visitor.py`` to keep
each codegen module under 400 lines.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import u
from flext_infra import (
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCodegenConstantAnalysis:
    """Census, deduplication, and MRO attribute analysis for constants."""

    @staticmethod
    def _analyze_class_internal(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str],
        max_files: int,
    ) -> t.Infra.Triple[
        Mapping[str, m.Infra.ConstantDefinition],
        t.Infra.StrSet,
        Mapping[str, Sequence[t.Infra.StrIntPair]],
    ]:
        """Shared logic: extract attributes and usages for a class."""
        cls = FlextInfraUtilitiesCodegenConstantAnalysis
        attrs = cls.extract_class_attributes_with_mro(class_path)
        if not attrs:
            return {}, set(), {}
        simple_class_name = class_path.rsplit(".", 1)[-1]
        used_attrs, usage_map = cls.scan_class_attribute_usages(
            root_path,
            simple_class_name,
            exclude_patterns,
            max_files,
        )
        return attrs, used_attrs, usage_map

    @staticmethod
    def extract_class_attributes_with_mro(
        class_path: str,
    ) -> Mapping[str, m.Infra.ConstantDefinition]:
        """Extract class attributes following MRO chain via importlib.

        Dynamically imports the class specified by ``class_path`` (e.g.,
        ``"flext_core.FlextConstants"``), walks its MRO, and collects all
        class-level attributes that look like constant declarations.

        Args:
            class_path: Dotted path to the class (module.ClassName).

        Returns:
            Mapping of attribute name to ConstantDefinition.

        """
        if "." not in class_path:
            return {}
        module_path, class_name = class_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_path)
        except (ImportError, ModuleNotFoundError):
            return {}
        cls_obj = getattr(module, class_name, None)
        if cls_obj is None or not isinstance(cls_obj, type):
            return {}

        attrs: MutableMapping[str, m.Infra.ConstantDefinition] = {}
        # Walk MRO in reverse so that more-specific classes override
        for klass in reversed(cls_obj.__mro__):
            if klass is object:
                continue
            klass_name = klass.__qualname__
            klass_module = getattr(klass, "__module__", module_path)
            for attr_name in vars(klass):
                if attr_name.startswith("_"):
                    continue
                attr_value = vars(klass)[attr_name]
                # Determine type annotation string
                annotations = getattr(klass, "__annotations__", {})
                ann = str(annotations.get(attr_name, ""))
                attrs[attr_name] = m.Infra.ConstantDefinition(
                    name=attr_name,
                    value_repr=repr(attr_value)[:200],
                    type_annotation=ann,
                    file_path=f"{klass_module}.{klass_name}",
                    class_path=klass_name,
                    project=klass_module.split(".")[0].replace("_", "-"),
                    line=1,
                )
        return attrs

    @staticmethod
    def scan_class_attribute_usages(
        root_path: Path,
        class_name: str,
        exclude_patterns: frozenset[str],
        max_files: int,
    ) -> tuple[t.Infra.StrSet, Mapping[str, Sequence[t.Infra.StrIntPair]]]:
        """Scan for usages of class attributes across Python files.

        Searches for patterns like ``ClassName.ATTR`` and ``c.Xxx.ATTR``
        in all Python files under ``root_path``.

        Args:
            root_path: Root directory to scan.
            class_name: Simple class name (e.g., "FlextConstants").
            exclude_patterns: Directory names to skip.
            max_files: Maximum number of files to scan.

        Returns:
            Tuple of (set of used attribute names,
            mapping of attr_name -> list of (file_path, line_num) pairs).

        """
        used_attrs: t.Infra.StrSet = set()
        usage_map: MutableMapping[str, MutableSequence[t.Infra.StrIntPair]] = {}
        # Build regex for direct class references: FlextXxxConstants.ATTR
        direct_pattern = re.compile(
            rf"\b{re.escape(class_name)}\.([A-Za-z_]\w*)",
        )
        # Build regex for alias references: c.Xxx.ATTR or c.ATTR
        prefix = class_name.replace("Constants", "")
        prefix = prefix.removeprefix("Flext")
        alias_pattern = re.compile(
            rf"\bc\.{re.escape(prefix)}\.([A-Za-z_]\w*)"
            if prefix
            else r"\bc\.([A-Za-z_]\w*)",
        )

        files_scanned = 0
        for py_file in root_path.rglob(c.Infra.Extensions.PYTHON_GLOB):
            if files_scanned >= max_files:
                break
            if any(excl in py_file.parts for excl in exclude_patterns):
                continue
            try:
                source = py_file.read_text(c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            files_scanned += 1
            for line_num, line in enumerate(source.splitlines(), start=1):
                for match in direct_pattern.finditer(line):
                    attr_name = match.group(1)
                    used_attrs.add(attr_name)
                    if attr_name not in usage_map:
                        usage_map[attr_name] = list[t.Infra.StrIntPair]()
                    usage_map[attr_name].append((str(py_file), line_num))
                for match in alias_pattern.finditer(line):
                    attr_name = match.group(1)
                    used_attrs.add(attr_name)
                    if attr_name not in usage_map:
                        usage_map[attr_name] = list[t.Infra.StrIntPair]()
                    usage_map[attr_name].append((str(py_file), line_num))
        return used_attrs, usage_map

    @staticmethod
    def analyze_class_object_census(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str] = frozenset({
            ".mypy_cache",
            c.Infra.Dunders.PYCACHE,
        }),
        max_files: int = 5000,
    ) -> Mapping[
        str,
        int
        | Mapping[str, int | t.IntMapping]
        | Mapping[str, t.IntMapping]
        | Mapping[str, Sequence[t.Infra.StrIntPair]],
    ]:
        """Comprehensive census of all objects in a class."""
        cls = FlextInfraUtilitiesCodegenConstantAnalysis
        attrs, used_attrs, usage_map = cls._analyze_class_internal(
            class_path,
            root_path,
            exclude_patterns,
            max_files,
        )
        if not attrs:
            return {}

        by_type: MutableMapping[str, t.MutableIntMapping] = {}
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
        exclude_patterns: frozenset[str] = frozenset({
            ".mypy_cache",
            c.Infra.Dunders.PYCACHE,
        }),
        max_files: int = 2000,
    ) -> Sequence[t.Infra.DeduplicationFix]:
        """Propose fixes to deduplicate constant values across a class."""
        cls = FlextInfraUtilitiesCodegenConstantAnalysis
        attrs, _, usage_map = cls._analyze_class_internal(
            class_path,
            root_path,
            exclude_patterns,
            max_files,
        )
        if not attrs:
            return []

        by_value: MutableMapping[str, t.Infra.MutableCensusRecordList] = {}
        for name, defn in attrs.items():
            value_key = defn.value_repr[:100]
            if value_key not in by_value:
                by_value[value_key] = list[t.Infra.CensusRecord]()
            by_value[value_key].append({
                "name": name,
                "type": defn.type_annotation,
                "usages": len(usage_map.get(name, [])),
            })

        fixes: MutableSequence[t.Infra.DeduplicationFix] = []
        for value, names_list in by_value.items():
            if len(names_list) <= 1:
                continue
            canonical = max(names_list, key=operator.itemgetter("usages"))
            duplicates = [n for n in names_list if n["name"] != canonical["name"]]
            fixes.append({
                "value": value,
                "canonical_name": canonical["name"],
                "canonical_usages": canonical["usages"],
                "duplicates": duplicates,
                "total_occurrences": len(names_list),
            })

        def _sort_key(x: t.Infra.DeduplicationFix) -> int:
            usages_val = x.get("canonical_usages", 0)
            usages = usages_val if isinstance(usages_val, int) else 0
            dups_val = x.get("duplicates", [])
            dups_len = len(dups_val) if isinstance(dups_val, (list, tuple)) else 0
            return usages * dups_len

        return sorted(fixes, key=_sort_key, reverse=True)

    @staticmethod
    def apply_deduplication_fix(
        fix_proposal: t.Infra.DeduplicationFix,
        root_path: Path,
        class_path: str,
        *,
        dry_run: bool = True,
    ) -> t.Infra.DeduplicationResult:
        """Apply a single deduplication fix using rope."""
        canonical_name = str(fix_proposal.get("canonical_name", ""))
        files_modified = 0
        replaced_names: MutableSequence[str] = []
        replaced_details: t.Infra.MutableCensusRecordList = []

        rope_project = FlextInfraUtilitiesRope.init_rope_project(root_path)

        if "." not in class_path:
            return {"status": "error", "message": "Invalid class path"}

        module_name, _class_name = class_path.rsplit(".", 1)
        resource = FlextInfraUtilitiesRope.get_file_resource(rope_project, module_name)
        if not resource:
            resource = FlextInfraUtilitiesRope.get_file_resource(
                rope_project,
                f"{module_name}.constants",
            )
        if not resource:
            return {
                "status": "error",
                "message": f"Could not locate resource for {module_name}",
            }

        duplicates_val = fix_proposal.get("duplicates", [])
        duplicates = duplicates_val if isinstance(duplicates_val, list) else []

        for dup in duplicates:
            if not u.is_mapping(dup):
                continue
            dup_name = str(dup.get("name", ""))
            offset = FlextInfraUtilitiesRope.find_definition_offset(
                rope_project,
                resource,
                dup_name,
            )
            if offset is None:
                continue
            replaced_names.append(dup_name)
            changed = FlextInfraUtilitiesRope.rename_symbol_workspace(
                rope_project,
                resource,
                offset,
                canonical_name,
                apply=not dry_run,
            )
            files_modified += len(changed)
            for ch in changed:
                replaced_details.append({
                    "file": ch,
                    "line": 0,
                    "old_name": dup_name,
                })

        return {
            "status": "success",
            "canonical": canonical_name,
            "replaced": replaced_names,
            "replaced_details": replaced_details,
            "files_modified": files_modified,
        }

    @staticmethod
    def detect_duplicate_constants(
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> Sequence[m.Infra.DuplicateConstantGroup]:
        """Detect duplicate constants by name and value across projects."""
        by_name: MutableMapping[str, MutableSequence[m.Infra.ConstantDefinition]] = {}
        for defn in definitions:
            if defn.name not in by_name:
                by_name[defn.name] = list[m.Infra.ConstantDefinition]()
            by_name[defn.name].append(defn)

        by_value: MutableMapping[str, MutableSequence[m.Infra.ConstantDefinition]] = {}
        for defn in definitions:
            if defn.value_repr not in by_value:
                by_value[defn.value_repr] = list[m.Infra.ConstantDefinition]()
            by_value[defn.value_repr].append(defn)

        duplicates: MutableSequence[m.Infra.DuplicateConstantGroup] = []
        for name, defs in by_name.items():
            if len(defs) > 1:
                values = {d.value_repr for d in defs}
                duplicates.append(
                    m.Infra.DuplicateConstantGroup(
                        constant_name=name,
                        definitions=defs,
                        is_value_identical=len(values) == 1,
                        canonical_ref="",
                    )
                )
        for value_key, defs in by_value.items():
            if len(defs) > 1:
                unique_names = {d.name for d in defs}
                if len(unique_names) > 1:
                    duplicates.append(
                        m.Infra.DuplicateConstantGroup(
                            constant_name=f"[value: {value_key}]",
                            definitions=defs,
                            is_value_identical=True,
                            canonical_ref="",
                        )
                    )
        return duplicates


__all__ = ["FlextInfraUtilitiesCodegenConstantAnalysis"]
