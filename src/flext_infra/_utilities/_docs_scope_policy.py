"""Configuration-backed docs scope policy and classification helpers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_cli import u

from flext_infra import c, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDocsScopeStateMixin,
    FlextInfraUtilitiesProjectManagedArtifacts,
)


class FlextInfraUtilitiesDocsScopePolicyMixin(FlextInfraUtilitiesDocsScopeStateMixin):
    """Interpret the authenticated docs policy for one project or workspace."""

    @staticmethod
    def config_path(repository_root: Path) -> Path:
        """Return the minimal docs policy settings path.

        Returns:
            The minimal docs policy settings path.

        """
        dir_docs: str = c.Infra.DIR_DOCS
        docs_config: str = c.Infra.DOCS_CONFIG_FILENAME
        return repository_root / dir_docs / docs_config

    @staticmethod
    def load_config(repository_root: Path) -> t.JsonMapping:
        """Load the minimal docs policy settings if present.

        Returns:
            The resulting ``t.JsonMapping``.

        Raises:
            TypeError: If docs config root must be a mapping.
            ValueError: If ``state.failure``; or if ``parsed.failure``.

        """
        path = FlextInfraUtilitiesDocsScopePolicyMixin.config_path(repository_root)
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
    def excluded_roots(repository_root: Path) -> t.Infra.StrSet:
        """Return every explicitly excluded root directory.

        The existing documentation scope owns exclusions; workspace composition
        is discovered independently from its Git declarations.

        Returns:
            Every explicitly excluded root directory.

        """
        owner = FlextInfraUtilitiesDocsScopePolicyMixin
        payload = owner.load_config(repository_root)
        scope = payload.get("scope")
        if not isinstance(scope, dict):
            return set()
        excluded = scope.get("exclude_roots")
        if not isinstance(excluded, list):
            return set()
        return {str(item).strip() for item in excluded if str(item).strip()}

    @staticmethod
    def project_docs_meta(project_root: Path) -> t.JsonMapping:
        """Return optional ``tool.flext.docs`` metadata from a project pyproject.

        Returns:
            Optional ``tool.flext.docs`` metadata from a project pyproject.

        """
        return FlextInfraUtilitiesDocsScopePolicyMixin.project_state(
            project_root,
        ).docs_meta

    @staticmethod
    def excluded_doc_path(project_root: Path, relative_path: Path) -> bool:
        """Return whether codegen excludes a docs-relative path from physical copy.

        Returns:
            Whether the docs-relative path is excluded by the typed copy policy.

        """
        codegen = (
            FlextInfraUtilitiesProjectManagedArtifacts
            .load_codegen_inputs(project_root)
            .unwrap()
            .spec
        )
        candidate = Path(c.Infra.DIR_DOCS) / relative_path
        return any(
            candidate.full_match(pattern) for pattern in codegen.docs_copy_patterns
        )

    @staticmethod
    def governed_project(project_name: str, repository_root: Path) -> bool:
        """Return whether a project belongs to the governed FLEXT docs scope.

        Returns:
            Whether a project belongs to the governed FLEXT docs scope.

        """
        project_root = repository_root / project_name
        docs_meta = FlextInfraUtilitiesDocsScopePolicyMixin.project_docs_meta(
            project_root,
        )
        is_enabled = FlextInfraUtilitiesDocsScopePolicyMixin.docs_scope_enabled(
            docs_meta,
        )
        return (
            project_name.startswith(c.Infra.PKG_PREFIX_HYPHEN)
            and project_name
            not in FlextInfraUtilitiesDocsScopePolicyMixin.excluded_roots(
                repository_root,
            )
            and is_enabled
        )

    @staticmethod
    def classify_project_from_meta(project_name: str, docs_meta: t.JsonMapping) -> str:
        """Classify a project using pre-loaded docs metadata (avoids re-parsing).

        Project-prefix heuristics derive from ``c.Infra.INTEGRATION_CLASS_PREFIXES``
        (SSOT for integration project family) so adding a new family member
        requires editing only the canonical class-prefix tuple.

        Returns:
            The resulting ``str``.

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
        """Return the required standard docs contract for FLEXT projects.

        Returns:
            The required standard docs contract for FLEXT projects.

        """
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
