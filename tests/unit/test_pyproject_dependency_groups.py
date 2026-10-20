"""Public conformance preserves native PEP 735 group structure and tiers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import config
from tests import c, m, p, t, tm, u


class TestsFlextInfraPyprojectDependencyGroups:
    """Exercise the same public TOML boundary consumed by native resolution."""

    @pytest.mark.parametrize("variant", ["same", "extras", "marker", "origin", "bound"])
    def test_development_composition_preserves_complete_requirement_identity(
        self,
        variant: str,
    ) -> None:
        """Authored occurrences and distinct policy obligations survive composition."""
        own = self._workspace(c.Infra.MakeProfile.STANDALONE).repository.distribution
        floor = "composition-floor>=1.0,<3.0"
        parsed = Requirement(floor)
        requirements = {
            "same": f"{parsed.name.upper()}{parsed.specifier}",
            "extras": f"{parsed.name}[feature]{parsed.specifier}",
            "marker": f"{floor}; implementation_name == 'cpython'",
            "origin": (
                f"{parsed.name} @ git+"
                f"{u.Tests.repository_ref(parsed.name).url}@{u.Tests.provider_branch()}"
            ),
            "bound": f"{parsed.name}>=2.0,<3.0",
        }
        authored = requirements[variant]
        declared = (authored, authored, f"{own}[feature]")
        policy = config.Infra.codegen.scaffold.project.model_copy(
            update={
                "dev": (floor, own, floor),
                "required_flext_dev": (),
            },
        )

        composed = u.Infra.project_development_requirements(
            policy,
            distribution=own,
            kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
            declared=declared,
        )

        tm.that(composed[: len(declared)], eq=declared)
        tm.that(
            composed[len(declared) :],
            eq=() if Requirement(authored) == Requirement(floor) else (floor,),
        )
        source = self._source(
            f"dev = {tm.ok(u.Cli.json_dumps(list(declared)))}\n"
            'examples = [{include-group = "dev"}]',
            project_fields="[project.optional-dependencies]\nfeature = []",
        )
        rendered = tm.ok(
            self._conform(
                source,
                c.Infra.MakeProfile.STANDALONE,
                required_dev_dependencies=composed,
            ),
        )
        actual = u.Tests.toml_mapping(u.Tests.toml_doc(rendered))
        groups = u.Tests.toml_mapping(actual["dependency-groups"])
        actual_entries = tuple(
            Requirement(requirement)
            for requirement in u.Tests.toml_strings(groups["dev"])
        )
        actual_requirements = set(actual_entries)
        tm.ok(Requirement(authored) in actual_requirements)
        tm.that(actual_entries.count(Requirement(authored)), eq=2)
        tm.ok(Requirement(floor) in actual_requirements)
        tm.ok(Requirement(f"{own}[feature]") in actual_requirements)
        tm.that(groups["examples"], eq=[{"include-group": "dev"}])
        project = u.Tests.toml_mapping(actual["project"])
        tm.that(project["dependencies"], eq=[])
        tm.that(project["optional-dependencies"], eq={"feature": []})
        tm.that(
            tm.ok(
                self._conform(
                    rendered,
                    c.Infra.MakeProfile.STANDALONE,
                    required_dev_dependencies=composed,
                ),
            ),
            eq=rendered,
        )

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
            f"name = {tm.ok(u.Cli.json_dumps(workspace.repository.distribution))}\n"
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
            f"dev = [{tm.ok(u.Cli.json_dumps(development))}, "
            '{include-group = "codegen"}, '
            f"{tm.ok(u.Cli.json_dumps(marked))}, {tm.ok(u.Cli.json_dumps(marked))}]\n"
            f"codegen = [{tm.ok(u.Cli.json_dumps(codegen))}]\n"
            'examples = ["example-only>=1.0", {include-group = "dev"}, '
            '"example-tail<3.0"]\n'
            'nested = [{include-group = "EXAMPLES"}, "nested-only>=1.0"]'
        )
        source = self._source(
            groups,
            project_fields=(
                f"[project.optional-dependencies]\nfeature = [{tm.ok(u.Cli.json_dumps(optional))}]"
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
            f"{authored_name} = [{tm.ok(u.Cli.json_dumps(marked))}, "
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
    def test_floor_merge_preserves_authored_requirement_variants(
        self,
        role: c.Infra.MakeProfile,
    ) -> None:
        """Floors retain authored bounds, extras, markers and Git occurrences."""
        authored_name, source, seed = self._variant_authored_sources()
        floor = "variant-floor>=2.0"
        overlaid = tm.ok(u.Infra.overlay_preserved(seed, source))
        expected = u.Tests.toml_mapping(u.Tests.toml_doc(source))
        overlaid_payload = u.Tests.toml_mapping(u.Tests.toml_doc(overlaid))
        tm.that(
            overlaid_payload["dependency-groups"],
            eq=expected["dependency-groups"],
        )
        conformed = tm.ok(
            self._conform(
                overlaid,
                role,
                required_dev_dependencies=(floor,),
            ),
        )
        self._assert_variant_floor_group(conformed, source, authored_name)
        repeated = tm.ok(u.Infra.overlay_preserved(seed, conformed))
        tm.that(
            tm.ok(
                self._conform(
                    repeated,
                    role,
                    required_dev_dependencies=(floor,),
                ),
            ),
            eq=conformed,
        )

    def _variant_authored_sources(self) -> t.Triple[str, str, str]:
        """Compose the authored variant project text with its empty seed.

        Returns:
            The authored dependency-group name with the authored and seed
            project texts.

        """
        name = "variant-floor"
        authored_bound = f"{name}>=1.0"
        extra = f"{name}[feature]>=1.0,<3.0"
        marked = f"{name}>=1.0; sys_platform == 'linux'"
        origin = u.Tests.repository_ref(name)
        direct = f"{name} @ git+{origin.url}@{u.Tests.provider_branch()}"
        dev = str(c.Infra.DEV)
        codegen = str(c.Infra.DependencyGroup.CODEGEN)
        authored_name = dev.capitalize()
        source = self._source(
            f"{authored_name} = [{tm.ok(u.Cli.json_dumps(authored_bound))}, {tm.ok(u.Cli.json_dumps(marked))}, "
            '{include-group = "base"}, '
            f"{tm.ok(u.Cli.json_dumps(extra))}, {tm.ok(u.Cli.json_dumps(direct))}, {tm.ok(u.Cli.json_dumps(marked))}]\n"
            f"{codegen} = []\n"
            "base = []\n"
            f'examples = [{{include-group = "{authored_name}"}}]',
        )
        seed = self._source(f"{dev} = []\n{codegen} = []")
        return (authored_name, source, seed)

    def _assert_variant_floor_group(
        self,
        conformed: str,
        source: str,
        authored_name: str,
    ) -> None:
        """Require the conformed floor group to retain every authored variant."""
        name = "variant-floor"
        floor = f"{name}>=2.0"
        authored_bound = f"{name}>=1.0"
        extra = f"{name}[feature]>=1.0,<3.0"
        marked = f"{name}>=1.0; sys_platform == 'linux'"
        origin = u.Tests.repository_ref(name)
        direct = f"{name} @ git+{origin.url}@{u.Tests.provider_branch()}"
        groups = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc(conformed))["dependency-groups"],
        )
        expected: t.JsonList = [
            floor,
            authored_bound,
            marked,
            {"include-group": "base"},
            extra,
            direct,
            marked,
        ]
        tm.that(
            u.Tests.toml_list(groups[authored_name]),
            len=len(expected),
            items=[{"eq": entry} for entry in expected],
        )
        tm.that(
            groups["examples"],
            eq=u.Tests.toml_mapping(
                u.Tests.toml_mapping(u.Tests.toml_doc(source))["dependency-groups"],
            )["examples"],
        )

    @pytest.mark.parametrize(
        "role",
        [c.Infra.MakeProfile.STANDALONE, c.Infra.MakeProfile.WORKSPACE],
    )
    @pytest.mark.parametrize("variant", ["extra", "marker", "bounded", "origin"])
    def test_internal_floor_yields_only_its_unbounded_matching_dimension(
        self,
        role: c.Infra.MakeProfile,
        variant: str,
    ) -> None:
        """Conditional requests and Git origins cannot erase an enforced bound."""
        name = config.Infra.codegen.infra_repository.distribution
        canonical = u.Tests.flext_source(name)
        source_url = Requirement(canonical).url
        tm.that(source_url, is_=str)
        floor = f"{name}>=0" if variant == "bounded" else name
        if variant == "extra":
            authored = f"{name}[feature] @ {source_url}"
        elif variant == "marker":
            authored = f"{canonical} ; sys_platform == 'linux'"
        elif variant == "origin":
            authored = f"{canonical}-authored-fixture"
        else:
            authored = canonical
        authored_requirement = Requirement(authored)
        dev = str(c.Infra.DEV)
        codegen = str(c.Infra.DependencyGroup.CODEGEN)
        source = self._source(
            f"{dev} = [{tm.ok(u.Cli.json_dumps(authored))}, "
            '{include-group = "base"}]\n'
            f"{codegen} = []\nbase = []",
        )

        conformed = tm.ok(
            self._conform(source, role, required_dev_dependencies=(floor,)),
        )

        groups = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc(conformed))["dependency-groups"],
        )
        generated = floor if variant == "bounded" else canonical
        expected = (
            [authored, {"include-group": "base"}]
            if variant == "origin"
            else [generated, authored, {"include-group": "base"}]
        )
        tm.that(
            u.Tests.toml_list(groups[dev]),
            len=len(expected),
            items=[{"eq": entry} for entry in expected],
        )
        observed_requirements = tuple(
            Requirement(entry)
            for entry in u.Tests.toml_list(groups[dev])
            if isinstance(entry, str)
        )
        tm.ok(authored_requirement in observed_requirements)
        tm.that(
            tm.ok(
                self._conform(conformed, role, required_dev_dependencies=(floor,)),
            ),
            eq=conformed,
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
            f"{name} = [{tm.ok(u.Cli.json_dumps(group_first))}, "
            '{include-group = "shared"}, '
            f"{tm.ok(u.Cli.json_dumps(group_last))}, {tm.ok(u.Cli.json_dumps(group_first))}]\n"
            f"{other} = []\n"
            "shared = []\n"
            f'examples = [{{include-group = "{name}"}}]',
            project_fields=(
                "[project.optional-dependencies]\n"
                f"{name} = {tm.ok(u.Cli.json_dumps(optional))}\n"
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
            (
                'dev = [{include-group = "codegen"}]\n'
                'codegen = [{include-group = "examples"}]\n'
                'examples = [{include-group = "dev"}]'
            ),
            "dev = []\nexamples = []\nEXAMPLES = []",
        ],
    )
    def test_conform_rejects_invalid_local_group_graph(self, groups: str) -> None:
        """A missing, ambiguous or cyclic local inclusion cannot be published."""
        result = self._conform(
            self._source(groups),
            c.Infra.MakeProfile.STANDALONE,
        )
        tm.ok(result.failure)

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
        tm.ok(result.failure)

    def test_runtime_dependencies_keep_pep508_string_grammar(self) -> None:
        """PEP 621 runtime dependency arrays reject PEP 735 inclusion tables."""
        source = self._source("dev = []").replace(
            "dependencies = []",
            'dependencies = [{include-group = "dev"}]',
        )
        result = self._conform(source, c.Infra.MakeProfile.STANDALONE)
        tm.ok(result.failure)

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
        with pytest.raises(
            ValueError,
            match="validation errors for DependencyGroupEntries",
        ):
            self._conform(source, c.Infra.MakeProfile.STANDALONE)

    def test_empty_native_groups_remain_available_for_inclusion(self) -> None:
        """Conform preserves the empty native groups its inclusions reference."""
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
