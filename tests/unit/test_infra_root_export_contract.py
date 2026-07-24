"""Root export contract for flext_infra external API (invariant-based).

Doctrine: the test does NOT freeze a copy of the generated ``__all__`` tuple
(that would be a second SSOT drifting from the codegen output). It asserts
the *laws* the generated contract must satisfy: deterministic ordering,
required public families present, no private/internal names, uniqueness.
"""

from __future__ import annotations

from flext_tests import tm

import flext_infra


class TestsFlextInfraRootExportContract:
    """Root package exports only the external API surface."""

    def test_root_all_is_sorted_and_unique(self) -> None:
        """Generated __all__ is deterministic: sorted and duplicate-free."""
        exports = tuple(flext_infra.__all__)
        tm.that(exports, eq=tuple(sorted(exports)))
        tm.that(len(exports), eq=len(set(exports)))

    def test_root_all_contains_required_public_families(self) -> None:
        """The canonical public families are present (not the exact list)."""
        exports = flext_infra.__all__
        required = (
            # config/settings SSOT singletons
            "config",
            "settings",
            # facade aliases (MRO layering c/t/p/m/u + operational r/e/x/h/d/s)
            "c",
            "t",
            "p",
            "m",
            "u",
            "r",
            "e",
            "x",
            "h",
            "d",
            "s",
            # public API + CLI entry points
            "FlextInfra",
            "FlextInfraCli",
            "infra",
            "main",
            "docs_main",
            # canonical facet classes
            "FlextInfraConstants",
            "FlextInfraTypes",
            "FlextInfraProtocols",
            "FlextInfraModels",
            "FlextInfraUtilities",
            "FlextInfraServiceBase",
            # dunder metadata
            "__version__",
            "__version_info__",
        )
        for name in required:
            tm.that(exports, has=name)

    def test_root_all_excludes_private_and_internal_names(self) -> None:
        """No leading-underscore names (beyond dunder) and no internal classes."""
        exports = flext_infra.__all__
        for name in exports:
            if name.startswith("_"):
                tm.that(name.startswith("__") and name.endswith("__"), eq=True)
        internal_names = (
            "FlextInfraConfig",
            "FlextInfraCodegenLazyInit",
            "FlextInfraConstantsBase",
            "FlextInfraGate",
            "FlextInfraSettings",
            "FlextInfraTypesAdapters",
            "FlextInfraWorkspaceChecker",
        )
        for name in internal_names:
            tm.that(exports, lacks=name)
            tm.that(hasattr(flext_infra, name), eq=False)

    def test_root_all_members_resolve_as_attributes(self) -> None:
        """Every exported name resolves on the package (lazy imports wired)."""
        for name in flext_infra.__all__:
            tm.that(hasattr(flext_infra, name), eq=True)
