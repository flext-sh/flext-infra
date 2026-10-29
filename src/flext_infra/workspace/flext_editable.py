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
from flext_infra.workspace import FlextInfraBindingService, FlextInfraWorkspaceDetector


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
        # --no-config keeps the consumer's own override-dependencies (its
        # pinned Git sources) from replacing the editable requirements.
        # Frozen installation already owns dependencies; source binding must
        # preserve that installed graph rather than resolve it a second time.
        installed = u.Cli.run_live(
            (
                str(uv.value),
                "pip",
                "install",
                "--no-config",
                "--no-deps",
                "--python",
                python,
                *(
                    argument
                    for source in selection.distributions.values()
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
        receipt = cls.receipt_path(runtime_root)
        u.Cli.ensure_dir(receipt.parent).unwrap()
        return u.Cli.atomic_write_text_file(
            receipt,
            selection.model_dump_json(indent=2),
        ).map(lambda _written: len(selection.distributions))

    @staticmethod
    def _elect(
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
            spec.value.repository.model_copy(update={"path": Path()}),
            *spec.value.subprojects,
        )
        distributions = {
            repository.distribution: (flext_root / repository.path).resolve()
            for repository in provided
            if repository.package
            and u.installed_distributions(
                name=repository.distribution,
                path=metadata_paths,
            )
        }
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
