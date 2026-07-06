"""Render context models for codegen templates."""

from __future__ import annotations

from typing import ClassVar

from flext_cli import m
from flext_infra.typings import t


class FlextInfraModelsCodegenRender:
    """Typed render contexts for generated lazy-init files."""

    class LazyInitStandardRender(m.ArbitraryTypesModel):
        """Template context for standard lazy-init package rendering."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        type_checking_enabled: bool = m.Field(
            description="Whether TYPE_CHECKING imports are emitted.",
        )
        use_merge_lazy_imports: bool = m.Field(
            description="Whether child lazy registries are merged.",
        )
        runtime_import_lines: str = m.Field(
            description="Runtime import block rendered before lazy map setup.",
        )
        child_module_paths: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Child module paths passed to merge_lazy_imports.",
        )
        excluded_lazy_names: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Names excluded from merged child lazy registries.",
        )
        inline_constants: t.StrPairSequence = m.Field(
            default_factory=tuple,
            description="Inline constant assignments.",
        )
        eager_export_names: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Eager export names passed to install_lazy_exports.",
        )
        lazy_module_groups: t.StrSequencePairSequence = m.Field(
            default_factory=tuple,
            description="Lazy imports grouped by module.",
        )
        lazy_alias_groups: t.StrPairSequencePairSequence = m.Field(
            default_factory=tuple,
            description="Lazy alias imports grouped by module.",
        )
        type_checking_lines: str = m.Field(
            description="Rendered TYPE_CHECKING block lines.",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Published generated exports.",
        )
        publish_all: bool = m.Field(description="Whether __all__ is generated.")

    class LazyInitDirectBootstrapRender(m.ArbitraryTypesModel):
        """Template context for direct bootstrap generated packages."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        runtime_import_lines: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Direct import lines emitted at runtime.",
        )
        inline_constants: t.StrPairSequence = m.Field(
            default_factory=tuple,
            description="Inline constant assignments.",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Generated __all__ names.",
        )

    class LazyInitFlextCoreRootRender(m.ArbitraryTypesModel):
        """Template context for the flext-core root generated package."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        import_lines: str = m.Field(
            default_factory=str,
            description="Rendered static import declarations.",
        )
        all_lines: str = m.Field(
            default_factory=str,
            description="Rendered public ``__all__`` entries.",
        )


__all__: list[str] = ["FlextInfraModelsCodegenRender"]
