"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r

from flext_infra import c, m, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.deps._modernizer_constraints import (
    FlextInfraPyprojectModernizerConstraintsMixin,
)
from flext_infra.deps._modernizer_document import (
    FlextInfraPyprojectModernizerDocumentMixin,
)
from flext_infra.deps._modernizer_payload import (
    FlextInfraPyprojectModernizerPayloadMixin,
)
from flext_infra.deps._modernizer_run import (
    FlextInfraPyprojectModernizerRunMixin,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraPyprojectModernizer(
    FlextInfraProjectSelectionServiceBase[bool],
    FlextInfraPyprojectModernizerConstraintsMixin,
    FlextInfraPyprojectModernizerPayloadMixin,
    FlextInfraPyprojectModernizerDocumentMixin,
    FlextInfraPyprojectModernizerRunMixin,
):
    """Modernize all workspace pyproject.toml files."""

    audit: Annotated[
        bool,
        m.Field(False, description="Audit pyproject changes without writing"),
    ] = False
    skip_check: Annotated[
        bool,
        m.Field(alias="skip-check", description="Skip post-write validation"),
    ] = False
    skip_comments: Annotated[
        bool,
        m.Field(alias="skip-comments", description="Skip managed comment updates"),
    ] = False
    rewrite_constraints: Annotated[
        bool,
        m.Field(
            alias="rewrite-constraints",
            description="Rewrite dependency constraints from uv.lock",
        ),
    ] = False
    constraint_policy: Annotated[
        c.Infra.DependencyConstraintPolicy,
        m.Field(
            alias="constraint-policy",
            description="Policy used when rewriting dependency constraints",
        ),
        m.BeforeValidator(
            lambda v: (
                c.Infra.DependencyConstraintPolicy(v.strip().lower())
                if isinstance(v, str)
                else v
            ),
        ),
    ] = c.Infra.DependencyConstraintPolicy.FLOOR

    def conform_source(
        self,
        source: str,
        *,
        path: Path,
    ) -> p.Result[str]:
        """Return one canonical pyproject using the same phases as workspace apply."""
        payload_source = u.Cli.toml_mapping_from_text(source)
        if payload_source is None:
            return r[str].fail(f"invalid TOML: {path}")
        try:
            payload = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
                payload_source,
            )
            canonical_dev = t.Infra.STR_SEQ_ADAPTER.validate_python(
                u.Infra.canonical_dev_dependencies_from_payload(payload),
            )
        except c.ValidationError as exc:
            return r[str].fail_op("pyproject model validation", exc)
        state = m.Infra.PyprojectDocumentState(
            pyproject_path=path,
            original_rendered=source,
            payload=payload,
        )
        self._process_document_state(
            state,
            canonical_dev=canonical_dev,
            dry_run=True,
            skip_comments=False,
        )
        if not state.rendered:
            return r[str].fail(f"pyproject tooling render failed: {path}")
        return r[str].ok(state.rendered)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute pyproject modernization for the configured workspace."""
        exit_code = self.run()
        if exit_code != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPyprojectModernizer"]
