"""Public contract for governed repository-root artifact ownership."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import p, t, u


class TestsRootArtifactOwnership:
    """Prove codegen config is the sole root-artifact ownership catalog."""

    def test_envrc_template_covers_every_repository_profile(self) -> None:
        """Every generated repository owns the same direnv activation contract."""
        entry = next(
            item
            for item in config.Infra.codegen.templates.entries
            if item.destination == c.Infra.ENVRC_FILENAME
        )

        tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))

    def test_markdown_config_templates_cover_every_repository_profile(self) -> None:
        entries = {
            item.destination: item
            for item in config.Infra.codegen.templates.entries
            if item.destination in {".markdownlint.json", ".markdownlintignore"}
        }

        tm.that(set(entries), eq={".markdownlint.json", ".markdownlintignore"})
        for entry in entries.values():
            tm.that(set(entry.profiles), eq=set(c.Infra.MakeProfile))
        tm.that(config.Infra.tooling.tools.markdown.exclude, has=".serena/**")

    # A full-surface conform materializes the complete managed tree plus git
    # hook installation; the slow marker consumes the config-owned 60s budget.
    @pytest.mark.slow
    @pytest.mark.timeout(60)
    def test_standalone_conform_projects_markdown_policy(
        self, infra_git_repo: Path
    ) -> None:
        root = infra_git_repo
        u.Tests.write_standalone_workspace_manifest(
            root, "flext-demo", upstream="flext_cli"
        )
        package_root = root / "src" / "flext_demo"
        tm.ok(u.Cli.ensure_dir(package_root))
        tm.ok(u.Cli.atomic_write_text_file(package_root / "__init__.py", ""))
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "pyproject.toml",
                '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
            )
        )
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.ALL,
            mode=c.Infra.CodegenConformMode.APPLY,
        )

        tm.ok(FlextInfraCodegenConform.execute_request(request, workspace))

        tm.that((root / ".markdownlint.json").is_file(), eq=True)
        ignore = (root / ".markdownlintignore").read_text(encoding="utf-8")
        tm.that(ignore, has=".serena/**")

    def test_governed_artifacts_have_one_explicit_policy(self) -> None:
        configured = config.Infra.codegen.managed_files
        paths = tuple(item.path.as_posix() for item in configured)

        tm.that(len(paths), eq=len(set(paths)))
        github_templates = {
            Path(entry.destination)
            for entry in config.Infra.codegen.templates.entries
            if Path(entry.destination).parts[:1] == (".github",)
        }
        github_managed = {
            item.path: item
            for item in configured
            if item.path.parts[:1] == (".github",)
        }
        tm.that(set(github_managed), eq=github_templates)
        tm.that(github_templates, empty=False)
        for owned in github_managed.values():
            tm.that(owned.policy, eq="full")

    def test_every_packaged_github_template_is_declared(self) -> None:
        """Keep the packaged GitHub tree and typed render manifest bijective."""
        template_root = (
            Path(__file__).parents[3]
            / "src"
            / "flext_infra"
            / "templates"
            / "project"
            / "base"
        )
        physical = {
            path.relative_to(template_root).as_posix().removesuffix(".j2")
            for path in (template_root / ".github").rglob("*.j2")
        }
        declared = {
            entry.destination
            for entry in config.Infra.codegen.templates.entries
            if Path(entry.destination).parts[:1] == (".github",)
        }

        tm.that(physical, eq=declared)

    def test_github_template_without_managed_owner_is_rejected(self) -> None:
        """Reject any config where a GitHub projection escapes full ownership."""
        spec = config.Infra.codegen
        github_managed = tuple(
            item for item in spec.managed_files if item.path.parts[:1] == (".github",)
        )
        target = github_managed[0]
        mutated = spec.model_copy(
            update={
                "managed_files": tuple(
                    item for item in spec.managed_files if item.path != target.path
                )
            }
        )

        with pytest.raises(ValueError, match="ownership mismatch"):
            type(spec).model_validate(mutated)

    def test_github_managed_owner_must_be_full(self) -> None:
        """Reject weaker policies for every config-declared GitHub artifact."""
        spec = config.Infra.codegen
        target = next(
            item for item in spec.managed_files if item.path.parts[:1] == (".github",)
        )
        mutated = spec.model_copy(
            update={
                "managed_files": tuple(
                    item.model_copy(update={"policy": "merge"})
                    if item.path == target.path
                    else item
                    for item in spec.managed_files
                )
            }
        )

        with pytest.raises(ValueError, match="must be full-managed"):
            type(spec).model_validate(mutated)

    def test_conform_uses_one_fixed_point_plan(self, infra_git_repo: Path) -> None:
        root = infra_git_repo
        u.Tests.write_standalone_workspace_manifest(
            root, "flext-demo", upstream="flext_cli"
        )
        package_root = root / "src" / "flext_demo"
        tm.ok(u.Cli.ensure_dir(package_root))
        tm.ok(u.Cli.atomic_write_text_file(package_root / "__init__.py", ""))
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "pyproject.toml",
                (
                    "[project]\n"
                    'name = "flext-demo"\n'
                    'version = "0.1.0"\n'
                    'requires-python = ">=3.13,<3.14"\n'
                    "dependencies = []\n"
                ),
            )
        )
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        tm.ok(FlextInfraCodegenConform.execute_request(request, workspace))
        manual = {
            "config/workspace.yaml": (root / "config" / "workspace.yaml").read_bytes(),
            "custom.mk": b"# manual project extension\n",
        }
        (root / "custom.mk").write_bytes(manual["custom.mk"])
        configured_policy = next(
            item.policy
            for item in config.Infra.codegen.managed_files
            if item.path == Path(c.Infra.MAKEFILE_FILENAME)
        )
        before = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )

        first = FlextInfraCodegenConform.execute_request(
            request, initial_workspace=workspace
        )
        result = tm.ok(first)
        governed = tuple(file for file in result.plan.files if file.policy is not None)
        tm.that(tuple(file.path for file in governed), eq=(root / "Makefile",))
        tm.that(governed[0].policy, eq=configured_policy)
        tm.that(result.written_files, eq=())
        after = tuple(
            sorted(
                (path.relative_to(root).as_posix(), path.read_bytes())
                for path in root.rglob("*")
                if path.is_file() and ".git" not in path.relative_to(root).parts
            )
        )
        tm.that(after, eq=before)
        for relative, expected in manual.items():
            tm.that((root / relative).read_bytes(), eq=expected)


class TestsAncestryNetworkBoundary:
    """The ancestry plan must never block indefinitely on a remote."""

    def test_origin_fetch_is_time_boxed(
        self, infra_git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Refreshing the baseline from origin runs under a declared timeout.

        mro-38p39: the ancestry plan shells `git fetch origin` whenever a remote
        is configured, and it passed no timeout. A slow or unreachable remote
        therefore blocked conform for as long as git waited -- measured at 7.44s
        cumulative in one unit test whose fixture pointed origin at a real
        GitHub URL, the single largest cost in the suite. Every other bounded
        subprocess in this codebase states c.Infra.TIMEOUT_SHORT; the network
        call, the one most able to hang, stated nothing.
        """
        root = infra_git_repo
        dist = u.Tests.repository_ref(config.Infra.name).distribution
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "pyproject.toml",
                f'[project]\nname = "{dist}"\nversion = "0.12.0.dev0"\n'
                'requires-python = ">=3.13,<3.14"\n',
            )
        )
        package_init = root / "src" / dist.replace("-", "_") / "__init__.py"
        package_init.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(package_init, ""))
        tests_init = root / "tests" / "__init__.py"
        tests_init.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(tests_init, ""))
        u.Tests.commit_git_changes(root, "Seed manifest-less topology")

        recorded: list[tuple[tuple[str, ...], int | None]] = []
        original = u.Cli.run_raw

        def _record(
            cmd: t.StrSequence,
            cwd: t.Cli.TextPath | None = None,
            timeout: int | None = None,
            env: t.StrMapping | None = None,
            remove_env_keys: t.StrSequence = (),
            input_data: str | bytes | None = None,
            *,
            capture: bool = True,
        ) -> p.Result[p.Cli.CommandOutput]:
            recorded.append((tuple(cmd), timeout))
            return original(
                cmd,
                cwd=cwd,
                timeout=timeout,
                env=env,
                remove_env_keys=remove_env_keys,
                input_data=input_data,
                capture=capture,
            )

        monkeypatch.setattr(u.Cli, "run_raw", _record)
        request = m.Infra.CodegenConformRequest(root=root)
        tm.ok(
            FlextInfraCodegenConform(workspace_root=root, request=request).plan(request)
        )

        fetches = [entry for entry in recorded if "fetch" in entry[0]]
        tm.that(bool(fetches), eq=True)
        for _command, timeout in fetches:
            tm.that(timeout, eq=c.Infra.TIMEOUT_SHORT)


__all__: list[str] = []
