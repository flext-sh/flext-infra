"""Census and introspection utilities for the refactor subpackage."""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from collections.abc import (
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path

from flext_infra import FlextInfraModelsRefactorCensus as mrc, c, m, p, t
from flext_infra._utilities.parsing import FlextInfraUtilitiesParsing


class FlextInfraUtilitiesRefactorCensus:
    """Census and source introspection helpers for refactor tools."""

    @staticmethod
    def build_facade_alias_map(
        facade_path: Path,
        facade_class_name: str,
    ) -> Mapping[str, t.Infra.StrPair]:
        """Parse a facade class to build flat alias -> (class, method) map."""
        if not facade_path.exists():
            return {}
        alias_map: MutableMapping[str, t.Infra.StrPair] = {}
        lines = facade_path.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()
        in_target = False
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith(f"class {facade_class_name}"):
                in_target = True
                continue
            if in_target and "staticmethod" in trimmed and "=" in trimmed:
                parts = trimmed.split("=", 1)
                alias = parts[0].strip()
                rhs = parts[1].strip()
                if rhs.startswith("staticmethod(") and rhs.endswith(")"):
                    target = rhs[13:-1].strip()
                    if "." in target:
                        cls_name, method_name = target.rsplit(".", 1)
                        alias_map[alias] = (cls_name, method_name)
        return alias_map

    @staticmethod
    def build_facade_inner_class_map(
        facade_path: Path,
        facade_class_name: str,
    ) -> t.StrMapping:
        """Map inner class names -> base class names in a facade."""
        if not facade_path.exists():
            return {}
        name_map: t.MutableStrMapping = {}
        lines = facade_path.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()
        in_target = False
        for line in lines:
            trimmed = line.strip()
            if trimmed.startswith(f"class {facade_class_name}"):
                in_target = True
                continue
            if in_target and trimmed.startswith("class "):
                parts = trimmed.split("class ", 1)[1].split(":", 1)[0].strip()
                if "(" in parts and parts.endswith(")"):
                    inner_name = parts.split("(", 1)[0].strip()
                    base_name = parts.split("(", 1)[1][:-1].strip()
                    if "," in base_name:
                        base_name = base_name.split(",")[0].strip()
                    name_map[inner_name] = base_name
        return name_map

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
            return c.Infra.DEFAULT_UNKNOWN
        best = max(matching_roots, key=lambda root: len(root.parts))
        return best.name

    @staticmethod
    def build_mro_target(
        family: str,
        core_project: str = c.Infra.PKG_CORE,
    ) -> mrc.MROFamilyTarget:
        """Create a generic target settings from a family code."""
        if family not in c.Infra.MRO_FAMILIES:
            msg = f"Invalid MRO family {family}"
            raise ValueError(msg)
        sf = c.Infra.FAMILY_SUFFIXES[family]
        return mrc.MROFamilyTarget(
            family=family,
            class_suffix=sf,
            package_dir=c.Infra.MRO_FAMILY_PACKAGE_DIRS[family],
            facade_module=c.Infra.MRO_FAMILY_FACADE_MODULES[family],
            facade_class_prefix=f"Flext{sf}",
            core_project=core_project,
        )

    @staticmethod
    def aggregate_usage_metrics(
        methods: Mapping[str, Sequence[mrc.CensusMethodInfo]],
        records: Sequence[mrc.CensusUsageRecord],
        files_scanned: int,
        parse_errors: int,
    ) -> mrc.UtilitiesCensusReport:
        """Pivot raw AST method visit occurrences into a structured usage report."""
        cnt: Counter[t.Infra.Triple[str, str, str]] = Counter()
        pcnt: Counter[t.Infra.Quad[str, str, str, str]] = Counter()

        for rec in records:
            cnt[rec.class_name, rec.method_name, rec.access_mode] += 1
            pcnt[rec.project, rec.class_name, rec.method_name, rec.access_mode] += 1

        cls_sums: MutableSequence[mrc.CensusClassSummary] = []
        unused = 0
        for cls, items in sorted(methods.items()):
            m_list: MutableSequence[mrc.CensusMethodSummary] = []
            for m_info in items:
                af = cnt.get(
                    (cls, m_info.name, c.Infra.CensusMode.ALIAS_FLAT),
                    0,
                )
                an = cnt.get(
                    (cls, m_info.name, c.Infra.CensusMode.ALIAS_NS),
                    0,
                )
                dr = cnt.get((cls, m_info.name, c.Infra.CensusMode.DIRECT), 0)
                tot = af + an + dr
                if tot == 0:
                    unused += 1
                m_list.append(
                    mrc.CensusMethodSummary(
                        name=m_info.name,
                        method_type=m_info.method_type,
                        alias_flat=af,
                        alias_namespaced=an,
                        direct=dr,
                        total=tot,
                    ),
                )
            cls_sums.append(
                mrc.CensusClassSummary(
                    class_name=cls,
                    source_file=items[0].source_file if items else "",
                    methods=tuple(m_list),
                ),
            )

        pj_sums: MutableMapping[
            str,
            MutableSequence[mrc.CensusProjectMethodUsage],
        ] = defaultdict(list)
        for (pj, cls, mx, mo), co in sorted(pcnt.items()):
            pj_sums[pj].append(
                mrc.CensusProjectMethodUsage(
                    class_name=cls,
                    method_name=mx,
                    access_mode=mo,
                    count=co,
                ),
            )

        return mrc.UtilitiesCensusReport(
            classes=tuple(cls_sums),
            projects=tuple(
                mrc.CensusProjectSummary(
                    project_name=p,
                    usages=tuple(us),
                    total=sum(u.count for u in us),
                )
                for p, us in sorted(pj_sums.items())
            ),
            total_classes=len(methods),
            total_methods=sum(len(v) for v in methods.values()),
            total_usages=len(records),
            total_unused=unused,
            files_scanned=files_scanned,
            parse_errors=parse_errors,
        )

    @staticmethod
    def export_pydantic_json(model_payload: m.BaseModel, export_path: Path) -> None:
        """Serialize any Pydantic model payload to a JSON file."""
        export_path.write_text(
            model_payload.model_dump_json(indent=2),
            encoding=c.Infra.ENCODING_DEFAULT,
        )

    @staticmethod
    def plan_simple_removal_edits(
        rope: p.Infra.RopeWorkspaceDsl,
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> Mapping[Path, tuple[t.Infra.IntPair, ...]] | None:
        """Plan safe line-range removals for simple top-level removal candidates."""
        if candidate.scope_path != candidate.object_name:
            return None
        if candidate.object_kind not in {"class", "function"}:
            return None
        definition_path = Path(candidate.file_path).resolve()
        definition_range = FlextInfraUtilitiesRefactorCensus._definition_line_range(
            rope.source(definition_path),
            candidate,
        )
        if definition_range is None:
            return None
        ranges_by_file: dict[Path, list[t.Infra.IntPair]] = defaultdict(list)
        ranges_by_file[definition_path].append(definition_range)
        for site in FlextInfraUtilitiesRefactorCensus._supporting_reference_sites(
            candidate
        ):
            site_path = Path(site.file_path).resolve()
            site_range = FlextInfraUtilitiesRefactorCensus._reference_line_range(
                rope.source(site_path),
                site,
            )
            if site_range is None:
                return None
            ranges_by_file[site_path].append(site_range)
        return {
            file_path: FlextInfraUtilitiesRefactorCensus.merge_line_ranges(ranges)
            for file_path, ranges in ranges_by_file.items()
        }

    @staticmethod
    def apply_line_ranges(
        source: str,
        ranges: Sequence[t.Infra.IntPair],
    ) -> str:
        """Remove one or more 1-based inclusive line ranges from Python source."""
        merged_ranges = FlextInfraUtilitiesRefactorCensus.merge_line_ranges(ranges)
        if not merged_ranges:
            return source
        removed_lines = {
            line_number
            for start, end in merged_ranges
            for line_number in range(start, end + 1)
        }
        lines = source.splitlines(keepends=True)
        return "".join(
            line
            for index, line in enumerate(lines, start=1)
            if index not in removed_lines
        )

    @staticmethod
    def merge_line_ranges(
        ranges: Sequence[t.Infra.IntPair],
    ) -> tuple[t.Infra.IntPair, ...]:
        """Merge overlapping or adjacent 1-based inclusive line ranges."""
        if not ranges:
            return ()
        ordered_ranges = sorted(ranges)
        merged: list[t.Infra.IntPair] = [ordered_ranges[0]]
        for start, end in ordered_ranges[1:]:
            previous_start, previous_end = merged[-1]
            if start <= previous_end + 1:
                merged[-1] = (previous_start, max(previous_end, end))
                continue
            merged.append((start, end))
        return tuple(merged)

    @staticmethod
    def _supporting_reference_sites(
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> tuple[m.Infra.Census.ReferenceSite, ...]:
        return (
            *candidate.test_reference_sites,
            *candidate.example_reference_sites,
            *candidate.script_reference_sites,
        )

    @staticmethod
    def _definition_line_range(
        source: str,
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> t.Infra.IntPair | None:
        module = FlextInfraUtilitiesParsing.parse_source_ast(source)
        if module is None:
            return None
        for node in module.body:
            if candidate.object_kind == "class" and isinstance(node, ast.ClassDef):
                if node.name == candidate.object_name:
                    return FlextInfraUtilitiesRefactorCensus._statement_line_range(node)
                continue
            if (
                candidate.object_kind == "function"
                and isinstance(
                    node,
                    ast.FunctionDef | ast.AsyncFunctionDef,
                )
                and node.name == candidate.object_name
            ):
                return FlextInfraUtilitiesRefactorCensus._statement_line_range(node)
        return None

    @staticmethod
    def _reference_line_range(
        source: str,
        site: m.Infra.Census.ReferenceSite,
    ) -> t.Infra.IntPair | None:
        module = FlextInfraUtilitiesParsing.parse_source_ast(source)
        if module is None:
            return None
        for node in module.body:
            start, end = FlextInfraUtilitiesRefactorCensus._statement_line_range(node)
            if not start <= site.line <= end:
                continue
            if isinstance(node, ast.ClassDef):
                return None
            return start, end
        return None

    @staticmethod
    def _statement_line_range(node: t.Infra.AstStmt) -> t.Infra.IntPair:
        start = getattr(node, "lineno", 1)
        decorators = getattr(node, "decorator_list", ())
        if decorators:
            start = min(getattr(decorator, "lineno", start) for decorator in decorators)
        end = getattr(node, "end_lineno", start) or start
        return start, end


__all__: list[str] = ["FlextInfraUtilitiesRefactorCensus"]
