"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import fnmatch
import re
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import FlextInfraRefactorRuleLoader

from pydantic import JsonValue, ValidationError

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesIo,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorLoader,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorPydantic,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    FlextInfraUtilitiesRope,
    FlextInfraUtilitiesYaml,
    c,
    m,
    t,
)
from flext_infra.refactor._utilities_census import FlextInfraUtilitiesRefactorCensus


class FlextInfraUtilitiesRefactor(
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorPydantic,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRefactorLoader,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorCensus,
):
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
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

    _MODULE_FAMILY_KEYS: t.StrSequence = (
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
    def is_final_annotation(annotation: object) -> bool:
        """Return whether one AST annotation represents ``Final``."""
        if isinstance(annotation, ast.Name):
            return annotation.id == "Final"
        if isinstance(annotation, ast.Attribute):
            return annotation.attr == "Final"
        if isinstance(annotation, ast.Subscript):
            return FlextInfraUtilitiesRefactor.is_final_annotation(annotation.value)
        return False

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

    @staticmethod
    def default_class_policy_path() -> Path:
        """Return the canonical class-nesting policy document path."""
        return Path(__file__).resolve().parent.parent / "rules" / "class-policy-v2.yml"

    @staticmethod
    def class_nesting_policy_by_family(
        policy_path: Path | None = None,
    ) -> Mapping[str, m.Infra.ClassNestingPolicy]:
        """Load the class-nesting policy matrix keyed by module family."""
        resolved_path = (
            policy_path
            if policy_path is not None
            else FlextInfraUtilitiesRefactor.default_class_policy_path()
        )
        try:
            loaded = FlextInfraUtilitiesRefactor.load_validated_policy_document(
                resolved_path
            )
        except ValueError:
            return {}
        by_family: dict[str, m.Infra.ClassNestingPolicy] = {}
        for raw in FlextInfraUtilitiesRefactor.mapping_list(
            loaded.get("policy_matrix"),
        ):
            try:
                policy = m.Infra.ClassNestingPolicy.model_validate(raw)
            except ValidationError:
                continue
            by_family[policy.family_name] = policy
        return by_family

    @staticmethod
    def _class_nesting_target_matches(target_namespace: str, pattern: str) -> bool:
        """Check whether a target namespace matches a forbidden-target pattern."""
        if pattern.endswith(".*"):
            return target_namespace.lower().startswith(pattern[:-2].lower())
        return target_namespace == pattern

    @staticmethod
    def _class_nesting_violation(
        *,
        symbol: str,
        family: str,
        target_namespace: str,
        is_helper: bool,
        policy_by_family: Mapping[str, m.Infra.ClassNestingPolicy],
    ) -> t.StrMapping | None:
        """Build a policy violation payload when class nesting is forbidden."""
        policy = policy_by_family.get(family)
        if policy is None:
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "unknown_module_family",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"declare explicit policy for {family}"
                ),
            }
        operation = (
            c.Infra.ReportKeys.HELPER_CONSOLIDATION
            if is_helper
            else c.Infra.ReportKeys.CLASS_NESTING
        )
        if operation not in policy.allowed_operations:
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "operation_not_allowed",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"allow {operation} in policy for {family}"
                ),
            }
        if operation in policy.forbidden_operations:
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "operation_forbidden",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"remove {operation} from forbidden_operations for {family}"
                ),
            }
        if any(
            FlextInfraUtilitiesRefactor._class_nesting_target_matches(
                target_namespace,
                pattern,
            )
            for pattern in policy.forbidden_targets
        ):
            return {
                c.Infra.ReportKeys.RULE_ID: f"precheck:{symbol}",
                c.Infra.ReportKeys.SOURCE_SYMBOL: symbol,
                c.Infra.ReportKeys.VIOLATION_TYPE: "forbidden_target",
                c.Infra.ReportKeys.SUGGESTED_FIX: (
                    f"choose allowed target for family {family}"
                ),
            }
        return None

    @staticmethod
    def validate_class_nesting_entry(
        entry: t.StrMapping,
        *,
        policy_by_family: Mapping[str, m.Infra.ClassNestingPolicy] | None = None,
        policy_path: Path | None = None,
    ) -> t.Infra.Pair[bool, t.StrMapping | None]:
        """Validate one class/helper nesting entry against the family policy."""
        symbol = entry.get(c.Infra.ReportKeys.LOOSE_NAME, "") or entry.get(
            "helper_name",
            "",
        )
        target_namespace = entry.get(c.Infra.ReportKeys.TARGET_NAMESPACE, "")
        current_file = entry.get(c.Infra.ReportKeys.CURRENT_FILE, "")
        if not symbol or not target_namespace or not current_file:
            return (True, None)
        family = FlextInfraUtilitiesRefactor.module_family_from_path(current_file)
        if family == "other_private":
            return (True, None)
        policies = (
            policy_by_family
            if policy_by_family is not None
            else FlextInfraUtilitiesRefactor.class_nesting_policy_by_family(policy_path)
        )
        violation = FlextInfraUtilitiesRefactor._class_nesting_violation(
            symbol=symbol,
            family=family,
            target_namespace=target_namespace,
            is_helper=bool(entry.get("helper_name", "")),
            policy_by_family=policies,
        )
        return (False, violation) if violation is not None else (True, None)

    @staticmethod
    def apply_nested_class_propagation(
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        mappings: t.StrMapping,
        changes: MutableSequence[str],
    ) -> str:
        """Apply nested class propagation and persist only when content changes."""
        source = FlextInfraUtilitiesRope.read_source(resource)
        updated = source
        for old_name, new_name in mappings.items():
            updated, _ = FlextInfraUtilitiesRope.replace_in_source(
                rope_project,
                resource,
                rf"\b{re.escape(old_name)}\b",
                new_name,
                apply=False,
            )
        if updated != source:
            changes.append(
                f"Applied nested class propagation ({len(mappings)} renames)"
            )
            FlextInfraUtilitiesRope.write_source(
                rope_project,
                resource,
                updated,
                description="nested class propagation",
            )
        return updated

    # ── Engine file collection ─────────────────────────────────────────

    @staticmethod
    def filter_engine_files(
        candidates: Sequence[Path],
        *,
        base_path: Path,
        pattern: str,
        ignore_patterns: set[str],
        allowed_extensions: set[str],
    ) -> Sequence[Path]:
        """Filter candidate files by pattern, extensions, and ignore rules."""

        def _accept(f: Path) -> bool:
            rel = str(f.relative_to(base_path))
            if not (fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f.name, pattern)):
                return False
            if allowed_extensions and f.suffix not in allowed_extensions:
                return False
            if f.name in ignore_patterns:
                return False
            rp = f.relative_to(base_path)
            return not any(part in ignore_patterns for part in rp.parts) and not any(
                fnmatch.fnmatch(str(rp), ip) for ip in ignore_patterns
            )

        return [f for f in candidates if _accept(f)]

    @staticmethod
    def collect_engine_project_files(
        rule_loader: FlextInfraRefactorRuleLoader,
        config: t.Infra.InfraValue,
        project: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> MutableSequence[Path] | None:
        """Iterate and filter Python files under a project.

        Returns None on error.
        """
        loader = rule_loader
        scan_dirs = frozenset(loader.extract_project_scan_dirs(config))
        ir = FlextInfraUtilitiesRefactor.iter_python_files(
            workspace_root=project,
            project_roots=[project],
            include_tests=c.Infra.Directories.TESTS in scan_dirs,
            include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
            include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
            src_dirs=scan_dirs or None,
        )
        if ir.is_failure:
            FlextInfraUtilitiesRefactorCli.refactor_error(
                ir.error or f"File iteration failed for {project}",
            )
            return None
        ign, ext = loader.extract_engine_file_filters(config)
        return list(
            FlextInfraUtilitiesRefactor.filter_engine_files(
                ir.value,
                base_path=project,
                pattern=pattern,
                ignore_patterns={str(i) for i in ign},
                allowed_extensions={str(i) for i in ext},
            )
        )

    @staticmethod
    def collect_engine_workspace_files(
        rule_loader: FlextInfraRefactorRuleLoader,
        config: t.Infra.InfraValue,
        workspace_root: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> Sequence[Path]:
        """Collect all candidate files under workspace projects."""
        loader = rule_loader
        root = workspace_root.resolve()
        scan_dirs = frozenset(loader.extract_project_scan_dirs(config))
        projects = FlextInfraUtilitiesRefactor.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        ign, ext = loader.extract_engine_file_filters(config)
        ignore_patterns = {str(i) for i in ign}
        allowed_extensions = {str(i) for i in ext}
        all_files: MutableSequence[Path] = []
        for proj in projects:
            ir = FlextInfraUtilitiesRefactor.iter_python_files(
                workspace_root=root,
                project_roots=[proj],
                include_tests=c.Infra.Directories.TESTS in scan_dirs,
                include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
                include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
                src_dirs=scan_dirs or None,
            )
            if ir.is_failure:
                FlextInfraUtilitiesRefactorCli.refactor_error(
                    ir.error or f"File iteration failed for {proj}",
                )
                continue
            all_files.extend(
                FlextInfraUtilitiesRefactor.filter_engine_files(
                    ir.value,
                    base_path=proj,
                    pattern=pattern,
                    ignore_patterns=ignore_patterns,
                    allowed_extensions=allowed_extensions,
                )
            )
        return all_files


__all__ = ["FlextInfraUtilitiesRefactor"]
