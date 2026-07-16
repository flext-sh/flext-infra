"""Canonical public-root and static-subpackage initializer rendering.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, config, m, t
from flext_infra.codegen._codegen_generation_renderers import (
    FlextInfraCodegenGenerationRenderersMixin,
)


# mro-wkii.17.26 (codex): Keep lazy loading only at the public package root and
# bind Ruff validation to each target project's real initializer path.
class FlextInfraCodegenGenerationStandardMixin(
    FlextInfraCodegenGenerationRenderersMixin
):
    """Render the two canonical generated initializer forms."""

    @staticmethod
    def _type_checking_filtered(plan: p.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Return public static imports with local facade classes as aliases."""
        source = plan.type_checking_map or plan.lazy_map
        public_exports = frozenset(plan.exports)
        filtered: dict[str, t.StrPair] = {
            name: target for name, target in source.items() if name in public_exports
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
    def _runtime_import_lines(cls, plan: p.Infra.LazyInitPlan) -> str:
        """Render explicit eager runtime imports."""
        return "\n".join(
            cls._generate_import_lines(cls._group_imports(plan.eager_dunders))
        )

    @classmethod
    def _root_context(cls, plan: p.Infra.LazyInitPlan) -> p.Infra.LazyInitRootRender:
        """Build one inline lazy context for a public package root."""
        current_pkg = plan.context.current_pkg
        # mro-wkii.17.26 (codex): rendering is a second fail-closed boundary;
        # private discovery entries can never become root attributes.
        public_exports = frozenset(plan.exports)
        lazy_map = {
            name: target
            for name, target in plan.lazy_map.items()
            if name in public_exports
        }
        lazy_entries = cls._build_lazy_entries(
            tuple(lazy_map),
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
    def _static_imports(cls, plan: p.Infra.LazyInitPlan) -> t.LazyAliasMap:
        """Select direct siblings plus declared aliases at a wrapper root."""
        current_pkg = plan.context.current_pkg
        prefix = f"{current_pkg}."
        is_wrapper_root = (
            current_pkg == plan.context.surface
            and current_pkg in c.Infra.ROOT_WRAPPER_SEGMENTS
        )
        combined = dict(plan.lazy_map)
        combined.update(plan.eager_dunders)
        return {
            name: target
            for name, target in combined.items()
            if name in plan.exports
            and bool(target[1])
            and (
                (
                    target[0].startswith(prefix)
                    and "." not in target[0].removeprefix(prefix)
                )
                # mro-wkii.17.26 (codex): wrapper roots retain the inherited
                # runtime facade aliases already approved by the planner.
                or (is_wrapper_root and not target[0].startswith(prefix))
            )
        }

    @classmethod
    def _static_import_lines(
        cls, current_pkg: str, imports: t.LazyAliasMap
    ) -> t.StrSequence:
        """Render explicit sibling-relative reexports for one subpackage."""
        lines: t.MutableSequenceOf[str] = []
        previous_relative: bool | None = None
        max_line_length = config.Infra.tooling.tools.ruff.line_length
        for module, entries in sorted(cls._group_imports(imports).items()):
            import_module = (
                f".{module.removeprefix(f'{current_pkg}.')}"
                if module.startswith(f"{current_pkg}.")
                else module
            )
            import_prefix = f"from {import_module} import ("
            if len(import_prefix) > max_line_length:
                msg = (
                    "static reexport cannot satisfy generated line-length contract: "
                    f"{import_prefix}"
                )
                raise ValueError(msg)
            current_relative = import_module.startswith(".")
            if lines and previous_relative is not current_relative:
                lines.append("")
            parts: t.MutableSequenceOf[str] = []
            for export_name, imported_name in sorted(entries):
                explicit_part = f"{imported_name} as {export_name}"
                part = explicit_part
                if len(explicit_part) + len("    ,") > max_line_length:
                    # NOTE (multi-agent, mro-wkii.17.26.2 / agent: codex): a
                    # literal __all__ preserves an oversized identity reexport.
                    if (
                        imported_name == export_name
                        and len(imported_name) + len("    ,") <= max_line_length
                    ):
                        part = imported_name
                    else:
                        msg = (
                            "static reexport cannot satisfy generated line-length "
                            f"contract; rename the source symbol: {explicit_part}"
                        )
                        raise ValueError(msg)
                parts.append(part)
            lines.extend(cls._format_import("", import_module, parts))
            previous_relative = current_relative
        return tuple(lines)

    @classmethod
    def _static_context(
        cls, plan: p.Infra.LazyInitPlan
    ) -> p.Infra.StaticPackageInitRender:
        """Build an explicit static subpackage context."""
        static_imports = cls._static_imports(plan)
        return m.Infra.StaticPackageInitRender(
            autogen_header=c.Infra.AUTOGEN_HEADER,
            docstring=cls._format_root_package_docstring(
                plan.context.current_pkg.rsplit(".", maxsplit=1)[-1]
            ),
            runtime_import_lines="\n".join(
                cls._static_import_lines(plan.context.current_pkg, static_imports)
            ),
            exports=cls._build_published_exports(tuple(static_imports), {}),
        )

    @classmethod
    def _render_root(cls, plan: p.Infra.LazyInitPlan) -> str:
        """Render one inline lazy public-root initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_ROOT_INIT,
            cls._root_context(plan),
            target_filename=str(plan.context.init_path),
        )

    @classmethod
    def _render_static(cls, plan: p.Infra.LazyInitPlan) -> str:
        """Render one explicit static or empty subpackage initializer."""
        return cls._render_model(
            c.Infra.TEMPLATE_STATIC_INIT,
            cls._static_context(plan),
            target_filename=str(plan.context.init_path),
        )


__all__: list[str] = ["FlextInfraCodegenGenerationStandardMixin"]
