"""Census removal evidence: unanchored definitions are never removal candidates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path


from flext_infra import m
from flext_infra.refactor.census import FlextInfraRefactorCensus


class TestsFlextInfraRefactorCensusRemovalEvidence:
    """Only a definition with collected reference evidence may be classified."""

    @staticmethod
    def _object(
        *,
        name: str,
        references_count: int,
        evidence_collected: bool,
    ) -> m.Infra.Object:
        """Build one census record with the classification inputs under test.

        Args:
            name: The name of the definition.
            references_count: The number of references collected.
            evidence_collected: Whether reference evidence has been collected.

        Returns:
            An instance of `m.Infra.Object` representing the census record.
        """
        return m.Infra.Object(
            name=name,
            kind="assignment",
            file_path=str(Path("scripts/generate.py")),
            line=20,
            project="demo",
            module_name="generate",
            scope_path=name,
        ).model_copy(
            update={
                "references_count": references_count,
                "reference_evidence_collected": evidence_collected,
            },
        )

    def test_zero_references_without_evidence_is_not_unused(self) -> None:
        """An unanchored search never yields an unused classification."""
        record = self._object(
            name="PublicThing",
            references_count=0,
            evidence_collected=False,
        )

        assert FlextInfraRefactorCensus._is_unused(record) is False

    def test_zero_references_with_evidence_is_unused(self) -> None:
        """A completed search over zero references classifies the definition."""
        record = self._object(
            name="PublicThing",
            references_count=0,
            evidence_collected=True,
        )

        assert FlextInfraRefactorCensus._is_unused(record) is True

    def test_referenced_definition_is_never_unused(self) -> None:
        """Collected references keep the definition classified as used."""
        record = self._object(
            name="PublicThing",
            references_count=2,
            evidence_collected=True,
        )

        assert FlextInfraRefactorCensus._is_unused(record) is False
