"""Modernize workspace pyproject.toml files to standardized format."""

from __future__ import annotations

from typing import Annotated, override

from flext_core import r
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.constants import c
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
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.utilities import u


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
            )
        ),
    ] = c.Infra.DependencyConstraintPolicy.FLOOR
    _tool_config: m.Infra.ToolConfigDocument = u.PrivateAttr()
    _paths_manager: FlextInfraExtraPathsManager | None = u.PrivateAttr(
        default_factory=lambda: None,
    )

    @override
    def model_post_init(self, __context: dict[str, p.AttributeProbe], /) -> None:
        """Initialize pyproject modernization collaborators after validation."""
        tool_config_result = u.Infra.load_tool_config()
        if tool_config_result.failure:
            msg = tool_config_result.error or "failed to load deps tool settings"
            raise ValueError(msg)
        self._tool_config = tool_config_result.value

    @property
    @override
    def paths_manager(self) -> FlextInfraExtraPathsManager:
        """Create the extra-paths manager only when a phase actually needs it."""
        if self._paths_manager is None:
            self._paths_manager = FlextInfraExtraPathsManager(
                workspace_root=self.root,
            )
        return self._paths_manager

    @override
    def execute(self) -> p.Result[bool]:
        """Execute pyproject modernization for the configured workspace."""
        exit_code = self.run()
        if exit_code != 0:
            return r[bool].fail("pyproject modernization failed")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraPyprojectModernizer"]
