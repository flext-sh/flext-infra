"""Alias and lazy-module resolution over the captured source inventory.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

from flext_cli import u
from flext_core import build_lazy_import_map

from flext_infra import c, m, p, t
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
        project: p.Infra.RopeProject,
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
        project: p.Infra.RopeProject,
        pymodule: p.Infra.RopeSemanticModule | None = None,
    ) -> t.MappingKV[str, m.Infra.SourceClassReference]:
        """Read native lazy routes without losing their exported attributes.

        ``install_lazy_exports`` accepts both a provider string and an explicit
        ``(provider, attribute)`` pair. An empty attribute elects the module
        itself. The same typed binding feeds source and upstream resolution;
        module-only consumers derive their projection from these bindings.
        The owning project supplies native import identities even when the
        initializer is parsed from proposed source rather than a live module.

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
        aliases: t.MutableMappingKV[str, m.Infra.SourceClassReference] = {}
        for occurrence in finder.find_occurrences(pymodule=parsed):
            mapping = cls._call_alias_source(source, words, occurrence.offset, parsed)
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

    @classmethod
    def _call_alias_source(
        cls,
        source: str,
        words: p.Infra.RopeWorder,
        offset: int,
        module: p.Infra.RopeParsedModule,
    ) -> str | None:
        """Return the alias-mapping argument text of one lazy-exports call.

        Args:
            source: Full native source text of the parsed package initializer.
            words: Rope's native primary and parenthesis reader.
            offset: Lexical offset of the candidate call occurrence.
            module: Authenticated native module supplying the call bindings.

        Returns:
            The literal mapping source, or None when the occurrence is not a
            lazy-exports call carrying mapping data.

        Raises:
            TypeError: If the lazy export occurrence has no native call expression.
            ValueError: If its mapping argument has no native source span.

        """
        if not words.is_a_function_being_called(offset):
            return None
        start, _end = words.get_primary_range(offset)
        _first, last = words.get_word_parens_range(offset)
        call_source = source[start:last]
        call = ast.parse(call_source, mode="eval").body
        if not isinstance(call, ast.Call):
            message = "Lazy export occurrence has no native call expression"
            raise TypeError(message)
        argument = next(
            (
                keyword.value
                for keyword in call.keywords
                if keyword.arg == "lazy_imports"
            ),
            None,
        )
        if argument is None:
            match call.args:
                case [_, _, positional_mapping, *_]:
                    argument = positional_mapping
                case _:
                    return None
        mapping = ast.get_source_segment(call_source, argument)
        if mapping is None:
            message = "Lazy export mapping argument has no native source span"
            raise ValueError(message)
        return cls._declared_alias_mapping_source(mapping, module)

    @classmethod
    def _declared_alias_mapping_source(
        cls,
        expression: str,
        module: p.Infra.RopeParsedModule,
        ancestors: frozenset[t.Pair[str, int]] = frozenset(),
    ) -> str:
        """Read one declared alias map without executing its source expressions.

        Returns:
            The dictionary literal supplied directly or through native bindings.

        Raises:
            TypeError: A native assignment has no expression value.
            ValueError: The map is ambiguous, cyclic, or not a declared literal.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        node = ast.parse(expression, mode="eval").body
        scope = module.get_scope()
        visited = set(ancestors)
        while True:
            if isinstance(node, ast.Dict):
                return cls._alias_literal_source(expression, node)
            if isinstance(node, ast.Call):
                if cls._native_alias_callable(
                    node.func,
                    scope,
                    ("flext_core", "flext_core.lazy"),
                    "build_lazy_import_map",
                ):
                    return cls._built_alias_mapping_source(
                        node, expression, module, frozenset(visited)
                    )
                if (
                    not cls._native_alias_callable(
                        node.func, scope, ("types",), "MappingProxyType"
                    )
                    or len(node.args) != 1
                    or node.keywords
                ):
                    message = "Lazy alias mapping requires its native immutable wrapper"
                    raise ValueError(message)
                node = node.args[0]
                continue
            binding = runtime.resolve_symbol(scope, node)
            if (
                binding is None
                or not FlextInfraUtilitiesRopeRuntimeTypes.assigned_name(binding)
                or len(binding.assignments) != 1
            ):
                message = "Lazy alias mapping requires one native assignment"
                raise ValueError(message)
            provider, line = runtime.definition_location(binding)
            if (
                not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider)
                or line is None
            ):
                message = "Lazy alias mapping requires a source declaration"
                raise ValueError(message)
            identity = provider.get_name(), line
            if identity in visited:
                message = f"Cyclic lazy alias mapping declaration: {identity!r}"
                raise ValueError(message)
            visited.add(identity)
            value = binding.assignments[0].ast_node
            if not isinstance(value, ast.expr):
                message = "Lazy alias mapping assignment has no native expression"
                raise TypeError(message)
            node = value
            module = provider
            expression = provider.source_code
            scope = provider.get_scope()

    @staticmethod
    def _alias_literal_source(source: str, node: ast.Dict) -> str:
        """Read the authenticated mapping's native source span.

        Returns:
            The complete dictionary expression.

        Raises:
            ValueError: The native mapping has no source span.

        """
        literal = ast.get_source_segment(source, node)
        if literal is None:
            message = "Lazy alias mapping has no native source span"
            raise ValueError(message)
        return literal

    @staticmethod
    def _native_alias_callable(
        expression: ast.expr,
        scope: p.Infra.RopeScope,
        expected_modules: t.StrSequence,
        expected_attribute: str,
    ) -> bool:
        """Prove a declared SDK callable from native import metadata alone.

        Returns:
            Whether the expression is the elected absolute native import.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        if isinstance(expression, ast.Name):
            binding = runtime.resolve_symbol(scope, expression)
            if not types.imported_name(binding):
                return False
            module = binding.imported_module
            attribute = binding.imported_name
        elif isinstance(expression, ast.Attribute) and isinstance(
            expression.value, ast.Name
        ):
            binding = runtime.resolve_symbol(scope, expression.value)
            if not types.imported_module(binding):
                return False
            module = binding
            attribute = expression.attr
        else:
            return False
        return (
            module.module_name in expected_modules
            and module.level == 0
            and attribute == expected_attribute
        )

    @classmethod
    def _built_alias_mapping_source(
        cls,
        call: ast.Call,
        source: str,
        module: p.Infra.RopeParsedModule,
        ancestors: frozenset[t.Pair[str, int]],
    ) -> str:
        """Compile literal SDK builder arguments through the native map owner.

        Returns:
            The canonical flat mapping literal produced by the SDK.

        Raises:
            ValueError: If arguments are ambiguous, dynamic or unsupported.

        """
        arguments = {keyword.arg: keyword.value for keyword in call.keywords}
        if (
            len(call.args) > 1
            or len(arguments) != len(call.keywords)
            or set(arguments) - {"module_groups", "alias_groups", "sort_keys"}
            or (call.args and "module_groups" in arguments)
        ):
            message = "Lazy builder requires its declared literal arguments"
            raise ValueError(message)
        if call.args:
            arguments["module_groups"] = call.args[0]
        modules: t.MappingKV[str, t.StrSequence] = {}
        aliases: t.MappingKV[str, t.SequenceOf[t.StrPair]] = {}
        for name in ("module_groups", "alias_groups"):
            argument = arguments.get(name)
            if argument is None or (
                isinstance(argument, ast.Constant) and argument.value is None
            ):
                continue
            expression = ast.get_source_segment(source, argument)
            if expression is None:
                message = "Lazy builder mapping has no native source span"
                raise ValueError(message)
            literal = ast.literal_eval(
                cls._declared_alias_mapping_source(expression, module, ancestors)
            )
            if name == "module_groups":
                modules = u.type_adapter(
                    t.TypeForm(t.MappingKV[str, t.StrSequence])
                ).validate_python(literal, strict=True)
            else:
                aliases = u.type_adapter(
                    t.TypeForm(t.MappingKV[str, t.SequenceOf[t.StrPair]])
                ).validate_python(literal, strict=True)
        sort = arguments.get("sort_keys", ast.Constant(value=True))
        match sort:
            case ast.Constant(value=True):
                sort_keys = True
            case ast.Constant(value=False):
                sort_keys = False
            case _:
                message = "Lazy builder ordering requires a literal boolean"
                raise ValueError(message)
        return repr(
            build_lazy_import_map(modules, alias_groups=aliases, sort_keys=sort_keys)
        )

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
    def _alias_literal_string(node: ast.expr) -> str | None:
        """Decode one native string constant without executing its expression.

        Returns:
            The sole primitive string constant, or None for another expression.

        """
        code = compile(
            ast.Expression(body=node), "<native constant>", "eval", dont_inherit=True
        )
        if code.co_names or code.co_freevars or len(code.co_consts) != 1:
            return None
        value = code.co_consts[0]
        return value if isinstance(value, str) else None

    @classmethod
    def _literal_exports(cls, source: str) -> t.LazyAliasMap:
        """Read the current native lazy export encodings from source regions.

        Returns:
            Provider and attribute pairs, including explicit module exports.

        Raises:
            ValueError: An export name or provider binding is not a literal string
                or a provider/attribute pair.

        """
        source = source.strip()
        if not (source.startswith("{") and source.endswith("}")):
            return {}
        result: t.MutableMappingKV[str, t.StrPair] = {}
        mapping = ast.parse(source, mode="eval").body
        if not isinstance(mapping, ast.Dict):
            return {}
        for key_node, value_node in zip(mapping.keys, mapping.values, strict=True):
            if key_node is None:
                return {}
            key = cls._alias_literal_string(key_node)
            if key is None:
                message = "Lazy export names require literal strings"
                raise ValueError(message)
            provider = cls._alias_literal_string(value_node)
            if provider is not None:
                result[key] = (provider, key)
                continue
            pair = (
                tuple(cls._alias_literal_string(element) for element in value_node.elts)
                if isinstance(value_node, ast.Tuple)
                else ()
            )
            match pair:
                case (str() as provider, str() as attribute):
                    result[key] = (provider, attribute)
                case _:
                    message = (
                        "Lazy export requires a provider or provider/attribute "
                        f"pair: {key}"
                    )
                    raise ValueError(message)
        return result


__all__: list[str] = ["FlextInfraUtilitiesRopeSourceBasesAliases"]
