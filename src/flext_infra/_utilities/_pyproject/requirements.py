"""Internal requirement rendering and workspace dependency-group policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from flext_infra import c, config, m, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRepository,
)
from flext_infra._utilities._pyproject._requirements_provenance import (
    FlextInfraUtilitiesPyprojectRequirementsProvenance,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra import p


class FlextInfraUtilitiesPyprojectRequirements:
    """Render internal requirements for the active workspace topology."""

    @staticmethod
    def generated_typing_version(
        implementation_version: str, files: t.MappingKV[Path, bytes]
    ) -> str:
        """Derive the producer version from ordered relative stub names and bytes.

        Returns:
            The exact implementation release plus its generated content digest.

        """
        digest = sha256()
        for relative, content in sorted(files.items()):
            digest.update(relative.as_posix().encode(c.DEFAULT_ENCODING))
            digest.update(content)
        return f"{Version(implementation_version).public}+{digest.hexdigest()}"

    @classmethod
    def generated_typing_packages(
        cls,
        document: t.Cli.TomlDocument,
        *,
        root: Path,
        policy: m.Infra.TypingGenerationPolicy,
        for_generation: bool = False,
    ) -> p.Result[t.VariadicTuple[m.Infra.GeneratedTypingPackage]]:
        """Authenticate declared local typing sources against the producer contract.

        Generation elects repair targets from metadata identity; admission always
        authenticates the complete generated snapshot unless explicitly producing it.

        Returns:
            Captured, validated local provenance, never a prefix exemption.

        """
        result = r[t.VariadicTuple[m.Infra.GeneratedTypingPackage]]
        sources = u.Cli.toml_table_path(document, ("tool", "uv", "sources"))
        if sources is None:
            return result.ok(())
        packages: list[m.Infra.GeneratedTypingPackage] = []
        for name, source in (
            u
            .json_mapping_adapter()
            .validate_python(
                u.Cli.toml_unwrap_item(sources),
            )
            .items()
        ):
            if not isinstance(source, Mapping) or not isinstance(
                source.get("path"), str
            ):
                continue
            path = source["path"]
            if not isinstance(path, str):
                continue
            candidate = root / path
            if not (
                canonicalize_name(name).startswith(
                    canonicalize_name(policy.distribution_prefix)
                )
                or candidate.is_relative_to(root / policy.directory)
            ):
                continue
            validated = cls._generated_typing_package(
                root, name, candidate, policy, for_generation=for_generation
            )
            if validated.failure:
                return result.from_failure(validated)
            packages.append(validated.value)
        return result.ok(tuple(packages))

    @classmethod
    def _generated_typing_package(
        cls,
        root: Path,
        name: str,
        candidate: Path,
        policy: m.Infra.TypingGenerationPolicy,
        *,
        for_generation: bool = False,
    ) -> p.Result[m.Infra.GeneratedTypingPackage]:
        """Read and authenticate one physical producer output, without global probes.

        Returns:
            Its typed provenance or the first invalid producer fact.

        """
        result = r[m.Infra.GeneratedTypingPackage]
        confined = root.resolve() / policy.directory
        package = candidate.resolve()
        if (
            not confined.resolve().is_relative_to(root.resolve())
            or not package.is_relative_to(confined.resolve())
            or package.parent != confined.resolve()
            or not (package / c.PYPROJECT_FILENAME).resolve().is_relative_to(package)
        ):
            return result.fail(
                f"generated typing package escapes producer directory: {candidate}"
            )
        metadata = u.Cli.atomic_read_binary_file_state(
            package / c.PYPROJECT_FILENAME, required=True
        )
        if metadata.failure:
            return result.from_failure(metadata)
        content = metadata.value.content
        if content is None or not content.startswith(
            c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING)
        ):
            return result.fail(
                f"generated typing package lacks producer metadata: {candidate}"
            )
        document = u.Cli.toml_parse_text(content.decode(c.DEFAULT_ENCODING))
        if document is None:
            return result.fail(f"invalid generated typing metadata: {candidate}")
        identity = cls._generated_typing_identity(
            document, metadata.value, name, policy
        )
        if identity.failure:
            return result.from_failure(identity)
        # A producer elects repair targets from their identity, not missing or stale
        # outputs. Admission consumers still require the complete content contract.
        return (
            identity
            if for_generation
            else cls._generated_typing_content(identity.value)
        )

    @staticmethod
    def _generated_typing_identity(
        document: t.Cli.TomlDocument,
        metadata: m.Cli.AtomicFileState,
        name: str,
        policy: m.Infra.TypingGenerationPolicy,
    ) -> p.Result[m.Infra.GeneratedTypingPackage]:
        """Validate metadata identities before admitting any local requirement.

        Returns:
            The producer identity bound to its captured metadata.

        """
        result = r[m.Infra.GeneratedTypingPackage]
        project = u.Cli.toml_table_child(document, "project")
        typing = u.Cli.toml_table_path(document, ("tool", "flext", "typing"))
        entries = u.Cli.toml_table_path(
            document, ("project", "entry-points", c.Infra.TYPING_STUB_ENTRY_POINT_GROUP)
        )
        wheel = u.Cli.toml_table_path(
            document, ("tool", "hatch", "build", "targets", "wheel")
        )
        if (
            project is None
            or typing is None
            or entries is None
            or wheel is None
            or len(entries) != 1
        ):
            return result.fail(
                f"generated typing package lacks producer contract: {metadata.path}"
            )
        module = next(iter(entries))
        version = u.Cli.toml_value(project, "version")
        implementation = u.Cli.toml_value(typing, "implementation")
        if (
            not c.Infra.PYTHON_IMPORT_NAME_RE.fullmatch(module)
            or module.startswith(c.Infra.INTERNAL_PREFIXES)
            or u.Cli.toml_value(entries, module) != module
            or tuple(u.Cli.toml_as_string_list(u.Cli.toml_value(wheel, "packages")))
            != (f"{module}-stubs",)
        ):
            return result.fail(
                f"generated typing stub identity mismatch: {metadata.path}"
            )
        if (
            canonicalize_name(policy.distribution_prefix + module)
            != canonicalize_name(name)
            or metadata.path.parent.name != canonicalize_name(name)
            or u.Cli.toml_value(project, "name") != canonicalize_name(name)
            or not isinstance(version, str)
            or not isinstance(implementation, str)
        ):
            return result.fail(
                f"generated typing package identity mismatch: {metadata.path}"
            )
        return result.ok(
            m.Infra.GeneratedTypingPackage(
                distribution=canonicalize_name(name),
                path=metadata.path.parent,
                module=module,
                implementation=implementation,
                version=version,
                inputs=(metadata,),
            )
        )

    @classmethod
    def _generated_typing_content(
        cls,
        identity: m.Infra.GeneratedTypingPackage,
    ) -> p.Result[m.Infra.GeneratedTypingPackage]:
        """Bind exact implementation and producer snapshot version to local stubs.

        Returns:
            The authenticated complete producer provenance.

        """
        result = r[m.Infra.GeneratedTypingPackage]
        parsed = Requirement(identity.implementation)
        bounds = tuple(parsed.specifier)
        if (
            any((parsed.url, parsed.marker, parsed.extras))
            or len(bounds) != 1
            or bounds[0].operator != "=="
            or "*" in bounds[0].version
        ):
            return result.fail(
                f"generated typing package implementation is not exact: {identity.path}"
            )
        version = Version(identity.version)
        if (
            version.public != Version(bounds[0].version).public
            or version.local is None
            or len(version.local) != len(sha256().hexdigest())
            or any(character not in "0123456789abcdef" for character in version.local)
        ):
            return result.fail(
                f"generated typing producer version mismatch: {identity.path}"
            )
        states: list[m.Cli.AtomicFileState] = list(identity.inputs)
        stub_root = identity.path / f"{identity.module}-stubs"
        files = tuple(sorted(stub_root.rglob("*.pyi")))
        if not files or not (stub_root / c.Infra.INIT_PYI).is_file():
            return result.fail(
                f"generated typing package has no stub entry point: {identity.path}"
            )
        for path in files:
            if not path.resolve().is_relative_to(identity.path):
                return result.fail(f"generated typing stub escapes package: {path}")
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            stub = state.content
            if stub is None or (
                path == stub_root / c.Infra.INIT_PYI
                and not stub.startswith(
                    c.Infra.TYPING_STUB_HEADER.encode(c.DEFAULT_ENCODING)
                )
            ):
                return result.fail(
                    f"generated typing stub entry point lacks producer content: {path}"
                )
            states.append(state)
        content = {
            state.path.relative_to(identity.path): state.content
            for state in states
            if state.path.suffix == ".pyi" and state.content is not None
        }
        if cls.generated_typing_version(bounds[0].version, content) != identity.version:
            return result.fail(
                f"generated typing producer digest mismatch: {identity.path}"
            )
        return result.ok(identity.model_copy(update={"inputs": tuple(states)}))

    @staticmethod
    def dependency_group_entries(
        value: t.JsonPayload,
    ) -> t.VariadicTuple[str | m.Infra.DependencyGroupInclude]:
        """Parse the shared native entry grammar without expanding inclusions.

        Returns:
            The resulting ``t.VariadicTuple[str | m.Infra.DependencyGroupInclude]``.

        """
        return m.Infra.DependencyGroupEntries.model_validate(value).root

    @classmethod
    def read_dependency_group(
        cls,
        container: t.Cli.TomlTable,
        name: str,
    ) -> t.VariadicTuple[str | m.Infra.DependencyGroupInclude]:
        """Read an absent or native array without permissive string extraction.

        Returns:
            The resulting ``t.VariadicTuple[str | m.Infra.DependencyGroupInclude]``.

        """
        value = u.Cli.toml_value(
            container,
            FlextInfraUtilitiesPyproject.dependency_group_name(container, name),
        )
        return (
            ()
            if value is None
            else cls.dependency_group_entries(u.Cli.toml_unwrap_item(value))
        )

    @classmethod
    def merge_dependency_group_entries(
        cls,
        generated: t.SequenceOf[str | m.Infra.DependencyGroupInclude],
        custom: t.SequenceOf[str | m.Infra.DependencyGroupInclude],
    ) -> t.VariadicTuple[str | m.Infra.DependencyGroupInclude]:
        """Lead missing complete requirements and preserve authored entries.

        Packaging owns requirement identity, including version constraints.
        Explicit retirement policy determines which authored entries are removed.

        Returns:
            The resulting ``t.VariadicTuple[str | m.Infra.DependencyGroupInclude]``.

        """
        active = frozenset(
            cls.active_development_requirements(
                tuple(entry for entry in custom if isinstance(entry, str)),
            ),
        )
        authored = tuple(
            entry for entry in custom if not isinstance(entry, str) or entry in active
        )
        requirements = {
            Requirement(entry) for entry in authored if isinstance(entry, str)
        }
        inclusions = {
            canonicalize_name(entry.include_group)
            for entry in authored
            if not isinstance(entry, str)
        }
        additions: list[str | m.Infra.DependencyGroupInclude] = []
        for entry in generated:
            if isinstance(entry, str):
                parsed = Requirement(entry)
                if parsed in requirements:
                    continue
                requirements.add(parsed)
            else:
                included = canonicalize_name(entry.include_group)
                if included in inclusions:
                    continue
                inclusions.add(included)
            additions.append(entry)
        return (*additions, *authored)

    @staticmethod
    def _development_requirement_identity(
        requirement: str,
    ) -> t.Pair[t.Pair[str, str], t.Pair[str | None, str | None]]:
        """Scope floor replacement to the same extras, marker and origin.

        Returns:
            The resulting ``t.Pair[t.Pair[str, str], t.Pair[str | None, str | None]]``.

        """
        parsed = Requirement(requirement)
        return (
            (canonicalize_name(parsed.name), ",".join(sorted(parsed.extras))),
            (str(parsed.marker) if parsed.marker is not None else None, parsed.url),
        )

    @staticmethod
    def requirement_group_fields(
        document: t.Cli.TomlDocument,
        project: t.Cli.TomlTable,
    ) -> Iterator[t.Pair[t.Cli.TomlTable, str]]:
        """Yield ``(section, group_name)`` for every declared requirement group.

        Optional dependencies hang off ``[project]`` while dependency groups hang
        off the document root; this is the single owner of that traversal for
        every requirement rewriter.

        Yields:
            Each ``t.Pair[t.Cli.TomlTable, str]``.

        """
        for section_name in (c.Infra.OPTIONAL_DEPENDENCIES, c.Infra.DEPENDENCY_GROUPS):
            parent = (
                project if section_name == c.Infra.OPTIONAL_DEPENDENCIES else document
            )
            section = u.Cli.toml_table_child(parent, section_name)
            if section is None:
                continue
            group_names = u.json_mapping_adapter().validate_python(
                u.Cli.toml_unwrap_item(section),
            )
            for group_name in group_names:
                yield section, group_name

    @classmethod
    def _normalize_requirements(
        cls,
        document: t.Cli.TomlDocument,
        *,
        declared_sources: t.StrMapping,
        candidate_sources: t.StrMapping,
        family_line: str | None,
        generated_local: t.VariadicTuple[m.Infra.GeneratedTypingPackage] = (),
    ) -> p.Result[bool]:
        """Render internal requirements from their declared Git provenance.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        provenance = FlextInfraUtilitiesPyprojectRequirementsProvenance(
            declared_sources=declared_sources,
            candidate_sources=candidate_sources,
            family_line=family_line,
            generated_local=generated_local,
        )
        project = u.Cli.toml_ensure_table(document, c.Infra.PROJECT)
        normalized = cls._normalize_requirement_field(
            project,
            c.Infra.DEPENDENCIES,
            provenance=provenance,
        )
        if normalized.failure:
            return normalized
        optional = u.Cli.toml_table_child(project, c.Infra.OPTIONAL_DEPENDENCIES)
        if optional is not None:
            for group_name in u.json_mapping_adapter().validate_python(
                u.Cli.toml_unwrap_item(optional),
            ):
                group_result = cls._normalize_requirement_field(
                    optional,
                    group_name,
                    provenance=provenance,
                )
                if group_result.failure:
                    return group_result
        return cls._normalize_dependency_groups(document, provenance=provenance)

    @classmethod
    def _normalize_dependency_groups(
        cls,
        document: t.Cli.TomlDocument,
        *,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[bool]:
        """Normalize PEP 508 strings in place around native inclusion entries.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        section = u.Cli.toml_table_child(document, c.Infra.DEPENDENCY_GROUPS)
        if section is None:
            return r[bool].ok(value=True)
        parsed = u.validate_value(
            m.Infra.DependencyGroupDeclarations,
            {"dependency-groups": u.Cli.toml_unwrap_item(section)},
        )
        if parsed.failure:
            return r[bool].from_failure(parsed)
        for group_name, entries in parsed.value.dependency_groups.items():
            values: list[str | m.Infra.DependencyGroupInclude] = []
            for entry in entries:
                if not isinstance(entry, str):
                    values.append(entry)
                    continue
                normalized = cls._canonical_requirement(entry, provenance=provenance)
                if normalized.failure:
                    return r[bool].from_failure(normalized)
                values.append(normalized.value)
            u.Cli.toml_sync_value(
                section,
                group_name,
                FlextInfraUtilitiesPyproject.dependency_group_wire(values),
            )
        return r[bool].ok(value=True)

    @classmethod
    def _normalize_requirement_field(
        cls,
        container: t.Cli.TomlDocument | t.Cli.TomlTable,
        key: str,
        *,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[bool]:
        """Normalize one dependency array and fail on model-less entries.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        raw_value = u.Cli.toml_value(container, key)
        if raw_value is None:
            return r[bool].ok(value=True)
        raw_items = u.Cli.json_as_sequence(raw_value)
        validated_items: p.Result[t.StrSequence] = u.validate_value(
            t.Infra.STR_SEQ_ADAPTER,
            raw_items,
            strict=True,
        )
        if validated_items.failure:
            return r[bool].fail_op(
                f"validate dependency group {key}",
                validated_items.error,
            )
        items = validated_items.value
        normalized_items: t.MutableSequenceOf[str] = []
        for item in items:
            normalized = cls._canonical_requirement(item, provenance=provenance)
            if normalized.failure:
                return r[bool].from_failure(normalized)
            normalized_items.append(normalized.value)
        canonical = tuple(
            sorted(dict.fromkeys(normalized_items), key=cls.dependency_order_key),
        )
        u.Cli.toml_sync_string_list(container, key, canonical)
        return r[bool].ok(value=True)

    @staticmethod
    def dependency_order_key(requirement: str) -> t.Pair[str, str]:
        """Order preserved and conformed requirements by name and complete spec.

        Returns:
            The resulting ``t.Pair[str, str]``.

        Raises:
            ValueError: If dependency ordering requires a named requirement.

        """
        name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if name is None:
            message = "dependency ordering requires a named requirement"
            raise ValueError(message)
        return name, requirement

    @classmethod
    def _canonical_requirement(
        cls,
        requirement: str,
        *,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[str]:
        """Render one internal requirement from its own declared Git source.

        The requirement line is the only authority for an internal
        dependency's canonical URL and branch: it is parsed and canonicalized
        (transport scheme only), never rewritten from provider policy. The ref
        is the dependency's integration line: uv.lock alone records the commit
        it resolves to, so a commit left in this generated projection is
        residue re-rendered on its line (an attached member's declared line,
        otherwise the detected FLEXT line) and never written back; without a
        line it fails loudly. Internal means the FLEXT family or an attached
        workspace member of any family. A source-less internal dependency that
        the active workspace overlay does not own is a loud failure.

        Returns:
            The resulting ``p.Result[str]``.

        """
        parsed_requirement = Requirement(requirement)
        local = next(
            (
                item
                for item in provenance.generated_local
                if item.distribution == canonicalize_name(parsed_requirement.name)
            ),
            None,
        )
        if local is not None:
            return cls._canonical_generated_typing_requirement(requirement, local)
        dependency_name = cls._internal_dependency_name(
            requirement,
            declared_sources=provenance.declared_sources,
            candidate_sources=provenance.candidate_sources,
        )
        if dependency_name is None:
            return r[str].ok(requirement.strip())
        if "@" not in requirement.partition(";")[0] and (
            FlextInfraUtilitiesDependencies
            .dependency_constraint(
                requirement,
                replace_source=True,
            )
            .partition(";")[0]
            .strip()
            != dependency_name
        ):
            # A PEP 508 URL cannot also encode bounds; keep explicit bounds intact.
            return r[str].ok(requirement.strip())
        prepared = cls._parsed_canonical_provenance(requirement)
        if prepared.failure:
            return r[str].from_failure(prepared)
        head, marker_pair, (url, declared_ref) = prepared.value
        resolved = cls._resolved_requirement_provenance(
            head,
            dependency_name,
            parsed=(url, declared_ref),
            line=provenance.family_line,
            provenance=provenance,
        )
        if resolved.failure:
            return r[str].from_failure(resolved)
        pins_commit = cls._pins_commit(
            candidate_sources=provenance.candidate_sources,
            dependency_name=dependency_name,
            declared_ref=declared_ref,
        )
        return cls._rendered_canonical(
            head,
            dependency_name,
            resolved.value,
            marker_pair,
            pins_commit=pins_commit,
        )

    @staticmethod
    def _canonical_generated_typing_requirement(
        requirement: str,
        local: m.Infra.GeneratedTypingPackage,
    ) -> p.Result[str]:
        """Preserve full requirements only when compatible with their local producer.

        Returns:
            The unchanged requirement or its source/constraint conflict.

        """
        parsed = Requirement(requirement)
        if parsed.url is not None or (
            parsed.specifier and not parsed.specifier.contains(local.version)
        ):
            return r[str].fail(
                "generated typing requirement conflicts with local producer: "
                f"{requirement}"
            )
        return r[str].ok(requirement.strip())

    @classmethod
    def _resolved_requirement_provenance(
        cls,
        head: str,
        dependency_name: str,
        *,
        parsed: t.Pair[str, str],
        line: str | None,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[t.Pair[t.Pair[str, str], str | None]]:
        """Apply the declared-member and candidate-commit provenance overrides.

        Returns:
            The resulting ``p.Result[t.Pair[t.Pair[str, str], str | None]]``.

        """
        url, declared_ref = parsed
        declared = provenance.declared_sources.get(dependency_name)
        if declared is not None:
            declared_result = cls._declared_member_override(head, declared)
            if declared_result.failure:
                return r[t.Pair[t.Pair[str, str], str | None]].from_failure(
                    declared_result,
                )
            # An attached member renders on the line its declaration carries.
            declared_url, member_line = declared_result.value
            if not url:
                url, declared_ref = declared_url, member_line
        candidate = provenance.candidate_sources.get(dependency_name)
        if candidate is not None:
            candidate_result = cls._candidate_commit_override(
                head,
                dependency_name,
                candidate,
                url,
            )
            if candidate_result.failure:
                return r[t.Pair[t.Pair[str, str], str | None]].from_failure(
                    candidate_result,
                )
            url, declared_ref = candidate_result.value
            line = declared_ref
        return r[t.Pair[t.Pair[str, str], str | None]].ok(((url, declared_ref), line))

    @staticmethod
    def _pins_commit(
        *,
        candidate_sources: t.StrMapping,
        dependency_name: str,
        declared_ref: str,
    ) -> bool:
        """Whether the rendered requirement pins an exact commit.

        Returns:
            The resulting ``bool``.

        """
        return candidate_sources.get(dependency_name) is None and (
            FlextInfraUtilitiesRepository.ref_is_commit(declared_ref)
        )

    @staticmethod
    def _internal_dependency_name(
        requirement: str,
        *,
        declared_sources: t.StrMapping,
        candidate_sources: t.StrMapping,
    ) -> str | None:
        """Return the dependency name when the requirement is internal.

        Returns:
            The dependency name, or None for an external requirement.

        """
        dependency_name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if dependency_name is None:
            return None
        if (
            dependency_name.startswith("flext-")
            or dependency_name in declared_sources
            or dependency_name in candidate_sources
        ):
            return dependency_name
        return None

    @classmethod
    def _parsed_canonical_provenance(
        cls,
        requirement: str,
    ) -> p.Result[t.Triple[str, t.Pair[bool, str], t.Pair[str, str]]]:
        """Parse one internal requirement's head, marker, and Git provenance.

        Returns:
            The canonical head, the rendered marker pair, and the declared
            Git source URL and ref.

        """
        requirement_part, separator, marker = requirement.partition(";")
        head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(requirement_part.strip())
        if head_match is None:
            return r[t.Triple[str, t.Pair[bool, str], t.Pair[str, str]]].fail(
                f"invalid internal requirement: {requirement}",
            )
        source = FlextInfraUtilitiesRepository.declared_git_source(requirement)
        if source.failure:
            return r[t.Triple[str, t.Pair[bool, str], t.Pair[str, str]]].from_failure(
                source,
            )
        marker_text = marker.strip()
        head = head_match.group("head").strip()
        marker_pair = (bool(separator and marker_text), marker_text)
        return r.ok((head, marker_pair, source.value))

    @staticmethod
    def _declared_member_override(
        head: str,
        declared: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Parse an attached member's declared Git source line.

        Returns:
            The declared URL and integration line.

        """
        source_line = f"{head} @ {declared}"
        parsed = FlextInfraUtilitiesRepository.declared_git_source(source_line)
        if parsed.failure:
            return r[t.Pair[str, str]].from_failure(parsed)
        return r[t.Pair[str, str]].ok(parsed.value)

    @staticmethod
    def _candidate_commit_override(
        head: str,
        dependency_name: str,
        candidate: str,
        url: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Validate and apply one candidate workspace overlay source.

        Returns:
            The candidate URL and the full commit it pins.

        """
        if not url:
            return r[t.Pair[str, str]].fail(
                "candidate dependency has no declared Git provenance: "
                f"{dependency_name}",
            )
        selected = FlextInfraUtilitiesRepository.declared_git_source(
            f"{head} @ {candidate}",
        )
        if selected.failure:
            return r[t.Pair[str, str]].from_failure(selected)
        candidate_url, candidate_commit = selected.value
        if not FlextInfraUtilitiesRepository.ref_is_commit(candidate_commit):
            return r[t.Pair[str, str]].fail(
                f"candidate dependency must pin a full Git commit: {dependency_name}",
            )
        if url and url != candidate_url:
            return r[t.Pair[str, str]].fail(
                "candidate dependency Git URL differs from declared provenance: "
                f"{dependency_name}",
            )
        return r[t.Pair[str, str]].ok((candidate_url, candidate_commit))

    @staticmethod
    def _rendered_canonical(
        head: str,
        dependency_name: str,
        resolved: t.Pair[t.Pair[str, str], str | None],
        marker: t.Pair[bool, str],
        *,
        pins_commit: bool,
    ) -> p.Result[str]:
        """Render the canonical inline Git requirement line.

        Returns:
            The resulting ``p.Result[str]``.

        """
        ((url, declared_ref), line) = resolved
        has_marker, marker_text = marker
        if not url:
            return r[str].fail(
                f"internal dependency declares no direct git source: {dependency_name}",
            )
        if pins_commit:
            if line is None:
                return r[str].fail(
                    f"internal dependency {dependency_name} pins commit "
                    f"{declared_ref} and no line is declared to re-render "
                    "it: uv.lock records the commit and only `make upg` moves it",
                )
            declared_ref = line
        # The inline Git source is the sole provenance for each independent
        # project lock, including the orchestration repository.
        inline = f"{head} @ git+{url}@{declared_ref}"
        return r[str].ok(f"{inline} ; {marker_text}" if has_marker else inline)

    @staticmethod
    def active_development_requirements(requirements: t.StrSequence) -> t.StrSequence:
        """Preserve declared requirements except explicitly retired distributions.

        Returns:
            Requirements retaining their order and complete constraints.

        Raises:
            ValueError: A retired distribution does not name a valid package.

        """
        retired_names = frozenset(
            FlextInfraUtilitiesDependencies.dep_name(requirement)
            for requirement in config.Infra.codegen.scaffold.project.retired_dev
        )
        if None in retired_names:
            msg = "Retired development distributions must name valid packages"
            raise ValueError(msg)
        return tuple(
            requirement
            for requirement in requirements
            if FlextInfraUtilitiesDependencies.dep_name(requirement)
            not in retired_names
        )

    @classmethod
    def _normalized_live_group_entries(
        cls,
        groups: t.Cli.TomlTable,
        dev_name: str,
        *,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[list[str | m.Infra.DependencyGroupInclude]]:
        """Normalize the live development group's entries in declared order.

        Returns:
            The resulting ``p.Result[list[str | m.Infra.DependencyGroupInclude]]``.

        """
        live_dev: list[str | m.Infra.DependencyGroupInclude] = []
        for entry in cls.read_dependency_group(groups, dev_name):
            if not isinstance(entry, str):
                live_dev.append(entry)
                continue
            normalized = cls._canonical_requirement(entry, provenance=provenance)
            if normalized.failure:
                return r[list[str | m.Infra.DependencyGroupInclude]].from_failure(
                    normalized
                )
            live_dev.append(normalized.value)
        return r[list[str | m.Infra.DependencyGroupInclude]].ok(live_dev)

    @classmethod
    def _sync_dependency_groups(
        cls,
        document: t.Cli.TomlDocument,
        *,
        project_name: str,
        required_dev_dependencies: t.StrSequence,
        provenance: FlextInfraUtilitiesPyprojectRequirementsProvenance,
    ) -> p.Result[bool]:
        """Sync development groups while applying explicit retirement policy.

        Returns:
            Normalized generated floors and preserved authored variants.

        Raises:
            ValueError: Retirement conflicts with required development dependencies.

        """
        if cls.active_development_requirements(required_dev_dependencies) != tuple(
            required_dev_dependencies,
        ):
            msg = "Canonical development requirements include retired distributions"
            raise ValueError(msg)
        groups = u.Cli.toml_ensure_table(document, c.Infra.DEPENDENCY_GROUPS)
        dev_name = FlextInfraUtilitiesPyproject.dependency_group_name(
            groups, str(c.Infra.DEV)
        )
        # A bare internal requirement carries no source or version constraint.
        # Preserve its declared direct source when composing the policy floor.
        live = cls._normalized_live_group_entries(
            groups,
            dev_name,
            provenance=provenance,
        )
        if live.failure:
            return r[bool].from_failure(live)
        live_dev = live.value
        sourced_live = tuple(
            requirement
            for requirement in live_dev
            if isinstance(requirement, str) and cls._declares_direct_source(requirement)
        )
        required_dev: list[str] = []
        for requirement in required_dev_dependencies:
            if FlextInfraUtilitiesDependencies.dep_name(requirement) == project_name:
                continue
            normalized = cls._canonical_requirement(requirement, provenance=provenance)
            if normalized.failure:
                return r[bool].from_failure(normalized)
            if (
                cls._floor_yields_to_declared_source(
                    requirement,
                    sourced_live,
                )
                and normalized.value not in live_dev
            ):
                continue
            required_dev.append(normalized.value)
        dev = cls.merge_dependency_group_entries(
            required_dev,
            live_dev,
        )
        if dev or u.Cli.toml_value(groups, dev_name) is not None:
            u.Cli.toml_sync_value(
                groups,
                dev_name,
                FlextInfraUtilitiesPyproject.dependency_group_wire(dev),
            )
        else:
            u.Cli.toml_remove_key_if_present(groups, dev_name)

        codegen_name = FlextInfraUtilitiesPyproject.dependency_group_name(
            groups,
            str(c.Infra.DependencyGroup.CODEGEN),
        )
        codegen = cls.merge_dependency_group_entries(
            (),
            cls.read_dependency_group(groups, codegen_name),
        )
        if codegen or u.Cli.toml_value(groups, codegen_name) is not None:
            u.Cli.toml_sync_value(
                groups,
                codegen_name,
                FlextInfraUtilitiesPyproject.dependency_group_wire(codegen),
            )
        else:
            u.Cli.toml_remove_key_if_present(groups, codegen_name)
        cls._remove_workspace_dependency_group(document)
        return r[bool].ok(value=True)

    @staticmethod
    def _declares_direct_source(requirement: str) -> bool:
        """Whether one requirement line declares a direct ``@ source``.

        Returns:
            The resulting ``bool``.

        """
        return "@" in requirement.partition(";")[0]

    @classmethod
    def _floor_yields_to_declared_source(
        cls,
        requirement: str,
        sourced_live: t.StrSequence,
    ) -> bool:
        """Whether a bare internal floor name must yield to a declared source.

        Returns:
            The resulting ``bool``.

        """
        parsed = Requirement(requirement)
        identity = cls._development_requirement_identity(requirement)
        if (
            not canonicalize_name(parsed.name).startswith("flext-")
            or parsed.url is not None
            or parsed.specifier
        ):
            return False
        return any(
            identity[0] == candidate[0]
            and identity[1][0] == candidate[1][0]
            and candidate[1][1] is not None
            for source in sourced_live
            for candidate in (cls._development_requirement_identity(source),)
        )

    @staticmethod
    def _remove_workspace_dependency_group(document: t.Cli.TomlDocument) -> None:
        """Drop the retired git-pinned ``workspace`` dependency group.

        The root's canonical dev group requests declared package members and
        their groups/extras; its path sources select local checkouts. A second
        membership group would be a competing generated owner.
        """
        groups = u.Cli.toml_table_child(document, c.Infra.DEPENDENCY_GROUPS)
        if groups is not None:
            u.Cli.toml_remove_key_if_present(groups, "workspace")

    @staticmethod
    def _validate_dependency_provenance(
        document: t.Cli.TomlDocument,
        *,
        workspace: p.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Require one internal dependency provenance for the active topology.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        payload = u.Cli.toml_as_mapping(document)
        if payload is None:
            return r[bool].fail("pyproject document is not a TOML mapping")
        project = payload.get(c.Infra.PROJECT)
        if not isinstance(project, Mapping):
            return r[bool].fail("pyproject content must define [project]")
        member_names = frozenset(
            member.distribution for member in workspace.subprojects
        )
        raw_values = FlextInfraUtilitiesPyprojectRequirements._raw_requirement_values(
            payload,
        )
        for requirement in raw_values:
            dependency_name = FlextInfraUtilitiesDependencies.dep_name(
                requirement,
            )
            if dependency_name is None or dependency_name not in member_names:
                continue
            provenance = FlextInfraUtilitiesPyprojectRequirements._member_provenance(
                dependency_name,
                requirement,
                workspace,
            )
            if provenance.failure:
                return r[bool].from_failure(provenance)
        return r[bool].ok(value=True)

    @staticmethod
    def _raw_requirement_values(payload: t.JsonMapping) -> t.StrSequence:
        """Collect every requirement line the document declares.

        Returns:
            The resulting ``t.StrSequence``.

        """
        raw_values: list[str] = []
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, Mapping):
            for key in (c.Infra.DEPENDENCIES, c.Infra.OPTIONAL_DEPENDENCIES):
                value = project.get(key)
                if isinstance(value, Mapping):
                    for group in value.values():
                        raw_values.extend(u.Cli.toml_as_string_list(group))
                else:
                    raw_values.extend(u.Cli.toml_as_string_list(value))
        groups = payload.get(c.Infra.DEPENDENCY_GROUPS)
        if isinstance(groups, Mapping):
            declared = m.Infra.DependencyGroupDeclarations.model_validate(
                {"dependency-groups": groups},
            )
            raw_values.extend(
                entry
                for group in declared.dependency_groups.values()
                for entry in group
                if isinstance(entry, str)
            )
        return tuple(raw_values)

    @staticmethod
    def _member_provenance(
        dependency_name: str,
        requirement: str,
        workspace: p.Infra.WorkspaceSpec,
    ) -> p.Result[bool]:
        """Require one member's requirement provenance to match its manifest.

        The manifest owns the Git URL; the requirement keeps its exact branch
        or locked revision in both root and standalone contexts.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        member = next(
            (
                item
                for item in workspace.subprojects
                if item.distribution == dependency_name
            ),
            None,
        )
        if member is not None and not member.url.startswith("https://"):
            return r[bool].fail(
                "internal dependency manifest provenance must be HTTPS: "
                f"{dependency_name} ({member.url})",
            )
        if member is None or "@" not in requirement.partition(";")[0]:
            return r[bool].ok(value=True)
        declared = FlextInfraUtilitiesRepository.declared_git_source(requirement)
        if declared.failure:
            return r[bool].from_failure(declared)
        if declared.value[0] != member.url:
            return r[bool].fail(
                f"internal dependency Git URL differs from manifest: {dependency_name}",
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraUtilitiesPyprojectRequirements"]
