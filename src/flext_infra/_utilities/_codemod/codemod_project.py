"""Project-scope analyses the codemod engine and its rule producers read.

ast-grep matches one file's syntax. Some laws are verdicts over the whole
project: whether a module takes part in an import cycle, whether a facade's
namespace composes every class its family package declares. These analyses
build those facts from the tree as it is; the generated rule producers turn
them into native utilities and file scopes, so ast-grep alone decides every
finding.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import MutableMapping
from pathlib import Path

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod.codemod_binding_chain import (
    FlextInfraUtilitiesCodemodBindingChain,
)
from flext_infra._utilities._codemod.codemod_native_cascade import (
    FlextInfraUtilitiesCodemodNativeCascade,
)
from flext_infra._utilities._codemod.codemod_native_package_utilities import (
    FlextInfraUtilitiesCodemodNativePackageUtilities,
)
from flext_infra._utilities._codemod.codemod_native_utilities import (
    FlextInfraUtilitiesCodemodNativeUtilities,
)
from flext_infra._utilities._rope._analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesRopeRuntimeTypes,
)


class FlextInfraUtilitiesCodemodProject(
    FlextInfraUtilitiesCodemodBindingChain.FlextInfraUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesCodemodNativeUtilities,
    FlextInfraUtilitiesCodemodNativePackageUtilities,
    FlextInfraUtilitiesCodemodNativeCascade,
    FlextInfraUtilitiesImportLaw,
):
    """Analyze project facts the codemod engine reads: packages, layers, graphs."""

    @classmethod
    def project_import_graph(
        cls,
        root: Path,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Return the runtime import graph and the module name of each file.

        Edges come from Rope's module-level import table, which leaves
        ``if TYPE_CHECKING:`` imports and function-local imports out: only
        imports that run when the module loads can form a cycle. Each target
        is truncated to the longest module the project defines.

        Live nodes use the workspace indexer's governed inventory, not Rope's
        recursive checkout enumeration. Declared members retain their import
        roots; unrelated checkouts and managed projections are not graph nodes.

        Returns:
            The runtime import graph and the module name of each file.

        """
        resolved = root.resolve()
        with FlextInfraUtilitiesWorkspaceSnapshot.workspace_snapshot(
            resolved,
            FlextInfraUtilitiesProjectDiscovery.governed_project_roots(resolved),
        ) as snapshot:
            project = snapshot.engine
            resources = tuple(
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    project.get_resource(path.relative_to(resolved).as_posix()),
                    path,
                )
                for member in snapshot.members
                for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
                    snapshot, member
                )
                if path.suffix == c.Infra.EXT_PYTHON
            )
            return cls.snapshot_import_graph(project, resources=resources)

    @classmethod
    def composes_family_package(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        facade_file: Path,
        namespace: str,
    ) -> bool:
        """Return whether ``namespace`` in a facade module composes its family.

        The family package of ``<pkg>/<stem>.py`` is ``<pkg>/_<stem>/``. Every
        class a module of that package declares in its ``__all__`` must be
        reachable through the bases of the facade's ``namespace`` class,
        following the bases each package class declares. A facade without a
        family package composes nothing and holds.

        Returns:
            Whether ``namespace`` in a facade module composes its family.

        """
        package = facade_file.parent / f"_{facade_file.stem}"
        if not package.is_dir():
            return True
        bases_by_class: MutableMapping[str, t.StrSequence] = {}
        exported: set[str] = set()
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        for module in sorted(package.rglob(f"*{c.Infra.EXT_PYTHON}")):
            if module.name == c.Infra.INIT_PY:
                continue
            declared = frozenset(snapshots.workspace_public_exports(snapshot, module))
            for (
                info
            ) in FlextInfraUtilitiesRopeAnalysisAstHelpers.class_info_from_module(
                snapshots.workspace_module_tree(snapshot, module),
            ):
                bases_by_class[info.name] = tuple(info.bases)
                if info.name in declared:
                    exported.add(info.name)
        pending = list(
            cls._nested_class_bases(
                snapshots.workspace_module_tree(snapshot, facade_file),
                namespace,
                facade_file,
            )
        )
        reached: set[str] = set()
        while pending:
            name = pending.pop()
            if name in reached:
                continue
            reached.add(name)
            pending.extend(bases_by_class.get(name, ()))
        return exported <= reached

    @staticmethod
    def _nested_class_bases(
        tree: t.Infra.AstModule,
        namespace: str,
        facade_file: Path,
    ) -> t.StrSequence:
        """Return the base names of class ``namespace`` nested in the facade.

        Returns:
            The base names of class ``namespace`` nested in the facade.

        Raises:
            ValueError: If class.

        """
        for node in FlextInfraUtilitiesRopeAnalysisAstHelpers.walk_ast_nodes(tree):
            if (
                FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node) == "ClassDef"
                and getattr(node, "name", "") == namespace
            ):
                return tuple(
                    name
                    for base in getattr(node, "bases", ()) or ()
                    if (
                        name
                        := FlextInfraUtilitiesRopeAnalysisAstHelpers.class_base_name(
                            base,
                        )
                    )
                )
        msg = f"class {namespace} is not declared in {facade_file}"
        raise ValueError(msg)

    @staticmethod
    def codemod_source_path(root: Path, file_path: Path) -> Path:
        """Resolve one finding file path against its project root.

        Returns:
            The absolute source path of the finding.

        """
        candidate = file_path if file_path.is_absolute() else root / file_path
        return (
            candidate.parent.resolve() / candidate.name
            if candidate.suffix == ".pyi"
            else candidate.resolve()
        )

    @classmethod
    def codemod_path_findings(
        cls,
        root: Path,
        paths: t.SequenceOf[Path],
        rules: t.SequenceOf[m.Infra.CodemodRule],
    ) -> t.VariadicTuple[m.Infra.AstGrepOwnedPathDiagnostic]:
        """Admit owned-path policy from the shared inventory, without parsing bytes.

        Returns:
            Detection-only records for the same rule and authenticated report route.

        """
        return tuple(
            m.Infra.AstGrepOwnedPathDiagnostic.model_validate({
                "file": path.relative_to(root.resolve()).as_posix(),
                "ruleId": rule.id,
                "severity": "error",
                "message": rule.message,
                "origin": "owned-path",
                "text": "",
                "lines": "",
                "range": {
                    "start": {"line": 0, "column": 0},
                    "end": {"line": 0, "column": 0},
                    "byteOffset": {"start": 0, "end": 0},
                },
            })
            for path in paths
            for rule in rules
            if rule.owned_path_suffix is not None
            and path.suffix == rule.owned_path_suffix
        )

    @classmethod
    def codemod_ambient_environ_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the rule failing real process-environment reads of the project.

        A read is an ``os.environ`` subscript or ``.get`` call, or an
        ``os.getenv`` call, through any module-level ``os`` binding that is
        never rebound at module level. The project's layer-zero files (the
        import-law classifier over each module name) and the stdlib-only
        entrypoints of its native isolated executions are the typed boundary
        itself, so the rule ignores them by exact path.

        Returns:
            The single native rule document keyed by its rule id.

        """
        root = project.resolve()
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
        sources = FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
        )
        boundary = sorted({
            *cls.codemod_layer_zero_files(snapshot, root),
            *(
                path.relative_to(root).as_posix()
                for path in cls.codemod_isolated_entrypoints(root, sources)
            ),
        })
        rule_id = (
            f"{c.Infra.CODEMOD_AMBIENT_ENVIRON_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        module = "os-module"
        member: dict[str, t.JsonValue] = {
            name: {
                "any": [
                    {
                        "kind": "attribute",
                        "all": [
                            {"has": {"field": "object", "matches": module}},
                            {"has": {"field": "attribute", "regex": f"^{name}$"}},
                        ],
                    },
                    cls._os_member_binding(name),
                ]
            }
            for name in ("environ", "getenv")
        }
        document: t.JsonMapping = {
            "id": rule_id,
            "language": "python",
            "severity": "error",
            "files": ["**/*.py"],
            "utils": {module: cls._os_module_binding()},
            "rule": {
                "any": [
                    {"pattern": "$ENV[$KEY]"},
                    {"pattern": "$ENV.get($$$ARGS)"},
                    {"pattern": "$GETENV($$$ARGS)"},
                ]
            },
            "constraints": {"ENV": member["environ"], "GETENV": member["getenv"]},
            "message": (
                "Ambient os.environ/os.getenv read outside the typed settings "
                "boundary: read the value through config.<Ns>.* or "
                "settings.<Ns>.* (owned by settings.py / _settings/) instead of "
                "the raw process environment."
            ),
        }
        if boundary:
            document = {
                **document,
                "ignores": [f"**/{relative}" for relative in boundary],
            }
        return {rule_id: document}

    @staticmethod
    def _imported_name(name: str, variable: str) -> t.JsonDict:
        """Match an import name binding ``variable``: plain or aliased ``name``.

        Returns:
            The native rule of one imported-name child of an import statement.

        """
        plain: t.JsonDict = {
            "kind": "dotted_name",
            "pattern": f"${variable}",
            "regex": f"^{name}$",
            "not": {"inside": {"kind": "aliased_import"}},
        }
        aliased: t.JsonDict = {
            "kind": "aliased_import",
            "all": [
                {"has": {"field": "name", "regex": f"^{name}$"}},
                {"has": {"field": "alias", "pattern": f"${variable}"}},
            ],
        }
        return {"any": [{"has": plain}, {"has": aliased}]}

    @staticmethod
    def _module_level_binding(variable: str, statement: t.JsonDict) -> t.JsonDict:
        """Match an identifier a module-level ``statement`` binds, never rebound.

        Returns:
            The native rule of a stable module-level import binding.

        """
        rebinding: t.JsonDict = {
            "kind": "expression_statement",
            "has": {
                "kind": "assignment",
                "has": {"field": "left", "pattern": f"${variable}"},
            },
        }
        return {
            "all": [
                {"kind": "identifier"},
                {"pattern": f"${variable}"},
                {
                    "inside": {
                        "kind": "module",
                        "stopBy": "end",
                        "all": [{"has": statement}, {"not": {"has": rebinding}}],
                    }
                },
            ]
        }

    @classmethod
    def _os_module_binding(cls) -> t.JsonDict:
        """Match an identifier a module-level ``import os [as X]`` binds.

        Returns:
            The native utility rule of the ``os`` module binding.

        """
        return cls._module_level_binding(
            "OSMODULE",
            {"kind": "import_statement", **cls._imported_name("os", "OSMODULE")},
        )

    @classmethod
    def _os_member_binding(cls, name: str) -> t.JsonDict:
        """Match an identifier a module-level ``from os import <name>`` binds.

        Returns:
            The native rule of the imported ``os`` member binding.

        """
        return cls._module_level_binding(
            "OSMEMBER",
            {
                "kind": "import_from_statement",
                "all": [
                    {"has": {"field": "module_name", "regex": "^os$"}},
                    cls._imported_name(name, "OSMEMBER"),
                ],
            },
        )

    @classmethod
    def codemod_isolated_entrypoints(
        cls, root: Path, sources: t.SequenceOf[Path]
    ) -> frozenset[Path]:
        """Elect the stdlib-only entrypoints of the project's native executions.

        Each execution metadata construction carrying the complete declared
        fields names its entrypoint by native class identity; the entrypoint
        holds the isolated role only while its own imports are stdlib-only.

        Returns:
            The entrypoint sources that hold the isolated-execution role.

        """
        fields = set(m.Cli.PythonScriptExecution.model_fields)
        candidates: dict[Path, list[ast.Call]] = {}
        for path in sources:
            text = path.read_text(encoding=c.DEFAULT_ENCODING)
            if "__module__" not in text:
                continue
            calls = [
                node
                for node in ast.walk(ast.parse(text))
                if isinstance(node, ast.Call)
                and {keyword.arg for keyword in node.keywords} == fields
                and any(
                    keyword.arg == "module"
                    and isinstance(keyword.value, ast.Attribute)
                    and keyword.value.attr == "__module__"
                    for keyword in node.keywords
                )
            ]
            if calls:
                candidates[path] = calls
        if not candidates:
            return frozenset()
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        elected: set[Path] = set()
        with FlextInfraUtilitiesRopeCore.open_project(root) as project:
            for path, calls in candidates.items():
                resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    project.get_resource(path.relative_to(root).as_posix()), path
                )
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
                for node in calls:
                    scope = runtime.scope_at(
                        module, runtime.source_offset(module.source_code, node.func)
                    )
                    target = cls._execution_entrypoint(project, module, scope, node)
                    if target is not None and cls._isolated_imports_hold(
                        target.read_text(encoding=c.DEFAULT_ENCODING)
                    ):
                        elected.add(target.resolve())
        return frozenset(elected)

    @staticmethod
    def _isolated_imports_hold(source: str) -> bool:
        """Prove the selected entrypoint's imports require only the native stdlib.

        Returns:
            Whether every import satisfies the existing isolated-execution contract.

        """
        imports = ast.walk(ast.parse(source))
        return all(
            all(
                alias.name.partition(".")[0] in sys.stdlib_module_names
                for alias in node.names
            )
            if isinstance(node, ast.Import)
            else node.level == 0
            and (node.module or "").partition(".")[0] in sys.stdlib_module_names
            for node in imports
            if isinstance(node, c.Infra.AST_IMPORT_TYPES)
        )

    @classmethod
    def _execution_entrypoint(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        node: ast.Call,
    ) -> Path | None:
        """Resolve one native execution metadata constructor's entrypoint.

        Returns:
            Its source path, or None for an unrelated constructor.

        Raises:
            ValueError: If the metadata or its entrypoint identity is invalid.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        fields = {keyword.arg: keyword.value for keyword in node.keywords}
        if set(fields) != set(m.Cli.PythonScriptExecution.model_fields):
            return None
        position = runtime.source_offset(module.source_code, node.func)
        lexical = runtime.scope_at(module, position)
        if lexical is not scope:
            return None
        constructor = runtime.resolve_symbol(lexical, node.func)
        if constructor is None or not types.py_class(constructor.get_object()):
            return None
        contract = m.Cli.PythonScriptExecution
        expected = runtime.qualified_name(
            project, contract.__qualname__, module_name=contract.__module__
        )
        if not cls._binding_symbols_match(expected, constructor):
            return None
        entry, role = fields["module"], fields["role"]
        if not (
            isinstance(entry, ast.Attribute)
            and entry.attr == "__module__"
            and isinstance(role, ast.Constant)
            and isinstance(role.value, str)
        ):
            msg = (
                "execution metadata requires native entrypoint identity "
                "and its declared role"
            )
            raise ValueError(msg)
        binding = runtime.resolve_symbol(lexical, entry.value)
        if binding is None or not types.py_class(binding.get_object()):
            msg = "execution entrypoint is not a native class declaration"
            raise ValueError(msg)
        target = binding.get_object().get_module()
        if target is None or (target_resource := target.get_resource()) is None:
            msg = "execution entrypoint has no original source resource"
            raise ValueError(msg)
        _ = m.Cli.PythonScriptExecution.model_validate(
            {"module": target.get_name(), "role": role.value},
        )
        return Path(target_resource.real_path)

    @classmethod
    def implementation_owner_modules(
        cls,
        project: p.Infra.RopeProject,
        condition: p.Infra.PrimitiveOwnerCondition,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
    ) -> t.Infra.RopeImplementationPaths:
        """Derive a primitive's implementation from native definitions and MRO.

        Imported consumers do not enter this closure. Source-defined helper
        calls in the primitive's own namespace and actual declaring-class bases
        do; a same-spelled local symbol cannot substitute for a native owner.

        Returns:
            The declaring module paths of the implementation owner closure.

        Raises:
            ValueError: When the condition argument shape is wrong.

        """
        if len(condition.arg) != c.Infra.PRIMITIVE_OWNER_OPERAND_COUNT:
            msg = "implementation-owner requires a module and public primitive"
            raise ValueError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        module_name, expression = condition.arg
        primitive = runtime.qualified_name(
            project, expression, module_name=module_name
        ).get_object()
        if not types.py_function(primitive):
            msg = (
                "implementation owner is not a source callable: "
                f"{module_name}.{expression}"
            )
            raise ValueError(msg)
        declaration = primitive.get_module()
        namespace = declaration.get_name().partition(".")[0]
        owners: set[Path] = set()
        visited: set[int] = set()
        pending: list[p.Infra.RopePyObject] = [primitive]
        while pending:
            target = pending.pop()
            if id(target) in visited:
                continue
            visited.add(id(target))
            discovered = cls._implementation_target(target, namespace, sources)
            if discovered is None:
                continue
            path, related = discovered
            owners.add(path)
            pending.extend(related)
        return frozenset(owners)

    @staticmethod
    def _implementation_target(
        target: p.Infra.RopePyObject,
        namespace: str,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[Path, list[p.Infra.RopePyObject]] | None:
        """Collect native implementation edges of one callable or class.

        Returns:
            The source path and related native declarations, when source-defined.

        Raises:
            ValueError: If the declaration has no source resource.
            TypeError: If the module has no supported AST.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        pending: list[p.Infra.RopePyObject] = []
        if not (types.py_class(target) or types.py_function(target)):
            return None
        module = target.get_module()
        scope = target.get_scope()
        if not types.source_module(module):
            return None
        resource = module.get_resource()
        if resource is None:
            msg = "native implementation declaration has no source resource"
            raise ValueError(msg)
        path = Path(resource.real_path)
        if types.py_class(target):
            pending.extend(
                base for base in target.get_superclasses() if types.py_class(base)
            )
            pending.extend(
                child.pyobject
                for child in scope.get_scopes()
                if child.get_kind()
                in {c.Infra.RopeScopeKind.FUNCTION, c.Infra.RopeScopeKind.CLASS}
            )
            return path, pending
        parent = scope.parent
        if parent is not None and parent.get_kind() == c.Infra.RopeScopeKind.CLASS:
            pending.append(parent.pyobject)
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            msg = "native implementation module has no supported Python AST"
            raise TypeError(msg)
        pending.extend(
            FlextInfraUtilitiesCodemodProject._implementation_calls(
                module,
                scope,
                tree,
                sources[path] if path in sources else resource.read(),
                namespace,
            )
        )
        return path, pending

    @staticmethod
    def _implementation_calls(
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        tree: ast.AST,
        source: str,
        namespace: str,
    ) -> list[p.Infra.RopePyObject]:
        """Resolve same-namespace calls within one exact lexical scope.

        Returns:
            Native helper declarations reachable from calls in the scope.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        pending: list[p.Infra.RopePyObject] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not (
                scope.get_body_start() <= node.lineno <= scope.get_end()
            ):
                continue
            offset = runtime.source_offset(source, node.func)
            lexical = runtime.scope_at(module, offset)
            if lexical is not scope:
                continue
            binding = runtime.resolve_symbol(lexical, node.func)
            if binding is None:
                continue
            helper = binding.get_object()
            provider = helper.get_module()
            if (
                (types.py_function(helper) or types.py_class(helper))
                and provider is not None
                and provider.get_name().partition(".")[0] == namespace
            ):
                pending.append(helper)
        return pending

    @classmethod
    def parse_namespace_validation(
        cls,
        validation: p.Result[m.Infra.ValidationReport],
        root: Path,
    ) -> p.Result[t.VariadicTuple[m.Infra.CensusViolation]]:
        """Convert the engine-backed namespace report into census violations.

        A violation is fixable when its rule declares a token fix or a rope
        relocation in the project's rule plan.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CensusViolation]]``.

        Raises:
            ValueError: If namespace violation does not follow the report format.

        """
        if validation.failure:
            return r[t.VariadicTuple[m.Infra.CensusViolation]].from_failure(validation)
        with cls.codemod_workspace_snapshot(root) as snapshot:
            planned = cls.codemod_rule_plan(snapshot)
        if planned.failure:
            return r[t.VariadicTuple[m.Infra.CensusViolation]].from_failure(planned)
        repairable = frozenset(
            rule.id
            for rule in planned.value.rules
            if rule.fixable
            or rule.relocation is not None
            or rule.id.partition(c.Infra.CODEMOD_GENERATED_ID_SEPARATOR)[0]
            in c.Infra.SEMANTIC_CUTOVER_RULE_IDS.values()
        )
        parsed: list[m.Infra.CensusViolation] = []
        for violation in validation.value.violations:
            match = c.Infra.VIOLATION_PATTERN.match(violation)
            if match is None:
                msg = (
                    f"namespace violation does not follow the report format: "
                    f"{violation}"
                )
                raise ValueError(msg)
            parsed.append(
                m.Infra.CensusViolation(
                    module=match.group("module"),
                    rule=match.group("rule"),
                    line=int(match.group("line")),
                    message=match.group("message"),
                    fixable=match.group("rule") in repairable,
                ),
            )
        return r[t.VariadicTuple[m.Infra.CensusViolation]].ok(tuple(parsed))


__all__: list[str] = ["FlextInfraUtilitiesCodemodProject"]
