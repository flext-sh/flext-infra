"""Canonical public-root and static-subpackage initializer rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)

if TYPE_CHECKING:
    from flext_infra import t


# mro-wkii.17.26 (codex): Keep lazy loading only at the public package root.
class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin
):
    """Render the two canonical generated initializer forms."""

    @staticmethod
    def _type_checking_filtered(plan: m.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Return public static imports not already bound eagerly."""
        source = plan.type_checking_map or plan.lazy_map
        wildcard_modules = frozenset(plan.wildcard_runtime_modules)
        public_exports = frozenset(plan.exports)
        return {
            name: target
            for name, target in source.items()
            if target[0] not in wildcard_modules and name in public_exports
        }

    @classmethod
    def _runtime_import_lines(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render eager and wildcard runtime imports."""
        lines: t.MutableSequenceOf[str] = [
            f"from {module} import *"
            for module in sorted(set(plan.wildcard_runtime_modules))
        ]
        eager_lines: t.MutableSequenceOf[str] = []
        eager_groups = cls._group_imports(plan.eager_dunders)
        previous_top: str | None = None
        for module in sorted(eager_groups, key=str.lower):
            top = module.split(".", maxsplit=1)[0]
            if previous_top is not None and top != previous_top:
                eager_lines.append("")
            parts = tuple(
                cls._format_reexport_import_part(imported_name, export_name)
                for export_name, imported_name in sorted(eager_groups[module])
                if imported_name
            )
            eager_lines.extend(cls._format_import("", module, parts))
            previous_top = top
        if lines and eager_lines:
            lines.append("")
        lines.extend(eager_lines)
        return "\n".join(lines)

    @classmethod
    def _root_context(cls, plan: m.Infra.LazyInitPlan) -> m.Infra.LazyInitRootRender:
        """Build one inline lazy context for a public package root."""
        current_pkg = plan.context.current_pkg
        lazy_map = dict(plan.lazy_map)
        lazy_entries = cls._build_lazy_entries(
            plan.exports,
            lazy_map,
            (current_pkg, frozenset(plan.child_packages_for_lazy), True),
        )
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        type_checking = cls._type_checking_filtered(plan)
        type_checking_lines = (
            cls.generate_type_checking(
                cls._group_imports(type_checking),
                include_flext_types=False,
                child_packages=(),
                local_package_root=current_pkg,
            )
            if type_checking
            else ()
        )
        return m.Infra.LazyInitRootRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(current_pkg),
            current_pkg=current_pkg,
            runtime_import_lines=cls._runtime_import_lines(plan),
            type_checking_lines="\n".join(type_checking_lines),
            lazy_module_groups=lazy_module_groups,
            lazy_alias_groups=lazy_alias_groups,
            exports=cls._build_published_exports(plan.exports, lazy_map),
        )

    @classmethod
    def _typing_stub_context(
        cls, plan: m.Infra.LazyInitPlan
    ) -> m.Infra.StaticPackageInitRender:
        """Build PEP 561 declarations for one public lazy package root."""
        published = cls._build_published_exports(plan.exports, dict(plan.lazy_map))
        published_names = frozenset(published)
        source = dict(plan.type_checking_map or plan.lazy_map)
        source.update(plan.eager_dunders)
        public_imports = {
            name: target for name, target in source.items() if name in published_names
        }
        type_checking = cls.generate_type_checking(
            cls._group_imports(public_imports),
            include_flext_types=False,
            child_packages=(),
            local_package_root=plan.context.current_pkg,
        )
        import_lines = tuple(line.removeprefix("    ") for line in type_checking[1:])
        return m.Infra.StaticPackageInitRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(plan.context.current_pkg),
            runtime_import_lines="\n".join(import_lines),
            exports=published,
        )

    @classmethod
    def _static_sibling_imports(cls, plan: m.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Select explicit exports owned by direct sibling modules."""
        current_pkg = plan.context.current_pkg
        prefix = f"{current_pkg}."
        combined = dict(plan.lazy_map)
        combined.update(plan.eager_dunders)
        return {
            name: target
            for name, target in combined.items()
            if name in plan.exports
            and target[0].startswith(prefix)
            and "." not in target[0].removeprefix(prefix)
        }

    @classmethod
    def _static_import_lines(cls, imports: t.LazyAliasMap) -> t.StrSequence:
        """Render explicit reexports for one non-root package."""
        lines: t.MutableSequenceOf[str] = []
        for module, entries in sorted(cls._group_imports(imports).items()):
            for export_name, imported_name in sorted(entries):
                if not imported_name:
                    lines.append(
                        cls._format_module_alias_import("", module, export_name)
                    )
                    continue
                parts = (cls._format_reexport_import_part(imported_name, export_name),)
                lines.extend(cls._format_import("", module, parts))
        return tuple(lines)

    @classmethod
    def _static_context(
        cls, plan: m.Infra.LazyInitPlan
    ) -> m.Infra.StaticPackageInitRender:
        """Build an explicit static or empty subpackage context."""
        sibling_imports = cls._static_sibling_imports(plan)
        return m.Infra.StaticPackageInitRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(
                plan.context.current_pkg.rsplit(".", maxsplit=1)[-1]
            ),
            runtime_import_lines="\n".join(cls._static_import_lines(sibling_imports)),
            exports=tuple(name for name in plan.exports if name in sibling_imports),
        )

    @classmethod
    def _render_root(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render one inline lazy public-root initializer."""
        return cls._render_model(c.Infra.TEMPLATE_ROOT_INIT, cls._root_context(plan))

    @classmethod
    def render_typing_stub(cls, plan: m.Infra.LazyInitPlan) -> str | None:
        """Render the PEP 561 stub for a public lazy package root."""
        if not cls._is_public_api_root_namespace(plan.context.current_pkg):
            return None
        return cls._render_model(
            c.Infra.TEMPLATE_ROOT_INIT_STUB, cls._typing_stub_context(plan)
        )

    @classmethod
    def _render_static(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render one explicit static or empty subpackage initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_STATIC_INIT, cls._static_context(plan)
        )


__all__: list[str] = ["FlextInfraCodegenGenerationStandardMixin"]
