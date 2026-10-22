"""Session binding of an external consumer onto one flext worktree.

An external project declares flext packages by pinned git URL, so it always
validates PUBLISHED code. A cross-project change therefore could not be reviewed
until it was published, which inverts the order of work.

The explicit ``workspace flext-binding`` CLI rebinds the consumer's physical
environment onto that checkout for the session. The consumer's
``pyproject.toml`` is never modified; running canonical setup restores its
declared resolution. This operation requires the provisioned consumer Python
and rejects CI before reading or changing the consumer environment.

Like canonical setup, binding considers all declared extras and dependency
groups. Consumer interpreter markers select active requirements; unrelated
dependencies constrain resolution without being installed as new roots.

The rebind set is derived from the intersection of what the consumer declares
and what the worktree actually provides, read from the worktree's own manifest —
never a hardcoded package list.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sysconfig
from collections.abc import MutableMapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from flext_infra import c, config, m, r, t, u
from flext_infra.workspace import FlextInfraWorkspaceDetector

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraBindingService:
    """Resolve and apply one session binding onto a flext worktree."""

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
    ) -> p.Result[t.StrMapping]:
        """Read PEP 508 facts from the authenticated consumer interpreter.

        Returns:
            The resulting ``p.Result[t.StrMapping]``.

        """
        environment = cls._consumer_environment(consumer_root, python)
        if environment.failure:
            return r[t.StrMapping].from_failure(environment)
        outcome = u.Cli.run(
            (str(python), "-I", "-c", c.Infra.BINDING_MARKER_SCRIPT),
            cwd=consumer_root,
        )
        if outcome.failure:
            return r[t.StrMapping].from_failure(outcome)
        facts = m.Infra.DependencyMarkerEnvironment.model_validate_json(
            outcome.value.stdout,
        )
        if facts.prefix.resolve() != environment.value.resolve():
            return r[t.StrMapping].fail(
                "binding interpreter reports a foreign environment",
            )
        return r[t.StrMapping].ok({
            key: str(value) for key, value in facts.model_dump().items()
        })

    @staticmethod
    def consumer_package_environment(
        *,
        consumer_root: Path,
        python: Path,
        packages: t.StrSequence,
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

    @staticmethod
    def _document(consumer_root: Path) -> t.Cli.TomlDocument:
        """Read the consumer declaration through its canonical parser.

        Returns:
            The resulting ``t.Cli.TomlDocument``.

        Raises:
            ValueError: If consumer dependency declaration is not valid TOML.

        """
        document = u.Cli.toml_parse_text(
            u.Cli.files_read_text(consumer_root / c.PYPROJECT_FILENAME).unwrap(),
        )
        if document is None:
            msg = "consumer dependency declaration is not valid TOML"
            raise ValueError(msg)
        return document

    @staticmethod
    def _binding_paths(
        *,
        requirements: t.StrSequence,
        flext_root: Path,
    ) -> p.Result[t.MappingKV[str, m.Infra.RepositoryRef]]:
        """Return the distributions this worktree can supply to the consumer.

        Fails closed when ``flext_root`` is not a flext workspace, so a mistyped
        path can never silently bind nothing and leave the consumer on its pins.

        Returns:
            The supplier repository of each selected distribution, by name.

        """
        result = r[t.MappingKV[str, m.Infra.RepositoryRef]]
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(flext_root)
        if workspace.failure:
            return result.fail(
                f"FLEXT is not a flext workspace: {flext_root}: "
                f"{workspace.error or 'manifest unreadable'}",
            )
        available: MutableMapping[str, m.Infra.RepositoryRef] = {}
        for repository in (workspace.value.repository, *workspace.value.subprojects):
            if not repository.package:
                continue
            name = u.Infra.dep_name(repository.distribution)
            if name is None or name in available:
                return result.fail(
                    f"binding supplier has an invalid or duplicate "
                    f"distribution: {repository.distribution}",
                )
            available[name] = repository
        names = {u.Infra.dep_name(item) for item in requirements}
        selected = {
            name: available[name] for name in sorted(available) if name in names
        }
        if not selected:
            return result.fail(
                "requested binding selects no active declared dependency: "
                f"declared={names!r}; available={tuple(available)!r}",
            )
        for repository in selected.values():
            path = (flext_root / repository.path).resolve()
            if not (path / c.PYPROJECT_FILENAME).is_file():
                return result.fail(
                    f"binding supplier package is not provisioned: {path}",
                )
        return result.ok(selected)

    @classmethod
    def plan_targets(
        cls,
        *,
        consumer_root: Path,
        flext_root: Path,
        python: Path,
    ) -> p.Result[t.MappingKV[str, m.Infra.RepositoryRef]]:
        """Resolve targets with marker facts from the consumer's interpreter.

        Returns:
            The supplier repository of each selected distribution, by name.

        """
        environment = cls.consumer_marker_environment(
            consumer_root=consumer_root,
            python=python,
        )
        if environment.failure:
            return r[t.MappingKV[str, m.Infra.RepositoryRef]].from_failure(environment)
        requirements = u.Infra.active_session_requirements(
            cls._document(consumer_root),
            environment=environment.value,
        )
        return cls._binding_paths(requirements=requirements, flext_root=flext_root)

    @classmethod
    def apply(
        cls,
        *,
        consumer_root: Path,
        flext_root: Path,
        python: Path,
    ) -> p.Result[int]:
        """Rebind the consumer environment onto the worktree for this session.

        Returns:
            The resulting ``p.Result[int]``.

        """
        ci = config.Infra.codegen.make.ci
        if u.Infra.env_value(ci.variable) == ci.value:
            return r[int].fail(
                f"local editable binding is prohibited with {ci.variable}={ci.value}",
            )
        environment = cls.consumer_marker_environment(
            consumer_root=consumer_root,
            python=python,
        )
        if environment.failure:
            return r[int].from_failure(environment)
        document = cls._document(consumer_root)
        requirements = u.Infra.active_session_requirements(
            document,
            environment=environment.value,
        )
        planned = cls._binding_paths(requirements=requirements, flext_root=flext_root)
        if planned.failure:
            return r[int].from_failure(planned)
        paths = {
            name: (flext_root / repository.path).resolve()
            for name, repository in planned.value.items()
        }
        resolution = u.Infra.session_dependency_requirements(
            document,
            requirements=requirements,
            selected=tuple(paths),
            environment=environment.value,
        )
        if resolution.failure:
            return r[int].from_failure(resolution)
        editables: list[str] = []
        for name, path in paths.items():
            editables.extend((
                "--editable",
                str(path) + u.Infra.dependency_extras(requirements, name),
            ))
        owned_environment = cls._consumer_environment(consumer_root, python).unwrap()
        with TemporaryDirectory(dir=owned_environment) as directory:
            arguments: list[str] = []
            for (option, filename), lines in zip(
                c.Infra.BINDING_RESOLUTION_FILES,
                (
                    (
                        *resolution.value.overrides,
                        *(
                            f"{name}{u.Infra.dependency_extras(requirements, name)}"
                            f" @ {path.as_uri()}"
                            for name, path in paths.items()
                        ),
                    ),
                    resolution.value.constraints,
                ),
                strict=True,
            ):
                if lines:
                    path = Path(directory) / filename
                    u.Cli.files_write_text(path, "\n".join(lines) + "\n").unwrap()
                    arguments.extend((option, str(path)))
            installed = u.Cli.run_checked(
                (
                    c.Infra.UV,
                    "pip",
                    "install",
                    # Why: the binding already translated the consumer's
                    # [tool.uv] overrides/constraints into the files above;
                    # uv would otherwise rediscover them from the cwd project
                    # and re-apply an override to the bound editable, sending
                    # its name to the registry instead of the worktree path.
                    "--no-config",
                    "--python",
                    str(python),
                    *arguments,
                    *editables,
                ),
                cwd=consumer_root,
            )
            if installed.failure:
                return r[int].from_failure(installed)
        # Resolve the consumer contract first; directory overrides are not editable.
        # Bind the sources without resolving that already-validated closure again.
        u.Cli.run_checked(
            (
                c.Infra.UV,
                "pip",
                "install",
                "--no-config",
                "--no-deps",
                "--reinstall",
                "--python",
                str(python),
                *editables,
            ),
            cwd=consumer_root,
        ).unwrap()
        u.Cli.info(
            f"flext binding: {len(paths)} package(s) bound to {flext_root} "
            f"({', '.join(paths)}); consumer_python={python}",
        )
        return r[int].ok(0)


__all__: list[str] = ["FlextInfraBindingService"]
