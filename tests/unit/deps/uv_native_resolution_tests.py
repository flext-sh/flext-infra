"""Local native UV qualification of self identity and dependency-group graphs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
from pathlib import Path

from flext_infra import config
from tests import c, m, p, t, tm, u


class TestsFlextInfraUvNativeResolution:
    """Resolve real local Git packages without external-service prerequisites."""

    @staticmethod
    def test_override_layers_elect_local_source_without_losing_inherited_policy(
        tmp_path: Path,
    ) -> None:
        """Compose real config layers and render only the elected global source."""
        repository = u.Tests.repository_ref("override-layer-consumer")
        sdk = u.Tests.repository_ref("override-layer-sdk")
        inherited = config.Infra.codegen.toolchain.uv_override_dependencies
        project_source = (
            f"{sdk.distribution.replace('-', '_').upper()} @ "
            f"git+{sdk.url}@project-policy"
        )
        local_source = f"{sdk.distribution} @ git+{sdk.url}@local-policy"
        marked = f'{sdk.distribution}>=2 ; sys_platform == "other-platform"'
        scoped: t.JsonDict = {
            "package": {"name": "override-layer-provider"},
            "dependencies": ["override-layer-leaf>=1"],
        }
        layers: tuple[tuple[str, t.JsonValueList], ...] = (
            ("codegen.yaml", [project_source, scoped, marked]),
            ("codegen.local.yaml", [local_source]),
        )
        for filename, entries in layers:
            tm.ok(
                u.Cli.yaml_dump(
                    tmp_path / "config" / filename,
                    {
                        "Infra": {
                            "codegen": {
                                "toolchain": {"uv_override_dependencies": entries}
                            }
                        }
                    },
                )
            )
        toolchain = tm.ok(u.Infra.load_codegen_inputs(tmp_path)).spec.toolchain
        u.Tests.write_native_resolution_project(tmp_path, repository.distribution)
        source = (tmp_path / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        resolution = m.Infra.UvResolutionSpec.model_validate({
            "link_mode": (toolchain.uv_link_mode),
            "constraint_dependencies": (tuple(toolchain.uv_constraint_dependencies)),
            "override_dependencies": (tuple(toolchain.uv_override_dependencies)),
            "environments": (tuple(toolchain.uv_environments)),
        })
        options = u.Infra.PyprojectConformOptions(
            flext_line=u.Tests.integration().model_copy(
                update={"base_url": u.Tests.provider().base_url}
            )
        )
        rendered = tm.ok(
            u.Infra.pyproject_conform(
                source,
                workspace=u.Tests.workspace_spec(repository),
                required_dev_dependencies=(),
                uv_resolution=resolution,
                options=options,
            )
        )
        observed = u.Tests.toml_list(
            u.Tests.toml_table_at(rendered, "tool", "uv")["override-dependencies"]
        )
        for entry in inherited:
            expected = (
                entry
                if isinstance(entry, str)
                else entry.model_dump(mode="json", exclude_none=True)
            )
            tm.that(observed, has=expected)
        tm.that(observed, has=local_source)
        tm.that(observed, lacks=project_source)
        tm.that(observed, has=scoped)
        tm.that(observed, has=marked)
        tm.that(
            tm.ok(
                u.Infra.pyproject_conform(
                    rendered,
                    workspace=u.Tests.workspace_spec(repository),
                    required_dev_dependencies=(),
                    uv_resolution=resolution,
                    options=options,
                )
            ),
            eq=rendered,
        )

    @staticmethod
    def _conformed_alias_document(
        root: Path,
        repository: p.Infra.RepositoryRef,
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
                    cooldown_days=toolchain.dependency_cooldown_days,
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
    ) -> p.Infra.LockedEnvironment:
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
    def test_conformed_group_aliases_resolve_without_merging_dependency_tiers(
        tmp_path: Path,
    ) -> None:
        """Real UV consumes authored aliases and includes after public conformance.

        This bounded native grammar fixture declares no generated dev floors.
        The separate first-party-profile scenario qualifies the SSOT floor set.
        """
        root = tmp_path / "project"
        repository = u.Tests.repository_ref("native-alias-root")
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
        extra_name = "feature"
        u.Tests.write_native_resolution_project(
            root,
            repository.distribution,
            dependencies=(requirements["runtime"],),
            groups=(
                "[project.optional-dependencies]\n"
                f"{extra_name} = [{json.dumps(requirements['extra'])}]\n"
                "[dependency-groups]\n"
                f"{dev} = [{json.dumps(requirements['development'])}]\n"
                f'{codegen} = [{{include-group = "{dev}"}}]\n'
                f'examples = [{{include-group = "{codegen}"}}, '
                f"{json.dumps(requirements['examples'])}]\n"
            ),
        )
        conformed = TestsFlextInfraUvNativeResolution._conformed_alias_document(
            root,
            repository,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(root / c.PYPROJECT_FILENAME, conformed),
        )
        directory = tmp_path / "resolution"
        view = u.Tests.toml_doc(conformed)
        groups = u.Tests.toml_mapping(
            u.Tests.toml_doc_mapping(view)["dependency-groups"],
        )
        tm.that(u.Tests.toml_list(groups[codegen]), eq=({"include-group": dev},))
        tm.that(
            u.Tests.toml_list(groups["examples"])[0],
            eq={"include-group": codegen},
        )
        locked = TestsFlextInfraUvNativeResolution._resolved_identity_lock(
            directory,
            view,
        )
        tm.that(
            {repository.distribution, *names.values()}.issubset(
                {package.name for package in locked.package},
            ),
            eq=True,
        )
        package = next(
            package
            for package in locked.package
            if package.name == repository.distribution
        )
        tm.that(
            {dependency.name for dependency in package.dependencies},
            eq={names["runtime"]},
        )
        tm.that(
            {
                dependency.name
                for dependency in package.optional_dependencies[extra_name]
            },
            eq={names["extra"]},
        )
        tm.that(
            (root / c.PYPROJECT_FILENAME).read_text(encoding=c.DEFAULT_ENCODING),
            eq=conformed,
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
    @c.Tests.MARK.parametrize("source_kind", ["path", "git"])
    def test_package_owned_runtime_source_is_resolved_natively(
        tmp_path: Path,
        source_kind: str,
    ) -> None:
        """Observe dependency-local runtime sources through real package metadata."""
        directory = tmp_path / "consumer"
        provider = tmp_path / "provider"
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
        u.Tests.write_native_resolution_project(
            directory,
            "runtime-owned-consumer",
            dependencies=(f"{provider_name}>=1.0.0",),
            uv=f"[tool.uv.sources]\n{provider_name} = {source}\n",
        )
        declared = (directory / c.PYPROJECT_FILENAME).read_bytes()
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
        tm.that((directory / c.PYPROJECT_FILENAME).read_bytes(), eq=declared)

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("identity", "expected_error"),
        [
            (
                "source-only",
                "Requirements contain conflicting URLs for package `identity-root`",
            ),
            ("global-self", None),
            (
                "scoped-self-unmapped",
                (
                    "`identity-root` is included as a workspace member, "
                    "but is missing an entry in `tool.uv.sources`"
                ),
            ),
            (
                "scoped-self",
                (
                    "Scoped override for `identity-provider` cannot use a URL "
                    "or path source for `identity-root`"
                ),
            ),
        ],
    )
    def test_native_self_identity_preserves_group_graph(
        tmp_path: Path,
        identity: str,
        *,
        expected_error: str | None,
    ) -> None:
        """Qualify source identity against native resolution and actual groups.

        A successful self-identity override resolves without the development or
        example dependencies, so it is not a candidate. The real Git backedge
        must not be removed from the provider to make a local root resolve.
        """
        root, root_name, provider_name = (
            TestsFlextInfraUvNativeResolution._write_self_identity_graph(
                tmp_path, identity
            )
        )
        declared = (root / c.PYPROJECT_FILENAME).read_bytes()
        process = tm.ok(u.Tests.resolve_native_identity_fixture(root))
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
            tm.fail((root / c.Infra.UV_LOCK_FILENAME).exists())
            return
        locked = u.Tests.toml_tables_at(
            (root / c.Infra.UV_LOCK_FILENAME).read_text(encoding="utf-8"),
            "package",
        )
        packages = set(u.Tests.toml_strings([package["name"] for package in locked]))
        tm.that(packages, has="identity-runtime")
        tm.that(packages, has="identity-extra")
        tm.that(packages, lacks="identity-inactive")
        for dependency in (provider_name, "identity-dev", "identity-examples"):
            tm.that(dependency in packages, eq=False)
        tm.that(sum(package["name"] == root_name for package in locked), eq=1)
        candidate = next(package for package in locked if package["name"] == root_name)
        tm.that(u.Tests.toml_mapping(candidate["source"]), lacks="git")

    @staticmethod
    def _write_self_identity_graph(
        tmp_path: Path, identity: str
    ) -> tuple[Path, str, str]:
        """Materialize the same local Git graph and declared dependency groups.

        Returns:
            The real root and both distribution identities used by consumers.

        Raises:
            ValueError: The fixture identity is not a declared resolution scenario.

        """
        root = tmp_path / "root"
        remote = tmp_path / "root-origin"
        provider = tmp_path / "provider"
        root_name = "identity-root"
        provider_name = "identity-provider"
        extra_name = "feature"
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
        u.Tests.write_native_resolution_project(
            provider,
            provider_name,
            dependencies=(f"{root_name} @ git+{remote.as_uri()}@{revision}",),
        )
        u.Tests.initialize_git_repo(provider)
        provider_revision = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD],
                cwd=provider,
            ),
        ).strip()
        development = (
            f"{provider_name} @ git+{provider.as_uri()}@{provider_revision}",
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
                    f'override-dependencies = ["{root_name}[{extra_name}]"]\n'
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
            case _:
                msg = f"Unknown native resolution fixture identity: {identity}"
                raise ValueError(msg)
        u.Tests.write_native_resolution_project(
            root,
            root_name,
            dependencies=(f"identity-runtime @ {leaves['identity-runtime'].as_uri()}",),
            groups=(
                "[project.optional-dependencies]\n"
                f"{extra_name} = {json.dumps(list(optional))}\n"
                f"{groups}"
                f"{policy}"
            ),
        )
        return root, root_name, provider_name
