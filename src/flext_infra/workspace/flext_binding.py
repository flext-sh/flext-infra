"""Observe the provisioned consumer's physical Python environment.

Native uv declarations and locks own installation and source selection. This
service only observes interpreter markers, package resolution and metadata for
the existing post-install provenance consumers; it never rebinds packages.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sysconfig
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, u
from flext_infra.workspace import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraBindingService:
    """Observe installed interpreter and package facts without changing sources."""

    @staticmethod
    def _consumer_environment(consumer_root: Path, python: Path) -> p.Result[Path]:
        """Require a physical consumer environment while permitting base Python links.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        context = FlextInfraWorkspaceDetector.resolution_context(consumer_root)
        if context.failure:
            return r[Path].from_failure(context)
        environment = context.value.environment_path
        scripts = Path(
            sysconfig.get_path(
                "scripts",
                scheme="venv",
                vars={"base": str(environment), "platbase": str(environment)},
            ),
        )
        expected = scripts / c.Infra.PromotedSelector.VENV_PYTHON
        # A composed member's own environment path must not borrow another
        # checkout's environment either, even when the workspace owns the runtime.
        for path in (
            environment,
            scripts,
            consumer_root / c.Infra.ENVIRONMENT_DIRECTORY,
        ):
            if path.is_symlink():
                return r[Path].fail(
                    f"binding requires a physical consumer environment: {path}",
                )
        if python.absolute() != expected.absolute():
            return r[Path].fail(
                f"binding interpreter must belong to the consumer: "
                f"expected={expected}, actual={python}",
            )
        if not (environment / c.Infra.ENVIRONMENT_METADATA).is_file() or not os.access(
            expected,
            os.X_OK,
        ):
            return r[Path].fail(
                f"binding requires the consumer's provisioned environment: "
                f"{environment}; run make setup",
            )
        return r[Path].ok(environment)

    @classmethod
    def consumer_marker_environment(
        cls,
        *,
        consumer_root: Path,
        python: Path,
    ) -> p.Result[Mapping[str, str]]:
        """Read PEP 508 facts from the authenticated consumer interpreter.

        Returns:
            The resulting ``p.Result[Mapping[str, str]]``.

        """
        environment = cls._consumer_environment(consumer_root, python)
        if environment.failure:
            return r[Mapping[str, str]].from_failure(environment)
        outcome = u.Cli.run(
            (str(python), "-I", "-c", c.Infra.BINDING_MARKER_SCRIPT),
            cwd=consumer_root,
        )
        if outcome.failure:
            return r[Mapping[str, str]].from_failure(outcome)
        facts = m.Infra.DependencyMarkerEnvironment.model_validate_json(
            outcome.value.stdout,
        )
        if facts.prefix.resolve() != environment.value.resolve():
            return r[Mapping[str, str]].fail(
                "binding interpreter reports a foreign environment",
            )
        return r[Mapping[str, str]].ok({
            key: str(value) for key, value in facts.model_dump().items()
        })

    @staticmethod
    def consumer_package_environment(
        *,
        consumer_root: Path,
        python: Path,
        packages: Sequence[str],
    ) -> p.Result[m.Infra.PythonEnvironmentObservation]:
        """Observe real package resolution and metadata in the elected Python.

        Returns:
            The observed package environment, or the first observation failure.

        """
        result_type = r[m.Infra.PythonEnvironmentObservation]
        environment = FlextInfraBindingService._consumer_environment(
            consumer_root,
            python,
        )
        if environment.failure:
            return result_type.from_failure(environment)
        physical = u.Cli.atomic_plan_directory_chain(environment.value)
        if physical.failure:
            return result_type.from_failure(physical)
        outcome = u.Cli.run(
            (str(python), "-I", "-c", c.Infra.BINDING_PACKAGE_SCRIPT, *packages),
            cwd=consumer_root,
        )
        if outcome.failure:
            return result_type.from_failure(outcome)
        facts = m.Infra.PythonEnvironmentObservation.model_validate_json(
            outcome.value.stdout,
        )
        identity = FlextInfraBindingService._validated_package_facts(
            environment.value,
            facts,
        )
        if identity.failure:
            return result_type.from_failure(identity)
        stable = FlextInfraBindingService._confirm_stable_environment(
            environment.value,
            physical.value,
        )
        if stable.failure:
            return result_type.from_failure(stable)
        u.Cli.info(
            f"environment python={python} prefix={facts.prefix} "
            f"metadata_paths={facts.metadata_paths}",
        )
        return result_type.ok(facts)

    @staticmethod
    def _validated_package_facts(
        environment: Path,
        facts: m.Infra.PythonEnvironmentObservation,
    ) -> p.Result[bool]:
        """Validate the reported facts against the elected environment.

        Requires the interpreter prefix, installed metadata directories, and
        every metadata path to agree with the elected environment.

        Returns:
            Success when every reported fact matches the elected environment.

        """
        result_type = r[bool]
        if facts.prefix.resolve() != environment.resolve():
            return result_type.fail("package interpreter reports a foreign environment")
        if not facts.metadata_paths:
            return result_type.fail(
                "package interpreter has no installed metadata directories",
            )
        for path in facts.metadata_paths:
            if not path.is_absolute() or not path.is_relative_to(
                facts.prefix.resolve()
            ):
                return result_type.fail(
                    f"installed metadata directory is outside the elected "
                    f"environment: {path}",
                )
            directory = u.Cli.atomic_plan_directory_chain(path)
            if directory.failure:
                return result_type.from_failure(directory)
            if directory.value.directories:
                return result_type.fail(
                    f"installed metadata directory is absent: {path}",
                )
        return result_type.ok(value=True)

    @staticmethod
    def _confirm_stable_environment(
        environment: Path,
        physical: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[bool]:
        """Require the elected environment identity to survive the observation.

        Returns:
            Success when the physical directory chain still matches the plan
            recorded before the interpreter probe.

        """
        result_type = r[bool]
        current = u.Cli.atomic_plan_directory_chain(environment)
        if current.failure:
            return result_type.from_failure(current)
        if current.value != physical:
            return result_type.fail(
                "package environment identity changed during observation",
            )
        return result_type.ok(value=True)


__all__: list[str] = ["FlextInfraBindingService"]
