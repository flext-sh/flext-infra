"""Local native UV qualification of portable roots and generated member views.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from flext_infra import config
from tests import c, m, t, tm, u


class TestsFlextInfraUvNativeResolutionWorkspace:
    """Resolve portable workspace roots and generated member views natively."""

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
            TestsFlextInfraUvNativeResolutionWorkspace._conformed_portable_root(
                root,
                checkout,
                root_ref,
                member_ref,
                marked=marked,
            )
        )
        (root / c.PYPROJECT_FILENAME).write_text(conformed, encoding="utf-8")
        local, standalone, standalone_directory = (
            TestsFlextInfraUvNativeResolutionWorkspace._portable_resolution_views(
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
            TestsFlextInfraUvNativeResolutionWorkspace._resolved_portable_member(
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
            TestsFlextInfraUvNativeResolutionWorkspace._member_groups_fixture(
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
        inputs = TestsFlextInfraUvNativeResolutionWorkspace._member_groups_inputs(
            (root, member),
            (root_name, member_name),
            content_only=content_only,
        )
        view = TestsFlextInfraUvNativeResolutionWorkspace._projected_member_view(inputs, root)
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
        packages = TestsFlextInfraUvNativeResolutionWorkspace._resolved_member_group_packages(
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
        second = TestsFlextInfraUvNativeResolutionWorkspace._projected_member_view(inputs, root)
        tm.that(u.Cli.toml_dumps(second), eq=u.Cli.toml_dumps(view))

