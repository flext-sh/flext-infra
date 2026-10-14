"""Exact filesystem-state primitives for Mise artifact transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import stat
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlsplit

from flext_infra import c, m, p, r, t, u

if TYPE_CHECKING:
    from importlib.metadata import Distribution


class FlextInfraMiseArtifactsFiles:
    """Exact filesystem-state primitives for Mise artifact transactions."""

    @classmethod
    def editable_project_source(
        cls,
        direct_url: m.Cli.AtomicFileState,
    ) -> p.Result[t.VariadicTuple[t.Pair[m.Cli.AtomicFileState, p.ProjectMetadata]]]:
        """Parse captured PEP 610 bytes and authenticate its declared project input.

        Returns:
            The editable source and metadata, or no entries for a noneditable source.

        """
        result_type = r[
            t.VariadicTuple[t.Pair[m.Cli.AtomicFileState, p.ProjectMetadata]]
        ]
        content = direct_url.content
        if content is None:
            return result_type.fail(
                f"producer metadata bytes are absent: {direct_url.path}"
            )
        parsed = r[m.Infra.DirectUrlReceipt].create_from_callable(
            partial(m.Infra.DirectUrlReceipt.model_validate_json, content)
        )
        if parsed.failure:
            return result_type.from_failure(parsed)
        receipt = parsed.value
        if receipt.dir_info is None or not receipt.dir_info.editable:
            return result_type.ok(())
        location = urlsplit(receipt.url)
        if location.scheme != "file" or location.netloc not in {"", "localhost"}:
            return result_type.fail(
                f"editable producer has no local physical root: {receipt.url}"
            )
        project = Path(unquote(location.path)).absolute()
        captured = cls.read_state(project / c.PYPROJECT_FILENAME, required=True)
        if captured.failure:
            return result_type.from_failure(captured)
        return u.Infra.read_project_metadata_result(project).map(
            lambda metadata: ((captured.value, metadata),)
        )

    @classmethod
    def capture_sources(
        cls,
        paths: t.IterableOf[Path],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Read ordered physical sources, stopping before the next path on failure.

        Returns:
            Exact authenticated file states in the caller's original order.

        """
        sources: list[m.Cli.AtomicFileState] = []
        for path in paths:
            captured = cls.read_state(path, required=True)
            if captured.failure:
                return r[t.VariadicTuple[m.Cli.AtomicFileState]].from_failure(captured)
            sources.append(captured.value)
        return r[t.VariadicTuple[m.Cli.AtomicFileState]].ok(tuple(sources))

    @classmethod
    def capture_tree_sources(
        cls,
        root: Path,
    ) -> p.Result[
        t.Pair[m.Cli.AtomicPhysicalTreeManifest, t.VariadicTuple[m.Cli.AtomicFileState]]
    ]:
        """Authenticate a complete native tree before selecting source resources.

        Returns:
            The physical inventory and its exact ordered source states.

        """
        return u.Cli.atomic_inventory_physical_tree(root).flat_map(
            lambda inventory: cls.capture_sources(
                entry.path
                for entry in inventory.entries
                if entry.kind == "file"
                and c.Infra.DUNDER_PYCACHE not in entry.path.parts
            ).map(lambda sources: (inventory, sources))
        )

    @classmethod
    def capture_distribution_sources(
        cls,
        distribution: Distribution,
    ) -> p.Result[
        t.Triple[
            t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
            t.VariadicTuple[m.Cli.AtomicFileState],
            t.VariadicTuple[Path],
        ]
    ]:
        """Capture native metadata and bindings before locating ownership paths.

        Returns:
            Physical metadata trees, all source states and declared file paths.

        """
        result_type = r[
            t.Triple[
                t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
                t.VariadicTuple[m.Cli.AtomicFileState],
                t.VariadicTuple[Path],
            ]
        ]
        declared = distribution.files
        if declared is None:
            return result_type.fail("producer distribution has no native file manifest")
        roots = {
            Path(str(distribution.locate_file(item))).absolute().parent
            for item in declared
            if item.parent.name.endswith(".dist-info")
        }
        trees: list[m.Cli.AtomicPhysicalTreeManifest] = []
        sources: list[m.Cli.AtomicFileState] = []
        for root in sorted(roots):
            captured = cls.capture_tree_sources(root)
            if captured.failure:
                return result_type.from_failure(captured)
            trees.append(captured.value[0])
            sources.extend(captured.value[1])
        bindings = cls.capture_sources(
            Path(str(distribution.locate_file(item))).absolute()
            for item in declared
            if item.suffix == ".pth"
        )
        if bindings.failure:
            return result_type.from_failure(bindings)
        name = distribution.metadata.get("Name")
        if not isinstance(name, str) or not name.strip():
            return result_type.fail("producer distribution has no declared name")
        return result_type.ok((
            tuple(trees),
            (*sources, *bindings.value),
            tuple(
                Path(str(distribution.locate_file(item))).absolute()
                for item in declared
            ),
        ))

    @classmethod
    def transaction_participants(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
    ) -> t.VariadicTuple[
        m.Infra.MiseToolchainProjectLayout | m.Infra.CodegenFileParticipant
    ]:
        """Return only explicitly registered publication owners.

        Returns:
            Only explicitly registered publication owners.

        """
        return (*layout.projects, *layout.file_participants)

    @classmethod
    def transaction_relative(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        path: Path,
    ) -> p.Result[str]:
        """Encode a file capability path without weakening workspace containment.

        Returns:
            The resulting ``p.Result[str]``.

        """
        participants = sorted(
            layout.file_participants,
            key=lambda item: -len(item.root.parts),
        )
        for participant in participants:
            if path.is_relative_to(participant.root):
                relative = cls.workspace_relative(participant.root, path)
                if relative.failure:
                    return relative
                return r[str].ok(f"{participant.selector}/{relative.value}")
        relative = cls.workspace_relative(layout.scope_root, path)
        if relative.success and relative.value.startswith("@"):
            return r[str].fail(f"reserved file capability path: {path}")
        return relative

    @classmethod
    def resolve_transaction(
        cls,
        layout: m.Infra.MiseToolchainWorkspaceLayout,
        selector: str,
        *,
        purpose: str,
    ) -> p.Result[Path]:
        """Resolve one journal path against its exact registered physical root.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        if not selector.startswith("@"):
            return cls.resolve_relative(layout.scope_root, selector, purpose=purpose)
        identity, separator, relative = selector.partition("/")
        participant = next(
            (item for item in layout.file_participants if item.selector == identity),
            None,
        )
        if not separator or participant is None:
            return r[Path].fail(f"unknown file publication capability: {selector}")
        physical = cls.physical_directory_identity(participant.root)
        if physical.failure:
            return r[Path].from_failure(physical)
        if physical.value != (participant.device, participant.inode):
            return r[Path].fail(
                f"file publication root identity changed: {participant.root}",
            )
        return cls.resolve_relative(participant.root, relative, purpose=purpose)

    @classmethod
    def digest(cls, content: bytes) -> str:
        """Return the exact lowercase SHA-256 identity for raw bytes.

        Returns:
            The exact lowercase SHA-256 identity for raw bytes.

        """
        return u.Cli.sha256_bytes(content)

    @classmethod
    def read_state(
        cls,
        path: Path,
        *,
        required: bool,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Read exact state through the canonical descriptor-authenticated owner.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        return u.Cli.atomic_read_binary_file_state(path, required=required)

    @classmethod
    def physical_directory_identity(cls, path: Path) -> p.Result[t.Pair[int, int]]:
        """Return the device/inode identity of one physical directory.

        Returns:
            The device/inode identity of one physical directory.

        """
        try:
            observed = path.lstat()
        except OSError as exc:
            return r[tuple[int, int]].fail_op("inspect generation directory", exc)
        reparse = getattr(observed, "st_file_attributes", 0) & getattr(
            stat,
            "FILE_ATTRIBUTE_REPARSE_POINT",
            0,
        )
        if not stat.S_ISDIR(observed.st_mode) or reparse:
            return r[tuple[int, int]].fail(
                f"generation directory is not physical: {path}",
            )
        return r[tuple[int, int]].ok((observed.st_dev, observed.st_ino))

    @classmethod
    def write_publication(
        cls,
        publication: m.Infra.CodegenStagedFile,
    ) -> p.Result[bool]:
        """Consume one staged create/replace/mode/delete through the CLI owner.

        Publication is a guarded atomic replace; the zero-residue law
        prohibits leaving backup copies beside managed destinations.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        before = publication.before
        replacement = publication.replacement
        if replacement is None:
            return cls.delete_state(before)
        if replacement.content is None or replacement.mode is None:
            return r[bool].fail(
                f"codegen staged replacement is absent: {replacement.path}",
            )
        published = u.Cli.atomic_publish_staged_binary_file_guarded(before, replacement)
        if published.failure:
            return r[bool].from_failure(published)
        observed = published.value
        observed_identity = (
            observed.path,
            observed.parent_device,
            observed.parent_inode,
            observed.content,
            observed.mode,
            observed.device,
            observed.inode,
            observed.link_count,
            observed.file_attributes,
            observed.reparse_tag,
        )
        replacement_identity = (
            before.path,
            before.parent_device,
            before.parent_inode,
            replacement.content,
            replacement.mode,
            replacement.device,
            replacement.inode,
            replacement.link_count,
            replacement.file_attributes,
            replacement.reparse_tag,
        )
        if observed_identity != replacement_identity:
            return r[bool].fail(
                f"published codegen file differs from staged identity: {before.path}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def delete_state(cls, state: m.Cli.AtomicFileState) -> p.Result[bool]:
        """Delete one exact existing state through the CLI owner.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if (
            state.content is None
            or state.mode is None
            or state.device is None
            or state.inode is None
        ):
            return r[bool].fail(
                f"cannot delete absent codegen file state: {state.path}",
            )
        return u.Cli.atomic_delete_binary_file_guarded(state)

    @classmethod
    def workspace_relative(cls, root: Path, path: Path) -> p.Result[str]:
        """Return a canonical lexical workspace-relative path selector.

        Returns:
            A canonical lexical workspace-relative path selector.

        """
        absolute_root = root.absolute()
        try:
            relative = path.absolute().relative_to(absolute_root)
        except ValueError as exc:
            return r[str].fail_op(f"resolve workspace artifact {path}", exc)
        selector = relative.as_posix()
        if not selector or selector == "." or ".." in relative.parts:
            return r[str].fail(f"invalid workspace artifact path: {path}")
        return r[str].ok(selector)

    @classmethod
    def resolve_relative(
        cls,
        root: Path,
        selector: str,
        *,
        purpose: str,
    ) -> p.Result[Path]:
        """Resolve a lexical relative selector without dereferencing its leaf.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        relative = Path(selector)
        if (
            relative.is_absolute()
            or relative.as_posix() != selector
            or not relative.parts
            or ".." in relative.parts
        ):
            return r[Path].fail(f"unsafe {purpose} path: {selector}")
        absolute_root = root.absolute()
        candidate = (absolute_root / relative).absolute()
        if not candidate.is_relative_to(absolute_root):
            return r[Path].fail(f"{purpose} path escapes its root: {selector}")
        return r[Path].ok(candidate)


__all__: list[str] = ["FlextInfraMiseArtifactsFiles"]
