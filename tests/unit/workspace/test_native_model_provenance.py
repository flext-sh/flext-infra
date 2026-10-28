"""Real model consumers of native source provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import m, tm


class TestsFlextInfraNativeModelProvenance:
    """Native observation contexts keep their real model contract."""

    @staticmethod
    def test_native_observation_defaults_preserve_mutable_evidence_contract() -> None:
        """Public contexts isolate defaults and validate incoming evidence records."""
        first = m.Infra.NativeObservationContext(paths=())
        second = m.Infra.NativeObservationContext(paths=())
        tm.that(first.evidence, eq=[])
        tm.that(first.evidence is not second.evidence, truth=True)

        record = m.Infra.NativeBindingEvidence(
            binding="builtins.len",
            kind="builtin",
            supplier="builtins",
            name="len",
            qualname="len",
        )
        first.evidence.append(record)
        tm.that(first.evidence, eq=[record])
        tm.that(second.evidence, eq=[])
        provided = m.Infra.NativeObservationContext(paths=(), evidence=[record])
        tm.that(provided.evidence, eq=[record])

        converted = m.Infra.NativeObservationContext.model_validate({
            "paths": (),
            "evidence": (),
        })
        converted.evidence.append(record)
        tm.that(converted.evidence, eq=[record])
        with pytest.raises(m.ValidationError, match="evidence"):
            m.Infra.NativeObservationContext.model_validate({
                "paths": (),
                "evidence": [{}],
            })
