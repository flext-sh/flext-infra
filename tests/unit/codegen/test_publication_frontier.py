"""Verify ordered publication ownership with real journaled filesystem effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import m, p, tm


class TestsPublicationFrontier:
    """Historical sources advance only through actual native publication effects."""

    @staticmethod
    @pytest.mark.parametrize("valid_payload", [False, True])
    def test_unchanged_files_require_their_real_staged_consumer(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        valid_payload: bool,
    ) -> None:
        """Unchanged bytes still require native model validation before acceptance."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra import r
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
)
from tests import c, m, p, t, tm, u
tmp_path = Path(sys.argv[2])
valid_payload = sys.argv[3] == "True"
root = u.Tests.git_repository(tmp_path)
target = root / "payload.json"
payload = (
    m.Infra.GitRepoRequest(repo_root=root).model_dump_json()
    if valid_payload
    else "{}"
)
tm.ok(u.Cli.atomic_write_text_file(target, payload))
before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True))
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root),
    producer=tm.ok(
        FlextInfraCodegenPreconditions.capture_producer(
            runtime_root, entrypoint=FlextInfraCodegenTransaction
        )
    ),
)
roots = {"@unchanged": root}
validated: p.Result[m.Infra.GitRepoRequest] | None = None

def consume(
    session: m.Infra.CodegenTransactionSession,
    _publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
) -> p.Result[m.Infra.CodegenTransactionSession]:
    global validated
    content = u.Cli.atomic_read_binary_file_state(target, required=True)
    if content.failure:
        return r[m.Infra.CodegenTransactionSession].from_failure(content)
    validated = r[m.Infra.GitRepoRequest].create_from_callable(
        lambda: m.Infra.GitRepoRequest.model_validate_json(
            tm.not_none(content.value.content)
        )
    )
    return validated.map(lambda _request: session)

analysis = m.Infra.CodegenPhaseAnalysis(
    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
    inputs=(before,),
    files=(
        m.Infra.CodegenFilePlan(
            project=root,
            path=target,
            before=before,
            desired_content=before.content,
            desired_mode=before.mode,
            source_states=(before,),
        ),
    ),
)
published = owner.run_files_locked(
    roots,
    lambda scope_root: owner.publish_file_phase_locked(
        scope_root,
        roots,
        analysis,
        m.Infra.CodegenPhasePublicationPolicy(
            directories=(), staged_validator=consume
        ),
    ),
)
assert validated is not None
if valid_payload:
    tm.that(tm.ok(published), eq=())
    tm.that(tm.ok(validated).repo_root, eq=root)
else:
    tm.fail(published)
    tm.that(isinstance(published.exception, m.ValidationError), eq=True)
    tm.that(published.exception is validated.exception, eq=True)
    tm.that(published.error, eq=validated.error)
tm.that(
    tm.ok(u.Cli.atomic_read_binary_file_state(target, required=True)),
    eq=before,
)
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            str(valid_payload),
        )

    @staticmethod
    @pytest.mark.parametrize("mutation", ["input-only", "aggregate-output"])
    def test_publication_rejects_source_drift_and_unowned_aggregate_outputs(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Consumed inputs stay physical, and only actual batches own outputs."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra.codegen import (
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsJournal,
    FlextInfraMiseArtifactsVerification,
)
from flext_infra.docs import FlextInfraDocGenerator
from tests import c, m, tm, u
tmp_path = Path(sys.argv[2])
mutation = sys.argv[3]
workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
member = workspace / "flext-a"
guide = member / c.Infra.DIR_DOCS / "guides/operator.md"
guide.parent.mkdir(parents=True, exist_ok=True)
guide.write_text("# Captured guide\n", encoding="utf-8")
generator = FlextInfraDocGenerator(
    repository_root=workspace,
    selected_projects=["flext-a"],
    include_root=False,
)
producer = tm.ok(
    FlextInfraCodegenPreconditions.capture_producer(
        runtime_root,
        entrypoint=generator.prepare_batches,
        collaborators=(generator.publish_batch,),
    )
)
receipts: list[m.Infra.CodegenPhaseOutcome] = []
bundle = tm.ok(
    next(
        generator.prepare_batches(
            producer=producer, publication_receipts=receipts
        )
    )
)
tm.that(guide in {state.path for state in bundle.source_states}, eq=True)
tm.ok(generator.publish_batch(bundle, publication_receipts=receipts))
tm.that(
    any(
        output.path == guide
        for receipt in receipts
        for output in receipt.outputs
    ),
    eq=False,
)
request = u.Tests.conform_request(
    workspace,
    what=c.Infra.CodegenConformSurface.ALL,
    scope=c.Infra.CodegenConformScope.ALL,
    mode=c.Infra.CodegenConformMode.APPLY,
)
published = tm.ok(
    FlextInfraCodegenTransaction.publish_operation_receipt(
        request,
        tuple(receipts),
        scope_roots=(member,),
        completed=True,
    )
)
if mutation == "input-only":
    guide.write_text("# Changed guide\n", encoding="utf-8")
    observed = FlextInfraMiseArtifactsVerification.publication_states_current(
        published
    )
    tm.fail(observed)
    tm.that(guide.read_text(encoding="utf-8"), eq="# Changed guide\n")
