"""Render context models for codegen templates."""

from __future__ import annotations

from typing import Annotated, ClassVar

from flext_cli import m
from flext_infra import t


class FlextInfraModelsCodegenRender:
    """Typed render contexts for generated lazy-init files."""

    class LazyInitStandardRender(m.ArbitraryTypesModel):
        """Template context for standard lazy-init package rendering."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid", validate_assignment=True
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

    class LazyInitRegistryWrapperRender(m.ArbitraryTypesModel):
        """Template context for thin registry-backed wrappers."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid", validate_assignment=True
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        registry_module: t.NonEmptyStr = m.Field(
            description="Importable lazy registry module.",
        )
        registry_name: t.NonEmptyStr = m.Field(description="Lazy registry symbol.")
        public_exports_name: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional public export contract symbol."),
        ] = None
        runtime_import_lines: str = m.Field(
            description="Rendered eager import block for non-lazy exports.",
        )
        inline_constants: t.StrPairSequence = m.Field(
            default_factory=tuple,
            description="Inline constant assignments.",
        )
        eager_export_names: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Eager names appended to public exports for root wrappers.",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Explicit public exports for root wrappers.",
        )
        publish_all: Annotated[
            bool,
            m.Field(
                description="Whether the wrapper owns the package public __all__.",
            ),
        ] = False

    class LazyInitRegistryRender(m.ArbitraryTypesModel):
        """Template context for split lazy registry aggregators."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        registry_name: t.NonEmptyStr = m.Field(description="Lazy registry symbol.")
        current_pkg: t.NonEmptyStr = m.Field(description="Owning package name.")
        part_imports: t.StrPairSequence = m.Field(
            default_factory=tuple,
            description="Registry part modules paired with exported part names.",
        )
        child_module_paths: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Child package lazy registries merged at runtime.",
        )
        excluded_lazy_names: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Names excluded from merged child lazy registries.",
        )

    class LazyInitRegistryPartRender(m.ArbitraryTypesModel):
        """Template context for one split lazy registry part."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        part_name: t.NonEmptyStr = m.Field(description="Lazy registry part symbol.")
        lazy_module_groups: t.StrSequencePairSequence = m.Field(
            default_factory=tuple,
            description="Lazy imports grouped by module.",
        )
        lazy_alias_groups: t.StrPairSequencePairSequence = m.Field(
            default_factory=tuple,
            description="Lazy alias imports grouped by module.",
        )

    class LazyInitTypingStubRender(m.ArbitraryTypesModel):
        """Template context for a generated package typing stub."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        import_lines: str = m.Field(description="Rendered static import declarations.")
        inline_constant_names: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Inline constant names declared directly in the stub.",
        )
        all_lines: str = m.Field(
            default_factory=str,
            description="Rendered ``__all__`` literal entries for the stub.",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple, description="Published generated exports."
        )

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


__all__: list[str] = ["FlextInfraModelsCodegenRender"]
