# AUTO-GENERATED FILE — Regenerate with: make gen
"""Lazy export registry."""

from __future__ import annotations

from flext_core.lazy import merge_lazy_imports
from flext_infra.tests.unit._constants._exports_lazy_part_01 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_01,
)
from flext_infra.tests.unit._constants._exports_lazy_part_02 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_02,
)
from flext_infra.tests.unit._constants._exports_lazy_part_03 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_03,
)
from flext_infra.tests.unit._constants._exports_lazy_part_04 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_04,
)
from flext_infra.tests.unit._constants._exports_lazy_part_05 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_05,
)
from flext_infra.tests.unit._constants._exports_lazy_part_06 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_06,
)
from flext_infra.tests.unit._constants._exports_lazy_part_07 import (
    TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_07,
)

_LOCAL_LAZY_IMPORTS = {
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_01,
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_02,
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_03,
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_04,
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_05,
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_06,
    **TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS_PART_07,
}

TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS = merge_lazy_imports(
    (
        "._constants",
        "._utilities",
        ".basemk",
        ".check",
        ".codegen",
        ".container",
        ".deps",
        ".discovery",
        ".docs",
        ".github",
        ".io",
        ".refactor",
        ".release",
        ".transformers",
        ".validate",
        ".workspace",
    ),
    _LOCAL_LAZY_IMPORTS,
    exclude_names=(
        "cleanup_submodule_namespace",
        "install_lazy_exports",
        "lazy_getattr",
        "logger",
        "merge_lazy_imports",
        "output",
        "output_reporting",
        "pytest_addoption",
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_configure",
        "pytest_runtest_setup",
        "pytest_runtest_teardown",
        "pytest_sessionfinish",
        "pytest_sessionstart",
        "pytest_terminal_summary",
        "pytest_warning_recorded",
    ),
    module_name="flext_infra.tests.unit",
)

__all__: list[str] = ["TESTS_FLEXT_INFRA_UNIT_LAZY_IMPORTS"]
