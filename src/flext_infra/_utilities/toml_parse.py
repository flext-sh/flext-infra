"""TOML dependency and project parsing helpers for flext-infra.

Advanced parsing operations for pyproject.toml: dependency extraction,
deduplication, namespace discovery, and tool configuration management.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import BaseModel, TypeAdapter, ValidationError

from flext_cli import u
from flext_core import r
from flext_infra import FlextInfraUtilitiesToml, c, t


class FlextInfraUtilitiesTomlParse:
    """TOML parsing helpers — dependency extraction and project configuration.

    Usage::

        from flext_infra import FlextInfraUtilitiesTomlParse

        name = FlextInfraUtilitiesTomlParse.dep_name("requests>=2.0")
    """

    @staticmethod
    def dep_name(spec: str) -> str:
        """Extract normalized dependency name from requirement specification."""
        base = spec.strip().split("@", 1)[0].strip()
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
    def ensure_pyright_execution_envs(
        pyright: t.Cli.TomlTable,
        expected: Sequence[Mapping[str, t.Infra.InfraValue]] | Sequence[BaseModel],
        changes: MutableSequence[str],
    ) -> None:
        """Ensure pyright executionEnvironments matches expected; append to changes if updated."""
        raw = FlextInfraUtilitiesToml.unwrap_item(
            FlextInfraUtilitiesToml.get(pyright, "executionEnvironments"),
        )
        current: Sequence[t.StrMapping] = []
        if isinstance(raw, list):
            with contextlib.suppress(ValidationError):
                current = TypeAdapter(Sequence[t.StrMapping]).validate_python(raw)
        normalized: Sequence[Mapping[str, t.Infra.InfraValue]] = [
            entry.model_dump(by_alias=True) if isinstance(entry, BaseModel) else entry
            for entry in expected
        ]
        if list(current) != normalized:
            pyright["executionEnvironments"] = normalized
            changes.append(
                "tool.pyright.executionEnvironments set with tests reportPrivateUsage=none",
            )

    @staticmethod
    def discover_first_party_namespaces(project_dir: Path) -> t.StrSequence:
        """Discover first-party namespace packages from src/ for tool configuration."""
        src_dir = project_dir / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return []
        namespaces: t.StrSequence = [
            entry.name
            for entry in sorted(src_dir.iterdir())
            if entry.is_dir()
            and entry.name != c.Infra.Dunders.PYCACHE
            and entry.name.isidentifier()
            and "-" not in entry.name
        ]
        return namespaces

    @staticmethod
    def workspace_dep_namespaces(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract Python package names of workspace (flext-*) dependencies.

        Converts hyphenated dependency names (``flext-core``) to Python namespace
        format (``flext_core``) so they can be added to ``known-first-party`` for
        projects that consume flext packages but are not themselves flext-prefixed.
        """
        all_deps = FlextInfraUtilitiesTomlParse.declared_dependency_names(doc)
        return sorted(
            dep.replace("-", "_")
            for dep in all_deps
            if dep.startswith(c.Infra.Packages.PREFIX_HYPHEN)
        )

    @staticmethod
    def project_dev_groups(doc: t.Cli.TomlDocument) -> Mapping[str, t.StrSequence]:
        """Extract optional-dependencies groups from project table."""
        project_raw = u.Cli.toml_get_table(doc, c.Infra.PROJECT)
        if project_raw is None:
            return {}
        optional_raw = u.Cli.toml_get_table(project_raw, c.Infra.OPTIONAL_DEPENDENCIES)
        if optional_raw is None:
            return {}
        opt_deps: t.Cli.TomlTable = optional_raw

        def _group_values(group_key: str) -> t.StrSequence:
            value = u.Cli.toml_get_item(opt_deps, group_key)
            return u.Cli.toml_as_string_list(value)

        return {
            c.Infra.DEV: _group_values(c.Infra.DEV),
            c.Infra.Directories.DOCS: _group_values(c.Infra.DOCS),
            c.Infra.SECURITY: _group_values(c.Infra.SECURITY),
            c.Infra.TEST: _group_values(c.Infra.TEST),
            c.Infra.Directories.TYPINGS: _group_values(c.Infra.Directories.TYPINGS),
        }

    @staticmethod
    def declared_dependency_names(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract normalized dependency names from all declared project groups."""
        raw: t.Infra.TomlData = doc.unwrap()
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

        project_val: t.Infra.InfraValue = raw.get(c.Infra.PROJECT)
        if u.is_mapping(project_val):
            _collect(project_val.get(c.Infra.DEPENDENCIES))
            optional_val: t.Infra.InfraValue = project_val.get(
                c.Infra.OPTIONAL_DEPENDENCIES,
            )
            if u.is_mapping(optional_val):
                for specs in optional_val.values():
                    _collect(specs)

        groups_val: t.Infra.InfraValue = raw.get("dependency-groups")
        if u.is_mapping(groups_val):
            for specs in groups_val.values():
                _collect(specs)

        tool_val: t.Infra.InfraValue = raw.get(c.Infra.TOOL)
        if not u.is_mapping(tool_val):
            return sorted(names)
        poetry_val: t.Infra.InfraValue = tool_val.get(c.Infra.POETRY)
        if not u.is_mapping(poetry_val):
            return sorted(names)
        deps_val: t.Infra.InfraValue = poetry_val.get(c.Infra.DEPENDENCIES)
        if not u.is_mapping(deps_val):
            return sorted(names)
        for dep_key in deps_val:
            dep_name = FlextInfraUtilitiesTomlParse.dep_name(str(dep_key))
            if dep_name and dep_name != "python":
                names.add(dep_name)
        return sorted(names)

    @staticmethod
    def canonical_dev_dependencies(root_doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Merge all dev dependency groups from root pyproject."""
        groups = FlextInfraUtilitiesTomlParse.project_dev_groups(root_doc)
        merged = [
            *groups.get(c.Infra.DEV, []),
            *groups.get(c.Infra.Directories.DOCS, []),
            *groups.get(c.Infra.SECURITY, []),
            *groups.get(c.Infra.TEST, []),
            *groups.get(c.Infra.Directories.TYPINGS, []),
        ]
        return FlextInfraUtilitiesTomlParse.dedupe_specs(merged)

    @staticmethod
    def read_plain(path: Path) -> r[t.Infra.ContainerDict]:
        """Read and parse a TOML file as a plain dict with r error handling."""
        result = u.Cli.toml_read_json(path)
        if result.is_failure:
            if not path.exists():
                return r[t.Infra.ContainerDict].ok({})
            return r[t.Infra.ContainerDict].fail(
                result.error or f"TOML read error: {path}",
            )
        try:
            data = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(result.value)
        except ValidationError as exc:
            return r[t.Infra.ContainerDict].fail(f"TOML read error: {exc}")
        return r[t.Infra.ContainerDict].ok(data)


__all__ = ["FlextInfraUtilitiesTomlParse"]
