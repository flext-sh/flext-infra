"""Behavior tests for pyproject overlay ownership of development requirements.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, tm, u
from tests.unit.pyproject_conform_topology_support import (
    TestsFlextInfraPyprojectConformTopologySupport,
)


class TestsFlextInfraPyprojectConformOverlayOwnership(
    TestsFlextInfraPyprojectConformTopologySupport,
):
    """Prove overlay-owned development entries are preserved and re-derived."""

    @pytest.mark.parametrize("attached", [False, True])
    def test_retired_development_requirements_do_not_reappear(
        self,
        tmp_path: Path,
        *,
        attached: bool,
    ) -> None:
        """The public generator removes retired items and preserves other inputs."""
        retired = config.Infra.codegen.scaffold.project.retired_dev
        retained = "fixture-retained-development"
        while retained in retired:
            retained += "-extra"
        entries = ", ".join(f'"{name}"' for name in (*retired, retained))
        source = (
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            f"[dependency-groups]\ndev = [{entries}]\n"
        )
        workspace = self._workspace(role=self._ROLE.STANDALONE)
        expected = {retained}
        if attached:
            member = self._member_ref("fixture-retirement-member", "member")
            workspace = self._workspace(member)
            member_file = tmp_path / member.path / c.PYPROJECT_FILENAME
            member_file.parent.mkdir()
            member_file.write_text(
                '[project]\nname = "fixture-retirement-member"\nversion = "0.1.0"\n'
                f"[dependency-groups]\ndev = [{entries}]\n",
                encoding="utf-8",
            )
            expected.add(self._inline_requirement(member))
        options = self._conform_options(tmp_path, workspace)
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            )
        )
        tm.that(
            set(u.Tests.toml_strings_at(rendered, "dependency-groups", "dev")),
            eq=expected,
        )
        repeated = tm.ok(
            u.Infra.pyproject_conform(
                rendered,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            )
        )
        tm.that(repeated, eq=rendered)

    def test_removed_member_environment_drops_only_owned_dev_entries(
        self,
        tmp_path: Path,
    ) -> None:
        """Membership/group removal preserves real CUSTOM constraints and bootstrap."""
        provider = self._member_ref("acme-engine", "libraries/engine")
        consumer = self._member_ref("acme-driver", "plugins/driver")
        workspace = self._workspace(provider, consumer)
        for member in workspace.subprojects:
            path = tmp_path / member.path / c.PYPROJECT_FILENAME
            path.parent.mkdir(parents=True)
            path.write_text(
                f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n'
                '[dependency-groups]\nqa = ["hypothesis>=6"]\n',
                encoding="utf-8",
            )
        custom_member = self._inline_requirement(provider)
        custom_bound = 'idna>=3; python_version >= "3.13"'
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            'dependencies = ["httpx>=0.27"]\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\n'
            f"dev = [\"{custom_member}\", '{custom_bound}']\n"
        )
        options = self._conform_options(tmp_path, workspace)
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        (tmp_path / consumer.path / c.PYPROJECT_FILENAME).write_text(
            f'[project]\nname = "{consumer.distribution}"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        remaining = self._workspace(consumer)
        options = self._conform_options(tmp_path, remaining)
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=remaining,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        dev = set(u.Tests.toml_strings_at(second, "dependency-groups", "dev"))
        tm.ok(custom_member in dev)
        tm.ok(custom_bound in dev)
        tm.fail("hypothesis>=6" in dev)
        tm.ok(self._inline_requirement(consumer) in dev)
        tm.that(
            u.Tests.toml_strings_at(second, "dependency-groups", "codegen"),
            eq=("build>=1",),
        )
        tm.fail("sources" in u.Tests.toml_table_at(second, "tool", "uv"))
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    second,
                    workspace=remaining,
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                ),
            ),
            eq=second,
        )

    def test_overlay_preserves_custom_values_and_rederives_owned_members(
        self,
        tmp_path: Path,
    ) -> None:
        """The real overlay consumes ownership comments before the next render."""
        member = self._member_ref("acme-engine", "libraries/engine")
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n',
            encoding="utf-8",
        )
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\n'
            'dev = ["hypothesis>=6"]\n'
        )
        workspace = self._workspace(member)
        options = self._conform_options(tmp_path, workspace)
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, first))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                merged,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(
            second,
            eq=first,
            msg="\n".join(unified_diff(first.splitlines(), second.splitlines())),
        )
        # A later explicit CUSTOM duplicate does not inherit the owned marker.
        custom_member = self._inline_requirement(member)
        live = first.replace(
            "dev = [\n",
            f'dev = [\n    "{custom_member}",\n',
            1,
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, live))
        tm.that(
            set(u.Tests.toml_strings_at(merged, "dependency-groups", "dev")),
            eq={"hypothesis>=6", custom_member},
        )

    def test_overlay_preserves_custom_codegen_and_rederives_member_groups(
        self,
        tmp_path: Path,
    ) -> None:
        """Template composition retains CUSTOM codegen additions and provenance."""
        member = self._member_ref("acme-engine", "libraries/engine")
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n'
            '[dependency-groups]\ndev = ["hypothesis>=6"]\n',
            encoding="utf-8",
        )
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["build>=1"]\ndev = []\n'
        )
        template = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ncodegen = ["ruff>=1"]\ndev = []\n'
        )
        workspace = self._workspace(member)
        options = self._conform_options(tmp_path, workspace)
        initial = tm.ok(u.Infra.overlay_preserved(template, source))
        tm.that(
            set(u.Tests.toml_strings_at(initial, "dependency-groups", "codegen")),
            eq={"build>=1", "ruff>=1"},
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                initial,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        merged = tm.ok(u.Infra.overlay_preserved(template, first))
        tm.that(
            set(u.Tests.toml_strings_at(merged, "dependency-groups", "codegen")),
            eq={"build>=1", "ruff>=1"},
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                merged,
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        tm.that(
            second,
            eq=first,
            msg="\n".join(unified_diff(first.splitlines(), second.splitlines())),
        )

    def test_marked_same_value_outside_dev_preserves_custom_dev(self) -> None:
        """An ownership-looking comment in QA cannot own a DEV occurrence."""
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            '[dependency-groups]\ndev = ["hypothesis>=6"]\n'
            'qa = [\n    "hypothesis>=6", # flext: derived member environment\n]\n'
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )
        tm.that(
            u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, source))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    first,
                    workspace=self._workspace(),
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                ),
            ),
            eq=first,
        )

    def test_full_line_comments_do_not_become_owned_dev_items(self) -> None:
        """Commented-out values and multiple hashes do not enter the item stream."""
        source = (
            '[project]\nname = "workspace"\nversion = "1.0.0"\n'
            "[dependency-groups]\ndev = [\n"
            '    # "hypothesis>=6", # flext: derived member environment\n'
            '    # "retired-generated>=1", # flext: derived member environment\n'
            '    "hypothesis>=6", # note # flext: derived member environment\n'
            "]\n"
        )
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
            ),
        )
        tm.that(
            u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )
        merged = tm.ok(u.Infra.overlay_preserved(source, source))
        tm.that(
            u.Tests.toml_strings_at(merged, "dependency-groups", "dev"),
            eq=("hypothesis>=6",),
        )

    def test_unmarked_duplicate_survives_direct_overlay_removal_and_fixed_point(
        self,
        tmp_path: Path,
    ) -> None:
        """Ownership is per occurrence throughout both generation entry paths."""
        member = self._member_ref("acme-driver", "plugins/driver")
        path = tmp_path / member.path / c.PYPROJECT_FILENAME
        path.parent.mkdir(parents=True)
        path.write_text(
            f'[project]\nname = "{member.distribution}"\nversion = "1.0.0"\n'
            '[dependency-groups]\nqa = ["hypothesis>=6"]\n',
            encoding="utf-8",
        )
        seed = '[project]\nname = "workspace"\nversion = "1.0.0"\n'
        options = self._conform_options(tmp_path, self._workspace(member))
        owned = tm.ok(
            u.Infra.pyproject_conform(
                seed,
                workspace=self._workspace(member),
                required_dev_dependencies=(),
                uv_resolution=self._toolchain_resolution(),
                options=options,
            ),
        )
        live = owned.replace("dev = [\n", 'dev = [\n    "hypothesis>=6",\n', 1)
        for entry in (live, tm.ok(u.Infra.overlay_preserved(seed, live))):
            first = tm.ok(
                u.Infra.pyproject_conform(
                    entry,
                    workspace=self._workspace(),
                    required_dev_dependencies=(),
                    uv_resolution=self._toolchain_resolution(),
                    options=options,
                ),
            )
            tm.that(
                u.Tests.toml_strings_at(first, "dependency-groups", "dev"),
                eq=("hypothesis>=6",),
            )
            for repeat in (first, tm.ok(u.Infra.overlay_preserved(seed, first))):
                actual = tm.ok(
                    u.Infra.pyproject_conform(
                        repeat,
                        workspace=self._workspace(),
                        required_dev_dependencies=(),
                        uv_resolution=self._toolchain_resolution(),
                        options=options,
                    )
                )
                tm.that(
                    actual,
                    eq=first,
                    msg="\n".join(
                        unified_diff(first.splitlines(), actual.splitlines())
                    ),
                )
