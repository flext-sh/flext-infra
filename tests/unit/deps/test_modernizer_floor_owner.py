"""Observe target-owned dependency floors through the public modernizer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest
from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import Version

from flext_infra.deps import FlextInfraPyprojectModernizer
from tests import c, t, tm, u


class TestsFlextInfraModernizerFloorOwner:
    """Real resolution updates only authored requirements of the selected target."""

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
    def _resolved_requirement() -> t.Pair[str, str]:
        """Select an actually provisioned package with a valid release floor.

        Returns:
            The resulting ``t.Pair[str, str]``.
        """
        return next(
            (name, version)
            for name, version in u.Infra.resolved_dependency_versions().items()
            if u.Infra.rewrite_requirement_constraint(
                f"{name}>=0.0.0",
                resolved_versions={name: version},
            )
            is not None
        )

    def test_rewrite_preserves_other_owners_and_converges(
        self,
        modernizer_workspace: Path,
    ) -> None:
        """Runtime, optional and group floors retain comments and sibling inputs."""
        name, version = self._resolved_requirement()
        path = modernizer_workspace / c.PYPROJECT_FILENAME
        source = modernizer_workspace / "config" / c.Infra.CODEGEN_CONFIG_FILENAME
        source_before = source.read_bytes()
        sibling = modernizer_workspace.parent / "other-project.toml"
        sibling.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        sibling_before = sibling.read_bytes()
        stale = f"{name}>=0.0.0"
        path.write_text(
            path.read_text(encoding="utf-8")
            + f'dependencies = ["{stale}"] # Keep requirement annotation.\n'
            + f'[project.optional-dependencies]\nfeature = ["{stale}"]\n'
            + f'[dependency-groups]\ndev = ["{stale}"]\n'
            + 'examples = [{include-group = "dev"}]\n',
            encoding="utf-8",
        )

        tm.that(self._run(modernizer_workspace), eq=0)

        rendered = path.read_text(encoding="utf-8")
        expected = tm.not_none(
            u.Infra.rewrite_requirement_constraint(
                stale,
                resolved_versions={name: version},
            )
        )
        for keys in (
            ("project", "dependencies"),
            ("project", "optional-dependencies", "feature"),
            ("dependency-groups", "dev"),
        ):
            tm.that(u.Tests.toml_strings_at(rendered, *keys), eq=(expected,))
        tm.that(rendered, has="# Keep requirement annotation.")
        tm.that(source.read_bytes(), eq=source_before)
        tm.that(sibling.read_bytes(), eq=sibling_before)
        tm.that(self._run(modernizer_workspace), eq=0)
        tm.that(path.read_text(encoding="utf-8"), eq=rendered)

    @pytest.mark.parametrize("section", ["runtime", "development"])
    def test_invalid_requirement_leaves_the_target_untouched(
        self,
        modernizer_workspace: Path,
        section: str,
    ) -> None:
        """Validate every selected requirement before publishing earlier changes."""
        name, _version = self._resolved_requirement()
        path = modernizer_workspace / c.PYPROJECT_FILENAME
        requirements = f'["{name}>=0.0.0", "invalid>=broken"]'
        path.write_text(
            path.read_text(encoding="utf-8")
            + (
                f"dependencies = {requirements}\n"
                if section == "runtime"
                else f"[dependency-groups]\ndev = {requirements}\n"
            ),
            encoding="utf-8",
        )
        before = path.read_bytes()

        with pytest.raises(InvalidRequirement):
            self._run(modernizer_workspace)

        tm.that(path.read_bytes(), eq=before)

    def test_preserves_markers_extras_compatible_bounds_and_direct_source(
        self,
        modernizer_workspace: Path,
    ) -> None:
        """Resolved floors retain authored PEP 508 policy and source identity."""
        name, version = self._resolved_requirement()
        resolved = Version(version)
        compatibility = ".".join(str(part) for part in (*resolved.release, 0)[:2])
        if resolved.epoch:
            compatibility = f"{resolved.epoch}!{compatibility}"
        original = Requirement(f"{name}[feature]~={compatibility}; os_name == 'posix'")
        direct = f"{name} @ https://example.org/package.whl"
        path = modernizer_workspace / c.PYPROJECT_FILENAME
        path.write_text(
            path.read_text(encoding="utf-8")
            + f'dependencies = ["{original}"]\n'
            + f'[dependency-groups]\ndev = ["{direct}"]\n',
            encoding="utf-8",
        )

        tm.that(self._run(modernizer_workspace), eq=0)

        rendered = path.read_text(encoding="utf-8")
        parsed = Requirement(
            u.Tests.toml_strings_at(rendered, "project", "dependencies")[0]
        )
        tm.that(parsed.extras, eq=original.extras)
        tm.that(parsed.marker == original.marker, eq=True)
        tm.that(parsed.specifier.contains(version, prereleases=True), eq=True)
        tm.that(str(parsed.specifier), has=f"~={compatibility}")
        tm.that(
            u.Tests.toml_strings_at(rendered, "dependency-groups", "dev"), eq=(direct,)
        )
