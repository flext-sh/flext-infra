"""Closed source-template witnesses for module-level generated functions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import sys
from pathlib import Path
from types import (
    BuiltinFunctionType,
    CodeType,
    FunctionType,
    GetSetDescriptorType,
    MemberDescriptorType,
    MethodDescriptorType,
    ModuleType,
    WrapperDescriptorType,
)

from flext_infra import m, p, r, t, u
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)


class FlextInfraWorkspaceGeneratedFunction:
    """Interpret a closed compiler's data without invoking its Python callbacks."""

    def __init__(self, witness: m.Infra.NativeSourceWitness) -> None:
        """Keep all observations local to the current immutable source witness."""
        self._witness = witness
        self._inputs: dict[Path, m.Cli.AtomicFileState] = {
            witness.source: witness.state,
        }
        self._trees: dict[Path, ast.Module] = {
            witness.source: ast.parse(
                witness.module.source_code, filename=str(witness.source),
            ),
        }
        self._codes: dict[Path, p.Infra.NativeCodeIdentity] = {
            witness.source: witness.code,
        }
        self._emitted: dict[int, m.Infra.NativeGeneratedFunctionProof] = {}
        self._dictionaries: set[int] = set()
        self._patterns: dict[int, str] = {}

    @classmethod
    def compile(
        cls,
        value: FunctionType,
        supplier: str,
        attribute: str,
        witness: m.Infra.NativeSourceWitness,
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Derive one emitted function from a unique physical literal invocation.

        No compiler factory, generated source, descriptor hook, or module hook
        executes here. Unsupported grammar raises its original ``ValueError``.

        Returns:
            Expected code, globals, annotations and consulted physical inputs.

        Raises:
            ValueError: If a source binding or closed compiler grammar is unproved.
        """
        engine = cls(witness)
        namespace = engine._module(supplier)
        if type(value) is not FunctionType or vars(namespace).get(attribute) is not value:
            msg = "generated function is not its registered source export"
            raise ValueError(msg)
        matches = []
        for match in witness.finder.get_matches(
            "${export} = ${factory}(${first}, ${second})", {},
        ):
            first, _last = match.get_region()
            scope = u.Infra.scope_at(witness.module, first)
            if scope.get_kind() != "Module":
                continue
            captured = {}
            for name in ("export", "factory", "first", "second"):
                start, end = u.Infra.semantic_capture_region(match, name)
                captured[name] = witness.module.source_code[start:end]
            if captured["export"] == attribute:
                matches.append(captured)
        if len(matches) != 1:
            msg = "generated function has no unique physical literal factory call"
            raise ValueError(msg)
        invocation = matches[0]
        factory_name = invocation["factory"]
        if not factory_name.isidentifier():
            msg = "generated function factory is not a direct source binding"
            raise ValueError(msg)
        factory = vars(namespace).get(factory_name)
        if type(factory) is not FunctionType or factory.__globals__ is not vars(namespace):
            msg = "generated function factory has a foreign execution namespace"
            raise ValueError(msg)
        function, tree, globals_ = engine._function(factory)
        if Path(factory.__code__.co_filename) != witness.source:
            msg = "generated function factory is outside its physical declaration"
            raise ValueError(msg)
        arguments = (
            *function.args.posonlyargs,
            *function.args.args,
        )
        if (
            len(arguments) != 2
            or function.args.kwonlyargs
            or function.args.vararg is not None
            or function.args.kwarg is not None
            or function.args.defaults
            or function.args.kw_defaults
        ):
            msg = "generated function compiler requires two closed literal parameters"
            raise ValueError(msg)
        literals = tuple(
            ast.parse(invocation[name], mode="eval").body
            for name in ("first", "second")
        )
        if any(not isinstance(item, ast.Constant) or type(item.value) is not str for item in literals):
            msg = "generated function compiler arguments are not exact string literals"
            raise ValueError(msg)
        local: dict[str, p.AttributeProbe] = {
            argument.arg: literal.value
            for argument, literal in zip(arguments, literals, strict=True)
        }
        returned = engine._statements(function.body, local, globals_, tree)
        if (
            type(returned) is not CodeType
            or id(returned) not in engine._emitted
            or len(engine._emitted) != 1
        ):
            msg = "closed compiler did not return its sole emitted function"
            raise ValueError(msg)
        proof = engine._emitted[id(returned)]
        if returned.co_name != attribute or value.__name__ != attribute:
            msg = "generated function name differs from its physical export"
            raise ValueError(msg)
        for state in engine._inputs.values():
            current = u.Cli.atomic_read_binary_file_state(
                state.path, required=True,
            ).unwrap()
            if current != state:
                msg = f"generated compiler source changed: {state.path}"
                raise ValueError(msg)
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            proof.model_copy(update={"inputs": tuple(engine._inputs.values())}),
        )

    @classmethod
    def compile_named_tuple(
        cls,
        owner: p.AttributeProbe,
        attribute: str,
        witness: m.Infra.NativeSourceWitness,
    ) -> p.Result[m.Infra.NativeGeneratedFunctionProof]:
        """Compile the physical native tuple lambda from its declared field layout."""
        if type(attribute) is not str or attribute != "__new__":
            msg = "native tuple source proof supports only its generated constructor"
            raise ValueError(msg)
        engine = cls(witness)
        namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        qualified = vars(type)["__qualname__"].__get__(owner, type(owner))
        if type(qualified) is not str:
            msg = "native tuple owner has no exact string qualified identity"
            raise ValueError(msg)
        first_line = namespace.get("__firstlineno__")
        location = str(first_line) if type(first_line) is int else "<unavailable>"
        invocation = engine._tuple_invocation(owner, witness)
        nodes = engine._trees[witness.source].body
        declaration = None
        for component in qualified.split(".") if invocation is None else ():
            candidates = [
                node for node in nodes
                if isinstance(node, ast.ClassDef) and node.name == component
            ]
            if len(candidates) != 1:
                msg = (
                    "native tuple has no unique physical class declaration: "
                    f"qualname={qualified[:160]!r}; attribute={attribute[:80]!r}; "
                    f"source={witness.source}; firstlineno={location}; "
                    f"component={component[:80]!r}; candidates={len(candidates)}"
                )
                raise ValueError(msg)
            declaration = candidates[0]
            nodes = declaration.body
        if declaration is None and invocation is None:
            msg = "native tuple has no physical declaration"
            raise ValueError(msg)
        fields = [
            node for node in declaration.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        ] if declaration is not None else []
        names = tuple(node.target.id for node in fields)
        module_name = namespace.get("__module__")
        if type(module_name) is not str:
            msg = "native tuple declaration has no registered module"
            raise ValueError(msg)
        module = engine._module(module_name)
        engine._source(module)
        defaults = []
        for field in fields:
            if field.value is None:
                if defaults:
                    msg = "native tuple required field follows a declared default"
                    raise ValueError(msg)
                continue
            defaults.append(
                engine._expression(
                    field.value, {}, vars(module), engine._trees[witness.source],
                ),
            )
        collections = engine._module("collections")
        factory = vars(collections).get("namedtuple")
        definition, tree, globals_ = engine._function(factory)
        engine._builtin("eval", globals_)
        emissions = [
            node for node in definition.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == attribute
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "eval"
            and not node.value.keywords
            and len(node.value.args) == 2
            and all(isinstance(argument, ast.Name) for argument in node.value.args)
        ]
        if len(emissions) != 1 or len(definition.args.args) < 2:
            msg = "native tuple compiler has no unique physical lambda emission"
            raise ValueError(msg)
        emission = emissions[0]
        typename = declaration.name if declaration is not None else invocation[0]
        raw_fields = list(names) if invocation is None else invocation[1]
        local = engine._tuple_normalization(
            definition,
            tree,
            globals_,
            typename,
            raw_fields,
            tuple(defaults) if invocation is None else invocation[2],
            emission,
        )
        names = local[definition.args.args[1].arg]
        observed_fields = namespace.get("_fields")
        if (
            type(names) is not tuple
            or any(type(name) is not str for name in names)
            or type(observed_fields) is not tuple
            or any(type(name) is not str for name in observed_fields)
            or observed_fields != names
            or len(set(names)) != len(names)
            or any(name.startswith("_") for name in names)
        ):
            msg = "native tuple field layout differs from physical constructor data"
            raise ValueError(msg)
        needed = {argument.id for argument in emission.value.args}
        before = definition.body[:definition.body.index(emission)]
        selected = []
        changed = True
        while changed:
            changed = False
            for node in before:
                written = {
                    item.id for item in ast.walk(node)
                    if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store)
                }
                if written & needed and not written & set(local):
                    if not any(node is previous for previous in selected):
                        selected.append(node)
                        changed = True
                    needed.update(
                        item.id for item in ast.walk(node)
                        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
                    )
        # The declaration's exact string fields already establish the native
        # constructor's normalization input; only code-bearing data flow runs.
        ordered = [
            node for node in before if any(node is item for item in selected)
        ]
        returned = engine._statements(ordered, local, globals_, tree)
        if returned is not None:
            msg = "native tuple code inputs return before their declared emission"
            raise ValueError(msg)
        text, generated_globals = (
            engine._expression(argument, local, globals_, tree)
            for argument in emission.value.args
        )
        if (
            type(text) is not str
            or type(generated_globals) is not dict
            or id(generated_globals) not in engine._dictionaries
            or type(generated_globals.get("__builtins__")) is not dict
            or generated_globals["__builtins__"]
        ):
            msg = "native tuple emission lacks closed text and empty builtin storage"
            raise ValueError(msg)
        parsed = ast.parse(text, mode="eval")
        if (
            not isinstance(parsed.body, ast.Lambda)
            or parsed.body.args.defaults
            or parsed.body.args.kw_defaults
            or parsed.body.args.vararg is not None
            or parsed.body.args.kwarg is not None
        ):
            msg = "native tuple constructor is not a closed physical lambda"
            raise ValueError(msg)
        root = builtins.compile(
            text, "<string>", "eval",
            dont_inherit=True, optimize=sys.flags.optimize,
        )
        codes = tuple(item for item in root.co_consts if type(item) is CodeType)
        if len(codes) != 1 or codes[0].co_freevars or codes[0].co_cellvars:
            msg = "native tuple lambda has unsupported executable closure state"
            raise ValueError(msg)
        annotations = {}
        if invocation is None:
            typing = engine._module("typing")
            annotator, _typing_tree, _typing_globals = engine._function(
                vars(typing).get("_make_nmtuple"),
            )
            assignments = [
                node for node in annotator.body
                if isinstance(node, ast.Assign) and len(node.targets) == 2
                and isinstance(node.targets[0], ast.Attribute)
                and node.targets[0].attr == "__annotations__"
                and isinstance(node.targets[1], ast.Attribute)
                and node.targets[1].attr == "__annotations__"
                and isinstance(node.targets[1].value, ast.Attribute)
                and node.targets[1].value.attr == "__new__"
            ]
            annotations = namespace.get("__annotations__")
            if (
                len(assignments) != 1
                or type(annotations) is not dict
                or any(type(name) is not str for name in annotations)
                or tuple(annotations) != names
            ):
                msg = "native tuple annotation storage lacks its physical attachment"
                raise ValueError(msg)
        for state in engine._inputs.values():
            if u.Cli.atomic_read_binary_file_state(
                state.path, required=True,
            ).unwrap() != state:
                msg = f"native tuple compiler source changed: {state.path}"
                raise ValueError(msg)
        return r[m.Infra.NativeGeneratedFunctionProof].ok(
            m.Infra.NativeGeneratedFunctionProof(
                code=codes[0],
                globals=generated_globals,
                annotations=annotations,
                defaults=local["defaults"],
                keyword_defaults=None,
                closure=(),
                inputs=tuple(engine._inputs.values()),
            ),
        )

    def _tuple_invocation(
        self,
        owner: p.AttributeProbe,
        witness: m.Infra.NativeSourceWitness,
    ) -> t.Triple[str, p.AttributeProbe, p.AttributeProbe | None] | None:
        """Elect a physical constructor assignment by its exact registered alias."""
        owner_namespace = vars(type)["__dict__"].__get__(owner, type(owner))
        supplier = owner_namespace.get("__module__")
        if type(supplier) is not str:
            msg = "native tuple constructor has no exact supplier name"
            raise ValueError(msg)
        module = self._module(supplier)
        namespace = vars(module)
        aliases = {
            name for name, value in namespace.items()
            if type(name) is str and value is owner
        }
        matches = []
        for match in witness.finder.get_matches(
            "${export} = ${invocation}", {},
        ):
            start, _end = match.get_region()
            if u.Infra.scope_at(witness.module, start).get_kind() != "Module":
                continue
            captured = {}
            for name in ("export", "invocation"):
                first, last = u.Infra.semantic_capture_region(match, name)
                captured[name] = witness.module.source_code[first:last]
            if captured["export"] in aliases:
                matches.append(captured)
        if not matches:
            return None
        if len(matches) != 1:
            msg = "native tuple has competing physical constructor assignments"
            raise ValueError(msg)
        invocation = matches[0]
        call = ast.parse(invocation["invocation"], mode="eval").body
        if (
            not isinstance(call, ast.Call)
            or len(call.args) != 2
            or any(isinstance(argument, ast.Starred) for argument in call.args)
            or len(call.keywords) > 1
            or any(keyword.arg != "defaults" for keyword in call.keywords)
        ):
            msg = "native tuple constructor has unsupported invocation inputs"
            raise ValueError(msg)
        collections = self._module("collections")
        tree = self._trees[witness.source]
        if isinstance(call.func, ast.Name):
            factory = self._global(call.func.id, namespace, tree)
        elif (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.attr == "namedtuple"
            and self._global(call.func.value.id, namespace, tree) is collections
        ):
            factory = vars(collections).get(call.func.attr)
        else:
            msg = "native tuple constructor has no exact physical imported binding"
            raise ValueError(msg)
        if factory is not vars(self._module("collections")).get("namedtuple"):
            msg = "native tuple constructor differs from its physical imported owner"
            raise ValueError(msg)
        self._function(factory)
        typename, fields = (self._tuple_literal(argument) for argument in call.args)
        defaults = (
            self._tuple_literal(call.keywords[0].value)
            if call.keywords else None
        )
        if (
            type(typename) is not str
            or vars(type)["__name__"].__get__(owner, type(owner)) != typename
            or not (
                type(fields) is str
                or (
                    (type(fields) is list or type(fields) is tuple)
                    and all(type(field) is str for field in fields)
                )
            )
            or not (
                defaults is None
                or type(defaults) is list
                or type(defaults) is tuple
            )
        ):
            msg = "native tuple constructor arguments are not closed string data"
            raise ValueError(msg)
        return typename, fields, defaults

    @staticmethod
    def _tuple_literal(node: ast.expr) -> p.AttributeProbe | None:
        """Read only exact scalar and fixed sequence literals from a constructor."""
        if isinstance(node, ast.Constant) and (
            type(node.value) is str
            or type(node.value) is int
            or type(node.value) is bool
            or node.value is None
        ):
            return node.value
        if isinstance(node, ast.List | ast.Tuple):
            items = [
                FlextInfraWorkspaceGeneratedFunction._tuple_literal(item)
                for item in node.elts
            ]
            return items if isinstance(node, ast.List) else tuple(items)
        msg = "native tuple constructor contains nonliteral data"
        raise ValueError(msg)

    def _tuple_normalization(
        self,
        definition: ast.FunctionDef,
        tree: ast.Module,
        namespace: t.MappingKV[str, p.AttributeProbe],
        typename: str,
        fields: p.AttributeProbe,
        defaults: p.AttributeProbe | None,
        emission: ast.Assign,
    ) -> t.MutableMappingKV[str, p.AttributeProbe]:
        """Interpret the source's exact input writes before lambda construction."""
        first, second = (argument.arg for argument in definition.args.args[:2])
        local = {
            first: typename,
            second: fields,
            **{
                argument.arg: self._default(default, namespace, tree)
                for argument, default in zip(
                    definition.args.kwonlyargs,
                    definition.args.kw_defaults,
                    strict=True,
                )
                if default is not None
            },
        }
        if "defaults" not in local:
            msg = "native tuple compiler has no physical default input"
            raise ValueError(msg)
        local["defaults"] = defaults
        selected = []
        for statement in definition.body[:definition.body.index(emission)]:
            written = {
                node.id for node in ast.walk(statement)
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
            }
            written.update(
                node.value.id for node in ast.walk(statement)
                if isinstance(node, ast.Subscript)
                and isinstance(node.ctx, ast.Store)
                and isinstance(node.value, ast.Name)
            )
            if first in written or second in written:
                selected.append(statement)
        if self._statements(selected, local, namespace, tree) is not None:
            msg = "native tuple normalization returns before physical emission"
            raise ValueError(msg)
        conversions = []
        attachments = []
        for statement in definition.body:
            if (
                not isinstance(statement, ast.If)
                or statement.orelse
                or not isinstance(statement.test, ast.Compare)
                or not isinstance(statement.test.left, ast.Name)
                or statement.test.left.id != "defaults"
                or len(statement.test.ops) != 1
                or not isinstance(statement.test.ops[0], ast.IsNot)
                or len(statement.test.comparators) != 1
                or not isinstance(statement.test.comparators[0], ast.Constant)
                or statement.test.comparators[0].value is not None
            ):
                continue
            for item in statement.body:
                if not isinstance(item, ast.Assign) or len(item.targets) != 1:
                    continue
                target = item.targets[0]
                if (
                    isinstance(target, ast.Name)
                    and target.id == "defaults"
                    and isinstance(item.value, ast.Call)
                    and isinstance(item.value.func, ast.Name)
                    and item.value.func.id == "tuple"
                    and not item.value.keywords
                    and len(item.value.args) == 1
                    and isinstance(item.value.args[0], ast.Name)
                    and item.value.args[0].id == "defaults"
                    and definition.body.index(statement) < definition.body.index(emission)
                ):
                    conversions.append(item)
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == emission.targets[0].id
                    and target.attr == "__defaults__"
                    and isinstance(item.value, ast.Name)
                    and item.value.id == "defaults"
                    and definition.body.index(statement) > definition.body.index(emission)
                ):
                    attachments.append(item)
        if len(conversions) != 1 or len(attachments) != 1:
            msg = "native tuple defaults lack unique physical normalization and attachment"
            raise ValueError(msg)
        writes = [
            node for node in ast.walk(definition)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id == "defaults"
        ]
        if (
            len(writes) != 1
            or writes[0] is not conversions[0].targets[0]
            or any(
                isinstance(node, ast.Attribute)
                and isinstance(node.ctx, ast.Store)
                and node.attr == "__defaults__"
                and node is not attachments[0].targets[0]
                for node in ast.walk(definition)
            )
        ):
            msg = "native tuple compiler has competing default metadata writes"
            raise ValueError(msg)
        if defaults is not None:
            self._statements(conversions, local, namespace, tree)
        if local["defaults"] is not None and type(local["defaults"]) is not tuple:
            msg = "native tuple defaults have unsupported normalized storage"
            raise ValueError(msg)
        return local

    @staticmethod
    def _module(name: str) -> ModuleType:
        module = sys.modules.get(name)
        if type(module) is not ModuleType:
            msg = f"closed compiler supplier is not a native module: {name}"
            raise ValueError(msg)
        return module

    def _source(self, module: ModuleType) -> t.Pair[Path, ast.Module]:
        namespace = vars(module)
        name = namespace.get("__name__")
        if type(name) is not str or sys.modules.get(name) is not module:
            msg = "closed compiler module has no registered identity"
            raise ValueError(msg)
        path = FlextInfraWorkspaceEnvironmentProvenance._module_source(name).unwrap()
        if path.suffix != ".py":
            msg = f"closed compiler supplier has no physical Python source: {name}"
            raise ValueError(msg)
        if path not in self._inputs:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if state.content is None:
                msg = f"closed compiler source is absent: {path}"
                raise ValueError(msg)
            self._inputs[path] = state
            self._trees[path] = ast.parse(state.content, filename=str(path))
            self._codes[path] = builtins.compile(
                state.content, str(path), "exec",
                dont_inherit=True, optimize=sys.flags.optimize,
            )
        return path, self._trees[path]

    def _function(
        self, function: FunctionType,
    ) -> t.Triple[ast.FunctionDef, ast.Module, t.MappingKV[str, p.AttributeProbe]]:
        if type(function) is not FunctionType:
            msg = "closed compiler callback is not an exact Python function"
            raise ValueError(msg)
        namespace = function.__globals__
        module_name = namespace.get("__name__")
        if type(module_name) is not str or namespace is not vars(self._module(module_name)):
            msg = "closed compiler function has foreign globals"
            raise ValueError(msg)
        path, tree = self._source(self._module(module_name))
        if (
            function.__closure__ is not None
            or function.__builtins__ is not vars(builtins)
            or any(
                isinstance(item, ast.ImportFrom) and item.module == "__future__"
                for item in tree.body
            )
        ):
            msg = "closed compiler function has unsupported closure or future inputs"
            raise ValueError(msg)
        candidates = tuple(
            item for item in tree.body
            if isinstance(item, ast.FunctionDef)
            and item.name == function.__name__
            and item.lineno == function.__code__.co_firstlineno
            and not item.decorator_list
        )
        pending = [self._codes[path]]
        matched = False
        while pending:
            code = pending.pop()
            matched |= (
                code == function.__code__
                and code.co_filename == function.__code__.co_filename
                and code.co_linetable == function.__code__.co_linetable
                and code.co_exceptiontable == function.__code__.co_exceptiontable
            )
            pending.extend(item for item in code.co_consts if type(item) is CodeType)
        if len(candidates) != 1 or not matched:
            msg = "closed compiler function differs from its physical compilation"
            raise ValueError(msg)
        declaration = candidates[0]
        defaults = tuple(
            self._default(item, namespace, tree)
            for item in declaration.args.defaults
        )
        observed_defaults = function.__defaults__ or ()
        keyword_defaults = {
            argument.arg: self._default(default, namespace, tree)
            for argument, default in zip(
                declaration.args.kwonlyargs,
                declaration.args.kw_defaults,
                strict=True,
            )
            if default is not None
        }
        observed_keywords = function.__kwdefaults__ or {}
        if (
            len(defaults) != len(observed_defaults)
            or set(keyword_defaults) != set(observed_keywords)
            or any(
                not self._same_default(expected, observed)
                for expected, observed in zip(
                    defaults, observed_defaults, strict=True,
                )
            )
            or any(
                not self._same_default(expected, observed_keywords[name])
                for name, expected in keyword_defaults.items()
            )
        ):
            msg = "closed compiler defaults differ from physical source bindings"
            raise ValueError(msg)
        return declaration, tree, namespace

    @staticmethod
    def _same_default(
        expected: p.AttributeProbe | None,
        observed: p.AttributeProbe | None,
    ) -> bool:
        if (
            type(expected) is str
            or type(expected) is int
            or type(expected) is bool
            or expected is None
        ):
            return type(observed) is type(expected) and observed == expected
        return observed is expected

    def _default(
        self,
        node: ast.expr,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe | None:
        if isinstance(node, ast.Constant) and (
            type(node.value) is str
            or type(node.value) is int
            or type(node.value) is bool
            or node.value is None
        ):
            return node.value
        if isinstance(node, ast.Tuple):
            return tuple(self._default(item, namespace, tree) for item in node.elts)
        if isinstance(node, ast.Name) and node.id in namespace:
            assignments = [
                statement.value for statement in tree.body
                if isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == node.id
            ]
            if (
                len(assignments) == 1
                and isinstance(assignments[0], ast.Call)
                and isinstance(assignments[0].func, ast.Name)
                and assignments[0].func.id == "object"
                and not assignments[0].args
                and not assignments[0].keywords
                and namespace.get("object", vars(builtins).get("object")) is object
                and type(namespace[node.id]) is object
            ):
                return namespace[node.id]
            if (
                len(assignments) == 1
                and isinstance(assignments[0], ast.Call)
                and isinstance(assignments[0].func, ast.Name)
                and not assignments[0].args
                and not assignments[0].keywords
            ):
                name = assignments[0].func.id
                owner = namespace.get(name)
                definitions = [
                    item for item in tree.body
                    if isinstance(item, ast.ClassDef) and item.name == name
                ]
                if (
                    len(definitions) == 1
                    and not definitions[0].decorator_list
                    and len(definitions[0].bases) == 1
                    and isinstance(definitions[0].bases[0], ast.Name)
                    and definitions[0].bases[0].id == "int"
                    and len(definitions[0].body) == 1
                    and isinstance(definitions[0].body[0], ast.Pass)
                    and type(owner) is type
                    and type(namespace[node.id]) is owner
                    and vars(type)["__bases__"].__get__(owner, type(owner)) == (int,)
                    and int.__index__(namespace[node.id]) == 0
                ):
                    return namespace[node.id]
        msg = "closed compiler default has no literal or native sentinel witness"
        raise ValueError(msg)

    @staticmethod
    def _builtin(name: str, namespace: t.MappingKV[str, p.AttributeProbe]) -> p.AttributeProbe:
        value = namespace.get(name, vars(builtins).get(name))
        if name in {"enumerate", "zip", "map", "list", "tuple", "str"}:
            if type(value) is not type or vars(builtins).get(name) is not value:
                msg = f"closed compiler data type binding is not native: {name}"
                raise ValueError(msg)
            storage = vars(type)["__dict__"].__get__(value, type(value))
            constructor = storage.get("__new__")
            if (
                vars(type)["__name__"].__get__(value, type(value)) != name
                or vars(type)["__module__"].__get__(value, type(value)) != "builtins"
                or type(constructor) is not BuiltinFunctionType
                or constructor.__self__ is not value
                or constructor.__name__ != "__new__"
            ):
                msg = f"closed compiler data constructor is interposed: {name}"
                raise ValueError(msg)
            return value
        if (
            type(value) is not BuiltinFunctionType
            or vars(builtins).get(name) is not value
            or value.__self__ is not builtins
            or value.__module__ != "builtins"
            or value.__name__ != name
        ):
            msg = f"closed compiler builtin binding is not native: {name}"
            raise ValueError(msg)
        return value

    def _global(
        self,
        name: str,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if name not in namespace:
            if name in {"hasattr", "getattr", "exec", "isinstance"}:
                return self._builtin(name, namespace)
            if name == "bool" and vars(builtins).get(name) is bool:
                return bool
            if name in {"str", "list", "tuple", "map"}:
                return self._builtin(name, namespace)
            msg = f"closed compiler global is not declared: {name}"
            raise ValueError(msg)
        value = namespace[name]
        bindings = [
            (statement, alias)
            for statement in tree.body
            if isinstance(statement, ast.Import | ast.ImportFrom)
            for alias in statement.names
            if (alias.asname or alias.name.split(".")[0]) == name
        ]
        if len(bindings) != 1:
            assignments = [
                statement.value for statement in tree.body
                if isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == name
            ]
            if len(assignments) == 1 and isinstance(assignments[0], ast.Call):
                if type(value) is object:
                    return self._default(ast.Name(id=name), namespace, tree)
                native = type(value)
                storage = vars(type)["__dict__"].__get__(native, type(native))
                operation = storage.get("findall")
                if (
                    type(operation) is MethodDescriptorType
                    and operation.__objclass__ is native
                ):
                    self._regex(name, value, namespace, tree)
                    return value
            msg = f"closed compiler global has no unique source import: {name}"
            raise ValueError(msg)
        statement, alias = bindings[0]
        if isinstance(statement, ast.Import):
            expected = self._module(alias.name if alias.asname else alias.name.split(".")[0])
        else:
            if statement.level or statement.module is None:
                msg = "closed compiler import requires an absolute physical supplier"
                raise ValueError(msg)
            provider = self._module(statement.module)
            self._source(provider)
            expected = vars(provider).get(alias.name)
        if value is not expected:
            msg = f"closed compiler import differs from its registered supplier: {name}"
            raise ValueError(msg)
        if type(value) is ModuleType:
            if value is sys:
                self._intern()
            else:
                self._source(value)
        return value

    def _intern(self) -> BuiltinFunctionType:
        """Authenticate the selected native string intrinsic and its interpreter."""
        path = FlextInfraWorkspaceEnvironmentProvenance._module_source("sys").unwrap()
        operation = vars(sys).get("intern")
        if (
            self._module("sys") is not sys
            or path != Path(sys.executable).resolve()
            or type(operation) is not BuiltinFunctionType
            or operation.__self__ is not sys
            or operation.__module__ != "sys"
            or operation.__name__ != "intern"
        ):
            msg = "closed compiler string interning intrinsic is interposed"
            raise ValueError(msg)
        if path not in self._inputs:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            if state.content is None:
                msg = f"closed compiler interpreter is absent: {path}"
                raise ValueError(msg)
            self._inputs[path] = state
        return operation

    def _mapped_strings(
        self,
        node: ast.Call,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> t.VariadicTuple[str]:
        """Derive exact string map data without calling the selected callback."""
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id != "map"
            or node.func.id in local
            or node.keywords
            or len(node.args) != 2
        ):
            msg = "closed compiler string map has unsupported construction"
            raise ValueError(msg)
        self._builtin("map", namespace)
        operation = self._expression(node.args[0], local, namespace, tree)
        if operation is not self._builtin("str", namespace) and operation is not self._intern():
            msg = "closed compiler map callback is outside native string data"
            raise ValueError(msg)
        values = self._expression(node.args[1], local, namespace, tree)
        if (
            not (type(values) is str or type(values) is tuple or type(values) is list)
            or any(type(value) is not str for value in values)
        ):
            msg = "closed compiler map contains authored conversion operands"
            raise ValueError(msg)
        return tuple(values)

    @staticmethod
    def _boolean(value: p.AttributeProbe) -> bool:
        if type(value) is bool:
            return value
        if value is None:
            return False
        if type(value) is int:
            return value != 0
        if (
            type(value) is str
            or type(value) is tuple
            or type(value) is list
            or type(value) is dict
        ):
            return len(value) != 0
        msg = "closed compiler condition has authored truth-value semantics"
        raise ValueError(msg)

    def _member(
        self, module: p.AttributeProbe, name: p.AttributeProbe,
    ) -> t.Pair[bool, p.AttributeProbe | None]:
        if type(module) is not ModuleType or type(name) is not str:
            msg = "closed compiler member lookup is not native module/string data"
            raise ValueError(msg)
        self._source(module)
        namespace = vars(module)
        if name in namespace:
            return True, namespace[name]
        if "__getattr__" in namespace:
            self._absent_member(module, name)
        return False, None

    def _absent_member(self, module: ModuleType, member: str) -> None:
        """Prove a literal hook path ends at native AttributeError without running it."""
        function = vars(module)["__getattr__"]
        declaration, tree, namespace = self._function(function)
        arguments = (*declaration.args.posonlyargs, *declaration.args.args)
        if (
            len(arguments) != 1
            or declaration.args.kwonlyargs
            or declaration.args.vararg is not None
            or declaration.args.kwarg is not None
            or declaration.args.defaults
        ):
            msg = "closed compiler module hook has unsupported argument storage"
            raise ValueError(msg)
        argument = arguments[0].arg
        local = {argument: member}
        statements = list(declaration.body)
        while statements:
            statement = statements.pop(0)
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and type(statement.value.value) is str
            ):
                continue
            if isinstance(statement, ast.If):
                test = statement.test
                if (
                    not isinstance(test, ast.Compare)
                    or len(test.ops) != 1
                    or len(test.comparators) != 1
                    or not isinstance(test.left, ast.Name)
                    or test.left.id != argument
                ):
                    msg = "closed compiler hook condition is not a literal member test"
                    raise ValueError(msg)
                operand = test.comparators[0]
                if isinstance(test.ops[0], ast.In) and isinstance(operand, ast.Set):
                    if any(
                        not isinstance(item, ast.Constant) or type(item.value) is not str
                        for item in operand.elts
                    ):
                        msg = "closed compiler hook membership has nonliteral operands"
                        raise ValueError(msg)
                    condition = any(member == item.value for item in operand.elts)
                elif (
                    isinstance(test.ops[0], ast.Eq)
                    and isinstance(operand, ast.Constant)
                    and type(operand.value) is str
                ):
                    condition = member == operand.value
                else:
                    msg = "closed compiler hook condition has unsupported semantics"
                    raise ValueError(msg)
                statements[:0] = statement.body if condition else statement.orelse
                continue
            if isinstance(statement, ast.Raise):
                raised = statement.exc
                if (
                    statement.cause is not None
                    or not isinstance(raised, ast.Call)
                    or not isinstance(raised.func, ast.Name)
                    or raised.func.id != "AttributeError"
                    or raised.keywords
                    or len(raised.args) != 1
                ):
                    msg = "closed compiler hook does not raise native AttributeError"
                    raise ValueError(msg)
                error = namespace.get("AttributeError", vars(builtins).get("AttributeError"))
                if type(error) is not type or error is not vars(builtins).get("AttributeError"):
                    msg = "closed compiler hook exception binding is not native"
                    raise ValueError(msg)
                storage = vars(type)["__dict__"].__get__(error, type(error))
                initializer = storage.get("__init__")
                if (
                    vars(type)["__name__"].__get__(error, type(error)) != "AttributeError"
                    or vars(type)["__module__"].__get__(error, type(error)) != "builtins"
                    or not (
                        type(initializer) is WrapperDescriptorType
                        or type(initializer) is MethodDescriptorType
                    )
                    or initializer.__objclass__ is not error
                ):
                    msg = "closed compiler hook exception constructor is interposed"
                    raise ValueError(msg)
                message = raised.args[0]
                if isinstance(message, ast.Constant) and type(message.value) is str:
                    return
                if not isinstance(message, ast.JoinedStr):
                    msg = "closed compiler hook exception message is not literal text"
                    raise ValueError(msg)
                for part in message.values:
                    if isinstance(part, ast.Constant) and type(part.value) is str:
                        continue
                    if (
                        not isinstance(part, ast.FormattedValue)
                        or not isinstance(part.value, ast.Name)
                        or part.format_spec is not None
                        or part.conversion not in (-1, ord("r"))
                    ):
                        msg = "closed compiler hook exception message invokes formatting"
                        raise ValueError(msg)
                    name = part.value.id
                    if name == argument:
                        value = local[name]
                    elif name == "__name__":
                        value = namespace.get(name)
                    else:
                        msg = "closed compiler hook exception message has an opaque binding"
                        raise ValueError(msg)
                    if type(value) is not str:
                        msg = "closed compiler hook exception message has an authored operand"
                        raise ValueError(msg)
                return
            msg = (
                "closed compiler selected module-hook statement is unsupported: "
                f"{type(statement).__name__}"
            )
            raise ValueError(msg)
        msg = "closed compiler module hook has no proved missing-member outcome"
        raise ValueError(msg)

    def _expression(
        self,
        node: ast.expr,
        local: t.MappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe:
        if isinstance(node, ast.Constant) and (
            type(node.value) is str
            or type(node.value) is int
            or type(node.value) is bool
            or node.value is None
        ):
            return node.value
        if isinstance(node, ast.Name):
            return local[node.id] if node.id in local else self._global(node.id, namespace, tree)
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "tuple"
            and node.attr == "__new__"
            and self._global("tuple", namespace, tree) is tuple
        ):
            return vars(tuple)["__new__"]
        if isinstance(node, ast.Attribute) and node.attr == "intern":
            receiver = self._expression(node.value, local, namespace, tree)
            if receiver is sys:
                return self._intern()
        if isinstance(node, ast.Dict):
            result = {}
            for key, value in zip(node.keys, node.values, strict=True):
                if key is None:
                    msg = "closed compiler dictionary unpacking is unsupported"
                    raise ValueError(msg)
                scalar = self._expression(key, local, namespace, tree)
                if type(scalar) is not str:
                    msg = "closed compiler dictionary keys must be exact strings"
                    raise ValueError(msg)
                result[scalar] = self._expression(value, local, namespace, tree)
            self._dictionaries.add(id(result))
            return result
        if isinstance(node, ast.Tuple):
            return tuple(self._expression(item, local, namespace, tree) for item in node.elts)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not self._boolean(self._expression(node.operand, local, namespace, tree))
        if isinstance(node, ast.BoolOp):
            for item in node.values:
                value = self._expression(item, local, namespace, tree)
                if isinstance(node.op, ast.And) and not self._boolean(value):
                    return value
                if isinstance(node.op, ast.Or) and self._boolean(value):
                    return value
            return value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._expression(node.left, local, namespace, tree)
            right = self._expression(node.right, local, namespace, tree)
            if type(left) is str and type(right) is str:
                return left + right
            if type(left) is int and type(right) is int:
                return left + right
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left = self._expression(node.left, local, namespace, tree)
            right = self._expression(node.comparators[0], local, namespace, tree)
            if isinstance(node.ops[0], ast.Is):
                return left is right
            if isinstance(node.ops[0], ast.IsNot):
                return left is not right
            if (
                type(left) is type(right)
                and (type(left) is str or type(left) is int or type(left) is bool)
            ):
                if isinstance(node.ops[0], ast.Eq):
                    return left == right
                if isinstance(node.ops[0], ast.NotEq):
                    return left != right
        if isinstance(node, ast.JoinedStr):
            parts = []
            for part in node.values:
                if isinstance(part, ast.Constant) and type(part.value) is str:
                    parts.append(part.value)
                elif isinstance(part, ast.FormattedValue) and part.conversion == -1 and part.format_spec is None:
                    value = self._expression(part.value, local, namespace, tree)
                    if type(value) is not str:
                        msg = "closed compiler interpolation is not exact string data"
                        raise ValueError(msg)
                    parts.append(value)
                else:
                    msg = "closed compiler interpolation has executable formatting"
                    raise ValueError(msg)
            return "".join(parts)
        if isinstance(node, ast.Subscript):
            mapping = self._expression(node.value, local, namespace, tree)
            if isinstance(node.slice, ast.Slice):
                bounds = tuple(
                    None if item is None else self._expression(item, local, namespace, tree)
                    for item in (node.slice.lower, node.slice.upper, node.slice.step)
                )
                if (
                    (type(mapping) is str or type(mapping) is tuple or type(mapping) is list)
                    and all(item is None or type(item) is int for item in bounds)
                ):
                    return mapping[slice(*bounds)]
                msg = "closed compiler slice has authored operands"
                raise ValueError(msg)
            key = self._expression(node.slice, local, namespace, tree)
            if type(mapping) is dict and type(key) is str:
                return mapping[key]
            if type(key) is int and (
                type(mapping) is str or type(mapping) is tuple or type(mapping) is list
            ):
                return mapping[key]
        if isinstance(node, ast.Call) and not node.keywords:
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "isinstance"
                and node.func.id not in local
                and len(node.args) == 2
            ):
                self._builtin("isinstance", namespace)
                value, expected = (
                    self._expression(item, local, namespace, tree)
                    for item in node.args
                )
                if (
                    expected is self._builtin("str", namespace)
                    and (
                        type(value) is str
                        or type(value) is tuple
                        or type(value) is list
                    )
                ):
                    return type(value) is str
                msg = "closed compiler instance predicate has authored operands"
                raise ValueError(msg)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in {"str", "list", "tuple"}
                and node.func.id not in local
                and len(node.args) == 1
            ):
                self._builtin(node.func.id, namespace)
                argument = node.args[0]
                if (
                    isinstance(argument, ast.Call)
                    and isinstance(argument.func, ast.Name)
                    and argument.func.id == "map"
                    and node.func.id in {"list", "tuple"}
                ):
                    values = self._mapped_strings(argument, local, namespace, tree)
                    return list(values) if node.func.id == "list" else values
                value = self._expression(argument, local, namespace, tree)
                if node.func.id == "str" and type(value) is str:
                    return value
                if type(value) is str or type(value) is tuple or type(value) is list:
                    if node.func.id == "list":
                        return list(value)
                    if node.func.id == "tuple":
                        return tuple(value)
                msg = "closed compiler construction has authored data operands"
                raise ValueError(msg)
            if isinstance(node.func, ast.Name) and node.func.id in {"hasattr", "getattr"}:
                if node.func.id in local:
                    msg = "closed compiler shadows its native lookup"
                    raise ValueError(msg)
                self._builtin(node.func.id, namespace)
                if len(node.args) != 2:
                    msg = "closed compiler member lookup has unsupported arity"
                    raise ValueError(msg)
                present, value = self._member(*(
                    self._expression(item, local, namespace, tree) for item in node.args
                ))
                if node.func.id == "hasattr":
                    return present
                if present:
                    return value
                msg = "closed compiler requires an absent module member"
                raise ValueError(msg)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in {"zip", "enumerate", "len"}
                and node.func.id not in local
            ):
                self._builtin(node.func.id, namespace)
                arguments = tuple(
                    self._expression(item, local, namespace, tree) for item in node.args
                )
                if not all(
                    type(item) is tuple or type(item) is list or type(item) is str
                    for item in arguments
                ):
                    msg = "closed compiler iteration has authored operands"
                    raise ValueError(msg)
                if node.func.id == "zip":
                    return tuple(zip(*arguments))
                if len(arguments) != 1:
                    msg = "closed compiler iteration has unsupported arity"
                    raise ValueError(msg)
                if node.func.id == "enumerate":
                    return tuple(enumerate(arguments[0]))
                return len(arguments[0])
            if isinstance(node.func, ast.Attribute):
                receiver = self._expression(node.func.value, local, namespace, tree)
                arguments = tuple(
                    self._expression(item, local, namespace, tree) for item in node.args
                )
                if type(receiver) is str:
                    if node.func.attr == "replace" and len(arguments) == 2 and all(type(item) is str for item in arguments):
                        return str.replace(receiver, arguments[0], arguments[1])
                    if node.func.attr == "split" and not arguments:
                        return str.split(receiver)
                    if node.func.attr == "startswith" and len(arguments) == 1 and type(arguments[0]) is str:
                        return str.startswith(receiver, arguments[0])
                    if node.func.attr == "join" and len(arguments) == 1 and (
                        type(arguments[0]) is tuple or type(arguments[0]) is list
                    ) and all(type(item) is str for item in arguments[0]):
                        return str.join(receiver, arguments[0])
                if id(receiver) in self._patterns:
                    if node.func.attr == "sub" and len(arguments) == 2 and all(type(item) is str for item in arguments):
                        pattern = self._patterns[id(receiver)]
                        if pattern == "^[ \t]+$" and arguments[0] == "":
                            return "\n".join(
                                ""
                                if line and all(character in " \t" for character in line)
                                else line
                                for line in arguments[1].split("\n")
                            )
                    if node.func.attr == "findall" and len(arguments) == 1 and type(arguments[0]) is str:
                        pattern = self._patterns[id(receiver)]
                        if pattern == "(^[ \t]*)(?:[^ \t\n])":
                            return [
                                line[:len(line) - len(line.lstrip(" \t"))]
                                for line in arguments[0].split("\n")
                                if line and any(character not in " \t" for character in line)
                            ]
                    msg = "closed compiler regex operation is outside its physical data grammar"
                    raise ValueError(msg)
                if type(receiver) is ModuleType and node.func.attr == "sub":
                    return self._prefix_sub(receiver, arguments)
                if receiver is sys and node.func.attr == "intern":
                    self._intern()
                    if len(arguments) == 1 and type(arguments[0]) is str:
                        return arguments[0]
                    msg = "closed compiler interning has authored data operands"
                    raise ValueError(msg)
                msg = "closed compiler method is outside native string/regex data"
                raise ValueError(msg)
            function = self._expression(node.func, local, namespace, tree)
            if type(function) is FunctionType and len(node.args) == 1:
                text = self._expression(node.args[0], local, namespace, tree)
                if type(text) is str:
                    return self._dedent(function, text)
        msg = f"closed compiler expression is unsupported: {type(node).__name__}"
        raise ValueError(msg)

    def _statements(
        self,
        statements: list[ast.stmt],
        local: t.MutableMappingKV[str, p.AttributeProbe],
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> p.AttributeProbe | None:
        for statement in statements:
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and type(statement.value.value) is str:
                continue
            if isinstance(statement, ast.Assign | ast.AnnAssign):
                if statement.value is None:
                    msg = "closed compiler assignment has no value"
                    raise ValueError(msg)
                value = self._expression(statement.value, local, namespace, tree)
                targets = statement.targets if isinstance(statement, ast.Assign) else (statement.target,)
                for target in targets:
                    if isinstance(target, ast.Name):
                        local[target.id] = value
                    elif isinstance(target, ast.Subscript):
                        mapping = self._expression(target.value, local, namespace, tree)
                        key = self._expression(target.slice, local, namespace, tree)
                        if (
                            type(mapping) is not dict
                            or id(mapping) not in self._dictionaries
                            or type(key) is not str
                        ):
                            msg = "closed compiler assignment has foreign native storage"
                            raise ValueError(msg)
                        mapping[key] = value
                    else:
                        msg = "closed compiler assignment target is unsupported"
                        raise ValueError(msg)
                continue
            if (
                isinstance(statement, ast.AugAssign)
                and isinstance(statement.target, ast.Name)
                and isinstance(statement.op, ast.Add)
            ):
                current = local[statement.target.id]
                added = self._expression(statement.value, local, namespace, tree)
                if type(current) is not str or type(added) is not str:
                    msg = "closed compiler augmentation has authored operands"
                    raise ValueError(msg)
                local[statement.target.id] = current + added
                continue
            if isinstance(statement, ast.For) and not statement.orelse:
                items = self._expression(statement.iter, local, namespace, tree)
                if type(items) is not tuple and type(items) is not list and type(items) is not str:
                    msg = "closed compiler loop has an authored iterator"
                    raise ValueError(msg)
                for item in items:
                    self._assign(statement.target, item, local)
                    returned = self._statements(statement.body, local, namespace, tree)
                    if type(returned) is ast.Break:
                        break
                    if returned is not None:
                        return returned
                continue
            if isinstance(statement, ast.Pass):
                continue
            if isinstance(statement, ast.Break):
                return statement
            if isinstance(statement, ast.If):
                condition = self._boolean(self._expression(statement.test, local, namespace, tree))
                returned = self._statements(
                    statement.body if condition else statement.orelse,
                    local, namespace, tree,
                )
                if returned is not None:
                    return returned
                continue
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                call = statement.value
                if not isinstance(call.func, ast.Name) or call.func.id != "exec" or call.keywords or len(call.args) != 3:
                    msg = "closed compiler effect is not a native compilation"
                    raise ValueError(msg)
                self._builtin("exec", namespace)
                text, globals_, locals_ = (
                    self._expression(item, local, namespace, tree) for item in call.args
                )
                if (
                    type(text) is not str
                    or type(globals_) is not dict
                    or type(locals_) is not dict
                    or id(globals_) not in self._dictionaries
                    or id(locals_) not in self._dictionaries
                    or globals_ is locals_
                ):
                    msg = "closed compiler requires fresh exact native dictionaries"
                    raise ValueError(msg)
                proof = self._emission(text, globals_)
                self._emitted[id(proof.code)] = proof
                locals_[proof.code.co_qualname] = proof.code
                continue
            if isinstance(statement, ast.Return) and statement.value is not None:
                return self._expression(statement.value, local, namespace, tree)
            msg = f"closed compiler statement is unsupported: {type(statement).__name__}"
            raise ValueError(msg)
        return None

    def _assign(
        self,
        target: ast.expr,
        value: p.AttributeProbe,
        local: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> None:
        if isinstance(target, ast.Name):
            local[target.id] = value
            return
        if isinstance(target, ast.Tuple) and type(value) is tuple and len(target.elts) == len(value):
            for child, item in zip(target.elts, value, strict=True):
                self._assign(child, item, local)
            return
        msg = "closed compiler loop target is not native fixed tuple storage"
        raise ValueError(msg)

    def _emission(
        self, text: str, globals_: t.MutableMappingKV[str, p.AttributeProbe],
    ) -> m.Infra.NativeGeneratedFunctionProof:
        parsed = ast.parse(text)
        if len(parsed.body) != 1 or not isinstance(parsed.body[0], ast.FunctionDef):
            msg = "closed compiler output is not one function declaration"
            raise ValueError(msg)
        function = parsed.body[0]
        arguments = (*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs)
        if (
            function.decorator_list
            or function.type_params
            or function.args.defaults
            or function.args.kw_defaults
            or function.args.vararg is not None
            or function.args.kwarg is not None
            or "__builtins__" in globals_
        ):
            msg = "closed compiler output has unsupported construction inputs"
            raise ValueError(msg)
        globals_["__builtins__"] = vars(builtins)
        annotations = {}
        for name, annotation in (
            *((argument.arg, argument.annotation) for argument in arguments),
            ("return", function.returns),
        ):
            if annotation is None:
                continue
            if isinstance(annotation, ast.Constant) and type(annotation.value) is str:
                annotations[name] = annotation.value
            elif isinstance(annotation, ast.Name):
                if annotation.id in globals_:
                    annotations[name] = globals_[annotation.id]
                elif annotation.id == "bool" and vars(builtins).get("bool") is bool:
                    annotations[name] = bool
                else:
                    msg = "closed compiler annotation binding is not declared"
                    raise ValueError(msg)
            else:
                msg = "closed compiler annotation would execute an expression"
                raise ValueError(msg)
        root = builtins.compile(
            text, "<string>", "exec", dont_inherit=True, optimize=sys.flags.optimize,
        )
        codes = tuple(item for item in root.co_consts if type(item) is CodeType)
        if len(codes) != 1 or codes[0].co_freevars or codes[0].co_cellvars:
            msg = "closed compiler output has executable nested construction"
            raise ValueError(msg)
        return m.Infra.NativeGeneratedFunctionProof(
            code=codes[0],
            globals=dict(globals_),
            annotations=annotations,
            defaults=None,
            keyword_defaults=None,
            closure=(),
            inputs=(),
        )

    def _dedent(self, function: FunctionType, text: str) -> str:
        """Interpret the physical transform body without invoking Python helpers."""
        declaration, tree, namespace = self._function(function)
        module = self._module(function.__module__)
        if (
            function.__module__ not in sys.stdlib_module_names
            or function.__name__ != "dedent"
            or vars(module).get("dedent") is not function
            or len(declaration.args.args) != 1
            or declaration.args.posonlyargs
            or declaration.args.kwonlyargs
            or declaration.args.vararg is not None
            or declaration.args.kwarg is not None
        ):
            msg = "closed compiler string transform is not the physical stdlib dedent"
            raise ValueError(msg)
        for call in (node for node in ast.walk(declaration) if isinstance(node, ast.Call)):
            if isinstance(call.func, ast.Name) and call.func.id in {"zip", "enumerate"}:
                self._builtin(call.func.id, namespace)
            if not isinstance(call.func, ast.Attribute) or not isinstance(call.func.value, ast.Name):
                continue
            name = call.func.value.id
            if name not in namespace:
                continue
            target = namespace[name]
            if type(target) is ModuleType:
                self._global(name, namespace, tree)
                operation = vars(target).get(call.func.attr)
                if type(operation) is not FunctionType:
                    msg = "dedent module callback is not a physical function"
                    raise ValueError(msg)
                self._function(operation)
            elif call.func.attr in {"sub", "findall"}:
                self._regex(name, target, namespace, tree)
        returned = self._statements(
            declaration.body, {declaration.args.args[0].arg: text}, namespace, tree,
        )
        if type(returned) is not str:
            msg = "closed compiler string transform did not return exact text"
            raise ValueError(msg)
        return returned

    def _prefix_sub(
        self, module: ModuleType, arguments: tuple[p.AttributeProbe, ...],
    ) -> str:
        """Admit only the native regex operation's literal multiline prefix form."""
        if len(arguments) != 3 or not all(type(item) is str for item in arguments):
            msg = "closed compiler regex substitution requires exact string data"
            raise ValueError(msg)
        pattern, replacement, text = arguments
        function = vars(module).get("sub")
        declaration, tree, namespace = self._function(function)
        body = [
            statement for statement in declaration.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and type(statement.value.value) is str
            )
        ]
        # The wrapper's only preceding branch handles positional extras, which
        # this exact three-argument call does not supply.
        if (
            len(body) != 2
            or not isinstance(body[0], ast.If)
            or not isinstance(body[0].test, ast.Name)
            or declaration.args.vararg is None
            or body[0].test.id != declaration.args.vararg.arg
            or body[0].orelse
            or not isinstance(body[1], ast.Return)
            or not isinstance(body[1].value, ast.Call)
            or body[1].value.keywords
        ):
            msg = "closed compiler regex wrapper has unsupported source semantics"
            raise ValueError(msg)
        result = body[1].value
        if (
            not isinstance(result.func, ast.Attribute)
            or result.func.attr != "sub"
            or not isinstance(result.func.value, ast.Call)
            or not isinstance(result.func.value.func, ast.Name)
            or result.func.value.keywords
            or len(result.func.value.args) != 2
            or len(result.args) != 3
            or len(declaration.args.args) != 3
            or len(declaration.args.kwonlyargs) != 2
        ):
            msg = "closed compiler regex wrapper is not its native delegation"
            raise ValueError(msg)
        names = tuple(argument.arg for argument in declaration.args.args)
        keywords = tuple(argument.arg for argument in declaration.args.kwonlyargs)
        actual = (
            *result.func.value.args,
            *result.args,
        )
        expected = (names[0], keywords[1], names[1], names[2], keywords[0])
        if any(
            not isinstance(node, ast.Name) or node.id != name
            for node, name in zip(actual, expected, strict=True)
        ):
            msg = "closed compiler regex delegation operands differ from source"
            raise ValueError(msg)
        compiler = namespace.get(result.func.value.func.id)
        self._function(compiler)
        if (
            replacement
            or not pattern.startswith("(?m)^")
            or any(character not in " \t" for character in pattern[5:])
        ):
            msg = "closed compiler regex pattern is outside literal prefix grammar"
            raise ValueError(msg)
        prefix = pattern[5:]
        return "\n".join(
            line[len(prefix):] if line.startswith(prefix) else line
            for line in text.split("\n")
        )

    def _regex(
        self,
        name: str,
        pattern: p.AttributeProbe,
        namespace: t.MappingKV[str, p.AttributeProbe],
        tree: ast.Module,
    ) -> None:
        assignments = [
            statement.value for statement in tree.body
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == name
        ]
        if (
            len(assignments) != 1
            or not isinstance(assignments[0], ast.Call)
            or not isinstance(assignments[0].func, ast.Attribute)
            or not isinstance(assignments[0].func.value, ast.Name)
            or assignments[0].func.attr != "compile"
            or assignments[0].keywords
            or len(assignments[0].args) != 2
            or not isinstance(assignments[0].args[0], ast.Constant)
            or type(assignments[0].args[0].value) is not str
            or not isinstance(assignments[0].args[1], ast.Attribute)
            or not isinstance(assignments[0].args[1].value, ast.Name)
            or assignments[0].args[1].value.id != assignments[0].func.value.id
        ):
            msg = "dedent regex has no closed physical constructor"
            raise ValueError(msg)
        constructor = assignments[0]
        supplier = self._global(constructor.func.value.id, namespace, tree)
        if type(supplier) is not ModuleType or vars(supplier).get("Pattern") is not type(pattern):
            msg = "dedent regex is not its registered native pattern type"
            raise ValueError(msg)
        self._function(vars(supplier)["compile"])
        native = type(pattern)
        storage = vars(type)["__dict__"].__get__(native, type(native))
        for operation in ("sub", "findall"):
            descriptor = storage.get(operation)
            if (
                type(descriptor) is not MethodDescriptorType
                or descriptor.__objclass__ is not native
            ):
                msg = "dedent pattern has no interpreter-owned regex operations"
                raise ValueError(msg)
        observed = {}
        for attribute in ("pattern", "flags"):
            descriptor = storage.get(attribute)
            if (
                not (
                    type(descriptor) is MemberDescriptorType
                    or type(descriptor) is GetSetDescriptorType
                )
                or descriptor.__objclass__ is not type(pattern)
            ):
                msg = "dedent regex has no native read-only state"
                raise ValueError(msg)
            observed[attribute] = descriptor.__get__(pattern, type(pattern))
        flag = vars(supplier).get(constructor.args[1].attr)
        unicode = vars(supplier).get("UNICODE")
        if any(
            not any(
                owner is int
                for owner in vars(type)["__mro__"].__get__(
                    type(operand), type(type(operand)),
                )
            )
            for operand in (flag, unicode)
        ):
            msg = "dedent regex flags are not native integers"
            raise ValueError(msg)
        if (
            type(observed["pattern"]) is not str
            or type(observed["flags"]) is not int
            or observed["pattern"] != constructor.args[0].value
            or observed["flags"] != (int.__index__(flag) | int.__index__(unicode))
        ):
            msg = "dedent regex state differs from its physical constructor"
            raise ValueError(msg)
        self._patterns[id(pattern)] = constructor.args[0].value


__all__: t.VariadicTuple[str] = ("FlextInfraWorkspaceGeneratedFunction",)
