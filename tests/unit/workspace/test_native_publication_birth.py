"""Real publication boundaries require their original authenticated objects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import p


class TestsNativePublicationBirth:
    """Typed transport preserves expectations without granting write authority."""

    @staticmethod
    @pytest.mark.parametrize("transport", ["original", "copy", "mapping", "json"])
    def test_reference_transport_cannot_authorize_a_publication(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        transport: str,
    ) -> None:
        """Only the reference born through the real import admits a new effect."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from tests import c, m, tm, u
root = u.Tests.git_repository(Path(sys.argv[2]))
transport = sys.argv[3]
producer = tm.ok(preconditions.capture_producer(
    runtime_root, entrypoint=FlextInfraCodegenTransaction))
reference = tm.not_none(producer.generator_reference)
if transport == "copy":
    reference = reference.model_copy()
elif transport == "mapping":
    reference = m.Infra.NativeImportReference.model_validate(reference.model_dump())
elif transport == "json":
    reference = m.Infra.NativeImportReference.model_validate_json(
        reference.model_dump_json())
producer = producer.model_copy(update={"generator_reference": reference})
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root), producer=producer)
target = root / "published.txt"
before = tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False))
analysis = m.Infra.CodegenPhaseAnalysis(
    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
    inputs=(),
    files=(m.Infra.CodegenFilePlan(
        project=root, path=target, before=before,
        desired_content=b"Authenticated publication\n",
        desired_mode=c.Infra.CONFIG_SPEC[1], source_states=()),))
roots = {"@birth": root}
published = owner.run_files_locked(
    roots, lambda scope_root: owner.publish_file_phase_locked(
        scope_root, roots, analysis,
        m.Infra.CodegenPhasePublicationPolicy(directories=())))
if transport == "original":
    tm.that(tm.ok(published), eq=(target,))
    tm.that(target.read_bytes(), eq=b"Authenticated publication\n")
else:
    tm.fail(published)
    tm.that(
        tm.ok(u.Cli.atomic_read_binary_file_state(target, required=False)), eq=before)
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            transport,
        )

    @staticmethod
    @pytest.mark.parametrize("transport", ["original", "copy", "mapping", "json"])
    def test_transported_outcomes_cannot_authorize_later_effects(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        transport: str,
    ) -> None:
        """A later transaction consumes only actual earlier publication receipts."""
        native_consumer(
            r"""sys.path.insert(0, sys.argv[1])
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from tests import c, m, tm, u
root = u.Tests.git_repository(Path(sys.argv[2]))
transport = sys.argv[3]
producer = tm.ok(preconditions.capture_producer(
    runtime_root, entrypoint=FlextInfraCodegenTransaction))
roots = {"@birth": root}
receipts = []
first = root / "first.txt"
first_before = tm.ok(u.Cli.atomic_read_binary_file_state(first, required=False))
first_analysis = m.Infra.CodegenPhaseAnalysis(
    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
    inputs=(),
    files=(m.Infra.CodegenFilePlan(
        project=root, path=first, before=first_before,
        desired_content=b"Retained earlier effect\n",
        desired_mode=c.Infra.CONFIG_SPEC[1], source_states=()),))
owner = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root), producer=producer)
tm.ok(owner.run_files_locked(
    roots, lambda scope_root: owner.publish_file_phase_locked(
        scope_root, roots, first_analysis,
        m.Infra.CodegenPhasePublicationPolicy(directories=()),
        publication_receipts=receipts)))
tm.that(len(receipts), eq=1)
receipt = receipts[0]
if transport == "copy":
    receipt = receipt.model_copy()
elif transport == "mapping":
    receipt = m.Infra.CodegenPhaseOutcome.model_validate(receipt.model_dump())
elif transport == "json":
    receipt = m.Infra.CodegenPhaseOutcome.model_validate_json(
        receipt.model_dump_json())
later = FlextInfraCodegenTransaction(
    FlextInfraCodegenMiseArtifacts(repository_root=root),
    producer=producer, prior_publications=(receipt,))
second = root / "second.txt"
second_before = tm.ok(u.Cli.atomic_read_binary_file_state(second, required=False))
second_analysis = m.Infra.CodegenPhaseAnalysis(
    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
    inputs=(),
    files=(m.Infra.CodegenFilePlan(
        project=root, path=second, before=second_before,
        desired_content=b"Dependent later effect\n",
        desired_mode=c.Infra.CONFIG_SPEC[1], source_states=()),))
published = later.run_files_locked(
    roots, lambda scope_root: later.publish_file_phase_locked(
        scope_root, roots, second_analysis,
        m.Infra.CodegenPhasePublicationPolicy(directories=())))
tm.that(first.read_bytes(), eq=b"Retained earlier effect\n")
if transport == "original":
    tm.that(tm.ok(published), eq=(second,))
    tm.that(second.read_bytes(), eq=b"Dependent later effect\n")
else:
    tm.fail(published)
    tm.that(tm.ok(u.Cli.atomic_read_binary_file_state(
        second, required=False)), eq=second_before)
""",
            str(Path(__file__).resolve().parents[3]),
            str(tmp_path),
            transport,
        )
