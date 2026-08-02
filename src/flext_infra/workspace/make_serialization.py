"""Capability-driven execution for the generated Make interface."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, override

from flext_core import r
from flext_infra import c, config, m, p, u
from flext_infra.base import s
from flext_infra.workspace._make_quality import FlextInfraMakeQualityMixin
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.serialization_lock import FlextInfraSerializationLockOwner


class FlextInfraMakeSerializationService(
    FlextInfraMakeQualityMixin, s[m.Infra.ProcessExit]
):
    """Resolve and execute one typed Make operation through its existing owner."""

    verb: Annotated[str, m.Field(description="Configured public Make verb")]
    makefile: Annotated[
        Path, m.Field(description="Generated Make owner for the invoked operation")
    ]
    selector_value: Annotated[
        str, m.Field(description="Caller selector; empty resolves from the verb graph")
    ] = ""
    apply_token: Annotated[
        str, m.Field(description="Caller mutation token validated by the graph")
    ] = ""
    make_level: Annotated[
        int,
        m.Field(ge=0, description="GNU Make recursion level at the public boundary"),
    ]

    @staticmethod
    def _profile(
        target: m.Infra.RepositoryConformTarget,
    ) -> p.Result[m.Infra.ProfileSpec]:
        profiles = tuple(
            item
            for item in config.Infra.codegen.profiles
            if item.name == target.make_profile
        )
        if len(profiles) != 1:
            return r.fail(
                f"Make profile must resolve exactly once: {target.make_profile}"
            )
        return r.ok(profiles[0])

    def _eligible_targets(
        self,
        workspace_root: Path,
        profile: m.Infra.ProfileSpec,
        invocation: m.Infra.MakeInvocationSpec,
        governed: tuple[m.Infra.MakeTargetSpec, ...],
    ) -> tuple[m.Infra.MakeTargetSpec, ...]:
        """Apply operation, environment, CI, and profile scope precedence."""
        current = tuple(item for item in governed if item.root == self.root.resolve())
        if invocation.operation.scope == "self":
            return current
        if invocation.operation.scope == "environment-owner":
            return (
                tuple(item for item in governed if item.root == workspace_root)
                if profile.environment_scope == "root"
                else current
            )
        if invocation.target_scope == "self":
            return current
        return governed if profile.execution_scope == "root" else current

    @classmethod
    def _requested_targets(
        cls,
        eligible: tuple[m.Infra.MakeTargetSpec, ...],
        requested: tuple[str, ...],
    ) -> p.Result[tuple[m.Infra.MakeTargetSpec, ...]]:
        """Resolve and stably deduplicate every external project selector."""
        return r.traverse(
            requested,
            lambda selector: cls._requested_target(eligible, selector),
        ).map(
            lambda selected: tuple(
                {target.root: target for target in selected}.values()
            )
        )

    @staticmethod
    def _requested_target(
        eligible: tuple[m.Infra.MakeTargetSpec, ...], selector: str
    ) -> p.Result[m.Infra.MakeTargetSpec]:
        """Resolve one external selector to exactly one governed target."""
        matches = tuple(
            item
            for item in eligible
            if selector
            in {
                item.repository.name,
                item.repository.distribution,
                item.repository.path.as_posix(),
            }
        )
        if len(matches) != 1:
            return r.fail(f"project selector must resolve exactly once: {selector}")
        return r.ok(matches[0])

    def _select_targets(
        self,
        workspace_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        profile: m.Infra.ProfileSpec,
        invocation: m.Infra.MakeInvocationSpec,
    ) -> p.Result[tuple[m.Infra.MakeTargetSpec, ...]]:
        """Select the operation's governed runtime targets."""
        governed = self._governed_targets(workspace_root, workspace)
        eligible = self._eligible_targets(
            workspace_root, profile, invocation, governed
        )
        requested = self._input_values(invocation, "projects")
        selected = (
            self._requested_targets(eligible, requested)
            if requested
            else r[tuple[m.Infra.MakeTargetSpec, ...]].ok(eligible)
        )
        if selected.failure:
            return selected
        candidates = selected.value
        if "package" in invocation.operation.requires:
            candidates = tuple(item for item in candidates if item.repository.package)
        if not candidates:
            return r.fail(
                f"Make operation {invocation.operation.name} resolved no targets"
            )
        return r.ok(candidates)

    @staticmethod
    def _is_managed_target(target: m.Infra.MakeTargetSpec) -> bool:
        """Validate the managed repository boundary from typed and live state."""
        repository = target.repository
        root = target.root
        return all(
            (
                not repository.read_only,
                repository.state is c.Infra.RepositoryState.ACTIVE,
                repository.codegen is not c.Infra.CodegenKind.NONE,
                root.is_dir(),
                (root / c.Infra.PYPROJECT_FILENAME).is_file(),
            )
        )

    @classmethod
    def _validate_target_capability(
        cls, selected: m.Infra.MakeTargetSpec, requirements: set[str]
    ) -> p.Result[bool]:
        """Validate one target against ordered operation requirements."""
        repository = selected.repository
        root = selected.root
        checks = (
            (
                "managed",
                cls._is_managed_target(selected),
                f"repository is not managed: {repository.name}",
            ),
            (
                "package",
                repository.package,
                f"repository is not a package: {repository.name}",
            ),
            (
                "git",
                (root / c.Infra.GIT_DIR).exists(),
                f"repository has no Git metadata: {root}",
            ),
            (
                "script",
                repository.script_dispatch is not None,
                f"repository has no script dispatcher: {repository.name}",
            ),
        )
        failures = tuple(
            message
            for requirement, valid, message in checks
            if all((requirement in requirements, not valid))
        )
        if failures:
            return r.fail(failures[0])
        return r.ok(True)

    @classmethod
    def _validate_target_capabilities(
        cls, context: m.Infra.MakeExecutionContext, requirements: set[str]
    ) -> p.Result[bool]:
        """Validate every selected target through the same capability table."""
        return r.traverse(
            context.targets,
            lambda selected: cls._validate_target_capability(
                selected, requirements
            ),
        ).map(lambda _: True)

    @staticmethod
    def _validate_environment_capability(
        context: m.Infra.MakeExecutionContext, requirements: set[str]
    ) -> p.Result[bool]:
        """Require the profile-owned interpreter for environment operations."""
        if "environment" not in requirements:
            return r.ok(True)
        environment = (
            context.environment_root
            / config.Infra.tooling.tools.pyright.path_rules.venv_name
        ).absolute()
        interpreter = Path(sys.executable).absolute()
        if not interpreter.is_file() or not interpreter.is_relative_to(environment):
            return r.fail(
                "Make runtime is not using the profile-owned environment: "
                f"{interpreter} (expected under {environment})"
            )
        return r.ok(True)

    @classmethod
    def _validate_capabilities(
        cls, context: m.Infra.MakeExecutionContext
    ) -> p.Result[bool]:
        """Validate target and environment requirements before execution."""
        requirements = set(context.invocation.operation.requires)
        return cls._validate_target_capabilities(context, requirements).flat_map(
            lambda _: cls._validate_environment_capability(context, requirements)
        )

    def _context_for_target(
        self,
        checkout: Path,
        workspace_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        target: m.Infra.RepositoryConformTarget,
    ) -> p.Result[m.Infra.MakeExecutionContext]:
        return u.Infra.repository_make_spec(
            config.Infra.codegen.make, target.repository
        ).flat_map(
            lambda make_config: self._resolve_invocation(make_config).flat_map(
                lambda invocation: self._profile(target).flat_map(
                    lambda profile: self._select_targets(
                        workspace_root, workspace, profile, invocation
                    ).map(
                        lambda targets: m.Infra.MakeExecutionContext(
                            workspace_root=workspace_root,
                            workspace=workspace,
                            target=target,
                            profile=profile,
                            environment_root=(
                                workspace_root
                                if profile.environment_scope == "root"
                                else checkout
                            ),
                            targets=targets,
                            invocation=invocation,
                            make=make_config,
                        )
                    )
                )
            )
        )

    def _resolve_context(
        self, checkout: Path
    ) -> p.Result[m.Infra.MakeExecutionContext]:
        return FlextInfraWorkspaceDetector.resolve_workspace_root(checkout).flat_map(
            lambda workspace_root: FlextInfraWorkspaceDetector.load_workspace_spec(
                workspace_root
            ).flat_map(
                lambda workspace: FlextInfraWorkspaceDetector.conform_target(
                    checkout, workspace
                ).flat_map(
                    lambda target: self._context_for_target(
                        checkout, workspace_root, workspace, target
                    )
                )
            )
        )

    def _selected_makefile(self, checkout: Path) -> p.Result[Path]:
        selected = self.makefile.resolve()
        if not selected.is_file():
            return r.fail(f"selected Make owner does not exist: {selected}")
        if selected.parent != checkout:
            return r.fail(
                f"selected Make owner must belong to the invoked checkout: {selected}"
            )
        return r.ok(selected)

    @staticmethod
    def _lock_path(context: m.Infra.MakeExecutionContext) -> p.Result[Path]:
        lock_path = (
            context.workspace_root / context.make.serialization.lock_path
        ).resolve()
        if not lock_path.is_relative_to(context.workspace_root):
            return r.fail(f"Make lock escapes governing root: {lock_path}")
        return r.ok(lock_path)

    def _run_context(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        def operation() -> p.Result[m.Infra.ProcessExit]:
            return self._execute_operation(context)

        def guarded() -> p.Result[m.Infra.ProcessExit]:
            return FlextInfraSerializationLockOwner.execute_guarded_make(
                context, operation, self._process_failure
            )

        if context.invocation.operation.consistency == "none":
            return guarded()
        return self._lock_path(context).flat_map(
            lambda lock_path: FlextInfraSerializationLockOwner.execute(
                (lock_path,),
                context.make.serialization.timeout_seconds,
                guarded,
                timeout_failure=self._lock_timeout_failure,
                acquisition_failure=self._lock_acquisition_failure,
            )
        )

    def _execute_context(
        self, checkout: Path, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        return self._validate_capabilities(context).flat_map(
            lambda _: self._selected_makefile(checkout)
        ).flat_map(lambda _: self._run_context(context))

    @classmethod
    def _lock_timeout_failure(
        cls, lock_path: Path, timeout_seconds: int
    ) -> p.Result[m.Infra.ProcessExit]:
        return cls._process_failure(
            c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
            f"timed out waiting for Make lock {lock_path} after {timeout_seconds}s",
        )

    @classmethod
    def _lock_acquisition_failure(cls, error: str) -> p.Result[m.Infra.ProcessExit]:
        return cls._process_failure(
            int(c.Infra.ScriptExitCode.INFRA), f"Make lock acquisition failed: {error}"
        )

    @override
    def execute(self) -> p.Result[m.Infra.ProcessExit]:
        if self.make_level != 0:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"public Make reentry is forbidden at MAKELEVEL={self.make_level}",
            )
        checkout = self.root.resolve()
        context = self._resolve_context(checkout)
        if context.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(context)
            )
        return self._execute_context(checkout, context.value)


__all__: list[str] = ["FlextInfraMakeSerializationService"]
