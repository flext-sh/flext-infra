from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from flext_infra import DetectorContext, FlextInfraImportAliasDetector
from tests import t, u


@pytest.fixture
def rope_project(tmp_path: Path) -> Iterator[t.Infra.RopeProject]:
    """Minimal rope project rooted at tmp_path."""
    project = u.Infra.init_rope_project(tmp_path, project_prefix="__never__")
    yield project
    project.close()


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_refactor_project(
    tmp_path: Path, *, package_name: str = "flext_demo"
) -> Path:
    project_root = tmp_path / "flext-demo"
    _write_file(project_root / "Makefile", "check:\n\t@true\n")
    _write_file(
        project_root / "pyproject.toml",
        '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
    )
    _write_file(
        project_root / "src" / package_name / "__init__.py",
        (
            "from __future__ import annotations\n\n"
            "_LAZY_IMPORTS: dict[str, tuple[str, str]] = {\n"
            '    "FlextDemoCodegenGeneration": (\n'
            '        "flext_demo.codegen.generation",\n'
            '        "FlextDemoCodegenGeneration",\n'
            "    ),\n"
            '    "c": ("flext_demo.constants", "c"),\n'
            '    "r": ("flext_core.result", "r"),\n'
            '    "s": ("flext_core.service", "s"),\n'
            '    "t": ("flext_demo.typings", "t"),\n'
            '    "u": ("flext_demo.utilities", "u"),\n'
            "}\n"
        ),
    )
    _write_file(
        project_root / "src" / package_name / "constants.py",
        (
            "from __future__ import annotations\n\n"
            "class FlextDemoConstants:\n"
            "    pass\n\n"
            "c = FlextDemoConstants\n"
        ),
    )
    _write_file(
        project_root / "src" / package_name / "typings.py",
        (
            "from __future__ import annotations\n\n"
            "class FlextDemoTypes:\n"
            "    pass\n\n"
            "t = FlextDemoTypes\n"
        ),
    )
    _write_file(
        project_root / "src" / package_name / "utilities.py",
        (
            "from __future__ import annotations\n\n"
            "class FlextDemoUtilities:\n"
            "    pass\n\n"
            "u = FlextDemoUtilities\n"
        ),
    )
    _write_file(
        project_root / "src" / package_name / "codegen" / "generation.py",
        (
            "from __future__ import annotations\n\n"
            "class FlextDemoCodegenGeneration:\n"
            "    pass\n"
        ),
    )
    return project_root


