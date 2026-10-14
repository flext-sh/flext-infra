"""Local native UV qualification of self identity and dependency-group graphs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraUvNativeResolution:
    """Resolve real local Git packages without external-service prerequisites."""

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
            optional=optional,
            groups='[dependency-groups]\ndev = ["resolution-root-dev>=1.0.0"]\n',
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
            optional=("resolution-member-feature>=1.0.0",) if declares_extras else None,
            groups=(
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
