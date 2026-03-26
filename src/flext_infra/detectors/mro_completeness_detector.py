"""Detect facade classes missing MRO composition bases via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import FlextInfraScanFileMixin, c, m, p, t, u


class FlextInfraMROCompletenessDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect facade classes missing MRO bases via rope."""

    _rule_id: ClassVar[str] = "namespace.mro_completeness"

    @override
    def _build_message(self, violation: BaseModel) -> str:
        d = violation.model_dump()
        return f"Facade '{d['facade_class']}' missing base '{d['missing_base']}' for family '{d['family']}'"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        return self.detect_file(
            file_path=file_path, rope_project=self._rope, parse_failures=self._pf
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.MROCompletenessViolation]:
        """Detect missing MRO bases: expected - declared = violations."""
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            if parse_failures is not None:
                parse_failures.append(
                    m.Infra.ParseFailureViolation.create(
                        file=str(file_path),
                        stage="mro-completeness",
                        error_type="ResourceNotFound",
                        detail=f"Cannot resolve {file_path.name}",
                    )
                )
            return []
        # Resolve facade class
        facade = u.Infra.find_facade_alias(res, family)
        if facade is None:
            suffix = c.Infra.FAMILY_SUFFIXES.get(family, "")
            if suffix:
                facade = next(
                    (
                        n
                        for n in u.Infra.get_module_classes(rope_project, res)
                        if n.endswith(suffix)
                    ),
                    None,
                )
        if facade is None:
            return []
        # Expected: local family classes + dep-graph parents
        # get_class_info returns ClassInfo(name, line, bases) — reuse for declared bases
        expected: dict[str, int] = {}
        declared: set[str] = set()
        scan_paths: list[Path] = [file_path]
        dn = c.Infra.FAMILY_DIRECTORIES.get(family, "")
        if dn:
            d = file_path.parent / dn
            if d.is_dir():
                scan_paths.extend(sorted(d.glob("*.py")))
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
        root = u.Infra.resolve_project_root(file_path)
        if root is not None:
            for base in u.Infra.build_expected_base_chains(project_root=root).get(
                family, []
            ):
                expected.setdefault(base, 1)
        return [
            m.Infra.MROCompletenessViolation.create(
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


__all__ = ["FlextInfraMROCompletenessDetector"]
