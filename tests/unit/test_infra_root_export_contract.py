"""Root export contract for flext_infra external API."""

from __future__ import annotations

import flext_infra

_EXPECTED_ROOT_EXPORTS: tuple[str, ...] = (
    "FlextInfra",
    "FlextInfraCli",
    "FlextInfraConstants",
    "FlextInfraEnforcementPytestPlugin",
    "FlextInfraModels",
    "FlextInfraProjectSelectionServiceBase",
    "FlextInfraProtocols",
    "FlextInfraProtocolsBase",
    "FlextInfraServiceBase",
    "FlextInfraSettings",
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
    "d",
    "e",
    "h",
    "infra",
    "m",
    "main",
    "p",
    "r",
    "s",
    "t",
    "u",
    "x",
)


class TestsFlextInfraRootExportContract:
    """Root package exports only the external API surface."""

    def test_root_all_is_external_api_allowlist(self) -> None:
        """Root __all__ stays pinned to the external API."""
        assert tuple(flext_infra.__all__) == _EXPECTED_ROOT_EXPORTS

    def test_root_does_not_resolve_internal_symbols(self) -> None:
        """Implementation classes remain available only from owning modules."""
        internal_names = (
            "FlextInfraCodegenLazyInit",
            "FlextInfraConstantsBase",
            "FlextInfraGate",
            "FlextInfraTypesAdapters",
            "FlextInfraWorkspaceChecker",
        )
        for name in internal_names:
            assert name not in flext_infra.__all__
            assert not hasattr(flext_infra, name)
