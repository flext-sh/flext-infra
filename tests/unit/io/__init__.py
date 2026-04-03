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
    from flext_core.constants import FlextConstants as c
    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.models import FlextModels as m
    from flext_core.protocols import FlextProtocols as p
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
    from flext_core.typings import FlextTypes as t
    from flext_core.utilities import FlextUtilities as u
    from tests.unit.io import (
        test_infra_json_io,
        test_infra_output_edge_cases,
        test_infra_output_formatting,
        test_infra_terminal_detection,
    )
    from tests.unit.io.test_infra_json_io import SampleModel, TestFlextInfraJsonService
    from tests.unit.io.test_infra_output_edge_cases import (
        TestInfraOutputEdgeCases,
        TestInfraOutputNoColor,
        TestMroFacadeMethods,
    )
    from tests.unit.io.test_infra_output_formatting import (
        ANSI_RE,
        TestInfraOutputHeader,
        TestInfraOutputMessages,
        TestInfraOutputProgress,
        TestInfraOutputStatus,
        TestInfraOutputSummary,
    )
    from tests.unit.io.test_infra_terminal_detection import (
        TestShouldUseColor,
        TestShouldUseUnicode,
    )

_LAZY_IMPORTS: FlextTypes.LazyImportIndex = {
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
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "test_infra_json_io": "tests.unit.io.test_infra_json_io",
    "test_infra_output_edge_cases": "tests.unit.io.test_infra_output_edge_cases",
    "test_infra_output_formatting": "tests.unit.io.test_infra_output_formatting",
    "test_infra_terminal_detection": "tests.unit.io.test_infra_terminal_detection",
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
