"""Hermetic Git provider: local bare mirrors that keep fixture sources real.

Governed fixtures declare their internal dependencies with direct Git sources
(a source-less internal dependency fails loudly), so ``uv lock`` inside a
fixture resolves those sources. These helpers serve the exact locked revisions
from local bare mirrors built out of objects this checkout already holds, and
the environment they return makes any network transport fail instead of
silently reaching a remote.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

from flext_infra import config, u
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, m, p, t, tm
from tests.utilities_fixture_project import TestsFlextInfraUtilitiesProjectFixtureMixin
from tests.utilities_toml import TestsFlextInfraUtilitiesTomlMixin


class TestsFlextInfraUtilitiesHermeticGitMixin:
    """Build and route the fixture provider through local Git mirrors."""

    @staticmethod
    def write_native_resolution_project(
        root: Path,
        distribution: str,
        *,
        dependencies: t.StrSequence = (),
        groups: str = "",
        uv: str = "",
    ) -> None:
        """Write static package metadata consumed by the real UV resolver.

        These are actual local packages, rather than command stand-ins. Their
        build backend and supported Python range follow the production owner.
        No build or installation is performed by this metadata fixture.
        ``groups`` carries any extra TOML text inserted after the ``[project]``
        dependencies, such as optional feature tables and dependency groups.
        """
        root.mkdir(parents=True, exist_ok=True)
        build = config.Infra.codegen.scaffold.build
        python = config.Infra.codegen.toolchain.python_required_version
        (root / c.PYPROJECT_FILENAME).write_text(
            "[build-system]\n"
            f"requires = {json.dumps(list(build.requirements))}\n"
            f"build-backend = {json.dumps(build.backend)}\n"
            "[project]\n"
            f"name = {json.dumps(distribution)}\n"
            'version = "1.0.0"\n'
            f"requires-python = {json.dumps(python)}\n"
            f"dependencies = {json.dumps(list(dependencies))}\n"
            f"{groups}\n{uv}\n",
            encoding="utf-8",
        )
        package = root / "src" / distribution.replace("-", "_")
        package.mkdir(parents=True, exist_ok=True)
        (package / "__init__.py").write_text(
            'IDENTITY = "native-resolution-fixture"\n',
            encoding="utf-8",
        )

    @staticmethod
    def resolve_native_identity_fixture(
        root: Path,
        *,
        git_environment: t.StrMapping | None = None,
    ) -> p.Result[p.Cli.CommandOutput]:
        """Observe native resolution without network, installation or lock repair.

        The caller is an owned test reached through the repository Make test
        surface. Its local Git origins remain real repositories; no resolver
        command, dependency metadata or failure is substituted.

        Returns:
            The raw resolver command outcome.
        """
        return u.Cli.run_raw(
            [
                c.Infra.UV,
                "lock",
                "--no-index",
                "--python",
                sys.executable,
                "--project",
                str(root),
            ],
            cwd=root,
            options=m.Cli.ProcessOptions(
                env={
                    **(git_environment or {}),
                    "GIT_ALLOW_PROTOCOL": "file",
                    "UV_NO_GITHUB_FAST_PATH": "1",
                },
                remove_env_keys=(*c.Tests.MAKE_ISOLATION_ENV_KEYS, "UV_OFFLINE"),
            ),
        )

    @staticmethod
    def locked_git_sources(
        project_root: Path,
    ) -> t.VariadicTuple[t.Triple[str, str, str]]:
        """Return every ``(url, rev, sha)`` Git source the checkout lock pins.

        The checkout itself is not in its lock; it joins as the infrastructure
        repository the fixture provider serves, at the checked-out commit.

        Returns:
            Every ``(url, rev, sha)`` Git source the checkout lock pins.

        """
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(project_root))
        lock = context.lock_path.read_text(encoding="utf-8")
        sources: t.MutableMappingKV[str, t.Triple[str, str, str]] = {}
        for package in TestsFlextInfraUtilitiesTomlMixin.toml_tables_at(
            lock, "package"
        ):
            source = TestsFlextInfraUtilitiesTomlMixin.toml_mapping(
                package.get("source")
            )
            locator = source.get("git")
            if isinstance(locator, str):
                parts = urlsplit(locator)
                url = f"{parts.scheme}://{parts.netloc}{parts.path}"
                (rev,) = parse_qs(parts.query)["rev"]
                sources[url] = (url, unquote(rev), parts.fragment)
                continue
            local = source.get("editable", source.get("directory"))
            if isinstance(local, str):
                directory = (context.lock_path.parent / local).resolve()
                repository = tm.ok(
                    FlextInfraWorkspaceDetector.load_workspace_spec(directory),
                ).repository
                tm.that(repository.distribution, eq=package.get("name"))
                head = tm.ok(
                    u.Cli.capture(
                        [c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD],
                        cwd=directory,
                    ),
                ).strip()
                sources[repository.url] = (
                    repository.url,
                    tm.ok(
                        u.Infra.flext_integration_line(
                            codegen=tm.ok(u.Infra.load_codegen_inputs(directory)).spec,
                            repository_root=directory,
                        ),
                    ).branch,
                    head,
                )
        infra = TestsFlextInfraUtilitiesProjectFixtureMixin.repository_ref(
            config.Infra.codegen.infra_repository.distribution,
        ).url
        head = tm.ok(
            u.Cli.capture(
                [c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD],
                cwd=project_root,
            ),
        ).strip()
        sources[infra] = (
            infra,
            TestsFlextInfraUtilitiesProjectFixtureMixin.provider_branch(),
            head,
        )
        return tuple(sources.values())

    @staticmethod
    def build_git_mirrors(project_root: Path, mirrors: Path) -> t.StrSequence:
        """Mirror each locked source's exact commit under its host and path.

        Objects come from this checkout or from the Git databases ``make setup``
        and ``make upg`` fetched into the native uv cache selected by the
        activated environment. Query uv itself so the fixture follows the same
        cache configuration as provisioning. No source is fetched from its remote;
        a commit found nowhere locally fails loudly: ``make setup`` provisions it.
        Each mirror borrows the origin database through ``objects/info/alternates``
        and pins only the branch ref: full history at zero copy cost (git
        refuses to update shallow roots, so a shallow mirror cannot serve a
        client whose uv cache lacks the history).

        Returns:
            The resulting ``t.StrSequence``.

        Raises:
            FileNotFoundError: If locked Git source is not held locally.

        """
        cache = Path(
            tm.ok(
                u.Cli.capture([c.Infra.UV, "cache", "dir"], cwd=project_root),
            ).strip(),
        )
        context = tm.ok(FlextInfraWorkspaceDetector.resolution_context(project_root))
        workspace = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(context.runtime_root),
        )
        databases = (
            project_root,
            context.runtime_root,
            *(context.runtime_root / member.path for member in workspace.subprojects),
            *sorted(cache.glob("git-v*/db/*")),
        )
        mirrored: list[str] = []
        for (
            url,
            rev,
            sha,
        ) in TestsFlextInfraUtilitiesHermeticGitMixin.locked_git_sources(project_root):
            origin = next(
                (
                    database
                    for database in databases
                    if u.Cli.process_succeeded(
                        tm.ok(
                            u.Cli.run_raw(
                                [c.Infra.GIT, "cat-file", "-e", f"{sha}^{{commit}}"],
                                cwd=database,
                            ),
                        ).outcome,
                    )
                ),
                None,
            )
            if origin is None:
                msg = f"locked Git source is not held locally: {url}@{sha}"
                raise FileNotFoundError(msg)
            parts = urlsplit(url)
            mirror = mirrors / parts.netloc / parts.path.lstrip("/")
            tm.ok(
                u.Cli.run_checked([
                    c.Infra.GIT,
                    "init",
                    "--quiet",
                    "--bare",
                    str(mirror),
                ]),
            )
            common = tm.ok(
                u.Cli.capture(
                    [
                        c.Infra.GIT,
                        "rev-parse",
                        "--path-format=absolute",
                        "--git-common-dir",
                    ],
                    cwd=origin,
                ),
            ).strip()
            tm.ok(
                u.Cli.atomic_write_text_file(
                    mirror / "objects" / "info" / "alternates",
                    f"{Path(common) / 'objects'}\n",
                ),
            )
            tm.ok(
                u.Cli.run_checked(
                    [c.Infra.GIT, "update-ref", f"refs/heads/{rev}", sha],
                    cwd=mirror,
                ),
            )
            mirrored.append(f"{url}@{rev}#{sha}")
        return tuple(mirrored)

    @staticmethod
    def hermetic_git_environment(mirrors: Path) -> t.StrMapping:
        """Route every mirrored host to its mirror and refuse any other transport.

        Git may speak only the ``file`` protocol, uv makes no network request
        and skips its GitHub API shortcut, so a fixture that still reaches a
        remote fails instead of passing on a live network. Global, system and
        inherited command configuration cannot add competing URL rewrites:
        the numbered configuration consists only of these declared mirrors.

        Returns:
            The resulting ``t.StrMapping``.

        """
        hosts = sorted(path.name for path in mirrors.iterdir() if path.is_dir())
        environment = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_PARAMETERS": "",
            "GIT_CONFIG_COUNT": str(len(hosts)),
            "GIT_ALLOW_PROTOCOL": "file",
            "UV_OFFLINE": "1",
            "UV_NO_GITHUB_FAST_PATH": "1",
        }
        for index, host in enumerate(hosts):
            environment[f"GIT_CONFIG_KEY_{index}"] = (
                f"url.{(mirrors / host).as_uri()}/.insteadOf"
            )
            environment[f"GIT_CONFIG_VALUE_{index}"] = f"https://{host}/"
        return environment
