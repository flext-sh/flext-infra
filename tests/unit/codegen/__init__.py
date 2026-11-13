# AUTO-GENERATED FILE — Regenerate with: make gen
"""Tests.unit.codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from tests.unit.codegen.ci_matrix_support import (
        TestsFlextInfraCodegenCiMatrixSupport,
    )
    from tests.unit.codegen.layout_support import TestsFlextInfraCodegenLayoutSupport
    from tests.unit.codegen.lazy_init_test_namespace_tests import (
        TestsFlextInfraLazyInitTestNamespace,
    )
    from tests.unit.codegen.test_codegen_ci_matrix import TestsFlextInfraCodegenCiMatrix
    from tests.unit.codegen.test_codegen_ci_matrix_analysis import (
        TestsFlextInfraCodegenCiMatrixAnalysis,
    )
    from tests.unit.codegen.test_codegen_ci_matrix_artifacts import (
        TestsFlextInfraCodegenCiMatrixArtifacts,
    )
    from tests.unit.codegen.test_facade_foreign_publication import (
        TestsFlextInfraFacadeForeignPublication,
    )


__all__: tuple[str, ...] = (
    "TestsFlextInfraCodegenCiMatrix",
    "TestsFlextInfraCodegenCiMatrixAnalysis",
    "TestsFlextInfraCodegenCiMatrixArtifacts",
    "TestsFlextInfraCodegenCiMatrixSupport",
    "TestsFlextInfraCodegenLayoutSupport",
    "TestsFlextInfraFacadeForeignPublication",
    "TestsFlextInfraLazyInitTestNamespace",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "TestsFlextInfraCodegenCiMatrix": ".test_codegen_ci_matrix",
        "TestsFlextInfraCodegenCiMatrixAnalysis": ".test_codegen_ci_matrix_analysis",
        "TestsFlextInfraCodegenCiMatrixArtifacts": ".test_codegen_ci_matrix_artifacts",
        "TestsFlextInfraCodegenCiMatrixSupport": ".ci_matrix_support",
        "TestsFlextInfraCodegenLayoutSupport": ".layout_support",
        "TestsFlextInfraFacadeForeignPublication": ".test_facade_foreign_publication",
        "TestsFlextInfraLazyInitTestNamespace": ".lazy_init_test_namespace_tests",
    },
    public_exports=__all__,
)
