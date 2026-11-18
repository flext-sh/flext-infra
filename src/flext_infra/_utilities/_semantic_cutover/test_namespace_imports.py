"""Semantic test-namespace import cutover planning.

Authored tests consume the public API of ``src``, ``scripts``, ``examples`` and
other first-party namespaces through the generated ``tests`` namespace. This
planner rewrites direct, deep, relative and non-canonical-alias imports to that
namespace so ``make mod`` fixes the whole import law, not only reports it.

The implementation is line/offset based over the rope-owned source; it never
imports ``ast`` or ``cst``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, p, t
from flext_infra._utilities import FlextInfraUtilitiesProjectManagedArtifacts
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesSemanticCutoverTestNamespaceImports(
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Rewrite test imports to the generated ``tests`` namespace."""

    FIRST_PARTY_TIERS: ClassVar[t.StrTuple] = (
        r"flext_[a-z0-9_]+",
        "scripts",
        "examples",
        "tools",
        "infra",
        "config",
    )
    FROM_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^from\s+(?P<module>\.+|\.*[A-Za-z_][\w.]*)\s+import\s+(?P<names>.+)$",
        re.DOTALL,
    )
    IMPORT_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^import\s+(?P<names>.+)$",
        re.DOTALL,
    )
    ALIAS_PARTS: ClassVar[int] = 3
    TESTS_NAMESPACE: ClassVar[str] = "tests"
    FLEXT_PREFIX: ClassVar[str] = "flext_"
    FLEXT_TESTS_PACKAGE: ClassVar[str] = "flext_tests"
    FLEXT_TESTS_ALIAS: ClassVar[str] = "api"
    META_DIRECTORY: ClassVar[str] = "_meta"

    @classmethod
    def _plan_test_namespace_imports(
        cls,
        root: Path,
        sources: Mapping[Path, str],
        findings: Sequence[p.Infra.ModOccurrence],
        *,
        project: p.Infra.RopeProject,
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan import rewrites for every finding in the selected phase.

        Returns:
            The semantic edits that converge the import law.

        """
        meta_root = root / c.Infra.DIR_TESTS / cls.META_DIRECTORY
        paths = tuple(
            sorted(
                {
                    (root / finding.file).resolve()
                    for finding in findings
                    if finding.file
                },
            ),
        )
        items = tuple(
            (path, sources[path])
            for path in paths
            if path in sources and not path.is_relative_to(meta_root)
        )
        first_party = cls._first_party(root, project)
        return cls._semantic_edits(
            items,
            lambda path, source: cls.rewrite_test_namespace_imports(
                root, path, source, first_party
            ),
        )

    @classmethod
    def _first_party(cls, root: Path, project: p.Infra.RopeProject) -> re.Pattern[str]:
        """First-party modules: the FLEXT tiers plus the repository's own facts.

        The declared package and the distribution a package-less repository
        consumes come from the repository declaration, so no consumer is
        named here.

        Returns:
            The compiled top-level module pattern.

        """
        declaration = (
            FlextInfraUtilitiesProjectManagedArtifacts
            .load_repository_declaration_inputs(root, source_project=project)
            .unwrap()
            .spec.project
        )
        declared = (
            ()
            if declaration is None
            else tuple(
                re.escape(name)
                for name in (declaration.package_name, declaration.upstream)
                if name
            )
        )
        alternatives = "|".join((*cls.FIRST_PARTY_TIERS, *declared))
        return re.compile(rf"^(?:{alternatives})(?:\.|$)")

    @classmethod
    def rewrite_test_namespace_imports(
        cls,
        root: Path,
        file_path: Path,
        source: str,
        first_party: re.Pattern[str],
    ) -> t.Infra.TransformResult:
        """Rewrite one module's imports and canonical aliases.

        Returns:
            The rewritten source and the applied changes.

        """
        groups = cls._import_groups(source)
        if not groups:
            return source, ()
        collected, renames, targeted = cls._collect_imports(
            root,
            file_path,
            groups,
            first_party,
        )
        if not collected:
            return source, ()
        merged = ", ".join(sorted(set(collected)))
        rewritten = cls._merge_imports(source, groups, targeted, merged, renames)
        if rewritten == source:
            return source, ()
        return rewritten, ("rewired test imports to the generated tests namespace",)

    @classmethod
    def _collect_imports(
        cls,
        root: Path,
        file_path: Path,
        groups: Sequence[tuple[int, int, str]],
        first_party: re.Pattern[str],
    ) -> tuple[list[str], dict[str, str], set[int]]:
        """Collect canonical names, alias renames and targeted groups.

        Returns:
            The collected names, renames and targeted group starts.

        """
        collected: list[str] = []
        renames: dict[str, str] = {}
        targeted: set[int] = set()
        for start, _end, logical in groups:
            parsed = cls._parse_import(logical)
            if parsed is None:
                continue
            module, names = parsed
            if not module:
                for target, bound in cls._plain_import_targets(names, first_party):
                    targeted.add(start)
                    collected.append(target)
                    if bound != target:
                        renames[bound] = target
                continue
            target = cls._target_module(root, file_path, module, first_party)
            if target is None:
                continue
            targeted.add(start)
            for name, alias in names:
                collected.append(name)
                if alias is not None and alias != name:
                    renames[alias] = name
        return collected, renames, targeted

    @classmethod
    def _merge_imports(
        cls,
        source: str,
        groups: Sequence[tuple[int, int, str]],
        targeted: set[int],
        merged: str,
        renames: Mapping[str, str],
    ) -> str:
        """Merge targeted imports and rename their stripped aliases.

        Returns:
            The rewritten source.

        """
        lines = source.splitlines(keepends=True)
        result: list[str] = []
        inserted = False
        group_by_start = {start: (start, end) for start, end, _ in groups}
        index = 0
        while index < len(lines):
            span = group_by_start.get(index)
            if span is None:
                result.append(lines[index])
                index += 1
                continue
            start, end = span
            if start in targeted:
                if not inserted:
                    result.append(f"from {cls.TESTS_NAMESPACE} import {merged}\n")
                    inserted = True
                index = end
                continue
            result.extend(lines[start:end])
            index = end
        if not inserted:
            position = cls._namespace_import_position(result)
            result.insert(
                position,
                f"from {cls.TESTS_NAMESPACE} import {merged}\n",
            )
        return "".join(cls._rename_aliases(line, renames) for line in result)

    @classmethod
    def _import_groups(cls, source: str) -> tuple[tuple[int, int, str], ...]:
        """Return top-level import statement spans and their logical text.

        Returns:
            A tuple of ``(start_line, end_line, logical_text)``.

        """
        lines = source.splitlines(keepends=True)
        groups: list[tuple[int, int, str]] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            if not line.startswith(("from ", "import ")):
                index += 1
                continue
            start = index
            depth = line.count("(") - line.count(")")
            index += 1
            while depth > 0 and index < len(lines):
                depth += lines[index].count("(") - lines[index].count(")")
                index += 1
            logical = "".join(lines[start:index]).strip()
            groups.append((start, index, logical))
        return tuple(groups)

    @classmethod
    def _parse_import(
        cls, logical: str
    ) -> tuple[str, tuple[tuple[str, str | None], ...]] | None:
        """Parse one logical import statement.

        Returns:
            The module and its ``(name, alias)`` entries, or ``None``.

        """
        text = logical.split("#", 1)[0].strip()
        match = cls.FROM_PATTERN.match(text)
        if match is not None:
            return match.group("module"), cls._parse_names(match.group("names"))
        match = cls.IMPORT_PATTERN.match(text)
        if match is None:
            return None
        names: list[tuple[str, str | None]] = []
        for entry in cls._split_commas(match.group("names")):
            parts = entry.split()
            if not parts:
                continue
            name = parts[0]
            alias = cls._alias(parts)
            names.append((name, alias))
        return "", tuple(names)

    @classmethod
    def _parse_names(cls, text: str) -> tuple[tuple[str, str | None], ...]:
        """Parse the names of a from-import.

        Returns:
            The ``(name, alias)`` entries.

        """
        cleaned = text.strip()
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = cleaned[1:-1]
        names: list[tuple[str, str | None]] = []
        for entry in cls._split_commas(cleaned):
            parts = entry.split()
            if not parts:
                continue
            name = parts[0]
            alias = cls._alias(parts)
            names.append((name, alias))
        return tuple(names)

    @classmethod
    def _alias(cls, parts: Sequence[str]) -> str | None:
        """Return the alias of one ``name as alias`` entry.

        Returns:
            The alias, or ``None`` when the entry has no alias.

        """
        if len(parts) >= cls.ALIAS_PARTS and parts[1] == "as":
            return parts[cls.ALIAS_PARTS - 1]
        return None

    @staticmethod
    def _split_commas(text: str) -> tuple[str, ...]:
        """Split a name list on top-level commas.

        Returns:
            The stripped entries.

        """
        entries: list[str] = []
        depth = 0
        start = 0
        for index, character in enumerate(text):
            if character in "([{":
                depth += 1
            elif character in ")]}":
                depth -= 1
            elif character == "," and depth == 0:
                entries.append(text[start:index].strip())
                start = index + 1
        tail = text[start:].strip()
        if tail:
            entries.append(tail)
        return tuple(entry for entry in entries if entry)

    @classmethod
    def _target_module(
        cls,
        root: Path,
        file_path: Path,
        module: str,
        first_party: re.Pattern[str],
    ) -> str | None:
        """Return the canonical test namespace target for a module.

        Returns:
            ``"tests"`` when the import must move, otherwise ``None``.

        """
        if module.startswith("."):
            resolved = cls._resolve_relative(root, file_path, module)
            if resolved is None:
                return None
            module = resolved
        if module == cls.TESTS_NAMESPACE or module.startswith(
            f"{cls.TESTS_NAMESPACE}."
        ):
            return cls.TESTS_NAMESPACE
        if first_party.match(module):
            return cls.TESTS_NAMESPACE
        return None

    @classmethod
    def _plain_import_targets(
        cls,
        names: Sequence[tuple[str, str | None]],
        first_party: re.Pattern[str],
    ) -> tuple[tuple[str, str], ...]:
        """First-party plain imports as canonical tests aliases.

        Returns:
            Each ``(target, bound)`` pair: the canonical alias and the name
            the import bound.

        """
        pairs: list[tuple[str, str]] = []
        for dotted, alias in names:
            root = dotted.split(".", 1)[0]
            if root == cls.TESTS_NAMESPACE:
                continue
            if not first_party.match(dotted):
                continue
            target = (
                cls.FLEXT_TESTS_ALIAS
                if root == cls.FLEXT_TESTS_PACKAGE
                else root.removeprefix(cls.FLEXT_PREFIX)
            )
            pairs.append((target, alias or root))
        return tuple(pairs)

    @staticmethod
    def _resolve_relative(
        root: Path,
        file_path: Path,
        module: str,
    ) -> str | None:
        """Resolve a relative module to its absolute name.

        Returns:
            The absolute module name, or ``None`` when it escapes the root.

        """
        level = len(module) - len(module.lstrip("."))
        remainder = module[level:]
        package = list(file_path.relative_to(root).parent.parts)
        if level > len(package) + 1:
            return None
        base = package[: max(len(package) - (level - 1), 0)]
        if remainder:
            base.extend(remainder.split("."))
        return ".".join(base)

    @staticmethod
    def _rename_aliases(line: str, renames: Mapping[str, str]) -> str:
        """Rename stripped aliases in one non-import usage line.

        Returns:
            The rewritten line.

        """
        for alias, canonical in renames.items():
            line = re.sub(rf"\b{re.escape(alias)}\b", canonical, line)
        return line

    @staticmethod
    def _namespace_import_position(lines: Sequence[str]) -> int:
        """Return the first safe import position after docstring/future.

        Returns:
            The insertion index.

        """
        position = 0
        if lines:
            first = lines[0].strip()
            if first.startswith(('"""', "'''")):
                quote = first[:3]
                position = 1
                while position < len(lines) and quote not in lines[position]:
                    position += 1
                position += 1
        while position < len(lines):
            stripped = lines[position].strip()
            if stripped.startswith(("from ", "import ")):
                position += 1
                continue
            if not stripped:
                position += 1
                continue
            break
        return position


__all__: list[str] = [
    "FlextInfraUtilitiesSemanticCutoverTestNamespaceImports",
]
