"""Phase: Ensure standard Ruff configuration inline with known-first-party overlay.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config, m, p, t, u
from flext_infra.deps.toml_phase import FlextInfraTomlPhaseService


class FlextInfraEnsureRuffConfigPhase:
    """Ensure standard Ruff configuration inline with known-first-party overlay."""

    def __init__(self, tool_config: p.Infra.ToolConfigDocument) -> None:
        """Store tool configuration used to build canonical Ruff settings."""
        self._tool_config = tool_config

    @staticmethod
    def _workspace_project_namespaces(project_dir: Path) -> t.StrSequence:
        """Discover child project packages when generating workspace root settings."""
        discovered = u.Infra.discover_projects(project_dir)
        if discovered.failure:
            return ()
        return sorted({
            project.package_name
            for project in discovered.value
            if (
                project.package_name
                and project.package_name.isidentifier()
                and (
                    project.workspace_role
                    == c.Infra.WorkspaceProjectRole.WORKSPACE_MEMBER
                )
            )
        })

    @staticmethod
    def _remove_stale_lint_section(doc: t.Cli.TomlDocument) -> t.StrSequence:
        """Remove the stale top-level ``[lint]`` table left by old configs."""
        if c.Infra.LINT_SECTION not in doc:
            return ()
        del doc[c.Infra.LINT_SECTION]
        return ["removed stale top-level [lint] section"]

    @staticmethod
    def _remove_stale_lint_section_payload(
        payload: t.MutableJsonMapping,
    ) -> t.StrSequence:
        """Remove the stale top-level ``[lint]`` table from one plain payload."""
        if u.Cli.toml_mapping_remove_key_if_present(payload, c.Infra.LINT_SECTION):
            return ["removed stale top-level [lint] section"]
        return ()

    def _phase(
        self,
        *,
        path: Path,
        workspace_namespaces: t.StrSequence,
        stale_patterns: t.StrSequence,
        include_handler: bool,
    ) -> p.Cli.TomlPhaseConfig:
        """Build the canonical Ruff phase for one project path."""
        ruff_cfg = self._tool_config.tools.ruff
        effective_src = sorted(ruff_cfg.src)
        # NOTE(mro-p68a.5, agent codex): models stay declaration-only; the
        # Ruff phase owns the derived union consumed by emitted tool config.
        effective_ignore = tuple(
            sorted({*ruff_cfg.lint.ignore, *ruff_cfg.lint.ignored_rule_rationales})
        )
        detected_packages = sorted({
            *config.Infra.tooling.tools.deptry.known_first_party,
            *u.Infra.discover_first_party_namespaces(path.parent),
            *workspace_namespaces,
            *self._workspace_project_namespaces(path.parent),
        })
        lint_nested_values: t.SequenceOf[tuple[str, t.JsonValue]] = (
            ("select", u.normalize_to_json_value(sorted(ruff_cfg.lint.select))),
            (c.Infra.IGNORE, u.normalize_to_json_value(effective_ignore)),
        )
        isort_values: list[tuple[str, t.JsonValue]] = [
            ("combine-as-imports", ruff_cfg.lint.isort.combine_as_imports),
            ("force-single-line", ruff_cfg.lint.isort.force_single_line),
            ("split-on-trailing-comma", ruff_cfg.lint.isort.split_on_trailing_comma),
        ]
        if detected_packages:
            isort_values.append((
                c.Infra.KNOWN_FIRST_PARTY_HYPHEN,
                u.normalize_to_json_value(detected_packages),
            ))
        phase = (
            m.Cli.TomlPhaseConfig
            .Builder("ruff")
            .table(c.Infra.RUFF)
            .deprecated(c.Infra.EXTEND)
            .list(c.Infra.EXCLUDE, sorted(ruff_cfg.exclude))
            .list("namespace-packages", sorted(ruff_cfg.namespace_packages))
            .value("fix", ruff_cfg.fix)
            .value("line-length", ruff_cfg.line_length)
            .value("preview", ruff_cfg.preview)
            .value("respect-gitignore", ruff_cfg.respect_gitignore)
            .value("show-fixes", ruff_cfg.show_fixes)
            .value("target-version", ruff_cfg.target_version)
            .list("src", effective_src)
            .nested(
                "format",
                values=(
                    ("docstring-code-format", ruff_cfg.format.docstring_code_format),
                    ("indent-style", ruff_cfg.format.indent_style),
                    ("line-ending", ruff_cfg.format.line_ending),
                    ("quote-style", ruff_cfg.format.quote_style),
                    (
                        "skip-magic-trailing-comma",
                        ruff_cfg.format.skip_magic_trailing_comma,
                    ),
                ),
            )
            .nested(c.Infra.LINT_SECTION, values=lint_nested_values)
            # mro-wkii.17.26.2 (codex): emit the canonical DOC201 scope while
            # preserving the rule for every multiline docstring.
            .nested(
                c.Infra.LINT_SECTION,
                "pydoclint",
                values=(
                    (
                        "ignore-one-line-docstrings",
                        ruff_cfg.lint.pydoclint.ignore_one_line_docstrings,
                    ),
                ),
            )
            # mro-wkii.17.26.2 (codex): emit the operator-approved Google
            # docstring convention from the validated tooling SSOT.
            .nested(
                c.Infra.LINT_SECTION,
                "pydocstyle",
                values=(("convention", ruff_cfg.lint.pydocstyle.convention),),
            )
            .nested(
                c.Infra.LINT_SECTION,
                "flake8-tidy-imports",
                "banned-api",
                values=tuple(
                    (name, u.normalize_to_json_value({"msg": message}))
                    for name, message in ruff_cfg.lint.banned_api.items()
                ),
            )
            .nested(c.Infra.LINT_SECTION, c.Infra.ISORT, values=tuple(isort_values))
            .nested(
                c.Infra.LINT_SECTION,
                "per-file-ignores",
                values=tuple(
                    (pattern, u.normalize_to_json_value(sorted(rules)))
                    for pattern, rules in ruff_cfg.lint.per_file_ignores.items()
                ),
                deprecated_keys=stale_patterns,
            )
            .build()
        )
        if include_handler:
            return phase.model_copy(
                update={"custom_handler": self._remove_stale_lint_section}
            )
        return phase

    def apply(self, doc: t.Cli.TomlDocument, *, path: Path) -> t.StrSequence:
        """Apply canonical Ruff tables with namespace-aware first-party detection."""
        per_file_ignores = u.Cli.toml_table_path(
            doc, (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION, "per-file-ignores")
        )
        stale_patterns = (
            [
                pattern
                for pattern in per_file_ignores
                if pattern not in self._tool_config.tools.ruff.lint.per_file_ignores
            ]
            if per_file_ignores is not None
            else ()
        )
        return FlextInfraTomlPhaseService.apply_phases(
            doc,
            self._phase(
                path=path,
                # mro-j47u (codex): installed and workspace FLEXT dependencies
                # share the same first-party import contract.
                workspace_namespaces=u.Infra.flext_dependency_namespaces(doc),
                stale_patterns=stale_patterns,
                include_handler=True,
            ),
        )

    def apply_payload(
        self, payload: t.MutableJsonMapping, *, path: Path
    ) -> t.StrSequence:
        """Apply canonical Ruff settings directly to one normalized payload."""
        per_file_ignores = u.Cli.toml_mapping_path(
            payload,
            (c.Infra.TOOL, c.Infra.RUFF, c.Infra.LINT_SECTION, "per-file-ignores"),
        )
        stale_patterns = (
            [
                pattern
                for pattern in list(per_file_ignores)
                if pattern not in self._tool_config.tools.ruff.lint.per_file_ignores
            ]
            if per_file_ignores is not None
            else ()
        )
        changes = list(
            FlextInfraTomlPhaseService.apply_payload_phases(
                payload,
                self._phase(
                    path=path,
                    workspace_namespaces=tuple(
                        u.Infra.flext_dependency_namespaces_from_payload(payload)
                    )
                    + config.Infra.tooling.tools.deptry.known_first_party
                    + (
                        u.Infra.project_name_from_payload(path, payload).replace(
                            "-", "_"
                        ),
                    ),
                    stale_patterns=stale_patterns,
                    include_handler=False,
                ),
            )
        )
        changes.extend(self._remove_stale_lint_section_payload(payload))
        return changes


__all__: list[str] = ["FlextInfraEnsureRuffConfigPhase"]
