"""Public render contract: a packaged data dir ships through exactly one route.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import tarfile
import zipfile
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, infra, m, main
from tests import t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


FIXTURE_DISTRIBUTION = "flext-packaging-fixture"
FIXTURE_DISTRIBUTION_DATA_DIR = "config"


def _rendered_target_table(root: Path, target: str) -> t.JsonMapping:
    """Read one rendered hatch build target table of the conformed project.

    Returns:
        The resulting ``t.JsonMapping``.

    """
    manifest = (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
    return u.Tests.toml_table_at(
        manifest,
        c.Infra.TOOL,
        "hatch",
        "build",
        "targets",
        target,
    )


class TestsFlextInfraCodegenPackagedDataWheel:
    """Rendered wheel and sdist targets never declare one data dir twice."""

    @staticmethod
    def _package_config_path(root: Path) -> Path:
        """Resolve the in-package data dir of the governed fixture project.

        Returns:
            The resulting ``Path``.

        """
        package_name = u.Tests.project_spec(FIXTURE_DISTRIBUTION).package_name
        return (
            root
            / c.Infra.DEFAULT_SRC_DIR
            / package_name
            / FIXTURE_DISTRIBUTION_DATA_DIR
        )

    @staticmethod
    def _prepare_runtime(root: Path) -> None:
        """Provision a physical runtime from the existing verified resolver lock."""
        _ = u.Tests.provision_runtime_environment(root)
        environment = u.Infra.runtime_environment_dir(root)
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / ".gitignore", f"/{environment.relative_to(root).as_posix()}/\n"
            ),
        )
        resolver = u.Infra.env_value("UV_PROJECT")
        tm.that(bool(resolver), eq=True)
        tm.ok(
            u.Cli.run_checked(
                ["uv", "sync", "--project", resolver, "--frozen", "--offline"],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"UV_PROJECT_ENVIRONMENT": str(environment)},
                ),
            ),
        )

    @staticmethod
    def _prepare_project(
        root: Path,
        *,
        package_config: bool,
        packaged_data_paths: tuple[str, ...] = (),
        packaged_data_excludes: tuple[str, ...] = (),
        repository_namespace_packages: tuple[str, ...] = (),
    ) -> None:
        """Materialize one governed project, optionally shipping in-package data."""
        _ = u.Tests.standalone_workspace(root, FIXTURE_DISTRIBUTION)
        TestsFlextInfraCodegenPackagedDataWheel._prepare_runtime(root)
        if package_config:
            tm.ok(
                u.Cli.atomic_write_text_file(
                    TestsFlextInfraCodegenPackagedDataWheel._package_config_path(root)
                    / "meltano.yaml",
                    "value: fixture\n",
                ),
            )
        # The generator detects the FLEXT line from the checkout's declared
        # infrastructure source; the canonical manifest routes never declare
        # one for a leaf fixture, so the pyproject declares the same typed
        # SSOT distribution the production loader resolves.
        infra_distribution = config.Infra.codegen.infra_repository.distribution
        declared_source = (
            f"{infra_distribution} @ git+{u.Tests.provider().base_url}"
            f"/{infra_distribution}.git@{u.Tests.provider_branch()}"
        )
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\n"
            f'name = "{FIXTURE_DISTRIBUTION}"\n'
            'version = "0.1.0"\n'
            'requires-python = "'
            f'{config.Infra.codegen.toolchain.python_required_version}"\n'
            f'dependencies = ["{declared_source}"]\n'
            "[build-system]\n"
            'requires = ["hatchling"]\n'
            'build-backend = "hatchling.build"\n',
            encoding="utf-8",
        )
        # The existing fixture package ships no cli module, so its manifest
        # declares none and conform renders no console script to load.
        _ = u.Tests.write_standalone_workspace_manifest(
            root,
            FIXTURE_DISTRIBUTION,
            declaration=u.Tests.StandaloneManifestDeclaration(
                cli_module=False,
                packaged_data_paths=packaged_data_paths,
                packaged_data_excludes=packaged_data_excludes,
                repository_namespace_packages=repository_namespace_packages,
            ),
        )
        u.Tests.git_bootstrap(
            root,
            (
                "remote",
                "set-url",
                c.Infra.GIT_ORIGIN,
                u.Tests.repository_ref(FIXTURE_DISTRIBUTION).url,
            ),
        )
        u.Tests.copy_tracked_mise_seeds(root)

    @staticmethod
    def _conform_self(root: Path) -> int:
        """Run codegen conform self-apply through the public CLI entrypoint.

        Returns:
            The resulting ``int``.

        """
        return main([
            c.Infra.CLI_GROUP_CODEGEN,
            "conform",
            "--root",
            str(root),
            "--scope",
            c.Infra.CodegenConformScope.SELF.value,
            "--mode",
            c.Infra.CodegenConformMode.APPLY.value,
        ])

    @staticmethod
    def _wheel_target(root: Path) -> t.JsonMapping:
        """Read the rendered wheel target of the conformed project.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        return _rendered_target_table(root, "wheel")

    @staticmethod
    def _wheel_force_include(root: Path) -> t.JsonMapping:
        """Read the rendered force-include map, empty when the table is absent.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        wheel = TestsFlextInfraCodegenPackagedDataWheel._wheel_target(root)
        return (
            u.Tests.toml_mapping(wheel["force-include"])
            if "force-include" in wheel
            else {}
        )

    @staticmethod
    def _sdist_include(root: Path) -> t.JsonList:
        """Read the rendered sdist's declared native only-include paths.

        Returns:
            The resulting ``t.JsonList``.

        """
        return u.Tests.toml_list(_rendered_target_table(root, "sdist")["only-include"])

    @staticmethod
    def _sdist_force_include(root: Path) -> t.JsonMapping:
        """Read declared source files retained unchanged by the sdist.

        Returns:
            The resulting ``t.JsonMapping``.

        """
        sdist = _rendered_target_table(root, "sdist")
        return (
            u.Tests.toml_mapping(sdist["force-include"])
            if "force-include" in sdist
            else {}
        )

    @pytest.mark.slow
    def test_declared_root_data_dir_stays_selected(self, infra_git_repo: Path) -> None:
        """A declared root directory reaches the wheel through native selection."""
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=(FIXTURE_DISTRIBUTION_DATA_DIR,),
        )

        applied = self._conform_self(infra_git_repo)

        tm.that(applied, eq=0)
        package_name = u.Tests.project_spec(FIXTURE_DISTRIBUTION).package_name
        sources = u.Tests.toml_mapping(self._wheel_target(infra_git_repo)["sources"])
        tm.that(
            sources.get(FIXTURE_DISTRIBUTION_DATA_DIR),
            eq=f"{package_name}/{FIXTURE_DISTRIBUTION_DATA_DIR}",
        )

    @pytest.mark.slow
    def test_undeclared_governance_config_stays_out_of_archives(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A governance config directory is not implicitly package data."""
        self._prepare_project(infra_git_repo, package_config=False)

        tm.that(self._conform_self(infra_git_repo), eq=0)

        tm.that(
            FIXTURE_DISTRIBUTION_DATA_DIR in self._wheel_force_include(infra_git_repo),
            eq=False,
        )
        tm.that(
            FIXTURE_DISTRIBUTION_DATA_DIR in self._sdist_include(infra_git_repo),
            eq=False,
        )

    @pytest.mark.slow
    def test_existing_infrastructure_dir_reaches_both_archives(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A project-owned IaC directory ships without a generator template row."""
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=("infra",),
        )
        infrastructure = infra_git_repo / "infra" / "ansible" / "site.yml"
        tm.ok(u.Cli.atomic_write_text_file(infrastructure, "---\n- hosts: all\n"))

        tm.that(self._conform_self(infra_git_repo), eq=0)

        package_name = u.Tests.project_spec(FIXTURE_DISTRIBUTION).package_name
        tm.that(
            u.Tests.toml_mapping(self._wheel_target(infra_git_repo)["sources"]).get(
                "infra",
            ),
            eq=f"{package_name}/infra",
        )
        tm.ok("infra" in self._sdist_include(infra_git_repo))

    @pytest.mark.slow
    def test_repository_namespace_retains_its_import_path(
        self,
        infra_git_repo: Path,
    ) -> None:
        """A declared root namespace ships at the same import path in both formats."""
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            repository_namespace_packages=("infra",),
        )
        source = infra_git_repo / "infra" / "pulumi" / "__main__.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "VALUE = 'fixture'\n"))

        tm.that(self._conform_self(infra_git_repo), eq=0)

        wheel = self._wheel_target(infra_git_repo)
        tm.ok("infra" in u.Tests.toml_list(wheel["only-include"]))
        tm.that(u.Tests.toml_mapping(wheel["sources"]).get("infra"), eq="infra")
        tm.ok("infra" in self._sdist_include(infra_git_repo))
        output = infra_git_repo.parent / "namespace-artifacts"
        wheel_dir = output / "wheel"
        sdist_dir = output / "sdist"
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "build",
                    "--project",
                    str(infra_git_repo),
                    "--wheel",
                    "--out-dir",
                    str(wheel_dir),
                ],
                cwd=infra_git_repo,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "build",
                    "--project",
                    str(infra_git_repo),
                    "--sdist",
                    "--out-dir",
                    str(sdist_dir),
                ],
                cwd=infra_git_repo,
            ),
        )
        with zipfile.ZipFile(next(wheel_dir.glob("*.whl"))) as archive:
            tm.that(archive.read("infra/pulumi/__main__.py"), eq=source.read_bytes())
        with tarfile.open(next(sdist_dir.glob("*.tar.gz"))) as archive:
            member = next(
                item
                for item in archive.getmembers()
                if item.name.endswith("/infra/pulumi/__main__.py")
            )
            stream = tm.not_none(archive.extractfile(member))
            with stream:
                tm.that(stream.read(), eq=source.read_bytes())

    @pytest.mark.slow
    def test_undeclared_infrastructure_dir_stays_out_of_archives(
        self,
        infra_git_repo: Path,
    ) -> None:
        """An unrelated root directory cannot enter a package by discovery."""
        self._prepare_project(infra_git_repo, package_config=False)
        infrastructure = infra_git_repo / "infra" / "ansible" / "site.yml"
        tm.ok(u.Cli.atomic_write_text_file(infrastructure, "---\n- hosts: all\n"))

        tm.that(self._conform_self(infra_git_repo), eq=0)

        tm.fail("infra" in self._wheel_force_include(infra_git_repo))
        tm.fail("infra" in self._sdist_include(infra_git_repo))

    @pytest.mark.slow
    def test_in_package_defaults_ship_once_in_standard_and_editable_manifest(
        self,
        infra_git_repo: Path,
    ) -> None:
        """Hatch forces the package source itself, never a competing root copy."""
        self._prepare_project(infra_git_repo, package_config=True)
        tm.ok(self._package_config_path(infra_git_repo).is_dir())

        applied = self._conform_self(infra_git_repo)

        tm.that(applied, eq=0)
        force_include = self._wheel_force_include(infra_git_repo)
        tm.fail(FIXTURE_DISTRIBUTION_DATA_DIR in force_include)
        tm.that(
            FIXTURE_DISTRIBUTION_DATA_DIR in self._sdist_include(infra_git_repo),
            eq=False,
        )
        # The package remains selected; defaults have one forced archive route.
        package_name = u.Tests.project_spec(FIXTURE_DISTRIBUTION).package_name
        config_source = self._package_config_path(infra_git_repo)
        destination = f"{package_name}/{c.CONFIG_DIR_NAME}"
        tm.that(
            force_include[config_source.relative_to(infra_git_repo).as_posix()],
            eq=destination,
        )
        wheel = self._wheel_target(infra_git_repo)
        tm.that(
            f"{c.Infra.DEFAULT_SRC_DIR}/{package_name}"
            in u.Tests.toml_list(wheel["only-include"]),
            eq=True,
        )
        output = infra_git_repo.parent / "package-default-artifacts"
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "build",
                    "--project",
                    str(infra_git_repo),
                    "--wheel",
                    "--out-dir",
                    str(output),
                ],
                cwd=infra_git_repo,
            ),
        )
        with zipfile.ZipFile(next(output.glob("*.whl"))) as archive:
            for source in config_source.rglob("*.yaml"):
                relative = source.relative_to(config_source).as_posix()
                installed = f"{destination}/{relative}"
                tm.that(archive.namelist().count(installed), eq=1)
                tm.that(archive.read(installed), eq=source.read_bytes())

    @pytest.mark.slow
    def test_declared_file_keeps_sibling_governance_out(
        self,
        infra_git_repo: Path,
    ) -> None:
        """One catalog file ships without its governance siblings."""
        catalog = "config/deployment.yaml"
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=(catalog,),
        )
        tm.ok(u.Cli.atomic_write_text_file(infra_git_repo / catalog, "profiles: {}\n"))
        tm.that(self._conform_self(infra_git_repo), eq=0)
        package_name = u.Tests.project_spec(FIXTURE_DISTRIBUTION).package_name
        tm.that(
            self._wheel_force_include(infra_git_repo).get(catalog),
            eq=f"{package_name}/{catalog}",
        )
        # A declared data file ships through the sdist force-include, never
        # by widening the source include to its whole directory.
        tm.that(
            self._sdist_force_include(infra_git_repo).get(catalog),
            eq=catalog,
        )
        tm.fail("config" in self._sdist_include(infra_git_repo))

    @pytest.mark.slow
    @pytest.mark.parametrize(
        "declarations",
        [
            ("../outside",),
            ("/absolute",),
            ("config", "config"),
            ("config", "config/workspace.yaml"),
        ],
    )
    def test_invalid_declaration_fails_before_effects(
        self,
        infra_git_repo: Path,
        declarations: tuple[str, ...],
    ) -> None:
        """Escaping and overlapping archive inputs cannot mutate the manifest."""
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=declarations,
        )
        before = (infra_git_repo / c.PYPROJECT_FILENAME).read_bytes()
        with pytest.raises(ValueError, match="packaged data"):
            self._conform_self(infra_git_repo)
        tm.that((infra_git_repo / c.PYPROJECT_FILENAME).read_bytes(), eq=before)

    @pytest.mark.slow
    def test_missing_data_fails_before_effects(self, infra_git_repo: Path) -> None:
        """A missing declared file cannot silently disappear from distributions."""
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=("absent/catalog.yaml",),
        )
        before = (infra_git_repo / c.PYPROJECT_FILENAME).read_bytes()
        with pytest.raises(FileNotFoundError, match="packaged data"):
            self._conform_self(infra_git_repo)
        tm.that((infra_git_repo / c.PYPROJECT_FILENAME).read_bytes(), eq=before)

    @pytest.mark.slow
    def test_declared_collision_fails_before_effects(
        self,
        infra_git_repo: Path,
    ) -> None:
        """Distinct roots cannot claim the same wheel destination."""
        self._prepare_project(
            infra_git_repo,
            package_config=True,
            packaged_data_paths=("config",),
        )
        before = (infra_git_repo / c.PYPROJECT_FILENAME).read_bytes()
        with pytest.raises(ValueError, match="collides"):
            self._conform_self(infra_git_repo)
        tm.that((infra_git_repo / c.PYPROJECT_FILENAME).read_bytes(), eq=before)

    @pytest.mark.slow
    @pytest.mark.parametrize(
        "link_kind",
        ["external", "transitive", "cycle", "dangling"],
    )
    def test_data_links_are_validated_transitively(
        self,
        infra_git_repo: Path,
        link_kind: str,
    ) -> None:
        """Hatch cannot traverse a link the preflight has not authenticated."""
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=("infra",),
        )
        data = infra_git_repo / "infra"
        data.mkdir()
        external = infra_git_repo.parent / "outside-data"
        external.write_text("outside", encoding="utf-8")
        if link_kind == "transitive":
            shared = infra_git_repo / "shared"
            shared.mkdir()
            (shared / "external").symlink_to(external)
            (data / "shared").symlink_to(shared, target_is_directory=True)
        elif link_kind == "cycle":
            (data / "cycle").symlink_to(data, target_is_directory=True)
        elif link_kind == "dangling":
            (data / "missing").symlink_to(infra_git_repo / "absent")
        else:
            (data / "external").symlink_to(external)
        before = (infra_git_repo / c.PYPROJECT_FILENAME).read_bytes()
        with pytest.raises((ValueError, FileNotFoundError)):
            self._conform_self(infra_git_repo)
        tm.that((infra_git_repo / c.PYPROJECT_FILENAME).read_bytes(), eq=before)

    @pytest.mark.slow
    def test_real_archives_preserve_data_selection(self, infra_git_repo: Path) -> None:
        """Direct wheel, sdist and rebuilt wheel carry the same selected bytes."""
        catalog = "config/deployment.yaml"
        asset = "infra/ansible/site.yml"
        self._prepare_project(
            infra_git_repo,
            package_config=False,
            packaged_data_paths=(catalog, "infra"),
        )
        tm.ok(u.Cli.atomic_write_text_file(infra_git_repo / catalog, "profiles: {}\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(infra_git_repo / asset, "---\n- hosts: all\n"),
        )
        tm.that(self._conform_self(infra_git_repo), eq=0)
        ignored = "infra/state.json"
        declaration = tm.ok(
            u.Infra.load_repository_declaration_inputs(infra_git_repo),
        ).spec
        project = tm.not_none(declaration.project).model_copy(
            update={"packaged_data_excludes": (ignored,)},
        )
        updated = declaration.model_copy(update={"project": project})
        tm.ok(
            u.Cli.yaml_dump(
                infra_git_repo / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": updated.model_dump(
                                mode="json", exclude_unset=True
                            )
                        }
                    }
                },
            ),
        )
        tm.ok(u.Cli.atomic_write_text_file(infra_git_repo / catalog, "profiles: {}\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(infra_git_repo / asset, "---\n- hosts: all\n"),
        )
        tm.ok(u.Cli.atomic_write_text_file(infra_git_repo / ignored, "private state\n"))
        tm.that(self._conform_self(infra_git_repo), eq=0)
        with (infra_git_repo / ".gitignore").open("a", encoding="utf-8") as stream:
            stream.write(f"\n/{ignored}\n/{catalog}\n")
        output = infra_git_repo.parent / "artifacts"
        direct = output / "direct"
        source = output / "source"
        rebuilt = output / "rebuilt"
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "build",
                    "--project",
                    str(infra_git_repo),
                    "--wheel",
                    "--out-dir",
                    str(direct),
                ],
                cwd=infra_git_repo,
            ),
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "build",
                    "--project",
                    str(infra_git_repo),
                    "--sdist",
                    "--out-dir",
                    str(source),
                ],
                cwd=infra_git_repo,
            ),
        )
        sdist = next(source.glob("*.tar.gz"))
        tm.ok(
            u.Cli.run_checked(
                ["uv", "build", str(sdist), "--wheel", "--out-dir", str(rebuilt)],
                cwd=infra_git_repo,
            ),
        )
        package_name = u.Tests.project_spec(FIXTURE_DISTRIBUTION).package_name
        expected = {
            catalog: (infra_git_repo / catalog).read_bytes(),
            asset: (infra_git_repo / asset).read_bytes(),
        }
        for directory in (direct, rebuilt):
            with zipfile.ZipFile(next(directory.glob("*.whl"))) as archive:
                for name, content in expected.items():
                    tm.that(archive.read(f"{package_name}/{name}"), eq=content)
                tm.fail(f"{package_name}/{ignored}" in archive.namelist())
                tm.that(
                    f"{package_name}/config/workspace.yaml" in archive.namelist(),
                    eq=False,
                )
        with tarfile.open(sdist) as archive:
            members = {
                member.name.partition("/")[2]: member
                for member in archive.getmembers()
                if member.isfile()
            }
            for name, content in expected.items():
                stream = tm.not_none(archive.extractfile(members[name]))
                with stream:
                    tm.that(stream.read(), eq=content)
            tm.fail(ignored in members)
            tm.fail("config/workspace.yaml" in members)

    @pytest.mark.slow
    def test_scaffold_validates_data_against_planned_files(
        self,
        tmp_path: Path,
    ) -> None:
        """A declared generated manifest is accepted before scaffold effects."""
        root = tmp_path / "scaffold-data"
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        repository = u.Tests.repository_ref(
            "scaffold-data",
            role=c.Infra.MakeProfile.STANDALONE,
        )
        package_name = "declared_scaffold_package"
        declared_file = next(
            entry.destination
            for entry in config.Infra.codegen.templates.entries
            if entry.destination.startswith(f"{c.CONFIG_DIR_NAME}/")
            and "{" not in entry.destination
            and c.Infra.MakeProfile.STANDALONE in entry.profiles
            and entry.delegate == c.Infra.TemplateDelegate.RENDER
            and not entry.requires_beads
            and not entry.requires_release_protocol
        )
        project = u.Tests.project_spec(repository.name).model_copy(
            update={
                "package_name": package_name,
                "class_stem": u.derive_class_stem(package_name),
                "packaged_data_paths": (declared_file,),
            },
        )
        workspace = u.Tests.workspace_spec(repository, project=project)
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        root.mkdir()
        _ = u.Tests.initialize_git_repo(root, origin_url=project.homepage)
        self._prepare_runtime(root)
        tm.fail((root / c.PYPROJECT_FILENAME).exists())
        tm.fail((root / declared_file).exists())
        tm.ok(infra.codegen_conform(request, workspace))
        tm.ok((root / declared_file).is_file())
        tm.that(
            self._wheel_force_include(root).get(declared_file),
            eq=f"{project.package_name}/{declared_file}",
        )
        wheel_dir = tmp_path / "scaffold-artifacts"
        tm.ok(
            u.Cli.run_checked(
                [
                    "uv",
                    "build",
                    "--project",
                    str(root),
                    "--wheel",
                    "--out-dir",
                    str(wheel_dir),
                ],
                cwd=root,
            ),
        )
        wheel = next(wheel_dir.glob("*.whl"))
        manifest = root / declared_file
        with zipfile.ZipFile(wheel) as archive:
            tm.that(
                archive.read(f"{project.package_name}/{declared_file}"),
                eq=manifest.read_bytes(),
            )
        consumer_root = tmp_path / "scaffold-consumer"
        consumer_root.mkdir()
        consumer = tm.ok(
            u.Cli.run_raw(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys\n"
                        "from pathlib import Path\n"
                        "from importlib.resources import files\n"
                        f"sys.path.insert(0, {str(wheel)!r})\n"
                        f"import {project.package_name} as package\n"
                        "payload = files(package).joinpath("
                        f"{declared_file!r}).read_bytes()\n"
                        f"print(payload == Path({str(manifest)!r}).read_bytes())\n"
                    ),
                ],
                cwd=consumer_root,
            ),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True, msg=consumer.stderr)
        tm.that(consumer.stdout.strip(), eq="True")
