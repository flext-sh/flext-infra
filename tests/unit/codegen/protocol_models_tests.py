"""Authenticated projection transactions independent of model-shaped mirrors.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import p


class TestsProjectionTransactions:
    """Retain source-epoch guarantees through the public native transaction owner."""

    @staticmethod
    @pytest.mark.parametrize("change", [None, "content", "membership"])
    def test_projected_outputs_keep_original_transaction_inputs(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        change: str | None,
    ) -> None:
        """Virtual outputs publish, but original file and membership changes fail."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from tests import c, m, tm, u
from flext_infra import config
root, _package = u.Tests.create_lazy_init_workspace(Path(sys.argv[2]))
change = None if sys.argv[3] == "None" else sys.argv[3]
source = root / "original-input.txt"
source.write_bytes(b"original input\n")
target = root / "unchanged-output.txt"
requested_change = None
phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root)
)
roots = owner.capability_roots(phase.value, (root,))

def publish(scope_root):
    original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
    before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
    plan = m.Infra.CodegenFilePlan(
        project=root, path=target, before=before,
        desired_content=b"published output\n",
        desired_mode=config.Infra.codegen.modes.file_default,
    )
    with u.Infra.facade_source_project(
        root, source_states=(original,), declared_files=(plan,)
    ) as binding:
        assert binding[0].source_bytes(source) == original.content
        assert target in binding[0].source_children(root)
        states, directories, topology = binding[1]()
        physical = next(item for item in directories
            if item.root.path == root and item.membership_queried)
        assert target.name not in {item.name for item in physical.entries}
    if requested_change == "content":
        source.write_bytes(b"changed input\n")
    elif requested_change == "membership":
        (root / "unplanned-input.txt").write_bytes(b"unplanned\n")
    plan = plan.model_copy(update={
        "source_states": states, "source_directories": directories,
        "source_query_topology": topology,
    })
    analysis = m.Infra.CodegenPhaseAnalysis(
        phase=phase, files=(plan,), inputs=states,
        source_directories=directories, source_query_topology=topology,
    )
    return owner.publish_file_phase_locked(
        scope_root, roots, analysis,
        m.Infra.CodegenPhasePublicationPolicy(directories=()),
    )

tm.ok(owner.run_files_locked(roots, publish))
assert target.read_bytes() == b"published output\n"
target = root / "planned-output.txt"
requested_change = change
if change == "membership":
    from pytest import raises
    with raises(ValueError, match="source directory membership changed:.*unplanned-input.txt"):
        owner.run_files_locked(roots, publish)
    assert not target.exists()
