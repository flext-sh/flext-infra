"""Public immutable nested payload relocation contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import flext_tests
import pytest

from flext_infra import infra
from tests import c, m, tm, u
from tests.unit.codemod.declaration_relocation_support import (
    TestsFlextInfraDeclarationRelocationSupport,
)


class TestsFlextInfraDeclarationRelocation:
    """Exercise real Rope bindings and preserve the original source inventory."""

    @staticmethod
    @pytest.mark.parametrize("lazy", [False, True])
    @pytest.mark.parametrize("consumer_name", ["_config.py", "_settings.py"])
    def test_settings_imports_do_not_promote_family_payload_to_layer_zero(
        tmp_path: Path,
        consumer_name: str,
        *,
        lazy: bool,
    ) -> None:
        """Family payloads retain their finding, never gaining a leaf-import bypass."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / "_models"
        family.mkdir()
        consumer = package / consumer_name
        owner = family / "config.py"
        base = family / "base.py"
        sources = {
            owner: "class ConfigPayload:\n    pass\n",
            base: "class ModelsBase:\n    pass\n",
            family / "__init__.py": (
                "from flext_core.lazy import install_lazy_exports\n"
                "install_lazy_exports(__name__, globals(), {\n"
                "    'ConfigPayload': '.config', 'ModelsBase': '.base',\n"
                "})\n"
                if lazy
                else f"from {package.name}._models.config import ConfigPayload\n"
                f"from {package.name}._models.base import ModelsBase\n"
            ),
            consumer: (
                f"from {package.name}._models import ("
                "ConfigPayload as Payload, ModelsBase)\n"
                "class Config(ModelsBase):\n    payload = Payload\n"
            ),
        }
        TestsFlextInfraDeclarationRelocationSupport.write(sources)
        planned = tm.ok(TestsFlextInfraDeclarationRelocationSupport.plan(root, sources))
        tm.that(planned, eq=())
        proposed = dict(sources)
        proposed.update({edit.file_path: edit.updated_source for edit in planned})
        tm.that(consumer.read_text(encoding="utf-8"), eq=sources[consumer])
        tm.that(
            proposed[consumer],
            lacks="._models.config import ConfigPayload as Payload",
        )
        tm.that(proposed[consumer], has="._models import ConfigPayload as Payload")
        tm.that(proposed[consumer], has="._models.base import ModelsBase")
        tm.that(
            len(TestsFlextInfraDeclarationRelocationSupport.findings(root, proposed)),
            eq=2,
        )
        repeated = tm.ok(
            TestsFlextInfraDeclarationRelocationSupport.plan(root, proposed)
        )
        tm.that(repeated, eq=())
        TestsFlextInfraDeclarationRelocationSupport.write(proposed)
        u.Tests.run_lazy_init_probe(
            f"from {package.name}.{consumer.stem} import Config; "
            f"from {package.name}._models.config import ConfigPayload; "
            f"from {package.name}._models.base import ModelsBase; "
            "assert Config.payload is ConfigPayload; "
            "assert issubclass(Config, ModelsBase)",
            python_paths=(str(package.parent),),
            cwd=root,
        )

    @staticmethod
    def test_own_reexport_rebinds_to_its_real_external_provider(
        tmp_path: Path,
    ) -> None:
        """Rope proves the external identity before changing a declaration import."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / "_models"
        family.mkdir()
        consumer = package / "_config.py"
        sources = {
            family / "__init__.py": "from flext_core import m\n__all__ = ['m']\n",
            consumer: (
                f"from {package.name}._models import m\n"
                "class Config(m.BaseModel):\n    value: str\n"
            ),
        }
        TestsFlextInfraDeclarationRelocationSupport.write(sources)
        edits = tm.ok(TestsFlextInfraDeclarationRelocationSupport.plan(root, sources))
        proposed = dict(sources)
        proposed.update({edit.file_path: edit.updated_source for edit in edits})
        tm.that(
            TestsFlextInfraDeclarationRelocationSupport.findings(root, proposed), eq=()
        )
        TestsFlextInfraDeclarationRelocationSupport.write(proposed)
        lines = u.Tests.run_lazy_init_probe(
            f"from {package.name}.{consumer.stem} import Config; "
            "print(Config(value='real-value').value)",
            python_paths=(str(package.parent),),
            cwd=root,
        )
        tm.that(lines, eq=["real-value"])

    @staticmethod
    def test_settings_imports_preserve_external_lazy_package(
        tmp_path: Path,
    ) -> None:
        """Resolve the actual external provider without treating it as local WIP."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = Path(flext_tests.__file__).resolve()
        tm.that(provider.is_relative_to(root), eq=False)
        consumer = package / "_settings.py"
        source = "from flext_tests import tm\nclass Settings:\n    matcher = tm\n"
        consumer.write_text(source, encoding="utf-8")
        planned = tm.ok(
            TestsFlextInfraDeclarationRelocationSupport.plan(root, {consumer: source})
        )
        tm.that(planned, eq=())
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_settings_imports_do_not_evade_illegal_declaration_owners(
        tmp_path: Path,
    ) -> None:
        """A non-config model leaf remains a finding, never a direct-import bypass."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = package / "_models"
        family.mkdir()
        sources = {
            family / "payload.py": "class Payload:\n    pass\n",
            family / "__init__.py": (
                f"from {package.name}._models.payload import Payload\n"
            ),
            package / "_config.py": (
                f"from {package.name}._models import Payload\n"
                "class Config:\n    payload = Payload\n"
            ),
        }
        TestsFlextInfraDeclarationRelocationSupport.write(sources)
        planned = tm.ok(TestsFlextInfraDeclarationRelocationSupport.plan(root, sources))
        tm.that(planned, eq=())
        findings = TestsFlextInfraDeclarationRelocationSupport.findings(root, sources)
        tm.that(len(findings), eq=1)

    @staticmethod
    @pytest.mark.parametrize("existing_imports", [False, True])
    def test_move_preserves_payloads_and_is_immutable_idempotent(
        tmp_path: Path,
        *,
        existing_imports: bool,
    ) -> None:
        """Test move preserves payloads and is immutable idempotent.

        Raises:
            RuntimeError: If Published payload module has no loader.

        """
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            variants=frozenset({"existing_imports"} if existing_imports else ()),
        )
        with infra.rope_workspace(root) as rope:
            origin = next(
                path
                for path in sources
                if path.parent.name
                == u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
            )
            binding = u.Infra.payload_declaration(
                rope.rope_project,
                origin,
                f"{u.derive_class_stem(root.name)}UtilitiesPayload.Payload",
            )
            tm.that(binding, none=False)
            tm.that(u.Infra.declaration_relocation_findings(rope, sources), eq=())
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            tm.that(len(planned.value), eq=3)
            proposed = dict(sources)
            proposed.update({
                edit.file_path: edit.updated_source for edit in planned.value
            })
            remaining = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=proposed,
            )
            tm.ok(remaining)
            tm.that(remaining.value, empty=True)
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
        target = next(
            path
            for path in sources
            if path.parent.name
            == u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
        )
        published = tmp_path / "published_payload.py"
        published.write_text(proposed[target], encoding="utf-8")
        spec = importlib.util.spec_from_file_location("published_payload", published)
        if spec is None or spec.loader is None:
            msg = "Published payload module has no loader"
            raise RuntimeError(msg)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        owner = f"{u.derive_class_stem(root.name)}ModelsPayload"
        payload = getattr(loaded, owner).Payload
        tm.that(
            payload.model_validate({"value": "consumer"}).model_dump(),
            eq={"value": "consumer"},
        )
        tm.that(payload.model_validate({}).model_dump(), eq={"value": "payload"})
        for path, source in proposed.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "from typing import get_args, get_type_hints; "
                        f"from {target.parent.parent.name} import m; "
                        f"from {target.parent.parent.name} import consumer; "
                        "assert consumer.build().__class__ is m.Payload; "
                        "assert get_type_hints(consumer.build)['return'] is m.Payload; "
                        "assert consumer.text == 'Original.Payload'; "
                        "hints = get_type_hints(consumer, include_extras=True); "
                        "assert get_args(hints['literal']) == ('Original.Payload',); "
                        "assert get_args(hints['metadata']) == (str, "
                        "'Original.Payload')"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(target.parent.parent.parent)}
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("body", "base"),
        [
            (
                (
                    "value: str = 'data'\n        def run(self):\n"
                    "            return self.value"
                ),
                "PayloadBase",
            ),
            ("value: str = 'data'", "BaseSettings"),
        ],
    )
    def test_behavior_and_settings_are_not_payload_movers(
        tmp_path: Path,
        body: str,
        base: str,
    ) -> None:
        """Test behavior and settings are not payload movers."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body=body,
            base=base,
        )
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        tm.ok(planned)
        tm.that(planned.value, empty=True)

    @staticmethod
    def test_cycle_refuses_without_mutation(tmp_path: Path) -> None:
        """Test cycle refuses without mutation."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            variants=frozenset({"cycle"}),
        )
        TestsFlextInfraDeclarationRelocationSupport.refuses(
            root, sources, "runtime import cycle"
        )

    @staticmethod
    def test_proposed_sources_not_disk_own_the_identity_snapshot(
        tmp_path: Path,
    ) -> None:
        """Test proposed sources not disk own the identity snapshot."""
        root, disk = TestsFlextInfraDeclarationRelocationSupport.seed(tmp_path)
        sources = {
            path: source.replace("class Payload(", "class Revised(").replace(
                ".Payload",
                ".Revised",
            )
            for path, source in disk.items()
            if path.name != "homonym.py"
        }
        sources.update({
            path: source for path, source in disk.items() if path.name == "homonym.py"
        })
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(result)
            tm.that(len(result.value), eq=3)
            sources.update({
                edit.file_path: edit.updated_source for edit in result.value
            })
            repeated = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(repeated)
            tm.that(repeated.value, empty=True)
        for path, source in disk.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_local_destination_capture_refuses_without_mutation(tmp_path: Path) -> None:
        """Test local destination capture refuses without mutation."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(tmp_path)
        consumer = next(path for path in sources if path.name == "consumer.py")
        sources[consumer] = sources[consumer].replace("def build()", "def build(m)")
        consumer.write_text(sources[consumer], encoding="utf-8")
        TestsFlextInfraDeclarationRelocationSupport.refuses(
            root, sources, "shadowed quoted type destination"
        )

    @staticmethod
    def test_quoted_field_dependency_is_transferred(tmp_path: Path) -> None:
        """Test quoted field dependency is transferred.

        Raises:
            RuntimeError: If Published decimal payload has no loader.

        """
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body="amount: 'Decimal'",
        )
        origin = next(
            path
            for path in sources
            if path.parent.name
            == u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        sources[origin] = "from decimal import Decimal\n" + sources[origin]
        origin.write_text(sources[origin], encoding="utf-8")
        target = TestsFlextInfraDeclarationRelocationSupport.models_edit(root, sources)
        published = tmp_path / "published_decimal.py"
        published.write_text(target.updated_source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("published_decimal", published)
        if spec is None or spec.loader is None:
            msg = "Published decimal payload has no loader"
            raise RuntimeError(msg)
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loaded
        try:
            spec.loader.exec_module(loaded)
            owner = f"{u.derive_class_stem(root.name)}ModelsPayload"
            payload = getattr(loaded, owner).Payload
            tm.that(
                payload.model_validate({"amount": "2.5"}).model_dump_json(),
                eq='{"amount":"2.5"}',
            )
        finally:
            del sys.modules[spec.name]

    @staticmethod
    @pytest.mark.parametrize(
        ("dependency", "annotation", "shadow"),
        [
            ("from decimal import Decimal as Amount", "Amount", "Amount"),
            ("import decimal as amounts", "amounts.Decimal", "amounts"),
        ],
    )
    @pytest.mark.parametrize("conflict", [False, True])
    def test_guarded_dependency_public_consumer(
        tmp_path: Path,
        dependency: str,
        annotation: str,
        shadow: str,
        *,
        conflict: bool,
    ) -> None:
        """Guarded aliases resolve at the model owner without capturing local names."""
        root, sources = TestsFlextInfraDeclarationRelocationSupport.seed(
            tmp_path,
            body=f"amount: '{annotation}'",
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        target = next(path for path in sources if path.parent.name == "_models")
        sources[origin] = (
            "from typing import TYPE_CHECKING as Checking\n"
            f"if Checking:\n    {dependency}\n"
            + sources[origin]
            + f"\ndef shadow({shadow}: str) -> str:\n    return {shadow}\n"
        )
        if conflict:
            sources[target] = f"{shadow} = str\n" + sources[target]
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            if conflict:
                with pytest.raises(ValueError, match="conflicting dependency"):
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=sources,
                    )
                planned = ()
            else:
                planned = tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=sources,
                    ),
                )
                proposed = dict(sources)
                proposed.update({
                    edit.file_path: edit.updated_source for edit in planned
                })
                tm.that(
                    tm.ok(
                        u.Infra.plan_semantic_cutover(
                            c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                            rope_workspace=rope,
                            sources=proposed,
                        ),
                    ),
                    eq=(),
                )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
        if conflict:
            return
        for edit in planned:
            edit.file_path.write_text(edit.updated_source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {target.parent.parent.name} import m; "
                        f"from {target.parent.parent.name}.consumer import build; "
                        f"from {target.parent.parent.name}._utilities.payload import "
                        f"shadow; "
                        "from decimal import Decimal; "
                        "from typing import get_type_hints; "
                        "assert get_type_hints(build)['return'] is m.Payload; "
                        "assert m.Payload.model_fields['amount'].annotation is "
                        "Decimal; "
                        "assert m.Payload.model_validate({'amount': '2.5'}).amount "
                        "== Decimal('2.5'); "
                        "assert "
                        "m.Payload.model_validate({'amount': '2.5'}).model_dump_json() "
                        '== \'{"amount":"2.5"}\'; '
                        "assert shadow('lexical') == 'lexical'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(target.parent.parent.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)
