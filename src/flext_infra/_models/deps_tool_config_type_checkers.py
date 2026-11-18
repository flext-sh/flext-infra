"""Pyrefly tool configuration models for the deps subpackage.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath
from typing import Annotated, Self

from flext_cli import m

from flext_infra import t
from flext_infra._models import FlextInfraModelsDepsToolConfigLinters


class FlextInfraModelsDepsToolConfigTypeCheckers:
    """Type checker configuration models."""

    class DiagnosticPathException(m.ContractModel):
        """One authorized rule-level exception for an existing file or directory.

        The entry renders the Pyrefly sub-config of its root; no second list
        exists.
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

    class PyreflyConfig(m.ArbitraryTypesModel):
        """Pyrefly execution and path policy; native options live in settings."""

        findings_exit_codes: tuple[int, ...] = m.Field(
            (), alias="findings-exit-codes", description="Native diagnostic statuses"
        )
        ruling_disabled_rules: tuple[t.NonEmptyStr, ...] = m.Field(
            (),
            alias="ruling-disabled-rules",
            strict=False,
            description=(
                "Operator-authorized global axioms: Pyrefly error kinds disabled "
                "at the SSOT for every project, projected as ignore."
            ),
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
            diagnostic_path_exceptions: tuple[
                (FlextInfraModelsDepsToolConfigTypeCheckers.DiagnosticPathException),
                ...,
            ] = m.Field(
                (),
                alias="diagnostic-path-exceptions",
                description=(
                    "Authorized rule exceptions; each entry renders its Pyrefly "
                    "sub-config."
                ),
            )

        path_rules: PathRulesConfig = m.Field(
            alias="path-rules", description="Pyrefly search-path rules."
        )


__all__: list[str] = ["FlextInfraModelsDepsToolConfigTypeCheckers"]
