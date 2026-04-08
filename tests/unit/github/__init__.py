# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Github package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import tests.unit.github.main_cli_tests as _tests_unit_github_main_cli_tests

    main_cli_tests = _tests_unit_github_main_cli_tests
    import tests.unit.github.main_dispatch_tests as _tests_unit_github_main_dispatch_tests

    main_dispatch_tests = _tests_unit_github_main_dispatch_tests
    import tests.unit.github.main_integration_tests as _tests_unit_github_main_integration_tests

    main_integration_tests = _tests_unit_github_main_integration_tests
    import tests.unit.github.main_tests as _tests_unit_github_main_tests

    main_tests = _tests_unit_github_main_tests
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
_LAZY_IMPORTS = {
    "c": ("flext_core.constants", "FlextConstants"),
    "d": ("flext_core.decorators", "FlextDecorators"),
    "e": ("flext_core.exceptions", "FlextExceptions"),
    "h": ("flext_core.handlers", "FlextHandlers"),
    "m": ("flext_core.models", "FlextModels"),
    "main_cli_tests": "tests.unit.github.main_cli_tests",
    "main_dispatch_tests": "tests.unit.github.main_dispatch_tests",
    "main_integration_tests": "tests.unit.github.main_integration_tests",
    "main_tests": "tests.unit.github.main_tests",
    "p": ("flext_core.protocols", "FlextProtocols"),
    "r": ("flext_core.result", "FlextResult"),
    "s": ("flext_core.service", "FlextService"),
    "t": ("flext_core.typings", "FlextTypes"),
    "u": ("flext_core.utilities", "FlextUtilities"),
    "x": ("flext_core.mixins", "FlextMixins"),
}

__all__ = [
    "c",
    "d",
    "e",
    "h",
    "m",
    "main_cli_tests",
    "main_dispatch_tests",
    "main_integration_tests",
    "main_tests",
    "p",
    "r",
    "s",
    "t",
    "u",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
