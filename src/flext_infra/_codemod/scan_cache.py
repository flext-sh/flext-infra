"""Persistent hierarchical scan cache for ast-grep.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from pathlib import Path

from flext_infra import c, p, settings, u

_AST_GREP_VERSION = "0.51.0"


class FlextInfraCodemodScanCache:
    """Persistent content-addressed cache for ast-grep scan results."""

    @classmethod
    def cache_directory(cls) -> Path:
        """Return the directory where scan caches are stored.

        Returns:
            The authenticated cache directory path.

        """
        path = settings.work_dir / "ast-grep" / "cache"
        u.Cli.ensure_dir(path).unwrap()
        return path

    @classmethod
    def compute_key(
        cls,
        *,
        config_path: Path,
        rule_ids: Sequence[str] = (),
        targets: Sequence[str] = (),
        sources: Sequence[p.Cli.AtomicFileState] = (),
        options: tuple[str, int | None] = ("scan", None),
    ) -> str:
        """Compute a deterministic SHA256 cache key from scan inputs.

        Returns:
            The hex digest representing this exact scan state.

        Raises:
            ValueError: If an atomic file state carries no content.

        """
        prefix, threads = options
        hasher = hashlib.sha256()
        hasher.update(prefix.encode())
        hasher.update(b"\x00")
        hasher.update(_AST_GREP_VERSION.encode())
        hasher.update(b"\x00")
        hasher.update(str(threads or 0).encode())
        hasher.update(b"\x00")

        if config_path.is_file():
            hasher.update(config_path.read_bytes())
        else:
            hasher.update(str(config_path).encode())
        hasher.update(b"\x00")

        for rule_id in sorted(rule_ids):
            hasher.update(rule_id.encode())
            hasher.update(b",")
        hasher.update(b"\x00")

        for target in sorted(targets):
            hasher.update(target.encode())
            hasher.update(b",")
        hasher.update(b"\x00")

        for source in sorted(sources, key=lambda item: str(item.path)):
            hasher.update(str(source.path).encode())
            if source.content is None:
                msg = "atomic file state has no content"
                raise ValueError(msg)
            hasher.update(hashlib.sha256(source.content).hexdigest().encode())
            hasher.update(b";")

        return hasher.hexdigest()

    @classmethod
    def lookup(cls, cache_key: str) -> Path | None:
        """Look up cached scan output JSONL if it exists and is valid.

        Returns:
            The existing cached JSONL file path, or None on cache miss.

        """
        target = cls.cache_directory() / f"{cache_key}.jsonl"
        if target.is_file() and target.stat().st_size > 0:
            return target
        return None

    @classmethod
    def store(cls, cache_key: str, stdout_file: Path) -> Path:
        """Store scan output JSONL atomically in the cache.

        Returns:
            The stored cache file path.

        """
        target = cls.cache_directory() / f"{cache_key}.jsonl"
        u.Cli.atomic_write_text_file(
            target,
            stdout_file.read_text(encoding=c.DEFAULT_ENCODING),
        ).unwrap()
        return target


__all__: list[str] = ["FlextInfraCodemodScanCache"]
