"""Lifecycle operation adapters for the typed Make runtime."""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeIs

from flext_core import r
from flext_infra import c, config, m, p, t, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.workspace._make_request import FlextInfraMakeRequestMixin
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.make_generation import FlextInfraMakeGenerationService
from flext_infra.worktree import FlextInfraWorktreeService

type _MakeOperationExecutor = Callable[
    [m.Infra.MakeExecutionContext], p.Result[m.Infra.ProcessExit]
]


class FlextInfraMakeLifecycleMixin(FlextInfraMakeRequestMixin):
    """Route non-quality Make operations to their existing canonical owners."""

    @classmethod
    def _process_failure(
        cls, raw_exit_code: int, message: str
    ) -> p.Result[m.Infra.ProcessExit]:
        outcome = m.Infra.ProcessExit(
            exit_code=u.Infra.normalize_process_exit_code(raw_exit_code),
            raw_exit_code=raw_exit_code,
            classification=u.Infra.classify_process_exit(raw_exit_code),
        )
        return r[m.Infra.ProcessExit].fail(
            message, error_code=c.Infra.PROCESS_EXIT_ERROR_CODE, error_data=outcome
        )

    @staticmethod
    def _success_exit() -> m.Infra.ProcessExit:
        return m.Infra.ProcessExit(
            exit_code=int(c.Infra.ScriptExitCode.PASS),
            raw_exit_code=int(c.Infra.ScriptExitCode.PASS),
            classification="success",
        )

    @classmethod
    def _owner_result[TValue](
        cls, result: p.Result[TValue]
    ) -> p.Result[m.Infra.ProcessExit]:
        """Normalize one canonical owner Result to the Make process contract."""
        if result.failure:
            return cls._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(result)
            )
        return r.ok(cls._success_exit())

    @classmethod
    def _command_result(
        cls, result: p.Result[p.Cli.CommandOutput], context: str
    ) -> p.Result[m.Infra.ProcessExit]:
        if result.failure:
            return cls._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(result)
            )
        output = result.value
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            return cls._process_failure(
                output.exit_code, detail if detail else f"{context} failed"
            )
        return r.ok(cls._success_exit())

    @classmethod
    def _command(
        cls, command: t.StrSequence, *, cwd: Path, context: str
    ) -> p.Result[m.Infra.ProcessExit]:
        return cls._command_result(
            u.Cli.run_raw(command, cwd=cwd, capture=False), context
        )

    @classmethod
    def _commands(
        cls, commands: tuple[t.StrSequence, ...], cwd: Path, context: str
    ) -> p.Result[m.Infra.ProcessExit]:
        return r.traverse(
            commands,
            lambda command: cls._command(command, cwd=cwd, context=context),
        ).map(lambda _: cls._success_exit())

    @staticmethod
    def _is_make_operation_executor(
        value: object,
    ) -> TypeIs[_MakeOperationExecutor]:
        return callable(value)

    def _execute_operation(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        method_name = "_execute_" + context.invocation.operation.name.replace(
            ".", "_"
        ).replace("-", "_")
        executor: object = getattr(self, method_name, None)
        if not self._is_make_operation_executor(executor):
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                "Make operation has no implementation owner: "
                f"{context.invocation.operation.name}",
            )
        return executor(context)

    def _execute_lifecycle_help(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        lines = ["Canonical Make interface:\n"]
        for verb in context.make.verbs:
            handlers = ", ".join(item.what for item in verb.handlers)
            apply = (
                f" {context.make.apply_variable}={context.make.apply_value}"
                if verb.apply_guarded
                else ""
            )
            lines.append(
                f"  make {verb.name} {context.make.selector}=<[{handlers}]>{apply}\n"
            )
        u.Cli.emit_raw("".join(lines))
        return r.ok(self._success_exit())

    def _reconcile_setup_gitlinks(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        if context.invocation.target_scope != "profile":
            return r.ok(self._success_exit())
        gitlinks = tuple(
            m.Infra.ManagedGitlinkSpec(
                repository=repository, branch=repository.branch
            )
            for repository in context.workspace.members
            if not repository.read_only
            and repository.state == c.Infra.RepositoryState.ACTIVE
        )
        reconciled = u.Infra.git_reconcile_managed_submodules(
            context.workspace_root, gitlinks
        )
        if reconciled.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(reconciled)
            )
        return r.ok(self._success_exit())

    @staticmethod
    def _setup_commands(
        context: m.Infra.MakeExecutionContext, environment: Path
    ) -> tuple[t.StrSequence, ...]:
        all_packages = (
            ("--all-packages",)
            if context.profile.setup_scope == "root-and-members"
            and context.invocation.target_scope == "profile"
            else ()
        )
        return (
            (c.Infra.UV, "venv", "--clear", str(environment)),
            (
                c.Infra.UV,
                "sync",
                "--project",
                str(context.environment_root),
                *all_packages,
                "--all-extras",
                "--all-groups",
                "--link-mode",
                config.Infra.codegen.toolchain.uv_link_mode,
            ),
            (c.Infra.UV, "pip", "check", "--python", str(environment)),
        )

    def _execute_environment_setup(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        environment = (
            context.environment_root
            / config.Infra.tooling.tools.pyright.path_rules.venv_name
        )
        return self._reconcile_setup_gitlinks(context).flat_map(
            lambda _: self._commands(
                self._setup_commands(context, environment),
                context.environment_root,
                "make setup",
            )
        ).flat_map(
            lambda _: self._owner_result(
                FlextInfraWorkspaceEnvironmentProvenance.validate(
                    context.environment_root
                )
            )
        )

    def _execute_dependencies_manage(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        dependency = next(
            iter(self._input_values(context.invocation, "dependency")), ""
        )
        action = context.invocation.handler.what
        if action == "upgrade":
            modernized = FlextInfraPyprojectModernizer(
                workspace_root=context.workspace_root,
                selected_projects=tuple(
                    item.repository.distribution for item in context.targets
                ),
                apply_changes=True,
                rewrite_constraints=True,
            ).execute()
            if modernized.failure:
                return self._process_failure(
                    int(c.Infra.ScriptExitCode.INFRA), r.require_error(modernized)
                )
        arguments = [
            c.Infra.UV,
            "lock",
            "--project",
            str(context.environment_root),
        ]
        if action == "check":
            arguments.append("--check")
        elif action == "upgrade":
            arguments.extend(
                ("--upgrade-package", dependency) if dependency else ("--upgrade",)
            )
        return self._command(
            arguments, cwd=context.environment_root, context="dependency lock"
        )

    def _execute_package_build(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        return r.traverse(
            context.targets,
            lambda selected: self._command(
                (c.Infra.UV, "build", "--project", str(selected.root)),
                cwd=selected.root,
                context="package build",
            ),
        ).map(lambda _: self._success_exit())

    def _execute_application_run(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        selected = context.targets[0]
        entrypoint = u.Infra.project_console_script(
            selected.root, selected.repository.distribution
        )
        if entrypoint.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(entrypoint)
            )
        executable = shutil.which(
            entrypoint.value, path=str(Path(sys.executable).absolute().parent)
        )
        if executable is None:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"managed console entrypoint is not installed: {entrypoint.value}",
            )
        return self._command(
            (executable, *self._input_values(context.invocation, "args")),
            cwd=selected.root,
            context=f"application run {entrypoint.value}",
        )

    @staticmethod
    def _emit_git_status(root: Path) -> p.Result[bool]:
        status = u.Infra.git_capture(root, ("status", "--short"))
        if status.failure:
            return r.fail(r.require_error(status))
        if status.value:
            u.Cli.emit_raw(status.value + "\n")
        return r.ok(True)

    def _execute_environment_status(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        u.Cli.emit_raw(
            f"profile={context.profile.name}\nproject={context.target.root}\n"
            f"runtime={context.environment_root}\n"
        )
        return self._owner_result(
            FlextInfraWorkspaceEnvironmentProvenance.validate(
                context.environment_root
            )
        ).flat_map(
            lambda _: self._command(
                (
                    c.Infra.UV,
                    "lock",
                    "--project",
                    str(context.environment_root),
                    "--check",
                ),
                cwd=context.environment_root,
                context="environment lock status",
            )
        ).flat_map(
            lambda _: r.traverse(
                context.targets,
                lambda selected: self._emit_git_status(selected.root),
            ).map(lambda _: self._success_exit())
        )

    @staticmethod
    def _documentation_actions(
        context: m.Infra.MakeExecutionContext,
    ) -> tuple[str, ...]:
        if context.invocation.handler.what != "all":
            return (context.invocation.handler.what,)
        return tuple(
            handler.what
            for handler in context.invocation.verb.handlers
            if handler.what != "all"
        )

    @classmethod
    def _execute_documentation_action(
        cls, context: m.Infra.MakeExecutionContext, action: str
    ) -> p.Result[m.Infra.ProcessExit]:
        from flext_infra.services.cli_routes import CliRouteService

        routes = CliRouteService.group_commands[c.Infra.CLI_GROUP_DOCS]
        route = next((item for item in routes if item.name == action), None)
        if route is None:
            return cls._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"documentation handler has no canonical route: {action}",
            )
        params = u.Cli.derive_model(
            route.model_cls,
            {
                "workspace_root": str(context.workspace_root),
                "selected_projects": [
                    item.repository.distribution for item in context.targets
                ],
                "output_dir": str(context.make.docs.reports_dir),
                "apply_changes": context.invocation.applying,
            },
        )
        executed = route.handler(params)
        return cls._owner_result(executed)

    def _execute_documentation_manage(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        return r.traverse(
            self._documentation_actions(context),
            lambda action: self._execute_documentation_action(context, action),
        ).map(lambda _: self._success_exit())
    @staticmethod
    def _artifact_paths(
        root: Path, artifact: m.Infra.CodegenArtifactSpec
    ) -> tuple[Path, ...]:
        return (
            tuple(root.rglob(artifact.name))
            if artifact.cleanup == "recursive"
            else (root / artifact.name,)
        )

    @staticmethod
    def _clean_artifact_path(path: Path, *, is_dir: bool) -> p.Result[bool]:
        if not path.exists():
            return r.ok(True)
        try:
            shutil.rmtree(path) if is_dir else path.unlink()
        except OSError as exc:
            return r.fail(f"failed to clean {path}: {exc}")
        return r.ok(True)

    @classmethod
    def _clean_target(
        cls, root: Path, artifacts: tuple[m.Infra.CodegenArtifactSpec, ...]
    ) -> p.Result[bool]:
        return r.traverse(
            artifacts,
            lambda artifact: r.traverse(
                cls._artifact_paths(root, artifact),
                lambda path: cls._clean_artifact_path(
                    path, is_dir=artifact.is_dir
                ),
            ),
        ).map(lambda _: True)

    def _execute_artifacts_clean(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        artifacts = tuple(
            item for item in config.Infra.codegen.artifacts if item.cleanup != "preserve"
        )
        return self._owner_result(
            r.traverse(
                context.targets,
                lambda selected: self._clean_target(selected.root, artifacts),
            )
        )

    @classmethod
    def _validate_release_target(cls, root: Path) -> p.Result[m.Infra.ProcessExit]:
        status = u.Infra.git_capture(root, ("status", "--porcelain"))
        if status.failure:
            return cls._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(status)
            )
        if status.value.strip():
            return cls._process_failure(
                int(c.Infra.ScriptExitCode.FAIL),
                f"release requires a clean checkout: {root}",
            )
        return r.ok(cls._success_exit())

    def _execute_release_status(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        return self._command(
            (c.Infra.UV, "lock", "--project", str(context.environment_root), "--check"),
            cwd=context.environment_root,
            context="release lock status",
        ).flat_map(
            lambda _: r.traverse(
                context.targets,
                lambda selected: self._validate_release_target(selected.root),
            ).map(lambda _: self._success_exit())
        )

    def _execute_conformance_project(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        root = context.target.root.resolve()
        conformed = FlextInfraCodegenConform(
            workspace_root=root,
            request=m.Infra.CodegenConformRequest(
                root=root,
                what=c.Infra.CodegenConformSurface.ALL,
                scope=context.target.conform_scope,
            ),
            initial_execution_context=context,
            projection_operation="conform",
        ).execute()
        return self._owner_result(conformed)

    def _execute_generation_project(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        generated = FlextInfraMakeGenerationService.execute_for(
            context, applying=context.invocation.applying
        )
        return self._owner_result(generated)

    def _execute_worktree_manage(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        executed = FlextInfraWorktreeService(
            workspace_root=Path(
                next(
                    iter(self._input_values(context.invocation, "workspace")),
                    str(context.target.root),
                )
            ),
            operation=c.Infra.WorktreeOperation(context.invocation.handler.what),
            branch=next(
                iter(self._input_values(context.invocation, "branch")), None
            ),
            base=next(iter(self._input_values(context.invocation, "base")), None),
            apply_changes=context.invocation.applying,
        ).execute()
        if executed.failure:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), r.require_error(executed)
            )
        if executed.value:
            u.Cli.emit_raw(executed.value + "\n")
        return r.ok(self._success_exit())

    def _execute_script_dispatch(
        self, context: m.Infra.MakeExecutionContext
    ) -> p.Result[m.Infra.ProcessExit]:
        selected = context.targets[0]
        dispatch = selected.repository.script_dispatch
        if dispatch is None:
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA), "script dispatcher is not configured"
            )
        dispatcher = (selected.root / dispatch.dispatcher).resolve()
        if not dispatcher.is_relative_to(selected.root) or not dispatcher.is_file():
            return self._process_failure(
                int(c.Infra.ScriptExitCode.INFRA),
                f"script dispatcher does not exist: {dispatcher}",
            )
        command = (
            sys.executable,
            str(dispatcher),
            context.invocation.verb.name,
            context.invocation.handler.what,
            *self._input_values(context.invocation, "args"),
        )
        apply_value = (
            context.make.apply_value
            if context.invocation.applying
            else context.make.apply_absent_value
        )
        return self._command_result(
            u.Cli.run_raw(
                command,
                cwd=selected.root,
                capture=False,
                env=u.Cli.process_env(
                    overrides={context.make.apply_variable: apply_value}
                ),
            ),
            "script dispatch "
            f"{context.invocation.verb.name}:{context.invocation.handler.what}",
        )


__all__: list[str] = ["FlextInfraMakeLifecycleMixin"]
