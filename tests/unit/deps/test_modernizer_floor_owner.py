"""Observe dependency floor ownership through the public modernizer service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import Version
from pydantic import ValidationError

from flext_infra import config
from flext_infra.deps import FlextInfraPyprojectModernizer
from tests import c, m, tm, u


class TestsFlextInfraModernizerFloorOwner:
    """Require local ownership, validated input, and comment-preserving writes."""

    @staticmethod
    def _source(root: Path) -> Path:
        return root / c.Infra.CODEGEN_CONFIG_DIR / c.Infra.CODEGEN_CONFIG_FILENAME

    @staticmethod
    def _run(root: Path) -> int:
        return FlextInfraPyprojectModernizer(
            repository_root=root,
            apply_changes=True,
            rewrite_constraints=True,
            skip_comments=True,
            skip_check=True,
        ).run()

    @staticmethod
    def _declare_member(root: Path, member_path: Path) -> None:
        repository = u.Tests.repository_ref("floor-workspace")
        member = u.Tests.repository_ref(config.Infra.name, path=member_path)
        manifest = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            members=(member,),
        )
        path = u.Infra.workspace_manifest_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        u.Cli.yaml_dump(path, manifest.model_dump(mode="json")).unwrap()

    @pytest.mark.parametrize("member_path", [None, Path("tooling/provider")])
    def test_rewrite_uses_declared_local_owner(
        self,
        modernizer_workspace: Path,
        member_path: Path | None,
    ) -> None:
        """Update the declared SSOT from real installed versions exactly once."""
        source = self._source(modernizer_workspace)
        versions = u.Infra.resolved_dependency_versions()
        requirement, name = next(
            (requirement, name)
            for profile in config.Infra.codegen.scaffold.project.dependency_profiles
            for requirement in profile.runtime
            if (name := u.Infra.dep_name(requirement)) in versions
        )
        tm.that(name, eq=u.Infra.dep_name(requirement))
        name = tm.not_none(name)
        original = source.read_text(encoding="utf-8")
        # ``>=0`` is a textual prefix of every 0.x floor the rewrite produces
        # (``>=0.8.0``), so the stale sentinel must not prefix a real release.
        stale = f"{name}>=0.0.0"
        source.write_text(
            original.replace(requirement, stale, 1) + "\n# Keep owner annotation.\n",
            encoding="utf-8",
        )
        if member_path is not None:
            member_source = self._source(modernizer_workspace / member_path)
            member_source.parent.mkdir(parents=True)
            source.rename(member_source)
            self._declare_member(modernizer_workspace, member_path)
            source = member_source

        tm.that(self._run(modernizer_workspace), eq=0)

        rendered = source.read_text(encoding="utf-8")
        tm.that(rendered, has=f"{name}>={versions[name]}")
        tm.that(rendered, lacks=stale)
        tm.that(rendered, has="# Keep owner annotation.")
        tm.that(self._run(modernizer_workspace), eq=0)
        tm.that(source.read_text(encoding="utf-8"), eq=rendered)
        if member_path is not None:
            tm.that(self._source(modernizer_workspace).exists(), eq=False)

    def test_upgrade_preserves_unowned_schema_and_comments(
        self,
        modernizer_workspace: Path,
    ) -> None:
        """Upgrade floors independently of unrelated generator-schema changes."""
        versions = u.Infra.resolved_dependency_versions()
        profile, name = next(
            (profile, name)
            for profile in config.Infra.codegen.scaffold.project.dependency_profiles
            for requirement in profile.runtime
            if (name := u.Infra.dep_name(requirement)) in versions
        )
        name = tm.not_none(name)
        stale = f"{name}>=0.0.0"
        content = (
            "# Preserve owner annotation.\n"
            "Infra:\n"
            "  codegen:\n"
            "    toolchain: # Previous generator schema.\n"
            "      worktree_environment_directory: .legacy-env\n"
            "    scaffold:\n"
            "      project:\n"
            "        dependency_profiles:\n"
            f"          - upstream: {profile.upstream}\n"
            "            runtime:\n"
            f"              - {stale} # Preserve requirement annotation.\n"
        )
        source = self._source(modernizer_workspace)
        source.write_text(content, encoding="utf-8")

        tm.that(self._run(modernizer_workspace), eq=0)

        rendered = source.read_text(encoding="utf-8")
        tm.that(rendered, eq=content.replace(stale, f"{name}>={versions[name]}"))
        tm.that(self._run(modernizer_workspace), eq=0)
        tm.that(source.read_text(encoding="utf-8"), eq=rendered)

    @pytest.mark.parametrize(
        "content",
        [
            "Infra: [broken\n",
            (
                "Infra:\n  codegen:\n    scaffold:\n      project:\n"
                "        dependency_profiles: []\n"
            ),
            (
                "Infra:\n  codegen:\n    scaffold:\n      project:\n"
                "        dependency_profiles:\n"
                "          - upstream: example\n"
                "            runtime: []\n"
            ),
            (
                "Infra:\n  codegen:\n    scaffold:\n      project:\n"
                "        dependency_profiles:\n"
                "          - upstream: example\n"
                "            runtime: [example>=0]\n"
                "          - upstream: example\n"
                "            runtime: [17]\n"
            ),
        ],
    )
    def test_malformed_owned_config_raises_without_writing(
        self,
        modernizer_workspace: Path,
        content: str,
    ) -> None:
        """An owned invalid document cannot become a successful empty update."""
        source = self._source(modernizer_workspace)
        source.write_text(content, encoding="utf-8")

        with pytest.raises(
            ValueError,
            match=r"codegen|scaffold|dependency_profiles|flow sequence|runtime",
        ):
            self._run(modernizer_workspace)

        tm.that(source.read_text(encoding="utf-8"), eq=content)

    @pytest.mark.parametrize("field", ["runtime", "codegen"])
    def test_invalid_requirement_policy_preserves_all_files(
        self,
        modernizer_workspace: Path,
        field: str,
    ) -> None:
        """Validate every declaration before writing even an earlier valid floor."""
        source = self._source(modernizer_workspace)
        versions = u.Infra.resolved_dependency_versions()
        name = next(iter(versions))
        invalid = "example>=broken"
        runtime = invalid if field == "runtime" else "example>=0"
        codegen = f"            codegen: [{invalid}]\n" if field == "codegen" else ""
        content = (
            "Infra:\n  codegen:\n    scaffold:\n      project:\n"
            "        dependency_profiles:\n"
            "          - upstream: example\n"
            f"            runtime: [{name}>=0]\n"
            "          - upstream: invalid-policy\n"
            f"            runtime: [{runtime}]\n"
            f"{codegen}"
        )
        source.write_text(content, encoding="utf-8")
        pyproject = modernizer_workspace / c.PYPROJECT_FILENAME
        original_pyproject = pyproject.read_bytes()

        with pytest.raises(ValidationError, match=field) as captured:
            self._run(modernizer_workspace)

        tm.that(
            isinstance(captured.value.errors()[0]["ctx"]["error"], InvalidRequirement),
            eq=True,
        )
        tm.that(source.read_text(encoding="utf-8"), eq=content)
        tm.that(pyproject.read_bytes(), eq=original_pyproject)

    def test_upgrade_preserves_compatible_release_and_direct_source(
        self,
        modernizer_workspace: Path,
    ) -> None:
        """Real installed floors preserve the source policy and converge on rerun."""
        versions = u.Infra.resolved_dependency_versions()
        name, version = next(
            (name, version)
            for name, version in versions.items()
            if u.Infra.constraint_specifier(version)
        )
        resolved = Version(version)
        release = resolved.release
        compatibility = f"{release[0]}.{release[1] if len(release) > 1 else 0}"
        if resolved.epoch:
            compatibility = f"{resolved.epoch}!{compatibility}"
        original = Requirement(f"{name}[feature]~={compatibility}; os_name == 'posix'")
        direct = f"{name}@https://example.org/package.whl"
        content = (
            "Infra:\n  codegen:\n    scaffold:\n      project:\n"
            "        dependency_profiles:\n"
            "          - upstream: example\n"
            f"            runtime:\n              - {original}\n"
            f"            codegen:\n              - {direct}\n"
        )
        source = self._source(modernizer_workspace)
        source.write_text(content, encoding="utf-8")

        tm.that(self._run(modernizer_workspace), eq=0)

        payload = u.Cli.yaml_safe_load(source).unwrap()
        infra = u.Cli.json_as_mapping(payload.get("Infra"))
        codegen = u.Cli.json_as_mapping(infra.get("codegen"))
        scaffold = u.Cli.json_as_mapping(codegen.get("scaffold"))
        project = u.Cli.json_as_mapping(scaffold.get("project"))
        profiles = u.Cli.json_as_sequence(project.get("dependency_profiles"))
        profile = m.Infra.ScaffoldDependencyProfileSpec.model_validate(profiles[0])
        parsed = Requirement(profile.runtime[0])
        tm.that(parsed.extras, eq=original.extras)
        tm.that(parsed.marker, eq=original.marker)
        tm.that(profile.codegen, eq=(direct,))
        tm.that(parsed.specifier.contains(version), eq=True)
        tm.that(str(parsed.specifier), has=f"~={compatibility}")
        tm.that(str(parsed.specifier), has=u.Infra.constraint_specifier(version))
        rendered = source.read_bytes()
        tm.that(self._run(modernizer_workspace), eq=0)
        tm.that(source.read_bytes(), eq=rendered)

    def test_consumer_without_owner_leaves_external_config_untouched(
        self,
        modernizer_workspace: Path,
    ) -> None:
        """An unrelated consumer never selects a sibling or installed SSOT."""
        source = self._source(modernizer_workspace)
        external = modernizer_workspace.parent / c.Infra.CODEGEN_CONFIG_FILENAME
        source.rename(external)
        original = external.read_bytes()
        consumer = "Infra:\n  codegen: {}\n"
        source.write_text(consumer, encoding="utf-8")

        tm.that(self._run(modernizer_workspace), eq=0)

        tm.that(external.read_bytes(), eq=original)
        tm.that(source.read_text(encoding="utf-8"), eq=consumer)

    def test_missing_declared_owner_raises(self, modernizer_workspace: Path) -> None:
        """A declared infrastructure owner must carry its configuration."""
        source = self._source(modernizer_workspace)
        source.rename(modernizer_workspace.parent / source.name)
        self._declare_member(modernizer_workspace, Path("tooling/provider"))

        with pytest.raises(ValueError, match=c.Infra.CODEGEN_CONFIG_FILENAME):
            self._run(modernizer_workspace)

    def test_external_configuration_symlink_raises(
        self,
        modernizer_workspace: Path,
    ) -> None:
        """A local-looking config cannot rewrite a different checkout."""
        source = self._source(modernizer_workspace)
        external = modernizer_workspace.parent / source.name
        source.rename(external)
        source.symlink_to(external)
        original = external.read_bytes()

        with pytest.raises(ValueError, match="outside workspace"):
            self._run(modernizer_workspace)

        tm.that(external.read_bytes(), eq=original)
