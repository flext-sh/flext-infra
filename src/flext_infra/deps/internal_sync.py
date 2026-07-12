"""Internal dependency synchronization service for managing FLEXT submodule dependencies."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, override

from flext_core import r

from flext_infra import FlextInfraServiceBase, c, m, p, settings, t, u
from flext_infra._utilities.deps_repos import FlextInfraInternalSyncRepoMixin
from flext_infra.deps._internal_sync_collect import FlextInfraInternalSyncCollectMixin


class FlextInfraInternalDependencySyncService(
    FlextInfraServiceBase[bool],
    FlextInfraInternalSyncRepoMixin,
    FlextInfraInternalSyncCollectMixin,
):
    """Synchronize internal FLEXT dependencies via git clone or workspace symlinks."""

    toml: Annotated[
        p.Infra.TomlReader | None,
        m.Field(
            default=None,
            exclude=True,
            description="Optional TOML reader override for dependency sync",
        ),
    ] = None

    @override
    def execute(self) -> p.Result[bool]:
        """Synchronize internal FLEXT dependencies for the configured workspace."""
        result = self.sync(self.workspace_root)
        if result.failure:
            return r[bool].fail(result.error or "internal dependency sync failed")
        return r[bool].ok(True)

    @staticmethod
    def validate_git_ref(ref_name: str) -> p.Result[str]:
        """Validate git reference name using project-safe regex."""
        if not c.Infra.GIT_REF_RE.fullmatch(ref_name):
            return r[str].fail(f"invalid git ref: {ref_name!r}")
        return r[str].ok(ref_name)

    @staticmethod
    def validate_repo_url(repo_url: str) -> p.Result[str]:
        """Validate repository URL against allowed GitHub format."""
        if not c.Infra.GITHUB_REPO_URL_RE.fullmatch(repo_url):
            return r[str].fail(f"invalid repository URL: {repo_url!r}")
        return r[str].ok(repo_url)

    def sync(self, project_root: Path) -> p.Result[int]:
        """Synchronize internal dependencies via git clone or workspace symlinks."""
        deps_result = self.collect_internal_deps(project_root)
        if deps_result.failure:
            return r[int].fail(deps_result.error or "dependency collection failed")
        deps = deps_result.value
        if not deps:
            return r[int].ok(0)
        workspace_mode, workspace_root = self.is_workspace_mode(project_root)
        map_file = project_root / "flext-repo-map.toml"
        repo_map: t.MappingKV[str, m.Infra.RepoUrls]
        if (
            workspace_mode
            and workspace_root
            and (workspace_root / c.Infra.GITMODULES).exists()
        ):
            repo_map = self.parse_gitmodules(workspace_root / c.Infra.GITMODULES)
            if map_file.exists():
                parsed_map_result = self.parse_repo_map(map_file)
                if parsed_map_result.failure:
                    return r[int].fail(
                        parsed_map_result.error or "failed to parse standalone map",
                    )
                repo_map = {**parsed_map_result.value, **repo_map}
        elif not map_file.exists():
            owner = self.infer_owner_from_origin(project_root)
            if owner is None:
                return r[int].fail(
                    "missing flext-repo-map.toml for standalone dependency resolution and unable to infer GitHub owner from remote.origin.url",
                )
            repo_map = self.synthesized_repo_map(
                owner,
                {dep_path.name for dep_path in deps.values()},
            )
            self.log.warning("sync_deps_synthesized_repo_map", owner=owner)
        else:
            parsed_map_result = self.parse_repo_map(map_file)
            if parsed_map_result.failure:
                return r[int].fail(
                    parsed_map_result.error or "failed to parse repo map",
                )
            repo_map = parsed_map_result.value
        ref_name = self.resolve_ref(project_root)
        # mro-wkii.4.15: dependency sync consumes the singleton without accessors.
        force_https = settings.Infra.github_actions or settings.Infra.use_https
        for dep_path in deps.values():
            repo_name = dep_path.name
            if repo_name not in repo_map:
                return r[int].fail(f"missing repo mapping for {repo_name}")
            if workspace_mode and workspace_root:
                sibling = workspace_root / repo_name
                if sibling.exists():
                    symlink_result = self.ensure_symlink(dep_path, sibling)
                    if symlink_result.failure:
                        return r[int].fail(
                            symlink_result.error or f"failed symlink for {repo_name}",
                        )
                    continue
            urls = repo_map[repo_name]
            selected_url = urls.https_url if force_https else urls.ssh_url
            checkout_result = self.ensure_checkout(dep_path, selected_url, ref_name)
            if checkout_result.failure:
                return r[int].fail(
                    checkout_result.error or f"checkout failed for {repo_name}",
                )
        return r[int].ok(0)

    def ensure_symlink(self, dep_path: Path, sibling: Path) -> p.Result[bool]:
        """Ensure a workspace dependency path points at the sibling checkout."""
        return u.Cli.ensure_symlink(dep_path, sibling)

    def ensure_checkout(
        self,
        dep_path: Path,
        repo_url: str,
        ref_name: str,
    ) -> p.Result[bool]:
        """Ensure dependency checkout exists and matches requested ref."""
        safe_repo_url_result = self.validate_repo_url(repo_url)
        if safe_repo_url_result.failure:
            return r[bool].fail(safe_repo_url_result.error or "invalid repository URL")
        safe_ref_name_result = self.validate_git_ref(ref_name)
        if safe_ref_name_result.failure:
            return r[bool].fail(safe_ref_name_result.error or "invalid git ref")
        safe_repo_url = safe_repo_url_result.value
        safe_ref_name = safe_ref_name_result.value
        parent_dir_result = u.Cli.ensure_dir(dep_path.parent)
        if parent_dir_result.failure:
            return r[bool].fail(
                parent_dir_result.error
                or f"failed to create parent dir for {dep_path}",
            )
        if not (dep_path / c.Infra.GIT_DIR).exists():
            try:
                if dep_path.exists() or dep_path.is_symlink():
                    if dep_path.is_dir() and (not dep_path.is_symlink()):
                        shutil.rmtree(dep_path)
                    else:
                        dep_path.unlink()
            except OSError as exc:
                return r[bool].fail(f"cleanup failed for {dep_path.name}: {exc}")
            cloned = u.Cli.run_checked([
                c.Infra.GIT,
                "clone",
                "--depth",
                "1",
                "--branch",
                safe_ref_name,
                safe_repo_url,
                str(dep_path),
            ])
            if cloned.failure:
                return r[bool].fail(f"clone failed for {dep_path.name}: {cloned.error}")
            return r[bool].ok(True)
        fetch = u.Cli.run_checked(
            [c.Infra.GIT, "fetch", c.Infra.GIT_ORIGIN],
            cwd=dep_path,
        )
        if fetch.failure:
            return r[bool].fail(f"fetch failed for {dep_path.name}: {fetch.error}")
        checkout = u.Cli.run_checked(
            [c.Infra.GIT, "checkout", safe_ref_name],
            cwd=dep_path,
        )
        if checkout.failure:
            return r[bool].fail(
                f"checkout failed for {dep_path.name}: {checkout.error}",
            )
        _ = u.Cli.run_checked(
            [c.Infra.GIT, "pull", c.Infra.GIT_ORIGIN, safe_ref_name],
            cwd=dep_path,
        )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraInternalDependencySyncService"]
