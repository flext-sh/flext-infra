"""Dependency parsing and inspection helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from importlib.metadata import requires
from importlib.resources import files
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name

from flext_cli import u
from flext_core import r
from flext_infra.constants import c

from .._utilities.pyproject import FlextInfraUtilitiesPyproject

if TYPE_CHECKING:
    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraUtilitiesDependencies:
    """Static helpers for inspecting dependency declarations in pyproject payloads."""

    @staticmethod
    def update_mise_lock(
        project_root: Path, *, platforms: t.StrSequence, staging_parent: Path
    ) -> p.Result[bool]:
        """Generate a fresh native Mise lock and publish it atomically."""
        launcher = project_root / "bin" / ("mise.cmd" if os.name == "nt" else "mise")
        if not launcher.is_file():
            return r[bool].fail(f"generated Mise launcher is absent: {launcher}")
        config_path = project_root / c.Infra.MISE_TOML_FILENAME
        config_state = u.Cli.atomic_read_binary_file_state(config_path, required=True)
        if config_state.failure:
            return r[bool].from_failure(config_state)
        if config_state.value.content is None:
            return r[bool].fail(f"generated Mise config is absent: {config_path}")
        live_lock = u.Cli.atomic_read_binary_file_state(
            project_root / c.Infra.MISE_LOCK_FILENAME, required=False
        )
        if live_lock.failure:
            return r[bool].from_failure(live_lock)
        parent_plan = u.Cli.atomic_plan_directory_chain(staging_parent)
        if parent_plan.failure:
            return r[bool].from_failure(parent_plan)
        parent_created = u.Cli.atomic_create_directory_chain_guarded(
            parent_plan.value, permission_mode=0o700
        )
        if parent_created.failure:
            return r[bool].from_failure(parent_created)
        temporary = u.Cli.files_create_temporary_directory(
            prefix="mise-lock-", parent_path=staging_parent
        )
        if temporary.failure:
            return r[bool].from_failure(temporary)
        stage_root = temporary.value
        staged_config = u.Cli.atomic_create_binary_file_guarded(
            stage_root / config_path.name,
            config_state.value.content,
            permission_mode=config_state.value.mode or 0o644,
        )
        generated: p.Result[bytes]
        if staged_config.failure:
            generated = r[bytes].from_failure(staged_config)
        else:
            executed = u.Cli.run_live(
                (
                    str(launcher),
                    "-C",
                    str(stage_root),
                    "lock",
                    "--bump",
                    "--platform",
                    ",".join(platforms),
                ),
                cwd=stage_root,
                timeout=c.Infra.TIMEOUT_LONG,
            )
            if executed.failure:
                generated = r[bytes].from_failure(executed)
            else:
                staged_lock = u.Cli.atomic_read_binary_file_state(
                    stage_root / c.Infra.MISE_LOCK_FILENAME, required=True
                )
                if staged_lock.failure:
                    generated = r[bytes].from_failure(staged_lock)
                elif staged_lock.value.content is None:
                    generated = r[bytes].fail("Mise generated an empty lock state")
                else:
                    generated = r[bytes].ok(staged_lock.value.content)
        manifest = u.Cli.atomic_inventory_physical_tree(stage_root)
        if manifest.failure:
            return r[bool].fail(
                f"{generated.error}; {manifest.error}"
                if generated.failure
                else manifest.error or "Mise staging inventory failed"
            )
        cleaned = u.Cli.atomic_cleanup_physical_tree_guarded(manifest.value)
        if cleaned.failure:
            return r[bool].fail(
                f"{generated.error}; {cleaned.error}"
                if generated.failure
                else cleaned.error or "Mise staging cleanup failed"
            )
        if generated.failure:
            return r[bool].from_failure(generated)
        published = u.Cli.atomic_write_binary_file_guarded(
            live_lock.value, generated.value, permission_mode=0o644
        )
        if published.failure:
            return r[bool].from_failure(published)
        return r[bool].ok(True)

    @staticmethod
    def dep_name(requirement: str, *, active_only: bool = False) -> str | None:
        """Extract one normalized dependency name, optionally evaluating markers."""
        text = requirement.strip()
        if not text:
            return None
        try:
            parsed = Requirement(text)
        except InvalidRequirement:
            parsed = None
        if parsed is not None:
            if (
                active_only
                and parsed.marker is not None
                and not parsed.marker.evaluate()
            ):
                return None
            return canonicalize_name(parsed.name)
        if ";" in text:
            text = text.split(";", maxsplit=1)[0].strip()
        if " @ " in text:
            text = text.split(" @ ", maxsplit=1)[0].strip()
        for separator in ("[", "==", ">=", "<=", "~=", "!=", ">", "<"):
            if separator in text:
                text = text.split(separator, maxsplit=1)[0].strip()
        if "/" in text:
            text = text.rsplit("/", maxsplit=1)[-1].strip()
        normalized = text.lower()
        return normalized or None

    @classmethod
    def project_dependency_names_from_payload(
        cls, payload: t.JsonMapping
    ) -> t.StrSequence:
        """Return strict names from the PEP 621 runtime dependency array."""
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            msg = "pyproject payload must define a [project] mapping"
            raise TypeError(msg)
        raw_dependencies = project.get(c.Infra.DEPENDENCIES, [])
        if not isinstance(raw_dependencies, list):
            msg = "[project].dependencies must be an array of requirement strings"
            raise TypeError(msg)
        names: list[str] = []
        for raw_requirement in raw_dependencies:
            if not isinstance(raw_requirement, str):
                msg = "[project].dependencies entries must be strings"
                raise TypeError(msg)
            dependency_name = cls.dep_name(raw_requirement)
            if dependency_name is None:
                msg = "[project].dependencies entries must not be blank"
                raise ValueError(msg)
            names.append(dependency_name)
        return tuple(names)

    @staticmethod
    def dependency_order(
        direct_names: t.StrSequence,
        *,
        dependencies: Callable[[str], t.StrSequence],
        prefix: str = "",
        normalize: Callable[[str], str] = canonicalize_name,
    ) -> t.StrSequence:
        """Return a dependency-first order for any named dependency graph."""
        graph: dict[str, tuple[str, ...]] = {}

        def collect(dependency_name: str) -> None:
            normalized = normalize(dependency_name)
            if normalized in graph:
                return
            children = tuple(
                child
                for raw_child in dependencies(normalized)
                if (child := normalize(raw_child))
                and (not prefix or child.startswith(prefix))
            )
            graph[normalized] = children
            for dependency in children:
                collect(dependency)

        roots = tuple(
            normalized
            for name in direct_names
            if (normalized := normalize(name))
            and (not prefix or normalized.startswith(prefix))
        )
        for root in roots:
            collect(root)
        ordered: list[str] = []
        visited: set[str] = set()
        active: list[str] = []

        def visit(distribution_name: str) -> None:
            if distribution_name in visited:
                return
            if distribution_name in active:
                cycle_start = active.index(distribution_name)
                cycle = " -> ".join((*active[cycle_start:], distribution_name))
                msg = f"cyclic dependency graph: {cycle}"
                raise ValueError(msg)
            active.append(distribution_name)
            for dependency in graph[distribution_name]:
                visit(dependency)
            active.pop()
            visited.add(distribution_name)
            ordered.append(distribution_name)

        for root in roots:
            visit(root)
        return tuple(ordered)

    @staticmethod
    def dependency_waves(
        edges: Mapping[str, t.StrSequence],
    ) -> t.SequenceOf[t.StrSequence]:
        """Split a closed named dependency graph into dependency-first waves.

        Wave ``n`` contains only names whose dependencies all live in earlier
        waves, so each wave may proceed in parallel while the sequence between
        waves stays strict. The graph is closed: every referenced name must be
        a key of ``edges``, and a cycle fails loudly.
        """
        unknown = sorted({
            dependency
            for deps in edges.values()
            for dependency in deps
            if dependency not in edges
        })
        if unknown:
            msg = "dependency graph references names outside the graph: " + ", ".join(
                unknown
            )
            raise ValueError(msg)
        pending = {name: set(deps) for name, deps in edges.items()}
        waves: list[t.StrSequence] = []
        while pending:
            ready = frozenset(name for name, deps in pending.items() if not deps)
            if not ready:
                msg = "cyclic dependency graph: " + ", ".join(sorted(pending))
                raise ValueError(msg)
            waves.append(tuple(sorted(ready)))
            pending = {
                name: deps - ready
                for name, deps in pending.items()
                if name not in ready
            }
        return tuple(waves)

    @classmethod
    def project_dependency_resource_files(
        cls,
        project_root: Path,
        *,
        resource_parts: t.StrSequence,
        distribution_prefix: str = "",
        suffix: str = "",
    ) -> t.SequenceOf[Path]:
        """Resolve runtime, local, and test dependency resources in order."""
        pyproject = project_root / c.Infra.PYPROJECT_FILENAME
        payload = u.Cli.toml_read_json(pyproject).unwrap()
        project_name = canonicalize_name(
            FlextInfraUtilitiesPyproject.project_name_from_payload(
                project_root, payload
            )
        )
        declared_names = cls.declared_dependency_names_from_payload(payload)

        def installed_dependencies(name: str) -> t.StrSequence:
            return tuple(
                dependency
                for raw_requirement in requires(name) or ()
                if (dependency := cls.dep_name(raw_requirement, active_only=True))
                is not None
            )

        ordered = list(
            cls.dependency_order(
                declared_names,
                dependencies=installed_dependencies,
                prefix=distribution_prefix,
            )
        )
        package_names: dict[str, str] = {
            name: name.replace("-", "_") for name in ordered
        }
        if not distribution_prefix or project_name.startswith(distribution_prefix):
            if project_name not in ordered:
                ordered.append(project_name)
            package_names[project_name] = (
                FlextInfraUtilitiesPyproject.package_name_from_payload(
                    project_root,
                    payload,
                    FlextInfraUtilitiesPyproject.docs_meta_from_payload(payload),
                )
            )
        discovered: list[Path] = []
        seen: set[Path] = set()
        for distribution_name in ordered:
            resource = files(package_names[distribution_name])
            for part in resource_parts:
                resource /= part
            resource_root = Path(str(resource))
            if not resource_root.is_dir():
                continue
            for candidate in sorted(resource_root.rglob(f"*{suffix}")):
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    discovered.append(resolved)
        return tuple(discovered)

    @staticmethod
    def constraint_specifier(version: str) -> str:
        """Return the resolved lock version as an open-ended dependency floor.

        PEP 440 permits a local version label only with ``==`` or ``!=``, so a
        floor built straight from a locally tagged resolution is rejected by
        every build backend. The public release is what a floor means, and the
        local build satisfies it.
        """
        public_version = version.strip().partition("+")[0]
        return f">={public_version}" if public_version else ""

    @classmethod
    def locked_dependency_versions(
        cls, lock_path: Path, *, sources: t.StrSequence = ("registry",)
    ) -> t.MappingKV[str, str]:
        """Return normalized package versions from one ``uv.lock`` file.

        ``sources`` selects the lock source kinds to read (``registry`` by
        default; ``git`` yields the siblings consumed through a pinned ref).
        """
        result: t.MappingKV[str, str] = {}
        if lock_path.is_file():
            raw_text = lock_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            payload_source = u.Cli.toml_mapping_from_text(raw_text)
            if payload_source is not None:
                payload = FlextInfraUtilitiesPyproject.validate_infra_payload(
                    payload_source
                )
                raw_packages = payload.get("package")
                if isinstance(raw_packages, list):
                    versions: dict[str, str] = {}
                    for raw_package in raw_packages:
                        if not isinstance(raw_package, Mapping):
                            continue
                        raw_source = raw_package.get("source")
                        if not isinstance(raw_source, Mapping) or not any(
                            kind in raw_source for kind in sources
                        ):
                            continue
                        raw_name = raw_package.get("name")
                        raw_version = raw_package.get(c.Infra.VERSION)
                        if not isinstance(raw_name, str) or not isinstance(
                            raw_version, str
                        ):
                            continue
                        dependency_name = cls.dep_name(raw_name)
                        if dependency_name is None:
                            continue
                        versions[dependency_name] = raw_version.strip()
                    result = dict(versions)
        return result

    @classmethod
    def rewrite_requirement_constraint(
        cls,
        requirement: str,
        *,
        locked_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence = (),
    ) -> str | None:
        """Rewrite one PEP 621 requirement to the resolved uv.lock floor."""
        result: str | None = None
        raw_text = requirement.strip()
        if raw_text:
            requirement_part, marker_separator, marker_part = raw_text.partition(";")
            if " @ " not in requirement_part:
                head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(
                    requirement_part.strip()
                )
                if head_match is not None:
                    head = head_match.group("head").strip()
                    dependency_name = cls.dep_name(head)
                    internal_set = set(internal_names)
                    if (
                        dependency_name is not None
                        and dependency_name not in internal_set
                    ):
                        locked_version = locked_versions.get(dependency_name)
                        if locked_version is not None:
                            try:
                                parsed = Requirement(requirement_part.strip())
                            except InvalidRequirement:
                                parsed = None
                            if parsed is not None and not parsed.specifier.contains(
                                locked_version, prereleases=True
                            ):
                                return None
                            retained = (
                                ()
                                if parsed is None
                                else tuple(
                                    str(specifier)
                                    for specifier in parsed.specifier
                                    if specifier.operator in {"<", "<=", "!="}
                                )
                            )
                            constraint = cls.constraint_specifier(locked_version)
                            if retained:
                                constraint = ",".join((constraint, *retained))
                            rewritten = f"{head}{constraint}"
                            marker_text = marker_part.strip()
                            if marker_separator and marker_text:
                                rewritten = f"{rewritten}; {marker_text}"
                            result = rewritten if rewritten != raw_text else None
        return result

    @classmethod
    def rewrite_poetry_constraint(
        cls,
        dependency_name: str,
        raw_value: t.Infra.InfraValue,
        *,
        locked_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence = (),
    ) -> t.Infra.InfraValue | None:
        """Rewrite one Poetry dependency to the resolved uv.lock floor."""
        result: t.Infra.InfraValue | None = None
        normalized_name = cls.dep_name(dependency_name)
        internal_set = set(internal_names)
        if (
            normalized_name is not None
            and normalized_name != "python"
            and normalized_name not in internal_set
        ):
            locked_version = locked_versions.get(normalized_name)
            if locked_version is not None:
                rewritten_specifier = cls.constraint_specifier(locked_version)
                if isinstance(raw_value, str):
                    result = (
                        rewritten_specifier
                        if raw_value != rewritten_specifier
                        else None
                    )
                elif isinstance(raw_value, Mapping) and not any(
                    key in raw_value for key in (c.Infra.PATH, "git", "url")
                ):
                    updated: t.MutableJsonMapping = dict(raw_value)
                    if updated.get(c.Infra.VERSION) != rewritten_specifier:
                        updated[c.Infra.VERSION] = rewritten_specifier
                        result = dict(updated)
        return result

    @staticmethod
    def dedupe_specs(specs: t.StrSequence) -> t.StrSequence:
        """Return deterministic unique dependency specs keyed by normalized name."""
        selected_by_name: dict[str, str] = {}
        for raw in specs:
            item = raw.strip()
            if not item:
                continue
            dependency_name = FlextInfraUtilitiesDependencies.dep_name(item)
            if dependency_name is None or dependency_name in selected_by_name:
                continue
            selected_by_name[dependency_name] = item
        return tuple(selected_by_name[name] for name in sorted(selected_by_name))

    @classmethod
    def declared_dependency_names(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
        """Return normalized dependency names from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.declared_dependency_names_from_payload(normalized)

    @classmethod
    def declared_dependency_names_from_payload(
        cls, payload: t.JsonMapping
    ) -> t.StrSequence:
        """Return normalized dependency names across supported dependency tables."""
        names: set[str] = set()
        cls._append_project_dependency_names(payload=payload, names=names)
        cls._append_dependency_group_names(payload=payload, names=names)
        cls._append_poetry_dependency_names(payload=payload, names=names)
        return tuple(sorted(names))

    @classmethod
    def _append_project_dependency_names(
        cls, *, payload: t.JsonMapping, names: set[str]
    ) -> None:
        """Append project dependency names."""
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            return
        cls._append_requirement_names(
            raw_requirements=project.get(c.Infra.DEPENDENCIES), names=names
        )
        optional_dependencies = project.get(c.Infra.OPTIONAL_DEPENDENCIES)
        if not isinstance(optional_dependencies, Mapping):
            return
        for raw_requirements in optional_dependencies.values():
            cls._append_requirement_names(
                raw_requirements=raw_requirements, names=names
            )

    @classmethod
    def _append_dependency_group_names(
        cls, *, payload: t.JsonMapping, names: set[str]
    ) -> None:
        """Append dependency group names."""
        dependency_groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if not isinstance(dependency_groups, Mapping):
            return
        for raw_requirements in dependency_groups.values():
            cls._append_requirement_names(
                raw_requirements=raw_requirements, names=names
            )

    @classmethod
    def _append_poetry_dependency_names(
        cls, *, payload: t.JsonMapping, names: set[str]
    ) -> None:
        """Append poetry dependency names."""
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, Mapping):
            return
        poetry = tool.get(c.Infra.POETRY)
        if not isinstance(poetry, Mapping):
            return
        cls._append_mapping_dependency_names(
            raw_mapping=poetry.get(c.Infra.DEPENDENCIES), names=names
        )
        poetry_groups = poetry.get(c.Infra.GROUP)
        if not isinstance(poetry_groups, Mapping):
            return
        for raw_group in poetry_groups.values():
            if not isinstance(raw_group, Mapping):
                continue
            cls._append_mapping_dependency_names(
                raw_mapping=raw_group.get(c.Infra.DEPENDENCIES), names=names
            )

    @classmethod
    def _append_requirement_names(
        cls, *, raw_requirements: t.Infra.InfraValue, names: set[str]
    ) -> None:
        """Append requirement names."""
        if not isinstance(raw_requirements, list):
            return
        for raw_requirement in raw_requirements:
            dependency_name = cls.dep_name(str(raw_requirement))
            if dependency_name is None:
                continue
            names.add(dependency_name)

    @classmethod
    def _append_mapping_dependency_names(
        cls, *, raw_mapping: t.Infra.InfraValue, names: set[str]
    ) -> None:
        """Append mapping dependency names."""
        if not isinstance(raw_mapping, Mapping):
            return
        for raw_name in raw_mapping:
            dependency_name = cls.dep_name(raw_name)
            if dependency_name is None or dependency_name == "python":
                continue
            names.add(dependency_name)

    @classmethod
    def local_dependency_names_from_payload(
        cls, payload: t.JsonMapping, *, workspace_project_names: t.StrSequence = ()
    ) -> t.StrSequence:
        """Return workspace-local dependency names from one payload."""
        declared = set(cls.declared_dependency_names_from_payload(payload))
        if not workspace_project_names:
            return ()
        workspace_names = set(workspace_project_names)
        return tuple(sorted(name for name in declared if name in workspace_names))

    @staticmethod
    def project_dev_groups_from_payload(
        payload: t.JsonMapping,
    ) -> t.MappingKV[str, t.StrSequence]:
        """Collect optional dependency groups from one normalized payload."""
        project = u.Cli.json_as_mapping(payload.get(c.Infra.PROJECT, None))
        optional = u.Cli.json_as_mapping(
            project.get(c.Infra.OPTIONAL_DEPENDENCIES, None)
        )
        groups = {
            str(group): tuple(
                str(item) for item in u.Cli.json_as_sequence(optional.get(group, None))
            )
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
        }
        return {group: values for group, values in groups.items() if values}

    @classmethod
    def project_dev_groups(
        cls, document: t.Cli.TomlDocument
    ) -> t.MappingKV[str, t.StrSequence]:
        """Collect optional dependency groups from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            # flext-j47u (codex): keep the empty mapping immutable and fully typed.
            return MappingProxyType(dict[str, tuple[str, ...]]())
        return cls.project_dev_groups_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.canonical_dev_dependencies_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies_from_payload(
        cls, payload: t.JsonMapping
    ) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one normalized payload."""
        groups = cls.project_dev_groups_from_payload(payload)
        return cls.dedupe_specs([
            requirement
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
            for requirement in groups.get(str(group), ())
        ])

    @classmethod
    def flext_dependency_namespaces(cls, document: t.Cli.TomlDocument) -> t.StrSequence:
        """Extract declared FLEXT dependency namespaces from one TOML document."""
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.flext_dependency_namespaces_from_payload(normalized)

    @classmethod
    def flext_dependency_namespaces_from_payload(
        cls, payload: t.MappingKV[str, t.Infra.InfraValue]
    ) -> t.StrSequence:
        """Extract every declared ``flext-*`` dependency as a Python namespace."""
        # flext-j47u (codex): FLEXT dependencies are first-party contracts even
        # when their uv source declaration is owned by an enclosing workspace.
        normalized = FlextInfraUtilitiesPyproject.validate_infra_payload(payload)
        return tuple(
            sorted(
                name.replace("-", "_")
                for name in cls.declared_dependency_names_from_payload(normalized)
                if name == "flext" or name.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesDependencies"]
