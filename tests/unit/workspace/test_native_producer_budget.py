"""The real conform producer is admitted inside its cold-probe budget.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import tm


class TestsFlextInfraNativeProducerBudget:
    """Producer admission is bounded by the probe deadline, never by its caller."""

    @staticmethod
    @pytest.mark.slow
    def test_conform_producer_admission_completes_within_its_probe_budget() -> None:
        """Admit the producer `make gen`, `make setup` and `make upg` actually run.

        The cold native-reference probe runs under the declared short timeout;
        a capture slower than that budget fails the admission with
        ``timed_out=True`` (flext-zd80z), so a successful admission is the
        budget proof.
        """
        admission = tm.ok(
            FlextInfraCodegenPreconditions.capture_producer(
                Path.cwd(),
                entrypoint=FlextInfraCodegenConform.execute_request,
            )
        )
        reference = tm.not_none(admission.generator_reference)
        tm.that(reference.sources, empty=False)
