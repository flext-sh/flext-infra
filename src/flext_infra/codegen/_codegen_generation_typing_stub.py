"""Typing-stub renderer for generated thin lazy-init wrappers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t


class FlextInfraCodegenGenerationTypingStubMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render static typing stubs for registry-backed wrappers."""

    if TYPE_CHECKING:

        @classmethod
        def _render_model(
            cls, template_name: str, context: m.ArbitraryTypesModel
        ) -> str:
            _ = (template_name, context)
            return ""

    @classmethod
    def _generate_stub_import_lines(
        cls,
        import_map: t.LazyAliasMap,
    ) -> t.StrSequence:
        """Generate explicit re-export imports for ``.pyi`` files."""
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
                    )
                )
            if attr_items:
                parts = tuple(
                    f"{attr_name} as {export_name}"
                    for export_name, attr_name in sorted(
                        attr_items,
                        key=lambda item: (item[1], item[0] != item[1]),
                    )
                )
                lines.extend(cls._format_import("", mod, parts))
            prev_top = top
        return tuple(lines)

    @staticmethod
    def _format_stub_all_entry(export_name: str) -> t.StrSequence:
        """Render one ``__all__`` entry accepted by ``.pyi`` lint rules."""
        if len(export_name) > c.Infra.STUB_STRING_LITERAL_LIMIT:
            message = (
                "public stub export exceeds Ruff's .pyi string literal limit: "
                f"{export_name}"
            )
            raise ValueError(message)
        return (f'    "{export_name}",',)

    @classmethod
    def _generate_stub_all_lines(cls, exports: t.StrSequence) -> str:
        """Generate sorted ``__all__`` entries for a typing stub."""
        lines: t.MutableSequenceOf[str] = []
        for export_name in sorted(dict.fromkeys(exports)):
            lines.extend(cls._format_stub_all_entry(export_name))
        return "\n".join(lines)

    @classmethod
    def generate_typing_stub(
        cls,
        exports: t.StrSequence,
        type_map: t.LazyAliasMap,
        inline_constants: t.StrMapping,
        *,
        include_all: bool = True,
    ) -> str:
        """Generate a static typing stub for a thin registry-backed wrapper."""
        published = tuple(dict.fromkeys(exports))
        import_map = {name: type_map[name] for name in published if name in type_map}
        inline_constant_names = tuple(
            name for name in published if name in inline_constants
        )
        if not import_map and not inline_constant_names:
            return ""
        context = m.Infra.LazyInitTypingStubRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            import_lines="\n".join(cls._generate_stub_import_lines(import_map)),
            inline_constant_names=inline_constant_names,
            all_lines=cls._generate_stub_all_lines(published) if include_all else "",
            exports=published,
        )
        return cls._render_model(c.Infra.TEMPLATE_TYPING_STUB, context)

    @classmethod
    def generate_flext_core_root_typing_stub(cls) -> str:
        """Generate flext-core root from lazy attributes and public ``__all__``."""
        root_exports_module = import_module("flext_core._root_exports")
        root_typing_parts_exports_module = import_module(
            "flext_core._root_typing_parts._exports",
        )
        root_all: t.StrSequence = root_exports_module.ROOT_ALL
        root_metadata_names: t.StrSequence = root_exports_module.ROOT_METADATA_NAMES
        root_typing_only_names: t.StrSequence = (
            root_exports_module.ROOT_TYPING_ONLY_NAMES
        )
        root_typing_parts_imports: t.StrMapping = (
            root_typing_parts_exports_module.FLEXT_CORE__ROOT_TYPING_PARTS_LAZY_IMPORTS
        )
        root_typing_names: tuple[str, ...] = tuple(root_all) + tuple(
            root_typing_only_names
        )
        type_map: dict[str, t.StrPair] = {
            name: (
                f"flext_core._root_typing_parts{root_typing_parts_imports[name]}",
                name,
            )
            for name in root_typing_names
            if name in root_typing_parts_imports
        }
        type_map.update({
            name: ("flext_core.__version__", name) for name in root_metadata_names
        })
        context = m.Infra.LazyInitFlextCoreRootRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            import_lines="\n".join(cls._generate_stub_import_lines(type_map)),
            all_lines=cls._generate_stub_all_lines(root_all),
        )
        return cls._render_model(c.Infra.TEMPLATE_FLEXT_CORE_ROOT_TYPING_STUB, context)


__all__: list[str] = ["FlextInfraCodegenGenerationTypingStubMixin"]
