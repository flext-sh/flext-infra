"""Behavioral tests for automatic Git topology and typed policy overlays."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_infra import config
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_tests import tm
from tests import c, m, u


class TestsFlextInfraInfraWorkspaceDetector:
    """Exercise physical Git, conform, Make, and Beads as separate decisions."""

    @staticmethod
    def _initialize_repository(
        repository_root: Path,
        *,
        origin: str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Create one real Git repository with optional PEP 621 metadata."""
        repository_root.mkdir(parents=True, exist_ok=True)
        tm.ok(
            u.Cli.run_checked(["git", "init", "-q", "-b", "main"], cwd=repository_root)
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"],
                cwd=repository_root,
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Tests"], cwd=repository_root
            )
        )
        (repository_root / "README.md").write_text("# Repository\n", encoding="utf-8")
        if project_name is not None:
            (repository_root / c.PYPROJECT_FILENAME).write_text(
                f'[project]\nname = "{project_name}"\nversion = "0.0.0"\n',
                encoding="utf-8",
            )
        tm.ok(u.Cli.run_checked(["git", "add", "."], cwd=repository_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "commit", "-q", "-m", "Initial commit"], cwd=repository_root
            )
        )
        if origin is not None:
            tm.ok(
                u.Cli.run_checked(
                    ["git", "remote", "add", "origin", origin], cwd=repository_root
                )
            )

    @classmethod
    def _add_submodule(
        cls,
        workspace_root: Path,
        *,
        path: str,
        canonical_url: str,
        branch: str | None = "main",
        malformed_pyproject: bool = False,
    ) -> Path:
        """Add one real Gitlink while retaining its declared canonical URL."""
        source_root = workspace_root.parent / f"{Path(path).name}-source"
        cls._initialize_repository(source_root)
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-q",
                    str(source_root),
                    path,
                ],
                cwd=workspace_root,
            )
        )
        member_root = workspace_root / path
        section = f"submodule.{Path(path).name}"
        tm.ok(
            u.Cli.run_checked(
                ["git", "remote", "set-url", "origin", canonical_url], cwd=member_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "config",
                    "--file",
                    ".gitmodules",
                    f"{section}.url",
                    canonical_url,
                ],
                cwd=workspace_root,
            )
        )
        if branch is not None:
            tm.ok(
                u.Cli.run_checked(
                    [
                        "git",
                        "config",
                        "--file",
                        ".gitmodules",
                        f"{section}.branch",
                        branch,
                    ],
                    cwd=workspace_root,
                )
            )
        if malformed_pyproject:
            (member_root / c.PYPROJECT_FILENAME).write_text(
                "[project\n", encoding="utf-8"
            )
        return member_root

    @classmethod
    def _managed_workspace(cls, tmp_path: Path) -> tuple[Path, Path]:
        """Create one same-provider root and managed child."""
        workspace_root = tmp_path / "workspace"
        cls._initialize_repository(
            workspace_root, origin="https://github.com/example/workspace.git"
        )
        member_root = cls._add_submodule(
            workspace_root,
            path="packages/member",
            canonical_url="https://github.com/example/member.git",
        )
        return workspace_root, member_root

    @staticmethod
    def _external_overlay() -> m.Infra.RepositoryTopologyOverlaySpec:
        """Read the configured external-reference exception from the typed SSOT."""
        return next(
            overlay
            for overlay in config.Infra.topology.overlays
            if overlay.external_refs
        )

    def test_overlay_config_validates_against_its_public_schema(self) -> None:
        """Prove the authored overlay and JSON schema stay in one round trip."""
        project_root = Path(__file__).resolve().parents[2]

        tm.ok(
            u.Cli.config_load(
                project_root / "config" / "topology.yaml",
                schema_path=(
                    project_root
                    / "src"
                    / "flext_infra"
                    / "schemas"
                    / "topology-overlay.schema.json"
                ),
                expand_env=False,
            )
        )

    def test_generic_manifestless_repository_is_standalone(
        self, tmp_path: Path
    ) -> None:
        """Derive any repository from Git and metadata without a hardcoded catalog."""
        project_root = tmp_path / "consumer"
        self._initialize_repository(
            project_root,
            origin="https://github.com/consumer-org/consumer-repository.git",
            project_name="consumer-distribution",
        )

        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(project_root))
        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(project_root))

        tm.that(spec.name, eq="consumer-repository")
        tm.that(spec.repository.distribution, eq="consumer-distribution")
        tm.that(spec.repository.role, eq=c.Infra.RepositoryRole.STANDALONE)
        tm.that(topology.physical, eq="independent")
        tm.that(topology.mode, eq=c.Infra.WorkspaceMode.STANDALONE)
        tm.that(topology.conform, eq="managed")
        tm.that(topology.make_profile, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(topology.beads_enabled, eq=False)

    def test_repository_without_git_is_generic_standalone(self, tmp_path: Path) -> None:
        """Support pre-init standalone projects from their physical local identity."""
        (tmp_path / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "local-project"\nversion = "0.0.0"\n', encoding="utf-8"
        )

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(tmp_path))

        tm.that(topology.physical, eq="independent")
        tm.that(topology.conform, eq="managed")
        tm.that(topology.repository.distribution, eq="local-project")

    def test_generated_manifest_is_not_topology_authority(self, tmp_path: Path) -> None:
        """Ignore a stale projection and derive behavior from Git plus overlays."""
        project_root = tmp_path / "consumer"
        self._initialize_repository(
            project_root, origin="https://github.com/example/consumer.git"
        )
        manifest = project_root / "config" / "workspace.yaml"
        manifest.parent.mkdir()
        manifest.write_text("not: valid: yaml\n", encoding="utf-8")

        tm.ok(
            FlextInfraWorkspaceDetector().detect(project_root),
            eq=c.Infra.WorkspaceMode.STANDALONE,
        )

    def test_gitlinks_automatically_make_workspace_root(self, tmp_path: Path) -> None:
        """Classify a root from real Gitlinks without per-project configuration."""
        workspace_root, _ = self._managed_workspace(tmp_path)

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(workspace_root))

        tm.that(topology.physical, eq="workspace-root")
        tm.that(topology.mode, eq=c.Infra.WorkspaceMode.WORKSPACE)
        tm.that(topology.make_profile, eq=c.Infra.MakeProfile.WORKSPACE_ROOT)
        tm.that(topology.managed_gitlinks, eq=("packages/member",))
        tm.that(topology.external_gitlinks, eq=())
        tm.that(topology.beads_enabled, eq=True)
        tm.that(topology.beads_namespace, eq=topology.repository.name)

    def test_attached_managed_child_conforms_as_standalone(
        self, tmp_path: Path
    ) -> None:
        """Separate physical attachment from the child's generated Make profile."""
        workspace_root, member_root = self._managed_workspace(tmp_path)

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(member_root))

        tm.that(topology.workspace_root, eq=workspace_root)
        tm.that(topology.physical, eq="attached")
        tm.that(topology.mode, eq=c.Infra.WorkspaceMode.STANDALONE)
        tm.that(topology.conform, eq="managed")
        tm.that(topology.make_profile, eq=c.Infra.MakeProfile.STANDALONE)
        tm.that(topology.repository.role, eq=c.Infra.RepositoryRole.STANDALONE)
        tm.that(topology.repository.checkout, eq=c.Infra.CheckoutKind.SUBMODULE)
        tm.that(topology.beads_enabled, eq=False)

    def test_different_provider_gitlink_is_external_by_construction(
        self, tmp_path: Path
    ) -> None:
        """Never manage a third-party Gitlink even without an explicit overlay."""
        workspace_root = tmp_path / "workspace"
        self._initialize_repository(
            workspace_root, origin="https://github.com/example/workspace.git"
        )
        member_root = self._add_submodule(
            workspace_root,
            path="vendor/upstream",
            canonical_url="https://github.com/upstream/upstream.git",
            malformed_pyproject=True,
        )

        root_topology = tm.ok(FlextInfraWorkspaceDetector.inspect(workspace_root))
        child_topology = tm.ok(FlextInfraWorkspaceDetector.inspect(member_root))

        tm.that(root_topology.managed_gitlinks, eq=())
        tm.that(root_topology.external_gitlinks, eq=("vendor/upstream",))
        tm.that(child_topology.physical, eq="attached")
        tm.that(child_topology.conform, eq="external")
        tm.that(child_topology.make_profile, eq=None)
        tm.that(child_topology.repository.role, eq=c.Infra.RepositoryRole.CONTENT_ONLY)
        tm.that(child_topology.repository.codegen, eq=c.Infra.CodegenKind.NONE)
        tm.that(child_topology.repository.package, eq=False)
        tm.that(child_topology.repository.editable, eq=False)
        tm.that(child_topology.repository.read_only, eq=True)

    def test_same_provider_fork_is_external_only_by_typed_overlay(
        self, tmp_path: Path
    ) -> None:
        """Apply the configured fork exception without scanning its source tree."""
        overlay = self._external_overlay()
        external = overlay.external_refs[0]
        workspace_root = tmp_path / overlay.match
        self._initialize_repository(
            workspace_root, origin=f"https://github.com/example/{overlay.match}.git"
        )
        member_root = self._add_submodule(
            workspace_root,
            path=external.path.as_posix(),
            canonical_url=f"https://github.com/example/{external.path.name}.git",
            malformed_pyproject=True,
        )

        root_topology = tm.ok(FlextInfraWorkspaceDetector.inspect(workspace_root))
        child_topology = tm.ok(FlextInfraWorkspaceDetector.inspect(member_root))

        tm.that(root_topology.external_gitlinks, eq=(external.path.as_posix(),))
        tm.that(root_topology.external_uses, eq=overlay.external_refs)
        tm.that(child_topology.conform, eq="external")
        tm.that(child_topology.external_uses, eq=(external,))

    def test_external_use_vocabulary_rejects_every_gate_category(self) -> None:
        """Keep external references structurally impossible to lint or typecheck."""
        for forbidden in ("lint", "type", "check", "conform", "mutation"):
            with pytest.raises(c.ValidationError):
                m.Infra.ExternalReferenceSpec.model_validate({
                    "path": "vendor/upstream",
                    "uses": [forbidden],
                })

    def test_independent_beads_opt_in_comes_from_typed_overlay(
        self, tmp_path: Path
    ) -> None:
        """Enable Beads only for an explicitly configured independent repository."""
        overlay = next(
            item
            for item in config.Infra.topology.overlays
            if item.beads.enabled and item.identity is None
        )
        project_root = tmp_path / overlay.match
        self._initialize_repository(
            project_root, origin=f"https://github.com/example/{overlay.match}.git"
        )

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(project_root))

        tm.that(topology.beads_enabled, eq=True)
        tm.that(topology.beads_namespace, eq=topology.repository.name)

    def test_identity_overlay_owns_exceptional_beads_namespace(
        self, tmp_path: Path
    ) -> None:
        """Derive an exceptional identity once and reuse it for Beads."""
        overlay = next(
            item for item in config.Infra.topology.overlays if item.identity is not None
        )
        project_root = tmp_path / overlay.match
        self._initialize_repository(
            project_root, origin=f"https://github.com/example/{overlay.match}.git"
        )

        topology = tm.ok(FlextInfraWorkspaceDetector.inspect(project_root))

        tm.that(topology.repository.name, eq=overlay.identity)
        tm.that(topology.beads_namespace, eq=overlay.identity)

    def test_independent_beads_overlay_is_rejected_after_becoming_workspace(
        self, tmp_path: Path
    ) -> None:
        """Force config cleanup when an independent exception gains Gitlinks."""
        overlay = next(
            item for item in config.Infra.topology.overlays if item.beads.enabled
        )
        workspace_root = tmp_path / overlay.match
        self._initialize_repository(
            workspace_root, origin=f"https://github.com/example/{overlay.match}.git"
        )
        self._add_submodule(
            workspace_root,
            path="member",
            canonical_url="https://github.com/example/member.git",
        )

        tm.fail(
            FlextInfraWorkspaceDetector.inspect(workspace_root),
            has="only valid for independent repositories",
        )

    def test_external_overlay_must_name_an_indexed_gitlink(
        self, tmp_path: Path
    ) -> None:
        """Reject stale external policy instead of silently scanning a new shape."""
        overlay = self._external_overlay()
        project_root = tmp_path / overlay.match
        self._initialize_repository(
            project_root, origin=f"https://github.com/example/{overlay.match}.git"
        )

        tm.fail(
            FlextInfraWorkspaceDetector.inspect(project_root),
            has="not indexed gitlinks",
        )

    def test_gitmodules_and_index_must_match(self, tmp_path: Path) -> None:
        """Fail closed when .gitmodules is not the exact indexed topology."""
        workspace_root, _ = self._managed_workspace(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                ["git", "rm", "--cached", "-q", "-f", "packages/member"],
                cwd=workspace_root,
            )
        )

        tm.fail(
            FlextInfraWorkspaceDetector.inspect(workspace_root),
            has="declared Git submodules and indexed gitlinks differ",
        )

    def test_missing_submodule_branch_uses_git_head_contract(
        self, tmp_path: Path
    ) -> None:
        """Honor Git's default remote HEAD when .gitmodules omits branch."""
        workspace_root = tmp_path / "workspace"
        self._initialize_repository(
            workspace_root, origin="https://github.com/example/workspace.git"
        )
        self._add_submodule(
            workspace_root,
            path="member",
            canonical_url="https://github.com/example/member.git",
            branch=None,
        )

        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(workspace_root))

        tm.that(spec.members[0].branch, eq="HEAD")

    def test_managed_attached_origin_mismatch_fails_closed(
        self, tmp_path: Path
    ) -> None:
        """Reject an attached managed checkout whose origin changed ownership."""
        _, member_root = self._managed_workspace(tmp_path)
        tm.ok(
            u.Cli.run_checked(
                [
                    "git",
                    "remote",
                    "set-url",
                    "origin",
                    "https://github.com/example/other.git",
                ],
                cwd=member_root,
            )
        )

        tm.fail(FlextInfraWorkspaceDetector.inspect(member_root), has="origin mismatch")

    def test_invalid_path_returns_failure(self) -> None:
        """Return a typed failure for an invalid filesystem path."""
        tm.fail(
            FlextInfraWorkspaceDetector().detect(Path("\0")),
            has="Workspace detection failed",
        )
