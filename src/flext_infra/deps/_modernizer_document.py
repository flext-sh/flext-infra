"""Document-state processing mixin for pyproject modernization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import tomlkit
from tomlkit.exceptions import ParseError
from tomlkit.items import InlineTable

from flext_core import r
from flext_infra import c, config, m, p, t, u
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.phases.consolidate_groups import FlextInfraConsolidateGroupsPhase
from flext_infra.deps.phases.ensure_coverage import FlextInfraEnsureCoverageConfigPhase
from flext_infra.deps.phases.ensure_formatting import (
    FlextInfraEnsureFormattingToolingPhase,
)
from flext_infra.deps.phases.ensure_mypy import FlextInfraEnsureMypyConfigPhase
from flext_infra.deps.phases.ensure_namespace import (
    FlextInfraEnsureNamespaceToolingPhase,
)
from flext_infra.deps.phases.ensure_packaging import FlextInfraEnsurePackagingPhase
from flext_infra.deps.phases.ensure_pydantic_mypy import (
    FlextInfraEnsurePydanticMypyConfigPhase,
)
from flext_infra.deps.phases.ensure_pyrefly import FlextInfraEnsurePyreflyConfigPhase
from flext_infra.deps.phases.ensure_pyright import FlextInfraEnsurePyrightConfigPhase
from flext_infra.deps.phases.ensure_pytest import FlextInfraEnsurePytestConfigPhase
from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
from flext_infra.deps.phases.ensure_vulture import FlextInfraEnsureVultureConfigPhase
from flext_infra.deps.phases.inject_comments import FlextInfraInjectCommentsPhase
from flext_infra.refactor.project_classifier import FlextInfraProjectClassifier

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class FlextInfraPyprojectModernizerDocumentMixin:
    """Read, classify, and process one parsed pyproject document state."""

    if TYPE_CHECKING:
        # Members provided by sibling mixins / the facade at runtime via MRO.
        _rewrite_dependency_constraints_payload: Callable[..., t.StrSequence]

        @property
        def root(self) -> Path: ...

        def _ensure_build_system_payload(
            self, payload: t.MutableJsonMapping
        ) -> t.StrSequence: ...

        def _remove_empty_poetry_groups_payload(
            self, payload: t.MutableJsonMapping
        ) -> t.StrSequence: ...

        def _reorder_document_inplace(self, doc: t.Cli.TomlDocument) -> None: ...

    def _classify_project(
        self, project_dir: Path, *, payload: t.JsonMapping | None = None
    ) -> p.Result[str]:
        """Classify project kind for pyright/coverage settings selection."""
        classifier = FlextInfraProjectClassifier(project_dir, pyproject_payload=payload)
        return r[str].ok(classifier.classify().project_kind)

    def _read_document_state(
        self, path: Path
    ) -> p.Result[p.Infra.PyprojectDocumentState]:
        """Read one pyproject once and keep one validated plain payload state."""
        read = u.Cli.files_read_text(path)
        if read.failure:
            return r[p.Infra.PyprojectDocumentState].fail(
                read.error or f"failed to read {path}"
            )
        original_rendered = read.value
        payload_source = u.Cli.toml_mapping_from_text(original_rendered)
        if payload_source is None:
            return r[p.Infra.PyprojectDocumentState].fail(f"invalid TOML: {path}")
        try:
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
                payload_source
            )
        except c.ValidationError as exc:
            return r[p.Infra.PyprojectDocumentState].fail_op(
                "TOML payload validation", exc
            )
        return r[p.Infra.PyprojectDocumentState].ok(
            m.Infra.PyprojectDocumentState(
                pyproject_path=path,
                original_rendered=original_rendered,
                payload=payload,
            )
        )

    def conform_existing_source(self, source: str, *, path: Path) -> p.Result[str]:
        """Merge owned Ruff entries while preserving established consumer tooling."""
        try:
            doc = tomlkit.parse(source)
        except ParseError as exc:
            return r[str].fail_op(f"invalid TOML: {path}", exc)
        existing = u.Cli.toml_table_path(
            doc, (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION, "per-file-ignores")
        )
        if existing is None:
            lint = u.Cli.toml_table_path(
                doc, (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION)
            )
            raw_lint = lint.get("per-file-ignores") if lint is not None else None
            if isinstance(raw_lint, InlineTable):
                return r[str].fail(
                    f"inline Ruff per-file-ignore table is unsupported: {path}"
                )
            return r[str].ok(source)
        missing = tuple(
            (pattern, rules)
            for pattern, rules in config.Infra.tooling.tools.ruff.lint.per_file_ignores.items()
            if pattern not in existing
        )
        if not missing:
            return r[str].ok(source)
        for pattern, rules in missing:
            existing.add(pattern, sorted(rules))
        rendered = doc.as_string()
        try:
            tomlkit.parse(rendered)
        except ParseError as exc:
            return r[str].fail_op(f"generated invalid TOML: {path}", exc)
        return r[str].ok(rendered)

    def _format_rendered_pyproject(self, path: Path, rendered: str) -> p.Result[str]:
        """Format rendered pyproject TOML with the workspace Taplo contract."""
        cmd = ["taplo", "format", "-", "--stdin-filepath", str(path)]
        config_path = self.root / ".taplo.toml"
        if config_path.is_file():
            cmd.extend(["--config", str(config_path)])
        # mro-45r9: do not let a generated target .mise.toml hijack Taplo lookup.
        format_cwd = next(
            (candidate for candidate in self.root.parents if candidate.is_dir()),
            self.root,
        )
        format_result = u.Cli.run_raw(
            cmd, cwd=format_cwd, input_data=rendered.encode(c.Cli.ENCODING_DEFAULT)
        )
        if format_result.failure:
            return r[str].fail(format_result.error or "taplo format failed")
        output = format_result.value
        if output.exit_code != 0:
            detail = (output.stderr or output.stdout).strip()
            return r[str].fail(f"taplo format failed ({output.exit_code}): {detail}")
        return r[str].ok(output.stdout)

    def _project_is_flext_child(self, project_dir: Path) -> bool:
        """Detect a FLEXT consumer that shares a parent workspace ``.venv``.

        A workspace *root* owns the canonical virtualenv locally
        (``<project>/.venv``); a *child* (any flext-based consumer repo)
        references the parent workspace venv (``../.venv``). This keeps the
        pyright ``venvPath`` / pyrefly interpreter classification correct even
        when ``deps modernize`` is invoked from inside the child itself (so
        ``workspace_root`` defaults to the child dir). The committed
        ``Makefile`` ``WORKSPACE_ROOT`` assignment is the durable backstop when
        no virtualenv exists at modernize time.


        Returns:
            Whether the project is a FLEXT child sharing the workspace environment.
        """
        rules = config.Infra.tooling.tools.pyright.path_rules
        venv_name = rules.venv_name
        if (project_dir / venv_name).is_dir():
            return False
        if (project_dir.parent / venv_name).is_dir():
            return True
        makefile = project_dir / "Makefile"
        read = u.Cli.files_read_text(makefile)
        if read.success:
            for raw_line in read.value.splitlines():
                stripped = raw_line.strip()
                if not stripped.startswith("WORKSPACE_ROOT") or ":=" not in stripped:
                    continue
                _, _, value = stripped.partition(":=")
                if value.strip().startswith(".."):
                    return True
        return False

    def _process_document_state(
        self,
        state: p.Infra.PyprojectDocumentState,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
        rewrite_constraints: bool = False,
        locked_versions: t.MappingKV[str, str] | None = None,
        internal_names: t.StrSequence = (),
        constraint_policy: c.Infra.DependencyConstraintPolicy = c.Infra.DependencyConstraintPolicy.FLOOR,
        declared_python_dirs: t.StrSequence = (),
    ) -> t.StrSequence:
        """Process one parsed pyproject state and collect changes."""
        path = state.pyproject_path
        original_rendered = state.original_rendered
        payload = state.payload
        is_root = path.parent.resolve() == self.root.resolve() and not (
            self._project_is_flext_child(path.parent)
        )
        project_kind = "core"
        if not is_root:
            kind_result = self._classify_project(path.parent, payload=payload)
            if kind_result.success:
                project_kind = kind_result.value
        # mro-j47u (codex): declared roots are topology facts only during atomic
        # creation; normal modernization still derives productive roots on disk.
        changes: t.MutableSequenceOf[str] = []
        paths_manager = FlextInfraExtraPathsManager(workspace_root=self.root)
        changes.extend(self._ensure_build_system_payload(payload))
        changes.extend(self._remove_empty_poetry_groups_payload(payload))
        if rewrite_constraints:
            changes.extend(
                self._rewrite_dependency_constraints_payload(
                    payload,
                    locked_versions=locked_versions or {},
                    internal_names=internal_names,
                    policy=constraint_policy,
                )
            )
        changes.extend(
            FlextInfraConsolidateGroupsPhase().apply_payload(payload, canonical_dev)
        )
        changes.extend(
            FlextInfraEnsurePytestConfigPhase(
                config.Infra.tooling.tools.pytest
            ).apply_payload(payload)
        )
        # mro-j47u (codex): Pyrefly derives its include globs from the canonical
        # Pyright roots, so resolve Pyright first and converge in one pass.
        changes.extend(
            FlextInfraEnsurePyrightConfigPhase().apply_payload(
                payload,
                is_root=is_root,
                workspace_root=self.root,
                project_dir=path.parent,
                project_kind=project_kind,
                paths_manager=paths_manager,
                declared_python_dirs=declared_python_dirs,
            )
        )
        changes.extend(
            FlextInfraEnsurePyreflyConfigPhase().apply_payload(
                payload,
                is_root=is_root,
                project_dir=path.parent,
                paths_manager=paths_manager,
                declared_python_dirs=declared_python_dirs,
            )
        )
        changes.extend(
            FlextInfraEnsureMypyConfigPhase(
                config.Infra.tooling.tools.mypy
            ).apply_payload(payload)
        )
        changes.extend(
            FlextInfraEnsurePydanticMypyConfigPhase(
                config.Infra.tooling.tools.pydantic_mypy
            ).apply_payload(payload)
        )
        changes.extend(FlextInfraEnsureFormattingToolingPhase().apply_payload(payload))
        changes.extend(
            FlextInfraEnsureNamespaceToolingPhase().apply_payload(payload, path=path)
        )
        changes.extend(
            FlextInfraEnsureRuffConfigPhase().apply_payload(payload, path=path)
        )
        changes.extend(
            FlextInfraEnsurePackagingPhase().apply_payload(
                payload, path=path, is_root=is_root
            )
        )
        # mro-j47u: existing projects consume the same Vulture SSOT as scaffolds.
        changes.extend(
            FlextInfraEnsureVultureConfigPhase(
                config.Infra.tooling.tools.vulture
            ).apply_payload(payload)
        )
        changes.extend(
            FlextInfraEnsureCoverageConfigPhase().apply_payload(
                payload, project_kind=project_kind
            )
        )
        changes.extend(
            paths_manager.sync_payload(
                payload, project_dir=path.parent, is_root=is_root
            )
        )
        doc: t.Cli.TomlDocument = u.Cli.toml_document_from_mapping(payload)
        self._reorder_document_inplace(doc)
        state.payload = payload
        rendered = doc.as_string()
        if not skip_comments:
            rendered, comment_changes = FlextInfraInjectCommentsPhase().apply(rendered)
            changes.extend(comment_changes)
        formatted_result = self._format_rendered_pyproject(path, rendered)
        if formatted_result.failure:
            return [formatted_result.error or "taplo format failed"]
        rendered = formatted_result.value
        normalized_original = original_rendered.rstrip() + "\n"
        normalized_rendered = rendered.rstrip() + "\n"
        state.rendered = normalized_rendered
        if normalized_rendered == normalized_original:
            return ()
        if not dry_run:
            # Persist the same normalized value used for change detection.
            u.write_file(path, normalized_rendered, encoding=c.Cli.ENCODING_DEFAULT)
        return changes


__all__: list[str] = ["FlextInfraPyprojectModernizerDocumentMixin"]
