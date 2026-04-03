"""MRO migration scanner utilities for the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from pathlib import Path

from rope.base.pyobjects import AbstractClass

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRope,
    c,
    m,
    t,
)

logger = logging.getLogger(__name__)


class FlextInfraUtilitiesRefactorMroScan:
    _MRO_SCAN_CONSTANT_PATTERN: re.Pattern[str] = c.Infra.SourceCode.CONSTANT_NAME_RE
    _MRO_SCAN_TYPE_PATTERN: re.Pattern[str] = re.compile(r"^_?[A-Za-z][A-Za-z0-9_]*$")

    @staticmethod
    def scan_workspace(
        *,
        workspace_root: Path,
        target: str,
    ) -> t.Infra.Pair[Sequence[m.Infra.MROScanReport], int]:
        """Scan workspace and collect migration reports for a target family."""
        if target not in c.Infra.MRO_TARGETS:
            empty_list: list[m.Infra.MROScanReport] = []
            return (empty_list, 0)

        results: list[m.Infra.MROScanReport] = []
        scanned = 0
        target_specs = FlextInfraUtilitiesRefactorMroScan._target_specs(target=target)
        for project_root in FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=workspace_root
        ):
            for target_spec in target_specs:
                for file_path in FlextInfraUtilitiesRefactorMroScan._iter_target_files(
                    project_root=project_root, target_spec=target_spec
                ):
                    scanned += 1
                    rope_proj = FlextInfraUtilitiesRope.init_rope_project(project_root)
                    try:
                        res = FlextInfraUtilitiesRope.get_resource_from_path(
                            rope_proj, file_path
                        )
                        if res:
                            report = FlextInfraUtilitiesRefactorMroScan.scan_file(
                                resource=res,
                                project_root=project_root,
                                target_spec=target_spec,
                            )
                            if report and report.candidates:
                                results.append(report)
                    finally:
                        rope_proj.close()
        return (results, scanned)

    @staticmethod
    def scan_file(
        *,
        resource: t.Infra.RopeResource,
        project_root: Path,
        target_spec: m.Infra.MROTargetSpec,
    ) -> m.Infra.MROScanReport | None:
        """Scan one file using rope and return migration candidates."""
        source = resource.read()
        facade = FlextInfraUtilitiesRefactorMroScan._find_facade(source, target_spec)
        if not facade:
            return None

        rel = Path(resource.path)
        module = ".".join([
            p for p in rel.with_suffix("").parts if p != c.Infra.Paths.DEFAULT_SRC_DIR
        ])

        candidates: list[m.Infra.MROSymbolCandidate] = []
        rope_proj = FlextInfraUtilitiesRope.init_rope_project(project_root)
        try:
            pycore = FlextInfraUtilitiesRope.get_pycore(rope_proj)
            pymodule = pycore.resource_to_pyobject(resource)
            lines = source.splitlines()

            for name, pyname in pymodule.get_attributes().items():
                loc = pyname.get_definition_location()
                if (
                    loc[0] is None
                    or loc[0].get_resource() != resource
                    or loc[1] is None
                ):
                    continue

                line = loc[1]
                if line < 1 or line > len(lines):
                    continue

                obj = pyname.get_object()
                src_line = lines[line - 1].strip()

                cand = FlextInfraUtilitiesRefactorMroScan._create_candidate(
                    name=name,
                    line=line,
                    src_line=src_line,
                    target_spec=target_spec,
                    obj=obj,
                )
                if cand:
                    candidates.append(cand)
        except Exception as exc:
            logger.info("MRO scan skipped for %s: %s", resource.real_path, exc)
        finally:
            rope_proj.close()

        return m.Infra.MROScanReport(
            file=resource.real_path,
            module=module,
            constants_class=facade,
            facade_alias=target_spec.family_alias,
            candidates=tuple(sorted(candidates, key=lambda c: c.line)),
        )

    @staticmethod
    def _create_candidate(
        *,
        name: str,
        line: int,
        src_line: str,
        target_spec: m.Infra.MROTargetSpec,
        obj: object,
    ) -> m.Infra.MROSymbolCandidate | None:
        alias = target_spec.family_alias
        kind = ""

        if alias == "t":
            if not FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_TYPE_PATTERN.match(
                name
            ):
                return None
            if "TypeAlias" in src_line or src_line.startswith(f"type {name}"):
                kind = "typealias"
            elif any(x in src_line for x in ("TypeVar", "ParamSpec", "NewType")):
                kind = "typevar"
        elif alias == "p":
            if isinstance(obj, AbstractClass):
                try:
                    get_bases = getattr(obj, "get_bases", None)
                    raw_bases = get_bases() if callable(get_bases) else list[object]()
                    bases: Sequence[AbstractClass] = (
                        [b for b in raw_bases if isinstance(b, AbstractClass)]
                        if isinstance(raw_bases, Sequence)
                        else []
                    )
                    if any("Protocol" in str(b.get_name()) for b in bases):
                        kind = "protocol"
                except Exception as exc:
                    logger.info("Protocol base scan skipped for %s: %s", name, exc)
        elif FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_CONSTANT_PATTERN.match(name):
            if re.match(rf"^{name}\s*(:|==?)\s*", src_line) and not name.islower():
                kind = "constant"

        if not kind:
            return None

        return m.Infra.MROSymbolCandidate(
            symbol=name, line=line, kind=kind, class_name="", facade_name=""
        )

    @staticmethod
    def _find_facade(source: str, spec: m.Infra.MROTargetSpec) -> str:
        assign = re.search(
            rf"^{re.escape(spec.family_alias)}\s*=\s*([A-Za-z_]\w*{spec.class_suffix})\b",
            source,
            re.MULTILINE,
        )
        if assign:
            return assign.group(1)
        cls = re.search(
            rf"^class\s+([A-Za-z_]\w*{spec.class_suffix})\b", source, re.MULTILINE
        )
        return cls.group(1) if cls else ""

    @staticmethod
    def _target_specs(target: str) -> t.Infra.VariadicTuple[m.Infra.MROTargetSpec]:
        all_specs = (
            m.Infra.MROTargetSpec(
                family_alias="c",
                file_names=c.Infra.MRO_CONSTANTS_FILE_NAMES,
                package_directory=c.Infra.MRO_CONSTANTS_DIRECTORY,
                class_suffix=c.Infra.CONSTANTS_CLASS_SUFFIX,
            ),
            m.Infra.MROTargetSpec(
                family_alias="t",
                file_names=c.Infra.MRO_TYPINGS_FILE_NAMES,
                package_directory=c.Infra.MRO_TYPINGS_DIRECTORY,
                class_suffix="Types",
            ),
            m.Infra.MROTargetSpec(
                family_alias="p",
                file_names=c.Infra.MRO_PROTOCOLS_FILE_NAMES,
                package_directory=c.Infra.MRO_PROTOCOLS_DIRECTORY,
                class_suffix="Protocols",
            ),
            m.Infra.MROTargetSpec(
                family_alias="m",
                file_names=c.Infra.MRO_MODELS_FILE_NAMES,
                package_directory=c.Infra.MRO_MODELS_DIRECTORY,
                class_suffix="Models",
            ),
            m.Infra.MROTargetSpec(
                family_alias="u",
                file_names=c.Infra.MRO_UTILITIES_FILE_NAMES,
                package_directory=c.Infra.MRO_UTILITIES_DIRECTORY,
                class_suffix="Utilities",
            ),
        )
        mapping = {
            "constants": "c",
            "typings": "t",
            "protocols": "p",
            "models": "m",
            "utilities": "u",
        }
        al = mapping.get(target)
        return tuple(s for s in all_specs if s.family_alias == al) if al else all_specs

    @staticmethod
    def _iter_target_files(
        *, project_root: Path, target_spec: m.Infra.MROTargetSpec
    ) -> Sequence[Path]:
        cands: set[Path] = set()
        for dn in c.Infra.MRO_SCAN_DIRECTORIES:
            root = project_root / dn
            if not root.is_dir():
                continue
            for p in FlextInfraUtilitiesIteration.iter_directory_python_files(root):
                if (
                    p.name in target_spec.file_names
                    or target_spec.package_directory in p.parts
                ):
                    cands.add(p)
        return sorted(cands)


__all__ = ["FlextInfraUtilitiesRefactorMroScan"]
