"""Test utilities for flext-infra."""

from __future__ import annotations

import re
import shutil
import types
from collections.abc import Callable, MutableMapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import override

import pytest
from flext_tests import FlextTestsUtilities

import flext_infra.deps.detector as detector_runtime_module
from flext_core import r
from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraCodegenConsolidator,
    FlextInfraCodegenLazyInit,
    FlextInfraDependencyDetectionService,
    FlextInfraGate,
    FlextInfraProjectMigrator,
    FlextInfraRefactorMROImportRewriter,
    FlextInfraRuntimeDevDependencyDetector,
    FlextInfraUtilities,
    FlextInfraWorkspaceChecker,
)
from tests import c, m, p, t


class ReleaseFakeUtilsNamespace:
    """Fake replacement for the release orchestrator utility namespace."""

    class Infra:
        """Fake Infra utilities namespace for release tests."""

        _git_checkout_result: r[bool] = r[bool].ok(True)
        _git_run_result: r[str] = r[str].ok("")
        _git_run_checked_result: r[bool] = r[bool].ok(True)
        _git_tag_exists_result: r[bool] = r[bool].ok(False)
        _git_create_tag_result: r[bool] = r[bool].ok(True)
        _git_checkout_side_effects: Sequence[r[bool]] | None = None
        _call_count: int = 0

        @classmethod
        def git_checkout(cls, *args: str, **kwargs: str) -> r[bool]:
            del args, kwargs
            if cls._git_checkout_side_effects is not None:
                idx = cls._call_count
                cls._call_count += 1
                return cls._git_checkout_side_effects[idx]
            return cls._git_checkout_result

        @classmethod
        def git_run(cls, *args: str, **kwargs: str) -> r[str]:
            del args, kwargs
            return cls._git_run_result

        @classmethod
        def git_run_checked(cls, *args: str, **kwargs: str) -> r[bool]:
            del args, kwargs
            return cls._git_run_checked_result

        @classmethod
        def git_tag_exists(cls, *args: str, **kwargs: str) -> r[bool]:
            del args, kwargs
            return cls._git_tag_exists_result

        @classmethod
        def git_create_tag(cls, *args: str, **kwargs: str) -> r[bool]:
            del args, kwargs
            return cls._git_create_tag_result

        @classmethod
        def resolve_projects(
            cls,
            workspace_root: Path,
            names: t.StrSequence,
        ) -> r[Sequence[SimpleNamespace]]:
            del cls, workspace_root, names
            return r[Sequence[SimpleNamespace]].ok([])

        @classmethod
        def generate_notes(
            cls,
            version: str,
            tag: str,
            projects: Sequence[SimpleNamespace],
            changes: str,
            output_path: Path,
        ) -> r[bool]:
            del cls, version, projects
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(f"# Release {tag}\n{changes}\n", encoding="utf-8")
            return r[bool].ok(True)

        @classmethod
        def reset(cls) -> None:
            cls._git_checkout_result = r[bool].ok(True)
            cls._git_run_result = r[str].ok("")
            cls._git_run_checked_result = r[bool].ok(True)
            cls._git_tag_exists_result = r[bool].ok(False)
            cls._git_create_tag_result = r[bool].ok(True)
            cls._git_checkout_side_effects = None
            cls._call_count = 0


