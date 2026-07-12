"""Pyproject.toml parsing helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra.constants import c
from flext_infra.typings import t

if TYPE_CHECKING:
    from tomlkit import TOMLDocument


def _validate_infra_payload(payload: object) -> t.Infra.ContainerDict | None:
    """Validate one plain mapping through the infra adapter.

    Centralizes the repeated try/except so callers only decide what sentinel
    to surface on failure.
    """
    try:
        return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(payload)
    except (c.ValidationError, ValueError):
        return None


class FlextInfraUtilitiesPyproject:
    """Static helpers for reading and normalizing ``pyproject.toml`` payloads."""

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
        validated = _validate_infra_payload(payload_result.value)
        return validated if validated is not None else {}

    @staticmethod
    def normalized_toml_payload(document: TOMLDocument) -> t.Infra.ContainerDict:
        """Return one TOML document normalized through the infra adapter."""
        payload = u.Cli.toml_as_mapping(document)
        if not payload:
            return {}
        validated = _validate_infra_payload(payload)
        return validated if validated is not None else {}

    @staticmethod
    def tool_flext_meta(
        project_root: Path,
    ) -> t.Infra.ContainerDict:
        """Return the normalized ``tool.flext`` table from a project root."""
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(
            project_root / c.Infra.PYPROJECT_FILENAME,
        )
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        return flext if isinstance(flext, dict) else {}

    @staticmethod
    def docs_meta_from_payload(
        payload: t.Infra.ContainerDict,
    ) -> t.Infra.ContainerDict:
        """Extract ``tool.flext.docs`` metadata from an already-parsed payload."""
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, dict):
            return {}
        flext = tool.get("flext")
        if not isinstance(flext, dict):
            return {}
        docs = flext.get("docs")
        return docs if isinstance(docs, dict) else {}

    @staticmethod
    def project_name_from_payload(
        entry: Path,
        payload: t.Infra.ContainerDict,
    ) -> str:
        """Return the declared project name from ``[project].name``."""
        project_section = payload.get("project")
        if not isinstance(project_section, dict):
            msg = f"{entry}: missing [project] table in pyproject.toml"
            raise TypeError(msg)
        raw_name = project_section.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            msg = f"{entry}: missing or empty [project].name in pyproject.toml"
            raise ValueError(msg)
        return raw_name.strip()

    @staticmethod
    def package_name_from_payload(
        project_root: Path,
        payload: t.Infra.ContainerDict,
        docs_meta: t.Infra.ContainerDict,
    ) -> str:
        """Return the primary package name using pre-loaded pyproject payload."""
        configured = docs_meta.get("package_name")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        current: t.Infra.ContainerDict | None = payload
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            if current is None:
                break
            candidate = current.get(key)
            current = candidate if isinstance(candidate, dict) else None
        packages = current.get("packages") if current is not None else None
        if isinstance(packages, list):
            for item in packages:
                package_path = Path(str(item).strip())
                if package_path.parts:
                    package_parts: tuple[str, ...] = package_path.parts
                    return package_parts[-1]
        src_dir = project_root / c.Infra.DEFAULT_SRC_DIR
        if src_dir.is_dir():
            for child in sorted(src_dir.iterdir()):
                if child.is_dir() and (child / c.Infra.INIT_PY).is_file():
                    child_path: Path = child
                    return child_path.name
        project_name = FlextInfraUtilitiesPyproject.project_name_from_payload(
            project_root,
            payload,
        )
        if project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN):
            msg = (
                f"{project_root}: cannot resolve package name — "
                "no [tool.flext.docs].package_name, no hatch wheel packages, "
                "and no src/<pkg>/__init__.py present"
            )
            raise ValueError(msg)
        return ""

    @staticmethod
    def project_package_name(project_root: Path) -> str:
        """Return the primary Python package name for a project root."""
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(
            project_root / c.Infra.PYPROJECT_FILENAME,
        )
        docs_meta = FlextInfraUtilitiesPyproject.docs_meta_from_payload(payload)
        return FlextInfraUtilitiesPyproject.package_name_from_payload(
            project_root,
            payload,
            docs_meta,
        )

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
        payload = FlextInfraUtilitiesPyproject.pyproject_payload(pyproject_path)
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


__all__: list[str] = [
    "FlextInfraUtilitiesPyproject",
    "_validate_infra_payload",
]
