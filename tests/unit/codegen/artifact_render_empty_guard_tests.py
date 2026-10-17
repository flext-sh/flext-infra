"""Contract tests for the empty-render publication guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import FlextInfraConfig, c, r
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
            initial_workspace=workspace,
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
    def test_python_output_is_prepared_under_planned_policy_and_idempotent(
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

        prepared = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(root, plans))
        emitted = tm.not_none(prepared[1].desired_content)
        tm.that(destination.exists(), eq=False)
        tm.that(metadata.read_text(encoding=c.DEFAULT_ENCODING), eq=before_metadata)
        tm.that(emitted.decode(c.DEFAULT_ENCODING), has='{"answer": 42}')
        tm.that("import os" in emitted.decode(c.DEFAULT_ENCODING), eq=False)
        repeated = tm.ok(FlextInfraCodegenStaging.prepare_python_plans(root, prepared))
        tm.that(
            tuple(plan.desired_content for plan in repeated),
            eq=tuple(plan.desired_content for plan in prepared),
        )

        stage = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {
                    plan.path: tm.not_none(plan.desired_content).decode(
                        c.DEFAULT_ENCODING
                    )
                    for plan in prepared
                },
            )
        )

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

        tm.ok(FlextInfraStagedPackage.consume_sources(stage, configured_check))

    @staticmethod
    def test_unrepairable_python_output_is_rejected_without_publication(
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
