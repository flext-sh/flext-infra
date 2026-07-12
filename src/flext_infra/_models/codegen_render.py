"""Render context models for codegen templates."""

from __future__ import annotations

from typing import ClassVar

from flext_cli import m
from flext_infra.typings import t


class FlextInfraModelsCodegenRender:
    """Typed render contexts for generated lazy-init files."""

    class LazyInitUnitManifestRender(m.ArbitraryTypesModel):
        """Template context for the per-project-root ``__unit__.py`` manifest."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        current_pkg: t.NonEmptyStr = m.Field(
            description="Importable project-root package name.",
        )
        # mro-i6nq.10: Static bindings make the manifest's literal __all__ valid.
        type_checking_lines: str = m.Field(
            default_factory=str,
            description="Derived TYPE_CHECKING imports for manifest exports.",
        )
        lazy_module_groups: t.StrSequencePairSequence = m.Field(
            default_factory=tuple,
            description="Lazy imports grouped by module (module -> names).",
        )
        lazy_alias_groups: t.StrPairSequencePairSequence = m.Field(
            default_factory=tuple,
            description="Lazy alias imports grouped by module.",
        )
        child_module_paths: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Child module paths merged at runtime by the root init.",
        )
        excluded_lazy_names: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Names excluded from the merged child lazy registries.",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Published root ``__all__`` names (frozen ABI).",
        )

    class LazyInitRootThinRender(m.ArbitraryTypesModel):
        """Template context for the thin project-root ``__init__.py``."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        current_pkg: t.NonEmptyStr = m.Field(
            description="Importable project-root package name.",
        )
        runtime_import_lines: str = m.Field(
            default_factory=str,
            description="Eager runtime imports (``__version__`` dunders).",
        )
        type_checking_lines: str = m.Field(
            default_factory=str,
            description="Derived ``if TYPE_CHECKING:`` imports for static resolvers.",
        )
        has_child_paths: bool = m.Field(
            description="Whether the root merges child lazy registries at runtime.",
        )

    class LazyInitEagerPackageRender(m.ArbitraryTypesModel):
        """Template context for eager-import non-root package initializers."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        runtime_import_lines: str = m.Field(
            default_factory=str,
            description="Eager sibling imports (``from <mod> import <Name>``).",
        )
        exports: t.StrSequence = m.Field(
            default_factory=tuple,
            description="Generated ``__all__`` names (sibling exports only).",
        )


__all__: list[str] = ["FlextInfraModelsCodegenRender"]
