# AUTO-GENERATED FILE — DO NOT EDIT MANUALLY.
# Regenerate with: make gen
#
"""Flext infra package."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING

from flext_core.lazy import install_lazy_exports, merge_lazy_imports

if _TYPE_CHECKING:
    from flext_cli import d, e, h, r, s, x
    from flext_core import FlextTypes

    from flext_infra.__version__ import *
    from flext_infra._constants import *
    from flext_infra._models import *
    from flext_infra._protocols import *
    from flext_infra._typings import *
    from flext_infra._utilities import *
    from flext_infra.basemk import *
    from flext_infra.check import *
    from flext_infra.cli import *
    from flext_infra.codegen import *
    from flext_infra.constants import *
    from flext_infra.deps import *
    from flext_infra.deps._phases import *
    from flext_infra.detectors import *
    from flext_infra.docs import *
    from flext_infra.gates import *
    from flext_infra.github import *
    from flext_infra.models import *
    from flext_infra.protocols import *
    from flext_infra.refactor import *
    from flext_infra.release import *
    from flext_infra.rules import *
    from flext_infra.transformers import *
    from flext_infra.typings import *
    from flext_infra.utilities import *
    from flext_infra.validate import *
    from flext_infra.workspace import *
    from flext_infra.workspace.maintenance import *

_LAZY_IMPORTS: Mapping[str, str | Sequence[str]] = merge_lazy_imports(
    (
        "flext_infra._constants",
        "flext_infra._models",
        "flext_infra._protocols",
        "flext_infra._typings",
        "flext_infra._utilities",
        "flext_infra.basemk",
        "flext_infra.check",
        "flext_infra.codegen",
        "flext_infra.deps",
        "flext_infra.detectors",
        "flext_infra.docs",
        "flext_infra.gates",
        "flext_infra.github",
        "flext_infra.refactor",
        "flext_infra.release",
        "flext_infra.rules",
        "flext_infra.transformers",
        "flext_infra.validate",
        "flext_infra.workspace",
    ),
    {
        "FlextInfraCli": "flext_infra.cli",
        "FlextInfraConstants": "flext_infra.constants",
        "FlextInfraModels": "flext_infra.models",
        "FlextInfraProtocols": "flext_infra.protocols",
        "FlextInfraTypes": "flext_infra.typings",
        "FlextInfraUtilities": "flext_infra.utilities",
        "FlextInfraVersion": "flext_infra.__version__",
        "__author__": "flext_infra.__version__",
        "__author_email__": "flext_infra.__version__",
        "__description__": "flext_infra.__version__",
        "__license__": "flext_infra.__version__",
        "__title__": "flext_infra.__version__",
        "__url__": "flext_infra.__version__",
        "__version__": "flext_infra.__version__",
        "__version_info__": "flext_infra.__version__",
        "_constants": "flext_infra._constants",
        "_models": "flext_infra._models",
        "_protocols": "flext_infra._protocols",
        "_typings": "flext_infra._typings",
        "_utilities": "flext_infra._utilities",
        "basemk": "flext_infra.basemk",
        "c": ("flext_infra.constants", "FlextInfraConstants"),
        "check": "flext_infra.check",
        "cli": "flext_infra.cli",
        "codegen": "flext_infra.codegen",
        "constants": "flext_infra.constants",
        "d": "flext_cli",
        "deps": "flext_infra.deps",
        "detectors": "flext_infra.detectors",
        "e": "flext_cli",
        "gates": "flext_infra.gates",
        "h": "flext_cli",
        "m": ("flext_infra.models", "FlextInfraModels"),
        "main": "flext_infra.cli",
        "models": "flext_infra.models",
        "p": ("flext_infra.protocols", "FlextInfraProtocols"),
        "protocols": "flext_infra.protocols",
        "r": "flext_cli",
        "refactor": "flext_infra.refactor",
        "rules": "flext_infra.rules",
        "s": "flext_cli",
        "t": ("flext_infra.typings", "FlextInfraTypes"),
        "transformers": "flext_infra.transformers",
        "typings": "flext_infra.typings",
        "u": ("flext_infra.utilities", "FlextInfraUtilities"),
        "utilities": "flext_infra.utilities",
        "validate": "flext_infra.validate",
        "workspace": "flext_infra.workspace",
        "x": "flext_cli",
    },
)


install_lazy_exports(__name__, globals(), _LAZY_IMPORTS)