else:
    unowned = tmp_path / "unowned.bin"
    tm.ok(u.Cli.atomic_write_text_file(unowned, "No publishing batch\n"))
    state = tm.ok(u.Cli.atomic_read_binary_file_state(unowned, required=True))
    output = tm.ok(
        FlextInfraMiseArtifactsJournal.source_record("output", state)
    )
    injected = published.model_copy(update={"outputs": (output,)})
    observed = FlextInfraMiseArtifactsVerification.publication_states_current(
        injected
    )
    tm.fail(observed)
    tm.that(unowned.read_bytes(), eq=b"No publishing batch\n")
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            mutation,
        )

    @staticmethod
    def test_public_receipt_preserves_native_cause_and_immutable_boundary() -> None:
        """Shared presets retain causal evidence and reject unauthorized state."""
        cause = ValueError("native publication failure")
        receipt = m.Infra.CodegenPhaseOutcome(exception=cause, error=str(cause))
        tm.that(receipt.exception is cause, eq=True)
        tm.that(
            m.Infra.CodegenPhaseOutcome.model_validate_json(
                receipt.model_dump_json()
            ).error,
            eq=str(cause),
        )
        with pytest.raises(m.ValidationError):
            receipt.error = ""
        with pytest.raises(m.ValidationError):
            m.Infra.CodegenPhaseOutcome.model_validate({"unowned": True})

    @staticmethod
    @pytest.mark.parametrize("external_drift", [False, True])
    def test_ordered_batches_authenticate_their_shared_destination(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        external_drift: bool,
    ) -> None:
        """Ordered batches share a destination, and external drift fails it."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra import infra, r
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
)
from tests import c, m, p, t, tm, u
tmp_path = Path(sys.argv[2])
external_drift = sys.argv[3] == "True"
root = u.Tests.git_repository(tmp_path)
target = root / c.Infra.MAKEFILE_FILENAME
tm.ok(u.Cli.atomic_write_text_file(target, "VALUE := initial\n"))
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root),
    producer=tm.ok(
        FlextInfraCodegenPreconditions.capture_producer(
            runtime_root, entrypoint=FlextInfraCodegenTransaction
        )
    ),
)
roots = {"@bootstrap-0": root}
receipts: list[m.Infra.CodegenPhaseOutcome] = []
for value in ("first", "second"):
    if value == "second" and external_drift:
        tm.ok(u.Cli.atomic_write_text_file(target, "VALUE := external\n"))
    before = tm.ok(
        u.Cli.atomic_read_binary_file_state(target, required=True),
    )
    plan = m.Infra.CodegenFilePlan(
        project=root,
        path=target,
        before=before,
        desired_content=f"VALUE := {value}\n".encode(c.DEFAULT_ENCODING),
        desired_mode=tm.not_none(before.mode),
        source_states=(before,),
    )

    def publish(
        scope: Path,
        *,
        before: m.Cli.AtomicFileState = before,
        plan: m.Infra.CodegenFilePlan = plan,
    ) -> p.Result[t.VariadicTuple[Path]]:
        started = owner.begin_files_locked(scope, roots, (before,))
        if started.failure:
            return r[t.VariadicTuple[Path]].from_failure(started)
        appended = owner.append_phase_locked(
            started.value,
            c.Infra.CodegenStagedFilePhase.CONFORM_BOOTSTRAP,
            (plan,),
        )
        if appended.failure:
            return r[t.VariadicTuple[Path]].from_failure(appended)
        return owner.commit_locked(
            appended.value,
            publication_receipts=receipts,
        )

    tm.ok(owner.run_files_locked(roots, publish))
request = u.Tests.conform_request(
    root,
    what=c.Infra.CodegenConformSurface.MAKEFILE,
    scope=c.Infra.CodegenConformScope.SELF,
    mode=c.Infra.CodegenConformMode.APPLY,
)
composed = owner.publish_operation_receipt(
    request,
    tuple(receipts),
    scope_roots=(root,),
    completed=True,
)
if external_drift:
    tm.that(composed.failure, eq=True)
    tm.that(composed.error or "", has="differs from preceding output")
else:
    tm.ok(composed)
    tm.that(
        target.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE := second\n"
    )
    tm.ok(
        infra.codegen_conform(
            request.model_copy(
                update={"mode": c.Infra.CodegenConformMode.CHECK}
            ),
        ),
    )
    tm.that(
        receipts[0].sources[0].sha256,
        eq=u.Cli.sha256_bytes(b"VALUE := initial\n"),
    )
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            str(external_drift),
        )
