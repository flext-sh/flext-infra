"""Fail-closed validation of local editables and locked CI build provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import sys
from base64 import urlsafe_b64encode
from functools import lru_cache
from importlib.metadata import Distribution, PackagePath
from json import dumps
from pathlib import Path
from sys import modules
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from flext_infra import c, config, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraBindingService,
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceLockCompleteness,
)
from flext_infra.workspace._environment_provenance_editable import (
    FlextInfraWorkspaceEnvironmentProvenanceEditableMixin,
)
from flext_infra.workspace._environment_provenance_module_source import (
    FlextInfraWorkspaceEnvironmentProvenanceModuleSourceMixin,
)


class FlextInfraWorkspaceEnvironmentProvenance(
    FlextInfraWorkspaceEnvironmentProvenanceModuleSourceMixin,
    FlextInfraWorkspaceEnvironmentProvenanceEditableMixin,
):
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
        observed = cls._observe_environment(repository_root, (repository,))
        if observed.failure:
            return result.from_failure(observed)
        installed = cls._member_installation(
            repository,
            metadata_paths=tuple(str(path) for path in observed.value.metadata_paths),
            environment_root=observed.value.prefix,
        )
        if installed.failure:
            return result.from_failure(installed)
        distribution, raw, receipt = installed.value
        if receipt.dir_info is not None and receipt.dir_info.editable:
            if not repository.editable:
                return result.fail(
                    "member editable installation differs from declaration: "
                    f"{repository.distribution}",
                )
            authenticated = cls.validate_editable_installation(
                repository,
                repository_root,
                distribution,
                receipt,
            )
            if authenticated.failure:
                return result.from_failure(authenticated)
            return u.Cli.atomic_read_binary_file_state(
                repository_root / repository.path / c.PYPROJECT_FILENAME,
                required=True,
            )
        return cls._locked_member_declaration(
            repository_root,
            repository,
            (distribution, raw, receipt),
            lock_state=lock_state,
            environment_root=observed.value.prefix,
        )

    @staticmethod
    def _member_installation(
        repository: m.Infra.RepositoryRef,
        *,
        metadata_paths: t.StrSequence,
        environment_root: Path,
    ) -> p.Result[t.Triple[Distribution, str, m.Infra.DirectUrlReceipt]]:
        """Read the member's unique installed distribution and native PEP 610 record.

        Returns:
            The distribution, original receipt bytes and validated URL declaration.

        """
        result = r[t.Triple[Distribution, str, m.Infra.DirectUrlReceipt]]
        matches = u.installed_distributions(
            name=repository.distribution,
            path=metadata_paths,
        )
        if len(matches) != 1:
            return result.fail(
                "member declaration needs one installed distribution: "
                f"{repository.distribution}",
            )
        distribution = matches[0]
        if (
            not Path(str(distribution.locate_file("")))
            .resolve()
            .is_relative_to(
                environment_root.resolve(),
            )
        ):
            return result.fail(
                "member distribution is outside the owned environment: "
                f"{repository.distribution}",
            )
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
        return result.ok((distribution, raw, receipt.value))

    @staticmethod
    def _member_locked_environment(
        repository_root: Path,
        lock_state: m.Cli.AtomicFileState | None,
    ) -> p.Result[m.Infra.LockedEnvironment]:
        """Parse only the captured lock elected by the physical runtime owner.

        Returns:
            The validated committed environment or its first lock failure.

        """
        result = r[m.Infra.LockedEnvironment]
        context = FlextInfraWorkspaceDetector.resolution_context(repository_root)
        if context.failure:
            return result.from_failure(context)
        if lock_state is None:
            lock_read = u.Cli.atomic_read_binary_file_state(
                context.value.lock_path,
                required=True,
            )
            if lock_read.failure:
                return result.from_failure(lock_read)
            lock_state = lock_read.value
        if (
            lock_state.path != context.value.lock_path.resolve()
            or lock_state.content is None
        ):
            return result.fail("member artifact needs its captured elected lock")
        locked_document = u.Cli.toml_parse_text(
            lock_state.content.decode(c.DEFAULT_ENCODING),
        )
        if locked_document is None:
            return result.fail("captured member artifact lock is invalid TOML")
        locked_payload = u.Cli.toml_as_mapping(locked_document)
        if locked_payload is None:
            return result.fail("captured member artifact lock is not a mapping")
        return result.create_from_callable(
            lambda: m.Infra.LockedEnvironment.model_validate_json(
                dumps(locked_payload)
            ),
        )

    @classmethod
    def _locked_member_declaration(
        cls,
        repository_root: Path,
        repository: m.Infra.RepositoryRef,
        installation: t.Triple[Distribution, str, m.Infra.DirectUrlReceipt],
        *,
        lock_state: m.Cli.AtomicFileState | None,
        environment_root: Path,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Bind the installed Git build to its lock and declared repository.

        Returns:
            The installed producer declaration authenticated by its build record.

        """
        result = r[m.Cli.AtomicFileState]
        distribution, raw, receipt = installation
        locked = cls._member_locked_environment(repository_root, lock_state)
        if locked.failure:
            return result.from_failure(locked)
        candidates = tuple(
            item
            for item in locked.value.package
            if u.Infra.dep_name(item.name) == u.Infra.dep_name(repository.distribution)
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
        if u.Infra.git_remote_identity(receipt.url) != u.Infra.git_remote_identity(
            repository.url
        ):
            return result.fail(
                "member artifact origin differs from declared repository: "
                f"{repository.distribution}",
            )
        return cls._member_recorded_declaration(
            repository,
            distribution,
            environment_root=environment_root,
        )

    @staticmethod
    def _member_declaration_state(
        repository: m.Infra.RepositoryRef,
        distribution: Distribution,
        *,
        environment_root: Path,
    ) -> p.Result[t.Pair[PackagePath, m.Cli.AtomicFileState]]:
        """Read the unique producer declaration inside the installed environment.

        Returns:
            The RECORD entry and its current authenticated physical file.

        """
        result = r[t.Pair[PackagePath, m.Cli.AtomicFileState]]
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
        if not path.is_relative_to(environment_root.resolve()):
            return result.fail(
                "member declaration escapes its installed environment: "
                f"{repository.distribution}",
            )
        captured = u.Cli.atomic_read_binary_file_state(path, required=True)
        if captured.failure:
            return result.from_failure(captured)
        return result.ok((resource, captured.value))

    @classmethod
    def _member_recorded_declaration(
        cls,
        repository: m.Infra.RepositoryRef,
        distribution: Distribution,
        *,
        environment_root: Path,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Authenticate declaration content through RECORD and the producer's wheel.

        Returns:
            The complete original declaration state or the first build mismatch.

        """
        result = r[m.Cli.AtomicFileState]
        captured = cls._member_declaration_state(
            repository,
            distribution,
            environment_root=environment_root,
        )
        if captured.failure:
            return result.from_failure(captured)
        resource, state = captured.value
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
        producer = u.Infra.parsed_pyproject(
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
        if metadata_paths is None and repositories:
            native = cls._observe_environment(root, repositories)
            if native.failure:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].from_failure(native)
            metadata_paths = tuple(str(path) for path in native.value.metadata_paths)
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
            repository.distribution,
            distribution,
            expected_root,
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        return r[bool].ok(value=True)

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.WorkspaceRequest,
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
        """Validate installed sources against the elected native lock.

        Returns:
            The resulting ``p.Result[int]``.

        """
        return cls.validate_locked(repository_root, metadata_paths=metadata_paths)

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
        return FlextInfraBindingService.consumer_package_environment(
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
    def _editable_import_verdict(
        cls,
        distribution: str,
        expected_root: Path,
        observation: m.Infra.PythonEnvironmentObservation | None,
    ) -> p.Result[bool]:
        """Bind editable import election to the already observed owned runtime.

        Returns:
            The same loaded-binding or resolver-only observation verdict.

        """
        if observation is None:
            return r[bool].ok(value=True)
        package_name = u.Infra.project_package_name(expected_root)
        directories = observation.package_directories.get(package_name, ())
        if (
            len(directories) != 1
            or not directories[0].is_dir()
            or not directories[0].resolve().is_relative_to(expected_root)
        ):
            return r[bool].fail(
                "editable provenance import source differs from declaration: "
                f"distribution={distribution} expected={expected_root} "
                f"actual={directories}",
            )
        if Path(sys.prefix).resolve() == observation.prefix.resolve():
            return cls._validate_import_source(distribution, expected_root)
        u.Cli.info(
            f"environment distribution={distribution} "
            f"import_source={directories[0].resolve()} "
            "loaded_import_binding=unobserved resolver_only=True",
        )
        return r[bool].ok(value=False)

    @classmethod
    def _validate_pth_inventory(
        cls,
        name: str,
        distribution: Distribution,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Prove the installed file inventory yields exactly one editable .pth.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        files = distribution.files
        if files is None:
            return r[bool].fail(
                "editable provenance has no installed file inventory: "
                f"distribution={name}",
            )
        u.Cli.info(
            f"environment distribution={name} "
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
            return r[bool].fail(
                "editable provenance pth count mismatch: "
                f"distribution={name} expected=1 "
                f"actual={len(pth_files)}",
            )
        return cls._validate_pth(
            name,
            pth_files[0],
            expected_root,
        )

    @classmethod
    def _validate_import_source(
        cls,
        distribution: str,
        expected_root: Path,
    ) -> p.Result[bool]:
        """Authenticate physical import bindings against the installed declaration.

        Returns:
            The resulting ``p.Result[bool]``.

        Executable declarations have a separate producer/check admission owner.
        Environment verification never traverses functions, classes or libraries
        exported by these module namespaces.

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
                f"distribution={distribution} expected={expected_root} "
                f"actual={package}",
            )
        u.Cli.info(
            f"environment distribution={distribution} "
            f"import_source={package.resolve()}",
        )
        names = tuple(
            name
            for name in tuple(modules)
            if name == package_name or name.startswith(f"{package_name}.")
        )
        for name in names:
            elected = cls.module_source(name)
            if elected.failure:
                return r[bool].from_failure(elected)
            if not elected.value.resolve().is_relative_to(expected_root):
                return r[bool].fail(
                    "editable provenance loaded import escapes declaration: "
                    f"distribution={distribution} "
                    f"module={name} expected={expected_root} actual={elected.value}",
                )
        if not names:
            u.Cli.info(
                f"environment distribution={distribution} "
                "loaded_import_binding=unobserved resolver_only=True",
            )
            return r[bool].ok(value=False)
        return r[bool].ok(value=True)

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
        consistency = FlextInfraWorkspaceLockCompleteness.verify_lock(repository_root)
        if consistency.failure:
            return r[int].from_failure(consistency)
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
        )
        if observed.failure:
            return r[int].from_failure(observed)
        workspace = observed.value
        members = {
            repository.distribution: repository
            for repository in workspace.subprojects
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
        # Native sources, including explicit suppliers outside this workspace,
        # come from the elected lock rather than an independently selected graph.
        required = set(members)
        required.update(
            item.name
            for item in locked.package
            if item.source.git is not None
            or item.source.editable is not None
            or item.source.directory is not None
            or item.source.url is not None
        )
        observation: m.Infra.PythonEnvironmentObservation | None = None
        if metadata_paths is None:
            native = FlextInfraBindingService.consumer_package_environment(
                consumer_root=repository_root,
                python=u.Infra.runtime_python(
                    repository_root,
                    runtime_root=context.value.runtime_root,
                ),
                packages=tuple(
                    sorted({
                        u.Infra.project_package_name(
                            (
                                context.value.resolution_root / item.source.editable
                            ).resolve(),
                        )
                        for item in locked.package
                        if item.source.editable is not None
                    }),
                ),
            )
            if native.failure:
                return r[int].from_failure(native)
            observation = native.value
            metadata_paths = tuple(str(path) for path in observation.metadata_paths)
        validated = 0
        for name in sorted(required):
            provenance = cls._validate_locked_provenance(
                name,
                locked,
                context.value,
                repository=members.get(name),
                metadata_paths=metadata_paths,
                observation=observation,
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
        context: m.Infra.WorkspaceRuntimeContext,
        *,
        repository: m.Infra.RepositoryRef | None,
        metadata_paths: t.StrSequence | None,
        observation: m.Infra.PythonEnvironmentObservation | None = None,
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
        if not location.is_relative_to(context.environment_path.resolve()):
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
        local_source = (
            item.source.editable
            if item.source.editable is not None
            else item.source.directory
        )
        if local_source is not None:
            if repository is not None:
                checkout = cls._workspace_checkout_verdict(
                    item,
                    repository,
                    context.runtime_root,
                    context.resolution_root,
                )
                if checkout.failure:
                    return r[bool].from_failure(checkout)
            return cls.validate_local_installation(
                item,
                context,
                distribution,
                observation=observation,
                repository=repository,
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
            environment_root=context.environment_path,
        )

    @classmethod
    def validate_local_installation(
        cls,
        item: m.Infra.LockedPackage,
        context: m.Infra.WorkspaceRuntimeContext,
        distribution: Distribution,
        *,
        observation: m.Infra.PythonEnvironmentObservation | None,
        repository: m.Infra.RepositoryRef | None,
    ) -> p.Result[bool]:
        """Authenticate installed local sources without resolving dependencies.

        uv owns declaration lowering and lock consistency. This post-install
        boundary checks its physical PEP 610, editable paths and observed imports.

        Returns:
            The original source-binding verdict or its first provenance failure.

        """
        source = (
            item.source.editable
            if item.source.editable is not None
            else item.source.directory
        )
        if source is None:
            return r[bool].fail(
                f"native local dependency has no locked path: {item.name}",
            )
        expected_root = (context.resolution_root / source).resolve()
        raw = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        if raw is None:
            return r[bool].fail(
                f"native local dependency lacks PEP 610 provenance: {item.name}",
            )
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(raw, strict=True)
        if receipt.dir_info is not None and receipt.dir_info.editable:
            if item.source.editable is None:
                return r[bool].fail(
                    f"editable installation differs from native lock: {item.name}",
                )
            declaration = u.Cli.toml_read_document(expected_root / c.PYPROJECT_FILENAME)
            if declaration.failure:
                return r[bool].from_failure(declaration)
            project = u.Cli.toml_table_path(declaration.value, ("project",))
            name = None if project is None else u.Cli.toml_value(project, "name")
            if not isinstance(name, str) or u.Infra.dep_name(name) != u.Infra.dep_name(
                item.name,
            ):
                return r[bool].fail(
                    f"editable declaration differs from native lock: {item.name}",
                )
            origin = cls._workspace_origin_verdict(
                item.name,
                raw,
                expected_root,
                editable=True,
            )
            if origin.failure:
                return r[bool].from_failure(origin)
            inventory = cls._validate_pth_inventory(
                item.name,
                distribution,
                expected_root,
            )
            if inventory.failure:
                return r[bool].from_failure(inventory)
            return cls._editable_import_verdict(item.name, expected_root, observation)
        if repository is not None:
            return cls._validate_workspace_build(
                item, repository, context, distribution
            )
        origin = cls._workspace_origin_verdict(item.name, raw, expected_root)
        if origin.failure:
            return r[bool].from_failure(origin)
        return cls._locked_pth_verdict(
            item.name,
            distribution,
            environment_root=context.environment_path,
        )

    @classmethod
    def _validate_workspace_build(
        cls,
        item: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef,
        context: m.Infra.WorkspaceRuntimeContext,
        distribution: Distribution,
    ) -> p.Result[bool]:
        """Authenticate a workspace checkout before accepting its installed build.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        checkout = cls._workspace_checkout_verdict(
            item,
            repository,
            context.runtime_root,
            context.resolution_root,
            immutable=u.Infra.env_value(config.Infra.codegen.make.ci.variable)
            == config.Infra.codegen.make.ci.value,
        )
        if checkout.failure:
            return r[bool].from_failure(checkout)
        origin = cls._workspace_origin_verdict(
            item.name,
            distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
            (context.runtime_root / repository.path).resolve(),
        )
        if origin.failure:
            return r[bool].from_failure(origin)
        return cls._locked_pth_verdict(
            item.name,
            distribution,
            environment_root=context.environment_path,
        )

    @classmethod
    def _workspace_checkout_verdict(
        cls,
        item: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        resolution_root: Path,
        *,
        immutable: bool = False,
    ) -> p.Result[bool]:
        """Bind native local sources, checking gitlinks only for immutable CI builds.

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
                item.source.virtual,
                item.source.url,
            )
        )
        if (
            source_kinds != 1
            or local_source is None
            or not expected_root.is_relative_to(repository_root)
        ):
            return r[bool].fail(
                f"locked workspace source differs from declaration: {item.name}",
            )
        if (resolution_root / local_source).resolve() != expected_root:
            return r[bool].fail(
                f"locked workspace source differs from declaration: {item.name}",
            )
        if not immutable:
            return r[bool].ok(value=True)
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=expected_root),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        if (
            identity.value.repo_root.resolve() != expected_root
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
        head_oid: str | None,
    ) -> p.Result[bool]:
        """Require the member HEAD, index and committed gitlink to be identical.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if head_oid is None:
            return r[bool].fail(
                "workspace member has no committed HEAD for its gitlink: "
                f"{repository.distribution}",
            )
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
        *,
        editable: bool = False,
    ) -> p.Result[bool]:
        """Prove a native local-directory receipt's source and installation mode.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if raw is None:
            return r[bool].fail(
                f"locked workspace build lacks PEP 610 provenance: {name}",
            )
        receipt = m.Infra.DirectUrlReceipt.model_validate_json(raw)
        if not editable and receipt.dir_info is not None and receipt.dir_info.editable:
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
            or receipt.dir_info.editable != editable
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

        Native local sources use ``_validate_native_local_installation`` with
        their explicit resolution root before this artifact-only boundary.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        if raw is None and (item.source.git is not None or item.source.url is not None):
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
        if (
            item.source.git is None
            and item.source.registry is None
            and item.source.url is None
        ):
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
        if item.source.url is not None and (
            receipt is None
            or receipt.url != item.source.url
            or receipt.dir_info is not None
            or receipt.vcs_info is not None
        ):
            return r[bool].fail(
                f"installed dependency origin differs from committed lock: {name}",
            )
        if item.source.registry is not None and receipt is not None:
            return r[bool].fail(
                f"registry dependency has a foreign direct origin: {name}"
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


__all__: list[str] = ["FlextInfraWorkspaceEnvironmentProvenance"]
