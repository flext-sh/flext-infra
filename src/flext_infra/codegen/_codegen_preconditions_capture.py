"""Cold producer source-authority capture mixin for generation preconditions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
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

from flext_infra import c, config, m, r, t, u
from flext_infra.codegen import FlextInfraMiseArtifactsFiles
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from flext_infra.workspace.native_reference import FlextInfraWorkspaceNativeReference

if TYPE_CHECKING:
    from importlib.metadata import Distribution

    from flext_infra import p


class FlextInfraCodegenPreconditionsCaptureMixin:
    """Elect physical producer providers and seal their cold source authority."""

    if TYPE_CHECKING:

        @staticmethod
        def unique_states(
            states: t.VariadicTuple[m.Cli.AtomicFileState],
        ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]: ...

        @staticmethod
        def _authenticated_receipt_files(
            by_path: t.MappingKV[Path, m.Cli.AtomicFileState],
            receipts: t.VariadicTuple[m.Cli.AtomicFileReceipt],
        ) -> p.Result[set[Path]]: ...

        @classmethod
        def source_authority_current(
            cls, authority: m.Infra.CodegenSourceAuthority
        ) -> p.Result[bool]: ...

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
        return cls.observed_source_authority(repository_root, tuple(nominated)).map(
            itemgetter(0)
        )

    @classmethod
    def observed_source_authority(
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


__all__: list[str] = ["FlextInfraCodegenPreconditionsCaptureMixin"]
