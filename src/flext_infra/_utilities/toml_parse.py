"""TOML dependency and project parsing helpers for flext-infra.

Advanced parsing operations for pyproject.toml: dependency extraction,
deduplication, namespace discovery, and tool configuration management.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import FlextCliUtilities
from flext_infra import c, p, r, t


class FlextInfraUtilitiesTomlParse:
    """TOML parsing helpers — dependency extraction and project configuration.

    Usage::

        from flext_infra import FlextInfraUtilitiesTomlParse

        name = FlextInfraUtilitiesTomlParse.dep_name("requests>=2.0")
    """

    @staticmethod
    def dep_name(spec: str) -> str:
        """Extract normalized dependency name from one requirement or local path."""
        base = spec.strip().split("@", 1)[0].strip().lstrip("/")
        for prefix in (f"{c.Infra.FLEXT_DEPS_DIR}/", "../", "./"):
            while base.startswith(prefix):
                base = base.removeprefix(prefix)
        match = c.Infra.DEP_NAME_RE.match(base)
        if match:
            return match.group(1).lower().replace("_", "-")
        return base.lower().replace("_", "-")

    @staticmethod
    def dedupe_specs(specs: t.StrSequence) -> t.StrSequence:
        """Deduplicate dependency specifications by normalized name, sorted by full spec string."""
        seen: t.MutableStrMapping = {}
        for spec in specs:
            key = FlextInfraUtilitiesTomlParse.dep_name(spec)
            if key and key not in seen:
                seen[key] = spec
        return sorted(seen.values())

    @staticmethod
    def _normalize_pep621_local_path(path_part: str) -> str | None:
        """Normalize one PEP 621 local path reference to a dep-name input."""
        normalized = path_part.strip()
        if not normalized:
            return None
        if normalized.startswith(("git+", "git@", "http://", "https://", "ssh://")):
            return None
        if "://" in normalized and not normalized.startswith("file://"):
            return None
        if normalized.startswith("file://"):
            normalized = normalized.removeprefix("file://").strip()
        elif normalized.startswith("file:"):
            normalized = normalized.removeprefix("file:").strip()
        elif not normalized.startswith(("./", "../", "/")):
            return None
        return normalized.removeprefix("./").strip() or None

    @staticmethod
    def workspace_dep_namespaces(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract Python package names of workspace (flext-*) dependencies.

        Converts hyphenated dependency names (``flext-core``) to Python namespace
        format (``flext_core``) so they can be added to ``known-first-party`` for
        projects that consume flext packages but are not themselves flext-prefixed.
        """
        return FlextInfraUtilitiesTomlParse.workspace_dep_namespaces_from_payload(
            doc.unwrap()
        )

    @staticmethod
    def workspace_dep_namespaces_from_payload(
        raw: t.Infra.ContainerDict,
    ) -> t.StrSequence:
        """Extract workspace dependency namespaces from one plain TOML payload."""
        return sorted(
            dep.replace("-", "_")
            for dep in FlextInfraUtilitiesTomlParse.declared_dependency_names_from_payload(
                raw
            )
            if dep.startswith(c.Infra.PKG_PREFIX_HYPHEN)
        )

    @staticmethod
    def local_dependency_names(
        doc: t.Cli.TomlDocument,
        *,
        workspace_project_names: t.StrSequence = (),
    ) -> t.StrSequence:
        """Extract normalized local/workspace dependency names across supported TOML sections."""
        raw: t.Infra.TomlData = doc.unwrap()
        return FlextInfraUtilitiesTomlParse.local_dependency_names_from_payload(
            raw,
            workspace_project_names=workspace_project_names,
        )

    @staticmethod
    def local_dependency_names_from_payload(
        raw: t.Infra.ContainerDict,
        *,
        workspace_project_names: t.StrSequence = (),
    ) -> t.StrSequence:
        """Extract normalized local/workspace dependency names from a TOML payload."""
        names: t.Infra.StrSet = set()
        workspace_names = set(workspace_project_names)
        project_table = raw.get(c.Infra.PROJECT)
        dependencies: t.StrSequence = []
        if isinstance(project_table, Mapping):
            raw_dependencies = project_table.get(c.Infra.DEPENDENCIES, [])
            if isinstance(raw_dependencies, Sequence) and not isinstance(
                raw_dependencies,
                str,
            ):
                dependencies = [
                    dep_entry
                    for dep_entry in raw_dependencies
                    if isinstance(dep_entry, str)
                ]
        declared_project_names = (
            {
                dep_name
                for dep_entry in dependencies
                if (dep_name := FlextInfraUtilitiesTomlParse.dep_name(dep_entry))
            }
            if isinstance(project_table, Mapping)
            else set()
        )
        for dep_entry in declared_project_names:
            if dep_entry in workspace_names:
                names.add(dep_entry)
        if isinstance(project_table, Mapping):
            for dep_entry in dependencies:
                if " @ " not in dep_entry:
                    continue
                _name, path_part = dep_entry.split(" @ ", 1)
                normalized_path = (
                    FlextInfraUtilitiesTomlParse._normalize_pep621_local_path(
                        path_part,
                    )
                )
                if normalized_path:
                    names.add(FlextInfraUtilitiesTomlParse.dep_name(normalized_path))
        tool_table = raw.get(c.Infra.TOOL)
        if not isinstance(tool_table, Mapping):
            return sorted(names)
        poetry_table = tool_table.get(c.Infra.POETRY)
        if isinstance(poetry_table, Mapping):
            deps_table = poetry_table.get(c.Infra.DEPENDENCIES)
            if isinstance(deps_table, Mapping):
                for dep_table in deps_table.values():
                    if not isinstance(dep_table, Mapping):
                        continue
                    dep_path = dep_table.get(c.Infra.PATH)
                    if isinstance(dep_path, str) and dep_path.strip():
                        names.add(FlextInfraUtilitiesTomlParse.dep_name(dep_path))
        uv_table = tool_table.get("uv")
        if not isinstance(uv_table, Mapping):
            return sorted(names)
        sources_table = uv_table.get("sources")
        if not isinstance(sources_table, Mapping):
            return sorted(names)
        for source_key, source_table in sources_table.items():
            dep_name = str(source_key)
            if declared_project_names and dep_name not in declared_project_names:
                continue
            if not isinstance(source_table, Mapping):
                continue
            workspace_val = source_table.get("workspace")
            if workspace_val is True:
                names.add(dep_name)
                continue
            source_path = source_table.get(c.Infra.PATH)
            if isinstance(source_path, str) and source_path.strip():
                names.add(FlextInfraUtilitiesTomlParse.dep_name(source_path))
        return sorted(names)

    @staticmethod
    def project_dev_groups(doc: t.Cli.TomlDocument) -> Mapping[str, t.StrSequence]:
        """Extract optional-dependencies groups from project table."""
        return FlextInfraUtilitiesTomlParse.project_dev_groups_from_payload(
            doc.unwrap()
        )

    @staticmethod
    def project_dev_groups_from_payload(
        raw: t.Infra.ContainerDict,
    ) -> Mapping[str, t.StrSequence]:
        """Extract optional-dependency groups from one plain TOML payload."""
        project_raw = raw.get(c.Infra.PROJECT)
        if not isinstance(project_raw, Mapping):
            return {}
        optional_raw = project_raw.get(c.Infra.OPTIONAL_DEPENDENCIES)
        if not isinstance(optional_raw, Mapping):
            return {}

        def _group_values(group_key: str) -> t.StrSequence:
            return FlextCliUtilities.Cli.toml_as_string_list(
                optional_raw.get(group_key, None)
            )

        return {
            c.Infra.DEV: _group_values(c.Infra.DEV),
            c.Infra.DIR_DOCS: _group_values(c.Infra.DOCS),
            c.Infra.SECURITY: _group_values(c.Infra.SECURITY),
            c.Infra.TEST: _group_values(c.Infra.TEST),
            c.Infra.DIR_TYPINGS: _group_values(c.Infra.DIR_TYPINGS),
        }

    @staticmethod
    def declared_dependency_names(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract normalized dependency names from all declared project groups."""
        raw: t.Infra.TomlData = doc.unwrap()
        return FlextInfraUtilitiesTomlParse.declared_dependency_names_from_payload(raw)

    @staticmethod
    def declared_dependency_names_from_payload(
        raw: t.Infra.ContainerDict,
    ) -> t.StrSequence:
        """Extract normalized dependency names from a plain TOML payload."""
        names: set[str] = set()

        def _collect(items: t.Infra.InfraValue) -> None:
            if not isinstance(items, Sequence) or isinstance(items, str):
                return
            for item in items:
                if not isinstance(item, str):
                    continue
                dep_name = FlextInfraUtilitiesTomlParse.dep_name(item)
                if dep_name:
                    names.add(dep_name)

        project_raw = raw.get(c.Infra.PROJECT)
        if isinstance(project_raw, Mapping):
            _collect(project_raw.get(c.Infra.DEPENDENCIES))
            optional_raw = project_raw.get(c.Infra.OPTIONAL_DEPENDENCIES)
            if isinstance(optional_raw, Mapping):
                for specs in optional_raw.values():
                    _collect(specs)

        groups_raw = raw.get("dependency-groups")
        if isinstance(groups_raw, Mapping):
            for specs in groups_raw.values():
                _collect(specs)

        tool_raw = raw.get(c.Infra.TOOL)
        if not isinstance(tool_raw, Mapping):
            return sorted(names)
        poetry_raw = tool_raw.get(c.Infra.POETRY)
        if not isinstance(poetry_raw, Mapping):
            return sorted(names)
        deps_raw = poetry_raw.get(c.Infra.DEPENDENCIES)
        if not isinstance(deps_raw, Mapping):
            return sorted(names)
        for dep_key in deps_raw:
            dep_name = FlextInfraUtilitiesTomlParse.dep_name(str(dep_key))
            if dep_name and dep_name != "python":
                names.add(dep_name)
        return sorted(names)

    @staticmethod
    def canonical_dev_dependencies(root_doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Merge all dev dependency groups from root pyproject."""
        return FlextInfraUtilitiesTomlParse.canonical_dev_dependencies_from_payload(
            root_doc.unwrap()
        )

    @staticmethod
    def canonical_dev_dependencies_from_payload(
        raw: t.Infra.ContainerDict,
    ) -> t.StrSequence:
        """Merge all dev dependency groups from one plain root payload."""
        groups = FlextInfraUtilitiesTomlParse.project_dev_groups_from_payload(raw)
        merged = [
            *groups.get(c.Infra.DEV, []),
            *groups.get(c.Infra.DIR_DOCS, []),
            *groups.get(c.Infra.SECURITY, []),
            *groups.get(c.Infra.TEST, []),
            *groups.get(c.Infra.DIR_TYPINGS, []),
        ]
        return FlextInfraUtilitiesTomlParse.dedupe_specs(merged)

    @staticmethod
    def read_plain(path: Path) -> p.Result[t.Infra.ContainerDict]:
        """Read and parse a TOML file as a plain dict with r error handling."""
        result = FlextCliUtilities.Cli.toml_read_json(path)
        if result.failure:
            if not path.exists():
                return r[t.Infra.ContainerDict].ok({})
            return r[t.Infra.ContainerDict].fail(
                result.error or f"TOML read error: {path}",
            )
        try:
            data = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(result.value)
        except c.ValidationError as exc:
            return r[t.Infra.ContainerDict].fail(f"TOML read error: {exc}")
        return r[t.Infra.ContainerDict].ok(data)


__all__: list[str] = ["FlextInfraUtilitiesTomlParse"]
