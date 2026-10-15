"""Alias and lazy-module resolution over the captured source inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from flext_infra import c, p, t
from flext_infra._utilities._semantic_cutover.family_type_references import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)


class FlextInfraUtilitiesRopeSourceBasesAliases:
    """Alias and lazy-module resolution part of the source-bases composite."""

    @classmethod
    def _stdlib_backing_module(cls, target: str) -> str | None:
        """Return the importable real module backing one virtual stdlib module.

        Returns:
            The backing module name when the target imports at runtime and its
            declaration file is importable under its own stem; otherwise None.

        """
        if cls._stdlib_backing_cache is None:
            cls._stdlib_backing_cache = {}
        cached = cls._stdlib_backing_cache.get(target, "")
        if cached:
            return cached or None
        backing: str | None = None
        try:
            runtime = importlib.import_module(target)
        except ImportError:
            runtime = None
        file = getattr(runtime, "__file__", None)
        if file:
            stem = Path(file).stem
            if stem != target.rpartition(".")[-1] and importlib.util.find_spec(stem):
                backing = stem
        cls._stdlib_backing_cache[target] = backing or ""
        return backing

    _stdlib_backing_cache: t.StrDict | None = None

    @classmethod
    def lazy_module_aliases(
        cls,
        module: str,
        path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject | None = None,
        pymodule: p.Infra.RopePyModule | None = None,
    ) -> t.StrDict:
        """Read the ``install_lazy_exports`` namespace alias map of one module.

        The canonical package facade binds its public namespace names (``m``,
        ``p``, ``t`` and siblings) to provider modules through a lazy-exports
        call whose final argument is the alias mapping. Those names are module
        reexports, not lexical imports, so the lexical inventory cannot see
        them; base references qualified through the facade (``m.BaseModel``
        with ``from <pkg> import m``) must rewrite to the provider module
        before namespace resolution.

        Returns:
            Alias name to absolute provider module path.

        Raises:
            TypeError: The parsed module is not a native Rope source module or
                the native parameter reader is absent.
            ValueError: The parsed module differs from its native Rope snapshot.

        """
        # Lazy package propagation belongs to initializers. Ordinary module
        # bindings are resolved by the lexical inventory, so their executable
        # bodies are not inputs to this package-alias reader.
        if path.name != c.Infra.INIT_PY:
            return {}
        # A required initializer that does not parse remains a real input error.
        parsed = (
            pymodule
            if pymodule is not None
            else FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, source
            )
        )
        if parsed.source_code != source:
            message = "Lazy aliases differ from their native Rope snapshot"
            raise ValueError(message)
        if not isinstance(parsed, p.Infra.RopeSourceModule):
            message = "Lazy aliases require a native Rope source module"
            raise TypeError(message)
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
            parsed.pycore.project, "install_lazy_exports"
        )
        words = FlextInfraUtilitiesRopeRuntimeModules.runtime_callable(
            "rope.base.worder", "Worder"
        )(source, handle_ignores=True)
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Lazy aliases require Rope's native parameter reader"
            raise TypeError(message)
        package = module
        aliases: t.StrDict = {}
        for occurrence in finder.find_occurrences(pymodule=parsed):
            mapping = cls._call_alias_source(source, words, occurrence.offset)
            if mapping is None:
                continue
            for key, value in cls._literal_mapping(mapping).items():
                resolved = cls._absolute_alias(package, value)
                if resolved is None:
                    continue
                aliases[key] = resolved
        return aliases

    @staticmethod
    def _call_alias_source(
        source: str,
        words: p.Infra.RopeWorder,
        offset: int,
    ) -> str | None:
        """Return the alias-mapping argument text of one lazy-exports call.

        Args:
            source: Full native source text of the parsed package initializer.
            words: Rope's native parameter reader over that source text.
            offset: Lexical offset of the candidate call occurrence.

        Returns:
            The literal mapping source, or None when the occurrence is not a
            lazy-exports call carrying mapping data.

        """
        if not words.is_a_function_being_called(offset):
            return None
        first, last = words.get_word_parens_range(offset)
        arguments, keywords = words.get_parameters(first, last - 1)
        mapping = next(
            (
                arg
                for arg in (*arguments, *(value for _name, value in keywords))
                if arg.lstrip().startswith("{")
                or arg.partition("(")[0].strip() == "MappingProxyType"
            ),
            None,
        )
        if mapping is None:
            return None
        mapping_start = source.index(mapping, first + 1, last)
        if mapping.partition("(")[0].strip() == "MappingProxyType":
            inner_first, inner_last = words.get_word_parens_range(mapping_start)
            return source[inner_first + 1 : inner_last - 1].strip()
        brace_first, brace_last = words.code_finder.get_word_parens_range(
            mapping_start, "{", "}"
        )
        return source[brace_first:brace_last]

    @staticmethod
    def _absolute_alias(package: str, value: str) -> str | None:
        """Rewrite one relative alias value to an absolute provider module path.

        Args:
            package: Absolute name of the package owning the alias map.
            value: Raw alias value read from the native mapping literal.

        Returns:
            The absolute module path, or None when the relative depth escapes
            the package root.

        """
        if not value.startswith("."):
            return value
        parts = package.split(".") if package else []
        depth = len(value) - len(value.lstrip("."))
        remainder = value.lstrip(".")
        if depth > len(parts):
            return None
        base = ".".join(parts[: len(parts) - depth + 1]) if depth else package
        return ".".join(part for part in (base, remainder) if part)

    @staticmethod
    def _literal_mapping(source: str) -> t.StrDict:
        """Read string module routes from native mapping-entry regions.

        Returns:
            Constant module routes, excluding attribute-valued export entries.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        source = source.strip()
        if not (source.startswith("{") and source.endswith("}")):
            return {}
        result: t.StrDict = {}
        split = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments
        for begin, end in split(source, 1, len(source) - 1, ","):
            parts = split(source, begin, end, ":")
            if len(parts) != 2:
                return {}
            (key_start, key_end), (value_start, value_end) = parts
            key = refactors.literal_string(source[key_start:key_end])
            if key is None:
                return {}
            value = refactors.literal_string(source[value_start:value_end])
            if value is None:
                result.pop(key, None)
            else:
                result[key] = value
        return result


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesAliases"]
