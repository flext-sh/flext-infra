"""Explicit locked repair of one declared native tool installation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, p, r, s, settings, u
from flext_infra.codegen import FlextInfraCodegenMiseToolchainProof


class FlextInfraCodegenMiseToolchainRepair(s[bool]):
    """Reinstall the selected locked tool, then use the existing reality proof."""

    repository_root: Annotated[
        Path,
        m.Field(description="Repository owning the selected tool and lock."),
    ]

    def _prepare(self, requested: str) -> m.Infra.MiseToolchainRepairPlan:
        """Bind the requested declaration and every required input before effects.

        Returns:
            The validated locked installation plan.

        Raises:
            ValueError: If the requested tool is not declared by the repository.

        """
        root = self.repository_root.expanduser().resolve()
        inputs = u.Infra.load_codegen_inputs(root).unwrap()
        entry = next(
            (tool for tool in inputs.spec.toolchain.tools if tool.name == requested),
            None,
        )
        if entry is None:
            message = f"toolchain repair refuses undeclared tool: {requested}"
            raise ValueError(message)
        states = tuple(
            u.Cli.atomic_read_binary_file_state(root / name, required=True).unwrap()
            for name in (c.Infra.MISE_TOML_FILENAME, c.Infra.MISE_LOCK_FILENAME)
        )
        lock = u.Cli.toml_read_json(root / c.Infra.MISE_LOCK_FILENAME).unwrap()
        version, _ = FlextInfraCodegenMiseToolchainProof.lock_identity(
            entry,
            lock,
            FlextInfraCodegenMiseToolchainProof.current_platform().unwrap(),
        ).unwrap()
        return m.Infra.MiseToolchainRepairPlan(
            repository_root=root,
            tool=entry.selector or entry.name,
            version=version,
            mise_executable=u.Infra.managed_mise_self(root).unwrap(),
            uv_executable=u.Infra.managed_mise_binary(c.Infra.UV, root).unwrap(),
            source_states=(*inputs.sources, *states),
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Repair only an explicit selection and reject any incomplete proof.

        Returns:
            The complete reality-proof result or the first installation failure.

        """
        requested = settings.Infra.toolchain_repair_tool
        if requested is None:
            alias = u.type_adapter(str).validate_python(
                type(settings.Infra)
                .model_fields["toolchain_repair_tool"]
                .validation_alias,
            )
            return r[bool].fail(
                f"fix-toolchain requires {alias} to name one declared tool",
            )
        plan = self._prepare(requested)
        u.Cli.atomic_verify_binary_file_states(plan.source_states).unwrap()
        installed = u.Cli.run_live(
            (
                str(plan.mise_executable),
                "-C",
                str(plan.repository_root),
                "install",
                "--locked",
                "--yes",
                "--force",
                f"{plan.tool}@{plan.version}",
            ),
            cwd=plan.repository_root,
            timeout=c.Infra.TIMEOUT_LONG,
        )
        if installed.failure:
            return r[bool].from_failure(installed)
        u.Cli.atomic_verify_binary_file_states(plan.source_states).unwrap()
        return FlextInfraCodegenMiseToolchainProof(
            repository_root=plan.repository_root,
            uv_executable=plan.uv_executable,
        ).execute()


__all__ = ["FlextInfraCodegenMiseToolchainRepair"]
