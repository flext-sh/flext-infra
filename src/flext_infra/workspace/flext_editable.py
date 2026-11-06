"""Elect, install and record the local FLEXT editable selection of setup.

``make setup FLEXT=<path>`` (operator ruling 2026-10-24, tracker memory
``operator-ruling-2026-10-24-setup-flext-editable-param``) reinstalls every
locked FLEXT distribution the workspace at ``<path>`` provides as editable and
records exactly that selection in a typed receipt owned by the runtime root.
A plain setup removes the receipt. The environment provenance gate admits an
editable FLEXT distribution only when this receipt names it, outside CI; the
selection is never inferred from installed PEP 610 metadata.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from packaging.utils import NormalizedName, canonicalize_name

from flext_infra import c, config, m, p, r, u
from flext_infra.workspace import (
    FlextInfraBindingService,
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironment,
)


class FlextInfraWorkspaceFlextEditable:
    """Own the FLEXT editable selection receipt and its installation."""

    @staticmethod
    def _ci_context() -> bool:
        ci = config.Infra.codegen.make.ci
        return u.Infra.env_value(ci.variable) == ci.value

    @staticmethod
    def receipt_path(runtime_root: Path) -> Path:
        """Return the runtime-owned selection receipt path.

        Returns:
            The receipt location under the runtime root's report directory.

        """
        return runtime_root / c.Infra.FLEXT_EDITABLE_SELECTION_RELATIVE_PATH

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.FlextEditableRequest,
    ) -> p.Result[int]:
        """Record the selection of ``request.flext_root``, or remove it.

        Returns:
            The number of distributions installed editable (0 when cleared).

        """
        context = FlextInfraWorkspaceDetector.resolution_context(
            request.repository_root,
        )
        if context.failure:
            return r[int].from_failure(context)
        runtime_root = context.value.runtime_root
        environment = (
            request.candidate_environment
            if request.candidate_environment is not None
            else u.Infra.runtime_environment_dir(
                runtime_root, runtime_root=runtime_root
            )
        )
        if (
            not environment.is_absolute()
            or environment.is_symlink()
            or environment.name != c.Infra.ENVIRONMENT_DIRECTORY
            or not environment.resolve().is_relative_to(runtime_root.resolve())
        ):
            return r[int].fail(
                "editable selection environment is outside its owned runtime"
            )
        receipt = cls.receipt_path(environment.parent)
        if request.flext_root is None:
            receipt.unlink(missing_ok=True)
            return r[int].ok(0)
        if cls._ci_context():
            return r[int].fail(
                f"FLEXT={request.flext_root} is a local development input; "
                "CI installs frozen locks only",
            )
        return cls._elect(
            runtime_root,
            request.flext_root.expanduser().resolve(),
            candidate_environment=environment,
        ).flat_map(
            lambda selection: cls._install(
                runtime_root, selection, candidate_environment=environment
            )
        )

    @classmethod
    def _resolve_provided_distributions(
        cls, runtime_root: Path, flext_root: Path, *, candidate_environment: Path
    ) -> p.Result[tuple[dict[str, Path], tuple[str, ...]]]:
        """Resolve the FLEXT distributions installed in one consumer environment.

        Returns:
            The provided distribution sources and the metadata paths.

        """
        spec = FlextInfraWorkspaceDetector.load_workspace_spec(flext_root)
        if spec.failure:
            return r[tuple[dict[str, Path], tuple[str, ...]]].from_failure(spec)
        observed = FlextInfraBindingService.consumer_package_environment(
            consumer_root=runtime_root,
            python=u.Infra.environment_python(candidate_environment),
            packages=(),
            candidate_environment=candidate_environment,
        )
        if observed.failure:
            return r[tuple[dict[str, Path], tuple[str, ...]]].from_failure(observed)
        metadata_paths = tuple(str(path) for path in observed.value.metadata_paths)
        provided = (
            (spec.value.repository, flext_root),
            *(
                (repository, flext_root / repository.path)
                for repository in spec.value.subprojects
            ),
        )
        # Every distribution the consumer DECLARES and the workspace PROVIDES is
        # an editable candidate — not only the currently-installed ones. The
        # frozen sync before this step may have removed a member entirely;
        # electing from installed
        # state alone then never restores it and the consumer's pin check fails
        # forever. The declared-deps intersection keeps workspace members the
        # consumer does not use (e.g. the umbrella meta-distribution) out of the
        # receipt — the provenance gate needs an installed distribution per
        # receipt member.
        document = u.Cli.toml_read_document(runtime_root / c.PYPROJECT_FILENAME)
        if document.failure:
            return r[tuple[dict[str, Path], tuple[str, ...]]].from_failure(document)
        consumer_name = canonicalize_name(
            u.Infra.project_name_from_payload(
                runtime_root / c.PYPROJECT_FILENAME, document.value
            )
        )
        declared = {
            canonicalize_name(name)
            for name in u.Infra.declared_dependency_names(document.value)
        }
        declared.add(consumer_name)
        distributions = {
            repository.distribution: (
                runtime_root
                if canonicalize_name(repository.distribution) == consumer_name
                else source.resolve()
            )
            for repository, source in provided
            if repository.package
            and canonicalize_name(repository.distribution) in declared
        }
        return r[tuple[dict[str, Path], tuple[str, ...]]].ok(
            (distributions, metadata_paths),
        )

    @staticmethod
    def _bind_editables(
        runtime_root: Path,
        sources: Mapping[str, Path],
        *,
        python: str,
        uv: Path,
    ) -> p.Result[bool]:
        """Replace locked distributions with editable bindings of their sources.

        Native UV builds the replacement before removing the current install,
        retaining the prior distribution if the build fails. Reinstallation
        refreshes strict editable file links as well as locked origins. The binding
        never discovers project configuration (``--no-config``): any
        ``[tool.uv] override-dependencies``, including the FLEXT workspace's
        own, would replace these explicit editable requests with the
        overridden git source. The binding is path-based
        (``c.Infra.FLEXT_EDITABLE_BUILD_SETTING``) so static resolvers see the
        source, never an import-hook finder only the interpreter follows.

        Returns:
            Success once the native replacement succeeds; its original failure
            otherwise.

        """
        installed = u.Cli.run_live(
            (
                str(uv),
                "pip",
                "install",
                "--no-config",
                "--reinstall",
                "--refresh",
                "--python",
                python,
                "--no-deps",
                "--config-setting",
                c.Infra.FLEXT_EDITABLE_BUILD_SETTING,
                *(
                    argument
                    for source in sources.values()
                    for argument in ("--editable", str(source))
                ),
            ),
            cwd=runtime_root,
            timeout=c.Infra.TIMEOUT_LONG,
        )
        if installed.failure:
            return r[bool].from_failure(installed)
        return r[bool].ok(value=True)

    @classmethod
    def _execute_pip_install(
        cls,
        runtime_root: Path,
        selection: p.Infra.FlextEditableSelection,
        *,
        python: str,
        uv: Path,
        candidate_environment: Path,
    ) -> p.Result[bool]:
        """Bind selected source directories editable and verify the result.

        The preceding frozen UV install owns the entire dependency graph; this
        pip operation only binds source directories, then checks the graph and
        verifies the installed origins match the selection.

        Returns:
            Whether the installation and verification succeeded.

        """
        pending = cls._pending_sources(
            runtime_root, selection, candidate_environment=candidate_environment
        )
        if pending.failure:
            return r[bool].from_failure(pending)
        sources = dict(pending.value)
        for name, source in selection.distributions.items():
            if name in sources:
                continue
            packaging = m.Infra.ProjectPackagingDeclaration.model_validate(
                u.Infra.pyproject_payload(source / c.PYPROJECT_FILENAME)
            )
            if packaging.build_backend in c.Infra.FLEXT_EDITABLE_SNAPSHOT_BACKENDS:
                sources[name] = source
        if sources:
            bound = cls._bind_editables(runtime_root, sources, python=python, uv=uv)
            if bound.failure:
                return bound
        checked = u.Cli.run_live(
            (str(uv), "pip", "check", "--python", python),
            cwd=runtime_root,
            timeout=c.Infra.TIMEOUT_LONG,
        )
        if checked.failure:
            return r[bool].from_failure(checked)
        verified = cls._pending_sources(
            runtime_root, selection, candidate_environment=candidate_environment
        )
        if verified.failure:
            return r[bool].from_failure(verified)
        if verified.value:
            return r[bool].fail(
                "installed editable origins differ from selection: "
                + ", ".join(verified.value)
            )
        return r[bool].ok(value=True)

    @classmethod
    def _install(
        cls,
        runtime_root: Path,
        selection: p.Infra.FlextEditableSelection,
        *,
        candidate_environment: Path,
    ) -> p.Result[int]:
        """Reinstall the selection editable, then publish its receipt.

        Returns:
            The number of distributions installed editable.

        """
        uv = u.Infra.managed_mise_binary("uv", runtime_root)
        if uv.failure:
            return r[int].from_failure(uv)
        python = str(u.Infra.environment_python(candidate_environment))
        executed = cls._execute_pip_install(
            runtime_root,
            selection,
            python=python,
            uv=uv.value,
            candidate_environment=candidate_environment,
        )
        if executed.failure:
            return r[int].from_failure(executed)
        return cls._record_editable_selection(
            runtime_root,
            selection,
            python=python,
            candidate_environment=candidate_environment,
        )

    @classmethod
    def _record_editable_selection(
        cls,
        runtime_root: Path,
        selection: p.Infra.FlextEditableSelection,
        *,
        python: str,
        candidate_environment: Path,
    ) -> p.Result[int]:
        """Verify installed editables and publish their selection receipt.

        Returns:
            The number of selected distributions, or the first verification failure.

        """
        observed = FlextInfraBindingService.consumer_package_environment(
            consumer_root=runtime_root,
            python=Path(python),
            packages=(),
            candidate_environment=candidate_environment,
        )
        if observed.failure:
            return r[int].from_failure(observed)
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            selection.flext_root
        )
        if workspace.failure:
            return r[int].from_failure(workspace)
        provided = {
            canonicalize_name(repository.distribution)
            for repository in (workspace.value.repository, *workspace.value.subprojects)
            if repository.package
        }
        packages = cls._editable_package_sources(selection, provided, observed.value)
        if packages.failure:
            return r[int].from_failure(packages)
        loaded = FlextInfraBindingService.consumer_package_environment(
            consumer_root=runtime_root,
            python=Path(python),
            packages=tuple(packages.value),
            candidate_environment=candidate_environment,
        )
        if loaded.failure:
            return r[int].from_failure(loaded)
        for package, source in packages.value.items():
            origins = loaded.value.package_directories[package]
            if not origins or any(
                not origin.is_relative_to(source.resolve()) for origin in origins
            ):
                return r[int].fail(
                    f"loaded editable package differs from selection: {package}: "
                    f"{origins}"
                )
        for name, source in selection.distributions.items():
            u.Cli.info(f"setup editable distribution={name} source={source}")
        receipt = cls.receipt_path(candidate_environment.parent)
        u.Cli.ensure_dir(receipt.parent).unwrap()
        return u.Cli.atomic_write_text_file(
            receipt,
            selection.model_dump_json(indent=2),
        ).map(lambda _written: len(selection.distributions))

    @staticmethod
    def _editable_package_sources(
        selection: p.Infra.FlextEditableSelection,
        provided: set[NormalizedName],
        observed: p.Infra.PythonEnvironmentObservation,
    ) -> p.Result[dict[str, Path]]:
        """Resolve each selected distribution's uniquely owned import packages.

        Returns:
            The import-package-to-source mapping, or the first ownership failure.

        """
        packages: dict[str, Path] = {}
        for distribution, source in selection.distributions.items():
            normalized = canonicalize_name(distribution)
            if normalized in provided:
                declarations = (
                    FlextInfraWorkspaceEnvironment.editable_declared_packages(
                        distribution, source
                    )
                )
                if declarations.failure:
                    return r[dict[str, Path]].from_failure(declarations)
                declared = tuple(name for name, _path in declarations.value)
            else:
                declared = tuple(
                    package
                    for package, providers in observed.package_distributions.items()
                    if normalized in map(canonicalize_name, providers)
                )
            for package in declared:
                if not isinstance(package, str) or not package:
                    return r[dict[str, Path]].fail(
                        "installed distribution declares no import packages: "
                        f"{distribution}"
                    )
                if packages.setdefault(package, source) != source:
                    return r[dict[str, Path]].fail(
                        f"competing editable import owners: {package}"
                    )
            if not declared:
                return r[dict[str, Path]].fail(
                    "installed distribution declares no import packages: "
                    f"{distribution}"
                )
        return r[dict[str, Path]].ok(packages)

    @classmethod
    def _elect(
        cls, runtime_root: Path, flext_root: Path, *, candidate_environment: Path
    ) -> p.Result[p.Infra.FlextEditableSelection]:
        """Select the FLEXT distributions this environment installed from its lock.

        Returns:
            The selection naming each provided and installed distribution.

        """
        result_type = r[p.Infra.FlextEditableSelection]
        if not (flext_root / c.Infra.GITMODULES).is_file():
            return result_type.fail(
                f"FLEXT={flext_root} is not a FLEXT workspace: no .gitmodules",
            )
        provided = cls._resolve_provided_distributions(
            runtime_root, flext_root, candidate_environment=candidate_environment
        )
        if provided.failure:
            return result_type.from_failure(provided)
        distributions, metadata_paths = provided.value
        configured = cls._configured_sources(runtime_root, flext_root, metadata_paths)
        if configured.failure:
            return result_type.from_failure(configured)
        for name, source in configured.value.items():
            if name in distributions and distributions[name] != source:
                return result_type.fail(
                    f"competing editable source declarations: {name}"
                )
            distributions[name] = source
        if not distributions:
            return result_type.fail(
                f"FLEXT={flext_root} provides no distribution installed in "
                f"{runtime_root}",
            )
        return result_type.ok(
            m.Infra.FlextEditableSelection(
                flext_root=flext_root,
                distributions=distributions,
            ),
        )

    @staticmethod
    def _configured_sources(
        runtime_root: Path, flext_root: Path, metadata_paths: tuple[str, ...]
    ) -> p.Result[Mapping[str, Path]]:
        """Elect explicitly configured sources from the installed dependency graph.

        A relative source resolves against the selected FLEXT workspace, the
        one physical root every checkout of the consumer shares, never against
        the consumer checkout (a linked worktree has other siblings).

        Returns:
            Validated project names and their physical source directories.

        """
        inputs = u.Infra.load_codegen_inputs(runtime_root)
        if inputs.failure:
            return r.from_failure(inputs)
        selected: dict[str, Path] = {}
        for name, declared in inputs.value.spec.toolchain.editable_sources.items():
            source = declared.expanduser()
            source = (source if source.is_absolute() else flext_root / source).resolve(
                strict=True
            )
            manifest = source / c.PYPROJECT_FILENAME
            actual = u.Infra.project_name_from_payload(
                manifest, u.Infra.pyproject_payload(manifest)
            )
            if actual != name:
                return r.fail(f"editable source identity differs: {name} != {actual}")
            if not u.installed_distributions(name=name, path=metadata_paths):
                return r.fail(f"editable source is not in the installed graph: {name}")
            selected[name] = source
        return r.ok(selected)

    @staticmethod
    def _pending_sources(
        runtime_root: Path,
        selection: p.Infra.FlextEditableSelection,
        *,
        candidate_environment: Path,
    ) -> p.Result[Mapping[str, Path]]:
        """Observe which selected origins still require source binding.

        Returns:
            Pending bindings, or an original physical provenance failure.

        """
        observed = FlextInfraBindingService.consumer_package_environment(
            consumer_root=runtime_root,
            python=u.Infra.environment_python(candidate_environment),
            packages=(),
            candidate_environment=candidate_environment,
        )
        if observed.failure:
            return r.from_failure(observed)
        metadata_paths = tuple(str(path) for path in observed.value.metadata_paths)
        provenance = FlextInfraWorkspaceEnvironment
        pending: dict[str, Path] = {}
        for name, source in selection.distributions.items():
            matches = u.installed_distributions(name=name, path=metadata_paths)
            if not matches:
                pending[name] = source
                continue
            if (
                len(matches) == 1
                and Path(str(matches[0].locate_file("")))
                .resolve()
                .is_relative_to(observed.value.prefix.resolve())
                and matches[0].read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE) is None
            ):
                pending[name] = source
                continue
            installed = provenance.distribution_installation(
                name,
                metadata_paths=metadata_paths,
                environment_root=observed.value.prefix,
            )
            if installed.failure:
                return r.from_failure(installed)
            _distribution, _raw, receipt = installed.value
            if (
                receipt.dir_info is None
                or not receipt.dir_info.editable
                or receipt.vcs_info is not None
                or receipt.url != source.as_uri()
            ):
                pending[name] = source
        return r.ok(pending)

    @classmethod
    def admitted_sources(cls, runtime_root: Path) -> p.Result[Mapping[str, Path]]:
        """Return the editable sources the local receipt admits, by distribution.

        CI never honours a selection, so every editable install there stays a
        provenance failure.

        Returns:
            The recorded distribution sources; empty when nothing is selected.

        """
        receipt = cls.receipt_path(runtime_root)
        if cls._ci_context() or not receipt.is_file():
            return r[Mapping[str, Path]].ok({})
        selection = m.Infra.FlextEditableSelection.model_validate_json(
            receipt.read_text(encoding=c.DEFAULT_ENCODING),
        )
        return r[Mapping[str, Path]].ok(selection.distributions)


__all__: list[str] = ["FlextInfraWorkspaceFlextEditable"]
