"""Lock-derived dependency floors written back to the codegen SSOT (flext-gzfd2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config, u

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraDepsFloorProfileWriter:
    """Rewrite dependency_profiles floors from the resolved uv.lock state."""

    @classmethod
    def rewrite_profiles_from_lock(
        cls,
        *,
        locked_versions: t.MappingKV[str, str],
        internal_names: t.StrSequence,
    ) -> t.StrSequence:
        """Update dependency_profiles in config/codegen.yaml with raised floors.

        Returns a list of change descriptions for the deps report.
        """
        # Resolve the config/codegen.yaml path through the loaded config's own dir
        ssot_path = type(config).ssot_config_dir() / "codegen.yaml"

        # Round-trip load preserves comments and ordering
        loaded = u.Cli.yaml_roundtrip_load_map(ssot_path)
        if loaded.failure:
            u.Cli.error(f"failed to load {ssot_path}: {loaded.failure}")
            return ()

        document = loaded.value

        # Navigate to Infra.codegen.scaffold.project.dependency_profiles
        infra = document.get("Infra")
        if not infra or not isinstance(infra, dict):
            u.Cli.error("Infra section missing in codegen.yaml")
            return ()
        codegen = infra.get("codegen")
        if not codegen or not isinstance(codegen, dict):
            u.Cli.error("Infra.codegen section missing in codegen.yaml")
            return ()
        scaffold = codegen.get("scaffold")
        if not scaffold or not isinstance(scaffold, dict):
            u.Cli.error("Infra.codegen.scaffold section missing in codegen.yaml")
            return ()
        project = scaffold.get("project")
        if not project or not isinstance(project, dict):
            u.Cli.error("Infra.codegen.scaffold.project section missing in codegen.yaml")
            return ()
        profiles = project.get("dependency_profiles")
        if not profiles or not isinstance(profiles, list):
            u.Cli.error("dependency_profiles missing or not a list in codegen.yaml")
            return ()

        changes: t.MutableSequenceOf[str] = []

        # Rewrite each profile's runtime and codegen requirement lists
        for profile in profiles:
            if not isinstance(profile, dict):
                continue
            upstream = str(profile.get("upstream", ""))
            runtime_reqs = profile.get("runtime")
            codegen_reqs = profile.get("codegen")
            for key_name, reqs in (("runtime", runtime_reqs), ("codegen", codegen_reqs)):
                if not isinstance(reqs, list):
                    continue
                for idx, req in enumerate(reqs):
                    if not isinstance(req, str):
                        continue
                    rewritten = u.Infra.rewrite_requirement_constraint(
                        req,
                        locked_versions=locked_versions,
                        internal_names=internal_names,
                    )
                    if rewritten is not None and rewritten != req:
                        # Update in place preserves surrounding comments/keys
                        reqs[idx] = rewritten
                        changes.append(f"profile({upstream}).{key_name}: {req} -> {rewritten}")

        if not changes:
            return ()

        # Dump back with comments preserved
        dumped = u.Cli.yaml_roundtrip_dump_text(document)
        if dumped.failure:
            u.Cli.error(f"failed to dump codegen.yaml: {dumped.failure}")
            return ()

        # Atomic write
        write_result = u.Cli.atomic_write_text_file(ssot_path, dumped.value)
        if write_result.failure:
            u.Cli.error(f"failed to write {ssot_path}: {write_result.failure}")
            return ()

        return tuple(changes)


__all__: list[str] = ["FlextInfraDepsFloorProfileWriter"]
