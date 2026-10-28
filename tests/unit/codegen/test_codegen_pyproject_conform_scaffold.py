"""Public behavior tests for pyproject provenance, idempotence and scaffold policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, t, tm, u
from tests.unit.codegen.pyproject_conform_support import (
    TestsFlextInfraPyprojectConformSupport,
)


class TestsFlextInfraCodegenPyprojectConformScaffold(
    TestsFlextInfraPyprojectConformSupport
):
    """Pyproject conformance: provenance, idempotence and scaffold policy."""

    def test_standalone_requires_declared_git_source(self) -> None:
        """A source-less internal dependency outside the workspace overlay fails.

        The workspace attaches only flext-core, whose declaration supplies the
        source; the infrastructure distribution is internal and unattached.
        """
        unattached = config.Infra.codegen.infra_repository.distribution
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{unattached}"]\n',
            workspace=self._workspace(role=c.Infra.MakeProfile.STANDALONE),
            required_dev_dependencies=(),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        tm.fail(result, has="internal dependency declares no direct git source")

    def test_standalone_canonicalizes_the_declared_git_source(self) -> None:
        """The declared requirement line is the only URL and branch authority."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        member = workspace.subprojects[0]
        declared = (
            f"{member.distribution} @ git+{member.url}@{u.Tests.provider_branch()}"
        )
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{declared}"]\n',
            workspace=workspace,
            required_dev_dependencies=(),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        rendered = tm.ok(result)
        tm.that(
            u.Tests.toml_strings_at(rendered, "project", "dependencies"),
            eq=(declared,),
        )

    def test_conformance_deletes_empty_uv_constraint_key(self) -> None:
        """An empty declared constraint set removes the retained key entirely."""
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={"uv_link_mode": "copy", "uv_constraint_dependencies": ()},
        )
        source = """[project]
name = "external-consumer"
dependencies = ["requests>=2"]

[tool.uv]
constraint-dependencies = ["uv>=0"]
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=self._workspace(),
                required_dev_dependencies=(),
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )

        uv_config = u.Tests.toml_table_at(conformed, "tool", "uv")
        tm.that(uv_config["link-mode"], eq=toolchain.uv_link_mode)
        tm.ok("constraint-dependencies" not in uv_config)

    def test_standalone_rejects_non_https_manifest_provenance(self) -> None:
        """Test standalone rejects non https manifest provenance."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        member = workspace.subprojects[0]
        declared = (
            f"{member.distribution} @ git+{member.url}@{u.Tests.provider_branch()}"
        )
        invalid_workspace = workspace.model_copy(
            update={
                "subprojects": (
                    member.model_copy(
                        update={"url": "git@github.com:flext-sh/flext-core.git"},
                    ),
                ),
            },
        )
        result = u.Infra.pyproject_conform(
            f'[project]\nname = "external-consumer"\ndependencies = ["{declared}"]\n',
            workspace=invalid_workspace,
            required_dev_dependencies=(),
            uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
        )
        tm.fail(result, has="internal dependency manifest provenance must be HTTPS")

    def test_full_conformance_is_idempotent_without_uv_version_pin(self) -> None:
        """Test full conformance is idempotent without uv version pin."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        toolchain = config.Infra.codegen.toolchain.model_copy(
            update={"uv_link_mode": "copy"},
        )
        required_dev = self._detached_dev_floors()
        declared_member_source = (
            f"flext-core @ git+{workspace.subprojects[0].url}@"
            f"{u.Tests.provider_branch()}"
        )
        source = f"""[project]
name = "external-consumer"
dependencies = ["{declared_member_source}", "requests>=2"]

[dependency-groups]
dev = ["custom-tool>=1"]

