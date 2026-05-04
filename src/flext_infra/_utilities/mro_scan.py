"""MRO migration scanner utilities for the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRopeCore,
    c,
    m,
    t,
    u,
)


class FlextInfraUtilitiesRefactorMroScan:
    """Flext infra utilities refactor mro scan."""

    _MRO_SCAN_CONSTANT_PATTERN: t.Infra.RegexPattern = c.Infra.CONSTANT_NAME_RE
    _MRO_SCAN_TYPE_PATTERN: t.Infra.RegexPattern = c.Infra.MRO_SCAN_TYPE_PATTERN
    _MRO_SCAN_PROTOCOL_BASE_PATTERN: t.Infra.RegexPattern = (
        c.Infra.MRO_SCAN_PROTOCOL_BASE_PATTERN
    )
    _ALL_SPECS: ClassVar[tuple[m.Infra.MROTargetSpec, ...]] = (
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
    _TARGET_MAP: ClassVar[tuple[tuple[str, str], ...]] = (
        ("constants", "c"),
        ("typings", "t"),
        ("protocols", "p"),
        ("models", "m"),
        ("utilities", "u"),
    )

    @staticmethod
    def scan_workspace(
        *,
        workspace_root: Path,
        target: str,
        project_names: t.StrSequence | None = None,
    ) -> tuple[t.SequenceOf[m.Infra.MROScanReport], int]:
        """Scan workspace and collect migration reports for a target family."""
        if target not in c.Infra.MRO_TARGETS:
            empty_list: list[m.Infra.MROScanReport] = []
            return (empty_list, 0)

        results: list[m.Infra.MROScanReport] = []
        scanned = 0
        target_specs = FlextInfraUtilitiesRefactorMroScan._target_specs(target)
        project_name_set: set[str] = set(project_names or ())
        for project_root in FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=workspace_root,
        ):
            if project_name_set and project_root.name not in project_name_set:
                continue
            scan_dirs = FlextInfraUtilitiesIteration.namespace_scan_dirs(project_root)
            iter_result = FlextInfraUtilitiesIteration.iter_python_files(
                workspace_root=project_root,
                project_roots=[project_root],
                include_tests=c.Infra.DIR_TESTS in scan_dirs,
                include_examples=c.Infra.DIR_EXAMPLES in scan_dirs,
                include_scripts=c.Infra.DIR_SCRIPTS in scan_dirs,
                src_dirs=scan_dirs or None,
            )
            if iter_result.failure:
                continue
            with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_proj:
                for target_spec in target_specs:
                    for file_path in iter_result.value:
                        if (
                            file_path.name not in target_spec.file_names
                            and target_spec.package_directory not in file_path.parts
                        ):
                            continue
                        scanned += 1
                        res = FlextInfraUtilitiesRopeCore.get_resource_from_path(
                            rope_proj,
                            file_path,
                        )
                        if res:
                            report = FlextInfraUtilitiesRefactorMroScan.scan_file(
                                rope_project=rope_proj,
                                resource=res,
                                target_spec=target_spec,
                            )
                            if report and report.candidates:
                                results.append(report)
        return (results, scanned)

    @staticmethod
    def scan_file(
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        target_spec: m.Infra.MROTargetSpec,
    ) -> m.Infra.MROScanReport | None:
        """Scan one file using rope and return migration candidates."""
        source = resource.read()
        facade = FlextInfraUtilitiesRefactorMroScan._find_facade(source, target_spec)
        if not facade:
            return None

        rel = Path(resource.path)
        module = ".".join([
            p for p in rel.with_suffix("").parts if p != c.Infra.DEFAULT_SRC_DIR
        ])

        candidates: list[m.Infra.MROSymbolCandidate] = []
        try:
            pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(rope_project, resource)
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
                class_header = FlextInfraUtilitiesRefactorMroScan._class_header(
                    lines=lines,
                    start_line=line,
                )
                block_start, block_end = (
                    FlextInfraUtilitiesRefactorMroScan._top_level_block_bounds(
                        lines=lines,
                        start_line=line,
                    )
                    if src_line.startswith("class ")
                    else (line, line)
                )

                cand = FlextInfraUtilitiesRefactorMroScan._create_candidate(
                    name=name,
                    block=(block_start, block_end),
                    src_line=src_line,
                    class_header=class_header,
                    target_spec=target_spec,
                    obj=obj,
                )
                if cand:
                    candidates.append(cand)
        except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS as exc:
            u.fetch_logger(__name__).info(
                "MRO scan skipped for %s: %s",
                resource.real_path,
                str(exc),
            )

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
        block: tuple[int, int],
        src_line: str,
        class_header: str,
        target_spec: m.Infra.MROTargetSpec,
        obj: t.Infra.RopePyObject,
    ) -> m.Infra.MROSymbolCandidate | None:
        """Create candidate."""
        line, end_line = block
        alias = target_spec.family_alias
        kind = ""

        match alias:
            case "t":
                if not FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_TYPE_PATTERN.match(
                    name
                ):
                    return None
                if "TypeAlias" in src_line or src_line.startswith(f"type {name}"):
                    kind = "typealias"
                elif any(x in src_line for x in ("TypeVar", "ParamSpec", "NewType")):
                    kind = "typevar"
            case "p":
                if FlextInfraUtilitiesRefactorMroScan._mro_scan_is_protocol_class(
                    name=name,
                    obj=obj,
                    class_header=class_header,
                ):
                    kind = "protocol"
            case _:
                if (
                    FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_CONSTANT_PATTERN.match(
                        name
                    )
                    and c.Infra.compile_assign_or_annotation_start(name).match(
                        src_line,
                    )
                    and not name.islower()
                ):
                    kind = "constant"

        if not kind:
            return None

        return m.Infra.MROSymbolCandidate(
            symbol=name,
            line=line,
            end_line=(end_line if end_line > line else None),
            kind=kind,
        )

    @staticmethod
    def _find_facade(
        source: str,
        spec: m.Infra.MROTargetSpec,
    ) -> str:
        """Find facade."""
        if assign := c.Infra.compile_facade_alias_assignment(
            spec.family_alias,
            spec.class_suffix,
        ).search(source):
            facade_name: str = assign.group(1)
            return facade_name
        return (
            str(m.group(1))
            if (
                m := c.Infra.compile_class_with_suffix(spec.class_suffix).search(
                    source,
                )
            )
            else ""
        )

    @staticmethod
    def _target_specs(target: str) -> tuple[m.Infra.MROTargetSpec, ...]:
        """Target specs."""
        al = dict(FlextInfraUtilitiesRefactorMroScan._TARGET_MAP).get(target)
        return (
            tuple(
                s
                for s in FlextInfraUtilitiesRefactorMroScan._ALL_SPECS
                if s.family_alias == al
            )
            if al
            else FlextInfraUtilitiesRefactorMroScan._ALL_SPECS
        )

    @staticmethod
    def _class_header(*, lines: t.StrSequence, start_line: int) -> str:
        """Class header."""
        header_parts: list[str] = []
        for current_line in lines[start_line - 1 :]:
            stripped = current_line.strip()
            if not stripped:
                if header_parts:
                    break
                continue
            header_parts.append(stripped)
            if ":" in stripped:
                break
        return " ".join(header_parts)

    @staticmethod
    def _top_level_block_bounds(
        *,
        lines: t.StrSequence,
        start_line: int,
    ) -> tuple[int, int]:
        """Top level block bounds."""
        class_line_index = start_line - 1
        start_index = class_line_index
        while start_index > 0:
            previous_line = lines[start_index - 1]
            if previous_line.startswith("@"):
                start_index -= 1
                continue
            break

        base_indent = len(lines[class_line_index]) - len(
            lines[class_line_index].lstrip()
        )
        end_index = class_line_index
        for current_index in range(class_line_index + 1, len(lines)):
            current_line = lines[current_index]
            stripped = current_line.strip()
            if not stripped:
                end_index = current_index
                continue
            if len(current_line) - len(current_line.lstrip()) <= base_indent:
                break
            end_index = current_index
        return (start_index + 1, end_index + 1)

    @classmethod
    def _mro_scan_is_protocol_class(
        cls,
        *,
        name: str,
        obj: t.Infra.RopePyObject,
        class_header: str,
    ) -> bool:
        """Mro scan is protocol class."""
        if isinstance(obj, FlextInfraUtilitiesRopeCore.ABSTRACT_CLASS_TYPES):
            try:
                bases = tuple(obj.get_superclasses())
                if any("Protocol" in str(b.get_name()) for b in bases):
                    return True
            except FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS as exc:
                u.fetch_logger(__name__).info(
                    "Protocol base scan skipped for %s: %s",
                    name,
                    str(exc),
                )
        return cls._class_header_declares_protocol(
            name=name,
            class_header=class_header,
        )

    @classmethod
    def _class_header_declares_protocol(cls, *, name: str, class_header: str) -> bool:
        """Class header declares protocol."""
        if (
            m := c.Infra.compile_class_header_with_bases(name).match(class_header)
        ) is None:
            return False
        return bool(cls._MRO_SCAN_PROTOCOL_BASE_PATTERN.search(m.group("bases")))


__all__: list[str] = ["FlextInfraUtilitiesRefactorMroScan"]
