"""Alias and lazy-module resolution over the captured source inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities._semantic_cutover.family_type_references import (
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities.rope_runtime_refactors import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
)
from flext_infra._utilities.rope_runtime_types import (
    FlextInfraUtilitiesRopeRuntimeTypes,
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
        pymodule: p.Infra.RopeSemanticModule | None = None,
    ) -> t.StrDict:
        """Project the provider module of every declared lazy export binding.

        Returns:
            Alias name to absolute provider module path.

        """
        return {
            name: binding.target
            for name, binding in cls.lazy_export_bindings(
                module,
                path,
                source,
                project=project,
                pymodule=pymodule,
            ).items()
        }

    @classmethod
    def lazy_export_bindings(
        cls,
        module: str,
        path: Path,
        source: str,
        *,
        project: p.Infra.RopeProject | None = None,
        pymodule: p.Infra.RopeSemanticModule | None = None,
    ) -> t.MappingKV[str, m.Infra.SourceClassReference]:
        """Read native lazy routes without losing their exported attributes.

        ``install_lazy_exports`` accepts both a provider string and an explicit
        ``(provider, attribute)`` pair. An empty attribute elects the module
        itself. The same typed binding feeds source and upstream resolution;
        module-only consumers derive their projection from these bindings.

        Returns:
            The absolute provider and exact attribute of every declared export.

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
            pymodule.get_module()
            if pymodule is not None
            else FlextInfraUtilitiesRopeRuntimeModules.build_string_module(
                project, source
            )
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(parsed):
            message = "Lazy aliases require a native Rope source module"
            raise TypeError(message)
        if parsed.source_code != source:
            message = "Lazy aliases differ from their native Rope snapshot"
            raise ValueError(message)
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.lexical_occurrence_finder(
            parsed.pycore.project, "install_lazy_exports"
        )
        words = FlextInfraUtilitiesRopeRuntimeModules.runtime_callable(
            "rope.base.worder", "Worder"
        )(source, handle_ignores=True)
        if not isinstance(words, p.Infra.RopeWorder):
            message = "Lazy aliases require Rope's native parameter reader"
            raise TypeError(message)
        aliases: dict[str, m.Infra.SourceClassReference] = {}
        for occurrence in finder.find_occurrences(pymodule=parsed):
            mapping = cls._call_alias_source(source, words, occurrence.offset)
            if mapping is None:
                continue
            for key, (provider, attribute) in cls._literal_exports(mapping).items():
                resolved = cls._absolute_alias(module, provider)
                if resolved is None:
                    message = f"Lazy provider escapes its package: {module}.{key}"
                    raise ValueError(message)
                aliases[key] = m.Infra.SourceClassReference(
                    target=resolved,
                    attributes=(attribute,) if attribute else (),
                    qualified_base=f"{module}.{key}",
                )
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
    def _literal_exports(source: str) -> t.LazyAliasMap:
        """Read the current native lazy export encodings from source regions.

        Returns:
            Provider and attribute pairs, including explicit module exports.

        Raises:
            ValueError: An export name or provider binding is not a literal string
                or a provider/attribute pair.

        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        source = source.strip()
        if not (source.startswith("{") and source.endswith("}")):
            return {}
        result: dict[str, t.StrPair] = {}
        split = FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_segments
        for begin, end in split(source, 1, len(source) - 1, ","):
            match split(source, begin, end, ":"):
                case [(key_start, key_end), (value_start, value_end)]:
                    pass
                case _:
                    return {}
            key = refactors.literal_string(source[key_start:key_end])
            if key is None:
                message = "Lazy export names require literal strings"
                raise ValueError(message)
            expression = source[value_start:value_end].strip()
            provider = refactors.literal_string(expression)
            if provider is not None:
                result[key] = (provider, key)
                continue
            if expression.startswith("(") and expression.endswith(")"):
                match tuple(
                    refactors.literal_string(expression[start:stop])
                    for start, stop in split(expression, 1, len(expression) - 1, ",")
                ):
                    case (str() as provider, str() as attribute):
                        result[key] = (provider, attribute)
                        continue
            message = (
                f"Lazy export requires a provider or provider/attribute pair: {key}"
            )
            raise ValueError(message)
        return result


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesAliases"]
