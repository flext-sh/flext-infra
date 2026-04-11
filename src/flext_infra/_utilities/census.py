"""Census and introspection utilities for the refactor subpackage."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import BaseModel

from flext_infra import (
    c,
    m,
    t,
)


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
    ) -> m.Infra.MROFamilyTarget:
        """Create a generic target config from a family code."""
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
                    methods=tuple(m_list),
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
            classes=tuple(cls_sums),
            projects=tuple(
                m.Infra.CensusProjectSummary(
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
    def export_pydantic_json(model_payload: BaseModel, export_path: Path) -> None:
        """Serialize any Pydantic model payload to a JSON file."""
        export_path.write_text(
            model_payload.model_dump_json(indent=2),
            encoding=c.Infra.ENCODING_DEFAULT,
        )


__all__ = ["FlextInfraUtilitiesRefactorCensus"]
