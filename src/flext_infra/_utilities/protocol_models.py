"""Project model data contracts by authenticated declaring source module.

The field renderer retains the existing native engine's expression nodes;
discovery, identity and ancestry remain owned by that engine.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import copy
import importlib
import operator
import re
import textwrap
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import is_protocol, override

from flext_cli import u

from flext_infra import c, config, m, p, r, t
from flext_infra._protocols_bootstrap import (
    consolidate_protocol_owners,
    is_source_bootstrap_owned,
    normalize_protocol_source,
    plan_protocol_facades,
)
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesLazyInitRender,
    FlextInfraUtilitiesLintRecipes,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesSemanticCutover,
    FlextInfraUtilitiesTransformerHeader,
)
from flext_infra._utilities._docs import FlextInfraUtilitiesDocsScopeState
from flext_infra._utilities._git import FlextInfraUtilitiesGitignore
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSource,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities.protected_edit_linting import (
    FlextInfraUtilitiesProtectedEditLinting,
)
from flext_infra._utilities.protocol_contracts import (
    FlextInfraUtilitiesModelsProtocolContracts,
)
from flext_infra._utilities.protocol_retirement import (
    FlextInfraUtilitiesModelsProtocolRetirement,
)
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


@dataclass(frozen=True, slots=True)
class _SourceFieldProjection:
    """One structural field declaration with its protocol mutability."""

    declaration: ast.AnnAssign
    read_only: bool
    description: str | None = None


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
        *,
        domain_owner: p.Infra.SourceClassReference | None = None,
        package_name: str | None = None,
    ) -> p.Result[Mapping[Path, str]]:
        """Plan protocol mirrors directly from an overlaid source project.

        This public bootstrap entry intentionally does not construct a Rope
        workspace. Its source view can therefore inventory Pydantic declarations
        whose annotations reference protocol facade members not generated yet.
        ``domain_owner`` limits repair to an existing public domain composition;
        omitting it retains complete inventory and collision validation.
        ``package_name`` binds the projection to one declared package layout;
        omitting it projects the primary distribution package.

        Returns:
            Relative protocol mirror sources, or the source inventory failure.

        """
        projection = cls._ModelProtocolProjection(
            repository_root, source_project, package_name=package_name
        )
        return (
            projection.domain_sources(domain_owner)
            if domain_owner is not None
            else projection.sources()
        )

    @classmethod
    def bootstrap_protocol_model_sources(
        cls, repository_root: Path, *, ports: p.Infra.CodegenConformPorts
    ) -> p.Result[bool]:
        """Publish bootstrap sources for every declared package owning models.

        Declared repository namespace packages precede the primary package,
        whose models may annotate their protocols.

        Returns:
            Whether any authenticated, normalized candidate changed live sources.

        """
        root = repository_root.expanduser().resolve()
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            root
        ) as binding:
            projection = cls._ModelProtocolProjection(root, binding[0])
            primary = projection._source_layout()
            packages = (
                *(
                    (layout[2], True)
                    for layout in projection._namespace_source_layouts()
                ),
                *(() if primary is None else ((primary[2], False),)),
            )
        changed = False
        for package_name, namespace_package in packages:
            published = cls._bootstrap_package_protocol_model_sources(
                root,
                ports=ports,
                package_name=package_name,
                namespace_package=namespace_package,
            )
            if published.failure:
                return published
            changed = published.value or changed
        return r[bool].ok(value=changed)

    @classmethod
    def _bootstrap_package_protocol_model_sources(
        cls,
        root: Path,
        *,
        ports: p.Infra.CodegenConformPorts,
        package_name: str,
        namespace_package: bool,
    ) -> p.Result[bool]:
        """Publish one package's bootstrap sources after the staged admission gate.

        A declared namespace package owning models receives its first protocol
        sources even before its ``_protocols`` directory exists; the primary
        package opts in by declaring that directory.

        Returns:
            Whether the authenticated, normalized candidate changed live sources.

        """
        with FlextInfraUtilitiesWorkspaceSnapshot.facade_source_project(
            root
        ) as binding:
            project = binding[0]
            projection = cls._ModelProtocolProjection(
                root, project, package_name=package_name
            )
            layout = projection._source_layout()
            if layout is None:
                return r[bool].ok(value=False)
            package, _stem, package_name = layout
            protocol_root = package / "_protocols"
            protocols_declared = project.source_query(protocol_root, "isdir")
            if not namespace_package and not protocols_declared:
                return r[bool].ok(value=False)
            originals = {
                directory / name: project.source_state(directory / name)
                for directory, _children, files in (
                    project.source_walk(protocol_root) if protocols_declared else ()
                )
                for name in files
                if name.endswith(c.Infra.EXT_PYTHON)
            }
            normalized = {
                path: normalize_protocol_source(
                    project.source_text(path),
                    package_name=package_name,
                    filename=str(path),
                )
                for path in originals
            }
            declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                root, (), normalized, source_project=project
            )
            with project.source_view(
                declared_files=declared, additional_source_folders=None
            ):
                planned = cls.protocol_model_sources_from_source(
                    root, project, package_name=package_name
                )
            if planned.failure:
                return r[bool].from_failure(planned)
            updates = {
                **normalized,
                **{root / path: text for path, text in planned.value.items()},
            }
            for path in updates:
                if path not in originals:
                    originals[path] = project.source_state(path, required=False)
            inputs = dict(originals)
            for directory, _children, files in project.source_walk(package / "_models"):
                for name in files:
                    if name.endswith(c.Infra.EXT_PYTHON):
                        path = directory / name
                        inputs[path] = project.source_state(path)
            manifest = root / c.PYPROJECT_FILENAME
            for path in (manifest, package / "models.py", Path(__file__).resolve()):
                inputs[path] = project.source_state(path)
            members = [
                (
                    cls._ModelProtocolProjection.module_name_for(relative),
                    holder.name,
                    tuple(
                        node.name
                        for node in holder.body
                        if isinstance(node, ast.ClassDef)
                    ),
                )
                for relative, text in planned.value.items()
                for holder in ast.parse(text).body
                if isinstance(holder, ast.ClassDef)
            ]

            def admit(
                candidate: Path, paths: Mapping[Path, Path]
            ) -> p.Result[
                tuple[tuple[p.Infra.CodegenFilePlan, ...], tuple[p.Cli.FileChange, ...]]
            ]:
                target = paths[manifest].parent
                consolidate_protocol_owners(target, planned.value)
                # Only the source-bootstrap protocol owner (flext-infra's own
                # family) republishes its bootstrap facade; consumers carry the
                # generated lazy init instead.
                bootstrap_init = (
                    target / package.relative_to(root) / "_protocols" / "__init__.py"
                )
                exported = (
                    cls._publish_bootstrap_protocol_facades(target, members)
                    if bootstrap_init.is_file()
                    and is_source_bootstrap_owned(bootstrap_init)
                    else r[bool].ok(value=False)
                )
                if exported.failure:
                    return r[
                        tuple[
                            tuple[p.Infra.CodegenFilePlan, ...],
                            tuple[p.Cli.FileChange, ...],
                        ]
                    ].from_failure(exported)
                plans = tuple(
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=path,
                        before=before,
                        desired_content=(target / path.relative_to(root)).read_bytes(),
                        desired_mode=before.mode
                        if before.mode is not None
                        else config.Infra.codegen.modes.file_default,
                        inputs=tuple(inputs.values()),
                    )
                    for path, before in originals.items()
                )
                repaired = ports.file_publisher.normalized_codegen_changes(plans)
                if repaired.failure:
                    return r[
                        tuple[
                            tuple[p.Infra.CodegenFilePlan, ...],
                            tuple[p.Cli.FileChange, ...],
                        ]
                    ].from_failure(repaired)
                for change in repaired.value:
                    destination = target / change.path.relative_to(root)
                    if change.desired_content is None:
                        destination.unlink()
                    else:
                        destination.write_bytes(change.desired_content)
                validated = ports.candidate_validator(root, candidate, (root,))
                if validated.failure:
                    return r[
                        tuple[
                            tuple[p.Infra.CodegenFilePlan, ...],
                            tuple[p.Cli.FileChange, ...],
                        ]
                    ].from_failure(validated)
                if not validated.value:
                    return r[
                        tuple[
                            tuple[p.Infra.CodegenFilePlan, ...],
                            tuple[p.Cli.FileChange, ...],
                        ]
                    ].fail("bootstrap candidate admission returned no acceptance")
                return r[
                    tuple[
                        tuple[p.Infra.CodegenFilePlan, ...],
                        tuple[p.Cli.FileChange, ...],
                    ]
                ].ok((plans, repaired.value))

            preview = ports.source_preview.preview_sources(
                root,
                {manifest: project.source_text(manifest), **updates},
                admit,
                options=m.Infra.StageSourceOptions(inputs=tuple(inputs.values())),
            ).flat_map(lambda outcome: outcome)
            if preview.failure:
                return r[bool].from_failure(preview)
            plans, changes = preview.value
            published = ports.file_publisher.publish_normalized_codegen_plans(
                root, plans, changes
            )
            if published.failure:
                return r[bool].from_failure(published)
            cls._install_bootstrap_facade_members(members, root)
            return r[bool].ok(value=bool(published.value))

    @classmethod
    def _publish_bootstrap_protocol_facades(
        cls,
        repository_root: Path,
        members: list[tuple[str, str, tuple[str, ...]]],
    ) -> p.Result[bool]:
        """Materialize the canonical facade plan in the staged source candidate.

        Returns:
            Whether composing the candidate changed a facade source.

        The public generation transaction owns the later guarded publication.
        This nested source-preview callback only materializes its admitted
        candidate so its validation sees the canonical facade MRO.

        """
        changed = False
        for path, source in plan_protocol_facades(repository_root).items():
            if source.startswith("# AUTO-GENERATED FILE"):
                source = c.Infra.AUTOGEN_HEADER + "\n" + source.partition("\n")[2]
            if not path.is_file() or path.read_text(encoding="utf-8") != source:
                path.write_text(source, encoding="utf-8")
                changed = True
        return r.ok(value=changed)

    @staticmethod
    def _install_bootstrap_facade_members(
        members: list[tuple[str, str, tuple[str, ...]]], repository_root: Path
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
        facade_module = importlib.import_module(f"{package_name}.protocols")
        package_stem = u.derive_class_stem(package_name.replace("_", "-"))
        family = package_stem.removeprefix("Flext")
        # flext-core is the root facade: source contracts belong on ``p`` itself,
        # not on a synthetic ``p.Core`` namespace.
        facade = (
            facade_module.p
            if package_name == "flext_core"
            else getattr(facade_module.p, family, None)
        )
        holder_prefix = f"{package_stem}Protocols"
        if not isinstance(facade, type):
            return
        for module_name, holder_name, names in members:
            if not module_name.startswith(
                f"{package_name}._protocols."
            ) or not holder_name.startswith(holder_prefix):
                continue
            module = importlib.import_module(module_name)
            holder = vars(module).get(holder_name)
            if not isinstance(holder, type) or holder.__module__ != module_name:
                continue
            for name in names:
                member = vars(holder).get(name)
                if isinstance(member, type):
                    setattr(facade, name, member)

    class _ModelProtocolProjection(
        FlextInfraUtilitiesSemanticCutover,
        FlextInfraUtilitiesModelsProtocolContracts,
    ):
        """Bind declaring-module projection to one native source candidate."""

        def __init__(
            self,
            repository_root: Path,
            source_project: p.Infra.RopeProject,
            *,
            workspace: p.Infra.RopeWorkspaceDsl | None = None,
            package_name: str | None = None,
        ) -> None:
            self.repository_root = repository_root
            self.project = source_project
            self._workspace = workspace
            self._bound_package_name = package_name
            self._documentation_language: t.Infra.DocumentationLanguage | None = None
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
            self.source_package_name = ""
            self.source_model_protocols: dict[str, str] = {}
            self.source_field_cache: dict[str, tuple[_SourceFieldProjection, ...]] = {}
            self.source_model_protocol_routes: dict[str, str] = {}
            self.source_protocol_retirements: dict[
                Path, tuple[tuple[str, str], ...]
            ] = {}
            self.source_protocol_rewrites: dict[
                Path, tuple[m.Infra.SourceRewrite, ...]
            ] = {}
            self.source_model_aliases: dict[
                str,
                tuple[Path, ast.TypeAlias, ast.Module, ast.ClassDef],
            ] = {}
            self.source_model_facade_protocols: dict[str, str] = {}
            self.source_model_facade_import_roots: frozenset[str] = frozenset()
            self.source_model_facade_model_routes: dict[str, str] = {}
            self.source_model_frozen: dict[str, bool] = {}
            self.source_model_root_annotations: dict[str, ast.expr] = {}
            self.source_model_package_exports: dict[tuple[str, str], str] = {}
            self.source_module_names: dict[int, str] = {}
            self.source_family_classes: dict[str, tuple[str, str, bool]] = {}
            self.source_copy_facade: tuple[str, str] | None = None
            self.source_copy_siblings: dict[str, str] = {}
            self.source_method_cache: dict[
                str, tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]
            ] = {}

        @property
        def workspace(self) -> p.Infra.RopeWorkspaceDsl:
            """Return the semantic workspace required by the full projector.

            Raises:
                RuntimeError: The source-only bootstrap has no Rope workspace.

            """
            if self._workspace is None:
                message = "semantic protocol projection requires a Rope workspace"
                raise RuntimeError(message)
            return self._workspace

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """The owning project's authenticated generated documentation language."""
            if self._documentation_language is None:
                declaration = FlextInfraUtilitiesProjectManagedArtifacts.load_repository_declaration_inputs(
                    self.repository_root, source_project=self.project
                ).unwrap()
                project = declaration.spec.project
                self._documentation_language = (
                    project.documentation_language
                    if project is not None
                    else FlextInfraUtilitiesDocsScopeState.docs_documentation_language({
                        "documentation_language": m.Infra.ProjectSpec.model_fields[
                            "documentation_language"
                        ].get_default(),
                    })
                )
            return self._documentation_language

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

        def domain_sources(
            self, reference: p.Infra.SourceClassReference
        ) -> p.Result[Mapping[Path, str]]:
            """Project one declared domain composition without electing other owners.

            The selection names a native source holder already composed by both
            public facades. Its part contracts remain authenticated inputs; a
            complete projection still validates every model and collision.

            Returns:
                The selected canonical sibling protocol source.

            Raises:
                ValueError: The reference is not one public local domain owner.

            """
            layout = self._source_layout()
            if layout is None or len(reference.attributes) != 1:
                message = "domain projection requires one declared holder"
                raise ValueError(message)
            package_dir, class_stem, package_name = layout
            self.package = package_dir
            self.package_name = package_name
            self.class_stem = class_stem
            owner = self._source_class(
                self.qualified_name(
                    self.project,
                    reference.attributes[0],
                    module_name=reference.target,
                )
            )
            qualified = ".".join((reference.target, *reference.attributes))
            if ".".join(self._source_class_identity(owner)) != qualified or (
                reference.qualified_base and reference.qualified_base != qualified
            ):
                message = "domain projection reference has another owner"
                raise ValueError(message)
            facade = (
                self.project
                .get_module(f"{package_name}.models")
                .get_attribute("m")
                .get_object()
            )
            if not self._source_facade_composes(facade, owner):
                message = "domain owner is not composed by its model facade"
                raise ValueError(message)
            rendered = self._source_domain_facade_protocols(
                package_dir, package_name, {}, selected_owner=owner
            )
            if len(rendered) != 1:
                message = "domain owner has no unique protocol sibling"
                raise ValueError(message)
            relative, content = next(iter(rendered.items()))
            declarations = [
                node.name
                for node in ast.parse(content).body
                if isinstance(node, ast.ClassDef)
            ]
            if len(declarations) != 1:
                message = "domain protocol has no unique declared holder"
                raise ValueError(message)
            owner = self._source_class(
                self.project.get_module(self.module_name_for(relative)).get_attribute(
                    declarations[0]
                )
            )
            facade = (
                self.project
                .get_module(f"{package_name}.protocols")
                .get_attribute("p")
                .get_object()
            )
            if not self._source_facade_composes(facade, owner):
                message = "domain holder is not composed by its protocol facade"
                raise ValueError(message)
            return r[Mapping[Path, str]].ok(rendered)

        def _source_facade_composes(
            self,
            facade: p.Infra.RopePyObject,
            owner: p.Infra.RopeSourceClass,
        ) -> bool:
            """Prove a holder through native MRO and declared facade namespaces.

            Returns:
                Whether a public facade composition reaches the selected holder.

            """
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            pending = [facade]
            visited: set[str] = set()
            while pending:
                current = pending.pop()
                if not self.py_class(current):
                    continue
                identity = FlextInfraUtilitiesRopeRuntime.native_object_identity(
                    current
                )
                if identity in visited:
                    continue
                visited.add(identity)
                if owner in current.get_mro():
                    return True
                pending.extend(
                    value
                    for binding in current.get_attributes().values()
                    if self.py_class(value := binding.get_object())
                    and model_base not in value.get_mro()
                )
            return False

        def _source_class_identity(
            self, value: p.Infra.RopeSourceClass
        ) -> tuple[str, str]:
            """Retain native qualnames under the declaring module's elected identity.

            Returns:
                The authenticated module import path and native class scope path.

            Raises:
                ValueError: The native declaration has no qualified scope path.

            """
            identity = FlextInfraUtilitiesRopeRuntime.native_object_identity(value)
            _module, separator, declaration = identity.partition("::")
            if not separator or not declaration:
                message = "source class has no native declaration identity"
                raise ValueError(message)
            return (
                FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    value.get_module(), source_project=self.project
                ),
                declaration,
            )

        def _source_model_sources(self) -> p.Result[Mapping[Path, str]]:
            """Project local Pydantic declarations using only the source view.

            The source inventory deliberately does not consult ``m`` or ``p``.
            Those facades are consumers of this projection and may be incomplete
            during bootstrap.

            Returns:
                Same-path protocol mirror sources derived from local model files.

            """
            self.source_field_cache.clear()
            result_type = r[Mapping[Path, str]]
            layout = self._source_layout()
            if layout is None:
                return result_type.ok({})
            package_dir, class_stem, package_name = layout
            self.package = package_dir
            self.package_name = package_name
            self.class_stem = class_stem
            self.source_package_name = package_name
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
                    model_module = ".".join((
                        package_name,
                        "_models",
                        *source_path.relative_to(models_root).with_suffix("").parts,
                    ))
                    self.source_module_names[id(tree)] = model_module
                    classes = self._source_model_classes(tree, model_module)
                    if not classes:
                        continue
                    destination = (
                        package_dir
                        / "_protocols"
                        / source_path.relative_to(models_root)
                    )
                    grouped[destination] = [(*entry, tree) for entry in classes]
            self._source_index_model_protocols(package_dir, package_name, grouped)
            conformance = self._source_model_conformance_source(
                package_dir, package_name, grouped
            )
            grouped = self._source_owned_model_protocols(grouped)
            rendered: dict[Path, str] = {}
            for destination, classes in sorted(grouped.items()):
                owner = self._source_generated_holder(destination)
                content = self._source_render_module(
                    destination, owner, classes, package_name
                )
                normalized = (
                    FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                        destination,
                        normalize_protocol_source(
                            content,
                            package_name=package_name,
                            filename=str(destination),
                        ),
                    ).unwrap()
                )
                self._source_validate_generated_module(normalized, destination, owner)
                rendered[destination.relative_to(self.repository_root)] = normalized
            rendered.update(
                self._source_domain_facade_protocols(
                    package_dir, package_name, rendered
                )
            )
            facade = self._source_protocol_aggregate(package_dir, class_stem, rendered)
            if facade is not None:
                rendered[
                    (package_dir / "protocols.py").relative_to(self.repository_root)
                ] = facade
            # Uses that named a displaced Protocol move to its facade route in
            # the same candidate, before the declaration itself retires.
            # Inside the package's own protocol family the own letter is
            # forbidden: a use moves to the generated holder class, imported
            # through its family package; elsewhere it moves to the facade route.
            family_root = (package_dir / "_protocols").resolve()
            for site, rewrites in self.source_protocol_rewrites.items():
                relative = site.relative_to(self.repository_root.resolve())
                original = rendered.get(relative, self.project.source_text(site))
                planned_rewrites = list(rewrites)
                family_imports: list[tuple[str, str]] = []
                if site.is_relative_to(family_root):
                    planned_rewrites = []
                    for rewrite in rewrites:
                        planned = self._source_planned_protocol(rewrite.text)
                        if planned is None:
                            message = (
                                "retired Protocol route has no planned holder: "
                                f"{rewrite.text} at {site}"
                            )
                            raise ValueError(message)
                        _member, holder, module = planned
                        planned_rewrites.append(
                            rewrite.model_copy(
                                update={
                                    "text": ".".join((
                                        holder,
                                        rewrite.text.rpartition(".")[2],
                                    ))
                                }
                            )
                        )
                        family_imports.append((module.rpartition(".")[0], holder))
                if relative in rendered:
                    # The module was already rendered by this candidate, so the
                    # native offsets no longer apply: each original qualified
                    # expression is replaced as a whole token instead.
                    disk = self.project.source_text(site)
                    source = original
                    for rewrite in planned_rewrites:
                        source = re.sub(
                            rf"(?<![\w.]){re.escape(disk[rewrite.start : rewrite.end])}"
                            r"(?![\w])",
                            rewrite.text,
                            source,
                        )
                else:
                    source = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                        resource=FlextInfraUtilitiesModelsProtocolRetirement.file_resource(
                            self.project, site
                        ),
                        source=original,
                        rewrites=planned_rewrites,
                    ).new_contents
                for family, holder in dict.fromkeys(family_imports):
                    source = FlextInfraUtilitiesTransformerHeader.ensure_alias_import(
                        source, family, holder
                    )
                normalized = (
                    FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                        self.repository_root / relative, source
                    ).unwrap()
                )
                rendered[relative] = self._source_wrap_overflowing_spellings(
                    self.repository_root / relative,
                    normalized,
                    tuple(rewrite.text for rewrite in planned_rewrites),
                )
            # Displaced authored Protocols retire in the candidate that composes
            # their projected owners, so no public route is ever unbound.
            for (
                relative,
                source,
            ) in FlextInfraUtilitiesModelsProtocolRetirement.retired_sources(
                self.project,
                self.repository_root,
                self.source_protocol_retirements,
                rendered,
            ).items():
                rendered[relative] = (
                    FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                        self.repository_root / relative, source
                    ).unwrap()
                )
            for relative, source in rendered.items():
                self._source_validate_generated_module(
                    source,
                    self.repository_root / relative,
                    relative.with_suffix("").name,
                )
            if conformance is not None:
                path, source = conformance
                rendered[path.relative_to(self.repository_root)] = source
            return result_type.ok(rendered)

        def _source_model_conformance_source(
            self,
            package_dir: Path,
            package_name: str,
            grouped: Mapping[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ],
        ) -> tuple[Path, str] | None:
            """Render constructor-to-port assignments for the mandatory candidate checker.

            Returns:
                The candidate's structural evidence source, or no public model pairs.

            """
            public = {
                source: route
                for route, source in self.source_model_facade_model_routes.items()
            }
            checks: list[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = []
            imports: list[str] = []
            for classes in grouped.values():
                imports.extend(self.source_annotation_imports(classes, package_name))
                for node, path, tree in classes:
                    identity = ".".join((self.source_module_names[id(tree)], *path))
                    model, port = (
                        public.get(identity),
                        self.source_model_protocol_routes.get(identity),
                    )
                    # A private model is no public facade member: its witness
                    # would read a private name across the facade boundary.
                    if (
                        model is None
                        or port is None
                        or any(part.startswith("_") for part in path)
                    ):
                        continue
                    parameters = []
                    for original in node.type_params:
                        parameter = copy.deepcopy(original)
                        for name in ("bound", "default_value"):
                            value = getattr(parameter, name, None)
                            if isinstance(value, ast.expr):
                                setattr(
                                    parameter,
                                    name,
                                    self._source_structural_annotation(
                                        value, tree, node, classes
                                    ),
                                )
                        parameters.append(ast.unparse(parameter))
                    arguments = tuple(
                        ("*" if isinstance(parameter, ast.TypeVarTuple) else "")
                        + parameter.name
                        for parameter in node.type_params
                    )
                    checks.append((model, port, tuple(parameters), arguments))
            imports = [
                ast.unparse(
                    ast.ImportFrom(module=node.module, names=names, level=node.level)
                )
                if isinstance(node, ast.ImportFrom)
                else ast.unparse(ast.Import(names=names))
                for statement in imports
                for node in ast.walk(ast.parse(statement))
                if isinstance(node, ast.Import | ast.ImportFrom)
                for names in (
                    [
                        alias
                        for alias in node.names
                        if (alias.asname or alias.name) not in {"m", "p"}
                    ],
                )
                if names
            ]
            path = (
                package_dir / "_protocols" / c.Infra.MODEL_PROTOCOL_CONFORMANCE_FILENAME
            )
            context = m.Infra.ModelProtocolConformanceRenderContext(
                header=c.Infra.AUTOGEN_HEADER,
                documentation_language=self.documentation_language,
                copyright_notice=FlextInfraUtilitiesLintRecipes.copyright_notice(
                    package_dir, module=path, source_project=self.project
                ),
                package_name=package_name,
                imports=tuple(dict.fromkeys(imports)),
                checks=tuple(sorted(checks)),
            )
            template = (
                FlextInfraUtilitiesGitignore.codegen_templates_root(
                    config.Infra.codegen
                )
                / c.Infra.TEMPLATE_MODEL_PROTOCOL_CONFORMANCE
            )
            source = u.Cli.template_render(template, context).unwrap()
            return path, FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                path, source
            ).unwrap()

        def _source_domain_facade_protocols(
            self,
            package_dir: Path,
            package_name: str,
            rendered: Mapping[Path, str],
            *,
            selected_owner: p.Infra.RopeSourceClass | None = None,
        ) -> dict[Path, str]:
            """Derive missing sibling holders from authenticated model compositions.

            Returns:
                Canonical protocol composition modules for private model domains.

            Raises:
                ValueError: If a model owner, base or Protocol counterpart is
                    ambiguous or absent.

            """
            models_root = package_dir / "_models"
            protocols_root = package_dir / "_protocols"
            model_module = self.project.get_module(f"{package_name}.models")
            protocol_module = self.project.get_module(f"{package_name}.protocols")
            model_facade = model_module.get_attribute("m").get_object()
            protocol_facade = protocol_module.get_attribute("p").get_object()
            model_prefix = model_facade.get_name()
            protocol_prefix = protocol_facade.get_name()
            family = model_prefix.removesuffix("Models").removeprefix("Flext")
            public_roots = [model_facade]
            if family:
                nested = model_facade.get_attributes().get(family)
                if nested is not None and self._source_model_facade_namespace(
                    nested.get_object()
                ) == (family,):
                    public_roots.append(self._source_class(nested))
            identity = FlextInfraUtilitiesRopeRuntime.native_object_identity
            public_ancestry = {
                identity(ancestor)
                for public in public_roots
                for ancestor in public.get_mro()
            }
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            template = (
                FlextInfraUtilitiesGitignore.codegen_templates_root(
                    config.Infra.codegen
                )
                / c.Infra.TEMPLATE_MODEL_PROTOCOL
            )
            result: dict[Path, str] = {}
            for model_domain, _children, _files in self.project.source_walk(
                models_root
            ):
                directory = protocols_root / model_domain.relative_to(models_root)
                if not directory.name.startswith("_"):
                    continue
                domain_name = directory.name.removeprefix("_")
                relative_domain = directory.relative_to(protocols_root)
                if not self.project.source_query(
                    model_domain / c.Infra.INIT_PY, "isfile"
                ):
                    continue
                protocol_sibling = directory.parent / f"{domain_name}.py"
                protocol_sibling_relative = protocol_sibling.relative_to(
                    self.repository_root
                )
                model_sibling = (
                    models_root / relative_domain.parent / f"{domain_name}.py"
                )
                in_place = not self.project.source_query(model_sibling, "isfile")
                if in_place:
                    # An owner declared inside `_x` itself (facade law) is the
                    # domain's single exported `...Models` class composing parts
                    # of the same domain; its mirror lives beside it.
                    located = self._source_in_place_model_owner(
                        model_domain, package_dir, package_name
                    )
                    if located is None:
                        continue
                    model_sibling = located
                    protocol_sibling = protocols_root / model_sibling.relative_to(
                        models_root
                    )
                    protocol_sibling_relative = protocol_sibling.relative_to(
                        self.repository_root
                    )
                if selected_owner is not None:
                    resource = selected_owner.get_module().get_resource()
                    if (
                        resource is None
                        or Path(resource.real_path).resolve() != model_sibling.resolve()
                    ):
                        continue
                module_name = ".".join((
                    package_name,
                    "_models",
                    *model_sibling.relative_to(models_root).with_suffix("").parts,
                ))
                source_module = self.project.get_module(module_name)
                source = self.project.source_text(model_sibling)
                tree = ast.parse(source, filename=str(model_sibling))
                owners: list[tuple[ast.ClassDef, p.Infra.RopeSourceClass]] = []
                for declaration in tree.body:
                    if not isinstance(declaration, ast.ClassDef) or not (
                        declaration.name.endswith("Models")
                        if in_place
                        else declaration.name.startswith(model_prefix)
                    ):
                        continue
                    binding = source_module.get_attribute(declaration.name)
                    if declaration.name not in (
                        FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                            source_module
                        )
                    ):
                        continue
                    owner = self._source_class(binding)
                    resource = owner.get_module().get_resource()
                    if (
                        resource is None
                        or Path(resource.real_path).resolve() != model_sibling.resolve()
                    ):
                        msg = f"model domain owner has conflicting source identity: {model_sibling}:{declaration.name}"
                        raise ValueError(msg)
                    if (
                        model_base in owner.get_mro()
                        and identity(owner) not in public_ancestry
                    ):
                        continue
                    owners.append((declaration, owner))
                if len(owners) > 1:
                    msg = f"model domain has competing public compositions: {model_sibling}"
                    raise ValueError(msg)
                if not owners:
                    continue
                declaration, owner = owners[0]
                if selected_owner is not None and owner is not selected_owner:
                    message = "domain selection differs from its declared owner"
                    raise ValueError(message)
                # A canonical namespace owner (no bases, one nested class) wraps
                # its composing domain class, possibly through several levels;
                # identity and composition are read from the innermost one.
                while True:
                    nested_owners = [
                        statement
                        for statement in declaration.body
                        if isinstance(statement, ast.ClassDef)
                    ]
                    if declaration.bases or len(nested_owners) != 1:
                        break
                    declaration = nested_owners[0]
                    owner = self._source_class(owner.get_attribute(declaration.name))
                if in_place:
                    protocol_owner = (
                        declaration.name.removesuffix("Models") + "Protocols"
                    )
                else:
                    protocol_owner = ""
                suffix = declaration.name.removeprefix(model_prefix)
                expected_suffix = "".join(
                    u.derive_class_stem(part.strip("_"))
                    for part in model_sibling
                    .relative_to(models_root)
                    .with_suffix("")
                    .parts
                )
                if not in_place and (not suffix or expected_suffix != suffix):
                    msg = f"model domain owner does not match its declared path: {model_sibling}"
                    raise ValueError(msg)
                protocol_owner = protocol_owner or f"{protocol_prefix}{suffix}"
                # A canonical namespace owner wraps its single composing domain
                # class; the composition is read from that nested declaration.
                nested = [
                    statement
                    for statement in declaration.body
                    if isinstance(statement, ast.ClassDef)
                ]
                if not declaration.bases and len(nested) == 1 and nested[0].bases:
                    declaration = nested[0]
                    owner = self._source_class(owner.get_attribute(declaration.name))
                bases: list[str] = []
                imports = ["from __future__ import annotations"]
                # A part chain (OperationErrors -> ServiceErrors -> Base) is
                # composed whole: every part class in the native ancestry of a
                # direct base is projected, in MRO order, once.
                part_classes: list[p.Infra.RopePyObject] = []
                for expression in declaration.bases:
                    binding = self.resolve_symbol(owner.get_scope(), expression)
                    if binding is None or not self.py_class(binding.get_object()):
                        msg = f"model domain base has no native class binding: {model_sibling}:{ast.unparse(expression)}"
                        raise ValueError(msg)
                    for ancestor in binding.get_object().get_mro():
                        ancestor_module = ancestor.get_module()
                        ancestor_resource = (
                            ancestor_module.get_resource()
                            if ancestor_module is not None
                            else None
                        )
                        if (
                            ancestor in part_classes
                            or ancestor_resource is None
                            or not Path(ancestor_resource.real_path)
                            .resolve()
                            .is_relative_to(models_root.resolve())
                        ):
                            continue
                        part_classes.append(ancestor)
                for model_base_class in part_classes:
                    base_declaration = model_base_class.get_ast()
                    if (
                        isinstance(base_declaration, ast.ClassDef)
                        and not base_declaration.bases
                        and all(
                            isinstance(statement, ast.Pass)
                            or (
                                isinstance(statement, ast.Expr)
                                and isinstance(statement.value, ast.Constant)
                                and isinstance(statement.value.value, str)
                            )
                            for statement in base_declaration.body
                        )
                    ):
                        continue
                    base_module = model_base_class.get_module()
                    resource = (
                        base_module.get_resource() if base_module is not None else None
                    )
                    if resource is None:
                        msg = f"model domain base has no source module: {model_base_class.get_name()}"
                        raise ValueError(msg)
                    base_path = Path(resource.real_path).resolve()
                    if not base_path.is_relative_to(models_root.resolve()):
                        msg = f"model domain base is outside its owning package: {base_path}"
                        raise ValueError(msg)
                    protocol_path = protocols_root / base_path.relative_to(
                        models_root.resolve()
                    )
                    protocol_relative = protocol_path.relative_to(self.repository_root)
                    protocol_source = rendered.get(protocol_relative)
                    if protocol_source is None:
                        if not self.project.source_query(protocol_path, "isfile"):
                            # Every model part is projected: a part without a
                            # protocol module declares no model to compose.
                            continue
                        protocol_source = self.project.source_text(protocol_path)
                    protocol_tree = ast.parse(
                        protocol_source, filename=str(protocol_path)
                    )
                    exported = (
                        FlextInfraUtilitiesRopeAnalysis.public_export_names_source(
                            FlextInfraUtilitiesRopeRuntime.build_string_module(
                                self.project, protocol_source
                            )
                        )
                    )
                    holders = [
                        statement.name
                        for statement in protocol_tree.body
                        if isinstance(statement, ast.ClassDef)
                        and statement.name in exported
                    ]
                    if len(holders) != 1:
                        msg = f"protocol part has no unique exported holder: {protocol_path}"
                        raise ValueError(msg)
                    protocol_base = holders[0]
                    if not any(
                        isinstance(statement, ast.ClassDef)
                        and statement.name == protocol_base
                        for statement in protocol_tree.body
                    ):
                        msg = f"protocol part export is not a class declaration: {protocol_path}:{protocol_base}"
                        raise ValueError(msg)
                    # A composing module imports a part holder through the part's
                    # family package, whose generated lazy exports publish it.
                    module = ".".join((
                        package_name,
                        "_protocols",
                        *protocol_path.relative_to(protocols_root).parent.parts,
                    ))
                    imports.append(f"from {module} import {protocol_base}")
                    bases.append(protocol_base)
                if not bases:
                    msg = f"model domain owner has no part composition: {model_sibling}"
                    raise ValueError(msg)
                context = m.Infra.ModelProtocolRenderContext(
                    header=c.Infra.AUTOGEN_HEADER,
                    documentation_language=self.documentation_language,
                    copyright_notice=FlextInfraUtilitiesLintRecipes.copyright_notice(
                        package_dir,
                        module=protocol_sibling,
                        source_project=self.project,
                    ),
                    imports=tuple(dict.fromkeys(imports)),
                    sibling_import_lines=(),
                    owner=protocol_owner,
                    bases=tuple(bases),
                    contracts=(),
                )
                existing = rendered.get(protocol_sibling_relative)
                if existing is None and self.project.source_query(
                    protocol_sibling, "isfile"
                ):
                    existing = self.project.source_text(protocol_sibling)
                source = (
                    self._source_compose_protocol_holder(
                        existing,
                        protocol_owner,
                        dict(zip(bases, imports[1:], strict=True)),
                    )
                    if existing is not None
                    else u.Cli.template_render(template, context).unwrap()
                )
                result[protocol_sibling_relative] = (
                    FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                        protocol_sibling,
                        normalize_protocol_source(
                            source,
                            package_name=package_name,
                            filename=str(protocol_sibling),
                        ),
                    ).unwrap()
                )
            return result

        def _source_in_place_model_owner(
            self, model_domain: Path, package_dir: Path, package_name: str
        ) -> Path | None:
            """Locate the in-domain module of the owner the model facade composes.

            The concrete decides: the domain has an in-place owner only when the
            package's ``models.py`` imports exactly one class from the domain,
            and that class's module lies inside the domain directory.

            Returns:
                The owner module path, or None when the facade composes the
                domain's parts directly (no owner).

            """
            domain = ".".join((
                package_name,
                *model_domain.relative_to(package_dir).parts,
            ))
            facade = package_dir / f"models{c.Infra.EXT_PYTHON}"
            tree = ast.parse(self.project.source_text(facade), filename=str(facade))
            imported = [
                (statement.module, alias.name)
                for statement in tree.body
                if isinstance(statement, ast.ImportFrom)
                and statement.module is not None
                and (
                    statement.module == domain
                    or statement.module.startswith(f"{domain}.")
                )
                for alias in statement.names
            ]
            if len(imported) != 1:
                return None
            module, _name = imported[0]
            if module == domain:
                return None
            owner = (
                model_domain
                / f"{module.removeprefix(f'{domain}.')}{c.Infra.EXT_PYTHON}"
            )
            return owner if self.project.source_query(owner, "isfile") else None

        @staticmethod
        def _source_compose_protocol_holder(
            source: str,
            owner: str,
            imports: Mapping[str, str],
            *,
            bases: Sequence[str] | None = None,
        ) -> str:
            """Compose native part holders while retaining all declared member bodies.

            Returns:
                Source with ordered native bases and authenticated runtime imports.

            Raises:
                ValueError: The holder or its source extent is ambiguous.

            """
            holders = [
                node
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.ClassDef) and node.name == owner
            ]
            if len(holders) != 1:
                msg = f"protocol composition has no unique holder: {owner}"
                raise ValueError(msg)
            holder = holders[0]
            occupied = [ast.unparse(base) for base in holder.bases]
            composed = (
                list(bases)
                if bases is not None
                else [*imports, *(name for name in occupied if name not in imports)]
            )
            if occupied != composed:
                lines = source.splitlines(keepends=True)
                offset = sum(map(len, lines[: holder.lineno - 1])) + holder.col_offset
                name_end = offset + len("class ") + len(holder.name)
                if holder.type_params:
                    parameter = holder.type_params[-1]
                    if parameter.end_lineno is None or parameter.end_col_offset is None:
                        msg = f"protocol type parameters have no source extent: {owner}"
                        raise ValueError(msg)
                    parameter_end = (
                        sum(map(len, lines[: parameter.end_lineno - 1]))
                        + parameter.end_col_offset
                    )
                    name_end = source.index("]", parameter_end) + 1
                if holder.bases:
                    first, last = holder.bases[0], holder.bases[-1]
                    if last.end_lineno is None or last.end_col_offset is None:
                        msg = f"protocol bases have no source extent: {owner}"
                        raise ValueError(msg)
                    start = sum(map(len, lines[: first.lineno - 1])) + first.col_offset
                    end = (
                        sum(map(len, lines[: last.end_lineno - 1]))
                        + last.end_col_offset
                    )
                    source = source[:start] + ", ".join(composed) + source[end:]
                elif composed:
                    source = (
                        source[:name_end]
                        + "("
                        + ", ".join(composed)
                        + ")"
                        + source[name_end:]
                    )
            for name, declaration in imports.items():
                statement = ast.parse(declaration).body[0]
                if (
                    not isinstance(statement, ast.ImportFrom)
                    or statement.module is None
                ):
                    msg = f"protocol base has no absolute import: {name}"
                    raise ValueError(msg)
                source = FlextInfraUtilitiesTransformerHeader.ensure_alias_import(
                    source, statement.module, name, runtime_required=True
                )
            return source

        def _source_protocol_aggregate(
            self, package_dir: Path, class_stem: str, rendered: Mapping[Path, str]
        ) -> str | None:
            """Compose nearest projected owners using the native model ancestry.

            Returns:
                The preserved public facade with redundant ancestor bases removed.

            """
            destination = package_dir / "protocols.py"
            if not self.project.source_query(destination, "isfile"):
                return None
            source = self.project.source_text(destination)
            if is_source_bootstrap_owned(destination):
                source = c.Infra.AUTOGEN_HEADER + "\n" + source.partition("\n")[2]
            module = self.project.get_module(f"{self.package_name}.protocols")
            facade_name = module.get_attribute("p").get_object().get_name()
            facade = next(
                node
                for node in ast.parse(source).body
                if isinstance(node, ast.ClassDef) and node.name == facade_name
            )
            namespace = next(
                (
                    node
                    for node in facade.body
                    if isinstance(node, ast.ClassDef)
                    and node.name == class_stem.removeprefix("Flext")
                ),
                facade,
            )
            candidates = [ast.unparse(base) for base in namespace.bases]
            imports: dict[str, str] = {}
            holders: dict[str, p.Infra.RopeSourceClass] = {}
            modules: dict[str, str] = {}
            for relative, content in rendered.items():
                target = self.repository_root / relative
                part = target.relative_to(package_dir / "_protocols")
                if part.parts[0].startswith("_"):
                    continue
                owner = next(
                    node.name
                    for node in ast.parse(content).body
                    if isinstance(node, ast.ClassDef)
                )
                if owner not in candidates:
                    candidates.append(owner)
                module_name = self.module_name_for(relative)
                imports[owner] = f"from {module_name} import {owner}"
                modules[owner] = module_name
            declared = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                self.repository_root,
                (),
                {
                    self.repository_root / path: content
                    for path, content in rendered.items()
                },
                source_project=self.project,
            )
            with self.project.source_view(
                declared_files=declared, additional_source_folders=None
            ):
                current = self.project.get_module(f"{self.package_name}.protocols")
                native_facade = self._source_class(current.get_attribute("p"))
                native_namespace = (
                    native_facade
                    if namespace is facade
                    else self._source_class(native_facade.get_attribute(namespace.name))
                )
                for name in candidates:
                    binding = (
                        self.project.get_module(modules[name]).get_attribute(name)
                        if name in modules
                        else self.resolve_symbol(native_namespace.get_scope(), name)
                    )
                    if binding is None:
                        msg = f"protocol aggregate base has no native binding: {name}"
                        raise ValueError(msg)
                    holders[name] = self._source_class(binding)
                identity = FlextInfraUtilitiesRopeRuntime.native_object_identity
                inherited = {
                    identity(ancestor)
                    for holder in holders.values()
                    for ancestor in holder.get_mro()[1:]
                }
                bases = [
                    name
                    for name in candidates
                    if identity(holders[name]) not in inherited
                ]
            source = self._source_compose_protocol_holder(
                source,
                namespace.name,
                {
                    name: declaration
                    for name, declaration in imports.items()
                    if name in bases
                },
                bases=bases,
            )
            return FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                destination, source
            ).unwrap()

        def _source_owned_model_protocols(
            self,
            grouped: Mapping[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ],
        ) -> dict[Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]]:
            """Keep model declarations with an authenticated public Protocol owner."""
            owned: dict[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ] = {}
            for path, declarations in grouped.items():
                retained = [
                    (node, model_path, tree)
                    for node, model_path, tree in declarations
                    if ".".join((
                        self.source_module_names[id(tree)],
                        *model_path,
                    ))
                    in self.source_model_protocol_routes
                ]
                if retained:
                    owned[path] = retained
            return owned

        def _source_index_model_protocols(
            self,
            package_dir: Path,
            package_name: str,
            grouped: Mapping[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ],
        ) -> None:
            """Index structural values by their authenticated model declaration path.

            A model nested inside another model receives its complete model path
            as a sibling contract name. It is a distinct value capability, not a
            writable class attribute required of the parent's instances. Source
            model namespaces and constructors remain unchanged; competing public
            or module identities fail before rendering.

            """
            self.source_model_package_exports = self._source_model_package_exports(
                package_dir, package_name
            )
            for destination, classes in grouped.items():
                relative = destination.relative_to(
                    package_dir / "_protocols"
                ).with_suffix("")
                module = ".".join((
                    package_name,
                    "_models",
                    *relative.parts,
                ))
                for node, path, tree in classes:
                    route = f"{module}.{'.'.join(path)}"
                    self.source_model_protocols[route] = "".join(
                        ancestor.name
                        for ancestor, ancestor_path, _source in classes
                        if path[: len(ancestor_path)] == ancestor_path
                    )
                    root_annotation = self._source_root_model_annotation(
                        node, tree, path
                    )
                    if root_annotation is not None:
                        self.source_model_root_annotations[route] = root_annotation
            self.source_model_facade_protocols = self._source_model_facade_owners(
                package_dir, package_name
            )
            self._source_unpublished_protocol_owners()
            self._source_index_model_aliases(grouped)
            self.source_protocol_retirements = self._source_retired_protocol_owners(
                package_dir, package_name, grouped
            )

        def _source_index_model_aliases(
            self,
            grouped: Mapping[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ],
        ) -> None:
            """Index model-namespace type aliases whose value names projected models.

            Such an alias is a model type; its protocol mirror is declared in the
            same generated holder, under the public route of its sibling models.

            """
            for destination, classes in grouped.items():
                for namespace in {
                    path[0] for _node, path, _tree in classes if len(path) > 1
                }:
                    members = [
                        (node, path, tree)
                        for node, path, tree in classes
                        if path[0] == namespace and len(path) == 2
                    ]
                    if not members:
                        continue
                    tree = members[0][2]
                    owner = next(
                        (
                            statement
                            for statement in tree.body
                            if isinstance(statement, ast.ClassDef)
                            and statement.name == namespace
                        ),
                        None,
                    )
                    if owner is None:
                        continue
                    sibling_names = {path[1] for _node, path, _tree in members}
                    route = ".".join((
                        self.source_module_names[id(tree)],
                        *members[0][1],
                    ))
                    public = self.source_model_protocol_routes.get(route)
                    if public is None:
                        continue
                    prefix = public.rpartition(".")[0]
                    for statement in owner.body:
                        if not isinstance(statement, ast.TypeAlias) or not isinstance(
                            statement.name, ast.Name
                        ):
                            continue
                        named = {
                            symbol.id if isinstance(symbol, ast.Name) else symbol.attr
                            for symbol in ast.walk(statement.value)
                            if isinstance(symbol, (ast.Name, ast.Attribute))
                        }
                        if named & sibling_names:
                            self.source_model_aliases[
                                f"{prefix}.{statement.name.id}"
                            ] = (destination, statement, tree, members[0][0])

        def _source_unpublished_protocol_owners(self) -> None:
            """Elect uncomposed declarations by their authenticated generated owner.

            Every same-path holder is composed by the protocol aggregate. A member
            not yet composed by the model facade therefore retains that holder's
            exact member route; competing generated routes remain an error.

            Raises:
                ValueError: Independent model declarations claim one public route.

            """
            claimed: dict[str, str] = {}
            for source, public in self.source_model_protocol_routes.items():
                previous = claimed.setdefault(public, source)
                if previous != source:
                    message = (
                        f"competing generated Protocol route {public}: "
                        f"{previous} and {source}"
                    )
                    raise ValueError(message)
            for source, member in self.source_model_protocols.items():
                if source in self.source_model_protocol_routes:
                    continue
                public = f"p.{member}"
                previous = claimed.setdefault(public, source)
                if previous != source:
                    message = (
                        f"competing generated Protocol route {public}: "
                        f"{previous} and {source}"
                    )
                    raise ValueError(message)
                self.source_model_protocol_routes[source] = public

        def _source_retired_protocol_owners(
            self,
            package_dir: Path,
            package_name: str,
            grouped: Mapping[
                Path, list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]]
            ],
        ) -> dict[Path, tuple[tuple[str, str], ...]]:
            """Plan the authored Protocols that their model projection displaces.

            The concrete model owns its structural contract. An authored
            same-named Protocol in the package's protocol family retires in the
            candidate that composes the projected holder when every authored
            member is projected; a stricter authored type is still covered.

            Returns:
                Each authored holder module with its ``(holder, member)`` pairs.

            Raises:
                ValueError: An authored Protocol declares members the model lacks,
                    or one of its uses would not rebind through the facade.

            """
            protocols_root = (package_dir / "_protocols").resolve()
            facade_module = self.project.get_module(f"{package_name}.protocols")
            facade = facade_module.get_attribute("p").get_object()
            protocol_base = self.qualified_name(
                self.project, "Protocol", module_name="typing"
            ).get_object()
            model_routes = {
                source_route: public_route
                for public_route, source_route in self.source_model_facade_model_routes.items()
            }
            planned: dict[Path, list[tuple[str, str]]] = {}
            displaced: list[p.Infra.RopeSourceClass] = []
            displaced_routes: list[str] = []
            owners: list[p.Infra.RopePyObject] = [facade]
            for destination, classes in grouped.items():
                for model, path, tree in classes:
                    route = ".".join((self.source_module_names[id(tree)], *path))
                    protocol_route = self.source_model_protocol_routes.get(route)
                    public_model = model_routes.get(route)
                    if protocol_route is None or public_model is None:
                        continue
                    member_name = protocol_route.rpartition(".")[2]
                    namespace = protocol_route.removeprefix("p.").rpartition(".")[0]
                    owner = facade
                    if namespace:
                        namespace_binding = self.resolve_symbol(
                            facade.get_scope(), namespace
                        )
                        if namespace_binding is None or not self.py_class(
                            namespace_binding.get_object()
                        ):
                            continue
                        owner = namespace_binding.get_object()
                        owners.append(owner)
                    expected = {
                        projection.declaration.target.id
                        for projection in self.source_fields(model, classes)
                        if isinstance(projection.declaration.target, ast.Name)
                    }
                    expected.update(
                        method.name for method in self.source_methods(model, classes)
                    )
                    # Every projected holder composes the mirrored model base,
                    # so the base contract's members are covered as well.
                    expected.update(self._source_model_base_members())
                    for holder in owner.get_mro():
                        if not self.py_class(holder):
                            continue
                        module = holder.get_module()
                        resource = module.get_resource() if module is not None else None
                        if resource is None:
                            continue
                        source_path = Path(resource.real_path).resolve()
                        if (
                            not source_path.is_relative_to(protocols_root)
                            or source_path == destination.resolve()
                        ):
                            continue
                        holder_node = holder.get_ast()
                        if not isinstance(holder_node, ast.ClassDef):
                            continue
                        for candidate in holder_node.body:
                            if (
                                not isinstance(candidate, ast.ClassDef)
                                or candidate.name != member_name
                            ):
                                continue
                            # Generated holders are stale projections, never
                            # competing owners; consolidation retires them.
                            if is_source_bootstrap_owned(
                                source_path,
                                candidate,
                                contract_docstrings=(
                                    c.Infra.DocumentationText.MODEL_PROTOCOL_CONTRACT.value
                                ),
                            ):
                                continue
                            candidate_binding = self.resolve_symbol(
                                holder.get_scope(), member_name
                            )
                            if candidate_binding is None:
                                continue
                            protocol = candidate_binding.get_object()
                            if (
                                not self.py_class(protocol)
                                or protocol_base not in protocol.get_mro()
                            ):
                                continue
                            actual = self.protocol_contract_members(
                                self.project, protocol, protocols_root
                            )
                            extra = {
                                name: actual[name]
                                for name in sorted(set(actual) - expected)
                            }
                            # A member the model lacks retires with its
                            # Protocol only when nothing consumes it.
                            consumers = (
                                FlextInfraUtilitiesModelsProtocolRetirement.member_consumers(
                                    self.project, extra
                                )
                                if extra
                                else ()
                            )
                            if consumers:
                                message = (
                                    "authored Protocol declares members its model "
                                    f"lacks: {source_path}:{holder_node.name}."
                                    f"{member_name} -> {public_model}; "
                                    f"members={sorted(extra)} consumers={list(consumers)}"
                                )
                                raise ValueError(message)
                            planned.setdefault(source_path, []).append((
                                holder_node.name,
                                member_name,
                            ))
                            displaced.append(protocol)
                            displaced_routes.append(protocol_route)
            blocked, self.source_protocol_rewrites = (
                FlextInfraUtilitiesModelsProtocolRetirement.facade_rebinding(
                    self.project, displaced, displaced_routes, owners
                )
            )
            if blocked:
                message = (
                    "retired Protocol uses do not rebind through the facade: "
                    f"{list(blocked)}"
                )
                raise ValueError(message)
            return {path: tuple(entries) for path, entries in planned.items()}

        def _source_root_model_annotation(
            self, model: ast.ClassDef, tree: ast.Module, path: tuple[str, ...]
        ) -> ast.expr | None:
            """Resolve a root specialization through its native base identity.

            Returns:
                The declared payload of the authenticated Pydantic root base.

            """
            owner = self.project.get_module(self.source_module_names[id(tree)])
            for part in path:
                owner = self._source_class(owner.get_attribute(part))
            root = self.qualified_name(
                self.project, "RootModel", module_name="pydantic"
            ).get_object()
            for base in model.bases:
                if not isinstance(base, ast.Subscript):
                    continue
                binding = self.resolve_symbol(owner.get_scope(), base.value)
                if binding is not None:
                    value = binding.get_object()
                    if self.py_class(value) and root in value.get_mro():
                        return base.slice
            return None

        @staticmethod
        def _source_declared_frozen(node: ast.ClassDef) -> bool | None:
            """Read the model's direct ``frozen`` override from its declaration."""
            configs = [
                statement.value
                for statement in node.body
                if isinstance(statement, (ast.AnnAssign, ast.Assign))
                and statement.value is not None
                and (
                    (
                        isinstance(statement, ast.AnnAssign)
                        and isinstance(statement.target, ast.Name)
                        and statement.target.id == "model_config"
                    )
                    or (
                        isinstance(statement, ast.Assign)
                        and any(
                            isinstance(target, ast.Name) and target.id == "model_config"
                            for target in statement.targets
                        )
                    )
                )
            ]
            if len(configs) > 1:
                msg = f"model has duplicate config declarations: {node.name}"
                raise ValueError(msg)
            if not configs:
                return None
            config = configs[0]
            if isinstance(config, ast.Dict):
                values = {
                    key.value: value
                    for key, value in zip(config.keys, config.values, strict=True)
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                }
                frozen = values.get("frozen")
            elif isinstance(config, ast.Call):
                frozen = next(
                    (
                        keyword.value
                        for keyword in config.keywords
                        if keyword.arg == "frozen"
                    ),
                    None,
                )
            else:
                return None
            if frozen is None:
                return None
            if not isinstance(frozen, ast.Constant) or not isinstance(
                frozen.value, bool
            ):
                msg = f"model frozen config is not a literal bool: {node.name}"
                raise TypeError(msg)
            return frozen.value

        def _source_effective_model_frozen(self, binding: p.Infra.RopePyName) -> bool:
            """Read effective Pydantic mutability through the native model MRO."""
            model = self._source_class(binding)
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            frozen = False
            for ancestor in reversed(model.get_mro()):
                if not self.py_class(ancestor) or model_base not in ancestor.get_mro():
                    continue
                declaration = ancestor.get_ast()
                if not isinstance(declaration, ast.ClassDef):
                    module = ancestor.get_module()
                    if module is not None and module.get_name().startswith("pydantic."):
                        continue
                    msg = "model MRO contains a class without source config"
                    raise ValueError(msg)
                config = self._source_declared_frozen(declaration)
                if config is not None:
                    frozen = config
            return frozen

        def _source_model_package_exports(
            self, package_dir: Path, package_name: str
        ) -> dict[tuple[str, str], str]:
            """Index first-party model package exports from their lazy declarations."""
            exports: dict[tuple[str, str], str] = {}
            root = package_dir / "_models"
            if not self.project.source_query(root, "isdir"):
                return exports
            for directory, _children, files in self.project.source_walk(root):
                if c.Infra.INIT_PY not in files:
                    continue
                path = directory / c.Infra.INIT_PY
                relative = directory.relative_to(package_dir)
                package = ".".join((package_name, *relative.parts))
                tree = ast.parse(self.project.source_text(path), filename=str(path))
                for statement in tree.body:
                    if (
                        not isinstance(statement, ast.If)
                        or not isinstance(statement.test, ast.Name)
                        or statement.test.id != "TYPE_CHECKING"
                    ):
                        continue
                    for imported in statement.body:
                        if not isinstance(imported, ast.ImportFrom) or imported.level:
                            continue
                        if imported.module is None:
                            continue
                        for alias in imported.names:
                            exports[package, alias.asname or alias.name] = (
                                f"{imported.module}.{alias.name}"
                            )
            return exports

        def _source_model_facade_owners(
            self, package_dir: Path, package_name: str
        ) -> dict[str, str]:
            """Index facade inheritance using native declaring identities.

            Returns:
                Unique public model routes paired with their structural ports.

            """
            module = self.project.get_module(f"{package_name}.models")
            facade = module.get_attribute("m").get_object()
            protocol_facade = (
                self.project
                .get_module(f"{package_name}.protocols")
                .get_attribute("p")
                .get_object()
            )
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            protocol_base = self.qualified_name(
                self.project, "Protocol", module_name="typing"
            ).get_object()
            owners: dict[str, set[str]] = {}
            protocols: dict[str, set[str]] = {}
            model_routes: dict[str, set[str]] = {}
            self.source_model_facade_import_roots = frozenset()

            def collect(
                owner: p.Infra.RopeSourceClass,
                path: tuple[str, ...],
                seen: frozenset[str],
                namespace: tuple[str, ...],
            ) -> None:
                identity = FlextInfraUtilitiesRopeRuntime.native_object_identity(owner)
                if identity in seen:
                    return
                for name, binding in owner.get_attributes().items():
                    value = binding.get_object()
                    if not self.py_class(value):
                        continue
                    declaring_module, declaration = self._source_class_identity(value)
                    route = f"{declaring_module}.{declaration}"
                    member = self.source_model_protocols.get(route)
                    if member is not None:
                        public = ".".join(("m", *path, name))
                        protocol = ".".join(("p", *namespace, member))
                        owners.setdefault(public, set()).add(protocol)
                        protocols.setdefault(route, set()).add(protocol)
                        model_routes.setdefault(public, set()).add(route)
                        self.source_model_facade_import_roots |= {
                            declaring_module.partition(".")[0]
                        }
                        self.source_model_frozen[route] = (
                            self._source_effective_model_frozen(binding)
                        )
                        collect(
                            value,
                            (*path, name),
                            seen
                            | {
                                FlextInfraUtilitiesRopeRuntime.native_object_identity(
                                    owner
                                )
                            },
                            namespace,
                        )
                    elif model_base in value.get_mro():
                        if declaring_module.startswith(f"{package_name}."):
                            continue
                        public_path = ".".join((*path, name))
                        port_binding = self.resolve_symbol(
                            protocol_facade.get_scope(), public_path
                        )
                        if port_binding is None:
                            continue
                        port = port_binding.get_object()
                        if (
                            not self.py_class(port)
                            or protocol_base not in port.get_mro()
                        ):
                            msg = f"upstream port is not a Protocol: {public_path}"
                            raise ValueError(msg)
                        if not any(
                            self._denotes(
                                decorator,
                                port.get_scope().parent,
                                "typing",
                                "runtime_checkable",
                            )
                            for decorator in port.get_ast().decorator_list
                        ):
                            msg = (
                                f"upstream port is not runtime_checkable: {public_path}"
                            )
                            raise ValueError(msg)
                        public = f"m.{public_path}"
                        protocol = f"p.{public_path}"
                        owners.setdefault(public, set()).add(protocol)
                        protocols.setdefault(route, set()).add(protocol)
                        model_routes.setdefault(public, set()).add(route)
                        self.source_model_facade_import_roots |= {
                            declaring_module.partition(".")[0]
                        }
                        self.source_model_frozen[route] = (
                            self._source_effective_model_frozen(binding)
                        )
                    else:
                        namespace_suffix = self._source_model_facade_namespace(value)
                        collect(
                            value,
                            (*path, *namespace_suffix),
                            seen
                            | {
                                FlextInfraUtilitiesRopeRuntime.native_object_identity(
                                    owner
                                )
                            },
                            (*namespace, *namespace_suffix),
                        )

            collect(facade, (), frozenset(), ())
            self.source_model_protocol_routes = {}
            for route, targets in protocols.items():
                bindings = [
                    self.resolve_symbol(
                        protocol_facade.get_scope(), target.removeprefix("p.")
                    )
                    for target in targets
                ]
                identities = {
                    FlextInfraUtilitiesRopeRuntime.native_object_identity(
                        binding.get_object()
                    )
                    for binding in bindings
                    if binding is not None
                }
                if len(identities) == 1 and "" not in identities:
                    self.source_model_protocol_routes[route] = min(
                        targets, key=lambda target: (target.count("."), target)
                    )
                elif len(targets) == 1:
                    self.source_model_protocol_routes[route] = next(iter(targets))
            self.source_model_facade_model_routes = {
                route: next(iter(targets))
                for route, targets in model_routes.items()
                if len(targets) == 1
            }
            return {
                route: next(iter(targets))
                for route, targets in owners.items()
                if len(targets) == 1
            }

        def _source_model_facade_namespace(
            self, value: p.Infra.RopePyObject
        ) -> tuple[str, ...]:
            """Return only nested namespace declarations owned by a models facade."""
            module = value.get_module()
            resource = module.get_resource() if module is not None else None
            if resource is None or Path(resource.real_path).name != "models.py":
                return ()
            facade = FlextInfraUtilitiesRopeAnalysis.published_facade_owner(
                self.project, resource
            )
            if facade is None or facade[0] != "m":
                return ()
            identity = FlextInfraUtilitiesRopeRuntime.native_object_identity(value)
            _module_name, separator, path = identity.partition("::")
            prefix = f"{facade[1]}."
            return (
                tuple(path.removeprefix(prefix).split("."))
                if separator and path.startswith(prefix)
                else ()
            )

        def _source_layout(self) -> tuple[Path, str, str] | None:
            """Return the bound package layout, else the primary distribution one.

            Returns:
                The package directory and facade class stem, if source declares one.

            Raises:
                ValueError: The bound package is not a declared layout.

            """
            primary = self._primary_source_layout()
            if self._bound_package_name is None or (
                primary is not None and primary[2] == self._bound_package_name
            ):
                return primary
            for layout in self._namespace_source_layouts():
                if layout[2] == self._bound_package_name:
                    return layout
            msg = f"package is not a declared model layout: {self._bound_package_name}"
            raise ValueError(msg)

        def _namespace_source_layouts(self) -> tuple[tuple[Path, str, str], ...]:
            """Discover declared namespace packages that own a models facade.

            A package qualifies when it holds both ``models.py`` and a ``_models``
            directory below a declared repository namespace package; its stem is
            read from the models facade and cross-checked against its protocols
            facade. A package whose protocols facade is still absent is skipped:
            the facades surface creates it in the same generation and the next
            pass projects its models.

            Returns:
                Namespace package layouts in deterministic dotted-name order.

            Raises:
                ValueError: A declared facade pair carries competing stems.

            """
            layouts: list[tuple[Path, str, str]] = []
            for (
                namespace
            ) in FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(
                self.repository_root, source_project=self.project
            ):
                namespace_root = self.repository_root / Path(*namespace.split("."))
                if not self.project.source_query(namespace_root, "isdir"):
                    continue
                for directory, children, files in self.project.source_walk(
                    namespace_root
                ):
                    if "models.py" not in files or "_models" not in children:
                        continue
                    model_name = self._source_facade_class_name(
                        directory / "models.py", "m"
                    )
                    if not model_name.endswith("Models"):
                        msg = f"public model facade name is not canonical: {directory}"
                        raise ValueError(msg)
                    class_stem = model_name.removesuffix("Models")
                    protocols = directory / "protocols.py"
                    if not self.project.source_query(protocols, "isfile"):
                        continue
                    if (
                        self._source_facade_class_name(protocols, "p")
                        != f"{class_stem}Protocols"
                    ):
                        msg = f"public model and protocol facades have competing stems: {directory}"
                        raise ValueError(msg)
                    package_name = ".".join(
                        directory.relative_to(self.repository_root).parts
                    )
                    layouts.append((directory, class_stem, package_name))
            layouts.extend(self._internal_tier_source_layouts())
            return tuple(sorted(layouts, key=operator.itemgetter(2)))

        def _internal_tier_source_layouts(self) -> tuple[tuple[Path, str, str], ...]:
            """Discover internal tiers (``tests``, ``examples``...) owning models.

            Internal tiers are detected, never declared: every direct child
            namespace of the repository root other than ``src``. A tier that
            holds ``models.py``, ``_models`` and ``protocols.py`` projects its
            models into ``<tier>/_protocols`` exactly like a public package, so
            ``p.<Tier>.*`` resolves in every tier (generator law point 5).

            Returns:
                Internal tier layouts; a tier without its facade pair is skipped.

            Raises:
                ValueError: A tier's facade pair carries competing stems.

            """
            layouts: list[tuple[Path, str, str]] = []
            _, children, _ = next(self.project.source_walk(self.repository_root))
            for child in sorted(children):
                directory = self.repository_root / child
                if child == c.Infra.DEFAULT_SRC_DIR or not (
                    FlextInfraUtilitiesProjectDiscovery.root_namespace(
                        self.repository_root, child, source_project=self.project
                    )
                    and self.project.source_query(directory / "models.py", "isfile")
                    and self.project.source_query(directory / "_models", "isdir")
                    and self.project.source_query(directory / "protocols.py", "isfile")
                ):
                    continue
                model_name = self._source_facade_class_name(
                    directory / "models.py", "m"
                )
                if not model_name.endswith("Models"):
                    msg = f"tier model facade name is not canonical: {directory}"
                    raise ValueError(msg)
                class_stem = model_name.removesuffix("Models")
                if (
                    self._source_facade_class_name(directory / "protocols.py", "p")
                    != f"{class_stem}Protocols"
                ):
                    msg = f"tier model and protocol facades have competing stems: {directory}"
                    raise ValueError(msg)
                layouts.append((directory, class_stem, child))
            return tuple(layouts)

        def _primary_source_layout(self) -> tuple[Path, str, str] | None:
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
            facade_names = {
                alias: self._source_facade_class_name(package_dir / module, alias)
                for module, alias in (("models.py", "m"), ("protocols.py", "p"))
            }
            model_name = facade_names["m"]
            protocol_name = facade_names["p"]
            if not model_name.endswith("Models") or not protocol_name.endswith(
                "Protocols"
            ):
                msg = "public model and protocol facade names are not canonical"
                raise ValueError(msg)
            class_stem = protocol_name.removesuffix("Protocols")
            if model_name != f"{class_stem}Models":
                msg = "public model and protocol facades have competing stems"
                raise ValueError(msg)
            return (
                package_dir,
                class_stem,
                package_name,
            )

        def _source_facade_class_name(self, path: Path, alias: str) -> str:
            """Read the canonical source class bound to a public facade alias."""
            if not self.project.source_query(path, "isfile"):
                msg = f"public facade source is absent: {path}"
                raise ValueError(msg)
            tree = ast.parse(self.project.source_text(path), filename=str(path))
            owners = {
                statement.value.id
                for statement in tree.body
                if isinstance(statement, ast.Assign)
                and isinstance(statement.value, ast.Name)
                and any(
                    isinstance(target, ast.Name) and target.id == alias
                    for target in statement.targets
                )
            }
            classes = {
                statement.name
                for statement in tree.body
                if isinstance(statement, ast.ClassDef) and statement.name in owners
            }
            if len(classes) != 1:
                msg = f"public facade alias has no unique class owner: {path}:{alias}"
                raise ValueError(msg)
            return next(iter(classes))

        def _source_model_classes(
            self,
            tree: ast.Module,
            module_name: str,
        ) -> list[tuple[ast.ClassDef, tuple[str, ...]]]:
            """Elect source model declarations through native Pydantic ancestry.

            Returns:
                Source classes whose actual native ancestry includes BaseModel.

            Raises:
                ValueError: A source declaration or its ancestry is unresolved.

            """
            module = self.project.get_module(module_name)
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            typed_dict_factories = tuple(
                self.qualified_name(
                    self.project, "TypedDict", module_name=provider
                ).get_object()
                for provider in ("typing", "typing_extensions")
            )
            classes: list[tuple[ast.ClassDef, tuple[str, ...]]] = []

            def collect(body: list[ast.stmt], parents: tuple[str, ...]) -> None:
                for node in body:
                    if not isinstance(node, ast.ClassDef):
                        continue
                    path = (*parents, node.name)
                    owner = module
                    for part in path[:-1]:
                        owner = owner.get_attribute(part).get_object()
                    source = self._source_class(owner.get_attribute(path[-1]))
                    if source.get_ast().lineno != node.lineno:
                        message = f"model declaration identity changed: {module_name}.{'.'.join(path)}"
                        raise ValueError(message)
                    ancestors = source.get_mro()
                    if model_base in ancestors:
                        classes.append((node, path))
                    elif any(
                        FlextInfraUtilitiesRopeRuntimeTypes.unresolved_witness(base)
                        and not any(
                            base.pyobject is factory for factory in typed_dict_factories
                        )
                        for base in ancestors
                    ):
                        message = f"model ancestry is unresolved: {module_name}.{'.'.join(path)}"
                        raise ValueError(message)
                    collect(node.body, path)

            collect(tree.body, ())
            return classes

        def _source_generated_holder(self, destination: Path) -> str:
            """Name the holder class the generator owns for one protocol module.

            Returns:
                The facade class stem, ``Protocols`` and the module's derived stems.

            Raises:
                ValueError: The package layout is not elected yet.

            """
            if self.package is None:
                message = "protocol holder naming has no elected package"
                raise ValueError(message)
            return (
                self.class_stem
                + "Protocols"
                + "".join(
                    u.derive_class_stem(part.strip("_"))
                    for part in destination
                    .relative_to(self.package / "_protocols")
                    .with_suffix("")
                    .parts
                )
            )

        def _source_authored_protocol_holder(
            self, destination: Path, package_name: str
        ) -> str:
            """Preserve the exported holder's authenticated source identity.

            Returns:
                The unique declared namespace containing structural contracts.

            Raises:
                ValueError: The destination has competing or absent public owners.

            """
            if self.package is None:
                message = "authored Protocol inventory has no elected package"
                raise ValueError(message)
            module_name = ".".join((
                package_name,
                *destination.relative_to(self.package).with_suffix("").parts,
            ))
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                self.project.get_module(module_name)
            )
            exports = FlextInfraUtilitiesRopeAnalysis.public_export_names_source(module)
            holders = []
            for name in exports:
                value = module.get_attribute(name).get_object()
                if not self.py_class(value) or value.get_module() is not module:
                    continue
                declaration = value.get_ast()
                if isinstance(declaration, ast.ClassDef) and any(
                    isinstance(child, ast.ClassDef) for child in declaration.body
                ):
                    holders.append(name)
            if len(holders) != 1:
                message = (
                    f"authored Protocol holder is absent or ambiguous: {destination}"
                )
                raise ValueError(message)
            return holders[0]

        def _source_render_module(
            self,
            destination: Path,
            owner: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            package_name: str,
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
            if existing is not None and not existing.startswith(c.Infra.AUTOGEN_HEADER):
                owner = self._source_authored_protocol_holder(destination, package_name)
            generated = self._source_generated_module(
                destination, owner, classes, package_name
            )
            if existing is None or existing.startswith(c.Infra.AUTOGEN_HEADER):
                return generated
            return self._source_extend_authored(
                existing,
                owner,
                classes,
                destination,
                package_name,
                generated_source=generated,
            )

        def _source_generated_module(
            self,
            destination: Path,
            owner: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            package_name: str,
        ) -> str:
            """Render source contracts through the canonical model template.

            Returns:
                The template-rendered module for the authenticated source models.

            """
            contracts: list[
                p.Infra.ModelProtocolRenderContext.ModelProtocolContract
            ] = []
            evaluated_bases: set[str] = set()
            names: set[str] = set()

            for node, path, tree in classes:
                name = self.source_model_protocols[
                    ".".join((self.source_module_names[id(tree)], *path))
                ]
                if name in names:
                    message = (
                        f"competing projected Protocol identity: {destination}:{name}"
                    )
                    raise ValueError(message)
                names.add(name)
                declarations: list[str] = []
                for projection in self.source_fields(node, classes):
                    field = projection.declaration
                    if isinstance(field.target, ast.Name):
                        annotation = ast.unparse(field.annotation)
                        if projection.read_only:
                            declarations.append(
                                ast.unparse(
                                    self._source_property_declaration(
                                        field.target.id,
                                        field.annotation,
                                        projection.description,
                                    )
                                )
                            )
                        else:
                            declarations.append(f"{field.target.id}: {annotation}")
                declarations.extend(
                    ast.unparse(method) for method in self.source_methods(node, classes)
                )
                # A member named ``property`` rebinds the builtin for every later
                # statement of the class body, so it is declared last.
                declarations.sort(
                    key=lambda declaration: declaration.startswith((
                        "@property\ndef property(",
                        "property:",
                    ))
                )
                copy_base = self._source_copy_capability(
                    self._source_model_class(node, classes), destination, owner
                )
                if copy_base:
                    evaluated_bases.add(copy_base)
                contracts.append(
                    m.Infra.ModelProtocolRenderContext.ModelProtocolContract(
                        name=name,
                        depth=0,
                        type_parameters=tuple(
                            ast.unparse(parameter)
                            for parameter in getattr(node, "type_params", ())
                        ),
                        bases=(copy_base, "Protocol") if copy_base else ("Protocol",),
                        declarations=tuple(declarations),
                    )
                )
            imports = (
                "from __future__ import annotations",
                "from collections.abc import Mapping, Sequence",
                "from typing import AbstractSet, TYPE_CHECKING, Protocol, runtime_checkable",
                *self._source_runtime_base_imports(evaluated_bases),
                *self.source_annotation_imports(classes, package_name, destination),
            )
            context = m.Infra.ModelProtocolRenderContext(
                header=c.Infra.AUTOGEN_HEADER,
                documentation_language=self.documentation_language,
                copyright_notice=FlextInfraUtilitiesLintRecipes.copyright_notice(
                    self.package or self.repository_root,
                    module=destination,
                    source_project=self.project,
                ),
                imports=tuple(dict.fromkeys(imports)),
                sibling_import_lines=(),
                owner=owner,
                contracts=tuple(contracts),
                aliases=tuple(
                    "type "
                    + statement.name.id
                    + " = "
                    + ast.unparse(
                        self._source_structural_annotation(
                            statement.value, alias_tree, model, classes
                        )
                    )
                    for alias_destination, statement, alias_tree, model in (
                        self.source_model_aliases.values()
                    )
                    if alias_destination == destination
                    and isinstance(statement.name, ast.Name)
                ),
            )
            template = (
                FlextInfraUtilitiesGitignore.codegen_templates_root(
                    config.Infra.codegen
                )
                / c.Infra.TEMPLATE_MODEL_PROTOCOL
            )
            return u.Cli.template_render(template, context).unwrap()

        @staticmethod
        def _source_validate_generated_module(
            source: str, destination: Path, owner: str
        ) -> None:
            """Reject invalid generated Protocol source before plan publication.

            Raises:
                ValueError: The generated source cannot be parsed.

            """
            try:
                ast.parse(source, filename=str(destination))
            except SyntaxError as error:
                message = (
                    "generated Protocol source is invalid: "
                    f"owner={owner} path={destination} "
                    f"line={error.lineno} column={error.offset}: {error.msg}"
                )
                raise ValueError(message) from error

        def source_annotation_imports(
            self,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            package_name: str,
            destination: Path | None = None,
        ) -> list[str]:
            """Retain imported non-facade annotation providers from source.

            A family letter is imported from the upstream package its facade
            extends, and a family class the annotations reference is imported from
            its family package unless the destination module declares it.

            Returns:
                Import statements needed by the source-derived field annotations.

            """
            annotations = [
                projection.declaration.annotation
                for node, _path, _tree in classes
                for projection in self.source_fields(node, classes)
            ]
            annotations.extend(
                parameter
                for node, _path, _tree in classes
                for parameter in node.type_params
            )
            for node, _path, _tree in classes:
                for method in self.source_methods(node, classes):
                    annotations.extend(
                        argument.annotation
                        for argument in (
                            *method.args.posonlyargs,
                            *method.args.args,
                            *method.args.kwonlyargs,
                            *([method.args.vararg] if method.args.vararg else []),
                            *([method.args.kwarg] if method.args.kwarg else []),
                        )
                        if argument.annotation is not None
                    )
                    if method.returns is not None:
                        annotations.append(method.returns)
                    annotations.extend(method.type_params)
            roots = {
                symbol.id
                for annotation in annotations
                for symbol in ast.walk(annotation)
                if isinstance(symbol, ast.Name)
            }
            runtime_imports: list[str] = []
            type_imports: list[str] = []
            families = FlextInfraUtilitiesCodegenNamespace.facade_families()
            in_family = (
                destination is not None
                and self.package is not None
                and destination.resolve().is_relative_to(
                    (self.package / "_protocols").resolve()
                )
            )
            for letter in sorted(roots & families.keys()):
                references = frozenset(
                    symbol.attr
                    for annotation in annotations
                    for symbol in ast.walk(annotation)
                    if isinstance(symbol, ast.Attribute)
                    and isinstance(symbol.value, ast.Name)
                    and symbol.value.id == letter
                )
                if in_family:
                    # Own members here are spelled through their family classes
                    # (imported below), never through the own letter.
                    references -= self._source_letter_own_members(letter)
                    if not references:
                        continue
                (type_imports if letter in {"m", "p"} else runtime_imports).append(
                    "from "
                    + self._source_letter_provider(
                        letter, references, in_family=in_family
                    )
                    + f" import {letter}"
                )
            declaring = (
                None
                if destination is None or self.package is None
                else ".".join(
                    destination.relative_to(self.package.parent).with_suffix("").parts
                )
            )
            type_imports.extend(
                f"from {family} import {name}"
                for name in sorted(roots & self.source_family_classes.keys())
                for family, module, _declared in (self.source_family_classes[name],)
                if module != declaring
            )
            statements = list(classes[0][2].body)
            for statement in statements:
                if isinstance(statement, ast.If) and (
                    (
                        isinstance(statement.test, ast.Name)
                        and statement.test.id == "TYPE_CHECKING"
                    )
                    or (
                        isinstance(statement.test, ast.Attribute)
                        and statement.test.attr == "TYPE_CHECKING"
                    )
                ):
                    statements.extend(statement.body)
                if isinstance(statement, ast.Import):
                    names = [
                        alias
                        for alias in statement.names
                        if (alias.asname or alias.name.partition(".")[0]) in roots
                        and alias.name.partition(".")[0] != "pydantic"
                    ]
                    if names:
                        for target, group in (
                            (
                                type_imports,
                                [
                                    alias
                                    for alias in names
                                    if (alias.asname or alias.name.partition(".")[0])
                                    in {"m", "p"}
                                ],
                            ),
                            (
                                runtime_imports,
                                [
                                    alias
                                    for alias in names
                                    if (alias.asname or alias.name.partition(".")[0])
                                    not in {"m", "p"}
                                ],
                            ),
                        ):
                            if group:
                                target.append(ast.unparse(ast.Import(names=group)))
                elif isinstance(statement, ast.ImportFrom) and statement.module not in {
                    "__future__",
                    "pydantic",
                }:
                    names = [
                        alias
                        for alias in statement.names
                        if (alias.asname or alias.name) in roots
                        and (alias.asname or alias.name) not in families
                    ]
                    if names:
                        model_source = statement.module.startswith(
                            f"{package_name}._models"
                        ) or statement.module.startswith(f"{package_name}._protocols")
                        type_names = [
                            alias
                            for alias in names
                            if model_source
                            or (alias.asname or alias.name) in {"m", "p"}
                        ]
                        runtime_names = [
                            alias for alias in names if alias not in type_names
                        ]
                        for target, group in (
                            (type_imports, type_names),
                            (runtime_imports, runtime_names),
                        ):
                            if group:
                                target.append(
                                    ast.unparse(
                                        ast.ImportFrom(
                                            module=statement.module,
                                            names=group,
                                            level=statement.level,
                                        )
                                    )
                                )
            if type_imports:
                runtime_imports.append(
                    "if TYPE_CHECKING:\n"
                    + "\n".join(f"    {item}" for item in dict.fromkeys(type_imports))
                )
            return list(dict.fromkeys(runtime_imports))

        def source_fields(
            self,
            node: ast.ClassDef,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> list[_SourceFieldProjection]:
            """Collect inherited structural fields in Python base precedence.

            Returns:
                Effective model fields with Pydantic annotation metadata removed.

            """
            tree = next(tree for candidate, _path, tree in classes if candidate is node)
            path = next(path for candidate, path, _tree in classes if candidate is node)
            module_name = self.source_module_names[id(tree)]
            route = ".".join((module_name, *path))
            if route in self.source_field_cache:
                return list(self.source_field_cache[route])
            model = self._source_model_class(node, classes)
            frozen = self._source_effective_model_frozen(
                self.qualified_name(
                    self.project, ".".join(path), module_name=module_name
                )
            )
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            declarations = list(classes)
            fields: dict[str, _SourceFieldProjection] = {}
            for ancestor in reversed(model.get_mro()):
                if (
                    not self.py_class(ancestor)
                    or ancestor is model_base
                    or model_base not in ancestor.get_mro()
                ):
                    continue
                declaration = ancestor.get_ast()
                source = ancestor.get_module()
                ancestor_tree = source.get_ast()
                if not isinstance(declaration, ast.ClassDef) or not isinstance(
                    ancestor_tree, ast.Module
                ):
                    msg = "model ancestor has no native source declaration"
                    raise TypeError(msg)
                ancestor_module, qualified = self._source_class_identity(ancestor)
                self.source_module_names[id(ancestor_tree)] = ancestor_module
                declarations.append((
                    declaration,
                    tuple(qualified.split(".")),
                    ancestor_tree,
                ))
                for projection in self._source_declared_fields(
                    declaration,
                    ancestor_tree,
                    declarations,
                    frozen=frozen,
                    scope=ancestor.get_scope(),
                ):
                    if not isinstance(projection.declaration.target, ast.Name):
                        message = "model field target is not an authenticated name"
                        raise TypeError(message)
                    fields[projection.declaration.target.id] = projection
            root_type = self.source_model_root_annotations.get(route)
            if root_type is not None:
                # The root type is a base subscript, evaluated in the scope
                # that encloses the model class.
                root_structural = self._source_structural_annotation(
                    root_type,
                    tree,
                    node,
                    declarations,
                    lexical=self
                    ._source_model_class(node, declarations)
                    .get_scope()
                    .parent,
                )
                fields["root"] = _SourceFieldProjection(
                    declaration=ast.AnnAssign(
                        target=ast.Name(id="root", ctx=ast.Store()),
                        annotation=root_structural,
                        value=None,
                        simple=1,
                    ),
                    # Same covariance law as declared fields: a rewritten
                    # (protocol or read-only container) root is a property.
                    read_only=frozen
                    or ast.dump(root_structural) != ast.dump(root_type),
                )
            self.source_field_cache[route] = tuple(fields.values())
            return list(self.source_field_cache[route])

        def _source_model_class(
            self,
            node: ast.ClassDef,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> p.Infra.RopeSourceClass:
            """Resolve an inventory declaration through its original module binding.

            Returns:
                The native class bound by the authenticated declaration.

            """
            path, tree = next(
                (path, tree) for candidate, path, tree in classes if candidate is node
            )
            return self._source_class(
                self.qualified_name(
                    self.project,
                    ".".join(path),
                    module_name=self.source_module_names[id(tree)],
                )
            )

        def _source_copy_capability(
            self, model: p.Infra.RopeSourceClass, destination: Path, owner: str
        ) -> str:
            """Reuse the precise copy port while leaving serialization at its owner.

            Returns:
                The structural base, or no base for a local authored override.

            Raises:
                ValueError: A native or structural copy owner cannot be proven.

            """
            native = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            method = model.get_attribute("model_copy").get_object()
            if method is not native.get_attribute("model_copy").get_object():
                declaring_module = method.get_module()
                resource = declaring_module.get_resource() if declaring_module else None
                if resource is not None and self.project.source_owned(
                    Path(resource.real_path)
                ):
                    return ""
                message = (
                    f"model copy owner is not a local declaration: {model.get_name()}"
                )
                raise ValueError(message)
            # The projector's typed ``p`` composition names the copy port; the
            # published facade of its declaring package closes the upstream chain.
            facade = self.qualified_name(
                self.project,
                "p",
                module_name=f"{p.Model.__module__.partition('.')[0]}.protocols",
            ).get_object()
            # The protocol mirrors the concrete base: a model of the core model
            # base composes the core model contract (dump and copy).
            port = self._source_class(facade.get_attribute(p.Model.__name__))
            protocol = self.qualified_name(
                self.project, "Protocol", module_name="typing"
            ).get_object()
            declaration = port.get_ast()
            lexical = port.get_scope().parent
            if (
                not isinstance(declaration, ast.ClassDef)
                or lexical is None
                or protocol not in port.get_mro()
                or not any(
                    self._denotes(decorator, lexical, "typing", "runtime_checkable")
                    for decorator in declaration.decorator_list
                )
            ):
                message = "model copy contract is not a runtime-checkable Protocol"
                raise ValueError(message)
            module, qualified = self._source_class_identity(port)
            holder, separator, member = qualified.rpartition(".")
            if not separator:
                message = "model copy contract has no declared family holder"
                raise ValueError(message)
            if module.partition(".")[0] == self.package_name:
                origin = (
                    self.repository_root
                    / "src"
                    / Path(*module.split(".")).with_suffix(".py")
                )
                if origin == destination and holder == owner:
                    return member
                if origin != destination:
                    # A sibling family class is imported through its family
                    # package, never through the facade under assembly.
                    family = module.rpartition(".")[0] or module
                    self.source_copy_siblings[holder] = f"from {family} import {holder}"
                return f"{holder}.{member}"
            if self.package is None:
                message = "model copy contract has no elected package"
                raise ValueError(message)
            if self.source_copy_facade is None:
                own = self._source_class(
                    self.qualified_name(
                        self.project, "p", module_name=f"{self.package_name}.protocols"
                    )
                )
                # The port's own declaring facade closes the upstream chain.
                self.source_copy_facade = self.upstream_protocol_facade(
                    (*own.get_mro()[1:], facade), self.package, port
                )
            return f"{self.source_copy_facade[0]}.{member}"

        def _source_runtime_base_imports(self, bases: set[str]) -> tuple[str, ...]:
            """Import every external base evaluated while creating a Protocol class.

            Annotation-only facade names remain under ``TYPE_CHECKING``. Protocol
            bases are evaluated during class creation and therefore require their
            provider at runtime.

            Returns:
                Deterministically ordered runtime imports for the base expressions.

            """
            providers = dict(
                () if self.source_copy_facade is None else (self.source_copy_facade,)
            )
            providers.update(self.source_copy_siblings)
            roots = {
                body.value.id
                for body in (ast.parse(base, mode="eval").body for base in bases)
                if isinstance(body, ast.Attribute) and isinstance(body.value, ast.Name)
            }
            return tuple(sorted(providers[root] for root in roots if root in providers))

        def source_methods(
            self,
            node: ast.ClassDef,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
        ) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef, ...]:
            """Project public authored callable contracts in native override order.

            Returns:
                Local method signatures with declaration-only Protocol bodies.

            Raises:
                TypeError: A source owner has no authenticated class AST.

            """
            model = self._source_model_class(node, classes)
            route = ".".join(self._source_class_identity(model))
            if route in self.source_method_cache:
                return self.source_method_cache[route]
            methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
            declarations = list(classes)
            for ancestor in reversed(model.get_mro()):
                if not self.py_class(ancestor):
                    continue
                resource = ancestor.get_module().get_resource()
                if resource is None or not self.project.source_owned(
                    Path(resource.real_path)
                ):
                    continue
                definition, tree = ancestor.get_ast(), ancestor.get_module().get_ast()
                if not isinstance(definition, ast.ClassDef) or not isinstance(
                    tree, ast.Module
                ):
                    message = "model callable owner has no authenticated source AST"
                    raise TypeError(message)
                module, qualified = self._source_class_identity(ancestor)
                self.source_module_names[id(tree)] = module
                declarations.append((definition, tuple(qualified.split(".")), tree))
                for method in definition.body:
                    if not isinstance(
                        method, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ) or method.name.startswith("_"):
                        continue
                    if isinstance(
                        method, ast.FunctionDef
                    ) and self._source_computed_field(method, tree, definition):
                        continue
                    projected = self._source_method_declaration(
                        method, definition, tree, declarations, ancestor.get_scope()
                    )
                    if projected is not None:
                        methods[method.name] = projected
            self.source_method_cache[route] = tuple(methods.values())
            return self.source_method_cache[route]

        def _source_method_decorators(
            self,
            method: ast.FunctionDef | ast.AsyncFunctionDef,
            scope: p.Infra.RopeScope,
        ) -> list[ast.expr] | None:
            """Authenticate descriptor binding separately from model behavior.

            Returns:
                Structural descriptors, or no declaration for native validation.

            """
            decorators: list[ast.expr] = []
            for decorator in method.decorator_list:
                name = next(
                    (
                        name
                        for name in ("classmethod", "staticmethod", "property")
                        if self._denotes(decorator, scope, "builtins", name)
                    ),
                    None,
                )
                if name is None:
                    expression = (
                        decorator.func if isinstance(decorator, ast.Call) else decorator
                    )
                    if any(
                        self._denotes(expression, scope, "pydantic", capability)
                        for capability in (
                            "field_validator",
                            "model_validator",
                            "field_serializer",
                            "model_serializer",
                        )
                    ):
                        return None
                    # A decorator without a proven descriptor contract can
                    # alter invocation or return behavior. It is behavior,
                    # not a structural Protocol member.
                    return None
                decorators.append(ast.Name(id=name, ctx=ast.Load()))
            return decorators

        def _source_method_declaration(
            self,
            method: ast.FunctionDef | ast.AsyncFunctionDef,
            owner: ast.ClassDef,
            tree: ast.Module,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            scope: p.Infra.RopeScope,
        ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
            """Retain native callable binding, types and literal parameter defaults.

            Returns:
                The method's structural declaration without implementation.

            Decorated behavior belongs to the model implementation. Only
            authenticated builtin descriptors are structural Protocol members.

            Raises:
                ValueError: A default has unproved runtime effects.
                TypeError: A required callable annotation is absent.

            """
            projected = copy.deepcopy(method)
            decorators = self._source_method_decorators(method, scope)
            if decorators is None:
                return None
            projected.decorator_list = decorators
            arguments = [
                *projected.args.posonlyargs,
                *projected.args.args,
                *projected.args.kwonlyargs,
            ]
            arguments.extend(
                argument
                for argument in (projected.args.vararg, projected.args.kwarg)
                if argument
            )
            positional = [*projected.args.posonlyargs, *projected.args.args]
            receiver = (
                positional[0]
                if positional
                and not any(
                    isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
                    for decorator in decorators
                )
                else None
            )
            for argument in arguments:
                if argument.annotation is None:
                    if argument is receiver:
                        continue
                    message = (
                        "model method parameter has no annotation: "
                        f"{method.name}:{argument.arg}"
                    )
                    raise TypeError(message)
                argument.annotation = self._source_structural_annotation(
                    argument.annotation, tree, owner, classes
                )
            if projected.returns is None:
                message = f"model method return has no annotation: {method.name}"
                raise TypeError(message)
            projected.returns = self._source_structural_annotation(
                projected.returns, tree, owner, classes
            )
            for default in (*projected.args.defaults, *projected.args.kw_defaults):
                if default is not None:
                    try:
                        ast.literal_eval(default)
                    except (ValueError, TypeError, SyntaxError) as error:
                        message = (
                            "model method default has unproved runtime effects: "
                            f"{method.name}"
                        )
                        raise ValueError(message) from error
            projected.body = [self._source_member_docstring(ast.get_docstring(method))]
            return ast.fix_missing_locations(projected)

        def _source_member_docstring(self, description: str | None) -> ast.Expr:
            """Derive a lint-clean one-line docstring for a projected member.

            The owning model's own description (``Field(description=...)`` or the
            authored docstring) is the source; a member without one receives the
            localized catalog message.

            Returns:
                A docstring-only body statement ending in sentence punctuation.

            """
            lines = [line.strip() for line in (description or "").splitlines()]
            summary = next((line for line in lines if line), None)
            if summary is None:
                summary = c.Infra.DocumentationText.MODEL_PROTOCOL_MEMBER.localized(
                    self.documentation_language
                )
            if not summary.endswith((".", "?", "!")):
                summary = f"{summary}."
            # A one-line summary is the only layout the docstring rules accept,
            # and the formatter never rewraps it: a description that cannot fit
            # beside its quotes at the member's depth becomes the description
            # paragraph under the localized catalog summary instead.
            routes = self.source_model_protocol_routes.values()
            depth = max((route.count(".") for route in routes), default=0)
            available = FlextInfraUtilitiesLazyInitRender.lazy_init_width() - 4 * (
                depth + 2
            )
            if len(summary) + len('""""""') <= available:
                return ast.Expr(value=ast.Constant(value=summary))
            generic = c.Infra.DocumentationText.MODEL_PROTOCOL_MEMBER.localized(
                self.documentation_language
            )
            return ast.Expr(
                value=ast.Constant(
                    value=f"{generic}\n\n"
                    + "\n".join(textwrap.wrap(summary, available))
                )
            )

        def _source_property_declaration(
            self, name: str, annotation: ast.expr, description: str | None
        ) -> ast.FunctionDef:
            """Project one read-only field as a documented Protocol property.

            Returns:
                The property declaration whose body is its derived docstring
                followed by the Protocol stub ``...``, so type checkers read it
                as an unimplemented contract rather than a function without
                a return.

            """
            return ast.fix_missing_locations(
                ast.FunctionDef(
                    name=name,
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="self")],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=[
                        self._source_member_docstring(description),
                        ast.Expr(value=ast.Constant(value=...)),
                    ],
                    decorator_list=[ast.Name(id="property", ctx=ast.Load())],
                    returns=annotation,
                    type_params=[],
                )
            )

        def _source_declared_fields(
            self,
            node: ast.ClassDef,
            tree: ast.Module,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            *,
            frozen: bool,
            scope: p.Infra.RopeScope,
        ) -> list[_SourceFieldProjection]:
            """Project one native declaration in its own lexical scope.

            Returns:
                Its data fields and computed properties without schema metadata.

            """
            fields: list[_SourceFieldProjection] = []
            for statement in node.body:
                final = None
                if isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    name = statement.target.id
                    if name.startswith("_") or name == "model_config":
                        continue
                    if (
                        self._source_typing_payload(
                            statement.annotation, tree, node, "ClassVar"
                        )
                        is not None
                    ):
                        continue
                    final = self._source_typing_payload(
                        statement.annotation, tree, node, "Final"
                    )
                    annotation = final or statement.annotation
                    metadata = [statement.value, *ast.walk(statement.annotation)]
                    field_frozen = False
                    description = None
                    for value in metadata:
                        if not isinstance(value, ast.Call) or not self._denotes(
                            value.func, scope, "pydantic", "Field"
                        ):
                            continue
                        for keyword in value.keywords:
                            if (
                                keyword.arg == "description"
                                and isinstance(keyword.value, ast.Constant)
                                and isinstance(keyword.value.value, str)
                            ):
                                description = keyword.value.value
                            if keyword.arg != "frozen":
                                continue
                            if not isinstance(
                                keyword.value, ast.Constant
                            ) or not isinstance(keyword.value.value, bool | type(None)):
                                message = f"field frozen metadata is not a native literal: {node.name}.{name}"
                                raise TypeError(message)
                            field_frozen = bool(keyword.value.value)
                    # The abstract Protocol mirrors the concrete declaration: a
                    # capitalized namespace field is an attribute there, so it is
                    # an attribute here too. A read-only property would need a
                    # capitalized function name, which the naming law rejects.
                    read_only = (
                        frozen or final is not None or field_frozen
                    ) and name == name.lower()
                elif isinstance(
                    statement, ast.FunctionDef
                ) and self._source_computed_field(statement, tree, node):
                    if statement.returns is None:
                        continue
                    name, annotation, read_only = (
                        statement.name,
                        statement.returns,
                        True,
                    )
                    description = ast.get_docstring(statement)
                else:
                    continue
                structural = self._source_structural_annotation(
                    annotation,
                    tree,
                    node,
                    classes,
                )
                fields.append(
                    _SourceFieldProjection(
                        declaration=ast.AnnAssign(
                            target=ast.Name(id=name, ctx=ast.Store()),
                            annotation=structural,
                            value=None,
                            simple=1,
                        ),
                        # A field whose type the projection rewrote to a
                        # protocol is covariant: only a read-only property lets
                        # the concrete model satisfy its own contract.
                        read_only=read_only
                        or ast.dump(structural) != ast.dump(annotation),
                        description=description,
                    )
                )
            return fields

        def _source_structural_annotation(
            self,
            annotation: ast.expr,
            tree: ast.Module,
            model: ast.ClassDef,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            *,
            lexical: p.Infra.RopeScope | None = None,
        ) -> ast.expr:
            """Project a source annotation into a covariant structural read contract.

            ``lexical`` names the scope a model base expression is evaluated in
            (the class enclosing the model), instead of the model's own body.

            The semantic projector already treats ``Annotated`` as its value
            type. Mirror that contract in the source bootstrap so Pydantic
            ``Field`` metadata remains owned by ``m`` and is never evaluated
            while importing a Protocol mirror. Mutable containers are exposed
            through their read-only ABCs, allowing nested model values to
            conform covariantly through a Protocol property.

            Returns:
                The recursively unwrapped declared value type.

            Raises:
                ValueError: If ``Annotated`` is ambiguous or has no value type.
                TypeError: If the annotation has no tuple or value type.

            """
            bindings = self._source_typing_bindings(tree, model, "Annotated")
            native = self.project.get_module(self.source_module_names[id(tree)])
            path = next(
                path
                for candidate, path, source in classes
                if candidate is model and source is tree
            )
            for part in path:
                native = self._source_class(native.get_attribute(part))
            scope = native.get_scope()

            class Project(ast.NodeTransformer):
                @override
                def visit_Name(self, node: ast.Name) -> ast.AST:
                    protocol_route = self_owner._source_protocol_member(
                        node.id, tree, model, classes, scope=lexical
                    )
                    if protocol_route is None:
                        return node
                    return ast.copy_location(
                        ast.parse(protocol_route, mode="eval").body,
                        node,
                    )

                @override
                def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
                    protocol_route = self_owner._source_protocol_member(
                        ast.unparse(node), tree, model, classes, scope=lexical
                    )
                    if protocol_route is not None:
                        return ast.copy_location(
                            ast.parse(protocol_route, mode="eval").body,
                            node,
                        )
                    root = node
                    while isinstance(root.value, ast.Attribute):
                        root = root.value
                    if isinstance(root.value, ast.Name) and (
                        root.value.id == "m"
                        or root.value.id.startswith("FlextInfraModels")
                    ):
                        message = (
                            "model annotation has no declared Protocol owner: "
                            f"{ast.unparse(node)}"
                        )
                        raise ValueError(message)
                    return self.generic_visit(node)

                @override
                def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
                    name = ast.unparse(node.value)
                    binding = self_owner.resolve_symbol(scope, node.value)
                    alias = (
                        self_owner.annotation_alias_definition(binding)
                        if binding is not None
                        else None
                    )
                    instance_wrapper = self_owner._denotes(
                        node.value, scope, "pydantic", "InstanceOf"
                    )
                    if alias is not None:
                        declaration, lexical = alias
                        value = declaration.value
                        while isinstance(value, ast.Subscript):
                            if self_owner._denotes(
                                value.value, lexical, "typing", "Annotated"
                            ):
                                if (
                                    not isinstance(value.slice, ast.Tuple)
                                    or not value.slice.elts
                                ):
                                    msg = "Annotated alias has no value type"
                                    raise ValueError(msg)
                                value = value.slice.elts[0]
                            elif any(
                                self_owner._denotes(
                                    value.value, lexical, module, member
                                )
                                for module, member in (
                                    ("pydantic", "InstanceOf"),
                                    ("pydantic.json_schema", "SkipJsonSchema"),
                                )
                            ):
                                value = value.slice
                            else:
                                break
                        instance_wrapper = instance_wrapper or (
                            isinstance(value, ast.Name)
                            and len(declaration.type_params) == 1
                            and value.id == declaration.type_params[0].name
                        )
                    if instance_wrapper:
                        return self.visit(node.slice)
                    if name in bindings:
                        if not isinstance(node.slice, ast.Tuple):
                            msg = "Annotated field has no value type tuple"
                            raise TypeError(msg)
                        if not node.slice.elts:
                            msg = "Annotated field has no value type"
                            raise TypeError(msg)
                        value = self.visit(node.slice.elts[0])
                        if not isinstance(value, ast.expr):
                            msg_0 = "Annotated value is not an expression"
                            raise TypeError(msg_0)
                        return value
                    if name == "Annotated":
                        msg = "model uses unbound typing.Annotated"
                        raise ValueError(msg)
                    if name.rpartition(".")[2] == "Literal":
                        # Literal members are runtime payload, not type identities.
                        return node
                    read_only = next(
                        (
                            target
                            for module, member, target in (
                                ("collections.abc", "MutableSequence", "Sequence"),
                                ("collections.abc", "MutableMapping", "Mapping"),
                                ("builtins", "list", "Sequence"),
                                ("builtins", "dict", "Mapping"),
                            )
                            if self_owner._denotes(node.value, scope, module, member)
                        ),
                        None,
                    )
                    if read_only is not None:
                        original = ast.dump(node.slice)
                        visited = self.generic_visit(node)
                        if not isinstance(visited, ast.Subscript) or (
                            ast.dump(visited.slice) == original
                        ):
                            return visited
                        # Elements rewritten to protocols make the container
                        # covariant only through its read-only ABC; a container
                        # of unchanged element types keeps its mutable contract.
                        return ast.copy_location(
                            ast.Subscript(
                                value=ast.Name(id=read_only, ctx=ast.Load()),
                                slice=visited.slice,
                                ctx=visited.ctx,
                            ),
                            visited,
                        )
                    return self.generic_visit(node)

            self_owner = self
            projected = Project().visit(
                ast.parse(ast.unparse(annotation), mode="eval").body
            )
            if not isinstance(projected, ast.expr):
                msg = "model annotation projection is not an expression"
                raise TypeError(msg)
            return self._source_family_references(
                ast.fix_missing_locations(projected), scope
            )

        def _source_protocol_member(
            self,
            expression: str,
            tree: ast.Module,
            model: ast.ClassDef,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            *,
            scope: p.Infra.RopeScope | None = None,
            visiting: tuple[str, ...] = (),
        ) -> str | None:
            """Resolve the native declaring identity of a model annotation.

            Returns:
                Its unique Protocol route, or None for a non-model declaration.

            Raises:
                ValueError: A model binding or its Protocol owner is unresolved.

            """
            module_name = self.source_module_names[id(tree)]
            paths = [
                path
                for node, path, source in classes
                if node is model and source is tree
            ]
            if len(paths) != 1:
                msg = "annotation has no unique native model scope"
                raise ValueError(msg)
            owner = self.project.get_module(module_name)
            for part in paths[0]:
                owner = self._source_class(owner.get_attribute(part))
            binding = self.resolve_symbol(scope or owner.get_scope(), expression)
            if binding is None:
                return None
            alias = self.annotation_alias_definition(binding)
            if alias is not None:
                declaration, lexical = alias
                alias_module = lexical.pyobject.get_module().get_name()
                if alias_module not in self.source_module_names.values():
                    return None
                identity = f"{alias_module}:{declaration.lineno}"
                if identity in visiting:
                    msg = f"recursive annotation alias: {expression}"
                    raise ValueError(msg)
                projector = self

                class Expand(ast.NodeTransformer):
                    @override
                    def visit_Name(self, node: ast.Name) -> ast.AST:
                        return self._symbol(node)

                    @override
                    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
                        return self._symbol(node)

                    def _symbol(self, node: ast.Name | ast.Attribute) -> ast.AST:
                        route = projector._source_protocol_member(
                            ast.unparse(node),
                            tree,
                            model,
                            classes,
                            scope=lexical,
                            visiting=(*visiting, identity),
                        )
                        return (
                            ast.parse(route, mode="eval").body
                            if route is not None
                            else node
                        )

                    @override
                    def visit_Subscript(self, node: ast.Subscript) -> ast.AST:
                        if projector._denotes(node.value, lexical, "typing", "Literal"):
                            return node
                        return self.generic_visit(node)

                return ast.unparse(Expand().visit(declaration.value))
            value = binding.get_object()
            if not self.py_class(value):
                return None
            model_base = self.qualified_name(
                self.project, "BaseModel", module_name="pydantic"
            ).get_object()
            ancestry = value.get_mro()
            if model_base not in ancestry:
                return None
            # A third-party model is an external boundary type with no FLEXT
            # projection; its concrete annotation stays as declared. Upstream
            # FLEXT families keep resolving through their composed facade.
            declaring = value.get_module().get_resource()
            if (
                declaring is None
                or not self.project.source_owned(Path(declaring.real_path))
            ) and value.get_module().get_name().partition(".")[
                0
            ] not in self.source_model_facade_import_roots | {self.source_package_name}:
                return None
            if any(
                FlextInfraUtilitiesRopeRuntimeTypes.unresolved_witness(base)
                for base in ancestry
            ):
                msg = f"annotation ancestry is unresolved: {expression}"
                raise ValueError(msg)
            identity = FlextInfraUtilitiesRopeRuntime.native_object_identity(value)
            route = ".".join(self._source_class_identity(value))
            protocol_route = self.source_model_protocol_routes.get(route)
            if protocol_route is None and route not in set(
                self.source_model_facade_model_routes.values()
            ) | set(self.source_model_protocols):
                # A model the package does not publish through its model facade
                # (a settings class, a boundary-local model) has no projected
                # contract; its concrete annotation stays as declared.
                return None
            if protocol_route is None:
                msg = f"model Protocol owner is absent or ambiguous: {expression} ({identity})"
                raise ValueError(msg)
            return protocol_route

        def _source_facade_class(self, letter: str) -> p.Infra.RopeSourceClass:
            """Resolve the package's own facade class bound to one family letter.

            Returns:
                The native facade class the package publishes under ``letter``.

            Raises:
                ValueError: The package declares no such facade class.

            """
            family = FlextInfraUtilitiesCodegenNamespace.facade_families()[letter]
            facade = (
                self.project
                .get_module(f"{self.source_package_name}.{family.module}")
                .get_attribute(letter)
                .get_object()
            )
            if not self.py_class(facade):
                message = f"package facade is not a native class: {letter}"
                raise ValueError(message)
            return facade

        def _source_letter_provider(
            self,
            letter: str,
            references: frozenset[str] = frozenset(),
            *,
            in_family: bool,
        ) -> str:
            """Elect the upstream package whose facade the package's letter composes.

            Inside the package's own families a letter is imported from the
            upstream package its facade extends, never from the package itself.

            Returns:
                The unique foreign package of the facade's direct bases.

            Raises:
                ValueError: The facade extends no or several foreign packages.

            """
            # Own intermediate bases (a family ``*Base`` class) are traversed:
            # the providers are the first foreign facades in the composition.
            providers: set[str] = set()
            pending = list(self._source_facade_class(letter).get_superclasses())
            while pending:
                base = pending.pop()
                if not self.py_class(base):
                    continue
                root = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    base.get_module(), source_project=self.project
                ).partition(".")[0]
                if root == self.source_package_name:
                    pending.extend(base.get_superclasses())
                else:
                    providers.add(root)
            if not providers:
                # The foundation package composes no foreign facade: its own
                # facade is the only provider of its letter.
                return self.source_package_name
            own_declared = self._source_letter_own_members(letter)
            own_references = references & own_declared
            if own_references and in_family:
                # Inside the own family an own member is spelled through its
                # family class (ENFORCE-051); binding the own letter would make
                # the family import its partially initialized package.
                message = (
                    f"own-namespace reference in a {letter} family module: "
                    f"{sorted(own_references)}; spell it through its family "
                    "class (ENFORCE-051)"
                )
                raise ValueError(message)
            if not in_family:
                # Modules outside the families read every letter from their
                # own package root, whose facade composes every upstream.
                return self.source_package_name
            if len(providers) > 1 and references:
                # A composed letter binds the direct upstream whose facade
                # exposes every referenced member, inherited ones included.
                providers = {
                    provider
                    for provider in providers
                    if self._source_letter_exposes(provider, letter, references)
                }
                if len(providers) > 1:
                    # Several upstreams inherit the members: the common base
                    # that declares them is the provider. When the members are
                    # declared at different levels, the most derived declaring
                    # base exposes them all through its own inheritance.
                    providers = {
                        provider
                        for provider in {
                            self._source_letter_declaring_package(letter, reference)
                            for reference in references
                        }
                        if self._source_letter_exposes(provider, letter, references)
                    }
            if len(providers) != 1:
                message = (
                    f"facade {letter} has no unique upstream package: "
                    f"{self.source_package_name} -> {sorted(providers)}; "
                    f"references={sorted(references)}"
                )
                raise ValueError(message)
            return next(iter(providers))

        def _source_wrap_overflowing_spellings(
            self, path: Path, source: str, spellings: tuple[str, ...]
        ) -> str:
            """Let respelled annotations that outgrow the line length wrap.

            A family spelling can exceed the declared line length where the
            formatter cannot split it (one annotated parameter per line);
            parenthesizing that annotation lets the formatter wrap it.

            Returns:
                The normalized source, rewrapped only where a line overflowed.

            """
            limit = self._source_line_length()
            lines = source.splitlines(keepends=True)
            for index, line in enumerate(lines):
                if len(line.rstrip("\n")) <= limit:
                    continue
                for spelling in spellings:
                    lines[index] = re.sub(
                        rf"(:\s*){re.escape(spelling)}(?![\w.])",
                        rf"\1({spelling})",
                        lines[index],
                    )
                # Family spellings emitted by the projection itself are
                # dotted annotations too; any that still overflows wraps.
                if len(lines[index].rstrip("\n")) > limit:
                    lines[index] = re.sub(
                        r"(:\s*)([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)(\s*(?:,|\)|=|$))",
                        r"\1(\2)\3",
                        lines[index],
                        count=1,
                    )
            wrapped = "".join(lines)
            if wrapped == source:
                return source
            return FlextInfraUtilitiesProtectedEditLinting.normalize_python_text(
                path, wrapped
            ).unwrap()

        def _source_line_length(self) -> int:
            """Read the line length the repository declares for Ruff.

            Returns:
                ``[tool.ruff] line-length`` from the repository manifest.

            Raises:
                ValueError: The manifest declares no Ruff line length.

            """
            manifest = self.repository_root / "pyproject.toml"
            declared = (
                tomllib
                .loads(self.project.source_text(manifest))
                .get("tool", {})
                .get("ruff", {})
                .get("line-length")
            )
            if not isinstance(declared, int):
                message = f"repository declares no Ruff line-length: {manifest}"
                raise ValueError(message)
            return declared

        @staticmethod
        def module_name_for(relative: Path) -> str:
            """Name the module of one repository-relative source path.

            A ``src`` layout and a repository namespace package share the rule:
            the leading ``src`` segment is dropped only when present.

            Returns:
                The dotted module name of ``relative``.

            """
            parts = relative.with_suffix("").parts
            return ".".join(parts[1:] if parts and parts[0] == "src" else parts)

        @staticmethod
        def _source_model_base_members() -> frozenset[str]:
            """Name the public members of the mirrored core model contract.

            Returns:
                Every public member the ``p.Model`` protocol chain declares.

            """
            return frozenset(
                name
                for contract in p.Model.__mro__
                if is_protocol(contract)
                for name in vars(contract)
                if not name.startswith("_")
            )

        def _source_letter_exposes(
            self, provider: str, letter: str, references: frozenset[str]
        ) -> bool:
            """Whether ``provider``'s facade exposes every referenced member.

            Returns:
                True when each reference resolves on the provider's letter,
                inherited members included.

            """
            module = FlextInfraUtilitiesCodegenNamespace.facade_families()[
                letter
            ].module
            scope = self._source_class(
                self.qualified_name(
                    self.project, letter, module_name=f"{provider}.{module}"
                )
            ).get_scope()
            return all(
                self.resolve_symbol(scope, reference) is not None
                for reference in references
            )

        def _source_letter_own_members(self, letter: str) -> frozenset[str]:
            """Name the members the package's own facade class declares itself.

            Returns:
                The nested class and alias names in the own facade's body.

            """
            declaration = self._source_facade_class(letter).get_ast()
            if not isinstance(declaration, ast.ClassDef):
                return frozenset()
            return frozenset(
                statement.name
                for statement in declaration.body
                if isinstance(statement, ast.ClassDef)
            )

        def _source_letter_declaring_package(self, letter: str, member: str) -> str:
            """Name the package whose facade class declares ``member`` itself.

            Returns:
                The root package of the first facade class in the composition
                order that declares ``member`` in its own body.

            Raises:
                ValueError: No facade class in the composition declares ``member``.

            """
            for base in self._source_facade_class(letter).get_mro()[1:]:
                if not self.py_class(base):
                    continue
                declaration = base.get_ast()
                if not isinstance(declaration, ast.ClassDef):
                    continue
                declared: set[str] = set()
                for statement in declaration.body:
                    if isinstance(statement, ast.ClassDef):
                        declared.add(statement.name)
                    elif isinstance(statement, ast.TypeAlias) and isinstance(
                        statement.name, ast.Name
                    ):
                        declared.add(statement.name.id)
                    elif isinstance(statement, ast.AnnAssign) and isinstance(
                        statement.target, ast.Name
                    ):
                        declared.add(statement.target.id)
                    elif isinstance(statement, ast.Assign):
                        declared.update(
                            target.id
                            for target in statement.targets
                            if isinstance(target, ast.Name)
                        )
                if member in declared:
                    return FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                        base.get_module(), source_project=self.project
                    ).partition(".")[0]
            message = f"no facade class declares {letter}.{member}"
            raise ValueError(message)

        def _source_binding_declaration(
            self, binding: p.Infra.RopePyName
        ) -> tuple[str, tuple[str, ...] | None] | None:
            """Locate the declaring module and class path of one native binding.

            Returns:
                The declaring module with the qualified path of its class or type
                alias, ``None`` as path for another assignment, or ``None`` when
                the binding has no source declaration.

            """
            value = binding.get_object()
            if self.py_class(value):
                module, qualified = self._source_class_identity(value)
                return module, tuple(qualified.split("."))
            alias = self.annotation_alias_definition(binding)
            if alias is not None:
                declaration, lexical = alias
                names: list[str] = []
                scope = lexical
                while scope.parent is not None:
                    names.append(scope.pyobject.get_name())
                    scope = scope.parent
                module = FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                    lexical.pyobject.get_module(), source_project=self.project
                )
                return module, (*reversed(names), declaration.name.id)
            supplier = FlextInfraUtilitiesRopeRuntime.source_import_binding(binding)
            if supplier is None:
                return None
            module, _line = FlextInfraUtilitiesRopeRuntime.definition_location(supplier)
            if module is None:
                return None
            return module.get_name(), None

        def _source_planned_protocol(self, route: str) -> tuple[str, str, str] | None:
            """Locate the holder that this projection will generate for a public route.

            A public Protocol route whose contract is generated by the same
            transaction has no native declaration yet: its holder, module and
            member follow from the model declaration it projects.

            Returns:
                The member path, holder class and holder module, or ``None`` when no
                projected model owns ``route``.

            """
            if self.package is None:
                return None
            routes = [
                model_route
                for model_route, public in self.source_model_protocol_routes.items()
                if public == route
            ]
            alias = self.source_model_aliases.get(route)
            if not routes and alias is not None:
                destination, _statement, _tree, _model = alias
                relative = destination.relative_to(self.package / "_protocols")
                return (
                    route.rpartition(".")[2],
                    self._source_generated_holder(destination),
                    ".".join((
                        self.source_package_name,
                        "_protocols",
                        *relative.with_suffix("").parts,
                    )),
                )
            if len(routes) != 1:
                return None
            module = max(
                (
                    name
                    for name in self.source_module_names.values()
                    if routes[0].startswith(f"{name}.")
                ),
                key=len,
            )
            relative = module.removeprefix(f"{self.source_package_name}._models.")
            destination = (
                self.package
                / "_protocols"
                / Path(*relative.split(".")).with_suffix(".py")
            )
            authored = self.project.source_query(
                destination, "isfile"
            ) and not self.project.source_text(destination).startswith(
                c.Infra.AUTOGEN_HEADER
            )
            return (
                self.source_model_protocols[routes[0]],
                self._source_authored_protocol_holder(
                    destination, self.source_package_name
                )
                if authored
                else self._source_generated_holder(destination),
                f"{self.source_package_name}._protocols.{relative}",
            )

        def _source_family_references(
            self, expression: ast.expr, scope: p.Infra.RopeScope
        ) -> ast.expr:
            """Spell every own-letter reference through its declaring family class.

            Inside a family package the package's own letters are forbidden: a
            member the package declares is reached through the family class that
            declares it, and the class is imported from its family package. A
            member an upstream package declares keeps its letter spelling, which
            the projection imports from that upstream package.

            Returns:
                The expression without own-letter chains that a family class owns.

            Raises:
                ValueError: An own-letter chain names no declared family member.

            """
            families = FlextInfraUtilitiesCodegenNamespace.facade_families()
            owner = self

            class Rewrite(ast.NodeTransformer):
                @override
                def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
                    root = node
                    while isinstance(root.value, ast.Attribute):
                        root = root.value
                    if not isinstance(root.value, ast.Name) or root.value.id not in (
                        families
                    ):
                        return self.generic_visit(node)
                    letter = root.value.id
                    bound = owner.resolve_symbol(scope, letter)
                    if bound is not None:
                        declared = owner._source_binding_declaration(bound)
                        if (
                            declared is None
                            or declared[0].partition(".")[0]
                            != owner.source_package_name
                        ):
                            return node
                    attributes: list[str] = []
                    leaf: ast.expr = node
                    while isinstance(leaf, ast.Attribute):
                        attributes.insert(0, leaf.attr)
                        leaf = leaf.value
                    facade = owner.project.get_module(
                        f"{owner.source_package_name}.{families[letter].module}"
                    )
                    # The declaring family class is the longest prefix naming a
                    # class or type alias; the rest is member access on it.
                    for size in range(len(attributes), 0, -1):
                        prefix = ".".join((letter, *attributes[:size]))
                        member = owner.resolve_symbol(facade.get_scope(), prefix)
                        declared = (
                            owner._source_binding_declaration(member)
                            if member is not None
                            else None
                        )
                        if declared is None or declared[1] is None:
                            continue
                        module, path = declared
                        if module.partition(".")[0] != owner.source_package_name:
                            return node
                        family = module.rpartition(".")[0]
                        if not family.rpartition(".")[2].startswith("_"):
                            continue
                        owner.source_family_classes[path[0]] = (family, module, True)
                        return ast.copy_location(
                            ast.parse(
                                ".".join((*path, *attributes[size:])), mode="eval"
                            ).body,
                            node,
                        )
                    planned = owner._source_planned_protocol(ast.unparse(node))
                    if planned is None:
                        message = (
                            "own-letter reference has no family class: "
                            f"{ast.unparse(node)}"
                        )
                        raise ValueError(message)
                    member_path, holder, module = planned
                    owner.source_family_classes[holder] = (
                        module.rpartition(".")[0],
                        module,
                        False,
                    )
                    return ast.copy_location(
                        ast.parse(f"{holder}.{member_path}", mode="eval").body, node
                    )

            rewritten = Rewrite().visit(expression)
            if not isinstance(rewritten, ast.expr):
                message = "family reference projection is not an expression"
                raise TypeError(message)
            return ast.fix_missing_locations(rewritten)

        def _source_imported_model_route(
            self, expression: str, tree: ast.Module, model: ast.ClassDef
        ) -> str | None:
            """Resolve one first-party model import without name-only selection.

            Returns:
                The exact first-party model route, or ``None`` for other imports.

            Raises:
                ValueError: The imported owner is shadowed or ambiguous.

            """
            root, _, suffix = expression.partition(".")
            routes: set[str] = set()
            foreign_binding = False
            for statement in tree.body:
                if isinstance(statement, ast.ImportFrom) and statement.level == 0:
                    for alias in statement.names:
                        if (alias.asname or alias.name) != root:
                            continue
                        if statement.module is None or not statement.module.startswith(
                            f"{self.source_package_name}._models."
                        ):
                            exported = self.source_model_package_exports.get((
                                statement.module or "",
                                alias.name,
                            ))
                            if exported is None:
                                foreign_binding = True
                                continue
                            routes.add(f"{exported}.{suffix}")
                        else:
                            routes.add(f"{statement.module}.{alias.name}.{suffix}")
                if isinstance(statement, ast.Import):
                    for alias in statement.names:
                        local = alias.asname or alias.name.partition(".")[0]
                        if local != root:
                            continue
                        if not alias.name.startswith(
                            f"{self.source_package_name}._models."
                        ):
                            foreign_binding = True
                            continue
                        routes.add(f"{alias.name}.{suffix}")
            shadowed = any(
                root in self._source_bound_names(statement)
                for statement in (*tree.body, *model.body)
                if not isinstance(statement, ast.Import | ast.ImportFrom)
            )
            if shadowed or foreign_binding or len(routes) > 1:
                if root != "m" and (shadowed or len(routes) > 1):
                    message = f"model import owner is shadowed or ambiguous: {root}"
                    raise ValueError(message)
                if routes and foreign_binding:
                    message = f"model import has competing owners: {root}"
                    raise ValueError(message)
            return next(iter(routes), None)

        def _source_model_facade_binding(
            self, tree: ast.Module, model: ast.ClassDef
        ) -> bool:
            """Authenticate one import of this package's public model facade.

            Returns:
                Whether ``m`` is bound only to the package's model facade.

            """
            owners = [
                statement.module
                for statement in tree.body
                if isinstance(statement, ast.ImportFrom)
                for alias in statement.names
                if alias.name == "m" and (alias.asname or alias.name) == "m"
            ]
            shadowed = any(
                "m" in self._source_bound_names(statement)
                for statement in (*tree.body, *model.body)
                if not isinstance(statement, ast.Import | ast.ImportFrom)
            )
            return (
                len(owners) == 1
                and owners[0] is not None
                and owners[0].partition(".")[0] in self.source_model_facade_import_roots
                and not shadowed
            )

        @classmethod
        def _source_typing_bindings(
            cls, tree: ast.Module, model: ast.ClassDef, symbol: str
        ) -> frozenset[str]:
            """Resolve one exact imported ``typing`` annotation spelling.

            Returns:
                Exact aliases imported from ``typing`` or ``typing_extensions``.

            Raises:
                ValueError: If a canonical import is shadowed or ambiguous.

            """
            modules = {"typing", "typing_extensions"}
            bindings = {
                alias.asname or alias.name
                for statement in tree.body
                if isinstance(statement, ast.ImportFrom) and statement.module in modules
                for alias in statement.names
                if alias.name == symbol
            }
            bindings.update(
                f"{alias.asname or alias.name.partition('.')[0]}.{symbol}"
                for statement in tree.body
                if isinstance(statement, ast.Import)
                for alias in statement.names
                if alias.name in modules
            )
            roots = frozenset(name.partition(".")[0] for name in bindings)
            shadowed = {
                name
                for statement in (*tree.body, *model.body)
                if not isinstance(statement, ast.Import | ast.ImportFrom)
                for name in cls._source_bound_names(statement)
            }
            ambiguous_imports = {
                name
                for statement in tree.body
                if isinstance(statement, ast.Import | ast.ImportFrom)
                for name in cls._source_bound_names(statement)
                if name in roots
                and not cls._source_typing_import(statement, name, symbol)
            }
            if roots.intersection(shadowed | ambiguous_imports):
                msg = "Annotated import is shadowed or ambiguous"
                raise ValueError(msg)
            return frozenset(bindings)

        @staticmethod
        def _source_typing_import(statement: ast.stmt, name: str, symbol: str) -> bool:
            """Prove one imported annotation provider from its source statement.

            Returns:
                Whether the statement binds ``name`` to ``typing.Annotated``.

            """
            if isinstance(statement, ast.ImportFrom):
                return statement.module in {"typing", "typing_extensions"} and any(
                    alias.name == symbol and (alias.asname or alias.name) == name
                    for alias in statement.names
                )
            if isinstance(statement, ast.Import):
                return any(
                    alias.name in {"typing", "typing_extensions"}
                    and (alias.asname or alias.name.partition(".")[0]) == name
                    for alias in statement.names
                )
            return False

        def _source_typing_payload(
            self,
            annotation: ast.expr,
            tree: ast.Module,
            model: ast.ClassDef,
            symbol: str,
        ) -> ast.expr | None:
            """Return one exact ``ClassVar`` or ``Final`` wrapped value type."""
            if not isinstance(annotation, ast.Subscript):
                return None
            bindings = self._source_typing_bindings(tree, model, symbol)
            return (
                annotation.slice if ast.unparse(annotation.value) in bindings else None
            )

        def _source_computed_field(
            self,
            declaration: ast.FunctionDef,
            tree: ast.Module,
            model: ast.ClassDef,
        ) -> bool:
            """Recognize only Pydantic computed fields bound through m or pydantic."""
            for decorator in declaration.decorator_list:
                expression = (
                    decorator.func if isinstance(decorator, ast.Call) else decorator
                )
                if (
                    isinstance(expression, ast.Attribute)
                    and isinstance(expression.value, ast.Name)
                    and expression.value.id == "m"
                    and expression.attr == "computed_field"
                    and self._source_model_facade_binding(tree, model)
                ):
                    return True
                if (
                    isinstance(expression, ast.Name)
                    and expression.id == "computed_field"
                    and any(
                        isinstance(statement, ast.ImportFrom)
                        and statement.module == "pydantic"
                        and any(
                            alias.name == "computed_field"
                            and (alias.asname or alias.name) == expression.id
                            for alias in statement.names
                        )
                        for statement in tree.body
                    )
                ):
                    return True
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

        def _source_extend_authored(
            self,
            source: str,
            owner: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            destination: Path,
            package_name: str,
            *,
            generated_source: str,
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
            annotation_updates: list[tuple[int, int, str]] = []
            offsets = [0]
            for line in source.splitlines(keepends=True):
                offsets.append(offsets[-1] + len(line))
            for node, _path, _module in classes:
                present = authored.get(node.name)
                fields = self.source_fields(node, classes)
                expected = {
                    projection.declaration.target.id: self._source_protocol_signature(
                        projection.declaration.annotation, tree, holder, destination
                    )
                    for projection in fields
                    if isinstance(projection.declaration.target, ast.Name)
                }
                if present is not None:
                    actual = {
                        field.target.id: self._source_protocol_signature(
                            field.annotation, tree, holder, destination
                        )
                        for field in present.body
                        if isinstance(field, ast.AnnAssign)
                        and isinstance(field.target, ast.Name)
                    }
                    projected = (
                        ast.get_docstring(present)
                        in c.Infra.DocumentationText.MODEL_PROTOCOL_CONTRACT.value
                    )
                    # An authored contract the projection fully covers yields to
                    # the projected one in place: the concrete model owns it.
                    covered = set(actual) <= set(expected) and {
                        statement.name
                        for statement in present.body
                        if isinstance(
                            statement, (ast.FunctionDef, ast.AsyncFunctionDef)
                        )
                    } <= {
                        *expected,
                        *(method.name for method in self.source_methods(node, classes)),
                        *self._source_model_base_members(),
                    }
                    if projected or covered:
                        emitted = next(
                            declaration
                            for declaration in ast.walk(ast.parse(generated_source))
                            if isinstance(declaration, ast.ClassDef)
                            and declaration.name == node.name
                        )
                        replacement = ast.get_source_segment(generated_source, emitted)
                        if (
                            replacement is None
                            or present.end_lineno is None
                            or present.end_col_offset is None
                        ):
                            msg = "projected contract has no source extent"
                            raise ValueError(msg)
                        annotation_updates.append((
                            offsets[present.lineno - 1] + present.col_offset,
                            offsets[present.end_lineno - 1] + present.end_col_offset,
                            replacement,
                        ))
                    elif any(
                        annotation != expected[name]
                        for name, annotation in actual.items()
                        if name in expected
                    ):
                        message = (
                            "incompatible authored protocol contract "
                            f"{owner}.{node.name}: {destination}; "
                            f"{[(name, annotation, expected[name]) for name, annotation in actual.items() if name in expected and annotation != expected[name]]}"
                        )
                        raise ValueError(message)
                    continue
                emitted = next(
                    declaration
                    for declaration in ast.walk(ast.parse(generated_source))
                    if isinstance(declaration, ast.ClassDef)
                    and declaration.name == node.name
                )
                replacement = ast.get_source_segment(generated_source, emitted)
                if replacement is None:
                    msg = "projected contract has no source extent"
                    raise ValueError(msg)
                additions.extend((
                    "    @runtime_checkable",
                    "    " + replacement,
                    "",
                ))
            for start, end, replacement in sorted(annotation_updates, reverse=True):
                source = source[:start] + replacement + source[end:]
            runtime_imports = self._source_runtime_base_imports({
                ast.unparse(base)
                for declaration in ast.walk(ast.parse(generated_source))
                if isinstance(declaration, ast.ClassDef)
                for base in declaration.bases
            })
            if not additions:
                return self._source_complete_imports(
                    source,
                    classes,
                    package_name,
                    destination,
                    runtime_imports=runtime_imports,
                )
            updated_tree = ast.parse(source, filename=str(destination))
            holder = next(
                node
                for node in updated_tree.body
                if isinstance(node, ast.ClassDef) and node.name == owner
            )
            lines = source.splitlines(keepends=True)
            if holder.end_lineno is None:
                message = (
                    f"authored protocol holder has no source extent: {destination}"
                )
                raise ValueError(message)
            lines.insert(holder.end_lineno, "\n" + "\n".join(additions).rstrip() + "\n")
            updated = "".join(lines)
            header = FlextInfraUtilitiesTransformerHeader
            for name in ("Protocol", "runtime_checkable"):
                updated = header.ensure_alias_import(
                    updated, "typing", name, runtime_required=True
                )
            return self._source_complete_imports(
                updated,
                classes,
                package_name,
                destination,
                runtime_imports=runtime_imports,
            )

        @staticmethod
        def _source_sibling_spelling(
            destination: Path, package_name: str, member: str
        ) -> tuple[str, str] | None:
            """Spell a member through the one sibling holder that declares it.

            A member authored in exactly one top-level holder of another
            module of the same family is spelled through that holder and
            imported through the family package; zero or several holders
            leave the route unresolved.

            Returns:
                The holder spelling and its family package, or ``None``.

            """
            holders: list[str] = []
            for sibling in sorted(destination.parent.glob("*.py")):
                if sibling == destination or sibling.name == c.Infra.INIT_PY:
                    continue
                for statement in ast.parse(sibling.read_text()).body:
                    if not isinstance(statement, ast.ClassDef):
                        continue
                    holders.extend(
                        statement.name
                        for nested in statement.body
                        if isinstance(nested, ast.ClassDef) and nested.name == member
                    )
            if len(holders) != 1:
                return None
            return (
                f"{holders[0]}.{member}",
                f"{package_name}.{destination.parent.name}",
            )

        def _source_complete_imports(
            self,
            source: str,
            classes: list[tuple[ast.ClassDef, tuple[str, ...], ast.Module]],
            package_name: str,
            destination: Path,
            *,
            runtime_imports: tuple[str, ...] = (),
        ) -> str:
            """Reconcile runtime bases separately from authored annotations.

            Returns:
                Source with every required provider bound exactly once.

            Raises:
                ValueError: A required provider cannot bind in the authored module.

            """
            for statement in runtime_imports:
                imported = ast.parse(statement).body[0]
                if not isinstance(imported, ast.ImportFrom) or imported.level:
                    msg = f"runtime base import is not an absolute from-import: {statement}"
                    raise ValueError(msg)
                for alias in imported.names:
                    source = FlextInfraUtilitiesTransformerHeader.ensure_alias_import(
                        source,
                        imported.module,
                        ast.unparse(alias),
                        runtime_required=True,
                    )
            tree = ast.parse(source)
            # Inside the own family an own-namespace route this projection
            # generates is spelled through its planned holder class, imported
            # through the holder's family package (ENFORCE-051).
            own_namespaces = self._source_letter_own_members("p")
            planned_spellings: dict[str, tuple[str, str]] = {}
            authored_spellings: dict[str, str] = {}
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Attribute)
                    and isinstance(node.value.value, ast.Name)
                    and node.value.value.id == "p"
                    and node.value.attr in own_namespaces
                ):
                    route = f"p.{node.value.attr}.{node.attr}"
                    planned = self._source_planned_protocol(route)
                    if planned is not None:
                        _member, holder, module = planned
                        planned_spellings[route] = (
                            f"{holder}.{node.attr}",
                            module.rpartition(".")[0],
                        )
                        continue
                    # A member already authored in a holder of this very module
                    # is spelled through that holder and needs no import.
                    authored = next(
                        (
                            statement.name
                            for statement in tree.body
                            if isinstance(statement, ast.ClassDef)
                            and any(
                                isinstance(member, ast.ClassDef)
                                and member.name == node.attr
                                for member in statement.body
                            )
                        ),
                        None,
                    )
                    if authored is not None:
                        authored_spellings[route] = f"{authored}.{node.attr}"
                    elif sibling := self._source_sibling_spelling(
                        destination, package_name, node.attr
                    ):
                        planned_spellings[route] = sibling
            for route, (spelling, family) in planned_spellings.items():
                source = re.sub(
                    rf"(?<![\w.]){re.escape(route)}(?![\w])", spelling, source
                )
                source = FlextInfraUtilitiesTransformerHeader.ensure_alias_import(
                    source, family, spelling.partition(".")[0]
                )
            for route, spelling in authored_spellings.items():
                source = re.sub(
                    rf"(?<![\w.]){re.escape(route)}(?![\w])", spelling, source
                )
            if planned_spellings or authored_spellings:
                tree = ast.parse(source)
            p_references = frozenset(
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "p"
            )
            unresolved = sorted({
                f"p.{node.value.attr}.{node.attr}"
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "p"
                and node.value.attr in own_namespaces
            })
            if unresolved:
                message = (
                    f"own-namespace references in a p family module {destination}: "
                    f"{unresolved}; spell them through their family classes "
                    "(ENFORCE-051)"
                )
                raise ValueError(message)
            # A module that references no ``p`` member binds no provider.
            provider = (
                self._source_letter_provider("p", p_references, in_family=True)
                if p_references
                else None
            )
            # The module-wide election sees every reference; any other binding
            # of the letter yields to it.
            root_imports = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                and not node.level
                and provider is not None
                and node.module != provider
                and any(
                    alias.name == "p" and alias.asname is None for alias in node.names
                )
            ]
            if root_imports:
                lines = source.splitlines(keepends=True)
                for imported in sorted(
                    root_imports, key=lambda node: node.lineno, reverse=True
                ):
                    if imported.end_lineno is None or imported.end_col_offset is None:
                        msg = f"protocol import has no source extent: {destination}"
                        raise ValueError(msg)
                    start = (
                        sum(map(len, lines[: imported.lineno - 1]))
                        + imported.col_offset
                    )
                    end = (
                        sum(map(len, lines[: imported.end_lineno - 1]))
                        + imported.end_col_offset
                    )
                    retained = [alias for alias in imported.names if alias.name != "p"]
                    declarations = (
                        [
                            ast.unparse(
                                ast.ImportFrom(
                                    module=package_name, names=retained, level=0
                                )
                            )
                        ]
                        if retained
                        else []
                    )
                    declarations.append(f"from {provider} import p")
                    source = (
                        source[:start]
                        + ("\n" + " " * imported.col_offset).join(declarations)
                        + source[end:]
                    )
            for statement in self.source_annotation_imports(
                classes, package_name, destination
            ):
                for imported in ast.walk(ast.parse(statement)):
                    if not isinstance(imported, (ast.Import, ast.ImportFrom)):
                        continue
                    for alias in imported.names:
                        module = (
                            f"{'.' * imported.level}{imported.module or ''}"
                            if isinstance(imported, ast.ImportFrom)
                            else None
                        )
                        try:
                            source = FlextInfraUtilitiesTransformerHeader.ensure_alias_import(
                                source,
                                module,
                                ast.unparse(alias),
                                runtime_required=(
                                    isinstance(imported, ast.ImportFrom)
                                    and imported.module == "typing"
                                    and alias.name in {"Protocol", "runtime_checkable"}
                                ),
                            )
                        except ValueError as error:
                            message = (
                                f"{destination}: cannot bind {alias.name} from "
                                f"{ast.unparse(imported)}: {error}"
                            )
                            raise ValueError(message) from error
            if provider is not None:
                source = FlextInfraUtilitiesTransformerHeader.ensure_alias_import(
                    source, provider, "p"
                )
            normalized = normalize_protocol_source(
                source, package_name=package_name, filename=str(destination)
            )
            return self._source_wrap_overflowing_spellings(
                destination,
                normalized,
                tuple(spelling for spelling, _family in planned_spellings.values()),
            )

        def _source_protocol_signature(
            self,
            annotation: ast.expr,
            tree: ast.Module,
            holder: ast.ClassDef,
            destination: Path,
            *,
            self_identity: str | None = None,
        ) -> str:
            """Compare structural annotations by their native declaring identities.

            ``self_identity`` names the Protocol being compared: inside it,
            ``typing.Self`` denotes that Protocol, which the model contract
            references by its public route.

            Returns:
                An identity-normalized signature with schema metadata removed.

            """
            bindings = self._source_typing_bindings(tree, holder, "Annotated")
            module_name = self.module_name_for(
                destination.relative_to(self.repository_root)
            )
            scope = self.project.get_module(module_name).get_scope()
            facade = self.project.get_module(
                f"{self.source_package_name}.protocols"
            ).get_attribute("p")
            projector = self

            class Normalize(ast.NodeTransformer):
                @override
                def visit_Name(self, node: ast.Name) -> ast.expr:
                    if self_identity is not None and projector._denotes(
                        node, scope, "typing", "Self"
                    ):
                        return ast.copy_location(
                            ast.Constant(value=self_identity), node
                        )
                    return self._identity(node)

                @override
                def visit_Attribute(self, node: ast.Attribute) -> ast.expr:
                    return self._identity(node)

                def _identity(self, node: ast.Name | ast.Attribute) -> ast.expr:
                    expression = ast.unparse(node)
                    binding = (
                        projector._member(facade, expression.removeprefix("p."))
                        if expression.startswith("p.")
                        else projector.resolve_symbol(scope, node)
                    )
                    family = projector.source_family_classes.get(
                        expression.partition(".")[0]
                    )
                    if binding is None and family is not None and family[2]:
                        # A projected family class is spelled before its import
                        # exists in the compared module: resolve it where it is
                        # declared, so both spellings share one identity. A member
                        # this projection still has to emit has no declaration
                        # yet; its declaring route is its identity.
                        holder_name, _separator, member = expression.partition(".")
                        holder_class = projector.qualified_name(
                            projector.project, holder_name, module_name=family[1]
                        ).get_object()
                        if member and member.partition(".")[0] not in (
                            holder_class.get_attributes()
                        ):
                            return ast.copy_location(
                                ast.Constant(value=f"{family[1]}:{expression}"), node
                            )
                        binding = projector.qualified_name(
                            projector.project, expression, module_name=family[1]
                        )
                    if binding is not None:
                        alias = projector.annotation_alias_definition(binding)
                        identity = (
                            f"{alias[1].pyobject.get_module().get_name()}:{alias[0].lineno}"
                            if alias is not None
                            else FlextInfraUtilitiesRopeRuntime.native_object_identity(
                                binding.get_object()
                            )
                        )
                        if identity:
                            return ast.copy_location(ast.Constant(value=identity), node)
                    return node

                @override
                def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
                    if ast.unparse(node.value) in bindings:
                        if not isinstance(node.slice, ast.Tuple) or not node.slice.elts:
                            msg = "Annotated field has no value type"
                            raise ValueError(msg)
                        return self.visit(node.slice.elts[0])
                    return self.generic_visit(node)

            normalized = Normalize().visit(copy.deepcopy(annotation))
            return ast.unparse(ast.fix_missing_locations(normalized))

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
                documentation_language=self.documentation_language,
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
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
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
            tree = ast.parse(rendered)
            self._normal_authored_imports(tree, module)
            for statement in ast.walk(tree):
                if (
                    not isinstance(statement, ast.ImportFrom)
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
            holder = next(node for node in tree.body if isinstance(node, ast.ClassDef))
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
                if isinstance(node, ast.ClassDef)
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
                origin = declaring.get_resource()
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
                The projected dependency, or None for a non-model symbol.

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
                FlextInfraUtilitiesRopeRuntime.expression_name(
                    scope, ast.unparse(node)
                ),
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
