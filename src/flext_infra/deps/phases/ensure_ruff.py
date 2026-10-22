"""Phase: Ensure standard Ruff configuration inline with known-first-party overlay.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from typing_extensions import TypeForm

from flext_infra import c, config, m, t, u
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.deps import FlextInfraExtraPathsManager
from flext_infra.deps.phases import FlextInfraToolTablesPhase
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraEnsureRuffConfigPhase:
    """Ensure standard Ruff configuration inline with known-first-party overlay."""

    def __init__(
        self,
        tool_config: m.Infra.ToolConfigDocument,
    ) -> None:
        """Bind the shared native policy without repository exemption overlays."""
        self._tool_config = tool_config

    @staticmethod
    def _workspace_exclusion_globs(project_dir: Path) -> t.StrSequence:
        """Return immutable repository and explicit exclusion path globs.

        Content-only repositories are foreign, read-only trees and therefore
        never enter Ruff. Explicit ``exclusions`` extend that same typed scope
        for non-repository paths without duplicating repository declarations.

        Returns:
            Immutable repository and explicit exclusion path globs.

        Raises:
            ValueError: If ``paths.failure``.

        """
        if not (project_dir / c.PYPROJECT_FILENAME).is_file():
            return ()
        paths = FlextInfraWorkspaceDetector.analysis_exclusion_paths(project_dir)
        if paths.failure:
            raise ValueError(paths.error or "workspace analysis scope is unavailable")
        return sorted(path.as_posix() for path in paths.value)

    @staticmethod
    def _analysis_exclusion_root_set(project_dir: Path) -> frozenset[str]:
        """First segments of the detector's declared analysis exclusions.

        Deliberately a DIFFERENT authority from
        ``FlextInfraToolTablesPhase.excluded_roots`` (the manifest
        non-participant set): this
        set drives the namespace-packages projection and follows the
        workspace detector's analysis-exclusion paths (gitmodules-driven).
        Like the manifest authority it is order-independent: a repository
        declares a retired tree once and every root-scoped projection
        converges.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If ``paths.failure``.

        """
        if not (project_dir / c.PYPROJECT_FILENAME).is_file():
            return frozenset()
        paths = FlextInfraWorkspaceDetector.analysis_exclusion_paths(project_dir)
        if paths.failure:
            raise ValueError(
                paths.error or "workspace analysis exclusions are unavailable",
            )
        return frozenset(p.parts[0] for p in paths.value if Path(p).parts)

    def _phase(
        self,
        *,
        path: Path,
        facts: m.Infra.RuffProjectFacts,
    ) -> m.Infra.DepsToml.PhaseConfig:
        """Build the canonical Ruff phase for one project path.

        Returns:
            The resulting ``m.Infra.DepsToml.PhaseConfig``.

        """
        ruff_cfg = self._tool_config.tools.ruff
        delegated_rules = FlextInfraGateRegistry.default().delegated_lint_rules(
            ruff_cfg.lint.rule_owners,
            check_gates=config.Infra.codegen.make.check_gates_default,
            repair_gates=(
                *config.Infra.codegen.make.check_gates_fixable,
                *config.Infra.codegen.make.fmt_gates,
            ),
        )
        workspace_exclusions = (
            self._workspace_exclusion_globs(path.parent)
            if facts.analysis_exclusions is None
            else facts.analysis_exclusions
        )
        # Dev/tooling source roots are config-declared, but a repository that
        # retired a tree (e.g. scripts/) must not keep analyzer entries naming
        # it: ruff fails hard on src roots whose directories do not exist, and
        # the namespace-packages contract only holds for roots on disk. The
        # declared lists stay the SSOT; existence filters the projection, with
        # roots the active plan is materializing accepted as present (the
        # extra-paths manager owns that declared set). In a Git checkout a root
        # is present only when Git tracks it: an ignored or untracked local
        # tree (a scratch scripts/ dir) must not change the projection, or the
        # local and CI renders of the same commit diverge.
        generated_roots = FlextInfraExtraPathsManager(
            repository_root=path.parent,
            generated_python_roots=facts.generated_python_roots,
        ).generated_python_roots
        tracked_roots = u.Infra.git_tracked_top_level_dir_names(path.parent)

        def _present(directory: str) -> bool:
            if directory in generated_roots:
                return True
            if tracked_roots is not None:
                return directory in tracked_roots
            return (path.parent / directory).is_dir()

        existing_root = tuple(
            directory
            for directory in u.Infra.native_tool_setting(
                self._tool_config, "ruff", "src", TypeForm(t.StrSequence)
            )
            if _present(directory)
        )
        excluded_roots = self._analysis_exclusion_root_set(path.parent)
        existing_namespace_packages = {
            directory
            for directory in (
                *u.Infra.native_tool_setting(
                    self._tool_config,
                    "ruff",
                    "namespace-packages",
                    TypeForm(t.StrSequence),
                ),
                *facts.repository_namespace_packages,
            )
            if directory not in excluded_roots
        }
        toml = m.Infra.DepsToml
        ruff_options = u.Infra.native_tool_configuration(
            self._tool_config, c.Infra.RUFF
        )
        ruff_options["target-version"] = (
            "py" + config.Infra.codegen.toolchain.python_version.replace(".", "")
        )
        ruff_options.update({
            "extend-exclude": list[t.JsonValue](
                sorted({
                    *config.Infra.codegen.analyzer_exclude_globs,
                    *workspace_exclusions,
                })
            ),
            "namespace-packages": list[t.JsonValue](
                sorted(existing_namespace_packages)
            ),
            "src": list[t.JsonValue](sorted(existing_root)),
        })
        lint_options = u.Cli.toml_mapping_ensure_table(
            ruff_options, c.Infra.LINT_SECTION
        )
        lint_options["ignore"] = list[t.JsonValue](
            sorted({
                *delegated_rules,
                *ruff_cfg.lint.ruling_disabled_rules,
                *u.Infra.native_tool_setting(
                    self._tool_config,
                    "ruff.lint",
                    "ignore",
                    TypeForm(t.StrSequence),
                ),
            })
        )
        isort_options = u.Cli.toml_mapping_ensure_table(lint_options, c.Infra.ISORT)
        isort_options[c.Infra.KNOWN_FIRST_PARTY_HYPHEN] = list[t.JsonValue](
            sorted(facts.first_party)
        )
        return toml.PhaseConfig(
            name="ruff",
            operations=(toml.SetOp(key=c.Infra.RUFF, value=ruff_options),),
        )

    def apply_payload(
        self,
        payload: t.MutableJsonMapping,
        *,
        path: Path,
        analysis_exclusions: t.StrSequence | None = None,
        generated_python_roots: t.StrSequence = (),
        repository_namespace_packages: t.StrTuple = (),
    ) -> t.StrSequence:
        """Apply canonical Ruff settings directly to one normalized payload.

        ``analysis_exclusions`` is the caller's declared topology; ``None``
        derives the workspace exclusion globs on disk.

        Returns:
            The resulting ``t.StrSequence``.

        """
        changes = list(
            u.Infra.apply_toml_phases(
                payload,
                self._phase(
                    path=path,
                    facts=m.Infra.RuffProjectFacts(
                        first_party=FlextInfraToolTablesPhase.first_party_namespaces(
                            path=path.parent,
                        ),
                        analysis_exclusions=analysis_exclusions,
                        generated_python_roots=generated_python_roots,
                        repository_namespace_packages=repository_namespace_packages,
                    ),
                ),
            ),
        )
        if u.Cli.toml_mapping_remove_key_if_present(payload, c.Infra.LINT_SECTION):
            changes.append("removed stale top-level [lint] section")
        return changes


__all__: list[str] = ["FlextInfraEnsureRuffConfigPhase"]
