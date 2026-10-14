"""Real model consumers of native source provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest
from pydantic import RootModel
from typing_inspection.introspection import AnnotationSource, inspect_annotation

from flext_core import m
from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from tests import tm


class TestsFlextInfraNativeModelProvenance:
    """Conditional metaclasses and nested presets keep their real runtime contract."""

    @staticmethod
    @pytest.mark.parametrize(
        "module_name",
        [
            RootModel.__module__,
            m.ContractModel.__module__,
            inspect_annotation.__module__,
        ],
    )
    def test_real_model_module_retains_authenticated_native_sources(
        module_name: str,
    ) -> None:
        """Validate real model presets and generated annotation inspection payloads."""
        root = RootModel[str].model_validate("wire-value")
        tm.that(root.model_dump(), eq="wire-value")
        inspection = inspect_annotation(str, annotation_source=AnnotationSource.ANY)
        tm.that(inspection.type, eq=str)
        module = import_module(module_name)
        assert module.__file__ is not None
        expected_source = Path(module.__file__).resolve()
        sources = FlextInfraWorkspaceEnvironmentProvenance.loaded_import_sources(
            module_name,
        ).unwrap()
        tm.that(sources, empty=False)
        tm.that(
            any(Path(source).resolve() == expected_source for _, source, _ in sources),
            eq=True,
        )
