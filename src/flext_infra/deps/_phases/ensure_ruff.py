"""Phase: Ensure standard Ruff configuration inline with known-first-party overlay."""

from __future__ import annotations

from collections.abc import MutableSequence
from pathlib import Path

import tomlkit
from tomlkit.container import Container
from tomlkit.items import Item, Table

from flext_infra import c, m, t, u


class FlextInfraEnsureRuffConfigPhase:
    """Ensure standard Ruff configuration inline with known-first-party overlay."""

    def __init__(self, tool_config: m.Infra.ToolConfigDocument) -> None:
        self._tool_config = tool_config

    def apply(
        self,
        doc: tomlkit.TOMLDocument,
        *,
        path: Path,
    ) -> t.StrSequence:
        changes: MutableSequence[str] = []
        tool: Item | Container | None = None
        if c.Infra.TOOL in doc:
            tool = doc[c.Infra.TOOL]
        if not isinstance(tool, Table):
            tool = tomlkit.table()
            doc[c.Infra.TOOL] = tool
        ruff = u.ensure_table(tool, c.Infra.RUFF)
        if c.Infra.EXTEND in ruff:
            del ruff[c.Infra.EXTEND]
            changes.append("tool.ruff.extend removed")

        ruff_cfg = self._tool_config.tools.ruff
        if sorted(
            u.as_string_list(u.get(ruff, c.Infra.EXCLUDE)),
        ) != sorted(ruff_cfg.exclude):
            ruff[c.Infra.EXCLUDE] = u.array(sorted(ruff_cfg.exclude))
            changes.append("tool.ruff.exclude set")
        for key, value in {
            "fix": ruff_cfg.fix,
            "line-length": ruff_cfg.line_length,
            "preview": ruff_cfg.preview,
            "respect-gitignore": ruff_cfg.respect_gitignore,
            "show-fixes": ruff_cfg.show_fixes,
            "target-version": ruff_cfg.target_version,
        }.items():
            if u.unwrap_item(u.get(ruff, key)) != value:
                ruff[key] = value
                changes.append(f"tool.ruff.{key} set")
        discovered_src = sorted(u.discover_python_dirs(path.parent))
        effective_src = discovered_src or sorted(ruff_cfg.src)
        if sorted(u.as_string_list(u.get(ruff, "src"))) != effective_src:
            ruff["src"] = u.array(effective_src)
            changes.append("tool.ruff.src set")

        ruff_format = u.ensure_table(ruff, "format")
        for key, value in {
            "docstring-code-format": ruff_cfg.format.docstring_code_format,
            "indent-style": ruff_cfg.format.indent_style,
            "line-ending": ruff_cfg.format.line_ending,
            "quote-style": ruff_cfg.format.quote_style,
        }.items():
            if u.unwrap_item(u.get(ruff_format, key)) != value:
                ruff_format[key] = value
                changes.append(f"tool.ruff.format.{key} set")

        lint = u.ensure_table(ruff, c.Infra.LINT_SECTION)
        if sorted(u.as_string_list(u.get(lint, "select"))) != sorted(
            ruff_cfg.lint.select,
        ):
            lint["select"] = u.array(sorted(ruff_cfg.lint.select))
            changes.append("tool.ruff.lint.select set")
        if sorted(
            u.as_string_list(u.get(lint, c.Infra.IGNORE)),
        ) != sorted(ruff_cfg.lint.ignore):
            lint[c.Infra.IGNORE] = u.array(sorted(ruff_cfg.lint.ignore))
            changes.append("tool.ruff.lint.ignore set")

        isort = u.ensure_table(lint, c.Infra.ISORT)
        for key, value in {
            "combine-as-imports": ruff_cfg.lint.isort.combine_as_imports,
            "force-single-line": ruff_cfg.lint.isort.force_single_line,
            "split-on-trailing-comma": ruff_cfg.lint.isort.split_on_trailing_comma,
        }.items():
            if u.unwrap_item(u.get(isort, key)) != value:
                isort[key] = value
                changes.append(f"tool.ruff.lint.isort.{key} set")

        per_file_ignores = u.ensure_table(lint, "per-file-ignores")
        for pattern in u.table_string_keys(per_file_ignores):
            if pattern not in ruff_cfg.lint.per_file_ignores:
                del per_file_ignores[pattern]
                changes.append(f"tool.ruff.lint.per-file-ignores.{pattern} removed")
        for pattern, rules in ruff_cfg.lint.per_file_ignores.items():
            if sorted(
                u.as_string_list(u.get(per_file_ignores, pattern)),
            ) != sorted(rules):
                per_file_ignores[pattern] = u.array(sorted(rules))
                changes.append(f"tool.ruff.lint.per-file-ignores.{pattern} set")

        detected_packages = sorted(
            {
                *u.discover_first_party_namespaces(path.parent),
                *u.workspace_dep_namespaces(doc),
            },
        )
        if detected_packages:
            current_kfp = sorted(
                u.as_string_list(
                    u.get(isort, c.Infra.KNOWN_FIRST_PARTY_HYPHEN),
                ),
            )
            if current_kfp != detected_packages:
                isort[c.Infra.KNOWN_FIRST_PARTY_HYPHEN] = u.array(
                    detected_packages,
                )
                changes.append(
                    f"tool.ruff.lint.isort.known-first-party set to {detected_packages}",
                )
        if c.Infra.LINT_SECTION in doc:
            del doc[c.Infra.LINT_SECTION]
            changes.append("removed stale top-level [lint] section")
        return changes


__all__ = ["FlextInfraEnsureRuffConfigPhase"]
