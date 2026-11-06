"""Publish planned protocol sources through the native guarded publication.

The source bootstrap owns the stdlib-only planning core; this owner composes
it with the native file-change machinery under the shared scope lock.
Consumers import publication capabilities through this owner, never through
the bootstrap module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from flext_cli import u

from flext_infra import m, p
from flext_infra._utilities._git import FlextInfraUtilitiesGitPhysicalScope
from flext_infra.protocols_bootstrap import (
    declared_protocol_package,
    normalize_protocol_source,
    plan_protocol_facades,
    plan_protocol_family_inits,
)


class FlextInfraUtilitiesProtocolPublication:
    """Publish planned protocol sources through the native guarded publication."""

    @staticmethod
    def _normalization_sources(
        root: Path, sources: Mapping[Path, str]
    ) -> Mapping[Path, str]:
        """Plan protocol normalization from one captured project declaration.

        Returns:
            Only the protocol modules whose normalized source differs.

        """
        package = declared_protocol_package(root, sources[root / "pyproject.toml"])
        directory = root / "src" / Path(*package.split(".")) / "_protocols"
        result: dict[Path, str] = {}
        for path, content in sources.items():
            if not path.is_relative_to(directory) or path.name == "__init__.py":
                continue
            normalized = normalize_protocol_source(
                content, package_name=package, filename=str(path)
            )
            if normalized != content:
                result[path] = normalized
        return result

    @classmethod
    def normalize_protocol_tree(cls, repository_root: Path) -> tuple[Path, ...]:
        """Normalize the declared protocol family through native guarded publication.

        Returns:
            The source paths changed by this normalization candidate.

        """
        root = repository_root.expanduser().resolve(strict=True)
        return cls._publish_protocol_sources(
            root, lambda sources: cls._normalization_sources(root, sources)
        )

    @staticmethod
    def _captured_protocol_sources(
        directory: Path,
    ) -> tuple[
        list[p.Cli.AtomicDirectoryInventory],
        dict[Path, p.Cli.AtomicFileState],
        set[Path],
    ]:
        """Walk the cold protocol source tree once and capture its state.

        Returns:
            The walked directory inventories, one binary state per Python
            file, and the facade destinations the publication must witness.

        Raises:
            ValueError: A protocol source is not a physical regular entry.

        """
        inventories: list[p.Cli.AtomicDirectoryInventory] = []
        states: dict[Path, p.Cli.AtomicFileState] = {}
        destinations: set[Path] = set()
        pending = [directory]
        while pending:
            current = pending.pop()
            inventory = u.Cli.inventory_physical_directory(current)
            inventories.append(inventory)
            for entry in inventory.entries:
                path = current / entry.name
                if entry.kind == "directory":
                    if entry.name != "__pycache__":
                        pending.append(path)
                elif entry.kind != "file":
                    message = f"protocol source is not a physical regular entry: {path}"
                    raise ValueError(message)
                elif path.suffix == ".py":
                    states[path] = u.Cli.atomic_read_binary_file_state(
                        path, required=True
                    ).unwrap()
            if current != directory and current.name.startswith("_"):
                destinations.add(current / "__init__.py")
                destinations.add(
                    current.parent / f"{current.name.removeprefix('_')}.py"
                )
        return inventories, states, destinations

    @classmethod
    def _publish_protocol_sources(
        cls,
        root: Path,
        planner: Callable[[Mapping[Path, str]], Mapping[Path, str]],
        *,
        package_name: str | None = None,
    ) -> tuple[Path, ...]:
        """Capture a cold source candidate and publish with native CAS and one lock.

        Returns:
            The changed source paths from the canonical file-change publisher.

        Raises:
            ValueError: A physical source, membership or destination lacks its witness.

        """
        root = root.resolve(strict=True)
        lock_path = FlextInfraUtilitiesGitPhysicalScope.lock_path(root)
        with u.Cli.file_changes_lock(lock_path):
            manifest = root / "pyproject.toml"
            states: dict[Path, p.Cli.AtomicFileState] = {
                manifest: u.Cli.atomic_read_binary_file_state(
                    manifest, required=package_name is None
                ).unwrap()
            }
            if package_name is None:
                declaration = states[manifest].content
                if declaration is None:
                    message = f"project declaration is absent: {manifest}"
                    raise ValueError(message)
                package_name = declared_protocol_package(
                    root, declaration.decode("utf-8")
                )
            package_root = root / "src" / Path(*package_name.split("."))
            inventories, captured, destinations = cls._captured_protocol_sources(
                package_root / "_protocols"
            )
            states.update(captured)
            destinations.update({
                package_root / "_protocols" / "__init__.py",
                package_root / "protocols.py",
            })
            for path in destinations:
                if path not in states:
                    states[path] = u.Cli.atomic_read_binary_file_state(path).unwrap()
            sources = {
                path: state.content.decode("utf-8")
                for path, state in states.items()
                if state.content is not None
            }
            planned = planner(sources)
            if any(path not in states for path in planned):
                message = "protocol source plan has an uncaptured destination"
                raise ValueError(message)
            for inventory in inventories:
                if u.Cli.inventory_physical_directory(inventory.root.path) != inventory:
                    message = (
                        f"protocol source membership changed: {inventory.root.path}"
                    )
                    raise ValueError(message)
            changes = tuple(
                m.Cli.FileChange(
                    path=path,
                    before=state,
                    desired_content=planned[path].encode("utf-8")
                    if path in planned
                    else state.content,
                    desired_mode=(state.mode if state.mode is not None else 0o644)
                    if path in planned
                    else state.mode,
                )
                for path, state in states.items()
            )
            return u.Cli.publish_file_changes(
                changes, lock_path=lock_path, nonsecret_source_paths=tuple(planned)
            ).unwrap()

    @classmethod
    def publish_protocol_facades(cls, repository_root: Path) -> tuple[Path, ...]:
        """Publish the source-only plan without importing the target protocol facade.

        Returns:
            The native guarded receipt, including only changed paths.

        """
        root = repository_root.resolve(strict=True)
        return cls._publish_protocol_sources(
            root,
            lambda sources: plan_protocol_facades(root, declared_sources=sources),
            package_name="flext_infra",
        )

    @classmethod
    def publish_protocol_family_inits(cls, repository_root: Path) -> tuple[Path, ...]:
        """Publish the missing family initializers of the declared protocol package.

        Returns:
            The native guarded receipt, including only changed paths.

        """
        root = repository_root.resolve(strict=True)
        return cls._publish_protocol_sources(
            root,
            lambda sources: plan_protocol_family_inits(
                root,
                package_name=declared_protocol_package(
                    root, sources[root / "pyproject.toml"]
                ),
                declared_sources=sources,
            ),
        )


__all__: list[str] = ["FlextInfraUtilitiesProtocolPublication"]
