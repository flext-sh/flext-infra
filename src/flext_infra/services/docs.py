"""Public docs service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence

from flext_core import r
from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
)


class FlextInfraServiceDocsMixin:
    """Expose documentation operations through the public infra facade."""

    def audit_docs(self, params: FlextInfraDocAuditor) -> r[bool]:
        """Audit documentation through the public facade."""
        return FlextInfraDocAuditor.execute_command(params)

    def fix_docs(self, params: FlextInfraDocFixer) -> r[bool]:
        """Fix documentation through the public facade."""
        return FlextInfraDocFixer.execute_command(params)

    def build_docs(self, params: FlextInfraDocBuilder) -> r[bool]:
        """Build documentation through the public facade."""
        return FlextInfraDocBuilder.execute_command(params)

    def generate_docs(self, params: FlextInfraDocGenerator) -> r[bool]:
        """Generate documentation through the public facade."""
        return FlextInfraDocGenerator.execute_command(params)

    def validate_docs(self, params: FlextInfraDocValidator) -> r[bool]:
        """Validate documentation through the public facade."""
        return FlextInfraDocValidator.execute_command(params)


__all__: Sequence[str] = ("FlextInfraServiceDocsMixin",)
