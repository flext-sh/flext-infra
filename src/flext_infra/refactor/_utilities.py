"""Refactor/CST helper utilities for infrastructure code analysis.

Centralizes CST (Concrete Syntax Tree) helpers previously defined as
module-level functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import libcst as cst
from pydantic import BaseModel, JsonValue, TypeAdapter, ValidationError

from flext_infra import (
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorLoader,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorPydantic,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    FlextInfraUtilitiesYaml,
    c,
    m,
    t,
)

_STR_MAPPING_ADAPTER: TypeAdapter[Sequence[t.StrMapping]] = TypeAdapter(
    Sequence[t.StrMapping],
)
_INFRA_SEQ_ADAPTER: TypeAdapter[Sequence[t.Infra.InfraValue]] = TypeAdapter(
    Sequence[t.Infra.InfraValue],
)
_INFRA_MAPPING_ADAPTER: TypeAdapter[Mapping[str, t.Infra.InfraValue]] = TypeAdapter(
    Mapping[str, t.Infra.InfraValue],
)


class FlextInfraUtilitiesRefactor(
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorPydantic,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    FlextInfraUtilitiesRefactorLoader,
    FlextInfraUtilitiesRefactorCli,
):
    """CST/refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        name = FlextInfraUtilitiesParsing.cst_module_name(cst_expr)
    """

    @staticmethod
    def module_path(*, file_path: Path, project_root: Path) -> str:
        """Compute dotted module path relative to a project root.

        Strips the ``src/`` directory component and file extension.

        Args:
            file_path: Absolute path to a Python file.
            project_root: Root directory of the project.

        Returns:
            Dotted module path (e.g., ``"flext_infra.refactor.engine"``).

        """
        rel = file_path.relative_to(project_root)
        parts = [part for part in rel.with_suffix("").parts if part != "src"]
        return ".".join(parts)

    _MODULE_FAMILY_KEYS: Sequence[str] = (
        "_models",
        "_utilities",
        "_dispatcher",
        "_decorators",
        "_runtime",
    )

    @staticmethod
    def module_family_from_path(path: str) -> str:
        """Resolve module family key from a source file path."""
        normalized = path.replace("\\", "/")
        for key in FlextInfraUtilitiesRefactor._MODULE_FAMILY_KEYS:
            if key in normalized:
                return key
        return "other_private"

    @staticmethod
    def entry_list(value: t.Infra.InfraValue | None) -> Sequence[t.StrMapping]:
        """Normalize class-nesting config entries to a strict list."""
        if value is None:
            return []
        try:
            return _STR_MAPPING_ADAPTER.validate_python(value)
        except ValidationError:
            msg = "class nesting entries must be a list"
            raise ValueError(msg) from None

    @staticmethod
    def string_list(value: t.Infra.InfraValue | None) -> t.StrSequence:
        """Normalize policy fields that should contain string collections."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            try:
                value_items: Sequence[t.Infra.InfraValue] = (
                    _INFRA_SEQ_ADAPTER.validate_python(value)
                )
            except ValidationError as exc:
                msg = "expected list value"
                raise ValueError(msg) from exc
            items: MutableSequence[str] = []
            for item in value_items:
                if not isinstance(item, str):
                    msg = "expected list value"
                    raise TypeError(msg)
                items.append(item)
            return items
        msg = "expected list value"
        raise ValueError(msg)

    @staticmethod
    def mapping_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Normalize policy fields that should contain mapping collections."""
        if value is None:
            return []
        if isinstance(value, list):
            try:
                value_items: Sequence[t.Infra.InfraValue] = (
                    _INFRA_SEQ_ADAPTER.validate_python(value)
                )
            except ValidationError as exc:
                msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
                raise ValueError(msg) from exc
            normalized: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
            for item in value_items:
                if not isinstance(item, dict):
                    continue
                normalized.append(
                    _INFRA_MAPPING_ADAPTER.validate_python(item),
                )
            return normalized
        msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
        raise ValueError(msg)

    @staticmethod
    def has_required_fields(
        entry: t.Infra.InfraValue,
        required_fields: t.StrSequence,
    ) -> bool:
        if not isinstance(entry, dict):
            return False
        return all(key in entry for key in required_fields)

    @staticmethod
    def normalize_module_path(path_value: Path) -> str:
        normalized = path_value.as_posix().replace("\\", "/")
        path = Path(normalized)
        parts = path.parts
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path.as_posix().lstrip("./")

    @staticmethod
    def project_scope_tokens(path_value: Path) -> t.Infra.StrSet:
        normalized = path_value.as_posix().replace("\\", "/")
        parts = Path(normalized).parts
        if not parts:
            return set()
        tokens: t.Infra.StrSet = set()
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            if src_index > 0:
                tokens.add(parts[src_index - 1])
            if src_index + 1 < len(parts):
                tokens.add(parts[src_index + 1])
        return tokens

    @staticmethod
    def rewrite_scope(entry: t.StrMapping) -> str:
        raw_scope = entry.get(c.Infra.ReportKeys.REWRITE_SCOPE, c.Infra.ReportKeys.FILE)
        scope = raw_scope.strip().lower()
        if scope in {
            c.Infra.ReportKeys.FILE,
            c.Infra.PROJECT,
            c.Infra.ReportKeys.WORKSPACE,
        }:
            return scope
        msg = f"unsupported rewrite_scope: {raw_scope}"
        raise ValueError(msg)

    @staticmethod
    def scope_applies_to_file(
        entry: t.StrMapping,
        current_file: Path,
        candidate_file: Path,
    ) -> bool:
        rewrite_scope = FlextInfraUtilitiesRefactor.rewrite_scope(entry)
        if rewrite_scope == c.Infra.ReportKeys.WORKSPACE:
            return True
        current_module = FlextInfraUtilitiesRefactor.normalize_module_path(current_file)
        candidate_module = FlextInfraUtilitiesRefactor.normalize_module_path(
            candidate_file,
        )
        if rewrite_scope == c.Infra.ReportKeys.FILE:
            return current_module == candidate_module
        current_tokens = FlextInfraUtilitiesRefactor.project_scope_tokens(current_file)
        candidate_tokens = FlextInfraUtilitiesRefactor.project_scope_tokens(
            candidate_file,
        )
        if current_tokens and candidate_tokens:
            return bool(current_tokens & candidate_tokens)
        return current_module == candidate_module

    @staticmethod
    def _extract_definition_required(
        definitions: Mapping[str, t.Infra.InfraValue],
        key: str,
    ) -> t.StrSequence | None:
        """Extract required fields from a named schema definition."""
        raw = definitions.get(key, {})
        if not isinstance(raw, dict):
            return None
        validated: Mapping[str, t.Infra.InfraValue] = (
            _INFRA_MAPPING_ADAPTER.validate_python(raw)
        )
        return FlextInfraUtilitiesRefactor.string_list(validated.get("required", []))

    @staticmethod
    def _all_entries_have_required(
        loaded: Mapping[str, t.Infra.InfraValue],
        field: str,
        required_fields: t.StrSequence,
    ) -> bool:
        """Check all entries under a mapping field have the required keys."""
        return all(
            FlextInfraUtilitiesRefactor.has_required_fields(entry, required_fields)
            for entry in FlextInfraUtilitiesRefactor.mapping_list(loaded.get(field))
        )

    @staticmethod
    def policy_document_schema_valid(
        loaded: Mapping[str, t.Infra.InfraValue],
        schema_path: Path,
    ) -> bool:
        schema_result = FlextInfraUtilitiesIo.read_json(schema_path)
        if schema_result.is_failure:
            return False
        raw_schema: Mapping[str, JsonValue] = schema_result.value
        schema: Mapping[str, t.Infra.InfraValue] = dict(raw_schema.items())
        top_required = FlextInfraUtilitiesRefactor.string_list(
            schema.get("required", []),
        )
        if not FlextInfraUtilitiesRefactor.has_required_fields(loaded, top_required):
            return False
        definitions_raw = schema.get("definitions", {})
        if not isinstance(definitions_raw, dict):
            return False
        try:
            definitions = _INFRA_MAPPING_ADAPTER.validate_python(definitions_raw)
        except ValidationError:
            return False
        policy_entry_required = (
            FlextInfraUtilitiesRefactor._extract_definition_required(
                definitions,
                "policyEntry",
            )
        )
        class_rule_required = FlextInfraUtilitiesRefactor._extract_definition_required(
            definitions,
            "classRule",
        )
        if policy_entry_required is None or class_rule_required is None:
            return False
        return FlextInfraUtilitiesRefactor._all_entries_have_required(
            loaded,
            "policy_matrix",
            policy_entry_required,
        ) and FlextInfraUtilitiesRefactor._all_entries_have_required(
            loaded,
            c.Infra.ReportKeys.RULES,
            class_rule_required,
        )

    @staticmethod
    def load_validated_policy_document(policy_path: Path) -> t.Infra.ContainerDict:
        try:
            loaded = FlextInfraUtilitiesYaml.safe_load_yaml(policy_path)
        except (OSError, TypeError) as exc:
            msg = f"failed to read policy document: {policy_path}"
            raise ValueError(msg) from exc
        raw_dict: Mapping[str, t.Infra.InfraValue] = dict(loaded.items())
        loaded_dict: t.Infra.ContainerDict = _INFRA_MAPPING_ADAPTER.validate_python(
            raw_dict,
        )
        schema_path = policy_path.with_name("class-policy-v2.schema.json")
        if not FlextInfraUtilitiesRefactor.policy_document_schema_valid(
            loaded_dict,
            schema_path,
        ):
            msg = "policy document failed schema validation"
            raise ValueError(msg)
        return loaded_dict

    # ── Generic AST introspection ─────────────────────────────────────

    @staticmethod
    def extract_public_methods_from_dir(
        package_dir: Path,
    ) -> Mapping[str, Sequence[t.Infra.Triple[str, str, str]]]:
        """Extract public methods from all .py files in a package directory.

        Returns:
            ``{class_name: [(method_name, method_type, source_file), ...]}``.

        """
        result: MutableMapping[str, Sequence[t.Infra.Triple[str, str, str]]] = {}
        for py_file in sorted(package_dir.glob(c.Infra.Extensions.PYTHON_GLOB)):
            if py_file.name == c.Infra.Files.INIT_PY:
                continue
            result.update(
                FlextInfraUtilitiesRefactor._extract_classes_ast(py_file),
            )
        return result

    @staticmethod
    def extract_public_methods_from_file(
        file_path: Path,
    ) -> Mapping[str, Sequence[t.Infra.Triple[str, str, str]]]:
        """Extract public methods from a single .py file.

        Returns:
            ``{class_name: [(method_name, method_type, source_file), ...]}``.

        """
        if not file_path.exists():
            return {}
        return FlextInfraUtilitiesRefactor._extract_classes_ast(file_path)

    @staticmethod
    def _append_unique(
        methods: MutableSequence[t.Infra.Triple[str, str, str]],
        entry: t.Infra.Triple[str, str, str],
    ) -> None:
        """Append entry if its name (first element) is not already present."""
        if not any(e[0] == entry[0] for e in methods):
            methods.append(entry)

    @staticmethod
    def _collect_inner_class_methods(
        inner_cls: ast.ClassDef,
        filename: str,
        methods: MutableSequence[t.Infra.Triple[str, str, str]],
    ) -> None:
        """Collect public methods from a nested class definition."""
        for inner in ast.iter_child_nodes(inner_cls):
            if isinstance(inner, ast.FunctionDef) and not inner.name.startswith("_"):
                entry = (f"{inner_cls.name}.{inner.name}", "static", filename)
                FlextInfraUtilitiesRefactor._append_unique(methods, entry)

    @staticmethod
    def _extract_classes_ast(
        py_file: Path,
    ) -> Mapping[str, Sequence[t.Infra.Triple[str, str, str]]]:
        """Internal: extract all public methods from classes using stdlib ast."""
        tree = FlextInfraUtilitiesParsing.parse_module_ast(py_file)
        if tree is None:
            return {}
        result: MutableMapping[
            str,
            MutableSequence[t.Infra.Triple[str, str, str]],
        ] = {}
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods: MutableSequence[t.Infra.Triple[str, str, str]] = []
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    decs = [
                        d.id
                        if isinstance(d, ast.Name)
                        else (d.attr if isinstance(d, ast.Attribute) else "")
                        for d in item.decorator_list
                    ]
                    mtype = (
                        "static"
                        if "staticmethod" in decs
                        else ("class" if "classmethod" in decs else "instance")
                    )
                    FlextInfraUtilitiesRefactor._append_unique(
                        methods,
                        (item.name, mtype, py_file.name),
                    )
                elif isinstance(item, ast.ClassDef) and not item.name.startswith("_"):
                    FlextInfraUtilitiesRefactor._collect_inner_class_methods(
                        item,
                        py_file.name,
                        methods,
                    )
            if methods:
                result[node.name] = methods
        return result

    @staticmethod
    def _extract_alias_from_assign(
        item: ast.Assign,
        alias_map: MutableMapping[str, t.Infra.StrPair],
    ) -> None:
        """Extract alias mapping from a staticmethod assignment node."""
        if not isinstance(item.value, ast.Call):
            return
        call = item.value
        if not (
            isinstance(call.func, ast.Name)
            and call.func.id == "staticmethod"
            and call.args
        ):
            return
        arg = call.args[0]
        resolved: t.Infra.StrPair | None = None
        if isinstance(arg, ast.Attribute):
            if isinstance(arg.value, ast.Name):
                resolved = (arg.value.id, arg.attr)
            elif isinstance(arg.value, ast.Attribute) and isinstance(
                arg.value.value,
                ast.Name,
            ):
                resolved = (arg.value.value.id, f"{arg.value.attr}.{arg.attr}")
        if resolved is None:
            return
        for target in item.targets:
            if isinstance(target, ast.Name):
                alias_map[target.id] = resolved

    @staticmethod
    def build_facade_alias_map(
        facade_path: Path,
        facade_class_name: str,
    ) -> Mapping[str, t.Infra.StrPair]:
        """Parse a facade class to build flat alias -> (class, method) map.

        Inspects ``staticmethod(...)`` assignments in the facade class.
        """
        tree = FlextInfraUtilitiesParsing.parse_module_ast(facade_path)
        if tree is None:
            return {}

        alias_map: MutableMapping[str, t.Infra.StrPair] = {}
        for node in ast.iter_child_nodes(tree):
            if not (isinstance(node, ast.ClassDef) and node.name == facade_class_name):
                continue
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.Assign):
                    FlextInfraUtilitiesRefactor._extract_alias_from_assign(
                        item,
                        alias_map,
                    )
        return alias_map

    @staticmethod
    def _extract_inner_class_bases(
        facade_node: ast.ClassDef,
    ) -> MutableMapping[str, str]:
        """Extract inner class name -> first base class name from a facade."""
        name_map: MutableMapping[str, str] = {}
        for item in ast.iter_child_nodes(facade_node):
            if not isinstance(item, ast.ClassDef):
                continue
            for base in item.bases:
                if isinstance(base, ast.Name):
                    name_map[item.name] = base.id
                    break
        return name_map

    @staticmethod
    def build_facade_inner_class_map(
        facade_path: Path,
        facade_class_name: str,
    ) -> t.StrMapping:
        """Map inner class names -> base class names in a facade.

        E.g. ``{"Conversion": "FlextUtilitiesConversion", ...}``.
        """
        tree = FlextInfraUtilitiesParsing.parse_module_ast(facade_path)
        if tree is None:
            return {}

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and node.name == facade_class_name:
                return FlextInfraUtilitiesRefactor._extract_inner_class_bases(node)
        return {}

    @staticmethod
    def identify_project_by_roots(
        file_path: Path,
        project_roots: Sequence[Path],
    ) -> str:
        """Identify project name for a file path (most-specific root wins)."""
        matching_roots = [
            root for root in project_roots if file_path.is_relative_to(root)
        ]
        if not matching_roots:
            return c.Infra.Defaults.UNKNOWN
        best = max(matching_roots, key=lambda root: len(root.parts))
        return best.name

    @staticmethod
    def build_mro_target(
        family: str,
        core_project: str = c.Infra.Census.CORE_PROJECT,
    ) -> m.Infra.MROFamilyTarget:
        """Create a generic target config t.NormalizedValue from a family code."""
        if family not in c.Infra.MRO_FAMILIES:
            msg = f"Invalid MRO family {family}"
            raise ValueError(msg)
        sf = c.Infra.FAMILY_SUFFIXES[family]
        return m.Infra.MROFamilyTarget(
            family=family,
            class_suffix=sf,
            package_dir=c.Infra.MRO_FAMILY_PACKAGE_DIRS[family],
            facade_module=c.Infra.MRO_FAMILY_FACADE_MODULES[family],
            facade_class_prefix=f"Flext{sf}",
            core_project=core_project,
        )

    @staticmethod
    def aggregate_usage_metrics(
        methods: Mapping[str, Sequence[m.Infra.CensusMethodInfo]],
        records: Sequence[m.Infra.CensusUsageRecord],
        files_scanned: int,
        parse_errors: int,
    ) -> m.Infra.UtilitiesCensusReport:
        """Pivot raw AST method visit occurrences into a structured usage report."""
        cnt: Counter[t.Infra.Triple[str, str, str]] = Counter()
        pcnt: Counter[t.Infra.Quad[str, str, str, str]] = Counter()

        for rec in records:
            cnt[rec.class_name, rec.method_name, rec.access_mode] += 1
            pcnt[rec.project, rec.class_name, rec.method_name, rec.access_mode] += 1

        cls_sums: MutableSequence[m.Infra.CensusClassSummary] = []
        unused = 0
        for cls, items in sorted(methods.items()):
            m_list: MutableSequence[m.Infra.CensusMethodSummary] = []
            for m_info in items:
                af = cnt.get(
                    (cls, m_info.name, c.Infra.Census.MODE_ALIAS_FLAT),
                    0,
                )
                an = cnt.get(
                    (cls, m_info.name, c.Infra.Census.MODE_ALIAS_NS),
                    0,
                )
                dr = cnt.get((cls, m_info.name, c.Infra.Census.MODE_DIRECT), 0)
                tot = af + an + dr
                if tot == 0:
                    unused += 1
                m_list.append(
                    m.Infra.CensusMethodSummary(
                        name=m_info.name,
                        method_type=m_info.method_type,
                        alias_flat=af,
                        alias_namespaced=an,
                        direct=dr,
                        total=tot,
                    ),
                )
            cls_sums.append(
                m.Infra.CensusClassSummary(
                    class_name=cls,
                    source_file=items[0].source_file if items else "",
                    methods=m_list,
                ),
            )

        pj_sums: MutableMapping[
            str,
            MutableSequence[m.Infra.CensusProjectMethodUsage],
        ] = defaultdict(list)
        for (pj, cls, mx, mo), co in sorted(pcnt.items()):
            pj_sums[pj].append(
                m.Infra.CensusProjectMethodUsage(
                    class_name=cls,
                    method_name=mx,
                    access_mode=mo,
                    count=co,
                ),
            )

        return m.Infra.UtilitiesCensusReport(
            classes=cls_sums,
            projects=[
                m.Infra.CensusProjectSummary(
                    project_name=p,
                    usages=us,
                    total=sum(u.count for u in us),
                )
                for p, us in sorted(pj_sums.items())
            ],
            total_classes=len(methods),
            total_methods=sum(len(v) for v in methods.values()),
            total_usages=len(records),
            total_unused=unused,
            files_scanned=files_scanned,
            parse_errors=parse_errors,
        )

    @staticmethod
    def export_pydantic_json(model_payload: BaseModel, export_path: Path) -> None:
        """Serialize any Pydantic model payload to a JSON file."""
        # Fallback to pure path string write since model_dump_json takes care of formatting
        export_path.write_text(
            model_payload.model_dump_json(indent=2),
            encoding=c.Infra.Encoding.DEFAULT,
        )

    @staticmethod
    def scan_cst_with_visitors(
        file_path: Path,
        *visitors: cst.CSTVisitor,
    ) -> cst.Module | None:
        """Parse CST and sequentially apply an arbitrary number of visitors."""
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if not tree:
            return None
        for visitor in visitors:
            tree.visit(visitor)
        return tree

    @staticmethod
    def is_final_annotation(*, annotation: ast.expr) -> bool:
        """Check if an annotation is ``Final`` or ``Final[T]``.

        Args:
            annotation: AST expression node to check.

        Returns:
            True if the annotation is Final or Final[T], False otherwise.

        """
        final_name = c.Infra.FINAL_ANNOTATION_NAME
        if isinstance(annotation, ast.Name):
            return annotation.id == final_name
        if isinstance(annotation, ast.Attribute):
            return annotation.attr == final_name
        if isinstance(annotation, ast.Subscript):
            base = annotation.value
            if isinstance(base, ast.Name):
                return base.id == final_name
            if isinstance(base, ast.Attribute):
                return base.attr == final_name
        return False


__all__ = ["FlextInfraUtilitiesRefactor"]
