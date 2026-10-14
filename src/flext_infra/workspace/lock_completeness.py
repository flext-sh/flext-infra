"""Fail-closed completeness validation of the committed uv.lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_infra import p, r, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraWorkspaceLockCompleteness:
    """Fail loud when the committed uv.lock lost resolved package entries.

    An interrupted resolution can leave a lock whose ``requires-dist``
    references distributions that carry no ``[[package]]`` block. The uv
    freshness fingerprint accepts that fragment, so every later
    ``--frozen`` sync installs the fragment too: the dev groups vanish
    with exit 0 and only surface minutes later as import failures. This
    check states the completeness fact at gate time, next to the lock.
    """

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.WorkspaceLockRequest,
    ) -> p.Result[int]:
        """Validate one CLI request against the checkout's committed lock.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return cls.validate(request.repository_root)

    @classmethod
    def validate(cls, repository_root: Path) -> p.Result[int]:
        """Require the checkout's committed lock to be complete.

        Returns:
            The resulting ``p.Result[int]``.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        lock_path = context.value.lock_path
        if not lock_path.is_file():
            return r[int].fail(f"{lock_path}: no committed lock; run make upg")
        return cls.validate_lock_file(lock_path)

    @classmethod
    def validate_lock_file(cls, lock_path: Path) -> p.Result[int]:
        """Require every lock-referenced distribution to have a package entry.

        Returns:
            The resulting ``p.Result[int]``.

        """
        parsed = (
            u.Cli.toml_parse_text(lock_path.read_text(encoding="utf-8"))
            if lock_path.is_file()
            else None
        )
        if parsed is None:
            return r[int].fail(
                f"{lock_path}: no committed lock or not valid TOML; run make upg",
            )
        packages = parsed.get("package") or ()
        locked: set[str] = set()
        referenced: set[str] = set()
        for entry in packages:
            if not isinstance(entry, Mapping):
                continue
            name = entry.get("name")
            if isinstance(name, str):
                locked.add(name)
            metadata = entry.get("metadata")
            requirements = (
                metadata.get("requires-dist") if isinstance(metadata, Mapping) else None
            )
            if not isinstance(requirements, list):
                continue
            for requirement in requirements:
                if not isinstance(requirement, Mapping):
                    continue
                required = requirement.get("name")
                if isinstance(required, str):
                    referenced.add(required)
        missing = sorted(referenced - locked)
        if missing:
            return r[int].fail(
                f"{lock_path}: {len(missing)} referenced distributions carry no "
                "[[package]] entry (a partial lock from an interrupted "
                f"resolution): {', '.join(missing)} — run make upg",
            )
        return r[int].ok(len(locked))


__all__: tuple[str, ...] = ("FlextInfraWorkspaceLockCompleteness",)
