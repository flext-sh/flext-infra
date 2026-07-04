"""Auto-generate standardized ``[tool.flext.*]`` tables in each project's pyproject.toml.

Uses the ``u.Cli`` TOML helpers (round-trip preserving formatting, comments,
and ordering). Project discovery uses ``u.Infra.discover_projects`` — the
canonical workspace member list.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from flext_core import r
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.utilities import u

if TYPE_CHECKING:
    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraCodegenPyprojectKeys(s[bool]):
    """Ensure every workspace project has standardized ``[tool.flext.*]`` tables.

    Reads each ``pyproject.toml`` via ``u.Cli`` TOML helpers (round-trip preserving),
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
            doc_result = u.Cli.toml_read_document(pyproject_path)
            if doc_result.failure:
                return r[bool].fail(
                    doc_result.error or f"pyproject-keys: cannot read {pyproject_path}",
                )
            doc = doc_result.value
            original_text = u.Cli.toml_dumps(doc)

            tool_flext_config = u.read_tool_flext_config(project_info.path)
            dumped = tool_flext_config.model_dump(exclude_none=True)

            tool: t.Cli.TomlTable = doc.setdefault(
                "tool",
                u.Cli.toml_table(super_table=True),
            )
            flext: t.Cli.TomlTable = tool.setdefault(
                "flext",
                u.Cli.toml_table(super_table=True),
            )

            for section_key in ("project", "namespace", "docs", "aliases"):
                section_data = dumped.get(section_key, {})
                if section_key not in flext:
                    flext[section_key] = u.Cli.toml_table()
                raw_item = flext[section_key]
                if not u.Cli.toml_is_table(raw_item):
                    msg = f"{project_info.name}: [tool.flext.{section_key}] is not a table"
                    raise TypeError(msg)
                section_table: t.Cli.TomlTable = raw_item
                for k, v in section_data.items():
                    if k not in section_table:
                        section_table[k] = v

            rendered = u.Cli.toml_dumps(doc)
            if rendered == original_text:
                continue

            if self.check_only or self.dry_run:
                u.Cli.info(
                    f"  stale: {pyproject_path.relative_to(self.workspace_root)}",
                )
                generated += 1
                continue

            write_result = u.Cli.atomic_write_text_file(pyproject_path, rendered)
            if write_result.failure:
                return r[bool].fail(
                    write_result.error
                    or f"pyproject-keys: cannot write {pyproject_path}",
                )
            generated += 1
            u.Cli.info(
                f"  generated: {pyproject_path.relative_to(self.workspace_root)}",
            )

        verb = "would update" if (self.check_only or self.dry_run) else "updated"
        u.Cli.info(f"pyproject-keys: {verb} {generated}")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenPyprojectKeys"]
