"""Workspace and project-layout fixture test utilities for flext-infra."""

from __future__ import annotations

from pathlib import Path

from flext_infra import u
from flext_infra.check.workspace_check import FlextInfraWorkspaceChecker
from flext_tests import tm
from tests import c, m, t
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin
from tests.utilities_git import TestsFlextInfraUtilitiesGitMixin


class TestsFlextInfraUtilitiesWorkspaceFixtureMixin:
    """Typed workspace and project-layout fixture helpers."""

    @staticmethod
    def mk_project(
        root: Path,
        name: str,
        *,
        pyproject: str = "[tool]\n",
        with_src: bool = False,
        with_git: bool = False,
    ) -> Path:
        """Provide the typed test helper `mk_project`."""
        project_dir = root / name
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")
        if with_src:
            package_dir = project_dir / "src" / name.replace("-", "_")
            package_dir.mkdir(parents=True, exist_ok=True)
            # FLEXT: with_src means a discoverable package, not an empty marker.
            (package_dir / "__init__.py").write_text("", encoding="utf-8")
        if with_git:
            (project_dir / ".git").mkdir(exist_ok=True)
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            project_dir, name
        )
        return project_dir

    @staticmethod
    def write_standalone_workspace_manifest(
        project_dir: Path,
        name: str,
        *,
        upstream: str | None = None,
        inherited_facets: t.StrSequence = (),
        root_modules: t.StrSequence = (),
        root_packages: t.StrSequence = (),
    ) -> Path:
        """Write the declared ``config/workspace.yaml`` of one standalone repository.

        The Makefile projection reads declarations only, so this fixture is
        the complete topology input for ``codegen conform --what makefile
        --scope self``. Every value is derived from the same typed SSOT the
        production loader validates against, never frozen by hand.
        """
        repository = TestsFlextInfraUtilitiesProjectFixtureMixin.repository_ref(
            name, role=c.Infra.MakeProfile.STANDALONE
        )
        project = TestsFlextInfraUtilitiesProjectFixtureMixin.project_spec(name)
        if upstream is not None:
            project = project.model_copy(update={"upstream": upstream})
        if inherited_facets:
            project = project.model_copy(
                update={"inherited_facets": tuple(inherited_facets)}
            )
        if root_modules or root_packages:
            project = project.model_copy(
                update={
                    "root_modules": tuple(root_modules),
                    "root_packages": tuple(root_packages),
                }
            )
        manifest = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=name,
            repository=repository,
            project=project,
        )
        config_dir = project_dir / c.CONFIG_DIR_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = config_dir / c.Infra.WORKSPACE_MANIFEST_FILENAME
        tm.ok(u.Cli.yaml_dump(manifest_path, manifest.model_dump(mode="json")))
        return manifest_path

    @staticmethod
    def standalone_workspace(
        project_dir: Path, name: str = "flext-demo"
    ) -> m.Infra.WorkspaceSpec:
        """Materialize and load the canonical minimal standalone fixture."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        package_root = project_dir / "src" / name.replace("-", "_")
        package_root.mkdir(parents=True, exist_ok=True)
        (package_root / "__init__.py").write_text("", encoding="utf-8")
        (project_dir / "pyproject.toml").write_text(
            "[project]\n"
            f'name = "{name}"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "dependencies = []\n",
            encoding="utf-8",
        )
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            project_dir, name
        )
        workspace = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(project_dir)
        )
        return workspace.model_copy(
            update={
                "project": TestsFlextInfraUtilitiesProjectFixtureMixin.project_spec(
                    name
                )
            }
        )

    @staticmethod
    def required_beads(
        workspace: m.Infra.WorkspaceSpec,
    ) -> m.Infra.BeadsProjectSpec:
        """Return the ledger identity the observed loader must always resolve.

        Every observed load owns a Beads identity — the loader rejects a
        spec without one — so a test asserting that identity states the
        contract here instead of reaching into the spec at each call site.
        """
        return workspace.beads

    @staticmethod
    def to_pascal(snake: str) -> str:
        """Convert a snake-case fixture name to PascalCase."""
        return "".join(part.title() for part in snake.split("_"))

    @staticmethod
    def src_module_files() -> t.StrSequence:
        """Return canonical FLEXT source-facade filenames."""
        return (
            "constants.py",
            "typings.py",
            "protocols.py",
            "models.py",
            "utilities.py",
        )

    @staticmethod
    def create_codegen_project(
        *, tmp_path: Path, name: str, pkg_name: str, files: t.StrMapping
    ) -> Path:
        """Provide the typed test helper `create_codegen_project`."""
        project = tmp_path / name
        project.mkdir()
        (project / "Makefile").touch()
        (project / "pyproject.toml").write_text(
            (f"[project]\nname='{name}'\ndependencies=['flext-core>=0.1.0']\n"),
            encoding="utf-8",
        )
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            project, name
        )
        pkg = project / "src" / pkg_name
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").touch()
        pascal_name = TestsFlextInfraUtilitiesWorkspaceFixtureMixin.to_pascal(
            pkg_name
        )
        (pkg / "typings.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import FlextTypes\n\n"
            f"class {pascal_name}Types(FlextTypes):\n    pass\n\n"
            f"t = {pascal_name}Types\n\n"
            f'__all__: list[str] = ["{pascal_name}Types", "t"]\n',
            encoding="utf-8",
        )
        (pkg / "constants.py").write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import FlextConstants\n\n"
            f"class {pascal_name}Constants(FlextConstants):\n    pass\n\n"
            f"c = {pascal_name}Constants\n\n"
            f'__all__: list[str] = ["{pascal_name}Constants", "c"]\n',
            encoding="utf-8",
        )
        for filename, content in files.items():
            (pkg / filename).write_text(content, encoding="utf-8")
        TestsFlextInfraUtilitiesGitMixin.initialize_git_repo(project)
        return project

    @staticmethod
    def create_scaffolder_test_project(
        *, tmp_path: Path, with_all_modules: bool
    ) -> Path:
        """Create a project fixture for scaffolder tests."""
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
        TestsFlextInfraUtilitiesProjectFixtureMixin.write_project_beads_config(
            project, "test-project"
        )
        pkg = project / "src" / "test_project"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").touch()
        if with_all_modules:
            for mod in TestsFlextInfraUtilitiesWorkspaceFixtureMixin.src_module_files():
                (pkg / mod).write_text(
                    f"class TestProject{mod.split('.')[0].title()}:\n    pass\n",
                    encoding="utf-8",
                )
        return project

    @staticmethod
    def create_checker_project(
        tmp_path: Path, *, project_name: str = "p1", with_src: bool = False
    ) -> tuple[FlextInfraWorkspaceChecker, Path]:
        """Provide the typed test helper `create_checker_project`."""
        checker = FlextInfraWorkspaceChecker(workspace=tmp_path)
        project_dir = TestsFlextInfraUtilitiesWorkspaceFixtureMixin.mk_project(
            tmp_path, project_name
        )
        if with_src:
            (project_dir / "src").mkdir(parents=True, exist_ok=True)
        return checker, project_dir


__all__: list[str] = ["TestsFlextInfraUtilitiesWorkspaceFixtureMixin"]