[tool.uv]
required-version = ">=0"
exclude-newer = "7 days"
exclude-newer-package = {{ cryptography = false }}
[tool.pyrefly]
python-interpreter-path = "../.venv/bin/python"
"""
        first = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=required_dev,
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )
        second = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=workspace,
                required_dev_dependencies=required_dev,
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )
        uv = u.Tests.toml_table_at(first, "tool", "uv")
        tm.that(second, eq=first)
        tm.that(uv["link-mode"], eq=toolchain.uv_link_mode)
        # The supply-chain cooldown is exterminated fleet-wide (flext-fphyv):
        # uv resolves every version published up to now, and a removed
        # declaration exterminates the keys everywhere (flext-gzfd2 class), so
        # pre-existing projections carrying the old cap converge to no keys.
        tm.ok("exclude-newer" not in uv)
        tm.ok("exclude-newer-package" not in uv)
        tm.ok("required-version" not in uv)
        tm.that(
            "python-interpreter-path"
            not in u.Tests.toml_table_at(first, "tool", "pyrefly"),
            eq=True,
        )
        dev_group = u.Tests.toml_strings_at(first, "dependency-groups", "dev")
        tm.ok("custom-tool>=1" in dev_group)
        # Why (CodeRabbit 3742335224): assert the exact requirement the typed
        # SSOT declares, not merely the package name. A name-only assertion
        # stays green even if the generated floor drifts away from the owner.
        # Why (hq-36xk): the requirement was selected by hardcoding the
        # "pre-commit" package name, which 30b4a37f5 removed from the SSOT when
        # it retired the legacy work lifecycle. `next()` then raised
        # StopIteration and the test failed for a reason unrelated to what it
        # measures. The expectation now derives from the same SSOT sequence
        # production reads, so it survives any legitimate change to that set.
        # A declared floor reaches the rendered group verbatim UNLESS it names a
        # workspace project, which dependency provenance rewrites to its tracked
        # integration-branch source. Asserting by package name keeps both shapes
        # in scope without re-encoding either.
        rendered_names = {u.Infra.dep_name(requirement) for requirement in dev_group}
        for requirement in required_dev:
            tm.ok(u.Infra.dep_name(requirement) in rendered_names)
        tm.that(
            u.Tests.toml_strings_at(first, "project", "dependencies")[0],
            eq=(
                f"{workspace.subprojects[0].distribution} @ "
                f"git+{workspace.subprojects[0].url}@{u.Tests.provider_branch()}"
            ),
        )

    def test_conformance_never_writes_the_project_version(self) -> None:
        """The release protocol is the only version writer; conform reads only."""
        workspace = self._workspace().model_copy(
            update={"project": u.Tests.project_spec("external-consumer")},
        )
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                '[project]\nname = "external-consumer"\n'
                'version = "0.0.1"\ndependencies = []\n',
                workspace=workspace,
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        tm.that(u.Tests.toml_table_at(conformed, "project")["version"], eq="0.0.1")

    def test_ssot_required_dev_floor_replaces_stale_same_name_pin(self) -> None:
        """Toolchain required_dev floors win over older same-package member pins."""
        workspace = self._workspace()
        toolchain = config.Infra.codegen.toolchain
        source = """[project]
name = "external-consumer"
dependencies = []

