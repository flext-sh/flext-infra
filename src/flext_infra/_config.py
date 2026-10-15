"""Typed, frozen config singleton for flext-infra (ADR-005/U18).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_cli import FlextCliConfig

from flext_infra._models._config.base import FlextInfraConfigModels
from flext_infra._models._config.vocabulary import FlextInfraConfigVocabulary


class FlextInfraConfig(FlextCliConfig):
    """Declarative flext-infra config loaded and validated once."""

    # Direct config.Infra is the only codegen information surface; no accessor
    # method.
    Infra: FlextInfraConfigModels.Infra

    @classmethod
    def ssot_config_dir(cls) -> Path:
        """Public resolution of the packaged/workspace ``config/`` directory.

        Returns:
            The resulting ``Path``.

        """
        return cls._config_dir()

    @classmethod
    @override
    def _config_files(cls) -> list[Path]:
        """Elect the existing whole-namespace sources for the global singleton.

        Returns:
            The resulting ``list[Path]``.

        """
        project_directory = Path.cwd() / FlextInfraConfigVocabulary.CODEGEN_CONFIG_DIR
        user_directory = cls._user_config_dir()
        inherited = super()._config_files()
        reserved = {
            FlextInfraConfigVocabulary.CODEGEN_LOCAL_OVERRIDES_FILENAME,
            FlextInfraConfigVocabulary.CODEGEN_ORG_OVERRIDES_FILENAME,
        }
        files = [
            item
            for item in inherited
            if item.name not in reserved and not item.is_relative_to(user_directory)
        ]
        org = (
            project_directory
            / FlextInfraConfigVocabulary.CODEGEN_ORG_OVERRIDES_FILENAME
        )
        if org.is_file():
            files.append(org)
        files.extend(item for item in inherited if item.is_relative_to(user_directory))
        local = (
            project_directory
            / FlextInfraConfigVocabulary.CODEGEN_LOCAL_OVERRIDES_FILENAME
        )
        if local.is_file():
            files.append(local)
        return list(dict.fromkeys(files))

    @classmethod
    def config_sources_for_repository(
        cls,
        repository_root: Path,
        *,
        filename: str,
    ) -> tuple[Path, ...]:
        """Elect exactly the declared file's library, project and local layers.

        The target root and owned filename are injected. No current directory,
        filename ordering or another repository's overrides select a layer.

        Returns:
            Packaged F.yaml, target F.yaml and target F.local.yaml in that order.

        Raises:
            ValueError: If the filename is not one repository-local YAML file.
            FileNotFoundError: If the declared packaged default is absent.
        """
        candidates = cls.config_layer_paths_for_repository(
            repository_root,
            filename=filename,
        )
        library = candidates[0]
        if not library.is_file():
            msg = f"declared packaged config default is missing: {library}"
            raise FileNotFoundError(msg)
        for path in candidates:
            if path.exists() and not path.is_file():
                msg = f"declared config layer is not a regular file: {path}"
                raise ValueError(msg)
        return tuple(dict.fromkeys(path for path in candidates if path.is_file()))

    @classmethod
    def config_layer_paths_for_repository(
        cls,
        repository_root: Path,
        *,
        filename: str,
    ) -> tuple[Path, Path, Path]:
        """Declare ordered config destinations independently of file existence.

        Returns:
            The library, project and local paths used by both reading and migration.

        Raises:
            ValueError: If the root or owned YAML filename is not explicit.
        """
        relative = Path(filename)
        if (
            not repository_root.is_absolute()
            or relative.name != filename
            or relative.suffix != ".yaml"
        ):
            msg = f"config requires an absolute root and one YAML filename: {filename}"
            raise ValueError(msg)
        directory = repository_root / FlextInfraConfigVocabulary.CODEGEN_CONFIG_DIR
        library = cls.ssot_config_dir() / relative
        project = directory / relative
        if project.resolve() == library.resolve():
            project = directory / relative.with_name(f"{relative.stem}.project.yaml")
        return (
            library,
            project,
            directory / relative.with_name(f"{relative.stem}.local.yaml"),
        )


# The public singleton keeps its type through circular facade analysis.
config: FlextInfraConfig = FlextInfraConfig.fetch_global()
"""Pre-instantiated frozen config singleton — ``from flext_infra import config``."""
__all__: list[str] = ["FlextInfraConfig", "config"]
