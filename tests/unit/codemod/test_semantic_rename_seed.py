"""Authenticated source campaigns and strict explicit rename artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

import pytest

from flext_infra import infra
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, tm, u


class TestsFlextInfraSemanticRenameSeed:
    """Source campaigns never weaken the explicit rename artifact contract."""

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
        tm.ok(
            FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                root, hydrated, state
            )
        )
        consumer.write_bytes(consumer.read_bytes() + b"# changed source epoch\n")
        tm.fail(
            FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
                root, hydrated, state
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
                campaign.source_directories, campaign.source_query_topology
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
            eq=f"semantic rename has no inventoried source: {package.name}.service.MissingFirst",
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original,)))