else:
    outcome = owner.run_files_locked(roots, publish)
    if change == "content":
        assert outcome.failure
        assert not target.exists()
    else:
        tm.ok(outcome)
        assert target.read_bytes() == b"published output\n"
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            str(change),
        )

    @staticmethod
    @pytest.mark.parametrize("owned_parent", [True, False])
    def test_missing_parent_epoch_requires_a_journal_owned_transition(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        owned_parent: bool,
    ) -> None:
        """Cross-phase input absence survives only the journal's actual parent gain."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra import config
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
    FlextInfraStagedPackage,
)
from tests import c, m, r, tm, u
root, _package = u.Tests.create_lazy_init_workspace(Path(sys.argv[2]))
owned_parent = sys.argv[3] == "True"
source = root / "input-parent" / "input.txt"
target = root / "owned-parent-output.txt"
phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root)
)
roots = owner.capability_roots(phase.value, (root,))

def publish(scope_root):
    original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=False))
    assert original.parent_device is None and original.content is None
    before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
    session = tm.ok(owner.begin_files_locked(scope_root, roots, (original,)))
    if owned_parent:
        session = tm.ok(owner.append_directories_locked(
            session, c.Infra.CodegenStagedFilePhase.LAYOUT, (source.parent,)
        ))
    else:
        source.parent.mkdir()
    bound = FlextInfraMiseArtifactsVerification.session_input_states((original,), session)
    if owned_parent:
        accepted = tm.ok(bound)
        assert accepted[0].content is None and accepted[0].device is None
        assert accepted[0].parent_inode == source.parent.stat().st_ino
        candidate = tm.ok(FlextInfraStagedPackage.plan_sources(
            root, {}, options=m.Infra.StageSourceOptions(inputs=accepted)
        ))
        assert next(item for item in candidate.inputs if item.path == source) == accepted[0]
        assert original.parent_inode is None and original.content is None
    else:
        assert bound.failure
    plan = m.Infra.CodegenFilePlan(
        project=root, path=target, before=before,
        desired_content=b"owned transition\n",
        desired_mode=config.Infra.codegen.modes.file_default,
        source_states=(original,),
    )
    appended = owner.append_phase_locked(session, phase, (plan,))
    if not owned_parent:
        assert appended.failure
        assert "parent" in appended.error and str(source.parent) in appended.error
        assert source.parent.is_dir() and not target.exists()
        return r[tuple[Path, ...]].from_failure(appended)
    ready = tm.ok(appended)
    journal, _state = tm.ok(FlextInfraMiseArtifactsJournal.read(ready.plan.layout))
    assert any(item.created is not None and item.created.path == source.parent
        for item in journal.directories)
    records = [item for item in journal.sources if item.path == source]
    assert any(item.phase == phase for item in records)
    assert all(item.parent_device is None and item.absent_parent is not None
        and source.parent in item.absent_parent.directories for item in records)
    return owner.commit_locked(ready)

result = owner.run_files_locked(roots, publish)
if owned_parent:
    tm.ok(result)
    assert target.read_bytes() == b"owned transition\n"
else:
    assert result.failure and not target.exists()
    assert source.parent.is_dir()
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            str(owned_parent),
        )

    @staticmethod
    @pytest.mark.parametrize("change", [None, "content", "identity"])
    def test_candidate_inputs_advance_only_through_native_publication(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        change: str | None,
    ) -> None:
        """A candidate reads owned new bytes but rejects subsequent foreign changes."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenMiseArtifacts, FlextInfraCodegenTransaction
from tests import c, m, tm, u
root, _package = u.Tests.create_lazy_init_workspace(Path(sys.argv[2]))
change = None if sys.argv[3] == "None" else sys.argv[3]
source = root / "publication-input.txt"
original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=False))
phase = c.Infra.CodegenStagedFilePhase.LAZY_INIT
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root)
)
roots = owner.capability_roots(phase.value, (root,))

def publish(scope_root):
    session = tm.ok(owner.begin_files_locked(scope_root, roots, (original,)))
    plan = m.Infra.CodegenFilePlan(
        project=root, path=source, before=original,
        desired_content=b"owned bytes\n",
        desired_mode=config.Infra.codegen.modes.file_default,
        source_states=(original,),
    )
    ready = tm.ok(owner.append_phase_locked(session, phase, (plan,)))
    receipt = tm.ok(owner.publication_outcome(ready, completed=True))
    return owner.commit_locked(ready).map(lambda _: receipt)

receipt = tm.ok(owner.run_files_locked(roots, publish))
assert original.content is None and original.device is None
if change == "content":
    source.write_bytes(b"foreign bytes\n")
elif change == "identity":
    foreign = root / "foreign-input.txt"
    foreign.write_bytes(b"owned bytes\n")
    foreign.chmod(source.stat().st_mode)
    foreign.replace(source)
reader = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root),
    prior_publications=(receipt,),
)
view = reader.preview_sources(
    root, {}, lambda candidate, _: (candidate / source.name).read_bytes(),
    options=m.Infra.CodegenSourcePreviewOptions(inputs=(original,), runtime_check=False),
)
if change is None:
    assert tm.ok(view) == b"owned bytes\n"
else:
    assert view.failure
assert original.content is None and original.device is None
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            str(change),
        )
