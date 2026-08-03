"""Beads ledger routing from isolated worktrees to the principal checkout.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from flext_infra import c, config, m, u
from tests import u as test_u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestCodegenBeadsLedger:
    """Route every Beads lifecycle to the principal ledger, never a worktree."""

    @staticmethod
    def _git(root: Path, *arguments: str) -> None:
        tm.ok(u.Cli.run_checked(["git", *arguments], cwd=root))

    @classmethod
    def _standalone_workspace(
        cls,
        root: Path,
        *,
        ledger_id: str | None,
        ledger_prefix: str | None = None,
        overlay: bool = True,
        attached_marker: bool = False,
    ) -> Path:
        """Create a manifested standalone repository with a real Git origin."""
        provider = config.Infra.codegen.providers[0]
        repository = test_u.Tests.repository_ref(config.Infra.name)
        root.mkdir(parents=True)
        cls._git(root, "init", "-q", "-b", provider.branch)
        cls._git(root, "config", "user.email", "infra@example.com")
        cls._git(root, "config", "user.name", "Infra Tests")
        marker = (
            "\n[tool.flext.workspace]\nattached = true\n" if attached_marker else ""
        )
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{repository.distribution}"\nversion = "0.12.0.dev0"\n'
            f'requires-python = ">=3.13,<3.14"\n{marker}',
            encoding="utf-8",
        )
        package_init = (
            root / "src" / repository.distribution.replace("-", "_") / "__init__.py"
        )
        package_init.parent.mkdir(parents=True)
        package_init.write_text("", encoding="utf-8")
        local_repository = repository.model_copy(
            update={
                "path": Path(),
                "role": c.Infra.RepositoryRole.STANDALONE,
                "checkout": c.Infra.CheckoutKind.INDEPENDENT,
                "editable": False,
            }
        )
        overlays = (
            (
                m.Infra.RepositoryPolicyOverlaySpec(
                    project=repository.distribution, beads_enabled=True
                ),
            )
            if overlay
            else ()
        )
        spec = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.distribution,
            repository=local_repository,
            ledger_id=ledger_id,
            ledger_prefix=ledger_prefix,
            repository_policy_overlays=overlays,
        )
        tm.ok(
            u.Cli.yaml_dump(
                root / "config" / "workspace.yaml",
                spec.model_dump(
                    mode="json",
                    exclude_none=True,
                    exclude={"external_dependency_paths"},
                ),
            )
        )
        origin = root.parent / f"{root.name}-origin.git"
        cls._git(root.parent, "init", "-q", "--bare", str(origin))
        cls._git(root, "add", "-A")
        cls._git(root, "commit", "-q", "-m", "Seed standalone workspace")
        cls._git(root, "remote", "add", "origin", str(origin))
        cls._git(root, "push", "-q", "-u", "origin", provider.branch)
        return root

    @classmethod
    def _beads_plan(cls, root: Path) -> m.Infra.BeadsPlan:
        """Plan one repository in check mode and return its single Beads plan."""
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(workspace_root=root).plan(request)
        )
        tm.that(len(planned.beads), eq=1)
        return planned.beads[0]

    def test_transaction_worktree_routes_ledger_to_principal(
        self, tmp_path: Path
    ) -> None:
        """Resolve the ledger of an isolated transaction to its principal checkout."""
        principal = self._standalone_workspace(tmp_path / "principal", ledger_id=None)
        transaction = tmp_path / "transaction"
        self._git(principal, "worktree", "add", "--detach", str(transaction))

        plan = self._beads_plan(transaction)

        tm.that(plan.enabled, eq=True)
        tm.that(plan.repository_root, eq=transaction.resolve())
        tm.that(plan.ledger_root, eq=principal.resolve())
        tm.that(plan.ledger_id, eq=None)
        repository = test_u.Tests.repository_ref(config.Infra.name)
        tm.that(plan.canonical_prefix, eq=repository.distribution)

    def test_principal_keeps_ledger_at_repository_root(self, tmp_path: Path) -> None:
        """Keep a principal checkout self-owned without worktree redirection."""
        principal = self._standalone_workspace(tmp_path / "principal", ledger_id=None)

        plan = self._beads_plan(principal)

        tm.that(plan.enabled, eq=True)
        tm.that(plan.repository_root, eq=principal.resolve())
        tm.that(plan.ledger_root, eq=principal.resolve())
        tm.that(plan.routes_to_principal_ledger, eq=False)

    def test_manifest_ledger_id_owns_database_not_issue_prefix(
        self, tmp_path: Path
    ) -> None:
        """Keep the declared ledger database distinct from the issue namespace.

        ai-hub-qwoc (landed in 1b8ac2d2): ``ledger_id`` is the Dolt-safe
        database identifier while ``canonical_prefix`` is the human-facing
        tracker namespace verified against the live ledger. Collapsing both
        silently renamed issue-prefix to the database form.
        """
        principal = self._standalone_workspace(
            tmp_path / "principal", ledger_id="workspace-ledger"
        )

        plan = self._beads_plan(principal)

        repository = test_u.Tests.repository_ref(config.Infra.name)
        tm.that(plan.ledger_id, eq="workspace-ledger")
        tm.that(plan.canonical_prefix, eq=repository.distribution)

    def test_declared_ledger_prefix_overrides_canonical_project_name(
        self, tmp_path: Path
    ) -> None:
        """Allow a workspace to declare an issue prefix that diverges from its name.

        mro-6fca: the flext workspace root tracks its issues under the ``mro-``
        namespace on the shared Dolt server, not ``flext-``. Deriving the issue
        prefix solely from ``canonical_project_name`` rebinds bd to a
        non-existent ledger and loses the live tracker. ``ledger_prefix`` is the
        typed, explicit override; when it is absent the canonical project name
        still wins, so the ai-hub-qwoc contract above is unchanged.
        """
        principal = self._standalone_workspace(
            tmp_path / "principal",
            ledger_id="mro",
            ledger_prefix="mro",
        )

        plan = self._beads_plan(principal)

        tm.that(plan.ledger_id, eq="mro")
        tm.that(plan.canonical_prefix, eq="mro")

    @classmethod
    def _plan(cls, root: Path) -> m.Infra.CodegenPlan:
        """Plan one repository in check mode."""
        request = m.Infra.CodegenConformRequest(
            root=root,
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.CHECK,
        )
        planned: m.Infra.CodegenPlan = tm.ok(
            FlextInfraCodegenConform(workspace_root=root).plan(request)
        )
        return planned

    @classmethod
    def _beads_config_render(cls, root: Path) -> str | None:
        """Return the rendered ledger config for one repository, if planned."""
        planned = cls._plan(root)
        match = next(
            (
                file
                for file in planned.files
                if file.path.as_posix().endswith(c.Infra.BEADS_CONFIG_RELPATH)
            ),
            None,
        )
        return match.rendered if match is not None else None

    @classmethod
    def _beads_metadata_render(cls, root: Path) -> str | None:
        """Return the rendered ledger-resolution marker, if planned."""
        planned = cls._plan(root)
        match = next(
            (
                file
                for file in planned.files
                if file.path.as_posix().endswith(c.Infra.BEADS_METADATA_RELPATH)
            ),
            None,
        )
        return match.rendered if match is not None else None

    @staticmethod
    def _toolchain_server() -> m.Infra.BeadsServerSpec:
        """Read the shared server block from the typed toolchain SSOT."""
        server = config.Infra.codegen.toolchain.beads.server
        if server is None:
            pytest.fail("toolchain SSOT must declare the beads server block")
        return server

    def test_owner_plan_renders_full_ledger_config(self, tmp_path: Path) -> None:
        """Render the full owned-ledger config for a Beads-enabled repository."""
        root = self._standalone_workspace(tmp_path / "owner", ledger_id="fleet-ledger")

        rendered = self._beads_config_render(root)

        if rendered is None:
            pytest.fail("owner plan must render the ledger config")
        server = self._toolchain_server()
        repository = test_u.Tests.repository_ref(config.Infra.name)
        # ai-hub-qwoc: issue-prefix is the tracker namespace derived from the
        # committed declaration, never the Dolt-safe ledger_id database name.
        tm.that(rendered, has=f'issue-prefix: "{repository.distribution}"')
        tm.that(rendered, has="database: fleet-ledger")
        tm.that(rendered, has="Owned ledger config")
        tm.that(rendered, has=f"mode: {server.mode}")
        tm.that(rendered, has=f"shared-server: {str(server.shared_server).lower()}")
        tm.that(rendered, has=f"host: {server.host}")
        tm.that(rendered, has=f"port: {server.port}")
        tm.that(rendered, has=f"user: {server.user}")
        # Quoted on purpose: bare `on` is a YAML boolean, not the string "on".
        # Deriva a expectativa do mesmo SSOT que o template serializa com
        # `| tojson`, entao o teste segue valido para qualquer valor declarado.
        tm.that(rendered, has=f"auto-commit: {json.dumps(server.auto_commit)}")

    def test_attached_standalone_plan_renders_routing_config(
        self, tmp_path: Path
    ) -> None:
        """Render a routing-only config for a marker-attached standalone."""
        root = self._standalone_workspace(
            tmp_path / "attached",
            ledger_id="attached-ledger",
            overlay=False,
            attached_marker=True,
        )

        rendered = self._beads_config_render(root)

        if rendered is None:
            pytest.fail("attached standalone plan must render the routing config")
        server = self._toolchain_server()
        repository = test_u.Tests.repository_ref(config.Infra.name)
        tm.that(rendered, has=f'issue-prefix: "{repository.distribution}"')
        tm.that(rendered, has="database: attached-ledger")
        tm.that(rendered, has="Routing-only client config")
        tm.that(rendered, has=f"mode: {server.mode}")
        tm.that(rendered, has=f"host: {server.host}")
        tm.that(rendered, has=f"port: {server.port}")
        tm.that(rendered, lacks="Owned ledger config")

    def test_plain_standalone_plan_renders_no_ledger_config(
        self, tmp_path: Path
    ) -> None:
        """Render nothing for a standalone without the Beads overlay."""
        root = self._standalone_workspace(
            tmp_path / "plain", ledger_id=None, overlay=False
        )

        tm.that(self._beads_config_render(root), eq=None)
        tm.that(self._beads_metadata_render(root), eq=None)

    def test_owner_plan_renders_ledger_resolution_marker(self, tmp_path: Path) -> None:
        """Bind the owned ledger to its Dolt database through the bd marker.

        mro-9wv8: bd resolves a checkout to its database through
        ``.beads/metadata.json`` and ``bd init`` never writes it, so a clone
        carrying only the generated ``config.yaml`` silently fell back to the
        default ``beads`` database and lost every issue to a throwaway store.
        """
        root = self._standalone_workspace(tmp_path / "owner", ledger_id="fleet-ledger")

        rendered = self._beads_metadata_render(root)

        if rendered is None:
            pytest.fail("owner plan must render the ledger-resolution marker")
        server = self._toolchain_server()
        marker = json.loads(rendered)
        tm.that(marker["dolt_database"], eq="fleet-ledger")
        tm.that(marker["dolt_mode"], eq=server.mode)
        tm.that(marker["backend"], eq=server.backend)
        tm.that(marker["database"], eq=server.backend)

    def test_attached_standalone_plan_renders_ledger_resolution_marker(
        self, tmp_path: Path
    ) -> None:
        """Bind a routing-only standalone to the same shared ledger database."""
        root = self._standalone_workspace(
            tmp_path / "attached",
            ledger_id="attached-ledger",
            overlay=False,
            attached_marker=True,
        )

        rendered = self._beads_metadata_render(root)

        if rendered is None:
            pytest.fail("attached standalone plan must render the marker")
        tm.that(json.loads(rendered)["dolt_database"], eq="attached-ledger")

    def test_tool_spec_rejects_malformed_checksum(self) -> None:
        """Reject a checksum that is not a SHA-256 hex digest."""
        with pytest.raises(c.ValidationError):
            m.Infra.BeadsToolSpec(
                selector="go:example.invalid/tool",
                version="0.0.1",
                reported_version="1.1.0",
                checksum="not-a-digest",
            )

    def test_server_block_loads_from_typed_ssot(self) -> None:
        """Load the shared server block with typed fields from the toolchain SSOT."""
        server = self._toolchain_server()
        tm.that(server.port > 0, eq=True)
        tm.that(bool(server.host), eq=True)
        tm.that(server.auto_commit in {"off", "on", "batch"}, eq=True)

    def test_checksum_mismatch_fails_closed(self, tmp_path: Path) -> None:
        """Reject a mise-resolved binary whose digest diverges from the SSOT pin."""
        plugin = tmp_path / "fake-bd-plugin"
        scripts = {
            "list-all": 'echo "1.1.0"\n',
            "download": (
                'mkdir -p "$ASDF_DOWNLOAD_PATH/bin"\n'
                'printf "#!/bin/sh\\necho bd version 1.1.0\\n" '
                '> "$ASDF_DOWNLOAD_PATH/bin/bd"\n'
                'chmod +x "$ASDF_DOWNLOAD_PATH/bin/bd"\n'
            ),
            "install": (
                'mkdir -p "$ASDF_INSTALL_PATH/bin"\n'
                'cp "$ASDF_DOWNLOAD_PATH/bin/bd" "$ASDF_INSTALL_PATH/bin/bd"\n'
                'chmod +x "$ASDF_INSTALL_PATH/bin/bd"\n'
            ),
        }
        for name, body in scripts.items():
            script = plugin / "bin" / name
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(f"#!/bin/sh\n{body}", encoding="utf-8")
            script.chmod(0o755)
        self._git(plugin, "init", "-q")
        self._git(plugin, "add", "-A")
        self._git(
            plugin,
            "-c",
            "user.email=infra@example.com",
            "-c",
            "user.name=Infra Tests",
            "commit",
            "-qm",
            "fake bd plugin",
        )
        root = self._standalone_workspace(tmp_path / "fake-bd-repo", ledger_id=None)
        (root / ".mise.toml").write_text(
            f'[plugins]\nbd = "file://{plugin}"\n\n[tools]\nbd = "1.1.0"\n',
            encoding="utf-8",
        )
        self._git(root, "add", ".mise.toml")
        self._git(root, "commit", "-qm", "Pin the fake bd plugin")
        tm.ok(u.Cli.run_checked(["mise", "trust", ".mise.toml"], cwd=root))
        tm.ok(u.Cli.run_checked(["mise", "install", "--yes", "bd"], cwd=root))
        # The fake plugin installs through the shared mise home; restore it
        # afterwards so no fixture state escapes the sandbox.
        mise_plugin_clone = Path.home() / ".local/share/mise/plugins/bd"
        mise_install_dir = Path.home() / ".local/share/mise/installs/bd"
        try:
            result = FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=root,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.CHECK,
                )
            )
            tm.fail(result, has="checksum mismatch")
        finally:
            shutil.rmtree(mise_plugin_clone, ignore_errors=True)
            shutil.rmtree(mise_install_dir, ignore_errors=True)
