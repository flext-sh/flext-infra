"""Canonical public-root and static-subpackage initializer rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)

if TYPE_CHECKING:
    from flext_infra import t


# mro-wkii.17.26 (codex): Keep lazy loading only at the public package root and
# bind Ruff validation to each target project's real initializer path.
class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin
):
    """Render the two canonical generated initializer forms."""

    @staticmethod
    def _published_exports(plan: m.Infra.LazyInitPlan) -> t.StrSequence:
        """Return package ABI names independently from internal lazy transport."""
        return (
            plan.exports if plan.published_exports is None else plan.published_exports
        )

    @staticmethod
    def _render_lazy_modules(groups: t.StrSequencePairSequence) -> str:
        """Render the canonical lazy module mapping."""
        if not groups:
            return "_LAZY_MODULES: dict[str, tuple[str, ...]] = {}"
        lines = ["_LAZY_MODULES: dict[str, tuple[str, ...]] = {"]
        item_comma = "," if len(groups) > 1 else ""
        for module, names in groups:
            values = ", ".join(f'"{name}"' for name in names)
            comma = "," if len(names) == 1 else ""
            inline = f'    "{module}": ({values}{comma}){item_comma}'
            if len(inline) <= c.Infra.MAX_LINE_LENGTH:
                lines.append(inline)
            else:
                lines.append(f'    "{module}": (')
                lines.extend(f'        "{name}",' for name in names)
                lines.append("    ),")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _render_lazy_alias_groups(groups: t.StrPairSequencePairSequence) -> str:
        """Render the canonical lazy alias mapping."""
        if not groups:
            return "_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {}"
        lines = ["_LAZY_ALIAS_GROUPS: dict[str, tuple[tuple[str, str], ...]] = {"]
        item_comma = "," if len(groups) > 1 else ""
        for module, pairs in groups:
            values = ", ".join(
                f'("{export_name}", "{attr_name}")' for export_name, attr_name in pairs
            )
            comma = "," if len(pairs) == 1 else ""
            inline = f'    "{module}": ({values}{comma}){item_comma}'
            if len(inline) <= c.Infra.MAX_LINE_LENGTH:
                lines.append(inline)
            else:
                lines.append(f'    "{module}": (')
                lines.extend(
                    f'        ("{export_name}", "{attr_name}"),'
                    for export_name, attr_name in pairs
                )
                lines.append("    ),")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _render_exports(exports: t.StrSequence) -> str:
        """Render the canonical public export tuple."""
        if not exports:
            return "__all__: tuple[str, ...] = ()"
        if len(exports) == 1:
            return f'__all__: tuple[str, ...] = ("{exports[0]}",)'
        return "\n".join((
            "__all__: tuple[str, ...] = (",
            *(f'    "{name}",' for name in exports),
            ")",
        ))

    @classmethod
    def _render_root_source(
        cls,
        *,
        plan: m.Infra.LazyInitPlan,
        runtime_import_lines: str,
        type_checking_lines: str,
        lazy_module_groups: t.StrSequencePairSequence,
        lazy_alias_groups: t.StrPairSequencePairSequence,
        exports: t.StrSequence,
    ) -> str:
        """Assemble the complete initializer with canonical Python spacing."""
        imports = ["from __future__ import annotations"]
        if type_checking_lines:
            imports.extend(("from typing import TYPE_CHECKING", ""))
        imports.append(
            "from flext_core.lazy import build_lazy_import_map, install_lazy_exports"
        )
        if runtime_import_lines:
            imports.extend(("", runtime_import_lines))
        sections = [
            c.Infra.AUTOGEN_HEADER.rstrip(),
            cls._format_root_package_docstring(plan.context.current_pkg),
            "\n".join(imports),
        ]
        if type_checking_lines:
            sections.append(type_checking_lines)
        sections.extend((
            cls._render_lazy_modules(lazy_module_groups),
            cls._render_lazy_alias_groups(lazy_alias_groups),
            (
                "_LAZY_IMPORTS = build_lazy_import_map(\n"
                "    _LAZY_MODULES, alias_groups=_LAZY_ALIAS_GROUPS, "
                "sort_keys=False\n"
                ")"
            ),
            cls._render_exports(exports),
            (
                "install_lazy_exports("
                "__name__, globals(), _LAZY_IMPORTS, public_exports=__all__)"
            ),
        ))
        return "\n\n".join(sections)

    @classmethod
    def _type_checking_filtered(cls, plan: m.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Return supported static imports with local facade classes as aliases."""
        source = plan.type_checking_map or plan.lazy_map
        public_names = frozenset(cls._published_exports(plan))
        wildcard_modules = frozenset(plan.wildcard_runtime_modules)
        # mro-pulj (codex): direct imports outside __all__ remain statically
        # declared because they are part of the established root interface.
        filtered: dict[str, t.StrPair] = {
            name: target
            for name, target in source.items()
            if name in public_names
            and target[0] not in wildcard_modules
            and name not in c.Infra.ROOT_TEMPLATE_RUNTIME_IMPORTS
        }
        for (
            alias_name,
            class_suffix,
        ) in c.Infra.PUBLIC_ROOT_TYPING_FACADE_SUFFIXES.items():
            alias_target = filtered.get(alias_name)
            if alias_target is None or alias_target[1] != alias_name:
                continue
            module_name = alias_target[0]
            candidates = tuple(
                export_name
                for export_name, target in filtered.items()
                if target == (module_name, export_name)
                and export_name.endswith(class_suffix)
            )
            if len(candidates) == 1:
                filtered[alias_name] = (module_name, candidates[0])
        return filtered

    @classmethod
    def _runtime_import_lines(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render explicit eager and wildcard runtime imports."""
        lines: t.MutableSequenceOf[str] = [
            f"from {module} import *"
            for module in sorted(set(plan.wildcard_runtime_modules))
        ]
        eager_lines: t.MutableSequenceOf[str] = []
        eager_groups = cls._group_imports(plan.eager_dunders)
        previous_top: str | None = None
        for module in sorted(eager_groups, key=str.lower):
            rendered_module = cls._compact_lazy_module_path(
                plan.context.current_pkg, module
            )
            top = rendered_module.split(".", maxsplit=1)[0]
            if previous_top is not None and top != previous_top:
                eager_lines.append("")
            parts = tuple(
                f"{imported_name} as {export_name}"
                for export_name, imported_name in sorted(eager_groups[module])
                if imported_name
            )
            for part in parts:
                eager_lines.extend(cls._format_import("", rendered_module, (part,)))
            previous_top = top
        if lines and eager_lines:
            lines.append("")
        lines.extend(eager_lines)
        return "\n".join(lines)

    @classmethod
    def _root_context(cls, plan: m.Infra.LazyInitPlan) -> m.Infra.LazyInitRootRender:
        """Build one inline lazy context for a public package root."""
        current_pkg = plan.context.current_pkg
        public_exports = cls._published_exports(plan)
        public_names = frozenset(public_exports)
        lazy_map = (
            dict(plan.lazy_map)
            if plan.published_exports == ()
            else {
                name: target
                for name, target in plan.lazy_map.items()
                if name in public_names
            }
        )
        lazy_entries = cls._build_lazy_entries(
            tuple(lazy_map),
            lazy_map,
            (current_pkg, frozenset(plan.child_packages_for_lazy), True),
        )
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        exports = cls._build_published_exports(public_exports, lazy_map)
        # Public exports are resolved only by the lazy map at runtime. Static
        # imports belong under TYPE_CHECKING; importing them eagerly defeats the
        # lazy contract and makes nested facades circular when they consume the
        # root facade during initialization.
        public_static_imports = cls._type_checking_filtered(plan)
        compacted_public_static_imports = {
            name: (cls._compact_lazy_module_path(current_pkg, mod), attr)
            for name, (mod, attr) in public_static_imports.items()
        }
        static_lines = cls._generate_import_lines(
            cls._group_imports(compacted_public_static_imports), indent="    "
        )
        type_checking_lines = (
            "\n".join(("if TYPE_CHECKING:", *static_lines)) if static_lines else ""
        )
        runtime_import_lines = cls._runtime_import_lines(plan)
        return m.Infra.LazyInitRootRender(
            rendered_source=cls._render_root_source(
                plan=plan,
                runtime_import_lines=runtime_import_lines,
                type_checking_lines=type_checking_lines,
                lazy_module_groups=lazy_module_groups,
                lazy_alias_groups=lazy_alias_groups,
                exports=exports,
            )
        )

    @classmethod
    def _static_context(
        cls, plan: m.Infra.LazyInitPlan
    ) -> m.Infra.StaticPackageInitRender:
        """Build a side-effect-free private or non-production initializer."""
        return m.Infra.StaticPackageInitRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(
                plan.context.current_pkg.rsplit(".", maxsplit=1)[-1]
            ),
        )

    @classmethod
    def _render_root(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render one inline lazy public-root initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_ROOT_INIT,
            cls._root_context(plan),
            target_filename=str(plan.context.init_path),
        )

    @classmethod
    def _render_static(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render one explicit static or empty subpackage initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_STATIC_INIT,
            cls._static_context(plan),
            target_filename=str(plan.context.init_path),
        )


__all__: list[str] = ["FlextInfraCodegenGenerationStandardMixin"]
