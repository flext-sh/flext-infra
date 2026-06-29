# AUTO-GENERATED FILE — Regenerate with: make gen
"""Constants package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import build_lazy_import_map, install_lazy_exports

if _t.TYPE_CHECKING:
    from flext_infra._constants.base import (
        FlextInfraConstantsBase as FlextInfraConstantsBase,
    )
    from flext_infra._constants.basemk import (
        FlextInfraConstantsBasemk as FlextInfraConstantsBasemk,
    )
    from flext_infra._constants.census import (
        FlextInfraConstantsCensus as FlextInfraConstantsCensus,
    )
    from flext_infra._constants.check import (
        FlextInfraConstantsCheck as FlextInfraConstantsCheck,
    )
    from flext_infra._constants.codegen import (
        FlextInfraConstantsCodegen as FlextInfraConstantsCodegen,
    )
    from flext_infra._constants.deps import (
        FlextInfraConstantsDeps as FlextInfraConstantsDeps,
    )
    from flext_infra._constants.docs import (
        FlextInfraConstantsDocs as FlextInfraConstantsDocs,
    )
    from flext_infra._constants.github import (
        FlextInfraConstantsGithub as FlextInfraConstantsGithub,
    )
    from flext_infra._constants.make import (
        FlextInfraConstantsMake as FlextInfraConstantsMake,
    )
    from flext_infra._constants.namespace import (
        FlextInfraConstantsNamespace as FlextInfraConstantsNamespace,
    )
    from flext_infra._constants.refactor import (
        FlextInfraConstantsRefactor as FlextInfraConstantsRefactor,
    )
    from flext_infra._constants.release import (
        FlextInfraConstantsRelease as FlextInfraConstantsRelease,
    )
    from flext_infra._constants.rope import (
        FlextInfraConstantsRope as FlextInfraConstantsRope,
    )
    from flext_infra._constants.source_code import (
        FlextInfraConstantsSourceCode as FlextInfraConstantsSourceCode,
    )
    from flext_infra._constants.validate import (
        FlextInfraConstantsSharedInfra as FlextInfraConstantsSharedInfra,
    )
    from flext_infra._constants.workspace import (
        FlextInfraConstantsWorkspace as FlextInfraConstantsWorkspace,
    )
_LAZY_IMPORTS = build_lazy_import_map(
    {
        ".base": ("FlextInfraConstantsBase",),
        ".basemk": ("FlextInfraConstantsBasemk",),
        ".census": ("FlextInfraConstantsCensus",),
        ".check": ("FlextInfraConstantsCheck",),
        ".codegen": ("FlextInfraConstantsCodegen",),
        ".deps": ("FlextInfraConstantsDeps",),
        ".docs": ("FlextInfraConstantsDocs",),
        ".github": ("FlextInfraConstantsGithub",),
        ".make": ("FlextInfraConstantsMake",),
        ".namespace": ("FlextInfraConstantsNamespace",),
        ".refactor": ("FlextInfraConstantsRefactor",),
        ".release": ("FlextInfraConstantsRelease",),
        ".rope": ("FlextInfraConstantsRope",),
        ".source_code": ("FlextInfraConstantsSourceCode",),
        ".validate": ("FlextInfraConstantsSharedInfra",),
        ".workspace": ("FlextInfraConstantsWorkspace",),
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS, publish_all=False)
