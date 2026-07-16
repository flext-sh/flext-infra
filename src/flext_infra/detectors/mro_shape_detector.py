"""Detect MRO-shape violations (ENFORCE-046/047/049/051) via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from flext_core import u
from flext_infra import m, t, u
from flext_infra._constants.rope import FlextInfraConstantsRope


class FlextInfraMROShapeDetector:
    """Detect MRO-shape violations using rope structural/semantic analysis."""

    _BINARY_ARITY = 2
    _CANONICAL_ALIAS_SUFFIXES: ClassVar[tuple[str, ...]] = (
        "Constants",
        "Models",
        "Protocols",
        "Base",
        "Types",
        "Utilities",
    )

    @staticmethod
    def detect_file(
        ctx: p.Infra.DetectorContext,
    ) -> t.SequenceOf[p.Infra.MROShapeViolation]:
        """Detect ENFORCE-046/047/049/051 for every local class in ``file_path``."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        res = u.Infra.fetch_python_resource(
            rope_project, file_path, skip_protected=True
        )
        if res is None:
            FlextInfraMROShapeDetector._record_parse_failure(
                ctx,
                error_type="ResourceNotFound",
                detail=f"Cannot resolve {file_path.name}",
            )
            return ()
        try:
            pymodule = u.Infra.get_pymodule(rope_project, res)
        except (
            *FlextInfraConstantsRope.RUNTIME_ERRORS,
            *FlextInfraConstantsRope.SYNTAX_ERRORS,
            TypeError,
            AttributeError,
            ValueError,
        ) as exc:
            FlextInfraMROShapeDetector._record_parse_failure(
                ctx, error_type=type(exc).__name__, detail=str(exc)
            )
            return ()
        tree = pymodule.get_ast()
        parent_map = FlextInfraMROShapeDetector._build_parent_map(tree)
        class_nodes = FlextInfraMROShapeDetector._collect_class_nodes(tree, parent_map)
        package_name = u.Infra.package_name(file_path).split(".", 1)[0]
        project_name = ctx.project_name or package_name.replace("_", "-")
        project_prefix = FlextInfraMROShapeDetector._project_prefix(project_name)
        valid_suffixes = FlextInfraMROShapeDetector._valid_alias_suffixes(package_name)
        violations: list[p.Infra.MROShapeViolation] = []
        for node, qualname in class_nodes:
            bases = FlextInfraMROShapeDetector._class_bases(node)
            if not bases:
                continue
            first_base = bases[0]
            is_nested = "." in qualname
            class_name = qualname.rsplit(".", 1)[-1]
            if is_nested:
                violation = FlextInfraMROShapeDetector._check_enforce_046(
                    node=node,
                    qualname=qualname,
                    first_base=first_base,
                    file_path=file_path,
                )
                if violation is not None:
                    violations.append(violation)
                continue
            utility_check = FlextInfraMROShapeDetector._check_enforce_051(
                node=node,
                class_name=class_name,
                bases=bases,
                first_base=first_base,
                file_path=file_path,
            )
            if utility_check is not None:
                violations.append(utility_check)
                continue
            facade_check = FlextInfraMROShapeDetector._check_enforce_047_049(
                node=node,
                class_name=class_name,
                bases=bases,
                first_base=first_base,
                project_prefix=project_prefix,
                valid_suffixes=valid_suffixes,
                pymodule=pymodule,
                file_path=file_path,
            )
            if facade_check is not None:
                violations.append(facade_check)
        return tuple(violations)

    @staticmethod
    def _record_parse_failure(
        ctx: p.Infra.DetectorContext, *, error_type: str, detail: str
    ) -> None:
        """Record MRO-shape parse failures, or fail loud without a collector."""
        if ctx.parse_failures is None:
            msg = f"mro_shape detector could not parse {ctx.file_path}: {detail}"
            raise RuntimeError(msg)
        ctx.parse_failures.append(
            m.Infra.ParseFailureViolation(
                file=str(ctx.file_path),
                stage="mro_shape",
                error_type=error_type,
                detail=detail,
            )
        )

    @staticmethod
    def _project_prefix(project_name: str) -> str:
        """Return the public class prefix for an installed or staged project."""
        try:
            return u.derive_class_stem(project_name)
        except RuntimeError:
            normalized_name = project_name.replace("-", "_").replace(".", "_")
            return "".join(
                part[:1].upper() + part[1:]
                for part in normalized_name.split("_")
                if part
            )

    @classmethod
    def _valid_alias_suffixes(cls, package_name: str) -> tuple[str, ...]:
        """Return metadata suffixes, or canonical FLEXT suffixes, plus ``*Base``."""
        suffixes = tuple(suffix for _, _, suffix in u.lazy_alias_suffixes(package_name))
        if not suffixes:
            suffixes = cls._CANONICAL_ALIAS_SUFFIXES
        return suffixes + tuple(f"{suffix}Base" for suffix in suffixes)

    @staticmethod
    def _is_facade(class_name: str, project_prefix: str) -> bool:
        """Return True when ``class_name`` is a module-level facade candidate."""
        return class_name.startswith((project_prefix, f"Tests{project_prefix}"))

    @staticmethod
    def _is_alias_or_service_base(
        base_name: str, valid_suffixes: tuple[str, ...]
    ) -> bool:
        """Return True when ``base_name`` is an alias, alias-base, or service root."""
        unparametrized = base_name.split("[", 1)[0]
        return unparametrized == "FlextService" or unparametrized.endswith(
            valid_suffixes
        )

    @staticmethod
    def _is_service_alias_base(
        first_base: str, project_prefix: str, pymodule: t.Infra.RopePyModule
    ) -> bool:
        """Return True when the first base is a project service alias base."""
        unparametrized = first_base.split("[", 1)[0]
        if not unparametrized.startswith(project_prefix):
            return False
        attributes = pymodule.get_attributes()
        if unparametrized not in attributes:
            return False
        try:
            obj = attributes[unparametrized].get_object()
        except (TypeError, AttributeError, ValueError):
            return False
        if not u.Infra.is_pyclass(obj):
            return False
        for superclass in obj.get_superclasses():
            name = u.Infra.superclass_name(superclass)
            if name.split("[", 1)[0] == "FlextService":
                return True
        return False

    @staticmethod
    def _alias_base_set(
        base_name: str, valid_suffixes: tuple[str, ...], pymodule: t.Infra.RopePyModule
    ) -> set[str]:
        """Return alias-base names reachable from one base class via rope."""
        attributes = pymodule.get_attributes()
        if base_name not in attributes:
            return set()
        try:
            obj = attributes[base_name].get_object()
        except (TypeError, AttributeError, ValueError):
            return set()
        if not u.Infra.is_pyclass(obj):
            return set()
        ancestors = {
            u.Infra.superclass_name(superclass).split("[", 1)[0]
            for superclass in FlextInfraMROShapeDetector._all_superclasses(obj)
        }
        return {name for name in ancestors if name.endswith(valid_suffixes)}

    @staticmethod
    def _single_peer_base_allowed(
        *,
        class_name: str,
        first_base: str,
        project_prefix: str,
        valid_suffixes: tuple[str, ...],
        pymodule: t.Infra.RopePyModule,
    ) -> bool:
        """Return True when a single peer base carries an alias-base ancestor."""
        if not FlextInfraMROShapeDetector._is_facade(class_name, project_prefix):
            return False
        unparametrized = first_base.split("[", 1)[0]
        if not unparametrized.startswith(project_prefix):
            return False
        if unparametrized.endswith(valid_suffixes):
            return False
        return bool(
            FlextInfraMROShapeDetector._alias_base_set(
                unparametrized, valid_suffixes, pymodule
            )
        )

    @staticmethod
    def _peer_first_allowed(
        *,
        class_name: str,
        bases: t.StrSequence,
        first_base: str,
        project_prefix: str,
        valid_suffixes: tuple[str, ...],
        pymodule: t.Infra.RopePyModule,
    ) -> bool:
        """Return True when ENFORCE-049 allows a peer concrete base first."""
        if not FlextInfraMROShapeDetector._is_facade(class_name, project_prefix):
            return False
        if len(bases) < FlextInfraMROShapeDetector._BINARY_ARITY:
            return False
        unparametrized = first_base.split("[", 1)[0]
        if not unparametrized.startswith(project_prefix):
            return False
        if unparametrized.endswith(valid_suffixes):
            return False
        alias_base_sets = [
            FlextInfraMROShapeDetector._alias_base_set(
                base.split("[", 1)[0], valid_suffixes, pymodule
            )
            for base in bases
        ]
        non_empty = [base_set for base_set in alias_base_sets if base_set]
        if not non_empty:
            return False
        return bool(set.intersection(*non_empty))

    @staticmethod
    def _all_superclasses(
        pyclass: object, visited: frozenset[int] | None = None
    ) -> t.SequenceOf[object]:
        """Return every superclass reachable from ``pyclass`` via rope."""
        visited_ids = visited or frozenset()
        class_id = id(pyclass)
        if class_id in visited_ids:
            return ()
        next_visited = visited_ids | {class_id}
        get_superclasses = getattr(pyclass, "get_superclasses", None)
        if not callable(get_superclasses):
            return ()
        try:
            raw_superclasses = get_superclasses()
        except (TypeError, AttributeError, ValueError):
            return ()
        direct: tuple[object, ...] = ()
        if isinstance(raw_superclasses, tuple):
            direct = raw_superclasses
        elif isinstance(raw_superclasses, Iterable):
            direct = tuple(raw_superclasses)
        result: list[object] = list(direct)
        for superclass in direct:
            result.extend(
                FlextInfraMROShapeDetector._all_superclasses(
                    superclass, visited=next_visited
                )
            )
        return tuple(result)

    @staticmethod
    def _check_enforce_047_049(
        *,
        node: object,
        class_name: str,
        bases: t.StrSequence,
        first_base: str,
        project_prefix: str,
        valid_suffixes: tuple[str, ...],
        pymodule: t.Infra.RopePyModule,
        file_path: Path,
    ) -> p.Infra.MROShapeViolation | None:
        """Return ENFORCE-047/049 violation when facade first base is invalid."""
        if not FlextInfraMROShapeDetector._is_facade(class_name, project_prefix):
            return None
        unparametrized = first_base.split("[", 1)[0]
        if FlextInfraMROShapeDetector._is_utilities_self_root(
            file_path, unparametrized
        ):
            return None
        if FlextInfraMROShapeDetector._is_alias_or_service_base(
            unparametrized, valid_suffixes
        ):
            return None
        if FlextInfraMROShapeDetector._is_service_alias_base(
            first_base, project_prefix, pymodule
        ):
            return None
        if len(bases) == 1 and FlextInfraMROShapeDetector._single_peer_base_allowed(
            class_name=class_name,
            first_base=first_base,
            project_prefix=project_prefix,
            valid_suffixes=valid_suffixes,
            pymodule=pymodule,
        ):
            return None
        if len(bases) >= FlextInfraMROShapeDetector._BINARY_ARITY and (
            FlextInfraMROShapeDetector._peer_first_allowed(
                class_name=class_name,
                bases=bases,
                first_base=first_base,
                project_prefix=project_prefix,
                valid_suffixes=valid_suffixes,
                pymodule=pymodule,
            )
        ):
            return None
        line = getattr(node, "lineno", 1)
        detail = (
            f"Facade '{class_name}' has {len(bases)} bases and first base "
            f"'{unparametrized}' is not an alias, alias-base, FlextService, "
            f"or allowed peer concrete"
        )
        return m.Infra.MROShapeViolation(
            file=str(file_path),
            line=line if isinstance(line, int) and line > 0 else 1,
            class_name=class_name,
            rule_id="047",
            detail=detail,
            first_base=unparametrized,
            expected_base="alias, alias-base, FlextService, or allowed peer",
        )

    @staticmethod
    def _check_enforce_046(
        *, node: object, qualname: str, first_base: str, file_path: Path
    ) -> p.Infra.MROShapeViolation | None:
        """Return ENFORCE-046 violation for redundant nested namespace class."""
        outer_name, _, _ = qualname.partition(".")
        first_base_qualname = first_base.split("[", 1)[0]
        if first_base_qualname != outer_name:
            return None
        if not FlextInfraMROShapeDetector._has_only_dunder_attrs(node):
            return None
        line = getattr(node, "lineno", 1)
        detail = (
            f"Nested class '{qualname}' redundantly inherits from outer "
            f"class '{outer_name}' and has only dunder attributes"
        )
        return m.Infra.MROShapeViolation(
            file=str(file_path),
            line=line if isinstance(line, int) and line > 0 else 1,
            class_name=qualname,
            rule_id="046",
            detail=detail,
            first_base=first_base_qualname,
            expected_base="remove redundant inner namespace",
        )

    @staticmethod
    def _check_enforce_051(
        *,
        node: object,
        class_name: str,
        bases: t.StrSequence,
        first_base: str,
        file_path: Path,
    ) -> p.Infra.MROShapeViolation | None:
        """Return ENFORCE-051 violation for utilities.py self-root import."""
        if len(bases) < FlextInfraMROShapeDetector._BINARY_ARITY:
            return None
        if not FlextInfraMROShapeDetector._is_utilities_self_root(
            file_path, first_base
        ):
            return None
        if not FlextInfraMROShapeDetector._class_body_uses_name(node, "u"):
            return None
        line = getattr(node, "lineno", 1)
        detail = (
            f"utilities.py class '{class_name}' uses 'u' as first base and "
            f"references 'u' in its body"
        )
        return m.Infra.MROShapeViolation(
            file=str(file_path),
            line=line if isinstance(line, int) and line > 0 else 1,
            class_name=class_name,
            rule_id="051",
            detail=detail,
            first_base="u",
            expected_base="explicit utility class instead of self-root 'u'",
        )

    @staticmethod
    def _is_utilities_self_root(file_path: Path, first_base: str) -> bool:
        """Return True for utilities.py classes rooted in the local ``u`` facade."""
        return file_path.name == "utilities.py" and first_base.split("[", 1)[0] == "u"

    @staticmethod
    def _class_bases(node: object) -> t.StrSequence:
        """Return base names for a ClassDef AST node via rope."""
        raw_bases = getattr(node, "bases", ())
        if not isinstance(raw_bases, (list, tuple)):
            return ()
        return tuple(
            base_name
            for base in raw_bases
            if (base_name := u.Infra.class_base_name(base))
        )

    @staticmethod
    def _build_parent_map(tree: object) -> dict[int, object]:
        """Map child node id -> parent node for the full module AST."""
        parent_map: dict[int, object] = {}
        stack: list[object] = [tree]
        while stack:
            parent = stack.pop()
            for field_name in getattr(parent, "_fields", ()):
                value = getattr(parent, field_name, None)
                if isinstance(value, list):
                    for child in value:
                        if hasattr(child, "_fields"):
                            parent_map[id(child)] = parent
                            stack.append(child)
                elif hasattr(value, "_fields"):
                    parent_map[id(value)] = parent
                    stack.append(value)
        return parent_map

    @staticmethod
    def _collect_class_nodes(
        tree: object, parent_map: dict[int, object]
    ) -> t.SequenceOf[tuple[object, str]]:
        """Return every ClassDef node with its dotted qualname."""
        result: list[tuple[object, str]] = []
        for node in u.Infra.walk_ast_nodes(tree):
            if u.Infra.node_kind(node) != "ClassDef":
                continue
            name = getattr(node, "name", "")
            if not isinstance(name, str) or not name:
                continue
            chain = [name]
            current = node
            while True:
                parent = parent_map.get(id(current))
                if parent is None:
                    break
                if u.Infra.node_kind(parent) == "ClassDef":
                    parent_name = getattr(parent, "name", "")
                    if isinstance(parent_name, str) and parent_name:
                        chain.append(parent_name)
                current = parent
            chain.reverse()
            result.append((node, ".".join(chain)))
        return tuple(result)

    @staticmethod
    def _has_only_dunder_attrs(node: object) -> bool:
        """Return True when a class body contains only dunder attributes."""
        body = getattr(node, "body", ())
        if not isinstance(body, (list, tuple)):
            return True
        for statement in body:
            kind = u.Infra.node_kind(statement)
            if kind in {"FunctionDef", "AsyncFunctionDef", "ClassDef"}:
                return False
            if kind in {"Assign", "AnnAssign"}:
                names = u.Infra.assignment_target_names(statement)
                if any(
                    not (name.startswith("__") and name.endswith("__"))
                    for name in names
                    if name
                ):
                    return False
        return True

    @staticmethod
    def _class_body_uses_name(node: object, name: str) -> bool:
        """Return True when a method body references ``name`` as a name/attribute."""
        body = getattr(node, "body", ())
        if not isinstance(body, (list, tuple)):
            return False
        for statement in body:
            if u.Infra.node_kind(statement) not in {"FunctionDef", "AsyncFunctionDef"}:
                continue
            for child in u.Infra.walk_ast_nodes(statement):
                if (
                    u.Infra.node_kind(child) == "Name"
                    and getattr(child, "id", "") == name
                ):
                    return True
                if u.Infra.node_kind(child) == "Attribute" and getattr(
                    child, "attr", ""
                ):
                    value = getattr(child, "value", None)
                    if (
                        value is not None
                        and u.Infra.node_kind(value) == "Name"
                        and getattr(value, "id", "") == name
                    ):
                        return True
        return False


__all__: list[str] = ["FlextInfraMROShapeDetector"]
