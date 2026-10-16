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
        authored = {
            canonicalize_name(Requirement(item).name): item
            for item in declarations
            if u.Infra.active_requirement(item, environment=markers) is not None
        }
        needed = {
            item.module
            for item in scan.report.root
            if item.error.code in {"DEP001", "DEP003", "DEP004"}
        }
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            context.runtime_root,
        ).unwrap()
        repositories = {
            canonicalize_name(repository.distribution): repository
            for repository in (workspace.repository, *workspace.subprojects)
        }
        providers: list[m.Infra.RuntimeDependencyProvider] = []
        for distribution in u.installed_distributions(
            path=tuple(str(path) for path in observed.metadata_paths),
        ):
            states = self._metadata_states(distribution, context.environment_path)
            name = distribution.metadata.get("Name")
            if name is None:
                return result.fail("installed dependency metadata lacks its Name")
            identity = canonicalize_name(name)
            if identity not in authored:
                continue
            receipt_state = states[-1]
            receipt = (
                m.Infra.DirectUrlReceipt.model_validate_json(receipt_state.content)
                if receipt_state.content is not None
                else None
            )
            modules = self._record_modules(distribution)
            repository = repositories.get(identity)
            editable = (
                receipt is not None
                and receipt.dir_info is not None
                and receipt.dir_info.editable
            )
            if editable and repository is not None:
                expected_root = (context.runtime_root / repository.path).resolve()
                modules.update(
                    name
                    for name, _path in FlextInfraWorkspaceEnvironmentProvenance.editable_declared_packages(
                        name,
                        expected_root,
                    ).unwrap()
                )
            supplied = tuple(sorted(needed.intersection(modules)))
            if not supplied:
                continue
            matches = tuple(
                item
                for item in locked.package
                if canonicalize_name(item.name) == identity
                and item.version == distribution.version
            )
            if len(matches) != 1:
                return result.fail(
                    f"dependency supplier lacks one exact lock entry: {name}",
                )
            package = matches[0]
            if editable:
                if (
                    repository is None
                    or receipt is None
                    or package.source.editable is None
                    or not repository.editable
                ):
                    return result.fail(
                        f"editable dependency lacks declared lock ownership: {name}",
                    )
                expected_root = (context.runtime_root / repository.path).resolve()
                if (
                    context.resolution_root / package.source.editable
                ).resolve() != expected_root:
                    return result.fail(
                        f"editable dependency differs from locked path: {name}",
                    )
                FlextInfraWorkspaceEnvironmentProvenance.validate_editable_installation(
                    repository,
                    context.runtime_root,
                    distribution,
                    receipt,
                ).unwrap()
                states += (
                    u.Cli.atomic_read_binary_file_state(
                        expected_root / c.PYPROJECT_FILENAME,
                        required=True,
                    ).unwrap(),
                )
            else:
                if package.source.registry is not None and receipt is not None:
                    return result.fail(
                        f"registry dependency has a foreign direct origin: {name}",
                    )
                FlextInfraWorkspaceEnvironmentProvenance.locked_origin_verdict(
                    name,
                    package,
                    receipt_state.content.decode(c.DEFAULT_ENCODING)
                    if receipt_state.content is not None
                    else None,
                ).unwrap()
            providers.append(
                m.Infra.RuntimeDependencyProvider(
                    modules=supplied,
                    package=package,
                    requirement=authored[identity],
                    inputs=states,
                ),
            )
        for module in needed:
            if sum(module in provider.modules for provider in providers) != 1:
                return result.fail(
                    "runtime import requires one authored, installed, locked "
                    f"supplier: {module}",
                )
        return result.ok(
            m.Infra.RuntimeDependencyInputs(
                target_root=project_root,
                python=self._python,
                lock=lock,
                providers=tuple(providers),
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
        metadata = tuple(
            Path(str(distribution.locate_file(file)))
            for file in files or ()
            if file.name == "METADATA" and file.parent.name.endswith(".dist-info")
        )
        if files is None or len(metadata) != 1:
            msg = "dependency supplier lacks one native metadata inventory"
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
