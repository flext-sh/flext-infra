"""Template renderers for generated ``__init__`` files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja2.runtime import StrictUndefined
from jinja2.utils import select_autoescape

from flext_infra.codegen._codegen_generation_static_contract import (
    FlextInfraCodegenGenerationStaticContractMixin,
)
from flext_infra.constants import c
from flext_infra.models import m

if TYPE_CHECKING:
    from flext_infra.protocols import p
    from flext_infra.typings import t


class FlextInfraCodegenGenerationRenderersMixin(
    FlextInfraCodegenGenerationStaticContractMixin,
):
    """Jinja-backed renderer helper methods."""

    @classmethod
    @override
    def _render_model(cls, template_name: str, context: m.ArbitraryTypesModel) -> str:
        """Render a typed template context with normalized trailing newline."""
        template = cls.get_template(template_name)
        rendered: str = template.render(**context.model_dump(mode="python"))
        return rendered.rstrip() + "\n"

    @classmethod
    def _generate_registry_wrapper_file(
        cls,
        current_pkg: str,
        registry_wrapper: m.Infra.LazyInitRegistryWrapper,
        runtime_import_lines: str,
        type_checking_lines: str,
        inline_constants: t.StrPairSequence,
        eager_export_names: t.StrSequence,
        exports: t.StrSequence,
        *,
        publish_all: bool,
    ) -> str:
        """Generate a thin package initializer backed by a lazy registry."""
        context = m.Infra.LazyInitRegistryWrapperRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(
                current_pkg.rsplit(".", maxsplit=1)[-1],
            ),
            registry_module=registry_wrapper.module,
            registry_name=registry_wrapper.name,
            public_exports_name=registry_wrapper.public_exports_name,
            runtime_import_lines=runtime_import_lines,
            type_checking_lines=type_checking_lines,
            inline_constants=inline_constants,
            eager_export_names=eager_export_names,
            exports=exports,
            publish_all=publish_all,
        )
        return cls._render_model(c.Infra.TEMPLATE_REGISTRY_WRAPPER, context)

    @classmethod
    def generate_registry_files(
        cls,
        current_pkg: str,
        registry_name: str,
        lazy_map: t.LazyAliasMap,
        child_packages_for_lazy: t.StrSequence,
        excluded_lazy_names: t.StrSequence,
        registry_filename: str = c.Infra.ROOT_EXPORTS_FILENAME,
    ) -> dict[str, str]:
        """Generate lazy registry files for a registry-backed wrapper."""
        lazy_entries = cls._build_lazy_entries(
            tuple(sorted(lazy_map)),
            lazy_map,
            (current_pkg, frozenset(child_packages_for_lazy), True),
        )
        if not lazy_entries:
            return {}
        lazy_module_groups, lazy_alias_groups = cls._group_lazy_entries(lazy_entries)
        generated: dict[str, str] = {}
        registry_context = m.Infra.LazyInitRegistryRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            registry_name=registry_name,
            current_pkg=current_pkg,
            lazy_module_groups=lazy_module_groups,
            lazy_alias_groups=lazy_alias_groups,
            child_module_paths=tuple(
                cls._compact_lazy_module_path(current_pkg, child_package)
                for child_package in child_packages_for_lazy
            ),
            excluded_lazy_names=tuple(
                sorted(c.Infra.INFRA_ONLY_EXPORTS | set(excluded_lazy_names)),
            ),
        )
        generated[registry_filename] = cls._render_model(
            c.Infra.TEMPLATE_REGISTRY,
            registry_context,
        )
        return generated

    @classmethod
    def _generate_direct_bootstrap_file(
        cls,
        exports: t.StrSequence,
        filtered: t.LazyAliasMap,
        inline_constants: t.StrMapping,
        current_pkg: str,
    ) -> str:
        """Generate direct imports for lazy bootstrap code."""
        runtime_groups = cls._group_imports(filtered)
        context = m.Infra.LazyInitDirectBootstrapRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(
                current_pkg.rsplit(".", maxsplit=1)[-1],
            ),
            runtime_import_lines=cls._generate_import_lines(runtime_groups),
            inline_constants=tuple(sorted(inline_constants.items())),
            exports=exports,
        )
        return cls._render_model(c.Infra.TEMPLATE_DIRECT_BOOTSTRAP, context)

    @classmethod
    def _generate_flext_core_root_file(cls) -> str:
        """Generate flext-core root from its canonical root export map."""
        context = cls.flext_core_root_static_contract()
        return cls._render_model(c.Infra.TEMPLATE_FLEXT_CORE_ROOT, context)

    @staticmethod
    def _build_env() -> t.Infra.JinjaEnvironment:
        """Create a Jinja2 environment for codegen templates."""
        template_root = Path(__file__).resolve().parent.parent / "templates"
        return Environment(
            loader=FileSystemLoader(str(template_root)),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=False,
            undefined=StrictUndefined,
            autoescape=select_autoescape(),
        )

    _env: t.Infra.JinjaEnvironment | None = None

    @classmethod
    def get_template(cls, name: str) -> p.Infra.RenderableTemplate:
        """Return a template narrowed to the local render protocol."""
        env = cls._env
        if env is None:
            env = cls._build_env()
            cls._env = env
        return env.get_template(name)


__all__: list[str] = ["FlextInfraCodegenGenerationRenderersMixin"]
