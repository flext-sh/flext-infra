"""Observe bootstrap coverage through real Git members and installed editables.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraMiseArtifactsVerification
from flext_infra.workspace import FlextInfraBindingService
from tests import c, m, p, tm, u


class TestsMakeBootstrapPublication:
    """Bootstrap preserves operation coverage across actual member transactions."""

    @staticmethod
    def workspace(tmp_path: Path) -> tuple[Path, tuple[Path, ...]]:
        root = tmp_path / "workspace"
        identity = u.Tests.BeadsIdentity(
            workspace="bootstrap-workspace",
            database="bootstrap_workspace",
            issue_prefix="bootstrap",
        )
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "bootstrap-workspace",
            beads=identity,
        )
        members = tuple(root / name for name in ("bootstrap-one", "bootstrap-two"))
        for member in members:
            u.Tests.WorktreeFixture.initialize_governed_project(
                member,
                member.name,
                beads=identity,
            )
            pyproject = member / c.PYPROJECT_FILENAME
            pyproject.write_text(
                pyproject.read_text(encoding=c.DEFAULT_ENCODING)
                + '\n[build-system]\nrequires = ["setuptools"]\n'
                'build-backend = "setuptools.build_meta"\n'
                '[tool.setuptools.packages.find]\nwhere = ["src"]\n',
                encoding=c.DEFAULT_ENCODING,
            )
            u.Tests.commit_git_changes(member, "declare real editable package")
            u.Tests.WorktreeFixture.attach_submodule(
                root,
                member,
                distribution=member.name,
                relative_path=member.name,
            )
        tm.ok(u.Tests.create_python_environment(root))
        uv = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root))
        tm.ok(
            u.Cli.run_checked(
                (
                    str(uv),
                    "pip",
                    "install",
                    "--no-deps",
                    "--python",
                    str(u.Infra.runtime_python(root)),
                    *(
                        item
                        for member in members
                        for item in ("--editable", str(member))
                    ),
                ),
                cwd=root,
            ),
        )
        return root, members

    @staticmethod
    def _receipt(root: Path) -> m.Infra.CodegenPhaseOutcome:
        return m.Infra.CodegenPhaseOutcome.model_validate_json(
            (
                root
                / FlextInfraMiseArtifactsVerification.publication_receipt(
                    c.Infra.CodegenConformSurface.MAKEFILE,
                )
            ).read_bytes(),
        )

    @staticmethod
    def _run(
        root: Path,
        *,
        check_only: bool = False,
        hosted: bool = False,
    ) -> p.Cli.CommandOutput:
        """Run the real CLI with an explicit native topology and gate partition.

        Returns:
            The completed CLI command outcome.

        """
        policy = config.Infra.codegen.make.uv_resolution
        ci = config.Infra.codegen.make.ci
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    c.Infra.CLI_GROUP_CODEGEN,
                    "init",
                    "--repository-root",
                    str(root),
                    *(("--check-only",) if check_only else ()),
                ),
                cwd=root,
                env={
                    policy.hosted_variable: policy.hosted_value if hosted else "",
                    **({} if hosted else {ci.variable: ci.value}),
                },
                remove_env_keys=(ci.variable,) if hosted else (),
            ),
        )
        u.Cli.emit_raw(outcome.stdout)
        u.Cli.emit_raw(outcome.stderr)
        return outcome

    def test_workspace_bootstrap_keeps_every_actual_root_checkable(
        self,
        tmp_path: Path,
    ) -> None:
        """Every requested target publishes its own independent bootstrap receipt."""
        root, members = self.workspace(tmp_path)

        for path in (root, *members):
            tm.that(u.Cli.process_succeeded(self._run(path).outcome), eq=True)
            receipt = self._receipt(path)
            tm.that(receipt.scope_roots, eq=(path,))
            tm.that(receipt.surface, eq=c.Infra.CodegenConformSurface.MAKEFILE)
            tm.that(receipt.scope, eq=c.Infra.CodegenConformScope.SELF)
            tm.that(receipt.written_files, eq=(path / c.Infra.MAKEFILE_FILENAME,))
            tm.that(
                u.Cli.process_succeeded(self._run(path, check_only=True).outcome),
                eq=True,
            )
            tm.ok(
                infra.codegen_conform(
                    u.Tests.conform_request(
                        path,
                        what=c.Infra.CodegenConformSurface.MAKEFILE,
                        scope=c.Infra.CodegenConformScope.SELF,
                        mode=c.Infra.CodegenConformMode.CHECK,
                    ),
                ),
            )
        tm.that(
            infra.codegen_conform(
                u.Tests.conform_request(
                    root,
                    what=c.Infra.CodegenConformSurface.ALL,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.CHECK,
                ),
            ).failure,
            eq=True,
        )

    def test_native_metadata_inventory_separates_installs_from_editable_sources(
        self,
        tmp_path: Path,
    ) -> None:
        """The elected Python resolves editable imports outside its install dirs."""
        root, members = self.workspace(tmp_path)
        package = u.Infra.project_package_name(members[0])
        facts = tm.ok(
            FlextInfraBindingService.consumer_package_environment(
                consumer_root=root,
                python=u.Infra.runtime_python(root),
                packages=(package,),
            ),
        )
        installed = u.installed_distributions(
            name=members[0].name,
            path=tuple(str(path) for path in facts.metadata_paths),
        )
        import_inventory = u.installed_distributions(
            name=members[0].name,
            path=tuple(str(path) for path in facts.import_paths),
        )
        u.Cli.emit_raw(
            f"native prefix={facts.prefix} install_metadata_count={len(installed)} "
            f"import_path_metadata_count={len(import_inventory)}\n",
        )
        for distribution in import_inventory:
            u.Cli.emit_raw(
                "native metadata location="
                f"{Path(str(distribution.locate_file(''))).resolve()}\n",
            )

        tm.that(len(installed), eq=1)
        tm.that(
            Path(str(installed[0].locate_file("")))
            .resolve()
            .is_relative_to(facts.prefix),
            eq=True,
        )
        tm.that(len(facts.package_directories[package]), eq=1)
        tm.that(
            facts.package_directories[package][0].resolve().is_relative_to(members[0]),
            eq=True,
        )

    def test_workspace_bootstrap_rejects_duplicate_installed_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """A second actual installed metadata directory remains a duplicate."""
        root, members = self.workspace(tmp_path)
        facts = tm.ok(
            FlextInfraBindingService.consumer_package_environment(
                consumer_root=root,
                python=u.Infra.runtime_python(root),
                packages=(u.Infra.project_package_name(members[0]),),
            ),
        )
        installed = u.installed_distributions(
            name=members[0].name,
            path=tuple(str(path) for path in facts.metadata_paths),
        )
        tm.that(len(installed), eq=1)
        metadata = next(
            item
            for item in tm.not_none(installed[0].files)
            if item.name == "METADATA" and item.parent.name.endswith(".dist-info")
        )
        directory = Path(str(installed[0].locate_file(metadata))).parent
        duplicate = directory.with_name(
            directory.name.removesuffix(".dist-info") + "-duplicate.dist-info",
        )
        shutil.copytree(directory, duplicate)

        result = self._run(root)

        tm.that(result.outcome.raw_return_code != 0, eq=True)
        tm.that(result.stderr + result.stdout, has="expected=1 actual=2")

    def test_workspace_bootstrap_rejects_a_foreign_metadata_prefix(
        self,
        tmp_path: Path,
    ) -> None:
        """Metadata directory links cannot borrow an external installation."""
        root, members = self.workspace(tmp_path)
        facts = tm.ok(
            FlextInfraBindingService.consumer_package_environment(
                consumer_root=root,
                python=u.Infra.runtime_python(root),
                packages=(u.Infra.project_package_name(members[0]),),
            ),
        )
        directory = facts.metadata_paths[0]
        foreign = tmp_path / "foreign-install-directory"
        directory.rename(foreign)
        directory.symlink_to(foreign, target_is_directory=True)

        result = self._run(root)

        tm.that(result.outcome.raw_return_code != 0, eq=True)
        tm.that(result.stderr + result.stdout, has="outside the elected environment")

    def test_member_failure_cannot_publish_completed_workspace_coverage(
        self,
        tmp_path: Path,
    ) -> None:
        """A failed member request cannot overwrite another target's receipt."""
        root, members = self.workspace(tmp_path)
        tm.that(u.Cli.process_succeeded(self._run(root).outcome), eq=True)
        receipt_path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.MAKEFILE,
        )
        root_before = receipt_path.read_bytes()
        foreign = members[-1] / "unowned.mk"
        foreign.write_text("# authored fixture\n", encoding=c.DEFAULT_ENCODING)
        target = members[-1] / c.Infra.MAKEFILE_FILENAME
        target.symlink_to(foreign)

        result = self._run(members[-1])
        tm.that(result.outcome.raw_return_code != 0, eq=True)
        tm.that(result.stderr + result.stdout, has=str(target))
        tm.that(receipt_path.read_bytes(), eq=root_before)

    def test_workspace_bootstrap_rejects_an_editable_from_another_checkout(
        self,
        tmp_path: Path,
    ) -> None:
        """The elected environment cannot lend a foreign member source."""
        root, members = self.workspace(tmp_path)
        foreign = tmp_path / "foreign-member"
        tm.ok(
            u.Cli.run_checked(
                (c.Infra.GIT, "clone", str(members[0]), str(foreign)),
                cwd=root,
            ),
        )
        uv = tm.ok(u.Infra.managed_mise_binary(c.Infra.UV, root))
        tm.ok(
            u.Cli.run_checked(
                (
                    str(uv),
                    "pip",
                    "install",
                    "--no-deps",
                    "--reinstall",
                    "--python",
                    str(u.Infra.runtime_python(root)),
                    "--editable",
                    str(foreign),
                ),
                cwd=root,
            ),
        )

        result = self._run(root)

        tm.that(result.outcome.raw_return_code != 0, eq=True)
        tm.that(result.stderr + result.stdout, has="direct_url mismatch")

    @pytest.mark.parametrize("hosted", [False, True])
    def test_hosted_election_is_independent_of_the_gate_partition(
        self,
        tmp_path: Path,
        hosted: bool,
    ) -> None:
        """Hosted init needs no member checkout, even when CI's gate token is absent."""
        root, members = self.workspace(tmp_path)
        if hosted:
            for member in members:
                shutil.rmtree(member)
        tm.that(
            u.Cli.process_succeeded(self._run(root, hosted=hosted).outcome), eq=True
        )
        tm.that(
            self._receipt(root).scope_roots,
            eq=(root,),
        )
