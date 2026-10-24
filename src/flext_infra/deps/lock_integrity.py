"""Committed generated TOML lock integrity verification.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import ClassVar, override

from flext_infra import FlextInfraServiceBase, c, config, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceLockCompleteness,
)


class FlextInfraLockIntegrityVerifier(FlextInfraServiceBase[bool]):
    """Verify the committed generated TOML locks of one repository root.

    Generated locks (``mise.lock``, ``uv.lock``) are projections that must
    never be merge-resolved: a textual merge concatenates tables and re-creates
    duplicate keys that surface far from the merge as cryptic resolver errors.
    The verifier parses each committed lock with the strict stdlib reader and
    fails naming the file, the parser cause, and every duplicated section.
    """

    _TABLE_HEADER: ClassVar[re.Pattern[str]] = re.compile(
        r"(?m)^[ \t]*(?:\[([^\][]+)\]|\[\[([^\][]+)\]\])[ \t]*(?:#.*)?$",
    )

    @staticmethod
    def upgrade_lock(request: p.Infra.WorkspaceRequest) -> p.Result[bool]:
        """Upgrade the elected native UV lock without generation or installation.

        Returns:
            Native upgrade and freshness verification, or the first failure.

        """
        selected = FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root
        )
        if selected.failure:
            return r[bool].from_failure(selected)
        context = selected.value
        binary = u.Infra.managed_mise_binary(c.Infra.UV, context.runtime_root)
        if binary.failure:
            return r[bool].from_failure(binary)
        options = m.Cli.ProcessOptions(
            env={"MISE_AUTO_INSTALL": c.ParserBooleanToken.ZERO},
            remove_env_keys=config.Infra.codegen.make.native_environment_unset,
        )
        locked = u.Cli.run_live(
            (
                str(binary.value),
                "lock",
                "--upgrade",
                "--refresh",
                "--project",
                str(context.runtime_root),
                "--python",
                str(
                    u.Infra.runtime_python(
                        context.project_root, runtime_root=context.runtime_root
                    )
                ),
                "--no-python-downloads",
            ),
            cwd=context.runtime_root,
            timeout=c.Infra.TIMEOUT_LONG,
            options=options,
        )
        if locked.failure:
            return r[bool].from_failure(locked)
        return FlextInfraWorkspaceLockCompleteness.verify_lock(
            context.runtime_root
        ).map(lambda _checked: True)

    @classmethod
    def _duplicated_sections(cls, text: str) -> t.StrSequence:
        """Enumerate table headers declared more than once in a corrupt lock.

        Returns:
            The resulting ``t.StrSequence``.

        """
        counts: t.MutableMappingKV[str, int] = {}
        for match in cls._TABLE_HEADER.finditer(text):
            key = (match.group(1) or match.group(2) or "").strip()
            counts[key] = counts.get(key, 0) + 1
        return tuple(sorted(key for key, count in counts.items() if count > 1))

    @classmethod
    def _verify_lock(cls, lock_path: Path) -> t.StrSequence:
        """Verify one committed lock, returning zero or more failure causes.

        Returns:
            The resulting ``t.StrSequence``.

        """
        if not lock_path.is_file():
            return (f"{lock_path.name}: missing committed generated lock",)
        text = lock_path.read_text(encoding="utf-8")
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            duplicated = cls._duplicated_sections(text)
            sections = (
                f"; duplicated sections: {', '.join(duplicated)}" if duplicated else ""
            )
            return (f"{lock_path.name}: {error}{sections}",)
        return ()

    @override
    def execute(self) -> p.Result[bool]:
        """Verify every committed generated TOML lock at the repository root.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        selected = FlextInfraWorkspaceDetector.resolution_context(self.repository_root)
        if selected.failure:
            return r[bool].from_failure(selected)
        failures: t.StrSequence = tuple(
            failure
            for lock_path in (
                selected.value.runtime_root / c.Infra.MISE_LOCK_FILENAME,
                selected.value.lock_path,
            )
            for failure in self._verify_lock(lock_path)
        )
        if failures:
            return r[bool].fail("; ".join(failures))
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraLockIntegrityVerifier"]
