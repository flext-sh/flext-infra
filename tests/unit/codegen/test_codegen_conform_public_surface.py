"""Public surface contract of the conform verb: docs, CLI routing, dependency scope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
import shutil
import stat
from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, config, infra
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenMakeBootstrap,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.services import FlextInfraCodegenRoutes
from tests import c, m, tm, u
from tests.unit.codegen.conform_support import TestsFlextInfraConformSupport

pytestmark = [pytest.mark.slow]


class TestsFlextInfraCodegenConformPublicSurface:
    """The conform public surface: docs bootstrap, CLI routing, dependency scope."""

    @staticmethod
    def test_dependency_apply_rejects_before_creating_target(tmp_path: Path) -> None:
        """A prohibited partial publication never initializes its target."""
        root = tmp_path / "uninitialized"
        result = infra.codegen_conform(
            u.Tests.conform_request(
                root,
                what=c.Infra.CodegenConformSurface.DEPENDENCIES,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.APPLY,
            ),
        )
        tm.that(result.failure, eq=True)
        tm.that(root.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize("surface", tuple(c.Infra.CodegenConformSurface))
    def test_request_constraints_follow_surface_contracts(
        tmp_path: Path,
        surface: c.Infra.CodegenConformSurface,
    ) -> None:
        """Every closed surface retains its typed selectors and scope boundary."""
        module = None
        if surface in c.Infra.FILE_ONLY_SURFACES:
            module = (
                "selected"
                if surface is c.Infra.CodegenConformSurface.FACADES
                else f"selected/{c.Infra.INIT_PY}"
            )
        request = m.Infra.CodegenGenerateRequest(
            root=tmp_path,
            what=surface,
            module=module,
        )
        restored = m.Infra.CodegenGenerateRequest.model_validate_json(
            request.model_dump_json(),
        )
        tm.that(restored.what is surface, eq=True)
        tm.that(restored.scope is request.scope, eq=True)
        if surface is c.Infra.CodegenConformSurface.FACADES:
            with pytest.raises(ValueError, match=r"requires.*--module"):
                m.Infra.CodegenGenerateRequest(root=tmp_path, what=surface)
        if surface in c.Infra.SELF_SCOPE_SURFACES | c.Infra.FILE_ONLY_SURFACES:
            with pytest.raises(ValueError, match="self repository scope"):
                m.Infra.CodegenGenerateRequest(
                    root=tmp_path,
                    what=surface,
                    module=module,
                    scope=c.Infra.CodegenConformScope.ALL,
                )

    @staticmethod
    def test_bootstrap_kind_belongs_only_to_the_requested_target(
        infra_git_repo: Path,
    ) -> None:
        """Native bootstrap publishes its own declaration and preserves other owners."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        kind = c.Infra.ProjectKind.INTERNAL_FLEXT
        _library, own, _local = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if own.is_file():
            payload = tm.ok(u.Cli.yaml_safe_load(own))
            declared = u.Cli.json_walk_path(payload, ("Infra", "codegen", "repository"))
            if isinstance(declared, dict):
                declared.pop("kind", None)
            tm.ok(u.Cli.yaml_dump(own, payload))
        sibling = root.parent / "unselected-config.yaml"
        sibling.write_text("OtherOwner:\n  enabled: true\n", encoding="utf-8")
        sibling_before = sibling.read_bytes()

        tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root, kind=kind).execute())

        declaration = tm.ok(u.Infra.load_repository_declaration_inputs(root))
        tm.that(declaration.spec.kind, eq=kind)
        tm.that(declaration.spec.model_fields_set, has="kind")
        tm.that(sibling.read_bytes(), eq=sibling_before)
        before = own.read_bytes()
        tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root, kind=kind).execute())
        tm.that(own.read_bytes(), eq=before)
        conflicting = next(
            candidate for candidate in c.Infra.ProjectKind if candidate != kind
        )
        result = FlextInfraCodegenMakeBootstrap(
            repository_root=root,
            kind=conflicting,
        ).execute()
        tm.that(result.failure, eq=True)
        tm.that(own.read_bytes(), eq=before)

    @staticmethod
    def test_make_bootstrap_publishes_only_its_actual_surface_receipt(
        infra_git_repo: Path,
    ) -> None:
        """Init qualifies changed and unchanged Make output without full gen."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root).execute())
        receipt_path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.MAKEFILE
        )
        for _ in range(2):
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
            )
            tm.ok(
                FlextInfraCodegenMakeBootstrap(
                    repository_root=root,
                    check_only=True,
                ).execute(),
            )
            tm.that(
                tm.ok(
                    u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
                ),
                eq=before,
            )
            rejected = infra.codegen_conform(
                u.Tests.conform_request(
                    root,
                    what=c.Infra.CodegenConformSurface.ALL,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.CHECK,
                ),
            )
            tm.that(rejected.failure, eq=True)
            tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root).execute())

    @staticmethod
    @pytest.mark.parametrize("drift", ["output", "source"])
    def test_bootstrap_check_rejects_drift_without_republishing(
        infra_git_repo: Path,
        drift: str,
    ) -> None:
        """Observational bootstrap rejects changed source and destination states."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        _, project_layer, _ = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        if drift == "source":
            project_layer.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.yaml_dump(project_layer, {"Infra": {"codegen": {}}}))
        tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root).execute())
        if drift == "output":
            target = root / c.Infra.MAKEFILE_FILENAME
            content = target.read_bytes()
        else:
            captured = tuple(
                source
                for source in tm.ok(u.Infra.load_codegen_inputs(root)).sources
                if source.path == project_layer
            )
            tm.that(len(captured), eq=1)
            source = captured[0]
            target = source.path
            content = tm.not_none(source.content)
        target.write_bytes(content + b"\n# publication drift\n")
        receipt_path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.MAKEFILE
        )
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
        )
        result = FlextInfraCodegenMakeBootstrap(
            repository_root=root,
            check_only=True,
        ).execute()
        tm.that(result.failure, eq=True)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(receipt_path, required=True)),
            eq=before,
        )

    @staticmethod
    def test_bootstrap_check_rejects_a_newly_created_optional_layer(
        infra_git_repo: Path,
    ) -> None:
        """A declared absent layer becoming valid input invalidates publication."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        _, _, local_layer = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        tm.that(local_layer.exists(), eq=False)
        tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root).execute())
        receipt_path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.MAKEFILE
        )
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
        )
        local_layer.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.yaml_dump(local_layer, {"Infra": {"codegen": {}}}))

        observed = FlextInfraCodegenMakeBootstrap(
            repository_root=root,
            check_only=True,
        ).execute()

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(receipt_path, required=True)),
            eq=before,
        )
        tm.that(observed.failure, eq=True)

    @staticmethod
    def test_bootstrap_check_authenticates_imported_template_resources(
        infra_git_repo: Path,
        tmp_path: Path,
    ) -> None:
        """A consumed private Jinja import invalidates its read-only receipt."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        codegen = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        entry = next(
            entry
            for entry in codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        templates = tmp_path / "private-templates"
        shutil.copytree(u.Infra.codegen_templates_root(codegen), templates)
        _, _, local_layer = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        local_layer.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.yaml_dump(
                local_layer,
                {"Infra": {"codegen": {"templates": {"root": str(templates)}}}},
            ),
        )
        source = templates / tm.not_none(entry.source)
        imported = tuple(
            state
            for state in tm.ok(u.Cli.template_capture_sources((source,)))
            if state.path != source
        )
        tm.that(bool(imported), eq=True)
        resource = imported[0]
        tm.ok(FlextInfraCodegenMakeBootstrap(repository_root=root).execute())
        receipt_path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.MAKEFILE
        )
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
        )
        resource.path.write_bytes(
            tm.not_none(resource.content) + b"\n{# imported resource drift #}\n",
        )

        observed = FlextInfraCodegenMakeBootstrap(
            repository_root=root,
            check_only=True,
        ).execute()

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(receipt_path, required=True)),
            eq=before,
        )
        tm.that(observed.failure, eq=True)

    @staticmethod
    def test_complete_fleet_receipt_covers_the_observed_root_subset(
        infra_git_repo: Path,
    ) -> None:
        """Complete ALL publication proves SELF without re-planning or effects."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        declared = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.ALL,
            scope=c.Infra.CodegenConformScope.ALL,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        request = m.Infra.CodegenConformRequest.model_validate_json(
            declared.model_dump_json(),
        )
        tm.ok(
            infra.codegen_conform(
                request,
                initial_workspace=workspace,
            ),
        )
        repeated = tm.ok(
            FlextInfraCodegenConform(
                repository_root=root,
                request=request,
                initial_workspace=workspace,
            ).plan(request),
        )
        policy = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        for relative in policy.uv_resolution_pyprojects:
            matches = tuple(
                file for file in repeated.files if file.path == root / relative
            )
            tm.that(len(matches), eq=1)
            tm.that(matches[0].desired_content is not None, eq=True)
        receipt_path = root / c.Infra.CODEGEN_PUBLICATION_REPORT_RELATIVE_PATH
        before = tm.ok(
            u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
        )
        receipt = m.Infra.CodegenPhaseOutcome.model_validate_json(
            tm.not_none(before.content),
        )
        tm.that(
            tuple(output.path for batch in receipt.batches for output in batch.outputs),
            has=root / c.Infra.MAKEFILE_FILENAME,
        )
        for scope in (
            c.Infra.CodegenConformScope.ALL,
            c.Infra.CodegenConformScope.SELF,
        ):
            tm.ok(
                infra.codegen_conform(
                    u.Tests.conform_request(
                        root,
                        what=c.Infra.CodegenConformSurface.ALL,
                        scope=scope,
                        mode=c.Infra.CodegenConformMode.CHECK,
                    ),
                ),
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(receipt_path, required=True)),
            eq=before,
        )

    @staticmethod
    @pytest.mark.parametrize("marker", ["<<<<<<< HEAD", "=======", ">>>>>>> incoming"])
    def test_envrc_bootstrap_preserves_other_surfaces_and_converges(
        infra_git_repo: Path,
        marker: str,
    ) -> None:
        """Recover activation without parsing dependencies or touching local inputs."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        destination = root / c.Infra.ENVRC_FILENAME
        tm.ok(u.Cli.atomic_write_text_file(destination, f"{marker}\n"))
        local = root / ".envrc.local"
        tm.ok(u.Cli.atomic_write_text_file(local, "export BOOTSTRAP_PROBE=preserved\n"))
        before = TestsFlextInfraConformSupport.project_tree(root)
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.ENVRC,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        result = tm.ok(infra.codegen_conform(request))
        tm.that(result.written_files, eq=(destination,))
        tm.ok(u.Cli.run_checked(["bash", "-n", str(destination)], cwd=root))
        after = TestsFlextInfraConformSupport.project_tree(root)
        tm.that(
            tuple(item for item in after if item[0] != destination.name),
            eq=tuple(item for item in before if item[0] != destination.name),
        )
        tm.that(tm.ok(infra.codegen_conform(request)).written_files, eq=())

    @staticmethod
    @pytest.mark.parametrize(
        "scope",
        [c.Infra.CodegenConformScope.DECLARED, c.Infra.CodegenConformScope.ALL],
    )
    def test_envrc_bootstrap_rejects_fleet_scope(
        scope: c.Infra.CodegenConformScope,
    ) -> None:
        """Recovery cannot widen activation publication to another checkout."""
        with pytest.raises(
            ValueError, match="envrc requires the self repository scope"
        ):
            u.Tests.conform_request(
                Path.cwd(),
                what=c.Infra.CodegenConformSurface.ENVRC,
                scope=scope,
                mode=c.Infra.CodegenConformMode.APPLY,
            )

    @staticmethod
    @pytest.mark.parametrize("initial_state", ["invalid", "absent", "wrong-mode"])
    def test_mise_config_repairs_invalid_toml_without_touching_other_surfaces(
        infra_git_repo: Path,
        initial_state: str,
    ) -> None:
        """Repair bytes and mode through the leased transaction, then converge."""
        root = infra_git_repo
        TestsFlextInfraConformSupport.seed_infra_package_tree(root)
        destination = root / c.Infra.MISE_TOML_FILENAME
        desired_mode = next(
            item.mode
            for item in config.Infra.codegen.managed_files
            if item.path == Path(destination.name)
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MISE_CONFIG,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        if initial_state == "invalid":
            tm.ok(
                u.Cli.atomic_write_text_file(
                    destination, '[tools]\npython="a"\npython="b"\n'
                )
            )
        elif initial_state == "absent" and destination.exists():
            destination.unlink()
        if initial_state == "wrong-mode":
            tm.ok(infra.codegen_conform(request))
            destination.chmod(desired_mode ^ stat.S_IWGRP)
        before = TestsFlextInfraConformSupport.project_tree(root)
        result = tm.ok(infra.codegen_conform(request))
        tm.that(result.written_files, eq=(destination,))
        tm.that(stat.S_IMODE(destination.stat().st_mode), eq=desired_mode)
        payload = u.Cli.toml_mapping_from_text(destination.read_text(encoding="utf-8"))
        tm.that(payload is not None, eq=True)
        tools = u.Tests.toml_table_at(destination.read_text(encoding="utf-8"), "tools")
        tm.that(
            set(tools),
            eq={
                "python",
                config.Infra.codegen.toolchain.mise_selector,
                *config.Infra.codegen.toolchain.tool_keys.values(),
            },
        )
        after = TestsFlextInfraConformSupport.project_tree(root)
        tm.that(
            tuple(item for item in after if item[0] != destination.name),
            eq=tuple(item for item in before if item[0] != destination.name),
        )
        tm.that(tm.ok(infra.codegen_conform(request)).written_files, eq=())
        tm.that(stat.S_IMODE(destination.stat().st_mode), eq=desired_mode)

    @staticmethod
    def _workspace_fixture(tmp_path: Path) -> tuple[Path, m.Infra.WorkspaceSpec]:
        """Scaffold the governed workspace fixture.

        Returns:
            The workspace root and its typed spec.

        """
        root_repository = u.Tests.repository_ref("flext")
        member = u.Tests.repository_ref("flext-sample", path=Path("flext-sample"))
        workspace = u.Tests.workspace_spec(
            root_repository,
            project=u.Tests.project_spec("flext"),
            subprojects=(member,),
        )
        root = tmp_path / "flext"
        root.mkdir()
        u.Tests.initialize_git_repo(root, origin_url=root_repository.url)
        u.Tests.write_standalone_workspace_manifest(
            root,
            root_repository.name,
            role=root_repository.role,
        )
        u.Tests.write_project_beads_config(root, root_repository.name)
        member_root = root / member.path
        beads = tm.not_none(workspace.beads)
        u.Tests.WorktreeFixture.initialize_governed_project(
            member_root,
            member.distribution,
            beads=u.Tests.BeadsIdentity(
                workspace=beads.workspace,
                database=beads.database,
                issue_prefix=beads.issue_prefix,
            ),
        )
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            member_root,
            distribution=member.distribution,
            relative_path=member.path.as_posix(),
        )
        u.Tests.copy_tracked_mise_seeds(root)
        return root, workspace

    @staticmethod
    def test_native_view_planning_preserves_the_first_package_failure(
        tmp_path: Path,
    ) -> None:
        """A failed scaffold prerequisite cannot become a missing-root read error."""
        root, workspace = TestsFlextInfraCodegenConformPublicSurface._workspace_fixture(
            tmp_path,
        )
        member = workspace.subprojects[0]
        package = (
            root
            / member.path
            / config.Infra.tooling.tools.pyright.path_rules.source_dir
            / u.Tests.project_spec(member.distribution).package_name
        )
        (package / c.Infra.INIT_PY).unlink()
        u.Tests.commit_git_changes(root / member.path, "remove declared package")
        u.Tests.WorktreeFixture.attach_submodule(
            root,
            root / member.path,
            distribution=member.distribution,
            relative_path=member.path.as_posix(),
        )
        service, request = TestsFlextInfraConformSupport.check_conform_service(
            root,
            workspace,
        )

        plan = tm.ok(service.plan(request))

        tm.that(bool(plan.issues), eq=True)
        cause = tm.not_none(plan.exception)
        tm.that(str(cause), has="cannot resolve package name")
        tm.that(str(cause), has=str(root / member.path))

    @staticmethod
    def test_workspace_uv_plan_owns_root_environment_and_local_member_sources(
        tmp_path: Path,
    ) -> None:
        """Keep workspace setup data complete without Make-side re-derivation."""
        root, workspace = TestsFlextInfraCodegenConformPublicSurface._workspace_fixture(
            tmp_path
        )
        service, request = TestsFlextInfraConformSupport.check_conform_service(
            root,
            workspace,
        )
        planned = service.plan(request)
        plan = tm.ok(planned)
        evidence_text = (root / c.Infra.CODEGEN_PLAN_REPORT_RELATIVE_PATH).read_text(
            encoding="utf-8",
        )
        evidence = m.Infra.CodegenPlanningReport.model_validate_json(evidence_text)
        tm.that(
            tuple(outcome.repository for outcome in evidence.outcomes),
            eq=tuple(repository.name for repository in plan.repositories),
        )
        planned_files = {file.path: file for file in plan.files}
        for outcome in evidence.outcomes:
            for file in outcome.files:
                original = planned_files[file.path]
                tm.that(
                    file.desired_digest,
                    eq=(
                        None
                        if original.desired_content is None
                        else f"sha256:{u.Cli.sha256_bytes(original.desired_content)}"
                    ),
                )
        tm.that(
            evidence_text,
            lacks=['"desired_content":', '"before":', '"environment":'],
        )
        environment = plan.uv_environments[0]
        tm.that(environment.environment_root, eq=root.resolve())
        target = TestsFlextInfraConformSupport.conform_target(
            root.resolve(),
            plan.repositories[0],
            make_profile=workspace.repository.role,
        )
        tm.that(
            environment,
            eq=service.uv_environment_plan(
                root=root.resolve(),
                target=target,
                workspace=workspace,
                config=config.Infra.codegen,
            ),
        )
        TestsFlextInfraCodegenConformPublicSurface._verified_uv_resolution_views(
            root, workspace, plan
        )

    @staticmethod
    def _verified_uv_resolution_views(
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        plan: m.Infra.CodegenPlan,
    ) -> None:
        """Verify both native resolution views' sources and member lines.

        Args:
            root: The governed workspace root.
            workspace: The loaded workspace specification.
            plan: The completed conform plan.

        """
        policy = tm.ok(u.Infra.load_codegen_inputs(root)).spec.make.uv_resolution
        views = (
            (policy.local_directory, (workspace.repository, *workspace.subprojects)),
            (policy.standalone_directory, (workspace.repository,)),
        )
        for relative, repositories in views:
            directory = (root / relative).resolve()
            document = u.Tests.codegen_file_text(
                next(
                    file
                    for file in plan.files
                    if file.path == directory / c.PYPROJECT_FILENAME
                ),
            )
            tm.that(
                u.Tests.toml_table_at(document, "tool", "uv", "sources"),
                eq={
                    repository.distribution: {
                        "path": (root / repository.path)
                        .resolve()
                        .relative_to(directory, walk_up=True)
                        .as_posix(),
                        "editable": repository.editable,
                    }
                    for repository in repositories
                    if repository.package
                },
            )
            if relative == policy.standalone_directory:
                parsed = tm.not_none(u.Cli.toml_parse_text(document))
                declared = tm.not_none(tm.not_none(workspace.project).flext_source)
                selected = tuple(
                    requirement
                    for requirement in tm.ok(u.Infra.document_requirement_lines(parsed))
                    if u.Infra.dep_name(requirement) == u.Infra.dep_name(declared)
                )
                tm.that(bool(selected), eq=True)
                for requirement in selected:
                    tm.that(
                        tm.ok(u.Infra.declared_git_source(requirement)),
                        eq=tm.ok(u.Infra.declared_git_source(declared)),
                    )

    @staticmethod
    def test_docs_config_apply_materializes_an_absent_docs_parent(
        infra_git_repo: Path,
    ) -> None:
        """Bootstrapping docs-config on a checkout without ``docs/`` publishes it."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        docs_dir = root / c.Infra.DIR_DOCS
        if docs_dir.exists():
            shutil.rmtree(docs_dir)

        TestsFlextInfraConformSupport.apply_conform_surface(
            root,
            workspace,
            c.Infra.CodegenConformSurface.DOCS_CONFIG,
        )

        projection = docs_dir / c.Infra.DOCS_CONFIG_FILENAME
        tm.ok(u.Cli.json_loads(projection.read_bytes()))

    @staticmethod
    @pytest.mark.parametrize("mode", tuple(c.Infra.CodegenConformMode))
    def test_public_cli_routes_check_and_apply_to_one_handler(
        infra_git_repo: Path,
        mode: c.Infra.CodegenConformMode,
    ) -> None:
        """Execute one public mode without changing an already conform tree."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        TestsFlextInfraConformSupport.apply_conform_surface(
            root,
            workspace,
            c.Infra.CodegenConformSurface.MAKEFILE,
        )
        before = TestsFlextInfraConformSupport.project_tree(root)
        receipt_path = root / FlextInfraMiseArtifactsVerification.publication_receipt(
            c.Infra.CodegenConformSurface.MAKEFILE
        )
        receipt_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(receipt_path, required=True),
        )
        route = next(
            route
            for route in FlextInfraCodegenRoutes.codegen_routes[
                c.Infra.CLI_GROUP_CODEGEN
            ]
            if route.name == "conform"
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=mode,
        )
        tm.ok(route.handler(request))
        tm.that(TestsFlextInfraConformSupport.project_tree(root), eq=before)
        if mode is c.Infra.CodegenConformMode.CHECK:
            tm.that(
                tm.ok(u.Cli.atomic_read_binary_file_state(receipt_path, required=True)),
                eq=receipt_before,
            )

    @staticmethod
    def test_unchanged_pyproject_apply_uses_the_authenticated_noop_path(
        infra_git_repo: Path,
    ) -> None:
        """A second public apply keeps an unchanged declaration and succeeds."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(infra.codegen_conform(request, initial_workspace=workspace))
        before = (root / c.PYPROJECT_FILENAME).read_bytes()
        tm.ok(infra.codegen_conform(request, initial_workspace=workspace))
        tm.that((root / c.PYPROJECT_FILENAME).read_bytes(), eq=before)

    # Integration-scale: the seed applies the complete surface on a real git
    # repository (plan, publication and its fixed-point re-plan; a pyproject
    # alone is not a fixed point, its [project.scripts] follows src/*/cli.py)
    # before the dependencies plan, so it runs in the slow phase under its
    # per-item bound. The public CLI route of the same check is proven by
    # test_public_cli_routes_check_and_apply_to_one_handler.
    @staticmethod
    @pytest.mark.slow
    def test_dependency_surface_excludes_unowned_managed_files(
        infra_git_repo: Path,
    ) -> None:
        """Plan only dependency metadata when another managed surface is invalid."""
        root = infra_git_repo
        workspace = TestsFlextInfraConformSupport.standalone_workspace(root)
        TestsFlextInfraConformSupport.apply_conform_surface(
            root,
            workspace,
            c.Infra.CodegenConformSurface.ALL,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "custom.mk",
                ".PHONY: public-handler\npublic-handler:\n\t@true\n",
            ),
        )
        u.Tests.commit_git_changes(root, "Seed generated project")
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.DEPENDENCIES,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned = FlextInfraCodegenConform(repository_root=root, request=request).plan(
            request,
        )
        tm.ok(planned)
        policy = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        expected = (
            root / c.PYPROJECT_FILENAME,
            *(root / relative for relative in policy.uv_resolution_pyprojects),
        )
        tm.that(tuple(file.path for file in planned.value.files), eq=expected)
        tm.that(
            tuple(
                u.Infra.codegen_file_requires_effect(file)
                for file in planned.value.files
            ),
            eq=(False,) * len(expected),
            msg="\n".join(
                line
                for file in planned.value.files
                for line in difflib.unified_diff(
                    file.path.read_text(encoding=c.DEFAULT_ENCODING).splitlines(),
                    u.Tests.codegen_file_text(file).splitlines(),
                    fromfile=str(file.path),
                    tofile=f"{file.path} (planned)",
                    lineterm="",
                )
            ),
        )
