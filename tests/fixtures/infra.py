"""Pytest fixtures for FLEXT infra tests.

Provides reusable fixtures for creating real project structures using tmp_path.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from flext_infra import config, settings, workspace
from tests import c, m, p, t, tm, u

_FIXTURES_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def native_cprofile(tmp_path: Path) -> Path:
    """Create real pstats outside any profiler owned by the pytest worker.

    Returns:
        The independently measured native profile.

    """
    profile = tmp_path / c.Infra.REPORTS_DIR_NAME / "fixture.pstats"
    profile.parent.mkdir(parents=True, exist_ok=True)
    workload = tmp_path / "profile_workload.py"
    workload.write_text("sum(range(3))\n", encoding=c.DEFAULT_ENCODING)
    tm.ok(
        u.Cli.run_checked(
            (
                sys.executable,
                "-m",
                "cProfile",
                "-o",
                str(profile),
                str(workload),
            ),
            cwd=tmp_path,
        )
    )
    return profile


@pytest.fixture
def native_consumer(tmp_path: Path) -> p.Tests.NativeConsumer:
    """Run native reference probes against real fixture source trees.

    Returns:
        The resulting ``p.Tests.NativeConsumer``.

    """
    runtime = tm.ok(
        workspace.FlextInfraWorkspaceDetector.resolution_context(_PROJECT_ROOT)
    ).runtime_root
    prelude = (
        "import importlib, pathlib, sys\n"
        "from pathlib import Path\n"
        "from flext_infra import m\n"
        "from flext_infra.codegen import FlextInfraCodegenPreconditions as "
        "preconditions\n"
        "from flext_infra.workspace.native_reference import "
        "FlextInfraWorkspaceNativeReference as native\n"
        f"runtime_root = Path({str(runtime)!r})\n"
    )

    def consume(code: str, *arguments: str, cwd: Path | None = None) -> None:
        u.Tests.run_lazy_init_probe(
            prelude + code,
            python_paths=(),
            arguments=arguments,
            cwd=tmp_path if cwd is None else cwd,
        )

    return consume


@pytest.fixture
def declaration_workspace(tmp_path: Path) -> t.Pair[Path, Path]:
    """Provide the standard FLEXT workspace fabric for native declarations.

    Returns:
        The resulting ``t.Pair[Path, Path]``.

    """
    return u.Tests.create_lazy_init_workspace(tmp_path)


@pytest.fixture
def source_preview_workspace(
    tmp_path: Path,
    session_runtime: p.Tests.SessionRuntime,
) -> t.Pair[Path, Path]:
    """Provide source preview with its own physical runtime and real dependencies.

    Returns:
        The workspace root and its source package.

    """
    root = tmp_path.with_name(f"{tmp_path.name}-source-preview")
    root.mkdir()
    u.Tests.initialize_git_repo(root)
    package = u.Tests.src_package(
        root,
        "sample",
        pyproject=(
            "[project]\nname = 'sample'\nversion = '1.0.0'\n"
            f'dependencies = ["{config.Infra.name}"]\n'
        ),
    )
    tm.ok(
        u.Tests.create_python_environment(
            root,
            dependency_projects=u.Tests.python_dependency_projects(root),
            session_runtime=session_runtime,
        ),
    )
    return root, package


@pytest.fixture
def binding_probe_rule() -> m.Infra.CodemodRule:
    """Supply one validated metadata owner for semantic binding probes.

    Returns:
        The probe rule whose consumer supplies its context conditions.

    """
    return m.Infra.CodemodRule(
        id="binding-probe",
        digest="probe",
        provider="probe",
        resource=Path("probe.yml"),
        fixable=True,
    )


def _read_fixture(*parts: str) -> str:
    return _FIXTURES_DIR.joinpath(*parts).read_text(encoding="utf-8")


def _modernizer_pyproject(name: str) -> str:
    return f'[project]\nname = "{name}"\nversion = "0.1.0"\n'


def _modernizer_workspace_pyproject(*members: str) -> str:
    base = _modernizer_pyproject("workspace")
    if not members:
        return base
    members_text = ", ".join(f'"{member}"' for member in members)
    return f"{base}\n[tool.uv.workspace]\nmembers = [{members_text}]\n"


def _write_modernizer_codegen_config(workspace: Path) -> None:
    """Copy the valid governed SSOT into the isolated modernizer owner.

    Constraint rewriting validates the complete typed codegen contract and
    must never write the installed infrastructure checkout (flext-eles2).
    """
    config_dir = workspace / c.Infra.CODEGEN_CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / c.Infra.CODEGEN_CONFIG_FILENAME).write_bytes(
        (
            _PROJECT_ROOT / c.Infra.CODEGEN_CONFIG_DIR / c.Infra.CODEGEN_CONFIG_FILENAME
        ).read_bytes(),
    )


@pytest.fixture
def deptry_report_payload() -> t.JsonPayload:
    """Provide ``deptry_report_payload``.

    Returns:
        The resulting ``t.JsonPayload``.

    """
    parsed = u.Cli.json_parse(_read_fixture("deps", "deptry_report.json"))
    parsed = tm.not_none(parsed)
    tm.ok(parsed)
    return parsed.value


@pytest.fixture
def runner_ci_context_cleared() -> Iterator[None]:
    """Keep the runner's CI context out of every test body.

    The approval path runs the suite under ``CI=Y``: collection reads it to
    deselect CI-excluded tests, but a test body must behave identically on a
    runner and on a workstation. Inherited ``CI`` silently selected CI-only
    contracts (the CI member identity, the CI resolution guard) in local
    scenarios; a scenario that exercises a CI contract passes the configured
    variable explicitly.

    Yields:
        Control inside the scoped environment.

    """
    with u.Tests.env_vars_context(
        vars_to_clear=(config.Infra.codegen.make.ci.variable,),
    ):
        yield


@pytest.fixture(scope="session")
def suite_runtime_root() -> Path:
    """Elect the runtime that owns this suite's checkout, through its owner.

    Fixture checkouts declare it as their runtime root, as a composed member
    declares its workspace's: the probes then run in a real environment
    holding the FLEXT packages, never in the bare runner interpreter.

    Returns:
        The physical runtime root of the suite checkout.

    """
    return tm.ok(u.Infra.runtime_owner_root(_PROJECT_ROOT))


@pytest.fixture
def profiling_enabled() -> Iterator[None]:
    """Opt child processes into profiling through the typed settings owner.

    Profiling is opt-in; the variable is the settings field's own declared
    alias, so a renamed setting cannot leave the scenario silently unprofiled.

    Yields:
        Control while spawned processes inherit the enabled setting.

    """
    alias = type(settings.Infra).model_fields["profile"].validation_alias
    tm.that(alias, is_=str)
    with u.Tests.env_vars_context(
        env_vars={str(alias): c.ParserBooleanToken.TRUE},
    ):
        yield


@pytest.fixture
def tool_config_document() -> m.Infra.ToolConfigDocument:
    """Provide ``tool_config_document``.

    Returns:
        The resulting ``m.Infra.ToolConfigDocument``.

    """
    return u.Tests.tool_config_document()


@pytest.fixture
def real_toml_project(tmp_path: Path) -> Path:
    """Create a real project with valid pyproject.toml.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    pyproject_content = """\
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
authors = [{name = "Test", email = "test@example.com"}]
"""
    (project_root / c.PYPROJECT_FILENAME).write_text(pyproject_content)
    return project_root


