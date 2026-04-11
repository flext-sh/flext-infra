"""Import bypass remover transformer — rope-based implementation.

Replaces try/except ImportError fallback blocks with the primary import.
"""

from __future__ import annotations

import re
from typing import override

from flext_infra import FlextInfraRopeTransformer, t


class FlextInfraRefactorImportBypassRemover(FlextInfraRopeTransformer):
    """Replace import bypass try/except blocks with the primary import."""

    _BYPASS_RE = re.compile(
        r"^try:\n"
        r"(    from .+\n)"
        r"except ImportError:\n"
        r"    from .+\n",
        re.MULTILINE,
    )

    @override
    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> t.Infra.TransformResult:
        """Remove try/except ImportError fallback blocks, keep the primary import."""
        source = resource.read()
        new_source, count = self._BYPASS_RE.subn(r"\1", source)
        if count == 0:
            no_changes: list[str] = []
            return source, no_changes
        changes = [f"Removed {count} import bypass fallback(s)"]
        for msg in changes:
            self._record_change(msg)
        resource.write(new_source)
        return new_source, list(self.changes)


__all__ = ["FlextInfraRefactorImportBypassRemover"]
