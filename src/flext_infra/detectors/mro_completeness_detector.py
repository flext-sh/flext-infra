"""Detect facade classes missing MRO composition bases via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)

from flext_infra import c, m, u


class FlextInfraMROCompletenessDetector:
    """Detect facade classes missing MRO bases via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.MROCompletenessViolation]:
        """Detect missing MRO bases: expected - declared = violations."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        parse_failures = ctx.parse_failures
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return []
        res = u.Infra.fetch_python_resource(
            rope_project, file_path, skip_protected=True
        )
        if res is None:
            if parse_failures is not None:
                parse_failures.append(
                    m.Infra.ParseFailureViolation(
                        file=str(file_path),
                        stage="mro-completeness",
                        error_type="ResourceNotFound",
                        detail=f"Cannot resolve {file_path.name}",
                    )
                )
            return []
        # Resolve facade class from declared module classes.
        module_classes = tuple(u.Infra.get_module_classes(rope_project, res))
        facade = None
        suffix = c.Infra.FAMILY_SUFFIXES.get(family, "")
        if suffix:
            facade = next(
                (name for name in module_classes if name.endswith(suffix)),
                None,
            )
        if facade is None:
            facade = next(
                (name for name in module_classes if name.startswith("Flext")),
                None,
            )
        if facade is None:
            return []
        # Expected: local family classes + dep-graph parents
        # get_class_info returns ClassInfo(name, line, bases) — reuse for declared bases
        expected: dict[str, int] = {}
        declared: set[str] = set()
        scan_paths = [file_path]
        dn = c.Infra.FAMILY_DIRECTORIES.get(family, "")
        if dn:
            d = file_path.parent / dn
            if d.is_dir():
                scan_paths.extend(sorted(d.glob(c.Infra.EXT_PYTHON_GLOB)))
            f = file_path.parent / f"{dn}.py"
            if f.is_file():
                scan_paths.append(f)
        for path in scan_paths:
            r = u.Infra.get_resource_from_path(rope_project, path)
            if r is None:
                continue
            for ci in u.Infra.get_class_info(rope_project, r):
                if ci.name == facade:
                    declared = set(ci.bases)
                elif not ci.name.startswith("_") and ci.name.startswith(facade):
                    expected[ci.name] = ci.line
        declared.update(u.Infra.parse_class_bases(res.read(), facade))
        root = u.Infra.resolve_project_root(file_path)
        if root is not None:
            for base in u.Infra.build_expected_base_chains(project_root=root).get(
                family, []
            ):
                expected.setdefault(base, 1)
        return [
            m.Infra.MROCompletenessViolation(
                file=str(file_path),
                line=line,
                family=family,
                facade_class=facade,
                missing_base=name,
                suggestion=f"Add '{name}' to '{facade}' bases",
            )
            for name, line in sorted(expected.items())
            if name not in declared
        ]


__all__: list[str] = ["FlextInfraMROCompletenessDetector"]
