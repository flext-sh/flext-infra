"""Collect target-authored dependency suppliers from the elected native runtime.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib.machinery import all_suffixes
from importlib.metadata import Distribution
from json import dumps
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraBindingService,
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)


class FlextInfraRuntimeDependencyCollector:
    """Authenticate suppliers without resolving or inventing requirement policy."""

    def __init__(self, *, python: Path, development_only: t.StrSequence) -> None:
        """Receive the interpreter and runtime exclusions from composition."""
        self._python = python.absolute()
        self._development_only = tuple(development_only)

    def __call__(
        self,
        project_root: Path,
        scan: m.Infra.DeptryScan,
        /,
    ) -> p.Result[m.Infra.RuntimeDependencyInputs]:
        """Bind native import findings to exact installed and locked suppliers.

        Returns:
            Provenance for the existing planner, never a second dependency plan.

        """
        result = r[m.Infra.RuntimeDependencyInputs]
        if (
            scan.settings.path != project_root / c.PYPROJECT_FILENAME
            or self._python.parent != scan.venv_bin
        ):
            return result.fail("dependency collector belongs to another scan runtime")
        context = FlextInfraWorkspaceDetector.resolution_context(project_root).unwrap()
        observed = FlextInfraBindingService.consumer_package_environment(
            consumer_root=project_root,
            python=self._python,
            packages=(),
        ).unwrap()
        lock = u.Cli.atomic_read_binary_file_state(
            context.lock_path,
            required=True,
        ).unwrap()
        if lock.content is None or scan.settings.content is None:
            return result.fail("dependency collector lacks native lock or declarations")
        payload = u.Cli.toml_mapping_from_text(lock.content.decode(c.DEFAULT_ENCODING))
        if payload is None:
            return result.fail(f"invalid native dependency lock: {lock.path}")
        locked = m.Infra.LockedEnvironment.model_validate_json(dumps(payload))
        document = u.Cli.toml_parse_text(
            scan.settings.content.decode(c.DEFAULT_ENCODING),
        )
        if document is None:
            return result.fail(f"invalid target declarations: {scan.settings.path}")
        markers = FlextInfraBindingService.consumer_marker_environment(
            consumer_root=project_root,
            python=self._python,
        ).unwrap()
        declarations = u.Infra.document_requirement_lines(document).unwrap()
        authored: t.MappingKV[str, str] = {
            canonicalize_name(Requirement(item).name): item
            for item in declarations
            if u.Infra.active_requirement(item, environment=markers) is not None
        }
        providers = self._collect_providers(
            context,
            scan,
            locked,
            authored,
            observed.metadata_paths,
        )
        if providers.failure:
            return result.from_failure(providers)
        return result.ok(
            m.Infra.RuntimeDependencyInputs(
                target_root=project_root,
                python=self._python,
                lock=lock,
                providers=providers.value,
                development_only=self._development_only,
                inputs=(
                    scan.settings,
                    u.Cli.atomic_read_binary_file_state(
                        context.pyproject_path,
                        required=True,
                    ).unwrap(),
                    u.Cli.atomic_read_binary_file_state(
                        context.runtime_root / c.Infra.GITMODULES,
                        required=False,
                    ).unwrap(),
                ),
            ),
        )

    def _collect_providers(
        self,
        context: m.Infra.WorkspaceRuntimeContext,
        scan: m.Infra.DeptryScan,
        locked: m.Infra.LockedEnvironment,
        authored: t.MappingKV[str, str],
        metadata_paths: t.SequenceOf[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.RuntimeDependencyProvider]]:
        """Elect suppliers in one native pass against this operation's inputs.

        Returns:
            All matching authored suppliers, preserving ambiguity for the planner.

        """
        result = r[t.VariadicTuple[m.Infra.RuntimeDependencyProvider]]
        needed = {
            item.module
            for item in scan.report.root
            if item.error.code in {"DEP001", "DEP003", "DEP004"}
        }
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            context.runtime_root,
        ).unwrap()
        repositories: t.MappingKV[str, m.Infra.RepositoryRef] = {
            canonicalize_name(repository.distribution): repository
            for repository in (workspace.repository, *workspace.subprojects)
        }

        def provider(
            distribution: Distribution,
        ) -> p.Result[t.VariadicTuple[m.Infra.RuntimeDependencyProvider]]:
            """Elect and authenticate one native distribution without another scan.

            Returns:
                The required supplier collection, or its original failure.

            """
            selected = r[t.VariadicTuple[m.Infra.RuntimeDependencyProvider]]
            states = self._metadata_states(distribution, context.environment_path)
            name = distribution.metadata.get("Name")
            if name is None:
                return selected.fail("installed dependency metadata lacks its Name")
            identity = canonicalize_name(name)
            if identity not in authored:
                return selected.ok(())
            receipt = (
                m.Infra.DirectUrlReceipt.model_validate_json(states[-1].content)
                if states[-1].content is not None
                else None
            )
            supplied = tuple(
                sorted(
                    needed.intersection(
                        self._distribution_modules(
                            distribution,
                            name,
                            repositories.get(identity),
                            context.runtime_root,
                            receipt,
                        ),
                    ),
                ),
            )
            if not supplied:
                return selected.ok(())
            package = self._locked_package(distribution, name, locked)
            extra_inputs = package.flat_map(
                lambda locked_package: self._provider_inputs(
                    context,
                    distribution,
                    locked_package,
                    repositories.get(identity),
                    states[-1],
                ),
            )
            if extra_inputs.failure:
                return selected.from_failure(extra_inputs)
            return selected.ok((
                m.Infra.RuntimeDependencyProvider(
                    modules=supplied,
                    package=package.value,
                    requirement=authored[identity],
                    inputs=(*states, *extra_inputs.value),
                ),
            ))

        providers: list[m.Infra.RuntimeDependencyProvider] = []
        for distribution in u.installed_distributions(
            path=tuple(str(path) for path in metadata_paths),
        ):
            selected = provider(distribution)
            if selected.failure:
                return result.from_failure(selected)
            providers.extend(selected.value)
        return result.ok(tuple(providers))

    @classmethod
    def _distribution_modules(
        cls,
        distribution: Distribution,
        name: str,
        repository: m.Infra.RepositoryRef | None,
        runtime_root: Path,
        receipt: m.Infra.DirectUrlReceipt | None,
    ) -> set[str]:
        """Combine native file modules with an authenticated editable declaration.

        Returns:
            The installed modules available for this dependency election.

        """
        modules = cls._record_modules(distribution)
        if (
            receipt is not None
            and receipt.dir_info is not None
            and receipt.dir_info.editable
            and repository is not None
        ):
            modules.update(
                module
                for module, _path in (
                    FlextInfraWorkspaceEnvironmentProvenance.editable_declared_packages(
                        name,
                        (runtime_root / repository.path).resolve(),
                    ).unwrap()
                )
            )
        return modules

    @staticmethod
    def _locked_package(
        distribution: Distribution,
        name: str,
        locked: m.Infra.LockedEnvironment,
    ) -> p.Result[m.Infra.LockedPackage]:
        """Require the same unique native name and version in the captured lock.

        Returns:
            The one matching locked package, or the original ownership failure.

        """
        identity = canonicalize_name(name)
        matches = tuple(
            item
            for item in locked.package
            if canonicalize_name(item.name) == identity
            and item.version == distribution.version
        )
        if len(matches) != 1:
            return r[m.Infra.LockedPackage].fail(
                f"dependency supplier lacks one exact lock entry: {name}"
            )
        return r[m.Infra.LockedPackage].ok(matches[0])

    @staticmethod
    def _provider_inputs(
        context: m.Infra.WorkspaceRuntimeContext,
        distribution: Distribution,
        package: m.Infra.LockedPackage,
        repository: m.Infra.RepositoryRef | None,
        receipt_state: m.Cli.AtomicFileState,
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Authenticate the installed supplier's locked origin and editable inputs.

        Returns:
            Additional declaration inputs, or the original provenance failure.

        """
        result = r[t.VariadicTuple[m.Cli.AtomicFileState]]
        name = package.name
        receipt = (
            m.Infra.DirectUrlReceipt.model_validate_json(receipt_state.content)
            if receipt_state.content is not None
            else None
        )
        if receipt is None or receipt.dir_info is None or not receipt.dir_info.editable:
            if package.source.registry is not None and receipt is not None:
                return result.fail(
                    f"registry dependency has a foreign direct origin: {name}"
                )
            FlextInfraWorkspaceEnvironmentProvenance.locked_origin_verdict(
                name,
                package,
                receipt_state.content.decode(c.DEFAULT_ENCODING)
                if receipt_state.content is not None
                else None,
            ).unwrap()
            return result.ok(())
        if (
            repository is None
            or package.source.editable is None
            or not repository.editable
        ):
            return result.fail(
                f"editable dependency lacks declared lock ownership: {name}"
            )
        expected_root = (context.runtime_root / repository.path).resolve()
        if (
            context.resolution_root / package.source.editable
        ).resolve() != expected_root:
            return result.fail(f"editable dependency differs from locked path: {name}")
        FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
            repository,
            context.runtime_root,
            distribution,
            receipt,
        ).unwrap()
        return result.ok((
            u.Cli.atomic_read_binary_file_state(
                expected_root / c.PYPROJECT_FILENAME,
                required=True,
            ).unwrap(),
        ))

    @staticmethod
    def _record_modules(distribution: Distribution) -> set[str]:
        """Derive import roots only from the distribution's native file inventory.

        Returns:
            Python module names the distribution actually ships.

        """
        return {
            file.parts[0].removesuffix(suffix)
            for file in distribution.files or ()
            for suffix in all_suffixes()
            if str(file).endswith(suffix)
            and file.parts[0].removesuffix(suffix).isidentifier()
        }

    @staticmethod
    def _metadata_states(
        distribution: Distribution,
        environment: Path,
    ) -> t.VariadicTuple[m.Cli.AtomicFileState]:
        """Capture metadata, RECORD, origin absence/presence and editable path files.

        Returns:
            Guardable input states inside the physical selected environment.

        Raises:
            ValueError: Distribution metadata or RECORD has no unique owned path.

        """
        files = distribution.files
        location = Path(str(distribution.locate_file(""))).resolve()
        metadata = tuple(
            path
            for file in files or ()
            if file.name == "METADATA"
            and file.parent.name.endswith(".dist-info")
            and (path := Path(str(distribution.locate_file(file))))
            .resolve()
            .parent.parent
            == location
        )
        if files is None or len(metadata) != 1:
            msg = (
                f"dependency supplier {distribution.name!r} lacks one native "
                f"metadata inventory: expected=1 observed={len(metadata)}"
            )
            raise ValueError(msg)
        paths = (
            metadata[0],
            metadata[0].with_name("RECORD"),
            *(
                Path(str(distribution.locate_file(file)))
                for file in files
                if file.suffix == ".pth"
            ),
            metadata[0].with_name(c.Infra.DISTRIBUTION_DIRECT_URL_FILE),
        )
        if any(
            not path.resolve().is_relative_to(environment.resolve()) for path in paths
        ):
            msg = "dependency supplier metadata leaves the selected environment"
            raise ValueError(msg)
        return tuple(
            u.Cli.atomic_read_binary_file_state(
                path,
                required=index != len(paths) - 1,
            ).unwrap()
            for index, path in enumerate(paths)
        )


__all__: list[str] = ["FlextInfraRuntimeDependencyCollector"]
