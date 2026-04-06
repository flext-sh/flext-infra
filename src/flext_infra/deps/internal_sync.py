"""Internal dependency synchronization service for managing FLEXT submodule dependencies."""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Mapping, MutableMapping
from pathlib import Path

from flext_core import FlextLogger
from flext_infra import FlextInfraInternalSyncRepoMixin, c, m, p, r, t, u


class FlextInfraInternalDependencySyncService(FlextInfraInternalSyncRepoMixin):
    """Synchronize internal FLEXT dependencies via git clone or workspace symlinks."""

    log = FlextLogger.create_module_logger(__name__)

    _OWNER_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"^git@github\.com:(?P<owner>[^/]+)/[^/]+(?:\.git)?$"),
        re.compile(r"^https://github\.com/(?P<owner>[^/]+)/[^/]+(?:\.git)?$"),
        re.compile(r"^http://github\.com/(?P<owner>[^/]+)/[^/]+(?:\.git)?$"),
    )

    def __init__(self) -> None:
        """Initialize the internal dependency sync service."""
        self.toml: p.Infra.TomlReader | None = None

    @staticmethod
    def ensure_symlink(target: Path, source: Path) -> r[bool]:
        """Ensure target points to source via directory symlink."""
        try:
            dir_result = u.Cli.ensure_dir(target.parent)
            if dir_result.is_failure:
                return r[bool].fail(
                    dir_result.error or f"failed to create parent dir for {target}",
                )
            if target.is_symlink() and target.resolve() == source.resolve():
                return r[bool].ok(True)
            if target.exists() or target.is_symlink():
                if target.is_dir() and (not target.is_symlink()):
                    shutil.rmtree(target)
                else:
                    target.unlink()
            target.symlink_to(source.resolve(), target_is_directory=True)
            return r[bool].ok(True)
        except OSError as exc:
            return r[bool].fail(f"failed to ensure symlink for {target}: {exc}")

    @staticmethod
    def is_internal_path_dep(raw_path: str) -> str | None:
        """Resolve repository name from internal path dependency notation."""
        normalized = raw_path.strip().removeprefix("./")
        if normalized.startswith(".flext-deps/"):
            return normalized.removeprefix(".flext-deps/")
        if normalized.startswith("../"):
            candidate = normalized.removeprefix("../")
            if candidate and "/" not in candidate:
                return candidate
        if normalized and "/" not in normalized and (normalized not in {".", ".."}):
            return normalized
        return None

    @staticmethod
    def validate_git_ref(ref_name: str) -> r[str]:
        """Validate git reference name using project-safe regex."""
        if not c.Infra.GIT_REF_RE.fullmatch(ref_name):
            return r[str].fail(f"invalid git ref: {ref_name!r}")
        return r[str].ok(ref_name)

    @staticmethod
    def validate_repo_url(repo_url: str) -> r[str]:
        """Validate repository URL against allowed GitHub format."""
        if not c.Infra.GITHUB_REPO_URL_RE.fullmatch(repo_url):
            return r[str].fail(f"invalid repository URL: {repo_url!r}")
        return r[str].ok(repo_url)

    def sync(self, project_root: Path) -> r[int]:
        """Synchronize internal dependencies via git clone or workspace symlinks."""
        deps_result = self.collect_internal_deps(project_root)
        if deps_result.is_failure:
            return r[int].fail(deps_result.error or "dependency collection failed")
        deps = deps_result.value
        if not deps:
            return r[int].ok(0)
        workspace_mode, workspace_root = self.is_workspace_mode(project_root)
        map_file = project_root / "flext-repo-map.toml"
        repo_map: Mapping[str, m.Infra.RepoUrls]
        if (
            workspace_mode
            and workspace_root
            and (workspace_root / c.Infra.Files.GITMODULES).exists()
        ):
            repo_map = self.parse_gitmodules(workspace_root / c.Infra.Files.GITMODULES)
            if map_file.exists():
                parsed_map_result = self.parse_repo_map(map_file)
                if parsed_map_result.is_failure:
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
            if parsed_map_result.is_failure:
                return r[int].fail(
                    parsed_map_result.error or "failed to parse repo map",
                )
            repo_map = parsed_map_result.value
        ref_name = self.resolve_ref(project_root)
        force_https = (
            os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("FLEXT_USE_HTTPS") == "1"
        )
        for dep_path in deps.values():
            repo_name = dep_path.name
            if repo_name not in repo_map:
                return r[int].fail(f"missing repo mapping for {repo_name}")
            if workspace_mode and workspace_root:
                sibling = workspace_root / repo_name
                if sibling.exists():
                    symlink_result = self.ensure_symlink(dep_path, sibling)
                    if symlink_result.is_failure:
                        return r[int].fail(
                            symlink_result.error or f"failed symlink for {repo_name}",
                        )
                    continue
            urls = repo_map[repo_name]
            selected_url = urls.https_url if force_https else urls.ssh_url
            checkout_result = self.ensure_checkout(dep_path, selected_url, ref_name)
            if checkout_result.is_failure:
                return r[int].fail(
                    checkout_result.error or f"checkout failed for {repo_name}",
                )
        return r[int].ok(0)

    def collect_internal_deps(self, project_root: Path) -> r[Mapping[str, Path]]:
        """Collect internal path dependencies from pyproject metadata."""
        pyproject = project_root / c.Infra.Files.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[Mapping[str, Path]].ok({})
        data_result = self._read_plain(pyproject)
        if data_result.is_failure:
            return r[Mapping[str, Path]].fail(
                data_result.error or f"failed to read {pyproject}",
            )
        data = data_result.value
        deps = u.Infra.deep_mapping(
            data, c.Infra.TOOL, c.Infra.POETRY, c.Infra.DEPENDENCIES
        )
        result: MutableMapping[str, Path] = {}
        for dep_name, dep_value in deps.items():
            dep_value_map = u.Infra.normalize_str_mapping(dep_value)
            if not dep_value_map:
                continue
            dep_path = dep_value_map.get(c.Infra.PATH)
            if not isinstance(dep_path, str):
                continue
            repo_name = self.is_internal_path_dep(dep_path)
            if repo_name is None:
                continue
            result[dep_name] = project_root / ".flext-deps" / repo_name
        project_obj = u.Infra.deep_mapping(data, c.Infra.PROJECT)
        project_deps_raw = project_obj.get(c.Infra.DEPENDENCIES)
        project_deps = u.Cli.toml_as_string_list(project_deps_raw)
        internal_dep_names: t.Infra.StrSet = set()
        for dep in project_deps:
            dep_name_match = c.Infra.DEP_NAME_RE.match(dep)
            if dep_name_match is not None:
                dep_name = dep_name_match.group(1)
                if dep_name.startswith(c.Infra.Packages.PREFIX_HYPHEN) or dep_name in {
                    "flext",
                    "flexcore",
                }:
                    internal_dep_names.add(dep_name)
            if " @ " not in dep:
                continue
            match = c.Infra.PEP621_PATH_RE.search(dep)
            if not match:
                continue
            repo_name = self.is_internal_path_dep(match.group("path"))
            if repo_name is None:
                continue
            _ = result.setdefault(repo_name, project_root / ".flext-deps" / repo_name)
        tool_obj = u.Infra.deep_mapping(data, c.Infra.TOOL)
        uv_obj = u.Infra.deep_mapping(tool_obj, "uv")
        sources_obj = u.Infra.deep_mapping(uv_obj, "sources")
        for dep_name in internal_dep_names:
            source_value = u.Infra.deep_mapping(sources_obj, dep_name)
            if not source_value:
                continue
            if source_value.get("workspace") is True:
                _ = result.setdefault(dep_name, project_root / ".flext-deps" / dep_name)
                continue
            source_path = source_value.get(c.Infra.PATH)
            if isinstance(source_path, str):
                repo_name = self.is_internal_path_dep(source_path)
                if repo_name is not None:
                    _ = result.setdefault(
                        repo_name,
                        project_root / ".flext-deps" / repo_name,
                    )
        return r[Mapping[str, Path]].ok(result)

    def ensure_checkout(self, dep_path: Path, repo_url: str, ref_name: str) -> r[bool]:
        """Ensure dependency checkout exists and matches requested ref."""
        safe_repo_url_result = self.validate_repo_url(repo_url)
        if safe_repo_url_result.is_failure:
            return r[bool].fail(safe_repo_url_result.error or "invalid repository URL")
        safe_ref_name_result = self.validate_git_ref(ref_name)
        if safe_ref_name_result.is_failure:
            return r[bool].fail(safe_ref_name_result.error or "invalid git ref")
        safe_repo_url = safe_repo_url_result.value
        safe_ref_name = safe_ref_name_result.value
        parent_dir_result = u.Cli.ensure_dir(dep_path.parent)
        if parent_dir_result.is_failure:
            return r[bool].fail(
                parent_dir_result.error
                or f"failed to create parent dir for {dep_path}",
            )
        if not (dep_path / c.Infra.Git.DIR).exists():
            try:
                if dep_path.exists() or dep_path.is_symlink():
                    if dep_path.is_dir() and (not dep_path.is_symlink()):
                        shutil.rmtree(dep_path)
                    else:
                        dep_path.unlink()
            except OSError as exc:
                return r[bool].fail(f"cleanup failed for {dep_path.name}: {exc}")
            cloned = u.Infra.git_run_checked([
                "clone",
                "--depth",
                "1",
                "--branch",
                safe_ref_name,
                safe_repo_url,
                str(dep_path),
            ])
            if cloned.is_failure:
                return r[bool].fail(f"clone failed for {dep_path.name}: {cloned.error}")
            return r[bool].ok(True)
        fetch = u.Infra.git_fetch(dep_path, c.Infra.Git.ORIGIN)
        if fetch.is_failure:
            return r[bool].fail(f"fetch failed for {dep_path.name}: {fetch.error}")
        checkout = u.Infra.git_checkout(dep_path, safe_ref_name)
        if checkout.is_failure:
            return r[bool].fail(
                f"checkout failed for {dep_path.name}: {checkout.error}",
            )
        _ = u.Infra.git_pull(dep_path, remote=c.Infra.Git.ORIGIN, branch=safe_ref_name)
        return r[bool].ok(True)

    @staticmethod
    def main() -> int:
        """Entry point for internal dependency synchronization CLI."""
        parser = u.Infra.create_parser(
            prog="flext-infra deps internal-sync",
            description="Synchronize internal FLEXT dependencies via git clone or workspace symlinks",
            flags=u.Infra.SharedFlags(include_apply=False),
        )
        args = parser.parse_args()
        cli_args = u.Infra.resolve(args)
        service = FlextInfraInternalDependencySyncService()
        result = service.sync(cli_args.workspace)
        if result.is_success:
            return result.value
        sync_error = result.error or "sync_internal_deps_failed"
        service.log.error("sync_internal_deps_failed", error_detail=sync_error)
        u.Infra.error(f"[sync-deps] {sync_error}")
        return 1


main = FlextInfraInternalDependencySyncService.main


if __name__ == "__main__":
    raise SystemExit(FlextInfraInternalDependencySyncService.main())
__all__ = ["FlextInfraInternalDependencySyncService"]
