"""Auto-generate standardized ``[tool.flext.*]`` tables in each project's pyproject.toml.

Uses ``tomlkit`` round-trip parsing to preserve existing formatting, comments,
and ordering.  Managed keys are defined in ``c.MANAGED_PYPROJECT_KEYS``.
Project discovery uses ``u.Infra.discover_projects`` — the canonical
workspace member list.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

import tomlkit

from flext_infra import c, p, r, t, u
from flext_infra.base import FlextInfraServiceBase


class FlextInfraCodegenPyprojectKeys(FlextInfraServiceBase[bool]):
    """Ensure every workspace project has standardized ``[tool.flext.*]`` tables.

    Reads each ``pyproject.toml`` via ``tomlkit`` (round-trip preserving),
    inserts or updates ``[tool.flext.project]``, ``[tool.flext.namespace]``,
    ``[tool.flext.docs]``, ``[tool.flext.aliases]`` sections with SSOT defaults,
    and writes back only if the content changed.
    """

    @override
    def execute(self) -> p.Result[bool]:
        """Generate [tool.flext.*] tables for each discovered project."""
        discovered = u.Infra.discover_projects(self.workspace_root)
        if not discovered.success:
            return r[bool].fail("pyproject-keys: project discovery failed")

        generated = 0

        for project_info in discovered.value:
            if self.project_filter and project_info.name != self.project_filter:
                continue

            pyproject_path = project_info.path / c.Infra.PYPROJECT_FILENAME
            original_text = pyproject_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            doc = tomlkit.parse(original_text)

            tool_flext_config = u.read_tool_flext_config(project_info.path)
            dumped = tool_flext_config.model_dump(exclude_none=True)

            tool: t.Infra.TomlTable = doc.setdefault(
                "tool", tomlkit.table(is_super_table=True)
            )
            flext: t.Infra.TomlTable = tool.setdefault(
                "flext", tomlkit.table(is_super_table=True)
            )

            for section_key in ("project", "namespace", "docs", "aliases"):
                section_data = dumped.get(section_key, {})
                if section_key not in flext:
                    flext[section_key] = tomlkit.table()
                item = flext[section_key]
                if not isinstance(item, tomlkit.items.Table):
                    msg = f"{project_info.name}: [tool.flext.{section_key}] is not a table"
                    raise TypeError(msg)
                for k, v in section_data.items():
                    if k not in item:
                        item[k] = v

            rendered = tomlkit.dumps(doc)
            if rendered == original_text:
                continue

            if self.check_only or self.dry_run:
                u.Infra.info(
                    f"  stale: {pyproject_path.relative_to(self.workspace_root)}",
                )
                generated += 1
                continue

            pyproject_path.write_text(rendered, encoding=c.Infra.ENCODING_DEFAULT)
            generated += 1
            u.Infra.info(
                f"  generated: {pyproject_path.relative_to(self.workspace_root)}",
            )

        verb = "would update" if (self.check_only or self.dry_run) else "updated"
        u.Infra.info(f"pyproject-keys: {verb} {generated}")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenPyprojectKeys"]
