# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Io package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.io import (
        test_infra_json_io as test_infra_json_io,
        test_infra_output_edge_cases as test_infra_output_edge_cases,
        test_infra_output_formatting as test_infra_output_formatting,
        test_infra_terminal_detection as test_infra_terminal_detection,
    )
    from tests.unit.io.test_infra_json_io import (
        SampleModel as SampleModel,
        TestFlextInfraJsonService as TestFlextInfraJsonService,
    )
    from tests.unit.io.test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases as TestInfraOutputEdgeCases,
        TestInfraOutputNoColor as TestInfraOutputNoColor,
        TestMroFacadeMethods as TestMroFacadeMethods,
    )
    from tests.unit.io.test_infra_output_formatting import (
        ANSI_RE as ANSI_RE,
        TestInfraOutputHeader as TestInfraOutputHeader,
        TestInfraOutputMessages as TestInfraOutputMessages,
        TestInfraOutputProgress as TestInfraOutputProgress,
        TestInfraOutputStatus as TestInfraOutputStatus,
        TestInfraOutputSummary as TestInfraOutputSummary,
    )
    from tests.unit.io.test_infra_terminal_detection import (
        TestShouldUseColor as TestShouldUseColor,
        TestShouldUseUnicode as TestShouldUseUnicode,
    )

_LAZY_IMPORTS: Mapping[str, Sequence[str]] = {
    "ANSI_RE": ["tests.unit.io.test_infra_output_formatting", "ANSI_RE"],
    "SampleModel": ["tests.unit.io.test_infra_json_io", "SampleModel"],
    "TestFlextInfraJsonService": [
        "tests.unit.io.test_infra_json_io",
        "TestFlextInfraJsonService",
    ],
    "TestInfraOutputEdgeCases": [
        "tests.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputEdgeCases",
    ],
    "TestInfraOutputHeader": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputHeader",
    ],
    "TestInfraOutputMessages": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputMessages",
    ],
    "TestInfraOutputNoColor": [
        "tests.unit.io.test_infra_output_edge_cases",
        "TestInfraOutputNoColor",
    ],
    "TestInfraOutputProgress": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputProgress",
    ],
    "TestInfraOutputStatus": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputStatus",
    ],
    "TestInfraOutputSummary": [
        "tests.unit.io.test_infra_output_formatting",
        "TestInfraOutputSummary",
    ],
    "TestMroFacadeMethods": [
        "tests.unit.io.test_infra_output_edge_cases",
        "TestMroFacadeMethods",
    ],
    "TestShouldUseColor": [
        "tests.unit.io.test_infra_terminal_detection",
        "TestShouldUseColor",
    ],
    "TestShouldUseUnicode": [
        "tests.unit.io.test_infra_terminal_detection",
        "TestShouldUseUnicode",
    ],
    "test_infra_json_io": ["tests.unit.io.test_infra_json_io", ""],
    "test_infra_output_edge_cases": ["tests.unit.io.test_infra_output_edge_cases", ""],
    "test_infra_output_formatting": ["tests.unit.io.test_infra_output_formatting", ""],
    "test_infra_terminal_detection": [
        "tests.unit.io.test_infra_terminal_detection",
        "",
    ],
}

_EXPORTS: Sequence[str] = [
    "ANSI_RE",
    "SampleModel",
    "TestFlextInfraJsonService",
    "TestInfraOutputEdgeCases",
    "TestInfraOutputHeader",
    "TestInfraOutputMessages",
    "TestInfraOutputNoColor",
    "TestInfraOutputProgress",
    "TestInfraOutputStatus",
    "TestInfraOutputSummary",
    "TestMroFacadeMethods",
    "TestShouldUseColor",
    "TestShouldUseUnicode",
    "test_infra_json_io",
    "test_infra_output_edge_cases",
    "test_infra_output_formatting",
    "test_infra_terminal_detection",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, _EXPORTS)
