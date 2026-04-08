# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    from tests import (
        conftest,
        constants,
        fixtures,
        fixtures_git,
        git_service,
        helpers,
        integration,
        models,
        protocols,
        refactor,
        runner_service,
        scenarios,
        test_infra_refactor_rope_migrations,
        typings,
        unit,
        utilities,
        workspace_factory,
        workspace_scenarios,
    )
    from tests.constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c
    from tests.helpers import TestsFlextInfraHelpers
    from tests.models import TestsFlextInfraModels, TestsFlextInfraModels as m
    from tests.protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p
    from tests.typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t
    from tests.utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u

    from flext_core.decorators import FlextDecorators as d
    from flext_core.exceptions import FlextExceptions as e
    from flext_core.handlers import FlextHandlers as h
    from flext_core.mixins import FlextMixins as x
    from flext_core.result import FlextResult as r
    from flext_core.service import FlextService as s
_LAZY_IMPORTS = merge_lazy_imports(
    (
        "tests.integration",
        "tests.refactor",
        "tests.unit",
    ),
    {
        "TestsFlextInfraConstants": ("tests.constants", "TestsFlextInfraConstants"),
        "TestsFlextInfraHelpers": ("tests.helpers", "TestsFlextInfraHelpers"),
        "TestsFlextInfraModels": ("tests.models", "TestsFlextInfraModels"),
        "TestsFlextInfraProtocols": ("tests.protocols", "TestsFlextInfraProtocols"),
        "TestsFlextInfraTypes": ("tests.typings", "TestsFlextInfraTypes"),
        "TestsFlextInfraUtilities": ("tests.utilities", "TestsFlextInfraUtilities"),
        "c": ("tests.constants", "TestsFlextInfraConstants"),
        "conftest": "tests.conftest",
        "constants": "tests.constants",
        "d": ("flext_core.decorators", "FlextDecorators"),
        "e": ("flext_core.exceptions", "FlextExceptions"),
        "fixtures": "tests.fixtures",
        "fixtures_git": "tests.fixtures_git",
        "git_service": "tests.git_service",
        "h": ("flext_core.handlers", "FlextHandlers"),
        "helpers": "tests.helpers",
        "integration": "tests.integration",
        "m": ("tests.models", "TestsFlextInfraModels"),
        "models": "tests.models",
        "p": ("tests.protocols", "TestsFlextInfraProtocols"),
        "protocols": "tests.protocols",
        "r": ("flext_core.result", "FlextResult"),
        "refactor": "tests.refactor",
        "runner_service": "tests.runner_service",
        "s": ("flext_core.service", "FlextService"),
        "scenarios": "tests.scenarios",
        "t": ("tests.typings", "TestsFlextInfraTypes"),
        "test_infra_refactor_rope_migrations": "tests.test_infra_refactor_rope_migrations",
        "typings": "tests.typings",
        "u": ("tests.utilities", "TestsFlextInfraUtilities"),
        "unit": "tests.unit",
        "utilities": "tests.utilities",
        "workspace_factory": "tests.workspace_factory",
        "workspace_scenarios": "tests.workspace_scenarios",
        "x": ("flext_core.mixins", "FlextMixins"),
    },
)
_ = _LAZY_IMPORTS.pop("cleanup_submodule_namespace", None)
_ = _LAZY_IMPORTS.pop("install_lazy_exports", None)
_ = _LAZY_IMPORTS.pop("lazy_getattr", None)
_ = _LAZY_IMPORTS.pop("logger", None)
_ = _LAZY_IMPORTS.pop("merge_lazy_imports", None)
_ = _LAZY_IMPORTS.pop("output", None)
_ = _LAZY_IMPORTS.pop("output_reporting", None)

__all__ = [
    "TestsFlextInfraConstants",
    "TestsFlextInfraHelpers",
    "TestsFlextInfraModels",
    "TestsFlextInfraProtocols",
    "TestsFlextInfraTypes",
    "TestsFlextInfraUtilities",
    "c",
    "conftest",
    "constants",
    "d",
    "e",
    "fixtures",
    "fixtures_git",
    "git_service",
    "h",
    "helpers",
    "integration",
    "m",
    "models",
    "p",
    "protocols",
    "r",
    "refactor",
    "runner_service",
    "s",
    "scenarios",
    "t",
    "test_infra_refactor_rope_migrations",
    "typings",
    "u",
    "unit",
    "utilities",
    "workspace_factory",
    "workspace_scenarios",
    "x",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
