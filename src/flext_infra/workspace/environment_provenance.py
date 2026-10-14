"""Fail-closed validation of local editables and locked CI build provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import sys
import sysconfig
from base64 import urlsafe_b64encode
from functools import lru_cache
from importlib.machinery import BuiltinImporter, FrozenImporter
from json import dumps
from pathlib import Path
from sys import modules
from typing import TYPE_CHECKING
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from flext_infra import c, m, p, r, t, u
from flext_infra._utilities._pyproject.document import (
    FlextInfraUtilitiesPyprojectDocument,
)
from flext_infra.workspace import (
    FlextInfraFlextBindingService,
    FlextInfraWorkspaceDetector,
)

if TYPE_CHECKING:
    from importlib.metadata import Distribution


class FlextInfraWorkspaceEnvironmentProvenance:
    """Bind installed packages to live local or immutable CI workspace sources."""

    @classmethod
    def member_project_declaration(
        cls,
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        *,
        lock_state: m.Cli.AtomicFileState | None = None,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Capture the authenticated live or installed producer declaration.

        Returns:
            Declaration bytes authenticated by editable ownership or the
            installed locked artifact's RECORD and producer build contract.
        """
        result = r[m.Cli.AtomicFileState]
        matches = u.installed_distributions(name=repository.distribution)
        if len(matches) != 1:
            return result.fail(
                "member declaration needs one installed distribution: "
                f"{repository.distribution}",
            )
        distribution = matches[0]
        raw = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        if raw is None:
            return result.fail(
                "member declaration lacks PEP 610 provenance: "
                f"{repository.distribution}",
            )
        receipt = r[m.Infra.DirectUrlReceipt].create_from_callable(
            lambda: m.Infra.DirectUrlReceipt.model_validate_json(raw, strict=True),
        )
        if receipt.failure:
            return result.from_failure(receipt)
        if receipt.value.dir_info is not None and receipt.value.dir_info.editable:
            if not repository.editable:
                return result.fail(
                    "member editable installation differs from declaration: "
                    f"{repository.distribution}",
                )
            authenticated = cls.validate_editable_installation(
                repository,
                repository_root,
                distribution,
                receipt.value,
            )
            if authenticated.failure:
                return result.from_failure(authenticated)
            return u.Cli.atomic_read_binary_file_state(
                repository_root / repository.path / c.PYPROJECT_FILENAME,
                required=True,
            )
        if lock_state is None:
            lock_read = u.Cli.atomic_read_binary_file_state(
                repository_root / c.Infra.UV_LOCK_FILENAME,
                required=True,
            )
            if lock_read.failure:
                return result.from_failure(lock_read)
            lock_state = lock_read.value
        if (
            lock_state.path != (repository_root / c.Infra.UV_LOCK_FILENAME).resolve()
            or lock_state.content is None
        ):
            return result.fail("member artifact needs its captured root lock")
        locked_document = u.Cli.toml_parse_text(
            lock_state.content.decode(c.DEFAULT_ENCODING),
        )
        if locked_document is None:
            return result.fail("captured member artifact lock is invalid TOML")
        locked_payload = u.Cli.toml_as_mapping(locked_document)
        if locked_payload is None:
            return result.fail("captured member artifact lock is not a mapping")
        locked = r[m.Infra.LockedEnvironment].create_from_callable(
            lambda: m.Infra.LockedEnvironment.model_validate_json(dumps(locked_payload)),
        )
        if locked.failure:
            return result.from_failure(locked)
        candidates = tuple(
            item
            for item in locked.value.package
            if u.Infra.dep_name(item.name)
            == u.Infra.dep_name(repository.distribution)
            and item.version == distribution.version
        )
        if len(candidates) != 1 or candidates[0].source.git is None:
            return result.fail(
                "member declaration requires its installed locked Git artifact: "
                f"{repository.distribution}",
            )
        origin = cls.locked_origin_verdict(
            repository.distribution,
            candidates[0],
            raw,
        )
        if origin.failure:
            return result.from_failure(origin)
        if u.Infra.git_remote_identity(receipt.value.url) != u.Infra.git_remote_identity(
            repository.url
        ):
            return result.fail(
                "member artifact origin differs from declared repository: "
                f"{repository.distribution}",
            )
        files = distribution.files
        if files is None:
            return result.fail(
                f"member artifact has no RECORD inventory: {repository.distribution}",
            )
        resources = tuple(item for item in files if item.name == c.PYPROJECT_FILENAME)
        if len(resources) != 1:
            return result.fail(
                "member artifact needs one packaged producer declaration: "
                f"{repository.distribution}; publish its generated wheel first",
            )
        resource = resources[0]
        path = Path(str(distribution.locate_file(resource))).resolve()
        if not path.is_relative_to(Path(sys.prefix).resolve()):
            return result.fail(
                "member declaration escapes its installed environment: "
                f"{repository.distribution}",
            )
        captured = u.Cli.atomic_read_binary_file_state(path, required=True)
        if captured.failure:
            return result.from_failure(captured)
        state = captured.value
        if (
            state.content is None
            or resource.hash is None
            or resource.hash.mode != "sha256"
            or resource.size != len(state.content)
            or resource.hash.value
            != urlsafe_b64encode(bytes.fromhex(u.Cli.sha256_bytes(state.content)))
            .rstrip(b"=")
            .decode("ascii")
        ):
            return result.fail(
                "member producer declaration differs from its RECORD: "
                f"{repository.distribution}",
            )
        producer = FlextInfraUtilitiesPyprojectDocument._parsed_pyproject(
            state.content.decode(c.DEFAULT_ENCODING),
        )
        if producer.failure:
            return result.from_failure(producer)
        document, name, _payload = producer.value
        force_include = u.Cli.toml_table_path(
            document,
            ("tool", "hatch", "build", "targets", "wheel", "force-include"),
        )
        if (
            u.Infra.dep_name(name) != u.Infra.dep_name(repository.distribution)
            or force_include is None
            or u.Cli.toml_value(force_include, c.PYPROJECT_FILENAME)
            != resource.as_posix()
        ):
            return result.fail(
                "packaged declaration differs from its producer build contract: "
                f"{repository.distribution}",
            )
        return result.ok(state)

    @staticmethod
    def _module_source(module_name: str) -> p.Result[Path]:
        """Observe native module origin; the isolated import authenticates election."""
        module = modules.get(module_name)
        if module is None:
            return r[Path].fail(
                f"producer source module is not registered: {module_name}"
            )
        namespace = vars(module)
        native = namespace.get("__spec__")
        if native is None or modules.get(native.name) is not module:
            return r[Path].fail(f"producer module lacks its native spec: {module_name}")
        if namespace.get("__loader__") is not native.loader:
            return r[Path].fail(
                f"producer module loader differs from native spec: {module_name}"
            )
        interpreter = Path(sys.executable).resolve()
        if native.origin in {"built-in", "frozen"}:
            importer = (
                BuiltinImporter if native.origin == "built-in" else FrozenImporter
            )
            expected = importer.find_spec(native.name)
            if expected is None or native.loader is not expected.loader:
                return r[Path].fail(
                    f"producer native interpreter loader differs: {module_name}"
                )
            if native.origin == "frozen" and (
                native.loader_state != expected.loader_state
                or getsourcefile(module) != native.loader_state.filename
            ):
                return r[Path].fail(
                    f"producer frozen source differs from interpreter: {module_name}"
                )
            return r[Path].ok(interpreter)
        if native.origin is None:
            locations = native.submodule_search_locations
            if locations is None or tuple(namespace.get("__path__", ())) != tuple(
                locations
            ):
                return r[Path].fail(
                    f"producer namespace paths differ from native spec: {module_name}"
                )
            if len(locations) != 1:
                return r[Path].fail(
                    f"producer namespace requires explicit multiple physical origins: {module_name}={tuple(locations)}",
                )
            root = Path(locations[0]).absolute()
            physical = u.Cli.atomic_plan_directory_chain(root)
            if physical.failure:
                return r[Path].from_failure(physical)
            return r[Path].ok(root)
        if namespace.get("__file__") != native.origin:
            return r[Path].fail(
                f"producer module file differs from native origin: {module_name}"
            )
        origin = Path(native.origin).absolute()
        if native.name.partition(".")[0] in sys.stdlib_module_names:
            base = Path(sys.base_prefix).resolve()
            standard = Path(
                sysconfig.get_path(
                    "stdlib",
                    vars={
                        "base": sys.base_prefix,
                        "platbase": sys.base_exec_prefix,
                    },
                )
            ).resolve()
            if not interpreter.is_relative_to(
                base
            ) or not origin.resolve().is_relative_to(standard):
                return r[Path].fail(
                    f"producer standard library differs from interpreter base: {module_name}"
                )
        return r[Path].ok(origin)

    @staticmethod
    @lru_cache(maxsize=1)
    def installed_toolchain_identity() -> str:
        """Fingerprint the interpreter and installed distribution provenance.

        PEP 610 records distinguish Git revisions with equal package versions.
        Editable source paths are excluded because consumers track their source
        files independently. Registry distributions have no direct-URL receipt.

        Returns:
            The installed environment's deterministic SHA-256 identity.
        """
        provenance: t.MutableSequenceOf[str] = []
        for distribution in u.installed_distributions():
            receipt = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
            dir_info = (
                None
                if receipt is None
                else m.Infra.DirectUrlReceipt.model_validate_json(receipt).dir_info
            )
            identity = (
                "editable" if dir_info is not None and dir_info.editable else receipt
            )
            provenance.append(
                f"{distribution.name}={distribution.version}:{identity!r}",
            )
        fingerprint = "\n".join((sys.version, *sorted(provenance)))
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    @classmethod
    def editable_members(
        cls,
        repository_root: Path,
        *,
        metadata_paths: t.StrSequence | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]:
        """Elect declared mutable members with authenticated installed editables.

        Frozen or registry-installed dependencies remain libraries even when
        their checkouts are present. The invocation's CI variable does not
        change the observed installation's ownership.

        Returns:
            Members whose installed metadata and physical source match declaration.

        """
        root = repository_root.expanduser().resolve()
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if workspace.failure:
            return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(workspace)
        repositories = tuple(
            repository
            for repository in u.Infra.mutable_flext_members(workspace.value)
            if repository.package
        )
        observation: m.Infra.PythonEnvironmentObservation | None = None
        if metadata_paths is None and repositories:
            native = cls._observe_environment(root, repositories)
            if native.failure:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(native)
            observation = native.value
            metadata_paths = tuple(str(path) for path in observation.metadata_paths)
        selected: list[m.Infra.RepositoryRef] = []
        for repository in repositories:
            matches = u.installed_distributions(
                name=repository.distribution,
                path=metadata_paths,
            )
            if len(matches) != 1:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                    "member provenance distribution count mismatch: "
                    f"distribution={repository.distribution} expected=1 "
                    f"actual={len(matches)}",
                )
            raw = matches[0].read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
            if raw is None:
                continue
            receipt = m.Infra.DirectUrlReceipt.model_validate_json(raw, strict=True)
            if receipt.dir_info is None or not receipt.dir_info.editable:
                continue
            if not repository.editable:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                    f"member is installed editable against declaration: "
                    f"{repository.distribution}",
                )
            authenticated = cls.validate_editable_installation(
                repository,
                root,
                matches[0],
                receipt,
            )
            if authenticated.failure:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(
                    authenticated,
                )
            selected.append(repository)
        return r[t.VariadicTuple[m.Infra.RepositoryRef]].ok(tuple(selected))

    @classmethod
    def validate_editable_installation(
        cls,
        repository: m.Infra.RepositoryRef,
        resolved_root: Path,
        distribution: Distribution,
        receipt: m.Infra.DirectUrlReceipt,
    ) -> p.Result[bool]:
        """Authenticate installation ownership without importing member code.

        Args:
            repository: The repository reference to validate.
            resolved_root: The resolved root path of the repository.
            distribution: The distribution object representing the installed package.
            receipt: The direct URL receipt for the editable installation.

        Returns:
            A result indicating whether the installation is authenticated.
        """
        expected_root = (resolved_root / repository.path).resolve()
        origin = cls._editable_url_verdict(
            repository.distribution,
            receipt,
            expected_root,
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        inventory = cls._validate_pth_inventory(
            repository,
            distribution,
            expected_root,
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        return cls._submodule_gitlink_verdict(
            repository,
            resolved_root,
            expected_root,
            r[bool].ok(value=True),
        )

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.WorkspaceEnvironmentRequest,
    ) -> p.Result[int]:
        """Validate one CLI request without mutating the environment.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return cls.validate(request.repository_root)

    @classmethod
    def validate(
        cls,
        repository_root: Path,
        *,
        metadata_paths: t.StrSequence | None = None,
    ) -> p.Result[int]:
        """Validate PEP 610 and editable path metadata for active members.

        Returns:
            The resulting ``p.Result[int]``.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        resolved_root = context.value.runtime_root
        if context.value.standalone:
            return cls.validate_locked(resolved_root, metadata_paths=metadata_paths)
        workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
            resolved_root,
        )
        if workspace_result.failure:
            return r[int].from_failure(workspace_result)
        repositories = tuple(
            repository
            for repository in (
                workspace_result.value.repository,
                *workspace_result.value.subprojects,
            )
            if repository.package and repository.editable
        )
        observation: m.Infra.PythonEnvironmentObservation | None = None
        if metadata_paths is None and repositories:
            native = cls._observe_environment(resolved_root, repositories)
            if native.failure:
                return r[int].from_failure(native)
            observation = native.value
            metadata_paths = tuple(str(path) for path in observation.metadata_paths)
        validated = 0
        for repository in repositories:
            provenance = cls._validate_editable_provenance(
                repository,
                resolved_root,
                metadata_paths=metadata_paths,
                observation=observation,
            )
            if provenance.failure:
                return r[int].from_failure(provenance)
            validated += int(provenance.value)
        return r[int].ok(validated)

    @staticmethod
    def _observe_environment(
        root: Path,
        repositories: t.VariadicTuple[m.Infra.RepositoryRef],
    ) -> p.Result[m.Infra.PythonEnvironmentObservation]:
        """Read package facts exclusively through the elected physical runtime.

        Args:
            root: The root path of the repository.
            repositories: The repository references to observe.

        Returns:
            A result containing the observed Python environment.
        """
        context = FlextInfraWorkspaceDetector.resolution_context(root)
        if context.failure:
            return r[m.Infra.PythonEnvironmentObservation].from_failure(context)
        return FlextInfraFlextBindingService.consumer_package_environment(
            consumer_root=root,
            python=u.Infra.runtime_python(
                root,
                runtime_root=context.value.runtime_root,
            ),
            packages=tuple(
                u.Infra.project_package_name(root / repository.path)
                for repository in repositories
            ),
        )

    @classmethod
    def _validate_editable_provenance(
        cls,
        repository: m.Infra.RepositoryRef,
        resolved_root: Path,
        *,
        metadata_paths: t.StrSequence | None,
        observation: m.Infra.PythonEnvironmentObservation | None,
    ) -> p.Result[bool]:
        """Prove one editable member's PEP 610 and path metadata provenance.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        matches = u.installed_distributions(
            name=repository.distribution,
            path=metadata_paths,
        )
        if len(matches) != 1:
            return r[bool].fail(
                "editable provenance distribution count mismatch: "
                f"distribution={repository.distribution} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        if observation is not None and not Path(
            str(distribution.locate_file("")),
        ).resolve().is_relative_to(observation.prefix.resolve()):
            return r[bool].fail(
                "editable distribution is outside the owned environment: "
                f"{repository.distribution}",
            )
        expected_root = (resolved_root / repository.path).resolve()
        direct_url_result = cls._validate_direct_url(
            repository.distribution,
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
            expected_root,
        )
        if direct_url_result.failure:
            return r[bool].from_failure(direct_url_result)
        inventory = cls._validate_pth_inventory(
            repository,
            distribution,
            expected_root,
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        if observation is None:
            source_result = r[bool].ok(value=True)
        else:
            package_name = u.Infra.project_package_name(expected_root)
            directories = observation.package_directories.get(package_name, ())
            if (
                len(directories) != 1
                or not directories[0].is_dir()
                or not directories[0].resolve().is_relative_to(expected_root)
            ):
                return r[bool].fail(
                    "editable provenance import source differs from declaration: "
                    f"distribution={repository.distribution} expected={expected_root} "
                    f"actual={directories}",
                )
            if Path(sys.prefix).resolve() == observation.prefix.resolve():
                source_result = cls._validate_import_source(repository, expected_root)
            else:
                u.Cli.info(
                    f"environment distribution={repository.distribution} "
                    f"import_source={directories[0].resolve()} "
                    "loaded_code=unobserved resolver_only=True",
                )
                source_result = r[bool].ok(value=False)
        if source_result.failure:
            return r[bool].from_failure(source_result)
        return cls._submodule_gitlink_verdict(
            repository,
            resolved_root,
            expected_root,
            source_result,
        )

    @classmethod
    def _validate_pth_inventory(
        cls,
        repository: m.Infra.RepositoryRef,
        distribution: Distribution,
        expected_root: Path,
    ) -> p.Result[int]:
        """Prove the installed file inventory yields exactly one editable .pth.

        Returns:
            The resulting ``p.Result[int]``.

        """
        files = distribution.files
        if files is None:
            return r[int].fail(
                "editable provenance has no installed file inventory: "
                f"distribution={repository.distribution}",
            )
        u.Cli.info(
            f"environment distribution={repository.distribution} "
            f"installed_version={distribution.version} "
            f"installed_location={distribution.locate_file('')} "
            f"record_files={len(files)} expected_source={expected_root}",
        )
        pth_files = tuple(
            Path(str(distribution.locate_file(file)))
            for file in files
            if str(file).endswith(".pth")
        )
        if len(pth_files) != 1:
            return r[int].fail(
                "editable provenance pth count mismatch: "
                f"distribution={repository.distribution} expected=1 "
                f"actual={len(pth_files)}",
            )
        return cls._validate_pth(
            repository.distribution,
            pth_files[0],
            expected_root,
        )

    @classmethod
    def _submodule_gitlink_verdict(
        cls,
        repository: m.Infra.RepositoryRef,
        resolved_root: Path,
        expected_root: Path,
        source_result: p.Result[bool],
    ) -> p.Result[bool]:
        """Extend a passing source verdict with the submodule gitlink identity.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if repository.checkout is not c.Infra.CheckoutKind.SUBMODULE:
            return source_result
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=expected_root),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        return cls._workspace_gitlink_verdict(
            repository,
            resolved_root,
            identity.value.head_oid,
        )

    @classmethod
    def _validate_import_source(
        cls,
        repository: m.Infra.RepositoryRef,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Authenticate loaded modules and owned code against the declared source.

        Returns:
            The resulting ``p.Result[bool]``.
        """
        package_name = u.Infra.project_package_name(expected_root)
        package = u.Infra.declared_package_dir(package_name)
        if (
            package is None
            or not package.is_dir()
            or not package.resolve().is_relative_to(expected_root)
        ):
            return r[bool].fail(
                "editable provenance import source differs from declaration: "
                f"distribution={repository.distribution} expected={expected_root} "
                f"actual={package}",
            )
        u.Cli.info(
            f"environment distribution={repository.distribution} "
            f"import_source={package.resolve()}",
        )
        sources = cls.loaded_import_sources(package_name, expected_root=expected_root)
        if sources.failure:
            return r[bool].from_failure(sources)
        if not sources.value:
            u.Cli.info(
                f"environment distribution={repository.distribution} "
                "loaded_code=unobserved resolver_only=True",
            )
            return r[bool].ok(value=False)
        return r[bool].ok(value=True)

    @classmethod
    def loaded_import_sources(
        cls,
        package_name: str,
        *,
        expected_root: Path | None = None,
        reference: m.Infra.NativeImportReference | None = None,
    ) -> p.Result[t.SequenceOf[t.Triple[str, str, str]]]:
        """Consume one pinned cold-native epoch, never a source-only admission."""
        from flext_infra.workspace.native_reference import (
            FlextInfraWorkspaceNativeReference,
        )

        names = tuple(
            sorted(
                name
                for name in tuple(modules)
                if name == package_name or name.startswith(f"{package_name}.")
            )
        )
        if not names:
            return r[t.SequenceOf[t.Triple[str, str, str]]].ok(())
        if reference is None:
            from flext_infra.codegen.codegen_preconditions import (
                FlextInfraCodegenPreconditions,
            )
            from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport

            cold = FlextInfraCodegenPreconditions.capture_source_authority(
                nominated=names
            )
            if cold.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(cold)
            inputs = FlextInfraCodegenPreconditions.authority_inputs(cold.value)
            if inputs.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(inputs)
            roots = [root.parent for _name, root in cold.value.generator_modules]
            for namespace in dict.fromkeys(name.partition(".")[0] for name in names):
                origin = cls._module_source(namespace)
                if origin.failure:
                    return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(origin)
                spec = modules[namespace].__spec__
                roots.append(
                    origin.value.parent.parent
                    if spec and spec.submodule_search_locations
                    else origin.value.parent
                )
            captured = FlextInfraValidateFreshImport.capture_native_reference(
                m.Infra.NativeImportRequest(
                    modules=names,
                    source_authority=cold.value,
                    inputs=inputs.value,
                    import_roots=tuple(dict.fromkeys(roots)),
                )
            )
            if captured.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(captured)
            source_files = captured.value.sources
        else:
            if not set(names).issubset(reference.modules):
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    f"native reference does not cover selected namespace: {package_name}",
                )
            if reference.runtime != Path(sys.executable).resolve():
                return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                    "native reference runtime differs",
                )
            from flext_infra.codegen.codegen_preconditions import (
                FlextInfraCodegenPreconditions,
            )

            current = FlextInfraCodegenPreconditions.source_authority_current(
                reference.source_authority
            )
            if current.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(current)
            observed = FlextInfraWorkspaceNativeReference.capture(reference.modules)
            if observed.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(observed)
            matched = FlextInfraWorkspaceNativeReference.compare(
                observed.value,
                reference,
            )
            if matched.failure:
                return r[t.SequenceOf[t.Triple[str, str, str]]].from_failure(matched)
            source_files = reference.sources
        if expected_root is not None:
            for identity, source, declaration in source_files:
                supplier = identity.partition("::")[0]
                if (
                    supplier == package_name or supplier.startswith(f"{package_name}.")
                ) and not Path(
                    declaration or source,
                ).resolve().is_relative_to(expected_root.resolve()):
                    return r[t.SequenceOf[t.Triple[str, str, str]]].fail(
                        f"producer loaded source escapes declared checkout: {identity}={declaration or source}",
                    )
        return r[t.SequenceOf[t.Triple[str, str, str]]].ok(source_files)

    @classmethod
    def validate_locked(
        cls,
        repository_root: Path,
        *,
        metadata_paths: t.StrSequence | None = None,
    ) -> p.Result[int]:
        """Prove locked artifacts and declared local members match their origins.

        Returns:
            The resulting ``p.Result[int]``.
        """
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return r[int].from_failure(context)
        repository_root = context.value.runtime_root
        document = u.Cli.toml_read_json(context.value.lock_path)
        if document.failure:
            return r[int].from_failure(document)
        # TOML arrays are wire arrays; JSON mode preserves the strict tuple contract.
        locked = m.Infra.LockedEnvironment.model_validate_json(dumps(document.value))
        observed = FlextInfraWorkspaceDetector.load_workspace_spec(
            repository_root,
            allow_unprovisioned_members=context.value.standalone,
        )
        if observed.failure:
            return r[int].from_failure(observed)
        workspace = observed.value
        members = {
            repository.distribution: repository
            for repository in (
                () if context.value.standalone else workspace.subprojects
            )
            if repository.package
        }
        if workspace.repository.package or any(
            item.name == workspace.repository.distribution
            and (item.source.editable is not None or item.source.directory is not None)
            for item in locked.package
        ):
            members[workspace.repository.distribution] = (
                workspace.repository.model_copy(
                    update={"path": Path()},
                )
            )
        # Local sources outside the declared member set must fail, not disappear.
        required = set(members)
        required.update(
            item.name
            for item in locked.package
            if item.source.git is not None
            or item.source.editable is not None
            or item.source.directory is not None
        )
        if metadata_paths is None:
            native = cls._observe_environment(repository_root, tuple(members.values()))
            if native.failure:
                return r[int].from_failure(native)
            metadata_paths = tuple(str(path) for path in native.value.metadata_paths)
        validated = 0
        for name in sorted(required):
            provenance = cls._validate_locked_provenance(
                name,
                locked,
                repository_root,
                resolution_root=context.value.resolution_root,
                repository=members.get(name),
                metadata_paths=metadata_paths,
                environment_root=context.value.environment_path,
            )
            if provenance.failure:
                return r[int].from_failure(provenance)
            validated += int(provenance.value)
        return r[int].ok(validated)

    @classmethod
    def _validate_locked_provenance(
        cls,
        name: str,
        locked: m.Infra.LockedEnvironment,
        repository_root: Path,
        *,
        resolution_root: Path,
        repository: m.Infra.RepositoryRef | None,
        metadata_paths: t.StrSequence | None,
        environment_root: Path,
    ) -> p.Result[bool]:
        """Prove one locked dependency's installed origin and path containment.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        distributions = u.installed_distributions(name=name, path=metadata_paths)
        if len(distributions) != 1:
            return r[bool].fail(
                f"locked provenance needs one installed distribution: {name}",
            )
        distribution = distributions[0]
        location = Path(str(distribution.locate_file(""))).resolve()
        if not location.is_relative_to(environment_root.resolve()):
            return r[bool].fail(
                f"locked dependency is outside the owned environment: {name}",
            )
        matches = tuple(
            item
            for item in locked.package
            if item.name == name and item.version == distribution.version
        )
        if len(matches) != 1:
            return r[bool].fail(
                f"installed version differs from committed lock: {name}",
            )
        item = matches[0]
        if repository is not None and (
            item.source.editable is not None or item.source.directory is not None
        ):
            return cls._validate_workspace_build(
                item,
                repository,
                repository_root,
                resolution_root,
                distribution,
                environment_root=environment_root,
            )
        origin = cls.locked_origin_verdict(
            name,
            matches[0],
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        return cls._locked_pth_verdict(
            name,
            distribution,
            environment_root=environment_root,
        )

    @classmethod
    def _validate_workspace_build(
        cls,
        item: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        resolution_root: Path,
        distribution: Distribution,
        *,
        environment_root: Path,
    ) -> p.Result[bool]:
        """Authenticate a workspace checkout before accepting its installed build.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        checkout = cls._workspace_checkout_verdict(
            item, repository, repository_root, resolution_root
        )
        if checkout.failure:
            return r[bool].from_failure(checkout)
        origin = cls._workspace_origin_verdict(
            item.name,
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
            (repository_root / repository.path).resolve(),
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        return cls._locked_pth_verdict(
            item.name,
            distribution,
            environment_root=environment_root,
        )

    @classmethod
    def _workspace_checkout_verdict(
        cls,
        item: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        resolution_root: Path,
    ) -> p.Result[bool]:
        """Bind the declared local lock source to a clean, committed checkout.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        expected_root = (repository_root / repository.path).resolve()
        local_source = (
            item.source.editable
            if item.source.editable is not None
            else item.source.directory
        )
        source_kinds = sum(
            source is not None
            for source in (
                item.source.editable,
                item.source.directory,
                item.source.git,
                item.source.registry,
            )
        )
        if (
            source_kinds != 1
            or local_source is None
            or repository.editable != (item.source.editable is not None)
            or not expected_root.is_relative_to(repository_root)
        ):
            return r[bool].fail(
                f"locked workspace source differs from declaration: {item.name}",
            )
        if (resolution_root / local_source).resolve() != expected_root:
            return r[bool].fail(
                f"locked workspace source differs from declaration: {item.name}",
            )
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=expected_root),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        if (
            identity.value.repo_root.resolve() != expected_root
            or identity.value.dirty
            or identity.value.origin_remote is None
            or u.Infra.git_remote_identity(identity.value.origin_remote)
            != u.Infra.git_remote_identity(repository.url)
        ):
            return r[bool].fail(
                f"workspace checkout identity differs from declaration: {item.name}",
            )
        if expected_root == repository_root:
            return r[bool].ok(value=True)
        return cls._workspace_gitlink_verdict(
            repository,
            repository_root,
            identity.value.head_oid,
        )

    @staticmethod
    def _workspace_gitlink_verdict(
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        head_oid: str,
    ) -> p.Result[bool]:
        """Require the member HEAD, index and committed gitlink to be identical.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if repository.checkout != c.Infra.CheckoutKind.SUBMODULE:
            return r[bool].fail(
                "workspace member has no declared gitlink checkout: "
                f"{repository.distribution}",
            )
        gitlink = u.Infra.git_staged_gitlink_oid(
            m.Infra.GitRefRequest(
                repo_root=repository_root,
                reference=repository.path.as_posix(),
            ),
        )
        if gitlink.failure:
            return r[bool].from_failure(gitlink)
        committed = u.Infra.git_rev_parse(
            m.Infra.GitCommitishRequest(
                repo_root=repository_root,
                commitish=f"{c.Infra.GIT_HEAD}:{repository.path.as_posix()}",
            ),
        )
        if committed.failure:
            return r[bool].from_failure(committed)
        if head_oid != gitlink.value.oid or gitlink.value.oid != committed.value.oid:
            return r[bool].fail(
                "workspace checkout differs from locked gitlink: "
                f"{repository.distribution}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _workspace_origin_verdict(
        name: str,
        raw: str | None,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Prove the noneditable build's native local-directory receipt.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if raw is None:
            return r[bool].fail(
                f"locked workspace build lacks PEP 610 provenance: {name}",
            )
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(raw)
        if receipt.dir_info is not None and receipt.dir_info.editable:
            return r[bool].fail(f"CI dependency is editable: {name}")
        parsed = urlparse(receipt.url)
        local_url = (
            parsed.scheme == "file"
            and parsed.netloc in {"", "localhost"}
            and not parsed.query
            and not parsed.fragment
        )
        actual_root = Path(url2pathname(unquote(parsed.path)))
        if (
            receipt.dir_info is None
            or receipt.vcs_info is not None
            or not local_url
            or not actual_root.is_absolute()
            or actual_root.resolve() != expected_root
        ):
            return r[bool].fail(
                f"locked workspace build direct_url mismatch: {name} "
                f"expected={expected_root} actual={receipt.url}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def locked_origin_verdict(
        cls,
        name: str,
        item: m.Infra.LockedPackage,
        raw: str | None,
    ) -> p.Result[bool]:
        """Prove one locked dependency's PEP 610 origin against the lock entry.

        Declared local members are authenticated by ``_validate_workspace_build``
        before this artifact-only boundary. Undeclared local lock sources cannot
        bypass checkout, gitlink, and noneditable receipt authentication.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if raw is None and item.source.git is not None:
            return r[bool].fail(
                f"locked dependency lacks PEP 610 provenance: {name}",
            )
        receipt = (
            m.Infra.DirectUrlReceipt.model_validate_json(raw)
            if raw is not None
            else None
        )
        if (
            receipt is not None
            and receipt.dir_info is not None
            and receipt.dir_info.editable
        ):
            return r[bool].fail(f"CI dependency is editable: {name}")
        if item.source.git is None and item.source.registry is None:
            return r[bool].fail(f"CI member needs a locked artifact source: {name}")
        if item.source.git is not None:
            expected = urlparse(item.source.git.removeprefix("git+"))
            if (
                receipt is None
                or receipt.vcs_info is None
                or receipt.vcs_info.vcs != "git"
                or receipt.vcs_info.commit_id != expected.fragment
                or u.Infra.git_remote_identity(receipt.url)
                != u.Infra.git_remote_identity(expected.geturl())
            ):
                return r[bool].fail(
                    f"installed dependency origin differs from committed lock: {name}",
                )
        return r[bool].ok(value=True)

    @staticmethod
    def _locked_pth_verdict(
        name: str,
        distribution: Distribution,
        *,
        environment_root: Path,
    ) -> p.Result[bool]:
        """Prove one installed artifact's path inventory stays environment-owned.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        files = distribution.files
        if files is None:
            return r[bool].fail(f"installed artifact has no file inventory: {name}")
        for file in files:
            if str(file).endswith(".pth"):
                path = Path(str(distribution.locate_file(file)))
                for line in path.read_text(encoding="utf-8").splitlines():
                    if Path(line).is_absolute() and not Path(
                        line,
                    ).resolve().is_relative_to(
                        environment_root.resolve(),
                    ):
                        return r[bool].fail(
                            f"CI artifact exposes an external source path: {name}",
                        )
        return r[bool].ok(value=True)

    @classmethod
    def _validate_direct_url(
        cls,
        distribution: str,
        raw_payload: str | None,
        expected_root: Path,
    ) -> p.Result[int]:
        """Validate one PEP 610 payload against the declared member root.

        Returns:
            The resulting ``p.Result[int]``.

        """
        if raw_payload is None:
            return r[int].fail(
                "editable provenance missing direct_url.json: "
                f"distribution={distribution} expected={expected_root}",
            )
        try:
            payload = m.Infra.DirectUrlReceipt.model_validate_json(
                raw_payload,
                strict=True,
            )
        except ValueError as exc:
            return r[int].fail_op(
                f"editable provenance direct_url validation ({distribution})",
                exc,
            )
        return cls._editable_url_verdict(distribution, payload, expected_root)

    @staticmethod
    def _editable_url_verdict(
        distribution: str,
        payload: m.Infra.DirectUrlReceipt,
        expected_root: Path,
    ) -> p.Result[int]:
        """Bind one parsed editable receipt to its declared physical source."""
        parsed = urlparse(payload.url)
        if (
            parsed.scheme != "file"
            or payload.dir_info is None
            or not payload.dir_info.editable
            or payload.vcs_info is not None
        ):
            revision = (
                payload.vcs_info.commit_id if payload.vcs_info is not None else None
            )
            return r[int].fail(
                "editable provenance is not an editable file URL: "
                f"distribution={distribution} expected={expected_root} "
                f"url={payload.url} installed_revision={revision}",
            )
        actual_root = Path(url2pathname(unquote(parsed.path))).resolve()
        if actual_root != expected_root:
            return r[int].fail(
                "editable provenance direct_url mismatch: "
                f"distribution={distribution} expected={expected_root} "
                f"actual={actual_root}",
            )
        return r[int].ok(1)

    @classmethod
    def _validate_pth(
        cls,
        distribution: str,
        pth_file: Path,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Validate the distribution-owned editable path file.

        Returns:
            Whether the distribution-owned editable paths are valid.

        """
        read_result = u.Cli.files_read_text(pth_file)
        if read_result.failure:
            return r[bool].from_failure(read_result)
        entries = tuple(
            line.strip()
            for line in read_result.value.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if not entries:
            return r[bool].fail(
                "editable provenance pth is empty: "
                f"distribution={distribution} path={pth_file}",
            )
        package_name = u.Infra.project_package_name(expected_root)
        payload = u.Infra.pyproject_payload(expected_root / c.PYPROJECT_FILENAME)
        wheel = payload
        for key in (c.Infra.TOOL, "hatch", "build", "targets", "wheel"):
            child = u.Cli.toml_mapping_child(wheel, key)
            if child is None:
                wheel = {}
                break
            wheel = child
        declared_paths = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            wheel.get("packages", ()),
            strict=True,
        )
        if declared_paths.failure:
            return r[bool].from_failure(declared_paths)
        primary_parts = tuple(package_name.split("."))
        packages: list[t.Pair[str, Path | None]] = []
        for declared in declared_paths.value:
            relative = Path(declared)
            target = (expected_root / relative).resolve()
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not target.is_relative_to(expected_root)
                or not target.is_dir()
            ):
                return r[bool].fail(
                    "editable provenance declared package path is invalid: "
                    f"distribution={distribution} package={declared}",
                )
            name = (
                package_name
                if relative.parts[-len(primary_parts) :] == primary_parts
                else relative.name
            )
            packages.append((name, target))
        if not packages:
            packages.append((package_name, None))
        exposed: set[t.Pair[str, Path | None]] = set()
        for entry in entries:
            if not Path(entry).is_absolute():
                return r[bool].fail(
                    "editable provenance pth entry is not an absolute source path: "
                    f"distribution={distribution} entry={entry}",
                )
            actual_source = Path(entry).resolve()
            if not actual_source.is_relative_to(expected_root):
                return r[bool].fail(
                    "editable provenance pth mismatch: "
                    f"distribution={distribution} expected_root={expected_root} "
                    f"actual={actual_source}",
                )
            if not actual_source.is_dir():
                return r[bool].fail(
                    "editable provenance source directory is not live: "
                    f"distribution={distribution} path={actual_source}",
                )
            elected = {
                (name, target)
                for name, target in packages
                if (
                    (
                        package := u.Infra.declared_package_dir(
                            name,
                            search_paths=(str(actual_source),),
                        )
                    )
                    is not None
                    and package.resolve().is_relative_to(expected_root)
                    and (target is None or package.resolve() == target)
                )
            }
            if not elected:
                return r[bool].fail(
                    "editable provenance pth exposes no declared package: "
                    f"distribution={distribution} path={actual_source}",
                )
            exposed.update(elected)
        if exposed != set(packages):
            return r[bool].fail(
                "editable provenance pth omits declared package sources: "
                f"distribution={distribution}",
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentProvenance"]
