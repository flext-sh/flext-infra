"""Standard generated lazy-init package assembly."""

from __future__ import annotations

from flext_infra import c, m, t
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)


class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin
):
    """Assemble standard generated package files from typed template context."""

    @staticmethod
    def _type_checking_filtered(
        type_checking_imports: t.LazyAliasMap | None,
        lazy_filtered: t.LazyAliasMap,
        wildcard_runtime_module_set: frozenset[str],
        *,
        publish_all: bool,
        public_export_set: frozenset[str],
    ) -> t.LazyAliasMap:
        """Return the static import map used by generated TYPE_CHECKING blocks."""
        source = type_checking_imports or lazy_filtered
        return {
            name: val
            for name, val in source.items()
            if val[0] not in wildcard_runtime_module_set
            and (not publish_all or name in public_export_set)
        }

    @classmethod
    def _runtime_import_block(
        cls,
        wildcard_runtime_modules: t.StrSequence | None,
        runtime_imports: t.LazyAliasMap,
    ) -> t.StrSequence:
        """Return runtime import lines for eager and wildcard imports."""
        runtime_import_lines = cls._generate_import_lines(
            cls._group_imports(runtime_imports),
        )
        runtime_import_block: t.MutableSequenceOf[str] = [
            f"from {module} import *"
            for module in sorted(set(wildcard_runtime_modules or ()))
        ]
        if runtime_import_block and runtime_import_lines:
            runtime_import_block.append("")
        runtime_import_block.extend(runtime_import_lines)
        return tuple(runtime_import_block)

    @classmethod
    def _standard_render_context(
        cls,
        current_pkg: str,
        inline_constants: t.StrMapping,
        published_exports: t.StrSequence,
        lazy_filtered: t.LazyAliasMap,
        type_checking_filtered: t.LazyAliasMap,
        runtime_import_block: t.StrSequence,
        children_lazy: t.StrSequence,
        rendered_child_module_paths: t.StrSequence,
        merged_excluded_lazy_names: t.StrSequence,
    ) -> m.Infra.LazyInitStandardRender:
        """Build the typed render context for a standard package."""
        publish_all = cls._is_public_api_root_namespace(current_pkg)
        lazy_entry_names = (
            tuple(sorted(lazy_filtered)) if publish_all else published_exports
        )
        lazy_entries = cls._build_lazy_entries(
            lazy_entry_names,
            lazy_filtered,
            (current_pkg, frozenset(children_lazy), not publish_all),
        )
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        type_checking_lines = (
            cls.generate_type_checking(
                cls._group_imports(type_checking_filtered),
                include_flext_types=False,
                child_packages=(),
                local_package_root=current_pkg,
            )
            if publish_all and type_checking_filtered
            else ()
        )
        docstring_pkg = current_pkg if publish_all else current_pkg.rsplit(".", 1)[-1]
        return m.Infra.LazyInitStandardRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(docstring_pkg),
            type_checking_enabled=bool(type_checking_lines),
            use_merge_lazy_imports=bool(rendered_child_module_paths),
            runtime_import_lines="\n".join(runtime_import_block),
            child_module_paths=rendered_child_module_paths,
            excluded_lazy_names=merged_excluded_lazy_names,
            inline_constants=tuple(sorted(inline_constants.items())),
            eager_export_names=tuple(
                name for name in published_exports if name not in lazy_filtered
            ),
            lazy_module_groups=lazy_module_groups,
            lazy_alias_groups=lazy_alias_groups,
            type_checking_lines="\n".join(type_checking_lines),
            exports=published_exports,
            publish_all=publish_all,
        )

    @classmethod
    def _render_standard_file(
        cls,
        context: m.Infra.LazyInitStandardRender,
    ) -> str:
        """Render a non-bootstrap generated package file."""
        out: t.MutableSequenceOf[str] = [
            context.autogen_header,
            context.docstring,
            "",
        ]
        preamble = cls.get_template(c.Infra.TEMPLATE_PREAMBLE_STANDARD).render(
            **context.model_dump(mode="python"),
        )
        out.extend(preamble.splitlines())
        if not context.runtime_import_lines:
            out.append("")
        body = cls.get_template(c.Infra.TEMPLATE_BODY).render(
            **context.model_dump(mode="python"),
        )
        body_lines = body.splitlines()
        out.extend(
            cls._collapse_blank_runs(
                body_lines[1:] if body_lines and not body_lines[0] else body_lines
            )
        )
        out.append("")
        getattr_content = cls.get_template(
            c.Infra.TEMPLATE_GETATTR_STANDARD,
        ).render(**context.model_dump(mode="python"))
        out.extend(getattr_content.splitlines())
        return "\n".join(out) + "\n"


__all__: list[str] = ["FlextInfraCodegenGenerationStandardMixin"]
