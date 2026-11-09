"""Pyright and Pyrefly tool configuration models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Annotated, ClassVar, Self

from flext_cli import m, u
from typing_extensions import TypeForm

from flext_infra import c, t
from flext_infra._models import FlextInfraModelsDepsToolConfigLinters


class FlextInfraModelsDepsToolConfigTypeCheckers:
    """Type checker configuration models."""

    class DiagnosticPathException(m.ContractModel):
        """One authorized rule-level exception for an existing file or directory.

        The same entry renders the Pyright execution environment and the
        Pyrefly sub-config of its root; no second list exists.
        """

        root: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project-relative file or directory the rules govern."),
        ]
        rationale: Annotated[
            t.NonEmptyStr,
            m.Field(description="Verified technical cause of the exception."),
        ]
        authorization: Annotated[
            (
                (FlextInfraModelsDepsToolConfigLinters.TrackerAuthorization)
                | (FlextInfraModelsDepsToolConfigLinters.OperatorAuthorization)
            ),
            m.Field(description="Tracker key or verbatim operator approval."),
        ]
        changes: Annotated[
            tuple[
                (FlextInfraModelsDepsToolConfigLinters.DiagnosticRuleChange),
                ...,
            ],
            m.Field(
                min_length=1,
                strict=False,
                description="Rule-level changes, each naming its checker.",
            ),
        ]

        @m.model_validator(mode="after")
        def _validate_scope(self) -> Self:
            """Keep the root project-relative and each checker rule single-valued.

            Returns:
                The validated exception.

            Raises:
                ValueError: If the root is absolute, escapes the project, is a
                    glob, or one checker rule changes twice.

            """
            path = PurePosixPath(self.root)
            violations = (
                path.is_absolute(),
                not path.parts,
                ".." in path.parts,
                path.as_posix() != self.root,
                any(token in self.root for token in "*?["),
            )
            if any(violations):
                msg = (
                    f"diagnostic exception root {self.root!r} must be a "
                    "normalized project-relative path, not a glob"
                )
                raise ValueError(msg)
            keys = [(change.checker, change.rule) for change in self.changes]
            if len(set(keys)) != len(keys):
                msg = f"diagnostic exception {self.root!r} changes one rule twice"
                raise ValueError(msg)
            return self

    class PyrightConfig(m.ArbitraryTypesModel):
        """Pyright strict settings loaded from YAML."""

        class ExecutionEnvironment(m.ContractModel):
            """Pyright execution environment entry."""

            model_config: ClassVar[t.ConfigDict] = m.ConfigDict(populate_by_name=True)

            root: Annotated[
                str,
                m.Field(description="Execution environment root path."),
            ]
            report_private_usage: str = m.Field(
                alias=c.Infra.REPORT_PRIVATE_USAGE,
                description="reportPrivateUsage override for this environment.",
            )
            extra_paths: Sequence[str] = m.Field(
                alias=c.Infra.EXTRA_PATHS,
                description="extraPaths applied to this execution environment.",
            )
            diagnostic_levels: Mapping[str, str] = m.Field(
                default_factory=u.empty(TypeForm(Mapping[str, str])),
                exclude=True,
                description=(
                    "Authorized native rule levels the renderer adds to this "
                    "environment's payload."
                ),
            )

        class PathRulesConfig(m.ArbitraryTypesModel):
            """Path resolution rules loaded from YAML."""

            project_root_env_dirs: Sequence[str] = m.Field(
                (),
                alias="project-root-env-dirs",
                description=(
                    "Included directories resolved from their project package parent."
                ),
            )

            source_dir: str = m.Field(
                "src", alias="source-dir", description="Primary source directory name."
            )
            project_root: str = m.Field(
                ".",
                alias="project-root",
                description="Project root path entry used in path resolution.",
            )
            env_dirs: Sequence[str] = m.Field(
                (),
                alias="env-dirs",
                description="Canonical execution environment directories in order.",
            )
            test_like_dirs: Sequence[str] = m.Field(
                (),
                alias="test-like-dirs",
                description="Env dirs that should include project root in extraPaths.",
            )
            default_excludes: Sequence[str] = m.Field(
                (),
                alias="default-excludes",
                description="Always-applied pyright exclude globs.",
            )
            ignored_diagnostic_globs: Sequence[str] = m.Field(
                (),
                alias="ignored-diagnostic-globs",
                description=(
                    "Pyright ignore globs for files that remain on search paths but "
                    "must not emit diagnostics."
                ),
            )
            diagnostic_path_exceptions: tuple[
                (FlextInfraModelsDepsToolConfigTypeCheckers.DiagnosticPathException),
                ...,
            ] = m.Field(
                (),
                alias="diagnostic-path-exceptions",
                description=(
                    "Authorized rule exceptions; each entry renders its Pyright "
                    "environment and its Pyrefly sub-config."
                ),
            )
            source_report_private_usage: str = m.Field(
                alias="source-report-private-usage",
                description="reportPrivateUsage value for source-dir execution envs.",
            )
            test_like_report_private_usage: str = m.Field(
                alias="test-like-report-private-usage",
                description="reportPrivateUsage value for test-like execution envs.",
            )
            other_report_private_usage: str = m.Field(
                alias="other-report-private-usage",
                description=(
                    "reportPrivateUsage value for non-source/non-test-like envs."
                ),
            )

        path_rules: PathRulesConfig = m.Field(
            alias="path-rules",
            description="Pyright path resolution and execution-env rules.",
        )
        ruling_disabled_rules: tuple[t.NonEmptyStr, ...] = m.Field(
            (),
            alias="ruling-disabled-rules",
            strict=False,
            description=(
                "Operator-authorized global axioms: Pyright rules disabled at "
                "the SSOT for every project, projected as level none."
            ),
        )

    class PyreflyConfig(m.ArbitraryTypesModel):
        """Pyrefly execution and path policy; native options live in settings."""

        findings_exit_codes: tuple[int, ...] = m.Field(
            (), alias="findings-exit-codes", description="Native diagnostic statuses"
        )

        class PathRulesConfig(m.ArbitraryTypesModel):
            """Path resolution rules loaded from YAML."""

            source_dir: str = m.Field(
                "src", alias="source-dir", description="Primary source directory name."
            )
            project_root: str = m.Field(
                ".",
                alias="project-root",
                description="Project root path entry used in search-path.",
            )
            env_dirs: Sequence[str] = m.Field(
                (),
                alias="env-dirs",
                description="Canonical directories used to build project-includes.",
            )
            workspace_include_children: bool = m.Field(
                default=False,
                alias="workspace-include-children",
                description="Whether root pyrefly should include child projects.",
            )
            workspace_include_child_env_dirs: Sequence[str] = m.Field(
                (),
                alias="workspace-include-child-env-dirs",
                description="Child env dirs included by root pyrefly when enabled.",
            )
            project_shared_search_paths: Sequence[str] = m.Field(
                (),
                alias="project-shared-search-paths",
                description=(
                    "Additional shared workspace paths for declared_repository pyrefly "
                    "search-path."
                ),
            )

        path_rules: PathRulesConfig = m.Field(
            alias="path-rules", description="Pyrefly search-path rules."
        )


__all__: list[str] = ["FlextInfraModelsDepsToolConfigTypeCheckers"]
