"""Installed and editable resource-root resolution for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path


class FlextInfraUtilitiesResources:
    """Resolve generated package data without depending on the process CWD."""

    @staticmethod
    def resource_root(name: str) -> Path:
        """Return one required resource root in installed or editable layout."""
        relative = Path(name)
        if relative.is_absolute() or len(relative.parts) != 1 or relative.name != name:
            msg = f"resource name must be one repository-root directory: {name}"
            raise ValueError(msg)
        package_root = Path(__file__).resolve().parent.parent
        # mro-qc84 (fix-forward): the project-root config/ is the canonical SSOT
        # (config-root-resolution law); a package-relative resource dir may exist
        # empty as a stray artifact, so require a non-empty directory and prefer
        # the first populated candidate.
        fallback: Path | None = None
        for candidate in (package_root / relative, package_root.parents[1] / relative):
            if candidate.is_dir():
                if any(candidate.iterdir()):
                    return candidate
                fallback = fallback or candidate
        if fallback is not None:
            return fallback
        msg = f"required flext-infra resource directory is missing: {name}"
        raise FileNotFoundError(msg)


__all__: list[str] = ["FlextInfraUtilitiesResources"]
