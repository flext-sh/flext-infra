"""Internal dependency synchronization service for managing FLEXT submodule dependencies."""

from __future__ import annotations

import shutil
from collections.abc import (
    Mapping,
    MutableMapping,
    Sequence,
)
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_infra import (
    FlextInfraDepsServiceBase,
    FlextInfraInternalSyncRepoMixin,
    FlextInfraSettings,
    c,
    m,
    p,
    r,
    t,
    u,
)


class FlextInfraInternalDependencySyncService(
    FlextInfraInternalSyncRepoMixin,
    FlextInfraDepsServiceBase,
):
    """Synchronize internal FLEXT dependencies via git clone or workspace symlinks."""

    log: ClassVar[p.Logger] = u.fetch_logger(__name__)
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
    def resolve_internal_repo_name(raw_path: str) -> str | None:
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
        repo_map: Mapping[str, m.Infra.RepoUrls]
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
        infra_settings = FlextInfraSettings()
        force_https = infra_settings.github_actions or infra_settings.use_https
        for dep_path in deps.values():
            repo_name = dep_path.name
            if repo_name not in repo_map:
                return r[int].fail(f"missing repo mapping for {repo_name}")
            if workspace_mode and workspace_root:
                sibling = workspace_root / repo_name
                if sibling.exists():
                    symlink_result = u.Cli.ensure_symlink(dep_path, sibling)
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

    def collect_internal_deps(self, project_root: Path) -> p.Result[Mapping[str, Path]]:
        """Collect internal path dependencies from pyproject metadata."""
        pyproject = project_root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.exists():
            return r[Mapping[str, Path]].ok({})
        data_result = self._read_plain(pyproject)
        if data_result.failure:
            return r[Mapping[str, Path]].fail(
                data_result.error or f"failed to read {pyproject}",
            )
        data = data_result.value
        deps = u.Cli.json_deep_mapping(
            data, c.Infra.TOOL, c.Infra.POETRY, c.Infra.DEPENDENCIES
        )
        result: MutableMapping[str, Path] = {}
        for dep_name, dep_value in deps.items():
            dep_value_map = u.Cli.json_as_mapping(dep_value)
            if not dep_value_map:
                continue
            dep_path = dep_value_map.get(c.Infra.PATH)
            if not isinstance(dep_path, str):
                continue
            repo_name = self.resolve_internal_repo_name(dep_path)
            if repo_name is None:
                continue
            result[dep_name] = project_root / ".flext-deps" / repo_name
        project_obj = u.Cli.json_deep_mapping(data, c.Infra.PROJECT)
        project_deps_raw = project_obj.get(c.Infra.DEPENDENCIES)
        project_deps: t.StrSequence = []
        if isinstance(project_deps_raw, str | int | float | bool) or (
            isinstance(project_deps_raw, Sequence)
            and not isinstance(
                project_deps_raw,
                str | bytes,
            )
        ):
            project_deps = u.Cli.toml_as_string_list(project_deps_raw)
        internal_dep_names: t.Infra.StrSet = set()
        for dep in project_deps:
            dep_name_match = c.Infra.DEP_NAME_RE.match(dep)
            if dep_name_match is not None:
                dep_name = dep_name_match.group(1)
                if dep_name.startswith(c.Infra.PKG_PREFIX_HYPHEN) or dep_name in {
                    "flext",
                    "flexcore",
                }:
                    internal_dep_names.add(dep_name)
            if " @ " not in dep:
                continue
            match = c.Infra.PEP621_PATH_RE.search(dep)
            if not match:
                continue
            repo_name = self.resolve_internal_repo_name(match.group("path"))
            if repo_name is None:
                continue
            _ = result.setdefault(repo_name, project_root / ".flext-deps" / repo_name)
        tool_obj = u.Cli.json_deep_mapping(data, c.Infra.TOOL)
        uv_obj = u.Cli.json_deep_mapping(tool_obj, "uv")
        sources_obj = u.Cli.json_deep_mapping(uv_obj, "sources")
        for dep_name in internal_dep_names:
            source_value = u.Cli.json_deep_mapping(sources_obj, dep_name)
            if not source_value:
                continue
            if source_value.get("workspace") is True:
                _ = result.setdefault(dep_name, project_root / ".flext-deps" / dep_name)
                continue
            source_path = source_value.get(c.Infra.PATH)
            if isinstance(source_path, str):
                repo_name = self.resolve_internal_repo_name(source_path)
                if repo_name is not None:
                    _ = result.setdefault(
                        repo_name,
                        project_root / ".flext-deps" / repo_name,
                    )
        return r[Mapping[str, Path]].ok(result)

    def ensure_checkout(
        self, dep_path: Path, repo_url: str, ref_name: str
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
