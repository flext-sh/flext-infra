"""Bootstrap-safe AST source scanner for MRO migration candidates."""

from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING, ClassVar

from flext_infra._models.mro_scan import FlextInfraModelsMroScan

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraUtilitiesMroScanSource:
    """Find facade aliases and movable top-level symbols using Python AST."""

    _CONSTANT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
    _IDENTIFIER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^_?[A-Za-z][A-Za-z0-9_]*$",
    )
    _FACADE_ALIAS_TEMPLATE: ClassVar[str] = r"(?m)^\s*{alias}\s*=\s*(\w+{suffix})\s*$"
    _CLASS_SUFFIX_TEMPLATE: ClassVar[str] = r"(?m)^class\s+(\w+{suffix})\b"

    @classmethod
    def find_facade(
        cls,
        source: str,
        spec: FlextInfraModelsMroScan.MROTargetSpec,
    ) -> str:
        """Find the facade class name for a target file."""
        alias_pattern = re.compile(
            cls._FACADE_ALIAS_TEMPLATE.format(
                alias=re.escape(spec.family_alias),
                suffix=re.escape(spec.class_suffix),
            ),
        )
        if alias_match := alias_pattern.search(source):
            return alias_match.group(1)
        suffix_pattern = re.compile(
            cls._CLASS_SUFFIX_TEMPLATE.format(suffix=re.escape(spec.class_suffix)),
        )
        return (
            suffix_match.group(1)
            if (suffix_match := suffix_pattern.search(source))
            else ""
        )

    @classmethod
    def candidates(
        cls,
        source: str,
        spec: FlextInfraModelsMroScan.MROTargetSpec,
    ) -> t.SequenceOf[FlextInfraModelsMroScan.MROSymbolCandidate]:
        """Return movable top-level symbols for the target family."""
        tree = ast.parse(source)
        candidates: list[FlextInfraModelsMroScan.MROSymbolCandidate] = []
        for node in tree.body:
            candidate = cls._candidate_from_node(node, spec)
            if candidate is not None:
                candidates.append(candidate)
        return tuple(sorted(candidates, key=lambda item: item.line))

    @classmethod
    def _candidate_from_node(
        cls,
        node: ast.stmt,
        spec: FlextInfraModelsMroScan.MROTargetSpec,
    ) -> FlextInfraModelsMroScan.MROSymbolCandidate | None:
        alias = spec.family_alias
        if alias == "t":
            return cls._typing_candidate(node)
        if alias == "p":
            return cls._protocol_candidate(node)
        return cls._constant_candidate(node)

    @classmethod
    def _constant_candidate(
        cls,
        node: ast.stmt,
    ) -> FlextInfraModelsMroScan.MROSymbolCandidate | None:
        name = cls._assignment_name(node)
        if name is None or name.islower() or cls._CONSTANT_PATTERN.match(name) is None:
            return None
        return cls._candidate(node=node, name=name, kind="constant")

    @classmethod
    def _typing_candidate(
        cls,
        node: ast.stmt,
    ) -> FlextInfraModelsMroScan.MROSymbolCandidate | None:
        name = cls._typing_name(node)
        if name is None or cls._IDENTIFIER_PATTERN.match(name) is None:
            return None
        kind = "typevar" if cls._is_typevar_assignment(node) else "typealias"
        return cls._candidate(node=node, name=name, kind=kind)

    @classmethod
    def _protocol_candidate(
        cls,
        node: ast.stmt,
    ) -> FlextInfraModelsMroScan.MROSymbolCandidate | None:
        if not isinstance(node, ast.ClassDef) or not cls._is_protocol_class(node):
            return None
        return cls._candidate(node=node, name=node.name, kind="protocol")

    @staticmethod
    def _candidate(
        *,
        node: ast.stmt,
        name: str,
        kind: str,
    ) -> FlextInfraModelsMroScan.MROSymbolCandidate:
        line = (
            min(decorator.lineno for decorator in node.decorator_list)
            if isinstance(node, ast.ClassDef) and node.decorator_list
            else node.lineno
        )
        return FlextInfraModelsMroScan.MROSymbolCandidate(
            symbol=name,
            line=line,
            end_line=node.end_lineno
            if node.end_lineno and node.end_lineno > line
            else None,
            kind=kind,
        )

    @staticmethod
    def _assignment_name(node: ast.stmt) -> str | None:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return node.target.id
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            return target.id if isinstance(target, ast.Name) else None
        return None

    @classmethod
    def _typing_name(cls, node: ast.stmt) -> str | None:
        if isinstance(node, ast.TypeAlias):
            return node.name.id
        name = cls._assignment_name(node)
        if isinstance(node, ast.AnnAssign) and cls._annotation_names_type_alias(node):
            return name
        return name if name and cls._is_typevar_assignment(node) else None

    @staticmethod
    def _annotation_names_type_alias(node: ast.AnnAssign) -> bool:
        match node.annotation:
            case ast.Name(id="TypeAlias"):
                return True
            case ast.Attribute(attr="TypeAlias"):
                return True
            case _:
                return False

    @staticmethod
    def _is_typevar_assignment(node: ast.stmt) -> bool:
        value = node.value if isinstance(node, ast.Assign | ast.AnnAssign) else None
        if not isinstance(value, ast.Call):
            return False
        func = value.func
        return (
            isinstance(func, ast.Name)
            and func.id in {"NewType", "ParamSpec", "TypeVar", "TypeVarTuple"}
        ) or (
            isinstance(func, ast.Attribute)
            and func.attr in {"NewType", "ParamSpec", "TypeVar", "TypeVarTuple"}
        )

    @staticmethod
    def _is_protocol_class(node: ast.ClassDef) -> bool:
        for base in node.bases:
            subject = base.value if isinstance(base, ast.Subscript) else base
            if isinstance(subject, ast.Name) and subject.id == "Protocol":
                return True
            if isinstance(subject, ast.Attribute) and subject.attr == "Protocol":
                return True
        return False


__all__: list[str] = ["FlextInfraUtilitiesMroScanSource"]
