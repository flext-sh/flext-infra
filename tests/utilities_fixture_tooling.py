"""Tooling and executable-environment fixture test utilities for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from functools import cache
from pathlib import Path
from textwrap import indent

from typing_extensions import TypeForm

from flext_infra import config, u, validate, workspace
from tests import c, m, p, r, t, tm
from tests.utilities_git import TestsFlextInfraUtilitiesGitMixin


class TestsFlextInfraUtilitiesToolingFixtureMixin:
    """Executable, Make, and toolchain-environment fixture helpers."""

    class PytestRunner:
        """Own the public runner fixtures shared by runtime validation tests."""

        @staticmethod
        def runner_for(
            cached_runner_project: Path,
            *,
            ci_context: bool = False,
            profile_collection: bool = False,
            slow_phase: bool = False,
            target_file: Path | None = None,
        ) -> validate.FlextInfraPytestRunner:
            """Bind a runner to its config-owned persistent cache and reports.

            Returns:
                The runner bound to the fixture's own cache and reports.

            """
            cache = config.Infra.codegen.make.testmon_cache
            testmon_db = (
                cached_runner_project.parent
                / ".testmon-cache"
                / cached_runner_project.name
                / cache.database_filename
            )
            testmon_db.parent.mkdir(parents=True, exist_ok=True)
            return validate.FlextInfraPytestRunner(
                repository_root=cached_runner_project,
                ci_context=ci_context,
                collection_command_prefix=(
                    (sys.executable, "-c", c.Infra.PYTEST_PROFILE_LAUNCHER)
                    if profile_collection
                    else ()
                ),
                started_at_monotonic=time.monotonic(),
                target=cache.target_directory,
                target_file=target_file,
                reports=cache.reports_directory,
                testmon_db=testmon_db,
                slow_phase=slow_phase,
            )

        @staticmethod
        def declared_project_runner(
            project_root: Path,
            name: str,
        ) -> validate.FlextInfraPytestRunner:
            """Declare the fixture identity before constructing its runner.

            Returns:
                The runner consuming the declared project identity.

            """
            pyproject = project_root / c.PYPROJECT_FILENAME
            pyproject.write_text(
                pyproject.read_text(encoding=c.DEFAULT_ENCODING)
                + f'\n[project]\nname = "{name}"\nversion = "0.1.0"\n',
                encoding=c.DEFAULT_ENCODING,
            )
            return TestsFlextInfraUtilitiesToolingFixtureMixin.PytestRunner.runner_for(
                project_root,
            )

        @staticmethod
        def declare_parallel_project(project_root: Path) -> None:
            """Select the fixture identity from the configured worker policy."""
            policy = config.Infra.tooling.tools.pytest
            parallel_project = next(
                name
                for name, ceiling in policy.parallel_worker_overrides.items()
                if (isinstance(ceiling, int) and ceiling > 1)
                or (
                    not isinstance(ceiling, int)
                    and ceiling.workers is not None
                    and ceiling.workers > 1
                )
            )
            pyproject = project_root / c.PYPROJECT_FILENAME
            pyproject.write_text(
                f'[project]\nname = "{parallel_project}"\nversion = "0.0.0"\n'
                + pyproject.read_text(encoding=c.DEFAULT_ENCODING),
                encoding=c.DEFAULT_ENCODING,
            )
            runner = (
                TestsFlextInfraUtilitiesToolingFixtureMixin.PytestRunner.runner_for(
                    project_root,
                )
            )
            tm.that(runner.parallel_worker_budget(policy) > 1, truth=True)

        @staticmethod
        def profile_parent(
            runner: p.Tests.PytestProfileContext,
            output: Path,
            *,
            target_file: Path | None = None,
        ) -> int:
            """Exercise the real profiling entry with the Make-owned inputs.

            Returns:
                The native profiling entry's successful return code.

            Raises:
                RuntimeError: If the profiling entry fails.

            """
            output.parent.mkdir(parents=True, exist_ok=True)
            policy = config.Infra.tooling.tools.pytest
            cache = config.Infra.codegen.make.testmon_cache
            log = output.with_suffix(".log")
            outcome = tm.ok(
                u.Cli.run_to_file(
                    (
                        sys.executable,
                        "-m",
                        "flext_infra._pytest_entry",
                        "profile",
                        str(output),
                    ),
                    log,
                    cwd=runner.repository_root,
                    options=m.Cli.ProcessOptions(
                        env=u.Cli.process_env(
                            overrides={
                                c.Infra.PYTEST_ENV_REPOSITORY_ROOT: str(
                                    runner.repository_root
                                ),
                                c.Infra.PYTEST_ENV_TARGET: str(runner.target),
                                c.Infra.PYTEST_ENV_TARGET_FILE: str(
                                    target_file
                                    if target_file is not None
                                    else runner.target_file or "",
                                ),
                                c.Infra.PYTEST_ENV_REPORTS: str(runner.reports),
                                cache.database_environment_variable: str(
                                    runner.testmon_db,
                                ),
                            },
                        ),
                        deadline=m.Cli.ProcessDeadline(
                            expires_at_monotonic=(
                                runner.started_at_monotonic + policy.run_timeout_seconds
                            ),
                            termination_grace_seconds=policy.termination_grace_seconds,
                        ),
                    ),
                ),
            )
            if not u.Cli.process_succeeded(outcome):
                raise RuntimeError(log.read_text(encoding=c.DEFAULT_ENCODING))
            return outcome.raw_return_code

        @staticmethod
        def profile_collection(
            output: Path,
            arguments: t.StrTuple,
        ) -> p.Cli.CommandOutput:
            """Use the real child launcher from the configured profiling runner.

            Returns:
                The native launcher command output.

            """
            return tm.ok(
                u.Cli.run_raw(
                    (
                        sys.executable,
                        "-c",
                        c.Infra.PYTEST_PROFILE_LAUNCHER,
                        str(output),
                        *arguments,
                    ),
                    cwd=output.parent,
                    timeout=config.Infra.tooling.tools.pytest.run_timeout_seconds,
                ),
            )

        @staticmethod
        def summary(reports_root: Path) -> str:
            """Read the latest native report summary through the files facade.

            Returns:
                The contents of the latest published summary.

            """
            latest_name = tm.ok(
                u.Cli.files_read_text(reports_root / "latest.txt"),
            ).strip()
            return tm.ok(
                u.Cli.files_read_text(reports_root / latest_name / "summary.txt"),
            )

    @staticmethod
    def mypy_deadline_limit() -> m.Infra.MypyResourceLimit:
        """Reserve harness startup and cleanup inside the configured slow budget.

        Returns:
            The resulting ``m.Infra.MypyResourceLimit``.

        """
        policy = config.Infra.tooling.tools.pytest
        available = (
            policy.slow_timeout_seconds
            - c.Infra.MYPY_TIMEOUT_GRACE_SECONDS
            - policy.termination_grace_seconds
        )
        return m.Infra.MypyResourceLimit(
            memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
            timeout_seconds=min(
                config.Infra.tooling.tools.mypy.timeout_seconds,
                available // 2,
            ),
        )

    @staticmethod
    def reap_mypy_descendant(pid_file: Path, timeout: int) -> None:
        """Reap a registered workload in pytest teardown, preserving call failures.

        Raises:
            RuntimeError: If ``snapshot.outcome.raw_return_code not in {0, 1} or
                snapshot.stderr``.

        """
        pid = pid_file.read_text(encoding=c.DEFAULT_ENCODING)
        snapshot = u.Cli.run_raw(
            ("/bin/ps", "-p", str(int(pid)), "-o", "stat="),
            timeout=timeout,
        ).unwrap()
        if snapshot.outcome.raw_return_code not in {0, 1} or snapshot.stderr:
            raise RuntimeError(snapshot.stderr)
        state = snapshot.stdout.strip()
        if state and not state.startswith("Z"):
            u.Cli.run(("/bin/kill", "-KILL", pid), timeout=timeout).unwrap()

    @staticmethod
    def mypy_workload(root: Path, plugin_body: str = "") -> m.Infra.MypyInvocation:
        """Create a real checker project with an optional workload plugin.

        Returns:
            The resulting ``m.Infra.MypyInvocation``.

        """
        source = root / "checked.py"
        source.write_text("value: int = 1\n", encoding=c.DEFAULT_ENCODING)
        config_file = root / c.PYPROJECT_FILENAME
        # The workload checks through the governed checker settings, so its
        # crash reporting (show_traceback) matches every managed project.
        # Each workload owns its cache inside its root: mypy's default
        # .mypy_cache is relative to the process cwd, which concurrent workers
        # share, and its SQLite metastore then fails with "database is locked".
        tooling = u.Infra.load_tooling_inputs(root).unwrap().document
        options = u.Infra.native_tool_configuration(tooling, "mypy")
        options["cache_dir"] = str(root / ".mypy_cache")
        options["python_version"] = config.Infra.codegen.toolchain.python_version
        if plugin_body:
            plugin = root / "workload.py"
            plugin.write_text(
                "from mypy.plugin import Plugin\n\n"
                "def plugin(version: str) -> type[Plugin]:\n"
                + indent(plugin_body, "    ")
                + "\n    return Plugin\n",
                encoding=c.DEFAULT_ENCODING,
            )
            options["plugins"] = [
                *u.Infra.native_tool_setting(
                    tooling, "mypy", "plugins", TypeForm(t.StrSequence)
                ),
                str(plugin),
            ]
        config_file.write_text(
            u.Cli.toml_dumps(
                u.Cli.toml_document_from_mapping({"tool": {"mypy": options}})
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        return m.Infra.MypyInvocation(targets=(source,), config_file=config_file)

    @staticmethod
    def managed_uv() -> str:
        """Resolve the checkout's Mise-managed UV executable, never a PATH shim.

        A fixture runs UV with its working directory inside disposable scratch,
        outside every Mise manifest. A shim resolved there has no declared
        version (CI installs tools only for this checkout), so the executable
        is resolved once through the toolchain owner against this checkout.

        Returns:
            The absolute UV executable the committed toolchain pins.

        """
        checkout = Path(__file__).resolve().parents[1]
        return str(tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, checkout)))

    @staticmethod
    def python_dependency_projects(root: Path) -> t.VariadicTuple[Path]:
        """Resolve declared fixture dependencies to actual workspace source owners.

        Only dependencies that are declared workspace members are resolved;
        external (PyPI) dependencies are skipped because they have no local
        source owner. A dependency that looks like a workspace member (its
        name is in the workspace spec) but is missing from the filesystem
        is a configuration error and is not silently skipped.

        Returns:
            The declared projects and their local runtime dependency closure.

        Raises:
            ValueError: When a ``flext-`` dependency has no workspace source owner.

        """
        checkout = Path(__file__).resolve().parents[1]
        context = tm.ok(
            workspace.FlextInfraWorkspaceDetector.resolution_context(checkout)
        )
        specification = tm.ok(
            workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
                context.runtime_root
            ),
        )
        projects = {
            repository.distribution: context.runtime_root / repository.path
            for repository in (specification.repository, *specification.subprojects)
        }
        metadata = tm.ok(u.Infra.read_project_metadata_result(root))
        selected: t.MutableMappingKV[str, Path] = {}
        pending = list(metadata.project.dependencies)
        while pending:
            requirement = pending.pop()
            name = u.Infra.dep_name(requirement)
            if name in selected or name is None:
                continue
            if name not in projects:
                if name.startswith("flext-"):
                    msg = (
                        f"Fixture dependency has no workspace source owner: "
                        f"{requirement}"
                    )
                    raise ValueError(msg)
                continue
            project = projects[name]
            selected[name] = project
            dependency = tm.ok(u.Infra.read_project_metadata_result(project))
            pending.extend(
                value
                for value in dependency.project.dependencies
                if u.Infra.dep_name(value) in projects
            )
        return tuple(selected.values())

    @staticmethod
    @cache
    def python_dependency_wheels(
        directory: Path,
        dependency_projects: t.VariadicTuple[Path],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Build current dependency sources once in the shared worker allocation.

        UV reuses its native artifact cache; no installed executor package or
        environment is copied into a fixture. The session owner removes the wheels.

        Returns:
            Real wheels, or the original build failure without retrying it.

        """
        fixture = TestsFlextInfraUtilitiesToolingFixtureMixin
        binary = fixture.managed_uv()
        wheels: list[Path] = []
        with u.Infra.codegen_transaction_lease(directory / "dependency-wheels.lock"):
            for project in dependency_projects:
                metadata = tm.ok(u.Infra.read_project_metadata_result(project))
                destination = directory / "dependency-wheels" / metadata.project.name
                destination.mkdir(parents=True, exist_ok=True)
                built = u.Cli.run_checked(
                    (
                        binary,
                        "build",
                        "--wheel",
                        "--python",
                        sys.executable,
                        "--out-dir",
                        str(destination),
                        str(project),
                    ),
                    cwd=project,
                )
                if built.failure:
                    return r[t.VariadicTuple[Path]].from_failure(built)
                artifacts = tuple(destination.glob("*.whl"))
                if len(artifacts) != 1:
                    return r[t.VariadicTuple[Path]].fail(
                        f"Dependency build must publish one wheel: {destination}",
                    )
                wheels.extend(artifacts)
        return r[t.VariadicTuple[Path]].ok(tuple(wheels))

    @staticmethod
    def create_python_environment(
        root: Path,
        *,
        dependency_projects: t.SequenceOf[Path] = (),
        session_runtime: p.Tests.SessionRuntime | None = None,
    ) -> p.Result[bool]:
        """Provision a physical fixture venv with session-built real dependencies.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        binary = u.Infra.managed_mise_binary(c.Infra.UV, Path.cwd())
        if binary.failure:
            return r[bool].from_failure(binary)
        environment = u.Infra.runtime_environment_dir(root)
        environment.parent.mkdir(parents=True, exist_ok=True)
        TestsFlextInfraUtilitiesToolingFixtureMixin.managed_uv()
        created = u.Cli.run_checked(
            [str(binary.value), "venv", "--python", sys.executable, str(environment)],
            cwd=root,
        )
        if created.failure or not dependency_projects:
            return created
        if session_runtime is None:
            return r[bool].fail("Fixture dependency builds require a session runtime")
        wheels = TestsFlextInfraUtilitiesToolingFixtureMixin.python_dependency_wheels(
            session_runtime.directory,
            tuple(dependency_projects),
        )
        if wheels.failure:
            return r[bool].from_failure(wheels)
        override_option, override_filename = c.Infra.BINDING_RESOLUTION_FILES[0]
        overrides = environment / override_filename
        bound = u.Cli.files_write_text(
            overrides,
            "".join(
                f"{tm.ok(u.Infra.read_project_metadata_result(project)).project.name}"
                f" @ {wheel.resolve().as_uri()}\n"
                for project, wheel in zip(
                    dependency_projects, wheels.value, strict=True
                )
            ),
        )
        if bound.failure:
            return r[bool].from_failure(bound)
        return u.Cli.run_checked(
            (
                str(binary.value),
                "pip",
                "install",
                "--python",
                str(environment),
                override_option,
                str(overrides),
                *(str(wheel) for wheel in wheels.value),
            ),
            cwd=root,
        )

    @classmethod
    def provision_python_project_environment(cls, root: Path) -> p.Result[bool]:
        """Provision a fixture interpreter and its real editable project.

        Returns:
            The installation result or the original environment failure.

        """
        created = cls.create_python_environment(root)
        if created.failure:
            return r[bool].from_failure(created)
        binary = u.Infra.managed_mise_binary(c.Infra.UV, Path.cwd())
        if binary.failure:
            return r[bool].from_failure(binary)
        return u.Cli.run_checked(
            (
                str(binary.value),
                "pip",
                "install",
                "--no-deps",
                "--python",
                str(u.Infra.runtime_environment_dir(root)),
                "--editable",
                str(root),
            ),
            cwd=root,
        )

    @staticmethod
    def provision_checkout(root: Path) -> None:
        """Make a fixture root a checkout whose environment owns the edit tools.

        Protected edits resolve every ``c.Infra.LINT_TOOLS`` executable plus
        python and pytest fail-closed from the checkout's runtime environment
        (``u.Infra.runtime_environment_dir``), which requires a Git checkout.
        The fixture becomes one through the single fixture Git owner and
        receives the real binaries this suite was provisioned with, linked
        inside the pytest-managed tree; a missing tool fails the fixture.

        Raises:
            FileExistsError: If fixture tool conflicts with provisioned executable; or
                if fixture tool path is already occupied.
            FileNotFoundError: If setup did not provision.

        """
        # Provisioning a runtime never rewrites a checkout's declared identity:
        # an existing checkout keeps its origin, only a bare root becomes one.
        if not (root / c.Infra.GIT_DIR).exists():
            TestsFlextInfraUtilitiesGitMixin.initialize_git_repo(root)
        provisioned = Path(sys.executable).parent
        bin_dir = u.Infra.runtime_environment_dir(root) / provisioned.name
        bin_dir.mkdir(parents=True, exist_ok=True)
        tools = {command[0] for _, command in c.Infra.LINT_TOOLS}
        for name in sorted(tools | {c.Infra.PYTHON, c.Infra.PYTEST}):
            source = provisioned / name
            if not source.is_file():
                msg = f"setup did not provision {name}: {source}"
                raise FileNotFoundError(msg)
            destination = bin_dir / name
            if destination.is_symlink():
                if destination.resolve(strict=True) == source.resolve(strict=True):
                    continue
                msg = (
                    f"fixture tool conflicts with provisioned executable: {destination}"
                )
                raise FileExistsError(msg)
            if destination.exists():
                msg = f"fixture tool path is already occupied: {destination}"
                raise FileExistsError(msg)
            destination.symlink_to(source)

    @staticmethod
    def make_read_only(path: Path) -> None:
        """Make one fixture path read-only."""
        path.chmod(0o444)

    @staticmethod
    def runtime_evaluated_roots() -> t.StrTuple:
        """Return the configured runtime-evaluated roots, first-seen order."""
        return tuple(
            dict.fromkeys(
                config.Infra.tooling.tools.ruff.lint.flake8_type_checking.runtime_evaluated_roots,
            ),
        )

    @staticmethod
    def runtime_root_import() -> str:
        """Return an import binding the first configured root as ``RuntimeRoot``."""
        module, _, name = (
            TestsFlextInfraUtilitiesToolingFixtureMixin.runtime_evaluated_roots()[
                0
            ].rpartition(".")
        )
        return f"from {module} import {name} as RuntimeRoot\n"

    @staticmethod
    def copy_tracked_mise_seeds(root: Path, *, source_root: Path | None = None) -> None:
        """Copy declared Mise inputs from this checkout or a native upgrade seed.

        A governed repository carries the declaration and the dependency lock
        together. Native dependency graphs referenced by the lock must travel
        with it so frozen setup never resolves replacements. Conform renders
        declarations; only ``make upg`` resolves new versions.
        """
        source_root = (
            Path(__file__).resolve().parents[1] if source_root is None else source_root
        )
        for relative in (
            c.Infra.MISE_TOML_FILENAME,
            c.Infra.MISE_LOCK_FILENAME,
        ):
            source = source_root / relative
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            _ = shutil.copy2(source, destination)

    @staticmethod
    def write_executable(path: Path, body: str) -> None:
        """Write one executable fixture with deterministic permissions."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding=c.DEFAULT_ENCODING)
        path.chmod(0o755)

    @staticmethod
    def declare_codemod_rules(root: Path, rules: t.StrMapping) -> None:
        """Point ``root`` at a local ast-grep catalog holding exactly ``rules``.

        Each key names one rule file and each value is its YAML body.
        """
        config_path = root / c.Infra.CODEMOD_CONFIG_RELPATH
        rules_root = config_path.parent / c.Cli.RULES_DIR_NAME
        tm.ok(u.Cli.ensure_dir(rules_root))
        tm.ok(
            u.Cli.atomic_write_text_file(
                config_path,
                f"{c.Infra.CODEMOD_SCOPE_KEY}: {c.Infra.CODEMOD_SCOPE_UNIVERSAL}\n"
                f"ruleDirs:\n  - {c.Cli.RULES_DIR_NAME}\ntestConfigs: []\n",
            ),
        )
        for name, body in rules.items():
            tm.ok(u.Cli.atomic_write_text_file(rules_root / f"{name}.yml", body))

    @staticmethod
    def run_isolated_make(
        args: t.StrSequence,
        *,
        cwd: Path,
        env: t.StrMapping | None = None,
        private_env: t.MappingKV[str, t.SecretStr] | None = None,
        capture: bool = True,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run Make without undeclared state inherited from outer pytest.

        The network bootstrap asks gh for a token when no GITHUB_TOKEN is set.
        gh here reads no configuration (``os.devnull`` is not a directory) and
        reaches no keyring (the session bus is disabled), so the host
        operator's stored credential never enters a test implicitly. Provisioning
        may explicitly supply the credential already elected by its root Make;
        private values are unwrapped only at the child-process boundary.

        Returns:
            The resulting ``p.Result[p.Cli.CommandOutput]``.

        """
        return u.Cli.run_raw(
            [c.Infra.MAKE, *args],
            cwd=cwd,
            options=m.Cli.ProcessOptions(
                env={
                    "GH_CONFIG_DIR": os.devnull,
                    "DBUS_SESSION_BUS_ADDRESS": "disabled:",
                    **(env or {}),
                    **{
                        key: value.get_secret_value()
                        for key, value in (private_env or {}).items()
                    },
                },
                remove_env_keys=tuple(
                    key
                    for key in c.Tests.MAKE_ISOLATION_ENV_KEYS
                    if (env is None or key not in env)
                    and (private_env is None or key not in private_env)
                ),
            ),
            capture=capture,
        )

    @staticmethod
    def is_docker_available() -> bool:
        """Return whether Docker is available to integration tests.

        Returns:
            Whether Docker is available to integration tests.

        """
        return shutil.which("docker") is not None

    @staticmethod
    def cli_shim(bin_dir: Path, name: str) -> Path:
        """Provide an executable that records arguments without reaching a service.

        ``gh`` and ``uv publish`` talk to GitHub and to a package index; a
        unit test proves the protocol's command contract against a recorded
        invocation, never against the real remote.

        Returns:
            The resulting ``Path``.

        """
        bin_dir.mkdir(parents=True, exist_ok=True)
        log = bin_dir / f"{name}.log"
        shim = bin_dir / name
        # A ``view`` of a release or pull request answers "absent" (exit 1),
        # the state every first publication starts from.
        shim.write_text(
            "#!/bin/sh\n"
            f'printf "%s\\n" "$*" >> "{log}"\n'
            'case "$2" in view) exit 1 ;; esac\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
        return log


__all__: list[str] = ["TestsFlextInfraUtilitiesToolingFixtureMixin"]
