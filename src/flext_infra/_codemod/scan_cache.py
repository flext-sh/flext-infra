"""Persistent per-source scan cache for ast-grep.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from flext_infra import p, settings, u


class FlextInfraCodemodScanCache:
    """Content-addressed native findings of one source under one staged ruleset.

    A fragment holds the exact JSONL records ast-grep emitted for one source,
    empty when the source has no finding. Its key authenticates the scanner
    release, every byte of the staged ruleset (configuration, rule bundle and
    utilities), the source's root-relative path and its content, so a change
    to any of them rescans only the sources it affects.
    """

    @classmethod
    def cache_directory(cls) -> Path:
        """Return the directory where scan fragments are stored.

        Returns:
            The authenticated cache directory path.

        """
        path = settings.work_dir / "ast-grep" / "cache"
        u.Cli.ensure_dir(path).unwrap()
        return path

    @classmethod
    def ruleset_digest(cls, ruleset_config: Path, scanner: Path) -> str:
        """Digest the scanner release and every staged ruleset document.

        Args:
            ruleset_config: The staged native configuration; its directory
                holds the complete projected ruleset.
            scanner: The resolved managed scanner executable.

        Returns:
            The hex digest of this exact scanner and ruleset.

        """
        root = ruleset_config.parent
        hasher = hashlib.sha256(str(scanner.resolve()).encode())
        for document in sorted(path for path in root.rglob("*") if path.is_file()):
            hasher.update(b"\x00")
            hasher.update(document.relative_to(root).as_posix().encode())
            hasher.update(b"=")
            hasher.update(hashlib.sha256(document.read_bytes()).digest())
        return hasher.hexdigest()

    @classmethod
    def source_key(
        cls, ruleset_digest: str, relative: Path, source: p.Cli.AtomicFileState
    ) -> str:
        """Key one source's findings under one ruleset digest.

        Returns:
            The hex digest of this ruleset, path and content.

        Raises:
            ValueError: If the atomic file state carries no content.

        """
        if source.content is None:
            msg = f"atomic file state has no content: {source.path}"
            raise ValueError(msg)
        hasher = hashlib.sha256(ruleset_digest.encode())
        hasher.update(b"\x00")
        hasher.update(relative.as_posix().encode())
        hasher.update(b"\x00")
        hasher.update(hashlib.sha256(source.content).digest())
        return hasher.hexdigest()

    @classmethod
    def lookup(cls, cache_key: str) -> Path | None:
        """Return the stored fragment, empty when the source has no finding.

        Returns:
            The fragment path, or None when this key was never scanned.

        """
        target = cls.cache_directory() / f"{cache_key}.jsonl"
        return target if target.is_file() else None

    @classmethod
    def store(cls, cache_key: str, records: str) -> Path:
        """Store one source's native records atomically.

        Returns:
            The stored fragment path.

        """
        target = cls.cache_directory() / f"{cache_key}.jsonl"
        u.Cli.atomic_write_text_file(target, records).unwrap()
        return target


__all__: list[str] = ["FlextInfraCodemodScanCache"]
