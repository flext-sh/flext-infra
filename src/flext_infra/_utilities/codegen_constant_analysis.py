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

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCodegenConstantAnalysis:
    """Census, deduplication, and MRO attribute analysis for constants."""

    @staticmethod
    def extract_class_attributes_with_mro(
        class_path: str,
    ) -> Mapping[str, m.Infra.ConstantDefinition]:
        """Extract all attributes from a class including MRO inheritance."""
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
        seen_names: t.Infra.StrSet = set()

        for base_cls in cls.__mro__[:-1]:
            for attr_name in dir(base_cls):
                if attr_name.startswith("_") or attr_name in seen_names:
                    continue
                defn = (
                    FlextInfraUtilitiesCodegenConstantAnalysis._classify_mro_attribute(
                        cls,
                        class_name,
                        attr_name,
                    )
                )
                if defn is not None:
                    result[attr_name] = defn
                seen_names.add(attr_name)
        return result

    @staticmethod
    def _classify_mro_attribute(
        target_cls: type[object],
        class_name: str,
        attr_name: str,
    ) -> m.Infra.ConstantDefinition | None:
        """Classify a single attribute from the MRO walk."""
        try:
            attr_value = getattr(target_cls, attr_name)
            if (
                callable(attr_value)
                and not isinstance(attr_value, type)
                and hasattr(attr_value, "__self__")
            ):
                return None
            attr_type = type(attr_value).__name__
            return m.Infra.ConstantDefinition(
                name=attr_name,
                value_repr=repr(attr_value)[:100],
                type_annotation=attr_type,
                file_path="<dynamic>",
                class_path=class_name,
                project="flext-core",
                line=1,
            )
        except (AttributeError, ValueError, TypeError, RecursionError):
            return None

    @staticmethod
    def scan_class_attribute_usages(
        root_path: Path,
        class_name: str,
        exclude_patterns: frozenset[str] = frozenset({
            ".mypy_cache",
            "__pycache__",
        }),
        max_files: int = c.Infra.MAX_SCAN_FILES,
    ) -> t.Infra.Pair[t.Infra.StrSet, Mapping[str, Sequence[t.Infra.StrIntPair]]]:
        """Scan workspace for usages of a specific class's attributes."""
        used_names: t.Infra.StrSet = set()
        usage_map: MutableMapping[str, MutableSequence[t.Infra.StrIntPair]] = {}
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
            if search_prefix not in source:
                continue
            files_scanned += 1
            FlextInfraUtilitiesCodegenConstantAnalysis._collect_attribute_refs(
                source,
                search_prefix,
                str(py_file),
                used_names,
                usage_map,
            )
        return used_names, usage_map

    @staticmethod
    def _collect_attribute_refs(
        source: str,
        search_prefix: str,
        file_path: str,
        used_names: t.Infra.StrSet,
        usage_map: MutableMapping[str, MutableSequence[t.Infra.StrIntPair]],
    ) -> None:
        """Collect attribute references from a single file's source text."""
        lines = source.split("\n")
        for line_num, line in enumerate(lines, 1):
            idx = 0
            while True:
                pos = line.find(search_prefix, idx)
                if pos == -1:
                    break
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
                        usage_map[attr_name] = list[tuple[str, int]]()
                    usage_map[attr_name].append((file_path, line_num))
                idx = pos + 1

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
    def analyze_class_object_census(
        class_path: str,
        root_path: Path,
        exclude_patterns: frozenset[str] = frozenset({
            ".mypy_cache",
            "__pycache__",
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
            "__pycache__",
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
            if not FlextUtilities.is_mapping(dup):
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
