"""Immutable source and journal preconditions for generation transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from functools import partial
from importlib.machinery import (
    ExtensionFileLoader,
    ModuleSpec,
    PathFinder,
    SourceFileLoader,
)
from importlib.metadata import packages_distributions
from operator import itemgetter
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsComparison,
    FlextInfraMiseArtifactsFiles,
    FlextInfraMiseArtifactsJournalRelocation,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference

if TYPE_CHECKING:
    from importlib.metadata import Distribution


class FlextInfraCodegenPreconditions:
    """Validate source consistency and receipt ownership before publishing."""

    @classmethod
    def elected_producer_modules(
        cls,
        repository_root: Path,
        *,
        nominated: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> p.Result[t.VariadicTuple[t.Pair[str, Path]]]:
        """Elect the physical closure of declared producer source dependencies.

        Returns:
            The complete elected namespace and physical-path pairs.

        Raises:
            TypeError: If an elected producer dependency resource is not a
                file.


        """
        result_type = r[t.VariadicTuple[t.Pair[str, Path]]]
        elected: t.DictKV[str, Path] = {}
        pending = [item.target for item in nominated]
        visited: set[Path] = set()
        with u.Infra.open_import_project(repository_root) as project:
            while pending:
                module_name = pending.pop(0)
                namespace = module_name.partition(".")[0]
                if namespace in sys.stdlib_module_names:
                    continue
                selected = cls._elect_namespace(namespace)
                if selected.failure:
                    return result_type.from_failure(selected)
                elected[namespace] = selected.value
                refined = cls._refined_module_spec(namespace, module_name)
                if refined.failure:
                    return result_type.from_failure(refined)
                spec = refined.value
                if spec.origin is None:
                    if spec.submodule_search_locations is not None:
                        # Namespace packages own physical portions, not an
                        # executable initializer. Their elected provider tree
                        # is captured; imported bindings are authenticated by
                        # the native observer separately.
                        continue
                    return result_type.fail(
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
                if not u.Infra.file_resource(resource):
                    msg = f"producer dependency resource is not a file: {path}"
                    raise TypeError(msg)
                declared = u.Infra.resolve_declared_module_imports(project, resource)
                semantic = u.Infra.resolve_semantic_module_imports(project, resource)
                pending.extend(dict.fromkeys((*declared.values(), *semantic.values())))
        return result_type.ok(tuple(sorted(elected.items())))

    @staticmethod
    def _refined_module_spec(
        namespace: str,
        module_name: str,
    ) -> p.Result[p.Infra.NativeModuleSpec]:
        """Elect the physical module prefix of a qualified import binding.

        Rope's declared imports include lexical symbols after the module path.
        Native finder refinement ends at that boundary; native binding
        observation authenticates the selected symbols separately.

        Returns:
            The native spec owning the import binding's physical module prefix.

        """
        result_type = r[p.Infra.NativeModuleSpec]
        spec = PathFinder.find_spec(namespace)
        if spec is None:
            return result_type.fail(
                f"producer import has no physical election: {namespace}",
            )
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
        return result_type.ok(spec)

    @staticmethod
    def _elect_namespace(namespace: str) -> p.Result[Path]:
        """Resolve one required source provider without importing it.

        Returns:
            The elected physical package root or module origin.

        """
        result_type = r[Path]
        spec = PathFinder.find_spec(namespace)
        if spec is None:
            return result_type.fail(
                f"producer import has no physical election: {namespace}"
            )
        if spec.submodule_search_locations:
            package_dir = u.Infra.declared_package_dir(namespace)
            if package_dir is None:
                return result_type.fail(f"producer package root is absent: {namespace}")
            return result_type.ok(package_dir.absolute())
        if spec.origin is not None:
            return result_type.ok(Path(spec.origin).absolute())
        return result_type.fail(f"producer module has no native origin: {namespace}")

    @classmethod
    def capture_source_authority(
        cls,
        repository_root: Path,
        *,
        nominated: t.SequenceOf[m.Infra.SourceClassReference],
    ) -> p.Result[m.Infra.CodegenSourceAuthority]:
        """Elect physical providers and pin their code, resources and metadata.

        Source declarations nominate providers; loaded bindings authenticate
        selected executable edges before any planning evaluation.

        Returns:
            The authenticated immutable producer closure.

        """
        return cls._observed_source_authority(repository_root, tuple(nominated)).map(
            itemgetter(0)
        )

    @classmethod
    def _observed_source_authority(
        cls,
        repository_root: Path,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
    ) -> p.Result[
        t.Pair[m.Infra.CodegenSourceAuthority, m.Infra.NativeImportObservation]
    ]:
        """Seal the producer authority together with the observation it elected.

        Returns:
            The sealed authority and the loaded-producer observation it rests on.

        """
        result_type = r[
            t.Pair[m.Infra.CodegenSourceAuthority, m.Infra.NativeImportObservation]
        ]
        rooted = cls._elected_source_roots(repository_root, names)
        if rooted.failure:
            return result_type.from_failure(rooted)
        roots, owners = rooted.value
        runtime = FlextInfraMiseArtifactsFiles.read_state(
            Path(sys.executable).resolve(), required=True
        )
        if runtime.failure:
            return result_type.from_failure(runtime)
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {
            runtime.value.path: runtime.value
        }
        observed = cls._observed_source_roots(names, roots, owners)
        if observed.failure:
            return result_type.from_failure(observed)
        trees: t.MutableMappingKV[Path, m.Cli.AtomicPhysicalTreeManifest] = {}
        captured = cls._runtime_dependency_roots(roots, owners, states).flat_map(
            lambda _: cls._captured_authority_states(
                names, roots, observed.value, trees, states
            )
        )
        if captured.failure:
            return result_type.from_failure(captured)
        owned = cls._authenticated_distribution_ownership(
            names, roots, states, trees, owners
        ).flat_map(lambda _: cls._loaded_provider_sources(roots, states))
        if owned.failure:
            return result_type.from_failure(owned)
        return cls._sealed_source_authority(
            names, roots, trees, states, bootstrap_inputs=owned.value
        ).map(lambda authority: (authority, observed.value))

    @classmethod
    def _runtime_dependency_roots(
        cls,
        roots: t.MutableMappingKV[str, Path],
        owners: t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Elect declared runtime dependencies before the cold SDK import.

        Live callable bindings do not enumerate imports performed while loading
        their packages. Installed requirements own that dependency closure;
        native import metadata and editable declarations own its import names.

        Returns:
            Success after electing the dependency roots and pinning declarations.

        """
        indexed = u.Infra.codemod_distributions()
        packages = packages_distributions()
        direct = {canonicalize_name(config.Infra.name)}
        direct.update(
            canonicalize_name(provider)
            for namespace, providers in packages.items()
            if namespace in roots
            for provider in providers
        )
        closure = u.Infra.codemod_runtime_closure(tuple(sorted(direct)), indexed)
        for namespace, providers in packages.items():
            if not any(canonicalize_name(name) in closure for name in providers):
                continue
            selected = cls._elect_runtime_namespace(namespace, roots, owners)
            if selected.failure:
                return r[bool].from_failure(selected)
        for name in sorted(closure):
            editable = cls._runtime_editable_roots(
                name, indexed[name], roots, owners, states
            )
            if editable.failure:
                return r[bool].from_failure(editable)
        return r[bool].ok(value=True)

    @classmethod
    def _elect_runtime_namespace(
        cls,
        namespace: str,
        roots: t.MutableMappingKV[str, Path],
        owners: t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
        *,
        project_root: Path | None = None,
    ) -> p.Result[bool]:
        """Bind a runtime namespace to its unchanged physical election.

        Returns:
            Success or the original election and editable-root failure.

        """
        selected = cls._elect_namespace(namespace)
        if selected.failure:
            return r[bool].from_failure(selected)
        if project_root is not None and not selected.value.is_relative_to(project_root):
            return r[bool].fail(
                f"runtime dependency is outside declared editable root: {namespace}"
            )
        previous = roots.setdefault(namespace, selected.value)
        if previous != selected.value:
            return r[bool].fail(f"runtime dependency election changed: {namespace}")
        owners.setdefault(namespace, set())
        return r[bool].ok(value=True)

    @classmethod
    def _runtime_editable_roots(
        cls,
        name: str,
        distribution: Distribution,
        roots: t.MutableMappingKV[str, Path],
        owners: t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Elect editable import names and retain the declarations consumed.

        Returns:
            Success or the first missing, unreadable or inconsistent declaration.

        """
        declared = distribution.files
        if declared is None:
            return r[bool].fail(
                f"runtime distribution has no native file manifest: {name}"
            )
        for entry in declared:
            path = Path(str(distribution.locate_file(entry))).absolute()
            if (
                path.name != c.Infra.DISTRIBUTION_DIRECT_URL_FILE
                or not path.parent.name.endswith(".dist-info")
            ):
                continue
            observed = FlextInfraMiseArtifactsFiles.read_state(path, required=True)
            if observed.failure:
                return r[bool].from_failure(observed)
            editable = FlextInfraMiseArtifactsFiles.editable_project_source(
                observed.value
            )
            if editable.failure:
                return r[bool].from_failure(editable)
            for project_source, metadata in editable.value:
                selected = cls._elect_runtime_namespace(
                    metadata.package_name,
                    roots,
                    owners,
                    project_root=project_source.path.parent,
                )
                if selected.failure:
                    return r[bool].from_failure(selected)
                sources = cls.unique_states((
                    *states.values(),
                    observed.value,
                    project_source,
                ))
                if sources.failure:
                    return r[bool].from_failure(sources)
                states.update((item.path, item) for item in sources.value)
        return r[bool].ok(value=True)

    @classmethod
    def _loaded_provider_sources(
        cls,
        roots: t.MappingKV[str, Path],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[
        t.VariadicTuple[t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileReceipt]]
    ]:
        """Pin already loaded elected-provider inputs for the atomic reader bootstrap.

        This observes registered modules without importing a provider. A source
        absent from these pins cannot execute before the child has its canonical
        atomic reader. Later source loads retain their own pre-execution receipts.

        Returns:
            The first provenance/read failure or the complete bootstrap pins.

        """
        result_type = r[
            t.VariadicTuple[t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileReceipt]]
        ]
        bootstrap: list[t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileReceipt]] = []
        standard = FlextInfraWorkspaceEnvironmentProvenance.standard_library_root()
        packages = (
            FlextInfraWorkspaceEnvironmentProvenance.standard_library_package_roots()
        )
        u.Cli.info("stage=native-loader-bootstrap sources=loaded-provider-inputs")
        for name, module in tuple(sys.modules.items()):
            namespace = name.partition(".")[0]
            if name == "__main__":
                continue
            if namespace in roots:
                elected = FlextInfraWorkspaceEnvironmentProvenance.module_source(name)
                if elected.failure:
                    return result_type.from_failure(elected)
                source = elected.value
            else:
                source = cls._runtime_bootstrap_file(module, standard, packages)
                if source is None:
                    continue
            if source in states or source.is_dir():
                continue
            captured = FlextInfraMiseArtifactsFiles.read_state(source, required=True)
            if captured.failure:
                return result_type.from_failure(captured)
            states[source] = captured.value
            if source.suffix == c.Infra.EXT_PYTHON:
                receipt = cls._bootstrap_source_receipt(captured.value)
                if receipt.failure:
                    return result_type.from_failure(receipt)
                bootstrap.append((captured.value, receipt.value))
        return result_type.ok(tuple(bootstrap))

    @classmethod
    def _bootstrap_source_receipt(
        cls,
        source: m.Cli.AtomicFileState,
    ) -> p.Result[m.Cli.AtomicFileReceipt]:
        """Bind a newly collected bootstrap buffer to its original native receipt.

        Returns:
            The receipt matching the exact original bytes and physical identity.

        """
        return u.Cli.atomic_read_binary_file_receipt(
            source.path, required=True
        ).flat_map(
            lambda receipt: cls._authenticated_receipt_files(
                {source.path: source}, (receipt,)
            ).map(lambda _: receipt)
        )

    @staticmethod
    def _runtime_bootstrap_file(
        module: t.Infra.NativeOperand,
        standard: Path,
        packages: t.SequenceOf[Path],
    ) -> Path | None:
        """Locate a resident runtime file without authenticating its module.

        Returns:
            The original physical stdlib input path, when native file storage
            agrees with its source or extension loader.

        """
        if not isinstance(module, ModuleType):
            return None
        storage = vars(ModuleType)["__dict__"].__get__(module, type(module))
        native = storage.get("__spec__")
        declared = storage.get("__file__")
        loader = storage.get("__loader__")
        if (
            type(native) is not ModuleSpec
            or not isinstance(declared, str)
            or type(declared) is not str
        ):
            return None
        if not isinstance(loader, (SourceFileLoader, ExtensionFileLoader)):
            return None
        if (
            type(loader) not in {SourceFileLoader, ExtensionFileLoader}
            or type(native.origin) is not str
            or native.origin != declared
            or native.loader is not loader
            or loader.path != declared
        ):
            return None
        source = Path(declared).absolute()
        physical = source.resolve()
        if not physical.is_relative_to(standard) or any(
            physical.is_relative_to(root) for root in packages
        ):
            return None
        return source

    @classmethod
    def _elected_source_roots(
        cls,
        repository_root: Path,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
    ) -> p.Result[
        t.Pair[
            t.DictKV[str, Path],
            t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
        ]
    ]:
        """Elect the producer closure and seed its ownership registry.

        Returns:
            The elected namespace roots and their per-namespace ownership sets.

        """
        result_type = r[
            t.Pair[
                t.DictKV[str, Path],
                t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
            ]
        ]
        if all(item.attributes for item in names):
            roots: t.DictKV[str, Path] = {}
            for item in names:
                namespace = item.target.partition(".")[0]
                selected = cls._elect_namespace(namespace)
                if selected.failure:
                    return result_type.from_failure(selected)
                roots[namespace] = selected.value
        else:
            elected = cls.elected_producer_modules(repository_root, nominated=names)
            if elected.failure:
                return result_type.from_failure(elected)
            roots = dict(elected.value)
        owners: t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]] = {
            name: set() for name in roots
        }
        return result_type.ok((roots, owners))

    @classmethod
    def _observed_source_roots(
        cls,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
        roots: t.MutableMappingKV[str, Path],
        owners: t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Observe loaded bindings and elect any additional supplier namespaces.

        Args:
            names: The nominated producer selections under authentication.
            roots: Elected namespace roots, extended with observed suppliers.
            owners: Per-namespace ownership sets, extended to match ``roots``.

        Returns:
            The authenticated native observation of the loaded producer.

        """
        result_type = r[m.Infra.NativeImportObservation]

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
        return observed

    @classmethod
    def _captured_authority_states(
        cls,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
        roots: t.MappingKV[str, Path],
        observed: m.Infra.NativeImportObservation,
        trees: t.MutableMappingKV[Path, m.Cli.AtomicPhysicalTreeManifest],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Capture selected declarations and explicitly inventoried module trees.

        Args:
            names: Native lexical or complete-module selections.
            roots: Elected namespace roots owning captured directories.
            observed: Native observation naming every declared source origin.
            trees: Physical tree manifests, extended with each captured tree.
            states: Atomic file states, extended with each captured entry.

        Returns:
            Success when every producer tree and source state is captured.

        """
        result_type = r[bool]
        source_files: list[Path] = []
        for path in dict.fromkeys((
            *(
                roots[item.target.partition(".")[0]]
                for item in names
                if not item.attributes
            ),
            *(
                Path(source)
                for _, origin, declaration in observed.sources
                for source in (origin, declaration)
                if source
            ),
        )):
            if path in trees or path in states:
                continue
            if path.is_dir():
                captured_tree = FlextInfraMiseArtifactsFiles.capture_tree_sources(path)
                if captured_tree.failure:
                    return result_type.from_failure(captured_tree)
                trees[path] = captured_tree.value[0]
                states.update((item.path, item) for item in captured_tree.value[1])
            else:
                source_files.append(path)
        captured_sources = FlextInfraMiseArtifactsFiles.capture_sources(
            tuple(path for path in source_files if path not in states)
        )
        if captured_sources.failure:
            return result_type.from_failure(captured_sources)
        states.update((item.path, item) for item in captured_sources.value)
        initializers = {
            parent / c.Infra.INIT_PY
            for root in roots.values()
            if root.is_dir() and root not in trees
            for source in (root / c.Infra.INIT_PY, *source_files)
            if source.is_relative_to(root)
            for parent in source.parents
            if parent.is_relative_to(root)
        }
        for path in sorted(initializers - states.keys()):
            initializer = FlextInfraMiseArtifactsFiles.read_state(path, required=False)
            if initializer.failure:
                return result_type.from_failure(initializer)
            states[path] = initializer.value
        return result_type.ok(value=True)

    @classmethod
    def _authenticated_distribution_ownership(
        cls,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
        roots: t.MappingKV[str, Path],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        trees: t.MutableMappingKV[Path, m.Cli.AtomicPhysicalTreeManifest],
        owners: t.MutableMappingKV[str, set[m.Cli.AtomicPhysicalTreeEntry]],
    ) -> p.Result[bool]:
        """Bind installed distributions to namespaces and refuse ambiguity.

        Args:
            names: The nominated producer selections under authentication.
            roots: Elected namespace roots under ownership proof.
            states: Captured atomic file states, extended per distribution.
            trees: Captured tree manifests, extended per distribution.
            owners: Per-namespace ownership sets, updated in place.

        Returns:
            Success when every producer namespace owns one physical identity.

        """
        result_type = r[bool]
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
        return result_type.ok(value=True)

    @classmethod
    def _sealed_source_authority(
        cls,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
        roots: t.MappingKV[str, Path],
        trees: t.MappingKV[Path, m.Cli.AtomicPhysicalTreeManifest],
        states: t.MappingKV[Path, m.Cli.AtomicFileState],
        *,
        bootstrap_inputs: t.VariadicTuple[
            t.Pair[m.Cli.AtomicFileState, m.Cli.AtomicFileReceipt]
        ],
    ) -> p.Result[m.Infra.CodegenSourceAuthority]:
        """Seal receipts into the cold authority and re-prove it current.

        Args:
            names: The nominated producer selections under authentication.
            roots: Elected namespace roots sealed into the authority.
            trees: Captured physical tree manifests.
            states: Captured atomic file states awaiting their receipts.
            bootstrap_inputs: Original buffered source candidates and receipts,
                pending actual import consumption.

        Returns:
            The authenticated immutable producer closure.

        """
        result_type = r[m.Infra.CodegenSourceAuthority]

        bootstrap_receipts = {receipt.path: receipt for _, receipt in bootstrap_inputs}
        receipts: list[m.Cli.AtomicFileReceipt] = []
        for state in states.values():
            if state.path in bootstrap_receipts:
                receipts.append(bootstrap_receipts[state.path])
                continue
            measured = u.Cli.atomic_read_binary_file_receipt(
                state.path,
                required=state.device is not None,
            )
            if measured.failure:
                return result_type.from_failure(measured)
            receipts.append(measured.value)
        authenticated = cls._authenticated_receipt_files(states, tuple(receipts))
        if authenticated.failure:
            return result_type.from_failure(authenticated)
        authority = m.Infra.CodegenSourceAuthority(
            runtime=Path(sys.executable).resolve(),
            optimize=sys.flags.optimize,
            inputs=tuple(receipts),
            bootstrap_sources=tuple(state for state, _ in bootstrap_inputs),
            generator_trees=tuple(trees.values()),
            generator_modules=tuple(sorted(roots.items())),
            selections=names,
        )
        private = authority.__pydantic_private__
        if private is None:
            return result_type.fail("source authority has no Pydantic private storage")
        private["_source_birth"] = (
            id(authority),
            u.Cli.sha256_bytes(authority.model_dump_json().encode(c.DEFAULT_ENCODING)),
        )
        return cls.source_authority_current(authority).map(lambda _current: authority)

    @classmethod
    def _bootstrap_source_paths(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[frozenset[Path]]:
        """Bind bootstrap buffers to original receipts without rereading candidates.

        Returns:
            Candidate paths outside protected runtime and resource inventories.

        """
        result_type = r[frozenset[Path]]
        if authority.bootstrap_sources:
            private = authority.__pydantic_private__
            if type(authority) is not m.Infra.CodegenSourceAuthority or (
                private is None
                or private.get("_source_birth")
                != (
                    id(authority),
                    u.Cli.sha256_bytes(
                        authority.model_dump_json().encode(c.DEFAULT_ENCODING)
                    ),
                )
            ):
                return result_type.fail(
                    "bootstrap source authority lacks its original capture "
                    "identity and payload"
                )
        sources = cls.unique_states(authority.bootstrap_sources)
        if sources.failure:
            return result_type.from_failure(sources)
        by_path = {source.path: source for source in sources.value}
        matched = cls._authenticated_receipt_files(by_path, authority.inputs)
        if matched.failure:
            return result_type.from_failure(matched)
        if matched.value != set(by_path):
            return result_type.fail("bootstrap source lacks its original receipt")
        protected = {
            authority.runtime,
            *(tree.root.path for tree in authority.generator_trees),
            *(
                entry.path
                for tree in authority.generator_trees
                for entry in tree.entries
            ),
        }
        return result_type.ok(frozenset(by_path).difference(protected))

    @classmethod
    def source_authority_current(
        cls, authority: m.Infra.CodegenSourceAuthority
    ) -> p.Result[bool]:
        """Re-prove cold election and physical state without executing providers.

        Returns:
            Success only for an unchanged capturing runtime, module election,
            pinned inputs and resource trees.

        """
        modules = cls._authority_modules_current(authority)
        if modules.failure:
            return r[bool].from_failure(modules)
        return cls._authority_inputs_current(authority)

    @classmethod
    def _authority_modules_current(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[bool]:
        """Re-prove the runtime, optimization and module election identities.

        Returns:
            Success only for the capturing runtime and unchanged elections.

        """
        result_type = r[bool]
        if authority.runtime != Path(sys.executable).resolve():
            return result_type.fail("cold producer runtime changed")
        if authority.optimize != sys.flags.optimize:
            return result_type.fail("cold producer compiler optimization changed")
        for namespace, root in authority.generator_modules:
            elected = cls._elect_namespace(namespace)
            if elected.failure:
                return result_type.from_failure(elected)
            if elected.value != root:
                return result_type.fail("cold producer module election changed")
        return result_type.ok(value=True)

    @classmethod
    def _authority_inputs_current(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[bool]:
        """Re-prove producer receipts and every captured resource tree.

        Returns:
            Success for unchanged producer inputs and inventories; bootstrap
            candidates retain their original buffered identities until consumed.

        """
        result_type = r[bool]
        bootstrap = cls._bootstrap_source_paths(authority)
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        for expected in authority.inputs:
            if expected.path in bootstrap.value:
                continue
            observed = u.Cli.atomic_read_binary_file_receipt(
                expected.path,
                required=expected.device is not None,
            )
            if observed.failure:
                return result_type.from_failure(observed)
            if observed.value != expected:
                return result_type.fail(
                    f"cold producer source changed: {expected.path}"
                )
        for tree in authority.generator_trees:
            observed = u.Cli.atomic_inventory_physical_tree(tree.root.path)
            if observed.failure:
                return result_type.from_failure(observed)
            if observed.value != tree:
                previous = {entry.path: entry for entry in tree.entries}
                current = {entry.path: entry for entry in observed.value.entries}
                changed = sorted(
                    path
                    for path in previous.keys() | current.keys()
                    if previous.get(path) != current.get(path)
                )
                return result_type.fail(
                    f"cold producer resource tree changed: {tree.root.path}; "
                    f"root_changed={tree.root != observed.value.root} "
                    f"changed_count={len(changed)} first={changed[:3]}"
                )
        return result_type.ok(value=True)

    @classmethod
    def authority_inputs(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Read producer payloads and retain original bootstrap candidate buffers.

        Returns:
            Protected inputs read through their authenticated descriptors and
            candidate inputs carrying their original authenticated bytes.

        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileState]]
        bootstrap = cls._bootstrap_source_paths(authority)
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        buffered = {
            source.path: source
            for source in authority.bootstrap_sources
            if source.path in bootstrap.value
        }
        states: list[m.Cli.AtomicFileState] = []
        for receipt in authority.inputs:
            if receipt.path in buffered:
                states.append(buffered[receipt.path])
                continue
            if receipt.device is None:
                current = u.Cli.atomic_read_binary_file_receipt(receipt.path)
                if current.failure:
                    return result_type.from_failure(current)
                if current.value != receipt:
                    return result_type.fail(
                        f"cold producer absent input changed: {receipt.path}",
                    )
                content = None
            elif receipt.size is not None:
                with u.Cli.atomic_binary_file_reader(receipt) as reader:
                    content = reader.read_range(0, receipt.size)
            else:
                return result_type.fail(
                    f"cold producer pinned input has no physical size: {receipt.path}",
                )
            states.append(
                m.Cli.AtomicFileState.model_validate({
                    **receipt.model_dump(
                        include=set(m.Cli.AtomicFileState.model_fields),
                    ),
                    "content": content,
                }),
            )
        return result_type.ok(tuple(states))

    @classmethod
    def admit_native_reference(
        cls,
        request: m.Infra.NativeImportRequest,
        original: m.Infra.NativeImportObservation,
        imported: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Seal an imported reference only after complete executable and input proof.

        Returns:
            The live reference after trace, binding, source and runtime admission.

        """
        result_type = r[m.Infra.NativeImportReference]
        observed = FlextInfraWorkspaceNativeReference.capture(request.modules)
        if observed.failure:
            return result_type.from_failure(observed)
        return cls._observed_native_reference(request, observed.value)

    @classmethod
    def _observed_native_reference(
        cls,
        request: m.Infra.NativeImportRequest,
        snapshot: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Prove one loaded-producer observation against the cold native import.

        The observation must still match the sealed authority inputs; the cold
        child then supplies the independent reference it is compared with.

        Returns:
            The sealed reference, or the first source or runtime failure.

        """
        result_type = r[m.Infra.NativeImportReference]
        observed = FlextInfraWorkspaceNativeReference.authored_sources_current(
            snapshot, request.source_authority.inputs
        ).map(lambda _: snapshot)
        if observed.failure:
            return result_type.from_failure(observed)
        cold = cls._cold_native_observation(request)
        if cold.failure:
            return result_type.from_failure(cold)
        reference = cold.value
        consumed = cls._executed_source_authority(request, reference, observed.value)
        if consumed.failure:
            return result_type.from_failure(consumed)
        return (
            FlextInfraWorkspaceNativeReference
            .compare(original, imported)
            .flat_map(
                lambda _: FlextInfraWorkspaceNativeReference.authored_sources_current(
                    imported, consumed.value.inputs
                )
            )
            .flat_map(lambda _: cls._native_runtime_current(request))
            .flat_map(lambda _: cls.source_authority_current(consumed.value))
        )
        return proof.flat_map(
            lambda _: cls._seal_native_reference(reference, consumed.value)
        )

    @classmethod
    def _cold_native_observation(
        cls,
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[m.Infra.NativeImportObservation]:
        """Admit the pinned inputs, then read the complete cold child outcome.

        Returns:
            The original native import observation, or the first admission or
            process failure.

        """
        result_type = r[m.Infra.NativeImportObservation]
        admitted = cls._native_inputs_current(request)
        if admitted.failure:
            return result_type.from_failure(admitted)
        consumer = FlextInfraValidateFreshImport(
            repository_root=request.repository_root,
            runtime_root=request.runtime_root,
        )
        output = consumer.native_reference_probe(request)
        if output.failure:
            return result_type.from_failure(output)
        if not u.Cli.process_succeeded(output.value.outcome) or output.value.stderr:
            return result_type.fail(
                f"cold native source import failed: {output.value.outcome}\n"
                f"stdout:\n{output.value.stdout}\nstderr:\n{output.value.stderr}",
            )
        return result_type.ok(
            m.Infra.NativeImportObservation.model_validate_json(output.value.stdout)
        )

    @staticmethod
    def _seal_native_reference(
        reference: m.Infra.NativeImportObservation,
        authority: m.Infra.CodegenSourceAuthority,
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Issue one live reference after full physical and executable admission.

        Returns:
            The exact reference with its Pydantic-owned private birth storage.

        """
        return r[m.Infra.NativeImportReference].ok(
            m.Infra.NativeImportReference(
                **reference.model_dump(),
                source_authority=authority,
            ),
        )

    @classmethod
    def reference_current(
        cls,
        reference: m.Infra.NativeImportReference,
    ) -> p.Result[bool]:
        """Re-prove a native reference by value against its sealed authority.

        A reference is a value: the same producer is current on every path
        (live, journaled, recovered) exactly when its source authority still
        proves the capturing runtime, module election and pinned inputs.

        Returns:
            Success only while the reference's source authority is current.

        """
        if type(reference) is not m.Infra.NativeImportReference:
            return r[bool].fail("native reference is not an admitted native import")
        return cls.source_authority_current(reference.source_authority)

    @classmethod
    def _executed_source_authority(
        cls,
        request: m.Infra.NativeImportRequest,
        observed: m.Infra.NativeImportObservation,
        original: m.Infra.NativeImportObservation,
    ) -> p.Result[m.Infra.CodegenSourceAuthority]:
        """Bind pre-execution child receipts to the original elected providers.

        Returns:
            The complete input authority after physical and execution-trace proof.

        """
        result_type = r[m.Infra.CodegenSourceAuthority]
        if not observed.executed_sources:
            return result_type.fail(
                "cold native import has no executed-source receipts"
            )
        consumed = cls._executed_sources_current(
            request.source_authority, observed.executed_sources
        )
        if consumed.failure:
            return result_type.from_failure(consumed)
        bootstrap = cls._bootstrap_source_paths(request.source_authority)
        if bootstrap.failure:
            return result_type.from_failure(bootstrap)
        executed = {receipt.path for receipt in observed.executed_sources}
        for supplier, origin, declaration in observed.sources:
            if supplier.partition("::")[0].partition(".")[0] in sys.stdlib_module_names:
                continue
            for source in (origin, declaration):
                if (
                    source
                    and Path(source).suffix == c.Infra.EXT_PYTHON
                    and Path(source) not in executed
                ):
                    return result_type.fail(
                        f"cold producer source was not compiled by its loader: {source}"
                    )
        graph_sources = {
            Path(source)
            for snapshot in (original, observed)
            for _, origin, declaration in snapshot.sources
            for source in (origin, declaration)
            if source
        }
        required = graph_sources | executed
        authority = request.source_authority.model_copy(
            update={
                "inputs": tuple(
                    receipt
                    for receipt in consumed.value
                    if receipt.path not in bootstrap.value or receipt.path in required
                ),
                "bootstrap_sources": (),
            }
        )
        return cls.source_authority_current(authority).map(lambda _: authority)

    @staticmethod
    def _executed_sources_current(
        authority: m.Infra.CodegenSourceAuthority,
        receipts: t.VariadicTuple[m.Cli.AtomicFileReceipt],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileReceipt]]:
        """Authenticate every child receipt within the original physical election.

        Returns:
            The original and newly consumed receipts with unchanged physical bytes.

        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileReceipt]]
        standard = FlextInfraWorkspaceEnvironmentProvenance.standard_library_root()
        packages = (
            FlextInfraWorkspaceEnvironmentProvenance.standard_library_package_roots()
        )
        roots = tuple(root for _, root in authority.generator_modules)
        pinned = {receipt.path: receipt for receipt in authority.inputs}
        executed: t.MutableMappingKV[Path, m.Cli.AtomicFileReceipt] = {}
        for receipt in receipts:
            path = receipt.path
            physical = path.resolve()
            runtime_source = physical.is_relative_to(standard) and not any(
                physical.is_relative_to(root) for root in packages
            )
            if not (
                runtime_source
                or any(
                    physical.is_relative_to(root.resolve())
                    if root.is_dir()
                    else physical == root.resolve()
                    for root in roots
                )
            ):
                return result_type.fail(
                    f"cold source escaped its elected provider: {path}"
                )
            previous = executed.get(path, pinned.get(path))
            if previous is not None and previous != receipt:
                return result_type.fail(f"cold source input changed: {path}")
            current = u.Cli.atomic_read_binary_file_receipt(path, required=True)
            if current.failure:
                return result_type.from_failure(current)
            if current.value != receipt:
                return result_type.fail(f"cold executed source changed: {path}")
            executed[path] = receipt
        return result_type.ok(tuple({**pinned, **executed}.values()))

    @classmethod
    def native_inputs_current(
        cls,
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[bool]:
        """Recheck the pinned inputs and the executing physical runtime.

        Returns:
            Success when source, environment and interpreter identities agree.

        """
        if request.modules != request.source_authority.selections or (
            request.import_roots
            != tuple(
                dict.fromkeys(
                    root.parent
                    for _, root in request.source_authority.generator_modules
                )
            )
        ):
            return r[bool].fail(
                "native import request differs from its elected source authority"
            )
        bootstrap = cls._bootstrap_source_paths(request.source_authority)
        if bootstrap.failure:
            return r[bool].from_failure(bootstrap)
        states = cls.unique_states(request.inputs)
        if states.failure:
            return r[bool].from_failure(states)
        by_path = {state.path: state for state in states.value}
        matched = cls._authenticated_receipt_files(
            by_path, request.source_authority.inputs
        )
        if matched.failure:
            return r[bool].from_failure(matched)
        if matched.value != set(by_path) or matched.value != {
            receipt.path for receipt in request.source_authority.inputs
        }:
            return r[bool].fail(
                "native import inputs differ from their complete captured receipts"
            )
        return (
            cls
            .source_authority_current(request.source_authority)
            .flat_map(
                lambda _: FlextInfraMiseArtifactsVerification.states_current(
                    tuple(
                        state
                        for state in request.inputs
                        if state.path not in bootstrap.value
                    )
                )
            )
            .flat_map(lambda _: cls._native_runtime_current(request))
        )

    @staticmethod
    def _native_runtime_current(
        request: m.Infra.NativeImportRequest,
    ) -> p.Result[bool]:
        """Re-prove the request's original physical environment and interpreter.

        Returns:
            Success only for unchanged environment, prefix and compiler mode.

        """
        environment = u.Infra.runtime_environment_dir(
            request.repository_root,
            runtime_root=request.runtime_root,
        )
        runtime = u.Infra.runtime_python(
            request.repository_root,
            runtime_root=request.runtime_root,
        )
        actual_environment = environment.absolute()
        actual_prefix = Path(sys.prefix).absolute()
        actual_runtime = runtime.resolve()
        if (
            environment.is_symlink()
            or actual_environment != actual_prefix
            or not runtime.is_file()
            or actual_runtime != request.source_authority.runtime
            or sys.flags.optimize != request.source_authority.optimize
        ):
            return r[bool].fail(
                "native reference runtime authority differs: "
                f"environment={actual_environment} symlink={environment.is_symlink()} "
                f"prefix={actual_prefix} runtime={actual_runtime} "
                f"runtime_file={runtime.is_file()} "
                f"expected_runtime={request.source_authority.runtime} "
                f"optimize={sys.flags.optimize} "
                f"expected_optimize={request.source_authority.optimize}"
            )
        return r[bool].ok(value=True)

    @classmethod
    def capture_producer(
        cls,
        repository_root: Path,
        *,
        entrypoint: p.AttributeProbe,
        collaborators: t.SequenceOf[p.AttributeProbe] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Authenticate the loaded producer against its cold physical authority.

        Returns:
            The authenticated producer phase analysis snapshot.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        selection = FlextInfraWorkspaceNativeReference.producer_selections(
            entrypoint,
            collaborators,
        )
        if selection.failure:
            return result_type.from_failure(selection)
        names = selection.value
        environment = Path(sys.prefix).absolute()
        if (
            environment.name != c.Infra.ENVIRONMENT_DIRECTORY
            or environment.is_symlink()
        ):
            return result_type.fail(
                f"producer runtime is not a physical managed environment: {environment}"
            )
        runtime_root = environment.parent
        reference = cls._capture_producer_reference(
            repository_root, runtime_root, names
        )
        if reference.failure:
            return result_type.from_failure(reference)
        consumed = cls.authority_inputs(reference.value.source_authority)
        if consumed.failure:
            return result_type.from_failure(consumed)
        authority = reference.value.source_authority
        snapshot = m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            files=(),
            inputs=consumed.value,
            generator_trees=authority.generator_trees,
            generator_modules=authority.generator_modules,
            generator_reference=reference.value,
        )
        return cls.producer_current(snapshot).map(lambda _current: snapshot)

    @classmethod
    def _capture_producer_reference(
        cls,
        repository_root: Path,
        runtime_root: Path,
        names: t.VariadicTuple[m.Infra.SourceClassReference],
    ) -> p.Result[m.Infra.NativeImportReference]:
        """Bind one elected source epoch to its independent native import.

        Returns:
            The live admitted reference or the first source/import failure.

        """
        result_type = r[m.Infra.NativeImportReference]
        u.Cli.info(
            f"stage=native-source-authority selections={len(names)} "
            f"runtime={runtime_root}",
        )
        sealed = cls._observed_source_authority(runtime_root, names)
        if sealed.failure:
            return result_type.from_failure(sealed)
        authority, observation = sealed.value
        u.Cli.info(
            f"stage=native-source-authority-complete "
            f"providers={len(authority.generator_modules)} "
            f"inputs={len(authority.inputs)}",
        )
        inputs = cls.authority_inputs(authority)
        if inputs.failure:
            return result_type.from_failure(inputs)
        request = m.Infra.NativeImportRequest(
            repository_root=repository_root,
            runtime_root=runtime_root,
            modules=names,
            inputs=inputs.value,
            source_authority=authority,
            import_roots=tuple(
                dict.fromkeys(
                    root.parent for _name, root in authority.generator_modules
                )
            ),
        )
        # The authority already observed these exact selections; a second
        # capture could only repeat it.
        return cls._observed_native_reference(request, observation)

    @classmethod
    def _distribution_providers(
        cls,
        distribution: Distribution,
        roots: t.MappingKV[str, Path],
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        trees: t.MutableMappingKV[Path, m.Cli.AtomicPhysicalTreeManifest],
    ) -> p.Result[t.MappingKV[str, t.VariadicTuple[m.Cli.AtomicPhysicalTreeEntry]]]:
        """Authenticate native metadata and derive physical namespace ownership.

        Returns:
            Each owned namespace bound to this descriptor's metadata identities.

        """
        result_type = r[
            t.MappingKV[str, t.VariadicTuple[m.Cli.AtomicPhysicalTreeEntry]]
        ]
        declared = distribution.files
        if declared is None:
            return result_type.fail("producer distribution has no native file manifest")
        paths = tuple(
            Path(str(distribution.locate_file(item))).absolute() for item in declared
        )
        root_depths = {len(root.parts) for root in roots.values()}
        # Native prefixes preserve anchor, case and lexical parent semantics.
        ownership_prefixes = {
            Path(*parts[:depth])
            for parts in (path.parts for path in paths)
            for depth in root_depths
        }
        namespaces = {
            namespace for namespace, root in roots.items() if root in ownership_prefixes
        }
        editable = cls._editable_distribution_namespaces(paths, roots)
        if editable.failure:
            return result_type.from_failure(editable)
        namespaces.update(editable.value[0])
        if not namespaces:
            return result_type.ok(
                dict[str, t.VariadicTuple[m.Cli.AtomicPhysicalTreeEntry]]()
            )
        captured = cls._captured_distribution_inputs(
            distribution, paths, tuple(editable.value[1].values())
        )
        if captured.failure:
            return result_type.from_failure(captured)
        sources = cls.unique_states((*states.values(), *captured.value[1]))
        if sources.failure:
            return result_type.from_failure(sources)
        trees.update((tree.root.path, tree) for tree in captured.value[0])
        states.update((item.path, item) for item in sources.value)
        return result_type.ok(
            dict.fromkeys(namespaces, tuple(tree.root for tree in captured.value[0]))
        )

    @staticmethod
    def _editable_distribution_namespaces(
        paths: t.VariadicTuple[Path], roots: t.MappingKV[str, Path]
    ) -> p.Result[t.Pair[set[str], t.DictKV[Path, m.Cli.AtomicFileState]]]:
        """Elect editable namespaces through their physical native metadata.

        Returns:
            The elected namespaces and every metadata/source input used.

        """
        result_type = r[t.Pair[set[str], t.DictKV[Path, m.Cli.AtomicFileState]]]
        namespaces: set[str] = set()
        elected: t.DictKV[Path, m.Cli.AtomicFileState] = {}
        for path in paths:
            if (
                path.name != c.Infra.DISTRIBUTION_DIRECT_URL_FILE
                or not path.parent.name.endswith(".dist-info")
            ):
                continue
            observed = FlextInfraMiseArtifactsFiles.read_state(path, required=True)
            if observed.failure:
                return result_type.from_failure(observed)
            state = observed.value
            parsed = FlextInfraMiseArtifactsFiles.editable_project_source(state)
            if parsed.failure:
                return result_type.from_failure(parsed)
            for project_source, metadata in parsed.value:
                namespace = metadata.package_name
                if namespace in roots:
                    if not roots[namespace].is_relative_to(project_source.path.parent):
                        return result_type.fail(
                            "producer source is outside declared editable root: "
                            f"{namespace}"
                        )
                    namespaces.add(namespace)
                    elected[state.path] = state
                    elected[project_source.path] = project_source
        return result_type.ok((namespaces, elected))

    @classmethod
    def _captured_distribution_inputs(
        cls,
        distribution: Distribution,
        paths: t.VariadicTuple[Path],
        elected: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
            t.VariadicTuple[m.Cli.AtomicFileState],
        ]
    ]:
        """Capture one elected distribution and reject conflicting input epochs.

        Returns:
            Its authenticated manifests and complete physical source states.

        """
        result_type = r[
            t.Pair[
                t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
                t.VariadicTuple[m.Cli.AtomicFileState],
            ]
        ]
        captured = FlextInfraMiseArtifactsFiles.capture_distribution_sources(
            distribution
        )
        if captured.failure:
            return result_type.from_failure(captured)
        if captured.value[2] != paths:
            return result_type.fail(
                "producer distribution file manifest changed while capturing ownership"
            )
        sources = cls.unique_states((*elected, *captured.value[1]))
        if sources.failure:
            return result_type.from_failure(sources)
        return result_type.ok((captured.value[0], sources.value))

    @classmethod
    def producer_current(
        cls,
        producer: m.Infra.CodegenPhaseAnalysis,
        *,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Authenticate the original epoch and relevant invocation-owned effects.

        Returns:
            Success only for unchanged inputs and native code, with changed
            physical sources accounted for by authenticated own outputs.

        """
        if not producer.inputs or producer.generator_reference is None:
            return r[bool].fail("producer context lacks authenticated source closure")
        states = cls.unique_states(producer.inputs)
        if states.failure:
            return r[bool].from_failure(states)
        by_path = {state.path: state for state in states.value}
        authority = producer.generator_reference.source_authority
        source_paths = {item.path for item in authority.inputs}
        own_outputs = tuple(
            output
            for output in outputs
            if output.path in source_paths
            or any(
                output.path.is_relative_to(tree.root.path)
                for tree in authority.generator_trees
            )
        )
        output_paths = {output.path for output in own_outputs}
        authenticated = cls._authenticated_receipt_files(by_path, authority.inputs)
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        # The native authority physically reauthenticates every matching receipt.
        # Extra planner inputs retain their own immediate snapshot proof.
        retained = tuple(
            state
            for state in states.value
            if state.path not in output_paths and state.path not in authenticated.value
        )
        current = FlextInfraMiseArtifactsComparison.states_current(retained)
        if current.failure:
            return current
        return cls.producer_trees_current(
            producer.generator_trees,
            own_outputs,
            modules=producer.generator_modules,
            reference=producer.generator_reference,
        )

    @staticmethod
    def _authenticated_receipt_files(
        by_path: t.MappingKV[Path, m.Cli.AtomicFileState],
        receipts: t.VariadicTuple[m.Cli.AtomicFileReceipt],
    ) -> p.Result[set[Path]]:
        """Bind buffered inputs to receipts before their native physical proof.

        Args:
            by_path: Captured states indexed by their physical path.
            receipts: Original authority receipts, including owned output preimages.

        Returns:
            Paths whose exact buffered state agrees with its original receipt.

        """
        result_type = r[set[Path]]
        covered: set[Path] = set()
        identity_fields = set(m.Cli.AtomicFileIdentity.model_fields)
        for receipt in receipts:
            state = by_path.get(receipt.path)
            if state is None:
                continue
            content = state.content
            if (
                state.model_dump(include=identity_fields),
                len(content) if content is not None else None,
                u.Cli.sha256_bytes(content) if content is not None else None,
            ) != (
                receipt.model_dump(include=identity_fields),
                receipt.size,
                receipt.sha256,
            ):
                return result_type.fail(
                    f"producer input differs from captured receipt: {state.path}"
                )
            covered.add(state.path)
        return result_type.ok(covered)

    @staticmethod
    def producer_trees_current(
        trees: t.VariadicTuple[m.Cli.AtomicPhysicalTreeManifest],
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
        *,
        modules: t.VariadicTuple[t.Pair[str, Path]],
        reference: m.Infra.NativeImportReference | None = None,
    ) -> p.Result[bool]:
        """Check the original native epoch without minting namespace-local proofs.

        Returns:
            Success only for the unchanged native epoch, its membership and
            its re-captured loaded bindings.

        """
        if reference is None:
            return r[bool].fail("producer closure lacks its pre-planning native epoch")
        birth = FlextInfraCodegenPreconditions.reference_current(reference)
        if birth.failure:
            return birth
        if (
            tuple(trees) != reference.source_authority.generator_trees
            or modules != reference.source_authority.generator_modules
        ):
            return r[bool].fail("producer native epoch belongs to another election")

        current = FlextInfraCodegenPreconditions.authority_current(
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

    @staticmethod
    def _authorized_outputs_current(
        outputs: t.SequenceOf[m.Infra.CodegenJournalSource],
    ) -> p.Result[bool]:
        """Authenticate every physical effect before permitting source substitution.

        Returns:
            The first physical mismatch or the exact recorded effects.

        """
        for expected in outputs:
            state = FlextInfraMiseArtifactsFiles.read_state(
                expected.path, required=expected.sha256 is not None
            )
            if state.failure:
                return r[bool].from_failure(state)
            recorded = FlextInfraMiseArtifactsJournalRelocation.source_record(
                expected.phase, state.value, previous=expected
            )
            if recorded.failure:
                return r[bool].from_failure(recorded)
            if recorded.value != expected:
                return r[bool].fail(
                    f"native authorized output changed: {expected.path}"
                )
        return r[bool].ok(value=True)

    @classmethod
    def authority_current(
        cls,
        authority: m.Infra.CodegenSourceAuthority,
        *,
        outputs: t.SequenceOf[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[bool]:
        """Validate physical source authority and only authenticated own effects.

        Returns:
            The original input/election proof, without creating execution authority.

        """
        modules = cls._authority_modules_current(authority)
        if modules.failure:
            return modules
        if not authority.inputs or authority.runtime not in {
            item.path for item in authority.inputs
        }:
            return r[bool].fail(
                "native source authority lacks its physical interpreter"
            )
        published = cls._authorized_outputs_current(outputs)
        if published.failure:
            return published
        output_paths = {item.path for item in outputs}
        for receipt in authority.inputs:
            if receipt.path in output_paths and receipt.path != authority.runtime:
                continue
            current = u.Cli.atomic_read_binary_file_receipt(
                receipt.path, required=receipt.device is not None
            )
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != receipt:
                return r[bool].fail(f"native source authority changed: {receipt.path}")
        return cls.source_trees_current(
            authority.generator_trees,
            tuple(outputs),
            modules=authority.generator_modules,
        )

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
        if not FlextInfraMiseArtifactsComparison.same_directory_identity(
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
            if not FlextInfraMiseArtifactsComparison.same_directory_identity(
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
        distribution_name = config.Infra.codegen.infra_repository.distribution
        matches = u.installed_distributions(name=distribution_name)
        if len(matches) != 1:
            return result_type.fail(
                f"rendering engine distribution count mismatch: "
                f"distribution={distribution_name} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        direct_url = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        receipt: m.Infra.DirectUrlReceipt | None = None
        if direct_url is not None:
            parsed = r[m.Infra.DirectUrlReceipt].create_from_callable(
                partial(m.Infra.DirectUrlReceipt.model_validate_json, direct_url)
            )
            if parsed.failure:
                return result_type.from_failure(parsed)
            receipt = parsed.value
        if (
            receipt is not None
            and receipt.dir_info is not None
            and receipt.dir_info.editable
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
                    distribution_name=distribution_name,
                )
            )
        )

    @staticmethod
    def _locked_engine_current(
        distribution: Distribution,
        direct_url: str | None,
        locked: m.Infra.LockedEnvironment,
        *,
        distribution_name: str,
    ) -> p.Result[bool]:
        """Compare the installed engine to the unique typed committed pin.

        Returns:
            Success for an unpinned/editable engine or its exact artifact origin.

        """
        result_type = r[bool]
        pinned = tuple(
            item for item in locked.package if item.name == distribution_name
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
            distribution_name, item, direct_url
        )
        if origin.failure:
            return origin
        if item.source.registry is not None and distribution.version != item.version:
            return result_type.fail(
                f"rendering engine {distribution_name}@{distribution.version} "
                f"is not the locked pin {distribution_name}@{item.version}: "
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
        *,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Bind the original producer epoch to the current admitted planner inputs.

        Returns:
            The planner's exact inputs and files with authenticated producer metadata.

        """
        current = cls.producer_current(producer, outputs=outputs)
        if current.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(current)
        return cls.compose_producer_analysis(analysis, producer, outputs=outputs)

    @classmethod
    def compose_producer_analysis(
        cls,
        analysis: m.Infra.CodegenPhaseAnalysis,
        producer: m.Infra.CodegenPhaseAnalysis,
        *,
        outputs: t.VariadicTuple[m.Infra.CodegenJournalSource] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Compose snapshots and producer metadata without granting authority.

        Returns:
            The planner analysis with its original producer metadata, or a
            conflicting snapshot failure.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        # Earlier owned publications may replace producer source bytes. Planner
        # inputs still agree among themselves; the native epoch is never rewritten.
        output_paths = {output.path for output in outputs}
        sources = cls.unique_states((
            *(state for state in producer.inputs if state.path not in output_paths),
            *analysis.inputs,
            *(source for plan in analysis.files for source in plan.source_states),
        ))
        if sources.failure:
            return result_type.from_failure(sources)
        return result_type.ok(
            analysis.model_copy(
                update={
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
        by_path: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
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
            FlextInfraMiseArtifactsComparison.states_current
        )
        if source_barrier.failure:
            return source_barrier
        destination_barrier = FlextInfraMiseArtifactsComparison.states_current(
            destinations,
        )
        if destination_barrier.failure:
            return destination_barrier
        return FlextInfraMiseArtifactsComparison.sources(plan)


__all__: list[str] = ["FlextInfraCodegenPreconditions"]
