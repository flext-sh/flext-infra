"""Project-scaffold manifest (data) for ``flext-infra codegen new``.

Per ADR-005 this is the single source of truth describing *which* templates make
up a new project and *where* each lands. The engine (``u.Cli.template_render_dir``,
flext-cli) is policy-free; this manifest + the rope-derived context carry all the
FLEXT naming policy. Adding a file or a kind is a data edit here + a ``.j2`` drop
in ``templates/``.

Output paths use ``{token}`` placeholders (resolved by the service from rope) so
the engine never sees FLEXT naming. NOTE: the large-row form migrates to
``config/codegen/project_manifest.yaml`` in the ``conform`` slice (ADR-005 SSOT).

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from enum import StrEnum, unique
from typing import Final


class FlextInfraConstantsCodegenProject:
    """Manifest + naming constants for project creation (flat in ``c.Infra.*``)."""

    @unique
    class ProjectKind(StrEnum):
        """New-project kind; drives deps, Makefile mode, and registration."""

        INTERNAL = "internal"
        EXTERNAL = "external"

    TEMPLATES_PROJECT_DIR: Final[str] = "project"
    "Subfolder under ``templates/`` holding project templates (engine param)."

    TEMPLATE_MODULE_SKELETON: Final[str] = "module_skeleton.py.j2"
    "Scaffold module-skeleton template (replaces the legacy f-string)."

    # Each row: (relpath_template, output_relpath, kinds, delegate, overwrite).
    # kinds: tuple of ProjectKind the row applies to (BOTH = internal+external).
    # delegate: "render" (cli engine) today; lazy_init/version_file/basemk later.
    _BOTH: Final[tuple[ProjectKind, ProjectKind]] = (
        ProjectKind.INTERNAL,
        ProjectKind.EXTERNAL,
    )
    _INTERNAL: Final[tuple[ProjectKind]] = (ProjectKind.INTERNAL,)
    _EXTERNAL: Final[tuple[ProjectKind]] = (ProjectKind.EXTERNAL,)

    PROJECT_TEMPLATE_ENTRIES: Final[
        tuple[tuple[str, str, tuple[ProjectKind, ...], str, bool], ...]
    ] = (
        # ---- shared (internal + external) ----
        ("_shared/conftest.py.j2", "conftest.py", _BOTH, "render", False),
        ("_shared/README.md.j2", "README.md", _BOTH, "render", False),
        ("_shared/LICENSE.j2", "LICENSE", _BOTH, "render", False),
        ("_shared/gitignore.j2", ".gitignore", _BOTH, "render", False),
        ("_shared/python-version.j2", ".python-version", _BOTH, "render", False),
        ("_shared/env.example.j2", ".env.example", _BOTH, "render", False),
        ("_shared/mkdocs.yml.j2", "mkdocs.yml", _BOTH, "render", False),
        (
            "_shared/src/__init__.py.j2",
            "src/{package_name}/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/__version__.py.j2",
            "src/{package_name}/__version__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/constants.py.j2",
            "src/{package_name}/constants.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/typings.py.j2",
            "src/{package_name}/typings.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/protocols.py.j2",
            "src/{package_name}/protocols.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/models.py.j2",
            "src/{package_name}/models.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/utilities.py.j2",
            "src/{package_name}/utilities.py",
            _BOTH,
            "render",
            False,
        ),
        ("_shared/src/base.py.j2", "src/{package_name}/base.py", _BOTH, "render", False),
        ("_shared/src/api.py.j2", "src/{package_name}/api.py", _BOTH, "render", False),
        (
            "_shared/src/_settings.py.j2",
            "src/{package_name}/_settings.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/_config.py.j2",
            "src/{package_name}/_config.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/services/__init__.py.j2",
            "src/{package_name}/services/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/config/ns.yaml.j2",
            "src/{package_name}/config/{ns}.yaml",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/src/py.typed.j2",
            "src/{package_name}/py.typed",
            _BOTH,
            "render",
            False,
        ),
        ("_shared/tests/__init__.py.j2", "tests/__init__.py", _BOTH, "render", False),
        ("_shared/tests/conftest.py.j2", "tests/conftest.py", _BOTH, "render", False),
        ("_shared/tests/base.py.j2", "tests/base.py", _BOTH, "render", False),
        (
            "_shared/tests/constants.py.j2",
            "tests/constants.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/tests/unit/__init__.py.j2",
            "tests/unit/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/tests/unit/test_smoke.py.j2",
            "tests/unit/test_smoke.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "_shared/tests/integration/__init__.py.j2",
            "tests/integration/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        ("_shared/tests/py.typed.j2", "tests/py.typed", _BOTH, "render", False),
        # ---- internal-only ----
        ("internal/pyproject.toml.j2", "pyproject.toml", _INTERNAL, "render", False),
        ("internal/Makefile.j2", "Makefile", _INTERNAL, "render", False),
        ("internal/custom.mk.j2", "custom.mk", _INTERNAL, "render", False),
        (
            "internal/projects_member.md.j2",
            "projects/{dist}.md",
            _INTERNAL,
            "render",
            False,
        ),
        ("internal/REGISTRATION.md.j2", "REGISTRATION.md", _INTERNAL, "render", False),
        # ---- external-only ----
        ("external/pyproject.toml.j2", "pyproject.toml", _EXTERNAL, "render", False),
        ("external/Makefile.j2", "Makefile", _EXTERNAL, "render", False),
        ("external/custom.mk.j2", "custom.mk", _EXTERNAL, "render", False),
    )


__all__: list[str] = ["FlextInfraConstantsCodegenProject"]
