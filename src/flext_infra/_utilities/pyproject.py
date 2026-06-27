"""Pyproject.toml parsing helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from tomlkit import TOMLDocument

from flext_cli import u
from flext_infra import c, t


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
