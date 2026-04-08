# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Constants package."""

from __future__ import annotations

import typing as _t

from flext_core.lazy import install_lazy_exports

if _t.TYPE_CHECKING:
    import flext_infra._constants.base as _flext_infra__constants_base

    base = _flext_infra__constants_base
    import flext_infra._constants.basemk as _flext_infra__constants_basemk
    from flext_infra._constants.base import FlextInfraConstantsBase

    basemk = _flext_infra__constants_basemk
    import flext_infra._constants.census as _flext_infra__constants_census
    from flext_infra._constants.basemk import FlextInfraConstantsBasemk

    census = _flext_infra__constants_census
    import flext_infra._constants.check as _flext_infra__constants_check
    from flext_infra._constants.census import FlextInfraConstantsCensus

    check = _flext_infra__constants_check
    import flext_infra._constants.codegen as _flext_infra__constants_codegen
    from flext_infra._constants.check import FlextInfraConstantsCheck

    codegen = _flext_infra__constants_codegen
    import flext_infra._constants.deps as _flext_infra__constants_deps
    from flext_infra._constants.codegen import FlextInfraConstantsCodegen

    deps = _flext_infra__constants_deps
    import flext_infra._constants.docs as _flext_infra__constants_docs
    from flext_infra._constants.deps import FlextInfraConstantsDeps

    docs = _flext_infra__constants_docs
    import flext_infra._constants.github as _flext_infra__constants_github
    from flext_infra._constants.docs import FlextInfraConstantsDocs

    github = _flext_infra__constants_github
    import flext_infra._constants.make as _flext_infra__constants_make
    from flext_infra._constants.github import FlextInfraConstantsGithub

    make = _flext_infra__constants_make
    import flext_infra._constants.refactor as _flext_infra__constants_refactor
    from flext_infra._constants.make import FlextInfraConstantsMake

    refactor = _flext_infra__constants_refactor
    import flext_infra._constants.release as _flext_infra__constants_release
    from flext_infra._constants.refactor import FlextInfraConstantsRefactor

    release = _flext_infra__constants_release
    import flext_infra._constants.rope as _flext_infra__constants_rope
    from flext_infra._constants.release import FlextInfraConstantsRelease

    rope = _flext_infra__constants_rope
    import flext_infra._constants.source_code as _flext_infra__constants_source_code
    from flext_infra._constants.rope import FlextInfraConstantsRope

    source_code = _flext_infra__constants_source_code
    import flext_infra._constants.validate as _flext_infra__constants_validate
    from flext_infra._constants.source_code import FlextInfraConstantsSourceCode

    validate = _flext_infra__constants_validate
    import flext_infra._constants.workspace as _flext_infra__constants_workspace
    from flext_infra._constants.validate import (
        FlextInfraConstantsCore,
        FlextInfraConstantsSharedInfra,
    )

    workspace = _flext_infra__constants_workspace
    from flext_infra._constants.workspace import FlextInfraConstantsWorkspace
_LAZY_IMPORTS = {
    "FlextInfraConstantsBasemk": (
        "flext_infra._constants.basemk",
        "FlextInfraConstantsBasemk",
    ),
    "FlextInfraConstantsCheck": (
        "flext_infra._constants.check",
        "FlextInfraConstantsCheck",
    ),
    "FlextInfraConstantsCodegen": (
        "flext_infra._constants.codegen",
        "FlextInfraConstantsCodegen",
    ),
    "FlextInfraConstantsBase": (
        "flext_infra._constants.base",
        "FlextInfraConstantsBase",
    ),
    "FlextInfraConstantsCensus": (
        "flext_infra._constants.census",
        "FlextInfraConstantsCensus",
    ),
    "FlextInfraConstantsMake": (
        "flext_infra._constants.make",
        "FlextInfraConstantsMake",
    ),
    "FlextInfraConstantsRope": (
        "flext_infra._constants.rope",
        "FlextInfraConstantsRope",
    ),
    "FlextInfraConstantsSourceCode": (
        "flext_infra._constants.source_code",
        "FlextInfraConstantsSourceCode",
    ),
    "FlextInfraConstantsCore": (
        "flext_infra._constants.validate",
        "FlextInfraConstantsCore",
    ),
    "FlextInfraConstantsDeps": (
        "flext_infra._constants.deps",
        "FlextInfraConstantsDeps",
    ),
    "FlextInfraConstantsDocs": (
        "flext_infra._constants.docs",
        "FlextInfraConstantsDocs",
    ),
    "FlextInfraConstantsGithub": (
        "flext_infra._constants.github",
        "FlextInfraConstantsGithub",
    ),
    "FlextInfraConstantsRefactor": (
        "flext_infra._constants.refactor",
        "FlextInfraConstantsRefactor",
    ),
    "FlextInfraConstantsRelease": (
        "flext_infra._constants.release",
        "FlextInfraConstantsRelease",
    ),
    "FlextInfraConstantsSharedInfra": (
        "flext_infra._constants.validate",
        "FlextInfraConstantsSharedInfra",
    ),
    "FlextInfraConstantsWorkspace": (
        "flext_infra._constants.workspace",
        "FlextInfraConstantsWorkspace",
    ),
    "base": "flext_infra._constants.base",
    "basemk": "flext_infra._constants.basemk",
    "census": "flext_infra._constants.census",
    "check": "flext_infra._constants.check",
    "codegen": "flext_infra._constants.codegen",
    "deps": "flext_infra._constants.deps",
    "docs": "flext_infra._constants.docs",
    "github": "flext_infra._constants.github",
    "make": "flext_infra._constants.make",
    "refactor": "flext_infra._constants.refactor",
    "release": "flext_infra._constants.release",
    "rope": "flext_infra._constants.rope",
    "source_code": "flext_infra._constants.source_code",
    "validate": "flext_infra._constants.validate",
    "workspace": "flext_infra._constants.workspace",
}

__all__ = [
    "FlextInfraConstantsBase",
    "FlextInfraConstantsBasemk",
    "FlextInfraConstantsCensus",
    "FlextInfraConstantsCheck",
    "FlextInfraConstantsCodegen",
    "FlextInfraConstantsCore",
    "FlextInfraConstantsDeps",
    "FlextInfraConstantsDocs",
    "FlextInfraConstantsGithub",
    "FlextInfraConstantsMake",
    "FlextInfraConstantsRefactor",
    "FlextInfraConstantsRelease",
    "FlextInfraConstantsRope",
    "FlextInfraConstantsSharedInfra",
    "FlextInfraConstantsSourceCode",
    "FlextInfraConstantsWorkspace",
    "base",
    "basemk",
    "census",
    "check",
    "codegen",
    "deps",
    "docs",
    "github",
    "make",
    "refactor",
    "release",
    "rope",
    "source_code",
    "validate",
    "workspace",
]


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
