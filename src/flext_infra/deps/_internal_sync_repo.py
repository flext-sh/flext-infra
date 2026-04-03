"""Repository resolution and workspace detection for internal dependency sync."""

from __future__ import annotations

import configparser
import os
import re
from collections.abc import Mapping, MutableMapping
from pathlib import Path

from flext_core import FlextLogger
from flext_infra import c, m, p, r, t, u


class FlextInfraInternalSyncRepoMixin:
    """Repository mapping, ref resolution, and workspace detection methods."""

    log: FlextLogger
    toml: p.Infra.TomlReader | None

    _OWNER_PATTERNS: tuple[re.Pattern[str], ...]

    def _read_plain(self, path: Path) -> r[t.Infra.ContainerDict]:
        if self.toml is not None:
            return self.toml.read_plain(path)
        return u.Infra.read_plain(path)

    @classmethod
    def owner_from_remote_url(cls, remote_url: str) -> str | None:
        """Extract GitHub owner from supported remote URL formats."""
        for pattern in cls._OWNER_PATTERNS:
            match = pattern.match(remote_url)
            if match:
                return match.group("owner")
        return None

    @staticmethod
    def ssh_to_https(url: str) -> str:
        """Convert GitHub SSH URL to HTTPS URL when needed."""
        if url.startswith("git@github.com:"):
            return f"https://github.com/{url.removeprefix('git@github.com:')}"
        return url

    def infer_owner_from_origin(self, project_root: Path) -> str | None:
        """Infer GitHub owner from remote origin URL."""
        remote = u.Infra.git_run(
            ["config", "--get", "remote.origin.url"],
            cwd=project_root,
        )
        if remote.is_failure:
            return None
        remote_val = remote.value
        return self.owner_from_remote_url(remote_val.strip())

    def is_workspace_mode(self, project_root: Path) -> t.Infra.Pair[bool, Path | None]:
        """Determine workspace mode and return resolved workspace root."""
        if os.getenv("FLEXT_STANDALONE") == "1":
            u.Infra.info("Standalone mode: skipping workspace dependency sync")
            return (False, None)
        env_workspace_root = self.workspace_root_from_env(project_root)
        if env_workspace_root is not None:
            return (True, env_workspace_root)
        superproject = u.Infra.git_run(
            ["rev-parse", "--show-superproject-working-tree"],
            cwd=project_root,
        )
        if superproject.is_success:
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
            repo_url = parser.get(section, c.Infra.ReportKeys.URL, fallback="").strip()
            if not repo_url:
                continue
            mapping[repo_name] = m.Infra.RepoUrls(
                ssh_url=repo_url,
                https_url=self.ssh_to_https(repo_url),
            )
        return mapping

    def parse_repo_map(self, path: Path) -> r[Mapping[str, m.Infra.RepoUrls]]:
        """Parse flext-repo-map TOML into repository URL entries."""
        data_result = self._read_plain(path)
        if data_result.is_failure:
            return r[Mapping[str, m.Infra.RepoUrls]].fail(
                data_result.error or "failed to read repository map",
            )
        data = data_result.value
        repos_obj = u.Infra.deep_mapping(data, "repo")
        if not repos_obj:
            return r[Mapping[str, m.Infra.RepoUrls]].ok({})
        result: MutableMapping[str, m.Infra.RepoUrls] = {}
        for repo_name, values in repos_obj.items():
            values_map = u.Infra.normalize_str_mapping(values)
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
        if os.getenv("GITHUB_ACTIONS") == "true":
            for key in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
                value = os.getenv(key)
                if value:
                    return value
        branch = u.Infra.git_current_branch(project_root)
        if branch.is_success:
            branch_val = branch.value
            current = branch_val.strip()
            if current and current != c.Infra.Git.HEAD:
                return current
        tag = u.Infra.git_run(["describe", "--tags", "--exact-match"], cwd=project_root)
        if tag.is_success:
            tag_val = tag.value
            return tag_val.strip()
        return c.Infra.Git.MAIN

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
        env_root = os.getenv("FLEXT_WORKSPACE_ROOT")
        if not env_root:
            return None
        candidate = Path(env_root).expanduser().resolve()
        if not candidate.exists() or not candidate.is_dir():
            return None
        if project_root.is_relative_to(candidate):
            return candidate
        return None

    @staticmethod
    def workspace_root_from_parents(project_root: Path) -> Path | None:
        """Locate workspace root by scanning parent directories for .gitmodules."""
        for candidate in (project_root, *project_root.parents):
            if (candidate / c.Infra.Files.GITMODULES).exists():
                return candidate
        return None


__all__ = ["FlextInfraInternalSyncRepoMixin"]