def test_import_alias_detector_skips_private_and_class_imports(
    tmp_path: Path,
    rope_project: t.Infra.RopeProject,
) -> None:
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "from __future__ import annotations\n"
        "from flext_core import FlextModelFoundation\n"
        "from flext_core import FlextModels\n"
        "from flext_core import m\n",
        encoding="utf-8",
    )

    violations = FlextInfraImportAliasDetector.detect_file(
        DetectorContext(
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
        "from flext_infra import FlextInfraNamespaceEnforcerModels\n"
        "from flext_core import m as mm\n",
        encoding="utf-8",
    )

    violations = FlextInfraImportAliasDetector.detect_file(
        DetectorContext(
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
        DetectorContext(
            file_path=sample_file,
            rope_project=rope_project,
        ),
    )
    assert violations == []


def test_namespace_rewriter_only_rewrites_runtime_alias_imports(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.py"
    source = (
        "from __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\n"
        "from flext_core import FlextModelFoundation\n"
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
    # Submodule import with short alias name removed; only future import remains.
    assert rewritten == "from __future__ import annotations\n"


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
        "from flext_core import c, m, r, t, u, p\n"
        "from flext_infra import FlextInfraNamespaceEnforcerModels\n"
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


def test_runtime_alias_migrator_merges_local_imports_in_src(tmp_path: Path) -> None:
    project_root = _build_refactor_project(tmp_path)
    target = project_root / "src" / "flext_demo" / "codegen" / "lazy_init.py"
    _write_file(
        target,
        (
            "from __future__ import annotations\n\n"
            "from flext_core import r, s\n"
            "from flext_demo import (\n"
            "    FlextDemoCodegenGeneration,\n"
            "    c,\n"
            "    t,\n"
            "    u,\n"
            ")\n"
        ),
    )

    results = u.Infra.migrate_runtime_alias_imports(
        workspace_root=tmp_path,
        aliases=["r", "s"],
        apply=True,
        project_names=["flext-demo"],
    )

    result = next(item for item in results if item.file_path == target)
    rewritten = target.read_text(encoding="utf-8")
    assert result.success is True
    assert result.modified is True
    assert "from flext_core import r, s" not in rewritten
    assert rewritten.count("from flext_demo import") == 1
    assert "FlextDemoCodegenGeneration" in rewritten
    assert "r," in rewritten
    assert "s," in rewritten


def test_runtime_alias_migrator_skips_unsafe_local_cycle(tmp_path: Path) -> None:
    project_root = _build_refactor_project(tmp_path)
    _write_file(
        project_root / "src" / "flext_demo" / "utilities.py",
        (
            "from __future__ import annotations\n\n"
            "from flext_demo._utilities.local import helper\n\n"
            "class FlextDemoUtilities:\n"
            "    pass\n\n"
            "u = FlextDemoUtilities\n"
        ),
    )
    target = project_root / "src" / "flext_demo" / "_utilities" / "local.py"
    source = (
        "from __future__ import annotations\n\n"
        "from flext_core import u\n\n"
        "def helper() -> str:\n"
        '    return "ok"\n'
    )
    _write_file(target, source)

    results = u.Infra.migrate_runtime_alias_imports(
        workspace_root=tmp_path,
        aliases=["u"],
        apply=False,
        project_names=["flext-demo"],
    )

    result = next(item for item in results if item.file_path == target)
    assert result.success is True
    assert result.modified is False
    assert "skipped unsafe runtime alias import: u" in result.changes
    assert target.read_text(encoding="utf-8") == source


def test_runtime_alias_migrator_merges_local_imports_in_tests(tmp_path: Path) -> None:
    project_root = _build_refactor_project(tmp_path)
    _write_file(
        project_root / "tests" / "__init__.py",
        (
            "from __future__ import annotations\n\n"
            "_LAZY_IMPORTS: dict[str, tuple[str, str]] = {\n"
            '    "r": ("flext_core.result", "r"),\n'
            '    "t": ("tests.typings", "t"),\n'
            '    "u": ("tests.utilities", "u"),\n'
            "}\n"
        ),
    )
    _write_file(
        project_root / "tests" / "typings.py",
        (
            "from __future__ import annotations\n\n"
            "class FlextTestsTypes:\n"
            "    pass\n\n"
            "t = FlextTestsTypes\n"
        ),
    )
    _write_file(
        project_root / "tests" / "utilities.py",
        (
            "from __future__ import annotations\n\n"
            "class FlextTestsUtilities:\n"
            "    pass\n\n"
            "u = FlextTestsUtilities\n"
        ),
    )
    target = project_root / "tests" / "unit" / "test_sample.py"
    _write_file(
        target,
        (
            "from __future__ import annotations\n\n"
            "from flext_core import r\n"
            "from tests import t, u\n"
        ),
    )

    results = u.Infra.migrate_runtime_alias_imports(
        workspace_root=tmp_path,
        aliases=["r"],
        apply=True,
        project_names=["flext-demo"],
    )

    result = next(item for item in results if item.file_path == target)
    rewritten = target.read_text(encoding="utf-8")
    assert result.success is True
    assert result.modified is True
    assert "from flext_core import r" not in rewritten
    assert rewritten.count("from tests import") == 1
    assert "r," in rewritten or "r\n" in rewritten
