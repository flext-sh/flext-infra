"""Mise executable resolution against the committed manifest and lock.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t


class FlextInfraUtilitiesMiseBinary:
    """Resolve declared tool executables and the Mise reader through Mise."""

    @staticmethod
    def managed_mise_binary(name: str, owner_root: Path) -> p.Result[Path]:
        """Resolve one declared tool's executable through Mise in ``owner_root``.

        The runtime manifest must declare the tool, then the existing lock owner
        selects its pinned release. Missing declarations or pins fail at this
        owner; they never select a host executable or resolve a moving request.
        ``make check`` consumes the same toolchain proof over the committed pins.

        Returns:
            The absolute executable inside the tool's install root, never a
            PATH shim.

        """
        tool = next(
            (
                item
                for item in config.Infra.codegen.toolchain.tools
                if item.name == name
            ),
            None,
        )
        if tool is None:
            return r[Path].fail(f"tool is not declared by the toolchain owner: {name}")
        reader = shutil.which(c.Infra.MISE)
        if reader is None:
            return r[Path].fail("Mise executable is absent; run make setup")
        selector = tool.selector or tool.name
        requested = FlextInfraUtilitiesMiseBinary._committed_mise_tool_request(
            owner_root,
            selector,
        )
        if requested.failure:
            return r[Path].from_failure(requested)
        if not requested.value:
            return r[Path].fail(f"runtime manifest does not declare {selector}")
        pinned = FlextInfraUtilitiesMiseBinary.locked_mise_version(
            owner_root,
            tool=tool.name,
            selector=requested.value[0],
        )
        if pinned.failure:
            return r[Path].from_failure(pinned)
        return FlextInfraUtilitiesMiseBinary._managed_mise_path(
            tool.version_probe.binary,
            owner_root,
            Path(reader),
            f"{selector}@{pinned.value}",
        )

    @staticmethod
    def managed_mise_self(owner_root: Path) -> p.Result[Path]:
        """Qualify the physical Mise reader before it loads project locks.

        The reader is the release the committed tree pins: the self-managed
        entry its ``.mise.toml`` declares, authenticated by the ``mise.lock``
        beside it. The generator's own target release never qualifies the
        reader: ``make upg`` runs this generator while the tree still declares
        the previous release, or none before self-management, and only the
        upgrade renders and locks the new one (C19). A committed manifest that
        declares no self-managed entry reads its locks with the host Mise.

        Returns:
            The installed self-managed executable, never a tool shim.

        """
        selected = shutil.which(c.Infra.MISE)
        if selected is None:
            return r[Path].fail("Mise executable is absent; run make setup")
        reader = Path(selected)
        return FlextInfraUtilitiesMiseBinary.committed_mise_self_release(
            owner_root,
        ).flat_map(
            lambda declared: FlextInfraUtilitiesMiseBinary._qualified_mise_reader(
                reader,
                owner_root,
                declared,
            ),
        )

    @staticmethod
    def _qualified_mise_reader(
        reader: Path,
        owner_root: Path,
        declared: tuple[str] | tuple[()],
    ) -> p.Result[Path]:
        """Authenticate the reader and its installed release against the lock pin.

        Returns:
            The installed self-managed executable, or the physical reader when
            the committed manifest declares no self-managed release.

        """
        if not declared:
            return r[Path].ok(reader.resolve(strict=True))
        return FlextInfraUtilitiesMiseBinary.locked_mise_version(
            owner_root,
            config.Infra.codegen.toolchain.mise_selector,
            declared[0],
        ).flat_map(
            lambda pinned: (
                FlextInfraUtilitiesMiseBinary
                .mise_self_identity(reader, pinned, owner_root)
                .flat_map(
                    lambda qualified: FlextInfraUtilitiesMiseBinary._managed_mise_path(
                        c.Infra.MISE,
                        owner_root,
                        qualified,
                        f"{config.Infra.codegen.toolchain.mise_selector}@{pinned}",
                    ),
                )
                .flat_map(
                    lambda installed: FlextInfraUtilitiesMiseBinary.mise_self_identity(
                        installed,
                        pinned,
                        owner_root,
                    ),
                )
            ),
        )

    @staticmethod
    def committed_mise_self_release(
        owner_root: Path,
    ) -> p.Result[tuple[str] | tuple[()]]:
        """Return the self-managed Mise release the committed manifest declares.

        The manifest is the ``.mise.toml`` beside the nearest ``mise.lock``.
        A tree without that lock and manifest pair, or whose manifest declares
        no self-managed entry, pins no reader release (typed absence).

        Returns:
            One declared release, or an empty tuple when the tree declares none.

        """
        lock_path = FlextInfraUtilitiesMiseBinary._mise_lock_path(owner_root)
        manifest = (
            None if lock_path is None else lock_path.parent / c.Infra.MISE_TOML_FILENAME
        )
        if manifest is None or not manifest.is_file():
            return r[tuple[str] | tuple[()]].ok(())
        return FlextInfraUtilitiesMiseBinary._committed_mise_tool_request(
            manifest.parent,
            config.Infra.codegen.toolchain.mise_selector,
        )

    @staticmethod
    def _committed_mise_tool_request(
        owner_root: Path, selector: str
    ) -> p.Result[tuple[str] | tuple[()]]:
        """Read the runtime owner's current request, independently of codegen targets.

        Returns:
            One scalar or table version request, or an empty declaration tuple.

        """
        manifest = next(
            (
                candidate / c.Infra.MISE_TOML_FILENAME
                for candidate in (owner_root, *owner_root.parents)
                if (candidate / c.Infra.MISE_TOML_FILENAME).is_file()
            ),
            None,
        )
        if manifest is None:
            return r[tuple[str] | tuple[()]].ok(())
        payload = u.Cli.toml_mapping_from_text(
            manifest.read_text(encoding=c.DEFAULT_ENCODING),
        )
        if payload is None:
            return r[tuple[str] | tuple[()]].fail(f"{manifest} is not valid TOML")
        tools = payload.get("tools", {})
        if not isinstance(tools, Mapping):
            return r[tuple[str] | tuple[()]].fail(
                f"{manifest} has a malformed [tools] table",
            )
        release = tools.get(selector)
        if release is None:
            return r[tuple[str] | tuple[()]].ok(())
        if isinstance(release, Mapping):
            release = release.get("version")
        if not isinstance(release, str) or not release:
            return r[tuple[str] | tuple[()]].fail(
                f"{manifest} declares a malformed Mise entry for "
                f"{selector}: {release!r}",
            )
        return r[tuple[str] | tuple[()]].ok((release,))

    @staticmethod
    def mise_self_identity(
        binary: Path, pinned: str, owner_root: Path
    ) -> p.Result[Path]:
        """Check the physical reader without invoking a lock-consuming command.

        Returns:
            The physical executable matching the committed self pin.

        """
        binary = binary.resolve(strict=True)
        identity = u.Cli.run_raw(
            (str(binary), "--version"),
            cwd=owner_root,
            timeout=c.Infra.TIMEOUT_SHORT,
            options=m.Cli.ProcessOptions(env=c.Infra.MISE_IDENTITY_PROBE_ENVIRONMENT),
        )
        if identity.failure:
            return r[Path].from_failure(identity)
        output = identity.value
        if not u.Cli.process_succeeded(output.outcome) or output.stderr.strip():
            return r[Path].fail(output.stderr or output.stdout)
        if output.stdout.split()[:1] != [pinned]:
            return r[Path].fail(
                f"Mise reader {binary} differs from lock: expected={pinned} "
                f"observed={output.stdout.strip()}; run make setup"
            )
        return r[Path].ok(binary)

    @staticmethod
    def _managed_mise_path(
        name: str, owner_root: Path, reader: Path, selector: str
    ) -> p.Result[Path]:
        located = u.Cli.run_raw(
            (str(reader), "-C", str(owner_root), "which", name, "--tool", selector),
            cwd=owner_root,
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if located.failure:
            return r[Path].from_failure(located)
        if (
            not u.Cli.process_succeeded(located.value.outcome)
            or located.value.stderr.strip()
        ):
            return r[Path].fail(located.value.stderr or located.value.stdout)
        binary = Path(located.value.stdout.strip())
        if not binary.is_absolute() or not binary.is_file():
            return r[Path].fail(f"managed executable is not an absolute file: {binary}")
        return r[Path].ok(binary.resolve(strict=True))

    @classmethod
    def locked_mise_version(
        cls,
        execution_root: Path,
        tool: str,
        selector: str,
    ) -> p.Result[str]:
        """Resolve the selector's pinned version from the committed mise.lock.

        Only ``make upg`` resolves a moving selector and writes mise.lock;
        every other execution must authenticate exactly what the lock pins,
        because a version taken from the selector itself sends the shim's
        resolution over the network on a cold cache.

        Returns:
            The resulting ``p.Result[str]``.

        """
        lock_path = cls._mise_lock_path(execution_root)
        if lock_path is None:
            return r[str].fail(
                f"no {c.Infra.MISE_LOCK_FILENAME} above {execution_root} pins "
                f"{tool}; run make upg so generation stays offline",
            )
        return cls._pinned_mise_lock_version(lock_path, tool=tool, selector=selector)

    @staticmethod
    def _mise_lock_path(execution_root: Path) -> Path | None:
        """Return the nearest committed mise.lock above the execution root.

        Returns:
            The resulting ``Path | None``.

        """
        return next(
            (
                candidate / c.Infra.MISE_LOCK_FILENAME
                for candidate in (execution_root, *execution_root.parents)
                if (candidate / c.Infra.MISE_LOCK_FILENAME).is_file()
            ),
            None,
        )

    @classmethod
    def _pinned_mise_lock_version(
        cls,
        lock_path: Path,
        *,
        tool: str,
        selector: str,
    ) -> p.Result[str]:
        """Authenticate the committed mise.lock version one selector pins.

        Returns:
            The resulting ``p.Result[str]``.

        """
        entries_result = cls._mise_lock_tool_entries(lock_path, tool=tool)
        if entries_result.failure:
            return r[str].from_failure(entries_result)
        for entry in entries_result.value:
            locked = cls._locked_entry_version(entry)
            if locked is None:
                return r[str].fail(
                    f"{lock_path} has a malformed [[tools.{tool}]] entry: {entry!r}",
                )
            pinned, specifiers = locked
            if selector in specifiers or selector == pinned:
                return r[str].ok(pinned)
        return r[str].fail(
            f"{lock_path} pins no {tool} for selector {selector!r}; run make upg",
        )

    @staticmethod
    def _mise_lock_tool_entries(
        lock_path: Path,
        *,
        tool: str,
    ) -> p.Result[t.SequenceOf[t.JsonValue]]:
        """Read one tool's lock entries from the committed mise.lock.

        Returns:
            The resulting ``p.Result[t.SequenceOf[t.JsonValue]]``.

        """
        payload = u.Cli.toml_mapping_from_text(
            lock_path.read_text(encoding=c.DEFAULT_ENCODING),
        )
        if payload is None:
            return r[t.SequenceOf[t.JsonValue]].fail(f"{lock_path} is not valid TOML")
        tools = payload.get("tools", {})
        if not isinstance(tools, Mapping):
            return r[t.SequenceOf[t.JsonValue]].fail(
                f"{lock_path} has a malformed [tools] table",
            )
        entries = tools.get(tool)
        if not isinstance(entries, list):
            return r[t.SequenceOf[t.JsonValue]].fail(
                f"{lock_path} pins no [[tools.{tool}]] entry",
            )
        return r[t.SequenceOf[t.JsonValue]].ok(entries)

    @staticmethod
    def _locked_entry_version(
        entry: t.JsonValue,
    ) -> t.Pair[str, t.SequenceOf[t.JsonValue]] | None:
        """Return one lock entry's pinned version and specifiers when wellformed.

        Returns:
            The resulting ``t.Pair | None``.

        """
        if not isinstance(entry, Mapping):
            return None
        pinned = entry.get("version")
        specifiers = entry.get("specifiers", ())
        if not isinstance(pinned, str) or not isinstance(specifiers, (list, tuple)):
            return None
        return pinned, specifiers


__all__: list[str] = ["FlextInfraUtilitiesMiseBinary"]
