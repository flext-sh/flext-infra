"""Detect missing or duplicate runtime alias assignments via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraScanFileMixin, c, m, p, t


class FlextInfraRuntimeAliasDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect missing/duplicate runtime aliases (e.g. m = FlextFooModels) via rope."""

    _rule_id: ClassVar[str] = "namespace.runtime_alias"
    _MESSAGE_TEMPLATE: ClassVar[str] = "Runtime alias '{alias}' {kind}: {detail}"

    def __init__(
        self,
        *,
        project_name: str,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize with project name and mandatory rope project."""
        super().__init__(rope_project=rope_project, parse_failures=parse_failures)
        self._project_name = project_name

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[m.Infra.RuntimeAliasViolation]:
        return self.detect_file(
            file_path=file_path,
            project_name=self._project_name,
            rope_project=self._rope,
            parse_failures=self._pf,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        project_name: str,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.RuntimeAliasViolation]:
        """Detect missing/duplicate runtime alias assignments in a facade file."""
        del parse_failures, project_name
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        source = cls._get_source_or_empty(rope_project, file_path)
        if source is None:
            return []
        matches = [
            hit.group(2)
            for hit in c.Infra.FACADE_ALIAS_RE.finditer(source)
            if hit.group(1) == family
        ]
        if not matches:
            return [
                m.Infra.RuntimeAliasViolation.create(
                    file=str(file_path),
                    kind="missing",
                    alias=family,
                    detail=f"No '{family} = ...' assignment found",
                )
            ]
        if len(matches) > 1:
            return [
                m.Infra.RuntimeAliasViolation.create(
                    file=str(file_path),
                    kind="duplicate",
                    alias=family,
                    detail=f"Found {len(matches)} '{family} = ...' assignments",
                )
            ]
        return []


__all__ = ["FlextInfraRuntimeAliasDetector"]
