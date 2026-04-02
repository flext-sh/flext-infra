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
from pydantic import BaseModel, JsonValue, ValidationError

from flext_core import FlextUtilities
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
            return t.Infra.STR_MAPPING_SEQ_ADAPTER.validate_python(value)
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
        if not isinstance(value, list):
            msg = "expected list value"
            raise TypeError(msg)
        try:
            validated: Sequence[t.Infra.InfraValue] = (
                t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError as exc:
            msg = "expected list value"
            raise ValueError(msg) from exc
        for item in validated:
            if not isinstance(item, str):
                msg = "expected list value"
                raise TypeError(msg)
        return [v for v in validated if isinstance(v, str)]

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
                    t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
                )
            except ValidationError as exc:
                msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
                raise ValueError(msg) from exc
            normalized: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
            for item in value_items:
                if not FlextUtilities.is_mapping(item):
                    continue
                normalized.append(
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item),
                )
            return normalized
        msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
        raise ValueError(msg)

    @staticmethod
    def has_required_fields(
        entry: t.Infra.InfraValue,
        required_fields: t.StrSequence,
    ) -> bool:
        if not FlextUtilities.is_mapping(entry):
            return False
        return all(key in entry for key in required_fields)

    @staticmethod
    def normalize_module_path(path_value: Path) -> str:
        parts = path_value.parts
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path_value.as_posix().lstrip("./")

    @staticmethod
    def project_scope_tokens(path_value: Path) -> t.Infra.StrSet:
        parts = path_value.parts
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
        scope = FlextUtilities.norm_str(raw_scope, case="lower")
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
    def policy_document_schema_valid(
        loaded: Mapping[str, t.Infra.InfraValue],
        schema_path: Path,
    ) -> bool:
        schema_result = FlextInfraUtilitiesIo.read_json(schema_path)
        if schema_result.is_failure:
            return False
        raw_schema: Mapping[str, JsonValue] = schema_result.value
        schema: Mapping[str, t.Infra.InfraValue] = dict(raw_schema)
        top_required = FlextInfraUtilitiesRefactor.string_list(
            schema.get("required", []),
        )
        if not FlextInfraUtilitiesRefactor.has_required_fields(loaded, top_required):
            return False
        definitions_raw = schema.get("definitions", {})
        if not FlextUtilities.is_mapping(definitions_raw):
            return False
        try:
            definitions = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(definitions_raw)
        except ValidationError:
            return False

        def _definition_required(key: str) -> t.StrSequence | None:
            raw = definitions.get(key, {})
            if not FlextUtilities.is_mapping(raw):
                return None
            validated: Mapping[str, t.Infra.InfraValue] = (
                t.Infra.INFRA_MAPPING_ADAPTER.validate_python(raw)
            )
            return FlextInfraUtilitiesRefactor.string_list(
                validated.get("required", []),
            )

        def _all_have_required(field: str, required: t.StrSequence) -> bool:
            return all(
                FlextInfraUtilitiesRefactor.has_required_fields(entry, required)
                for entry in FlextInfraUtilitiesRefactor.mapping_list(
                    loaded.get(field),
                )
            )

        policy_req = _definition_required("policyEntry")
        rule_req = _definition_required("classRule")
        if policy_req is None or rule_req is None:
            return False
        return _all_have_required(
            "policy_matrix",
            policy_req,
        ) and _all_have_required(c.Infra.ReportKeys.RULES, rule_req)

    @staticmethod
    def load_validated_policy_document(policy_path: Path) -> t.Infra.ContainerDict:
        try:
            loaded = FlextInfraUtilitiesYaml.safe_load_yaml(policy_path)
        except (OSError, TypeError) as exc:
            msg = f"failed to read policy document: {policy_path}"
            raise ValueError(msg) from exc
        raw_dict: Mapping[str, t.Infra.InfraValue] = dict(loaded)
        loaded_dict: t.Infra.ContainerDict = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                raw_dict,
            )
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
    def _decorator_method_type(func: ast.FunctionDef) -> str:
        """Resolve method type from decorator list."""
        for dec in func.decorator_list:
            if isinstance(dec, ast.Name):
                name = dec.id
            elif isinstance(dec, ast.Attribute):
                name = dec.attr
            else:
                continue
            if name == "staticmethod":
                return "static"
            if name == "classmethod":
                return "class"
        return "instance"

    @staticmethod
    def _extract_classes_ast(
        py_file: Path,
    ) -> Mapping[str, Sequence[t.Infra.Triple[str, str, str]]]:
        """Extract all public methods from classes using stdlib ast."""
        tree = FlextInfraUtilitiesParsing.parse_module_ast(py_file)
        if tree is None:
            return {}
        result: MutableMapping[
            str,
            MutableSequence[t.Infra.Triple[str, str, str]],
        ] = {}
        filename = py_file.name
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods: MutableSequence[t.Infra.Triple[str, str, str]] = []
            seen: set[str] = set()
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                    if item.name not in seen:
                        seen.add(item.name)
                        mtype = FlextInfraUtilitiesRefactor._decorator_method_type(item)
                        methods.append((item.name, mtype, filename))
                elif isinstance(item, ast.ClassDef) and not item.name.startswith("_"):
                    for inner in ast.iter_child_nodes(item):
                        if isinstance(
                            inner, ast.FunctionDef
                        ) and not inner.name.startswith("_"):
                            qualified = f"{item.name}.{inner.name}"
                            if qualified not in seen:
                                seen.add(qualified)
                                methods.append((qualified, "static", filename))
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
            if not (isinstance(node, ast.ClassDef) and node.name == facade_class_name):
                continue
            name_map: MutableMapping[str, str] = {}
            for item in ast.iter_child_nodes(node):
                if not isinstance(item, ast.ClassDef):
                    continue
                for base in item.bases:
                    if isinstance(base, ast.Name):
                        name_map[item.name] = base.id
                        break
            return name_map
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
    def _is_final_name(node: ast.expr) -> bool:
        """Check if a bare Name or Attribute resolves to ``Final``."""
        final = c.Infra.FINAL_ANNOTATION_NAME
        if isinstance(node, ast.Name):
            return node.id == final
        if isinstance(node, ast.Attribute):
            return node.attr == final
        return False

    @staticmethod
    def is_final_annotation(*, annotation: ast.expr) -> bool:
        """Check if an annotation is ``Final`` or ``Final[T]``."""
        if isinstance(annotation, ast.Subscript):
            return FlextInfraUtilitiesRefactor._is_final_name(annotation.value)
        return FlextInfraUtilitiesRefactor._is_final_name(annotation)


__all__ = ["FlextInfraUtilitiesRefactor"]
