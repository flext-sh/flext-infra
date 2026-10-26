"""Lazy-init initializer rendering in its Ruff fixed-point form (``u.Infra``).

The layout is a pure function of the plan, the static Python model and the
owning project's declarations; Ruff isort/format owns every ordering and
wrapping rule reproduced here, so ``make gen`` and ``make fix`` converge.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from operator import itemgetter
from pathlib import Path

from flext_cli import u

from flext_infra import FlextInfraConfig, c, config, m, t
from flext_infra._utilities._docs_scope_state import (
    FlextInfraUtilitiesDocsScopeStateMixin,
)
from flext_infra._utilities.lint_recipes import FlextInfraUtilitiesLintRecipes
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.native_tooling import FlextInfraUtilitiesNativeTooling
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)


class FlextInfraUtilitiesLazyInitRender:
    """Render planned initializers through the canonical template."""

    @staticmethod
    def lazy_init_width() -> int:
        """Return the Ruff line length every generated line fits.

        Returns:
            The configured line length.

        """
        return FlextInfraUtilitiesNativeTooling.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )

    @staticmethod
    def lazy_init_project_root(run: m.Infra.PythonModelRun, pkg_dir: Path) -> Path:
        """Return the nearest enclosing directory declaring a ``pyproject.toml``.

        Returns:
            The owning project root of ``pkg_dir``.

        """
        return next(
            folder
            for folder in (pkg_dir, *pkg_dir.parents)
            if run.source_project.source_query(folder / c.PYPROJECT_FILENAME, "isfile")
        )

    @classmethod
    def lazy_init_render(
        cls,
        plan: m.Infra.LazyInitPlan,
        *,
        model: m.Infra.PythonModelRun,
        first_party: frozenset[str],
    ) -> str:
        """Render one written initializer.

        ``first_party`` names the owning project's first-party namespaces.

        Returns:
            The initializer source, compiled before it is returned.

        """
        current = plan.context.current_pkg
        helpers = (
            c.Infra.LAZY_BOOTSTRAP_HELPERS
            if current == c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE
            else ()
        )
        public = {
            name: target
            for name, target in {**plan.lazy_map, **plan.eager_dunders}.items()
            if name in plan.exports and name not in helpers
        }
        entries = {
            name: (cls._lazy_init_compact_module(current, module), attr)
            for name, (module, attr) in public.items()
            if name not in plan.eager_dunders
        }
        project_root = cls.lazy_init_project_root(model, plan.context.pkg_dir)
        first_party |= {current}
        rendered = u.Cli.template_render(
            FlextInfraConfig.ssot_config_dir().parent
            / "templates"
            / c.Infra.TEMPLATE_ROOT_INIT,
            m.Infra.LazyInitRootRender(
                autogen_header=c.Infra.AUTOGEN_HEADER,
                docstring=cls._lazy_init_docstring(plan, project_root, model),
                runtime_import_lines=cls._lazy_init_runtime_imports(helpers),
                type_checking_lines="\n".join(
                    cls._lazy_init_type_checking(public, first_party)
                ),
                eager_binding_lines=cls._lazy_init_eager_bindings(plan, first_party),
                exports_tuple=cls._lazy_init_exports_tuple((*public, *helpers)),
                lazy_export_mapping=cls._lazy_init_mapping(entries),
            ),
        ).unwrap()
        compile(rendered, str(plan.context.init_path), "exec")
        return rendered.rstrip() + "\n"

    @staticmethod
    def _lazy_init_docstring(
        plan: m.Infra.LazyInitPlan,
        project_root: Path,
        model: m.Infra.PythonModelRun,
    ) -> str:
        """Return the package docstring in the owning project's language.

        Returns:
            The docstring literal carrying the repository copyright notice.

        """
        # Language and notice depend only on the owning project; every package
        # of that project in this run shares one read of its declaration.
        known = model.project_notices.get(project_root)
        if known is None:
            view = model.source_project
            artifacts = FlextInfraUtilitiesProjectManagedArtifacts
            scope_state = FlextInfraUtilitiesDocsScopeStateMixin
            declaration = artifacts.load_repository_declaration_inputs(
                project_root, source_project=view
            ).unwrap()
            language = (
                declaration.spec.project.documentation_language
                if declaration.spec.project is not None
                else scope_state.docs_documentation_language({
                    "documentation_language": m.Infra.ProjectSpec.model_fields[
                        "documentation_language"
                    ].get_default(),
                })
            )
            known = (
                language,
                FlextInfraUtilitiesLintRecipes.copyright_notice(
                    project_root, source_project=view
                ),
            )
            model.project_notices[project_root] = known
        language, notice = known
        label = plan.context.current_pkg.replace("_", " ").replace("-", " ").strip()
        summary = c.Infra.DocumentationText.PACKAGE_DOCSTRING.localized(
            language
        ).format(package_name=" ".join(word.capitalize() for word in label.split()))
        return f'"""{summary}\n\n{notice}\n"""'

    @staticmethod
    def lazy_init_export_key(name: str) -> t.Pair[int, str]:
        """Order one public name like Ruff ``RUF022``.

        Returns:
            Constants, then classes, then lower-case names, ASCII within each.

        """
        return (0 if name.isupper() else 1 if name[:1].isupper() else 2, name)

    @staticmethod
    def _lazy_init_section(
        module: str, first_party: frozenset[str]
    ) -> t.Pair[int, str]:
        """Rank an import by Ruff isort section, then by module.

        Returns:
            Third-party, then first-party, then relative imports.

        """
        if module.startswith("."):
            return (2, module.lower())
        return (int(module.split(".", 1)[0] in first_party), module.lower())

    @staticmethod
    def _lazy_init_item_key(item: t.StrPair) -> t.Pair[t.Pair[int, str], bool]:
        """Order an imported member like Ruff isort ``order-by-type``.

        Returns:
            The member's type group and case-folded name, then its alias flag.

        """
        export, imported = item
        return FlextInfraUtilitiesCodegenNamespace.isort_member_key(
            imported or export
        ), export != imported

    @classmethod
    def _lazy_init_import(
        cls, indent: str, module: str, parts: t.StrSequence
    ) -> t.StrSequence:
        """Emit one Ruff-canonical ``from`` import.

        Line length is the formatter's concern: an import that does not fit is
        emitted in Ruff's parenthesized one-member-per-line form, even when the
        owner line itself is longer than the configured width.

        Returns:
            The compact line, or one member per wrapped line.

        """
        compact = f"{indent}from {module} import {', '.join(parts)}"
        if len(compact) <= cls.lazy_init_width():
            return (compact,)
        return (
            f"{indent}from {module} import (",
            *(f"{indent}    {part}," for part in parts),
            f"{indent})",
        )

    @classmethod
    def _lazy_init_runtime_imports(cls, helpers: t.StrSequence) -> str:
        """Render the lazy-helper import, the only pre-installer runtime import.

        Returns:
            The runtime import lines.

        """
        return "\n".join(
            cls._lazy_init_import(
                "",
                c.Infra.LAZY_BOOTSTRAP_MODULE,
                helpers or ("install_lazy_exports",),
            )
        )

    @classmethod
    def _lazy_init_eager_bindings(
        cls,
        plan: m.Infra.LazyInitPlan,
        first_party: frozenset[str],
    ) -> str:
        """Render eager dunder bindings that run after the lazy installer.

        A dunder named like its submodule (``__version__``) must be bound
        eagerly: the import system rebinds the package attribute to the
        submodule object on the submodule's first load, so a lazy entry is
        shadowed whenever the submodule loads first. Binding after the
        installer lets that submodule consume the package's own facades
        without an initialization cycle; ``TYPE_CHECKING`` carries the static
        contract, so the runtime-only block is invisible to type checkers.

        Returns:
            The guarded runtime block, empty without eager dunders.

        """
        groups: defaultdict[str, list[t.StrPair]] = defaultdict(list)
        for name in sorted(plan.eager_dunders):
            module, attr = plan.eager_dunders[name]
            groups[module].append((name, attr))
        if not groups:
            return ""
        statements = sorted(
            (
                (
                    cls._lazy_init_section(module, first_party),
                    cls._lazy_init_import(
                        "    ",
                        module,
                        tuple(
                            attr if attr == name else f"{attr} as {name}"
                            for name, attr in sorted(items)
                            if attr
                        ),
                    ),
                )
                for module, items in groups.items()
            ),
            key=itemgetter(0),
        )
        lines = ["if not TYPE_CHECKING:"]
        previous: int | None = None
        for (section, _), statement in statements:
            if previous is not None and section != previous:
                lines.append("")
            lines.extend(statement)
            previous = section
        return "\n".join(lines)

    @staticmethod
    def _lazy_init_import_groups(
        public: t.LazyAliasMap,
    ) -> t.MappingKV[str, t.SequenceOf[t.StrPair]]:
        """Group public targets by the module their static import names.

        Preserve the elected origin used by the runtime lazy mapping.

        Returns:
            The ``(export, imported)`` pairs per importing module.

        """
        groups: defaultdict[str, list[t.StrPair]] = defaultdict(list)
        for name in sorted(public):
            module, attr = public[name]
            groups[module].append((name, attr))
        return groups

    @classmethod
    def _lazy_init_type_checking(
        cls,
        public: t.LazyAliasMap,
        first_party: frozenset[str],
    ) -> t.StrSequence:
        """Render the static import contract of the public exports.

        Every name is imported from the module that declares it, never
        assigned: an initializer propagates and never declares.

        Returns:
            The ``if TYPE_CHECKING:`` block lines, empty without exports.

        """
        merged = cls._lazy_init_import_groups(public)
        if not merged:
            return ()
        lines = ["if TYPE_CHECKING:"]
        previous: int | None = None
        for module in sorted(
            merged, key=lambda name: cls._lazy_init_section(name, first_party)
        ):
            section = cls._lazy_init_section(module, first_party)[0]
            if previous is not None and section != previous:
                lines.append("")
            previous = section
            lines.extend(cls._lazy_init_module_lines(module, merged[module]))
        return lines

    @classmethod
    def _lazy_init_module_lines(
        cls, module: str, items: t.SequenceOf[t.StrPair]
    ) -> t.StrSequence:
        """Render one importing module's static member import.

        Returns:
            The member import lines.

        """
        parts = tuple(
            dict.fromkeys(
                attr if attr == name else f"{attr} as {name}"
                for name, attr in sorted(items, key=cls._lazy_init_item_key)
            )
        )
        return cls._lazy_init_import("    ", module, parts) if parts else ()

    @classmethod
    def _lazy_init_exports_tuple(cls, names: t.StrSequence) -> str:
        """Render ``__all__`` exactly as Ruff formats it.

        Returns:
            The tuple literal, compact when it fits the line length.

        """
        ordered = sorted(dict.fromkeys(names), key=cls.lazy_init_export_key)
        if not ordered:
            return "()"
        inner = ", ".join(f'"{name}"' for name in ordered)
        compact = f"({inner},)" if len(ordered) == 1 else f"({inner})"
        if len("__all__: tuple[str, ...] = ") + len(compact) <= cls.lazy_init_width():
            return compact
        return "(\n    " + ",\n    ".join(f'"{name}"' for name in ordered) + ",\n)"

    @classmethod
    def _lazy_init_mapping(cls, entries: t.LazyAliasMap) -> str:
        """Render the installer's immutable export mapping as Ruff formats it.

        Returns:
            The ``MappingProxyType`` argument line(s).

        """
        ordered = sorted(entries, key=cls.lazy_init_export_key)
        inner = ", ".join(
            f'"{name}": "{module}"'
            if name == attr
            else f'"{name}": ("{module}", "{attr}")'
            for name in ordered
            for module, attr in (entries[name],)
        )
        compact = f"    MappingProxyType({{{inner}}}),"
        if len(compact) <= cls.lazy_init_width():
            return compact
        lines = ["    MappingProxyType({"]
        indent = "        "
        for name in ordered:
            module, attr = entries[name]
            if attr == name:
                line = f'{indent}"{name}": "{module}",'
                lines.extend(
                    (line,)
                    if len(line) <= cls.lazy_init_width()
                    else (
                        f'{indent}"{name}": (',
                        f'{indent}    "{module}"',
                        f"{indent}),",
                    )
                )
                continue
            line = f'{indent}"{name}": ("{module}", "{attr}"),'
            lines.extend(
                (line,)
                if len(line) <= cls.lazy_init_width()
                else (
                    f'{indent}"{name}": (',
                    f'{indent}    "{module}",',
                    f'{indent}    "{attr}",',
                    f"{indent}),",
                )
            )
        lines.append("    }),")
        return "\n".join(lines)

    @staticmethod
    def _lazy_init_compact_module(current: str, module: str) -> str:
        """Express a lazy target relative to ``current`` when they share a root.

        Returns:
            The relative module path, or ``module`` unchanged when foreign.

        """
        if not current or module.startswith("."):
            return module
        root = current.split(".", 1)[0]
        if module.split(".", 1)[0] == root:
            current_parts, module_parts = current.split("."), module.split(".")
            common = 0
            for left, right in zip(current_parts, module_parts, strict=False):
                if left != right:
                    break
                common += 1
            return "." * (len(current_parts) - common + 1) + ".".join(
                module_parts[common:]
            )
        if module.startswith("_"):
            return f".{module}"
        internal = frozenset(current.split(".")[1:])
        first = module.split(".", 1)[0]
        if internal & c.Infra.LOCAL_INFERRED_SEGMENTS:
            return module
        if first in internal or (
            current == root
            and "." in module
            and first in c.Infra.LOCAL_INFERRED_SEGMENTS
        ):
            return f".{module}"
        return module


__all__: list[str] = ["FlextInfraUtilitiesLazyInitRender"]
