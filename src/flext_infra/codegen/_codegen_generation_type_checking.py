"""TYPE_CHECKING render helpers for lazy-init generation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import config, p, u
from flext_infra.codegen import FlextInfraCodegenGenerationImportsMixin

if TYPE_CHECKING:
    from flext_infra import m, t


class FlextInfraCodegenGenerationTypeCheckingMixin(
    FlextInfraCodegenGenerationImportsMixin,
):
    """TYPE_CHECKING block generation helper methods."""

    @staticmethod
    def _type_checking_provider(
        mod: str,
        source_project: p.Infra.RopeProject,
        package_context: m.Infra.LazyInitPackageContext | None,
    ) -> t.Triple[p.Infra.RopeParsedModule, str, p.Infra.RopeFile | None]:
        """Resolve owned declarations relative to their elected package resource.

        A future namespace must not lose its declarations to an installed
        regular package before its initializer has been generated.

        Returns:
            The native declaration, proof import and lexical import resource.

        """
        if package_context is not None and (
            mod == package_context.current_pkg
            or mod.startswith(f"{package_context.current_pkg}.")
        ):
            folder = source_project.get_folder(
                package_context.pkg_dir.relative_to(
                    Path(source_project.root.real_path)
                ).as_posix()
            )
            relative = mod.removeprefix(package_context.current_pkg).removeprefix(".")
            owner = source_project.get_relative_module(relative, folder, 1)
            resource = source_project.get_file(
                package_context.init_path.relative_to(
                    Path(source_project.root.real_path)
                ).as_posix()
            )
            return u.Infra.require_parsed_module(owner), f".{relative}", resource
        return (
            u.Infra.require_parsed_module(source_project.get_module(mod)),
            mod,
            None,
        )

    @staticmethod
    def _native_class_export_binding(
        mod: str,
        attr_name: str,
        items: t.StrPairSequence,
        source_project: p.Infra.RopeProject,
        package_context: m.Infra.LazyInitPackageContext | None = None,
    ) -> str:
        """Bind bare class aliases only to an elected original declaration.

        Returns:
            The published class name, or the unchanged non-class binding.

        Raises:
            TypeError: If the parsed provider does not expose a module AST.
            ValueError: If the rendered import changes the proven class identity.

        """
        owner, proof_import, resource = (
            FlextInfraCodegenGenerationTypeCheckingMixin._type_checking_provider(
                mod, source_project, package_context
            )
        )
        tree = owner.get_ast()
        if not isinstance(tree, ast.Module):
            message = "Static class exports require a native module AST"
            raise TypeError(message)
        aliases = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == attr_name
            and isinstance(node.value, ast.Name)
        ]
        if len(aliases) != 1:
            return attr_name
        assignments = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id == attr_name
        ]
        if len(assignments) != 1:
            return attr_name
        alias = aliases[0]
        original = alias.value
        if (
            not isinstance(original, ast.Name)
            or (original.id, original.id) not in items
        ):
            return attr_name
        declarations = [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == original.id
        ]
        binding = owner.get_attributes().get(attr_name)
        canonical = owner.get_attributes().get(original.id)
        if (
            len(declarations) != 1
            or declarations[0].lineno >= alias.lineno
            or binding is None
            or canonical is None
            or any(
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Store)
                and node.id == original.id
                for node in ast.walk(tree)
            )
        ):
            return attr_name
        target = canonical.get_object()
        if (
            not u.Infra.py_class(target)
            or target.get_module() is not owner
            or binding.get_object() is not target
            or target.get_ast() is not declarations[0]
        ):
            return attr_name
        attributes = u.Infra.build_string_module(
            source_project,
            f"from {proof_import} import {original.id} as {attr_name}\n",
            resource=resource,
        ).get_attributes()
        if attributes[attr_name].get_object() is not target:
            message = f"Static class export identity changed: {mod}.{attr_name}"
            raise ValueError(message)
        return original.id

    @classmethod
    def _owned_child_imports(
        cls,
        mod: str,
        items: t.StrPairSequence,
        *,
        source_project: p.Infra.RopeProject,
        occupied_names: set[str],
        package_context: m.Infra.LazyInitPackageContext | None = None,
    ) -> t.StrSequence:
        """Bind a proven child module's exports without importing its parent.

        Returns:
            Absolute module imports followed by identity-preserving static aliases.

        Raises:
            ValueError: If a binding is not declared by its owner or cannot fit.

        """
        owner, proof_import, resource = cls._type_checking_provider(
            mod, source_project, package_context
        )
        parent_module, _, _ = cls._type_checking_provider(
            mod.rpartition(".")[0], source_project, package_context
        )
        # Reuse this module's existing binding so a second render is byte-stable.
        blocked = occupied_names | {
            name
            for name, binding in parent_module.get_scope().get_names().items()
            if not u.Infra.pymodule(value := binding.get_object()) or value is not owner
        }
        index = 0
        while (alias := f"_owner_{index}") in blocked:
            index += 1
        occupied_names.add(alias)
        prefix = cls._format_type_checking_module_alias_import("    ", mod, alias)
        lines = list(prefix)
        for export_name, attr_name in sorted(items, key=cls._import_item_sort_key):
            binding = owner.get_attributes().get(attr_name)
            if binding is None or binding.get_object().get_module() is not owner:
                message = (
                    "Owned child static export is not declared by its module: "
                    f"{mod}.{attr_name}"
                )
                raise ValueError(message)
            expression = f"{alias}.{attr_name}"
            compact = f"    {export_name} = {expression}"
            lines.extend(
                (compact,)
                if len(compact)
                <= u.Infra.native_tool_setting(
                    config.Infra.tooling, "ruff", "line-length", int
                )
                else (f"    {export_name} = (", f"        {expression}", "    )")
            )
        if any(
            len(line)
            > u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff", "line-length", int
            )
            for line in lines
        ):
            message = f"Owned child static binding exceeds Ruff line length: {mod}"
            raise ValueError(message)
        attributes = u.Infra.build_string_module(
            source_project,
            "\n".join((
                *cls._format_type_checking_module_alias_import("", proof_import, alias),
                *(line.removeprefix("    ") for line in lines[len(prefix) :]),
            ))
            + "\n",
            resource=resource,
        ).get_attributes()
        for export_name, attr_name in items:
            binding = attributes.get(export_name)
            if (
                binding is None
                or binding.get_object()
                is not owner.get_attributes()[attr_name].get_object()
            ):
                message = f"Owned child static identity changed: {mod}.{attr_name}"
                raise ValueError(message)
        return tuple(lines)

    @staticmethod
    def _collapse_to_children(
        groups: t.MappingKV[str, t.StrPairSequence],
        child_packages: t.StrSequence | None,
    ) -> t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]:
        """Collapse child module imports into configured child packages.

        Returns:
            The resulting ``t.MappingKV[str, t.MutableSequenceOf[t.StrPair]]``.

        """
        sorted_children: list[str] = sorted(
            set(child_packages or []),
            key=len,
            reverse=True,
        )
        collapsed: MutableMapping[str, list[t.StrPair]] = defaultdict(list)
        for mod, items in groups.items():
            target = mod
            for child_package in sorted_children:
                if mod.startswith(child_package + ".") or mod == child_package:
                    target = child_package
                    break
            collapsed[target].extend(items)
        return collapsed

    @staticmethod
    def _has_flext_types(collapsed: t.MappingKV[str, t.StrPairSequence]) -> bool:
        """Return whether a collapsed import map already imports FlextTypes.

        Returns:
            Whether a collapsed import map already imports FlextTypes.

        """
        return any(
            export_name == "FlextTypes"
            for items in collapsed.values()
            for export_name, _ in items
        )

    @staticmethod
    def _type_checking_sort_key(mod: str, root_names: frozenset[str]) -> t.StrPair:
        """Rank an import by ruff isort section, then by module path.

        ruff/isort partitions imports into sections — third-party, then
        first-party (this package's own root), then local (relative) — sorted
        alphabetically within each section and separated by a single blank
        line (``section_whitelines``). The legacy rank lumped every absolute
        import into one alphabetical run, so a third-party import (e.g.
        ``flext_tests``) sorted ahead of this package's own first-party import,
        violating I001 in the generated ``tests`` initializers. Sections are
        derived from the emitted module's owner and the package root so the
        generated order mirrors each project's ruff isort config.

        Returns:
            The resulting ``t.StrPair``.

        """
        if mod.startswith("."):
            return ("2", mod.lower())  # local-folder section
        own_top = mod.split(".", maxsplit=1)[0]
        return ("1" if own_top in root_names else "0", mod.lower())

    @staticmethod
    def _merge_root_alias_groups(
        collapsed: t.MappingKV[str, t.MutableSequenceOf[t.StrPair]],
    ) -> MutableMapping[str, t.StrPairSequence]:
        """Group each elected static reexport by its emitted import owner.

        Returns:
            The resulting ``MutableMapping[str, t.StrPairSequence]``.

        """
        merged: MutableMapping[str, t.StrPairSequence] = {}
        for mod, items in collapsed.items():
            for export_name, attr_name in items:
                owner, imported = (
                    (mod.rpartition(".")[0], mod.rsplit(".", maxsplit=1)[-1])
                    if not attr_name and "." in mod
                    else (mod, attr_name)
                )
                merged[owner] = (
                    *merged.get(owner, ()),
                    (export_name, imported),
                )
        return merged

    @staticmethod
    def _emit_type_checking_module(
        mod: str,
        items: t.StrPairSequence,
        lines: t.MutableSequenceOf[str],
        module_exports: frozenset[str],
        context: tuple[
            str | None,
            p.Infra.RopeProject | None,
            set[str],
            t.MutableSequenceOf[str],
            m.Infra.LazyInitPackageContext | None,
        ],
    ) -> None:
        """Emit one TYPE_CHECKING import from its resolved owner."""
        local_package_root, source_project, occupied_names, aliases, package_context = (
            context
        )
        if (
            len(f"    from {mod} import (")
            > u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff", "line-length", int
            )
            and mod.rpartition(".")[0] == local_package_root
            and source_project is not None
            and all(attr for _name, attr in items)
        ):
            lines.extend(
                FlextInfraCodegenGenerationTypeCheckingMixin._owned_child_imports(
                    mod,
                    items,
                    source_project=source_project,
                    occupied_names=occupied_names,
                    package_context=package_context,
                ),
            )
            return
        parts: t.MutableSequenceOf[str] = []
        for export_name, attr_name in sorted(
            items,
            key=FlextInfraCodegenGenerationTypeCheckingMixin._import_item_sort_key,
        ):
            if not attr_name:
                lines.extend(
                    FlextInfraCodegenGenerationTypeCheckingMixin._format_type_checking_module_alias_import(
                        "    ", mod, export_name
                    )
                )
                continue
            imported_name = (
                FlextInfraCodegenGenerationTypeCheckingMixin._native_class_export_binding(
                    mod, attr_name, items, source_project, package_context
                )
                if source_project is not None
                else attr_name
            )
            if imported_name[:1].isupper() and export_name[:1].islower():
                parts.append(imported_name)
                aliases.append(f"    {export_name} = {imported_name}")
                continue
            parts.append(
                f"{imported_name} as {export_name}"
                if export_name in module_exports
                else FlextInfraCodegenGenerationTypeCheckingMixin._format_import_part(
                    imported_name, export_name
                )
            )
        deduped_parts = tuple(dict.fromkeys(parts))
        if deduped_parts:
            lines.extend(
                FlextInfraCodegenGenerationTypeCheckingMixin._format_import(
                    "    ",
                    mod,
                    deduped_parts,
                ),
            )

    @classmethod
    def generate_type_checking(
        cls,
        groups: t.MappingKV[str, t.StrPairSequence],
        *,
        include_flext_types: bool = True,
        child_packages: t.StrSequence | None = None,
        local_package_root: str | None = None,
        root_names: frozenset[str] | None = None,
    ) -> t.StrSequence:
        """Generate a TYPE_CHECKING import block.

        Returns:
            The resulting ``t.StrSequence``.

        """
        return cls._generate_type_checking(
            groups,
            (include_flext_types, child_packages, local_package_root, root_names),
        )

    @classmethod
    def _generate_type_checking(
        cls,
        groups: t.MappingKV[str, t.StrPairSequence],
        publication: tuple[
            bool, t.StrSequence | None, str | None, frozenset[str] | None
        ],
        *,
        source_project: p.Infra.RopeProject | None = None,
        package_context: m.Infra.LazyInitPackageContext | None = None,
    ) -> t.StrSequence:
        """Render the public import contract against its optional frozen source view.

        Returns:
            The canonical static imports and proven owned-child class bindings.

        """
        include_flext_types, child_packages, local_package_root, root_names = (
            publication
        )
        if not groups and not include_flext_types:
            return ()
        if not groups:
            return ("if TYPE_CHECKING:", "    from flext_core import FlextTypes")
        normalized_groups: MutableMapping[str, t.StrPairSequence] = {}
        for mod, items in groups.items():
            resolved = cls.normalize_type_checking_module_path(
                mod,
                local_package_root,
            )
            cls._reject_noncanonical_type_checking_import(
                resolved,
                local_package_root,
                items,
            )
            normalized_groups[resolved] = (*normalized_groups.get(resolved, ()), *items)
        collapsed = cls._collapse_to_children(normalized_groups, child_packages)
        module_exports = frozenset(
            name for items in collapsed.values() for name, attr in items if not attr
        )
        merged_groups = cls._merge_root_alias_groups(collapsed)
        # With include_flext_types=False the collapsed groups are the only
        # content the block would carry; a package whose references collapsed
        # away (its re-exported children moved elsewhere) must render no
        # TYPE_CHECKING block at all — a bare "if TYPE_CHECKING:" header is
        # invalid Python and breaks every conform that follows.
        if not merged_groups and not include_flext_types:
            return ()
        # Derive the set of first-party roots for isort sectioning. When the
        # caller provides an explicit root_names (e.g. test facades need both
        # "tests" and the project package), use it; otherwise fall back to the
        # single root_name so non-test packages are unaffected.
        effective_root_names = (
            root_names
            if root_names is not None
            else frozenset({
                "" if not local_package_root else local_package_root.split(".")[0]
            })
        )
        lines: t.MutableSequenceOf[str] = ["if TYPE_CHECKING:"]
        aliases: t.MutableSequenceOf[str] = []
        flext_types_emitted = include_flext_types and not cls._has_flext_types(
            collapsed,
        )
        if flext_types_emitted:
            lines.append("    from flext_core import FlextTypes")

        def type_checking_module_key(mod: str) -> t.StrPair:
            return cls._type_checking_sort_key(mod, effective_root_names)

        occupied_names = {
            name for items in merged_groups.values() for name, _attr in items
        }
        # ``from flext_core import FlextTypes`` (when emitted above) is the
        # leading absolute import; seed the previous section so the first loop
        # group only separates on a real ruff isort section transition rather
        # than against an empty prior state, and so the local-section blank that
        # follows the absolutes is preserved.
        previous_section: str | None = (
            cls._type_checking_sort_key("flext_core", effective_root_names)[0]
            if flext_types_emitted
            else None
        )
        for mod in sorted(merged_groups, key=type_checking_module_key):
            if (
                previous_section is not None
                and type_checking_module_key(mod)[0] != previous_section
            ):
                lines.append("")
            cls._emit_type_checking_module(
                mod,
                merged_groups[mod],
                lines,
                module_exports,
                (
                    local_package_root,
                    source_project,
                    occupied_names,
                    aliases,
                    package_context,
                ),
            )
            previous_section = type_checking_module_key(mod)[0]
        if aliases:
            lines.extend(("", *aliases))
        return () if len(lines) == 1 else lines


__all__: list[str] = ["FlextInfraCodegenGenerationTypeCheckingMixin"]
