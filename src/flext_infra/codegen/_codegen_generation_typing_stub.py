"""Typing-stub renderer for generated thin lazy-init wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, t
from flext_infra.codegen._codegen_generation_lazy_entries import (
    FlextInfraCodegenGenerationLazyEntriesMixin,
)


class FlextInfraCodegenGenerationTypingStubMixin(
    FlextInfraCodegenGenerationLazyEntriesMixin
):
    """Render static typing stubs for registry-backed wrappers."""

    if TYPE_CHECKING:

        @classmethod
        def _render_model(
            cls, template_name: str, context: m.ArbitraryTypesModel
        ) -> str: ...

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


__all__: list[str] = ["FlextInfraCodegenGenerationTypingStubMixin"]
