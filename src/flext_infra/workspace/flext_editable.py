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
        request: m.Infra.FlextEditableRequest,
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
        receipt = cls.receipt_path(runtime_root)
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
        ).flat_map(lambda selection: cls._install(runtime_root, selection))

    @classmethod
    def _install(
        cls,
        runtime_root: Path,
        selection: m.Infra.FlextEditableSelection,
    ) -> p.Result[int]:
        """Reinstall the selection editable, then publish its receipt.

        Returns:
            The number of distributions installed editable.

        """
        uv = u.Infra.managed_mise_binary("uv", runtime_root)
        if uv.failure:
            return r[int].from_failure(uv)
        python = str(u.Infra.runtime_python(runtime_root, runtime_root=runtime_root))
        pending = cls._pending_sources(runtime_root, selection)
        if pending.failure:
            return r[int].from_failure(pending)
        # The preceding frozen UV install owns the entire dependency graph.
        # This pip operation only binds selected source directories; the graph
        # and actual installed origins must still be verified before admission.
        if pending.value:
            installed = u.Cli.run_live(
                (
                    python,
                    "-m",
                    "pip",
                    "install",
                    "--no-deps",
                    *(
                        argument
                        for source in pending.value.values()
                        for argument in ("--editable", str(source))
                    ),
                ),
                cwd=runtime_root,
                timeout=c.Infra.TIMEOUT_LONG,
            )
            if installed.failure:
                return r[int].from_failure(installed)
        checked = u.Cli.run_live(
            (str(uv.value), "pip", "check", "--python", python),
            cwd=runtime_root,
            timeout=c.Infra.TIMEOUT_LONG,
        )
        if checked.failure:
            return r[int].from_failure(checked)
        verified = cls._pending_sources(runtime_root, selection)
        if verified.failure:
            return r[int].from_failure(verified)
        if verified.value:
            return r[int].fail(
                "installed editable origins differ from selection: "
                + ", ".join(verified.value)
            )
        for name, source in selection.distributions.items():
            u.Cli.info(f"setup editable distribution={name} source={source}")
        receipt = cls.receipt_path(runtime_root)
        u.Cli.ensure_dir(receipt.parent).unwrap()
        return u.Cli.atomic_write_text_file(
            receipt,
            selection.model_dump_json(indent=2),
        ).map(lambda _written: len(selection.distributions))

    @classmethod
    def _elect(
        cls,
        runtime_root: Path,
        flext_root: Path,
    ) -> p.Result[m.Infra.FlextEditableSelection]:
        """Select the FLEXT distributions this environment installed from its lock.

        Returns:
            The selection naming each provided and installed distribution.

        """
        result_type = r[m.Infra.FlextEditableSelection]
        if not (flext_root / c.Infra.GITMODULES).is_file():
            return result_type.fail(
                f"FLEXT={flext_root} is not a FLEXT workspace: no .gitmodules",
            )
        spec = FlextInfraWorkspaceDetector.load_workspace_spec(flext_root)
        if spec.failure:
            return result_type.from_failure(spec)
        observed = FlextInfraBindingService.consumer_package_environment(
            consumer_root=runtime_root,
            python=u.Infra.runtime_python(runtime_root, runtime_root=runtime_root),
            packages=(),
        )
        if observed.failure:
            return result_type.from_failure(observed)
        metadata_paths = tuple(str(path) for path in observed.value.metadata_paths)
        provided = (
            (spec.value.repository, flext_root),
            *(
                (repository, flext_root / repository.path)
                for repository in spec.value.subprojects
            ),
        )
        distributions = {
            repository.distribution: source.resolve()
            for repository, source in provided
            if repository.package
            and u.installed_distributions(
                name=repository.distribution,
                path=metadata_paths,
            )
        }
        configured = cls._configured_sources(runtime_root, metadata_paths)
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
        runtime_root: Path, metadata_paths: tuple[str, ...]
    ) -> p.Result[Mapping[str, Path]]:
        """Elect explicitly configured sources from the installed dependency graph.

        Returns:
            Validated project names and their physical source directories.

        """
        inputs = u.Infra.load_codegen_inputs(runtime_root)
        if inputs.failure:
            return r.from_failure(inputs)
        selected: dict[str, Path] = {}
        for name, declared in inputs.value.spec.toolchain.editable_sources.items():
            source = declared.expanduser()
            source = (
                source if source.is_absolute() else runtime_root / source
            ).resolve(strict=True)
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
        runtime_root: Path, selection: m.Infra.FlextEditableSelection
    ) -> p.Result[Mapping[str, Path]]:
        """Observe which selected origins still require source binding.

        Returns:
            Pending bindings, or an original physical provenance failure.

        """
        observed = FlextInfraBindingService.consumer_package_environment(
            consumer_root=runtime_root,
            python=u.Infra.runtime_python(runtime_root, runtime_root=runtime_root),
            packages=(),
        )
        if observed.failure:
            return r.from_failure(observed)
        metadata_paths = tuple(str(path) for path in observed.value.metadata_paths)
        provenance = FlextInfraWorkspaceEnvironment
        pending: dict[str, Path] = {}
        for name, source in selection.distributions.items():
            matches = u.installed_distributions(name=name, path=metadata_paths)
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
