"""Project model data contracts by authenticated declaring source module.

The field renderer retains the existing native engine's expression nodes;
discovery, identity and ancestry remain owned by that engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import importlib
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._protocols_bootstrap import normalize_protocol_tree
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesSemanticCutover,
)
from flext_infra._utilities._git import FlextInfraUtilitiesGitignore
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._rope.source import FlextInfraUtilitiesRopeSource
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


class FlextInfraUtilitiesModelsProtocol:
    """Own the existing projector while its native semantic cutover is completed."""

    @classmethod
    def protocol_model_sources(
        cls, workspace: p.Infra.RopeWorkspaceDsl
    ) -> p.Result[Mapping[Path, str]]:
        """Return protocol sources without importing or publishing the target.

        Returns:
            Relative generated declarations, or the inventory's original failure.
            An absent declared facade/layout has no applicable projection.

        """
        return cls.protocol_model_sources_from_source(
            workspace.repository_root, workspace.rope_project
        )

    @classmethod
    def protocol_model_sources_from_source(
        cls,
        repository_root: Path,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[Mapping[Path, str]]:
        """Plan protocol mirrors directly from an overlaid source project.

        This public bootstrap entry intentionally does not construct a Rope
        workspace. Its source view can therefore inventory Pydantic declarations
        whose annotations reference protocol facade members not generated yet.

        Returns:
            Relative protocol mirror sources, or the source inventory failure.

        """
        return cls._ModelProtocolProjection(repository_root, source_project).sources()

    @classmethod
    def bootstrap_protocol_model_sources(cls, repository_root: Path) -> p.Result[bool]:
        """Publish source-derived protocol contracts before semantic admission.

        The first public generation cannot use the normal workspace or identity
        path: its Pydantic models may reference exactly the facade contracts this
        operation creates. The normal executor retries its identity admission
        after this bounded, atomic source bootstrap.

        Returns:
            Whether any source-derived protocol mirror was published.

        """
        root = repository_root.expanduser().resolve()
        normalized = normalize_protocol_tree(root)
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            root
        ) as binding:
            planned = cls.protocol_model_sources_from_source(root, binding[0])
        if planned.failure:
            return r[bool].from_failure(planned)
        members: list[tuple[str, tuple[str, ...]]] = []
        for relative, content in planned.value.items():
            destination = root / relative
            written = u.Cli.atomic_write_text_file(destination, content)
            if written.failure:
                return r[bool].from_failure(written)
            tree = ast.parse(content, filename=str(destination))
            holder = next(
                (node for node in tree.body if isinstance(node, ast.ClassDef)), None
            )
            if holder is not None:
                members.append((
                    ".".join(
                        relative.relative_to("src").with_suffix("").parts
                        if relative.parts[0] == "src"
                        else relative.with_suffix("").parts
                    ),
                    tuple(
                        node.name
                        for node in holder.body
                        if isinstance(node, ast.ClassDef)
                    ),
                ))
        cls._install_bootstrap_facade_members(members, root)
        return r[bool].ok(value=bool(normalized or planned.value))

    @staticmethod
    def _install_bootstrap_facade_members(
        members: list[tuple[str, tuple[str, ...]]], repository_root: Path
    ) -> None:
        """Bind published protocol members on the already-loaded public facade.

        This is the live equivalent of lazy facade export wiring. It is confined
        to the invocation that published the source contracts; ordinary codegen
        regenerates the durable facade projection immediately afterwards.
        """
        package = repository_root / "src"
        package_name = next(
            path.name for path in package.iterdir() if (path / "protocols.py").is_file()
        )
        facade = importlib.import_module(f"{package_name}.protocols").p.Infra
        for module_name, names in members:
            module = importlib.import_module(module_name)
            holder = next(
                value
                for value in vars(module).values()
                if isinstance(value, type)
                and value.__name__.startswith("Flext")
                and "Protocols" in value.__name__
            )
            for name in names:
                setattr(facade, name, getattr(holder, name))

    class _ModelProtocolProjection(
        FlextInfraUtilitiesSemanticCutover,
    ):
        """Bind declaring-module projection to one native source candidate."""

        def __init__(
            self,
            repository_root: Path,
            source_project: p.Infra.RopeProject,
        ) -> None:
            self.repository_root = repository_root
            self.project = source_project
            self.models: dict[str, p.Infra.RopePyName] = {}
            self.destinations: dict[str, Path] = {}
            self.canonical_routes: dict[str, str] = {}
            self.facades: dict[str, p.Infra.RopePyName] = {}
            self.package: Path | None = None
            self.package_name = ""
            self.class_stem = ""
            self.imports: dict[str, str] = {}
            self.selected: set[str] = set()
            self.references: dict[str, str] = {}
            self.parameters: set[str] = set()
            self.type_parameters: dict[str, list[t.Infra.AstTypeParameter]] = {}
            self.dependencies: set[str] = set()
            self.member_cache: dict[str, p.Infra.RopePyName | None] = {}

        def sources(self) -> p.Result[Mapping[Path, str]]:
            """Inventory declaring model sources before any semantic module opens.

            Returns:
                Generated data contracts, or the inventory or render failure.

            """
            # Pydantic evaluates annotations while Rope opens a semantic module.
            # Bootstrap must therefore derive the first mirror from the overlaid
            # source bytes, before a missing ``p`` facade member can make a model
            # declaration unopenable.
            return self._source_model_sources()

        def _source_model_sources(self) -> p.Result[Mapping[Path, str]]:
            """Project local Pydantic declarations using only the source view.

            The source inventory deliberately does not consult ``m`` or ``p``.
            Those facades are consumers of this projection and may be incomplete
            during bootstrap.

            Returns:
                Same-path protocol mirror sources derived from local model files.

            """
            result_type = r[Mapping[Path, str]]
            layout = self._source_layout()
            if layout is None:
                return result_type.ok({})
            package_dir, class_stem = layout
            models_root = package_dir / "_models"
            if not self.project.source_query(models_root, "isdir"):
                return result_type.ok({})
            grouped: dict[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ] = {}
            for directory, _children, files in self.project.source_walk(models_root):
                for filename in sorted(files):
                    source_path = directory / filename
                    if (
                        source_path.suffix != ".py"
                        or source_path.name == c.Infra.INIT_PY
                    ):
                        continue
                    tree = ast.parse(
                        self.project.source_text(source_path), filename=str(source_path)
                    )
                    classes = self._source_model_classes(tree)
                    if not classes:
                        continue
                    destination = (
                        package_dir
                        / "_protocols"
                        / source_path.relative_to(models_root)
                    )
                    grouped[destination] = [(*entry, tree) for entry in classes]
            rendered: dict[Path, str] = {}
            for destination, classes in sorted(grouped.items()):
                owner = (
                    class_stem
                    + "Protocols"
                    + "".join(
                        u.derive_class_stem(part.strip("_"))
                        for part in destination
                        .relative_to(package_dir / "_protocols")
                        .with_suffix("")
                        .parts
                    )
                )
                content = self._source_render_module(destination, owner, classes)
                rendered[destination.relative_to(self.repository_root)] = content
            return result_type.ok(rendered)

        def _source_layout(self) -> tuple[Path, str] | None:
            """Discover the package solely from the overlaid pyproject source.

            Returns:
                The package directory and facade class stem, if source declares one.

            """
            manifest = self.repository_root / c.PYPROJECT_FILENAME
            if not self.project.source_query(manifest, "isfile"):
                return None
            payload = tomllib.loads(self.project.source_text(manifest))
            project = payload.get("project", {})
            tool = payload.get("tool", {})
            flext = tool.get("flext", {}) if isinstance(tool, dict) else {}
            docs = flext.get("docs", {}) if isinstance(flext, dict) else {}
            package_name = docs.get("package_name") if isinstance(docs, dict) else None
            if not isinstance(package_name, str):
                name = project.get("name") if isinstance(project, dict) else None
                if not isinstance(name, str):
                    return None
                package_name = name.replace("-", "_")
            package = Path(*package_name.split("."))
            source_root = self.repository_root / "src"
            package_dir = source_root / package
            if not self.project.source_query(package_dir, "isdir"):
                package_dir = self.repository_root / package
            if not self.project.source_query(package_dir, "isdir"):
                return None
            return package_dir, u.derive_class_stem(package_name.replace("_", "-"))

        @staticmethod
        def _source_model_classes(
            tree: ast.Module,
        ) -> list[tuple[ast.ClassDef, tuple[str, ...]]]:
            """Return nested model declarations detected from their source bases."""
            classes: list[tuple[ast.ClassDef, tuple[str, ...]]] = []

            def collect(body: list[ast.stmt], parents: tuple[str, ...]) -> None:
                for statement in body:
                    if not isinstance(statement, ast.ClassDef):
                        continue
                    classes.append((statement, (*parents, statement.name)))
                    collect(statement.body, (*parents, statement.name))

            collect(tree.body, ())
            known: set[tuple[str, ...]] = set()
            changed = True
            model_bases = {
                "BaseModel",
                "ContractModel",
                "FlexibleModel",
                "RootModel",
                "FrozenArbitrary",
            }
            while changed:
                changed = False
                for node, path in classes:
                    bases = {
                        ast.unparse(base).rpartition(".")[2] for base in node.bases
                    }
                    local = {(*path[:-1], base) for base in bases}
                    if path not in known and (
                        bool(bases & model_bases) or bool(local & known)
                    ):
                        known.add(path)
                        changed = True
            return [(node, path) for node, path in classes if path in known]

        def _source_render_module(
            self,
            destination: Path,
            owner: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> str:
            """Render one same-path protocol mirror from its parsed declarations.

            Returns:
                The generated module or authored source extended with missing ports.

            """
            existing = (
                self.project.source_text(destination)
                if self.project.source_query(destination, "isfile")
                else None
            )
            generated = self._source_generated_module(owner, classes)
            if existing is None or existing.startswith(c.Infra.AUTOGEN_HEADER):
                return generated
            return self._source_extend_authored(existing, owner, classes, destination)

        @classmethod
        def _source_generated_module(
            cls,
            owner: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> str:
            """Render canonical nested runtime-checkable contracts without imports.

            Returns:
                The full generated module source.

            """
            lines = [
                c.Infra.AUTOGEN_HEADER,
                '"""Source-derived structural model contracts."""',
                "",
                "from __future__ import annotations",
                "from typing import Protocol, runtime_checkable",
                *cls.source_annotation_imports(classes),
                "",
                "",
                f"class {owner}:",
                '    """Own the structural model contracts declared by this module."""',
            ]
            for node, _path, _tree in classes:
                lines.extend((
                    "",
                    "    @runtime_checkable",
                    f"    class {node.name}(Protocol):",
                    (
                        '        """Structural data contract projected from the '
                        'owning model."""'
                    ),
                ))
                fields = cls.source_fields(node, classes)
                if fields:
                    lines.extend(
                        f"        {field.target.id}: {ast.unparse(field.annotation)}"
                        for field in fields
                        if isinstance(field.target, ast.Name)
                    )
                else:
                    lines.append("        pass")
            lines.extend(("", "", "__all__: list[str] = [", f'    "{owner}",', "]", ""))
            return "\n".join(lines)

        @classmethod
        def source_annotation_imports(
            cls,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> list[str]:
            """Retain imported non-facade annotation providers from source.

            Returns:
                Import statements needed by the source-derived field annotations.

            """
            roots = {
                symbol.id
                for node, _path, _tree in classes
                for field in cls.source_fields(node, classes)
                for symbol in ast.walk(field.annotation)
                if isinstance(symbol, ast.Name)
            }
            imports: list[str] = []
            excluded = {"m", "p", "pydantic"}
            for statement in classes[0][2].body:
                if isinstance(statement, ast.Import):
                    names = [
                        alias
                        for alias in statement.names
                        if (alias.asname or alias.name.partition(".")[0]) in roots
                        and alias.name.partition(".")[0] not in excluded
                    ]
                    if names:
                        imports.append(ast.unparse(ast.Import(names=names)))
                elif isinstance(statement, ast.ImportFrom) and statement.module not in {
                    "__future__",
                    "pydantic",
                }:
                    names = [
                        alias
                        for alias in statement.names
                        if (alias.asname or alias.name) in roots
                        and (alias.asname or alias.name) not in excluded
                    ]
                    if names:
                        imports.append(
                            ast.unparse(
                                ast.ImportFrom(
                                    module=statement.module,
                                    names=names,
                                    level=statement.level,
                                )
                            )
                        )
            return imports

        @classmethod
        def source_fields(
            cls,
            node: ast.ClassDef,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> list[ast.AnnAssign]:
            """Collect inherited structural fields in Python base precedence.

            Returns:
                Effective model fields with Pydantic annotation metadata removed.

            """
            by_name = {
                candidate.name: (candidate, tree) for candidate, _path, tree in classes
            }

            def collect(
                candidate: ast.ClassDef, tree: ast.Module, seen: set[str]
            ) -> dict[str, ast.AnnAssign]:
                if candidate.name in seen:
                    return {}
                seen = {*seen, candidate.name}
                fields: dict[str, ast.AnnAssign] = {}
                for base in reversed(candidate.bases):
                    parent = by_name.get(ast.unparse(base).rpartition(".")[2])
                    if parent is not None:
                        fields.update(collect(*parent, seen))
                fields.update({
                    statement.target.id: statement
                    for statement in candidate.body
                    if isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and not statement.target.id.startswith("_")
                    and statement.target.id != "model_config"
                })
                return {
                    name: ast.AnnAssign(
                        target=field.target,
                        annotation=cls._source_structural_annotation(
                            field.annotation, tree, candidate
                        ),
                        value=None,
                        simple=field.simple,
                    )
                    for name, field in fields.items()
                }

            tree = next(tree for candidate, _path, tree in classes if candidate is node)
            return list(collect(node, tree, set()).values())

        @classmethod
        def _source_structural_annotation(
            cls,
            annotation: ast.expr,
            tree: ast.Module,
            model: ast.ClassDef,
        ) -> ast.expr:
            """Drop ``Annotated`` metadata from a structural protocol field.

            The semantic projector already treats ``Annotated`` as its value
            type. Mirror that contract in the source bootstrap so Pydantic
            ``Field`` metadata remains owned by ``m`` and is never evaluated
            while importing a Protocol mirror.

            Returns:
                The recursively unwrapped declared value type.

            Raises:
                ValueError: If ``Annotated`` is shadowed or has no value type.

            """
            bindings: dict[str, str] = {}
            canonical_modules = {"typing", "typing_extensions"}
            for statement in tree.body:
                if isinstance(statement, ast.ImportFrom):
                    if statement.module not in canonical_modules:
                        continue
                    for alias in statement.names:
                        if alias.name != "Annotated":
                            continue
                        name = alias.asname or alias.name
                        previous = bindings.setdefault(name, "typing.Annotated")
                        if previous != "typing.Annotated":
                            msg = f"conflicting Annotated import in {tree}"
                            raise ValueError(msg)
                elif isinstance(statement, ast.Import):
                    for alias in statement.names:
                        if alias.name not in canonical_modules:
                            continue
                        module = alias.asname or alias.name.partition(".")[0]
                        name = f"{module}.Annotated"
                        previous = bindings.setdefault(name, "typing.Annotated")
                        if previous != "typing.Annotated":
                            msg = f"conflicting Annotated import in {tree}"
                            raise ValueError(msg)
            names = frozenset(bindings)
            if names and any(
                name in names
                for statement in tree.body
                if not isinstance(statement, ast.Import | ast.ImportFrom)
                for name in cls._source_bound_names(statement)
            ):
                msg = "module shadows its Annotated import"
                raise ValueError(msg)
            roots = frozenset(name.partition(".")[0] for name in names)
            if any(
                bound in roots and not cls._source_typing_import(statement, bound)
                for statement in tree.body
                if isinstance(statement, ast.Import | ast.ImportFrom)
                for bound in cls._source_bound_names(statement)
            ):
                msg = "module has an ambiguous Annotated import"
                raise ValueError(msg)
            if names and any(
                name in names
                for statement in model.body
                for name in cls._source_bound_names(statement)
            ):
                msg = "model shadows its Annotated import"
                raise ValueError(msg)
            while isinstance(annotation, ast.Subscript):
                name = ast.unparse(annotation.value)
                if name not in bindings:
                    if name == "Annotated":
                        msg = "model uses unbound typing.Annotated"
                        raise ValueError(msg)
                    break
                if not isinstance(annotation.slice, ast.Tuple):
                    msg = "Annotated field has no value type tuple"
                    raise ValueError(msg)
                if not annotation.slice.elts:
                    msg = "Annotated field has no value type"
                    raise ValueError(msg)
                annotation = annotation.slice.elts[0]
            return annotation

        @staticmethod
        def _source_typing_import(statement: ast.stmt, name: str) -> bool:
            """Prove one imported annotation provider from its source statement."""
            if isinstance(statement, ast.ImportFrom):
                return statement.module in {"typing", "typing_extensions"} and any(
                    alias.name == "Annotated" and (alias.asname or alias.name) == name
                    for alias in statement.names
                )
            if isinstance(statement, ast.Import):
                return any(
                    alias.name in {"typing", "typing_extensions"}
                    and (alias.asname or alias.name.partition(".")[0]) == name
                    for alias in statement.names
                )
            return False

        @staticmethod
        def _source_bound_names(statement: ast.stmt) -> frozenset[str]:
            """Return names bound by one source statement without descending scopes."""
            if isinstance(
                statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                return frozenset({statement.name})
            if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                return frozenset(
                    node.id
                    for target in targets
                    for node in ast.walk(target)
                    if isinstance(node, ast.Name)
                )
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                return frozenset(
                    alias.asname or alias.name.partition(".")[0]
                    for alias in statement.names
                    if alias.name != "*"
                )
            return frozenset()

        @classmethod
        def _source_extend_authored(
            cls,
            source: str,
            owner: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            destination: Path,
        ) -> str:
            """Preserve authored contracts and append only missing nested ports.

            Returns:
                The authored source with only absent contracts inserted.

            Raises:
                ValueError: The canonical holder is absent or a contract conflicts.

            """
            tree = ast.parse(source, filename=str(destination))
            holder = next(
                (
                    node
                    for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.name == owner
                ),
                None,
            )
            if holder is None:
                message = (
                    "authored protocol destination has no exported canonical holder "
                    f"{owner}: {destination}"
                )
                raise ValueError(message)
            authored = {
                node.name: node
                for node in holder.body
                if isinstance(node, ast.ClassDef)
            }
            additions: list[str] = []
            for node, _path, _module in classes:
                present = authored.get(node.name)
                fields = cls.source_fields(node, classes)
                expected = {
                    field.target.id: ast.unparse(field.annotation)
                    for field in fields
                    if isinstance(field.target, ast.Name)
                }
                if present is not None:
                    actual = {
                        field.target.id: ast.unparse(field.annotation)
                        for field in present.body
                        if isinstance(field, ast.AnnAssign)
                        and isinstance(field.target, ast.Name)
                    }
                    if any(
                        annotation != expected[name]
                        for name, annotation in actual.items()
                        if name in expected
                    ):
                        message = (
                            "incompatible authored protocol contract "
                            f"{owner}.{node.name}: {destination}"
                        )
                        raise ValueError(message)
                    continue
                additions.extend((
                    "    @runtime_checkable",
                    f"    class {node.name}(Protocol):",
                    (
                        '        """Structural data contract projected from the '
                        'owning model."""'
                    ),
                ))
                additions.extend(
                    f"        {field.target.id}: {ast.unparse(field.annotation)}"
                    for field in fields
                    if isinstance(field.target, ast.Name)
                )
                if not fields:
                    additions.append("        pass")
                additions.append("")
            if not additions:
                return source
            lines = source.splitlines(keepends=True)
            if "from typing import Protocol" not in source:
                position = next(
                    (
                        index + 1
                        for index, line in enumerate(lines)
                        if line.startswith("from __future__ import")
                    ),
                    0,
                )
                lines.insert(
                    position, "from typing import Protocol, runtime_checkable\n"
                )
            if holder.end_lineno is None:
                message = (
                    f"authored protocol holder has no source extent: {destination}"
                )
                raise ValueError(message)
            lines.insert(holder.end_lineno, "\n" + "\n".join(additions).rstrip() + "\n")
            return "".join(lines)

        def render(self) -> p.Result[Mapping[Path, str]]:
            """Render the admitted native model inventory without publishing it.

            Returns:
                Generated data contracts, or a competing-destination failure.

            """
            result_type = r[Mapping[Path, str]]
            if self.package is None or not {"m", "p"}.issubset(self.facades):
                return result_type.ok({})
            self.selected.update(self._declared())
            declarations: dict[str, list[t.Infra.AstStatement]] = {}
            imports: dict[str, dict[str, str]] = {}
            dependencies: dict[str, set[str]] = {}
            while pending := sorted(self.selected - declarations.keys()):
                for route in pending:
                    self.imports = {
                        "future": "from __future__ import annotations",
                        "protocol": "from typing import Protocol, runtime_checkable",
                    }
                    self.dependencies = set()
                    declarations[route] = self._fields(self.models[route])
                    self.type_parameters[route] = self._type_parameters(
                        self.models[route]
                    )
                    imports[route] = self.imports
                    dependencies[route] = self.dependencies
            grouped: dict[Path, list[str]] = {}
            for route in sorted(declarations):
                grouped.setdefault(self.destinations[route], []).append(route)
            rendered: dict[Path, str] = {}
            owners: dict[str, Path] = {}
            for path, routes in sorted(grouped.items()):
                owner = self.references[routes[0]].partition(".")[0]
                previous = owners.setdefault(owner, path)
                if previous != path:
                    return result_type.fail(
                        f"competing native model protocol holder {owner}: "
                        f"{previous} and {path}"
                    )
                names: dict[str, str] = {}
                for route in routes:
                    name = self._source_class(self.models[route]).get_name()
                    previous_route = names.setdefault(name, route)
                    if previous_route != route:
                        return result_type.fail(
                            f"competing model contracts {name}: {path}"
                        )
                rendered[path.relative_to(self.workspace.repository_root)] = (
                    self._render_module(
                        path, routes, declarations, imports, dependencies
                    )
                )
            return result_type.ok(rendered)

        def _render_module(
            self,
            destination: Path,
            routes: list[str],
            declarations: dict[str, list[t.Infra.AstStatement]],
            imports: dict[str, dict[str, str]],
            dependencies: dict[str, set[str]],
        ) -> str:
            """Render all contracts from one declaring module under one holder.

            Returns:
                The generated or safely extended authored source.

            Raises:
                ValueError: If no package was inventoried.

            """
            if self.package is None:
                message = "protocol projection has no inventoried package"
                raise ValueError(message)
            owner = self.references[routes[0]].partition(".")[0]
            siblings = tuple(
                sorted(
                    {
                        self.references[dependency].partition(".")[0]
                        for route in routes
                        for dependency in dependencies[route]
                    }
                    - {owner}
                )
            )
            selected_imports: dict[str, str] = {}
            for route in routes:
                for name, statement in imports[route].items():
                    previous = selected_imports.setdefault(name, statement)
                    if previous != statement:
                        message = (
                            f"competing protocol module import {name}: {destination}"
                        )
                        raise ValueError(message)
            if siblings:
                selected_imports["protocol"] = (
                    "from typing import TYPE_CHECKING, Protocol, runtime_checkable"
                )
            selected_imports.pop(owner, None)
            # Field extraction still supplies legacy expression nodes. Convert
            # them once at this boundary; module structure is template-owned.
            context = m.Infra.ModelProtocolRenderContext(
                header=c.Infra.AUTOGEN_HEADER,
                copyright_notice=FlextInfraUtilitiesLintRecipes.copyright_notice(
                    self.package,
                    module=destination,
                    source_project=self.project,
                ),
                imports=tuple(sorted(set(selected_imports.values()))),
                sibling_import_lines=tuple(
                    FlextInfraUtilitiesLazyInitRender.source_import_lines(
                        "    ",
                        f"{self.package_name}."
                        f"{FlextInfraUtilitiesCodegenNamespace.facade_families()['p'].directory}",
                        siblings,
                    )
                )
                if siblings
                else (),
                owner=owner,
                contracts=tuple(
                    m.Infra.ModelProtocolRenderContext.ModelProtocolContract(
                        name=self._source_class(self.models[route]).get_name(),
                        type_parameters=self._declaration_text(
                            self.type_parameters[route]
                        ),
                        declarations=self._declaration_text(declarations[route]),
                    )
                    for route in routes
                ),
            )
            template = (
                FlextInfraUtilitiesGitignore.codegen_templates_root(
                    config.Infra.codegen
                )
                / c.Infra.TEMPLATE_MODEL_PROTOCOL
            )
            content = u.Cli.template_render(template, context).unwrap()
            resource = self.workspace.resource(destination)
            if resource is None:
                return content
            existing = self.project.source_text(destination)
            if existing.startswith(c.Infra.AUTOGEN_HEADER):
                # A general generation marker alone never proves this owner.
                if not existing.startswith(content.split('"""', maxsplit=1)[0]) or (
                    '"""Source-derived structural model contracts.' not in existing
                ):
                    message = (
                        "protocol destination has unproven generated ownership: "
                        f"{destination}"
                    )
                    raise ValueError(message)
                return content
            return self._extend_authored(destination, existing, context)

        @staticmethod
        def _declaration_text(
            nodes: Sequence[t.Infra.AstStatement | t.Infra.AstTypeParameter],
        ) -> tuple[str, ...]:
            """Render the existing engine's expressions.

            Returns:
                Declaration text without reparsing model sources.

            """
            return tuple(
                FlextInfraUtilitiesRopeAnalysis.Tree.unparse(
                    FlextInfraUtilitiesRopeAnalysis.Tree.fix_missing_locations(node)
                )
                for node in nodes
            )

        def _extend_authored(
            self,
            destination: Path,
            source: str,
            context: p.Infra.ModelProtocolRenderContext,
        ) -> str:
            """Append absent contracts without replacing authored bytes or interfaces.

            Existing contracts must have the same projected data signature. Extra
            authored methods remain untouched; ambiguous owners and import bindings
            fail before any file plan is returned.

            Returns:
                The preserved source with absent contracts inserted.

            Raises:
                ValueError: The owner, contract, import or source extent conflicts.
                TypeError: The owner has no native class declaration.

            """
            resource = self.workspace.resource(destination)
            if resource is None:
                message = f"authored protocol source is unavailable: {destination}"
                raise ValueError(message)
            module = self.require_semantic_module(
                FlextInfraUtilitiesRopeCore.resolve_pymodule(self.project, resource)
            )
            binding = module.get_attributes().get(context.owner)
            if binding is None or context.owner not in (
                FlextInfraUtilitiesRopeAnalysis.public_export_names_source(module)
            ):
                message = (
                    "authored protocol destination has no exported canonical holder "
                    f"{context.owner}: {destination}"
                )
                raise ValueError(message)
            holder = self._source_class(binding)
            if holder.get_module() is not module:
                message = (
                    "authored protocol holder is not declared in its mirror: "
                    f"{context.owner}: {destination}"
                )
                raise ValueError(message)
            missing = self._missing_contracts(holder, context, destination)
            if not missing:
                return source
            template = (
                FlextInfraUtilitiesGitignore.codegen_templates_root(
                    config.Infra.codegen
                )
                / c.Infra.TEMPLATE_MODEL_PROTOCOL
            )
            rendered = u.Cli.template_render(
                template, context.model_copy(update={"contracts": tuple(missing)})
            ).unwrap()
            additions = self._authored_additions(rendered, module)
            lines = source.splitlines(keepends=True)
            declaration = holder.get_ast()
            if not isinstance(
                declaration, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef
            ):
                message = (
                    f"authored protocol holder has no class declaration: {destination}"
                )
                raise TypeError(message)
            if declaration.col_offset or declaration.lineno == declaration.end_lineno:
                message = (
                    "authored protocol holder requires a multiline top-level suite: "
                    f"{destination}"
                )
                raise ValueError(message)
            if declaration.end_lineno is None:
                message = (
                    f"authored protocol holder has no source extent: {destination}"
                )
                raise ValueError(message)
            lines.insert(declaration.end_lineno, "\n" + "\n".join(additions) + "\n")
            imports = list(context.imports)
            if context.sibling_import_lines:
                imports.append(
                    "if TYPE_CHECKING:\n" + "\n".join(context.sibling_import_lines)
                )
            position = FlextInfraUtilitiesRopeSource.find_import_insert_position(
                source.splitlines(keepends=True), past_existing=False
            )
            imports = [statement for statement in imports if statement not in source]
            lines.insert(position, "\n".join(imports) + "\n" if imports else "")
            return "".join(lines)

        def _missing_contracts(
            self,
            holder: p.Infra.RopeSourceClass,
            context: p.Infra.ModelProtocolRenderContext,
            destination: Path,
        ) -> list[p.Infra.ModelProtocolRenderContext.ModelProtocolContract]:
            """Validate existing authored signatures before extending their holder.

            Returns:
                Only contracts absent from the authored holder.

            Raises:
                ValueError: An authored contract has an incompatible signature.

            """
            missing: list[p.Infra.ModelProtocolRenderContext.ModelProtocolContract] = []
            protocol_base = self.qualified_name(
                self.project, "Protocol", module_name="typing"
            ).get_object()
            for contract in context.contracts:
                present = holder.get_attributes().get(contract.name)
                if present is None:
                    missing.append(contract)
                    continue
                if (
                    protocol_base
                    not in self.class_ancestry(self._source_class(present))
                    or sorted(self._declaration_text(self._fields(present)))
                    != sorted(contract.declarations)
                    or self._declaration_text(self._type_parameters(present))
                    != contract.type_parameters
                ):
                    message = (
                        f"incompatible authored protocol contract "
                        f"{context.owner}.{contract.name}: {destination}"
                    )
                    raise ValueError(message)
            return missing

        def _authored_additions(
            self, rendered: str, module: p.Infra.RopeSourceModule
        ) -> list[str]:
            """Read template-owned class slots and authenticate import receivers.

            Returns:
                Template-rendered contract suites, retaining their indentation.

            Raises:
                ValueError: An import would replace an authored binding.

            """
            tree = FlextInfraUtilitiesRopeAnalysis.Tree.parse(rendered)
            self._normal_authored_imports(tree, module)
            for statement in FlextInfraUtilitiesRopeAnalysis.Tree.walk(tree):
                if (
                    not isinstance(
                        statement, FlextInfraUtilitiesRopeAnalysis.Tree.ImportFrom
                    )
                    or statement.module == "__future__"
                ):
                    continue
                for alias in statement.names:
                    receiver = alias.asname or alias.name
                    existing = module.get_attributes().get(receiver)
                    if existing is not None and not self.same_name(
                        existing,
                        self.qualified_name(
                            self.project, alias.name, module_name=statement.module
                        ),
                    ):
                        message = (
                            f"authored protocol import collision {receiver}: "
                            f"{module.get_name()}"
                        )
                        raise ValueError(message)
            holder = next(
                node
                for node in tree.body
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef)
            )
            lines = rendered.splitlines(keepends=True)
            return [
                "".join(
                    lines[
                        min([
                            node.lineno,
                            *(item.lineno for item in node.decorator_list),
                        ])
                        - 1 : node.end_lineno
                    ]
                )
                for node in holder.body
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef)
            ]

        def _normal_authored_imports(
            self, tree: t.Infra.AstModule, module: p.Infra.RopeSourceModule
        ) -> None:
            """Authenticate normal imports as well as imported member receivers.

            Raises:
                ValueError: An import would replace an authored binding.

            """
            for statement in tree.body:
                if not isinstance(
                    statement, FlextInfraUtilitiesRopeAnalysis.Tree.Import
                ):
                    continue
                for alias in statement.names:
                    receiver = alias.asname or alias.name.partition(".")[0]
                    existing = module.get_attributes().get(receiver)
                    provider = alias.name if alias.asname else receiver
                    if existing is not None and existing.get_object() is not (
                        self.project.get_module(provider)
                    ):
                        message = (
                            f"authored protocol import collision {receiver}: "
                            f"{module.get_name()}"
                        )
                        raise ValueError(message)

        def _inventory(self) -> p.Result[bool]:
            """Admit native identities before deriving their protocol references.

            Returns:
                Applicability when admitted, or the model inventory's failure.

            """
            result_type = r[bool]
            layout = FlextInfraUtilitiesCodegenNamespace.layout(
                self.workspace.repository_root, rope_project=self.project
            )
            if layout is None:
                return result_type.ok(value=False)
            self.package_name = layout.package_name
            self.class_stem = layout.class_stem
            self.package = layout.package_dir
            self._inventory_facades()
            if not {"m", "p"}.issubset(self.facades):
                return result_type.ok(value=False)
            inventoried = self._inventory_models()
            if inventoried.failure:
                return result_type.from_failure(inventoried)
            families = FlextInfraUtilitiesCodegenNamespace.facade_families()
            if self.package is None:
                return result_type.fail("model protocol inventory lost its package")
            model_directory = self.package / families["m"].directory
            for route, binding in self.models.items():
                if not self._owned(binding):
                    continue
                source = self._source_class(binding)
                resource = source.get_module().get_resource()
                if resource is None:
                    return result_type.fail(
                        f"model has no declaring source resource: {route}"
                    )
                path = Path(resource.real_path)
                if (
                    not path.is_relative_to(model_directory)
                    or path.name == c.Infra.INIT_PY
                ):
                    continue
                relative = path.relative_to(model_directory)
                destination = self.package / families["p"].directory / relative
                owner = (
                    self.class_stem
                    + families["p"].suffix
                    + "".join(
                        u.derive_class_stem(part.strip("_"))
                        for part in relative.with_suffix("").parts
                    )
                )
                self.destinations[route] = destination
                self.references[route] = f"{owner}.{source.get_name()}"
            return result_type.ok(value=True)

        def _inventory_facades(self) -> None:
            """Elect the native model and protocol exports in this package.

            Raises:
                TypeError: An indexed protocol file is not a native source module.
                ValueError: If an indexed source resource is unavailable.

            """
            for entry in self.workspace.modules():
                if entry.package_dir != self.package:
                    continue
                resource = self.workspace.resource(entry.file_path)
                if resource is None:
                    message = (
                        f"indexed protocol input is unavailable: {entry.file_path}"
                    )
                    raise ValueError(message)
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    self.project, resource
                )
                if not self.source_module(module):
                    message = (
                        f"indexed protocol file is not a source module: "
                        f"{entry.file_path}"
                    )
                    raise TypeError(message)
                if not {"m", "p"}.intersection(
                    FlextInfraUtilitiesRopeAnalysis.public_export_names_source(module)
                ):
                    continue
                owner = (FlextInfraUtilitiesRopeAnalysis.published_facade_owner)(
                    self.project, resource
                )
                if owner is not None and owner[0] in {"m", "p"}:
                    self.facades[owner[0]] = module.get_attribute(owner[1])
                    self.package = entry.package_dir

        def _inventory_models(self) -> p.Result[bool]:
            """Close native model identities through their published namespaces.

            Read native attribute bindings without resolving their names again
            through a lexical scope. Class aliases retain the same canonical
            binding used by annotation resolution. An ancestry failure retains
            its cause at the existing operation boundary; it never removes a
            model from the inventory silently.

            Returns:
                Admission, or a contextual ambiguous/competing identity failure.
                Native ancestry exceptions retain their existing causal boundary.

            """
            result_type = r[bool]
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            pending: list[
                tuple[
                    str,
                    p.Infra.RopePyName,
                    tuple[p.Infra.RopePyObject, ...],
                ]
            ] = [("", self.facades["m"], ())]
            while pending:
                prefix, binding, ancestors = pending.pop()
                value = binding.get_object()
                if not self.py_class(value) or value in ancestors:
                    continue
                for name, member in sorted(value.get_attributes().items()):
                    if name.startswith("_"):
                        continue
                    child = member.get_object()
                    if not self.py_class(child):
                        continue
                    route = f"{prefix}{name}"
                    canonical = self.class_assignment_binding(member)
                    if canonical is None:
                        return result_type.fail(
                            f"model class alias has no canonical identity: p.{route}"
                        )
                    canonical_class = canonical.get_object()
                    if not self.py_class(canonical_class):
                        continue
                    registered = self._register_model(
                        route, canonical, canonical_class, model_base
                    )
                    if registered.failure:
                        return result_type.from_failure(registered)
                    pending.append((f"{route}.", canonical, (*ancestors, value)))
            return self._inventory_local_models(model_base)

        def _inventory_local_models(
            self, model_base: p.Infra.RopePyObject
        ) -> p.Result[bool]:
            """Inventory local declarations independently of facade consumption.

            Returns:
                Admission, or a competing local model identity failure.

            Raises:
                ValueError: An indexed source resource is unavailable.

            """
            result_type = r[bool]
            if self.package is None:
                return result_type.fail("local model inventory has no package")
            # Published aliases are consumers, not the declaration inventory.
            # Walk every local model source through its existing native module,
            # including classes that have not yet reached the facade.
            directory = self.package / (
                FlextInfraUtilitiesCodegenNamespace.facade_families()["m"].directory
            )
            for entry in self.workspace.modules():
                if not entry.file_path.is_relative_to(directory):
                    continue
                resource = self.workspace.resource(entry.file_path)
                if resource is None:
                    message = f"indexed model source is unavailable: {entry.file_path}"
                    raise ValueError(message)
                module = self.require_semantic_module(
                    FlextInfraUtilitiesRopeCore.resolve_pymodule(self.project, resource)
                )
                registered = self._inventory_module_models(module, model_base)
                if registered.failure:
                    return result_type.from_failure(registered)
            return result_type.ok(value=True)

        def _inventory_module_models(
            self,
            module: p.Infra.RopeSourceModule,
            model_base: p.Infra.RopePyObject,
        ) -> p.Result[bool]:
            """Walk native declarations while excluding inherited foreign bindings.

            Returns:
                Admission, or a competing local model identity failure.

            """
            result_type = r[bool]
            candidates = list(module.get_attributes().values())
            visited: set[int] = set()
            while candidates:
                binding = candidates.pop()
                value = binding.get_object()
                if not self.py_class(value) or id(value) in visited:
                    continue
                visited.add(id(value))
                if value.get_module() is not module:
                    continue
                candidates.extend(value.get_attributes().values())
                if model_base not in self.class_ancestry(value):
                    continue
                if any(
                    self.same_name(binding, known) for known in self.models.values()
                ):
                    continue
                registered = self._register_model(
                    value.get_name(), binding, value, model_base
                )
                if registered.failure:
                    return result_type.from_failure(registered)
            return result_type.ok(value=True)

        def _register_model(
            self,
            route: str,
            binding: p.Infra.RopePyName,
            model_class: p.Infra.RopeSourceClass,
            model_base: p.Infra.RopePyObject,
        ) -> p.Result[bool]:
            """Record one canonical model identity under its published route.

            Returns:
                Admission, or a competing identity failure for the route.

            """
            result_type = r[bool]
            if model_base in self.class_ancestry(model_class):
                previous = self.models.setdefault(route, binding)
                if not self.same_name(previous, binding):
                    return result_type.fail(f"competing model identities for p.{route}")
            return result_type.ok(value=True)

        def _declared(self) -> set[str]:
            """Select one route per local native declaration, never legacy tokens.

            Returns:
                The canonical routes for all mirrored model declarations.

            Raises:
                ValueError: Distinct models compete for one protocol identity.

            """
            declared: dict[str, str] = {}
            entities: dict[str, str] = {}
            for route in sorted(self.destinations):
                name = self._source_class(self.models[route]).get_name()
                elected = entities.setdefault(name, route)
                if not self.same_name(self.models[elected], self.models[route]):
                    message = (
                        f"competing flat protocol entity {name}: {elected}, {route}"
                    )
                    raise ValueError(message)
                previous = declared.setdefault(self.references[route], route)
                if not self.same_name(self.models[previous], self.models[route]):
                    message = (
                        "competing model identities for protocol "
                        f"{self.references[route]}"
                    )
                    raise ValueError(message)
            self.canonical_routes = declared
            return set(declared.values())

        def _fields(self, binding: p.Infra.RopePyName) -> list[t.Infra.AstStatement]:
            """Retain inherited annotated data, never defaults or model methods.

            Returns:
                Annotated attributes in native C3 override order.

            Raises:
                TypeError: If a model declaration is absent.

            """
            fields: dict[str, t.Infra.AstStatement] = {}
            source = self._source_class(binding)
            definition = source.get_ast()
            if not isinstance(
                definition, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef
            ):
                message = "model has no authenticated class declaration"
                raise TypeError(message)
            self.parameters = {
                parameter.name
                for parameter in definition.type_params
                if isinstance(
                    parameter,
                    FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar
                    | FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec
                    | FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple,
                )
            }
            native_ancestors = source.get_mro()
            if not all(
                FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(native_ancestor)
                or FlextInfraUtilitiesRopeRuntimeTypes.unresolved_witness(
                    native_ancestor
                )
                for native_ancestor in native_ancestors
            ):
                # Uma primeira leitura pelo índice fonte lazy pode observar
                # transientes de construção: a própria avaliação completa os
                # módulos envolvidos só depois de sua pilha desenrolar, então
                # uma re-leitura settled segue; uma testemunha não resolvida
                # persistente ocupa seu slot por política dc15 e é pulada.
                source.invalidate_bases()
                native_ancestors = source.get_mro()
            for native_ancestor in reversed(native_ancestors):
                if FlextInfraUtilitiesRopeRuntimeTypes.unresolved_witness(
                    native_ancestor
                ):
                    continue
                ancestor = FlextInfraUtilitiesRopeRuntime.require_class_object(
                    native_ancestor,
                    f"model protocol ancestor of {source.get_name()}",
                )
                if not self.py_class(ancestor):
                    continue
                declaring = ancestor.get_module()
                origin = declaring.get_resource() if declaring is not None else None
                if origin is None or not Path(
                    origin.real_path
                ).resolve().is_relative_to(self.project.root.real_path):
                    # Foreign runtime bases (pydantic internals, stdlib,
                    # third-party) are the projection's consumer boundary:
                    # their members are never protocol ancestors.
                    continue
                node, lexical = ancestor.get_ast(), ancestor.get_scope()
                if not isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                    message = "model ancestor has no authenticated class declaration"
                    raise TypeError(message)
                self._collect_fields(node, lexical, fields)
            return list(fields.values())

        def _field_declaration(
            self, statement: t.Infra.AstStatement, scope: p.Infra.RopeScope
        ) -> tuple[str, t.Infra.AstExpression] | None:
            """Select annotated storage or a native computed field's return type.

            Returns:
                The declared field and annotation, or no data declaration.

            Raises:
                TypeError: If a computed field has no return annotation.

            """
            if isinstance(
                statement, FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign
            ) and isinstance(
                statement.target, FlextInfraUtilitiesRopeAnalysis.Tree.Name
            ):
                return statement.target.id, statement.annotation
            if not isinstance(
                statement, FlextInfraUtilitiesRopeAnalysis.Tree.FunctionDef
            ) or not any(
                self._denotes(
                    decorator.func
                    if isinstance(decorator, FlextInfraUtilitiesRopeAnalysis.Tree.Call)
                    else decorator,
                    scope,
                    "pydantic",
                    "computed_field",
                )
                for decorator in statement.decorator_list
            ):
                return None
            if statement.returns is None:
                message = "computed model field has no return annotation"
                raise TypeError(message)
            return statement.name, statement.returns

        def _collect_fields(
            self,
            node: t.Infra.AstClassDefinition,
            scope: p.Infra.RopeScope,
            fields: dict[str, t.Infra.AstStatement],
        ) -> None:
            """Apply one native declaration's field overrides in C3 collection order."""
            for statement in node.body:
                declaration = self._field_declaration(statement, scope)
                if declaration is None:
                    continue
                name, annotation = declaration
                if name.startswith("_") or name == "model_config":
                    continue
                if isinstance(
                    annotation, FlextInfraUtilitiesRopeAnalysis.Tree.Subscript
                ) and self._denotes(annotation.value, scope, "typing", "ClassVar"):
                    # Armazenamento de classe (ClassVar) não é campo de
                    # modelo: exclui da projeção e segue.
                    fields.pop(name, None)
                    continue
                if isinstance(
                    annotation, FlextInfraUtilitiesRopeAnalysis.Tree.Subscript
                ) and self._denotes(annotation.value, scope, "typing", "Final"):
                    annotation = annotation.slice
                fields[name] = FlextInfraUtilitiesRopeAnalysis.Tree.AnnAssign(
                    target=FlextInfraUtilitiesRopeAnalysis.Tree.Name(
                        id=name, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Store()
                    ),
                    annotation=self._annotation(annotation, scope, ()),
                    value=None,
                    simple=1,
                )

        def _type_parameters(
            self, binding: p.Infra.RopePyName
        ) -> list[t.Infra.AstTypeParameter]:
            """Rebind parameter bounds without mutating the engine's cached AST.

            Returns:
                Source-owned PEP 695 parameters in their original declaration order.

            Raises:
                TypeError: If a native class or supported parameter is absent.

            """
            source = self._source_class(binding)
            node = source.get_ast()
            if not isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.ClassDef):
                message = "model parameters have no native class declaration"
                raise TypeError(message)
            scope = source.get_scope()
            parameters: list[t.Infra.AstTypeParameter] = []
            for parameter in node.type_params:
                if not isinstance(
                    parameter,
                    FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar
                    | FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec
                    | FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple,
                ):
                    message = "model has an unsupported native type parameter"
                    raise TypeError(message)
                default = (
                    self._annotation(parameter.default_value, scope, ())
                    if parameter.default_value is not None
                    else None
                )
                if isinstance(parameter, FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar):
                    bound = (
                        self._annotation(parameter.bound, scope, ())
                        if parameter.bound is not None
                        else None
                    )
                    parameters.append(
                        FlextInfraUtilitiesRopeAnalysis.Tree.TypeVar(
                            name=parameter.name, bound=bound, default_value=default
                        )
                    )
                elif isinstance(
                    parameter, FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec
                ):
                    parameters.append(
                        FlextInfraUtilitiesRopeAnalysis.Tree.ParamSpec(
                            name=parameter.name, default_value=default
                        )
                    )
                else:
                    parameters.append(
                        FlextInfraUtilitiesRopeAnalysis.Tree.TypeVarTuple(
                            name=parameter.name, default_value=default
                        )
                    )
            return parameters

        def _annotation(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Restore source-bound annotation closure without target imports.

            Returns:
                A structural annotation with model dependencies projected to p.

            """
            if (
                isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Name)
                and node.id in self.parameters
            ):
                return node
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Constant):
                if isinstance(node.value, str):
                    return self._annotation(
                        FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                            node.value
                        ),
                        scope,
                        visiting,
                    )
                return node
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Subscript):
                return self._annotation_subscript(node, scope, visiting)
            if isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.Name
                | FlextInfraUtilitiesRopeAnalysis.Tree.Attribute,
            ):
                return self._annotation_symbol(node, scope, visiting)
            return self._annotation_container(node, scope, visiting)

        def _annotation_subscript(
            self,
            node: t.Infra.AstSubscript,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Retain generic arguments without interpreting literal or metadata data.

            Returns:
                The projected generic or the structural Annotated payload.

            Raises:
                ValueError: If Annotated has no native payload.

            """
            if self._denotes(node.value, scope, "typing", "Annotated"):
                if not isinstance(
                    node.slice, FlextInfraUtilitiesRopeAnalysis.Tree.Tuple
                ):
                    message = "Annotated has no native payload"
                    raise ValueError(message)
                return self._annotation(node.slice.elts[0], scope, visiting)
            if self._denotes(node.value, scope, "typing", "Literal"):
                return FlextInfraUtilitiesRopeAnalysis.Tree.Subscript(
                    value=self._annotation(node.value, scope, visiting),
                    slice=self._literal_slice(node.slice, scope, visiting),
                    ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load(),
                )
            return FlextInfraUtilitiesRopeAnalysis.Tree.Subscript(
                value=self._annotation(node.value, scope, visiting),
                slice=self._annotation(node.slice, scope, visiting),
                ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load(),
            )

        def _literal_slice(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Bind literal members to their declaring imports, constants intact.

            Returns:
                A literal slice whose symbolic members are provider-bound.

            """
            if isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.Tuple
                | FlextInfraUtilitiesRopeAnalysis.Tree.List,
            ):
                values = [
                    self._literal_slice(item, scope, visiting) for item in node.elts
                ]
                if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Tuple):
                    return FlextInfraUtilitiesRopeAnalysis.Tree.Tuple(
                        elts=values, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load()
                    )
                return FlextInfraUtilitiesRopeAnalysis.Tree.List(
                    elts=values, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load()
                )
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Constant):
                return node
            return self._annotation(node, scope, visiting)

        def _annotation_container(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Project native union, sequence and unpacking annotation shapes.

            Returns:
                A container with its original structural kind.

            Raises:
                TypeError: If the native shape is unsupported.

            """
            if isinstance(
                node, FlextInfraUtilitiesRopeAnalysis.Tree.BinOp
            ) and isinstance(node.op, FlextInfraUtilitiesRopeAnalysis.Tree.BitOr):
                return FlextInfraUtilitiesRopeAnalysis.Tree.BinOp(
                    left=self._annotation(node.left, scope, visiting),
                    op=FlextInfraUtilitiesRopeAnalysis.Tree.BitOr(),
                    right=self._annotation(node.right, scope, visiting),
                )
            if isinstance(
                node,
                FlextInfraUtilitiesRopeAnalysis.Tree.Tuple
                | FlextInfraUtilitiesRopeAnalysis.Tree.List,
            ):
                values = [self._annotation(item, scope, visiting) for item in node.elts]
                return (
                    FlextInfraUtilitiesRopeAnalysis.Tree.Tuple(
                        elts=values, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load()
                    )
                    if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Tuple)
                    else FlextInfraUtilitiesRopeAnalysis.Tree.List(
                        elts=values, ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load()
                    )
                )
            if isinstance(node, FlextInfraUtilitiesRopeAnalysis.Tree.Starred):
                return FlextInfraUtilitiesRopeAnalysis.Tree.Starred(
                    value=self._annotation(node.value, scope, visiting),
                    ctx=FlextInfraUtilitiesRopeAnalysis.Tree.Load(),
                )
            message = (
                f"unsupported native model annotation: "
                f"{FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node)}"
            )
            raise TypeError(message)

        def _annotation_symbol(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            visiting: t.StrTuple,
        ) -> t.Infra.AstExpression:
            """Resolve model, authored port and alias identities in the native scope.

            Returns:
                A source-bound annotation using its declaring import provider.

            Raises:
                TypeError: If a forbidden loose annotation is selected.
                ValueError: If a source annotation alias recurses.

            """
            binding = self.resolve_symbol(scope, node)
            if self._denotes(node, scope, "builtins", "object") or self._denotes(
                node, scope, "typing", "Any"
            ):
                message = (
                    f"forbidden generated protocol annotation: "
                    f"{FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node)}"
                )
                raise TypeError(message)
            projected = self._model_annotation(node, scope, binding)
            if projected is not None:
                return projected
            port = self._protocol_annotation(binding)
            if port is not None:
                return port
            alias = (
                self.annotation_alias_definition(binding)
                if binding is not None
                else None
            )
            if alias is not None:
                declaration, lexical = alias
                name = declaration.name.id
                if name in visiting:
                    message = f"recursive model annotation alias: {name}"
                    raise ValueError(message)
                if not declaration.type_params:
                    return self._annotation(
                        declaration.value, lexical, (*visiting, name)
                    )
            root = FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node).partition(".")[0]
            if binding is not None and self.same_name(
                self.facades["p"], self.expression_name(scope, root)
            ):
                return self._declared_port(
                    binding,
                    FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node).partition(".")[
                        2
                    ],
                )
            source = FlextInfraUtilitiesRopeAnalysis.Tree.unparse(node)
            self._require_nonmodel_annotation(binding, source)
            aliases = self._imports(source, scope)
            renamed = aliases.get(root, root)
            return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                f"{renamed}{source[len(root) :]}"
            )

        def _require_nonmodel_annotation(
            self, binding: p.Infra.RopePyName | None, source: str
        ) -> None:
            """Never retain a concrete model import as a substitute for its contract.

            Raises:
                ValueError: A concrete model has no admitted protocol identity.

            """
            if binding is None:
                return
            value = binding.get_object()
            if not self.py_class(value):
                return
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            if model_base in self.class_ancestry(value):
                message = (
                    f"model annotation has no admitted protocol identity: {source}"
                )
                raise ValueError(message)

        def _protocol_annotation(
            self, binding: p.Infra.RopePyName | None
        ) -> t.Infra.AstExpression | None:
            """Retain a direct authored protocol identity, including local recursion.

            Returns:
                Its family-bound annotation, or no protocol declaration.

            """
            if binding is None:
                return None
            value = binding.get_object()
            if not self.py_class(value) or not self._owned(binding):
                return None
            protocol_base = self.qualified_name(
                self.project, "Protocol", module_name="typing"
            ).get_object()
            if protocol_base not in self.class_ancestry(value):
                return None
            return self._declared_port(binding, value.get_name())

        def _model_annotation(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            binding: p.Infra.RopePyName | None,
        ) -> t.Infra.AstExpression | None:
            """Select a consumed model dependency or preserve its authored port.

            A model reference whose class another package declares stays that
            package's contract: its mirror belongs to its owner, never to a
            consumer that reaches it through an annotation.

            Returns:
                The projected dependency, or None for a non-model symbol or a
                model declared outside this package.

            Raises:
                ValueError: A selected model has no mirrored local declaration.

            """
            for route, model in self.models.items():
                root, separator, tail = FlextInfraUtilitiesRopeAnalysis.Tree.unparse(
                    node
                ).partition(".")
                future_port = (
                    separator
                    and tail == route
                    and self.same_name(
                        self.facades["p"], self.expression_name(scope, root)
                    )
                )
                if (
                    not future_port
                    and binding is not None
                    and self.same_name(model, binding)
                    and not self._owned(model)
                ):
                    port = self._member(self.facades["p"], route)
                    if port is None:
                        message = (
                            "upstream model dependency has no published protocol: "
                            f"{route}"
                        )
                        raise ValueError(message)
                    return self._declared_port(port, route)
                if future_port or (
                    binding is not None and self.same_name(model, binding)
                ):
                    port = self._member(self.facades["p"], route)
                    owner = port.get_object().get_module() if port is not None else None
                    if (
                        route not in self.references
                        and port is not None
                        and self.source_module(owner)
                        and not owner.source_code.startswith(c.Infra.AUTOGEN_HEADER)
                    ):
                        return self._declared_port(port, route)
                    if route not in self.references:
                        message = (
                            "model dependency has no local mirrored declaration: "
                            f"{route}"
                        )
                        raise ValueError(message)
                    selected = self.canonical_routes[self.references[route]]
                    self.selected.add(selected)
                    self.dependencies.add(selected)
                    return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                        self.references[route]
                    )
            return None

        def _owned(self, model: p.Infra.RopePyName) -> bool:
            """Whether this package's source declares the model class.

            Returns:
                True when the model's declaring resource lies in this package.

            """
            module = model.get_object().get_module()
            resource = module.get_resource() if self.source_module(module) else None
            return (
                resource is not None
                and self.package is not None
                and Path(resource.real_path).is_relative_to(self.package)
            )

        def _declared_port(
            self, binding: p.Infra.RopePyName, route: str
        ) -> t.Infra.AstExpression:
            """Retain an authored contract through its nearest family export.

            Returns:
                The declaring class path without reentering the facade under assembly.

            Raises:
                TypeError: If the authored port has no native source class.
                ValueError: If the authored port has no declaring resource.

            """
            self._require_nonmodel_annotation(binding, route)
            inherited = self._inherited_port(binding, route)
            if inherited is not None:
                return inherited
            value = binding.get_object()
            if not self.py_class(value):
                message = "authored protocol annotation has no native source class"
                raise TypeError(message)
            module = value.get_module()
            resource = module.get_resource()
            if resource is None:
                message = "authored protocol annotation has no declaring resource"
                raise ValueError(message)
            if self.package is None or not Path(resource.real_path).is_relative_to(
                self.package
            ):
                message = (
                    f"inherited protocol has no native public facade owner: {route}"
                )
                raise ValueError(message)
            names = [value.get_name()]
            scope = value.get_scope()
            while scope.parent is not None:
                scope = scope.parent
                if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
                    names.append(scope.pyobject.get_name())
            names.reverse()
            package = (FlextInfraUtilitiesRopeAnalysis.package_name_for_module)(
                module.get_name(), resource
            )
            self.imports[names[0]] = f"from {package} import {names[0]}"
            return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                ".".join(names)
            )

        def _inherited_port(
            self, binding: p.Infra.RopePyName, route: str
        ) -> t.Infra.AstExpression | None:
            """Retain upstream namespaces through their native published p alias.

            Returns:
                The nearest inherited public reference, or no upstream owner.

            """
            facade = FlextInfraUtilitiesRopeRuntime.require_class_object(
                self.facades["p"].get_object(), "protocol facade"
            )
            for native_ancestor in facade.get_mro():
                ancestor = FlextInfraUtilitiesRopeRuntime.require_class_object(
                    native_ancestor, "protocol facade ancestor"
                )
                module = ancestor.get_module()
                if not self.source_module(module):
                    continue
                resource = module.get_resource()
                if resource is None or (
                    self.package is not None
                    and Path(resource.real_path).is_relative_to(self.package)
                ):
                    continue
                exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                    module
                )
                published = module.get_attributes().get("p")
                if (
                    "p" not in exports
                    or published is None
                    or published.get_object() is not ancestor
                ):
                    continue
                member = self._member(published, route)
                if member is None or not self.same_name(member, binding):
                    continue
                provider = module.get_name().rpartition(".")[0]
                alias = f"{provider.replace('.', '_')}_p"
                self.imports[alias] = f"from {provider} import p as {alias}"
                return FlextInfraUtilitiesRopeAnalysis.Tree.parse_expression_source(
                    f"{alias}.{route}"
                )
            return None

        def _imports(self, source: str, scope: p.Infra.RopeScope) -> Mapping[str, str]:
            """Reuse native imports with provider-bound lexical aliases.

            Returns:
                Annotation roots rebound to their exact declaring import providers.

            Raises:
                ValueError: If source or import ownership is absent or competing.

            """
            module = scope.pyobject.get_module()
            if not self.source_module(module):
                message = "model annotation has no authenticated declaring module"
                raise ValueError(message)
            roots = {
                source[begin:end].partition(".")[0]
                for begin, end in (
                    FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(
                        source
                    )
                )
            }
            rebound: dict[str, str] = {}
            for (
                information
            ) in FlextInfraUtilitiesSemanticDeclarationRelocation.native_import_infos(
                self.project, module
            ):
                aliases = tuple(
                    (name, alias)
                    for name, alias in information.names_and_aliases
                    if (alias or name.partition(".")[0]) in roots
                )
                if not aliases:
                    continue
                if isinstance(information, p.Infra.RopeFromImport):
                    provider = self._import_provider(module, information)
                    projected = tuple(
                        (name, f"{provider.replace('.', '_')}_{alias or name}")
                        for name, alias in aliases
                    )
                    rebound.update(
                        (alias or name, projected_alias)
                        for (name, alias), (_name, projected_alias) in zip(
                            aliases, projected, strict=True
                        )
                    )
                    imported = FlextInfraUtilitiesRopeRuntime.from_import(
                        provider, 0, projected
                    )
                else:
                    imported = FlextInfraUtilitiesRopeRuntime.normal_import(aliases)
                    rebound.update(
                        (
                            alias or name.partition(".")[0],
                            alias or name.partition(".")[0],
                        )
                        for name, alias in aliases
                    )
                statement = imported.get_import_statement()
                for name, alias in aliases:
                    root = alias or name.partition(".")[0]
                    receiver = rebound[root]
                    previous = self.imports.setdefault(receiver, statement)
                    if previous != statement:
                        message = f"competing lexical annotation import: {receiver}"
                        raise ValueError(message)
            self._validate_builtins(roots - rebound.keys(), scope)
            return rebound

        def _validate_builtins(
            self,
            roots: set[str],
            scope: p.Infra.RopeScope,
        ) -> None:
            """Require exact native builtin identities for roots without imports.

            Raises:
                ValueError: If an annotation root has no authenticated owner.

            """
            builtins = self.require_semantic_module(
                self.project.get_module("builtins")
            ).get_attributes()
            for root in roots:
                builtin = builtins.get(root)
                if builtin is None or not self.same_name(
                    builtin, self.expression_name(scope, root)
                ):
                    message = f"annotation has no authenticated imported owner: {root}"
                    raise ValueError(message)

        @staticmethod
        def _import_provider(
            module: p.Infra.RopeSourceModule,
            information: p.Infra.RopeFromImport,
        ) -> str:
            """Resolve a relative native import in its declaring package.

            Returns:
                The absolute native import provider.

            Raises:
                ValueError: If the annotation import has no native resource.

            """
            resource = module.get_resource()
            if resource is None:
                message = "annotation import has no native resource"
                raise ValueError(message)
            return FlextInfraUtilitiesRopeAnalysis.resolve_import_module(
                current_package=(
                    FlextInfraUtilitiesRopeAnalysis.package_name_for_module(
                        module.get_name(), resource
                    )
                ),
                module_name=information.module_name,
                level=information.level,
            )

        def _denotes(
            self,
            node: t.Infra.AstExpression,
            scope: p.Infra.RopeScope,
            module: str,
            name: str,
        ) -> bool:
            return self.same_name(
                self.qualified_name(self.project, name, module_name=module),
                self.resolve_symbol(scope, node),
            )

        def _member(
            self, binding: p.Infra.RopePyName, route: str
        ) -> p.Infra.RopePyName | None:
            value = binding.get_object()
            if not self.py_class(value):
                return None
            return self.resolve_symbol(value.get_scope(), route)

        def _source_class(self, binding: p.Infra.RopePyName) -> p.Infra.RopeSourceClass:
            """Require the source capability already proved by model admission.

            Returns:
                The authenticated model declaration, never a loaded target class.

            Raises:
                TypeError: If the model has no authenticated native source class.

            """
            value = binding.get_object()
            if not self.py_class(value):
                message = "model has no authenticated native source class"
                raise TypeError(message)
            return value


__all__: list[str] = ["FlextInfraUtilitiesModelsProtocol"]
