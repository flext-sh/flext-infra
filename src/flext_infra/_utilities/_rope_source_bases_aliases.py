"""Alias and lazy-module resolution over the captured source inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from flext_infra import c, p, t
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
            if not words.is_a_function_being_called(occurrence.offset):
                continue
            first, last = words.get_word_parens_range(occurrence.offset)
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
                continue
            mapping_start = source.index(mapping, first + 1, last)
            if mapping.partition("(")[0].strip() == "MappingProxyType":
                first, last = words.get_word_parens_range(mapping_start)
                mapping = source[first + 1 : last - 1].strip()
            else:
                first, last = words.code_finder.get_word_parens_range(
                    mapping_start, "{", "}"
                )
                mapping = source[first:last]
            for key, value in cls._literal_mapping(mapping).items():
                if value.startswith("."):
                    parts = package.split(".") if package else []
                    depth = len(value) - len(value.lstrip("."))
                    remainder = value.lstrip(".")
                    if depth > len(parts):
                        continue
                    base = (
                        ".".join(parts[: len(parts) - depth + 1]) if depth else package
                    )
                    value = ".".join(part for part in (base, remainder) if part)
                aliases[key] = value
        return aliases

    @staticmethod
    def _literal_mapping(source: str) -> t.StrDict:
        """Decode flat alias data from complete native Rope string tokens.

        Returns:
            Constant alias pairs, or no aliases for dynamic mapping data.
        """
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        regions = refactors.ignored_regions(source)
        strings = tuple(
            (start, end)
            for start, end, metadata in regions
            if metadata.get("prefix") is not None
        )
        if not strings or len(strings) % 2:
            return {}
        remaining = list(source)
        for start, end, metadata in regions:
            if metadata.get("prefix") is None:
                remaining[start:end] = " " * (end - start)
        text = "".join(remaining)
        if text[: strings[0][0]].strip() != "{":
            return {}
        result: t.StrDict = {}
        for index in range(0, len(strings), 2):
            key_start, key_end = strings[index]
            value_start, value_end = strings[index + 1]
            if text[key_end:value_start].strip() != ":":
                return {}
            key = refactors.literal_string(source[key_start:key_end])
            value = refactors.literal_string(source[value_start:value_end])
            if key is None or value is None:
                return {}
            if index and text[strings[index - 1][1] : key_start].strip() != ",":
                return {}
            result[key] = value
        tail = "".join(text[strings[-1][1] :].split())
        return result if tail in {"}", ",}"} else {}


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesAliases"]
