"""Import bypass remover transformer — rope-based implementation.

Replaces try/except ImportError fallback blocks with the primary import.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from flext_infra import FlextInfraUtilitiesRope, t
from flext_infra.transformers._base import FlextInfraRopeTransformer


class FlextInfraRefactorImportBypassRemover(FlextInfraRopeTransformer):
    """Replace import bypass try/except blocks with the primary import."""

    _BYPASS_RE = re.compile(
        r"^try:\n"
        r"(    from .+\n)"
        r"except ImportError:\n"
        r"    from .+\n",
        re.MULTILINE,
    )

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Remove try/except ImportError fallback blocks, keep the primary import."""
        source = FlextInfraUtilitiesRope.read_source(resource)
        new_source, count = self._BYPASS_RE.subn(r"\1", source)
        if count == 0:
            return source, []
        changes = [f"Removed {count} import bypass fallback(s)"]
        for msg in changes:
            self._record_change(msg)
        FlextInfraUtilitiesRope.write_source(
            rope_project,
            resource,
            new_source,
            description="remove import bypass",
        )
        return new_source, list(self.changes)


__all__ = ["FlextInfraRefactorImportBypassRemover"]
