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

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these enums define the
    # one public conform contract shared by new and existing repositories. The
    # declarative values live in config/codegen.yaml; constants only type the
    # closed vocabulary used by models and CLI dispatch.

    @unique
    class CodegenConformScope(StrEnum):
        """Repository selection accepted by ``codegen conform``."""

        SELF = "self"
        MEMBERS = "members"
        ALL = "all"

    @unique
    class CodegenConformMode(StrEnum):
        """Read-only or write mode accepted by ``codegen conform``."""

        CHECK = "check"
        APPLY = "apply"

    @unique
    class MakeProfile(StrEnum):
        """Generated Makefile profile for one repository."""

        WORKSPACE_ROOT = "workspace-root"
        WORKSPACE_MEMBER = "workspace-member"
        STANDALONE = "standalone"

    @unique
    class RepositoryRole(StrEnum):
        """Repository role in a declared workspace topology."""

        WORKSPACE_ROOT = "workspace-root"
        WORKSPACE_MEMBER = "workspace-member"
        STANDALONE = "standalone"
        CONTENT_ONLY = "content-only"
        EXCLUDED = "excluded"

    @unique
    class RepositoryState(StrEnum):
        """Lifecycle state used by repository selection."""

        ACTIVE = "active"
        CONTENT_ONLY = "content-only"
        EXCLUDED = "excluded"

    @unique
    class ProjectKind(StrEnum):
        """New-project kind; drives deps, Makefile mode, and registration."""

        INTERNAL = "internal"
        EXTERNAL = "external"

    TEMPLATES_PROJECT_DIR: Final[str] = "project"
    "Subfolder under ``templates/`` holding project templates (engine param)."

    CODEGEN_CONFIG_FILENAME: Final[str] = "codegen.yaml"
    CODEGEN_SCHEMA_FILENAME: Final[str] = "codegen.schema.json"
    WORKSPACE_MANIFEST_FILENAME: Final[str] = "workspace.yaml"
    WORKSPACE_SCHEMA_FILENAME: Final[str] = "workspace.schema.json"
    CUSTOM_MAKE_FILENAME: Final[str] = "custom.mk"
    CUSTOM_HANDLER_PREFIX: Final[str] = "_custom_"
    PUBLIC_MAKE_VERBS: Final[tuple[str, ...]] = (
        "help",
        "setup",
        "deps",
        "build",
        "check",
        "test",
        "format",
        "run",
        "status",
        "docs",
        "clean",
        "release",
        "codegen",
    )

    TEMPLATE_MODULE_SKELETON: Final[str] = "module_skeleton.py.j2"
    "Scaffold module-skeleton template (replaces the legacy f-string)."

    # Each row: (relpath_template, output_relpath, kinds, delegate, overwrite).
    # kinds: tuple of ProjectKind the row applies to (BOTH = internal+external).
    # delegate: "render" (cli engine) today; lazy_init/version_file/basemk later.
    # Layout (operator, mro-wkii.13): base/ = common to both kinds (pyproject with
    # ``{% if project_kind %}`` branches); internal/ = member + REGISTRATION deltas;
    # external/ = delta-only (currently empty => external == base).
    _BOTH: Final[tuple[ProjectKind, ProjectKind]] = (
        ProjectKind.INTERNAL,
        ProjectKind.EXTERNAL,
    )
    _INTERNAL: Final[tuple[ProjectKind]] = (ProjectKind.INTERNAL,)
    _EXTERNAL: Final[tuple[ProjectKind]] = (ProjectKind.EXTERNAL,)

    PROJECT_TEMPLATE_ENTRIES: Final[
        tuple[tuple[str, str, tuple[ProjectKind, ...], str, bool], ...]
    ] = (
        # ---- base (internal + external): root files ----
        ("base/README.md.j2", "README.md", _BOTH, "render", False),
        ("base/LICENSE.j2", "LICENSE", _BOTH, "render", False),
        ("base/gitignore.j2", ".gitignore", _BOTH, "render", False),
        ("base/python-version.j2", ".python-version", _BOTH, "render", False),
        ("base/env.example.j2", ".env.example", _BOTH, "render", False),
        # NOTE(mro-wkii.14, agent codegen): mise + direnv para entregar
        # python/uv/ruff padronizados (.mise.toml) e ativação automática do
        # ambiente (.envrc) em todo scaffold.
        ("base/.mise.toml.j2", ".mise.toml", _BOTH, "render", False),
        ("base/.envrc.j2", ".envrc", _BOTH, "render", False),
        # NOTE(mro-wkii.14, agent codegen): external consumes flext-* directly via
        # git+branch in [tool.uv.sources]; local dev uses editable git submodules
        # under .flext-src/ (make setup). No flext-repo-map.toml / .flext-deps.
        ("base/Makefile.j2", "Makefile", _BOTH, "render", False),
        ("base/custom.mk.j2", "custom.mk", _BOTH, "render", False),
        ("base/pyproject.toml.j2", "pyproject.toml", _BOTH, "render", False),
        # NOTE(mro-wkii.13, agent codegen): minimal VS Code settings for the
        # generated project (interpreter .venv, ruff, pyrefly, pytest->tests).
        (
            "base/.vscode/settings.json.j2",
            ".vscode/settings.json",
            _BOTH,
            "render",
            False,
        ),
        # NOTE(mro-wkii.13, agent codegen): root conftest.py.j2 removed — pytest
        # config lives ONLY in tests/conftest.py (entry below). Generating a root
        # conftest.py put it outside tests/ and broke FLEXT layout (operator).
        # ---- base (internal + external): src package ----
        (
            "base/src/__init__.py.j2",
            "src/{package_name}/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        ("base/src/api.py.j2", "src/{package_name}/api.py", _BOTH, "render", False),
        # NOTE(mro-wkii.14, agent codegen): cli.py + __main__.py — thin declarative
        # CLI (algar/cosmos pattern) with 1 `ping` route; entry [project.scripts].
        ("base/src/cli.py.j2", "src/{package_name}/cli.py", _BOTH, "render", False),
        (
            "base/src/__main__.py.j2",
            "src/{package_name}/__main__.py",
            _BOTH,
            "render",
            False,
        ),
        ("base/src/base.py.j2", "src/{package_name}/base.py", _BOTH, "render", False),
        (
            "base/src/models.py.j2",
            "src/{package_name}/models.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/typings.py.j2",
            "src/{package_name}/typings.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/protocols.py.j2",
            "src/{package_name}/protocols.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/constants.py.j2",
            "src/{package_name}/constants.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/utilities.py.j2",
            "src/{package_name}/utilities.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_config.py.j2",
            "src/{package_name}/_config.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_settings.py.j2",
            "src/{package_name}/_settings.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/py.typed.j2",
            "src/{package_name}/py.typed",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/services/__init__.py.j2",
            "src/{package_name}/services/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/config/ns.yaml.j2",
            "src/{package_name}/config/{ns}.yaml",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): src _models ----
        (
            "base/src/_models/__init__.py.j2",
            "src/{package_name}/_models/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_models/config.py.j2",
            "src/{package_name}/_models/config.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_models/settings.py.j2",
            "src/{package_name}/_models/settings.py",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): src _constants ----
        (
            "base/src/_constants/__init__.py.j2",
            "src/{package_name}/_constants/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_constants/config.py.j2",
            "src/{package_name}/_constants/config.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_constants/settings.py.j2",
            "src/{package_name}/_constants/settings.py",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): src _protocols ----
        (
            "base/src/_protocols/__init__.py.j2",
            "src/{package_name}/_protocols/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_protocols/config.py.j2",
            "src/{package_name}/_protocols/config.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_protocols/settings.py.j2",
            "src/{package_name}/_protocols/settings.py",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): src _utilities ----
        (
            "base/src/_utilities/__init__.py.j2",
            "src/{package_name}/_utilities/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_utilities/config.py.j2",
            "src/{package_name}/_utilities/config.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/src/_utilities/settings.py.j2",
            "src/{package_name}/_utilities/settings.py",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): tests ----
        ("base/tests/__init__.py.j2", "tests/__init__.py", _BOTH, "render", False),
        ("base/tests/conftest.py.j2", "tests/conftest.py", _BOTH, "render", False),
        ("base/tests/base.py.j2", "tests/base.py", _BOTH, "render", False),
        (
            "base/tests/constants.py.j2",
            "tests/constants.py",
            _BOTH,
            "render",
            False,
        ),
        ("base/tests/typings.py.j2", "tests/typings.py", _BOTH, "render", False),
        (
            "base/tests/protocols.py.j2",
            "tests/protocols.py",
            _BOTH,
            "render",
            False,
        ),
        ("base/tests/models.py.j2", "tests/models.py", _BOTH, "render", False),
        (
            "base/tests/utilities.py.j2",
            "tests/utilities.py",
            _BOTH,
            "render",
            False,
        ),
        ("base/tests/settings.py.j2", "tests/settings.py", _BOTH, "render", False),
        ("base/tests/py.typed.j2", "tests/py.typed", _BOTH, "render", False),
        (
            "base/tests/unit/__init__.py.j2",
            "tests/unit/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/tests/unit/test_smoke.py.j2",
            "tests/unit/test_smoke.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/tests/unit/py.typed.j2",
            "tests/unit/py.typed",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/tests/integration/__init__.py.j2",
            "tests/integration/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        # NOTE(mro-wkii.13, agent codegen): every leaf test package owns a
        # base.py with its first class (mirrors src/; operator directive).
        (
            "base/tests/integration/base.py.j2",
            "tests/integration/base.py",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): shared fixtures (unified conftest SSOT) ----
        (
            "base/tests/fixtures/__init__.py.j2",
            "tests/fixtures/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        # ---- base (internal + external): e2e (public-entrypoint behavior) ----
        (
            "base/tests/e2e/__init__.py.j2",
            "tests/e2e/__init__.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/tests/e2e/base.py.j2",
            "tests/e2e/base.py",
            _BOTH,
            "render",
            False,
        ),
        (
            "base/tests/e2e/py.typed.j2",
            "tests/e2e/py.typed",
            _BOTH,
            "render",
            False,
        ),
        # ---- internal-only (member registration) ----
        (
            "internal/projects_member.md.j2",
            "projects/{dist}.md",
            _INTERNAL,
            "render",
            False,
        ),
        (
            "internal/REGISTRATION.md.j2",
            "REGISTRATION.md",
            _INTERNAL,
            "render",
            False,
        ),
    )


__all__: list[str] = ["FlextInfraConstantsCodegenProject"]
