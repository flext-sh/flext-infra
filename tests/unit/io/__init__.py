# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Io package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if _TYPE_CHECKING:
    from flext_core import FlextTypes

    from tests.unit.io.test_infra_json_io import *
    from tests.unit.io.test_infra_output_edge_cases import *
    from tests.unit.io.test_infra_output_formatting import *
    from tests.unit.io.test_infra_terminal_detection import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = {
    "ANSI_RE": "tests.unit.io.test_infra_output_formatting",
    "SampleModel": "tests.unit.io.test_infra_json_io",
    "TestFlextInfraJsonService": "tests.unit.io.test_infra_json_io",
    "TestInfraOutputEdgeCases": "tests.unit.io.test_infra_output_edge_cases",
    "TestInfraOutputHeader": "tests.unit.io.test_infra_output_formatting",
    "TestInfraOutputMessages": "tests.unit.io.test_infra_output_formatting",
    "TestInfraOutputNoColor": "tests.unit.io.test_infra_output_edge_cases",
    "TestInfraOutputProgress": "tests.unit.io.test_infra_output_formatting",
    "TestInfraOutputStatus": "tests.unit.io.test_infra_output_formatting",
    "TestInfraOutputSummary": "tests.unit.io.test_infra_output_formatting",
    "TestMroFacadeMethods": "tests.unit.io.test_infra_output_edge_cases",
    "TestShouldUseColor": "tests.unit.io.test_infra_terminal_detection",
    "TestShouldUseUnicode": "tests.unit.io.test_infra_terminal_detection",
    "test_infra_json_io": "tests.unit.io.test_infra_json_io",
    "test_infra_output_edge_cases": "tests.unit.io.test_infra_output_edge_cases",
    "test_infra_output_formatting": "tests.unit.io.test_infra_output_formatting",
    "test_infra_terminal_detection": "tests.unit.io.test_infra_terminal_detection",
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
