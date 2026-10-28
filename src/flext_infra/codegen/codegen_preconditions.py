"""Rendering-engine precondition: the running engine is the one the lock pins.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from functools import partial
from json import dumps
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, config, m, p, r, workspace as workspace_services

if TYPE_CHECKING:
    from importlib.metadata import Distribution


class FlextInfraCodegenPreconditions:
    """Prove the executing flext-infra is the engine the target lock pins."""

    @staticmethod
    def rendering_engine(repository_root: Path) -> p.Result[bool]:
        """Prove the executing engine is the flext-infra the target's lock pins.

        Editable bindings and targets without an engine pin use their own tree.

        Returns:
            Success only for the declared rendering origin and registry version.

        """
        result_type = r[bool]
        context = workspace_services.FlextInfraWorkspaceDetector.resolution_context(
            repository_root
        )
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
                    partial(
                        m.Infra.LockedEnvironment.model_validate_json,
                        dumps(payload),
                    )
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
        origin = (
            workspace_services.FlextInfraWorkspaceEnvironmentProvenance.locked_origin_verdict
        )(distribution_name, item, direct_url)
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


__all__: list[str] = ["FlextInfraCodegenPreconditions"]
