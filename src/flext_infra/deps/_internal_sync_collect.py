"""Internal dependency collection — extracted concern of the internal sync service."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, p, r, t, u


class FlextInfraInternalSyncCollectMixin:
    """Collect internal path dependencies from pyproject metadata.

    Composed into FlextInfraInternalDependencySyncService via MRO; reads the
    target ``pyproject.toml`` through the repo mixin's ``_read_plain`` helper
    and resolves every internal ``.flext-deps`` path dependency.
    """

    if TYPE_CHECKING:
        # Provided by FlextInfraInternalSyncRepoMixin on the composed facade.
        def _read_plain(self, path: Path) -> p.Result[t.Infra.ContainerDict]: ...

    @staticmethod
    def resolve_internal_repo_name(raw_path: str) -> str | None:
        """Resolve repository name from internal path dependency notation."""
        normalized = raw_path.strip().removeprefix("./")
        if normalized.startswith(".flext-deps/"):
            return normalized.removeprefix(".flext-deps/")
        if normalized.startswith("../"):
            candidate = normalized.removeprefix("../")
            if candidate and "/" not in candidate:
                return candidate
        if normalized and "/" not in normalized and (normalized not in {".", ".."}):
            return normalized
        return None

    def collect_internal_deps(
        self, project_root: Path
    ) -> p.Result[t.MappingKV[str, Path]]:
        """Collect internal path dependencies from pyproject metadata."""
        pyproject = project_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[t.MappingKV[str, Path]].ok({})
        data_result = self._read_plain(pyproject)
        if data_result.failure:
            return r[t.MappingKV[str, Path]].fail(
                data_result.error or f"failed to read {pyproject}"
            )
        data = data_result.value
        deps = u.Cli.json_deep_mapping(
            data, c.Infra.TOOL, c.Infra.POETRY, c.Infra.DEPENDENCIES
        )
        result: MutableMapping[str, Path] = {}
        for dep_name, dep_value in deps.items():
            dep_value_map = u.Cli.json_as_mapping(dep_value)
            if not dep_value_map:
                continue
            dep_path = dep_value_map.get(c.Infra.PATH)
            if not isinstance(dep_path, str):
                continue
            repo_name = self.resolve_internal_repo_name(dep_path)
            if repo_name is None:
                continue
            result[dep_name] = project_root / ".flext-deps" / repo_name
        project_obj = u.Cli.json_deep_mapping(data, c.Infra.PROJECT)
        project_deps_raw = project_obj.get(c.Infra.DEPENDENCIES)
        project_deps: t.StrSequence = [
            str(item) for item in u.Cli.json_as_sequence(project_deps_raw)
        ]
        internal_dep_names: t.Infra.StrSet = set()
        for dep in project_deps:
            dep_name_match = c.Infra.DEP_NAME_RE.match(dep)
            if dep_name_match is not None:
                dep_name = dep_name_match.group(1)
                if (
                    dep_name.startswith(c.Infra.PKG_PREFIX_HYPHEN)
                    or dep_name == "flext"
                ):
                    internal_dep_names.add(dep_name)
            if " @ " not in dep:
                continue
            match = c.Infra.PEP621_PATH_RE.search(dep)
            if not match:
                continue
            repo_name = self.resolve_internal_repo_name(match.group("path"))
            if repo_name is None:
                continue
            _ = result.setdefault(repo_name, project_root / ".flext-deps" / repo_name)
        tool_obj = u.Cli.json_deep_mapping(data, c.Infra.TOOL)
        uv_obj = u.Cli.json_deep_mapping(tool_obj, "uv")
        sources_obj = u.Cli.json_deep_mapping(uv_obj, "sources")
        for dep_name in internal_dep_names:
            source_value = u.Cli.json_deep_mapping(sources_obj, dep_name)
            if not source_value:
                continue
            if source_value.get("workspace") is True:
                _ = result.setdefault(dep_name, project_root / ".flext-deps" / dep_name)
                continue
            source_path = source_value.get(c.Infra.PATH)
            if isinstance(source_path, str):
                repo_name = self.resolve_internal_repo_name(source_path)
                if repo_name is not None:
                    _ = result.setdefault(
                        repo_name, project_root / ".flext-deps" / repo_name
                    )
        return r[t.MappingKV[str, Path]].ok(result)


__all__: list[str] = ["FlextInfraInternalSyncCollectMixin"]
