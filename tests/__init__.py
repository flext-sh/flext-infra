# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Tests package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _t.TYPE_CHECKING:
    import tests.conftest as _tests_conftest

    conftest = _tests_conftest
    import tests.constants as _tests_constants

    constants = _tests_constants
    import tests.fixtures as _tests_fixtures
    from tests.constants import TestsFlextInfraConstants, TestsFlextInfraConstants as c

    fixtures = _tests_fixtures
    import tests.fixtures_git as _tests_fixtures_git

    fixtures_git = _tests_fixtures_git
    import tests.git_service as _tests_git_service

    git_service = _tests_git_service
    import tests.helpers as _tests_helpers

    helpers = _tests_helpers
    import tests.integration as _tests_integration
    from tests.helpers import TestsFlextInfraHelpers

    integration = _tests_integration
    import tests.models as _tests_models

    models = _tests_models
    import tests.protocols as _tests_protocols
    from tests.models import TestsFlextInfraModels, TestsFlextInfraModels as m

    protocols = _tests_protocols
    import tests.refactor as _tests_refactor
    from tests.protocols import TestsFlextInfraProtocols, TestsFlextInfraProtocols as p

    refactor = _tests_refactor
    import tests.runner_service as _tests_runner_service

    runner_service = _tests_runner_service
    import tests.scenarios as _tests_scenarios

    scenarios = _tests_scenarios
    import tests.test_infra_refactor_rope_migrations as _tests_test_infra_refactor_rope_migrations

    test_infra_refactor_rope_migrations = _tests_test_infra_refactor_rope_migrations
    import tests.typings as _tests_typings

    typings = _tests_typings
    import tests.unit as _tests_unit
    from tests.typings import TestsFlextInfraTypes, TestsFlextInfraTypes as t

    unit = _tests_unit
    import tests.utilities as _tests_utilities

    utilities = _tests_utilities
    import tests.workspace_factory as _tests_workspace_factory
    from tests.utilities import TestsFlextInfraUtilities, TestsFlextInfraUtilities as u

    workspace_factory = _tests_workspace_factory
    import tests.workspace_scenarios as _tests_workspace_scenarios

    workspace_scenarios = _tests_workspace_scenarios
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
