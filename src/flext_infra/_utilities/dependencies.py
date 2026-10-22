"""Dependency parsing and inspection helpers for flext-infra utilities.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from base64 import urlsafe_b64encode
from collections.abc import Callable, Mapping, MutableMapping
from importlib.metadata import Distribution, PackagePath
from json import dumps
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencyRequirements,
    FlextInfraUtilitiesPyproject,
)
from flext_infra._utilities._dependency_deptry import (
    FlextInfraUtilitiesDependencyDeptryMixin,
)

_EXACT_INSTALL_METADATA_NAMES: frozenset[str] = frozenset({"METADATA", "RECORD"})
_EXACT_INSTALL_METADATA_COUNT: int = 2


class FlextInfraUtilitiesDependencies(
    FlextInfraUtilitiesDependencyDeptryMixin,
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
    ) -> p.Result[t.Pair[m.Infra.LockedEnvironment, t.JsonMapping]]:
        """Authenticate provenance and decode the lock and declaration payloads.

        Returns:
            The validated locked environment and native pyproject mapping.

        """
        result_type = r[t.Pair[m.Infra.LockedEnvironment, t.JsonMapping]]
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
    ) -> p.Result[
        t.VariadicTuple[t.Pair[m.Infra.RuntimeDependencyProvider, Requirement]]
    ]:
        """Parse provider requirements and authenticate them against the lock.

        Returns:
            Parsed provider requirement pairs, or the first provenance failure.

        """
        result_type = r[
            t.VariadicTuple[t.Pair[m.Infra.RuntimeDependencyProvider, Requirement]]
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
        suppliers: t.VariadicTuple[
            t.Pair[m.Infra.RuntimeDependencyProvider, Requirement]
        ],
        *,
        development_only: t.StrTuple,
    ) -> t.Pair[list[str], list[str]]:
        """Select retained runtime requirements and collect unresolved modules.

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
        }
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
    ) -> t.MappingKV[str, t.StrSequence]:
        """Collect optional dependency groups from one normalized payload.

        Returns:
            The resulting ``t.MappingKV[str, t.StrSequence]``.

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
    ) -> t.MappingKV[str, t.StrSequence]:
        """Collect optional dependency groups from one TOML document.

        Returns:
            The resulting ``t.MappingKV[str, t.StrSequence]``.

        """
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            # Keep the empty mapping immutable and fully typed.
            return MappingProxyType(dict[str, t.VariadicTuple[str]]())
        return cls.project_dev_groups_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies(
        cls,
        document: t.Cli.TomlDocument,
    ) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one TOML document.

        Returns:
            The resulting ``t.StrSequence``.

        """
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.canonical_dev_dependencies_from_payload(normalized)

    @classmethod
    def canonical_dev_dependencies_from_payload(
        cls,
        payload: t.JsonMapping,
    ) -> t.StrSequence:
        """Merge all canonical dev dependency groups from one normalized payload.

        Returns:
            The resulting ``t.StrSequence``.

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
        declared: t.StrSequence = (),
    ) -> t.StrSequence:
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
    ) -> t.StrSequence:
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

    @staticmethod
    def dependency_order(
        direct_names: t.StrSequence,
        *,
        dependencies: Callable[[str], t.StrSequence],
        prefix: str = "",
        normalize: Callable[[str], str] = canonicalize_name,
    ) -> t.StrSequence:
        """Return a dependency-first order for any named dependency graph.

        Returns:
            A dependency-first order for any named dependency graph.

        """
        graph: MutableMapping[str, t.VariadicTuple[str]] = {}

        def collect(dependency_name: str) -> None:
            normalized = normalize(dependency_name)
            if normalized in graph:
                return
            children = tuple(
                child
                for raw_child in dependencies(normalized)
                if (child := normalize(raw_child))
                and (not prefix or child.startswith(prefix))
            )
            graph[normalized] = children
            for dependency in children:
                collect(dependency)

        roots = tuple(
            normalized
            for name in direct_names
            if (normalized := normalize(name))
            and (not prefix or normalized.startswith(prefix))
        )
        for root in roots:
            collect(root)
        ordered: list[str] = []
        visited: set[str] = set()
        active: list[str] = []

        def visit(distribution_name: str) -> None:
            if distribution_name in visited:
                return
            if distribution_name in active:
                cycle_start = active.index(distribution_name)
                cycle = " -> ".join((*active[cycle_start:], distribution_name))
                msg = f"cyclic dependency graph: {cycle}"
                raise ValueError(msg)
            active.append(distribution_name)
            for dependency in graph[distribution_name]:
                visit(dependency)
            active.pop()
            visited.add(distribution_name)
            ordered.append(distribution_name)

        for root in roots:
            visit(root)
        return tuple(ordered)

    @classmethod
    def workspace_dependency_order(
        cls,
        root: Path,
        repositories: t.SequenceOf[p.Infra.RepositoryRef],
        *,
        planned_manifests: t.SequenceOf[m.Infra.CodegenFilePlan] = (),
    ) -> t.StrSequence:
        """Order declared packages by their actual runtime dependency graph.

        Returns:
            Dependencies before consumers, with stable distribution-name ties.

        Raises:
            ValueError: If distributions collide or the runtime graph is cyclic.

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
        graph: dict[str, tuple[str, ...]] = {}
        for name, repository in by_name.items():
            project = (root / repository.path).resolve()
            path = project / c.PYPROJECT_FILENAME
            plan = manifests.get(path)
            if plan is None:
                physical = u.Cli.toml_read_json(path)
                if physical.failure:
                    raise ValueError(physical.error) from physical.exception
                payload = physical.value
            else:
                if plan.project.resolve() != project or plan.desired_content is None:
                    msg = f"planned manifest has no owning payload: {path}"
                    raise ValueError(msg)
                payload = u.Cli.toml_mapping_from_text(
                    plan.desired_content.decode(c.DEFAULT_ENCODING),
                )
                if payload is None:
                    msg = f"invalid planned manifest: {path}"
                    raise ValueError(msg)
            graph[name] = tuple(
                dependency
                for dependency in cls.project_dependency_names_from_payload(
                    payload,
                )
                if dependency in by_name
            )
        waves = cls.dependency_waves(graph)
        if waves.failure:
            raise ValueError(waves.error)
        return tuple(
            by_name[name].distribution for wave in waves.value for name in wave
        )

    @staticmethod
    def dependency_waves[NameT: str](
        edges: Mapping[NameT, t.StrSequence],
    ) -> p.Result[t.SequenceOf[t.SequenceOf[NameT]]]:
        """Split a closed named dependency graph into dependency-first waves.

        Wave ``n`` contains only names whose dependencies all live in earlier
        waves, so each wave may proceed in parallel while the sequence between
        waves stays strict. The graph is closed: every referenced name must be
        a key of ``edges``; an unknown reference or a cycle fails the result
        instead of raising, so callers (release publish ordering, codemod
        provider ordering) compose it through ``p.Result`` chaining.

        Returns:
            The resulting ``p.Result[t.SequenceOf[t.SequenceOf[NameT]]]``.

        """
        unknown = sorted({
            dependency
            for deps in edges.values()
            for dependency in deps
            if dependency not in edges
        })
        if unknown:
            return r[t.SequenceOf[t.SequenceOf[NameT]]].fail(
                "dependency graph references names outside the graph: "
                + ", ".join(unknown),
            )
        pending: dict[NameT, set[str]] = {
            name: set(deps) for name, deps in edges.items()
        }
        waves: list[tuple[NameT, ...]] = []
        while pending:
            ready = frozenset(name for name, deps in pending.items() if not deps)
            if not ready:
                return r[t.SequenceOf[t.SequenceOf[NameT]]].fail(
                    "cyclic dependency graph: " + ", ".join(sorted(pending)),
                )
            waves.append(tuple(sorted(ready)))
            pending = {
                name: deps - ready
                for name, deps in pending.items()
                if name not in ready
            }
        return r[t.SequenceOf[t.SequenceOf[NameT]]].ok(tuple(waves))

    @classmethod
    def installed_resource_snapshot(
        cls,
        distribution: str,
        *,
        resource_parts: t.StrSequence,
        environment_root: Path,
    ) -> p.Result[m.Infra.InstalledResourceSnapshot]:
        """Select one declared distribution resource without importing its namespace.

        Returns:
            Original resource and inventory snapshots, or the first causal failure.

        """
        result_type = r[m.Infra.InstalledResourceSnapshot]
        supplier = cls._elected_installed_supplier(distribution, resource_parts)
        if supplier.failure:
            return result_type.from_failure(supplier)
        elected = cls._elected_installed_resource(
            supplier.value,
            distribution,
            resource_parts,
        )
        if elected.failure:
            return result_type.from_failure(elected)
        resource, metadata_entries = elected.value
        states = cls._captured_installed_states(
            supplier.value,
            environment_root,
            (*metadata_entries, resource),
        )
        if states.failure:
            return result_type.from_failure(states)
        if not cls._resource_matches_record(resource, states.value[-1]):
            return result_type.fail(
                f"installed resource differs from its owning RECORD: {distribution} "
                f"{'/'.join(resource_parts)}",
            )
        rechecked = cls._rechecked_installed_inventory(
            supplier.value,
            states.value,
            distribution,
        )
        if rechecked.failure:
            return result_type.from_failure(rechecked)
        return result_type.ok(
            m.Infra.InstalledResourceSnapshot(
                resource=states.value[-1],
                inventory=tuple(states.value[:-1]),
            ),
        )

    @staticmethod
    def _elected_installed_supplier(
        distribution: str,
        resource_parts: t.StrSequence,
    ) -> p.Result[Distribution]:
        """Authenticate one installed distribution and its resource components.

        Returns:
            The single elected installed distribution, or the election failure.

        """
        result_type = r[Distribution]
        if not resource_parts or any(
            not part
            or part in {".", ".."}
            or "/" in part
            or "\\" in part
            or "\0" in part
            for part in resource_parts
        ):
            return result_type.fail(
                "installed resource requires exact relative components"
            )
        installed = u.installed_distributions(name=distribution)
        if len(installed) != 1:
            return result_type.fail(
                f"installed resource requires one distribution: {distribution}; "
                f"observed={len(installed)}",
            )
        supplier = installed[0]
        if canonicalize_name(supplier.metadata["Name"]) != canonicalize_name(
            distribution
        ):
            return result_type.fail(
                f"installed resource distribution identity differs: {distribution}",
            )
        return result_type.ok(supplier)

    @staticmethod
    def _elected_installed_resource(
        supplier: Distribution,
        distribution: str,
        resource_parts: t.StrSequence,
    ) -> p.Result[t.Pair[PackagePath, t.VariadicTuple[PackagePath]]]:
        """Elect the exact RECORD resource entry beside its native metadata pair.

        Returns:
            The resource entry and its METADATA and RECORD inventory entries.

        """
        result_type = r[t.Pair[PackagePath, t.VariadicTuple[PackagePath]]]
        records = supplier.files
        if records is None:
            return result_type.fail(
                f"installed resource has no RECORD inventory: {distribution}",
            )
        resource_entries = tuple(
            item
            for item in records
            if item.parts[-len(resource_parts) :] == tuple(resource_parts)
        )
        if len(resource_entries) != 1:
            return result_type.fail(
                f"installed resource requires one exact RECORD entry: {distribution} "
                f"{'/'.join(resource_parts)}; observed={len(resource_entries)}",
            )
        metadata_entries = tuple(
            item
            for item in records
            if item.name in {"METADATA", "RECORD"}
            and item.parent.name.endswith(".dist-info")
        )
        if (
            frozenset(item.name for item in metadata_entries)
            != (_EXACT_INSTALL_METADATA_NAMES)
            or len(metadata_entries) != _EXACT_INSTALL_METADATA_COUNT
        ):
            return result_type.fail(
                "installed resource needs its exact METADATA and RECORD: "
                f"{distribution}",
            )
        return result_type.ok((resource_entries[0], metadata_entries))

    @staticmethod
    def _captured_installed_states(
        supplier: Distribution,
        environment_root: Path,
        entries: t.SequenceOf[PackagePath],
    ) -> p.Result[list[m.Cli.AtomicFileState]]:
        """Capture the byte state of every elected entry inside its environment.

        Args:
            supplier: The elected installed distribution owning the entries.
            environment_root: Physical root the entries must stay inside.
            entries: RECORD entries captured in inventory-then-resource order.

        Returns:
            The captured states in entry order, or the first capture failure.

        """
        result_type = r[list[m.Cli.AtomicFileState]]
        prefix = environment_root.expanduser().resolve(strict=True)
        states: list[m.Cli.AtomicFileState] = []
        for entry in entries:
            path = Path(str(supplier.locate_file(entry))).resolve(strict=True)
            if not path.is_relative_to(prefix):
                return result_type.fail(
                    f"installed resource escapes its physical environment: {path}",
                )
            captured = u.Cli.atomic_read_binary_file_state(path, required=True)
            if captured.failure:
                return result_type.from_failure(captured)
            states.append(captured.value)
        return result_type.ok(states)

    @staticmethod
    def _resource_matches_record(
        resource: PackagePath,
        state: m.Cli.AtomicFileState,
    ) -> bool:
        """Authenticate one captured resource against its RECORD digest row.

        Args:
            resource: The elected RECORD entry declaring the expected digest.
            state: The captured byte state of the resource file.

        Returns:
            Whether the captured content matches its RECORD digest and size.

        """
        return not (
            state.content is None
            or resource.hash is None
            or resource.hash.mode != "sha256"
            or resource.size != len(state.content)
            or resource.hash.value
            != urlsafe_b64encode(bytes.fromhex(u.Cli.sha256_bytes(state.content)))
            .rstrip(b"=")
            .decode("ascii")
        )

    @staticmethod
    def _rechecked_installed_inventory(
        supplier: Distribution,
        states: t.SequenceOf[m.Cli.AtomicFileState],
        distribution: str,
    ) -> p.Result[bool]:
        """Authenticate the METADATA and RECORD owners and their byte stability.

        Args:
            supplier: The elected installed distribution owning the inventory.
            states: Captured states in inventory-then-resource order.
            distribution: Elected distribution spelling used in failure text.

        Returns:
            Whether the inventory is native and survived capture unchanged.

        """
        result_type = r[bool]
        inventory = tuple(states[:-1])
        for name in ("METADATA", "RECORD"):
            recorded = next(item for item in inventory if item.path.name == name)
            raw = supplier.read_text(name)
            if raw is None or recorded.content != raw.encode(c.DEFAULT_ENCODING):
                return result_type.fail(
                    "installed resource inventory has a foreign owner: "
                    f"{distribution} {name}",
                )
        unchanged = u.Cli.atomic_verify_binary_file_states(states)
        if unchanged.failure:
            return result_type.from_failure(unchanged)
        return result_type.ok(value=True)

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
    def resolved_dependency_versions(cls) -> t.MappingKV[str, str]:
        """Read registry versions from the provisioned runtime, not release provenance.

        Returns:
            The resulting ``t.MappingKV[str, str]``.

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
        resolved_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence = (),
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
        internal_names: t.StrSequence,
    ) -> t.Pair[str, Requirement] | None:
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
    ) -> t.StrSequence:
        """Return normalized dependency names from one TOML document.

        Returns:
            Normalized dependency names from one TOML document.

        """
        normalized = FlextInfraUtilitiesPyproject.normalized_toml_payload(document)
        if not normalized:
            return ()
        return cls.declared_dependency_names_from_payload(normalized)

    @classmethod
    def declared_dependency_names_from_payload(
        cls,
        payload: t.JsonMapping,
    ) -> t.StrSequence:
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
        workspace_project_names: t.StrSequence = (),
    ) -> t.StrSequence:
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
