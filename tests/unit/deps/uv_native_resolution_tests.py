"""Local native UV qualification of self identity and dependency-group graphs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest
from packaging.requirements import Requirement

from flext_infra import config
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)
from tests import c, m, t, tm, u


class TestsFlextInfraUvNativeResolution:
    """Resolve real local Git packages without external-service prerequisites."""

    @staticmethod
    def _conformed_alias_document(
        root: Path,
        repository: m.Infra.RepositoryRef,
    ) -> str:
        """Conform the authored alias fixture without merging dependency tiers.

        Args:
            root: Project directory holding the authored pyproject.
            repository: Repository reference of the fixture project.

        Returns:
            The conformed pyproject source text.

        """
        toolchain = config.Infra.codegen.toolchain
        return tm.ok(
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

    @staticmethod
    def _resolved_identity_lock(
        directory: Path,
        view: t.Cli.TomlDocument,
    ) -> m.Infra.LockedEnvironment:
        """Write the resolution view and resolve its native identity lock.

        Args:
            directory: Resolution directory receiving the conformed view.
            view: Conformed native resolution document to resolve.

        Returns:
            The locked environment produced by the native resolution.

        """
        directory.mkdir(parents=True)
        tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, view))
        process = tm.ok(u.Tests.resolve_native_identity_fixture(directory))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        return m.Infra.LockedEnvironment.model_validate_json(
            json.dumps(
                tm.ok(u.Cli.toml_read_json(directory / c.Infra.UV_LOCK_FILENAME)),
            ),
        )

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
            tier: f"{names[tier]} @ {path.as_uri()}" for tier, path in leaves.items()
        }
        dev = str(c.Infra.DEV).capitalize()
        codegen = str(c.Infra.DependencyGroup.CODEGEN).capitalize()
        u.Tests.write_native_resolution_project(
            root,
            root_name,
            dependencies=(requirements["runtime"],),
            groups=(
                "[project.optional-dependencies]\n"
                f"extra = [{json.dumps(requirements['extra'])}]\n"
                "[dependency-groups]\n"
                f"{dev} = [{json.dumps(requirements['development'])}]\n"
                f'{codegen} = [{{include-group = "{dev}"}}]\n'
                f'examples = [{{include-group = "{codegen}"}}, '
                f"{json.dumps(requirements['examples'])}]\n"
            ),
        )
        repository = u.Tests.repository_ref(root_name)
        conformed = TestsFlextInfraUvNativeResolution._conformed_alias_document(
            root,
            repository,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(root / c.PYPROJECT_FILENAME, conformed),
        )
        policy = config.Infra.codegen.make.uv_resolution
        directory = root / (
            policy.local_directory if mode == "local" else policy.standalone_directory
        )
        view = tm.ok(
            u.Infra.pyproject_native_resolution_view(
                m.Infra.UvResolutionProject(
                    repository=repository,
                    directory=root,
                    document=u.Tests.toml_doc(conformed),
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
        locked = TestsFlextInfraUvNativeResolution._resolved_identity_lock(
            directory,
            view,
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
            {
                dependency.name
                for dependency in package.optional_dependencies["feature"]
            },
            eq={names["extra"]},
        )
        tm.that(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
            eq=conformed,
        )

    @classmethod
    def _first_party_resolution_inputs(
        cls,
    ) -> tuple[
        Path,
        Path,
        m.Cli.AtomicFileState,
        m.Infra.WorkspaceIntegrationSpec,
        m.Infra.RepositoryRef,
        m.Infra.UvResolutionSpec,
    ]:
        """Resolve the live line, lock, supplier, and UV spec of this checkout.

        Returns:
            The runtime root, its checkout, the lock state, the detected
            integration line, the configured supplier reference, and the
            toolchain UV spec.

        """
        toolchain = config.Infra.codegen.toolchain
        checkout = Path(__file__).resolve().parents[3]
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(checkout))
        lock_state = tm.ok(
            u.Cli.atomic_read_binary_file_state(context.lock_path, required=True),
        )
        line = tm.ok(
            u.Infra.flext_integration_line(
                codegen=config.Infra.codegen,
                repository_root=checkout,
            ),
        )
        supplier = tm.ok(
            u.Infra.configured_repository_ref(
                codegen=config.Infra.codegen,
                repository_root=checkout,
            ),
        )
        resolution = m.Infra.UvResolutionSpec(
            link_mode=toolchain.uv_link_mode,
            constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
            environments=tuple(toolchain.uv_environments),
        )
        return context.runtime_root, checkout, lock_state, line, supplier, resolution

    @classmethod
    def _conformed_first_party_documents(
        cls,
        root: Path,
    ) -> t.MappingKV[str, t.Cli.TomlDocument]:
        """Retain complete conformed profile documents before internal qualification.

        Args:
            root: Directory receiving one conformed project per first-party member.

        Returns:
            Mapping of member distribution name to its conformed TOML document.

        """
        documents: dict[str, t.Cli.TomlDocument] = {}
        runtime_root, checkout, lock_state, line, supplier, resolution = (
            cls._first_party_resolution_inputs()
        )
        for name, upstream in (
            ("flext-core", "flext_core"),
            ("flext-cli", "flext_core"),
            ("flext-infra", "flext_cli"),
            ("flext-tests", "flext_cli"),
        ):
            declared = supplier.model_copy(
                update={
                    "name": name,
                    "distribution": name,
                    "url": f"{(line.base_url or 'https://github.com/flext-sh/').rstrip('/')}/{name}.git",
                    "path": (
                        checkout.relative_to(runtime_root)
                        if name == supplier.distribution
                        else Path(name)
                    ),
                },
            )
            captured = tm.ok(
                FlextInfraWorkspaceEnvironmentProvenance.member_project_declaration(
                    runtime_root,
                    declared,
                    lock_state=lock_state,
                ),
            )
            tm.ok(u.Infra.member_declaration_requirements(captured, name))
            source = tm.not_none(captured.content).decode(c.DEFAULT_ENCODING)
            path = root / name
            path.mkdir(parents=True)
            workspace = u.Tests.workspace_spec(
                u.Tests.repository_ref(name),
                project=u.Tests.project_spec(name).model_copy(
                    update={"upstream": upstream},
                ),
            ).model_copy(update={"integration": line})
            conformed = tm.ok(
                u.Infra.pyproject_conform(
                    source,
                    workspace=workspace,
                    required_dev_dependencies=u.Infra.project_development_requirements(
                        config.Infra.codegen.scaffold.project,
                        distribution=name,
                        kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                    ),
                    uv_resolution=resolution,
                    options=u.Infra.PyprojectConformOptions(
                        flext_line=line,
                    ),
                ),
            )
            cls._assert_requirement_tiers(conformed, source)
            tm.ok(u.Cli.atomic_write_text_file(path / c.PYPROJECT_FILENAME, conformed))
            documents[name] = u.Tests.toml_doc(conformed)
        return documents

    @staticmethod
    def _assert_requirement_tiers(
        conformed: str,
        source: str,
    ) -> None:
        """Read the complete consumer document without replacing its declared tiers."""
        before = u.Tests.toml_doc_mapping(u.Tests.toml_doc(source))
        after = u.Tests.toml_doc_mapping(u.Tests.toml_doc(conformed))
        source_project = u.Tests.toml_mapping(before["project"])
        observed_project = u.Tests.toml_mapping(after["project"])
        tm.that(
            {
                Requirement(requirement)
                for requirement in u.Tests.toml_list(
                    observed_project.get("dependencies", []),
                )
                if isinstance(requirement, str)
            },
            eq={
                Requirement(requirement)
                for requirement in u.Tests.toml_list(
                    source_project.get("dependencies", []),
                )
                if isinstance(requirement, str)
            },
        )
        tm.that(
            observed_project.get("optional-dependencies", {}),
            eq=source_project.get("optional-dependencies", {}),
        )
        source_groups = u.Tests.toml_mapping(before.get("dependency-groups", {}))
        observed_groups = u.Tests.toml_mapping(after.get("dependency-groups", {}))
        for name, entries in source_groups.items():
            observed = u.Tests.toml_list(observed_groups[name])
            for entry in u.Tests.toml_list(entries):
                if isinstance(entry, str):
                    tm.that(
                        Requirement(entry)
                        in {
                            Requirement(requirement)
                            for requirement in observed
                            if isinstance(requirement, str)
                        },
                        eq=True,
                    )
                else:
                    tm.that(entry in observed, eq=True)

    @staticmethod
    def _internal_requirement_document(
        document: t.Cli.TomlDocument,
        packages: t.MappingKV[str, Path],
    ) -> t.Cli.TomlDocument:
        """Qualify only the real internal edges, without fabricating third parties.

        Args:
            document: Conformed project document whose requirements are scoped.
            packages: Internal distributions mapped to their local checkout paths.

        Returns:
            A no-index qualification copy retaining internal requirements in
            their original categories, including extras and marker branches.

        """
        payload = cast(
            "dict[str, t.JsonValue]",
            deepcopy(u.Tests.toml_mapping(u.Cli.toml_unwrap_item(document))),
        )
        constraints: list[str] = []

        def internal(requirements: t.JsonValue) -> list[t.JsonValue]:
            selected: list[t.JsonValue] = []
            for raw in u.Tests.toml_list(requirements):
                if not isinstance(raw, str):
                    selected.append(raw)
                    continue
                requirement = Requirement(raw)
                if requirement.name not in packages:
                    continue
                if requirement.specifier:
                    constraints.append(
                        u.Infra.dependency_constraint(raw, replace_source=True),
                    )
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

        project = cast(
            "dict[str, t.JsonValue]", u.Tests.toml_mapping(payload["project"])
        )
        project["dependencies"] = internal(project.get("dependencies", []))
        optional = cast(
            "dict[str, t.JsonValue]",
            u.Tests.toml_mapping(project.get("optional-dependencies", {})),
        )
        for extra, requirements in optional.items():
            optional[extra] = internal(requirements)
        project["optional-dependencies"] = optional
        groups = cast(
            "dict[str, t.JsonValue]",
            u.Tests.toml_mapping(payload.get("dependency-groups", {})),
        )
        for group, requirements in groups.items():
            groups[group] = internal(requirements)
        payload["project"] = project
        payload["dependency-groups"] = groups
        tool = cast(
            "dict[str, t.JsonValue]", u.Tests.toml_mapping(payload.get("tool", {}))
        )
        uv = cast("dict[str, t.JsonValue]", u.Tests.toml_mapping(tool.get("uv", {})))
        if "override-dependencies" in uv:
            uv["override-dependencies"] = internal(uv["override-dependencies"])
        constraints.extend(
            requirement
            for requirement in u.Tests.toml_list(
                uv.get("constraint-dependencies", []),
            )
            if isinstance(requirement, str)
            and Requirement(requirement).name in packages
        )
        uv["constraint-dependencies"] = list(dict.fromkeys(constraints))
        tool["uv"] = uv
        payload["tool"] = tool
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
        complete = self._conformed_first_party_documents(tmp_path / "complete")
        packages = {name: tmp_path / "native" / name for name in complete}
        original = {
            name: u.Cli.toml_dumps(document) for name, document in complete.items()
        }
        inputs: dict[str, m.Infra.UvResolutionProject] = {}
        for name, document in complete.items():
            directory = packages[name]
            limited = self._internal_requirement_document(document, packages)
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
    def _provider_source_locator(
        directory: Path,
        provider_name: str,
    ) -> t.JsonMapping:
        """Read the locked source locator of one resolved provider package.

        Args:
            directory: Resolution directory holding the native lock file.
            provider_name: Distribution name of the resolved provider.

        Returns:
            The locked source locator mapping of the provider package.

        """
        packages = u.Tests.toml_tables_at(
            (directory / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
            "package",
        )
        resolved = next(
            package for package in packages if package["name"] == provider_name
        )
        return u.Tests.toml_mapping(resolved["source"])

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
            source = (
                f"{{git = {json.dumps(provider.as_uri())},"
                f" rev = {json.dumps(revision)}}}"
            )
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
        locator = TestsFlextInfraUvNativeResolution._provider_source_locator(
            directory,
            provider_name,
        )
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
    def _conformed_portable_root(
        root: Path,
        checkout: Path,
        root_ref: m.Infra.RepositoryRef,
        member_ref: m.Infra.RepositoryRef,
        *,
        marked: bool,
    ) -> tuple[str, Requirement]:
        """Author and conform the workspace root over a bare member origin.

        Args:
            root: Workspace root authoring the member dependency.
            checkout: Member checkout published to the bare origin.
            root_ref: Repository reference of the workspace root.
            member_ref: Repository reference of the member.
            marked: Whether the authored requirement carries an environment
                marker.

        Returns:
            The conformed root document and the authored member requirement.

        """
        origin = root.parent / "member-origin.git"
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
        if marked:
            requirement += ' ; python_version >= "0"'
        authored = Requirement(requirement)
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
                    member_declarations=(
                        tm.ok(
                            u.Cli.atomic_read_binary_file_state(
                                checkout / c.PYPROJECT_FILENAME,
                                required=True,
                            ),
                        ),
                    ),
                ),
            ),
        )
        return conformed, authored

    @staticmethod
    def _portable_resolution_views(
        root: Path,
        checkout: Path,
        root_ref: m.Infra.RepositoryRef,
        member_ref: m.Infra.RepositoryRef,
        conformed: str,
    ) -> tuple[t.Cli.TomlDocument, t.Cli.TomlDocument, Path]:
        """Project the local and standalone native resolution views.

        Args:
            root: Workspace root projected as the primary resolution input.
            checkout: Member checkout projected as the member input.
            root_ref: Repository reference of the workspace root.
            member_ref: Repository reference of the member.
            conformed: Conformed root document text to project.

        Returns:
            The local view, the standalone view, and the standalone
            resolution directory.

        """
        policy = config.Infra.codegen.make.uv_resolution
        root_input = m.Infra.UvResolutionProject(
            repository=root_ref,
            directory=root,
            document=u.Tests.toml_doc(conformed),
        )
        member_input = m.Infra.UvResolutionProject(
            repository=member_ref,
            directory=checkout,
            document=u.Tests.toml_doc(
                (checkout / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
        )
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
        return local, standalone, standalone_directory

    @staticmethod
    def _resolved_portable_member(
        standalone_directory: Path,
        standalone: t.Cli.TomlDocument,
        origin: Path,
        member_ref: m.Infra.RepositoryRef,
    ) -> t.JsonMapping:
        """Resolve the standalone view after the member checkout disappears.

        Args:
            standalone_directory: Directory receiving the standalone view.
            standalone: Standalone native resolution document.
            origin: Bare Git origin substituting the disappeared checkout.
            member_ref: Repository reference of the resolved member.

        Returns:
            The locked source locator of the Git-resolved member package.

        """
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
        return u.Tests.toml_mapping(member_package["source"])

    @staticmethod
    @pytest.mark.parametrize("marked", [False, True])
    def test_conformed_workspace_root_resolves_without_member_checkout(
        tmp_path: Path,
        *,
        marked: bool,
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
        conformed, authored = (
            TestsFlextInfraUvNativeResolution._conformed_portable_root(
                root,
                checkout,
                root_ref,
                member_ref,
                marked=marked,
            )
        )
        (root / c.PYPROJECT_FILENAME).write_text(conformed, encoding="utf-8")
        local, standalone, standalone_directory = (
            TestsFlextInfraUvNativeResolution._portable_resolution_views(
                root,
                checkout,
                root_ref,
                member_ref,
                conformed,
            )
        )
        actual_uv = u.Tests.toml_table_at(conformed, "tool", "uv")
        actual = u.Tests.toml_doc(conformed)
        member_requirements = tuple(
            Requirement(line)
            for line in tm.ok(u.Infra.document_requirement_lines(actual))
            if Requirement(line).name == member_ref.distribution
        )
        tm.that(bool(member_requirements), eq=True)
        for projected in member_requirements:
            tm.that(projected.url, eq=authored.url)
            tm.that(str(projected.marker), eq=str(authored.marker))
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
        tm.that(
            TestsFlextInfraUvNativeResolution._resolved_portable_member(
                standalone_directory,
                standalone,
                origin,
                member_ref,
            ),
            has="git",
        )
        tm.that((root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"), eq=conformed)

    @staticmethod
    def _member_groups_fixture(
        tmp_path: Path,
        *,
        declares_extras: bool,
        content_only: bool,
        explicit_overrides: bool,
    ) -> tuple[
        Path,
        Path,
        str,
        str,
        dict[str, Path],
        tuple[str, ...],
        str,
    ]:
        """Author a workspace plus member pair with grouped native sources.

        Args:
            tmp_path: Test-scoped scratch root.
            declares_extras: Whether both projects declare a feature extra.
            content_only: Whether the root participates as content only.
            explicit_overrides: Whether authored UV overrides are declared.

        Returns:
            The root, the member, both distribution names, the leaf provider
            paths, the authored overrides, and the bound member requirement.

        """
        root = tmp_path / "workspace"
        member = root / "member"
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
        required_python = config.Infra.codegen.toolchain.python_required_version
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
                f'dev = {{requires-python = "{required_python}"}}\n'
            ),
        )
        return root, member, root_name, member_name, leaves, overrides, member_bound

    @staticmethod
    def _member_groups_inputs(
        checkouts: t.Pair[Path, Path],
        names: t.Pair[str, str],
        *,
        content_only: bool,
    ) -> t.Pair[m.Infra.UvResolutionProject, m.Infra.UvResolutionProject]:
        """Build the projected root and member resolution inputs.

        Args:
            checkouts: Root and member checkout directories.
            names: Root and member distribution names.
            content_only: Whether the root participates as content only.

        Returns:
            The root and member resolution project inputs.

        """
        documents = (
            u.Tests.toml_doc(
                (checkouts[0] / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
            u.Tests.toml_doc(
                (checkouts[1] / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
            ),
        )
        return (
            m.Infra.UvResolutionProject(
                repository=u.Tests.repository_ref(names[0]).model_copy(
                    update={"package": not content_only, "editable": True},
                ),
                directory=checkouts[0],
                document=documents[0],
            ),
            m.Infra.UvResolutionProject(
                repository=u.Tests.repository_ref(names[1]).model_copy(
                    update={"editable": False},
                ),
                directory=checkouts[1],
                document=documents[1],
            ),
        )

    @staticmethod
    def _projected_member_view(
        inputs: t.Pair[m.Infra.UvResolutionProject, m.Infra.UvResolutionProject],
        root: Path,
    ) -> t.Cli.TomlDocument:
        """Project the native resolution view over the member inputs.

        Args:
            inputs: Root and member resolution project inputs.
            root: Workspace root owning the resolution directory.

        Returns:
            The projected native resolution view document.

        """
        return tm.ok(
            u.Infra.pyproject_native_resolution_view(
                inputs[0],
                members=(inputs[1],),
                directory=root / "resolution",
                policy=config.Infra.codegen.make.uv_resolution,
            ),
        )

    @staticmethod
    def _resolved_member_group_packages(
        root: Path,
        view: t.Cli.TomlDocument,
    ) -> set[str]:
        """Resolve the projected view natively and read its locked package names.

        Args:
            root: Workspace root owning the resolution directory.
            view: Projected native resolution view document.

        Returns:
            The locked package names of the native resolution.

        """
        directory = root / "resolution"
        directory.mkdir()
        tm.ok(u.Cli.toml_write_document(directory / c.PYPROJECT_FILENAME, view))
        process = tm.ok(u.Tests.resolve_native_identity_fixture(directory))
        tm.that(
            u.Cli.process_succeeded(process.outcome),
            eq=True,
            msg=process.stdout + process.stderr,
        )
        return set(
            u.Tests.toml_strings([
                package["name"]
                for package in u.Tests.toml_tables_at(
                    (directory / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
                    "package",
                )
            ]),
        )

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
        root, member, root_name, member_name, leaves, overrides, member_bound = (
            TestsFlextInfraUvNativeResolution._member_groups_fixture(
                tmp_path,
                declares_extras=declares_extras,
                content_only=content_only,
                explicit_overrides=explicit_overrides,
            )
        )
        original = (
            u.Cli.toml_dumps(
                u.Tests.toml_doc(
                    (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                ),
            ),
            u.Cli.toml_dumps(
                u.Tests.toml_doc(
                    (member / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                ),
            ),
        )
        inputs = TestsFlextInfraUvNativeResolution._member_groups_inputs(
            (root, member),
            (root_name, member_name),
            content_only=content_only,
        )
        view = TestsFlextInfraUvNativeResolution._projected_member_view(inputs, root)
        uv = u.Tests.toml_mapping(
            u.Tests.toml_mapping(u.Tests.toml_doc_mapping(view)["tool"])["uv"],
        )
        for override in overrides:
            tm.that(
                u.Tests.toml_strings(uv["override-dependencies"]),
                has=override,
            )
        tm.that(
            u.Tests.toml_strings(uv["constraint-dependencies"]),
            has=u.Infra.dependency_constraint(member_bound, replace_source=True),
        )
        tm.that(
            u.Tests.toml_mapping(u.Tests.toml_mapping(uv["sources"])[member_name])[
                "editable"
            ],
            eq=inputs[1].repository.editable,
        )
        if not content_only:
            tm.that(
                u.Tests.toml_mapping(u.Tests.toml_mapping(uv["sources"])[root_name])[
                    "editable"
                ],
                eq=inputs[0].repository.editable,
            )
        groups = u.Tests.toml_mapping(
            u.Tests.toml_doc_mapping(view)["dependency-groups"]
        )
        tm.that(
            u.Tests.toml_strings(
                groups[
                    root_name
                    + (
                        config.Infra.codegen.make.uv_resolution
                    ).virtual_distribution_suffix
                ]
            ),
            eq=(member_name + ("[feature]" if declares_extras else ""),),
        )
        if not content_only:
            tm.that(
                u.Tests.toml_strings(
                    u.Tests.toml_mapping(u.Tests.toml_doc_mapping(view)["project"])[
                        "dependencies"
                    ],
                ),
                eq=(root_name + ("[feature]" if declares_extras else ""),),
            )
        tm.that(
            groups,
            has=(
                f"{member_name}"
                f"{config.Infra.codegen.make.uv_resolution.member_group_separator}dev"
            ),
        )
        tm.that(
            u.Tests.toml_list(
                groups[
                    f"{member_name}"
                    f"{config.Infra.codegen.make.uv_resolution.member_group_separator}"
                    "examples"
                ],
            )[0],
            eq={
                "include-group": (
                    f"{member_name}"
                    f"{config.Infra.codegen.make.uv_resolution.member_group_separator}dev"
                )
            },
        )
        packages = TestsFlextInfraUvNativeResolution._resolved_member_group_packages(
            root,
            view,
        )
        for name in leaves:
            tm.that(
                name in packages,
                eq=declares_extras
                or name not in {"resolution-feature", "resolution-member-feature"},
            )
        tm.that(
            (
                u.Cli.toml_dumps(
                    u.Tests.toml_doc(
                        (root / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                    ),
                ),
                u.Cli.toml_dumps(
                    u.Tests.toml_doc(
                        (member / c.PYPROJECT_FILENAME).read_text(encoding="utf-8"),
                    ),
                ),
            ),
            eq=original,
        )
        second = TestsFlextInfraUvNativeResolution._projected_member_view(inputs, root)
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
        root, root_name, provider_name = (
            TestsFlextInfraUvNativeResolution._write_self_identity_graph(
                tmp_path, identity
            )
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

    @staticmethod
    def _write_self_identity_graph(
        tmp_path: Path, identity: str
    ) -> t.Triple[Path, str, str]:
        """Materialize the same local Git graph and declared dependency groups.

        Returns:
            The real root and both distribution identities used by consumers.

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
            groups=(
                "[project.optional-dependencies]\n"
                f"extra = {json.dumps(list(optional))}\n"
                f"{groups}"
                f"{policy}"
            ),
        )
        return root, root_name, provider_name
