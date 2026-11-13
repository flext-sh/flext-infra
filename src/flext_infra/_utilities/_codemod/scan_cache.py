"""Persistent two-level cache for ast-grep scans in gitignored storage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar

from flext_cli import u

from flext_infra import c
from flext_infra._utilities._codemod.native_cascade import (
    FlextInfraUtilitiesCodemodNativeCascade,
)
from flext_infra._utilities.iteration_directory import (
    FlextInfraUtilitiesIterationDirectory,
)


class FlextInfraCodemodScanCache:
    """Persistent two-level cache for ast-grep findings."""

    _version_cache: ClassVar[str | None] = None

    @staticmethod
    def ensure_safe_storage(directory: Path) -> Path:
        """Ensure the directory exists and contains a .gitignore file.

        Returns:
            The ensured safe storage directory path.

        """
        u.Cli.ensure_dir(directory).unwrap()
        gitignore = directory / ".gitignore"
        if not gitignore.is_file():
            gitignore.write_text("*\n!.gitignore\n", encoding=c.DEFAULT_ENCODING)
        return directory

    @classmethod
    def cache_directory(cls, root: Path) -> Path:
        """Return the gitignored persistent cache directory under .reports.

        Returns:
            Path to the persistent cache directory.

        """
        return cls.ensure_safe_storage(root / ".reports" / "ast-grep" / "cache")

    @classmethod
    def ast_grep_version(cls, root: Path) -> str:
        """Return ast-grep version string.

        Returns:
            The detected or cached version string.

        """
        if cls._version_cache is not None:
            return cls._version_cache
        del root
        binary = FlextInfraUtilitiesCodemodNativeCascade.codemod_tool_binary(
            c.Infra.SG
        )
        executed = u.Cli.run_raw((str(binary), "--version"))
        version = (executed.value.stdout if executed.ok else "").strip() or "0.51.0"
        cls._version_cache = version
        return version

    @staticmethod
    def sources_digest(root: Path, targets: Sequence[str]) -> str:
        """Compute deterministic SHA256 of all python files in targets.

        Returns:
            Hexdigest string of the sources digest.

        """
        hasher = hashlib.sha256()
        for target in sorted(targets):
            target_path = root / target
            if target_path.is_file():
                hasher.update(str(target).encode())
                hasher.update(hashlib.sha256(target_path.read_bytes()).digest())
            elif target_path.is_dir():
                for file_path in sorted(
                    FlextInfraUtilitiesIterationDirectory.iter_directory_python_files(
                        target_path, repository_root=root
                    )
                ):
                    hasher.update(file_path.relative_to(root).as_posix().encode())
                    hasher.update(hashlib.sha256(file_path.read_bytes()).digest())
        return hasher.hexdigest()

    @classmethod
    def cache_key(
        cls,
        root: Path,
        rules_digest: str,
        sources_digest: str,
        threads: int,
    ) -> str:
        """Build sha256 cache key including rules, sources, threads, version.

        Returns:
            The computed cache key hexdigest.

        """
        version = cls.ast_grep_version(root)
        payload = f"{rules_digest}:{sources_digest}:{threads}:{version}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @classmethod
    def get_cached_raw_output(cls, root: Path, key: str) -> Path | None:
        """Retrieve cached raw JSONL path if cache key file exists.

        Returns:
            Path to the cached JSONL file if present, None otherwise.

        """
        cache_file = cls.cache_directory(root) / f"{key}.jsonl"
        return cache_file if cache_file.is_file() else None

    @classmethod
    def put_cached_raw_output(cls, root: Path, key: str, source_path: Path) -> None:
        """Store raw JSONL output in cache atomically."""
        cache_dir = cls.cache_directory(root)
        cache_file = cache_dir / f"{key}.jsonl"
        u.Cli.atomic_write_text_file(
            cache_file, source_path.read_text(encoding=c.DEFAULT_ENCODING)
        ).unwrap()


__all__: list[str] = ["FlextInfraCodemodScanCache"]
