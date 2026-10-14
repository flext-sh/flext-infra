"""Real model consumers of native source provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from inspect import getfile
from pathlib import Path

import pytest
from pydantic import RootModel
from typing_inspection.introspection import AnnotationSource, inspect_annotation

from flext_core import m
from flext_infra.codegen import FlextInfraCodegenPreconditions
from tests import p, tm


class TestsFlextInfraNativeModelProvenance:
    """Conditional metaclasses and nested presets keep their real runtime contract."""

    @staticmethod
    @pytest.mark.parametrize(
        "entrypoint",
        [RootModel.model_construct, inspect_annotation, m.ContractModel.model_validate],
    )
    def test_real_model_module_retains_authenticated_native_sources(
        entrypoint: p.AttributeProbe,
    ) -> None:
        """Validate real model presets and generated annotation inspection payloads."""
        root = RootModel[str].model_validate("wire-value")
        tm.that(root.model_dump(), eq="wire-value")
        inspection = inspect_annotation(str, annotation_source=AnnotationSource.ANY)
        tm.that(inspection.type, eq=str)
        preset = m.ContractModel.model_validate({})
        tm.that(preset.model_dump(), eq={})
        expected_source = Path(getfile(entrypoint)).resolve()
        admission = tm.ok(
            FlextInfraCodegenPreconditions.capture_producer(
                Path.cwd(), entrypoint=entrypoint
            )
        )
        assert admission.generator_reference is not None
        sources = admission.generator_reference.sources
        tm.that(sources, empty=False)
        tm.that(
            any(Path(source).resolve() == expected_source for _, source, _ in sources),
            eq=True,
        )