@pytest.fixture
def real_makefile_project(tmp_path: Path) -> Path:
    """Create a real project with valid Makefile.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "makefile_project"
    project_root.mkdir()
    makefile_content = """\
.PHONY: help setup check test

help:
\t@echo "Available targets"

setup:
\t@echo "Setting up"

check:
\t@echo "Checking"

test:
\t@echo "Testing"
"""
    (project_root / "Makefile").write_text(makefile_content)
    return project_root


@pytest.fixture
def real_python_package(tmp_path: Path) -> Path:
    """Create a real Python package with src layout.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "python_package"
    project_root.mkdir()
    src_dir = project_root / "src" / "test_pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Test package."""\n__version__ = "0.1.0"\n')
    (src_dir / "identity.py").write_text(
        '"""Substantive unique source consumed by real scanner fixtures."""\n\n'
        "def normalize_identity(parts: tuple[str, ...]) -> str:\n"
        '    """Normalize one ordered identity without duplicated code."""\n'
        "    normalized = tuple(part.strip() for part in parts if part.strip())\n"
        "    if not normalized:\n"
        '        raise ValueError("identity requires at least one non-empty part")\n'
        '    return "::".join(normalized).casefold()\n',
        encoding="utf-8",
    )
    (project_root / c.PYPROJECT_FILENAME).write_text(
        '[project]\nname = "test-pkg"\nversion = "0.1.0"\n',
    )
    return project_root


