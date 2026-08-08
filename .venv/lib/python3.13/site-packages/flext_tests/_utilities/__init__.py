# @generated AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Tests. Utilities package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if TYPE_CHECKING:
    from . import _files as _files, _matchers as _matchers
    from ._files._assertions import (
        FlextTestsFilesAssertionsMixin as FlextTestsFilesAssertionsMixin,
    )
    from ._files._batch import FlextTestsFilesBatchMixin as FlextTestsFilesBatchMixin
    from ._files._comparison import (
        FlextTestsFilesComparisonMixin as FlextTestsFilesComparisonMixin,
    )
    from ._files._contexts import (
        FlextTestsFilesContextsMixin as FlextTestsFilesContextsMixin,
    )
    from ._files._creation import (
        FlextTestsFilesCreationMixin as FlextTestsFilesCreationMixin,
    )
    from ._files._info import FlextTestsFilesInfoMixin as FlextTestsFilesInfoMixin
    from ._files._lifecycle import (
        FlextTestsFilesLifecycleMixin as FlextTestsFilesLifecycleMixin,
    )
    from ._files._reading import (
        FlextTestsFilesReadingMixin as FlextTestsFilesReadingMixin,
    )
    from ._matchers._assertions import (
        FlextTestsMatchersAssertionsMixin as FlextTestsMatchersAssertionsMixin,
    )
    from ._matchers._containment import (
        FlextTestsMatchersContainmentMixin as FlextTestsMatchersContainmentMixin,
    )
    from ._matchers._result import (
        FlextTestsMatchersResultMixin as FlextTestsMatchersResultMixin,
    )
    from ._matchers._scope import (
        FlextTestsMatchersScopeMixin as FlextTestsMatchersScopeMixin,
    )
    from ._matchers._that import (
        FlextTestsMatchersThatMixin as FlextTestsMatchersThatMixin,
    )
    from ._matchers._typeguards import (
        FlextTestsMatchersTypeGuardsMixin as FlextTestsMatchersTypeGuardsMixin,
    )
    from .container import (
        FlextTestsContainerHelpersUtilitiesMixin as FlextTestsContainerHelpersUtilitiesMixin,
    )
    from .files import FlextTestsFilesUtilitiesMixin as FlextTestsFilesUtilitiesMixin
    from .fixtures_dsl import FlextTestsFixturesDSLMixin as FlextTestsFixturesDSLMixin
    from .generic import (
        FlextTestsGenericHelpersUtilitiesMixin as FlextTestsGenericHelpersUtilitiesMixin,
    )
    from .handler import (
        FlextTestsHandlerHelpersUtilitiesMixin as FlextTestsHandlerHelpersUtilitiesMixin,
    )
    from .make import FlextTestsMakeUtilitiesMixin as FlextTestsMakeUtilitiesMixin
    from .make_contract import (
        FlextTestsMakeContractUtilitiesMixin as FlextTestsMakeContractUtilitiesMixin,
    )
    from .make_parsing import (
        FlextTestsMakeParsingUtilitiesMixin as FlextTestsMakeParsingUtilitiesMixin,
    )
    from .make_registry import (
        FlextTestsMakeRegistryUtilitiesMixin as FlextTestsMakeRegistryUtilitiesMixin,
    )
    from .make_rendering import (
        FlextTestsMakeRenderingUtilitiesMixin as FlextTestsMakeRenderingUtilitiesMixin,
    )
    from .matchers import (
        FlextTestsMatchersUtilities as FlextTestsMatchersUtilities,
        tm as tm,
    )
    from .payload import FlextTestsPayloadUtilities as FlextTestsPayloadUtilities
    from .result import FlextTestsResultUtilitiesMixin as FlextTestsResultUtilitiesMixin
    from .settings import (
        FlextTestsConfigHelpersUtilitiesMixin as FlextTestsConfigHelpersUtilitiesMixin,
    )
    from .testcontext import (
        FlextTestsTestContextUtilitiesMixin as FlextTestsTestContextUtilitiesMixin,
    )
    from .validator import (
        FlextTestsValidatorUtilitiesMixin as FlextTestsValidatorUtilitiesMixin,
    )
    from .workspace_cleanup import (
        FlextTestsWorkspaceCleanupUtilitiesMixin as FlextTestsWorkspaceCleanupUtilitiesMixin,
    )
    from .workspace_cleanup_git import (
        FlextTestsWorkspaceCleanupGitUtilitiesMixin as FlextTestsWorkspaceCleanupGitUtilitiesMixin,
    )
    from .workspace_cleanup_inspect import (
        FlextTestsWorkspaceCleanupInspectUtilitiesMixin as FlextTestsWorkspaceCleanupInspectUtilitiesMixin,
    )
    from .workspace_cleanup_paths import (
        FlextTestsWorkspaceCleanupPathsUtilitiesMixin as FlextTestsWorkspaceCleanupPathsUtilitiesMixin,
    )
    from .workspace_cleanup_plan import (
        FlextTestsWorkspaceCleanupPlanUtilitiesMixin as FlextTestsWorkspaceCleanupPlanUtilitiesMixin,
    )

