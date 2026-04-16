"""Test utilities for flext-infra."""

from __future__ import annotations

import re
import shutil
import subprocess
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

import pytest
from flext_tests import FlextTestsUtilities

from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenLazyInit,
    FlextInfraDependencyDetectionService,
    FlextInfraGate,
    FlextInfraProjectMigrator,
    FlextInfraRefactorMROImportRewriter,
    FlextInfraRuntimeDevDependencyDetector,
    FlextInfraWorkspaceChecker,
    u,
)
from tests import c, m, p, r, t


class TestsFlextInfraUtilities(FlextTestsUtilities, u):
    """Typed test utilities for flext-infra."""

    class Infra(u.Infra):
        """Infra-specific utilities namespace."""

        class Tests(FlextTestsUtilities.Tests):
            """Canonical test helper namespace."""

            class DeptrySelector(u.Infra):
                """Protocol-compatible selector backed by a real Result."""

                _result: ClassVar[p.Result[Sequence[m.Infra.ProjectInfo]] | None] = None

                def __init__(
                    self,
                    result: p.Result[Sequence[m.Infra.ProjectInfo]],
                ) -> None:
                    type(self)._result = result

                @staticmethod
                @override
                def resolve_projects(
                    workspace_root: Path,
                    names: t.StrSequence,
                ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
                    del workspace_root, names
                    result = TestsFlextInfraUtilities.Infra.Tests.DeptrySelector._result
                    if result is None:
                        return r[Sequence[m.Infra.ProjectInfo]].fail(
                            "selector result not configured",
                        )
                    return result

            class DeptryRunner(p.Cli.CommandRunner):
                """Protocol-compatible runner backed by a real Result."""

                def __init__(
                    self,
                    result: p.Result[m.Cli.CommandOutput],
                ) -> None:
                    self._result = result

                @override
                def run_raw(
                    self,
                    cmd: t.StrSequence,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                    input_data: bytes | None = None,
                ) -> p.Result[m.Cli.CommandOutput]:
                    del cmd, cwd, timeout, env, input_data
                    return self._result

                @override
                def run(
                    self,
                    cmd: t.StrSequence,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                ) -> p.Result[m.Cli.CommandOutput]:
                    del cmd, cwd, timeout, env
                    if self._result.failure:
                        return self._result
                    output = self._result.value
                    if output.exit_code != 0:
                        return r[m.Cli.CommandOutput].fail(
                            output.stderr or output.stdout or "Command failed",
                        )
                    return self._result

                @override
                def capture(
                    self,
                    cmd: t.StrSequence,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                ) -> p.Result[str]:
                    result = self.run(cmd, cwd=cwd, timeout=timeout, env=env)
                    if result.failure:
                        return r[str].fail(result.error or "Command failed")
                    return r[str].ok(result.unwrap().stdout.strip())

                @override
                def run_checked(
                    self,
                    cmd: t.StrSequence,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                ) -> p.Result[bool]:
                    result = self.run(cmd, cwd=cwd, timeout=timeout, env=env)
                    if result.failure:
                        return r[bool].fail(result.error or "Command failed")
                    return r[bool].ok(True)

                @override
                def run_to_file(
                    self,
                    cmd: t.StrSequence,
                    output_file: t.Cli.PathLike,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                ) -> p.Result[int]:
                    result = self.run_raw(cmd, cwd=cwd, timeout=timeout, env=env)
                    if result.failure:
                        return r[int].fail(result.error or "Command failed")
                    output_path = (
                        output_file
                        if isinstance(output_file, Path)
                        else Path(output_file)
                    )
                    output_path.write_text(
                        f"{result.value.stdout}{result.value.stderr}",
                        encoding="utf-8",
                    )
                    return r[int].ok(result.value.exit_code)

            class TomlReaderSequence(p.Infra.TomlReader):
                """Protocol-compatible TOML reader that replays typed results."""

                def __init__(
                    self,
                    values: Sequence[p.Result[t.Infra.ContainerDict]],
                ) -> None:
                    self._values = list(values)
                    self._index = 0

                @override
                def read_plain(self, path: Path) -> p.Result[t.Infra.ContainerDict]:
                    del path
                    current = self._index
                    self._index = current + 1
                    if not self._values:
                        return r[t.Infra.ContainerDict].fail(
                            "toml reader sequence is empty",
                        )
                    return (
                        self._values[current]
                        if current < len(self._values)
                        else self._values[-1]
                    )

            class SequenceRunner(DeptryRunner):
                """Protocol-compatible runner that replays command results in order."""

                def __init__(
                    self,
                    results: Sequence[p.Result[m.Cli.CommandOutput]],
                ) -> None:
                    self._results = list(results)
                    self._index = 0
                    self.commands: MutableSequence[tuple[str, ...]] = []

                def _next_result(self) -> p.Result[m.Cli.CommandOutput]:
                    current = self._index
                    self._index = current + 1
                    if not self._results:
                        return r[m.Cli.CommandOutput].fail(
                            "runner result sequence is empty",
                        )
                    return (
                        self._results[current]
                        if current < len(self._results)
                        else self._results[-1]
                    )

                @override
                def run_raw(
                    self,
                    cmd: t.StrSequence,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                    input_data: bytes | None = None,
                ) -> p.Result[m.Cli.CommandOutput]:
                    self.commands.append(tuple(cmd))
                    del cmd, cwd, timeout, env, input_data
                    return self._next_result()

                @override
                def run(
                    self,
                    cmd: t.StrSequence,
                    cwd: t.Cli.PathLike | None = None,
                    timeout: int | None = None,
                    env: t.Cli.StrEnvMapping | None = None,
                ) -> p.Result[m.Cli.CommandOutput]:
                    self.commands.append(tuple(cmd))
                    del cmd, cwd, timeout, env
                    result = self._next_result()
                    if result.failure:
                        return result
                    output = result.value
                    if output.exit_code != 0:
                        return r[m.Cli.CommandOutput].fail(
                            output.stderr or output.stdout or "Command failed",
                        )
                    return result

            @staticmethod
            def ok_result[ValueT](value: ValueT) -> p.Result[ValueT]:
                return r[ValueT].ok(value)

            @staticmethod
            def fail_result[ValueT](message: str) -> p.Result[ValueT]:
                return r[ValueT].fail(message)

            @staticmethod
            def infra_mapping(
                value: t.Infra.InfraMapping,
            ) -> t.Infra.ContainerDict:
                return t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)

            @staticmethod
            def infra_mapping_result(
                value: t.Infra.InfraMapping,
            ) -> p.Result[t.Infra.ContainerDict]:
                return r[t.Infra.ContainerDict].ok(
                    TestsFlextInfraUtilities.Infra.Tests.infra_mapping(value),
                )

            @staticmethod
            def tool_config_document() -> m.Infra.ToolConfigDocument:
                result = u.Infra.load_tool_config()
                assert result.success
                return result.value

            @staticmethod
            def toml_doc_mapping(doc: t.Cli.TomlDocument) -> t.Cli.JsonMapping:
                return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    u.Cli.normalize_json_value(doc.unwrap()),
                )

            @staticmethod
            def toml_mapping(value: t.RecursiveContainer | None) -> t.Cli.JsonMapping:
                return t.Cli.JSON_MAPPING_ADAPTER.validate_python(
                    u.Cli.normalize_json_value(value),
                )

            @staticmethod
            def toml_list(value: t.RecursiveContainer | None) -> t.Cli.JsonList:
                return t.Cli.JSON_LIST_ADAPTER.validate_python(
                    u.Cli.normalize_json_value(value),
                )

            @staticmethod
            def toml_strings(value: t.RecursiveContainer | None) -> t.StrSequence:
                return t.Infra.STR_SEQ_ADAPTER.validate_python(
                    u.Cli.normalize_json_value(value),
                )

            @staticmethod
            def command_runner(
                *,
                stdout: str = "",
                stderr: str = "",
                returncode: int = 0,
            ) -> p.Cli.CommandRunner:
                return TestsFlextInfraUtilities.Infra.Tests.DeptryRunner(
                    TestsFlextInfraUtilities.Infra.Tests.ok_result(
                        TestsFlextInfraUtilities.Infra.Tests.stub_run(
                            stdout=stdout,
                            stderr=stderr,
                            returncode=returncode,
                        ),
                    ),
                )

            class MigratorDiscovery:
                """Typed discovery stub for migrator behavior tests."""

                def __init__(
                    self,
                    projects: Sequence[m.Infra.ProjectInfo] | None = None,
                    *,
                    error: str = "",
                ) -> None:
                    self._projects = projects or []
                    self._error = error

                def discover_projects(
                    self,
                    workspace_root: Path,
                ) -> p.Result[Sequence[m.Infra.ProjectInfo]]:
                    _ = workspace_root
                    if self._error:
                        return r[Sequence[m.Infra.ProjectInfo]].fail(self._error)
                    return r[Sequence[m.Infra.ProjectInfo]].ok(self._projects)

            class MigratorGenerator(FlextInfraBaseMkGenerator):
                """Typed base.mk generator stub for migrator behavior tests."""

                def __init__(self, content: str = "", *, fail: str = "") -> None:
                    self._content = content
                    self._fail = fail

                @override
                def generate_basemk(
                    self,
                    settings: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
                ) -> p.Result[str]:
                    del settings
                    if self._fail:
                        return r[str].fail(self._fail)
                    return r[str].ok(self._content)

            @staticmethod
            def is_docker_available() -> bool:
                return shutil.which("docker") is not None

            @staticmethod
            def is_project_valid(project_name: str) -> bool:
                return (
                    bool(project_name)
                    and project_name
                    .replace("-", "")
                    .replace(
                        "_",
                        "",
                    )
                    .isalnum()
                )

            @staticmethod
            def stub_run(
                *,
                stdout: str = "",
                stderr: str = "",
                returncode: int = 0,
            ) -> m.Cli.CommandOutput:
                return m.Cli.CommandOutput(
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=returncode,
                )

            @staticmethod
            def mk_project(
                root: Path,
                name: str,
                *,
                pyproject: str = "[tool]\n",
                with_src: bool = False,
                with_git: bool = False,
            ) -> Path:
                project_dir = root / name
                project_dir.mkdir(parents=True, exist_ok=True)
                (project_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")
                if with_src:
                    (project_dir / "src").mkdir(exist_ok=True)
                if with_git:
                    (project_dir / ".git").mkdir(exist_ok=True)
                return project_dir

            @staticmethod
            def create_docs_workspace(
                root: Path,
                *,
                project_names: t.StrSequence = (),
                include_fixable_link: bool = False,
            ) -> Path:
                workspace = root / "workspace"
                workspace.mkdir(parents=True, exist_ok=True)

                def _write(path: Path, content: str) -> None:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")

                readme = "# Root\n"
                docs_readme = "# Docs\n\n## Overview\n"
                if include_fixable_link:
                    _write(workspace / "docs/guides/setup.md", "# Setup\n")
                    docs_readme = (
                        "# Docs\n\n## Overview\n\n"
                        "See [Setup](guides/setup) for details.\n"
                    )
                _write(workspace / "README.md", readme)
                _write(workspace / "docs/README.md", docs_readme)
                _write(workspace / "docs/index.md", "# Index\n")
                _write(workspace / "docs/architecture/README.md", "# Architecture\n")
                _write(workspace / "docs/guides/README.md", "# Guides\n")
                _write(workspace / "docs/projects/README.md", "# Projects\n")
                _write(workspace / "docs/api-reference/README.md", "# API Reference\n")

                for name in project_names:
                    project = workspace / name
                    project.mkdir(parents=True, exist_ok=True)
                    _write(
                        project / "pyproject.toml",
                        (f'[project]\nname = "{name}"\nversion = "0.1.0"\n'),
                    )
                    _write(project / "README.md", f"# {name}\n")
                    _write(project / "docs/README.md", "# Project Docs\n")
                    _write(project / "docs/architecture.md", "# Architecture\n")
                    _write(project / "docs/dev.md", "# Development\n")
                    _write(project / "docs/api.md", "# API\n")

                return workspace

            @staticmethod
            def create_github_workspace(
                root: Path,
                *,
                project_names: t.StrSequence = (),
                source_workflow: str = "name: CI\n",
                pr_exit_codes: t.StrMapping | None = None,
            ) -> Path:
                workspace = root / "workspace"
                workspace.mkdir(parents=True, exist_ok=True)
                workflow_dir = workspace / ".github/workflows"
                workflow_dir.mkdir(parents=True, exist_ok=True)
                (workflow_dir / "ci.yml").write_text(
                    source_workflow,
                    encoding="utf-8",
                )
                exit_codes = dict(pr_exit_codes or {})
                for name in project_names:
                    project = workspace / name
                    project.mkdir(parents=True, exist_ok=True)
                    (project / "pyproject.toml").write_text(
                        (
                            "[project]\n"
                            f'name = "{name}"\n'
                            'version = "0.1.0"\n'
                            'dependencies = ["flext-core>=0.1.0"]\n'
                        ),
                        encoding="utf-8",
                    )
                    src_dir = project / "src" / name.replace("-", "_")
                    src_dir.mkdir(parents=True, exist_ok=True)
                    (src_dir / "__init__.py").write_text("", encoding="utf-8")
                    exit_code = str(exit_codes.get(name, "0"))
                    (project / "Makefile").write_text(
                        f"pr:\n\t@exit {exit_code}\n",
                        encoding="utf-8",
                    )
                return workspace

            @staticmethod
            def create_release_workspace(
                root: Path,
                *,
                project_names: t.StrSequence = (),
                root_validate_exit_code: str = "0",
                root_build_exit_code: str = "0",
                project_validate_exit_codes: t.StrMapping | None = None,
                project_build_exit_codes: t.StrMapping | None = None,
                initialize_root_git: bool = False,
                initialize_project_git: bool = False,
            ) -> Path:
                workspace = root / "workspace"
                workspace.mkdir(parents=True, exist_ok=True)
                (workspace / "pyproject.toml").write_text(
                    (
                        "[project]\n"
                        'name = "workspace-root"\n'
                        'version = "0.1.0"\n'
                        'dependencies = ["flext-core>=0.1.0"]\n'
                    ),
                    encoding="utf-8",
                )
                (workspace / "Makefile").write_text(
                    (
                        "val:\n"
                        f"\t@exit {root_validate_exit_code}\n"
                        "build:\n"
                        f"\t@exit {root_build_exit_code}\n"
                    ),
                    encoding="utf-8",
                )
                validate_exit_codes = dict(project_validate_exit_codes or {})
                build_exit_codes = dict(project_build_exit_codes or {})
                for name in project_names:
                    project = workspace / name
                    project.mkdir(parents=True, exist_ok=True)
                    (project / "pyproject.toml").write_text(
                        (
                            "[project]\n"
                            f'name = "{name}"\n'
                            'version = "0.1.0"\n'
                            'dependencies = ["flext-core>=0.1.0"]\n'
                        ),
                        encoding="utf-8",
                    )
                    src_dir = project / "src" / name.replace("-", "_")
                    src_dir.mkdir(parents=True, exist_ok=True)
                    (src_dir / "__init__.py").write_text("", encoding="utf-8")
                    validate_exit_code = validate_exit_codes.get(name, "0")
                    build_exit_code = build_exit_codes.get(name, "0")
                    (project / "Makefile").write_text(
                        (
                            "val:\n"
                            f"\t@exit {validate_exit_code}\n"
                            "build:\n"
                            f"\t@exit {build_exit_code}\n"
                        ),
                        encoding="utf-8",
                    )
                if initialize_root_git:
                    TestsFlextInfraUtilities.Infra.Tests.initialize_git_repo(workspace)
                else:
                    (workspace / ".git").mkdir(exist_ok=True)
                if initialize_project_git:
                    for name in project_names:
                        TestsFlextInfraUtilities.Infra.Tests.initialize_git_repo(
                            workspace / name,
                        )
                return workspace

            @staticmethod
            def create_path_sync_workspace(
                root: Path,
                *,
                root_pyproject: str,
                projects: t.StrMapping | None = None,
                gitmodules_members: t.StrSequence = (),
                extra_dirs: t.StrSequence = (),
            ) -> Path:
                workspace = root / "workspace"
                workspace.mkdir(parents=True, exist_ok=True)
                (workspace / "pyproject.toml").write_text(
                    root_pyproject,
                    encoding="utf-8",
                )
                if gitmodules_members:
                    gitmodules_lines: list[str] = []
                    for name in gitmodules_members:
                        gitmodules_lines.extend((
                            f'[submodule "{name}"]',
                            f"\tpath = {name}",
                            f"\turl = https://example.invalid/{name}.git",
                            "",
                        ))
                    (workspace / ".gitmodules").write_text(
                        "\n".join(gitmodules_lines).rstrip() + "\n",
                        encoding="utf-8",
                    )
                for directory in extra_dirs:
                    (workspace / directory).mkdir(parents=True, exist_ok=True)
                for name, pyproject in dict(projects or {}).items():
                    project = workspace / name
                    project.mkdir(parents=True, exist_ok=True)
                    (project / "pyproject.toml").write_text(
                        pyproject,
                        encoding="utf-8",
                    )
                    package = project / "src" / name.replace("-", "_")
                    package.mkdir(parents=True, exist_ok=True)
                    (package / "__init__.py").write_text("", encoding="utf-8")
                return workspace

            @staticmethod
            def create_path_sync_pyproject(
                *,
                name: str,
                dependency_path: str = "",
                workspace_members: t.StrSequence = (),
            ) -> str:
                lines = ["[project]", f'name = "{name}"']
                if dependency_path:
                    lines.append(
                        f'dependencies = ["flext-core @ file://{dependency_path}"]',
                    )
                    lines.extend((
                        "",
                        "[tool.poetry.dependencies]",
                        f'flext-core = {{ path = "{dependency_path}" }}',
                    ))
                if workspace_members:
                    members = ", ".join(f'"{member}"' for member in workspace_members)
                    lines.extend((
                        "",
                        "[tool.uv.workspace]",
                        f"members = [{members}]",
                    ))
                return "\n".join(lines) + "\n"

            @staticmethod
            def initialize_git_repo(repo_root: Path) -> None:
                commands: Sequence[t.StrSequence] = (
                    (c.Infra.GIT, "init", "-b", "main"),
                    (c.Infra.GIT, "config", "user.email", "tests@flext.local"),
                    (c.Infra.GIT, "config", "user.name", "Flext Tests"),
                    (c.Infra.GIT, "add", "-A"),
                    (c.Infra.GIT, "commit", "-m", "init"),
                )
                for command in commands:
                    _ = subprocess.run(
                        command,
                        cwd=repo_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )

            @staticmethod
            def to_pascal(snake: str) -> str:
                return "".join(part.title() for part in snake.split("_"))

            @staticmethod
            def src_module_files() -> tuple[str, ...]:
                return (
                    "constants.py",
                    "typings.py",
                    "protocols.py",
                    "models.py",
                    "utilities.py",
                )

            @staticmethod
            def create_codegen_project(
                *,
                tmp_path: Path,
                name: str,
                pkg_name: str,
                files: t.StrMapping,
            ) -> Path:
                project = tmp_path / name
                project.mkdir()
                (project / "Makefile").touch()
                (project / "pyproject.toml").write_text(
                    (f"[project]\nname='{name}'\ndependencies=['flext-core>=0.1.0']\n"),
                    encoding="utf-8",
                )
                (project / ".git").mkdir()
                pkg = project / "src" / pkg_name
                pkg.mkdir(parents=True)
                (pkg / "__init__.py").touch()
                pascal_name = TestsFlextInfraUtilities.Infra.Tests.to_pascal(pkg_name)
                (pkg / "typings.py").write_text(
                    "from flext_core import FlextTypes\n"
                    f"class {pascal_name}Types(FlextTypes):\n    pass\n",
                    encoding="utf-8",
                )
                (pkg / "constants.py").write_text(
                    "from flext_core import FlextConstants\n"
                    f"class {pascal_name}Constants(FlextConstants):\n    pass\n",
                    encoding="utf-8",
                )
                for filename, content in files.items():
                    (pkg / filename).write_text(content, encoding="utf-8")
                return project

            @staticmethod
            def create_scaffolder_test_project(
                *,
                tmp_path: Path,
                with_all_modules: bool,
            ) -> Path:
                project = tmp_path / "test-project"
                project.mkdir()
                (project / "Makefile").touch()
                (project / "pyproject.toml").write_text(
                    (
                        "[project]\nname='test-project'\n"
                        "dependencies=['flext-core>=0.1.0']\n"
                    ),
                    encoding="utf-8",
                )
                (project / ".git").mkdir()
                pkg = project / "src" / "test_project"
                pkg.mkdir(parents=True)
                (pkg / "__init__.py").touch()
                if with_all_modules:
                    for mod in TestsFlextInfraUtilities.Infra.Tests.src_module_files():
                        (pkg / mod).write_text(
                            f"class TestProject{mod.split('.')[0].title()}:\n    pass\n",
                            encoding="utf-8",
                        )
                return project

            @staticmethod
            def create_migrator_project(
                project_root: Path,
                name: str = "project-a",
            ) -> m.Infra.ProjectInfo:
                return m.Infra.ProjectInfo.model_validate(
                    obj={
                        "name": name,
                        "path": project_root,
                        "stack": "python/external",
                        "has_tests": False,
                        "has_src": True,
                    },
                )

            @staticmethod
            def create_project_info(
                project_root: Path,
                *,
                name: str = c.Infra.Tests.Fixtures.Deps.PROJECT_NAME,
                stack: str = c.Infra.Tests.Fixtures.Workspace.PROJECT_STACK,
                has_tests: bool = False,
                has_src: bool = True,
                project_class: str = c.Infra.Tests.Fixtures.Workspace.PROJECT_CLASS,
                package_name: str = (
                    c.Infra.Tests.Fixtures.Workspace.PROJECT_PACKAGE_NAME
                ),
                workspace_role: c.Infra.WorkspaceProjectRole = (
                    c.Infra.WorkspaceProjectRole.ATTACHED
                ),
            ) -> m.Infra.ProjectInfo:
                return m.Infra.ProjectInfo(
                    name=name,
                    path=project_root,
                    stack=stack,
                    has_tests=has_tests,
                    has_src=has_src,
                    project_class=project_class,
                    package_name=package_name,
                    workspace_role=workspace_role,
                )

            @staticmethod
            def create_command_output(
                *,
                stdout: str = "",
                stderr: str = "",
                exit_code: int = 0,
                duration: float = 0.0,
            ) -> m.Cli.CommandOutput:
                return m.Cli.CommandOutput(
                    stdout=stdout,
                    stderr=stderr,
                    exit_code=exit_code,
                    duration=duration,
                )

            @staticmethod
            def create_deptry_service(
                *,
                projects: Sequence[m.Infra.ProjectInfo] | None = None,
                selection_error: str | None = None,
                command_output: m.Cli.CommandOutput | None = None,
                run_error: str | None = None,
            ) -> FlextInfraDependencyDetectionService:
                service = FlextInfraDependencyDetectionService()
                service.selector = TestsFlextInfraUtilities.Infra.Tests.DeptrySelector(
                    (
                        r[Sequence[m.Infra.ProjectInfo]].fail(selection_error)
                        if selection_error is not None
                        else r[Sequence[m.Infra.ProjectInfo]].ok(list(projects or []))
                    ),
                )
                service.runner = TestsFlextInfraUtilities.Infra.Tests.DeptryRunner(
                    (
                        r[m.Cli.CommandOutput].fail(run_error)
                        if run_error is not None
                        else r[m.Cli.CommandOutput].ok(
                            command_output
                            or TestsFlextInfraUtilities.Infra.Tests.create_command_output()
                        )
                    ),
                )
                return service

            @staticmethod
            def patch_public_infra(
                monkeypatch: pytest.MonkeyPatch,
                name: str,
                value: t.Infra.Tests.PublicProjectDiscoveryStub | t.Scalar,
            ) -> None:
                patched = staticmethod(value) if callable(value) else value
                monkeypatch.setattr(
                    u.Infra,
                    name,
                    patched,
                )

            @staticmethod
            def create_lazy_init_workspace(
                tmp_path: Path,
                *,
                project_name: str = c.Infra.Tests.Fixtures.Codegen.LazyInit.PROJECT_NAME,
                package_name: str = c.Infra.Tests.Fixtures.Codegen.LazyInit.PACKAGE_NAME,
            ) -> tuple[Path, Path]:
                workspace_root = tmp_path / project_name
                package_root = workspace_root / c.Infra.DEFAULT_SRC_DIR / package_name
                package_root.mkdir(parents=True)
                (workspace_root / "Makefile").write_text(
                    "check:\n\t@true\n",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                (workspace_root / c.Infra.PYPROJECT_FILENAME).write_text(
                    (f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n'),
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                (package_root / c.Infra.INIT_PY).write_text(
                    "",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                return (workspace_root, package_root)

            @staticmethod
            def write_lazy_init_namespace_module(
                module_path: Path,
                *,
                class_name: str,
                alias: str,
                docstring: str = "Test namespace.",
            ) -> None:
                export_list = f'"{class_name}", "{alias}"'
                module_path.write_text(
                    (
                        f'"""{docstring}"""\n\n'
                        "from __future__ import annotations\n\n"
                        f"__all__: list[str] = [{export_list}]\n\n"
                        f"class {class_name}:\n"
                        "    pass\n\n"
                        f"{alias} = {class_name}\n"
                    ),
                    encoding=c.Infra.ENCODING_DEFAULT,
                )

            @staticmethod
            def write_lazy_init_version_module(package_root: Path) -> None:
                (package_root / "__version__.py").write_text(
                    (
                        f'__version__ = "{c.Infra.Tests.Fixtures.Codegen.LazyInit.VERSION}"\n'
                        "__version_info__ = "
                        f"{c.Infra.Tests.Fixtures.Codegen.LazyInit.VERSION_INFO}\n"
                    ),
                    encoding=c.Infra.ENCODING_DEFAULT,
                )

            @staticmethod
            def run_lazy_init(
                workspace_root: Path,
                *,
                check_only: bool = False,
            ) -> int:
                return FlextInfraCodegenLazyInit(
                    workspace=workspace_root,
                ).generate_inits(check_only=check_only)

            @staticmethod
            def create_lazy_init_service(
                workspace_root: Path,
            ) -> FlextInfraCodegenLazyInit:
                return FlextInfraCodegenLazyInit(workspace=workspace_root)

            @staticmethod
            def extract_lazy_init_exports(source: str) -> tuple[bool, t.StrSequence]:
                for name, value_str in u.Infra.get_module_level_assignments(source):
                    if name == c.Infra.DUNDER_ALL:
                        return (
                            True,
                            tuple(re.findall(r'["\']([^"\']+)["\']', value_str)),
                        )
                return (False, ())

            @staticmethod
            def consolidate_codegen(
                *,
                workspace_root: Path,
                project: str | None = None,
                dry_run: bool = True,
            ) -> p.Result[str]:
                if project is None:
                    return FlextInfraCodegenConsolidator(
                        workspace=workspace_root,
                        dry_run=dry_run,
                    ).execute()
                return FlextInfraCodegenConsolidator(
                    workspace=workspace_root,
                    dry_run=dry_run,
                    project_name=project,
                ).execute()

            @staticmethod
            def build_mro_import_workspace(
                tmp_path: Path,
            ) -> tuple[Path, Path, Path]:
                workspace_root = tmp_path
                project_root = (
                    workspace_root / c.Infra.Tests.Fixtures.Refactor.PROJECT_NAME
                )
                package_root = (
                    project_root
                    / c.Infra.DEFAULT_SRC_DIR
                    / c.Infra.Tests.Fixtures.Refactor.PACKAGE_NAME
                )
                package_root.mkdir(parents=True)
                (project_root / ".git").mkdir()
                (project_root / "Makefile").write_text(
                    "test:\n\t@true\n",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                (project_root / c.Infra.PYPROJECT_FILENAME).write_text(
                    "[project]\nname = 'flext-demo'\nversion = '0.1.0'\n",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                (package_root / c.Infra.INIT_PY).write_text(
                    "",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                constants_path = package_root / "constants.py"
                constants_path.write_text(
                    "from __future__ import annotations\n\n"
                    f'{c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME} = "{c.Infra.Tests.Fixtures.Refactor.SYMBOL_VALUE}"\n\n'
                    f"class {c.Infra.Tests.Fixtures.Refactor.CONSTANTS_CLASS}:\n"
                    "    pass\n\n"
                    f"{c.Infra.Tests.Fixtures.Refactor.FACADE_ALIAS} = {c.Infra.Tests.Fixtures.Refactor.CONSTANTS_CLASS}\n",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                consumer_path = package_root / "consumer.py"
                consumer_path.write_text(
                    "from __future__ import annotations\n\n"
                    f"from demo_pkg.constants import {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}\n\n"
                    f"value = {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}\n",
                    encoding=c.Infra.ENCODING_DEFAULT,
                )
                return (workspace_root, constants_path, consumer_path)

            @staticmethod
            def create_mro_scan_report(constants_path: Path) -> m.Infra.MROScanReport:
                return m.Infra.MROScanReport(
                    file=str(constants_path),
                    module="demo_pkg.constants",
                    constants_class=c.Infra.Tests.Fixtures.Refactor.CONSTANTS_CLASS,
                    facade_alias=c.Infra.Tests.Fixtures.Refactor.FACADE_ALIAS,
                    candidates=(
                        m.Infra.MROSymbolCandidate(
                            symbol=c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME,
                            line=3,
                            kind="constant",
                            class_name="",
                            facade_name=c.Infra.Tests.Fixtures.Refactor.FACADE_ALIAS,
                        ),
                    ),
                )

            @staticmethod
            def migrate_workspace_mro_imports(
                *,
                workspace_root: Path,
                constants_path: Path,
                apply: bool,
            ) -> tuple[
                Sequence[m.Infra.MROFileMigration],
                Sequence[m.Infra.MRORewriteResult],
                t.StrSequence,
            ]:
                return FlextInfraRefactorMROImportRewriter.migrate_workspace(
                    workspace_root=workspace_root,
                    scan_results=[
                        TestsFlextInfraUtilities.Infra.Tests.create_mro_scan_report(
                            constants_path,
                        )
                    ],
                    apply=apply,
                )

            @staticmethod
            def patch_mro_import_rewriter_write_failure(
                monkeypatch: pytest.MonkeyPatch,
            ) -> None:
                def _fail_write(
                    *,
                    workspace_root: Path,
                    file_path: Path,
                    updated_source: str,
                ) -> t.Infra.EditResult:
                    del workspace_root, file_path, updated_source
                    return (False, ("  REVERTED src/demo_pkg/constants.py:",))

                monkeypatch.setattr(
                    FlextInfraRefactorMROImportRewriter,
                    "_protected_source_write",
                    staticmethod(_fail_write),
                )

            @staticmethod
            def create_migrator_discovery(
                projects: Sequence[m.Infra.ProjectInfo] | None = None,
                *,
                error: str = "",
            ) -> p.Infra.Discovery:
                return TestsFlextInfraUtilities.Infra.Tests.MigratorDiscovery(
                    projects,
                    error=error,
                )

            @staticmethod
            def create_migrator_generator(
                content: str = "",
                *,
                fail: str = "",
            ) -> FlextInfraBaseMkGenerator:
                return TestsFlextInfraUtilities.Infra.Tests.MigratorGenerator(
                    content,
                    fail=fail,
                )

            @staticmethod
            def build_project_migrator(
                project: m.Infra.ProjectInfo,
                base_mk: str,
                *,
                workspace_root: Path | None = None,
                dry_run: bool = False,
            ) -> FlextInfraProjectMigrator:
                migrator = FlextInfraProjectMigrator(
                    workspace=workspace_root or Path("/dummy"),
                    apply=not dry_run,
                    dry_run=dry_run,
                )
                migrator.discovery = (
                    TestsFlextInfraUtilities.Infra.Tests.create_migrator_discovery([
                        project
                    ])
                )
                migrator.generator = (
                    TestsFlextInfraUtilities.Infra.Tests.create_migrator_generator(
                        base_mk
                    )
                )
                return migrator

            @staticmethod
            def detect_command(
                workspace_root: Path,
                **overrides: t.Infra.Tests.DetectCommandOverride,
            ) -> m.Infra.DetectCommand:
                return m.Infra.DetectCommand.model_validate({
                    "workspace": str(workspace_root),
                    **overrides,
                })

            @staticmethod
            def create_detector_deps_stub(
                project_paths: Sequence[Path],
            ) -> TestsFlextInfraUtilities.Infra.Tests.DetectorDepsStub:
                return TestsFlextInfraUtilities.Infra.Tests.DetectorDepsStub(
                    project_paths
                )

            @staticmethod
            def setup_detector_runtime(
                tmp_path: Path,
                deps: p.Infra.DepsService,
                *,
                deptry_exists: bool = True,
                reporting: p.Infra.ReportingService | None = None,
                runner: p.Infra.RunnerService | None = None,
            ) -> FlextInfraRuntimeDevDependencyDetector:
                deptry_path = tmp_path / c.Infra.VENV_BIN_REL / c.Infra.DEPTRY
                deptry_path.parent.mkdir(parents=True, exist_ok=True)
                if deptry_exists:
                    deptry_path.write_text("", encoding="utf-8")
                return FlextInfraRuntimeDevDependencyDetector(
                    reporting=reporting,
                    deps=deps,
                    runner=runner,
                )

            @staticmethod
            def write_migrator_project(project_root: Path) -> None:
                project_root.mkdir(parents=True, exist_ok=True)
                (project_root / ".git").mkdir(parents=True, exist_ok=True)
                (project_root / "base.mk").write_text("OLD_BASE\n", encoding="utf-8")
                (project_root / "Makefile").write_text(
                    'python "$(WORKSPACE_ROOT)/scripts/check/workspace_check.py"\n',
                    encoding="utf-8",
                )
                (project_root / "pyproject.toml").write_text(
                    "[project]\n",
                    encoding="utf-8",
                )
                (project_root / ".gitignore").write_text("", encoding="utf-8")

            @staticmethod
            def create_gate_execution(
                gate: str = "lint",
                project: str = "p",
                *,
                passed: bool = True,
                issues: Sequence[m.Infra.Issue] | None = None,
            ) -> m.Infra.GateExecution:
                return m.Infra.GateExecution(
                    result=m.Infra.GateResult(
                        gate=gate,
                        project=project,
                        passed=passed,
                        errors=(),
                        duration=0.0,
                    ),
                    issues=tuple(issues or ()),
                    raw_output="",
                )

            @staticmethod
            def make_issue(
                *,
                file: str = "a.py",
                line: int = 1,
                column: int = 1,
                code: str = "E1",
                message: str = "Error",
            ) -> m.Infra.Issue:
                return m.Infra.Issue(
                    file=file,
                    line=line,
                    column=column,
                    code=code,
                    message=message,
                    severity="error",
                )

            @staticmethod
            def make_project(
                name: str = "p",
                gates: MutableMapping[str, m.Infra.GateExecution] | None = None,
            ) -> m.Infra.ProjectResult:
                resolved_gates: MutableMapping[str, m.Infra.GateExecution] = (
                    gates
                    if gates is not None
                    else {
                        "lint": TestsFlextInfraUtilities.Infra.Tests.create_gate_execution()
                    }
                )
                return m.Infra.ProjectResult.model_validate({
                    "project": name,
                    "gates": resolved_gates,
                })

            @staticmethod
            def create_checker_project(
                tmp_path: Path,
                *,
                project_name: str = "p1",
                with_src: bool = False,
            ) -> tuple[FlextInfraWorkspaceChecker, Path]:
                checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
                project_dir = TestsFlextInfraUtilities.Infra.Tests.mk_project(
                    tmp_path,
                    project_name,
                )
                if with_src:
                    (project_dir / "src").mkdir(parents=True, exist_ok=True)
                return checker, project_dir

            @staticmethod
            def create_check_project_iter_stub(
                projects: Sequence[m.Infra.ProjectResult],
            ) -> t.Infra.Tests.ProjectCheckStub:
                project_iter = iter(projects)

                def _fake_check(
                    _self: object,
                    _project_dir: Path,
                    _gates: t.StrSequence,
                    _ctx: m.Infra.GateContext,
                ) -> m.Infra.ProjectResult:
                    del _self, _project_dir, _gates, _ctx
                    return next(project_iter)

                return _fake_check

            @staticmethod
            def patch_gate_run(
                monkeypatch: pytest.MonkeyPatch,
                gate_class: t.Infra.Tests.GateClass,
                *,
                stdout: str = "",
                stderr: str = "",
                returncode: int = 0,
            ) -> None:
                fixed_result = TestsFlextInfraUtilities.Infra.Tests.stub_run(
                    stdout=stdout,
                    stderr=stderr,
                    returncode=returncode,
                )

                def _run(
                    _self: FlextInfraGate,
                    _cmd: t.StrSequence,
                    _cwd: Path,
                    timeout: int = 120,
                    env: dict[str, str] | None = None,
                ) -> m.Cli.CommandOutput:
                    del _self, _cmd, _cwd, timeout, env
                    return fixed_result

                monkeypatch.setattr(gate_class, "_run", _run)

            @staticmethod
            def patch_gate_run_sequence(
                monkeypatch: pytest.MonkeyPatch,
                gate_class: t.Infra.Tests.GateClass,
                outputs: Sequence[m.Cli.CommandOutput],
            ) -> None:
                index = {"value": 0}

                def _run(
                    _self: FlextInfraGate,
                    _cmd: t.StrSequence,
                    _cwd: Path,
                    timeout: int = 120,
                    env: dict[str, str] | None = None,
                ) -> m.Cli.CommandOutput:
                    del _self, _cmd, _cwd, timeout, env
                    current = index["value"]
                    index["value"] = current + 1
                    return outputs[current] if current < len(outputs) else outputs[-1]

                monkeypatch.setattr(gate_class, "_run", _run)

            @staticmethod
            def patch_python_dir_detection(
                monkeypatch: pytest.MonkeyPatch,
                gate_class: t.Infra.Tests.GateClass,
                *,
                has_python_dirs: bool,
            ) -> None:
                if gate_class.__name__ == "FlextInfraPyreflyGate":

                    def _get_check_dirs(
                        _self: FlextInfraGate,
                        _project_dir: Path,
                        _ctx: m.Infra.GateContext,
                    ) -> t.StrSequence:
                        del _self, _project_dir, _ctx
                        return ["src"] if has_python_dirs else []

                    monkeypatch.setattr(gate_class, "_get_check_dirs", _get_check_dirs)
                    return

                def _existing_dirs(
                    _self: FlextInfraGate, _project_dir: Path
                ) -> t.StrSequence:
                    del _self, _project_dir
                    return ["src"]

                def _dirs_with_py(
                    _project_dir: Path, _dirs: t.StrSequence
                ) -> t.StrSequence:
                    del _project_dir, _dirs
                    return ["src"] if has_python_dirs else []

                monkeypatch.setattr(gate_class, "_existing_check_dirs", _existing_dirs)
                monkeypatch.setattr(
                    gate_class, "_dirs_with_py", staticmethod(_dirs_with_py)
                )

            @staticmethod
            def create_gate_context(
                workspace_root: Path,
                *,
                reports_dir: Path | None = None,
            ) -> m.Infra.GateContext:
                return m.Infra.GateContext(
                    workspace=workspace_root,
                    reports_dir=reports_dir or workspace_root,
                )

            @staticmethod
            def run_gate_check(
                gate_class: t.Infra.Tests.GateClass,
                workspace_root: Path,
                project_dir: Path,
                *,
                ctx: m.Infra.GateContext | None = None,
                reports_dir: Path | None = None,
                runner: p.Cli.CommandRunner | None = None,
            ) -> m.Infra.GateExecution:
                gate = gate_class(workspace_root, runner=runner)
                return gate.check(
                    project_dir,
                    ctx
                    or TestsFlextInfraUtilities.Infra.Tests.create_gate_context(
                        workspace_root,
                        reports_dir=reports_dir,
                    ),
                )

            @staticmethod
            def create_fake_run_raw(
                result: p.Result[m.Cli.CommandOutput] | str,
            ) -> t.Infra.Tests.RawRunStub:
                def _fake_run_raw(
                    _cmd: t.StrSequence,
                    cwd: Path | None = None,
                    timeout: int | None = None,
                    env: t.StrMapping | None = None,
                ) -> p.Result[m.Cli.CommandOutput]:
                    del _cmd, cwd, timeout, env
                    return (
                        r[m.Cli.CommandOutput].fail(result)
                        if isinstance(result, str)
                        else result
                    )

                return _fake_run_raw

            @staticmethod
            def create_check_project_stub(
                project: m.Infra.ProjectResult,
            ) -> t.Infra.Tests.ProjectCheckStub:
                def _fake_check(
                    _self: object,
                    _project_dir: Path,
                    _gates: t.StrSequence,
                    _ctx: m.Infra.GateContext,
                ) -> m.Infra.ProjectResult:
                    del _self, _project_dir, _gates, _ctx
                    return project

                return _fake_check

            class DetectorReportStub:
                """Minimal report stub for dependency detector tests."""

                def __init__(self, raw_count: int) -> None:
                    self._raw_count = raw_count

                def model_dump(self) -> MutableMapping[str, t.IntMapping]:
                    return {"deptry": {"raw_count": self._raw_count}}

            class DetectorDepsStub(
                p.Infra.DepsService,
                p.Infra.TypingsDepsService,
            ):
                """Typed dependency service stub for detector tests."""

                def __init__(self, project_paths: Sequence[Path]) -> None:
                    self.project_paths = project_paths
                    self.discovery_failure: str | None = None
                    self.deptry_failure: str | None = None
                    self.typings_failure: str | None = None

                @override
                def discover_project_paths(
                    self,
                    workspace_root: Path,
                    *,
                    projects_filter: t.StrSequence | None = None,
                ) -> p.Result[Sequence[Path]]:
                    del workspace_root, projects_filter
                    if self.discovery_failure is not None:
                        return r[Sequence[Path]].fail(self.discovery_failure)
                    return r[Sequence[Path]].ok(self.project_paths)

                @override
                def run_deptry(
                    self,
                    project_path: Path,
                    venv_bin: Path,
                ) -> p.Result[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]]:
                    del project_path, venv_bin
                    if self.deptry_failure is not None:
                        return r[
                            t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]
                        ].fail(self.deptry_failure)
                    return r[t.Infra.Pair[Sequence[t.Infra.ContainerDict], int]].ok(
                        ([], 0),
                    )

                @override
                def build_project_report(
                    self,
                    project_name: str,
                    deptry_issues: Sequence[t.Infra.ContainerDict],
                ) -> TestsFlextInfraUtilities.Infra.Tests.DetectorReportStub:
                    del project_name, deptry_issues
                    return TestsFlextInfraUtilities.Infra.Tests.DetectorReportStub(0)

                @override
                def get_required_typings(
                    self,
                    project_path: Path,
                    venv_bin: Path,
                    limits_path: Path | None = None,
                    *,
                    include_mypy: bool = True,
                ) -> p.Result[m.Infra.TypingsReport]:
                    del project_path, venv_bin, limits_path
                    del include_mypy
                    if self.typings_failure is not None:
                        return r[m.Infra.TypingsReport].fail(self.typings_failure)
                    return r[m.Infra.TypingsReport].ok(
                        m.Infra.TypingsReport(to_add=[]),
                    )

                @override
                def load_dependency_limits(
                    self,
                    limits_path: Path | None = None,
                ) -> t.StrMapping:
                    del limits_path
                    limits: dict[str, str] = {}
                    return limits


u = TestsFlextInfraUtilities

__all__: list[str] = ["TestsFlextInfraUtilities", "u"]
