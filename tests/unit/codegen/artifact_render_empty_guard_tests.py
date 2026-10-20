"""Contract tests for the empty-render publication guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from flext_infra import FlextInfraConfig, c, r
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenStaging
from flext_infra.codegen.staged_package import FlextInfraStagedPackage
from flext_infra.gates import FlextInfraRuffFormatGate, FlextInfraRuffLintGate
from tests import m, tm, u

if TYPE_CHECKING:
    from tests import p


class TestsFlextInfraArtifactRenderEmptyGuard:
    """A managed render that produced no content must fail loud, never publish.

    A workflow fragment gated on an undeclared capability layer (the
    ``private_dependency_auth`` incident, bead cosmos-dxtk7) rendered 0 bytes
    and was emitted verbatim: consumers inspected the directory, saw the
    artifact present, and concluded the capability was delivered while every
    step it owns was silently absent. The render funnel owns the refusal:
    empty render in, typed planning issue out, naming the template, the
    destination, and the declaration cause.
    """

    @staticmethod
    def _plan_render(
        tmp_path: Path,
        content: str,
    ) -> tuple[p.Result[m.Infra.CodegenPlan], Path, Path]:
        """Plan a template declared through the target's repository-local config.

        Returns:
            The planning result, template source path, and destination path.

        """
        root = tmp_path / "project"
        root.mkdir()
        codegen = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        entry = next(
            entry
            for entry in codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        source = tm.not_none(entry.source)
        templates = tmp_path / "templates"
        shutil.copytree(u.Infra.codegen_templates_root(codegen), templates)
        # A nonempty conditional source renders exactly the supplied test content.
        (templates / source).write_text(
            "{% if false %}undeclared capability{% endif %}" + content,
            encoding="utf-8",
        )
        _, _, local_config = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        local_config.parent.mkdir()
        tm.ok(
            u.Cli.yaml_dump(
                local_config,
                {"Infra": {"codegen": {"templates": {"root": str(templates)}}}},
            ),
        )
        effective = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        tm.that(u.Infra.codegen_templates_root(effective), eq=templates)
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.initialize_git_repo(root)
        repository = u.Tests.repository_ref("fixture-project")
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        planned = FlextInfraCodegenConform(
            repository_root=root,
            state=m.Infra.CodegenConformState(
                repository_root=root,
                initial_workspace=workspace,
                request=request,
            ),
        ).plan(request)
        return planned, source, root / entry.destination

    @staticmethod
    def test_empty_render_fails_loud_naming_template_and_cause(
        tmp_path: Path,
    ) -> None:
        """A 0-byte render produces a planning issue naming template and cause."""
        refused, source, destination = (
            TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
                tmp_path,
                "",
            )
        )
        plan = tm.ok(refused)
        tm.that(bool(plan.issues), eq=True)
        diagnostic = "\n".join(issue.message for issue in plan.issues)
        tm.that(
            diagnostic,
            has=str(source),
        )
        tm.that(
            diagnostic,
            has=destination.name,
        )
        tm.that(diagnostic, has="render produced no content")
        tm.that(diagnostic, has="consumer declaration error")
        tm.that(any(file.path == destination for file in plan.files), eq=False)
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_whitespace_render_fails_loud_with_template_stage_prefix(
        tmp_path: Path,
    ) -> None:
        """A whitespace-only render is refused and carries the planner banner."""
        refused, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            "  \n\t\n",
        )
        plan = tm.ok(refused)
        tm.that(bool(plan.issues), eq=True)
        diagnostic = "\n".join(issue.message for issue in plan.issues)
        tm.that(diagnostic, has="stage=templates ")
        tm.that(diagnostic, has="repository=")
        tm.that(diagnostic, has="publishing a 0-byte artifact is forbidden")
        tm.that(any(file.path == destination for file in plan.files), eq=False)
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_rendered_content_passes_through_verbatim(
        tmp_path: Path,
    ) -> None:
        """A render with real content passes through byte-exact."""
        content = "ready:\n\t@echo ready\n"
        kept, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            content,
        )
        tm.that(kept.failure, eq=False)
        plan = tm.ok(kept)
        tm.that(bool(plan.issues), eq=False)
        tm.that(u.Tests.planned_text(plan, destination.name), eq=content)
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_semantic_output_is_prepared_under_planned_policy_and_idempotent(
        tmp_path: Path,
    ) -> None:
        """Prepared producer bytes pass configured lint and format immediately."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        documentation = root / "docs" / "consumer.md"
        documentation.parent.mkdir()
        documentation.write_text("# Consumer Context\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.git_bootstrap(root, ("add", str(documentation.relative_to(root))))
        metadata = root / c.PYPROJECT_FILENAME
        before_metadata = metadata.read_text(encoding=c.DEFAULT_ENCODING)
        document = tm.not_none(u.Cli.toml_parse_text(before_metadata))
        # Ruff's rule identifiers are external contracts. Elect a different
        # destination policy in the planned metadata, leaving live policy stale.
        document["tool"] = {"ruff": {"lint": {"select": ["F", "UP", "I"]}}}
        planned_metadata = u.Cli.toml_dumps(document)
        destination = package / "prepared.py"
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=tm.ok(u.Cli.atomic_read_binary_file_state(path, required=False)),
                desired_content=content.encode(c.DEFAULT_ENCODING),
                desired_mode=c.Infra.CONFIG_SPEC[1],
            )
            for path, content in (
                (metadata, planned_metadata),
                (destination, "import os\n\nvalues=dict(answer=42)\n"),
            )
        )

        sealed = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(root, plans))
        tm.that(
            tuple(plan.desired_content for plan in sealed),
            eq=tuple(plan.desired_content for plan in plans),
        )
        prepared = tm.ok(
            FlextInfraCodegenStaging.prepare_python_plans(
                root, sealed, prepare=u.Infra.normalize_source_plan
            )
        )
        emitted = tm.not_none(prepared[1].desired_content)
        tm.that(destination.exists(), eq=False)
        tm.that(metadata.read_text(encoding=c.DEFAULT_ENCODING), eq=before_metadata)
        tm.that(emitted.decode(c.DEFAULT_ENCODING), eq="values = dict(answer=42)\n")
        tm.that("import os" in emitted.decode(c.DEFAULT_ENCODING), eq=False)
        receipt = tm.not_none(prepared[0].prepared_sources)
        if not isinstance(receipt, m.Infra.StageSourcePlan):
            pytest.fail("Preparation did not return the canonical source receipt")
        tm.that(all(plan.prepared_sources is receipt for plan in prepared), eq=True)
        tm.that(bool(receipt.source_query_topology), eq=True)
        tm.that(bool(receipt.source_directories), eq=True)
        tm.that(
            dict(receipt.prepared_hashes),
            eq={
                plan.path: u.Cli.sha256_bytes(tm.not_none(plan.desired_content))
                for plan in prepared
            },
        )
        repeated = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(root, prepared))
        tm.that(
            tuple(plan.desired_content for plan in repeated),
            eq=tuple(plan.desired_content for plan in prepared),
        )
        tm.that(all(plan.prepared_sources is receipt for plan in repeated), eq=True)

        def configured_check(view: Path) -> p.Result[bool]:
            tm.that(
                (view / documentation.relative_to(root)).read_bytes(),
                eq=documentation.read_bytes(),
            )
            selected = view / destination.relative_to(root)
            context = m.Infra.GateContext(repository_root=view, reports_dir=tmp_path)
            for gate in (FlextInfraRuffLintGate(view), FlextInfraRuffFormatGate(view)):
                execution = gate.check_files((selected,), view, context)
                tm.that(execution.result.passed, eq=True, msg=execution.raw_output)
            return r[bool].ok(value=True)

        tm.ok(FlextInfraStagedPackage.consume_sources(receipt, configured_check))

    @staticmethod
    @pytest.mark.parametrize(
        "source",
        ["import os\n\nvalues=dict(answer=42)\n", "result = undeclared_supplier\n"],
    )
    def test_generator_seals_exact_proposed_bytes_without_semantic_repair(
        tmp_path: Path,
        source: str,
    ) -> None:
        """Sealing authenticates bytes; repair and runtime own separate verdicts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "generated.py"
        before = tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False))
        proposal = m.Infra.CodegenFilePlan(
            project=root,
            path=destination,
            before=before,
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=c.Infra.CONFIG_SPEC[1],
        )
        prepared = tm.ok(
            FlextInfraCodegenStaging.prepare_python_plans(root, (proposal,))
        )
        sealed = prepared[0]
        receipt = tm.not_none(sealed.prepared_sources)
        tm.that(sealed.desired_content, eq=proposal.desired_content)
        tm.that(receipt.updates[destination], eq=source)
        tm.that(
            dict(receipt.prepared_hashes)[destination],
            eq=u.Cli.sha256_bytes(tm.not_none(proposal.desired_content)),
        )
        tm.that(bool(receipt.source_query_topology), eq=True)
        repeated = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(root, prepared))
        tm.that(repeated[0].desired_content, eq=proposal.desired_content)
        tm.that(repeated[0].prepared_sources is receipt, eq=True)
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False)),
            eq=before,
        )

    @staticmethod
    def test_unrepairable_semantic_output_is_rejected_without_publication(
        tmp_path: Path,
    ) -> None:
        """An unrepaired native finding stays causal and never reaches live bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "rejected.py"
        source = "result = undeclared_supplier\n"
        before = tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False))
        rejected = FlextInfraCodegenStaging.prepare_python_plans(
            root,
            (
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=destination,
                    before=before,
                    desired_content=source.encode(c.DEFAULT_ENCODING),
                    desired_mode=c.Infra.CONFIG_SPEC[1],
                ),
            ),
            prepare=u.Infra.normalize_source_plan,
        )
        tm.that(rejected.failure, eq=True)
        tm.that(str(rejected.error), has="undeclared_supplier")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=False)),
            eq=before,
        )

    @staticmethod
    def test_candidate_admission_preserves_original_consumer_cause(
        tmp_path: Path,
    ) -> None:
        """Read-only admission preserves its original failure and live source."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "rejected.py"
        source = "value = 1\n"
        plan = tm.ok(FlextInfraStagedPackage.plan_sources(root, {destination: source}))
        original = OSError("declared candidate consumer failed")

        def reject(view: Path) -> p.Result[bool]:
            tm.that(
                (view / destination.relative_to(root)).read_text(
                    encoding=c.DEFAULT_ENCODING
                ),
                eq=source,
            )
            return r[bool].fail(str(original), exception=original)

        rejected = FlextInfraStagedPackage.consume_sources(plan, reject)
        tm.that(rejected.failure, eq=True)
        tm.that(rejected.exception is original, eq=True)
        tm.that(destination.exists(), eq=False)

    @staticmethod
    def test_admission_refuses_candidate_mutation_instead_of_resealing(
        tmp_path: Path,
    ) -> None:
        """A checker cannot prepare or mutate bytes inside read-only admission."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "unchanged.py"
        destination.write_text("value = 1\n", encoding=c.DEFAULT_ENCODING)
        before = tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=True))
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {destination: tm.not_none(before.content).decode(c.DEFAULT_ENCODING)},
            )
        )

        def mutate(view: Path) -> p.Result[bool]:
            (view / destination.relative_to(root)).write_text(
                "value = 2\n", encoding=c.DEFAULT_ENCODING
            )
            return r[bool].ok(value=True)

        rejected = FlextInfraStagedPackage.consume_sources(plan, mutate)
        tm.that(rejected.failure, eq=True)
        tm.that(str(rejected.error), has="changed during read-only admission")
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(destination, required=True)),
            eq=before,
        )

    @staticmethod
    def test_public_check_schema_cannot_redirect_candidate_runtime() -> None:
        """The public CLI payload never exposes a physical runtime override."""
        schema = m.Infra.RunCommand.model_json_schema(by_alias=True)
        properties = schema["properties"]
        tm.that("runtime_root" in properties, eq=False)
        tm.that("runtime-root" in properties, eq=False)

    @staticmethod
    def test_project_preparation_does_not_merge_independent_policy_contexts(
        tmp_path: Path,
    ) -> None:
        """Each owning project receives only its own planned lint policy."""
        workspace = u.Tests.create_lazy_init_workspace(tmp_path)[0]
        plans: list[m.Infra.CodegenFilePlan] = []
        destinations: list[Path] = []
        metadata_paths: list[Path] = []
        for name, selected in (("first", "F"), ("second", "UP")):
            root, package = u.Tests.create_lazy_init_workspace(
                workspace,
                project_name=f"prepared-{name}",
                package_name=f"prepared_{name}",
            )
            metadata = root / c.PYPROJECT_FILENAME
            document = tm.not_none(
                u.Cli.toml_parse_text(metadata.read_text(encoding=c.DEFAULT_ENCODING))
            )
            document["tool"] = {"ruff": {"lint": {"select": [selected]}}}
            destination = package / "prepared.py"
            destinations.append(destination)
            metadata_paths.append(metadata)
            for path, content in (
                (metadata, u.Cli.toml_dumps(document)),
                (destination, "import os\n\nvalue = 1\n"),
            ):
                plans.append(
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=tm.ok(
                            u.Cli.atomic_read_binary_file_state(path, required=False)
                        ),
                        desired_content=content.encode(c.DEFAULT_ENCODING),
                        desired_mode=c.Infra.CONFIG_SPEC[1],
                    )
                )

        prepared = tm.ok(
            FlextInfraCodegenStaging.prepare_python_plans(
                workspace, tuple(plans), prepare=u.Infra.normalize_source_plan
            )
        )
        by_path = {plan.path: plan for plan in prepared}
        first, second = (by_path[path] for path in destinations)
        tm.that(b"import os" in tm.not_none(first.desired_content), eq=False)
        tm.that(b"import os" in tm.not_none(second.desired_content), eq=True)
        for local, foreign_metadata in (
            (first, metadata_paths[1]),
            (second, metadata_paths[0]),
        ):
            receipt = tm.not_none(local.prepared_sources)
            tm.that(foreign_metadata in receipt.updates, eq=False)
            for source in local.source_states:
                if source.path == foreign_metadata:
                    tm.that(source.content, eq=foreign_metadata.read_bytes())
        tm.that(
            tuple(plan.dependency_group for plan in prepared),
            eq=tuple(plan.dependency_group for plan in plans),
        )
        tm.that(any(path.exists() for path in destinations), eq=False)
        updates = {
            plan.path: tm.not_none(plan.desired_content).decode(c.DEFAULT_ENCODING)
            for plan in prepared
        }
        unselected = tm.ok(FlextInfraStagedPackage.plan_sources(workspace, updates))
        rejected = FlextInfraStagedPackage.project_layouts(unselected, first.project)
        tm.that(rejected.failure, eq=True)
        tm.that(str(rejected.error), has="no original source authority")
        joint = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                workspace,
                updates,
                options=m.Infra.StageSourceOptions(
                    workspaces=(first.project, second.project),
                ),
            )
        )
        elected = tm.ok(FlextInfraStagedPackage.project_layouts(joint, first.project))
        tm.that(first.project in {layout.project_root for layout in elected}, eq=True)
        tm.that(second.project in {layout.project_root for layout in elected}, eq=False)

    @staticmethod
    def test_candidate_checker_requires_original_physical_environment(
        tmp_path: Path,
    ) -> None:
        """A staged checkout cannot borrow the running checker's environment."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "consumer.py"
        source_plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(root, {destination: "value = 1\n"})
        )
        candidate = tmp_path / "candidate"
        candidate.mkdir()
        rejected = FlextInfraWorkspaceChecker(
            repository_root=candidate
        ).execute_candidate(
            m.Infra.RunCommand(
                repository_root=candidate,
                reports_dir=str(tmp_path / "reports"),
                check_only=True,
            ),
            source_plan,
            project_root=root,
            runtime_report=m.Infra.ValidationReport(
                passed=False,
                summary="Original physical runtime is absent; admission has not run",
            ),
        )
        tm.that(rejected.failure, eq=True)
        tm.that(str(rejected.error), has=str(u.Infra.runtime_environment_dir(root)))
        tm.that(destination.exists(), eq=False)
