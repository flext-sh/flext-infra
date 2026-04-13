from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraImportAliasDetector
from tests import m, t, u


def test_import_alias_detector_skips_private_and_class_imports(
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core import FlextModelsBase\n"
        "from flext_core import FlextModels\n"
        "from flext_core import m\n",
        encoding="utf-8",
    )

    violations = FlextInfraImportAliasDetector.detect_file(
        m.Infra.DetectorContext(
            file_path=sample_file,
            rope_project=rope_project,
        ),
    )
    assert violations == []


def test_import_alias_detector_skips_nested_private_and_as_renames(
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_infra import FlextInfraModelsNamespaceEnforcer\n"
        "from flext_core import m as mm\n",
        encoding="utf-8",
    )

    violations = FlextInfraImportAliasDetector.detect_file(
        m.Infra.DetectorContext(
            file_path=sample_file,
            rope_project=rope_project,
        ),
    )
    assert violations == []


def test_import_alias_detector_skips_facade_and_subclass_files(
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    sample_file = tmp_path / "models.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core import u\n"
        "from flext_core import FlextModels\n\n"
        "class FlextFooModels(FlextModels):\n"
        "    pass\n",
        encoding="utf-8",
    )

    violations = FlextInfraImportAliasDetector.detect_file(
        m.Infra.DetectorContext(
            file_path=sample_file,
            rope_project=rope_project,
        ),
    )
    assert violations == []


def test_namespace_rewriter_only_rewrites_runtime_alias_imports(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        "from flext_core import FlextModelsBase\n"
        "from flext_core import FlextModels\n"
        "from flext_core import m\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    # Top-level package imports (from flext_core import X) are preserved by the
    # cleaner — only submodule imports (from flext_core.<sub> import X) are removed.
    assert rewritten == source


def test_namespace_rewriter_keeps_contextual_alias_subset(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    source = "from __future__ import annotations\nfrom flext_core import u\n"
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    # Top-level package imports are preserved by the cleaner.
    assert rewritten == source


def test_namespace_rewriter_skips_facade_and_subclass_files(tmp_path: Path) -> None:
    sample_file = tmp_path / "models.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core import u\n"
        "from flext_core import FlextModels\n\n"
        "class FlextFooModels(FlextModels):\n"
        "    pass\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    # Top-level package imports are preserved (not submodule), so file is unchanged.
    assert "from flext_core import u" in rewritten
    assert "FlextModels" in rewritten
    assert rewritten == source


def test_namespace_rewriter_skips_nested_private_as_rename_and_duplicates(
    tmp_path: Path,
) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n"
        "from flext_core import c, m, r, p, t, u, p\n"
        "from flext_infra import FlextInfraModelsNamespaceEnforcer\n"
        "from flext_core import m as mm\n"
        "from flext_core import (m)\n"
    )
    sample_file.write_text(source, encoding="utf-8")

    u.Infra.rewrite_import_violations(
        py_files=[sample_file],
        project_package="flext_core",
    )

    rewritten = sample_file.read_text(encoding="utf-8")
    # Top-level package imports are not touched by the submodule cleaner.
    # flext_infra import also preserved (different package than project_package).
    assert rewritten == source
