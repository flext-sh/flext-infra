"""Resolve uv source dependencies for FlextInfraExtraPathsManager."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, t, u

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraExtraPathsSourceMixin:
    """Mixin for pyrefly search paths backed by ``[tool.uv.sources]``."""

    if TYPE_CHECKING:
        _tool_config: m.Infra.ToolConfigDocument

    @staticmethod
    def _project_relative_path(*, project_dir: Path, target_dir: Path) -> str:
        """Return a pyrefly search-path entry relative to one project root."""
        return Path(os.path.relpath(target_dir, start=project_dir)).as_posix()

    def _uv_source_search_roots(self, source_root: Path) -> t.SequenceOf[Path]:
        """Return import roots for one path dependency source."""
        source_dir = (
            source_root / self._tool_config.tools.pyrefly.path_rules.source_dir
        )
        if source_dir.is_dir() and any(source_dir.rglob(c.Infra.EXT_PYTHON_GLOB)):
            return (source_dir,)
        skip_dirs = c.Infra.COMMON_EXCLUDED_DIRS | frozenset({c.Infra.DIR_TESTS})
        if u.Infra.discover_python_dirs(source_root, skip_dirs=skip_dirs) or any(
            source_root.glob(c.Infra.EXT_PYTHON_GLOB),
        ):
            return (source_root,)
        return ()

    def _uv_source_paths(
        self,
        payload: t.Infra.ContainerDict,
        *,
        project_dir: Path,
    ) -> t.StrSequence:
        """Resolve ``[tool.uv.sources]`` path/editable dependencies to source roots."""
        declared = set(u.Infra.declared_dependency_names_from_payload(payload))
        if not declared:
            return ()
        tool = u.Cli.json_as_mapping(payload.get(c.Infra.TOOL))
        uv = u.Cli.json_as_mapping(tool.get("uv"))
        sources = u.Cli.json_as_mapping(uv.get("sources"))
        if not sources:
            return ()
        resolved: t.MutableSequenceOf[str] = []
        seen: t.Infra.StrSet = set()
        for raw_name, raw_source in sources.items():
            dep_name = u.Infra.dep_name(raw_name)
            if dep_name is None or dep_name not in declared:
                continue
            source = u.Cli.json_as_mapping(raw_source)
            raw_path = source.get("path")
            if not isinstance(raw_path, str) or not raw_path.strip():
                continue
            source_root = Path(raw_path)
            if not source_root.is_absolute():
                source_root = project_dir / source_root
            if not source_root.is_dir():
                continue
            for source_search_root in self._uv_source_search_roots(source_root):
                search_path = self._project_relative_path(
                    project_dir=project_dir,
                    target_dir=source_search_root,
                )
                if search_path in seen:
                    continue
                seen.add(search_path)
                resolved.append(search_path)
        return tuple(resolved)


__all__: list[str] = ["FlextInfraExtraPathsSourceMixin"]
