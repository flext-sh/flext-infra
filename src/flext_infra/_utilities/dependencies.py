"""Dependency parsing and inspection helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shlex
from collections.abc import Mapping, MutableMapping, Sequence
from json import dumps
from pathlib import Path
from types import MappingProxyType
from urllib.parse import quote

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependency,
    FlextInfraUtilitiesDependencyRequirements,
)


class FlextInfraUtilitiesDependencies(
    FlextInfraUtilitiesDependency,
    FlextInfraUtilitiesDependencyRequirements,
):
    """Workspace dependency policy composed over independent requirement parsing."""

    @staticmethod
    def runtime_dependency_plan(
        scan: m.Infra.DeptryScan,
        inputs: m.Infra.RuntimeDependencyInputs,
    ) -> p.Result[m.Infra.RuntimeDependencyPlan]:
        """Calculate native-evidenced changes from explicit supplier provenance.

        Preserve target-owned requirement strings, including their sources, extras
        and markers. Installation never establishes that an import is applicable.

        Returns:
            The target requirement changes and unresolved native import identities.

        """
        result_type = r[m.Infra.RuntimeDependencyPlan]
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
            m.Infra.RuntimeDependencyPlan(
                source=scan.source,
                before=scan.settings,
                dependencies=tuple(selected),
                unresolved_modules=tuple(dict.fromkeys(unresolved)),
                inputs=(
                    inputs.lock,
                    *inputs.inputs,
                    *(
                        state
                        for provider in inputs.providers
                        for state in provider.inputs
                    ),
                    scan.settings,
                    scan.report_state,
                ),
            )
        )

    @staticmethod
    def _locked_environment_and_document(
        scan: m.Infra.DeptryScan,
        inputs: m.Infra.RuntimeDependencyInputs,
    ) -> p.Result[tuple[m.Infra.LockedEnvironment, t.JsonMapping]]:
        """Authenticate provenance and decode the lock and declaration payloads.

        Returns:
            The validated locked environment and native pyproject mapping.

        """
        result_type = r[tuple[m.Infra.LockedEnvironment, t.JsonMapping]]
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
        scan: m.Infra.DeptryScan,
        document: t.JsonMapping,
    ) -> p.Result[m.Infra.DepsToml.MemberRequirements]:
        """Read the project table into its typed requirement declarations.

        Returns:
            The validated member requirements, or the declaration failure.

        """
        result_type = r[m.Infra.DepsToml.MemberRequirements]
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
        inputs: m.Infra.RuntimeDependencyInputs,
        locked: m.Infra.LockedEnvironment,
    ) -> p.Result[tuple[tuple[m.Infra.RuntimeDependencyProvider, Requirement], ...]]:
        """Parse provider requirements and authenticate them against the lock.

        Returns:
            Parsed provider requirement pairs, or the first provenance failure.

        """
        result_type = r[
            tuple[tuple[m.Infra.RuntimeDependencyProvider, Requirement], ...]
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
        scan: m.Infra.DeptryScan,
        declarations: m.Infra.DepsToml.MemberRequirements,
        suppliers: tuple[tuple[m.Infra.RuntimeDependencyProvider, Requirement], ...],
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
            if diagnostic.error.code not in {"DEP001", "DEP003", "DEP004"}:
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
        plan: m.Infra.RuntimeDependencyPlan,
    ) -> p.Result[bool]:
        """Publish only the calculated runtime list against unchanged source states.

        The caller owns the repository mutation lease. Locks remain owned by upg.
        Unresolved import suppliers reject the plan before any publication work.

        Returns:
            Whether the original target declaration changed.

        """
        if plan.unresolved_modules:
            return r[bool].fail(
                "runtime import requires one authored, installed, locked supplier: "
                + ", ".join(plan.unresolved_modules),
            )
        u.Cli.atomic_verify_binary_file_states(plan.inputs).unwrap()
        unchanged = cls._verified_deptry_sources(
            plan.source,
            moment="before publication",
        )
        if unchanged.failure:
            return r[bool].from_failure(unchanged)
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
        scaffold: m.Infra.ScaffoldProjectSpec,
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
                if kind is c.Infra.ProjectKind.INTERNAL_FLEXT
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
        planned_manifests: Sequence[m.Infra.CodegenFilePlan] = (),
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
        planned_manifests: Sequence[m.Infra.CodegenFilePlan] = (),
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
        workspace: m.Infra.WorkspaceSpec,
        distribution: str,
        *,
        planned_manifests: Sequence[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[m.Infra.BootstrapRequirementsRenderSpec]:
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
        by_name = {
            canonicalize_name(repository.distribution): repository
            for repository in repositories
        }
        return u.Cli.dag_closure(graph, frozenset((distribution,))).flat_map(
            lambda closed: u.Cli.dag_order({name: graph[name] for name in closed}).map(
                lambda names: m.Infra.BootstrapRequirementsRenderSpec(
                    requirements=tuple(
                        shlex.quote(
                            f"{name} @ file:"
                            + quote(f"./{by_name[name].path.as_posix()}", safe="/")
                        )
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
        planned_manifests: Sequence[m.Infra.CodegenFilePlan] = (),
        inputs: Sequence[m.Cli.AtomicFileState] = (),
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

    @staticmethod
    def _workspace_manifest_payload(
        project: Path,
        manifests: Mapping[Path, m.Infra.CodegenFilePlan],
        *,
        observations: Mapping[Path, m.Cli.AtomicFileState] | None = None,
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
            if observations is not None:
                observed = observations.get(path)
                if observed is None or observed.content is None:
                    msg = f"workspace manifest has no captured input: {path}"
                    raise ValueError(msg)
                payload = u.Cli.toml_mapping_from_text(
                    observed.content.decode(c.DEFAULT_ENCODING)
                )
                if payload is None:
                    msg = f"invalid captured manifest: {path}"
                    raise ValueError(msg)
                return payload
            physical = u.Cli.toml_read_json(path)
            if physical.failure:
                raise ValueError(physical.error) from physical.exception
            return physical.value
        if plan.project.resolve() != project or plan.desired_content is None:
            msg = f"planned manifest has no owning payload: {path}"
            raise ValueError(msg)
        payload = u.Cli.toml_mapping_from_text(
            plan.desired_content.decode(c.DEFAULT_ENCODING),
        )
        if payload is None:
            msg = f"invalid planned manifest: {path}"
            raise ValueError(msg)
        return payload

    @staticmethod
    def constraint_specifier(version: str) -> str:
        """Return the resolved installed version as an open-ended dependency floor.

        PEP 440 permits a local version label only with ``==`` or ``!=``, so a
        floor built straight from a locally tagged resolution is rejected by
        every build backend. The public release is what a floor means, and the
        local build satisfies it.

        A prerelease resolution is not a floor either: publishing ``>=X.Yb1``
        forces every downstream consumer onto that beta, which is how the fleet
        ended up pinned to ``pydantic>=2.14.0b1`` from a single runtime resolution. The
        empty string means "this resolution cannot serve as a public floor", and
        every caller keeps the declared constraint instead of rewriting it.

        Returns:
            The resolved installed version as an open-ended dependency floor.

        """
        public_version = version.strip().partition("+")[0]
        if not public_version:
            return ""
        try:
            parsed_version = Version(public_version)
        except InvalidVersion:
            return ""
        if parsed_version.is_prerelease:
            return ""
        return f">={public_version}"

    @classmethod
    def resolved_dependency_versions(cls) -> Mapping[str, str]:
        """Read registry versions from the provisioned runtime, not release provenance.

        Returns:
            The resulting ``Mapping[str, str]``.

        Raises:
            TypeError: If Installed distribution has no Name metadata.
            ValueError: If No registry packages found in the provisioned runtime; or if
                Invalid installed distribution name; or if Ambiguous installed version.

        """
        versions: MutableMapping[str, str] = {}
        for distribution in u.installed_distributions():
            if distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE) is not None:
                continue
            name = distribution.metadata.get("Name")
            if name is None:
                msg = "Installed distribution has no Name metadata"
                raise TypeError(msg)
            normalized = cls.dep_name(name)
            if normalized is None:
                msg = f"Invalid installed distribution name: {name}"
                raise ValueError(msg)
            version = distribution.version
            if normalized in versions and versions[normalized] != version:
                msg = f"Ambiguous installed version: {normalized}"
                raise ValueError(msg)
            versions[normalized] = version
        if not versions:
            msg = "No registry packages found in the provisioned runtime"
            raise ValueError(msg)
        return versions

    @classmethod
    def rewrite_requirement_constraint(
        cls,
        requirement: str,
        *,
        resolved_versions: Mapping[str, str],
        internal_names: Sequence[str] = (),
    ) -> str | None:
        """Rewrite one PEP 621 requirement to the resolved runtime floor.

        Returns:
            The resulting ``str | None``.

        """
        guard = cls._rewritable_requirement(requirement, internal_names)
        if guard is None:
            return None
        dependency_name, parsed = guard
        raw_text = requirement.strip()
        head = parsed.name
        if parsed.extras:
            head = f"{head}[{','.join(sorted(parsed.extras))}]"
        locked_version = resolved_versions.get(dependency_name)
        if locked_version is None:
            return None
        if not parsed.specifier.contains(
            locked_version,
            prereleases=True,
        ):
            return None
        retained = tuple(
            sorted(
                str(specifier)
                for specifier in parsed.specifier
                if specifier.operator != ">="
            )
        )
        constraint = cls.constraint_specifier(locked_version)
        if not constraint:
            return None
        if retained:
            constraint = ",".join((constraint, *retained))
        rewritten = f"{head}{constraint}"
        if parsed.marker is not None:
            rewritten = f"{rewritten}; {parsed.marker}"
        return rewritten if rewritten != raw_text else None

    @classmethod
    def _rewritable_requirement(
        cls,
        requirement: str,
        internal_names: Sequence[str],
    ) -> tuple[str, Requirement] | None:
        """Parse the complete declaration before deciding whether it is rewritable.

        Returns:
            The dependency name and parsed requirement, or None for a direct
            reference or an internal dependency. Invalid declarations raise
            the original PEP 508 parsing error.

        """
        parsed = Requirement(requirement.strip())
        dependency_name = canonicalize_name(parsed.name)
        if parsed.url is not None or dependency_name in {
            canonicalize_name(name) for name in internal_names
        }:
            return None
        return dependency_name, parsed

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
