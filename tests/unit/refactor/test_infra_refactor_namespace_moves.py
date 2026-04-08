from __future__ import annotations

from pathlib import Path

from tests import m, u


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_project(tmp_path: Path) -> tuple[Path, Path]:
    project_root = tmp_path / "flext-demo"
    package_root = project_root / "src" / "demo_pkg"
    _write_file(
        project_root / "pyproject.toml",
        '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
    )
    _write_file(project_root / "Makefile", "check:\n\t@true\n")
    _write_file(package_root / "__init__.py", "from __future__ import annotations\n")
    return (project_root, package_root)


def test_rewrite_manual_protocol_violations_uses_public_runtime_api(
    tmp_path: Path,
) -> None:
    project_root, package_root = _build_project(tmp_path)
    protocols_file = package_root / "protocols.py"
    source_file = package_root / "service.py"
    consumer_file = package_root / "consumer.py"
    _write_file(
        protocols_file,
        "from __future__ import annotations\n\nclass ExistingProtocol:\n    pass\n",
    )
    _write_file(
        source_file,
        (
            "from __future__ import annotations\n\n"
            "from typing import Protocol\n\n"
            "class External(Protocol):\n"
            "    def call(self) -> str:\n"
            "        ...\n"
        ),
    )
    _write_file(
        consumer_file,
        (
            "from __future__ import annotations\n\n"
            "from demo_pkg.service import External\n\n"
            "def use(dep: External) -> External:\n"
            "    return dep\n"
        ),
    )

    u.Infra.rewrite_manual_protocol_violations(
        project_root=project_root,
        py_files=[source_file, consumer_file],
        violations=[
            m.Infra.ManualProtocolViolation(
                file=str(source_file),
                line=5,
                name="External",
            )
        ],
    )

    assert "class External(Protocol):" not in source_file.read_text(encoding="utf-8")
    assert "from demo_pkg.protocols import External" in consumer_file.read_text(
        encoding="utf-8",
    )
    protocols_text = protocols_file.read_text(encoding="utf-8")
    assert "from typing import Protocol" in protocols_text
    assert "class External(Protocol):" in protocols_text
    assert source_file.with_suffix(".py.bak").exists()
    assert consumer_file.with_suffix(".py.bak").exists()
    assert protocols_file.with_suffix(".py.bak").exists()


def test_rewrite_manual_typing_alias_violations_uses_public_runtime_api(
    tmp_path: Path,
) -> None:
    project_root, package_root = _build_project(tmp_path)
    typings_file = package_root / "typings.py"
    source_file = package_root / "service.py"
    _write_file(
        typings_file,
        "from __future__ import annotations\n\nTYPE_READY = True\n",
    )
    _write_file(
        source_file,
        (
            "from __future__ import annotations\n\n"
            "from collections.abc import Mapping\n"
            "from typing import TypeAlias\n\n"
            "PayloadMap: TypeAlias = Mapping[str, str]\n"
            "value = 1\n"
        ),
    )

    u.Infra.rewrite_manual_typing_alias_violations(
        project_root=project_root,
        violations=[
            m.Infra.ManualTypingAliasViolation(
                file=str(source_file),
                line=6,
                name="PayloadMap",
            )
        ],
        parse_failures=[],
    )

    source_text = source_file.read_text(encoding="utf-8")
    typings_text = typings_file.read_text(encoding="utf-8")
    assert "PayloadMap: TypeAlias = Mapping[str, str]" not in source_text
    assert "PayloadMap: TypeAlias = Mapping[str, str]" in typings_text
    assert "from collections.abc import Mapping" in typings_text
    assert "from typing import TypeAlias" in typings_text
    assert source_file.with_suffix(".py.bak").exists()
    assert typings_file.with_suffix(".py.bak").exists()


def test_rewrite_compatibility_alias_violations_uses_public_runtime_api(
    tmp_path: Path,
) -> None:
    _, package_root = _build_project(tmp_path)
    source_file = package_root / "models.py"
    _write_file(
        source_file,
        (
            "from __future__ import annotations\n\n"
            "class NewThing:\n"
            "    pass\n\n"
            "LegacyThing = NewThing\n"
            "REGISTRY = [LegacyThing]\n"
        ),
    )

    u.Infra.rewrite_compatibility_alias_violations(
        violations=[
            m.Infra.CompatibilityAliasViolation(
                file=str(source_file),
                line=6,
                alias_name="LegacyThing",
                target_name="NewThing",
            )
        ],
        parse_failures=[],
    )

    source_text = source_file.read_text(encoding="utf-8")
    assert "LegacyThing = NewThing" not in source_text
    assert "REGISTRY = [NewThing]" in source_text
    assert source_file.with_suffix(".py.bak").exists()
