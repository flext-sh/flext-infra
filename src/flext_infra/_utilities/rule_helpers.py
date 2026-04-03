"""Shared helper logic extracted from rules/*.py for zero-inline-helper policy.

All private helpers, regex-based parsers, and module-level constants that were
previously defined inside rule files live here as static methods.
"""

from __future__ import annotations

import re
from collections.abc import MutableSequence, Sequence
from typing import ClassVar

from pydantic import TypeAdapter, ValidationError

from flext_infra import CONTAINER_DICT_SEQ_ADAPTER, FlextInfraUtilitiesParsing, c, m, t


class FlextInfraUtilitiesRuleHelpers:
    """Static helpers extracted from rules/ — accessible via u.Infra.*."""

    DEF_CLASS_RE: ClassVar[re.Pattern[str]] = c.Infra.SourceCode.DEF_CLASS_RE
    IMPORT_FROM_RE: ClassVar[re.Pattern[str]] = c.Infra.SourceCode.FROM_IMPORT_RE
    IMPORT_RE: ClassVar[re.Pattern[str]] = c.Infra.SourceCode.IMPORT_RE
    ASSIGN_RE: ClassVar[re.Pattern[str]] = c.Infra.SourceCode.ASSIGN_RE
    FINAL_ASSIGN_RE: ClassVar[re.Pattern[str]] = c.Infra.SourceCode.FINAL_ASSIGN_RE

    _RULE_CONFIG_SEQ_ADAPTER: TypeAdapter[
        Sequence[m.Infra.ImportModernizerRuleConfig]
    ] = TypeAdapter(Sequence[m.Infra.ImportModernizerRuleConfig])

    # ── Import modernizer helpers ───────────────────────────────────

    @staticmethod
    def parse_import_names(names_str: str) -> Sequence[tuple[str, str]]:
        """Parse 'A, B as C, D' into [(name, bound), ...]."""
        result: MutableSequence[tuple[str, str]] = []
        for part in names_str.split(","):
            part = part.strip().rstrip("\\").strip()
            if not part or part.startswith(("(", ")")):
                continue
            if " as " in part:
                name, alias = part.split(" as ", 1)
                result.append((name.strip(), alias.strip()))
            else:
                result.append((part, part))
        return result

    @staticmethod
    def parse_param_names(params_str: str) -> t.Infra.StrSet:
        """Parse parameter names from a function signature string."""
        names: t.Infra.StrSet = set()
        for part in params_str.split(","):
            item = part.strip()
            if not item or item == "/":
                continue
            name = item.split(":")[0].split("=")[0].strip().lstrip("*")
            if name:
                names.add(name)
        return names

    @staticmethod
    def collect_from_import_bound_names(
        source: str,
        *,
        module_name: str,
    ) -> t.Infra.StrSet:
        """Collect bound names imported from a target module."""
        rh = FlextInfraUtilitiesRuleHelpers
        bound_names: t.Infra.StrSet = set()
        for match in c.Infra.SourceCode.FROM_IMPORT_RE.finditer(source):
            if match.group(1) != module_name:
                continue
            bound_names.update(
                bound for _name, bound in rh.parse_import_names(match.group(2))
            )
        for match in c.Infra.SourceCode.FROM_IMPORT_BLOCK_RE.finditer(source):
            if match.group(1) != module_name:
                continue
            bound_names.update(
                bound for _name, bound in rh.parse_import_names(match.group(2))
            )
        return bound_names

    @staticmethod
    def parse_forbidden_rules(
        value: t.Infra.InfraValue,
    ) -> Sequence[m.Infra.ImportModernizerRuleConfig]:
        """Parse and validate forbidden import rule configs."""
        try:
            raw_items: Sequence[t.Infra.ContainerDict] = (
                CONTAINER_DICT_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError:
            return []
        normalized: Sequence[t.Infra.ContainerDict] = [
            {
                "module": item.get("module", ""),
                "symbol_mapping": item.get("symbol_mapping", {}),
            }
            for item in raw_items
        ]
        try:
            return (
                FlextInfraUtilitiesRuleHelpers._RULE_CONFIG_SEQ_ADAPTER.validate_python(
                    normalized,
                )
            )
        except ValidationError:
            return []

    @staticmethod
    def collect_blocked_aliases(
        source: str,
        runtime_aliases: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        """Collect aliases blocked by definitions, non-core imports, and assignments."""
        rh = FlextInfraUtilitiesRuleHelpers
        blocked: t.Infra.StrSet = set()
        for match in rh.DEF_CLASS_RE.finditer(source):
            name = match.group(1)
            if name in runtime_aliases:
                blocked.add(name)
        for match in rh.IMPORT_FROM_RE.finditer(source):
            module = match.group(1)
            if module == c.Infra.Packages.CORE_UNDERSCORE:
                continue
            for _name, bound in rh.parse_import_names(match.group(2)):
                if bound in runtime_aliases:
                    blocked.add(bound)
        for match in rh.IMPORT_RE.finditer(source):
            for _name, bound in rh.parse_import_names(match.group(1)):
                if bound in runtime_aliases:
                    blocked.add(bound)
        for match in rh.ASSIGN_RE.finditer(source):
            name = match.group(1)
            if name in runtime_aliases:
                blocked.add(name)
        return blocked

    @staticmethod
    def collect_shadowed_aliases(
        source: str,
        runtime_aliases: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        """Collect runtime-alias names shadowed inside function bodies."""
        shadowed: t.Infra.StrSet = set()
        for match in c.Infra.SourceCode.FUNC_PARAM_RE.finditer(source):
            params = match.group(1)
            for param in params.split(","):
                param_name = param.strip().split(":")[0].split("=")[0].strip()
                if param_name.startswith("*"):
                    param_name = param_name.lstrip("*")
                if param_name in runtime_aliases:
                    shadowed.add(param_name)
        return shadowed

    # ── MRO class migration helpers ─────────────────────────────────

    @staticmethod
    def find_final_candidates(source: str) -> Sequence[m.Infra.MROSymbolCandidate]:
        """Find module-level Final-annotated constants via regex."""
        rh = FlextInfraUtilitiesRuleHelpers
        candidates: MutableSequence[m.Infra.MROSymbolCandidate] = []
        for i, line in enumerate(source.splitlines(), start=1):
            stripped = line.lstrip()
            if line != stripped and stripped:
                continue
            match = rh.FINAL_ASSIGN_RE.match(stripped)
            if match and rh.is_constant_candidate(match.group(1)):
                candidates.append(
                    m.Infra.MROSymbolCandidate(symbol=match.group(1), line=i),
                )
        return candidates

    @staticmethod
    def first_constants_class_name(source: str) -> str:
        """Find the first class ending with Constants suffix."""
        for match in c.Infra.SourceCode.CLASS_NAME_RE.finditer(source):
            name = match.group(1)
            if name.endswith(c.Infra.CONSTANTS_CLASS_SUFFIX):
                return name
        return ""

    # ── Future annotations helper ───────────────────────────────────

    @staticmethod
    def find_future_annotations_insert_index(lines: Sequence[str]) -> int:
        """Find insertion index after module docstring for future annotations."""
        return FlextInfraUtilitiesParsing.index_after_docstring_and_future_imports(
            lines
        )

    # ── Class reconstructor helper ──────────────────────────────────

    @staticmethod
    def apply_regex_renames(
        source: str,
        mappings: t.StrMapping,
    ) -> str:
        """Apply word-boundary regex renames to source text."""
        ns = source
        for old_name, new_name in mappings.items():
            ns, _ = re.compile(rf"\b{re.escape(old_name)}\b").subn(new_name, ns)
        return ns


__all__ = ["FlextInfraUtilitiesRuleHelpers"]
