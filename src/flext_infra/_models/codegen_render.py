"""Render context models for codegen templates."""

from __future__ import annotations

from typing import ClassVar

from flext_cli import m
from flext_infra.typings import t


class FlextInfraModelsCodegenRender:
    """Typed render contexts for generated lazy-init files."""

    # NOTE (multi-agent, mro-wkii.17 / agent: uv_overlay_owner): keep the
    # module-skeleton template boundary model-backed and immutable.
    class ModuleSkeletonRenderContext(m.ContractModel):
        """Validated context for one generated module skeleton."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            frozen=True,
            str_strip_whitespace=False,
        )

        class_name: t.NonEmptyStr = m.Field(description="Generated class name.")
        base_class: t.NonEmptyStr = m.Field(description="Generated base class name.")
        base_import_block: str = m.Field(description="Rendered base import block.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")

    class LazyInitUnitManifestRender(m.ArbitraryTypesModel):
        """Template context for a package ``__unit__.py`` manifest."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        current_pkg: t.NonEmptyStr = m.Field(
            description="Importable package name.",
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
        """Template context for a thin package ``__init__.py``."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(
            extra="forbid",
            validate_assignment=True,
        )

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        current_pkg: t.NonEmptyStr = m.Field(
            description="Importable package name.",
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


__all__: list[str] = ["FlextInfraModelsCodegenRender"]
