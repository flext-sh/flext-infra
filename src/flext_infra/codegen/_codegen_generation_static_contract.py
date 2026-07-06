"""Static type-checking contract renderer for generated lazy-init wrappers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.typings import t


class FlextInfraCodegenGenerationStaticContractMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin,
):
    """Render static import contracts for generated package initializers."""

    if TYPE_CHECKING:

        @classmethod
        def _render_model(
            cls,
            template_name: str,
            context: m.ArbitraryTypesModel,
        ) -> str:
            _ = (template_name, context)
            return ""

    @classmethod
    def _generate_static_import_lines(
        cls,
        import_map: t.LazyAliasMap,
    ) -> t.StrSequence:
        """Generate explicit imports for static analysis contracts."""
        groups = cls._group_imports(import_map)
        if not groups:
            return ()
        lines: t.MutableSequenceOf[str] = []
        prev_top: str | None = None
        for mod in sorted(groups, key=str.lower):
            top = mod.split(".")[0]
            if prev_top is not None and top != prev_top:
                lines.append("")
            alias_items: t.MutableSequenceOf[t.StrPair] = []
            attr_items: t.MutableSequenceOf[t.StrPair] = []
            for export_name, attr_name in groups[mod]:
                if attr_name:
                    attr_items.append((export_name, attr_name))
                    continue
                alias_items.append((export_name, attr_name))
            for export_name, _ in sorted(alias_items):
                if "." not in mod:
                    lines.append(f"import {mod} as {export_name}")
                    continue
                parent_mod, _, child_name = mod.rpartition(".")
                lines.extend(
                    cls._format_import(
                        "",
                        parent_mod,
                        (f"{child_name} as {export_name}",),
                    ),
                )
            if attr_items:
                parts = tuple(
                    cls._format_import_part(attr_name, export_name)
                    for export_name, attr_name in sorted(
                        attr_items,
                        key=lambda item: (item[1], item[0] != item[1]),
                    )
                )
                lines.extend(cls._format_import("", mod, parts))
            prev_top = top
        return tuple(lines)

    @staticmethod
    def _format_all_entry(export_name: str) -> t.StrSequence:
        """Render one public ``__all__`` entry for a generated Python module."""
        return (f'    "{export_name}",',)

    @classmethod
    def _generate_all_lines(cls, exports: t.StrSequence) -> str:
        """Generate sorted public ``__all__`` entries."""
        lines: t.MutableSequenceOf[str] = []
        for export_name in sorted(dict.fromkeys(exports)):
            lines.extend(cls._format_all_entry(export_name))
        return "\n".join(lines)

    @classmethod
    def flext_core_root_static_contract(
        cls,
        *,
        include_metadata: bool = False,
    ) -> m.Infra.LazyInitFlextCoreRootRender:
        """Generate flext-core root static imports and public ``__all__`` lines."""
        root_exports_module = import_module("flext_core._root_exports")
        root_typing_parts_exports_module = import_module(
            "flext_core._root_typing_parts._exports",
        )
        root_all: t.StrSequence = root_exports_module.ROOT_ALL
        root_typing_only_names: t.StrSequence = (
            root_exports_module.ROOT_TYPING_ONLY_NAMES
        )
        root_typing_parts_imports: t.StrMapping = (
            root_typing_parts_exports_module.FLEXT_CORE__ROOT_TYPING_PARTS_LAZY_IMPORTS
        )
        root_typing_names: tuple[str, ...] = tuple(root_all) + tuple(
            root_typing_only_names,
        )
        type_map: dict[str, t.StrPair] = {
            name: (
                f"flext_core._root_typing_parts{root_typing_parts_imports[name]}",
                name,
            )
            for name in root_typing_names
            if name in root_typing_parts_imports
        }
        if include_metadata:
            root_metadata_names: t.StrSequence = root_exports_module.ROOT_METADATA_NAMES
            type_map.update({
                name: ("flext_core.__version__", name) for name in root_metadata_names
            })
        return m.Infra.LazyInitFlextCoreRootRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            import_lines="\n".join(cls._generate_static_import_lines(type_map)),
            all_lines=cls._generate_all_lines(root_all),
        )


__all__: list[str] = ["FlextInfraCodegenGenerationStaticContractMixin"]
