"""Repository resolution and workspace detection for internal dependency sync."""

from __future__ import annotations

import configparser
from collections.abc import (
    Mapping,
    MutableMapping,
)
from pathlib import Path

from flext_cli import u
from flext_infra import FlextInfraSettings, c, m, p, r, t


class FlextInfraInternalSyncRepoMixin:
    """Repository mapping, ref resolution, and workspace detection methods."""

    log: p.Logger
    toml: p.Infra.TomlReader | None

    def _read_plain(self, path: Path) -> p.Result[t.Infra.ContainerDict]:
        if self.toml is not None:
            return self.toml.read_plain(path)
        plain_result = u.Cli.toml_read_json(path)
        if plain_result.failure:
            return r[t.Infra.ContainerDict].fail(
                plain_result.error or f"failed to read {path}",
            )
        return r[t.Infra.ContainerDict].ok(
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(plain_result.value),
        )

    @classmethod
    def owner_from_remote_url(cls, remote_url: str) -> str | None:
        """Extract GitHub owner from supported remote URL formats."""
        for pattern in c.Infra.GITHUB_OWNER_PATTERNS:
            match = pattern.match(remote_url)
            if match:
                owner: str = match.group("owner")
                return owner
        return None

    @staticmethod
    def ssh_to_https(url: str) -> str:
        """Convert GitHub SSH URL to HTTPS URL when needed."""
        if url.startswith("git@github.com:"):
            return f"https://github.com/{url.removeprefix('git@github.com:')}"
        return url

    def infer_owner_from_origin(self, project_root: Path) -> str | None:
        """Infer GitHub owner from remote origin URL."""
        remote = u.Cli.capture(
            [c.Infra.GIT, "config", "--get", "remote.origin.url"],
            cwd=project_root,
        )
        if remote.failure:
            return None
        remote_val = remote.value
        return self.owner_from_remote_url(remote_val.strip())

    def is_workspace_mode(self, project_root: Path) -> t.Pair[bool, Path | None]:
        """Determine workspace mode and return resolved workspace root."""
        settings = FlextInfraSettings()
        if settings.standalone:
            u.Cli.info("Standalone mode: skipping workspace dependency sync")
            return (False, None)
        env_workspace_root = self.workspace_root_from_env(project_root)
        if env_workspace_root is not None:
            return (True, env_workspace_root)
        superproject = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--show-superproject-working-tree"],
            cwd=project_root,
        )
        if superproject.success:
            sp_val = superproject.value
            value = sp_val.strip()
            if value:
                return (True, Path(value))
        heuristic_workspace_root = self.workspace_root_from_parents(project_root)
        if heuristic_workspace_root is not None:
            return (True, heuristic_workspace_root)
        return (False, None)

    def parse_gitmodules(self, path: Path) -> Mapping[str, m.Infra.RepoUrls]:
        """Parse .gitmodules file into repo URL mapping."""
        parser = configparser.RawConfigParser()
        _ = parser.read(path)
        mapping: MutableMapping[str, m.Infra.RepoUrls] = {}
        for section in parser.sections():
            if not section.startswith("submodule "):
                continue
            repo_name = section.split('"')[1]
            repo_url = parser.get(section, c.Infra.RK_URL, fallback="").strip()
            if not repo_url:
                continue
            mapping[repo_name] = m.Infra.RepoUrls(
                ssh_url=repo_url,
                https_url=self.ssh_to_https(repo_url),
            )
        return mapping

    def parse_repo_map(self, path: Path) -> p.Result[Mapping[str, m.Infra.RepoUrls]]:
        """Parse flext-repo-map TOML into repository URL entries."""
        data_result = self._read_plain(path)
        if data_result.failure:
            return r[Mapping[str, m.Infra.RepoUrls]].fail(
                data_result.error or "failed to read repository map",
            )
        data = data_result.value
        repos_obj = u.Cli.json_deep_mapping(data, "repo")
        if not repos_obj:
            return r[Mapping[str, m.Infra.RepoUrls]].ok({})
        result: MutableMapping[str, m.Infra.RepoUrls] = {}
        for repo_name, values in repos_obj.items():
            values_map = u.Cli.json_as_mapping(values)
            if not values_map:
                continue
            ssh_url = str(values_map.get("ssh_url", ""))
            https_url = str(values_map.get("https_url", self.ssh_to_https(ssh_url)))
            if ssh_url:
                result[repo_name] = m.Infra.RepoUrls(
                    ssh_url=ssh_url,
                    https_url=https_url,
                )
        return r[Mapping[str, m.Infra.RepoUrls]].ok(result)

    def resolve_ref(self, project_root: Path) -> str:
        """Resolve dependency sync git reference for current environment."""
        settings = FlextInfraSettings()
        if settings.github_actions:
            for value in (settings.github_head_ref, settings.github_ref_name):
                if value:
                    return value
        branch = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_root,
        )
        if branch.success:
            branch_val = branch.value
            current = branch_val.strip()
            if current and current != c.Infra.GIT_HEAD:
                return current
        tag = u.Cli.capture(
            [c.Infra.GIT, "describe", "--tags", "--exact-match"],
            cwd=project_root,
        )
        if tag.success:
            tag_val = tag.value
            return tag_val.strip()
        return c.Infra.GIT_MAIN

    def synthesized_repo_map(
        self,
        owner: str,
        repo_names: t.Infra.StrSet,
    ) -> Mapping[str, m.Infra.RepoUrls]:
        """Build default repository URL mapping from owner and repo set."""
        result: MutableMapping[str, m.Infra.RepoUrls] = {}
        for repo_name in sorted(repo_names):
            ssh_url = f"git@github.com:{owner}/{repo_name}.git"
            result[repo_name] = m.Infra.RepoUrls(
                ssh_url=ssh_url,
                https_url=self.ssh_to_https(ssh_url),
            )
        return result

    def workspace_root_from_env(self, project_root: Path) -> Path | None:
        """Resolve workspace root from environment when valid for project root."""
        candidate = FlextInfraSettings().workspace_root
        if candidate is None:
            return None
        if not candidate.exists() or not candidate.is_dir():
            return None
        if project_root.is_relative_to(candidate):
            return candidate
        return None

    @staticmethod
    def workspace_root_from_parents(project_root: Path) -> Path | None:
        """Locate workspace root by scanning parent directories for .gitmodules."""
        for candidate in (project_root, *project_root.parents):
            if (candidate / c.Infra.GITMODULES).exists():
                return candidate
        return None


__all__: list[str] = ["FlextInfraInternalSyncRepoMixin"]
