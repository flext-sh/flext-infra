"""Validated external tool cache locations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, p, settings


class FlextInfraUtilitiesResourceLimits:
    """Resolve the declared shared caches of the quality tools."""

    @staticmethod
    def ruff_cache_directory() -> Path:
        """Resolve the one Ruff cache every checkout shares.

        Ruff keys its own entries by version and package root inside the
        directory, so no FLEXT namespace is added on top of it.

        Returns:
            The declared external Ruff cache directory.

        """
        return FlextInfraUtilitiesResourceLimits.external_cache_directory(
            config.Infra.codegen.make.ruff_cache,
        )

    @staticmethod
    def external_cache_directory(
        spec: p.Infra.ExternalCacheDirectory,
    ) -> Path:
        """Resolve one declared FLEXT cache below the XDG cache home.

        Returns:
            ``$XDG_CACHE_HOME`` (or ``$HOME`` plus the home cache directory)
            joined with the spec's FLEXT-owned storage directory.

        """
        home = settings.env_lookup(spec.data_home_environment_variable) or str(
            Path(settings.env_required(spec.user_home_environment_variable))
            / spec.home_cache_directory,
        )
        return Path(home) / spec.external_storage_directory


__all__: list[str] = ["FlextInfraUtilitiesResourceLimits"]
