"""Root export contract for flext_infra external API."""

from __future__ import annotations

from flext_tests import tm

import flext_infra

# mro-wkii.4.15: pin the generated direct config/settings singleton surface.
_EXPECTED_ROOT_EXPORTS: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraServiceBase",
    "FlextInfraTypes",
    "FlextInfraUtilities",
    "__author__",
    "__author_email__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "__version_info__",
    "basemk",
    "c",
    "config",
    "d",
    "docs_main",
    "e",
    "h",
    "infra",
    "m",
    "main",
    "p",
    "r",
    "s",
    "settings",
    "t",
    "u",
    "x",
)


class TestsFlextInfraRootExportContract:
    """Root package exports only the external API surface."""

    def test_root_all_is_external_api_allowlist(self) -> None:
        """Root __all__ stays pinned to the external API."""
        tm.that(tuple(flext_infra.__all__), eq=_EXPECTED_ROOT_EXPORTS)

    def test_root_does_not_resolve_internal_symbols(self) -> None:
        """Implementation classes remain available only from owning modules."""
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
            tm.that(flext_infra.__all__, lacks=name)
            tm.that(hasattr(flext_infra, name), eq=False)
