"""Configuration-backed docs scope policy and classification helpers."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from flext_cli import u
from flext_infra import c, t

from .._utilities._docs_scope_state import FlextInfraUtilitiesDocsScopeStateMixin


class FlextInfraUtilitiesDocsScopePolicyMixin(FlextInfraUtilitiesDocsScopeStateMixin):
    """Interpret the authenticated docs policy for one project or workspace."""

    @staticmethod
    def config_path(workspace_root: Path) -> Path:
        """Return the minimal docs policy settings path."""
        dir_docs: str = c.Infra.DIR_DOCS
        docs_config: str = c.Infra.DOCS_CONFIG_FILENAME
        return workspace_root / dir_docs / docs_config

    @staticmethod
    def load_config(workspace_root: Path) -> t.JsonMapping:
        """Load the minimal docs policy settings if present."""
        path = FlextInfraUtilitiesDocsScopePolicyMixin.config_path(workspace_root)
        # An absent optional config has no parent identity to authenticate. A
        # present parent is delegated to the atomic owner, which still rejects
        # symlinks, unsafe identities, and every real read failure.
        if not path.parent.exists():
            return {}
        state = u.Cli.atomic_read_binary_file_state(path, required=False)
        if state.failure:
            raise ValueError(state.error or f"docs config is unsafe: {path}")
        if state.value.content is None:
            return {}
        parsed = u.Cli.json_loads(state.value.content)
        if parsed.failure:
            raise ValueError(parsed.error or f"docs config JSON is invalid: {path}")
        value = parsed.value
        if not isinstance(value, dict):
            msg = f"docs config root must be a mapping: {path}"
            raise TypeError(msg)
        validated = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        return dict(validated)

    @staticmethod
    def excluded_roots(workspace_root: Path) -> t.Infra.StrSet:
        """Return explicitly excluded root directories from docs scope."""
        payload = FlextInfraUtilitiesDocsScopePolicyMixin.load_config(workspace_root)
        scope = payload.get("scope")
        if not isinstance(scope, dict):
            return set()
        excluded = scope.get("exclude_roots")
        if not isinstance(excluded, list):
            return set()
        return {str(item).strip() for item in excluded if str(item).strip()}

    @staticmethod
    def project_docs_meta(project_root: Path) -> t.JsonMapping:
        """Return optional ``tool.flext.docs`` metadata from a project pyproject."""
        return FlextInfraUtilitiesDocsScopePolicyMixin.project_state(
            project_root
        ).docs_meta

    @staticmethod
    def docs_meta_list(project_root: Path, key: str) -> t.StrSequence:
        """Return one normalized string-list value from ``tool.flext.docs``."""
        docs_meta = FlextInfraUtilitiesDocsScopePolicyMixin.project_docs_meta(
            project_root
        )
        raw = docs_meta.get(key)
        if not isinstance(raw, list):
            return ()
        return [str(item).strip() for item in raw if str(item).strip()]

    @staticmethod
    def is_excluded_doc_path(project_root: Path, relative_path: Path) -> bool:
        """Return whether a relative docs path is excluded by ``tool.flext.docs``."""
        candidate = relative_path.as_posix()
        for pattern in FlextInfraUtilitiesDocsScopePolicyMixin.docs_meta_list(
            project_root, "exclude_docs"
        ):
            if fnmatch(candidate, pattern):
                return True
        return False

    @staticmethod
    def is_governed_project(project_name: str, workspace_root: Path) -> bool:
        """Return whether a project belongs to the governed FLEXT docs scope."""
        project_root = workspace_root / project_name
        docs_meta = FlextInfraUtilitiesDocsScopePolicyMixin.project_docs_meta(
            project_root
        )
        enabled = docs_meta.get("enabled", True)
        is_enabled = enabled if isinstance(enabled, bool) else True
        return (
            project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            and project_name
            not in FlextInfraUtilitiesDocsScopePolicyMixin.excluded_roots(
                workspace_root
            )
            and is_enabled
        )

    @staticmethod
    def classify_project_from_meta(project_name: str, docs_meta: t.JsonMapping) -> str:
        """Classify a project using pre-loaded docs metadata (avoids re-parsing).

        Project-prefix heuristics derive from ``c.Infra.INTEGRATION_CLASS_PREFIXES``
        (SSOT for integration project family) so adding a new family member
        requires editing only the canonical class-prefix tuple.
        """
        configured = docs_meta.get("project_class")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        integration_prefixes = tuple(
            f"{c.Infra.PKG_PREFIX_HYPHEN}{prefix.removeprefix('Flext').lower()}-"
            for prefix in c.Infra.INTEGRATION_CLASS_PREFIXES
        )
        if project_name.startswith(integration_prefixes):
            return "integration"
        if project_name == f"{c.Infra.PKG_PREFIX_HYPHEN}infra":
            return "infra"
        if project_name == f"{c.Infra.PKG_PREFIX_HYPHEN}tests":
            return "test"
        return "domain"

    @staticmethod
    def required_project_files() -> t.StrSequence:
        """Return the required standard docs contract for FLEXT projects."""
        return [
            "README.md",
            "docs/index.md",
            "docs/guides/README.md",
            "docs/api-reference/README.md",
            "docs/api-reference/generated/overview.md",
            "docs/api-reference/generated/public-api.md",
            "docs/api-reference/generated/modules/index.md",
            "mkdocs.yml",
        ]


__all__: list[str] = ["FlextInfraUtilitiesDocsScopePolicyMixin"]
