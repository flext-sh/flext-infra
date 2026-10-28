"""Committed generated TOML lock integrity verification.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import re
from collections.abc import Mapping, MutableMapping, Sequence
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
    The verifier parses each committed lock with the flext-cli TOML reader and
    fails naming the file, the parser cause, and every duplicated section.
    """

    _TABLE_HEADER: ClassVar[re.Pattern[str]] = re.compile(
        r"(?m)^[ \t]*(?:\[([^\][]+)\]|\[\[([^\][]+)\]\])[ \t]*(?:#.*)?$",
    )

    @classmethod
    def upgrade_lock(
        cls,
        request: p.Infra.WorkspaceRequest,
        runner: p.Cli.CommandRunner,
    ) -> p.Result[bool]:
        """Upgrade the elected native UV and Mise locks, the only lock writer.

        Native uv elects the runtime root: a workspace resolves every declared
        member together in its single root lock, and a standalone checkout
        resolves its own lock. No member is resolved separately; uv's
        ``--upgrade`` implies its own ``--refresh``. The composition root
        injects the command runner every native call uses.

        Returns:
            Native upgrade and freshness verification, or the first failure.

        """
        return FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root,
        ).flat_map(
            lambda context: (
                cls
                ._native_uv(runner, context.runtime_root, ("lock", "--upgrade"))
                .flat_map(
                    lambda _locked: FlextInfraWorkspaceLockCompleteness.verify_lock(
                        context.runtime_root,
                    ),
                )
                .flat_map(
                    lambda _verified: cls._upgrade_mise_lock(
                        runner,
                        context.runtime_root,
                    ),
                )
            ),
        )

    @classmethod
    def _upgrade_mise_lock(
        cls,
        runner: p.Cli.CommandRunner,
        runtime_root: Path,
    ) -> p.Result[bool]:
        """Lock, in one pass, only the Mise tools whose resolution changed.

        Every governed repository (the runtime root and each declared member)
        renders its own ``.mise.toml`` and commits its own ``mise.lock`` for
        standalone consumption, and Mise resolves a member's tools from the
        member's lock. The single upgrade pass therefore relocks each of them.
        Plain ``mise lock`` refreshes the metadata of every locked version and
        downloads each provenance artifact again. The native ``--dry-run
        --json`` preview costs only version resolution and names exactly the
        tools whose locked version would change; tools missing a declared
        platform join them. Mise then locks and verifies those tools alone.

        Returns:
            Success when every lock is current, or the first native failure.

        """
        return u.Infra.managed_mise_self(runtime_root).flat_map(
            lambda mise: cls._lock_mise_roots(
                runner,
                mise,
                u.Infra.governed_project_roots(runtime_root),
            ),
        )

    @classmethod
    def _lock_mise_roots(
        cls,
        runner: p.Cli.CommandRunner,
        mise: Path,
        roots: Sequence[Path],
    ) -> p.Result[bool]:
        """Relock each governed repository in order, stopping at the first failure.

        Returns:
            Success when every lock is current, or the first native failure.

        """
        for root in roots:
            locked = cls._relock_mise_root(runner, root, mise)
            if locked.failure:
                return locked
        return r[bool].ok(value=True)

    @classmethod
    def _relock_mise_root(
        cls,
        runner: p.Cli.CommandRunner,
        root: Path,
        mise: Path,
    ) -> p.Result[bool]:
        """Select and lock the changed tools of one governed repository.

        Returns:
            Success when its lock is current, or the native lock's failure.

        """
        return cls._mise_lock_selection(runner, root, mise).flat_map(
            lambda tools: cls._lock_mise_tools(runner, root, mise, tools),
        )

    @staticmethod
    def _mise_lock_command(runtime_root: Path, mise: Path) -> Sequence[str]:
        """Native Mise lock re-resolving moving selectors for this runtime.

        Returns:
            The command prefix every Mise lock invocation shares.

        """
        return (str(mise), "-C", str(runtime_root), "lock", "--bump")

    @classmethod
    def _mise_lock_selection(
        cls,
        runner: p.Cli.CommandRunner,
        runtime_root: Path,
        mise: Path,
    ) -> p.Result[Sequence[str]]:
        """Tools whose locked version changes, then tools missing a platform.

        Returns:
            The ordered unique tool names Mise must lock, possibly none.

        """
        return runner.capture(
            (*cls._mise_lock_command(runtime_root, mise), "--dry-run", "--json"),
            cwd=runtime_root,
            timeout=c.Infra.TIMEOUT_LONG,
        ).flat_map(
            lambda preview: u.Cli.toml_read_json(
                runtime_root / c.Infra.MISE_LOCK_FILENAME,
            ).flat_map(lambda lock: cls._selected_mise_tools(preview, lock)),
        )

    @classmethod
    def _selected_mise_tools(
        cls,
        preview: str,
        lock: t.JsonMapping,
    ) -> p.Result[Sequence[str]]:
        """Merge the previewed version changes with the platform gaps.

        Returns:
            The ordered unique tool names, version changes first.

        """
        changes = u.type_adapter(tuple[m.Infra.MiseLockChange, ...]).validate_json(
            preview,
        )
        return cls._incomplete_mise_tools(lock).map(
            lambda incomplete: tuple(
                dict.fromkeys((*(change.name for change in changes), *incomplete)),
            ),
        )

    @classmethod
    def _lock_mise_tools(
        cls,
        runner: p.Cli.CommandRunner,
        runtime_root: Path,
        mise: Path,
        tools: Sequence[str],
    ) -> p.Result[bool]:
        """Lock and verify exactly the selected tools for every declared platform.

        Returns:
            Success, or the native lock's original failure.

        """
        if not tools:
            u.Cli.info(
                f"{runtime_root / c.Infra.MISE_LOCK_FILENAME}: no version change "
                "and no missing platform; nothing to lock",
            )
            return r[bool].ok(value=True)
        return runner.run_live(
            (*cls._mise_lock_command(runtime_root, mise), *tools),
            cwd=runtime_root,
            timeout=c.Infra.TIMEOUT_LONG,
        ).map(lambda _output: True)

    @staticmethod
    def _incomplete_mise_tools(lock: t.JsonMapping) -> p.Result[Sequence[str]]:
        """Name every locked tool lacking a table for a declared platform.

        Returns:
            Lock tool keys whose locked versions miss a declared platform.

        """
        locked = lock.get("tools")
        if not isinstance(locked, Mapping):
            return r[Sequence[str]].fail(
                f"{c.Infra.MISE_LOCK_FILENAME} has no [tools] table; run make upg",
            )
        platforms = tuple(
            c.Infra.MISE_LOCK_PLATFORM_KEY.format(platform=platform)
            for platform in config.Infra.codegen.toolchain.mise_lockfile_platforms
        )
        return r[Sequence[str]].ok(
            tuple(
                name
                for name, versions in locked.items()
                if isinstance(versions, Sequence)
                and not isinstance(versions, str)
                and any(
                    not isinstance(version, Mapping) or key not in version
                    for version in versions
                    for key in platforms
                )
            )
        )

    @staticmethod
    def _native_uv(
        runner: p.Cli.CommandRunner,
        runtime_root: Path,
        arguments: Sequence[str],
    ) -> p.Result[bool]:
        """Run one native uv project command with the runtime interpreter.

        Returns:
            Success of the native command, or its original failure.

        """
        return u.Infra.managed_mise_binary(c.Infra.UV, runtime_root).flat_map(
            lambda binary: runner.run_live(
                (
                    str(binary),
                    *arguments,
                    "--project",
                    str(runtime_root),
                    "--python",
                    str(
                        u.Infra.runtime_python(runtime_root, runtime_root=runtime_root)
                    ),
                    "--no-python-downloads",
                ),
                cwd=runtime_root,
                timeout=c.Infra.TIMEOUT_LONG,
                options=m.Cli.ProcessOptions(
                    env={"MISE_AUTO_INSTALL": c.ParserBooleanToken.ZERO},
                    remove_env_keys=config.Infra.codegen.make.native_environment_unset,
                ),
            ).map(lambda _output: True),
        )

    @classmethod
    def _duplicated_sections(cls, text: str) -> Sequence[str]:
        """Enumerate table headers declared more than once in a corrupt lock.

        Returns:
            The resulting ``Sequence[str]``.

        """
        counts: MutableMapping[str, int] = {}
        for match in cls._TABLE_HEADER.finditer(text):
            key = (match.group(1) or match.group(2) or "").strip()
            counts[key] = counts.get(key, 0) + 1
        return tuple(sorted(key for key, count in counts.items() if count > 1))

    @classmethod
    def _verify_lock(cls, lock_path: Path) -> p.Result[bool]:
        """Verify one committed lock, naming the file and repeated sections.

        Returns:
            Success, or the parser cause with every duplicated section.

        """
        if not lock_path.is_file():
            return r[bool].fail(f"{lock_path.name}: missing committed generated lock")
        return (
            u.Cli
            .toml_read_document(lock_path)
            .map(lambda _document: True)
            .map_error(lambda error: cls._lock_failure(lock_path, error))
        )

    @classmethod
    def _lock_failure(cls, lock_path: Path, error: str) -> str:
        """Describe a corrupt lock by its name, parser cause and repeated sections.

        Returns:
            The failure message for the corrupt lock.

        """
        duplicated = cls._duplicated_sections(lock_path.read_text(encoding="utf-8"))
        sections = (
            f"; duplicated sections: {', '.join(duplicated)}" if duplicated else ""
        )
        return f"{lock_path.name}: {error}{sections}"

    @override
    def execute(self) -> p.Result[bool]:
        """Verify every committed generated TOML lock, stopping at the first defect.

        Returns:
            Success, or the first lock's failure.

        """
        return FlextInfraWorkspaceDetector.resolution_context(
            self.repository_root,
        ).flat_map(
            lambda selected: self._verify_lock(
                selected.runtime_root / c.Infra.MISE_LOCK_FILENAME,
            ).flat_map(lambda _mise: self._verify_lock(selected.lock_path)),
        )


__all__: list[str] = ["FlextInfraLockIntegrityVerifier"]