@pytest.fixture
def cached_runner_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a real one-test consumer for the public cached pytest runner.

    Returns:
        The resulting ``Path``.

    """
    external_cache = tmp_path / "external-cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(external_cache))
    monkeypatch.setenv("LOCALAPPDATA", str(external_cache))
    project_root = tmp_path / "cached_runner_project"
    policy = config.Infra.codegen.make.testmon_cache
    package_root = project_root / c.Infra.DEFAULT_SRC_DIR / "runner_sample"
    tests_root = project_root / policy.target_directory
    package_root.mkdir(parents=True)
    tests_root.mkdir(parents=True)
    # A faithful consumer project carries the fleet-standard coverage
    # boundary: the Cython provider mapping of dependency_injector is not
    # parseable source and is omitted by every fleet coverage config.
    tm.ok(
        u.Cli.toml_write_mapping(
            project_root / c.PYPROJECT_FILENAME,
            {
                "tool": {
                    "coverage": {
                        "run": {"omit": ["*/dependency_injector/providers.pyx"]},
                    },
                    "pytest": {
                        "ini_options": {
                            "pythonpath": [c.Infra.DEFAULT_SRC_DIR],
                            "markers": list(
                                config.Infra.tooling.tools.pytest.standard_markers,
                            ),
                        },
                    },
                },
            },
        ),
    )
    (package_root / "__init__.py").write_text(
        "def answer() -> int:\n    return 42\n",
        encoding="utf-8",
    )
    # The runner contract is proven through process evidence (exit codes,
    # manifests, accounting), not through the child's assertion library. The
    # consumer's suite stays on plain asserts: every nested runner lifecycle
    # imports the child suite, and the shared assertion facade drags the full
    # infrastructure model materialization into each of those interpreters.
    (tests_root / "test_runtime.py").write_text(
        "from runner_sample import answer\n\n"
        "def test_runtime() -> None:\n"
        "    assert answer() == 42\n",
        encoding="utf-8",
    )
    return project_root


@pytest.fixture
def policy_violation_project(tmp_path: Path) -> Path:
    """Create a real consumer whose suite violates the slow-timeout policy.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "policy_violation_project"
    policy = config.Infra.codegen.make.testmon_cache
    tests_root = project_root / policy.target_directory
    tests_root.mkdir(parents=True)
    # The ini value is an arbitrary non-production budget owned by this probe.
    (project_root / c.PYPROJECT_FILENAME).write_text(
        '[tool.pytest.ini_options]\nflext_slow_timeout_seconds = "30"\n',
        encoding="utf-8",
    )
    (tests_root / "test_policy.py").write_text(
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.mark.timeout(1)\n"
        "def test_breaks_policy() -> None:\n"
        "    pass\n",
        encoding="utf-8",
    )
    return project_root


