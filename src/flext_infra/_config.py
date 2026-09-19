"""Typed, frozen config singleton for flext-infra (ADR-005/U18).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_cli.config import FlextCliConfig

from ._models._config.base import FlextInfraConfigModels


class FlextInfraConfig(FlextCliConfig):
    """Declarative flext-infra config loaded and validated once."""

    # NOTE (multi-agent, flext-wkii.9 + flext-wkii.17 / agent: codex): direct
    # config.Infra is the only codegen information surface; no accessor method.
    # NOTE (flext-sltx): CONFIG_DIR stays the relative default so
    # flext-core FlextConfig._config_dir() resolves the packaged flext_infra/config
    # in a wheel install AND the repo-root config/ in an editable source checkout.
    # An absolute parents[2] value broke every git-dep/wheel consumer (config poison).
    CONFIG_DIR: ClassVar[str] = "config"
    Infra: FlextInfraConfigModels.Infra

    @classmethod
    def ssot_config_dir(cls) -> Path:
        """Public resolution of the packaged/workspace ``config/`` directory."""
        return cls._config_dir()

    LOCAL_OVERRIDES_FILENAME: ClassVar[str] = "codegen-overrides.local.yaml"
    """Optional gitignored per-clone override file, merged after every tracked config.

    Operator-private values (project overrides, CI submodule credentials) that
    must never be committed to this public repository are declared here
    instead. The file goes through the exact tracked-file pipeline — strict
    duplicate-key loader, deep merge with list concatenation, full model
    validation — and merges last, so its scalars win and its dict entries
    (e.g. ``ci_private_submodules``, ``project_overrides``) add cleanly beside
    the public ones. Read once when the config singleton is first fetched; an
    absent file is a no-op.
    """

    ORG_OVERRIDES_FILENAME: ClassVar[str] = "codegen-org.yaml"
    """Tracked org-layer declarations of the repository being governed.

    A private organization that consumes this generator declares its own doc
    checkouts in ``config/codegen-org.yaml`` at the root of ITS repository —
    org data is allowed there because the file is tracked by the org's own
    (private) repository, never by this public one. The generator merges it
    when invoked from that repository root (the generated Makefiles always run
    there, so CI resolves the same values local runs do). Same strict
    pipeline; merged after the operator's local file; absent file is a no-op.
    Provider identity is never declared here: it is detected from each
    repository's own ``config/workspace.yaml`` and dependency declarations.
    """

    @classmethod
    @override
    def _config_files(cls) -> list[Path]:
        """Tracked configs and operator overlays first, the local file last.

        The sorted glob would discover the local override file in first
        position (``.local`` sorts before ``.yaml``), where it would lose
        every scalar collision; it is filtered out of the discovered set and
        appended explicitly exactly once so it merges with the highest
        precedence of any file source.
        """
        files = [
            item
            for item in super()._config_files()
            if item.name != cls.LOCAL_OVERRIDES_FILENAME
        ]
        local = cls._config_dir() / cls.LOCAL_OVERRIDES_FILENAME
        if local.is_file():
            files.append(local)
        org = Path.cwd() / cls.CONFIG_DIR / cls.ORG_OVERRIDES_FILENAME
        if org.is_file():
            files.append(org)
        return files


config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""

__all__: list[str] = ["FlextInfraConfig", "config"]
