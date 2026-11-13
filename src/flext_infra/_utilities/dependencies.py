"""Dependency parsing and inspection helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from json import dumps
from pathlib import Path
from types import MappingProxyType
from urllib.parse import quote

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependency,
    FlextInfraUtilitiesDependencyRequirements,
    FlextInfraUtilitiesManagedConflicts,
)
from flext_infra._utilities._git import FlextInfraUtilitiesGitMutationScope


class FlextInfraUtilitiesDependencies(
    FlextInfraUtilitiesDependency,
    FlextInfraUtilitiesDependencyRequirements,
):
    """Workspace dependency policy composed over independent requirement parsing."""

    @staticmethod
    def runtime_dependency_plan(
        scan: p.Infra.DeptryScan,
        inputs: p.Infra.RuntimeDependencyInputs,
    ) -> p.Result[p.Infra.RuntimeDependencyPlan]:
        """Calculate native-evidenced changes from explicit supplier provenance.

        Preserve target-owned requirement strings, including their sources, extras
        and markers. Installation never establishes that an import is applicable.

        Returns:
            The target requirement changes and unresolved native import identities.

        """
        result_type = r[p.Infra.RuntimeDependencyPlan]
        payload = FlextInfraUtilitiesDependencies._locked_environment_and_document(
            scan,
            inputs,
        )
        if payload.failure:
            return result_type.from_failure(payload)
        locked, document = payload.value
        declarations = FlextInfraUtilitiesDependencies._declared_runtime_requirements(
            scan,
            document,
        )
        if declarations.failure:
            return result_type.from_failure(declarations)
        suppliers = FlextInfraUtilitiesDependencies._validated_import_suppliers(
            inputs,
            locked,
        )
        if suppliers.failure:
            return result_type.from_failure(suppliers)
        selected, unresolved = FlextInfraUtilitiesDependencies._runtime_selections(
            scan,
            declarations.value,
            suppliers.value,
            development_only=inputs.development_only,
            used_without_import=(*inputs.invoked_executables, *inputs.loaded_plugins),
        )
        return result_type.ok(
            m.Infra.RuntimeDependencyPlan.model_validate({
                "source": (scan.source),
                "before": (scan.settings),
                "dependencies": (tuple(selected)),
                "unresolved_modules": (tuple(dict.fromkeys(unresolved))),
                "inputs": ((
                    inputs.lock,
                    *inputs.inputs,
                    *(
                        state
                        for provider in inputs.providers
                        for state in provider.inputs
                    ),
                    scan.settings,
                    scan.report_state,
                )),
            })
        )

    @staticmethod
    def _locked_environment_and_document(
        scan: p.Infra.DeptryScan,
        inputs: p.Infra.RuntimeDependencyInputs,
    ) -> p.Result[tuple[p.Infra.LockedEnvironment, t.JsonMapping]]:
        """Authenticate provenance and decode the lock and declaration payloads.

        Returns:
            The validated locked environment and native pyproject mapping.

        """
        result_type = r[tuple[p.Infra.LockedEnvironment, t.JsonMapping]]
        target = inputs.target_root
        if (
            not target.is_absolute()
            or scan.settings.path != target / c.PYPROJECT_FILENAME
        ):
            return result_type.fail("dependency provenance belongs to another target")
        if (
            not inputs.python.is_absolute()
            or inputs.python.parent != scan.venv_bin
            or scan.settings.content is None
        ):
            return result_type.fail(
                "dependency provenance lacks its interpreter or settings"
            )
        if (
            inputs.lock.path.name != c.Infra.UV_LOCK_FILENAME
            or inputs.lock.content is None
        ):
            return result_type.fail("dependency provenance lacks its native UV lock")
        lock_payload = u.Cli.toml_mapping_from_text(
            inputs.lock.content.decode(c.DEFAULT_ENCODING),
        )
        if lock_payload is None:
            return result_type.fail(f"invalid dependency lock: {inputs.lock.path}")
        locked = m.Infra.LockedEnvironment.model_validate_json(dumps(lock_payload))
        document = u.Cli.toml_mapping_from_text(
            scan.settings.content.decode(c.DEFAULT_ENCODING),
        )
        if document is None:
            return result_type.fail(
                f"invalid dependency declaration: {scan.settings.path}"
            )
        return result_type.ok((locked, document))

    @staticmethod
    def _declared_runtime_requirements(
        scan: p.Infra.DeptryScan,
        document: t.JsonMapping,
    ) -> p.Result[p.Infra.MemberRequirements]:
        """Read the project table into its typed requirement declarations.

        Returns:
            The validated member requirements, or the declaration failure.

        """
        result_type = r[p.Infra.MemberRequirements]
        project = u.Cli.toml_mapping_child(document, c.Infra.PROJECT)
        if project is None:
            return result_type.fail(
                f"project declaration is absent: {scan.settings.path}"
            )
        declarations = m.Infra.DepsToml.MemberRequirements.model_validate({
            "name": project[c.Infra.NAME],
            "dependencies": project.get(c.Infra.DEPENDENCIES, []),
            "optional_dependencies": project.get(c.Infra.OPTIONAL_DEPENDENCIES, {}),
            "dependency-groups": document.get(c.Infra.DEPENDENCY_GROUPS, {}),
        })
        return result_type.ok(declarations)

    @staticmethod
    def _validated_import_suppliers(
        inputs: p.Infra.RuntimeDependencyInputs,
        locked: p.Infra.LockedEnvironment,
    ) -> p.Result[tuple[tuple[p.Infra.RuntimeDependencyProvider, Requirement], ...]]:
        """Parse provider requirements and authenticate them against the lock.

        Returns:
            Parsed provider requirement pairs, or the first provenance failure.

        """
        result_type = r[
            tuple[tuple[p.Infra.RuntimeDependencyProvider, Requirement], ...]
        ]
        suppliers = tuple(
            (provider, Requirement(provider.requirement))
            for provider in inputs.providers
        )
        for provider, requirement in suppliers:
            if provider.package not in locked.package:
                return result_type.fail(
                    "import supplier differs from the selected lock: "
                    f"{provider.package.name}",
                )
            if canonicalize_name(requirement.name) != canonicalize_name(
                provider.package.name
            ):
                return result_type.fail(
                    "import supplier requirement differs from its locked identity: "
                    f"{provider.package.name}",
                )
        return result_type.ok(suppliers)

    @staticmethod
    def _runtime_selections(
        scan: p.Infra.DeptryScan,
        declarations: p.Infra.MemberRequirements,
        suppliers: tuple[tuple[p.Infra.RuntimeDependencyProvider, Requirement], ...],
        *,
        development_only: t.StrTuple,
        used_without_import: t.StrTuple,
    ) -> tuple[list[str], list[str]]:
        """Select retained runtime requirements and collect unresolved modules.

        A requirement deptry reports unused stays when the project uses it
        without an import: it invokes one of its console scripts, or pytest
        autoloads it through its plugin entry point.

        Returns:
            The retained requirement strings and the unresolved import modules.

        """
        runtime = declarations.dependencies
        development = tuple(
            item
            for group in declarations.dependency_groups.values()
            for item in group
            if isinstance(item, str)
        ) + tuple(
            item
            for group in declarations.optional_dependencies.values()
            for item in group
        )
        parsed_runtime = tuple(Requirement(item) for item in runtime)
        parsed_development = tuple(Requirement(item) for item in development)
        forbidden = {
            canonicalize_name(Requirement(item).name) for item in development_only
        }
        unused = {
            canonicalize_name(item.module)
            for item in scan.report.root
            if item.error.code == c.Infra.DEPTRY_UNUSED_DEPENDENCY_CODE
        } - set(used_without_import)
        selected = [
            raw
            for raw, requirement in zip(runtime, parsed_runtime, strict=True)
            if canonicalize_name(requirement.name) not in unused
        ]
        unresolved: list[str] = []
        for diagnostic in scan.report.root:
            if diagnostic.error.code not in c.Infra.DEPTRY_UNDECLARED_IMPORT_CODES:
                continue
            providers = tuple(
                (provider, requirement)
                for provider, requirement in suppliers
                if diagnostic.module in provider.modules
            )
            if len(providers) != 1:
                unresolved.append(diagnostic.module)
                continue
            provider = providers[0][0]
            name = canonicalize_name(provider.package.name)
            if name == canonicalize_name(declarations.name) or name in forbidden:
                unresolved.append(diagnostic.module)
                continue
            authored = tuple(
                raw
                for raw, parsed in zip(development, parsed_development, strict=True)
                if canonicalize_name(parsed.name) == name
            )
            additions = authored or (provider.requirement,)
            selected.extend(item for item in additions if item not in selected)
        return selected, unresolved

    @classmethod
    def publish_runtime_dependency_plan(
        cls,
        plan: p.Infra.RuntimeDependencyPlan,
    ) -> p.Result[bool]:
        """Publish only the calculated runtime list against unchanged source states.

        This owner holds its own publication lease, so a caller never wraps the
        scan, the plan and the write in one long lock. Unresolved import
        suppliers reject the plan before any publication work.

        Returns:
            Whether the original target declaration changed.

        """
        if plan.unresolved_modules:
            return r[bool].fail(
                "runtime import requires one authored, installed, locked supplier: "
                + ", ".join(plan.unresolved_modules),
            )
        lease = FlextInfraUtilitiesGitMutationScope.mutation_lock_path(
            plan.before.path.parent
        )
        if lease.failure:
            return r[bool].from_failure(lease)
        with u.Cli.file_changes_lock(lease.value):
            u.Cli.atomic_verify_binary_file_states(plan.inputs).unwrap()
            unchanged = cls._verified_deptry_sources(
                plan.source,
                moment="before publication",
            )
            if unchanged.failure:
                return r[bool].from_failure(unchanged)
            return cls._sync_runtime_dependency_declaration(plan)

    @staticmethod
    def _sync_runtime_dependency_declaration(
        plan: p.Infra.RuntimeDependencyPlan,
    ) -> p.Result[bool]:
        """Write the calculated runtime list into the verified declaration.

        The caller holds the publication lease and has verified every source
        state the plan was calculated from.

        Returns:
            Whether the original target declaration changed.

        """
        if plan.before.content is None:
            return r[bool].fail(f"dependency declaration is absent: {plan.before.path}")
        document = u.Cli.toml_parse_text(plan.before.content.decode(c.DEFAULT_ENCODING))
        if document is None:
            return r[bool].fail(f"invalid dependency declaration: {plan.before.path}")
        project = u.Cli.toml_table_child(document, c.Infra.PROJECT)
        if project is None:
            return r[bool].fail(f"project declaration is absent: {plan.before.path}")
        changed = u.Cli.toml_sync_string_list(
            project, c.Infra.DEPENDENCIES, plan.dependencies
        )
        if changed:
            u.Cli.atomic_write_binary_file_guarded(
                plan.before,
                document.as_string().encode(c.DEFAULT_ENCODING),
                permission_mode=plan.before.mode,
            ).unwrap()
        return r[bool].ok(changed)

    @staticmethod
    def project_dev_groups_from_payload(
        payload: t.JsonMapping,
    ) -> Mapping[str, Sequence[str]]:
        """Collect optional dependency groups from one normalized payload.

        Returns:
            The resulting ``Mapping[str, Sequence[str]]``.

        """
        project = u.Cli.json_as_mapping(payload.get(c.Infra.PROJECT, None))
        optional = u.Cli.json_as_mapping(
            project.get(c.Infra.OPTIONAL_DEPENDENCIES, None),
        )
        groups = {
            str(group): tuple(
                str(item) for item in u.Cli.json_as_sequence(optional.get(group, None))
            )
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
        }
        return {group: values for group, values in groups.items() if values}

    @classmethod
    def project_dev_groups(
        cls,
        document: t.Cli.TomlDocument,
    ) -> Mapping[str, Sequence[str]]:
        """Collect optional dependency groups from one TOML document.

        Returns:
            The resulting ``Mapping[str, Sequence[str]]``.

        """
        normalized = u.Cli.toml_as_mapping(document) or {}
        if not normalized:
            # Keep the empty mapping immutable and fully typed.
            return MappingProxyType(dict[str, tuple[str, ...]]())
        return cls.project_dev_groups_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies(
        cls,
        document: t.Cli.TomlDocument,
    ) -> Sequence[str]:
        """Merge all canonical dev dependency groups from one TOML document.

        Returns:
            The resulting ``Sequence[str]``.

        """
        normalized = u.Cli.toml_as_mapping(document) or {}
        if not normalized:
            return ()
        return cls.canonical_dev_dependencies_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies_from_payload(
        cls,
        payload: t.JsonMapping,
    ) -> Sequence[str]:
        """Merge all canonical dev dependency groups from one normalized payload.

        Returns:
            The resulting ``Sequence[str]``.

        """
        groups = cls.project_dev_groups_from_payload(payload)
        return cls.dedupe_specs([
            requirement
            for group in c.Infra.CANONICAL_DEV_DEPENDENCY_GROUPS
            for requirement in groups.get(str(group), ())
        ])

    @staticmethod
    def project_development_requirements(
        scaffold: p.Infra.ScaffoldProjectSpec,
        *,
        distribution: str,
        kind: c.Infra.ProjectKind,
        declared: Sequence[str] = (),
    ) -> Sequence[str]:
        """Compose development policy over the target's own requirement declarations.

        Existing requirement spellings, marker variants and sources stay intact.
        FLEXT suppliers apply only to the declared FLEXT kind and never to their
        own distribution; installed packages and project names do not elect policy.

        Returns:
            Authored requirements followed by missing applicable suppliers.

        """
        own = canonicalize_name(distribution)
        authored = tuple(declared)
        retained = {Requirement(item) for item in authored}
        policy = (
            *scaffold.dev,
            *(
                scaffold.required_flext_dev
                if kind in c.Infra.TOOLCHAIN_GOVERNED_KINDS
                else ()
            ),
        )
        additions: list[str] = []
        for requirement in policy:
            parsed = Requirement(requirement)
            if canonicalize_name(parsed.name) == own or parsed in retained:
                continue
            retained.add(parsed)
            additions.append(requirement)
        return (*authored, *additions)

    @classmethod
    def project_dependency_names_from_payload(
        cls,
        payload: t.JsonMapping,
    ) -> Sequence[str]:
        """Return strict names from the PEP 621 runtime dependency array.

        Returns:
            Strict names from the PEP 621 runtime dependency array.

        Raises:
            TypeError: If pyproject payload must define a [project] mapping; or if
                [project].dependencies must be an array of requirement strings; or if
                [project].dependencies entries must be strings.
            ValueError: If [project].dependencies entries must not be blank.

        """
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            msg = "pyproject payload must define a [project] mapping"
            raise TypeError(msg)
        raw_dependencies = project.get(c.Infra.DEPENDENCIES, [])
        if not isinstance(raw_dependencies, list):
            msg = "[project].dependencies must be an array of requirement strings"
            raise TypeError(msg)
        names: list[str] = []
        for raw_requirement in raw_dependencies:
            if not isinstance(raw_requirement, str):
                msg = "[project].dependencies entries must be strings"
                raise TypeError(msg)
            dependency_name = cls.dep_name(raw_requirement)
            if dependency_name is None:
                msg = "[project].dependencies entries must not be blank"
                raise ValueError(msg)
            names.append(dependency_name)
        return tuple(names)

    @classmethod
    def workspace_dependency_order(
        cls,
        root: Path,
        repositories: Sequence[p.Infra.RepositoryRef],
        *,
        planned_manifests: Sequence[p.Infra.CodegenFilePlan] = (),
    ) -> Sequence[str]:
        """Order declared packages by their actual runtime dependency graph.

        Returns:
            Dependencies before consumers, with stable distribution-name ties.

        """
        return tuple(
            name
            for wave in cls.workspace_dependency_waves(
                root, repositories, planned_manifests=planned_manifests
            )
            for name in wave
        )

    @classmethod
    def workspace_dependency_waves(
        cls,
        root: Path,
        repositories: Sequence[p.Infra.RepositoryRef],
        *,
        planned_manifests: Sequence[p.Infra.CodegenFilePlan] = (),
    ) -> Sequence[Sequence[str]]:
        """Group declared packages into runtime-dependency-first waves.

        Returns:
            Distributions per wave; a wave depends only on earlier waves.

        Raises:
            ValueError: If distributions collide or the runtime graph is cyclic.

        """
        by_name: Mapping[str, p.Infra.RepositoryRef] = {
            canonicalize_name(repository.distribution): repository
            for repository in repositories
        }
        if len(by_name) != len(repositories):
            msg = "workspace declares duplicate distribution identities"
            raise ValueError(msg)
        graph = cls.workspace_dependency_graph(
            root, repositories, planned_manifests=planned_manifests
        )
        waves = u.Cli.dag_waves(graph)
        if waves.failure:
            raise ValueError(waves.error)
        return tuple(
            tuple(by_name[name].distribution for name in wave) for wave in waves.value
        )

    @classmethod
    def workspace_bootstrap_requirements(
        cls,
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
        distribution: str,
        *,
        planned_manifests: Sequence[p.Infra.CodegenFilePlan] = (),
    ) -> p.Result[p.Infra.BootstrapRequirementsRenderSpec]:
        """Project the candidate closure while retaining original observations.

        Returns:
            The bootstrap requirements render specification.

        """
        if not workspace.inputs:
            return r.fail("bootstrap requires authenticated workspace inputs")
        repositories = (workspace.repository, *workspace.subprojects)
        graph = cls.workspace_dependency_graph(
            root,
            repositories,
            planned_manifests=planned_manifests,
            inputs=workspace.inputs,
        )
        by_name: Mapping[str, p.Infra.RepositoryRef] = {
            canonicalize_name(repository.distribution): repository
            for repository in repositories
        }
        return u.Cli.dag_closure(graph, frozenset((distribution,))).flat_map(
            lambda closed: u.Cli.dag_order({name: graph[name] for name in closed}).map(
                lambda names: m.Infra.BootstrapRequirementsRenderSpec(
                    # requirements files are not shell: shlex quoting breaks
                    # uv pip; PEP 508 direct reference + URL-encoded path is
                    # the portable form for pip and uv alike.
                    requirements=tuple(
                        f"{name} @ file:"
                        + quote(f"./{by_name[name].path.as_posix()}", safe="/")
                        for name in names
                    ),
                    inputs=(
                        *workspace.inputs,
                        *(
                            state
                            for plan in planned_manifests
                            for state in (plan.before, *plan.inputs)
                        ),
                    ),
                )
            )
        )

    @classmethod
    def workspace_dependency_graph(
        cls,
        root: Path,
        repositories: Sequence[p.Infra.RepositoryRef],
        *,
        planned_manifests: Sequence[p.Infra.CodegenFilePlan] = (),
        inputs: Sequence[p.Cli.AtomicFileState] = (),
    ) -> Mapping[str, tuple[str, ...]]:
        """Read the declared local graph through the existing manifest owner.

        Args:
            root: Repository root that anchors every repository reference.
            repositories: Declared repository references to inventory.
            planned_manifests: Staged manifest plans that shadow the disk.
            inputs: Authenticated atomic source states already captured.

        Returns:
            Canonical distribution identities and their local dependencies.

        Raises:
            ValueError: If distribution or planned manifest identities collide.

        """
        by_name = {
            canonicalize_name(repository.distribution): repository
            for repository in repositories
        }
        if len(by_name) != len(repositories):
            msg = "workspace declares duplicate distribution identities"
            raise ValueError(msg)
        manifests = {plan.path.resolve(): plan for plan in planned_manifests}
        if len(manifests) != len(planned_manifests):
            msg = "workspace declares duplicate planned manifest paths"
            raise ValueError(msg)
        observations = {state.path: state for state in inputs}
        return {
            name: tuple(
                dependency
                for dependency in cls.project_dependency_names_from_payload(
                    cls._workspace_manifest_payload(
                        (root / repository.path).resolve(),
                        manifests,
                        observations=observations if inputs else None,
                    ),
                )
                if dependency in by_name
            )
            for name, repository in by_name.items()
        }

    @classmethod
    def _workspace_manifest_payload(
        cls,
        project: Path,
        manifests: Mapping[Path, p.Infra.CodegenFilePlan],
        *,
        observations: Mapping[Path, p.Cli.AtomicFileState] | None = None,
    ) -> t.JsonMapping:
        """Read one project's dependency manifest, planned payload first.

        Args:
            project: The resolved project root.
            manifests: Planned manifests indexed by resolved path.
            observations: Authenticated source states already captured, keyed
                by resolved path.

        Returns:
            The planned manifest payload, or the physical one when unplanned.

        Raises:
            ValueError: If the manifest cannot be read, or a planned manifest has
                no owning payload or does not parse.

        """
        path = project / c.PYPROJECT_FILENAME
        plan = manifests.get(path)
        if plan is None:
            content = cls._workspace_manifest_unplanned_content(
                path, observations=observations
            )
        else:
            if plan.project.resolve() != project or plan.desired_content is None:
                msg = f"planned manifest has no owning payload: {path}"
                raise ValueError(msg)
            content = plan.desired_content
        recovered = (
            FlextInfraUtilitiesManagedConflicts.pyproject_managed_file().flat_map(
                lambda spec: FlextInfraUtilitiesManagedConflicts.recover_managed_toml(
                    content.decode(c.DEFAULT_ENCODING),
                    conflict_sections=spec.conflict_sections,
                )
            )
        )
        if recovered.failure:
            if recovered.exception is not None:
                raise recovered.exception
            raise ValueError(recovered.error)
        payload = u.Cli.toml_mapping_from_text(recovered.value)
        if payload is None:
            msg = f"invalid workspace manifest: {path}"
            raise ValueError(msg)
        return payload

    @staticmethod
    def _workspace_manifest_unplanned_content(
        path: Path,
        *,
        observations: Mapping[Path, p.Cli.AtomicFileState] | None,
    ) -> bytes:
        """Read an unplanned manifest from its captured input or from disk.

        Args:
            path: The resolved manifest path.
            observations: Authenticated source states already captured, keyed
                by resolved path.

        Returns:
            The captured bytes when observations exist, else the physical bytes.

        Raises:
            ValueError: If the manifest has no captured input, cannot be read,
                or is absent.

        """
        if observations is not None:
            observed = observations.get(path)
            if observed is None or observed.content is None:
                msg = f"workspace manifest has no captured input: {path}"
                raise ValueError(msg)
            return observed.content
        physical = u.Cli.atomic_read_binary_file_state(path, required=True)
        if physical.failure:
            if physical.exception is not None:
                raise physical.exception
            raise ValueError(physical.error)
        content = physical.value.content
        if content is None:
            msg = f"workspace manifest is absent: {path}"
            raise ValueError(msg)
        return content

    @staticmethod
    def registry_requirement_name(
        requirement: str,
        sourced: frozenset[str],
    ) -> str | None:
        """Return the canonical name of one requirement the index resolves.

        A direct reference or a name bound to a ``[tool.uv.sources]`` entry
        (FLEXT members and forks) resolves outside the index and its cooldown.

        Returns:
            The canonical distribution name, or None outside the index.

        """
        parsed = Requirement(requirement)
        name = canonicalize_name(parsed.name)
        return None if parsed.url is not None or name in sourced else name

    @staticmethod
    def pinned_requirement(requirement: str) -> bool:
        """Whether one requirement pins an exact release (``==`` or ``===``).

        Returns:
            True when any clause of its specifier is an exact match.

        """
        return any(
            clause.operator in {"==", "==="}
            for clause in Requirement(requirement).specifier
        )

    @staticmethod
    def bounded_requirement(
        requirement: str,
        operator: str,
        version: str | None,
    ) -> str:
        """Set one requirement's upg-owned bound to ``operator version``.

        A floor keeps every authored clause except ``>=``; a pin owns the
        whole specifier. ``None`` drops the owned bound, so native resolution
        chooses the release. Extras and the marker are kept.

        Returns:
            The rewritten requirement line.

        """
        parsed = Requirement(requirement)
        extras = f"[{','.join(sorted(parsed.extras))}]" if parsed.extras else ""
        kept = (
            ()
            if operator == c.Infra.UPG_PIN_OPERATOR
            else sorted(
                str(clause)
                for clause in parsed.specifier
                if clause.operator != operator
            )
        )
        owned = () if version is None else (f"{operator}{version}",)
        specifier = ",".join((*owned, *kept))
        marker = f"; {parsed.marker}" if parsed.marker is not None else ""
        return f"{parsed.name}{extras}{specifier}{marker}"

    @staticmethod
    def requirement_arrays(
        payload: t.JsonMapping,
    ) -> Sequence[tuple[tuple[str, ...], str]]:
        """Return every requirement array of one pyproject by table path.

        Returns:
            ``(table path, key)`` pairs in declaration order: project
            dependencies, each extra, each dependency group and the
            ``[tool.uv]`` constraint dependencies.

        """
        optional = (c.Infra.PROJECT, c.Infra.OPTIONAL_DEPENDENCIES)
        groups = (c.Infra.DEPENDENCY_GROUPS,)
        return (
            ((c.Infra.PROJECT,), c.Infra.DEPENDENCIES),
            *(
                (path, key)
                for path in (optional, groups)
                for key in u.Cli.toml_mapping_path(payload, path) or {}
            ),
            ((c.Infra.TOOL, c.Infra.UV), c.Infra.UV_CONSTRAINT_DEPENDENCIES_KEY),
        )

    @classmethod
    def declared_dependency_names(
        cls,
        document: t.Cli.TomlDocument,
    ) -> Sequence[str]:
        """Return normalized dependency names from one TOML document.

        Returns:
            Normalized dependency names from one TOML document.

        """
        normalized = u.Cli.toml_as_mapping(document) or {}
        if not normalized:
            return ()
        return cls.declared_dependency_names_from_payload(normalized)

    @classmethod
    def declared_dependency_names_from_payload(
        cls,
        payload: t.JsonMapping,
    ) -> Sequence[str]:
        """Return normalized dependency names across supported dependency tables.

        Returns:
            Normalized dependency names across supported dependency tables.

        """
        names: set[str] = set()
        cls._append_project_dependency_names(payload=payload, names=names)
        cls._append_dependency_group_names(payload=payload, names=names)
        cls._append_poetry_dependency_names(payload=payload, names=names)
        return tuple(sorted(names))

    @classmethod
    def _append_project_dependency_names(
        cls,
        *,
        payload: t.JsonMapping,
        names: set[str],
    ) -> None:
        """Append project dependency names."""
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            return
        cls._append_requirement_names(
            raw_requirements=project.get(c.Infra.DEPENDENCIES),
            names=names,
        )
        optional_dependencies = project.get(c.Infra.OPTIONAL_DEPENDENCIES)
        if not isinstance(optional_dependencies, Mapping):
            return
        for raw_requirements in optional_dependencies.values():
            cls._append_requirement_names(
                raw_requirements=raw_requirements,
                names=names,
            )

    @classmethod
    def _append_dependency_group_names(
        cls,
        *,
        payload: t.JsonMapping,
        names: set[str],
    ) -> None:
        """Append dependency group names."""
        dependency_groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if not isinstance(dependency_groups, Mapping):
            return
        for raw_requirements in dependency_groups.values():
            cls._append_requirement_names(
                raw_requirements=raw_requirements,
                names=names,
            )

    @classmethod
    def _append_poetry_dependency_names(
        cls,
        *,
        payload: t.JsonMapping,
        names: set[str],
    ) -> None:
        """Append poetry dependency names."""
        tool = payload.get(c.Infra.TOOL)
        if not isinstance(tool, Mapping):
            return
        poetry = tool.get(c.Infra.POETRY)
        if not isinstance(poetry, Mapping):
            return
        cls._append_mapping_dependency_names(
            raw_mapping=poetry.get(c.Infra.DEPENDENCIES),
            names=names,
        )
        poetry_groups = poetry.get(c.Infra.GROUP)
        if not isinstance(poetry_groups, Mapping):
            return
        for raw_group in poetry_groups.values():
            if not isinstance(raw_group, Mapping):
                continue
            cls._append_mapping_dependency_names(
                raw_mapping=raw_group.get(c.Infra.DEPENDENCIES),
                names=names,
            )

    @classmethod
    def _append_requirement_names(
        cls,
        *,
        raw_requirements: t.JsonValue,
        names: set[str],
    ) -> None:
        """Append requirement names."""
        if not isinstance(raw_requirements, list):
            return
        for raw_requirement in raw_requirements:
            dependency_name = cls.dep_name(str(raw_requirement))
            if dependency_name is None:
                continue
            names.add(dependency_name)

    @classmethod
    def _append_mapping_dependency_names(
        cls,
        *,
        raw_mapping: t.JsonValue,
        names: set[str],
    ) -> None:
        """Append mapping dependency names."""
        if not isinstance(raw_mapping, Mapping):
            return
        for raw_name in raw_mapping:
            dependency_name = cls.dep_name(raw_name)
            if dependency_name is None or dependency_name == "python":
                continue
            names.add(dependency_name)

    @classmethod
    def local_dependency_names_from_payload(
        cls,
        payload: t.JsonMapping,
        *,
        workspace_project_names: Sequence[str] = (),
    ) -> Sequence[str]:
        """Return workspace-local dependency names from one payload.

        Returns:
            Workspace-local dependency names from one payload.

        """
        declared = set(cls.declared_dependency_names_from_payload(payload))
        if not workspace_project_names:
            return ()
        workspace_names = set(workspace_project_names)
        return tuple(sorted(name for name in declared if name in workspace_names))


__all__: list[str] = ["FlextInfraUtilitiesDependencies"]
