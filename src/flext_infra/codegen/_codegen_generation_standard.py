"""Canonical public-root and static-subpackage initializer rendering."""

from __future__ import annotations

from sys import stdlib_module_names
from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)

if TYPE_CHECKING:
    from flext_infra import t


# flext-wkii.17.26 (codex): Keep lazy loading only at the public package root and
# bind Ruff validation to each target project's real initializer path.
class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin
):
    """Render the two canonical generated initializer forms."""

    @staticmethod
    def _is_stdlib_import(target: t.StrPair) -> bool:
        """Return whether an absolute import target belongs to the stdlib."""
        module = target[0]
        return (
            not module.startswith(".")
            and module.partition(".")[0] in stdlib_module_names
        )

    @staticmethod
    def _type_checking_filtered(plan: m.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Return supported static imports with local facade classes as aliases."""
        source = plan.type_checking_map or plan.lazy_map
        public_names = frozenset(plan.exports)
        wildcard_modules = frozenset(plan.wildcard_runtime_modules)
        # flext-pulj (codex): direct imports outside __all__ remain statically
        # declared because they are part of the established root interface.
        filtered: dict[str, t.StrPair] = {
            name: target
            for name, target in source.items()
            if name in public_names
            and target[0] not in wildcard_modules
            and name not in c.Infra.ROOT_TEMPLATE_BINDINGS
            and not FlextInfraCodegenGenerationStandardMixin._is_stdlib_import(target)
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
    def _lazy_groups(
        cls, plan: m.Infra.LazyInitPlan
    ) -> tuple[
        t.SequenceOf[t.StrSequencePair],
        t.SequenceOf[t.StrPairSequencePair],
        t.LazyAliasMap,
    ]:
        """Build owned lazy metadata groups and their filtered public map."""
        current_pkg = plan.context.current_pkg
        public_names = frozenset(plan.exports)
        lazy_map = {
            name: target
            for name, target in plan.lazy_map.items()
            if name in public_names
            and name not in c.Infra.ROOT_TEMPLATE_BINDINGS
            and not cls._is_stdlib_import(target)
        }
        lazy_entries = cls._build_lazy_entries(
            tuple(lazy_map),
            lazy_map,
            (current_pkg, frozenset(plan.child_packages_for_lazy), True),
        )
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        return lazy_module_groups, lazy_alias_groups, lazy_map

    @staticmethod
    def _format_lazy_group_entry(
        module: str,
        values: t.StrSequence,
        *,
        trailing: bool,
        indent: str = "            ",
    ) -> t.StrSequence:
        """Format one mapping entry exactly as Ruff formats a tuple value."""
        inner = ", ".join(values)
        if len(values) == 1:
            inner = f"{inner},"
        compact = f'{indent}"{module}": ({inner}),'
        if len(compact) <= c.Infra.MAX_LINE_LENGTH:
            return (compact,)
        value_indent = f"{indent}    "
        separator = "," if trailing else ""
        return (
            f'{indent}"{module}": (',
            *(f"{value_indent}{value}," for value in values),
            f"{indent}){separator}",
        )

    @staticmethod
    def _format_exports_tuple(exports: t.StrSequence) -> str:
        """Render a canonical public export tuple, including the empty form."""
        if not exports:
            return "()"
        inner = ", ".join(f'"{name}"' for name in exports)
        if len(exports) == 1:
            inner = f"{inner},"
        compact = f"({inner})"
        if len("__all__: tuple[str, ...] = ") + len(compact) <= c.Infra.MAX_LINE_LENGTH:
            return compact
        return "\n".join(("(", *(f'    "{name}",' for name in exports), ")"))

    @classmethod
    def _format_lazy_module_mapping(
        cls, groups: t.SequenceOf[t.StrSequencePair]
    ) -> str:
        """Render the immutable module mapping without a formatter subprocess."""
        if not groups:
            return "        MappingProxyType({}),"
        if len(groups) == 1:
            module, names = groups[0]
            inner = ", ".join(f'"{name}"' for name in names)
            if len(names) == 1:
                inner = f"{inner},"
            compact = f'        MappingProxyType({{"{module}": ({inner})}}),'
            if len(compact) <= c.Infra.MAX_LINE_LENGTH:
                return compact
        lines: t.MutableSequenceOf[str] = ["        MappingProxyType({"]
        for module, names in groups:
            lines.extend(
                cls._format_lazy_group_entry(
                    module,
                    tuple(f'"{name}"' for name in names),
                    trailing=len(groups) > 1,
                )
            )
        lines.append("        }),")
        return "\n".join(lines)

    @classmethod
    def _format_lazy_alias_mapping(
        cls, groups: t.SequenceOf[t.StrPairSequencePair]
    ) -> str:
        """Render the immutable alias mapping without a formatter subprocess."""
        if not groups:
            return "        alias_groups=MappingProxyType({}),"
        if len(groups) == 1:
            module, pairs = groups[0]
            values = tuple(
                f'("{export_name}", "{attr_name}")' for export_name, attr_name in pairs
            )
            inner = ", ".join(values)
            if len(values) == 1:
                inner = f"{inner},"
            compact = (
                f'        alias_groups=MappingProxyType({{"{module}": ({inner})}}),'
            )
            if len(compact) <= c.Infra.MAX_LINE_LENGTH:
                return compact
        lines: t.MutableSequenceOf[str] = ["        alias_groups=MappingProxyType({"]
        for module, pairs in groups:
            lines.extend(
                cls._format_lazy_group_entry(
                    module,
                    tuple(
                        f'("{export_name}", "{attr_name}")'
                        for export_name, attr_name in pairs
                    ),
                    trailing=len(groups) > 1,
                )
            )
        lines.append("        }),")
        return "\n".join(lines)

    @classmethod
    def _root_context(cls, plan: m.Infra.LazyInitPlan) -> m.Infra.LazyInitRootRender:
        """Build one lazy context for a public package root."""
        lazy_module_groups, lazy_alias_groups, lazy_map = cls._lazy_groups(plan)
        current_pkg = plan.context.current_pkg
        public_type_checking_imports = cls._type_checking_filtered(plan)
        type_checking_lines = "\n".join(
            cls.generate_type_checking(
                cls._group_imports(public_type_checking_imports),
                include_flext_types=False,
                child_packages=plan.child_packages_for_lazy,
                local_package_root=current_pkg,
            )
        )
        return m.Infra.LazyInitRootRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(current_pkg),
            runtime_import_lines=cls._runtime_import_lines(plan),
            type_checking_lines=type_checking_lines,
            exports_tuple=cls._format_exports_tuple(
                cls._build_published_exports(
                    tuple(
                        name
                        for name in plan.exports
                        if name in lazy_map or name in plan.eager_dunders
                    ),
                    lazy_map,
                )
            ),
            lazy_module_mapping=cls._format_lazy_module_mapping(lazy_module_groups),
            lazy_alias_mapping=cls._format_lazy_alias_mapping(lazy_alias_groups),
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