_LAZY_MODULES: dict[str, tuple[str, ...]] = {
    "._files": ("_files",),
    "._files._assertions": ("FlextTestsFilesAssertionsMixin",),
    "._files._batch": ("FlextTestsFilesBatchMixin",),
    "._files._comparison": ("FlextTestsFilesComparisonMixin",),
    "._files._contexts": ("FlextTestsFilesContextsMixin",),
    "._files._creation": ("FlextTestsFilesCreationMixin",),
    "._files._info": ("FlextTestsFilesInfoMixin",),
    "._files._lifecycle": ("FlextTestsFilesLifecycleMixin",),
    "._files._reading": ("FlextTestsFilesReadingMixin",),
    "._matchers": ("_matchers",),
    "._matchers._assertions": ("FlextTestsMatchersAssertionsMixin",),
    "._matchers._containment": ("FlextTestsMatchersContainmentMixin",),
    "._matchers._result": ("FlextTestsMatchersResultMixin",),
    "._matchers._scope": ("FlextTestsMatchersScopeMixin",),
    "._matchers._that": ("FlextTestsMatchersThatMixin",),
    "._matchers._typeguards": ("FlextTestsMatchersTypeGuardsMixin",),
    ".container": ("FlextTestsContainerHelpersUtilitiesMixin",),
    ".files": ("FlextTestsFilesUtilitiesMixin",),
    ".fixtures_dsl": ("FlextTestsFixturesDSLMixin",),
    ".generic": ("FlextTestsGenericHelpersUtilitiesMixin",),
    ".handler": ("FlextTestsHandlerHelpersUtilitiesMixin",),
    ".make": ("FlextTestsMakeUtilitiesMixin",),
    ".make_contract": ("FlextTestsMakeContractUtilitiesMixin",),
    ".make_parsing": ("FlextTestsMakeParsingUtilitiesMixin",),
    ".make_registry": ("FlextTestsMakeRegistryUtilitiesMixin",),
    ".make_rendering": ("FlextTestsMakeRenderingUtilitiesMixin",),
    ".matchers": ("FlextTestsMatchersUtilities", "tm"),
    ".payload": ("FlextTestsPayloadUtilities",),
    ".result": ("FlextTestsResultUtilitiesMixin",),
    ".settings": ("FlextTestsConfigHelpersUtilitiesMixin",),
    ".testcontext": ("FlextTestsTestContextUtilitiesMixin",),
    ".validator": ("FlextTestsValidatorUtilitiesMixin",),
    ".workspace_cleanup": ("FlextTestsWorkspaceCleanupUtilitiesMixin",),
    ".workspace_cleanup_git": ("FlextTestsWorkspaceCleanupGitUtilitiesMixin",),
    ".workspace_cleanup_inspect": ("FlextTestsWorkspaceCleanupInspectUtilitiesMixin",),
    ".workspace_cleanup_paths": ("FlextTestsWorkspaceCleanupPathsUtilitiesMixin",),
    ".workspace_cleanup_plan": ("FlextTestsWorkspaceCleanupPlanUtilitiesMixin",),
}


_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}


_LAZY_IMPORTS = build_lazy_import_map(
    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, sort_keys=False
)

_PUBLIC_EXPORTS: tuple[str, ...] = (
    "FlextTestsConfigHelpersUtilitiesMixin",
    "FlextTestsContainerHelpersUtilitiesMixin",
    "FlextTestsFilesAssertionsMixin",
    "FlextTestsFilesBatchMixin",
    "FlextTestsFilesComparisonMixin",
    "FlextTestsFilesContextsMixin",
    "FlextTestsFilesCreationMixin",
    "FlextTestsFilesInfoMixin",
    "FlextTestsFilesLifecycleMixin",
    "FlextTestsFilesReadingMixin",
    "FlextTestsFilesUtilitiesMixin",
    "FlextTestsFixturesDSLMixin",
    "FlextTestsGenericHelpersUtilitiesMixin",
    "FlextTestsHandlerHelpersUtilitiesMixin",
    "FlextTestsMakeContractUtilitiesMixin",
    "FlextTestsMakeParsingUtilitiesMixin",
    "FlextTestsMakeRegistryUtilitiesMixin",
    "FlextTestsMakeRenderingUtilitiesMixin",
    "FlextTestsMakeUtilitiesMixin",
    "FlextTestsMatchersAssertionsMixin",
    "FlextTestsMatchersContainmentMixin",
    "FlextTestsMatchersResultMixin",
    "FlextTestsMatchersScopeMixin",
    "FlextTestsMatchersThatMixin",
    "FlextTestsMatchersTypeGuardsMixin",
    "FlextTestsMatchersUtilities",
    "FlextTestsPayloadUtilities",
    "FlextTestsResultUtilitiesMixin",
    "FlextTestsTestContextUtilitiesMixin",
    "FlextTestsValidatorUtilitiesMixin",
    "FlextTestsWorkspaceCleanupGitUtilitiesMixin",
    "FlextTestsWorkspaceCleanupInspectUtilitiesMixin",
    "FlextTestsWorkspaceCleanupPathsUtilitiesMixin",
    "FlextTestsWorkspaceCleanupPlanUtilitiesMixin",
    "FlextTestsWorkspaceCleanupUtilitiesMixin",
    "_files",
    "_matchers",
    "tm",
)

__all__: tuple[str, ...] = tuple(_PUBLIC_EXPORTS)

install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)
