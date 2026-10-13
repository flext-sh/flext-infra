"""Runtime-derived dependency floors written back to the codegen SSOT.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, u

if TYPE_CHECKING:
    from ruamel.yaml.comments import CommentedMap

    from flext_infra import t


class FlextInfraDepsFloorProfileWriter:
    """Rewrite dependency_profiles floors from the provisioned runtime."""

    @staticmethod
    def _source_paths(root: Path) -> t.SequenceOf[m.Cli.AtomicFileState]:
        """Elect writable source layers that actually declare dependency profiles.

        Returns:
            Captured configuration states owned by this operation's root.

        Raises:
            ValueError: If a declaring source escapes its owner, lacks captured
                bytes, or contains invalid dependency profiles.

        """
        root = root.resolve()
        captured = u.Infra.load_config_document_inputs(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        ).unwrap()
        sources: list[m.Cli.AtomicFileState] = []
        for source in captured.sources:
            if not source.path.is_relative_to(root):
                continue
            if not source.path.resolve().is_relative_to(root):
                message = (
                    "dependency floor configuration is outside its owner: "
                    f"{source.path}"
                )
                raise ValueError(message)
            if source.content is None:
                message = (
                    f"dependency floor source has no captured bytes: {source.path}"
                )
                raise ValueError(message)
            document = u.Infra.read_codegen_config_document(source.content).unwrap()
            profiles = u.Cli.json_walk_path(
                document,
                ("Infra", "codegen", "scaffold", "project", "dependency_profiles"),
            )
            if profiles is None:
                continue
            FlextInfraDepsFloorProfileWriter._validated_sections(document, source.path)
            sources.append(source)
        return tuple(sources)

    @classmethod
    def rewrite_profiles_from_resolution(
        cls,
        *,
        root: Path,
        resolved_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence,
    ) -> t.StrSequence:
        """Update dependency_profiles in the caller's local codegen owner.

        ``root`` is the modernizer's own declared ``--repository-root``.
        Only authenticated layers inside this root that explicitly declare
        profiles are writable. A consumer delta containing other settings
        carries no dependency-floor publication authority.

        Returns a list of change descriptions for the deps report.

        Returns:
            The resulting ``t.StrSequence``.

        """
        sources = cls._source_paths(root)
        if not sources:
            return ()
        changes: list[str] = []
        for source in sources:
            ssot_path = source.path
            document = cls._loaded_document(ssot_path)
            observed = u.Cli.atomic_read_binary_file_state(
                ssot_path, required=True
            ).unwrap()
            if observed != source:
                message = f"dependency floor source changed during read: {ssot_path}"
                raise ValueError(message)
            sections = cls._validated_sections(document, ssot_path)
            rewritten = cls._rewrite_profiles(
                sections,
                ssot_path,
                resolved_versions=resolved_versions,
                internal_names=internal_names,
            )
            if not rewritten:
                continue
            dumped = u.Cli.yaml_roundtrip_dump_text(document).unwrap()
            u.Cli.atomic_write_binary_file_guarded(
                source,
                dumped.encode(c.DEFAULT_ENCODING),
                permission_mode=source.mode,
            ).unwrap()
            changes.extend(rewritten)
        return tuple(changes)

    @staticmethod
    def _loaded_document(ssot_path: Path) -> CommentedMap:
        """Round-trip load the dependency floor owner document.

        Returns:
            The loaded comment-preserving mapping document.

        Raises:
            ValueError: If ``loaded.failure`` — a missing or unparseable owner is
                the same invalid-owner failure as a missing section: one
                ValueError contract, original cause chained.

        """
        loaded = u.Cli.yaml_roundtrip_load_map(ssot_path)
        if loaded.failure:
            raise ValueError(loaded.error) from loaded.exception
        return loaded.value

    @staticmethod
    def _validated_sections(
        document: t.MappingKV[str, t.JsonValue],
        ssot_path: Path,
    ) -> t.Pair[
        t.SequenceOf[t.JsonValue],
        t.SequenceOf[m.Infra.ScaffoldDependencyProfileSpec],
    ]:
        """Navigate to and validate the dependency-profile declaration sections.

        Returns:
            The ``(raw_profiles, validated_profiles)`` pair.

        Raises:
            ValueError: If Infra section missing in; or if Infra.codegen section
                missing in; or if Infra.codegen.scaffold section missing in; or if
                Infra.codegen.scaffold.project section missing in; or if
                dependency_profiles missing or not a list in.

        """
        # Navigate to Infra.codegen.scaffold.project.dependency_profiles
        infra = document.get("Infra")
        if not infra or not isinstance(infra, dict):
            message = f"Infra section missing in {ssot_path}"
            raise ValueError(message)
        codegen = infra.get("codegen")
        if not codegen or not isinstance(codegen, dict):
            message = f"Infra.codegen section missing in {ssot_path}"
            raise ValueError(message)
        scaffold = codegen.get("scaffold")
        if not scaffold or not isinstance(scaffold, dict):
            message = f"Infra.codegen.scaffold section missing in {ssot_path}"
            raise ValueError(message)
        project = scaffold.get("project")
        if not project or not isinstance(project, dict):
            message = f"Infra.codegen.scaffold.project section missing in {ssot_path}"
            raise ValueError(message)
        profiles = project.get("dependency_profiles")
        if not profiles or not isinstance(profiles, list):
            message = f"dependency_profiles missing or not a list in {ssot_path}"
            raise ValueError(message)
        # Dependency modernization precedes generation during an upgrade. Only
        # the profiles belong to this writer; unrelated sections may still use
        # the previous generator's schema. Validate every profile before edits.
        validated = tuple(
            m.Infra.ScaffoldDependencyProfileSpec.model_validate(profile)
            for profile in profiles
        )
        return (profiles, validated)

    @classmethod
    def _rewrite_profiles(
        cls,
        sections: t.Pair[
            t.SequenceOf[t.JsonValue],
            t.SequenceOf[m.Infra.ScaffoldDependencyProfileSpec],
        ],
        ssot_path: Path,
        *,
        resolved_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence,
    ) -> t.StrSequence:
        """Rewrite each profile's runtime and codegen requirement lists.

        Returns:
            One change description per rewritten requirement constraint.

        Raises:
            TypeError: If dependency profile must be a mapping in; or if ``not
                isinstance(reqs, list)``; or if ``not isinstance(req, str)``.

        """
        profiles, validated = sections
        changes: t.MutableSequenceOf[str] = []
        for profile, contract in zip(
            profiles,
            validated,
            strict=True,
        ):
            if not isinstance(profile, dict):
                message = f"dependency profile must be a mapping in {ssot_path}"
                raise TypeError(message)
            upstream = contract.upstream
            runtime_reqs = profile.get("runtime")
            codegen_reqs = profile.get("codegen", [])
            for key_name, reqs in (
                ("runtime", runtime_reqs),
                ("codegen", codegen_reqs),
            ):
                if not isinstance(reqs, list):
                    message = f"{upstream}.{key_name} must be a list in {ssot_path}"
                    raise TypeError(message)
                for idx, req in enumerate(reqs):
                    if not isinstance(req, str):
                        message = (
                            f"{upstream}.{key_name} requires strings in {ssot_path}"
                        )
                        raise TypeError(message)
                    rewritten = u.Infra.rewrite_requirement_constraint(
                        req,
                        resolved_versions=resolved_versions,
                        internal_names=internal_names,
                    )
                    if rewritten is not None and rewritten != req:
                        # Update in place preserves surrounding comments/keys
                        reqs[idx] = rewritten
                        changes.append(
                            f"profile({upstream}).{key_name}: {req} -> {rewritten}",
                        )
        return tuple(changes)


__all__: list[str] = ["FlextInfraDepsFloorProfileWriter"]
