"""Census removal evidence: unanchored definitions are never removal candidates.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import infra
from flext_infra.refactor.census import FlextInfraRefactorCensus
from tests import m, tm


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
            is_facade_member=False,
            references_count=references_count,
            reference_evidence_collected=evidence_collected,
        )

    def test_zero_references_without_evidence_is_not_unused(self) -> None:
        """An unanchored search never yields an unused classification."""
        record = self._object(
            name="PublicThing",
            references_count=0,
            evidence_collected=False,
        )

        assert FlextInfraRefactorCensus.unused(record) is False

    def test_zero_references_with_evidence_is_unused(self) -> None:
        """A completed search over zero references classifies the definition."""
        record = self._object(
            name="PublicThing",
            references_count=0,
            evidence_collected=True,
        )

        assert FlextInfraRefactorCensus.unused(record) is True

    def test_referenced_definition_is_never_unused(self) -> None:
        """Collected references keep the definition classified as used."""
        record = self._object(
            name="PublicThing",
            references_count=2,
            evidence_collected=True,
        )

        assert FlextInfraRefactorCensus.unused(record) is False

    @staticmethod
    def test_service_composes_validated_options(tmp_path: Path) -> None:
        """Service construction retains request filters and immutable options."""
        json_output = tmp_path / "census.json"
        impact_map_output = tmp_path / "impact.json"
        options = m.Infra.CensusInput(
            repository_root=tmp_path,
            kinds=("function",),
            rules=("unused",),
            families=("c",),
            json_output=str(json_output),
            impact_map_output=str(impact_map_output),
            include_local_scopes=False,
        )
        service = FlextInfraRefactorCensus(
            workspace_factory=infra.rope_workspace,
            repository_root=options.repository_root,
            source_preview=infra.source_preview(options.repository_root),
            options=options,
        )
        tm.that(service.options, eq=options)
        tm.that(service.json_output_path, eq=json_output)
        tm.that(service.impact_map_output_path, eq=impact_map_output)
        tm.that(service.options.include_local_scopes, eq=options.include_local_scopes)
        for name, expected in m.Infra.CensusOptions.model_config.items():
            assert name in service.model_config
            tm.that(service.model_config.get(name), eq=expected)

    @staticmethod
    def test_service_defaults_use_declared_options(tmp_path: Path) -> None:
        """Omitted options are constructed by the canonical options model."""
        service = FlextInfraRefactorCensus(
            workspace_factory=infra.rope_workspace,
            repository_root=tmp_path,
            source_preview=infra.source_preview(tmp_path),
        )
        tm.that(service.options, eq=m.Infra.CensusOptions())
