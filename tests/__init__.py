# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Infra package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _TYPE_CHECKING:
    from flext_tests import d, e, r, s, x

    from tests.constants import *
    from tests.fixtures import *
    from tests.fixtures_git import *
    from tests.git_service import *
    from tests.helpers import *
    from tests.models import *
    from tests.protocols import *
    from tests.refactor import *
    from tests.runner_service import *
    from tests.scenarios import *
    from tests.test_infra_refactor_rope_migrations import *
    from tests.typings import *
    from tests.unit import *
    from tests.unit._utilities import *
    from tests.unit.basemk import *
    from tests.unit.check import *
    from tests.unit.codegen import *
    from tests.unit.container import *
    from tests.unit.deps import *
    from tests.unit.discovery import *
    from tests.unit.docs import *
    from tests.unit.github import *
    from tests.unit.io import *
    from tests.unit.refactor import *
    from tests.unit.release import *
    from tests.unit.validate import *
    from tests.utilities import *
    from tests.workspace_factory import *
    from tests.workspace_scenarios import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = merge_lazy_imports(
    (
        "tests.refactor",
        "tests.unit",
    ),
    {
        "BrokenScenario": "tests.workspace_scenarios",
        "DependencyScenario": "tests.scenarios",
        "DependencyScenarios": "tests.scenarios",
        "EmptyScenario": "tests.workspace_scenarios",
        "FlextInfraTestConstants": "tests.constants",
        "FlextInfraTestHelpers": "tests.helpers",
        "FlextInfraTestModels": "tests.models",
        "FlextInfraTestProtocols": "tests.protocols",
        "FlextInfraTestTypes": "tests.typings",
        "FlextInfraTestUtilities": "tests.utilities",
        "FullScenario": "tests.workspace_scenarios",
        "GitScenario": "tests.scenarios",
        "GitScenarios": "tests.scenarios",
        "MinimalScenario": "tests.workspace_scenarios",
        "RealGitService": "tests.git_service",
        "RealSubprocessRunner": "tests.runner_service",
        "SubprocessScenario": "tests.scenarios",
        "SubprocessScenarios": "tests.scenarios",
        "TestNestedClassPropagationRopeMigration": "tests.test_infra_refactor_rope_migrations",
        "TestSymbolPropagatorRopeMigration": "tests.test_infra_refactor_rope_migrations",
        "WorkspaceFactory": "tests.workspace_factory",
        "WorkspaceScenario": "tests.scenarios",
        "WorkspaceScenarios": "tests.scenarios",
        "c": ("tests.constants", "FlextInfraTestConstants"),
        "constants": "tests.constants",
        "d": "flext_tests",
        "e": "flext_tests",
        "fixtures": "tests.fixtures",
        "fixtures_git": "tests.fixtures_git",
        "git_service": "tests.git_service",
        "h": "tests.helpers",
        "helpers": "tests.helpers",
        "m": ("tests.models", "FlextInfraTestModels"),
        "models": "tests.models",
        "p": ("tests.protocols", "FlextInfraTestProtocols"),
        "protocols": "tests.protocols",
        "r": "flext_tests",
        "real_docs_project": "tests.fixtures",
        "real_git_repo": "tests.fixtures_git",
        "real_makefile_project": "tests.fixtures",
        "real_python_package": "tests.fixtures",
        "real_toml_project": "tests.fixtures",
        "real_workspace": "tests.fixtures",
        "refactor": "tests.refactor",
        "runner_service": "tests.runner_service",
        "s": "flext_tests",
        "scenarios": "tests.scenarios",
        "t": ("tests.typings", "FlextInfraTestTypes"),
        "test_infra_refactor_rope_migrations": "tests.test_infra_refactor_rope_migrations",
        "typings": "tests.typings",
        "u": ("tests.utilities", "FlextInfraTestUtilities"),
        "unit": "tests.unit",
        "utilities": "tests.utilities",
        "workspace_factory": "tests.workspace_factory",
        "workspace_scenarios": "tests.workspace_scenarios",
        "x": "flext_tests",
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
