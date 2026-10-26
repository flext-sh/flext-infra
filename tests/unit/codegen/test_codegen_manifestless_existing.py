"""Public regression coverage for manifestless existing repositories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, t, tm, u


# Exemplar: conform materializes a full managed tree on disk, so the render
# itself dominates the runtime. The class carries the config-owned slow budget
# (Infra.tooling.tools.pytest.slow-timeout-seconds) instead of a hardcoded
# ceiling, so a real hang still aborts at the declared wall.
@pytest.mark.slow
class TestsFlextInfraCodegenManifestlessExisting:
    """Tests for ``FlextInfraCodegenManifestlessExisting``."""

    @staticmethod
    def seed_manifest_pyproject(root: Path) -> str:
        """Seed the root manifest with one custom dev-group requirement.

        Returns:
            The written manifest source text.

        """
        pyproject_source = tm.ok(
            u.Cli.files_read_text(Path.cwd() / c.PYPROJECT_FILENAME)
        )
        # An external CUSTOM requirement: a FLEXT-family name without a direct
        # Git source is a source-less internal dependency, which conform
        # refuses loudly by design.
        custom_dev_requirement = 'custom-dev-tool>=0.1; python_version < "3.0"'
        pyproject_payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Tests.toml_payload(pyproject_source),
        )
        dev_groups = u.Cli.toml_mapping_ensure_table(
            pyproject_payload,
            c.Infra.DEPENDENCY_GROUPS,
        )
        dev_groups[str(c.Infra.DEV)] = [
            *u.Cli.json_as_sequence(dev_groups.get(str(c.Infra.DEV))),
            custom_dev_requirement,
        ]
        pyproject_source = u.Cli.toml_dumps(
            u.Cli.toml_document_from_mapping(pyproject_payload),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(root / c.PYPROJECT_FILENAME, pyproject_source)
        )
        package_name = u.Infra.project_package_name(Path.cwd())
        package_init = root / c.Infra.DEFAULT_SRC_DIR / package_name / "__init__.py"
        package_init.parent.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        return pyproject_source

    @staticmethod
    def seed_declared_entry_targets(root: Path, pyproject_source: str) -> None:
        """Stub every declared script and entry-point target in the tree.

        The copied manifest declares scripts and entry points; conform's
        fresh-import gate loads each one, so the seeded tree carries every
        declared target (module and attribute) inside its own package —
        never a copy of the whole production package.
        """
        manifest = tm.not_none(u.Cli.toml_mapping_from_text(pyproject_source))
        project_table = u.Cli.json_as_mapping(
            u.Cli.toml_mapping_child(manifest, "project"),
        )
        entry_groups = u.Cli.json_as_mapping(
            u.Cli.toml_mapping_child(project_table, "entry-points"),
        )
        declared_groups = (
            u.Cli.json_as_mapping(u.Cli.toml_mapping_child(project_table, "scripts")),
            u.Cli.json_as_mapping(
                u.Cli.toml_mapping_child(project_table, "gui-scripts"),
            ),
            *(u.Cli.json_as_mapping(group) for group in entry_groups.values()),
        )
        # A dotted target (``Class.member``) resolves through attribute access,
        # so the seeded class carries each declared member.
        targets: t.MutableMappingKV[Path, t.MutableMappingKV[str, set[str]]] = {}
        for entries in declared_groups:
            for target in entries.values():
                module_name, _, attribute = str(target).partition(":")
                module_path = (
                    root / c.Infra.DEFAULT_SRC_DIR / Path(*module_name.split("."))
                ).with_suffix(".py")
                owner, _, member = attribute.partition(".")
                members = targets.setdefault(module_path, {}).setdefault(owner, set())
                if member:
                    members.add(member)
        for module_path, owners in targets.items():
            tm.ok(
                u.Cli.atomic_write_text_file(
                    module_path,
                    "".join(
                        f"class {owner}:\n"
                        + (
                            "".join(
                                f"    {member} = None\n" for member in sorted(members)
                            )
                            or "    pass\n"
                        )
                        + "\n\n"
                        for owner, members in sorted(owners.items())
                    ),
                ),
            )

    @staticmethod
    def seed_existing_tree(root: Path, seeded: t.StrMapping) -> None:
        """Copy the externally managed extras and commit the seeded tree."""
        vscode_settings = root / ".vscode" / "settings.json"
        vscode_settings.parent.mkdir()
        tm.ok(
            u.Cli.atomic_write_text_file(
                vscode_settings,
                tm.ok(u.Cli.files_read_text(Path.cwd() / ".vscode" / "settings.json")),
            ),
        )
        for relative, content in seeded.items():
            tm.ok(u.Cli.atomic_write_text_file(root / relative, content))
        u.Tests.write_project_beads_config(root, config.Infra.name)
        tm.ok(u.Cli.run_checked(["git", "add", "-A"], cwd=root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "--no-verify", "-m", "Seed manifestless tree"],
                cwd=root,
            ),
        )

    @staticmethod
    def test_existing_root_uses_pep621_metadata_for_managed_artifacts(
        infra_git_repo: Path,
    ) -> None:
        """Test existing root uses pep621 metadata for managed artifacts."""
        root = infra_git_repo
        repository = u.Tests.repository_ref(config.Infra.name)
        # Why: LICENSE has no generator and is genuinely exists_or_absent.
        # README.md is also externally_managed/exists_or_absent for conform's
        # managed-file surface, but `execute_request` runs the full apply
        # pipeline including docs generation, which regenerates README.md
        # from live project metadata regardless of prior content — so only
        # LICENSE is proven byte-preserved here.
        preserved = {"LICENSE": "existing license\n"}
        seeded = {**preserved, "README.md": "# Existing repository\n"}
        manifestless = TestsFlextInfraCodegenManifestlessExisting
        pyproject_source = manifestless.seed_manifest_pyproject(root)
        manifestless.seed_declared_entry_targets(root, pyproject_source)
        manifestless.seed_existing_tree(root, seeded)

        derived = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        tm.that(derived.repository.name, eq=repository.name)
        tm.that(derived.repository.distribution, eq=repository.distribution)
        tm.that(derived.repository.path, eq=Path())
        tm.that(derived.project, eq=None)
        # Apply is complete or nothing: a partial surface is a check-only view.
        request = u.Tests.conform_request(
            root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(request))
        initial_plan = tm.ok(
            FlextInfraCodegenConform.Generate(repository_root=root).plan(request),
        )
        plans = {
            file.path.relative_to(root).as_posix(): file for file in initial_plan.files
        }
        tm.that(
            sum(
                file.path == root / c.PYPROJECT_FILENAME for file in initial_plan.files
            ),
            eq=1,
        )
        tm.fail(u.Infra.codegen_file_requires_effect(plans[c.PYPROJECT_FILENAME]))

        # Why: .env.example carries no managed_files entry, so it is never
        # planned for an existing (manifestless) checkout.
        tm.fail(".env.example" in plans)
        tm.fail((root / ".env.example").exists())
        # Why: LICENSE and README.md are not managed_files entries — conform
        # never plans them, so the preserved bytes are proven by direct read.
        for relative, content in preserved.items():
            tm.fail(relative in plans)
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        # Why: the real PEP 621-derived ProjectSpec (authors + upstream) now
        # resolves the tooling context correctly on the first pass, so these
        # managed files already converge after one apply — the fabricated
        # synthetic spec previously left them requiring a second pass.
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.fail(u.Infra.codegen_file_requires_effect(plans[required]))

        tm.ok(infra.codegen_conform(request))
        tm.fail((root / ".env.example").exists())
        for relative, content in preserved.items():
            tm.that((root / relative).read_text(encoding="utf-8"), eq=content)
        tm.ok((root / "README.md").is_file())
        for required in ("Makefile", ".mise.toml", ".python-version", ".gitignore"):
            tm.ok((root / required).is_file())
        fixed_point = FlextInfraCodegenConform.Generate(repository_root=root).plan(
            request.model_copy(update={"mode": c.Infra.CodegenConformMode.CHECK}),
        )
        verified = tm.ok(fixed_point)
        tm.that(
            tuple(
                file.path
                for file in verified.files
                if u.Infra.codegen_file_requires_effect(file)
            ),
            eq=(),
        )

    @staticmethod
    def seed_root_distribution(tmp_path: Path, license_id: str) -> Path:
        """Seed a manifestless root declaring ``license_id`` in its PEP 621 manifest.

        Since 208716f4f the checkout must declare the infrastructure line it
        consumes; a manifestless root declares it the way a real member does,
        through its development group's direct Git source.

        Returns:
            The seeded repository root.

        """
        base = config.Infra.codegen.scaffold.project.config_bases[-1]
        distribution = base.distribution
        # Every internal development dependency the SSOT requires carries its
        # own direct Git source, exactly as a real standalone member declares.
        internal_dev = tuple(
            u.Tests.repository_ref(name)
            for name in dict.fromkeys(
                u.Infra.dep_name(requirement)
                for requirement in (
                    config.Infra.codegen.infra_repository.distribution,
                    *config.Infra.codegen.scaffold.project.dev,
                    *config.Infra.codegen.scaffold.project.required_flext_dev,
                )
            )
            if name is not None and name.startswith("flext-")
        )
        dev_group = ", ".join(
            f'"{ref.distribution} @ git+{ref.url}@{u.Tests.provider_branch()}"'
            for ref in internal_dev
        )
        u.Tests.copy_tracked_mise_seeds(tmp_path)
        root = tmp_path / distribution
        package = root / c.Infra.DEFAULT_SRC_DIR / base.module
        package.mkdir(parents=True)
        tm.ok(u.Cli.atomic_write_text_file(package / "__init__.py", ""))
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / c.PYPROJECT_FILENAME,
                f'[project]\nname = "{distribution}"\nversion = "0.12.0.dev0"\n'
                f'description = "{distribution} root fixture"\n'
                f"requires-python = "
                f'"{config.Infra.codegen.toolchain.python_required_version}"\n'
                'authors = [{name = "FLEXT Team", email = "team@flext.dev"}]\n'
                f'license = "{license_id}"\n'
                "dependencies = []\n"
                "\n[dependency-groups]\n"
                f"dev = [{dev_group}]\n",
            ),
        )
        u.Tests.write_project_beads_config(root, distribution)
        u.Tests.initialize_git_repo(
            root,
            origin_url=u.Tests.repository_ref(distribution).url,
        )
        return root

    @staticmethod
    def plan_surface(
        root: Path,
        what: c.Infra.CodegenConformSurface,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Plan the ``what`` surface of ``root`` in check mode.

        Returns:
            The conform plan result.

        """
        return FlextInfraCodegenConform.Generate(repository_root=root).plan(
            u.Tests.conform_request(
                root,
                what=what,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            ),
        )

    @staticmethod
    def test_root_distribution_preserves_its_runtime_requirements(
        tmp_path: Path,
    ) -> None:
        """The tree's root declares no flext runtime dependency and still conforms.

        Since 208716f4f the checkout must declare the infrastructure line it
        consumes; a manifestless root declares it the way a real member does,
        through its development group's direct Git source.
        """
        manifestless = TestsFlextInfraCodegenManifestlessExisting
        base = config.Infra.codegen.scaffold.project.config_bases[-1]
        root = manifestless.seed_root_distribution(
            tmp_path,
            u.Tests.project_spec(base.distribution).license,
        )

        plan = tm.ok(
            manifestless.plan_surface(root, c.Infra.CodegenConformSurface.PYPROJECT),
        )
        rendered = u.Tests.codegen_file_text(
            next(file for file in plan.files if file.path.name == c.PYPROJECT_FILENAME),
        )
        tm.that(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
            eq=(),
        )

    @staticmethod
    @pytest.mark.parametrize(
        "license_id",
        config.Infra.codegen.scaffold.project.supported_licenses,
    )
    def test_undeclared_root_renders_the_license_its_manifest_declares(
        tmp_path: Path,
        license_id: str,
    ) -> None:
        """An undeclared tree's derived identity carries its own PEP 621 license."""
        manifestless = TestsFlextInfraCodegenManifestlessExisting
        root = manifestless.seed_root_distribution(tmp_path, license_id)

        plan = tm.ok(
            manifestless.plan_surface(root, c.Infra.CodegenConformSurface.ALL),
        )
        rendered = u.Tests.codegen_file_text(
            next(file for file in plan.files if file.path.name == c.PYPROJECT_FILENAME),
        )
        tm.that(
            u.Cli.json_walk_path(
                u.Tests.toml_payload(rendered),
                (c.Infra.PROJECT, c.Infra.LICENSE),
            ),
            eq=license_id,
        )

    @staticmethod
    def test_undeclared_root_with_an_unsupported_license_fails_loud(
        tmp_path: Path,
    ) -> None:
        """No supported license replaces the one an undeclared tree declares."""
        unsupported = "LicenseRef-Unsupported"
        root = TestsFlextInfraCodegenManifestlessExisting.seed_root_distribution(
            tmp_path,
            unsupported,
        )

        plan = tm.ok(
            TestsFlextInfraCodegenManifestlessExisting.plan_surface(
                root,
                c.Infra.CodegenConformSurface.ALL,
            ),
        )

        tm.that(plan.files, empty=True)
        tm.that(
            "\n".join(issue.message for issue in plan.issues),
            has=f"unsupported scaffold license: {unsupported}",
        )
