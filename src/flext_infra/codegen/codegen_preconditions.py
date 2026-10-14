"""Immutable source and journal preconditions for generation transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from functools import partial
from importlib.machinery import PathFinder
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen._mise_artifacts_files import FlextInfraMiseArtifactsFiles
from flext_infra.codegen._mise_artifacts_state import FlextInfraMiseArtifactsState
from flext_infra.codegen._mise_artifacts_verification import (
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.workspace import FlextInfraWorkspaceDetector
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from importlib.metadata import Distribution

    from flext_infra import p

_ENGINE_DISTRIBUTION = config.Infra.codegen.infra_repository.distribution


class FlextInfraCodegenPreconditions:
    """Validate source consistency and receipt ownership before publishing."""

    @classmethod
    def elected_producer_modules(
        cls, *, nominated: t.SequenceOf[m.Infra.SourceClassReference]
    ) -> p.Result[t.VariadicTuple[t.Pair[str, Path]]]:
        """Elect the physical closure of declared producer source dependencies.

        Returns:
            The complete elected namespace and physical-path pairs.
        """
        elected: dict[str, Path] = {}
        pending = [item.target for item in nominated]
        visited: set[Path] = set()
        with u.Infra.open_import_project(Path.cwd()) as project:
            while pending:
                module_name = pending.pop(0)
                namespace = module_name.partition(".")[0]
                if namespace in sys.stdlib_module_names:
                    continue
                selected = cls._elect_namespace(namespace)
                if selected.failure:
                    return r[t.VariadicTuple[t.Pair[str, Path]]].from_failure(selected)
                elected[namespace] = selected.value
                spec = PathFinder.find_spec(namespace)
                qualified = namespace
                for component in module_name.split(".")[1:]:
                    if spec.submodule_search_locations is None:
                        break
                    child = PathFinder.find_spec(
                        f"{qualified}.{component}",
                        spec.submodule_search_locations,
                    )
                    if child is None:
                        break
                    spec = child
                    qualified += f".{component}"
                if spec.origin is None:
                    if spec.submodule_search_locations is not None:
                        # Namespace packages own physical portions, not an
                        # executable initializer. Their elected provider tree
                        # is captured; imported bindings are authenticated by
                        # the native observer separately.
                        continue
                    return r[t.VariadicTuple[t.Pair[str, Path]]].fail(
                        f"declared producer dependency has no source: {module_name}",
                    )
                path = Path(spec.origin).absolute()
                if path in visited or path.suffix != c.Infra.EXT_PYTHON:
                    continue
                visited.add(path)
                resource = u.Infra.runtime_callable("rope.base.resources", "File")(
                    u.Infra.runtime_callable("rope.base.project", "get_no_project")(),
                    str(path),
                )
                declared = u.Infra.resolve_declared_module_imports(project, resource)
                semantic = u.Infra.resolve_semantic_module_imports(project, resource)
                pending.extend(dict.fromkeys((*declared.values(), *semantic.values())))
        return r[t.VariadicTuple[t.Pair[str, Path]]].ok(tuple(sorted(elected.items())))

    @staticmethod
    def _elect_namespace(namespace: str) -> p.Result[Path]:
        """Resolve one required source provider without importing it."""
        result_type = r[Path]
        spec = PathFinder.find_spec(namespace)
        if spec is None:
            return result_type.fail(
                f"producer import has no physical election: {namespace}"
            )
        if spec.submodule_search_locations:
            selected = r[Path | None].create_from_callable(
                partial(u.Infra.declared_package_dir, namespace)
            )
        elif spec.origin is not None:
            selected = r[Path | None].ok(Path(spec.origin))
        else:
            return result_type.fail(
                f"producer module has no native origin: {namespace}"
            )
        if selected.failure:
            return result_type.from_failure(selected)
        if selected.value is None:
            return result_type.fail(f"producer package root is absent: {namespace}")
        return result_type.ok(selected.value.absolute())

    @classmethod
    def capture_source_authority(
        cls, *, nominated: t.SequenceOf[m.Infra.SourceClassReference]
    ) -> p.Result[m.Infra.CodegenSourceAuthority]:
        """Elect physical providers and pin their code, resources and metadata.

        Source declarations nominate providers; loaded bindings authenticate
        selected executable edges before any planning evaluation.

        Returns:
            The authenticated immutable producer closure.
        """
        result_type = r[m.Infra.CodegenSourceAuthority]
        names = tuple(nominated)
        elected = cls.elected_producer_modules(nominated=names)
        if elected.failure:
            return result_type.from_failure(elected)
        roots = dict(elected.value)
        states: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        trees: MutableMapping[Path, m.Cli.AtomicPhysicalTreeManifest] = {}
        owners: MutableMapping[str, set[m.Cli.AtomicPhysicalTreeEntry]] = {
            name: set() for name in roots
        }
        from flext_infra.workspace.native_reference import (
            FlextInfraWorkspaceNativeReference,
        )

        observed = FlextInfraWorkspaceNativeReference.capture(names)
        if observed.failure:
            return result_type.from_failure(observed)
        for supplier, _origin, _declaration in observed.value.sources:
            namespace = supplier.partition("::")[0].partition(".")[0]
            if namespace in roots or namespace in sys.stdlib_module_names:
                continue
            selected = cls._elect_namespace(namespace)
            if selected.failure:
                return result_type.from_failure(selected)
            roots[namespace] = selected.value
            owners[namespace] = set()
        for namespace, root in roots.items():
            if root.is_dir():
                captured_tree = FlextInfraMiseArtifactsFiles.capture_tree_sources(root)
                if captured_tree.failure:
                    return result_type.from_failure(captured_tree)
                trees[root] = captured_tree.value[0]
                states.update((item.path, item) for item in captured_tree.value[1])
        source_files: list[Path] = []
        for path in dict.fromkeys(
            Path(declaration or origin)
            for _, origin, declaration in observed.value.sources
        ):
            if path.is_dir():
                captured_tree = FlextInfraMiseArtifactsFiles.capture_tree_sources(path)
                if captured_tree.failure:
                    return result_type.from_failure(captured_tree)
                trees[path] = captured_tree.value[0]
                states.update((item.path, item) for item in captured_tree.value[1])
            else:
                source_files.append(path)
        captured_sources = FlextInfraMiseArtifactsFiles.capture_sources(source_files)
        if captured_sources.failure:
            return result_type.from_failure(captured_sources)
        states.update((item.path, item) for item in captured_sources.value)
        for distribution in u.installed_distributions():
            captured = cls._distribution_providers(distribution, roots, states, trees)
            if captured.failure:
                return result_type.from_failure(captured)
            for namespace, identities in captured.value.items():
                owners[namespace].update(identities)
        for namespace, providers in owners.items():
            explicit = any(
                not item.attributes and item.target.partition(".")[0] == namespace
                for item in names
            )
            if len(providers) != 1 and not (not providers and explicit):
                ownership = tuple(
                    (item.path, item.device, item.inode) for item in providers
                )
                return result_type.fail(
                    "producer namespace has ambiguous physical distribution ownership: "
                    f"{namespace}: {ownership}"
                )
        receipts: list[m.Cli.AtomicFileReceipt] = []
        for state in states.values():
            measured = u.Cli.atomic_read_binary_file_receipt(
                state.path,
                required=state.device is not None,
            )
            if measured.failure:
                return result_type.from_failure(measured)
            if measured.value.device is not None:
                with u.Cli.atomic_binary_file_reader(measured.value) as reader:
                    if reader.read_range(0, measured.value.size) != state.content:
                        return result_type.fail(
                            f"producer source changed while sealing authority: {state.path}",
                        )
            receipts.append(measured.value)
        authority = m.Infra.CodegenSourceAuthority(
            runtime=Path(sys.executable).resolve(),
            optimize=sys.flags.optimize,
            inputs=tuple(receipts),
            generator_trees=tuple(trees.values()),
            generator_modules=tuple(sorted(roots.items())),
        )
        authored = FlextInfraWorkspaceNativeReference.authored_sources_current(
            observed.value, authority.inputs
        )
        if authored.failure:
            return result_type.from_failure(authored)
        return cls.source_authority_current(authority).map(lambda _current: authority)

    @classmethod
    def source_authority_current(
        cls, authority: m.Infra.CodegenSourceAuthority
    ) -> p.Result[bool]:
        """Re-prove cold election and physical state without executing providers."""
        if authority.runtime != Path(sys.executable).resolve():
            return r[bool].fail("cold producer runtime changed")
        if authority.optimize != sys.flags.optimize:
            return r[bool].fail("cold producer compiler optimization changed")
        for namespace, root in authority.generator_modules:
            elected = cls._elect_namespace(namespace)
            if elected.failure:
                return r[bool].from_failure(elected)
            if elected.value != root:
                return r[bool].fail("cold producer module election changed")
        for expected in authority.inputs:
            observed = u.Cli.atomic_read_binary_file_receipt(
                expected.path,
                required=expected.device is not None,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != expected:
                return r[bool].fail(f"cold producer source changed: {expected.path}")
        for tree in authority.generator_trees:
            observed = u.Cli.atomic_inventory_physical_tree(tree.root.path)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != tree:
                return r[bool].fail(
                    f"cold producer resource tree changed: {tree.root.path}"
                )
        return r[bool].ok(value=True)

    @staticmethod
    def authority_inputs(
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Read pinned payloads through the CLI receipt's authenticated descriptor."""
        states: list[m.Cli.AtomicFileState] = []
        for receipt in authority.inputs:
            if receipt.device is None:
                current = u.Cli.atomic_read_binary_file_receipt(receipt.path)
                if current.failure:
                    return r[t.VariadicTuple[m.Cli.AtomicFileState]].from_failure(
                        current
                    )
                if current.value != receipt:
                    return r[t.VariadicTuple[m.Cli.AtomicFileState]].fail(
                        f"cold producer absent input changed: {receipt.path}",
                    )
                content = None
            else:
                with u.Cli.atomic_binary_file_reader(receipt) as reader:
                    content = reader.read_range(0, receipt.size)
            states.append(
                m.Cli.AtomicFileState.model_validate({
                    **receipt.model_dump(
                        include=set(m.Cli.AtomicFileState.model_fields),
                    ),
                    "content": content,
                }),
            )
        return r[t.VariadicTuple[m.Cli.AtomicFileState]].ok(tuple(states))

    @classmethod
    def capture_producer(
        cls, repository_root: Path, *, entrypoint: p.AttributeProbe
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Authenticate the loaded producer against its cold physical authority."""
        from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport

        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(context)
        from flext_infra.workspace.native_reference import (
            FlextInfraWorkspaceNativeReference,
        )

        selection = FlextInfraWorkspaceNativeReference.producer_selection(entrypoint)
        if selection.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(selection)
        names = (selection.value,)
        cold = cls.capture_source_authority(nominated=names)
        if cold.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(cold)
        inputs = cls.authority_inputs(cold.value)
        if inputs.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(inputs)
        reference = FlextInfraValidateFreshImport.capture_native_reference(
            m.Infra.NativeImportRequest(
                repository_root=context.value.runtime_root,
                runtime_root=context.value.runtime_root,
                modules=names,
                inputs=inputs.value,
                source_authority=cold.value,
                import_roots=tuple(
                    dict.fromkeys(
                        root.parent for _name, root in cold.value.generator_modules
                    )
                ),
            ),
        )
        if reference.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(reference)
        snapshot = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=(),
            inputs=inputs.value,
            generator_trees=cold.value.generator_trees,
            generator_modules=cold.value.generator_modules,
            generator_reference=reference.value,
        )
        return cls.producer_current(snapshot).map(lambda _current: snapshot)

    @staticmethod
    def _distribution_providers(
        distribution: Distribution,
        roots: t.MappingKV[str, Path],
        states: MutableMapping[Path, m.Cli.AtomicFileState],
        trees: MutableMapping[Path, m.Cli.AtomicPhysicalTreeManifest],
    ) -> p.Result[t.MappingKV[str, t.VariadicTuple[m.Cli.AtomicPhysicalTreeEntry]]]:
        """Authenticate native metadata and derive physical namespace ownership.

        Returns:
            Each owned namespace bound to this descriptor's metadata identities.
        """
        result_type = r[
            t.MappingKV[str, t.VariadicTuple[m.Cli.AtomicPhysicalTreeEntry]]
        ]
        captured = FlextInfraMiseArtifactsFiles.capture_distribution_sources(
            distribution
        )
        if captured.failure:
            return result_type.from_failure(captured)
        trees.update((tree.root.path, tree) for tree in captured.value[0])
        states.update((item.path, item) for item in captured.value[1])
        root_depths = {len(root.parts) for root in roots.values()}
        # Native prefixes preserve anchor, case and lexical parent semantics.
        ownership_prefixes = {
            Path(*parts[:depth])
            for parts in (path.parts for path in captured.value[2])
            for depth in root_depths
        }
        namespaces = {
            namespace for namespace, root in roots.items() if root in ownership_prefixes
        }
        for tree in captured.value[0]:
            state = states.get(tree.root.path / c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
            if state is None:
                continue
            parsed = FlextInfraMiseArtifactsFiles.editable_project_source(state)
            if parsed.failure:
                return result_type.from_failure(parsed)
            if parsed.value is None:
                continue
            project_source, metadata = parsed.value
            states[project_source.path] = project_source
            namespace = metadata.package_name
            if namespace in roots:
                if not roots[namespace].is_relative_to(project_source.path.parent):
                    return result_type.fail(
                        "producer source is outside declared editable root: "
                        f"{namespace}"
                    )
                namespaces.add(namespace)
        return result_type.ok(
            dict.fromkeys(namespaces, tuple(tree.root for tree in captured.value[0]))
        )

    @classmethod
    def producer_current(cls, producer: m.Infra.CodegenPhaseAnalysis) -> p.Result[bool]:
        """Authenticate every captured input before selecting a consumer scope."""
        if not producer.inputs or not producer.generator_trees:
            return r[bool].fail("producer context lacks authenticated source closure")
        states = cls.unique_states(producer.inputs)
        if states.failure:
            return r[bool].from_failure(states)
        by_path = {state.path: state for state in states.value}
        covered: set[Path] = set()
        representatives: set[Path] = set()
        for tree in producer.generator_trees:
            representative: Path | None = None
            for entry in tree.entries:
                if entry.kind != "file" or c.Infra.DUNDER_PYCACHE in entry.path.parts:
                    continue
                state = by_path.get(entry.path)
                if state is None or state.content is None:
                    continue
                if (
                    u.Cli.sha256_bytes(state.content),
                    len(state.content),
                    state.mode,
                    state.device,
                    state.inode,
                    state.link_count,
                    state.parent_device,
                    state.parent_inode,
                    state.file_attributes,
                    state.reparse_tag,
                ) != (
                    entry.sha256,
                    entry.size,
                    entry.mode,
                    entry.device,
                    entry.inode,
                    entry.link_count,
                    entry.parent_device,
                    entry.parent_inode,
                    entry.file_attributes,
                    entry.reparse_tag,
                ):
                    return r[bool].fail(
                        f"producer input differs from captured tree: {state.path}"
                    )
                covered.add(state.path)
                if representative is None:
                    representative = state.path
            if representative is not None:
                representatives.add(representative)
        # Native inventory authenticates every covered file. Keep one complete
        # file snapshot per tree and every input outside that proof, including
        # optional absence and editable bindings captured outside package roots.
        retained = tuple(
            state
            for state in states.value
            if state.path not in covered or state.path in representatives
        )
        current = FlextInfraMiseArtifactsVerification.states_current(retained)
        if current.failure:
            return current
        return cls.producer_trees_current(
            producer.generator_trees,
            modules=producer.generator_modules,
            reference=producer.generator_reference,
        )

    @staticmethod
    def producer_trees_current(
        trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
        *,
        modules: t.VariadicTuple[t.Pair[str, Path]],
        reference: m.Infra.NativeImportReference | None = None,
    ) -> p.Result[bool]:
        """Check the original native epoch without minting namespace-local proofs."""
        if reference is None:
            return r[bool].fail("producer closure lacks its pre-planning native epoch")
        if (
            tuple(trees) != reference.source_authority.generator_trees
            or modules != reference.source_authority.generator_modules
        ):
            return r[bool].fail("producer native epoch belongs to another election")
        from flext_infra.workspace.native_reference import (
            FlextInfraWorkspaceNativeReference,
        )

        current = FlextInfraWorkspaceNativeReference.authority_current(
            reference.source_authority, outputs=outputs
        )
        if current.failure:
            return current
        observed = FlextInfraWorkspaceNativeReference.capture(reference.modules)
        if observed.failure:
            return r[bool].from_failure(observed)
        return FlextInfraWorkspaceNativeReference.compare(observed.value, reference)

    @staticmethod
    def source_trees_current(
        trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
        *,
        modules: t.VariadicTuple[t.Pair[str, Path]],
    ) -> p.Result[bool]:
        """Reauthenticate whole trees, then compare source membership and identity.

        Interpreter bytecode is derived, not a source input. It is excluded only
        after native inventory has authenticated all physical entries. Native
        output receipts, never path guesses, authorize publication membership.

        Returns:
            Success only for unchanged trees, election and executing sources.
        """
        for tree in trees:
            current = FlextInfraCodegenPreconditions._producer_tree_current(
                tree, outputs
            )
            if current.failure:
                return current
        if not modules:
            return r[bool].fail("producer module election changed after capture")
        for namespace, root in modules:
            elected = FlextInfraCodegenPreconditions._elect_namespace(namespace)
            if elected.failure:
                return r[bool].from_failure(elected)
            if elected.value != root:
                return r[bool].fail("producer module election changed after capture")
        return r[bool].ok(value=True)

    @classmethod
    def _producer_tree_current(
        cls,
        tree: m.Cli.AtomicPhysicalTreeManifest,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Authenticate physical inventory before directory and file proof.

        Returns:
            Success only for this tree's native identities and journaled effects.
        """
        inventory = u.Cli.atomic_inventory_physical_tree(tree.root.path)
        if inventory.failure:
            return r[bool].from_failure(inventory)
        if not FlextInfraMiseArtifactsVerification.same_directory_identity(
            tree.root, inventory.value.root
        ):
            return r[bool].fail(f"producer root identity changed: {tree.root.path}")
        if any(item.kind == "symlink" for item in inventory.value.entries):
            return r[bool].fail(
                f"producer resource has a physical alias: {tree.root.path}"
            )
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
        live = {
            item.path: item
            for item in inventory.value.entries
            if item.kind == "directory"
            and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        admitted = {
            parent
            for path, item in own.items()
            if item.sha256 is not None
            for parent in path.parents
            if parent.is_relative_to(tree.root.path) and parent != tree.root.path
        }
        if set(live) != set(directories) | admitted:
            return r[bool].fail(
                f"producer directory membership changed: {tree.root.path}"
            )
        for path, before in directories.items():
            if not FlextInfraMiseArtifactsVerification.same_directory_identity(
                before, live[path]
            ):
                return r[bool].fail(f"producer directory identity changed: {path}")
        return cls._producer_files_current(tree, inventory.value, own)

    @staticmethod
    def _producer_files_current(
        tree: m.Cli.AtomicPhysicalTreeManifest,
        inventory: m.Cli.AtomicPhysicalTreeManifest,
        own: t.MappingKV[Path, m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Verify source files and every admitted effect against native receipts.

        Returns:
            Success for exact membership, byte, mode and physical identities.
        """
        expected = {
            item.path: item
            for item in tree.entries
            if item.kind == "file" and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        observed = {
            item.path: item
            for item in inventory.entries
            if item.kind == "file" and c.Infra.DUNDER_PYCACHE not in item.path.parts
        }
        if set(observed) != (set(expected) - set(own)) | {
            path for path, item in own.items() if item.sha256 is not None
        }:
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
            if path not in own and observed[path] != before:
                return r[bool].fail(f"producer resource identity changed: {path}")
        return r[bool].ok(value=True)

    @staticmethod
    def rendering_engine(repository_root: Path) -> p.Result[bool]:
        """Prove the executing engine is the flext-infra the target's lock pins.

        Editable bindings and targets without an engine pin use their own tree.

        Returns:
            Success only for the declared rendering origin and registry version.
        """
        result_type = r[bool]
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return result_type.from_failure(context)
        lock_path = context.value.lock_path
        if not lock_path.is_file():
            return result_type.ok(value=True)
        matches = u.installed_distributions(name=_ENGINE_DISTRIBUTION)
        if len(matches) != 1:
            return result_type.fail(
                f"rendering engine distribution count mismatch: "
                f"distribution={_ENGINE_DISTRIBUTION} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        direct_url = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        receipt = r[m.Infra.DirectUrlReceipt | None].create_from_callable(
            lambda: (
                m.Infra.DirectUrlReceipt.model_validate_json(direct_url)
                if direct_url is not None
                else None
            )
        )
        if receipt.failure:
            return result_type.from_failure(receipt)
        if (
            receipt.value is not None
            and receipt.value.dir_info is not None
            and receipt.value.dir_info.editable
        ):
            return result_type.ok(value=True)
        return (
            u.Cli
            .toml_read_json(lock_path)
            .flat_map(
                lambda payload: r[m.Infra.LockedEnvironment].create_from_callable(
                    partial(m.Infra.LockedEnvironment.model_validate, payload)
                )
            )
            .flat_map(
                partial(
                    FlextInfraCodegenPreconditions._locked_engine_current,
                    distribution,
                    direct_url,
                )
            )
        )

    @staticmethod
    def _locked_engine_current(
        distribution: Distribution,
        direct_url: str | None,
        locked: m.Infra.LockedEnvironment,
    ) -> p.Result[bool]:
        """Compare the installed engine to the unique typed committed pin.

        Returns:
            Success for an unpinned/editable engine or its exact artifact origin.
        """
        result_type = r[bool]
        pinned = tuple(
            item for item in locked.package if item.name == _ENGINE_DISTRIBUTION
        )
        if not pinned:
            return result_type.ok(value=True)
        if len(pinned) != 1:
            return result_type.fail(
                "rendering engine has ambiguous committed lock entries"
            )
        item = pinned[0]
        if item.source.editable is not None:
            return result_type.ok(value=True)
        origin = FlextInfraWorkspaceEnvironmentProvenance.locked_origin_verdict(
            _ENGINE_DISTRIBUTION, item, direct_url
        )
        if origin.failure:
            return origin
        if item.source.registry is not None and distribution.version != item.version:
            return result_type.fail(
                f"rendering engine {_ENGINE_DISTRIBUTION}@{distribution.version} "
                f"is not the locked pin {_ENGINE_DISTRIBUTION}@{item.version}: "
                "the environment is stale — cure: make setup (stale environment) "
                "or make upg (stale pin); never a hand-edited generated file",
            )
        return result_type.ok(value=True)

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

    @classmethod
    def bind_producer_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        producer: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Bind each staged consumer to the exact pre-planning producer inputs.

        Returns:
            A new analysis retaining the authenticated producer's full closure.
        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        current = cls.producer_current(producer)
        if current.failure:
            return result_type.from_failure(current)
        inputs = cls.unique_states((*analysis.inputs, *producer.inputs))
        if inputs.failure:
            return result_type.from_failure(inputs)
        files: list[m.Infra.CodegenFilePlan] = []
        for plan in analysis.files:
            sources = cls.unique_states((*plan.source_states, *producer.inputs))
            if sources.failure:
                return result_type.from_failure(sources)
            files.append(plan.model_copy(update={"source_states": sources.value}))
        return result_type.ok(
            analysis.model_copy(
                update={
                    "inputs": inputs.value,
                    "files": tuple(files),
                    "generator_trees": producer.generator_trees,
                    "generator_modules": producer.generator_modules,
                    "generator_reference": producer.generator_reference,
                }
            )
        )

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
