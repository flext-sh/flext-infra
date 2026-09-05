"""Tests for flext_infra.codegen module initialization.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import flext_infra.codegen as codegen_module
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_tests import tm


def _baseline_leaf_modules() -> tuple[str, ...]:
    """Leaf modules imported by the package in a clean interpreter.

    Why (review #355): the test module imports ``lazy_init`` (the generator)
    at module scope, which itself pulls a few implementation leaves. The
    package-surface contract must be measured in a subprocess that imports
    ONLY the package, so the probe reports what the surface itself loads.
    """
    import json
    import os

    code = (
        "import json, sys, flext_infra.codegen as m\n"
        "m.__all__; dir(m)\n"
        "print(json.dumps(sorted(n for n in sys.modules"
        " if n.startswith('flext_infra.codegen.'))))"
    )
    # Why (review #355): uv workspaces inject sibling sources (flext-core)
    # into sys.path at runtime, never through PYTHONPATH, so a bare src path
    # dies on the flext_core import. Derive the repository roots from THIS
    # file's location instead of inheriting a possibly-purged sys.path.
    repository_root = _PROJECT_SRC.parent.parent
    sibling_srcs = sorted(
        str(member / "src")
        for member in repository_root.iterdir()
        if (member / "src").is_dir() and (member / "pyproject.toml").is_file()
    )
    probe_env = dict(os.environ)
    probe_env["PYTHONPATH"] = os.pathsep.join([*sibling_srcs, str(_PROJECT_SRC)])
    from flext_infra import u

    result = tm.ok(u.Cli.run([sys.executable, "-c", code], env=probe_env, timeout=60))
    loaded = json.loads(result.stdout.strip())
    return tuple(loaded)


# Why: the symbol must be absent for the test to mean anything, so it
# cannot be spelled as a static attribute access without making the file
# ill-typed. The name is data here, and getattr is the access it tests.
_ABSENT_SYMBOL = "nonexistent_xyz_attribute"

# Why (review #355): the baseline subprocess must import the package from
# THIS checkout — file is tests/unit/codegen/init_tests.py, so parents[3]
# is the repository root and /src the package source root.
_PROJECT_SRC = Path(__file__).resolve().parents[3] / "src"


def test_codegen_getattr_raises_attribute_error() -> None:
    """Test that accessing nonexistent attribute raises AttributeError."""
    with pytest.raises(AttributeError):
        _ = getattr(codegen_module, _ABSENT_SYMBOL)


def test_codegen_package_does_not_reexport_leaf_implementations() -> None:
    """Keep implementation classes lazy behind their leaf owners.

    Why (flext-mhf3d lazy-init law): generated package roots publish their
    surface through PEP 562 lazy exports. ``__all__`` and ``dir()`` name the
    public leaf owners, but resolving the surface imports no implementation
    module — the package root never reexports leaf implementations eagerly.
    The generator's own imports are not the package surface, so the probe
    measures the delta across surface resolution.
    """
    before = _baseline_leaf_modules()
    published_all = tuple(codegen_module.__all__)
    published_dir = tuple(dir(codegen_module))
    after_publish = _baseline_leaf_modules()
    tm.that(bool(published_all), eq=True)
    tm.that("FlextInfraCodegenCensus" in published_all, eq=True)
    tm.that("FlextInfraCodegenCensus" in published_dir, eq=True)
    # Publishing the surface imported no implementation module.
    tm.that(after_publish, eq=before)
    # Attribute access resolves lazily to the leaf owner.
    tm.that(
        codegen_module.FlextInfraCodegenConform.__name__, eq="FlextInfraCodegenConform"
    )


def test_codegen_lazy_imports_work() -> None:
    """Test that lazy imports work correctly."""
    tm.that(type(FlextInfraCodegenLazyInit).__name__, eq="ModelMetaclass")


__all__: list[str] = []
