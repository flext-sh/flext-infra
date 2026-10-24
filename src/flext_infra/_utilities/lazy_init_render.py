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
from flext_infra._utilities.python_model import FlextInfraUtilitiesPythonModel


class FlextInfraUtilitiesLazyInitRender:
    """Render planned initializers through the canonical template."""

    @staticmethod
    def width() -> int:
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
            for name, target in plan.lazy_map.items()
            if name in plan.exports and name not in helpers
        }
        children = frozenset(plan.child_packages_for_lazy)
        entries = {
            name: (cls._compact_module(current, module), attr)
            for name, (module, attr) in public.items()
            if attr or module not in children or name == module.rsplit(".", 1)[-1]
        }
        project_root = cls.lazy_init_project_root(model, plan.context.pkg_dir)
        first_party |= {current}
        rendered = u.Cli.template_render(
            FlextInfraConfig.ssot_config_dir().parent
            / "templates"
            / c.Infra.TEMPLATE_ROOT_INIT,
            m.Infra.LazyInitRootRender(
                autogen_header=c.Infra.AUTOGEN_HEADER,
                docstring=cls._docstring(plan, project_root, model),
                runtime_import_lines=cls._runtime_imports(plan, helpers, first_party),
                type_checking_lines="\n".join(
                    cls._type_checking(public, plan, first_party, model)
                ),
                exports_tuple=cls._exports_tuple((
                    *(
                        name
                        for name in plan.exports
                        if name in entries or name in plan.eager_dunders
                    ),
                    *helpers,
                )),
                lazy_export_mapping=cls._mapping(entries),
            ),
        ).unwrap()
        compile(rendered, str(plan.context.init_path), "exec")
        return rendered.rstrip() + "\n"

    @staticmethod
    def _docstring(
        plan: m.Infra.LazyInitPlan,
        project_root: Path,
        model: m.Infra.PythonModelRun,
    ) -> str:
        """Return the package docstring in the owning project's language.

        Returns:
            The docstring literal carrying the repository copyright notice.

        """
        view = model.source_project
        artifacts = FlextInfraUtilitiesProjectManagedArtifacts
        declaration = artifacts.load_repository_declaration_inputs(
            project_root, source_project=view
        ).unwrap()
        language = (
            declaration.spec.project.documentation_language
            if declaration.spec.project is not None
            else FlextInfraUtilitiesDocsScopeStateMixin.docs_documentation_language({
                "documentation_language": m.Infra.ProjectSpec.model_fields[
                    "documentation_language"
                ].get_default(),
            })
        )
        label = plan.context.current_pkg.replace("_", " ").replace("-", " ").strip()
        summary = c.Infra.DocumentationText.PACKAGE_DOCSTRING.localized(
            language
        ).format(package_name=" ".join(word.capitalize() for word in label.split()))
        notice = FlextInfraUtilitiesLintRecipes.copyright_notice(
            plan.context.pkg_dir, source_project=view
        )
        return f'"""{summary}\n\n{notice}\n"""'

    @staticmethod
    def export_key(name: str) -> t.Pair[int, str]:
        """Order one public name like Ruff ``RUF022``.

        Returns:
            Constants, then classes, then lower-case names, ASCII within each.

        """
        return (0 if name.isupper() else 1 if name[:1].isupper() else 2, name)

    @staticmethod
    def _section(module: str, first_party: frozenset[str]) -> t.Pair[int, str]:
        """Rank an import by Ruff isort section, then by module.

        Returns:
            Third-party, then first-party, then relative imports.

        """
        if module.startswith("."):
            return (2, module.lower())
        return (int(module.split(".", 1)[0] in first_party), module.lower())

    @staticmethod
    def _item_key(item: t.StrPair) -> t.Pair[t.Pair[int, str], bool]:
        """Order an imported member like Ruff isort ``order-by-type``.

        Returns:
            The member's type group and case-folded name, then its alias flag.

        """
        export, imported = item
        return FlextInfraUtilitiesCodegenNamespace.isort_member_key(
            imported or export
        ), export != imported

    @classmethod
    def _import(cls, indent: str, module: str, parts: t.StrSequence) -> t.StrSequence:
        """Emit one Ruff-canonical ``from`` import within the line length.

        Returns:
            The compact line, or one member per wrapped line.

        Raises:
            ValueError: If even the wrapped owner line exceeds the line length.

        """
        compact = f"{indent}from {module} import {', '.join(parts)}"
        if len(compact) <= cls.width():
            return (compact,)
        if len(f"{indent}from {module} import (") > cls.width():
            msg = (
                f"Absolute import owner {module!r} exceeds Ruff line length "
                f"{cls.width()}; select its canonical public package export."
            )
            raise ValueError(msg)
        return (
            f"{indent}from {module} import (",
            *(f"{indent}    {part}," for part in parts),
            f"{indent})",
        )

    @classmethod
    def _module_alias(cls, indent: str, module: str, name: str) -> t.StrSequence:
        """Emit ``from parent import child as name`` for one module object.

        Returns:
            The compact line, or its wrapped form.

        """
        if "." not in module:
            return (f"{indent}import {module} as {name}",)
        parent, _, child = module.rpartition(".")
        compact = f"{indent}from {parent} import {child} as {name}"
        if len(compact) <= cls.width():
            return (compact,)
        return (
            f"{indent}from {parent} import (",
            f"{indent}    {child} as {name},",
            f"{indent})",
        )

    @classmethod
    def _runtime_imports(
        cls,
        plan: m.Infra.LazyInitPlan,
        helpers: t.StrSequence,
        first_party: frozenset[str],
    ) -> str:
        """Render eager and lazy-helper imports as one isort-ordered block.

        Returns:
            The runtime import lines.

        """
        groups: defaultdict[str, list[t.StrPair]] = defaultdict(list)
        for name in sorted(plan.eager_dunders):
            module, attr = plan.eager_dunders[name]
            groups[module].append((name, attr))
        statements = [
            (
                cls._section(module, first_party),
                cls._import(
                    "",
                    module,
                    tuple(
                        attr if attr == name else f"{attr} as {name}"
                        for name, attr in sorted(items)
                        if attr
                    ),
                ),
            )
            for module, items in groups.items()
        ]
        statements.append((
            cls._section(c.Infra.LAZY_BOOTSTRAP_MODULE, first_party),
            cls._import(
                "",
                c.Infra.LAZY_BOOTSTRAP_MODULE,
                helpers or ("install_lazy_exports",),
            ),
        ))
        lines: list[str] = []
        previous: int | None = None
        for (section, _), statement in sorted(statements, key=itemgetter(0)):
            if previous is not None and section != previous:
                lines.append("")
            lines.extend(statement)
            previous = section
        return "\n".join(lines)

    @staticmethod
    def _import_groups(
        public: t.LazyAliasMap, children: t.StrSequence
    ) -> t.Pair[t.MappingKV[str, t.SequenceOf[t.StrPair]], frozenset[str]]:
        """Group public targets by the module their static import names.

        Child-module targets collapse into their child package and module
        objects import from their parent package.

        Returns:
            The ``(export, imported)`` pairs per importing module, and the
            names published as module objects.

        """
        ordered = sorted(set(children), key=len, reverse=True)
        collapsed: defaultdict[str, list[t.StrPair]] = defaultdict(list)
        for name in sorted(public):
            module, attr = public[name]
            owner = next(
                (
                    child
                    for child in ordered
                    if module == child or module.startswith(f"{child}.")
                ),
                module,
            )
            collapsed[owner].append((name, attr))
        merged: defaultdict[str, list[t.StrPair]] = defaultdict(list)
        for module, items in collapsed.items():
            for name, attr in items:
                if not attr and "." in module:
                    parent, _, child = module.rpartition(".")
                    merged[parent].append((name, child))
                else:
                    merged[module].append((name, attr))
        return merged, frozenset(
            name for items in collapsed.values() for name, attr in items if not attr
        )

    @classmethod
    def _type_checking(
        cls,
        public: t.LazyAliasMap,
        plan: m.Infra.LazyInitPlan,
        first_party: frozenset[str],
        model: m.Infra.PythonModelRun,
    ) -> t.StrSequence:
        """Render the static import contract of the public exports.

        A class alias imports its original class and binds the alias; an
        owner line too long for Ruff binds through ``_owner_N`` aliases.

        Returns:
            The ``if TYPE_CHECKING:`` block lines, empty without exports.

        """
        merged, module_objects = cls._import_groups(
            public, plan.child_packages_for_lazy
        )
        if not merged:
            return ()
        occupied = {name for items in merged.values() for name, _ in items}
        lines = ["if TYPE_CHECKING:"]
        aliases: list[str] = []
        previous: int | None = None
        for module in sorted(merged, key=lambda name: cls._section(name, first_party)):
            section = cls._section(module, first_party)[0]
            if previous is not None and section != previous:
                lines.append("")
            previous = section
            items = merged[module]
            if (
                len(f"    from {module} import (") > cls.width()
                and module.rpartition(".")[0] == plan.context.current_pkg
                and all(attr for _, attr in items)
            ):
                lines.extend(cls._owned_child(module, items, plan, occupied, model))
            else:
                lines.extend(
                    cls._module_lines(module, items, module_objects, model, aliases)
                )
        if aliases:
            lines.extend(("", *aliases))
        return lines if len(lines) > 1 else ()

    @classmethod
    def _module_lines(
        cls,
        module: str,
        items: t.SequenceOf[t.StrPair],
        module_objects: frozenset[str],
        model: m.Infra.PythonModelRun,
        aliases: list[str],
    ) -> t.StrSequence:
        """Render one importing module's static imports.

        Returns:
            The module-object imports, then the member import; class aliases
            are appended to ``aliases``.

        """
        python = FlextInfraUtilitiesPythonModel
        source = python.python_model_module(model, module)
        lines: list[str] = []
        parts: list[str] = []
        for name, attr in sorted(items, key=cls._item_key):
            if not attr:
                lines.extend(cls._module_alias("    ", module, name))
                continue
            original = (
                python.python_model_static_class_alias(model, source, attr)
                if source is not None
                else ""
            )
            imported = original if (original, original) in items else attr
            if imported[:1].isupper() and name[:1].islower():
                parts.append(imported)
                aliases.append(f"    {name} = {imported}")
            elif name in module_objects or imported != name:
                parts.append(f"{imported} as {name}")
            else:
                parts.append(imported)
        if parts:
            lines.extend(cls._import("    ", module, tuple(dict.fromkeys(parts))))
        return lines

    @classmethod
    def _owned_child(
        cls,
        module: str,
        items: t.SequenceOf[t.StrPair],
        plan: m.Infra.LazyInitPlan,
        occupied: set[str],
        model: m.Infra.PythonModelRun,
    ) -> t.StrSequence:
        """Bind a child module's declarations through one ``_owner_N`` alias.

        An ``_owner_N`` already bound to this module in the current
        initializer is reused, so a second render is byte-stable.

        Returns:
            The module alias import followed by its static bindings.

        Raises:
            ValueError: If a binding is not declared by the module or cannot fit.

        """
        python = FlextInfraUtilitiesPythonModel
        source = python.python_model_module(model, module)
        blocked = set(occupied)
        if model.source_project.source_query(plan.context.init_path, "isfile"):
            init = python.python_model_module_at(
                model, plan.context.init_path, plan.context.current_pkg
            )
            blocked.update(
                name
                for name in python.python_model_members(init)
                if python.python_model_import_target(init, name) != module
            )
        prefix = c.Infra.LAZY_INIT_OWNER_ALIAS_PREFIX
        index = 0
        while f"{prefix}{index}" in blocked:
            index += 1
        alias = f"{prefix}{index}"
        occupied.add(alias)
        # Ruff separates the owner import from its bindings by one blank line.
        lines = [*cls._module_alias("    ", module, alias), ""]
        for name, attr in sorted(items, key=cls._item_key):
            if source is None or not python.python_model_defines(source, attr):
                msg = (
                    "Owned child static export is not declared by its module: "
                    f"{module}.{attr}"
                )
                raise ValueError(msg)
            compact = f"    {name} = {alias}.{attr}"
            lines.extend(
                (compact,)
                if len(compact) <= cls.width()
                else (f"    {name} = (", f"        {alias}.{attr}", "    )")
            )
        if any(len(line) > cls.width() for line in lines):
            msg = f"Owned child static binding exceeds Ruff line length: {module}"
            raise ValueError(msg)
        return tuple(lines)

    @classmethod
    def _exports_tuple(cls, names: t.StrSequence) -> str:
        """Render ``__all__`` exactly as Ruff formats it.

        Returns:
            The tuple literal, compact when it fits the line length.

        """
        ordered = sorted(dict.fromkeys(names), key=cls.export_key)
        if not ordered:
            return "()"
        inner = ", ".join(f'"{name}"' for name in ordered)
        compact = f"({inner},)" if len(ordered) == 1 else f"({inner})"
        if len("__all__: tuple[str, ...] = ") + len(compact) <= cls.width():
            return compact
        return "(\n    " + ",\n    ".join(f'"{name}"' for name in ordered) + ",\n)"

    @classmethod
    def _mapping(cls, entries: t.LazyAliasMap) -> str:
        """Render the installer's immutable export mapping as Ruff formats it.

        Returns:
            The ``MappingProxyType`` argument line(s).

        """
        ordered = sorted(entries, key=cls.export_key)
        inner = ", ".join(
            f'"{name}": "{module}"'
            if name == attr or not attr
            else f'"{name}": ("{module}", "{attr}")'
            for name in ordered
            for module, attr in (entries[name],)
        )
        compact = f"    MappingProxyType({{{inner}}}),"
        if len(compact) <= cls.width():
            return compact
        lines = ["    MappingProxyType({"]
        indent = "        "
        for name in ordered:
            module, attr = entries[name]
            if attr in {name, ""}:
                line = f'{indent}"{name}": "{module}",'
                lines.extend(
                    (line,)
                    if len(line) <= cls.width()
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
                if len(line) <= cls.width()
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
    def _compact_module(current: str, module: str) -> str:
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
