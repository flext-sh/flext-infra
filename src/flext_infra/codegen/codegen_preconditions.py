"""Immutable source and journal preconditions for generation transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import sys
import tomllib
from collections.abc import MutableMapping
from functools import partial
from importlib.machinery import PathFinder
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlsplit

from flext_infra import c, m, r, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)

if TYPE_CHECKING:
    from flext_infra import p, t

_ENGINE_DISTRIBUTION = "flext-infra"


class FlextInfraCodegenPreconditions:
    """Validate source consistency and receipt ownership before publishing."""

    @classmethod
    def capture_producer(cls) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Elect physical providers and pin their code, resources and metadata.

        Loaded names nominate providers; cold import resolution and native
        descriptor inventory authenticate them before any planning evaluation.
        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        namespaces = {
            base.__module__.partition(".")[0]
            for facade in (c, m, u)
            for base in facade.__mro__
            if base.__module__.partition(".")[0] not in sys.stdlib_module_names
        }
        roots: MutableMapping[str, Path] = {}
        states: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        trees: MutableMapping[Path, m.Cli.AtomicPhysicalTreeManifest] = {}
        owners: MutableMapping[str, set[str]] = {name: set() for name in namespaces}
        for namespace in sorted(namespaces):
            spec = PathFinder.find_spec(namespace)
            if spec is None:
                return result_type.fail(
                    f"producer import is no longer elected: {namespace}"
                )
            if spec.submodule_search_locations:
                selected = r[Path | None].create_from_callable(
                    partial(u.Infra.declared_package_dir, namespace)
                )
                if selected.failure:
                    return result_type.from_failure(selected)
                if selected.value is None:
                    return result_type.fail(
                        f"producer package root is absent: {namespace}"
                    )
                root = selected.value.absolute()
                inventory = u.Cli.atomic_inventory_physical_tree(root)
                if inventory.failure:
                    return result_type.from_failure(inventory)
                trees[root] = inventory.value
                paths = tuple(
                    item.path
                    for item in inventory.value.entries
                    if item.kind == "file"
                    and c.Infra.DUNDER_PYCACHE not in item.path.parts
                )
            elif spec.origin is not None:
                root = Path(spec.origin).absolute()
                paths = (root,)
            else:
                return result_type.fail(
                    f"producer import has no physical origin: {namespace}"
                )
            roots[namespace] = root
            loaded = FlextInfraWorkspaceEnvironmentProvenance.loaded_import_sources(
                namespace
            )
            if loaded.failure:
                return result_type.from_failure(loaded)
            for symbol, origin, class_source in loaded.value:
                physical = Path(class_source or origin).absolute()
                if physical != root and not physical.is_relative_to(root):
                    return result_type.fail(
                        f"producer loaded source differs from elected provider: "
                        f"{symbol}={physical}; elected={root}"
                    )
            for path in paths:
                captured = u.Cli.atomic_read_binary_file_state(path, required=True)
                if captured.failure:
                    return result_type.from_failure(captured)
                states[path] = captured.value
        for distribution in u.installed_distributions():
            declared = distribution.files
            if declared is None:
                return result_type.fail(
                    "producer distribution has no native file manifest"
                )
            metadata_roots = {
                Path(distribution.locate_file(item)).absolute().parent
                for item in declared
                if item.parent.name.endswith(".dist-info")
            }
            for root in sorted(metadata_roots):
                inventory = u.Cli.atomic_inventory_physical_tree(root)
                if inventory.failure:
                    return result_type.from_failure(inventory)
                trees[root] = inventory.value
                for entry in inventory.value.entries:
                    if entry.kind != "file":
                        continue
                    captured = u.Cli.atomic_read_binary_file_state(
                        entry.path, required=True
                    )
                    if captured.failure:
                        return result_type.from_failure(captured)
                    states[entry.path] = captured.value
            for item in declared:
                if item.suffix == ".pth":
                    path = Path(distribution.locate_file(item)).absolute()
                    captured = u.Cli.atomic_read_binary_file_state(path, required=True)
                    if captured.failure:
                        return result_type.from_failure(captured)
                    states[path] = captured.value
            name = distribution.metadata.get("Name")
            if not isinstance(name, str) or not name.strip():
                return result_type.fail("producer distribution has no declared name")
            paths = tuple(
                Path(distribution.locate_file(item)).absolute() for item in declared
            )
            for namespace, root in roots.items():
                if any(path == root or path.is_relative_to(root) for path in paths):
                    owners[namespace].add(name)
            receipts = tuple(
                state
                for path, state in states.items()
                if path.parent in metadata_roots
                and path.name == c.Infra.DISTRIBUTION_DIRECT_URL_FILE
            )
            for state in receipts:
                content = state.content
                if content is None:
                    return result_type.fail(
                        f"producer metadata bytes are absent: {state.path}"
                    )
                parsed = r[m.Infra.DirectUrlReceipt].create_from_callable(
                    partial(m.Infra.DirectUrlReceipt.model_validate_json, content)
                )
                if parsed.failure:
                    return result_type.from_failure(parsed)
                if parsed.value.dir_info is None or not parsed.value.dir_info.editable:
                    continue
                location = urlsplit(parsed.value.url)
                if location.scheme != "file" or location.netloc not in {
                    "",
                    "localhost",
                }:
                    return result_type.fail(
                        f"editable producer has no local physical root: {parsed.value.url}"
                    )
                project = Path(unquote(location.path)).absolute()
                captured = u.Cli.atomic_read_binary_file_state(
                    project / c.PYPROJECT_FILENAME, required=True
                )
                if captured.failure:
                    return result_type.from_failure(captured)
                states[captured.value.path] = captured.value
                metadata = u.Infra.read_project_metadata_result(project)
                if metadata.failure:
                    return result_type.from_failure(metadata)
                namespace = metadata.value.package_name
                if namespace in roots:
                    if not roots[namespace].is_relative_to(project):
                        return result_type.fail(
                            f"producer source is outside declared editable root: {namespace}"
                        )
                    owners[namespace].add(name)
        for namespace, providers in owners.items():
            if len(providers) != 1:
                return result_type.fail(
                    f"producer namespace has ambiguous distribution ownership: {namespace}: {sorted(providers)}"
                )
        snapshot = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=(),
            inputs=tuple(states.values()),
            generator_trees=tuple(trees.values()),
        )
        verified = cls.producer_current(snapshot)
        if verified.failure:
            return result_type.from_failure(verified)
        return result_type.ok(snapshot)

    @classmethod
    def producer_current(cls, producer: m.Infra.CodegenPhaseAnalysis) -> p.Result[bool]:
        """Authenticate every captured input before selecting a consumer scope."""
        if not producer.inputs or not producer.generator_trees:
            return r[bool].fail("producer context lacks authenticated source closure")
        current = FlextInfraMiseArtifactsVerification.states_current(producer.inputs)
        if current.failure:
            return current
        return cls.producer_trees_current(producer.generator_trees)

    @staticmethod
    def producer_trees_current(
        trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Reauthenticate whole trees, then compare source membership and identity.

        Interpreter bytecode is derived, not a source input. It is excluded only
        after native inventory has authenticated all physical entries. Native
        output receipts, never path guesses, authorize publication membership.
        """
        for tree in trees:
            inventory = u.Cli.atomic_inventory_physical_tree(tree.root.path)
            if inventory.failure:
                return r[bool].from_failure(inventory)
            if (
                inventory.value.root.device,
                inventory.value.root.inode,
                inventory.value.root.mount_id,
                inventory.value.root.mode,
                inventory.value.root.parent_device,
                inventory.value.root.parent_inode,
            ) != (
                tree.root.device,
                tree.root.inode,
                tree.root.mount_id,
                tree.root.mode,
                tree.root.parent_device,
                tree.root.parent_inode,
            ):
                return r[bool].fail(f"producer root identity changed: {tree.root.path}")
            if any(item.kind == "symlink" for item in inventory.value.entries):
                return r[bool].fail(
                    f"producer resource has a physical alias: {tree.root.path}"
                )
            expected = {
                item.path: item
                for item in tree.entries
                if item.kind == "file" and c.Infra.DUNDER_PYCACHE not in item.path.parts
            }
            observed = {
                item.path: item
                for item in inventory.value.entries
                if item.kind == "file" and c.Infra.DUNDER_PYCACHE not in item.path.parts
            }
            own = {
                item.path: item
                for item in outputs
                if item.path.is_relative_to(tree.root.path)
            }
            directories = {
                item.path: item
                for item in tree.entries
                if item.kind == "directory"
                and c.Infra.DUNDER_PYCACHE not in item.path.parts
            }
            live_directories = {
                item.path: item
                for item in inventory.value.entries
                if item.kind == "directory"
                and c.Infra.DUNDER_PYCACHE not in item.path.parts
            }
            admitted_directories = {
                parent
                for path, item in own.items()
                if item.sha256 is not None
                for parent in path.parents
                if parent.is_relative_to(tree.root.path) and parent != tree.root.path
            }
            if set(live_directories) != set(directories) | admitted_directories:
                return r[bool].fail(
                    f"producer directory membership changed: {tree.root.path}"
                )
            for path, before in directories.items():
                after = live_directories[path]
                if (
                    after.device,
                    after.inode,
                    after.mode,
                    after.parent_device,
                    after.parent_inode,
                ) != (
                    before.device,
                    before.inode,
                    before.mode,
                    before.parent_device,
                    before.parent_inode,
                ):
                    return r[bool].fail(f"producer directory identity changed: {path}")
            paths = (set(expected) - set(own)) | {
                path for path, item in own.items() if item.sha256 is not None
            }
            if set(observed) != paths:
                return r[bool].fail(
                    f"producer resource membership changed: {tree.root.path}"
                )
            for path, receipt in own.items():
                if receipt.sha256 is None:
                    continue
                after = observed[path]
                if (
                    after.sha256,
                    after.mode,
                    after.device,
                    after.inode,
                    after.parent_device,
                    after.parent_inode,
                ) != (
                    receipt.sha256,
                    receipt.mode,
                    receipt.device,
                    receipt.inode,
                    receipt.parent_device,
                    receipt.parent_inode,
                ):
                    return r[bool].fail(f"producer effect receipt changed: {path}")
            for path, before in expected.items():
                if path in own:
                    continue
                after = observed[path]
                if (
                    after.mode,
                    after.device,
                    after.inode,
                    after.parent_device,
                    after.parent_inode,
                    after.sha256,
                ) != (
                    before.mode,
                    before.device,
                    before.inode,
                    before.parent_device,
                    before.parent_inode,
                    before.sha256,
                ):
                    return r[bool].fail(f"producer resource identity changed: {path}")
        physical_roots = {tree.root.path for tree in trees}
        namespaces = {
            base.__module__.partition(".")[0]
            for facade in (c, m, u)
            for base in facade.__mro__
            if base.__module__.partition(".")[0] not in sys.stdlib_module_names
        }
        for namespace in namespaces:
            selected = r[Path | None].create_from_callable(
                partial(u.Infra.declared_package_dir, namespace)
            )
            if selected.failure:
                return r[bool].from_failure(selected)
            if (
                selected.value is None
                or selected.value.absolute() not in physical_roots
            ):
                return r[bool].fail(
                    f"producer election changed after capture: {namespace}"
                )
            loaded = FlextInfraWorkspaceEnvironmentProvenance.loaded_import_sources(
                namespace
            )
            if loaded.failure:
                return r[bool].from_failure(loaded)
            for symbol, origin, class_source in loaded.value:
                path = Path(class_source or origin).absolute()
                if not path.is_relative_to(selected.value.absolute()):
                    return r[bool].fail(
                        f"loaded producer origin changed: {symbol}={path}"
                    )
        return r[bool].ok(value=True)

    @staticmethod
    def rendering_engine(repository_root: Path) -> p.Result[bool]:
        """Prove the executing engine is the flext-infra the target's lock pins.

        A standalone consumer resolves flext-infra from its ``uv.lock``; an
        engine foreign to that pin renders with templates the target never
        declared — the split brain that forced hand repairs on generated
        files. The fleet's own checkout and any editable binding render from
        their own tree and are exempt; a target without a lock is the same
        case (nothing declares an engine to agree with).

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return result_type.from_failure(context)
        lock_path = context.value.lock_path
        if not lock_path.is_file():
            return result_type.ok(True)
        matches = u.installed_distributions(name=_ENGINE_DISTRIBUTION)
        if len(matches) != 1:
            return result_type.fail(
                f"rendering engine distribution count mismatch: "
                f"distribution={_ENGINE_DISTRIBUTION} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        direct_url = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        provenance = json.loads(direct_url) if direct_url else {}
        if provenance.get("dir_info", {}).get("editable"):
            return result_type.ok(True)
        lock = tomllib.loads(lock_path.read_text(encoding=c.DEFAULT_ENCODING))
        pinned = next(
            (
                package
                for package in lock.get("package", ())
                if package.get("name") == _ENGINE_DISTRIBUTION
            ),
            None,
        )
        if pinned is None:
            return result_type.ok(True)
        source = pinned.get("source", {})
        if source.get("editable") is not None:
            return result_type.ok(True)
        locked_commit = (source.get("git") or "").rsplit("#", 1)[-1] or None
        running_commit = provenance.get("vcs_info", {}).get("commit_id")
        if locked_commit is not None and running_commit is not None:
            if running_commit == locked_commit:
                return result_type.ok(True)
            return result_type.fail(
                f"rendering engine {_ENGINE_DISTRIBUTION}@{running_commit} "
                f"is not the locked pin {_ENGINE_DISTRIBUTION}@{locked_commit}: "
                "the environment is stale — cure: make setup (stale environment) "
                "or make upg (stale pin); never a hand-edited generated file",
            )
        locked_version = pinned.get("version")
        if locked_version is not None and distribution.version != locked_version:
            return result_type.fail(
                f"rendering engine {_ENGINE_DISTRIBUTION}@{distribution.version} "
                f"is not the locked pin {_ENGINE_DISTRIBUTION}@{locked_version}: "
                "the environment is stale — cure: make setup (stale environment) "
                "or make upg (stale pin); never a hand-edited generated file",
            )
        return result_type.ok(True)

    @staticmethod
    def phase_sources(
        phase: str,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]]]:
        """Reject conflicting observations and tag each source with its phase.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[str,
                m.Cli.AtomicFileState]]]``.

        """
        return FlextInfraCodegenPreconditions.unique_states(
            tuple(source for plan in plans for source in plan.source_states)
        ).map(lambda sources: tuple((phase, source) for source in sources))

    @staticmethod
    def unique_states(
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Preserve the first identity per path and refuse conflicting snapshots.

        Returns:
            The authenticated ordered union or its first identity conflict.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        by_path: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        for file_state in states:
            if by_path.setdefault(file_state.path, file_state) != file_state:
                return result_type.fail(
                    f"planner observed two states for {file_state.path}"
                )
        return result_type.ok(tuple(by_path.values()))

    @staticmethod
    def prepublication_barriers(
        plan: m.Infra.MiseToolchainWorkspacePlan,
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
        destinations: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Require unchanged source and destination identities before writing.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        source_barrier = FlextInfraCodegenPreconditions.unique_states(sources).flat_map(
            FlextInfraMiseArtifactsVerification.states_current
        )
        if source_barrier.failure:
            return source_barrier
        destination_barrier = FlextInfraMiseArtifactsVerification.states_current(
            destinations,
        )
        if destination_barrier.failure:
            return destination_barrier
        return FlextInfraMiseArtifactsVerification.sources(plan)

    @staticmethod
    def unchanged_journal(
        session: m.Infra.CodegenTransactionSession,
        changed_error: str,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Require the complete journal receipt; a lease cannot authorize replacement.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        observed = FlextInfraMiseArtifactsState.journal_state(session.plan.layout)
        observed_snapshot = (
            None
            if observed.failure
            else FlextInfraMiseArtifactsState.journal_snapshot(observed.value)
        )
        expected = session.journal_state
        if observed.failure or observed_snapshot != expected:
            return result_type.fail(
                observed.error or changed_error,
                error_data={
                    "cleanup_error": "journal authority mismatch vs session receipt",
                },
            )
        return result_type.ok(session)


__all__: list[str] = ["FlextInfraCodegenPreconditions"]