class ReleaseSelectionStub:
    """Typed selection stub for release orchestrator tests."""

    def __init__(self) -> None:
        self.resolve_result = r[Sequence[m.Infra.ProjectInfo]].ok([])

    def resolve_projects(
        self,
        workspace_root: Path,
        names: t.StrSequence,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        del workspace_root, names
        return self.resolve_result


class DetectorReportStub:
    """Minimal report stub for dependency detector tests."""

    def __init__(self, raw_count: int) -> None:
        self._raw_count = raw_count

    def model_dump(self) -> MutableMapping[str, t.IntMapping]:
        return {"deptry": {"raw_count": self._raw_count}}


class DetectorDepsStub:
    """Typed dependency service stub for detector tests."""

    def __init__(self, project_paths: Sequence[Path]) -> None:
        self.project_paths = project_paths
        self.discovery_failure: str | None = None
        self.deptry_failure: str | None = None
        self.typings_failure: str | None = None

    def discover_project_paths(
        self,
        root: Path,
        *,
        projects_filter: t.StrSequence | None = None,
    ) -> r[Sequence[Path]]:
        del root, projects_filter
        if self.discovery_failure is not None:
            return r[Sequence[Path]].fail(self.discovery_failure)
        return r[Sequence[Path]].ok(self.project_paths)

    def run_deptry(
        self,
        project_path: Path,
        venv_bin: Path,
    ) -> r[tuple[Sequence[t.StrMapping], int]]:
        del project_path, venv_bin
        if self.deptry_failure is not None:
            return r[tuple[Sequence[t.StrMapping], int]].fail(self.deptry_failure)
        return r[tuple[Sequence[t.StrMapping], int]].ok(([], 0))

    def build_project_report(
        self,
        project_name: str,
        issues: Sequence[t.StrMapping],
    ) -> DetectorReportStub:
        del project_name, issues
        return DetectorReportStub(0)

    def get_required_typings(
        self,
        project_path: Path,
        venv_bin: Path,
        *,
        limits_path: Path,
    ) -> r[types.SimpleNamespace]:
        del project_path, venv_bin, limits_path
        if self.typings_failure is not None:
            return r[types.SimpleNamespace].fail(self.typings_failure)
        typings = types.SimpleNamespace(to_add=[])

        def _model_dump() -> MutableMapping[str, t.StrSequence]:
            return {"to_add": []}

        setattr(typings, "model_dump", _model_dump)
        return r[types.SimpleNamespace].ok(typings)

    def load_dependency_limits(
        self,
        limits_path: Path | None = None,
    ) -> t.StrMapping:
        del limits_path
        limits: dict[str, str] = {}
        return limits


type ProjectCheckStub = Callable[..., m.Infra.ProjectResult]
type RawRunStub = Callable[..., r[m.Cli.CommandOutput]]


class TestsFlextInfraUtilities(FlextTestsUtilities, FlextInfraUtilities):
    """Typed test utilities for flext-infra."""

    class Infra(FlextInfraUtilities.Infra):
        """Infra-specific utilities namespace."""

        class Tests(FlextTestsUtilities.Tests):
            """Canonical test helper namespace."""

            class DeptrySelector:
                """Protocol-compatible selector backed by a real Result."""

                def __init__(
                    self,
                    result: r[Sequence[m.Infra.ProjectInfo]],
                ) -> None:
                    self._result = result

                def resolve_projects(
                    self,
                    workspace_root: Path,
                    names: t.StrSequence,
                ) -> r[Sequence[m.Infra.ProjectInfo]]:
                    del workspace_root, names
                    return self._result

            class DeptryRunner:
                """Protocol-compatible runner backed by a real Result."""

                def __init__(
                    self,
                    result: r[m.Cli.CommandOutput],
                ) -> None:
                    self._result = result

                def run_raw(
                    self,
                    cmd: t.StrSequence,
                    cwd: Path | None = None,
                    timeout: int | None = None,
                    env: t.StrMapping | None = None,
                ) -> r[m.Cli.CommandOutput]:
                    del cmd, cwd, timeout, env
                    return self._result

            @staticmethod
            def ok_result[ValueT](value: ValueT) -> r[ValueT]:
                return r[ValueT].ok(value)

            @staticmethod
            def fail_result[ValueT](message: str) -> r[ValueT]:
                return r[ValueT].fail(message)

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
                ) -> r[Sequence[m.Infra.ProjectInfo]]:
                    _ = workspace_root
                    if self._error:
                        return r[Sequence[m.Infra.ProjectInfo]].fail(self._error)
                    return r[Sequence[m.Infra.ProjectInfo]].ok(self._projects)

            class MigratorGenerator(FlextInfraBaseMkGenerator):
                """Typed base.mk generator stub for migrator behavior tests."""

                def __init__(self, content: str = "", *, fail: str = "") -> None:
                    super().__init__()
                    self._content = content
                    self._fail = fail

                @override
                def generate_basemk(
                    self,
                    config: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
                ) -> r[str]:
                    del config
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
                value: object,
            ) -> None:
                patched = staticmethod(value) if callable(value) else value
                monkeypatch.setattr(
                    FlextInfraUtilities.Infra,
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
                package_root = (
                    workspace_root / c.Infra.Paths.DEFAULT_SRC_DIR / package_name
                )
                package_root.mkdir(parents=True)
                (workspace_root / "Makefile").write_text(
                    "check:\n\t@true\n",
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                (workspace_root / c.Infra.Files.PYPROJECT_FILENAME).write_text(
                    (
                        "[project]\n"
                        f'name = "{project_name}"\n'
                        'version = "0.1.0"\n'
                    ),
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                (package_root / c.Infra.Files.INIT_PY).write_text(
                    "",
                    encoding=c.Infra.Encoding.DEFAULT,
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
                        f'__all__ = [{export_list}]\n\n'
                        f"class {class_name}:\n"
                        "    pass\n\n"
                        f"{alias} = {class_name}\n"
                    ),
                    encoding=c.Infra.Encoding.DEFAULT,
                )

            @staticmethod
            def write_lazy_init_version_module(package_root: Path) -> None:
                (package_root / "__version__.py").write_text(
                    (
                        f'__version__ = "{c.Infra.Tests.Fixtures.Codegen.LazyInit.VERSION}"\n'
                        "__version_info__ = "
                        f"{c.Infra.Tests.Fixtures.Codegen.LazyInit.VERSION_INFO}\n"
                    ),
                    encoding=c.Infra.Encoding.DEFAULT,
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
                    if name == c.Infra.Dunders.ALL:
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
            ) -> r[str]:
                payload: t.Infra.MutableInfraMapping = {
                    "workspace_root": workspace_root,
                    "dry_run": dry_run,
                }
                if project is not None:
                    payload["project"] = project
                return FlextInfraCodegenConsolidator.model_validate(payload).execute()

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
                    / c.Infra.Paths.DEFAULT_SRC_DIR
                    / c.Infra.Tests.Fixtures.Refactor.PACKAGE_NAME
                )
                package_root.mkdir(parents=True)
                (project_root / ".git").mkdir()
                (project_root / "Makefile").write_text(
                    "test:\n\t@true\n",
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                (project_root / c.Infra.Files.PYPROJECT_FILENAME).write_text(
                    "[project]\nname = 'flext-demo'\nversion = '0.1.0'\n",
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                (package_root / c.Infra.Files.INIT_PY).write_text(
                    "",
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                constants_path = package_root / "constants.py"
                constants_path.write_text(
                    "from __future__ import annotations\n\n"
                    f'{c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME} = "{c.Infra.Tests.Fixtures.Refactor.SYMBOL_VALUE}"\n\n'
                    f"class {c.Infra.Tests.Fixtures.Refactor.CONSTANTS_CLASS}:\n"
                    "    pass\n\n"
                    f"{c.Infra.Tests.Fixtures.Refactor.FACADE_ALIAS} = {c.Infra.Tests.Fixtures.Refactor.CONSTANTS_CLASS}\n",
                    encoding=c.Infra.Encoding.DEFAULT,
                )
                consumer_path = package_root / "consumer.py"
                consumer_path.write_text(
                    "from __future__ import annotations\n\n"
                    f"from demo_pkg.constants import {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}\n\n"
                    f"value = {c.Infra.Tests.Fixtures.Refactor.SYMBOL_NAME}\n",
                    encoding=c.Infra.Encoding.DEFAULT,
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
                    *args: object,
                    **kwargs: object,
                ) -> tuple[bool, tuple[str, ...]]:
                    del args, kwargs
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
            def patch_release_utils_namespace(
                monkeypatch: pytest.MonkeyPatch,
                orchestrator_module: object,
            ) -> type[ReleaseFakeUtilsNamespace]:
                ReleaseFakeUtilsNamespace.Infra.reset()
                monkeypatch.setattr(
                    orchestrator_module,
                    "u",
                    ReleaseFakeUtilsNamespace,
                )
                return ReleaseFakeUtilsNamespace

            @staticmethod
            def create_release_selection() -> ReleaseSelectionStub:
                return ReleaseSelectionStub()

            @staticmethod
            def patch_release_projects(
                monkeypatch: pytest.MonkeyPatch,
                *,
                result: r[Sequence[m.Infra.ProjectInfo]] | None = None,
            ) -> None:
                selection = (
                    TestsFlextInfraUtilities.Infra.Tests.create_release_selection()
                )
                if result is not None:
                    selection.resolve_result = result

                def _resolve_projects(
                    workspace_root: Path,
                    names: t.StrSequence,
                ) -> r[Sequence[m.Infra.ProjectInfo]]:
                    return selection.resolve_projects(workspace_root, names)

                monkeypatch.setattr(
                    u.Infra,
                    "resolve_projects",
                    staticmethod(_resolve_projects),
                )

            @staticmethod
            def patch_deptry_exists(
                monkeypatch: pytest.MonkeyPatch,
                *,
                exists: bool,
            ) -> None:
                def _exists(_: Path) -> bool:
                    return exists

            @staticmethod
            def create_detector_deps_stub(
                project_paths: Sequence[Path],
            ) -> DetectorDepsStub:
                return DetectorDepsStub(project_paths)

            @staticmethod
            def setup_detector_runtime(
                monkeypatch: pytest.MonkeyPatch,
                tmp_path: Path,
                deps: DetectorDepsStub,
                *,
                deptry_exists: bool = True,
            ) -> FlextInfraRuntimeDevDependencyDetector:
                del tmp_path
                monkeypatch.setattr(
                    detector_runtime_module,
                    "FlextInfraDependencyDetectionService",
                    lambda: deps,
                )
                TestsFlextInfraUtilities.Infra.Tests.patch_deptry_exists(
                    monkeypatch,
                    exists=deptry_exists,
                )
                return FlextInfraRuntimeDevDependencyDetector()

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
                    else {"lint": u.Infra.Tests.create_gate_execution()}
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
            ) -> ProjectCheckStub:
                project_iter = iter(projects)

                def _fake_check(
                    *_args: object, **_kwargs: object
                ) -> m.Infra.ProjectResult:
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
                    _cmd: Sequence[str],
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
                    _cmd: Sequence[str],
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
                    ) -> Sequence[str]:
                        del _self, _project_dir, _ctx
                        return ["src"] if has_python_dirs else []

                    monkeypatch.setattr(gate_class, "_get_check_dirs", _get_check_dirs)
                    return

                def _existing_dirs(
                    _self: FlextInfraGate, _project_dir: Path
                ) -> Sequence[str]:
                    del _self, _project_dir
                    return ["src"]

                def _dirs_with_py(
                    _project_dir: Path, _dirs: Sequence[str]
                ) -> Sequence[str]:
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
            ) -> m.Infra.GateExecution:
                gate = gate_class(workspace_root)
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
                result: r[m.Cli.CommandOutput] | str,
            ) -> RawRunStub:
                def _fake_run_raw(
                    _cmd: Sequence[str],
                    **_kw: object,
                ) -> r[m.Cli.CommandOutput]:
                    del _cmd, _kw
                    return (
                        r[m.Cli.CommandOutput].fail(result)
                        if isinstance(result, str)
                        else result
                    )

                return _fake_run_raw

            @staticmethod
            def create_fake_run_projects(
                passed: bool | None = None,
                error_msg: str | None = None,
            ) -> m.Infra.Tests.RunProjectsMock:
                return m.Infra.Tests.RunProjectsMock(passed=passed, error_msg=error_msg)

            @staticmethod
            def create_check_project_stub(
                project: m.Infra.ProjectResult,
            ) -> ProjectCheckStub:
                def _fake_check(
                    *_args: object, **_kwargs: object
                ) -> m.Infra.ProjectResult:
                    del _args, _kwargs
                    return project

                return _fake_check


u = TestsFlextInfraUtilities
__all__ = ["TestsFlextInfraUtilities", "u"]
