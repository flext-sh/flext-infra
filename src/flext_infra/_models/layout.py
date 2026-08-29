"""Layout engine config contracts and planning/apply result models.

flext-0wuz (epic flext-hzox): every layout decision is declarative data validated
from ``config/codegen.yaml`` — the engine carries zero hardcoded knowledge.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated, Literal

from flext_cli import m
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins as mm


class _LayoutContract(m.ContractModel):
    """Private declarative base for schema-loaded layout records.

    Mirrors ``_ConfigContract`` from ``_models/config.py``; kept local because
    ``config.py`` consumes this module (a reverse import would be a cycle).
    """

    model_config = m.ConfigDict(
        strict=False, frozen=True, extra="forbid", str_strip_whitespace=False
    )


class FlextInfraModelsLayout:
    """Field-only layout SSOT contracts and engine result models."""

    class LayoutSpec(_LayoutContract):
        """Fully modeled content of the ``layout`` section of ``codegen.yaml``."""

        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        severity: Annotated[
            Literal["warning", "error"],
            m.Field(description="Gate posture: warning reports, error fails"),
        ]
        archive_root: Annotated[
            t.NonEmptyStr, m.Field(description="Archive-not-delete root directory")
        ]
        docs_target: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical documentation directory")
        ]
        examples_target: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical examples directory")
        ]
        diagrams_target: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical diagrams directory")
        ]
        allow_hidden: Annotated[
            bool, m.Field(description="Whether any `.*` root entry is canonical")
        ] = True
        canonical_root_files: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Files allowed at the project root"),
        ]
        canonical_root_dotfiles: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Documented dotfiles allowed at the project root"),
        ]
        canonical_root_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Directories allowed at the project root"),
        ]
        move_docs_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Root docs directories moved under docs_target"),
        ]
        move_docs_files: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Root Markdown files moved under docs_target"),
        ]
        move_example_files: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Sample data files moved under examples_target"),
        ]
        move_diagram_globs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Root diagram globs moved under diagrams_target"),
        ]
        archive_names: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Root entries archived into archive_root"),
        ]
        archive_globs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Root entry globs archived into archive_root"),
        ]
        special_root_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Root directories skipped by the layout engine "
                    "(e.g. content submodule trees under data/)"
                )
            ),
        ] = ()
        reference_root_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "External reference corpora allowed at root "
                    "(same class as docs/references; not product docs)"
                )
            ),
        ] = ()

    class LayoutFinding(_LayoutContract):
        """One planned or executed layout decision for a project entry."""

        rule: Annotated[t.Infra.LayoutRule, m.Field(description="Decision kind")]
        path: Annotated[
            t.NonEmptyStr, m.Field(description="Project-relative source path")
        ]
        target: Annotated[
            str, m.Field(description="Project-relative destination path")
        ] = ""
        message: Annotated[
            t.NonEmptyStr, m.Field(description="Human-readable decision detail")
        ]
        status: Annotated[
            t.Infra.LayoutStatus, m.Field(description="Execution status")
        ] = "planned"

    class LayoutProjectReport(mm.ProjectNameMixin, _LayoutContract):
        """Per-project layout plan or apply outcome."""

        findings: Annotated[
            tuple[FlextInfraModelsLayout.LayoutFinding, ...],
            m.Field(description="All layout decisions for the project"),
        ] = ()

        @m.computed_field
        @property
        def actionable(self) -> tuple[FlextInfraModelsLayout.LayoutFinding, ...]:
            """Findings the engine acts on in apply mode (never review)."""
            return tuple(
                finding for finding in self.findings if finding.rule != "review"
            )

        @m.computed_field
        @property
        def applied_count(self) -> int:
            """Number of findings executed by an apply run."""
            return sum(1 for finding in self.findings if finding.status == "applied")

    class LayoutRunReport(_LayoutContract):
        """Batch layout outcome across the selected projects."""

        reports: Annotated[
            tuple[FlextInfraModelsLayout.LayoutProjectReport, ...],
            m.Field(description="Per-project layout outcomes"),
        ] = ()


__all__: list[str] = ["FlextInfraModelsLayout"]
