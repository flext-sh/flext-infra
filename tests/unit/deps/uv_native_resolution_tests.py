"""Local native UV qualification of self identity and dependency-group graphs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from flext_infra import config
from tests import c, m, t, tm, u


class TestsFlextInfraUvNativeResolution:
    """Resolve real local Git packages without external-service prerequisites."""

    @staticmethod
    @pytest.mark.parametrize("mode", ["local", "standalone"])
    def test_conformed_group_aliases_resolve_without_merging_dependency_tiers(
        tmp_path: Path,
        mode: str,
    ) -> None:
        """Real UV consumes authored aliases and includes after public conformance.

        This bounded native grammar fixture declares no generated dev floors.
        The separate first-party-profile scenario qualifies the SSOT floor set.
        """
        root = tmp_path / "project"
        root_name = "native-alias-root"
        leaves = {
            tier: tmp_path / tier
            for tier in ("runtime", "development", "examples", "extra")
        }
        names = {tier: f"native-alias-{tier}" for tier in leaves}
        for tier, path in leaves.items():
            u.Tests.write_native_resolution_project(path, names[tier])
        requirements = {
            tier: f"{names[tier]} @ {path.as_uri()}"
            for tier, path in leaves.items()
        }
        dev = str(c.Infra.DEV).capitalize()
        codegen = str(c.Infra.DependencyGroup.CODEGEN).capitalize()
        u.Tests.write_native_resolution_project(
            root,
            root_name,
            dependencies=(requirements["runtime"],),
            optional=(requirements["extra"],),
            groups=(
                "[dependency-groups]\n"
                f"{dev} = [{json.dumps(requirements['development'])}]\n"
                f'{codegen} = [{{include-group = "{dev}"}}]\n'
                f'examples = [{{include-group = "{codegen}"}}, '
                f"{json.dumps(requirements['examples'])}]\n"
            ),
        )
        repository = u.Tests.repository_ref(root_name)
        toolchain = config.Infra.codegen.toolchain
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
                workspace=u.Tests.workspace_spec(repository),
                required_dev_dependencies=(),
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
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(root / c.PYPROJECT_FILENAME, conformed),
        )
        complete = u.Tests.toml_doc(conformed)
        policy = config.Infra.codegen.make.uv_resolution
        directory = root / (
            policy.local_directory
            if mode == "local"
            else policy.standalone_directory
        )
        view = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                m.Infra.UvResolutionProject(
                    repository=repository,
                    directory=root,
                    document=complete,
                ),
                members=(),
                directory=directory,
                policy=policy,
            ),
        )
        groups = u.Tests.toml_mapping(
            u.Tests.toml_doc_mapping(view)["dependency-groups"],
        )
        tm.that(u.Tests.toml_list(groups[codegen]), eq=[{"include-group": dev}])
        tm.that(
            u.Tests.toml_list(groups["examples"])[0],
            eq={"include-group": codegen},
        )
        directory.mkdir(parents=True)
        tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, view))
        process = tm.ok(u.Tests.resolve_native_identity_fixture(directory))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        locked = m.Infra.LockedEnvironment.model_validate_json(
            json.dumps(
                tm.ok(u.Cli.toml_read_json(directory / c.Infra.UV_LOCK_FILENAME)),
            ),
        )
        tm.that(
            {root_name, *names.values()}.issubset(
                {package.name for package in locked.package},
            ),
            eq=True,
        )
        package = next(
            package for package in locked.package if package.name == root_name
        )
        tm.that(
            {dependency.name for dependency in package.dependencies},
            eq={names["runtime"]},
        )
        tm.that(
            {dependency.name for dependency in package.optional_dependencies["feature"]},
            eq={names["extra"]},
        )
        tm.that(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
            eq=conformed,
        )

    @staticmethod
    def _profile_requirement(requirement: str) -> str:
        """Declare authored internal sources through the fixture's public provider."""
        parsed = Requirement(requirement)
        if not parsed.name.startswith("flext-") or parsed.url is not None:
            return requirement
        source = Requirement(u.Tests.flext_source(parsed.name))
        extras = f"[{','.join(sorted(parsed.extras))}]" if parsed.extras else ""
        marker = f" ; {parsed.marker}" if parsed.marker else ""
        return f"{parsed.name}{extras} @ {source.url}{marker}"

    @classmethod
    def _conformed_first_party_profiles(
        cls,
        root: Path,
    ) -> t.MappingKV[str, t.Cli.TomlDocument]:
        """Retain complete conformed profile documents before internal qualification."""
        documents: dict[str, t.Cli.TomlDocument] = {}
        profiles = config.Infra.codegen.scaffold.project.dependency_profiles
        toolchain = config.Infra.codegen.toolchain
        line = u.Tests.integration().model_copy(
            update={"base_url": u.Tests.provider().base_url},
        )
        resolution = m.Infra.UvResolutionSpec(
            link_mode=toolchain.uv_link_mode,
            constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
            environments=tuple(toolchain.uv_environments),
        )
        for name, upstream in (
            ("flext-core", "flext_core"),
            ("flext-cli", "flext_core"),
            ("flext-infra", "flext_cli"),
            ("flext-tests", "flext_cli"),
        ):
            profile = tm.not_none(
                u.Infra.composed_dependency_profile(
                    profiles,
                    upstream=upstream,
                    distribution=name,
                ),
            )
            runtime = tuple(
                requirement
                for requirement in profile.runtime
                if u.Infra.dep_name(requirement) != name
            )
            codegen = tuple(
                requirement
                for requirement in profile.codegen
                if u.Infra.dep_name(requirement) != name
            )
            development = [
                cls._profile_requirement(requirement)
                for requirement in config.Infra.codegen.scaffold.project.dev
                if u.Infra.dep_name(requirement) != name
            ]
            path = root / name
            u.Tests.write_native_resolution_project(
                path,
                name,
                dependencies=tuple(cls._profile_requirement(item) for item in runtime),
                groups=(
                    "[dependency-groups]\n"
                    f"dev = {json.dumps(development)}\n"
                    "codegen = "
                    f"{json.dumps([cls._profile_requirement(item) for item in codegen])}\n"
                    'examples = [{include-group = "dev"}]\n'
                ),
            )
            repository = u.Tests.repository_ref(name)
            workspace = u.Tests.workspace_spec(
                repository,
                project=u.Tests.project_spec(name).model_copy(
                    update={"upstream": upstream},
                ),
            )
            conformed = tm.ok(
                u.Infra.pyproject_conform(
                    (path / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                    workspace=workspace,
                    required_dev_dependencies=config.Infra.codegen.scaffold.project.dev,
                    uv_resolution=resolution,
                    options=u.Infra.PyprojectConformOptions(
                        flext_line=line,
                    ),
                ),
            )
            cls._assert_profile_tiers(conformed, name, runtime, codegen)
            tm.ok(u.Cli.atomic_write_text_file(path / c.PYPROJECT_FILENAME, conformed))
            documents[name] = u.Tests.toml_doc(conformed)
        return documents

    @staticmethod
    def _assert_profile_tiers(
        conformed: str,
        name: str,
        runtime: t.StrSequence,
        codegen: t.StrSequence,
    ) -> None:
        """Read the complete consumer document without replacing its declared tiers."""
        observed_runtime = {
            Requirement(requirement).name: Requirement(requirement)
            for requirement in u.Tests.toml_strings_at(
                conformed,
                "project",
                "dependencies",
            )
        }
        tm.that(
            set(observed_runtime),
            eq={Requirement(requirement).name for requirement in runtime},
        )
        for raw in runtime:
            requirement = Requirement(raw)
            observed = observed_runtime[requirement.name]
            tm.that(
                (observed.extras, str(observed.marker), str(observed.specifier)),
                eq=(
                    requirement.extras,
                    str(requirement.marker),
                    str(requirement.specifier),
                ),
            )
        tm.that(
            {
                Requirement(requirement).name
                for requirement in u.Tests.toml_strings_at(
                    conformed,
                    "dependency-groups",
                    "codegen",
                )
            },
            eq={Requirement(requirement).name for requirement in codegen},
        )
        expected_dev = {
            Requirement(requirement).name
            for requirement in u.Infra.active_development_requirements(
                config.Infra.codegen.scaffold.project.dev,
            )
            if Requirement(requirement).name != name
        }
        tm.that(
            {
                Requirement(requirement).name
                for requirement in u.Tests.toml_strings_at(
                    conformed,
                    "dependency-groups",
                    str(c.Infra.DEV),
                )
            },
            eq=expected_dev,
        )

    @staticmethod
    def _internal_profile_document(
        document: t.Cli.TomlDocument,
        packages: t.MappingKV[str, Path],
    ) -> t.Cli.TomlDocument:
        """Qualify only the real internal edges, without fabricating third parties."""
        payload = deepcopy(u.Tests.toml_mapping(u.Cli.toml_unwrap_item(document)))

        def internal(requirements: t.JsonValue) -> list[t.JsonValue]:
            selected: list[t.JsonValue] = []
            for raw in u.Tests.toml_list(requirements):
                if not isinstance(raw, str):
                    selected.append(raw)
                    continue
                requirement = Requirement(raw)
                if requirement.name not in packages:
                    continue
                extras = (
                    f"[{','.join(sorted(requirement.extras))}]"
                    if requirement.extras
                    else ""
                )
                marker = f" ; {requirement.marker}" if requirement.marker else ""
                selected.append(
                    f"{requirement.name}{extras} @ git+"
                    f"{packages[requirement.name].as_uri()}@"
                    f"{u.Tests.integration().branch}{marker}",
                )
            return selected

        project = u.Tests.toml_mapping(payload["project"])
        project["dependencies"] = internal(project.get("dependencies", []))
        groups = u.Tests.toml_mapping(payload.get("dependency-groups", {}))
        for group, requirements in groups.items():
            groups[group] = internal(requirements)
        payload["project"] = project
        payload["dependency-groups"] = groups
        return u.Cli.toml_document_from_mapping(payload)

    @pytest.mark.parametrize("root_name", ["flext-core", "flext-infra"])
    def test_real_first_party_profile_groups_survive_native_composition(
        self,
        tmp_path: Path,
        root_name: str,
    ) -> None:
        """Dev backedges remain groups through conform and both native views.

        Full conformed metadata is retained independently. Native no-index
        resolution qualifies its first-party graph only; it does not prove
        third-party resolution or wheel runtime installation.
        """
        complete = self._conformed_first_party_profiles(tmp_path / "complete")
        packages = {name: tmp_path / "native" / name for name in complete}
        original = {
            name: u.Cli.toml_dumps(document) for name, document in complete.items()
        }
        inputs: dict[str, m.Infra.UvResolutionProject] = {}
        for name, document in complete.items():
            directory = packages[name]
            limited = self._internal_profile_document(document, packages)
            directory.mkdir(parents=True)
            tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, limited))
            package = directory / "src" / name.replace("-", "_")
            package.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            u.Tests.initialize_git_repo(directory)
            u.Tests.checkout_integration(directory)
            inputs[name] = m.Infra.UvResolutionProject(
                repository=u.Tests.repository_ref(name),
                directory=directory,
                document=limited,
            )
        order = u.Infra.workspace_dependency_order(
            tmp_path / "native",
            tuple(
                project.repository.model_copy(update={"path": Path(name)})
                for name, project in inputs.items()
            ),
        )
        for name, project in inputs.items():
            runtime = u.Tests.toml_strings_at(
                u.Cli.toml_dumps(project.document),
                "project",
                "dependencies",
            )
            for requirement in runtime:
                provider = Requirement(requirement).name
                tm.that(order.index(provider) < order.index(name), eq=True)
        for mode in ("local", "standalone"):
            directory = tmp_path / mode
            directory.mkdir()
            view = tm.ok(
                u.Infra.pyproject_native_resolution_view(
                    inputs[root_name],
                    members=(
                        tuple(
                            project
                            for name, project in inputs.items()
                            if name != root_name
                        )
                        if mode == "local"
                        else ()
                    ),
                    directory=directory,
                    policy=config.Infra.codegen.make.uv_resolution,
                ),
            )
            tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, view))
            resolved = tm.ok(u.Tests.resolve_native_identity_fixture(directory))
            tm.that(
                u.Cli.process_succeeded(resolved.outcome),
                eq=True,
                msg=resolved.stdout + resolved.stderr,
            )
            locked = u.Tests.toml_tables_at(
                (directory / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
                "package",
            )
            tm.that(
                set(packages).issubset({package["name"] for package in locked}),
                eq=True,
            )
        tm.that(
            {name: u.Cli.toml_dumps(document) for name, document in complete.items()},
            eq=original,
        )

    @staticmethod
    @pytest.mark.parametrize("consumer", ["root", "member"])
    @pytest.mark.parametrize("source_kind", ["path", "git"])
    def test_package_owned_runtime_source_is_resolved_natively(
        tmp_path: Path,
        consumer: str,
        source_kind: str,
    ) -> None:
        """Observe dependency-local runtime sources through real package metadata."""
        root = tmp_path / "workspace"
        member = root / "member"
        provider = tmp_path / "provider"
        directory = root / "resolution"
        provider_name = "runtime-only-provider"
        u.Tests.write_native_resolution_project(provider, provider_name)
        revision = ""
        if source_kind == "git":
            u.Tests.initialize_git_repo(provider)
            revision = tm.ok(
                u.Cli.capture(
                    [c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD],
                    cwd=provider,
                ),
            ).strip()
            source = f"{{git = {json.dumps(provider.as_uri())}, rev = {json.dumps(revision)}}}"
        else:
            source = f"{{path = {json.dumps(str(provider))}, editable = false}}"
        inputs: list[m.Infra.UvResolutionProject] = []
        originals: list[str] = []
        for label, path, name in (
            ("root", root, "runtime-owned-root"),
            ("member", member, "runtime-owned-member"),
        ):
            selected = label == consumer
            u.Tests.write_native_resolution_project(
                path,
                name,
                dependencies=(f"{provider_name}>=1.0.0",) if selected else (),
                uv=(
                    f"[tool.uv.sources]\n{provider_name} = {source}\n"
                    if selected
                    else ""
                ),
            )
            document = u.Tests.toml_doc(
                (path / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            )
            inputs.append(
                m.Infra.UvResolutionProject(
                    repository=u.Tests.repository_ref(name),
                    directory=path,
                    document=document,
                ),
            )
            originals.append(u.Cli.toml_dumps(document))
        view = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                inputs[0],
                members=(inputs[1],) if consumer == "member" else (),
                directory=directory,
                policy=config.Infra.codegen.make.uv_resolution,
            ),
        )
        directory.mkdir()
        tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, view))
        process = tm.ok(u.Tests.resolve_native_identity_fixture(directory))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        packages = u.Tests.toml_tables_at(
            (directory / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
            "package",
        )
        resolved = next(
            package for package in packages if package["name"] == provider_name
        )
        locator = u.Tests.toml_mapping(resolved["source"])
        if source_kind == "git":
            tm.that(locator["git"], has=revision)
        else:
            actual = locator["directory"]
            tm.that(actual, is_=str)
            if isinstance(actual, str):
                tm.that((directory / actual).resolve(), eq=provider)
        tm.that(
            [u.Cli.toml_dumps(project.document) for project in inputs],
            eq=originals,
        )

    @staticmethod
    def test_conformed_workspace_root_resolves_without_member_checkout(
        tmp_path: Path,
    ) -> None:
        """Resolve the actual conformed root's Git groups after members disappear."""
        root = tmp_path / "workspace"
        checkout = root / "member"
        origin = tmp_path / "member-origin.git"
        root_ref = u.Tests.repository_ref(
            "identity-portable-root",
            role=c.Infra.MakeProfile.WORKSPACE,
        )
        member_ref = u.Tests.repository_ref(
            "identity-portable-member",
            path=Path("member"),
        )
        u.Tests.write_native_resolution_project(checkout, member_ref.distribution)
        u.Tests.initialize_git_repo(checkout)
        branch = u.Tests.integration().branch
        if branch != c.Infra.GIT_MAIN:
            u.Tests.git_bootstrap(checkout, ("branch", branch))
        u.Tests.git_bootstrap(
            root,
            ("clone", "--bare", str(checkout), str(origin)),
        )
        requirement = f"{member_ref.distribution} @ git+{member_ref.url}@{branch}"
        u.Tests.write_native_resolution_project(
            root,
            root_ref.distribution,
            groups=f"[dependency-groups]\nexamples = [{json.dumps(requirement)}]\n",
            uv=(
                "[tool.uv.sources]\n"
                f"{member_ref.distribution} = "
                f'{{path = "member", editable = {str(member_ref.editable).lower()}}}\n'
            ),
        )
        workspace = u.Tests.workspace_spec(
            root_ref,
            subprojects=(member_ref,),
        )
        toolchain = config.Infra.codegen.toolchain
        conformed = tm.ok(
            u.Infra.pyproject_conform(
                (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                workspace=workspace,
                required_dev_dependencies=(),
                uv_resolution=m.Infra.UvResolutionSpec(
                    link_mode=toolchain.uv_link_mode,
                    constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
                    environments=tuple(toolchain.uv_environments),
                    override_dependencies=(f"{root_ref.distribution}>=1.0.0,<2.0.0",),
                ),
                options=u.Infra.PyprojectConformOptions(
                    repository_root=root,
                    flext_line=u.Tests.integration(),
                ),
            ),
        )
        (root / c.PYPROJECT_FILENAME).write_text(conformed, encoding="utf-8")
        actual = u.Tests.toml_doc(conformed)
        root_input = m.Infra.UvResolutionProject(
            repository=root_ref,
            directory=root,
            document=actual,
        )
        member_input = m.Infra.UvResolutionProject(
            repository=member_ref,
            directory=checkout,
            document=u.Tests.toml_doc(
                (checkout / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
        )
        policy = config.Infra.codegen.make.uv_resolution
        local = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                root_input,
                members=(member_input,),
                directory=root / policy.local_directory,
                policy=policy,
            ),
        )
        standalone_directory = root / policy.standalone_directory
        standalone = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                root_input,
                members=(),
                directory=standalone_directory,
                policy=policy,
            ),
        )
        actual_uv = u.Tests.toml_table_at(conformed, "tool", "uv")
        tm.that(
            u.Tests.toml_strings(actual_uv["override-dependencies"]),
            eq=(f"{root_ref.distribution}>=1.0.0,<2.0.0",),
        )
        tm.that(actual_uv, lacks="sources")
        standalone_uv = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(standalone)["tool"])["uv"],
        )
        tm.that(
            member_ref.distribution
            in u.Tests.toml_mapping(standalone_uv.get("sources")),
            eq=False,
        )
        local_sources = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(local)["tool"])["uv"],
        )
        tm.that(
            u.Tests.toml_mapping(
                u.Tests.toml_mapping(local_sources["sources"])[member_ref.distribution],
            )["editable"],
            eq=member_ref.editable,
        )
        checkout.rename(root / "unavailable-member")
        tm.that(checkout.exists(), eq=False)
        standalone_directory.mkdir(parents=True)
        tm.ok(
            u.Cli.toml_write_document(
                standalone_directory / c.PYPROJECT_FILENAME,
                standalone,
            ),
        )
        process = tm.ok(
            u.Tests.resolve_native_identity_fixture(
                standalone_directory,
                git_environment={
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": f"url.{origin.as_uri()}.insteadOf",
                    "GIT_CONFIG_VALUE_0": member_ref.url,
                },
            ),
        )
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        packages = u.Tests.toml_tables_at(
            (standalone_directory / c.Infra.UV_LOCK_FILENAME).read_text(
                encoding="utf-8"
            ),
            "package",
        )
        member_package = next(
            package
            for package in packages
            if package["name"] == member_ref.distribution
        )
        tm.that(u.Tests.toml_mapping(member_package["source"]), has="git")
        tm.that((root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"), eq=conformed)

    @staticmethod
    @pytest.mark.parametrize("explicit_overrides", [True, False])
    @pytest.mark.parametrize("declares_extras", [True, False])
    @pytest.mark.parametrize("content_only", [True, False])
    def test_generated_workspace_view_retains_member_groups(
        tmp_path: Path,
        *,
        declares_extras: bool,
        content_only: bool,
        explicit_overrides: bool,
    ) -> None:
        """Resolve actual projected member groups and both declared-extra shapes."""
        root = tmp_path / "workspace"
        member = root / "member"
        directory = root / "resolution"
        root_name = "resolution-root"
        member_name = "resolution-member"
        leaves = {
            name: tmp_path / name
            for name in (
                "resolution-runtime",
                "resolution-root-dev",
                "resolution-member-dev",
                "resolution-member-examples",
                "resolution-feature",
                "resolution-member-feature",
            )
        }
        for name, path in leaves.items():
            u.Tests.write_native_resolution_project(path, name)
        optional = ("resolution-feature>=1.0.0",) if declares_extras else None
        member_bound = (
            f"{member_name}>=1.0.0; python_full_version >= "
            f'"{config.Infra.codegen.toolchain.python_version}"'
        )
        overrides = (
            (
                (
                    f"{root_name}>=1.0.0,<2.0.0; python_full_version >= "
                    f'"{config.Infra.codegen.toolchain.python_version}"'
                ),
                f"{member_name}>=1.0.0,<2.0.0",
            )
            if explicit_overrides and not content_only
            else ((f"{member_name}>=1.0.0,<2.0.0",) if explicit_overrides else ())
        )
        root_extra_source = (
            "resolution-feature = "
            f"{{path = {json.dumps(str(leaves['resolution-feature']))}, "
            'extra = "feature"}\n'
            if declares_extras
            else ""
        )
        member_extra_source = (
            "resolution-member-feature = "
            f"{{path = {json.dumps(str(leaves['resolution-member-feature']))}, "
            'extra = "feature"}\n'
            if declares_extras
            else ""
        )
        u.Tests.write_native_resolution_project(
            root,
            root_name,
            dependencies=(
                f"resolution-runtime @ {leaves['resolution-runtime'].as_uri()}",
                member_bound,
            ),
            groups=(
                ""
                if optional is None
                else "[project.optional-dependencies]\n"
                f"feature = {json.dumps(list(optional))}\n"
            )
            + '[dependency-groups]\ndev = ["resolution-root-dev>=1.0.0"]\n',
            uv=(
                "[tool.uv]\n"
                f"override-dependencies = {json.dumps(overrides)}\n"
                "[tool.uv.sources]\nresolution-root-dev = "
                f"{{path = {json.dumps(str(leaves['resolution-root-dev']))}}}\n"
                f'{member_name} = {{path = "member", editable = false}}\n'
                f"{root_extra_source}"
            ),
        )
        u.Tests.write_native_resolution_project(
            member,
            member_name,
            groups=(
                ""
                if not declares_extras
                else "[project.optional-dependencies]\nfeature = "
                f"{json.dumps(['resolution-member-feature>=1.0.0'])}\n"
            )
            + (
                "[dependency-groups]\n"
                'dev = ["resolution-member-dev>=1.0.0"]\n'
                'examples = [{include-group = "dev"}, '
                f'"resolution-member-examples @ '
                f'{leaves["resolution-member-examples"].as_uri()}"]\n'
            ),
            uv=(
                "[tool.uv.sources]\nresolution-member-dev = "
                f"{{path = {json.dumps(str(leaves['resolution-member-dev']))}, "
                'group = "dev"}\n'
                f"{member_extra_source}"
                "[tool.uv.dependency-groups]\n"
                f'dev = {{requires-python = "{config.Infra.codegen.toolchain.python_required_version}"}}\n'
            ),
        )
        root_document = u.Tests.toml_doc(
            (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
        )
        member_document = u.Tests.toml_doc(
            (member / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
        )
        original = (
            u.Cli.toml_dumps(root_document),
            u.Cli.toml_dumps(member_document),
        )
        root_input = m.Infra.UvResolutionProject(
            repository=u.Tests.repository_ref(root_name).model_copy(
                update={"package": not content_only, "editable": True},
            ),
            directory=root,
            document=root_document,
        )
        member_input = m.Infra.UvResolutionProject(
            repository=u.Tests.repository_ref(member_name).model_copy(
                update={"editable": False},
            ),
            directory=member,
            document=member_document,
        )
        policy = config.Infra.codegen.make.uv_resolution
        view = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                root_input,
                members=(member_input,),
                directory=directory,
                policy=policy,
            ),
        )
        payload = u.Tests.toml_doc_mapping(view)
        uv = u.Tests.toml_mapping(u.Tests.toml_mapping(payload["tool"])["uv"])
        view_overrides = u.Tests.toml_strings(uv["override-dependencies"])
        for override in overrides:
            tm.that(view_overrides, has=override)
        tm.that(
            u.Tests.toml_strings(uv["constraint-dependencies"]),
            has=u.Infra.dependency_constraint(member_bound, replace_source=True),
        )
        sources = u.Tests.toml_mapping(uv["sources"])
        tm.that(
            u.Tests.toml_mapping(sources[member_name])["editable"],
            eq=member_input.repository.editable,
        )
        if not content_only:
            tm.that(
                u.Tests.toml_mapping(sources[root_name])["editable"],
                eq=root_input.repository.editable,
            )
        group_name = f"{member_name}{policy.member_group_separator}dev"
        groups = u.Tests.toml_mapping(payload["dependency-groups"])
        binding_group = root_name + policy.virtual_distribution_suffix
        tm.that(
            u.Tests.toml_strings(groups[binding_group]),
            eq=(member_name + ("[feature]" if declares_extras else ""),),
        )
        if not content_only:
            tm.that(
                u.Tests.toml_strings(
                    u.Tests.toml_mapping(payload["project"])["dependencies"],
                ),
                eq=(root_name + ("[feature]" if declares_extras else ""),),
            )
        tm.that(groups, has=group_name)
        tm.that(
            u.Tests.toml_list(
                groups[f"{member_name}{policy.member_group_separator}examples"],
            )[0],
            eq={"include-group": group_name},
        )
        directory.mkdir()
        tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, view))
        process = tm.ok(u.Tests.resolve_native_identity_fixture(directory))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        packages = set(
            u.Tests.toml_strings([
                package["name"]
                for package in u.Tests.toml_tables_at(
                    (directory / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
                    "package",
                )
            ]),
        )
        for name in leaves:
            tm.that(
                name in packages,
                eq=declares_extras
                or name not in {"resolution-feature", "resolution-member-feature"},
            )
        tm.that(
            (u.Cli.toml_dumps(root_document), u.Cli.toml_dumps(member_document)),
            eq=original,
        )
        second = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                root_input,
                members=(member_input,),
                directory=directory,
                policy=policy,
            ),
        )
        tm.that(u.Cli.toml_dumps(second), eq=u.Cli.toml_dumps(view))

    @staticmethod
    @pytest.mark.parametrize(
        ("identity", "expected_error", "preserves_groups"),
        [
            (
                "source-only",
                "Requirements contain conflicting URLs for package `identity-root`",
                False,
            ),
            ("global-self", None, False),
            (
                "scoped-self-unmapped",
                (
                    "`identity-root` is included as a workspace member, "
                    "but is missing an entry in `tool.uv.sources`"
                ),
                False,
            ),
            (
                "scoped-self",
                (
                    "Scoped override for `identity-provider` cannot use a URL "
                    "or path source for `identity-root`"
                ),
                False,
            ),
            ("virtual-root", None, True),
        ],
    )
    def test_native_self_identity_preserves_group_graph(
        tmp_path: Path,
        identity: str,
        *,
        expected_error: str | None,
        preserves_groups: bool,
    ) -> None:
        """Qualify source identity against native resolution and actual groups.

        A successful resolution that loses development or example dependencies
        is a broken candidate. The real Git backedge must not be removed from
        the provider to make a local root resolve.
        """
        root = tmp_path / "root"
        remote = tmp_path / "root-origin"
        provider = tmp_path / "provider"
        root_name = "identity-root"
        provider_name = "identity-provider"
        leaves = {
            name: tmp_path / name
            for name in (
                "identity-runtime",
                "identity-dev",
                "identity-examples",
                "identity-extra",
                "identity-inactive",
            )
        }
        for name, path in leaves.items():
            u.Tests.write_native_resolution_project(path, name)
        u.Tests.write_native_resolution_project(remote, root_name)
        u.Tests.initialize_git_repo(remote)
        revision = tm.ok(
            u.Cli.capture([c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD], cwd=remote),
        ).strip()
        backedge = f"{root_name} @ git+{remote.as_uri()}@{revision}"
        u.Tests.write_native_resolution_project(
            provider,
            provider_name,
            dependencies=(backedge,),
        )
        u.Tests.initialize_git_repo(provider)
        provider_revision = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD],
                cwd=provider,
            ),
        ).strip()
        provider_requirement = (
            f"{provider_name} @ git+{provider.as_uri()}@{provider_revision}"
        )
        development = (
            provider_requirement,
            f"identity-dev @ {leaves['identity-dev'].as_uri()}",
        )
        examples = f"identity-examples @ {leaves['identity-examples'].as_uri()}"
        groups = (
            "[dependency-groups]\n"
            f"dev = {json.dumps(development)}\n"
            'examples = [{include-group = "dev"}, '
            f"{json.dumps(examples)}]\n"
        )
        optional = (
            (
                f"identity-extra @ {leaves['identity-extra'].as_uri()}"
                " ; python_full_version >= "
                f'"{config.Infra.codegen.toolchain.python_version}"'
            ),
            (
                f"identity-inactive @ {leaves['identity-inactive'].as_uri()}"
                " ; python_full_version < "
                f'"{config.Infra.codegen.toolchain.python_version}"'
            ),
        )
        policy = '[tool.uv]\nconstraint-dependencies = ["identity-runtime==1.0.0"]\n'
        match identity:
            case "source-only":
                policy += f"[tool.uv.sources]\n{root_name} = {{workspace = true}}\n"
            case "global-self":
                policy += (
                    f'override-dependencies = ["{root_name}[feature]"]\n'
                    f"[tool.uv.sources]\n{root_name} = {{workspace = true}}\n"
                )
            case "scoped-self" | "scoped-self-unmapped":
                policy += (
                    "override-dependencies = ["
                    f'{{package = {{name = "{provider_name}"}}, '
                    f'dependencies = ["{root_name}"]}}]\n'
                )
                if identity == "scoped-self":
                    policy += f"[tool.uv.sources]\n{root_name} = {{workspace = true}}\n"
        u.Tests.write_native_resolution_project(
            root,
            root_name,
            dependencies=(f"identity-runtime @ {leaves['identity-runtime'].as_uri()}",),
            optional=optional,
            groups=groups,
            uv=policy,
        )
        resolution_root = root
        if identity == "virtual-root":
            resolution_root = tmp_path / "resolution"
            resolution_root.mkdir()
            view = tm.ok(
                u.Infra.pyproject_native_resolution_view(
                    m.Infra.UvResolutionProject(
                        repository=u.Tests.repository_ref(root_name),
                        directory=root,
                        document=u.Tests.toml_doc(
                            (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                        ),
                    ),
                    members=(),
                    directory=resolution_root,
                    policy=config.Infra.codegen.make.uv_resolution,
                ),
            )
            tm.ok(
                u.Cli.toml_write_document(
                    resolution_root / c.PYPROJECT_FILENAME,
                    view,
                ),
            )
        declared = (root / c.PYPROJECT_FILENAME).read_bytes()
        process = tm.ok(u.Tests.resolve_native_identity_fixture(resolution_root))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=expected_error is None,
            msg=process.stdout + process.stderr,
        )
        tm.that((root / c.PYPROJECT_FILENAME).read_bytes(), eq=declared)
        if expected_error is not None:
            tm.that(
                process.stdout + process.stderr,
                has=expected_error,
            )
            tm.that((root / c.Infra.UV_LOCK_FILENAME).exists(), eq=False)
            return
        locked = u.Tests.toml_tables_at(
            (resolution_root / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
            "package",
        )
        packages = set(u.Tests.toml_strings([package["name"] for package in locked]))
        tm.that(packages, has="identity-runtime")
        tm.that(packages, has="identity-extra")
        tm.that(packages, lacks="identity-inactive")
        for dependency in (provider_name, "identity-dev", "identity-examples"):
            tm.that(dependency in packages, eq=preserves_groups)
        tm.that(sum(package["name"] == root_name for package in locked), eq=1)
        candidate = next(package for package in locked if package["name"] == root_name)
        tm.that(u.Tests.toml_mapping(candidate["source"]), lacks="git")
