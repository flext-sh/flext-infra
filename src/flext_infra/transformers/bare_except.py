"""Rewrite bare ``except:`` clauses to ``except Exception:``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import override

from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t


class FlextInfraRefactorBareExcept(FlextInfraRopeTransformer):
    """Replace bare ``except:`` with ``except Exception:``."""

    _description = "rewrite bare except to except Exception"

    _BARE_EXCEPT_RE: re.Pattern[str] = re.compile(
        r"^(?P<indent>\s*)except\s*:(?P<trail>.*)$",
        re.MULTILINE,
    )

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Rewrite every bare except clause."""

        def replacer(match: re.Match[str]) -> str:
            self._record_change("Rewrote bare except to except Exception")
            return f"{match.group('indent')}except Exception:{match.group('trail')}"

        updated = self._BARE_EXCEPT_RE.sub(replacer, source)
        return updated, list(self.changes)


__all__: list[str] = ["FlextInfraRefactorBareExcept"]
