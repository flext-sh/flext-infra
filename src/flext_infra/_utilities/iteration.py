"""Workspace Python file iteration helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import fnmatch
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from functools import cache
from pathlib import Path

from flext_cli import u
from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from tomlkit import TOMLDocument

from flext_infra import c, p, r, t


class FlextInfraUtilitiesIteration:
    """Static helpers for discovering and iterating Python projects in workspace.

    Core concept: A "project" is a directory with Makefile (or go.mod)
    AND at least one configured source directory (src/, tests/, examples/, scripts/).

    Used by: build orchestration, validation, and code generation tools.
    """

    @staticmethod
    def dep_name(requirement: str) -> str | None:
        """Extract normalized dependency name from one requirement spec."""
        text = requirement.strip()
        if not text:
            return None
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

    @staticmethod
    def _normalized_toml_payload(document: TOMLDocument) -> t.Infra.ContainerDict:
        """Return one TOML document normalized through the infra adapter."""
        payload = u.Cli.toml_as_mapping(document)
        if not payload:
            return {}
        try:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
        except c.ValidationError:
            return {}

    @staticmethod
    def dedupe_specs(specs: t.StrSequence) -> t.StrSequence:
        """Return deterministic unique dependency specs keyed by normalized name."""
        selected_by_name: dict[str, str] = {}
        for raw in specs:
            item = str(raw).strip()
            if not item:
                continue
            dependency_name = FlextInfraUtilitiesIteration.dep_name(item)
            if dependency_name is None or dependency_name in selected_by_name:
                continue
            selected_by_name[dependency_name] = item
        return tuple(selected_by_name[name] for name in sorted(selected_by_name))

    @classmethod
    def declared_dependency_names(cls, document: TOMLDocument) -> t.StrSequence:
        """Return normalized dependency names from one TOML document."""
        normalized = cls._normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.declared_dependency_names_from_payload(normalized)

    @classmethod
    def declared_dependency_names_from_payload(
        cls,
        payload: t.Infra.ContainerDict,
    ) -> t.StrSequence:
        """Return normalized dependency names across supported dependency tables."""
        names: set[str] = set()
        cls._append_project_dependency_names(payload=payload, names=names)
        cls._append_dependency_group_names(payload=payload, names=names)
        cls._append_poetry_dependency_names(payload=payload, names=names)
        return tuple(sorted(names))

    @classmethod
    def _append_project_dependency_names(
        cls,
        *,
        payload: t.Infra.ContainerDict,
        names: set[str],
    ) -> None:
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            return
        cls._append_requirement_names(
            raw_requirements=project.get(c.Infra.DEPENDENCIES),
            names=names,
        )
        optional_dependencies = project.get(c.Infra.OPTIONAL_DEPENDENCIES)
        if not isinstance(optional_dependencies, Mapping):
            return
        for raw_requirements in optional_dependencies.values():
            cls._append_requirement_names(
                raw_requirements=raw_requirements,
                names=names,
            )

    @classmethod
    def _append_dependency_group_names(
        cls,
        *,
        payload: t.Infra.ContainerDict,
        names: set[str],
    ) -> None:
        dependency_groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if not isinstance(dependency_groups, Mapping):
            return
        for raw_requirements in dependency_groups.values():
            cls._append_requirement_names(
                raw_requirements=raw_requirements,
                names=names,
            )

    @classmethod
    def _append_poetry_dependency_names(
        cls,
        *,
        payload: t.Infra.ContainerDict,
        names: set[str],
    ) -> None:
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, Mapping):
            return
        poetry = tool.get(c.Infra.POETRY)
        if not isinstance(poetry, Mapping):
            return
        cls._append_mapping_dependency_names(
            raw_mapping=poetry.get(c.Infra.DEPENDENCIES),
            names=names,
        )
        poetry_groups = poetry.get(c.Infra.GROUP)
        if not isinstance(poetry_groups, Mapping):
            return
        for raw_group in poetry_groups.values():
            if not isinstance(raw_group, Mapping):
                continue
            cls._append_mapping_dependency_names(
                raw_mapping=raw_group.get(c.Infra.DEPENDENCIES),
                names=names,
            )

    @classmethod
    def _append_requirement_names(
        cls,
        *,
        raw_requirements: t.Infra.InfraValue,
        names: set[str],
    ) -> None:
        if not isinstance(raw_requirements, list):
            return
        for raw_requirement in raw_requirements:
            dependency_name = cls.dep_name(str(raw_requirement))
            if dependency_name is None:
                continue
            names.add(dependency_name)

    @classmethod
    def _append_mapping_dependency_names(
        cls,
        *,
        raw_mapping: t.Infra.InfraValue,
        names: set[str],
    ) -> None:
        if not isinstance(raw_mapping, Mapping):
            return
        for raw_name in raw_mapping:
            dependency_name = cls.dep_name(str(raw_name))
            if dependency_name is None or dependency_name == "python":
                continue
            names.add(dependency_name)

    @classmethod
    def local_dependency_names_from_payload(
        cls,
        payload: t.Infra.ContainerDict,
        *,
        workspace_project_names: t.StrSequence = (),
    ) -> t.StrSequence:
        """Return workspace-local dependency names from one payload."""
        declared = set(cls.declared_dependency_names_from_payload(payload))
        if not workspace_project_names:
            return ()
        workspace_names = {str(name) for name in workspace_project_names}
        return tuple(sorted(name for name in declared if name in workspace_names))

    @staticmethod
    def project_dev_groups_from_payload(
        payload: t.Infra.ContainerDict,
    ) -> Mapping[str, t.StrSequence]:
        """Collect optional dependency groups from one normalized payload."""
        project = u.Cli.json_as_mapping(payload.get(c.Infra.PROJECT, None))
        optional = u.Cli.json_as_mapping(
            project.get(c.Infra.OPTIONAL_DEPENDENCIES, None),
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
        cls,
        document: TOMLDocument,
    ) -> Mapping[str, t.StrSequence]:
        """Collect optional dependency groups from one TOML document."""
        normalized = cls._normalized_toml_payload(document)
        if not normalized:
            return {}
        return cls.project_dev_groups_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies(
        cls,
        document: TOMLDocument,
    ) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one TOML document."""
        normalized = cls._normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.canonical_dev_dependencies_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies_from_payload(
        cls,
        payload: t.Infra.ContainerDict,
    ) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one normalized payload."""
        groups = cls.project_dev_groups_from_payload(payload)
        return cls.dedupe_specs([
            requirement
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
            for requirement in groups.get(str(group), ())
        ])

    @classmethod
    def workspace_dep_namespaces(
        cls,
        document: TOMLDocument,
    ) -> t.StrSequence:
        """Extract workspace-local dependency namespaces from one TOML document."""
        normalized = cls._normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.workspace_dep_namespaces_from_payload(normalized)

    @classmethod
    def workspace_dep_namespaces_from_payload(
        cls,
        payload: Mapping[str, t.Infra.InfraValue],
    ) -> t.StrSequence:
        """Extract workspace-local dependency namespaces from one normalized payload."""
        try:
            normalized = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
        except c.ValidationError:
            return ()
        tool = normalized.get(c.Infra.TOOL)
        if not isinstance(tool, Mapping):
            return ()
        uv = tool.get("uv")
        if not isinstance(uv, Mapping):
            return ()
        sources = uv.get("sources")
        if not isinstance(sources, Mapping):
            return ()
        workspace_project_names = tuple(
            dependency_name
            for raw_name, raw_source in sources.items()
            if isinstance(raw_source, Mapping)
            if raw_source.get("workspace") is True
            if (dependency_name := cls.dep_name(str(raw_name))) is not None
        )
        if not workspace_project_names:
            return ()
        return tuple(
            sorted(
                dependency_name.replace("-", "_")
                for dependency_name in cls.local_dependency_names_from_payload(
                    normalized,
                    workspace_project_names=workspace_project_names,
                )
            )
        )

    @staticmethod
    @cache
    def pyproject_payload(
        pyproject_path: Path,
    ) -> t.Infra.ContainerDict:
        """Return one parsed ``pyproject.toml`` payload validated against ``t.Infra``.

        Disk read is delegated to ``u.Cli.toml_read_json`` (cached at
        flext-cli utility layer); this method caches the validated typed payload.
        ``pyproject_path`` is the file path; ``Path`` is the canonical
        cache key (no ``str(...)`` proxy round-trip).
        """
        if not pyproject_path.is_file():
            return {}
        payload_result = u.Cli.toml_read_json(pyproject_path)
        if payload_result.failure:
            return {}
        try:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload_result.value)
        except ValueError:
            return {}

    @staticmethod
    def _tool_flext_meta(
        project_root: Path,
    ) -> t.Infra.ContainerDict:
        """Return the normalized ``tool.flext`` table from a project root."""
        payload = FlextInfraUtilitiesIteration.pyproject_payload(
            project_root / c.Infra.PYPROJECT_FILENAME,
        )
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        return flext if isinstance(flext, dict) else {}

    @staticmethod
    @cache
    def workspace_member_names(workspace_root: Path) -> t.StrSequence:
        """Return configured workspace members from ``[tool.flext.workspace]`` or ``[tool.uv.workspace]``.

        Cached by ``workspace_root`` (``Path`` is hashable). Both
        ``[tool.flext.workspace] members`` and ``[tool.uv.workspace] members``
        are honoured (first non-empty wins).
        """
        pyproject_path = workspace_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject_path.is_file():
            return ()
        payload = FlextInfraUtilitiesIteration.pyproject_payload(pyproject_path)
        if not payload:
            return ()
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return ()
        for tool_name in ("flext", "uv"):
            tool_config = tool.get(tool_name)
            if not isinstance(tool_config, dict):
                continue
            workspace_config = tool_config.get("workspace")
            if not isinstance(workspace_config, dict):
                continue
            members = workspace_config.get("members")
            if not isinstance(members, list):
                continue
            normalized = tuple(
                member_name for item in members if (member_name := str(item).strip())
            )
            if normalized:
                return normalized
        return ()

    @staticmethod
    def namespace_meta(project_root: Path) -> t.Infra.ContainerDict:
        """Return optional ``tool.flext.namespace`` metadata for one project."""
        flext_meta = FlextInfraUtilitiesIteration._tool_flext_meta(project_root)
        namespace = flext_meta.get("namespace")
        return namespace if isinstance(namespace, dict) else {}

    @staticmethod
    def namespace_enabled(project_root: Path) -> bool:
        """Return whether namespace enforcement is enabled for a project."""
        enabled = FlextInfraUtilitiesIteration.namespace_meta(project_root).get(
            "enabled",
            True,
        )
        return enabled if isinstance(enabled, bool) else True

    @staticmethod
    def namespace_scan_dirs(project_root: Path) -> frozenset[str]:
        """Return configured scan dirs for namespace enforcement."""
        configured = FlextInfraUtilitiesIteration.namespace_meta(project_root).get(
            "scan_dirs",
        )
        if isinstance(configured, list):
            normalized = frozenset(
                str(item).strip() for item in configured if str(item).strip()
            )
            if normalized:
                return normalized
        return frozenset(c.Infra.MRO_SCAN_DIRECTORIES)

    @staticmethod
    def namespace_include_dynamic_dirs(project_root: Path) -> bool:
        """Return whether namespace enforcement should scan non-canonical dirs."""
        include_dynamic_dirs = FlextInfraUtilitiesIteration.namespace_meta(
            project_root,
        ).get("include_dynamic_dirs")
        return include_dynamic_dirs if isinstance(include_dynamic_dirs, bool) else False

    @staticmethod
    @cache
    def _git_tracked_scope_relative_paths(scope_root: str) -> tuple[str, ...] | None:
        """Return tracked file paths relative to one scope or ``None`` outside Git."""
        resolved_root = Path(scope_root)
        try:
            repo = Repo(resolved_root, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError, OSError, ValueError):
            return None
        if repo.bare or repo.working_tree_dir is None:
            return None
        repo_root = Path(repo.working_tree_dir).resolve()
        try:
            scope_prefix = resolved_root.resolve().relative_to(repo_root)
        except ValueError:
            return None
        scope_prefix_text = "" if not scope_prefix.parts else scope_prefix.as_posix()
        prefix_with_sep = f"{scope_prefix_text}/" if scope_prefix_text else ""
        normalized: set[str] = set()
        for tracked_path, _stage in repo.index.entries:
            path_text = str(Path(tracked_path).as_posix())
            if not path_text:
                continue
            if prefix_with_sep:
                if not path_text.startswith(prefix_with_sep):
                    continue
                relative_path = path_text[len(prefix_with_sep) :]
            else:
                relative_path = path_text
            if relative_path:
                normalized.add(relative_path)
        return tuple(sorted(normalized))

    @classmethod
    def _git_tracked_scope_paths(cls, scope_root: Path) -> Sequence[Path] | None:
        """Return tracked files under one scope as absolute paths when Git is active."""
        resolved_root = scope_root.resolve()
        relative_paths = cls._git_tracked_scope_relative_paths(str(resolved_root))
        if relative_paths is None:
            return None
        return [
            resolved_root / Path(relative_path)
            for relative_path in relative_paths
            if (resolved_root / Path(relative_path)).is_file()
        ]

    @classmethod
    def _git_tracked_top_level_dir_names(
        cls,
        scope_root: Path,
    ) -> frozenset[str] | None:
        """Return tracked top-level directory names under one scope when Git is active."""
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(scope_root.resolve())
        )
        if relative_paths is None:
            return None
        return frozenset(
            relative.parts[0]
            for relative_path in relative_paths
            if (relative := Path(relative_path)).parts
        )

    @classmethod
    def _project_descriptor_is_tracked(
        cls,
        workspace_root: Path,
        project_root: Path,
    ) -> bool:
        """Return whether one candidate project has a tracked descriptor file."""
        relative_paths = cls._git_tracked_scope_relative_paths(
            str(workspace_root.resolve()),
        )
        if relative_paths is None:
            return True
        tracked_paths = frozenset(relative_paths)
        resolved_workspace = workspace_root.resolve()
        resolved_project = project_root.resolve()
        relative_prefix = ""
        if resolved_project != resolved_workspace:
            relative_prefix = (
                resolved_project.relative_to(resolved_workspace).as_posix() + "/"
            )
        tracked_gitlink = relative_prefix.removesuffix("/")
        if tracked_gitlink and tracked_gitlink in tracked_paths:
            return True
        return any(
            f"{relative_prefix}{filename}" in tracked_paths
            for filename in (c.Infra.PYPROJECT_FILENAME, c.Infra.GO_MOD)
        )

    @classmethod
    def iter_matching_files(
        cls,
        root: Path,
        *,
        includes: t.StrSequence,
        excludes: t.StrSequence = (),
    ) -> Sequence[Path]:
        """Return files in one scope through the canonical git-aware selection path."""
        if not root.is_dir():
            return []
        tracked_files = cls._git_tracked_scope_paths(root)
        candidates = (
            tracked_files
            if tracked_files is not None
            else [path for path in root.rglob("*") if path.is_file()]
        )
        return sorted(
            {
                path
                for path in candidates
                if path.is_file()
                if (
                    not includes
                    or any(
                        fnmatch.fnmatch(path.relative_to(root).as_posix(), pattern)
                        for pattern in includes
                    )
                )
                if not any(
                    fnmatch.fnmatch(path.relative_to(root).as_posix(), pattern)
                    for pattern in excludes
                )
            },
        )

    @staticmethod
    def discover_project_roots(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
    ) -> Sequence[Path]:
        """Discover all project directories under workspace root.

        Algorithm:
          1. Check if workspace_root itself looks like a project
          2. Scan immediate children for project-like directories
          3. Return sorted list, or fallback to [workspace_root] if has src/

        The fallback handles workspaces where all code is in workspace_root/src
        rather than organized into subdirectory projects.

        Args:
            workspace_root: Root directory to start search from.
            scan_dirs: Directory names indicating a project exists (e.g., "src", "tests").
                Must be frozenset for use as constant. Defaults to standard project dirs.

        Returns:
            List of project root paths sorted by name.
            Includes workspace_root itself if it looks like a project.
            At minimum returns [workspace_root] if workspace_root/src/ exists.

        """
        configured_members = FlextInfraUtilitiesIteration.workspace_member_names(
            workspace_root,
        )
        candidates = FlextInfraUtilitiesIteration.discover_project_candidates(
            workspace_root,
            scan_dirs=scan_dirs,
        )
        if configured_members:
            configured_order = {
                name: idx for idx, name in enumerate(configured_members)
            }
            non_root_candidates = [
                candidate for candidate in candidates if candidate != workspace_root
            ]
            if non_root_candidates:
                return sorted(
                    non_root_candidates,
                    key=lambda candidate: configured_order.get(
                        candidate.name, len(configured_members)
                    ),
                )
        return candidates

    @staticmethod
    def _looks_like_project(
        path: Path,
        *,
        effective_scan_dirs: frozenset[str],
        configured_member_set: frozenset[str],
    ) -> bool:
        """Return whether one path matches the canonical governed project shape."""
        if not path.is_dir():
            return False
        pyproject_path = path / c.Infra.PYPROJECT_FILENAME
        go_mod_path = path / c.Infra.GO_MOD
        if not pyproject_path.exists() and not go_mod_path.exists():
            return False
        if go_mod_path.exists():
            return any((path / dir_name).is_dir() for dir_name in effective_scan_dirs)
        if path.name in configured_member_set:
            return True
        if (path / c.Infra.MAKEFILE_FILENAME).exists():
            return True
        payload = FlextInfraUtilitiesIteration.pyproject_payload(pyproject_path)
        if not payload:
            return False
        dependency_names: set[str] = set(
            FlextInfraUtilitiesIteration.declared_dependency_names_from_payload(
                payload,
            )
        )
        if c.Infra.PKG_CORE in dependency_names:
            return True
        return any((path / dir_name).is_dir() for dir_name in effective_scan_dirs)

    @staticmethod
    def _attached_top_level_dir_names(scope_root: Path) -> frozenset[str]:
        """Return top-level dir names whose pyproject opts in via ``[tool.flext.workspace] attached = true``.

        Reads each candidate's ``pyproject.toml`` through the canonical
        ``u.read_tool_flext_config`` helper from flext-core; the typed
        ``ProjectToolFlextWorkspace`` model enforces the contract. Sub-repos
        without a pyproject or whose ``[tool.flext.workspace]`` table is
        absent / ``attached = false`` are not surfaced.
        """
        attached: list[str] = []
        for entry in sorted(scope_root.iterdir(), key=lambda item: item.name):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            if not (entry / c.Infra.PYPROJECT_FILENAME).is_file():
                continue
            try:
                cfg = u.read_tool_flext_config(entry)
            except (OSError, ValueError):
                # OSError covers FileNotFoundError; ValueError covers
                # tomllib.TOMLDecodeError and pydantic.ValidationError.
                continue
            if cfg.workspace.attached:
                attached.append(entry.name)
        return frozenset(attached)

    @staticmethod
    def discover_project_candidates(
        workspace_root: Path,
        *,
        scan_dirs: frozenset[str] | None = None,
        include_attached: bool = False,
    ) -> Sequence[Path]:
        """Return all canonical project candidates before any consumer-specific filtering.

        When ``include_attached`` is True, sub-repos whose own ``pyproject.toml``
        carries ``[tool.flext.workspace] attached = true`` are surfaced
        alongside the git-tracked dirs of ``workspace_root``. Default (False)
        preserves the previous workspace-only enumeration.
        """
        roots: MutableSequence[Path] = []
        effective_scan_dirs = scan_dirs or frozenset(c.Infra.MRO_SCAN_DIRECTORIES)
        configured_members = FlextInfraUtilitiesIteration.workspace_member_names(
            workspace_root,
        )
        configured_member_set = frozenset(configured_members)
        resolved_workspace_root = workspace_root.resolve()
        tracked_child_dirs = (
            FlextInfraUtilitiesIteration._git_tracked_top_level_dir_names(
                resolved_workspace_root,
            )
        )
        attached_child_dirs = (
            FlextInfraUtilitiesIteration._attached_top_level_dir_names(
                resolved_workspace_root,
            )
            if include_attached
            else frozenset()
        )

        if FlextInfraUtilitiesIteration._looks_like_project(
            resolved_workspace_root,
            effective_scan_dirs=effective_scan_dirs,
            configured_member_set=configured_member_set,
        ) and FlextInfraUtilitiesIteration._project_descriptor_is_tracked(
            resolved_workspace_root,
            resolved_workspace_root,
        ):
            roots.append(resolved_workspace_root)
        if tracked_child_dirs is None and not attached_child_dirs:
            candidate_entries: Sequence[Path] = sorted(
                workspace_root.iterdir(),
                key=lambda item: item.name,
            )
        else:
            candidate_entries = [
                resolved_workspace_root / dir_name
                for dir_name in sorted(
                    frozenset(tracked_child_dirs or ()) | attached_child_dirs,
                )
            ]
        roots.extend(
            [
                entry.resolve()
                for entry in candidate_entries
                if entry.is_dir()
                and (not entry.name.startswith("."))
                and (
                    entry.name in attached_child_dirs
                    or FlextInfraUtilitiesIteration._project_descriptor_is_tracked(
                        resolved_workspace_root,
                        entry.resolve(),
                    )
                )
                and FlextInfraUtilitiesIteration._looks_like_project(
                    entry.resolve(),
                    effective_scan_dirs=effective_scan_dirs,
                    configured_member_set=configured_member_set,
                )
            ],
        )
        if not roots and (resolved_workspace_root / c.Infra.DEFAULT_SRC_DIR).is_dir():
            return [resolved_workspace_root]
        return roots

    @staticmethod
    def iter_directory_python_files(
        directory: Path,
        *,
        pattern: str | None = None,
        skip_pycache: bool = True,
    ) -> Sequence[Path]:
        """Iterate Python files in a single directory tree.

        Scoped to one directory (project src, subdirectory, etc.) — unlike
        ``iter_python_files`` which discovers across the whole workspace.

        Args:
            directory: Root directory to scan.
            pattern: Glob pattern (defaults to ``*.py``).
            skip_pycache: Exclude ``__pycache__`` paths (default True).

        Returns:
            Sorted list of matching file paths. Empty list if directory
            does not exist.

        """
        if not directory.is_dir():
            return []
        effective_pattern = pattern or c.Infra.EXT_PYTHON_GLOB
        tracked_files = FlextInfraUtilitiesIteration._git_tracked_scope_paths(directory)
        files = (
            sorted(directory.rglob(effective_pattern))
            if tracked_files is None
            else [
                file_path
                for file_path in tracked_files
                if fnmatch.fnmatch(
                    file_path.relative_to(directory).as_posix(),
                    effective_pattern,
                )
            ]
        )
        ignored_parts = (
            c.Infra.ITERATION_EXCLUDED_PARTS
            if skip_pycache
            else c.Infra.ITERATION_EXCLUDED_PARTS - {c.Infra.DUNDER_PYCACHE}
        )
        return [
            file_path
            for file_path in files
            if FlextInfraUtilitiesIteration.matches_canonical_python_file(file_path)
            if not FlextInfraUtilitiesIteration._is_ignored_python_path(
                file_path,
                ignored_parts=ignored_parts,
            )
        ]

    @staticmethod
    def matches_canonical_python_file(path: Path) -> bool:
        """Return True only for real ``.py`` source files."""
        return (
            path.is_file()
            and path.suffix == c.Infra.EXT_PYTHON
            and path.suffixes == [c.Infra.EXT_PYTHON]
        )

    @staticmethod
    def _is_ignored_python_path(
        path: Path,
        *,
        ignored_parts: frozenset[str] | None = None,
    ) -> bool:
        """Return whether a Python path lives under an ignored directory tree."""
        effective_ignored_parts = ignored_parts or c.Infra.ITERATION_EXCLUDED_PARTS
        return any(
            part in effective_ignored_parts
            or (part.startswith(".") and part not in {".", ".."})
            for part in path.parts
        )

    @classmethod
    def iter_python_files(
        cls,
        workspace_root: Path,
        *,
        project_roots: Sequence[Path] | None = None,
        include_tests: bool = True,
        include_examples: bool = True,
        include_scripts: bool = True,
        include_dynamic_dirs: bool = True,
        src_dirs: frozenset[str] | None = None,
    ) -> p.Result[Sequence[Path]]:
        """Discover and iterate all Python files across workspace projects.

        Args:
            workspace_root: Workspace root to discover from.
            project_roots: Pre-discovered project paths to skip discovery phase.
                Useful for caching results across multiple calls.
            include_tests: Include tests/ directories (default True).
            include_examples: Include examples/ directories (default True).
            include_scripts: Include scripts/ directories (default True).
            src_dirs: Which subdirectories to scan. Defaults to standard locations.
                src/ is always included regardless of include_* flags.

        Returns:
            Result[Sequence[Path]] - Success contains sorted unique file paths.
            Failure if: workspace inaccessible, discovery fails, or OSError.

        """
        try:
            roots = project_roots or cls.discover_project_roots(
                workspace_root=workspace_root,
            )
            selected_dirs = src_dirs or frozenset(
                {
                    c.Infra.DEFAULT_SRC_DIR,
                    c.Infra.DIR_TESTS,
                    c.Infra.DIR_EXAMPLES,
                    c.Infra.DIR_SCRIPTS,
                },
            )
            include_flags = {
                c.Infra.DEFAULT_SRC_DIR: True,
                c.Infra.DIR_TESTS: include_tests,
                c.Infra.DIR_EXAMPLES: include_examples,
                c.Infra.DIR_SCRIPTS: include_scripts,
            }
            files: MutableSequence[Path] = []
            for project_root in roots:
                cls._iter_known_dirs(
                    project_root,
                    include_flags,
                    selected_dirs,
                    files,
                )
                if include_dynamic_dirs:
                    cls._iter_dynamic_dirs(
                        project_root,
                        files,
                    )
            return r[Sequence[Path]].ok(sorted(set(files)))
        except OSError as exc:
            return r[Sequence[Path]].fail(f"python file iteration failed: {exc}")

    @staticmethod
    def _iter_known_dirs(
        project_root: Path,
        include_flags: t.BoolMapping,
        selected_dirs: frozenset[str],
        files: MutableSequence[Path],
    ) -> None:
        """Collect Python files from known project directories (src, tests, etc.)."""
        for dir_name, enabled in include_flags.items():
            if (not enabled) or (dir_name not in selected_dirs):
                continue
            directory = project_root / dir_name
            if directory.is_dir():
                files.extend(
                    FlextInfraUtilitiesIteration.iter_directory_python_files(
                        directory,
                    ),
                )

    @staticmethod
    def _iter_dynamic_dirs(
        project_root: Path,
        files: MutableSequence[Path],
    ) -> None:
        """Discover additional directories with Python files (docs/, tools/, etc.)."""
        tracked_dir_names = (
            FlextInfraUtilitiesIteration._git_tracked_top_level_dir_names(
                project_root,
            )
        )
        for subdir in project_root.iterdir():
            if not subdir.is_dir():
                continue
            dir_name = subdir.name
            if dir_name in frozenset(c.Infra.MRO_SCAN_DIRECTORIES):
                continue
            if dir_name.startswith("."):
                continue
            if tracked_dir_names is not None and dir_name not in tracked_dir_names:
                continue
            py_files = FlextInfraUtilitiesIteration.iter_directory_python_files(
                subdir,
            )
            if py_files:
                files.extend(py_files)

    @staticmethod
    def iter_workspace_python_modules(
        workspace_root: Path,
        *,
        exclude_packages: frozenset[str] | None = None,
        include_tests: bool = True,
    ) -> p.Result[Sequence[t.Pair[Path, Path]]]:
        """Discover all Python modules across workspace projects.

        Returns tuples of (project_root, file_path) for every Python file
        found in the workspace. Optionally excludes packages by name and
        can skip test directories.

        Args:
            workspace_root: Root directory of the workspace.
            exclude_packages: Project directory names to exclude.
            include_tests: Whether to include files under tests/ dirs.

        Returns:
            Result containing list of (project_root, file_path) tuples.

        """
        try:
            roots = FlextInfraUtilitiesIteration.discover_project_roots(
                workspace_root=workspace_root,
            )
            effective_exclude = exclude_packages or frozenset()
            result: MutableSequence[t.Pair[Path, Path]] = []
            for project_root in roots:
                if project_root.name in effective_exclude:
                    continue
                files_result = FlextInfraUtilitiesIteration.iter_python_files(
                    workspace_root=workspace_root,
                    project_roots=[project_root],
                    include_tests=include_tests,
                )
                if files_result.failure:
                    continue
                result.extend(
                    (project_root, file_path) for file_path in files_result.value
                )
            return r[Sequence[t.Pair[Path, Path]]].ok(result)
        except OSError as exc:
            return r[Sequence[t.Pair[Path, Path]]].fail(
                f"workspace python module iteration failed: {exc}",
            )

    @staticmethod
    def resolve_project_root(file_path: Path) -> Path | None:
        """Walk up from file_path to find the project root containing pyproject.toml."""
        current = file_path.parent
        for _ in range(10):
            if (current / c.Infra.PYPROJECT_FILENAME).is_file():
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None


__all__: list[str] = ["FlextInfraUtilitiesIteration"]
