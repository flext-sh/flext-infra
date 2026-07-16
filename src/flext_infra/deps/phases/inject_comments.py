"""Phase: Inject managed/custom markers into pyproject.toml.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, config, t, u


class FlextInfraInjectCommentsPhase:
    """Inject managed/custom markers into pyproject.toml."""

    _MYPY_RATIONALE_HEADER = (
        "# FLEXT mypy suppression rationale (validated at the facade-MRO boundary):"
    )
    _RUFF_RATIONALE_HEADER = (
        "# FLEXT Ruff suppression rationale (validated against semantic facet order):"
    )
    _PYRIGHT_RATIONALE_HEADER = (
        "# FLEXT Pyright suppression rationale (validated at the facade-MRO boundary):"
    )

    @classmethod
    def _mypy_rationale_lines(cls) -> t.StrSequence:
        """Render evidence-backed Mypy exclusions from the tooling SSOT."""
        return (
            cls._MYPY_RATIONALE_HEADER,
            *(
                f"# FLEXT mypy[{code}]: {rationale}"
                for code, rationale in sorted(
                    config.Infra.tooling.tools.mypy.disabled_error_codes.items()
                )
            ),
        )

    @classmethod
    def _ruff_rationale_lines(cls) -> t.StrSequence:
        """Render evidence-backed Ruff exclusions from the tooling SSOT."""
        return (
            cls._RUFF_RATIONALE_HEADER,
            *(
                f"# FLEXT ruff[{code}]: {rationale}"
                for code, rationale in sorted(
                    config.Infra.tooling.tools.ruff.lint.ignored_rule_rationales.items()
                )
            ),
        )

    @classmethod
    def _pyright_rationale_lines(cls) -> t.StrSequence:
        """Render evidence-backed Pyright exclusions from the tooling SSOT."""
        return (
            cls._PYRIGHT_RATIONALE_HEADER,
            *(
                f"# FLEXT pyright[{code}]: {rationale}"
                for code, rationale in sorted(
                    config.Infra.tooling.tools.pyright.global_suppression_rationales.items()
                )
            ),
        )

    @classmethod
    def _managed_marker_lines(cls) -> t.Infra.StrSet:
        """Return the managed marker lines."""
        markers = {marker for _section_prefix, marker in c.Infra.COMMENT_MARKERS}
        markers.add(c.Infra.DEV_OPTIONAL_DEPS_MARKER)
        markers.add(c.Infra.LEGACY_AUTO_MARKER)
        markers.add(c.Infra.LEGACY_AUTO_BANNER_LINE)
        markers.update(c.Infra.BANNER.splitlines())
        markers.update(cls._mypy_rationale_lines())
        markers.update(cls._ruff_rationale_lines())
        markers.update(cls._pyright_rationale_lines())
        return markers

    @staticmethod
    def _is_managed_comment(
        item: t.Cli.TomlItem, managed_lines: t.Infra.StrSet
    ) -> bool:
        """Match managed text only after TOML parsed it as comment trivia."""
        text = item.as_string().strip()
        return text in managed_lines or text.startswith((
            "# Sections with [MANAGED] are enforced",
            "# FLEXT mypy[",
            "# FLEXT ruff[",
            "# FLEXT pyright[",
        ))

    @classmethod
    def _collect_structure(
        cls, parent: t.Cli.TomlDocument | t.Cli.TomlTable, prefix: t.StrSequence = ()
    ) -> tuple[
        tuple[tuple[t.StrSequence, t.Cli.TomlTable], ...],
        tuple[t.Cli.TomlContainer, ...],
    ]:
        """Collect ordered table and container references without rendering text."""
        container = parent.value if u.Cli.toml_is_table(parent) else parent
        tables: t.MutableSequenceOf[tuple[t.StrSequence, t.Cli.TomlTable]] = []
        containers: t.MutableSequenceOf[t.Cli.TomlContainer] = [container]
        for key, item in tuple(container.body):
            if key is None:
                continue
            path = (*prefix, key.key)
            if u.Cli.toml_is_table(item):
                tables.append((path, item))
                nested_tables, nested_containers = cls._collect_structure(item, path)
                tables.extend(nested_tables)
                containers.extend(nested_containers)
            elif u.Cli.toml_is_aot(item):
                for table in item.body:
                    tables.append((path, table))
                    nested_tables, nested_containers = cls._collect_structure(
                        table, path
                    )
                    tables.extend(nested_tables)
                    containers.extend(nested_containers)
        return tuple(tables), tuple(containers)

    @staticmethod
    def _remove_legacy_group(document: t.Cli.TomlDocument) -> bool:
        """Remove only the invalid legacy dependency table from the TOML tree."""
        group = u.Cli.toml_table_child(document, "group")
        if group is None:
            return False
        dev = u.Cli.toml_table_child(group, "dev")
        if dev is None or "dependencies" not in dev:
            return False
        dev.remove("dependencies")
        if not dev:
            group.remove("dev")
        if not group:
            document.remove("group")
        return True

    @classmethod
    def _remove_managed_comments(
        cls, document: t.Cli.TomlDocument, containers: t.SequenceOf[t.Cli.TomlContainer]
    ) -> None:
        """Remove managed comments while preserving all scalar and custom trivia."""
        managed_lines = cls._managed_marker_lines()
        for container in containers:
            retained = container.body[:0]
            discarded_indexes: t.MutableSequenceOf[int] = []
            for index, (key, item) in enumerate(container.body):
                if key is None and cls._is_managed_comment(item, managed_lines):
                    discarded_indexes.append(index)
                    continue
                whitespace = key is None and not item.as_string().strip()
                if whitespace and item.as_string().count("\n") > 1:
                    anchor = next(
                        (
                            previous
                            for previous_key, previous in reversed(retained)
                            if previous_key is not None or previous.as_string().strip()
                        ),
                        None,
                    )
                    if anchor is not None:
                        trail = anchor.trivia.trail.rstrip("\n")
                        anchor.trivia.trail = f"{trail}\n\n"
                        discarded_indexes.append(index)
                        continue
                retained.append((key, item))
            if discarded_indexes:
                u.Cli.toml_discard_unkeyed_items(container, discarded_indexes)
        leading_indexes: t.MutableSequenceOf[int] = []
        for index, (key, item) in enumerate(document.body):
            if key is not None or item.as_string().strip():
                break
            leading_indexes.append(index)
        if leading_indexes:
            u.Cli.toml_discard_unkeyed_items(document, leading_indexes)

    @staticmethod
    def _marker_for_path(path: t.StrSequence) -> t.Pair[str, str | None]:
        """Return the rendered canonical header and its configured marker."""
        section_header = f"[{'.'.join(path)}]"
        for section_prefix, marker_text in c.Infra.COMMENT_MARKERS:
            if section_header.startswith(section_prefix):
                return section_header, marker_text
        return section_header, None

    @classmethod
    def _first_rendered_item(
        cls, parent: t.Cli.TomlDocument | t.Cli.TomlTable
    ) -> t.Cli.TomlItem | None:
        """Find the first serialized item beneath non-rendered super tables."""
        container = parent.value if u.Cli.toml_is_table(parent) else parent
        for key, item in container.body:
            if key is None:
                if item.as_string().strip():
                    return item
                continue
            if u.Cli.toml_is_table(item) and item.is_super_table():
                nested = cls._first_rendered_item(item)
                if nested is not None:
                    return nested
                continue
            if u.Cli.toml_is_aot(item):
                return next(iter(item.body), None)
            return item
        return None

    @staticmethod
    def _prepend_marker(item: t.Cli.TomlItem, marker: str) -> None:
        """Attach one marker to the trivia immediately preceding an item."""
        item.trivia.indent = f"{marker}\n{item.trivia.indent}"

    @classmethod
    def _inject_structural_comments(
        cls,
        tables: t.SequenceOf[tuple[t.StrSequence, t.Cli.TomlTable]],
        changes: t.MutableSequenceOf[str],
    ) -> None:
        """Attach configured markers and rationales to parsed table trivia."""
        emitted_markers: set[str] = set()
        for path, table in tables:
            normalized_path = tuple(path)
            if normalized_path == ("project", "optional-dependencies"):
                target: t.Cli.TomlItem | None = table
                if table.is_super_table():
                    target = u.Cli.toml_item_child(table, "dev")
                if (
                    target is not None
                    and c.Infra.DEV_OPTIONAL_DEPS_MARKER not in emitted_markers
                ):
                    cls._prepend_marker(target, c.Infra.DEV_OPTIONAL_DEPS_MARKER)
                    changes.append("marker injected for optional-dependencies.dev")
                    emitted_markers.add(c.Infra.DEV_OPTIONAL_DEPS_MARKER)
            if table.is_super_table():
                continue
            section_header, marker = cls._marker_for_path(path)
            if marker is not None and marker not in emitted_markers:
                cls._prepend_marker(table, marker)
                changes.append(f"marker injected for {section_header}")
                emitted_markers.add(marker)
            rationale_lines: t.StrSequence = ()
            rationale_name = ""
            if normalized_path == ("tool", "mypy"):
                rationale_lines = cls._mypy_rationale_lines()
                rationale_name = "Mypy"
            elif normalized_path == ("tool", "ruff", "lint"):
                rationale_lines = cls._ruff_rationale_lines()
                rationale_name = "Ruff"
            elif normalized_path == ("tool", "pyright"):
                rationale_lines = cls._pyright_rationale_lines()
                rationale_name = "Pyright"
            if rationale_lines:
                rationale_block = "\n".join(rationale_lines)
                table.trivia.trail = f"\n{rationale_block}\n"
                changes.append(f"{rationale_name} suppression rationales injected")

    def apply(self, rendered: str) -> t.Pair[str, t.StrSequence]:
        """Inject managed banner/markers and return updated TOML plus change messages."""
        # NOTE (multi-agent, mro-wkii.17.26.2.26 / agent: codex): all detection
        # and mutation is structural so TOML-looking text inside scalars is opaque.
        document = u.Cli.toml_parse_text(rendered)
        if document is None:
            msg = "managed comment injection requires valid TOML"
            raise ValueError(msg)
        baseline = u.Cli.toml_as_mapping(document)
        if not baseline:
            msg = "managed comment injection requires non-empty TOML"
            raise ValueError(msg)
        changes: t.MutableSequenceOf[str] = []
        lines = rendered.splitlines()
        cleaned_lines, cleanup_changes = self._strip_managed_lines(lines)
        changes.extend(cleanup_changes)
        banner_lines = c.Infra.BANNER.splitlines()
        out: t.MutableSequenceOf[str] = [*banner_lines]
        if lines[: len(banner_lines)] != banner_lines:
            changes.append("managed banner injected")
        emitted_markers: set[str] = set()
        for line in cleaned_lines:
            stripped = line.strip()
            marker = self._marker_for_section(stripped)
            if marker and marker not in emitted_markers:
                out.append(marker)
                changes.append(f"marker injected for {stripped}")
                emitted_markers.add(marker)
            if stripped == "[project.optional-dependencies]" or stripped.startswith(
                "optional-dependencies.dev"
            ):
                self._inject_dev_markers(out, changes, emitted_markers)
            out.append(line)
            if stripped == "[tool.mypy]":
                out.extend(self._mypy_rationale_lines())
                changes.append("Mypy suppression rationales injected")
            elif stripped == "[tool.ruff.lint]":
                out.extend(self._ruff_rationale_lines())
                changes.append("Ruff suppression rationales injected")
            elif stripped == "[tool.pyright]":
                out.extend(self._pyright_rationale_lines())
                changes.append("Pyright suppression rationales injected")
        updated = "\n".join(self._collapse_blank_lines(out)).rstrip() + "\n"
        original = rendered.rstrip() + "\n"
        if updated == original:
            return (updated, [])
        return (updated, changes)


__all__: list[str] = ["FlextInfraInjectCommentsPhase"]
