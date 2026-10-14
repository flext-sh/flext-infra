"""Public conformance preserves native PEP 735 group structure and tiers."""

from __future__ import annotations

import json

import pytest
from packaging.utils import canonicalize_name

from flext_infra import config
from tests import c, m, p, t, tm, u


class TestsPyprojectDependencyGroups:
    """Exercise the same public TOML boundary consumed by native resolution."""

    @staticmethod
    def _workspace(role: c.Infra.MakeProfile) -> m.Infra.WorkspaceSpec:
        return u.Tests.workspace_spec(
            u.Tests.repository_ref("workspace", role=role),
        )

    @classmethod
    def _conform(
        cls,
        source: str,
        role: c.Infra.MakeProfile,
        *,
        required_dev_dependencies: t.StrSequence = (),
    ) -> p.Result[str]:
        toolchain = config.Infra.codegen.toolchain
        return u.Infra.pyproject_conform(
            source,
            workspace=cls._workspace(role),
            required_dev_dependencies=required_dev_dependencies,
            uv_resolution=m.Infra.UvResolutionSpec(
                link_mode=toolchain.uv_link_mode,
                constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
                environments=tuple(toolchain.uv_environments),
            ),
            options=u.Infra.PyprojectConformOptions(
                flext_line=u.Tests.integration().model_copy(
                    update={"base_url": u.Tests.provider().base_url},
                ),
            ),
        )

    @classmethod
    def _source(cls, groups: str, *, project_fields: str = "") -> str:
        workspace = cls._workspace(c.Infra.MakeProfile.STANDALONE)
        return (
            "[project]\n"
            f"name = {json.dumps(workspace.repository.distribution)}\n"
            'version = "0.1.0"\n'
            "dependencies = []\n"
            f"{project_fields}\n"
            "[dependency-groups]\n"
            f"{groups}\n"
        )

    @pytest.mark.parametrize(
        "role",
        [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE],
    )
    def test_conform_preserves_ordered_nested_includes_and_dependency_tiers(
        self,
        role: c.Infra.MakeProfile,
    ) -> None:
        """Native tables retain position, repeated occurrences and Git provenance."""
        development = u.Tests.flext_source("flext-tests")
        codegen = u.Tests.flext_source("flext-infra")
        marked = "group-only[feature]>=1.0,<2.0; python_version >= '3.13'"
        optional = "optional-only[feature]>=1.0; python_version >= '3.13'"
        groups = (
            f"dev = [{json.dumps(development)}, "
            '{include-group = "codegen"}, '
            f"{json.dumps(marked)}, {json.dumps(marked)}]\n"
            f"codegen = [{json.dumps(codegen)}]\n"
            'examples = ["example-only>=1.0", {include-group = "dev"}, '
            '"example-tail<3.0"]\n'
            'nested = [{include-group = "EXAMPLES"}, "nested-only>=1.0"]'
        )
        source = self._source(
            groups,
            project_fields=(
                "[project.optional-dependencies]\n"
                f"feature = [{json.dumps(optional)}]"
            ),
        )
        rendered = tm.ok(self._conform(source, role))
        expected = u.Tests.toml_mapping(u.Tests.toml_doc(source))
        actual = u.Tests.toml_mapping(u.Tests.toml_doc(rendered))
        tm.that(
            u.Tests.toml_mapping(actual["dependency-groups"]),
            eq=u.Tests.toml_mapping(expected["dependency-groups"]),
        )
        expected_project = u.Tests.toml_mapping(expected["project"])
        actual_project = u.Tests.toml_mapping(actual["project"])
        tm.that(
            actual_project["dependencies"],
            eq=expected_project["dependencies"],
        )
        tm.that(
            actual_project["optional-dependencies"],
            eq=expected_project["optional-dependencies"],
        )
        tm.that(tm.ok(self._conform(rendered, role)), eq=rendered)

    @pytest.mark.parametrize(
        "role",
        [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE],
    )
    @pytest.mark.parametrize(
        "group_name",
        [str(c.Infra.DEV), str(c.Infra.DependencyGroup.CODEGEN)],
    )
    def test_normalized_group_identity_does_not_create_a_second_group(
        self,
        role: c.Infra.MakeProfile,
        group_name: str,
    ) -> None:
        """A valid authored spelling keeps its includes when managed floors merge."""
        authored_name = group_name.capitalize()
        dev_name = str(c.Infra.DEV)
        codegen_name = str(c.Infra.DependencyGroup.CODEGEN)
        other = codegen_name if group_name == dev_name else dev_name
        marked = "group-case-preserved[feature]>=1.0,<3.0; sys_platform == 'linux'"
        source = self._source(
            f"{authored_name} = [{json.dumps(marked)}, "
            '{include-group = "base"}]\n'
            f"{other} = []\n"
            "base = []\n"
            f'examples = [{{include-group = "{authored_name}"}}]',
        )
        floors = config.Infra.codegen.scaffold.project.dev
        rendered = tm.ok(
            self._conform(source, role, required_dev_dependencies=floors),
        )
        actual = u.Tests.toml_mapping(u.Tests.toml_doc(rendered))
        expected = u.Tests.toml_mapping(u.Tests.toml_doc(source))
        groups = u.Tests.toml_mapping(actual["dependency-groups"])
        expected_groups = u.Tests.toml_mapping(expected["dependency-groups"])
        tm.that(
            tuple(
                name
                for name in groups
                if canonicalize_name(name) == canonicalize_name(group_name)
            ),
            eq=(authored_name,),
        )
        tm.that(
            u.Tests.toml_list(groups[authored_name])[-2:],
            eq=u.Tests.toml_list(expected_groups[authored_name]),
        )
        tm.that(groups["examples"], eq=expected_groups["examples"])
        actual_dev_name = next(
            name
            for name in groups
            if canonicalize_name(name) == canonicalize_name(dev_name)
        )
        actual_floor_names = {
            u.Infra.dep_name(entry)
            for entry in u.Tests.toml_list(groups[actual_dev_name])
            if isinstance(entry, str)
        }
        tm.that(
            {u.Infra.dep_name(entry) for entry in floors}.issubset(
                actual_floor_names,
            ),
            eq=True,
        )
        tm.that(
            tm.ok(
                self._conform(rendered, role, required_dev_dependencies=floors),
            ),
            eq=rendered,
        )

    @pytest.mark.parametrize(
        "role",
        [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE],
    )
    @pytest.mark.parametrize("name", ["dev", "codegen"])
    def test_extra_name_does_not_migrate_its_requirements_into_a_group(
        self,
        role: c.Infra.MakeProfile,
        name: str,
    ) -> None:
        """An extra and a group with the same name remain independent declarations."""
        optional = sorted((
            "optional-only[feature]>=1.0,<2.0; sys_platform == 'linux'",
            "optional-only[feature]>=2.0,<3.0; sys_platform != 'linux'",
        ))
        group_first = "group-only[feature]>=1.0,<4.0; python_version >= '3.13'"
        group_last = "group-only[feature]>=2.0,<5.0; python_version < '3.13'"
        other = "codegen" if name == "dev" else "dev"
        source = self._source(
            f"{name} = [{json.dumps(group_first)}, "
            '{include-group = "shared"}, '
            f"{json.dumps(group_last)}, {json.dumps(group_first)}]\n"
            f"{other} = []\n"
            "shared = []\n"
            f'examples = [{{include-group = "{name}"}}]',
            project_fields=(
                "[project.optional-dependencies]\n"
                f"{name} = {json.dumps(optional)}\n"
                'feature = ["independent-extra>=1.0,<2.0"]'
            ),
        )
        rendered = tm.ok(self._conform(source, role))
        expected = u.Tests.toml_mapping(u.Tests.toml_doc(source))
        actual = u.Tests.toml_mapping(u.Tests.toml_doc(rendered))
        expected_project = u.Tests.toml_mapping(expected["project"])
        actual_project = u.Tests.toml_mapping(actual["project"])
        tm.that(
            actual_project["optional-dependencies"],
            eq=expected_project["optional-dependencies"],
        )
        tm.that(
            actual["dependency-groups"],
            eq=expected["dependency-groups"],
        )
        tm.that(
            actual_project["dependencies"],
            eq=expected_project["dependencies"],
        )
        tm.that(tm.ok(self._conform(rendered, role)), eq=rendered)

    @pytest.mark.parametrize(
        "groups",
        [
            'dev = [{include-group = "missing"}]',
            'dev = [{include-group = "dev"}]',
            'dev = [{include-group = "codegen"}]\n'
            'codegen = [{include-group = "examples"}]\n'
            'examples = [{include-group = "dev"}]',
            'dev = []\nexamples = []\nEXAMPLES = []',
        ],
    )
    def test_conform_rejects_invalid_local_group_graph(self, groups: str) -> None:
        """A missing, ambiguous or cyclic local inclusion cannot be published."""
        result = self._conform(
            self._source(groups),
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.that(result.failure, eq=True)

    def test_optional_dependencies_keep_pep508_string_grammar(self) -> None:
        """PEP 735 inclusion tables never become PEP 621 runtime or extra entries."""
        result = self._conform(
            self._source(
                "dev = []",
                project_fields=(
                    "[project.optional-dependencies]\n"
                    'feature = [{include-group = "dev"}]'
                ),
            ),
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.that(result.failure, eq=True)

    def test_runtime_dependencies_keep_pep508_string_grammar(self) -> None:
        source = self._source("dev = []").replace(
            "dependencies = []",
            'dependencies = [{include-group = "dev"}]',
        )
        result = self._conform(source, c.Infra.MakeProfile.STANDALONE)
        tm.that(result.failure, eq=True)

    @pytest.mark.parametrize(
        "entry",
        [
            '{"include-group" = "examples", unexpected = "value"}',
            '{"include-group" = 42}',
            "42",
        ],
    )
    def test_invalid_native_entries_escape_at_the_public_boundary(
        self,
        entry: str,
    ) -> None:
        """The typed parser exposes malformed tables before they can be rewritten."""
        source = self._source(f"dev = [{entry}]\nexamples = []")
        with pytest.raises(ValueError):
            self._conform(source, c.Infra.MakeProfile.STANDALONE)

    def test_empty_native_groups_remain_available_for_inclusion(self) -> None:
        source = self._source(
            'dev = []\ncodegen = []\nexamples = [{include-group = "dev"}, '
            '{include-group = "codegen"}]',
        )
        rendered = tm.ok(self._conform(source, c.Infra.MakeProfile.STANDALONE))
        actual = u.Tests.toml_mapping(u.Tests.toml_doc(rendered))
        expected = u.Tests.toml_mapping(u.Tests.toml_doc(source))
        tm.that(
            actual["dependency-groups"],
            eq=expected["dependency-groups"],
        )