[dependency-groups]
dev = ["rumdl>=0.2.46", "custom-tool>=1"]
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=("rumdl>=0.2.45",),
                uv_resolution=self._uv_resolution(toolchain),
            ),
        )
        dev_group = u.Tests.toml_strings_at(conformed, "dependency-groups", "dev")
        tm.ok("rumdl>=0.2.45" in dev_group)
        tm.ok("rumdl>=0.2.46" not in dev_group)
        tm.ok("custom-tool>=1" in dev_group)

    def test_conform_retires_dependency_edge_suppression(self) -> None:
        """Conformance preserves real declared edges and removes retired suppression."""
        workspace = self._workspace(role=c.Infra.MakeProfile.STANDALONE)
        dependency = "example-dependency>=1"
        exclusion = '{ package = {name="example-dependency"}, dependencies=["other"] }'
        source = f"""[project]
name = "{workspace.repository.distribution}"
dependencies = ["{dependency}"]
[tool.uv]
exclude-dependencies = [{exclusion}]
"""
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=self._detached_dev_floors(),
                uv_resolution=self._uv_resolution(
                    config.Infra.codegen.toolchain,
                ),
            ),
        )
        uv = u.Tests.toml_table_at(conformed, "tool", "uv")
        tm.ok("exclude-dependencies" not in uv)
        project = u.Tests.toml_table_at(conformed, "project")
        tm.ok(dependency in u.Tests.toml_strings(project["dependencies"]))

    @staticmethod
    def test_workspace_root_keeps_dependency_resolution_unsuppressed(
        tmp_path: Path,
    ) -> None:
        """Adding a declared member never manufactures dependency-edge exclusions."""
        rendered = u.Tests.scaffold_text(
            tmp_path / "fixture-project",
            c.PYPROJECT_FILENAME,
            members=("fixture-member",),
        )
        uv = u.Tests.toml_table_at(rendered, "tool", "uv")
        tm.ok("exclude-dependencies" not in uv)

    @staticmethod
    def test_scaffold_omits_diagnostic_suppression_catalogs(tmp_path: Path) -> None:
        """The shipped Jinja surface cannot restore retired exemption tables."""
        rendered = u.Tests.scaffold_text(
            tmp_path / "no-suppression-project",
            c.PYPROJECT_FILENAME,
            what=c.Infra.CodegenConformSurface.PYPROJECT,
        )
        lint = u.Tests.toml_table_at(rendered, "tool", "ruff", "lint")
        for key in (
            "extend-ignore",
            "per-file-ignores",
            "extend-per-file-ignores",
        ):
            tm.that(lint, lacks=key)
        tm.that(
            lint["ignore"], eq=sorted(config.Infra.tooling.tools.ruff.lint.rule_owners)
        )
        mypy = u.Tests.toml_table_at(rendered, "tool", "mypy")
        policy = config.Infra.tooling.tools.mypy
        if policy.ruling_disable_error_codes:
            tm.that(
                mypy["disable_error_code"],
                eq=list(policy.ruling_disable_error_codes),
            )
        else:
            tm.that(mypy, lacks="disable_error_code")
        tm.that(mypy.get("ignore_errors", False), eq=False)
        for entry in u.Tests.toml_list(mypy.get("overrides", [])):
            override = u.Tests.toml_mapping(entry)
            tm.that(override, lacks="disable_error_code")
            tm.that(override.get("ignore_errors", False), eq=False)

    @staticmethod
    def test_scaffold_mypy_policy_matches_ssot_and_converges(tmp_path: Path) -> None:
        """The actual Jinja scaffold preserves typed policy on repeated rendering."""
        root = tmp_path / "fixture-project"
        surface = c.Infra.CodegenConformSurface.PYPROJECT
        first = u.Tests.scaffold_text(root, c.PYPROJECT_FILENAME, what=surface)
        mypy = u.Tests.toml_table_at(first, "tool", "mypy")
        policy = config.Infra.tooling.tools.mypy
        if policy.ruling_disable_error_codes:
            tm.that(
                mypy["disable_error_code"],
                eq=list(policy.ruling_disable_error_codes),
            )
        else:
            tm.that(mypy, lacks="disable_error_code")
        for key, value in u.Infra.native_tool_settings(
            config.Infra.tooling, "mypy"
        ).items():
            tm.that(mypy[key], eq=value)
        tm.that(
            u.Tests.toml_table_at(first, "tool", "pydantic-mypy"),
            eq=u.Infra.native_tool_settings(config.Infra.tooling, "pydantic-mypy"),
        )
        tm.that(
            u.Tests.scaffold_text(root, c.PYPROJECT_FILENAME, what=surface),
            eq=first,
        )

    @staticmethod
    @pytest.mark.parametrize("members", [(), ("fixture-member",)])
    def test_scaffold_pyrefly_policy_matches_ssot_and_converges(
        tmp_path: Path,
        members: Sequence[str],
    ) -> None:
        """Both repository roles render each declared diagnostic exactly once."""
        root = tmp_path / "fixture-project"
        surface = c.Infra.CodegenConformSurface.PYPROJECT
        first = u.Tests.scaffold_text(
            root,
            c.PYPROJECT_FILENAME,
            members=members,
            what=surface,
        )
        tm.that(
            u.Tests.toml_table_at(first, "tool", "pyrefly", "errors"),
            eq=u.Infra.native_tool_settings(config.Infra.tooling, "pyrefly.errors"),
        )
        tm.that(
            u.Tests.scaffold_text(
                root,
                c.PYPROJECT_FILENAME,
                members=members,
                what=surface,
            ),
            eq=first,
        )

    @staticmethod
    def test_pyrefly_diagnostic_pairs_elect_the_last_declared_value() -> None:
        """A later layer replaces a diagnostic through the common registry."""
        registry = dict(config.Infra.tooling.settings)
        registry["pyrefly.errors"] = (
            ("bad-argument-count", "warn"),
            ("bad-argument-count", "error"),
        )
        validated = m.Infra.ToolConfigDocument.model_validate({
            **config.Infra.tooling.model_dump(
                by_alias=True, exclude_computed_fields=True
            ),
            "settings": registry,
        })
        tm.that(
            u.Infra.native_tool_settings(validated, "pyrefly.errors"),
            eq={"bad-argument-count": "error"},
        )

    @staticmethod
    @pytest.mark.parametrize("selection", ["reordered", "subset", "empty"])
    def test_pyrefly_policy_preserves_valid_diagnostic_selections(
        selection: str,
    ) -> None:
        """Validation does not freeze the selected diagnostic set or its order."""
        policy = config.Infra.tooling
        errors = tuple(policy.settings["pyrefly.errors"])
        if selection == "reordered":
            selected = tuple(reversed(errors))
        elif selection == "subset":
            selected = errors[::2]
        else:
            selected = ()
        registry = dict(policy.settings)
        registry["pyrefly.errors"] = selected
        validated = m.Infra.ToolConfigDocument.model_validate({
            **policy.model_dump(by_alias=True, exclude_computed_fields=True),
            "settings": registry,
        })
        tm.that(tuple(validated.settings["pyrefly.errors"]), eq=selected)

    @staticmethod
    def _assert_unmanaged_tool_tables_survive(
        live: str,
        rendered: str,
        document: t.JsonMapping,
    ) -> None:
        """`ruff` is managed: the rendered projection wins over the live file.

        `bandit` is unmanaged and live-only, so it survives untouched.
        """
        tool = tm.not_none(u.Cli.toml_mapping_child(document, "tool"))
        ruff = tm.not_none(u.Cli.toml_mapping_child(tool, "ruff"))
        bandit = tm.not_none(u.Cli.toml_mapping_child(tool, "bandit"))
        live_tool = u.Tests.toml_table_at(live, "tool")
        rendered_payload = tm.not_none(u.Cli.toml_mapping_from_text(rendered))
        rendered_tool = tm.not_none(u.Cli.toml_mapping_child(rendered_payload, "tool"))
        rendered_ruff = tm.not_none(u.Cli.toml_mapping_child(rendered_tool, "ruff"))
        tm.that(ruff["line-length"], eq=rendered_ruff["line-length"])
        live_bandit = u.Cli.toml_mapping_child(live_tool, "bandit")
        tm.that(bandit["skips"], eq=(live_bandit or {}).get("skips"))

    def test_overlay_preserves_custom_scripts_and_unmanaged_tools(self) -> None:
        """Package requirements survive without restoring stale profile pins."""
        rendered = """[project]
name = "flext"
dependencies = ["pydantic>=2"]
scripts = {flext = "flext.cli:main"}

[dependency-groups]
codegen = [
    "flext-infra @ git+https://github.com/flext-sh/flext-infra.git@0.12.0-dev",
]
dev = ["rumdl>=0.2.45"]

[tool.ruff]
line-length = 88
"""
        live = """[project]
name = "flext"
dependencies = [
    "pydantic>=1",
    "beartype>=0.22",
    "custom-runtime[feature]>=2; python_version < '3.14'",
    "custom-runtime[feature]>=3; python_version >= '3.14'",
]
scripts = {flext = "flext.workspace:main", flext-dev = "flext.dev:main"}

[dependency-groups]
codegen = ["obsolete-codegen"]
dev = ["rumdl>=0.2.40", "custom-audit>=1"]

[tool.ruff]
line-length = 120

[tool.bandit]
skips = ["B101"]
"""
        live_document = tm.not_none(u.Cli.toml_parse_text(live))
        u.Infra.sync_member_dev_provenance(
            live_document,
            custom=(),
            group=c.Infra.DependencyGroup.CODEGEN,
        )
        live = u.Cli.toml_dumps(live_document)
        first = tm.ok(u.Infra.overlay_preserved(rendered, live))
        document = tm.not_none(u.Cli.toml_mapping_from_text(first))
        project = tm.not_none(u.Cli.toml_mapping_child(document, "project"))
        expected_requirements = frozenset({
            "pydantic>=2",
            "beartype>=0.22",
            "custom-runtime[feature]>=2; python_version < '3.14'",
            "custom-runtime[feature]>=3; python_version >= '3.14'",
        })
        tm.that(
            frozenset(u.Tests.toml_strings_at(first, "project", "dependencies")),
            eq=expected_requirements,
        )
        tm.that(tm.ok(u.Infra.overlay_preserved(rendered, first)), eq=first)
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                first,
                workspace=self._workspace(),
                required_dev_dependencies=("rumdl>=0.2.45",),
                uv_resolution=self._uv_resolution(config.Infra.codegen.toolchain),
            ),
        )
        tm.that(
            frozenset(
                u.Tests.toml_strings_at(conformed, "project", "dependencies"),
            ),
            eq=expected_requirements,
        )
        repeated = tm.ok(u.Infra.overlay_preserved(rendered, conformed))
        tm.that(
            frozenset(
                u.Tests.toml_strings_at(repeated, "project", "dependencies"),
            ),
            eq=expected_requirements,
        )
        # Membership alone hides a required-first / alphabetical oscillation.
        # Exercise both public owners; neither may reorder the other's output.
        canonical_dependencies = u.Tests.toml_strings_at(
            conformed,
            "project",
            "dependencies",
        )
        tm.that(
            u.Tests.toml_strings_at(first, "project", "dependencies"),
            eq=canonical_dependencies,
        )
        tm.that(
            u.Tests.toml_strings_at(repeated, "project", "dependencies"),
            eq=canonical_dependencies,
        )
        dev = u.Tests.toml_strings_at(conformed, "dependency-groups", "dev")
        tm.ok("custom-audit>=1" in dev)
        tm.ok("rumdl>=0.2.45" in dev)
        tm.ok("rumdl>=0.2.40" not in dev)
        tm.that(
            tuple(u.Tests.toml_strings_at(first, "dependency-groups", "codegen")),
            eq=(
                (
                    "flext-infra @ git+https://github.com/flext-sh/flext-infra.git"
                    "@0.12.0-dev"
                ),
            ),
        )
        tm.ok("flext-dev" in u.Tests.toml_mapping(project["scripts"]))
        self._assert_unmanaged_tool_tables_survive(live, rendered, document)
