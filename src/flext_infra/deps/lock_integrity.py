"""Committed generated TOML lock integrity verification.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, config, p, r, s, t, u
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraLockIntegrityVerifier(s[bool]):
    """Verify the committed generated TOML locks of one repository root.

    Generated locks (``mise.lock``, ``uv.lock``) are projections that must
    never be merge-resolved: a textual merge concatenates tables and re-creates
    duplicate keys that surface far from the merge as cryptic resolver errors.
    The verifier parses each committed lock with the flext-cli TOML reader and
    fails naming the file, the parser cause, and every duplicated section.
    """

    _TABLE_HEADER: ClassVar[t.RegexPattern] = re.compile(
        r"(?m)^[ \t]*(?:\[([^\][]+)\]|\[\[([^\][]+)\]\])[ \t]*(?:#.*)?$",
    )

    @classmethod
    def verify_pin_convergence(
        cls,
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[bool]:
        """Verify every governed ``uv.lock`` pins shared Git deps to one SHA.

        Returns:
            Success when every shared Git pin converges, or the first drift.

        """
        resolved = FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root
        )
        if resolved.failure:
            return r.from_failure(resolved)
        runtime_root = resolved.value.runtime_root
        observed: MutableMapping[tuple[str, str], MutableMapping[str, list[Path]]] = {}
        for project_root in u.Infra.governed_project_roots(runtime_root):
            lock_path = project_root / c.Infra.UV_LOCK_FILENAME
            if not lock_path.is_file():
                continue
            parsed = u.Cli.toml_read_json(lock_path)
            if parsed.failure:
                return r[bool].from_failure(parsed)
            cls._collect_git_pins(lock_path, parsed.value, observed)
        return cls._validate_git_pin_convergence(runtime_root, observed)

    @staticmethod
    def _collect_git_pins(
        lock_path: Path,
        lock: t.JsonMapping,
        observed: MutableMapping[tuple[str, str], MutableMapping[str, list[Path]]],
    ) -> None:
        packages = lock.get("package")
        if not isinstance(packages, Sequence) or isinstance(packages, str):
            return
        for entry in packages:
            if not isinstance(entry, Mapping):
                continue
            name = entry.get("name")
            source = entry.get("source")
            if not isinstance(name, str) or not isinstance(source, Mapping):
                continue
            git_url = source.get("git")
            if not isinstance(git_url, str) or "#" not in git_url:
                continue
            url_and_rev, _, sha = git_url.partition("#")
            if not sha:
                continue
            observed.setdefault((name, url_and_rev), {}).setdefault(sha, []).append(
                lock_path
            )

    @staticmethod
    def _validate_git_pin_convergence(
        runtime_root: Path,
        observed: Mapping[tuple[str, str], Mapping[str, Sequence[Path]]],
    ) -> p.Result[bool]:
        mismatches: list[str] = []
        for (name, url_and_rev), by_sha in sorted(observed.items()):
            if len(by_sha) <= 1:
                continue
            details = ", ".join(
                f"{sha[:10]} "
                f"({', '.join(str(p.relative_to(runtime_root)) for p in paths)})"
                for sha, paths in sorted(by_sha.items())
            )
            mismatches.append(f"{name} [{url_and_rev}]: {details}")
        if mismatches:
            return r[bool].fail(
                "git pin divergence across governed uv.lock files: "
                + "; ".join(mismatches),
            )
        return r[bool].ok(value=True)

    @classmethod
    def repair_mise_platforms(
        cls,
        request: p.Infra.WorkspaceRequest,
        runner: p.Cli.CommandRunner,
    ) -> p.Result[bool]:
        """Migrate legacy locks or repair missing platforms for governed repositories.

        Generated ``make upg`` owns every native stage before this one: it
        relocks the tools whose ``mise lock --bump --dry-run`` preview is not
        ``[]`` and writes the UV lock. This repair reads each governed
        ``mise.lock`` in the isolated upgrade executor. An explicit version-3
        lock needs a native format upgrade over all declared platforms,
        then any tool still missing a platform table is repaired.

        Returns:
            Success when no declared platform is missing, or the first failure.

        """
        resolved = FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root
        )
        if resolved.failure:
            return r.from_failure(resolved)
        root = resolved.value.runtime_root
        return u.Infra.managed_mise_self(root).flat_map(
            lambda mise: cls._repair_mise_roots(
                runner,
                mise,
                u.Infra.governed_project_roots(root),
            ),
        )

    @classmethod
    def _repair_mise_roots(
        cls,
        runner: p.Cli.CommandRunner,
        mise: Path,
        roots: Sequence[Path],
    ) -> p.Result[bool]:
        """Repair each governed repository in order, stopping at the first failure.

        Returns:
            Success when every lock covers its platforms, or the first failure.

        """
        for root in roots:
            repaired = cls._repair_mise_root(runner, root, mise)
            if repaired.failure:
                return repaired
        return r[bool].ok(value=True)

    @classmethod
    def _repair_mise_root(
        cls,
        runner: p.Cli.CommandRunner,
        root: Path,
        mise: Path,
    ) -> p.Result[bool]:
        """Choose the native repair for one governed lock.

        Returns:
            Success when its lock covers every platform, or the native failure.

        """
        return (
            u.Cli
            .toml_read_json(root / c.Infra.MISE_LOCK_FILENAME)
            .flat_map(lambda lock: cls._migrate_mise_format(runner, root, mise, lock))
            .flat_map(cls._incomplete_mise_tools)
            .flat_map(lambda tools: cls._lock_mise_tools(runner, root, mise, tools))
        )

    @classmethod
    def _migrate_mise_format(
        cls,
        runner: p.Cli.CommandRunner,
        root: Path,
        mise: Path,
        lock: t.JsonMapping,
    ) -> p.Result[t.JsonMapping]:
        """Migrate an explicit version-3 lock before checking coverage.

        Returns:
            The current lock document, or the first native failure.

        """
        version = lock.get(c.Infra.MISE_LOCK_VERSION_KEY)
        if (
            isinstance(version, int)
            and version == c.Infra.MISE_LOCK_MIGRATION_SOURCE_VERSION
        ):
            lock_path = root / c.Infra.MISE_LOCK_FILENAME
            return cls._run_mise_lock(runner, root, mise, "--upgrade").flat_map(
                lambda _: cls._read_upgraded_mise_lock(lock_path),
            )
        return r[t.JsonMapping].ok(lock)

    @staticmethod
    def _read_upgraded_mise_lock(path: Path) -> p.Result[t.JsonMapping]:
        """Read the native writer's migrated lock before platform repair.

        Returns:
            The upgraded lock document, or its first invalid result.

        """
        result = u.Cli.toml_read_json(path)
        if result.failure:
            return result
        version = result.value.get(c.Infra.MISE_LOCK_VERSION_KEY)
        if (
            not isinstance(version, int)
            or version <= c.Infra.MISE_LOCK_MIGRATION_SOURCE_VERSION
        ):
            return r[t.JsonMapping].fail(
                f"{path}: mise lock --upgrade left lockfile version {version!r}",
            )
        return result

    @staticmethod
    def _run_mise_lock(
        runner: p.Cli.CommandRunner,
        root: Path,
        mise: Path,
        *args: str,
    ) -> p.Result[bool]:
        """Run the elected native lock write in its owning checkout.

        Returns:
            Success, or the original Mise failure.

        """
        return runner.run_live(
            (str(mise), "-C", str(root), "lock", *args),
            cwd=root,
            timeout=c.Infra.TIMEOUT_LONG,
        ).map(lambda _output: True)

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
                f"{runtime_root / c.Infra.MISE_LOCK_FILENAME}: no missing "
                "platform; nothing to lock",
            )
            return r[bool].ok(value=True)
        return cls._run_mise_lock(runner, runtime_root, mise, "--bump", *tools)

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