@pytest.fixture(scope="session")
def mod_workspace_artifact(
    session_runtime: p.Tests.SessionRuntime,
) -> t.Pair[Path, Path]:
    """Build the worker's native refactor fixture distribution once.

    Returns:
        The source template and its backend-produced wheel.

    """
    project_document = u.read_project_document_cached(_PROJECT_ROOT)
    project = u.build_project_metadata(_PROJECT_ROOT, project_document)
    workspace = session_runtime.directory / "mod_workspace"
    build = config.Infra.codegen.scaffold.build
    build_backend = tm.ok(u.Cli.json_dumps(build.backend))
    build_requirements = tm.ok(u.Cli.json_dumps(list(build.requirements)))
    author_name = tm.ok(u.Cli.json_dumps(project.project.authors[0].name))
    license_id = tm.ok(
        u.Cli.json_dumps(
            u.Cli.json_walk_path(
                u.Infra.pyproject_payload(_PROJECT_ROOT / c.PYPROJECT_FILENAME),
                (c.Infra.PROJECT, c.Infra.LICENSE),
            ),
        ),
    )
    tm.ok(u.Cli.ensure_dir(workspace))
    tm.ok(
        u.Cli.atomic_write_text_file(
            workspace / c.PYPROJECT_FILENAME,
            (
                "[build-system]\n"
                f"build-backend = {build_backend}\n"
                f"requires = {build_requirements}\n"
                "\n"
                "[project]\n"
                f'name = "{workspace.name.replace("_", "-")}"\n'
                f'version = "{project.project.version}"\n'
                f"authors = [{{name = {author_name}}}]\n"
                f"license = {license_id}\n"
                f"{c.Infra.DEPENDENCIES} = []\n"
            ),
        ),
    )
    # A declared distribution owns a package: resolving the package name from
    # `[project].name` alone is impossible for a `flext-` distribution, so a
    # fixture without `src/<pkg>/` is not the project it claims to be. The
    # package follows the fixture's own declared name: naming it after the
    # real project would shadow the installed flext_infra for Rope, and every
    # packaged campaign binding (flext_infra.c / .t) would lose its owner.
    package_dir = workspace / c.Infra.DEFAULT_SRC_DIR / workspace.name
    tm.ok(u.Cli.ensure_dir(package_dir))
    tm.ok(
        u.Cli.atomic_write_text_file(
            package_dir / c.Infra.INIT_PY,
            '"""Public refactor-mod fixture package."""\n\n'
            "from __future__ import annotations\n",
        ),
    )
    tm.ok(
        u.Cli.atomic_write_text_file(
            workspace / "sample.py",
            # The fixture owns every name it uses and carries exactly one
            # defect: the governance rule the tests exercise. Undefined names
            # or an unresolvable import would make the diagnostic gates red for
            # a reason unrelated to the rule, and mod's own contract is that
            # the tree is clean before and after.
            (
                '"""Public refactor-mod fixture module with one governance defect."""\n'
                "\n"
                "from __future__ import annotations\n"
                "\n"
                "from flext_core import t\n"
                "\n"
                "class _FixtureInfra:\n"
                '    """Stand-in infra namespace owning every name'
                ' the fixture uses."""\n'
                "\n"
                "    @staticmethod\n"
                "    def serialization_lock_execute(\n"
                "        paths: tuple[str, ...], timeout: float\n"
                "    ) -> None:\n"
                '        """Accept the governed call shape without any effect."""\n'
                "\n"
                "\n"
                "class _FixtureFacade:\n"
                '    """Stand-in utilities facade exposing the infra namespace."""\n'
                "\n"
                "    Infra = _FixtureInfra\n"
                "\n"
                "\n"
                "u = _FixtureFacade()\n"
                "paths: tuple[str, ...] = ()\n"
                "timeout: float = 1.0\n"
                "\n"
                "u.Infra.serialization_lock_execute(paths, timeout)\n"
            ),
        ),
    )
    wheels = tm.ok(
        u.Tests.python_dependency_wheels(
            session_runtime.directory,
            (workspace,),
        ),
    )
    return workspace, wheels[0]


@pytest.fixture
def mod_workspace(
    installed_dependency_path: Path,
    mod_workspace_artifact: t.Pair[Path, Path],
) -> Path:
    """Provide case-local sources and a genuinely installed fixture distribution.

    Returns:
        The source workspace beside the installed package root.

    """
    template, wheel = mod_workspace_artifact
    workspace = installed_dependency_path.parent / template.name
    shutil.copytree(template, workspace)
    tm.ok(
        u.Cli.run_checked(
            (
                u.Tests.managed_uv(),
                "pip",
                "install",
                "--no-config",
                "--python",
                sys.executable,
                "--no-deps",
                "--target",
                str(installed_dependency_path),
                str(wheel),
            ),
            cwd=workspace,
        ),
    )
    u.Tests.initialize_git_repo(workspace)
    return workspace


