"""Authenticated source campaigns and strict explicit rename artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod import (
    FlextInfraCodemodSemanticApply,
    FlextInfraModGateEngine,
    FlextInfraModTextGateEngine,
)
from tests import c, m, tm, u


class TestsFlextInfraSemanticRenameSeed:
    """Source campaigns never weaken the explicit rename artifact contract."""

    @staticmethod
    def test_text_plan_consumes_declared_move_without_reelecting_live_sources(
        tmp_path: Path,
    ) -> None:
        """Text effects preserve original identities, modes and elected scope."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source, destination = package / "service.py", package / "meaningful.py"
        outside = package / "outside.py"
        text = 'value = "before"\n'
        source.write_text(text, encoding=c.DEFAULT_ENCODING)
        source.chmod(0o750)
        outside.write_text(text, encoding=c.DEFAULT_ENCODING)
        rules = root / c.Infra.CODEMOD_TEXT_RULES_RELPATH
        rules.parent.mkdir(parents=True, exist_ok=True)
        rules.write_text(
            "rules:\n  - id: elected-source\n    find: before\n    replace: after\n",
            encoding=c.DEFAULT_ENCODING,
        )
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {source: None, destination: text},
                options=m.Infra.StageSourceOptions(
                    modes={destination: tm.not_none(original.mode)}
                ),
            )
        )
        before = tm.ok(u.Cli.atomic_inventory_physical_tree(root))
        _report, analysis = tm.ok(
            FlextInfraModTextGateEngine.plan(
                root,
                sources={destination: text},
                source_states=plan.inputs,
                declared_files=plan.declared_files,
            )
        )
        tm.that(analysis.issues, empty=True)
        tm.that(tuple(effect.path for effect in analysis.files), eq=(destination,))
        tm.that(
            analysis.files[0].desired_content,
            eq=text.replace("before", "after").encode(c.DEFAULT_ENCODING),
        )
        tm.that(analysis.files[0].desired_mode, eq=original.mode)
        tm.that(
            analysis.files[0].before,
            eq=next(
                effect.before
                for effect in plan.declared_files
                if effect.path == destination
            ),
        )
        _report, rejected = tm.ok(
            FlextInfraModTextGateEngine.plan(
                root,
                sources={destination: text},
                source_states=plan.inputs,
                declared_files=tuple(
                    effect.model_copy(
                        update={
                            "before": original.model_copy(
                                update={"content": b"forged preimage\n"}
                            )
                        }
                    )
                    if effect.path == source
                    else effect
                    for effect in plan.declared_files
                ),
            )
        )
        tm.that(rejected.files, empty=True)
        tm.ok(isinstance(rejected.exception, ValueError))
        tm.ok(u.Cli.atomic_verify_binary_file_states(plan.inputs))
        tm.that(tm.ok(u.Cli.atomic_inventory_physical_tree(root)), eq=before)

    @staticmethod
    def test_candidate_scan_preserves_declared_executable_move_without_live_effects(
        tmp_path: Path,
    ) -> None:
        """The scan elects desired sources and keeps original absence witnesses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        destination = package / "meaningful.py"
        text = "class Service:\n    pass\n"
        source.write_text(text, encoding=c.DEFAULT_ENCODING)
        source.chmod(0o750)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {source: None, destination: text},
                options=m.Infra.StageSourceOptions(
                    modes={destination: tm.not_none(original.mode)}
                ),
            )
        )
        report = tm.ok(
            infra.source_preview(root).preview_sources(
                plan.workspace,
                plan.updates,
                lambda view, _paths: FlextInfraModGateEngine.scan_candidate(
                    root, view, plan
                ).unwrap(),
                options=m.Infra.CodegenSourcePreviewOptions(
                    inputs=plan.inputs, modes=plan.modes, runtime_check=False
                ),
            )
        )
        states = {state.path: state for state in tm.not_none(report.source_states)}
        tm.that(source in states, eq=False)
        tm.that(states[destination].content, eq=original.content)
        tm.that(states[destination].mode, eq=original.mode)
        tm.ok(u.Cli.atomic_verify_binary_file_states(plan.inputs))
        tm.that(destination.exists(), eq=False)

    @staticmethod
    @pytest.mark.parametrize("mismatch", ["undeclared", "preimage", "staged"])
    def test_candidate_scan_rejects_unproven_retirement_before_effects(
        tmp_path: Path,
        mismatch: str,
    ) -> None:
        """A tombstone needs its exact original and materialized absence witnesses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        source.write_text("class Service:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        plan = tm.ok(FlextInfraStagedPackage.plan_sources(root, {source: None}))
        if mismatch == "undeclared":
            plan = plan.model_copy(update={"declared_files": ()})
        elif mismatch == "preimage":
            effect = plan.declared_files[0]
            original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
            plan = plan.model_copy(
                update={
                    "declared_files": (
                        effect.model_copy(
                            update={
                                "before": original.model_copy(
                                    update={"content": b"different preimage\n"}
                                )
                            }
                        ),
                    )
                }
            )
        view = tmp_path / "scan-view"
        staged = view / source.relative_to(root)
        staged.parent.mkdir(parents=True)
        if mismatch == "staged":
            staged.write_bytes(source.read_bytes())
        before = tm.ok(u.Cli.atomic_inventory_physical_tree(root))
        tm.fail(
            FlextInfraModGateEngine.scan_candidate(root, view, plan),
            has="semantic scan",
        )
        tm.that(tm.ok(u.Cli.atomic_inventory_physical_tree(root)), eq=before)
        tm.ok(u.Cli.atomic_verify_binary_file_states(plan.inputs))

    @staticmethod
    def test_package_preview_expands_files_modes_and_cross_root_consumers(
        tmp_path: Path,
    ) -> None:
        """A package preview retains nested content and never moves live sources."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="package-receiver", package_name="package_receiver"
        )
        origin = package / "parts"
        nested = origin / "nested"
        nested.mkdir(parents=True)
        contents = {
            origin / "__init__.py": "from .service import Original\n",
            origin / "service.py": "class Original:\n    pass\n",
            nested / "__init__.py": "",
            nested / "consumer.py": "from ..service import Original\n",
        }
        for path, content in contents.items():
            path.write_text(content, encoding=c.DEFAULT_ENCODING)
        source = origin / "service.py"
        source.chmod(0o750)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.parts.service import Original\n",
            encoding=c.DEFAULT_ENCODING,
        )
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.parts",
                    replacement_name="_parts",
                    reason="Explicit package naming decision",
                ),
            ),
            consumer_roots=(receiver,),
        )
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, selections
                )
            )
        target = package / "_parts"
        tm.that(
            artifact.moves,
            eq=tuple(
                sorted((path, target / path.relative_to(origin)) for path in contents)
            ),
        )
        for path, content in contents.items():
            tm.that(artifact.candidate.updates[path], eq=None)
            tm.that(
                artifact.candidate.updates[target / path.relative_to(origin)],
                eq=content,
            )
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
        tm.that(artifact.candidate.modes[target / source.name], eq=original.mode)
        tm.that(artifact.candidate.updates[consumer], has="._parts.service")
        tm.fail(target.exists())
        tm.that(artifact.source_directories, empty=False)
        tm.that(artifact.source_query_topology, empty=False)
        tm.ok(u.Cli.atomic_verify_binary_file_states(artifact.source_states))
        tm.ok(
            u.Cli.atomic_verify_directory_queries(
                artifact.source_directories,
                artifact.source_query_topology,
                publications=m.Cli.AtomicDirectoryQueryEffects(
                    membership_policy=tuple(
                        sorted(config.Infra.codegen.source_scan_ignored)
                    )
                ),
            )
        )
        (nested / "new.py").write_text("", encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="source directory membership changed"):
            u.Cli.atomic_verify_directory_queries(
                artifact.source_directories,
                artifact.source_query_topology,
                publications=m.Cli.AtomicDirectoryQueryEffects(
                    membership_policy=tuple(
                        sorted(config.Infra.codegen.source_scan_ignored)
                    )
                ),
            )

    @staticmethod
    @pytest.mark.parametrize(
        "conflict", ["payload", "directory", "module", "child", "empty"]
    )
    def test_package_preview_rejects_incomplete_or_overlapping_moves(
        tmp_path: Path, conflict: str
    ) -> None:
        """Unsupported resources and occupied or overlapping moves fail prepublish."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        origin = package / "parts"
        origin.mkdir()
        initializer = origin / "__init__.py"
        initializer.write_text("", encoding=c.DEFAULT_ENCODING)
        source = origin / "service.py"
        content = "class Original:\n    pass\n"
        source.write_text(content, encoding=c.DEFAULT_ENCODING)
        decisions = [
            m.Infra.SemanticRenameSelection(
                qualified_name=f"{package.name}.parts",
                replacement_name="_parts",
                reason="Explicit package naming decision",
            )
        ]
        if conflict == "payload":
            (origin / "resource.json").write_text("{}", encoding=c.DEFAULT_ENCODING)
            diagnostic = "cannot preserve uninventoried payload"
        elif conflict == "directory":
            (package / "_parts").mkdir()
            diagnostic = "destination is occupied"
        elif conflict == "module":
            (package / "_parts.py").write_text("", encoding=c.DEFAULT_ENCODING)
            diagnostic = "destination is occupied"
        elif conflict == "empty":
            (origin / "empty").mkdir()
            diagnostic = "cannot preserve empty directory"
        else:
            decisions.append(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.parts.service",
                    replacement_name="renamed",
                    reason="Overlapping child decision",
                )
            )
            diagnostic = "separate virtual waves for overlapping selections"
        selections = m.Infra.SemanticRenameSelections(decisions=tuple(decisions))
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match=diagnostic),
        ):
            FlextInfraCodemodSemanticApply.build_rename_plan(
                root, workspace, selections
            )
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=content)
        tm.ok(initializer.exists())

    @staticmethod
    def test_native_rename_artifact_authenticates_selected_sources(
        tmp_path: Path,
    ) -> None:
        """A real naming decision round-trips and rejects external source drift."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="seed-receiver",
            package_name="seed_receiver",
        )
        driver = root / c.Infra.REPORTS_DIR_NAME / "native" / "seed.artifact"
        driver.parent.mkdir(parents=True, exist_ok=True)
        source = package / "service.py"
        source.write_text("class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.service import Original\nVALUE = Original()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, consumer)
        )
        selections = m.Infra.SemanticRenameSelections(
            decisions=(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.Original",
                    replacement_name="Renamed",
                    reason="Explicit domain rename",
                ),
            ),
            consumer_roots=(receiver,),
        )
        with infra.rope_workspace(root) as workspace:
            artifact = tm.ok(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, selections
                )
            )
        tm.that(len(artifact.decisions), eq=1)
        tm.that(artifact.candidate.updates[consumer], has="Renamed")
        tm.that(artifact.consumer_roots, eq=(receiver,))
        for original in originals:
            tm.ok(original in artifact.source_states)
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        tm.ok(u.Cli.atomic_write_text_file(driver, artifact.model_dump_json()))
        state = tm.ok(u.Cli.atomic_read_binary_file_state(driver, required=True))
        hydrated = m.Infra.SemanticRenamePlan.model_validate_json(
            tm.not_none(state.content)
        )
        with infra.rope_workspace(root) as workspace:
            tm.ok(
                FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                    root, hydrated, state, workspace
                )
            )
        consumer.write_bytes(consumer.read_bytes() + b"# changed source epoch\n")
        with infra.rope_workspace(root) as workspace:
            tm.fail(
                FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                    root, hydrated, state, workspace
                )
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states((originals[0], state)))

    @staticmethod
    @pytest.mark.parametrize("drift", ["source", "directory", "topology"])
    def test_source_campaign_authenticates_external_source_elections(
        tmp_path: Path, drift: str
    ) -> None:
        """A campaign without rename intent retains file and namespace witnesses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        receiver, receiver_package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="source-receiver",
            package_name="source_receiver",
        )
        source = package / "service.py"
        source.write_text("class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        consumer = receiver_package / "consumer.py"
        consumer.write_text(
            f"from {package.name}.service import Original\nVALUE = Original()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        campaign = tm.ok(
            FlextInfraCodemodSemanticApply.build_source_plan(root, (receiver,))
        )
        tm.that(
            m.Infra.SemanticSourcePlan.model_validate_json(campaign.model_dump_json()),
            eq=campaign,
        )
        tm.fail(isinstance(campaign, m.Infra.SemanticRenamePlan))
        tm.that(campaign.candidate.updates, empty=True)
        tm.that(campaign.consumer_roots, eq=(receiver,))
        tm.ok({source, consumer} <= {state.path for state in campaign.source_states})
        tm.that(campaign.source_directories, empty=False)
        tm.that(campaign.source_query_topology, empty=False)
        tm.ok(u.Cli.atomic_verify_binary_file_states(campaign.source_states))
        tm.ok(
            u.Cli.atomic_verify_directory_queries(
                campaign.source_directories,
                campaign.source_query_topology,
                publications=m.Cli.AtomicDirectoryQueryEffects(
                    membership_policy=tuple(
                        sorted(config.Infra.codegen.source_scan_ignored)
                    )
                ),
            )
        )
        if drift == "source":
            consumer.write_bytes(consumer.read_bytes() + b"# changed source epoch\n")
        elif drift == "directory":
            (receiver_package / "new_consumer.py").write_text(
                "VALUE = 1\n", encoding=c.DEFAULT_ENCODING
            )
        else:
            previous = receiver_package.with_name("previous-package")
            receiver_package.rename(previous)
            receiver_package.symlink_to(previous, target_is_directory=True)
        tm.fail(
            FlextInfraCodemodSemanticApply.publish_candidate(
                root, campaign, publish=False
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @staticmethod
    def test_readonly_resource_receipt_is_not_a_python_planning_target(
        tmp_path: Path,
    ) -> None:
        """An external producer resource remains authenticated, never rewrite-owned."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        content = "value = 1\n"
        source.write_text(content, encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        resource = tmp_path / "producer.yaml"
        resource.write_text("version: 1\n", encoding=c.DEFAULT_ENCODING)
        receipt = tm.ok(u.Cli.atomic_read_binary_file_state(resource, required=True))
        campaign = tm.ok(
            FlextInfraCodemodSemanticApply.compose_candidate(
                tm.ok(FlextInfraCodemodSemanticApply.build_source_plan(root)),
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                    inputs=(receipt,),
                    files=(),
                ),
            )
        )
        tm.that(campaign.candidate.updates, empty=True)
        tm.ok(receipt in campaign.source_states)
        tm.ok(receipt in campaign.candidate.inputs)
        tm.ok(FlextInfraStagedPackage.source_inputs_current(campaign.candidate))
        with FlextInfraCodemodSemanticApply.planning_workspace(
            root, campaign, {source: content}
        ) as graph:
            with closing(
                u.Infra.snapshot_project(graph.rope_project, {source: content})
            ) as snapshot:
                planned = next(
                    file
                    for file in snapshot.get_python_files()
                    if Path(file.real_path) == source
                )
                tm.that(planned.read(), eq=content)
            with pytest.raises(ValueError, match="outside its input inventory"):
                u.Infra.snapshot_project(graph.rope_project, {resource: "version: 2\n"})
        resource.write_bytes(tm.not_none(receipt.content) + b"changed: true\n")
        tm.fail(FlextInfraStagedPackage.source_inputs_current(campaign.candidate))
        tm.fail(
            FlextInfraCodemodSemanticApply.publish_candidate(
                root, campaign, publish=False
            )
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))

    @staticmethod
    def test_empty_rename_is_rejected_at_construction_json_and_builder(
        tmp_path: Path,
    ) -> None:
        """An authenticated no-op source campaign is never a rename artifact."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        campaign = tm.ok(FlextInfraCodemodSemanticApply.build_source_plan(root))
        with pytest.raises(ValueError, match="decisions"):
            m.Infra.SemanticRenamePlan(
                decisions=(), edits=(), candidate=campaign.candidate
            )
        payload = campaign.model_dump(mode="json")
        payload.update(decisions=[], edits=[], moves=[])
        content = tm.ok(u.Cli.json_dumps(payload))
        with pytest.raises(ValueError, match="decisions"):
            m.Infra.SemanticRenamePlan.model_validate_json(content)
        driver = root / "empty.artifact"
        tm.ok(u.Cli.atomic_write_text_file(driver, content))
        with pytest.raises(ValueError, match="decisions"):
            FlextInfraCodemodSemanticApply.load_rename_artifact(
                root, m.Infra.ModCommand(repository_root=root, rename_plan=driver)
            )
        with infra.rope_workspace(root) as workspace:
            tm.fail(
                FlextInfraCodemodSemanticApply.build_rename_plan(
                    root, workspace, m.Infra.SemanticRenameSelections(decisions=())
                ),
                has="explicit naming decision",
            )
        failure = RuntimeError("first source planner failure")
        with pytest.raises(RuntimeError) as raised:
            FlextInfraCodemodSemanticApply.compose_candidate(
                campaign,
                m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                    files=(),
                    inputs=campaign.source_states,
                    exception=failure,
                ),
            )
        tm.ok(raised.value is failure)

    @staticmethod
    def test_missing_selected_identity_is_not_an_empty_campaign(tmp_path: Path) -> None:
        """The first inventory exception escapes instead of dropping selections."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "service.py"
        source.write_text("class Original:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        selections = m.Infra.SemanticRenameSelections(
            decisions=tuple(
                m.Infra.SemanticRenameSelection(
                    qualified_name=f"{package.name}.service.{name}",
                    replacement_name="Renamed",
                    reason="Explicit inventory must resolve every selection",
                )
                for name in ("MissingFirst", "MissingSecond")
            )
        )
        with (
            infra.rope_workspace(root) as workspace,
            pytest.raises(ValueError, match="MissingFirst") as failure,
        ):
            FlextInfraCodemodSemanticApply.build_rename_plan(
                root, workspace, selections
            )
        tm.that(
            str(failure.value),
            eq=(
                "semantic rename has no inventoried source: "
                f"{package.name}.service.MissingFirst"
            ),
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
