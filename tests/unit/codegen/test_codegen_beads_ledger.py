"""Beads ledger routing from isolated worktrees to the principal checkout.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


class TestCodegenBeadsLedger:
    """Route every Beads lifecycle to the principal ledger, never a worktree."""

    @staticmethod
    def _git(root: Path, *arguments: str) -> None:
        tm.ok(u.Cli.run_checked(["git", *arguments], cwd=root))

    @classmethod
    def _standalone_workspace(cls, root: Path, *, ledger_id: str | None) -> Path:
        """Create a manifested standalone repository with an enabled Beads overlay."""
        provider = config.Infra.codegen.providers[0]
        repository = next(
            item
            for item in config.Infra.codegen.repositories
            if item.distribution == config.Infra.name
        )
        root.mkdir(parents=True)
        cls._git(root, "init", "-q", "-b", provider.branch)
        cls._git(root, "config", "user.email", "infra@example.com")
        cls._git(root, "config", "user.name", "Infra Tests")
        (root / "pyproject.toml").write_text(
            f'[project]\nname = "{repository.distribution}"\nversion = "0.12.0.dev0"\n'
            'requires-python = ">=3.13,<3.14"\n',
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
        spec = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.distribution,
            repository=local_repository,
            ledger_id=ledger_id,
            repository_policy_overlays=(
                m.Infra.RepositoryPolicyOverlaySpec(
                    project=repository.distribution, beads_enabled=True
                ),
            ),
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
        repository = next(
            item
            for item in config.Infra.codegen.repositories
            if item.distribution == config.Infra.name
        )
        tm.that(plan.canonical_prefix, eq=repository.distribution)

    def test_principal_keeps_ledger_at_repository_root(self, tmp_path: Path) -> None:
        """Keep a principal checkout self-owned without worktree redirection."""
        principal = self._standalone_workspace(tmp_path / "principal", ledger_id=None)

        plan = self._beads_plan(principal)

        tm.that(plan.enabled, eq=True)
        tm.that(plan.repository_root, eq=principal.resolve())
        tm.that(plan.ledger_root, eq=None)

    def test_manifest_ledger_id_owns_tracker_namespace(self, tmp_path: Path) -> None:
        """Derive the tracker identity from the declared ledger, never the repo name."""
        principal = self._standalone_workspace(
            tmp_path / "principal", ledger_id="workspace-ledger"
        )

        plan = self._beads_plan(principal)

        tm.that(plan.ledger_id, eq="workspace-ledger")
        tm.that(plan.canonical_prefix, eq="workspace-ledger")