@pytest.fixture
def real_workspace(tmp_path: Path) -> Path:
    """Create a real multi-project workspace.

    Returns:
        The resulting ``Path``.

    """
    repository_root = tmp_path / "workspace"
    repository_root.mkdir()
    (repository_root / "Makefile").write_text(
        ".PHONY: help\nhelp:\n\t@echo 'Workspace'\n",
    )
    (repository_root / c.PYPROJECT_FILENAME).write_text(
        '[project]\nname = "workspace"\nversion = "0.1.0"\n',
    )
    for i in range(1, 4):
        project_dir = repository_root / f"project_{i}"
        project_dir.mkdir()
        (project_dir / c.PYPROJECT_FILENAME).write_text(
            f'[project]\nname = "project-{i}"\nversion = "0.1.0"\n',
        )
        src_dir = project_dir / "src" / f"project_{i}"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").write_text(f'"""Project {i}."""\n')
    return repository_root


@pytest.fixture
def modernizer_workspace(tmp_path: Path) -> Path:
    """Provide ``modernizer_workspace``.

    Returns:
        The resulting ``Path``.

    """
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    # The governed tree above the workspace carries the committed Mise
    # declaration and lock that activate its locked tools.
    u.Tests.copy_tracked_mise_seeds(tmp_path)
    (workspace / c.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject(),
        encoding="utf-8",
    )
    u.Tests.write_beads_project(
        workspace,
        workspace="workspace",
        database="workspace",
        issue_prefix="workspace",
    )
    _write_modernizer_codegen_config(workspace)
    return workspace


@pytest.fixture
def modernizer_workspace_with_projects(modernizer_workspace: Path) -> Path:
    """Provide ``modernizer_workspace_with_projects``.

    Returns:
        The resulting ``Path``.

    """
    (modernizer_workspace / c.PYPROJECT_FILENAME).write_text(
        _modernizer_workspace_pyproject("selected", "ignored"),
        encoding="utf-8",
    )
    selected = u.Tests.mk_project(
        modernizer_workspace,
        "selected",
        pyproject=_modernizer_pyproject("selected"),
    )
    ignored = u.Tests.mk_project(
        modernizer_workspace,
        "ignored",
        pyproject=_modernizer_pyproject("ignored"),
    )
    for project in (selected, ignored):
        u.Tests.write_beads_project(
            project,
            workspace="workspace",
            database=project.name,
            issue_prefix=project.name,
        )
    (modernizer_workspace / ".gitmodules").write_text(
        '[submodule "selected"]\n\tpath = selected\n'
        "\turl = https://github.com/flext-sh/selected.git\n"
        '[submodule "ignored"]\n\tpath = ignored\n'
        "\turl = https://github.com/flext-sh/ignored.git\n",
        encoding="utf-8",
    )
    # FLEXT: public modernizer commands fail loud outside a real Git workspace.
    u.Tests.initialize_git_repo(modernizer_workspace)
    return modernizer_workspace


@pytest.fixture
def real_docs_project(tmp_path: Path) -> Path:
    """Create a real project with documentation.

    Returns:
        The resulting ``Path``.

    """
    project_root = tmp_path / "docs_project"
    project_root.mkdir()
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "README.md").write_text("# Documentation\n")
    (docs_dir / "index.md").write_text("# Index\n")
    (project_root / "README.md").write_text("# Project\n")
    (project_root / c.PYPROJECT_FILENAME).write_text(
        '[project]\nname = "docs-project"\nversion = "0.1.0"\n',
    )
    return project_root


@pytest.fixture
def semantic_rope_workspace(tmp_path: Path) -> t.Pair[t.Infra.RopeProject, Path]:
    """Create a real rope workspace with semantic-analysis fixtures.

    Returns:
        The resulting ``t.Pair[t.Infra.RopeProject, Path]``.

    """
    repository_root = tmp_path / "rope_workspace"
    package_root = repository_root / "src" / "rope_demo"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "models.py").write_text(
        "from pathlib import Path\n\n"
        "class Animal:\n"
        "    pass\n\n"
        "class Dog(Animal):\n"
        "    home = Path('kennel')\n\n"
        "    @staticmethod\n"
        "    def fetch() -> str:\n"
        "        return 'ball'\n\n"
        "    @classmethod\n"
        "    def breed(cls) -> str:\n"
        "        return cls.__name__\n\n"
        "    def _wag(self) -> str:\n"
        "        return 'wag'\n",
        encoding="utf-8",
    )
    (package_root / "services.py").write_text(
        "from rope_demo.models import Dog\n\n"
        "class Kennel:\n"
        "    def adopt(self) -> Dog:\n"
        "        return Dog()\n",
        encoding="utf-8",
    )

    rope_project = u.Infra.init_rope_project(repository_root)
    return rope_project, repository_root


@pytest.fixture
def models_resource(
    semantic_rope_workspace: t.Pair[t.Infra.RopeProject, Path],
) -> t.Infra.RopeFile:
    """Return the Rope resource for the semantic models fixture module.

    Returns:
        The Rope resource for the semantic models fixture module.

    """
    rope_project, repository_root = semantic_rope_workspace
    resource = u.Infra.resolve_resource_from_path(
        rope_project,
        repository_root / "src" / "rope_demo" / "models.py",
    )
    return tm.not_none(resource)


@pytest.fixture
def services_resource(
    semantic_rope_workspace: t.Pair[t.Infra.RopeProject, Path],
) -> t.Infra.RopeFile:
    """Return the Rope resource for the semantic services fixture module.

    Returns:
        The Rope resource for the semantic services fixture module.

    """
    rope_project, repository_root = semantic_rope_workspace
    resource = u.Infra.resolve_resource_from_path(
        rope_project,
        repository_root / "src" / "rope_demo" / "services.py",
    )
    return tm.not_none(resource)
