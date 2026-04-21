"""Scan projects for namespace facade class presence and status via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)
from pathlib import Path

from flext_infra import (
    c,
    m,
    t,
    u,
)


class FlextInfraScanner:
    """Scan projects for namespace facade classes via rope."""

    @classmethod
    def scan_project(
        cls,
        *,
        project_root: Path,
        project_name: str,
        rope_project: t.Infra.RopeProject,
        parse_failures: Sequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.FacadeStatus]:
        """Return FacadeStatus for each family (c, t, p, m, u) in a project."""
        del parse_failures
        del project_name

        layout = u.Infra.layout(project_root)
        if layout is None or not layout.src_dir.is_dir():
            return [
                m.Infra.FacadeStatus(
                    family=family,
                    exists=False,
                    class_name="",
                    file="",
                    symbol_count=0,
                )
                for family in c.Infra.FAMILY_SUFFIXES
            ]
        stem = layout.class_stem
        src_dir = layout.src_dir
        results: list[m.Infra.FacadeStatus] = []
        for family, suffix in c.Infra.FAMILY_SUFFIXES.items():
            expected = f"{stem}{suffix}"
            pattern = c.Infra.FAMILY_FILES[family]
            found_class, found_file, symbols = "", "", 0
            for file_path in src_dir.rglob(pattern):
                res = u.Infra.get_resource_from_path(
                    rope_project,
                    file_path,
                )
                if res is None:
                    continue
                classes = u.Infra.get_module_classes(rope_project, res)
                match = next(
                    (n for n in classes if n == expected or n.endswith(suffix)),
                    None,
                )
                if match is not None:
                    found_class = match
                    found_file = str(file_path)
                    symbols = u.Infra.get_class_symbol_count(
                        rope_project,
                        res,
                        match,
                    )
                    break
            results.append(
                m.Infra.FacadeStatus(
                    family=family,
                    exists=bool(found_class),
                    class_name=found_class,
                    file=found_file,
                    symbol_count=symbols,
                )
            )
        return results
