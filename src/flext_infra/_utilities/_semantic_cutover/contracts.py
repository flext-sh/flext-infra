"""Identity-constrained contract migration through native Rope ChangeSets.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import inspect
import sys
from collections.abc import (
    Callable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from contextlib import AbstractContextManager
from functools import partial
from pathlib import Path
from typing import NamedTuple

from flext_cli import cli, u
from typing_extensions import TypeForm

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesDependencyRequirements,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectDocument
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope._analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesSemanticConstantSources,
    FlextInfraUtilitiesSemanticCutoverClassScope,
    FlextInfraUtilitiesSemanticCutoverModelFields,
    FlextInfraUtilitiesSemanticDeclarationRelocation,
    FlextInfraUtilitiesSemanticDeclarationRetirement,
    FlextInfraUtilitiesSemanticDelegations,
    FlextInfraUtilitiesSemanticFamilyTypeReferences,
)
from flext_infra._utilities._semantic_cutover.model_envelopes import (
    FlextInfraUtilitiesSemanticModelEnvelopes,
)
from flext_infra._utilities._semantic_cutover.model_field_contracts import (
    FlextInfraUtilitiesSemanticModelFieldContracts,
)
from flext_infra._utilities._semantic_cutover.opaque_ports import (
    FlextInfraUtilitiesSemanticOpaquePorts,
)


class FlextInfraUtilitiesSemanticContracts(
    FlextInfraUtilitiesSemanticCutoverModelFields,
    FlextInfraUtilitiesSemanticModelFieldContracts,
    FlextInfraUtilitiesSemanticModelEnvelopes,
):
    """Reuse the joint semantic loop and immutable Rope source inventory."""

    class _AnnotationMemberOwner(NamedTuple):
        """Authenticated source and destination namespaces for one rule."""

        rule: p.Infra.RopeContractRule
        source: str
        source_owner: p.Infra.RopeSourceClass
        target: str
        owner: str
        members: Mapping[str, p.Infra.RopePyName]

    class _AnnotationMemberState(NamedTuple):
        """One annotation offset and its immutable model-owner plan."""

        owner: FlextInfraUtilitiesSemanticContracts._AnnotationMemberOwner
        offset: int

    class _ContractSources(Mapping[Path, str]):
        """Read-only live view of staged updates over authenticated source inputs."""

        def __init__(
            self,
            updates: Mapping[Path, str],
            originals: Mapping[Path, str],
        ) -> None:
            """Retain both source layers by reference without widening their access."""
            self._updates = updates
            self._originals = originals

        def __getitem__(self, path: Path) -> str:
            """Return the staged value when present, otherwise its original input."""
            return (
                self._updates[path] if path in self._updates else self._originals[path]
            )

        def __iter__(self) -> Iterator[Path]:
            """Preserve original key order and append newly staged paths.

            Yields:
                Each source path once, in the source overlay's stable order.

            """
            yield from self._originals
            yield from (path for path in self._updates if path not in self._originals)

        def __len__(self) -> int:
            """Count each path once without materializing or copying source data.

            Returns:
                The number of distinct paths in the live overlay.

            """
            return len(self._originals) + sum(
                path not in self._originals for path in self._updates
            )

    @classmethod
    def _plan_rope_contracts(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[t.Infra.RopeSourcePath, str],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Return source-authenticated edits for the normalization phase's rules.

        Returns:
            The resulting semantic migration edits.

        """
        computed = cls.plan_computed_model_field_contracts(
            workspace, sources, workspace.model_protocol_routes
        )
        if computed.failure:
            return computed
        working: dict[t.Infra.RopeSourcePath, str] = dict(sources)
        for edit in computed.value:
            working[edit.file_path] = edit.updated_source
        additions: list[p.Infra.RopeSignatureAddition] = []
        removals: list[p.Infra.RopeSignatureRemoval] = []
        transfers: list[p.Infra.RopeMethodTransfer] = []
        rules = cls.declared_contract_rules(
            workspace.repository_root,
            signature_additions=additions,
            signature_removals=removals,
            method_transfers=transfers,
        )
        standard = cls.plan_contract_rules(
            workspace,
            working,
            tuple(
                rule
                for rule in rules
                if rule.phase == c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION
            ),
            options=m.Infra.ContractAdmissionOptions.model_validate({
                "signature_additions": additions,
                "signature_removals": removals,
                "method_transfers": transfers,
            }),
        )
        if standard.failure:
            return standard
        for edit in standard.value:
            working[edit.file_path] = edit.updated_source
        all_edits: list[p.Infra.SemanticMigrationEdit] = []
        for path, original in sources.items():
            if working.get(path) != original:
                changes: list[str] = []
                for edit in (*computed.value, *standard.value):
                    if edit.file_path == path:
                        changes.extend(edit.changes)
                all_edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=original,
                        updated_source=working[path],
                        changes=tuple(
                            dict.fromkeys(changes or ("contract normalization",))
                        ),
                    )
                )
        return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(tuple(all_edits))

    @staticmethod
    def declared_contract_rules(
        repository_root: t.Infra.RopeSourcePath,
        *,
        signature_additions: MutableSequence[p.Infra.RopeSignatureAddition]
        | None = None,
        method_transfers: MutableSequence[p.Infra.RopeMethodTransfer] | None = None,
        signature_removals: MutableSequence[p.Infra.RopeSignatureRemoval] | None = None,
        catalogue_inputs: MutableSequence[p.Cli.AtomicFileState] | None = None,
    ) -> Sequence[p.Infra.RopeContractRule]:
        """Load universal and elected repo rules with unique IDs and known families.

        Returns:
            Authenticated rules from the packaged and elected project catalogues.

        Raises:
            ValueError: If a catalogue disappears, IDs collide, or ownership or
                family declarations are invalid.

        """
        packaged = (
            type(config).ssot_config_dir().parent
            / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        )
        roots = dict.fromkeys((
            repository_root.resolve(),
            *FlextInfraUtilitiesProjectDiscovery.discover_rope_project_roots(
                repository_root
            ),
        ))
        catalogues: tuple[tuple[Path, Path | None], ...] = (
            (packaged, None),
            *(
                (root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH, root)
                for root in roots
                if root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH != packaged
                and (root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH).is_file()
            ),
        )
        rules: MutableSequence[p.Infra.RopeContractRule] = []
        for catalogue, owner_root in catalogues:
            declared, state = (
                FlextInfraUtilitiesSemanticContracts._extend_declared_contract_rules(
                    catalogue,
                    owner_root,
                    rules,
                )
            )
            if catalogue_inputs is not None:
                catalogue_inputs.append(state)
            if signature_additions is not None:
                signature_additions.extend(declared.signature_additions)
            if signature_removals is not None:
                signature_removals.extend(declared.signature_removals)
            if method_transfers is not None:
                method_transfers.extend(declared.method_transfers)
        ids = [rule.id for rule in rules]
        ids.extend(addition.id for addition in signature_additions or ())
        ids.extend(removal.id for removal in signature_removals or ())
        ids.extend(transfer.id for transfer in method_transfers or ())
        if len(ids) != len(set(ids)):
            message = "duplicate Rope contract rule identities"
            raise ValueError(message)
        families = FlextInfraUtilitiesCodegenNamespace.facade_families()
        for rule in rules:
            unknown = set(rule.families).difference(families)
            if unknown:
                message = f"{rule.id}: undeclared Rope contract families: {unknown}"
                raise ValueError(message)
        return tuple(rules)

    @staticmethod
    def _extend_declared_contract_rules(
        catalogue: Path,
        owner_root: Path | None,
        rules: MutableSequence[p.Infra.RopeContractRule],
    ) -> tuple[p.Infra.RopeContractRules, p.Cli.AtomicFileState]:
        """Decode one catalogue and admit only rules owned by its project.

        Returns:
            The validated declarations and their original source observation.

        Raises:
            ValueError: A declared ownership transfer is not project-owned.

        """
        state = u.Cli.atomic_read_binary_file_state(catalogue, required=True).unwrap()
        if state.content is None:
            message = f"Rope contract catalogue disappeared: {catalogue}"
            raise ValueError(message)
        declared = u.Cli.config_decode(
            u.Cli.yaml_parse(state.content.decode(c.DEFAULT_ENCODING)).unwrap(),
            m.Infra.RopeContractRules,
            source_path=catalogue,
            metadata=m.Infra.RopeContractOrigin(owner_root=owner_root),
        )
        if declared.method_transfers and owner_root is None:
            message = "method ownership transfer requires its project catalogue"
            raise ValueError(message)
        for rule in declared.rules:
            if rule.ownership_transfer is not None and owner_root is None:
                message = (
                    f"{rule.id}: ownership transfer requires its project catalogue"
                )
                raise ValueError(message)
            rules.append(rule)
        return declared, state

    @classmethod
    def plan_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[t.Infra.RopeSourcePath, str],
        rules: Sequence[p.Infra.RopeContractRule],
        *,
        options: p.Infra.ContractAdmissionOptions | None = None,
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan native changes for the selected contract rules.

        The supplied ``sources`` are the phase's authority: every source whose
        bytes differ from the bound native view is bound before any native
        selection, so a re-plan over applied edits reads those edits.

        Returns:
            Edits for the selected native contract rules.

        """
        project = workspace.rope_project
        with project.source_view(
            declared_files=FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                Path(project.root.real_path),
                (),
                {
                    path: source
                    for path, source in sources.items()
                    if not project.source_query(path, "isfile")
                    or project.source_text(path) != source
                },
                source_project=project,
            ),
            additional_source_folders=None,
        ):
            return cls._plan_contract_rules_in_view(
                workspace, sources, rules, options=options
            )

    @classmethod
    def _plan_contract_rules_in_view(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[t.Infra.RopeSourcePath, str],
        rules: Sequence[p.Infra.RopeContractRule],
        *,
        options: p.Infra.ContractAdmissionOptions | None,
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan the selected contract rules over the bound phase sources.

        Returns:
            Edits for the selected native contract rules.

        """
        analysis_sources: dict[Path, str] = {}
        inserted: dict[Path, tuple[str, ...]] = {}
        dependency_views: dict[Path, str] = {}
        for selection in rules:
            revision = selection.source_revision
            if (
                selection.operation
                == c.Infra.RopeContractOperation.RETIRE_GENERIC_TYPING_WRAPPERS
                and revision is not None
            ):
                path, candidate, names = cls._generic_collection_history(
                    workspace.rope_project, selection, revision=revision
                )
                # An owned provider is an editable candidate whose historical
                # declarations are withdrawn before publication. A Python-path
                # dependency only lends its historical names to consumer
                # selection through a read-only analysis view.
                if workspace.rope_project.source_owned(path):
                    analysis_sources[path] = candidate
                    inserted[path] = names
                else:
                    dependency_views[path] = candidate
        plans = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(workspace.rope_project.root.real_path),
            (),
            analysis_sources,
            source_project=workspace.rope_project,
        )
        with workspace.rope_project.source_view(
            declared_files=plans,
            additional_source_folders=None,
            analysis_files=dependency_views,
        ):
            return cls._plan_bound_contract_rules(
                workspace, sources, rules, options, (analysis_sources, inserted)
            )

    @classmethod
    def _plan_bound_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
        rules: Sequence[p.Infra.RopeContractRule],
        options: p.Infra.ContractAdmissionOptions | None,
        witnesses: tuple[Mapping[Path, str], Mapping[Path, tuple[str, ...]]],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan effects from current consumers, retaining analysis-only witnesses.

        Returns:
            The planned semantic migration edits.

        Raises:
            ValueError: If a contract transfer is not owned or a witness is lost.

        """
        analysis_sources, inserted = witnesses
        rules = tuple(
            derived
            for rule in rules
            for derived in (
                cls._generic_collection_contract_rules(workspace.rope_project, rule)
                if rule.operation
                == c.Infra.RopeContractOperation.RETIRE_GENERIC_TYPING_WRAPPERS
                else (rule,)
            )
        )
        providers = cls._contract_receiver_sources(workspace, sources, rules)
        items = tuple(
            sorted({**dict(cls._editable_sources(sources)), **providers}.items())
        )
        if not items or not (
            rules
            or (
                options is not None
                and (
                    options.signature_additions
                    or options.signature_removals
                    or options.method_transfers
                )
            )
        ):
            return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(())
        cls._require_owned_contract_transfers(workspace, rules)
        working, applied, owned_modules = cls._apply_contract_rules(
            workspace,
            sources,
            rules,
            tuple((path, analysis_sources.get(path, source)) for path, source in items),
            options
            if options is not None
            else m.Infra.ContractAdmissionOptions.model_validate({}),
        )
        for path, names in inserted.items():
            if path not in working or not names:
                continue
            with workspace.rope_project.source_view(
                declared_files=cls._contract_source_plans(
                    workspace.rope_project, working, {path: ()}
                ),
                additional_source_folders=None,
            ) as project:
                module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix()
                        ),
                        path,
                    ),
                )
                rewrites = tuple(
                    m.Infra.SourceRewrite(
                        start=module.source_code.rfind("\n", 0, declaration.start) + 1,
                        end=module.source_code.index("\n", declaration.end) + 1,
                        text="",
                    )
                    for provider in module.get_scope().get_defined_names().values()
                    if isinstance(
                        owner := provider.get_object(), p.Infra.RopeSourceClass
                    )
                    for (
                        declaration,
                        name,
                        _body,
                    ), _parameters in cls._generic_collection_declarations(
                        module, owner
                    )
                    if module.source_code[name.start : name.end] in names
                )
                if len(rewrites) != len(names):
                    msg = (
                        "analysis-only generic declarations lost their native ownership"
                    )
                    raise ValueError(msg)
                resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    module.get_resource(), path
                )
                stripped = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                    resource, working[path], rewrites
                ).new_contents
                working[path] = (
                    FlextInfraUtilitiesSemanticDeclarationRelocation.remove_orphaned_imports(
                        project, resource, working[path], stripped
                    )
                )
                if working[path] != sources[path]:
                    applied.setdefault(path, []).append(
                        "completed analysis-only declaration withdrawal"
                    )
        return cls._finish_contract_edits(
            workspace,
            sources,
            rules,
            items,
            (working, applied, owned_modules),
        )

    @classmethod
    def _generic_collection_history(
        cls,
        project: p.Infra.RopeProject,
        selection: p.Infra.RopeContractRule,
        *,
        revision: t.NonEmptyStr,
    ) -> tuple[Path, str, tuple[str, ...]]:
        """Compose authenticated historical declarations into an analysis-only view.

        Returns:
            The historical path, source text and declared names.

        """
        _identity, provider, module, resource = cls._generic_history_provider(
            project, selection
        )
        path = Path(resource.real_path).resolve()
        current = module.source_code
        current_names = frozenset(provider.get_attributes())
        anchor, indentation = cls._generic_history_anchor(
            current, module.get_source_binding_index().fragments, provider
        )
        with cls._generic_history_view(
            project, path, cls._generic_history_source(path, revision)
        ):
            _identity, provider, module, _resource = cls._generic_history_provider(
                project, selection
            )
            declarations, names, imports = cls._generic_history_declarations(
                module, provider, current_names
            )
        candidate = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            current,
            (
                m.Infra.SourceRewrite(
                    start=anchor.start,
                    end=anchor.start,
                    text=("\n" + indentation).join(declarations) + "\n" + indentation,
                ),
            )
            if declarations
            else (),
        ).new_contents
        for import_module, members in imports.items():
            with cls._generic_history_view(project, path, candidate):
                imported = FlextInfraUtilitiesRopeImports.add_import(
                    project, resource, import_module, tuple(members), apply=False
                )
                if imported is not None:
                    candidate = imported
        return path, candidate, tuple(names)

    @staticmethod
    def _generic_history_view(
        project: p.Infra.RopeProject,
        path: Path,
        source: str,
    ) -> AbstractContextManager[p.Infra.RopeProject]:
        """Bind one provider source for analysis by its project ownership.

        An owned provider is a declared candidate of this project. A
        Python-path dependency is bound read-only: native resolution reads it
        while publication never sees it.

        Returns:
            The native source view reading the supplied provider source.

        """
        if project.source_owned(path):
            return project.source_view(
                declared_files=FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                    Path(project.root.real_path),
                    (),
                    {path: source},
                    source_project=project,
                ),
                additional_source_folders=None,
            )
        return project.source_view(
            declared_files=None,
            additional_source_folders=None,
            analysis_files={path: source},
        )

    @classmethod
    def _generic_history_provider(
        cls,
        project: p.Infra.RopeProject,
        selection: p.Infra.RopeContractRule,
    ) -> tuple[str, p.Infra.RopeSourceClass, p.Infra.RopePyModule, p.Infra.RopeFile]:
        """Authenticate the elected provider, its module and its source file.

        Returns:
            The identity constraint, provider class, module and native file.

        Raises:
            TypeError: If the provider is not a native source class or module.

            ValueError: If the constraint or the resource is missing.

        """
        (constraint,) = selection.arguments.values()
        if not isinstance(constraint, str) or not constraint.startswith("name="):
            msg = f"{selection.id}: provider requires a native name constraint"
            raise ValueError(msg)
        identity = constraint.removeprefix("name=")
        provider = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, identity
        ).get_object()
        if not isinstance(provider, p.Infra.RopeSourceClass):
            msg = f"{selection.id}: provider is not a native source class"
            raise TypeError(msg)
        module = provider.get_module()
        resource = module.get_resource()
        if resource is None:
            msg = f"{selection.id}: historical provider requires source and revision"
            raise ValueError(msg)
        return (
            identity,
            provider,
            module,
            FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                resource, identity
            ),
        )

    @staticmethod
    def _generic_history_anchor(
        current: str,
        native: Sequence[p.Infra.RopeSourceFragment],
        provider: p.Infra.RopeSourceClass,
    ) -> tuple[p.Infra.RopeSourceFragment, str]:
        """Elect the provider's type-alias anchor and its source indentation.

        Returns:
            The anchor fragment and the indentation text before it.

        """
        name = next(
            fragment
            for fragment in native
            if fragment.context.role == "type-alias-name"
            and fragment.context.structural_scope.pyobject is provider
        )
        (anchor,) = (
            fragment
            for fragment in native
            if fragment.depth == name.depth - 1
            and fragment.start <= name.start < name.end <= fragment.end
        )
        indentation = current[current.rfind("\n", 0, anchor.start) + 1 : anchor.start]
        return anchor, indentation

    @staticmethod
    def _generic_history_source(
        path: Path,
        revision: t.NonEmptyStr,
    ) -> str:
        """Read the provider's committed source at its admitted revision.

        The caller supplies its already-admitted revision and the Git identity
        owner elects the worktree root.

        Returns:
            The historical source text of the provider's file.

        """
        root = (
            FlextInfraUtilitiesGit
            .git_identity(m.Infra.GitRepoRequest(repo_root=path.parent))
            .unwrap()
            .repo_root
        )
        blobs = FlextInfraUtilitiesGit.git_committed_directory_blobs(
            root,
            path.parent.relative_to(root).as_posix(),
            revision=revision,
        ).unwrap()
        return blobs[path.name].decode(c.DEFAULT_ENCODING)

    @classmethod
    def _generic_history_declarations(
        cls,
        historical_module: p.Infra.RopePyModule,
        provider: p.Infra.RopeSourceClass,
        current_names: frozenset[str],
    ) -> tuple[list[str], list[str], dict[str, set[str]]]:
        """Compose forwarding declarations from the historical module.

        Returns:
            The declaration texts, their alias names and required imports.

        """
        declarations: list[str] = []
        names: list[str] = []
        imports: dict[str, set[str]] = {}
        for (
            declaration,
            alias,
            body,
        ), parameters in cls._generic_collection_declarations(
            historical_module,
            provider,
        ):
            alias_name = historical_module.source_code[alias.start : alias.end]
            if alias_name in current_names:
                continue
            origin = cls._generic_collection_origin(historical_module, body)
            if origin is None:
                continue
            member, native_identity, import_module = origin
            suffix = cls._generic_collection_forwarding_suffix(
                historical_module,
                declaration,
                alias_name,
                parameters,
                native_identity,
            )
            if suffix is None:
                continue
            formal = ", ".join(parameters)
            declarations.append(
                f"type {alias_name}[{formal}] = {member}[{formal}{suffix}]"
            )
            names.append(alias_name)
            if import_module is not None:
                imports.setdefault(import_module, set()).add(member)
        return declarations, names, imports

    @classmethod
    def _generic_collection_contract_rules(
        cls,
        project: p.Infra.RopeProject,
        selection: p.Infra.RopeContractRule,
    ) -> tuple[p.Infra.RopeContractRule, ...]:
        """Derive native collection substitutions from one elected provider.

        The provider's source-binding index elects declarations and their formal
        regions. Native matching proves complete forwarding bodies; neither
        alias spelling nor an independently parsed source elects a migration.

        Returns:
            Transient rules retaining exact provider and argument identities.

        """
        identity, provider, module, _resource = cls._generic_history_provider(
            project, selection
        )
        return tuple(
            derived
            for fragments, parameters in cls._generic_collection_declarations(
                module, provider
            )
            for derived in cls._generic_collection_body_rules(
                selection, identity, module, fragments, parameters
            )
        )

    @staticmethod
    def _generic_collection_declarations(
        module: p.Infra.RopePyModule,
        provider: p.Infra.RopeSourceClass,
    ) -> Iterator[
        tuple[
            tuple[
                p.Infra.RopeSourceFragment,
                p.Infra.RopeSourceFragment,
                p.Infra.RopeSourceFragment,
            ],
            tuple[str, ...],
        ]
    ]:
        """Elect only this provider's direct generic declarations.

        Yields:
            Declaration, name and body regions with their native formal names.

        Raises:
            ValueError: The source index has incomplete or constrained regions.

        """
        fragments = module.get_source_binding_index().fragments
        for name in fragments:
            if name.context.role != "type-alias-name" or (
                name.context.structural_scope.pyobject is not provider
            ):
                continue
            declarations = tuple(
                fragment
                for fragment in fragments
                if fragment.depth == name.depth - 1
                and fragment.start <= name.start < name.end <= fragment.end
            )
            if len(declarations) != 1:
                msg = "generic alias has no unique native source owner"
                raise ValueError(msg)
            declaration = declarations[0]
            parameters = tuple(
                module.source_code[fragment.start : fragment.end]
                for fragment in fragments
                if fragment.context.role == "type-parameter-token"
                and declaration.start
                <= fragment.start
                < fragment.end
                <= declaration.end
            )
            if not parameters:
                continue
            if not all(parameter.isidentifier() for parameter in parameters):
                msg = "unsupported constrained generic type parameter"
                raise ValueError(msg)
            bodies = tuple(
                fragment
                for fragment in fragments
                if fragment.context.role == "type-alias-value"
                and fragment.depth == declaration.depth + 1
                and declaration.start
                <= fragment.start
                < fragment.end
                <= declaration.end
            )
            if len(bodies) != 1:
                msg = "generic alias has no unique native body"
                raise ValueError(msg)
            yield (declaration, name, bodies[0]), parameters

    @classmethod
    def _generic_collection_body_rules(
        cls,
        selection: p.Infra.RopeContractRule,
        provider_identity: str,
        module: p.Infra.RopePyModule,
        fragments: tuple[
            p.Infra.RopeSourceFragment,
            p.Infra.RopeSourceFragment,
            p.Infra.RopeSourceFragment,
        ],
        parameters: tuple[str, ...],
    ) -> tuple[p.Infra.RopeContractRule, ...]:
        """Prove one complete native forwarding body before deriving its rule.

        Returns:
            One identity-constrained substitution, or no rule for a domain alias.

        """
        declaration, name, body = fragments
        origin = cls._generic_collection_origin(module, body)
        if origin is None:
            return ()
        member, identity, module_name = origin
        alias = module.source_code[name.start : name.end]
        suffix = cls._generic_collection_forwarding_suffix(
            module, declaration, alias, parameters, identity
        )
        if suffix is None:
            return ()
        actual = ", ".join(f"${{item{index}}}" for index in range(len(parameters)))
        return (
            m.Infra.RopeContractRule(
                id=f"{selection.id}:{alias}",
                owner_root=selection.owner_root,
                phase=selection.phase,
                pattern=f"${{alias}}[{actual}]",
                goal=f"{member}[{actual}{suffix}]",
                arguments={"alias": f"name={provider_identity}.{alias}"},
                imports={member: f"from {module_name} import {member}"}
                if module_name is not None
                else {},
                # A builtin origin is proven by its unshadowed lexical name;
                # only an imported origin carries a module-qualified binding.
                bindings={member: identity} if module_name is not None else {},
                unshadowed_builtins=(member,) if module_name is None else (),
            ),
        )

    @classmethod
    def _generic_collection_origin(
        cls,
        module: p.Infra.RopePyModule,
        body: p.Infra.RopeSourceFragment,
    ) -> tuple[str, str, str | None] | None:
        """Resolve a direct stdlib generic origin through its lexical binding.

        Returns:
            Native member, identity and import module, or no collection origin.

        Raises:
            ValueError: A captured generic origin cannot be resolved.

        """
        elected = cls._generic_origin_class(module, body)
        if elected is None:
            return None
        value, binding = elected
        owner = value.get_module()
        module_name = (
            value.builtin.__module__
            if isinstance(value, p.Infra.RopeBuiltinClass)
            else None
            if owner is None
            else owner.get_name()
        )
        member = value.get_name()
        if isinstance(binding, p.Infra.RopeImportedName):
            module_name = binding.imported_module.module_name
            if module_name is None:
                msg = "relative generic collection origin is not native"
                raise ValueError(msg)
            return member, f"{module_name}.{binding.imported_name}", module_name
        if isinstance(value, p.Infra.RopeBuiltinClass):
            return member, f"__builtins__.{member}", None
        if owner is None:
            msg = "native collection class has no declaring module"
            raise ValueError(msg)
        return member, f"{owner.get_name()}.{member}", owner.get_name()

    @classmethod
    def _generic_origin_class(
        cls,
        module: p.Infra.RopePyModule,
        body: p.Infra.RopeSourceFragment,
    ) -> tuple[p.Infra.RopeClassObject, p.Infra.RopePyName] | None:
        """Elect the stdlib generic origin class behind one lexical binding.

        Returns:
            The bound class object and its name binding, or no origin class.

        Raises:
            ValueError: A captured generic origin cannot be resolved.

        """
        origins = tuple(
            fragment
            for fragment in module.get_source_binding_index().fragments
            if fragment.start == body.start
            and fragment.end < body.end
            and all(
                part.isidentifier()
                for part in module.source_code[fragment.start : fragment.end].split(".")
            )
        )
        if not origins:
            return None
        origin = max(origins, key=lambda fragment: fragment.end)
        binding = FlextInfraUtilitiesRopeRuntimeModules.expression_name(
            origin.context.environment,
            module.source_code[origin.start : origin.end],
        )
        if binding is None:
            msg = "unresolved native generic collection origin"
            raise ValueError(msg)
        value = binding.get_object()
        if not isinstance(value, p.Infra.RopeClassObject):
            return None
        if isinstance(value, p.Infra.RopeBuiltinClass):
            module_name = value.builtin.__module__
        else:
            owner_module = value.get_module()
            module_name = None if owner_module is None else owner_module.get_name()
        if module_name is None or (
            module_name.partition(".")[0] not in sys.stdlib_module_names
        ):
            return None
        if "__class_getitem__" not in value.get_attributes():
            return None
        return value, binding

    @staticmethod
    def _generic_collection_forwarding_suffix(
        module: p.Infra.RopePyModule,
        declaration: p.Infra.RopeSourceFragment,
        alias: str,
        parameters: tuple[str, ...],
        identity: str,
    ) -> str | None:
        """Match the whole native declaration, retaining its argument arity.

        Returns:
            The native variadic suffix, or None for a non-forwarding domain alias.

        """
        formal = ", ".join(parameters)
        variants = ("", ", ...") if len(parameters) == 1 else ("",)
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(module)
        for variadic in variants:
            pattern = f"type {alias}[{formal}] = ${{origin}}[{formal}{variadic}]"
            matches = finder.get_matches(
                pattern,
                {"origin": f"name={identity}"},
                start=declaration.start,
                end=declaration.end,
            )
            if any(
                match.get_region() == (declaration.start, declaration.end)
                for match in matches
            ):
                return variadic
        return None

    @staticmethod
    def _contract_receiver_sources(
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[t.Infra.RopeSourcePath, str],
        rules: Sequence[p.Infra.RopeContractRule],
    ) -> MutableMapping[t.Infra.RopeSourcePath, str]:
        # Elect receivers without making unrelated generated sources editable.
        retirement = FlextInfraUtilitiesSemanticDeclarationRetirement
        providers: MutableMapping[t.Infra.RopeSourcePath, str] = {}
        for rule in rules:
            if rule.ownership_transfer is None:
                continue
            for identity in rule.bindings.values():
                binding = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
                    workspace.rope_project, identity
                )
                module = retirement.contract_transfer_module(binding)
                resource = module.get_resource()
                if resource is None:
                    msg = f"{rule.id}: transfer receiver has no native source"
                    raise ValueError(msg)
                path = Path(resource.real_path).resolve()
                if path in sources:
                    providers[path] = sources[path]
        return providers

    @classmethod
    def _require_owned_contract_transfers(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        rules: Sequence[p.Infra.RopeContractRule],
    ) -> None:
        source_project = workspace.rope_project
        for rule in rules:
            if rule.ownership_transfer is None:
                continue
            owner = FlextInfraUtilitiesSemanticDeclarationRelocation.contract_rule_root(
                workspace.repository_root, rule, source_project=source_project
            )
            layout = FlextInfraUtilitiesCodegenNamespace.layout(
                owner, rope_project=source_project
            )
            if layout is None:
                msg = "ownership transfer requires its declared project namespace"
                raise ValueError(msg)
            if not (
                rule.ownership_transfer[0] == layout.package_name
                or rule.ownership_transfer[0].startswith(f"{layout.package_name}.")
            ):
                message = f"{rule.id}: an external library declaration cannot retire"
                raise ValueError(message)

    @classmethod
    def _apply_contract_rules(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[t.Infra.RopeSourcePath, str],
        rules: Sequence[p.Infra.RopeContractRule],
        items: tuple[tuple[Path, str], ...],
        options: p.Infra.ContractAdmissionOptions,
    ) -> tuple[
        MutableMapping[Path, str],
        MutableMapping[Path, MutableSequence[str]],
        MutableMapping[str, Path],
    ]:
        working = dict(items)
        proposed_sources = cls._ContractSources(working, sources)
        applied: MutableMapping[Path, MutableSequence[str]] = {}
        with workspace.rope_project.source_view(
            declared_files=None, additional_source_folders=None
        ) as project:
            owned_modules = {
                FlextInfraUtilitiesRopeCore.resolve_pymodule(
                    project,
                    FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                        project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix()
                        ),
                        path,
                    ),
                ).get_name(): path
                for path, _source in items
                if any(rule.ownership_transfer is not None for rule in rules)
                and path.is_relative_to(workspace.repository_root)
            }
        implementation_owners: MutableMapping[
            tuple[str, str], t.Infra.RopeImplementationPaths
        ] = {}
        restrictions = (options.annotation_only, options.class_alias_only)
        for declared_rule in rules:
            for pattern, goal in cls._source_contract_templates(
                workspace.rope_project,
                declared_rule,
                working,
                applied,
            ):
                rule = (
                    m.Infra.RopeContractRule.model_validate(
                        declared_rule, from_attributes=True
                    ).model_copy(update={"pattern": pattern, "goal": goal})
                    if declared_rule.defaulted_field
                    or (pattern, goal) != (declared_rule.pattern, declared_rule.goal)
                    else declared_rule
                )
                with workspace.rope_project.source_view(
                    declared_files=cls._contract_source_plans(
                        workspace.rope_project, working, applied
                    ),
                    additional_source_folders=None,
                ) as project:
                    cls._apply_contract_members(
                        project,
                        rule,
                        cls._contract_rule_members(
                            project,
                            rule,
                            proposed_sources,
                            (implementation_owners, working, owned_modules, workspace),
                            restrictions,
                        ),
                        (working, applied),
                        preserves_bindings=(
                            rule.operation
                            is c.Infra.RopeContractOperation.NORMALIZE_MODEL_ENVELOPES
                        ),
                    )
        for addition in options.signature_additions:
            with workspace.rope_project.source_view(
                declared_files=cls._contract_source_plans(
                    workspace.rope_project, working, applied
                ),
                additional_source_folders=None,
            ) as project:
                cls._apply_contract_members(
                    project,
                    addition,
                    FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                        FlextInfraUtilitiesRopeRuntimeRefactors.signature_addition_changes(
                            project, addition, tuple(working)
                        ).changes,
                        f"{addition.id}: invalid signature changes",
                    ).unwrap(),
                    (working, applied),
                )
        for removal in options.signature_removals:
            for planner in (
                FlextInfraUtilitiesRopeRuntimeRefactors.signature_replacement_changes,
                FlextInfraUtilitiesRopeRuntimeRefactors.signature_removal_changes,
            ):
                with workspace.rope_project.source_view(
                    declared_files=cls._contract_source_plans(
                        workspace.rope_project, working, applied
                    ),
                    additional_source_folders=None,
                ) as project:
                    changes = planner(project, removal, tuple(working))
                    if changes is not None:
                        cls._apply_contract_members(
                            project,
                            removal,
                            FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                                changes.changes,
                                f"{removal.id}: invalid signature changes",
                            ).unwrap(),
                            (working, applied),
                        )
        for transfer in options.method_transfers:
            with workspace.rope_project.source_view(
                declared_files=cls._contract_source_plans(
                    workspace.rope_project, working, applied
                ),
                additional_source_folders=None,
            ) as project:
                changes = (
                    FlextInfraUtilitiesRopeRuntimeRefactors.method_transfer_changes
                )(
                    project,
                    transfer,
                    tuple(working),
                    FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver(
                        project, sources={}
                    ),
                )
                if changes is not None:
                    cls._apply_contract_members(
                        project,
                        transfer,
                        FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                            changes.changes, f"{transfer.id}: invalid method changes"
                        ).unwrap(),
                        (working, applied),
                    )
        return working, applied, owned_modules

    @classmethod
    def _source_contract_templates(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        sources: Mapping[Path, str],
        applied: Mapping[Path, Sequence[str]],
    ) -> Sequence[tuple[str, str]]:
        """Elect templates from the same invocation's planned source binding.

        Returns:
            Native pattern and replacement pairs, without retaining the view.

        """
        with project.source_view(
            declared_files=cls._contract_source_plans(project, sources, applied),
            additional_source_folders=None,
        ):
            if rule.annotation_member_source is not None:
                return ((rule.pattern, rule.goal),)
            return cls._field_contract_templates(
                project,
                rule,
                tuple(
                    project.get_resource(
                        path.relative_to(Path(project.root.real_path)).as_posix()
                    )
                    for path in sources
                ),
            )

    @staticmethod
    def _annotation_source_member_exists(
        scope: p.Infra.RopeScope,
        namespace: str,
        member: str,
    ) -> bool:
        """Distinguish a real source contract from an absent native member.

        Returns:
            Whether the resolved namespace declares the member.

        Raises:
            ValueError: The source namespace is bound to Rope's unknown object.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        source_root = runtime.expression_name(scope, namespace.partition(".")[0])
        if source_root is None:
            return False
        unknown = runtime.runtime_callable("rope.base.pyobjects", "get_unknown")()
        if source_root.get_object() is unknown:
            message = f"annotation source binding is ambiguous: {namespace}"
            raise ValueError(message)
        source = runtime.expression_name(scope, namespace)
        if source is None:
            return False
        source_object = source.get_object()
        if source_object is unknown:
            message = f"annotation source namespace is ambiguous: {namespace}"
            raise ValueError(message)
        return member in source_object.get_attributes()

    @staticmethod
    def _annotation_member_context(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
    ) -> _AnnotationMemberOwner:
        """Resolve the declared source and target facade members once.

        Returns:
            The rule, source prefix, destination prefix/owner, and owner members.

        Raises:
            ValueError: The rule does not declare its source or destination owner.
            TypeError: The source owner is not a native Rope class.

        """
        source = rule.annotation_member_source
        target, separator, capture = rule.goal.rpartition(".")
        if source is None or not separator or capture != "${member}":
            message = f"{rule.id}: annotation owner declaration is incomplete"
            raise ValueError(message)
        if target.partition(".")[0] == c.Infra.FacadeFamily.M:
            message = f"{rule.id}: model typing destination is prohibited: {target}"
            raise ValueError(message)
        owner = rule.bindings.get(target)
        source_owner = rule.bindings.get(source)
        if owner is None or source_owner is None:
            message = f"{rule.id}: annotation destination owner is undeclared"
            raise ValueError(message)
        source_identity = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, source_owner
        ).get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(source_identity):
            message = f"{rule.id}: annotation source owner is not a native class"
            raise TypeError(message)
        members = (
            FlextInfraUtilitiesRopeRuntimeModules
            .qualified_name(project, owner)
            .get_object()
            .get_attributes()
        )
        return FlextInfraUtilitiesSemanticContracts._AnnotationMemberOwner(
            rule, source, source_identity, target, owner, members
        )

    @staticmethod
    def _contract_source_plans(
        project: p.Infra.RopeProject,
        sources: Mapping[Path, str],
        applied: Mapping[Path, Sequence[str]],
    ) -> tuple[p.Infra.CodegenFilePlan, ...]:
        """Bind changed consumers while retaining the entry provider plans.

        Returns:
            Existing plans unchanged, or their original-witness consumer updates.

        """
        if not applied:
            return project.source_plans
        return FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            Path(project.root.real_path),
            (),
            {path: sources[path] for path in applied},
            source_project=project,
        )

    @staticmethod
    def _apply_contract_members(
        project: p.Infra.RopeProject,
        rule: (
            p.Infra.RopeContractRule
            | p.Infra.RopeSignatureAddition
            | p.Infra.RopeSignatureRemoval
            | p.Infra.RopeMethodTransfer
        ),
        members: Sequence[p.Infra.RopeChangeContents],
        state: tuple[
            MutableMapping[Path, str], MutableMapping[Path, MutableSequence[str]]
        ],
        *,
        preserves_bindings: bool = False,
    ) -> None:
        """Accept only captured consumer effects; provider reads are not writes.

        Raises:
            ValueError: If ``path not in working``.

        """
        working, applied = state
        for change in members:
            path = Path(change.resource.real_path).resolve()
            if path not in working:
                msg = f"{rule.id}: effect is outside captured consumers: {path}"
                raise ValueError(msg)
            relocation = FlextInfraUtilitiesSemanticDeclarationRelocation
            proposed = (
                change.new_contents
                if preserves_bindings
                else relocation.remove_orphaned_imports(
                    project, change.resource, working[path], change.new_contents
                )
            )
            if proposed != working[path]:
                working[path] = proposed
                applied.setdefault(path, []).append(rule.id)
        cli.display_text(f"mod: Rope contract {rule.id}: changed_files={len(members)}")

    @classmethod
    def _contract_rule_members(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        sources: Mapping[Path, str],
        context: tuple[
            MutableMapping[tuple[str, str], t.Infra.RopeImplementationPaths],
            Mapping[Path, str],
            Mapping[str, Path],
            p.Infra.RopeWorkspaceDsl,
        ],
        restrictions: tuple[bool, bool],
    ) -> list[p.Infra.RopeChangeContents]:
        if rule.operation in {
            c.Infra.RopeContractOperation.NORMALIZE_MODEL_ENVELOPES,
            c.Infra.RopeContractOperation.NORMALIZE_OPAQUE_MUTABLE_PORTS,
        }:
            workspace = context[3]
            checker = workspace.model_envelope_checker
            if checker is None:
                message = "model-envelope admission requires its native checker"
                raise RuntimeError(message)
            transform = (
                cls.model_envelope_changes
                if rule.operation
                == c.Infra.RopeContractOperation.NORMALIZE_MODEL_ENVELOPES
                else FlextInfraUtilitiesSemanticOpaquePorts.opaque_port_changes
            )
            return transform(
                project,
                rule,
                cls._contract_scope_resources(project, rule, tuple(context[1])),
                checker(context[1]),
                (
                    workspace.model_protocol_identities
                    if rule.operation
                    == c.Infra.RopeContractOperation.NORMALIZE_MODEL_ENVELOPES
                    else workspace.model_protocol_routes
                ),
            )
        if rule.annotation_member_source is not None:
            return cls._annotation_member_changes(
                project, rule, sources, tuple(context[1])
            )
        if rule.operation == c.Infra.RopeContractOperation.NORMALIZE_EXHAUSTIVE_ENUM:
            return cls._exhaustive_enum_contracts(
                project, rule, sources, tuple(context[1])
            )
        if rule.operation == c.Infra.RopeContractOperation.MATERIALIZE_DELEGATIONS:
            return FlextInfraUtilitiesSemanticDelegations.materialize_delegations(
                project, sources, tuple(context[1]), rule.id
            )
        resources = cls._contract_scope_resources(project, rule, tuple(context[1]))
        members: list[p.Infra.RopeChangeContents] = []
        for (
            selected_rule,
            selected_resources,
        ) in FlextInfraUtilitiesImportLaw.import_contract_routes(
            project, rule, resources, sources
        ):

            def admit(
                module: p.Infra.RopePyModule,
                match: p.Infra.RopeContractMatch,
                selected_rule: p.Infra.RopeContractRule = selected_rule,
            ) -> bool:
                return cls._admit_contract_restrictions(
                    project,
                    module,
                    match,
                    (
                        restrictions[0] or selected_rule.annotation_only,
                        restrictions[1],
                    ),
                ) and (
                    cls._admit_contract_match(
                        project,
                        selected_rule,
                        module,
                        match,
                        context=(
                            context[0],
                            sources,
                            context[2],
                        ),
                    )
                )

            changes = FlextInfraUtilitiesRopeRuntimeRefactors.restructure_changes(
                project,
                m.Infra.RopeRestructureRequest(
                    pattern=selected_rule.pattern,
                    goal=selected_rule.goal,
                    arguments=cls._contract_arguments(selected_rule),
                    resources=selected_resources,
                    imports=selected_rule.imports,
                    match_filter=admit,
                ),
            )
            members.extend(
                FlextInfraUtilitiesRopeRuntimeRefactors.change_set_members(
                    changes.changes, f"{rule.id}: invalid Rope content changes"
                ).unwrap()
            )
        return members

    @classmethod
    def _annotation_member_changes(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        sources: Mapping[Path, str],
        paths: Sequence[Path],
    ) -> list[p.Infra.RopeChangeContents]:
        """Plan only bound annotation-member edits through Rope content changes.

        Returns:
            Native Rope content changes for unresolved members owned by the declared
            declared destination namespace.

        Raises:
            ValueError: A source snapshot, member owner, or binding is ambiguous.

        """
        context = cls._annotation_member_context(project, rule)
        changes = []
        for resource in cls._contract_scope_resources(project, rule, paths):
            path = Path(resource.real_path).resolve()
            if path.suffix != c.Infra.EXT_PYTHON:
                continue
            source = sources.get(path)
            if source is None:
                message = (
                    f"{rule.id}: scoped annotation source was not captured: {path}"
                )
                raise ValueError(message)
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            )
            if module.source_code != source:
                message = (
                    f"{rule.id}: annotation source differs from captured Rope view: "
                    f"{path}"
                )
                raise ValueError(message)
            edits, import_modules = cls._annotation_member_edits(
                project, module, source, context
            )
            if not edits:
                continue
            changes.append(
                cls._annotation_member_content_change(
                    project,
                    resource,
                    source,
                    (rule, module, edits, import_modules),
                )
            )
        return changes

    @staticmethod
    def _annotation_member_content_change(
        project: p.Infra.RopeProject,
        resource: p.Infra.RopeResource,
        source: str,
        plan: tuple[
            p.Infra.RopeContractRule,
            p.Infra.RopePyModule,
            Sequence[p.Infra.SourceRewrite],
            set[str],
        ],
    ) -> p.Infra.RopeChangeContents:
        """Compose annotation and missing-import edits into one Rope change.

        Returns:
            One native Rope content change retaining the original file witness.

        Raises:
            ValueError: An import route is conflicting or cannot be planned.

        """
        rule, module, edits, import_modules = plan
        proposed = FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource, source, edits
        ).new_contents
        if not import_modules:
            return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
                resource, source, edits
            )
        if len(import_modules) != 1:
            message = f"{rule.id}: one module elected multiple destination facades"
            raise ValueError(message)
        root = Path(project.root.real_path).resolve()
        import_module = next(iter(import_modules))
        plans = FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
            root,
            (),
            {Path(resource.real_path).resolve(): proposed},
            source_project=project,
        )
        with project.source_view(
            declared_files=plans, additional_source_folders=None
        ) as candidate:
            candidate_resource = candidate.get_resource(
                Path(resource.real_path).resolve().relative_to(root).as_posix()
            )
            candidate_file = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                candidate_resource, Path(resource.real_path).resolve()
            )
            imported = FlextInfraUtilitiesRopeImports.add_import(
                candidate,
                candidate_file,
                import_module,
                (rule.goal.partition(".")[0],),
                apply=False,
            )
        if imported is None:
            message = (
                f"{rule.id}: Rope did not add the required destination import from "
                f"{import_module} in {module.get_name()}"
            )
            raise ValueError(message)
        return FlextInfraUtilitiesRopeRuntimeRefactors.content_change(
            resource,
            source,
            (m.Infra.SourceRewrite(start=0, end=len(source), text=imported),),
        )

    @staticmethod
    def _annotation_member_edits(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        source: str,
        context: FlextInfraUtilitiesSemanticContracts._AnnotationMemberOwner,
    ) -> tuple[list[p.Infra.SourceRewrite], set[str]]:
        """Build Rope span edits in actual annotation regions.

        Returns:
            Nonoverlapping annotation edits and required public facade imports.

        """
        references = FlextInfraUtilitiesSemanticFamilyTypeReferences
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        edits: list[p.Infra.SourceRewrite] = []
        import_modules: set[str] = set()
        for begin, end, _line in references.annotation_regions(source, module):
            scope = runtime.scope_at(module, begin)
            annotation = source[begin:end]
            state = (
                project,
                module,
                FlextInfraUtilitiesSemanticContracts._AnnotationMemberState(
                    context, begin
                ),
                import_modules,
            )
            replace = partial(
                FlextInfraUtilitiesSemanticContracts._annotation_member_replacement,
                context=state,
            )
            updated = references.rewrite_type_source(
                annotation, project, scope, replace
            )
            if updated != annotation:
                edits.append(m.Infra.SourceRewrite(start=begin, end=end, text=updated))
        return edits, import_modules

    @staticmethod
    def _annotation_member_replacement(
        scope: p.Infra.RopeScope,
        expression: str,
        context: tuple[
            p.Infra.RopeProject,
            p.Infra.RopePyModule,
            FlextInfraUtilitiesSemanticContracts._AnnotationMemberState,
            set[str],
        ],
    ) -> str | None:
        """Resolve the source and destination identities for one annotation.

        Returns:
            The destination spelling for an owned member, or no edit when a
            real protocol already provides the source member.

        Raises:
            ValueError: The source, target, or destination binding is ambiguous.

        """
        owner = context[2].owner
        if not expression.startswith(f"{owner.source}."):
            return None
        member = expression.removeprefix(f"{owner.source}.")
        if not member.isidentifier():
            return None
        if not FlextInfraUtilitiesSemanticContracts._annotation_source_owner_matches(
            scope, owner
        ):
            return None
        expected = FlextInfraUtilitiesSemanticContracts._annotation_member_target(
            scope, owner, member
        )
        if expected is None:
            return None
        destination_path = f"{owner.target}.{member}"
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        destination = runtime.expression_name(scope, destination_path)
        root_binding = runtime.expression_name(scope, owner.target.partition(".")[0])
        if runtime.same_name(expected, destination):
            if isinstance(
                root_binding, (p.Infra.RopeImportedName, p.Infra.RopeImportedModule)
            ) and not runtime.imported_binding_precedes(
                context[0],
                context[1],
                owner.target.partition(".")[0],
                context[2].offset,
            ):
                context[3].add(
                    FlextInfraUtilitiesSemanticContracts._annotation_member_import(
                        context[0], context[1], owner, member
                    )
                )
            return destination_path
        if root_binding is None:
            context[3].add(
                FlextInfraUtilitiesSemanticContracts._annotation_member_import(
                    context[0], context[1], owner, member
                )
            )
            return destination_path
        unknown = runtime.runtime_callable("rope.base.pyobjects", "get_unknown")()
        if root_binding.get_object() is unknown:
            message = (
                f"{owner.rule.id}: target {owner.target} binding is ambiguous in "
                f"{context[1].get_name()}"
            )
            raise ValueError(message)
        message = (
            f"{owner.rule.id}: annotation destination {destination_path} does not "
            f"resolve to {owner.owner}.{member} in {context[1].get_name()}"
        )
        raise ValueError(message)

    @staticmethod
    def _annotation_member_target(
        scope: p.Infra.RopeScope,
        owner: FlextInfraUtilitiesSemanticContracts._AnnotationMemberOwner,
        member: str,
    ) -> p.Infra.RopePyName | None:
        """Admit actual model references while retaining real protocol members.

        Returns:
            The declared native destination, or no edit for an existing protocol.

        Raises:
            ValueError: A model source is missing or shadowed, the destination is
                absent, or a native SDK typing destination changes identity.

        """
        model_source = owner.source.partition(".")[0] == c.Infra.FacadeFamily.M
        if FlextInfraUtilitiesSemanticContracts._annotation_source_member_exists(
            scope, owner.source, member
        ):
            if not model_source:
                return None
        elif model_source:
            message = (
                f"{owner.rule.id}: model annotation source is undeclared: "
                f"{owner.source}.{member}"
            )
            raise ValueError(message)
        expected = owner.members.get(member)
        if expected is None:
            message = (
                f"{owner.rule.id}: {owner.source}.{member} has no member in "
                f"declared owner {owner.owner}"
            )
            raise ValueError(message)
        if model_source:
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            source_member = owner.source_owner.get_attributes().get(member)
            if source_member is None or not runtime.same_name(
                source_member,
                runtime.expression_name(scope, f"{owner.source}.{member}"),
            ):
                message = (
                    f"{owner.rule.id}: model annotation source is shadowed: "
                    f"{owner.source}.{member}"
                )
                raise ValueError(message)
            if owner.target.partition(".")[0] != c.Infra.FacadeFamily.P and not (
                runtime.same_name(source_member, expected)
            ):
                message = (
                    f"{owner.rule.id}: native typing destination changes source "
                    f"identity: {owner.target}.{member}"
                )
                raise ValueError(message)
        return expected

    @staticmethod
    def _annotation_source_owner_matches(
        scope: p.Infra.RopeScope,
        owner: FlextInfraUtilitiesSemanticContracts._AnnotationMemberOwner,
    ) -> bool:
        """Authenticate the actual protocol namespace and native ancestry.

        Returns:
            Whether the declared source owner or a native subclass is bound.

        Raises:
            ValueError: The lexical source path resolves to an unknown provider.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        source = runtime.expression_name(scope, owner.source)
        if source is not None:
            source_object = source.get_object()
            unknown = runtime.runtime_callable("rope.base.pyobjects", "get_unknown")()
            if source_object is unknown:
                message = f"{owner.rule.id}: source namespace {owner.source} is unknown"
                raise ValueError(message)
            if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(source_object):
                return False
            return owner.source_owner in source_object.get_mro()
        return False

    @staticmethod
    def _annotation_member_import(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        owner: FlextInfraUtilitiesSemanticContracts._AnnotationMemberOwner,
        member: str,
    ) -> str:
        """Prove the scoped package publishes the expected destination facade.

        Returns:
            The selected package root for Rope's public import organizer.

        Raises:
            ValueError: The package root does not publish the configured owner.

        """
        package_root = module.get_name().partition(".")[0]
        if owner.rule.scope is None or module.get_name() not in {
            target.module for target in owner.rule.scope.targets
        }:
            message = (
                f"{owner.rule.id}: package root {package_root} is not in declared scope"
            )
            raise ValueError(message)
        expected = owner.members.get(member)
        if expected is None:
            message = f"{owner.rule.id}: destination owner has no member {member}"
            raise ValueError(message)
        target_prefix = owner.target
        public = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, f"{package_root}.{target_prefix}.{member}"
        )
        if not FlextInfraUtilitiesRopeRuntimeModules.same_name(expected, public):
            message = (
                f"{owner.rule.id}: public package {package_root} does not publish "
                f"{owner.owner}.{member}"
            )
            raise ValueError(message)
        return package_root

    @staticmethod
    def _contract_scope_resources(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        paths: Sequence[Path],
    ) -> tuple[p.Infra.RopeResource, ...]:
        """Return only native modules declared by a rule's closed scope.

        The project manifest supplies the distribution identity and Rope supplies the
        module identity. Both must match one declared pair, preventing a rule scoped
        for one package from leaking into another package with an alike source shape.

        Returns:
            Every candidate resource for an unscoped rule, or its admitted subset.

        """
        root = Path(project.root.real_path)
        resources = tuple(
            project.get_resource(path.relative_to(root).as_posix()) for path in paths
        )
        if rule.scope is None:
            return resources
        targets = {(item.distribution, item.module) for item in rule.scope.targets}
        selected: list[p.Infra.RopeResource] = []
        distributions: dict[Path, str] = {}
        for resource in resources:
            path = Path(resource.real_path).resolve()
            owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                root, path, source_project=project
            )
            if owner is None:
                continue
            distribution = distributions.get(owner)
            if distribution is None:
                payload = FlextInfraUtilitiesPyprojectDocument.pyproject_payload(
                    owner / c.PYPROJECT_FILENAME
                )
                distribution = (
                    FlextInfraUtilitiesDependencyRequirements.distribution_identity(
                        FlextInfraUtilitiesPyprojectDocument.project_name_from_payload(
                            owner / c.PYPROJECT_FILENAME, payload
                        )
                    )
                )
                distributions[owner] = distribution
            module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
                project, resource
            ).get_name()
            if (distribution, module) in targets:
                selected.append(resource)
        return tuple(selected)

    class _EnumProjection(FlextInfraUtilitiesSemanticConstantSources):
        """Own one native enum pass and its invocation-local observations."""

        def __init__(
            self,
            project: p.Infra.RopeProject,
            rule: p.Infra.RopeContractRule,
            sources: Mapping[Path, str],
            paths: Sequence[Path],
            admit: Callable[
                [
                    p.Infra.RopeProject,
                    p.Infra.RopeContractRule,
                    p.Infra.RopePyModule,
                    p.Infra.RopeScope,
                ],
                bool,
            ],
        ) -> None:
            """Bind native capabilities and source observations to this invocation.

            Raises:
                TypeError: A declared native matching constraint is not a string.

            """
            self.project, self.rule, self.sources, self.admit = (
                project,
                rule,
                sources,
                admit,
            )
            self.modules = {
                path: FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                    FlextInfraUtilitiesRopeCore.resolve_pymodule(
                        project,
                        project.get_resource(
                            path.relative_to(Path(project.root.real_path)).as_posix()
                        ),
                    )
                )
                for path in paths
            }
            self.arguments: dict[str, str] = {}
            for name, constraint in rule.arguments.items():
                if not isinstance(constraint, str):
                    message = f"{rule.id}: enum constraints must be native strings"
                    raise TypeError(message)
                self.arguments[name] = constraint
            self.references: dict[
                p.Infra.RopeSourceModule, tuple[tuple[int, int], ...]
            ] = {}
            self.protected: dict[
                p.Infra.RopeSourceModule, frozenset[tuple[int, int]]
            ] = {}
            self.statements: dict[
                p.Infra.RopeSourceModule, tuple[tuple[int, int], ...]
            ] = {}
            self.quoted: dict[
                p.Infra.RopeSourceModule,
                tuple[tuple[int, int, str, p.Infra.RopeScope], ...],
            ] = {}
            self.members: dict[
                p.Infra.RopeSourceClass, Mapping[str, p.Infra.RopePyName]
            ] = {}
            self.calls: dict[
                tuple[p.Infra.RopeSourceModule, int, int],
                tuple[bool, tuple[Sequence[str], Sequence[tuple[str, str]]]] | None,
            ] = {}
            self.discriminators: dict[
                p.Infra.RopeSourceClass,
                set[tuple[p.Infra.RopeSourceModule, int, int, str | None]],
            ] = {}
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            self.field_factory = runtime.qualified_name(project, "pydantic.Field")
            self.discriminator = runtime.qualified_name(
                project, "pydantic.Discriminator"
            )
            self.classvar = runtime.qualified_name(project, "typing.ClassVar")
            self.final = runtime.qualified_name(project, "typing.Final")

        def _observe(self, module: p.Infra.RopeSourceModule) -> None:
            """Capture native references and statements once for this source epoch."""
            if module in self.references:
                return
            references = FlextInfraUtilitiesSemanticFamilyTypeReferences
            self.references[module] = references.reference_regions(module.source_code)
            self.protected[module] = references.expression_payload_ranges(
                module.source_code, self.project, module.get_scope(), module=module
            )
            self.statements[module] = tuple(
                (item.start_offset, item.end_offset)
                for item in FlextInfraUtilitiesRopeStructure.logical_statements(
                    module.source_code
                )
            )
            self.quoted[module] = references.quoted_type_regions(
                module.source_code, self.project, module
            )

        def _primaries(
            self,
            module: p.Infra.RopeSourceModule,
            region: tuple[int, int],
            *,
            types_only: bool = False,
        ) -> Iterator[tuple[str, p.Infra.RopeScope]]:
            """Yield ordinary and quoted references with their native scopes.

            Yields:
                Each reference and the SDK scope that authenticates its binding.

            """
            self._observe(module)
            references = FlextInfraUtilitiesSemanticFamilyTypeReferences
            bindings = module.get_source_binding_index()
            protected = (
                self.protected[module] if types_only else frozenset[tuple[int, int]]()
            )
            for start, stop in self.references[module]:
                if region[0] <= start < stop <= region[1] and not any(
                    first <= start < stop <= last for first, last in protected
                ):
                    yield (
                        module.source_code[start:stop],
                        bindings.context_at(start).environment,
                    )
            for start, stop, literal, scope in self.quoted[module]:
                if region[0] <= start < stop <= region[1]:
                    selected: list[str] = []
                    references.rewrite_type_source(
                        literal,
                        self.project,
                        scope,
                        lambda _scope, expression, *, _selected=selected: (
                            _selected.append(expression)
                        ),
                    )
                    yield from ((expression, scope) for expression in selected)

        def _assigned_statements(
            self, binding: p.Infra.RopePyName
        ) -> tuple[tuple[p.Infra.RopeSourceModule, tuple[int, int]], ...]:
            """Locate the source statements defining an assigned native binding.

            Returns:
                Source modules and statements owning the assigned declaration.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            if not isinstance(binding, p.Infra.RopeAssignedName):
                return ()
            provider, line = runtime.definition_location(binding)
            if (
                not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider)
                or line is None
            ):
                return ()
            self._observe(provider)
            offset = provider.lines.get_line_start(line)
            return tuple(
                (provider, region)
                for region in self.statements[provider]
                if region[0] <= offset < region[1]
            )

        def _dependencies(
            self,
            module: p.Infra.RopeSourceModule,
            region: tuple[int, int],
            *,
            types_only: bool = False,
        ) -> tuple[
            set[p.Infra.RopeSourceClass],
            tuple[tuple[p.Infra.RopeSourceModule, tuple[int, int]], ...],
        ]:
            """Follow assigned/imported metadata through native reference closure.

            Returns:
                Source classes and statements reached by the closure.

            Raises:
                ValueError: A named dependency has unresolved import provenance.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            pending = [(module, region)]
            visited: set[tuple[str, int, int]] = set()
            models: set[p.Infra.RopeSourceClass] = set()
            statements: list[tuple[p.Infra.RopeSourceModule, tuple[int, int]]] = []
            while pending:
                current, selected = pending.pop()
                key = current.get_name(), *selected
                if key in visited:
                    continue
                visited.add(key)
                statements.append((current, selected))
                for expression, scope in self._primaries(
                    current, selected, types_only=types_only
                ):
                    binding = runtime.resolve_symbol(scope, expression)
                    if binding is None:
                        continue
                    binding = runtime.source_import_binding(binding)
                    if binding is None:
                        message = "Enum discriminator import provenance is unresolved"
                        raise ValueError(message)
                    models.update(self._class_dependencies(binding))
                    pending.extend(self._assigned_statements(binding))
            return models, tuple(statements)

        @staticmethod
        def _class_dependencies(
            binding: p.Infra.RopePyName,
        ) -> set[p.Infra.RopeSourceClass]:
            """Describe a native source class and its source-defined ancestry.

            Returns:
                Native classes described by this binding, without instance guesses.

            """
            target = binding.get_object()
            if not isinstance(target, p.Infra.RopeSourceClass):
                return set()
            return {
                ancestor
                for ancestor in target.get_mro()
                if isinstance(ancestor, p.Infra.RopeSourceClass)
            }

        def _type_qualifier(
            self,
            module: p.Infra.RopeSourceModule,
            region: tuple[int, int],
            marker: p.Infra.RopePyName,
        ) -> bool:
            """Authenticate a typing qualifier through native annotation aliases.

            Returns:
                Whether the type-position dependency closure names that qualifier.

            """
            _classes, dependencies = self._dependencies(module, region, types_only=True)
            return any(
                FlextInfraUtilitiesRopeRuntimeModules.same_name(
                    marker, self._terminal(scope, expression)
                )
                for provider, selected in dependencies
                for expression, scope in self._primaries(
                    provider, selected, types_only=True
                )
            )

        def _native_call(
            self, module: p.Infra.RopeSourceModule, primary: tuple[int, int]
        ) -> tuple[bool, tuple[Sequence[str], Sequence[tuple[str, str]]]] | None:
            """Observe a Field or Discriminator call once through native identity.

            Returns:
                Its discriminator role and native arguments, or no relevant call.

            """
            key = module, *primary
            if key in self.calls:
                return self.calls[key]
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            binding = runtime.resolve_symbol(
                module.get_source_binding_index().context_at(primary[0]).environment,
                module.source_code[primary[0] : primary[1]],
            )
            if binding is not None:
                binding = runtime.source_import_binding(binding)
            discriminator = runtime.same_name(self.discriminator, binding)
            parameters = (
                refactors.native_call_parameters(module.source_code, primary)
                if discriminator or runtime.same_name(self.field_factory, binding)
                else None
            )
            observed = (discriminator, parameters) if parameters is not None else None
            self.calls[key] = observed
            return observed

        def _statement_calls(
            self, module: p.Infra.RopeSourceModule, region: tuple[int, int]
        ) -> Iterator[tuple[p.Infra.RopeSourceModule, int, int, str | None]]:
            """Yield discriminator observations for one authenticated statement.

            Yields:
                Marker calls and the source region authenticating their arguments.

            """
            self._observe(module)
            for first, last in self.references[module]:
                if not region[0] <= first < last <= region[1]:
                    continue
                call = self._native_call(module, (first, last))
                if call is None:
                    continue
                positional, keywords = call[1]
                marker = next(
                    (value for name, value in keywords if name == "discriminator"),
                    positional[0] if call[0] and positional else None,
                )
                if any(value.startswith("*") for value in positional):
                    yield module, first, region[1], None
                elif marker is not None:
                    yield module, first, region[1], marker

        def _index_discriminators(self) -> None:
            """Associate native calls with their model dependencies once per pass."""
            for module in self.modules.values():
                self._observe(module)
                for statement in self.statements[module]:
                    models, dependencies = self._dependencies(module, statement)
                    calls = {
                        call
                        for provider, region in dependencies
                        for call in self._statement_calls(provider, region)
                    }
                    for model in models:
                        self.discriminators.setdefault(model, set()).update(calls)

        def _is_discriminator(self, model: p.Infra.RopeSourceClass, field: str) -> bool:
            """Retain real discriminator fields without rescanning source modules.

            Returns:
                Whether a proven native string marker names the field.

            Raises:
                ValueError: Its associated marker is opaque or dynamically expanded.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            for module, start, last, marker in self.discriminators.get(model, ()):
                if marker is None:
                    message = "Enum discriminator requires explicit native arguments"
                    raise ValueError(message)
                source = module.source_code
                if any(
                    source[first:stop] == marker
                    for first, stop in refactors.semantic_regions(
                        module, repr(field), arguments={}, start=start, end=last
                    )
                ):
                    return True
                if marker not in {"None", "False"} and not any(
                    source[first:stop] == marker
                    for first, stop in self._strings(module)
                ):
                    message = (
                        "Enum discriminator requires a native string field identity"
                    )
                    raise ValueError(message)
            return False

        @staticmethod
        def _strings(
            module: p.Infra.RopeSourceModule,
        ) -> set[tuple[int, int]]:
            """Return exact native string-literal regions, excluding comments.

            Returns:
                Half-open regions that the native lexer identifies as strings.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            return {
                (start, stop)
                for start, stop, _metadata in refactors.ignored_regions(
                    module.source_code
                )
                if module.source_code[start:stop].lstrip("rRuU").startswith(("'", '"'))
            }

        def _members(
            self, owner: p.Infra.RopeSourceClass
        ) -> Mapping[str, p.Infra.RopePyName]:
            """Prove the existing plain-unique admission through native matching.

            Returns:
                Owned members of an admitted enum, or no admission for another shape.

            """
            if owner in self.members:
                return self.members[owner]
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            if tuple(owner.get_superclasses()) != (
                runtime.qualified_name(self.project, "enum.StrEnum").get_object(),
            ):
                return {}
            defined = owner.get_scope().get_defined_names()
            if (
                not defined
                or len(defined) == 1
                or any(
                    name.startswith("_")
                    or not isinstance(binding, p.Infra.RopeAssignedName)
                    or len(binding.assignments) != 1
                    for name, binding in defined.items()
                )
            ):
                return {}
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                owner.get_module()
            )
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            region = refactors.source_declaration_region(module, owner.get_ast())
            members = dict(
                sorted(
                    defined.items(),
                    key=lambda item: item[1].get_definition_location()[1] or 0,
                )
            )
            body = [repr(owner.get_doc())] if owner.get_doc() is not None else []
            body.extend(
                f"{name} = ${{value{index}}}" for index, name in enumerate(members)
            )
            pattern = (
                "@${unique}\nclass "
                + owner.get_name()
                + "(${strenum}):\n    "
                + "\n    ".join(body)
            )
            arguments = {"unique": "name=enum.unique", "strenum": "name=enum.StrEnum"}
            strings = self._strings(module)
            for match in refactors.semantic_finder(module).get_matches(
                pattern, arguments
            ):
                first, last = match.get_region()
                if first <= region[0] < last == region[1] and all(
                    refactors.semantic_capture_region(module, match, f"value{index}")
                    in strings
                    for index in range(len(members))
                ):
                    self.members[owner] = members
                    return members
            self.members[owner] = {}
            return {}

        def _terminal(
            self, scope: p.Infra.RopeScope, expression: str
        ) -> p.Infra.RopePyName | None:
            """Reuse native constant provenance and assignment-alias resolution.

            Returns:
                The terminal native binding, when that identity is provable.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            binding = runtime.resolve_symbol(scope, expression)
            return (
                runtime.class_assignment_binding(
                    self._constant_terminal(self.project, binding, expression),
                    classes_only=False,
                )
                if binding is not None
                else None
            )

        def _owners(
            self,
            module: p.Infra.RopeSourceModule,
            scope: p.Infra.RopeScope,
            payload: tuple[int, int],
        ) -> Iterator[
            tuple[p.Infra.RopeSourceClass, Mapping[str, p.Infra.RopePyName], str]
        ]:
            """Yield unique native enum owners named by a Literal payload.

            Yields:
                An enum, its proven members and an authored reference to that owner.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            observed: set[p.Infra.RopeSourceClass] = set()
            for first, last in self.references[module]:
                if not payload[0] <= first < last <= payload[1]:
                    continue
                expression = module.source_code[first:last]
                terminal = self._terminal(scope, expression)
                if terminal is None:
                    continue
                provider, line = runtime.definition_location(terminal)
                if (
                    not FlextInfraUtilitiesRopeRuntimeTypes.source_module(provider)
                    or line is None
                ):
                    continue
                owner = runtime.scope_at(
                    provider, provider.lines.get_line_start(line)
                ).pyobject
                if not isinstance(owner, p.Infra.RopeSourceClass) or owner in observed:
                    continue
                observed.add(owner)
                members = self._members(owner)
                if members:
                    yield owner, members, expression

        def _matches_domain(
            self,
            module: p.Infra.RopeSourceModule,
            scope: p.Infra.RopeScope,
            match: p.Infra.RopeContractMatch,
            members: Mapping[str, p.Infra.RopePyName],
        ) -> bool:
            """Prove exact member coverage and binding stability before effects.

            Returns:
                Whether every capture is the same complete enum domain.

            Raises:
                ValueError: A captured alias has unresolved or unstable provenance.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            expected = {member.get_definition_location() for member in members.values()}
            captured: list[tuple[p.Infra.RopeParsedModule | None, int | None]] = []
            for index in range(len(members)):
                first, last = refactors.semantic_capture_region(
                    module, match, f"member{index}"
                )
                text = module.source_code[first:last]
                if not all(part.isidentifier() for part in text.split(".")):
                    return False
                terminal = self._terminal(scope, text)
                if terminal is None:
                    message = f"{self.rule.id}: enum member has no native terminal"
                    raise ValueError(message)
                if not FlextInfraUtilitiesCodemodProject.stable_binding_chain(
                    (self.project, module, scope), text, first, self.sources
                ):
                    message = f"{self.rule.id}: enum annotation binding is ambiguous"
                    raise ValueError(message)
                captured.append(terminal.get_definition_location())
            return len(captured) == len(expected) and set(captured) == expected

        @staticmethod
        def _owner_route(
            scope: p.Infra.RopeScope,
            owner: p.Infra.RopeSourceClass,
            authored: str,
        ) -> tuple[str, tuple[str, str] | None]:
            """Elect an existing route or native declaring-class import.

            Returns:
                Enum spelling and the optional required source import.

            Raises:
                ValueError: The declaring-class import shadows an existing name.

            """
            runtime = FlextInfraUtilitiesRopeRuntimeModules
            prefix = authored.rpartition(".")[0]
            binding = runtime.resolve_symbol(scope, prefix) if prefix else None
            if binding is not None and binding.get_object() is owner:
                return prefix, None
            lexical: p.Infra.RopeScope | None = scope
            while lexical is not None:
                for name, binding in lexical.get_defined_names().items():
                    terminal = runtime.class_assignment_binding(binding)
                    if terminal is not None and terminal.get_object() is owner:
                        resolved = runtime.resolve_symbol(scope, name)
                        if resolved is not None and resolved.get_object() is owner:
                            return name, None
                lexical = lexical.parent
            names = [owner.get_name()]
            enclosing = owner.get_scope().parent
            while (
                enclosing is not None
                and enclosing.get_kind() == c.Infra.RopeScopeKind.CLASS
            ):
                names.append(enclosing.pyobject.get_name())
                enclosing = enclosing.parent
            names.reverse()
            if runtime.resolve_symbol(scope, names[0]) is not None:
                message = f"Enum declaring-class import is shadowed: {names[0]}"
                raise ValueError(message)
            return ".".join(names), (owner.get_module().get_name(), names[0])

        def _field_calls(
            self,
            module: p.Infra.RopeSourceModule,
            regions: tuple[tuple[int, int], ...],
        ) -> Iterator[
            tuple[tuple[int, int], tuple[Sequence[str], Sequence[tuple[str, str]]]]
        ]:
            """Yield native Field call shapes within the elected source regions.

            Yields:
                Callee regions with their native positional and keyword arguments.

            """
            for first, last in self.references[module]:
                if not any(start <= first < last <= stop for start, stop in regions):
                    continue
                call = self._native_call(module, (first, last))
                if call is not None and not call[0]:
                    yield (first, last), call[1]

        def _default_regions(
            self,
            module: p.Infra.RopeSourceModule,
            match: p.Infra.RopeContractMatch,
            contract: tuple[int, int],
        ) -> tuple[tuple[int, int], ...]:
            """Extract direct and Field defaults through native source captures.

            Returns:
                Direct or Field-owned default regions requiring producer proof.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            direct = (
                refactors.semantic_capture_region(module, match, "default")
                if match.get_ast("default") is not None
                else None
            )
            regions: list[tuple[int, int]] = []
            calls: set[tuple[int, int]] = set()
            for primary, parameters in self._field_calls(
                module, (contract, *((direct,) if direct is not None else ()))
            ):
                capture, arguments = self._default_pattern(*parameters)
                pattern = module.source_code[slice(*primary)] + f"({arguments})"
                for call in refactors.semantic_finder(module).get_matches(
                    pattern, {}, start=primary[0], end=match.get_region()[1]
                ):
                    calls.add(call.get_region())
                    if capture is not None:
                        regions.append(
                            refactors.semantic_capture_region(module, call, capture)
                        )
            return (
                *regions,
                *((direct,) if direct is not None and direct not in calls else ()),
            )

        @staticmethod
        def _default_pattern(
            positional: Sequence[str],
            keywords: Sequence[tuple[str, str]],
        ) -> tuple[str | None, str]:
            """Describe a native Field call and its default-value capture.

            Returns:
                The capture name and native argument pattern.

            Raises:
                ValueError: Opaque arguments or factories lack enum-domain proof.

            """
            if any(value.startswith("*") for value in positional) or any(
                not name.isidentifier() for name, _value in keywords
            ):
                message = "Enum default requires explicit native Field arguments"
                raise ValueError(message)
            if any(name == "default_factory" for name, _value in keywords):
                message = (
                    "Enum default factory requires a proven enum-domain producer "
                    "before migration"
                )
                raise ValueError(message)
            arguments = [f"${{pos{index}}}" for index in range(len(positional))]
            arguments.extend(
                f"{name}=${{kw{index}}}"
                for index, (name, _value) in enumerate(keywords)
            )
            capture = next(
                (
                    f"kw{index}"
                    for index, (name, _value) in enumerate(keywords)
                    if name == "default"
                ),
                "pos0" if positional else None,
            )
            return capture, ", ".join(arguments)

        def _default_change(
            self,
            module: p.Infra.RopeSourceModule,
            region: tuple[int, int],
            domain: tuple[
                p.Infra.RopeSourceClass, Mapping[str, p.Infra.RopePyName], str
            ],
        ) -> p.Infra.SourceRewrite | None:
            """Rewrite native literal defaults or prove existing enum producers.

            Returns:
                A scalar default rewrite, or no edit for a proven producer.

            Raises:
                ValueError: A string has no unique native enum-member producer.

            """
            owner, members, prefix = domain
            value = module.source_code[slice(*region)]
            if value in {"None", "True", "False", "..."}:
                return None
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            if region in self._strings(module):
                provider = FlextInfraUtilitiesRopeRuntimeTypes.require_source_module(
                    owner.get_module()
                )
                selected = refactors.source_declaration_region(
                    provider, owner.get_ast()
                )
                matches = [
                    name
                    for name in members
                    if refactors.semantic_regions(
                        provider,
                        f"{name} = {value}",
                        arguments={},
                        start=selected[0],
                        end=selected[1],
                    )
                ]
                if len(matches) != 1:
                    message = "Enum default string has no unique native member producer"
                    raise ValueError(message)
                return m.Infra.SourceRewrite(
                    start=region[0], end=region[1], text=f"{prefix}.{matches[0]}"
                )
            self._prove_default_value(module, region, domain)
            return None

        def _prove_default_value(
            self,
            module: p.Infra.RopeSourceModule,
            region: tuple[int, int],
            domain: tuple[
                p.Infra.RopeSourceClass, Mapping[str, p.Infra.RopePyName], str
            ],
        ) -> None:
            """Authenticate scalar and container producers before annotation changes.

            Raises:
                ValueError: The producer has no native enum-domain proof.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            source = module.source_code
            calls = bool(refactors.word_call_regions(source, region))
            if not calls and any(
                region[0] <= first < last <= region[1]
                for first, last in self._strings(module)
            ):
                message = (
                    "Enum container default requires proven enum-domain elements "
                    "before migration"
                )
                raise ValueError(message)
            locations = {
                member.get_definition_location() for member in domain[1].values()
            }
            for first, last in self.references[module]:
                if not region[0] <= first < last <= region[1]:
                    continue
                if (
                    calls
                    and refactors.native_call_parameters(source, (first, last)) is None
                ):
                    continue
                binding = self._terminal(
                    module.get_source_binding_index().context_at(first).environment,
                    source[first:last],
                )
                if binding is None or (
                    binding.get_object() is not domain[0]
                    if calls
                    else isinstance(binding, p.Infra.RopeAssignedName)
                    and binding.get_definition_location() not in locations
                ):
                    message = (
                        "Enum default producer requires a proven enum-domain value "
                        "before migration"
                    )
                    raise ValueError(message)

        def _literal_domains(
            self,
            module: p.Infra.RopeSourceModule,
            scope: p.Infra.RopeScope,
            literal: p.Infra.RopeContractMatch,
        ) -> Iterator[
            tuple[p.Infra.RopeSourceClass, Mapping[str, p.Infra.RopePyName], str]
        ]:
            """Yield complete domains proven by the native Literal captures.

            Yields:
                Admitted enum domains whose captures prove complete membership.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            payload = refactors.semantic_capture_region(module, literal, "members")
            for domain in self._owners(module, scope, payload):
                captures = ", ".join(
                    f"${{member{index}}}" for index in range(len(domain[1]))
                )
                pattern = f"${{literal}}[{captures}]"
                for match in refactors.semantic_finder(module).get_matches(
                    pattern,
                    self.arguments,
                    start=literal.get_region()[0],
                    end=literal.get_region()[1],
                ):
                    if self._matches_domain(module, scope, match, domain[1]):
                        yield domain

        def _field_context(
            self,
            module: p.Infra.RopeSourceModule,
            match: p.Infra.RopeContractMatch,
        ) -> (
            tuple[p.Infra.RopeScope, tuple[int, int], str, p.Infra.RopeSourceClass]
            | None
        ):
            """Authenticate the declaring model, field and annotation region.

            Returns:
                The native field context, or no admission outside an eligible model.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            binding_context = module.get_source_binding_index().context_at(
                match.get_region()[0]
            )
            scope = binding_context.structural_scope
            if not self.admit(self.project, self.rule, module, scope):
                return None
            contract = refactors.semantic_capture_region(module, match, "contract")
            field = module.source_code[
                slice(*refactors.semantic_capture_region(module, match, "field"))
            ]
            if (
                not field.isidentifier()
                or field.startswith("_")
                or not isinstance(model := scope.pyobject, p.Infra.RopeSourceClass)
            ):
                return None
            return binding_context.environment, contract, field, model

        def _field_defaults(
            self,
            module: p.Infra.RopeSourceModule,
            match: p.Infra.RopeContractMatch,
            contract: tuple[int, int],
        ) -> tuple[tuple[int, int], ...]:
            """Keep required Final fields distinct from unproved class-data defaults.

            Returns:
                Effective default regions for an eligible model field.

            Raises:
                ValueError: An assigned Final declaration lacks required-field proof.

            """
            regions = self._default_regions(module, match, contract)
            if (
                match.get_ast("default") is not None
                and self._type_qualifier(module, contract, self.final)
                and any(module.source_code[slice(*value)] != "..." for value in regions)
            ):
                message = (
                    "Enum Final declaration requires native required-field proof "
                    "before migration"
                )
                raise ValueError(message)
            return regions

        def _field_rewrites(
            self,
            module: p.Infra.RopeSourceModule,
            match: p.Infra.RopeContractMatch,
        ) -> tuple[tuple[p.Infra.SourceRewrite, ...], set[tuple[str, str]]]:
            """Plan a model field through native declaration and consumer proofs.

            Returns:
                Authenticated field/default rewrites and their required imports.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            context = self._field_context(module, match)
            if context is None:
                return (), set()
            self._observe(module)
            protected = self.protected[module]
            edits: dict[tuple[int, int], p.Infra.SourceRewrite] = {}
            imports: set[tuple[str, str]] = set()
            for literal in refactors.semantic_finder(module).get_matches(
                self.rule.pattern,
                self.arguments,
                start=context[1][0],
                end=context[1][1],
            ):
                selected = literal.get_region()
                if any(
                    start <= selected[0] < selected[1] <= stop
                    for start, stop in protected
                ):
                    continue
                for domain in self._literal_domains(module, context[0], literal):
                    if self._type_qualifier(
                        module, context[1], self.classvar
                    ) or self._is_discriminator(context[3], context[2]):
                        continue
                    prefix, required = self._owner_route(
                        context[0], domain[0], domain[2]
                    )
                    for default in self._field_defaults(module, match, context[1]):
                        change = self._default_change(
                            module, default, (domain[0], domain[1], prefix)
                        )
                        if change is not None:
                            edits[change.start, change.end] = change
                    edits[selected] = m.Infra.SourceRewrite(
                        start=selected[0], end=selected[1], text=prefix
                    )
                    if required is not None:
                        imports.add(required)
            return tuple(edits.values()), imports

        def _module_rewrites(
            self,
            module: p.Infra.RopeSourceModule,
        ) -> tuple[tuple[p.Infra.SourceRewrite, ...], set[tuple[str, str]]]:
            """Complete domain proofs before entering any import candidate view.

            Returns:
                Annotation/default edits and native import requirements.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            edits: dict[tuple[int, int], p.Infra.SourceRewrite] = {}
            imports: set[tuple[str, str]] = set()
            for pattern in (
                "${field}: ${contract}",
                "${field}: ${contract} = ${default}",
            ):
                for match in refactors.semantic_finder(module).get_matches(pattern, {}):
                    changes, required = self._field_rewrites(module, match)
                    edits.update(((edit.start, edit.end), edit) for edit in changes)
                    imports.update(required)
            return tuple(edits.values()), imports

        def _module_change(
            self,
            path: Path,
            module: p.Infra.RopeSourceModule,
            planned: tuple[tuple[p.Infra.SourceRewrite, ...], set[tuple[str, str]]],
        ) -> p.Infra.RopeChangeContents:
            """Compose already-proven edits through native import candidate views.

            Returns:
                A native content change with its original source preimage.

            """
            refactors = FlextInfraUtilitiesRopeRuntimeRefactors
            resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                module.get_resource(), path
            )
            updated = refactors.content_change(
                resource, module.source_code, planned[0]
            ).new_contents
            for package, name in sorted(planned[1]):
                with self.project.source_view(
                    declared_files=FlextInfraUtilitiesWorkspaceSnapshot.workspace_declared_sources(
                        Path(self.project.root.real_path),
                        (),
                        {path: updated},
                        source_project=self.project,
                    ),
                    additional_source_folders=None,
                ):
                    imported = FlextInfraUtilitiesRopeImports.add_import(
                        self.project, resource, package, (name,), apply=False
                    )
                    if imported is not None:
                        updated = imported
            return refactors.content_change(
                resource,
                module.source_code,
                (
                    m.Infra.SourceRewrite(
                        start=0, end=len(module.source_code), text=updated
                    ),
                ),
            )

        def changes(self) -> list[p.Infra.RopeChangeContents]:
            """Return the complete native edit list without publishing effects.

            Returns:
                Native changes whose declaration and consumer proofs completed.

            """
            self._index_discriminators()
            planned = {
                path: self._module_rewrites(module)
                for path, module in self.modules.items()
            }
            return [
                self._module_change(path, module, planned[path])
                for path, module in self.modules.items()
                if planned[path][0]
            ]

    @classmethod
    def _exhaustive_enum_contracts(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        sources: Mapping[Path, str],
        paths: Sequence[Path],
    ) -> list[p.Infra.RopeChangeContents]:
        """Compose the invocation-local native enum pass in the existing planner.

        Returns:
            The operation's complete native content changes before publication.

        """
        return cls._EnumProjection(
            project, rule, sources, paths, cls._admit_contract_scope
        ).changes()

    @staticmethod
    def _admit_contract_restrictions(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        restrictions: tuple[bool, bool],
    ) -> bool:
        first, last = match.get_region()
        references = FlextInfraUtilitiesSemanticFamilyTypeReferences
        if restrictions[0]:
            if not any(
                begin <= first < last <= end
                for begin, end, _line in references.annotation_regions(
                    module.source_code, module
                )
            ):
                return False
            scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(module, first)
            payloads = references.expression_payload_ranges(
                module.source_code, project, scope, module=module
            )
            if any(begin < last and first < end for begin, end in payloads):
                return False
        if restrictions[1]:
            captured_node = match.get_ast("receiver")
            tree = module.get_ast()
            if (
                not any(
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.value is captured_node
                    for node in ast.walk(tree)
                )
                or FlextInfraUtilitiesRopeRuntimeModules.scope_at(
                    module, first
                ).get_kind()
                != c.Infra.RopeScopeKind.CLASS
            ):
                return False
        return True

    @classmethod
    def _finish_contract_edits(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[t.Infra.RopeSourcePath, str],
        rules: Sequence[p.Infra.RopeContractRule],
        items: tuple[tuple[Path, str], ...],
        result: tuple[
            MutableMapping[Path, str],
            MutableMapping[Path, MutableSequence[str]],
            MutableMapping[str, Path],
        ],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        working, applied, owned_modules = result
        retirement_sources = {**sources, **working}
        retired, providers = (
            FlextInfraUtilitiesSemanticDeclarationRetirement.retire_contract_owners(
                workspace, retirement_sources, rules, owned_modules
            )
        )
        working.update((path, retirement_sources[path]) for path in working)
        if any(
            rule.operation == c.Infra.RopeContractOperation.MATERIALIZE_DELEGATIONS
            for rule in rules
        ) and any(working[path] != source for path, source in items):
            FlextInfraUtilitiesSemanticDeclarationRelocation.preflight_semantic_import_graph(
                workspace, sources, retirement_sources
            )
        for path, original in items:
            if working[path] != original or path in providers:
                applied.setdefault(path, []).append(
                    "completed native ownership transfer"
                )
        return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=source,
                    updated_source=working[path],
                    retire_file=path in retired,
                    changes=tuple(applied[path]),
                )
                for path, source in items
                if source != working[path] or path in providers
            )
        )

    @classmethod
    def _admit_contract_match(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        *,
        context: tuple[
            MutableMapping[tuple[str, str], t.Infra.RopeImplementationPaths],
            Mapping[t.Infra.RopeSourcePath, str],
            Mapping[str, t.Infra.RopeSourcePath] | None,
        ],
    ) -> bool:
        """Prove native receivers, evaluation safety and destination bindings.

        Args:
            project: The rope project containing the module.
            rule: The contract rule being evaluated.
            module: The Python module under consideration.
            match: The specific contract match instance.
            context: A tuple containing the current state of implementation owners,
              sources, and owned modules.

        Returns:
            Whether every native admission proof accepts the captured match.

        Raises:
            ValueError: If the contract cannot be admitted due to assertion lowering
              requirements.

        """
        implementation_owners, sources, owned_modules = context
        if not cls._admit_contract_origin(
            project, rule, module, match, (implementation_owners, sources)
        ) or not cls._admit_contract_call(project, rule, module, match):
            return False
        if rule.receiver_methods and not cls._admitted_factory_receiver(
            project, module, match, rule.receiver_methods
        ):
            return False
        scope = FlextInfraUtilitiesRopeRuntimeModules.scope_at(
            module, match.get_region()[0]
        )
        if not cls._admit_contract_transfer(
            project, rule, module, match, (scope, owned_modules)
        ) or not cls._admit_contract_scope(project, rule, module, scope):
            return False
        if not cls._admit_readonly_contract(project, rule, match, scope):
            return False
        cls._require_deferred_annotation(project, rule, module, match, (scope, sources))
        cls._require_contract_evaluation(project, rule, module, match, scope)
        if not cls._admitted_unshadowed_builtins(rule, scope):
            if rule.pattern.startswith("assert "):
                message = (
                    f"{rule.id}: assert lowering requires unshadowed builtins "
                    f"in {module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
            return False
        return FlextInfraUtilitiesImportLaw.import_contract_bindings(
            project, rule, module, scope, match.get_region()[0]
        )

    @staticmethod
    def _admit_contract_origin(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        context: tuple[
            MutableMapping[tuple[str, str], t.Infra.RopeImplementationPaths],
            Mapping[t.Infra.RopeSourcePath, str],
        ],
    ) -> bool:
        implementation_owners, _sources = context
        resource = module.get_resource()
        if rule.value_default is not None:
            default = match.get_ast(rule.value_default)
            if isinstance(default, ast.Constant) and default.value is Ellipsis:
                return False
        if rule.factory_default is not None:
            factory = match.get_ast(rule.factory_default)
            if isinstance(factory, ast.Constant) and factory.value is None:
                return False
            if rule.readonly_contract is not None and not isinstance(
                factory, c.Infra.AST_NAME_REFERENCE_TYPES
            ):
                return False
        if rule.implementation_owner is not None:
            identity = rule.implementation_owner
            if identity not in implementation_owners:
                implementation_owners[identity] = (
                    FlextInfraUtilitiesCodemodProject.implementation_owner_modules(
                        project,
                        m.Infra.CodemodPrimitiveOwner(arg=identity),
                    )
                )
            if (
                resource is not None
                and Path(resource.real_path) in implementation_owners[identity]
            ):
                return False
        return True

    @classmethod
    def _admit_contract_call(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
    ) -> bool:
        if rule.required_field or rule.defaulted_field or rule.private_attribute:
            if not cls._admitted_field_metadata(project, rule, module, match):
                return False
        elif rule.call_target is not None:
            captured = match.get_ast(rule.call_target)
            tree = module.get_ast()
            if captured is None:
                msg = f"{rule.id}: call target requires an original native AST capture"
                raise ValueError(msg)
            invocation = next(
                (
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and node.func is captured
                ),
                None,
            )
            if invocation is None:
                return False
            return cls._admit_invocation_arguments(rule, invocation)
        elif rule.explicit_arguments:
            message = f"{rule.id}: explicit-argument proof requires a call target"
            raise ValueError(message)
        elif rule.missing_keywords:
            msg_0 = f"{rule.id}: missing-keyword proof requires a call target"
            raise ValueError(msg_0)
        return True

    @staticmethod
    def _admit_invocation_arguments(
        rule: p.Infra.RopeContractRule,
        invocation: ast.Call,
    ) -> bool:
        if rule.explicit_arguments and (
            any(isinstance(argument, ast.Starred) for argument in invocation.args)
            or any(keyword.arg is None for keyword in invocation.keywords)
        ):
            message = f"{rule.id}: expanded arguments have no proven contract"
            raise ValueError(message)
        if rule.missing_keywords:
            if any(
                keyword.arg in rule.missing_keywords for keyword in invocation.keywords
            ):
                return False
            if any(keyword.arg is None for keyword in invocation.keywords):
                message = (
                    f"{rule.id}: expanded keywords cannot prove missing injected ports"
                )
                raise ValueError(message)
        return True

    @staticmethod
    def _admit_contract_transfer(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        context: tuple[
            p.Infra.RopeScope,
            Mapping[str, t.Infra.RopeSourcePath] | None,
        ],
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        scope, owned_modules = context
        if rule.ownership_transfer is not None:
            if owned_modules is None:
                message = (
                    f"{rule.id}: ownership transfer has no original project inventory"
                )
                raise ValueError(message)
            relocation = FlextInfraUtilitiesSemanticDeclarationRetirement
            original = relocation.contract_transfer_binding(
                project, rule.ownership_transfer, owned_modules
            )
            first, last = match.get_region()
            if any(
                left <= first and last <= right
                for assignment in module.get_source_binding_index().assignment_layouts(
                    scope
                )
                for _name, (left, right) in assignment.targets
            ):
                return False
            expression = ast.parse(module.source_code[first:last], mode="eval").body
            selected = (
                expression.func if isinstance(expression, ast.Call) else expression
            )
            actual = runtime.resolve_symbol(scope, selected)
            if original is None:
                # Already-migrated destinations and unrelated homonyms are not
                # original receivers. An unresolved original receiver is not a
                # successful retirement receipt.
                if any(
                    FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                        project,
                        module,
                        match.get_ast(capture),
                        constraints,
                        name=capture,
                    )
                    for capture, constraints in rule.arguments.items()
                ):
                    message = (
                        f"{rule.id}: transferred owner is absent "
                        "but a receiver survives"
                    )
                    raise ValueError(message)
                return False
            unknown = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
                "rope.base.pyobjects", "get_unknown"
            )()
            if actual is None or (
                actual.get_object() == unknown
                and relocation.contract_assignment(actual) is None
            ):
                message = (
                    f"{rule.id}: unproven transferred receiver in "
                    f"{module.get_name()}:{scope.get_start()}"
                )
                raise ValueError(message)
            if not runtime.same_name(original, actual):
                return False
        return True

    @classmethod
    def _admit_contract_scope(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if rule.scope_kinds and scope.get_kind() not in rule.scope_kinds:
            return False
        if rule.families and not cls._admitted_family(rule, module):
            return False
        ancestry = FlextInfraUtilitiesDeclarationPayload.class_ancestry(scope.pyobject)
        return not (
            rule.model_bases
            and not any(
                runtime.qualified_name(project, name).get_object() in ancestry
                for name in rule.model_bases
            )
        )

    @staticmethod
    def _admit_readonly_contract(
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        match: p.Infra.RopeContractMatch,
        scope: p.Infra.RopeScope,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        if rule.readonly_contract is not None:
            if not rule.readonly_origins:
                message = f"{rule.id}: read-only admission requires native origins"
                raise ValueError(message)
            contract = match.get_ast(rule.readonly_contract)
            if not isinstance(contract, ast.expr):
                message = f"{rule.id}: read-only contract has no native expression"
                raise ValueError(message)
            origin = runtime.annotation_origin(project, contract, scope)
            unknown = FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
                "rope.base.pyobjects", "get_unknown"
            )()
            if (
                origin is None
                or origin.get_object() == unknown
                or not any(
                    (expected := runtime.qualified_name(project, identity)).get_object()
                    != unknown
                    and runtime.same_name(origin, expected)
                    for identity in rule.readonly_origins
                )
            ):
                return False
        return True

    @classmethod
    def _require_deferred_annotation(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        context: tuple[p.Infra.RopeScope, Mapping[t.Infra.RopeSourcePath, str]],
    ) -> None:
        scope, sources = context
        if rule.deferred_contract is not None:
            captured = match.get_ast(rule.deferred_contract)
            tree = module.get_ast()
            annotation = next(
                (
                    node.annotation
                    for node in ast.walk(tree)
                    if isinstance(node, ast.AnnAssign)
                    and any(part is captured for part in ast.walk(node.annotation))
                ),
                None,
            )
            if annotation is None:
                message = (
                    f"{rule.id}: deferred contract has no complete field annotation"
                )
                raise ValueError(message)
            cls._require_deferred_contract(
                project, rule, module, (scope, annotation, match), sources
            )

    @classmethod
    def _require_contract_evaluation(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        scope: p.Infra.RopeScope,
    ) -> None:
        refactors = FlextInfraUtilitiesRopeRuntimeRefactors
        if rule.pattern.startswith("assert "):
            source = module.source_code
            region = match.get_region()
            tree = module.get_ast()
            statement = next(
                (
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Assert)
                    and node.test is match.get_ast("predicate")
                ),
                None,
            )
            message = (
                f"{rule.id}: assert lowering requires a complete standalone statement "
                f"with retained trivia in {module.get_name()}:"
                f"{statement.lineno if statement is not None else scope.get_start()}"
            )
            line_start = source.rfind("\n", 0, region[0]) + 1
            partial_line = (
                source[line_start : region[0]].strip()
                or source[region[1] :].partition("\n")[0].strip()
            )
            if (
                statement is None
                or statement.msg is not match.get_ast("message")
                or (
                    ast.get_source_segment(source, statement)
                    != source[region[0] : region[1]]
                )
                or partial_line
                or source[:line_start].rstrip("\r\n").endswith("\\")
            ):
                raise ValueError(message)
            captures = tuple(
                refactors.semantic_capture_region(module, match, name)
                for name in ("predicate", "message")
                if match.get_ast(name) is not None
            )
            # Native Restructure retains only captured text and reindents every
            # subsequent line. Never drop trivia or indent a literal's payload.
            for ignored in refactors.ignored_regions(source):
                if region[0] <= ignored[0] < region[1] and (
                    (
                        source[ignored[0] : ignored[1]].startswith("#")
                        and not any(
                            start <= ignored[0] < ignored[1] <= stop
                            for start, stop in captures
                        )
                    )
                    or (
                        line_start < region[0]
                        and len(source[ignored[0] : ignored[1]].splitlines()) > 1
                    )
                ):
                    raise ValueError(message)
        discarded = next(
            (
                capture
                for capture in rule.drops
                if not isinstance(match.get_ast(capture), ast.Constant)
            ),
            None,
        )
        if discarded is not None:
            message = (
                f"{rule.id}: cannot discard authored evaluation of {discarded} "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)
        # Only the capture the goal evaluates again must be free of calls; the
        # rest of the declaration (Annotated metadata, the field call) runs once.
        if rule.repeats is not None and refactors.word_call_regions(
            module.source_code,
            refactors.semantic_capture_region(module, match, rule.repeats),
        ):
            message = (
                f"{rule.id}: annotation evaluation cannot repeat authored calls "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)
        if rule.repeats is not None and not cls._admitted_repeated_contract(
            scope, match.get_ast(rule.repeats)
        ):
            message = (
                f"{rule.id}: annotation has an unbound enclosing owner; "
                "retain the native factory and fix its declaring source"
            )
            raise ValueError(message)
        if (
            rule.reorders_annotation
            and len(cls._field_reordered_calls(project, rule, module, match)) != 1
        ):
            message = (
                f"{rule.id}: annotation evaluation cannot reorder authored calls "
                f"in {module.get_name()}:{scope.get_start()}"
            )
            raise ValueError(message)

    @classmethod
    def _require_deferred_contract(
        cls,
        project: p.Infra.RopeProject,
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
        contract: tuple[p.Infra.RopeScope, ast.expr, p.Infra.RopeContractMatch],
        sources: Mapping[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Prove native closure identities without evaluating or unquoting types.

        Raises:
            ValueError: If the field has no proven native resolution.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        field = contract[2].get_ast("field")
        field_binding = (
            runtime.resolve_symbol(contract[0], field)
            if isinstance(field, ast.expr)
            else None
        )
        message = (
            f"{rule.id}: deferred contract has no proven native resolution "
            f"in {module.get_name()}:{contract[0].get_start()}; "
            "fix the declaring source with its actual resolved contract"
        )
        if field_binding is None:
            raise ValueError(message)
        pending = [(contract[1], contract[0], frozenset[str]())]
        metadata: list[tuple[ast.expr, p.Infra.RopeScope]] = []
        visited: set[tuple[str, int]] = set()
        intrinsics = cls._deferred_intrinsics(project, rule)
        while pending:
            current = pending.pop()
            cls._deferred_expression_aliases(
                project,
                current,
                (sources, message, intrinsics),
                metadata,
                (pending, visited),
            )
        if metadata:
            cls._require_idempotent_metadata(
                project, tuple(metadata), field_binding, message, sources
            )

    @staticmethod
    def _deferred_intrinsics(
        project: p.Infra.RopeProject, rule: p.Infra.RopeContractRule
    ) -> tuple[
        Mapping[str, p.Infra.RopePyName],
        tuple[p.Infra.RopePyName, ...],
        t.Infra.RopeNativeObject,
    ]:
        builtin_module = project.get_module("__builtin__")
        names = FlextInfraUtilitiesSemanticContracts._deferred_builtin_names(
            builtin_module
        )
        intrinsic_types = tuple(
            FlextInfraUtilitiesRopeRuntimeModules.qualified_name(project, identity)
            for identity in (
                *rule.readonly_origins,
                "typing.Annotated",
                "typing.Literal",
            )
        )
        unknown = u.type_adapter(
            TypeForm(t.Port[t.Infra.RopeNativeObject])
        ).validate_python(
            FlextInfraUtilitiesRopeRuntimeTypes.runtime_callable(
                c.Infra.ROPE_PYOBJECTS_MODULE, "get_unknown"
            )(),
            strict=True,
        )
        return names, intrinsic_types, unknown

    @staticmethod
    def _deferred_builtin_names(
        module: p.AttributeProbe,
    ) -> Mapping[str, p.Infra.RopePyName]:
        if not isinstance(module, p.Infra.RopeSemanticModule):
            message = "native builtins module has no semantic module contract"
            raise TypeError(message)
        return module.get_attributes()

    @classmethod
    def _deferred_expression_aliases(
        cls,
        project: p.Infra.RopeProject,
        expression: tuple[ast.expr, p.Infra.RopeScope, frozenset[str]],
        context: tuple[
            Mapping[t.Infra.RopeSourcePath, str],
            str,
            tuple[
                Mapping[str, p.Infra.RopePyName],
                tuple[p.Infra.RopePyName, ...],
                t.Infra.RopeNativeObject,
            ],
        ],
        metadata: list[tuple[ast.expr, p.Infra.RopeScope]],
        state: tuple[
            list[tuple[ast.expr, p.Infra.RopeScope, frozenset[str]]],
            set[tuple[str, int]],
        ],
    ) -> None:
        lexical = expression[1]
        closure: p.Infra.RopeScope | None = lexical
        while closure is not None and closure.get_kind() == c.Infra.RopeScopeKind.CLASS:
            closure = closure.parent
        if closure is None:
            raise ValueError(context[1])
        holder = lexical.pyobject.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder):
            raise ValueError(context[1])
        source = ast.unparse(expression[0])
        tree = ast.parse(source, mode="eval")
        protected = (
            FlextInfraUtilitiesSemanticFamilyTypeReferences.expression_payload_ranges(
                source, project, lexical
            )
        )
        metadata_regions = cls._deferred_metadata_regions(
            project, (source, tree), lexical, metadata, (protected, context[1])
        )
        cls._deferred_reference_aliases(
            project,
            (source, tree, expression[2], metadata_regions),
            (lexical, closure, holder),
            context,
            state,
        )

    @staticmethod
    def _deferred_metadata_regions(
        project: p.Infra.RopeProject,
        syntax: tuple[str, ast.Expression],
        lexical: p.Infra.RopeScope,
        metadata: list[tuple[ast.expr, p.Infra.RopeScope]],
        context: tuple[frozenset[tuple[int, int]], str],
    ) -> list[tuple[int, int]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        source, tree = syntax
        protected, message = context
        calls: set[ast.Call] = set()
        regions: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript) or not isinstance(
                node.slice, ast.Tuple
            ):
                continue
            binding = runtime.resolve_symbol(lexical, node.value)
            if binding is None or not runtime.same_name(
                binding, runtime.qualified_name(project, "typing.Annotated")
            ):
                continue
            for item in node.slice.elts[1:]:
                metadata.append((item, lexical))
                text = ast.get_source_segment(source, item)
                if text is None:
                    failure = f"{message}; metadata has no source region"
                    raise ValueError(failure)
                begin = runtime.source_offset(source, item)
                regions.append((begin, begin + len(text)))
                calls.update(
                    child for child in ast.walk(item) if isinstance(child, ast.Call)
                )
        FlextInfraUtilitiesSemanticContracts._require_deferred_evaluation(
            syntax, protected, calls, message
        )
        return regions

    @staticmethod
    def _require_deferred_evaluation(
        syntax: tuple[str, ast.Expression],
        protected: frozenset[tuple[int, int]],
        calls: set[ast.Call],
        message: str,
    ) -> None:
        source, tree = syntax
        for (
            begin,
            end,
            _metadata,
        ) in FlextInfraUtilitiesRopeRuntimeRefactors.ignored_regions(source):
            if FlextInfraUtilitiesSemanticFamilyTypeReferences.string_constant(
                source[begin:end]
            ) is not None and not any(
                first <= begin and end <= last for first, last in protected
            ):
                failure = f"{message}; quoted type identity is unresolved"
                raise ValueError(failure)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if node not in calls:
                failure = f"{message}; authored evaluation cannot repeat"
                raise ValueError(failure)

    @classmethod
    def _deferred_reference_aliases(
        cls,
        project: p.Infra.RopeProject,
        syntax: tuple[str, ast.Expression, frozenset[str], list[tuple[int, int]]],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope, p.Infra.RopeSourceModule],
        context: tuple[
            Mapping[t.Infra.RopeSourcePath, str],
            str,
            tuple[
                Mapping[str, p.Infra.RopePyName],
                tuple[p.Infra.RopePyName, ...],
                t.Infra.RopeNativeObject,
            ],
        ],
        state: tuple[
            list[tuple[ast.expr, p.Infra.RopeScope, frozenset[str]]],
            set[tuple[str, int]],
        ],
    ) -> None:
        source, tree, parameters, regions = syntax
        identifiers = {
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, c.Infra.AST_NAME_REFERENCE_TYPES)
        }
        for (
            begin,
            end,
        ) in FlextInfraUtilitiesSemanticFamilyTypeReferences.reference_regions(source):
            primary = source[begin:end]
            if primary not in identifiers or primary.partition(".")[0] in parameters:
                continue
            alias = cls._deferred_primary_alias(
                project,
                (primary, any(a <= begin and end <= b for a, b in regions)),
                scopes,
                context,
            )
            if alias is not None:
                cls._enqueue_deferred_alias(alias, state[0], state[1])

    @staticmethod
    def _deferred_primary_alias(
        project: p.Infra.RopeProject,
        reference: tuple[str, bool],
        scopes: tuple[p.Infra.RopeScope, p.Infra.RopeScope, p.Infra.RopeSourceModule],
        context: tuple[
            Mapping[t.Infra.RopeSourcePath, str],
            str,
            tuple[
                Mapping[str, p.Infra.RopePyName],
                tuple[p.Infra.RopePyName, ...],
                t.Infra.RopeNativeObject,
            ],
        ],
    ) -> tuple[ast.TypeAlias, p.Infra.RopeScope] | None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        primary, metadata = reference
        lexical, closure, holder = scopes
        sources, message, intrinsics = context
        original = runtime.expression_name(lexical, primary)
        actual = runtime.expression_name(closure, primary)
        alias = (
            runtime.annotation_alias_definition(original)
            if original is not None
            else None
        )
        if (
            original is None
            or actual is None
            or (
                FlextInfraUtilitiesSemanticContracts._is_unknown_native_object(
                    actual.get_object(), intrinsics[2]
                )
                and alias is None
            )
            or not runtime.same_name(original, actual)
        ):
            failure = f"{message}; unresolved closure identity: {primary}"
            raise ValueError(failure)
        if metadata:
            return None
        builtin = intrinsics[0].get(primary)
        if builtin is not None and runtime.same_name(builtin, actual):
            return None
        if alias is not None or any(
            runtime.same_name(expected, actual) for expected in intrinsics[1]
        ):
            stable = all(
                FlextInfraUtilitiesCodemodProject.single_reaching_binding(
                    holder, closure, candidate, len(holder.source_code)
                )
                for candidate in dict.fromkeys((primary.partition(".")[0], primary))
            )
        else:
            stable = FlextInfraUtilitiesCodemodProject.stable_binding_chain(
                (project, holder, closure), primary, len(holder.source_code), sources
            )
        if not stable:
            failure = f"{message}; unstable closure binding: {primary}"
            raise ValueError(failure)
        return alias

    @staticmethod
    def _is_unknown_native_object(
        value: p.AttributeProbe,
        unknown: t.Infra.RopeNativeObject,
    ) -> bool:
        if not isinstance(
            value,
            FlextInfraUtilitiesRopeRuntimeTypes.runtime_type(
                c.Infra.ROPE_PYOBJECTS_MODULE, "PyObject"
            ),
        ):
            message = "native binding has no Rope object identity"
            raise TypeError(message)
        return (value == unknown) is True

    @staticmethod
    def _enqueue_deferred_alias(
        alias: tuple[ast.TypeAlias, p.Infra.RopeScope],
        pending: list[tuple[ast.expr, p.Infra.RopeScope, frozenset[str]]],
        visited: set[tuple[str, int]],
    ) -> None:
        declaration, owner_scope = alias
        owner = owner_scope.pyobject.get_module()
        key = (owner.get_name(), declaration.lineno)
        if key in visited:
            return
        visited.add(key)
        parameters: set[str] = set()
        for parameter in declaration.type_params:
            if not isinstance(parameter, c.Infra.AST_TYPE_PARAM_TYPES):
                failure = "native alias has an unknown type parameter"
                raise TypeError(failure)
            parameters.add(parameter.name)
        pending.append((declaration.value, owner_scope, frozenset(parameters)))

    @staticmethod
    def _metadata_constructors(
        project: p.Infra.RopeProject,
        field: p.Infra.RopePyName,
        failure: str,
    ) -> list[tuple[p.Infra.RopePyName, bool]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        # The SDK owns the declarative constraint constructors, not a local name list.
        lookup = runtime.qualified_name(
            project, "pydantic.fields.FieldInfo.metadata_lookup"
        )
        owner, line = runtime.definition_location(lookup)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(owner):
            raise ValueError(failure)
        owner_tree = owner.get_ast()
        table = next(
            (
                node
                for node in ast.walk(owner_tree)
                if isinstance(node, ast.AnnAssign)
                and node.lineno == line
                and isinstance(node.value, ast.Dict)
            ),
            None,
        )
        if table is None or not isinstance(table.value, ast.Dict):
            raise ValueError(failure)
        table_scope = runtime.scope_at(
            owner, runtime.source_offset(owner.source_code, table)
        )
        constructors: list[tuple[p.Infra.RopePyName, bool]] = [(field, False)]
        dataclass = runtime.qualified_name(project, "dataclasses.dataclass")
        for value in table.value.values:
            if not isinstance(value, c.Infra.AST_NAME_REFERENCE_TYPES):
                continue
            binding = runtime.resolve_symbol(table_scope, value)
            if binding is None:
                raise ValueError(failure)
            constructors.append((
                binding,
                FlextInfraUtilitiesSemanticContracts._metadata_constructor_frozen(
                    dataclass, binding, failure
                ),
            ))
        return constructors

    @staticmethod
    def _metadata_constructor_frozen(
        dataclass: p.Infra.RopePyName,
        binding: p.Infra.RopePyName,
        failure: str,
    ) -> bool:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        origin, location = runtime.definition_location(binding)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(origin):
            raise ValueError(failure)
        origin_tree = origin.get_ast()
        declaration = next(
            (
                node
                for node in ast.walk(origin_tree)
                if isinstance(node, ast.ClassDef) and node.lineno == location
            ),
            None,
        )
        if declaration is None:
            raise ValueError(failure)
        lexical = runtime.scope_at(
            origin, runtime.source_offset(origin.source_code, declaration)
        )
        return any(
            isinstance(decorator, ast.Call)
            and (factory := runtime.resolve_symbol(lexical, decorator.func)) is not None
            and runtime.same_name(dataclass, factory)
            and any(
                keyword.arg == "frozen"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in decorator.keywords
            )
            for decorator in declaration.decorator_list
        )

    @classmethod
    def _require_idempotent_metadata(
        cls,
        project: p.Infra.RopeProject,
        metadata: tuple[tuple[ast.expr, p.Infra.RopeScope], ...],
        field: p.Infra.RopePyName,
        message: str,
        sources: Mapping[t.Infra.RopeSourcePath, str],
    ) -> None:
        """Require declarative metadata, not merely a stable binding to a callback.

        Raises:
            ValueError: If authored metadata effects cannot be proven idempotent.

        """
        failure = f"{message}; additional validation effects are not proven idempotent"
        constructors = cls._metadata_constructors(project, field, failure)
        pending = [
            (node, lexical, False, frozenset[tuple[str, int]]())
            for node, lexical in metadata
        ]
        while pending:
            node, lexical, bound, visiting = pending.pop()
            children: list[ast.expr]
            match node:
                case ast.Constant():
                    continue
                case ast.Tuple() | ast.List() | ast.Set():
                    if bound and not isinstance(node, ast.Tuple):
                        raise ValueError(failure)
                    children = list(node.elts)
                case ast.Dict():
                    if bound or any(key is None for key in node.keys):
                        raise ValueError(failure)
                    children = [
                        key for key in node.keys if key is not None
                    ] + node.values
                case ast.UnaryOp(op=ast.UAdd() | ast.USub()):
                    children = [node.operand]
                case ast.Call():
                    children = cls._metadata_call_children(
                        node, lexical, (bound, constructors), failure
                    )
                case ast.Name() | ast.Attribute():
                    value = cls._metadata_bound_value(
                        project, node, lexical, (sources, failure, visiting)
                    )
                    pending.append((
                        value[0],
                        value[1],
                        True,
                        visiting | {value[2]},
                    ))
                    continue
                case _:
                    raise ValueError(failure)
            pending.extend((child, lexical, False, visiting) for child in children)

    @staticmethod
    def _metadata_call_children(
        node: ast.Call,
        lexical: p.Infra.RopeScope,
        constructors: tuple[bool, Sequence[tuple[p.Infra.RopePyName, bool]]],
        failure: str,
    ) -> list[ast.expr]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        bound, declared = constructors
        actual = runtime.resolve_symbol(lexical, node.func)
        # A stable mutable metadata instance can acquire a different schema.
        if actual is None or not any(
            runtime.same_name(actual, constructor) and (not bound or frozen)
            for constructor, frozen in declared
        ):
            raise ValueError(failure)
        holder = lexical.pyobject.get_module()
        callee = ast.unparse(node.func)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder) or not all(
            FlextInfraUtilitiesCodemodProject.single_reaching_binding(
                holder, lexical, candidate, len(holder.source_code)
            )
            for candidate in dict.fromkeys((callee.partition(".")[0], callee))
        ):
            raise ValueError(failure)
        return list(node.args) + [item.value for item in node.keywords]

    @staticmethod
    def _metadata_bound_value(
        project: p.Infra.RopeProject,
        node: ast.Name | ast.Attribute,
        lexical: p.Infra.RopeScope,
        context: tuple[
            Mapping[t.Infra.RopeSourcePath, str], str, frozenset[tuple[str, int]]
        ],
    ) -> tuple[ast.expr, p.Infra.RopeScope, tuple[str, int]]:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        sources, failure, visiting = context
        binding = runtime.resolve_symbol(lexical, node)
        if binding is None:
            raise ValueError(failure)
        module = lexical.pyobject.get_module()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module) or not (
            FlextInfraUtilitiesCodemodProject.stable_binding_chain(
                (project, module, lexical),
                ast.unparse(node),
                len(module.source_code),
                sources,
            )
        ):
            raise ValueError(failure)
        holder, location = runtime.definition_location(binding)
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(holder):
            raise ValueError(failure)
        if location is None:
            raise ValueError(failure)
        key = (holder.get_name(), location)
        if key in visiting:
            raise ValueError(failure)
        bound_name = (
            binding.imported_name
            if isinstance(binding, p.Infra.RopeImportedName)
            else ast.unparse(node).rpartition(".")[-1]
        )
        holder_tree = holder.get_ast()
        declaration = next(
            (
                item
                for item in ast.walk(holder_tree)
                if isinstance(item, c.Infra.AST_ASSIGNMENT_TYPES)
                and item.lineno == location
                and item.value is not None
                and any(
                    isinstance(target, ast.Name) and target.id == bound_name
                    for target in (
                        item.targets if isinstance(item, ast.Assign) else (item.target,)
                    )
                )
            ),
            None,
        )
        if declaration is None or declaration.value is None:
            raise ValueError(failure)
        return (
            declaration.value,
            runtime.scope_at(
                holder, runtime.source_offset(holder.source_code, declaration)
            ),
            key,
        )

    @staticmethod
    def _admitted_repeated_contract(
        scope: p.Infra.RopeScope,
        contract: p.AttributeProbe | None,
    ) -> bool:
        """Keep annotation-only references to classes still under construction lazy.

        Returns:
            Whether repeated evaluation avoids enclosing classes under construction.

        Raises:
            TypeError: If the capture has no original Python syntax tree.

        """
        if not isinstance(contract, ast.AST):
            message = "repeated contract requires the original native syntax tree"
            raise TypeError(message)
        constructing: list[p.Infra.RopePyObject] = []
        enclosing: p.Infra.RopeScope | None = scope
        while (
            enclosing is not None
            and enclosing.get_kind() == c.Infra.RopeScopeKind.CLASS
        ):
            constructing.append(enclosing.pyobject)
            enclosing = enclosing.parent
        if not constructing:
            return True
        pending: list[tuple[ast.AST, frozenset[str]]] = [(contract, frozenset())]
        while pending:
            node, bound = pending.pop()
            primary = node
            while isinstance(primary, ast.Attribute):
                primary = primary.value
            if (
                isinstance(node, c.Infra.AST_NAME_REFERENCE_TYPES)
                and isinstance(primary, ast.Name)
                and isinstance(primary.ctx, ast.Load)
                and primary.id not in bound
            ):
                binding = FlextInfraUtilitiesRopeRuntimeModules.resolve_symbol(
                    scope, node
                )
                if binding is not None and binding.get_object() in constructing:
                    return False
            for (
                children,
                local,
            ) in FlextInfraUtilitiesSemanticCutoverClassScope.evaluated_parts(node):
                pending.extend((child, bound | local) for child in children)
        return True

    @staticmethod
    def _admitted_family(
        rule: p.Infra.RopeContractRule,
        module: p.Infra.RopePyModule,
    ) -> bool:
        """Elect a physical source's family from its native qualified identity.

        Returns:
            Whether the elected family is declared by the contract rule.

        Raises:
            ValueError: If the family-constrained module has no source resource.

        """
        if module.get_resource() is None:
            message = f"{rule.id}: family-constrained match has no source resource"
            raise ValueError(message)
        _package, *parts = module.get_name().split(".")
        if not parts:
            return False
        family = (
            FlextInfraUtilitiesCodegenNamespace.facade_family_of_file(
                f"{parts[0]}.py",
            )
            if len(parts) == 1
            else FlextInfraUtilitiesCodegenNamespace.facade_family_of_directory(
                parts[0],
            )
        )
        return family in rule.families

    @staticmethod
    def _admitted_unshadowed_builtins(
        rule: p.Infra.RopeContractRule,
        scope: p.Infra.RopeScope,
    ) -> bool:
        """Require every builtin to retain its native lexical binding.

        Returns:
            Whether all required builtin names remain unshadowed.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        return all(
            (lexical := runtime.lexical_scope(scope, name)) is not None
            and lexical.get_kind() == c.Infra.RopeScopeKind.MODULE
            and name not in lexical.get_defined_names()
            for name in rule.unshadowed_builtins
        )

    @classmethod
    def _admitted_factory_receiver(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        match: p.Infra.RopeContractMatch,
        methods: Sequence[str],
    ) -> bool:
        """Admit discarded compatible receivers; never inline factory evaluation.

        Returns:
            Whether the captured factory has only proven discarded consumers.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        tree = module.get_ast()
        parents = FlextInfraUtilitiesRopeAnalysis.ast_parent_map(tree)
        nodes: MutableMapping[tuple[type[ast.AST], int], ast.AST] = {
            (type(node), runtime.source_offset(module.source_code, node)): node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call | ast.Name)
        }
        start, _end = match.get_region()
        call = nodes.get((ast.Call, start))
        if not isinstance(call, ast.Call):
            return False

        result_contract: str | None = inspect.get_annotations(
            getattr(p.Logger, methods[0])
        ).get("return")
        return cls._admit_factory_uses(
            project,
            module,
            cls._factory_bound_receiver(project, module, call, parents),
            (parents, nodes, methods, result_contract),
        )

    @staticmethod
    def _prove_logging_value(
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        argument: p.Infra.RopeAstNode,
    ) -> None:
        if not isinstance(argument, ast.AST):
            message = "native logging argument proof requires source syntax"
            raise TypeError(message)
        if any(
            FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                project,
                module,
                argument,
                f"{c.Infra.ROPE_BUILTIN_TYPE_CONSTRAINT_PREFIX}{native}",
                name="",
            )
            for native in ("str", "bool", "int", "float")
        ):
            return
        u.json_value_adapter().validate_python(ast.literal_eval(argument), strict=True)

    @classmethod
    def _factory_bound_receiver(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        call: ast.Call,
        parents: Mapping[int, t.Infra.RopeAstNode],
    ) -> ast.Call | None:
        while (
            isinstance(member := parents.get(id(call)), ast.Attribute)
            and member.value is call
        ):
            declared = getattr(p.Logger, member.attr, None)
            if (
                not callable(declared)
                or inspect.get_annotations(declared).get("return") != "Self"
            ):
                break
            invocation = parents.get(id(member))
            if not isinstance(invocation, ast.Call) or invocation.func is not member:
                return None
            cls._require_factory_bound_call(
                project, module, member, invocation, inspect.signature(declared)
            )
            call = invocation
        return call

    @classmethod
    def _require_factory_bound_call(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        member: ast.Attribute,
        invocation: ast.Call,
        signature: inspect.Signature,
    ) -> None:
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        native_scope = runtime.scope_at(
            module, runtime.source_offset(module.source_code, member)
        )
        # The bound member hangs off the factory's native call result, so Rope
        # infers it statically from the call; no identifier chain can name it.
        bound = runtime.runtime_callable("rope.base.evaluate", "eval_node")(
            native_scope, member
        )
        if (
            not isinstance(bound, p.Infra.RopePyName)
            or any(keyword.arg is None for keyword in invocation.keywords)
            or any(isinstance(argument, ast.Starred) for argument in invocation.args)
        ):
            message = (
                "unproven native bound context: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        signature.bind(
            None,
            *invocation.args,
            **{
                keyword.arg: keyword.value
                for keyword in invocation.keywords
                if keyword.arg is not None
            },
        )
        if invocation.keywords and not any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        ):
            message = (
                "unproven native bound keywords: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        for argument in invocation.args:
            if not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
                project,
                module,
                argument,
                f"{c.Infra.ROPE_BUILTIN_TYPE_CONSTRAINT_PREFIX}str",
                name="",
            ):
                message = (
                    "unproven native bound key: "
                    f"{module.get_name()}:{invocation.lineno}"
                )
                raise ValueError(message)
        for keyword in invocation.keywords:
            cls._prove_logging_value(project, module, keyword.value)

    @staticmethod
    def _discarded_logging_emission(
        node: p.Infra.RopeAstNode,
        parents: Mapping[int, t.Infra.RopeAstNode],
        methods: Sequence[str],
        result_contract: str | None,
    ) -> bool:
        member = parents.get(id(node))
        invocation = parents.get(id(member))
        statement = parents.get(id(invocation))
        declared = (
            getattr(p.Logger, member.attr, None)
            if isinstance(member, ast.Attribute)
            else None
        )
        output = (
            getattr(p.OutputLogger, member.attr, None)
            if isinstance(member, ast.Attribute)
            else None
        )
        return (
            isinstance(member, ast.Attribute)
            and member.value is node
            and (
                member.attr in methods
                or callable(output)
                or (
                    callable(declared)
                    and inspect.get_annotations(declared).get("return")
                    == result_contract
                )
            )
            and isinstance(invocation, ast.Call)
            and invocation.func is member
            and isinstance(statement, ast.Expr)
            and statement.value is invocation
        )

    @classmethod
    def _prove_logging_arguments(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        node: p.Infra.RopeAstNode,
        parents: Mapping[int, t.Infra.RopeAstNode],
        methods: Sequence[str],
    ) -> None:
        member = parents[id(node)]
        invocation = parents[id(member)]
        if not isinstance(member, ast.Attribute) or not isinstance(
            invocation, ast.Call
        ):
            message = "native emission proof has no method invocation"
            raise TypeError(message)
        if (
            member.attr not in methods
            or not invocation.args
            or invocation.keywords
            or any(isinstance(argument, ast.Starred) for argument in invocation.args)
        ):
            message = (
                "unproven native logging emission contract: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        if not FlextInfraUtilitiesRopeRuntimeRefactors.semantic_capture(
            project,
            module,
            invocation.args[0],
            f"{c.Infra.ROPE_BUILTIN_TYPE_CONSTRAINT_PREFIX}str",
            name="",
        ):
            message = (
                "logging migration requires a proven string message: "
                f"{module.get_name()}:{invocation.lineno}"
            )
            raise ValueError(message)
        for argument in invocation.args[1:]:
            # Native literals have no authored evaluation to discard or run
            # during planning; the canonical JSON port proves the payload.
            cls._prove_logging_value(project, module, argument)

    @classmethod
    def _admit_factory_uses(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        call: ast.Call | None,
        context: tuple[
            Mapping[int, t.Infra.RopeAstNode],
            Mapping[tuple[type[ast.AST], int], ast.AST],
            Sequence[str],
            str | None,
        ],
    ) -> bool:
        if call is None:
            return False
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        parents, _nodes, methods, result_contract = context
        assignment = parents.get(id(call))
        if not isinstance(assignment, c.Infra.AST_ASSIGNMENT_TYPES):
            if not cls._discarded_logging_emission(
                call, parents, methods, result_contract
            ):
                return False
            cls._prove_logging_arguments(project, module, call, parents, methods)
            return True
        target = cls._factory_assignment_target(module, call, assignment)
        if target is None:
            return False
        offset = runtime.source_offset(module.source_code, target)
        scope = runtime.scope_at(module, offset)
        if scope.get_kind() == c.Infra.RopeScopeKind.CLASS:
            return False
        binding = runtime.resolve_symbol(scope, target)
        return binding is not None and cls._admit_factory_occurrences(
            project, module, (target, binding, offset), context
        )

    @staticmethod
    def _factory_assignment_target(
        module: p.Infra.RopePyModule,
        call: ast.Call,
        assignment: ast.Assign | ast.AnnAssign,
    ) -> ast.Name | None:
        if assignment.value is not call:
            return None
        if isinstance(assignment, ast.Assign):
            if len(assignment.targets) != 1:
                return None
            target = assignment.targets[0]
        else:
            target = assignment.target
        if not isinstance(target, ast.Name):
            return None
        if (
            target.id
            in FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(module)
        ):
            return None
        return target

    @classmethod
    def _admit_factory_occurrences(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        target_binding: tuple[ast.Name, p.Infra.RopePyName, int],
        context: tuple[
            Mapping[int, t.Infra.RopeAstNode],
            Mapping[tuple[type[ast.AST], int], ast.AST],
            Sequence[str],
            str | None,
        ],
    ) -> bool:
        parents, nodes, methods, result_contract = context
        target, binding, offset = target_binding
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.create_occurrence_finder(
            project, target.id, binding, imports=False, in_hierarchy=False
        )
        definitions = 0
        uses: MutableSequence[p.Infra.RopeAstNode] = []
        for occurrence in finder.find_occurrences(pymodule=module):
            position, _stop = occurrence.get_word_range()
            if occurrence.is_defined() or occurrence.is_written():
                if position != offset:
                    return False
                definitions += 1
                continue
            receiver = nodes.get((ast.Name, position))
            if receiver is None or not cls._discarded_logging_emission(
                receiver, parents, methods, result_contract
            ):
                return False
            uses.append(receiver)
        if definitions != 1 or not uses:
            return False
        for receiver in uses:
            cls._prove_logging_arguments(project, module, receiver, parents, methods)
        return True


__all__: list[str] = ["FlextInfraUtilitiesSemanticContracts"]
