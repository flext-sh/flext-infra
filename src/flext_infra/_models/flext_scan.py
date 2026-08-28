"""Bootstrap-safe FLEXT scan contracts."""

from __future__ import annotations

from typing import Annotated, ClassVar

from flext_core import m, t


class FlextInfraModelsFlextScan:
    """Models consumed by FLEXT scan before the flext_infra facade is loaded."""

    class FLEXTSymbolCandidate(m.ArbitraryTypesModel):
        """Unified symbol candidate used by FLEXT scan and rewrites."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        facade_name: Annotated[str, m.Field(description="Facade alias/import name")] = (
            ""
        )
        symbol: Annotated[t.NonEmptyStr, m.Field(description="Symbol name")]
        line: Annotated[t.PositiveInt, m.Field(description="Source line number")]
        end_line: Annotated[
            int | None,
            m.Field(description="Inclusive end line for multi-line declarations"),
        ] = None
        kind: Annotated[str, m.Field(description="constant|typevar|typealias")] = (
            "constant"
        )
        class_name: Annotated[str, m.Field(description="Target class name")] = ""

    class FLEXTScanReport(m.ArbitraryTypesModel):
        """Scan result for one FLEXT candidate file."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        file: Annotated[t.NonEmptyStr, m.Field(description="Absolute file path")]
        module: Annotated[t.NonEmptyStr, m.Field(description="Import module path")]
        constants_class: Annotated[
            str, m.Field(description="First constants/facade class name")
        ] = ""
        facade_alias: Annotated[str, m.Field(description="Facade alias letter")] = "c"
        candidates: t.VariadicTuple[FlextInfraModelsFlextScan.FLEXTSymbolCandidate] = (
            m.Field(default_factory=tuple, description="Module-level symbol candidates")
        )

    class FLEXTTargetSpec(m.ContractModel):
        """Specification for an FLEXT target family."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        family_alias: Annotated[
            t.NonEmptyStr, m.Field(description="Family alias letter")
        ]
        file_names: Annotated[frozenset[str], m.Field(description="File name patterns")]
        package_directory: Annotated[
            t.NonEmptyStr, m.Field(description="Package directory name")
        ]
        class_suffix: Annotated[t.NonEmptyStr, m.Field(description="Class suffix")]


__all__: list[str] = ["FlextInfraModelsFlextScan"]
