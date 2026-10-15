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

from flext_infra import infra, p, r
from flext_infra.codegen import (
    FlextInfraCodegenLazyInit,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenTransaction,
)
from flext_infra.codemod import FlextInfraCodemodSemanticApply, FlextInfraModGateEngine
from flext_infra.transformers import FlextInfraSemanticPublication
from tests import c, m, t, tm, u


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
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
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
            findings = u.Infra.declaration_relocation_findings(rope, proposed)
            tm.that(len(findings), eq=2)
            repeated = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=proposed,
                ),
            )
            tm.that(repeated, eq=())
        for path, source in proposed.items():
            path.write_text(source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.{consumer.stem} import Config; "
                        f"from {package.name}._models.config import ConfigPayload; "
                        f"from {package.name}._models.base import ModelsBase; "
                        "assert Config.payload is ConfigPayload; "
                        "assert issubclass(Config, ModelsBase)"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

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
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
            proposed = dict(sources)
            proposed.update({edit.file_path: edit.updated_source for edit in edits})
            tm.that(u.Infra.declaration_relocation_findings(rope, proposed), eq=())
        for path, source in proposed.items():
            path.write_text(source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.{consumer.stem} import Config; "
                        "print(Config(value='real-value').value)"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)
        tm.that(result.stdout.strip(), eq="real-value")

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
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources={consumer: source},
                ),
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
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
            tm.that(planned, eq=())
            findings = u.Infra.declaration_relocation_findings(rope, sources)
            tm.that(len(findings), eq=1)

    @staticmethod
    def _seed(
        tmp_path: Path,
        *,
        body: str = "value: str = Field(default='payload')",
        base: str = "PayloadBase",
        variants: frozenset[str] = frozenset(),
    ) -> t.Pair[Path, t.MutableMappingKV[Path, str]]:
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        stem = u.derive_class_stem(root.name)
        models = (
            package / u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
        )
        utilities = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        models.mkdir()
        utilities.mkdir()
        (models / "__init__.py").write_text("", encoding="utf-8")
        (utilities / "__init__.py").write_text("", encoding="utf-8")
        owner = f"{stem}ModelsPayload"
        source_owner = f"{stem}UtilitiesPayload"
        facade = f"{stem}Models"
        sources = {
            models / "payload.py": (
                '"""Authored payload family."""\nfrom __future__ import annotations\n'
                + (
                    "from pydantic import BaseModel as PayloadBase, Field\n"
                    if "existing_imports" in variants
                    else ""
                )
                + (
                    f"from {package.name}._utilities.payload import {source_owner}\n"
                    if "cycle" in variants
                    else ""
                )
                + f"class {owner}:\n    pass\n\n__all__ = ['{owner}']\n"
            ),
            package / "models.py": (
                f"from {package.name}._models.payload import {owner}\n"
                f"class {facade}"
                f"{'' if 'uncomposed' in variants else f'({owner})'}:\n"
                f"    pass\nm = {facade}\n"
                f"__all__ = ['{facade}', 'm']\n"
            ),
            utilities / "payload.py": (
                "from pydantic import BaseModel as PayloadBase, Field\n"
                "from pydantic_settings import BaseSettings\n"
                f"class {source_owner}:\n"
                f"    class Payload({base}):\n        {body}\n"
                f"\ndef local():\n    return {source_owner}.Payload()\n"
                + (
                    f"class {stem}StrayHolder:\n"
                    "    class Stray(PayloadBase):\n        value: str = 'stray'\n"
                    if "stray" in variants
                    else ""
                )
                + f"\n__all__ = ['{source_owner}']\n"
            ),
            package / "consumer.py": (
                "from __future__ import annotations\n"
                "from typing import Annotated, Literal\n"
                f"from {package.name}._utilities.payload "
                f"import {source_owner} as Original\n"
                "def build() -> 'Original.Payload':\n    return Original.Payload()\n"
                "text = 'Original.Payload'\n"
                "literal: Literal['Original.Payload']\n"
                "metadata: Annotated[str, 'Original.Payload']\n"
            ),
            package / "homonym.py": (
                "class Original:\n    class Payload:\n        pass\n"
                "value = Original.Payload()\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        if "uncomposed" not in variants:
            facade_path = package / c.Infra.MODELS_PY
            rendered = tm.not_none(
                u.Infra.render_utility_facade(package, family="m"),
            )
            sources[facade_path] = rendered
            facade_path.write_text(rendered, encoding="utf-8")
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        return root, sources

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
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
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
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
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
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            variants=frozenset({"cycle"}),
        )
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match="runtime import cycle"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_proposed_sources_not_disk_own_the_identity_snapshot(
        tmp_path: Path,
    ) -> None:
        """Test proposed sources not disk own the identity snapshot."""
        root, disk = TestsFlextInfraDeclarationRelocation._seed(tmp_path)
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
        root, sources = TestsFlextInfraDeclarationRelocation._seed(tmp_path)
        consumer = next(path for path in sources if path.name == "consumer.py")
        sources[consumer] = sources[consumer].replace("def build()", "def build(m)")
        consumer.write_text(sources[consumer], encoding="utf-8")
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match="shadowed quoted type destination"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_quoted_field_dependency_is_transferred(tmp_path: Path) -> None:
        """Test quoted field dependency is transferred.

        Raises:
            RuntimeError: If Published decimal payload has no loader.

        """
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
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
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            target = next(
                edit
                for edit in planned.value
                if edit.file_path.parent.name
                == u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
            )
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
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
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

    @staticmethod
    @pytest.mark.parametrize("guard", ["TYPE_CHECKING", "Checking"])
    def test_unrelated_type_checking_guard_refuses_without_mutation(
        tmp_path: Path,
        guard: str,
    ) -> None:
        """A same-spelled local flag is not the typing module's guard identity."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            body="amount: 'Amount'",
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        sources[origin] = (
            f"{guard} = False\nif {guard}:\n"
            "    from decimal import Decimal as Amount\n" + sources[origin]
        )
        origin.write_text(sources[origin], encoding="utf-8")
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=r"unresolved/outer dependency.*Amount"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("refused", ["destination", "exposure"])
    @pytest.mark.parametrize("independent_group", [False, True])
    def test_failed_dependent_group_preserves_independent_public_runtime(
        tmp_path: Path,
        refused: str,
        *,
        independent_group: bool,
    ) -> None:
        """A destination refusal recovers only its invocation's dependent group."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            body="count: int = Field(default=3)",
        )
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        target = next(path for path in sources if path.parent.name == "_models")
        package = target.parent.parent
        blocked = target if refused == "destination" else target.parent / "__init__.py"
        if refused == "exposure":
            blocked.write_text("", encoding="utf-8")
            sources[blocked] = ""
        independent = root / "independent.py"
        independent.write_text("VALUE = 'before'\n", encoding="utf-8")
        independent_before = tm.ok(
            u.Cli.atomic_read_binary_file_state(independent, required=True)
        )
        plans = [
            m.Infra.CodegenFilePlan(
                project=root,
                path=independent,
                before=independent_before,
                desired_content=b"VALUE = 'after'\n",
                desired_mode=independent_before.mode,
                dependency_group=independent.stem if independent_group else None,
            )
        ]
        for edit in edits:
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(edit.file_path, required=True)
            )
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=edit.file_path,
                    before=before,
                    desired_content=edit.updated_source.encode("utf-8"),
                    desired_mode=before.mode,
                    dependency_group=package.name,
                )
            )
        if refused == "exposure":
            exposure = tm.ok(
                FlextInfraCodegenLazyInit(repository_root=root).plan_files()
            )
            plans.extend(
                item.model_copy(update={"dependency_group": package.name})
                for item in exposure.files
                if item.path == blocked
            )
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root)
        )
        receipts: list[m.Infra.CodegenStagedFile] = []

        def refuse_destination(
            session: m.Infra.CodegenTransactionSession,
            _staged: t.VariadicTuple[m.Infra.CodegenStagedFile],
        ) -> p.Result[m.Infra.CodegenTransactionSession]:
            before = tm.ok(u.Cli.atomic_read_binary_file_state(blocked, required=True))
            tm.ok(
                u.Cli.atomic_write_binary_file_guarded(
                    before,
                    sources[blocked].encode("utf-8")
                    + b"\n# authored destination change\n",
                    permission_mode=before.mode,
                )
            )
            return r[m.Infra.CodegenTransactionSession].ok(session)

        def publish(scope: Path) -> p.Result[t.VariadicTuple[Path]]:
            started = transaction.begin_files_locked(scope, {f"@{root.name}": root}, ())
            if started.failure:
                return r[t.VariadicTuple[Path]].from_failure(started)
            admitted = transaction.append_phase_locked(
                started.value,
                c.Infra.CodegenStagedFilePhase.SEMANTIC,
                tuple(plans),
                staged_validator=refuse_destination,
            )
            if admitted.failure:
                return r[t.VariadicTuple[Path]].from_failure(admitted)
            return transaction.commit_locked(admitted.value, published_files=receipts)

        failed = transaction.run_files_locked({f"@{root.name}": root}, publish)
        tm.fail(failed)
        tm.that(independent.read_text(encoding="utf-8"), eq="VALUE = 'after'\n")
        tm.that(
            blocked.read_text(encoding="utf-8"),
            eq=sources[blocked] + "\n# authored destination change\n",
        )
        for path, source in sources.items():
            if path != blocked:
                tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(tuple(item.before.path for item in receipts), eq=(independent,))
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        f"from {package.name}.consumer import build; "
                        f"from {package.name} import m; "
                        "from independent import VALUE; "
                        "assert not hasattr(m, 'Payload'); "
                        "assert build().count == 3; assert VALUE == 'after'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent) + ":" + str(root)}
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize("accepted", [False, True])
    def test_public_group_cutover_is_accepted_or_recovers_on_consumer_rejection(
        tmp_path: Path,
        *,
        accepted: bool,
    ) -> None:
        """A fresh consumer accepts the full cutover, never a partial runtime."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            body="count: int = Field(default=3)",
        )
        before_sources = {path: path.read_bytes() for path in root.rglob("*.py")}
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        target = next(path for path in sources if path.parent.name == "_models")
        package = target.parent.parent
        plans: list[m.Infra.SemanticFilePlan] = []
        for edit in edits:
            before = tm.ok(
                u.Cli.atomic_read_binary_file_state(edit.file_path, required=True)
            )
            source = edit.updated_source
            if not accepted and edit.file_path == target:
                source = source.replace("Field(default=3)", "Field(default=7)")
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=root,
                    path=edit.file_path,
                    before=before,
                    desired_content=source.encode("utf-8"),
                    desired_mode=before.mode,
                    changes=("declaration relocation",),
                )
            )

        def consume() -> p.Result[bool]:
            result = u.Cli.run(
                (
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        f"from {package.name} import m; "
                        f"from {package.name}.consumer import build; "
                        "assert build().__class__ is m.Payload; "
                        "assert build().count == 3; "
                        "assert m.Payload.model_validate({'count': 4}).model_dump() == "
                        "{'count': 4}"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
            if result.failure:
                return r[bool].from_failure(result)
            return r[bool].ok(u.Cli.process_succeeded(result.value.outcome))

        result = FlextInfraSemanticPublication.publish_semantic_file_plans(
            plans,
            repository_root=root,
            projection_roots=(root,),
            dependency_group=package.name,
            validator=consume,
        )
        if accepted:
            tm.ok(result)
            tm.that(tm.ok(consume()), eq=True)
            with infra.rope_workspace(root) as rope:
                tm.that(
                    tm.ok(
                        u.Infra.plan_semantic_cutover(
                            c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                            rope_workspace=rope,
                            sources={
                                path: path.read_text(encoding="utf-8")
                                for path in sources
                            },
                        )
                    ),
                    eq=(),
                )
        else:
            tm.fail(result)
            for path, content in before_sources.items():
                tm.that(path.read_bytes(), eq=content)
            original = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-B",
                        "-c",
                        (
                            f"from {package.name}.consumer import build; "
                            "assert build().count == 3"
                        ),
                    ),
                    cwd=root,
                    options=m.Cli.ProcessOptions(
                        env={"PYTHONPATH": str(package.parent)}
                    ),
                )
            )
            tm.that(u.Cli.process_succeeded(original.outcome), eq=True)

    @staticmethod
    def test_real_scan_selects_the_immutable_declaration_phase(tmp_path: Path) -> None:
        """Test real scan selects the immutable declaration phase."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(tmp_path)
        preflight = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        phase = c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
        rule_id = c.Infra.SEMANTIC_CUTOVER_RULE_IDS[phase]
        tm.that(
            any(finding.rule_id == rule_id for finding in preflight.entries),
            eq=True,
        )
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources=sources,
                findings=preflight.entries,
            )
            tm.ok(planned)
            tm.that(len(planned.value), eq=3)
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("nested_local", [False, True])
    def test_validator_and_computed_field_runtime_preserved(
        tmp_path: Path,
        *,
        nested_local: bool,
    ) -> None:
        """Test validator and computed field runtime preserved.

        Raises:
            RuntimeError: If Published validator has no loader.

        """
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            body=(
                "value: int = 1\n"
                "        @field_validator('value')\n"
                "        @classmethod\n"
                "        def normalize(cls, value: int) -> int:\n"
                + (
                    "            scratch = [item * 2 for item in (value,)]\n"
                    "            return scratch[0]\n"
                    if nested_local
                    else "            return value * 2\n"
                )
                + "        @computed_field\n"
                "        @property\n"
                "        def derived(self) -> int:\n"
                "            return self.value + 1"
            ),
        )
        origin = next(
            path
            for path in sources
            if path.parent.name
            == u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        sources[origin] = (
            "from pydantic import field_validator, computed_field\n" + sources[origin]
        )
        origin.write_text(sources[origin], encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            target = next(
                edit
                for edit in planned.value
                if edit.file_path.parent.name
                == u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).directory
            )
        published = tmp_path / "published_validator.py"
        published.write_text(target.updated_source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("published_validator", published)
        if spec is None or spec.loader is None:
            msg = "Published validator has no loader"
            raise RuntimeError(msg)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        owner = f"{u.derive_class_stem(root.name)}ModelsPayload"
        tm.that(
            getattr(loaded, owner).Payload.model_validate({"value": 3}).model_dump(),
            eq={"value": 6, "derived": 7},
        )

    @staticmethod
    def test_generated_sources_refuse_the_whole_plan(tmp_path: Path) -> None:
        """Test unsafe sources refuse the whole plan."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(tmp_path)
        path = next(path for path in sources if path.name == "consumer.py")
        sources[path] = c.Infra.AUTOGEN_HEADERS[0] + "\n" + sources[path]
        expected = "generated consumer"
        path.write_text(sources[path], encoding="utf-8")
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=expected),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_unresolved_source_owner_is_a_finding_not_a_crash(
        tmp_path: Path,
    ) -> None:
        """An unexpected outer owner is reported while resolvable moves apply."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            variants=frozenset({"stray"}),
        )
        stem = u.derive_class_stem(root.name)
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            findings = u.Infra.declaration_relocation_findings(rope, sources)
        tm.ok(planned)
        tm.that(len(planned.value), eq=3)
        unresolved = tuple(
            finding
            for finding in findings
            if finding.declaration == f"{stem}StrayHolder.Stray"
        )
        tm.that(len(unresolved), eq=1)
        tm.that(unresolved[0].expected_owner, eq=f"{stem}UtilitiesPayload")
        tm.that(bool(unresolved[0].reason), eq=True)
        tm.that(
            all(
                finding.file_path in sources and finding.reason for finding in findings
            ),
            eq=True,
        )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.slow
    def test_uncomposed_model_owner_preserves_findings_and_failed_publication(
        tmp_path: Path,
    ) -> None:
        """An unresolved owner stays visible; failed candidate gates publish nothing."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(
            tmp_path,
            variants=frozenset({"uncomposed"}),
        )
        stem = u.derive_class_stem(root.name)
        origin = next(
            path
            for path in sources
            if path.parent.name
            == u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        tm.that(sources[origin], lacks="from __future__ import annotations")
        preflight = FlextInfraModGateEngine.authored(
            FlextInfraModGateEngine.scan(root, fix=False).unwrap(),
        )
        tm.that(
            any(
                finding.rule_id == "require-future-annotations"
                for finding in preflight.entries
            ),
            eq=True,
        )
        with infra.rope_workspace(root) as rope:
            findings = FlextInfraCodemodSemanticApply.relocation_findings(
                root,
                preflight,
                rope,
            )
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            tm.that(planned.value, empty=True)
            applied = FlextInfraCodemodSemanticApply.apply(
                root,
                preflight,
                rope,
                source_preview=infra.source_preview(root),
                workspace_factory=infra.rope_workspace,
            )
        tm.that(len(findings), eq=1)
        tm.that(findings[0].file_path, eq=origin.resolve())
        tm.that(findings[0].declaration, eq=f"{stem}UtilitiesPayload.Payload")
        tm.that(findings[0].expected_owner, has="one authored model owner")
        tm.that(findings[0].reason, has="found []")
        tm.fail(applied)
        tm.that(applied.error, has="quality checks failed")
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("split", [False, True])
    def test_public_preset_dependency_moves_without_self_facade_cycle(
        tmp_path: Path,
        *,
        split: bool,
    ) -> None:
        """The public model consumer loads the relocated payload and its preset."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(tmp_path)
        stem = u.derive_class_stem(root.name)
        target = next(path for path in sources if path.parent.name == "_models")
        owner = f"{stem}ModelsPayload"
        sources[target] = (
            "from pydantic import BaseModel, Field\n"
            f"class {owner}:\n    Field = Field\n"
            "    class Preset(BaseModel):\n        pass\n"
            f"__all__ = ['{owner}']\n"
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        sources[origin] = f"from {target.parent.parent.name} import m\n" + sources[
            origin
        ].replace("class Payload(PayloadBase)", "class Payload(m.Preset)").replace(
            "Field(default=", "m.Field(default="
        )
        sources[origin] = sources[origin].replace(
            "\ndef local():",
            "\n    @staticmethod\n    def consume(value: Payload) -> str:\n"
            "        return value.value\n\ndef local():",
        )
        if split:
            parts = origin.parent / "_payload_parts"
            parts.mkdir()
            (parts / "__init__.py").write_text("", encoding="utf-8")
            sources[parts / "payload_part.py"] = sources.pop(origin)
            sources[origin] = (
                f"from {target.parent.parent.name}._utilities."
                "_payload_parts.payload_part "
                f"import {stem}UtilitiesPayload\n"
                f"__all__ = ['{stem}UtilitiesPayload']\n"
            )
            sources[target.parent.parent / "utilities.py"] = (
                f"from {target.parent.parent.name}._utilities.payload "
                f"import {stem}UtilitiesPayload\n"
                f"class {stem}Utilities({stem}UtilitiesPayload):\n    pass\n"
                f"u = {stem}Utilities\n__all__ = ['u', '{stem}Utilities']\n"
            )
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        tm.that(u.Tests.run_lazy_init(root), eq=0)
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
        for edit in planned:
            edit.file_path.write_text(edit.updated_source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {target.parent.parent.name} import m; "
                        f"from {target.parent.parent.name}._utilities.payload "
                        f"import {stem}UtilitiesPayload; "
                        "from typing import get_type_hints; "
                        f"assert get_type_hints({stem}UtilitiesPayload.consume)"
                        "['value'] is m.Payload; "
                        "assert issubclass(m.Payload, m.Preset); "
                        "assert m.Payload.model_validate("
                        "{'value': 'consumer'}).value == 'consumer'"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(target.parent.parent.parent)}
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True)

    @staticmethod
    @pytest.mark.parametrize("competing", [False, True])
    def test_composed_preset_identity_resolves_local_model_owner(
        tmp_path: Path,
        *,
        competing: bool,
    ) -> None:
        """Unrelated composition parts do not compete with the preset owner."""
        root, sources = TestsFlextInfraDeclarationRelocation._seed(tmp_path)
        stem = u.derive_class_stem(root.name)
        target = next(path for path in sources if path.parent.name == "_models")
        owner = f"{stem}ModelsPayload"
        sources[target] = (
            "from pydantic import BaseModel\n"
            f"class {owner}:\n    class Preset(BaseModel):\n        pass\n"
            f"__all__ = ['{owner}']\n"
        )
        origin = next(path for path in sources if path.parent.name == "_utilities")
        sources[origin] = (
            f"from {target.parent.parent.name}._models.payload import {owner}\n"
            + sources[origin].replace(
                "class Payload(PayloadBase)", f"class Payload({owner}.Preset)"
            )
        )
        other = target.with_name("other.py")
        other_owner = f"{stem}ModelsOther"
        sources[other] = (
            f"from {target.parent.parent.name}._models.payload import {owner}\n"
            f"class {other_owner}{f'({owner})' if competing else ''}:\n    pass\n"
            f"__all__ = ['{other_owner}']\n"
        )
        facade = target.parent.parent / "models.py"
        sources[facade] = (
            f"from {target.parent.parent.name}._models.other import {other_owner}\n"
            + sources[facade].replace(f"({owner})", f"({owner}, {other_owner})")
        )
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            findings = u.Infra.declaration_relocation_findings(rope, sources)
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
        payload_findings = tuple(
            finding
            for finding in findings
            if finding.declaration == f"{stem}UtilitiesPayload.Payload"
        )
        tm.that(bool(payload_findings), eq=competing)
        tm.that(
            all(
                finding.file_path in sources and finding.reason for finding in findings
            ),
            eq=True,
        )
        tm.that(bool(planned), eq=not competing)
        if competing:
            return
        proposed = dict(sources)
        proposed.update({edit.file_path: edit.updated_source for edit in planned})
        for path, source in proposed.items():
            path.write_text(source, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {target.parent.parent.name} import m; "
                        "from pydantic import ValidationError; "
                        "assert m.Payload.model_validate({'value': 'consumer'}).value "
                        "== 'consumer'\n"
                        "try:\n    m.Payload.model_validate({'value': []})\n"
                        "except ValidationError:\n    print('rejected')\n"
                        "else:\n    raise AssertionError('invalid payload accepted')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(target.parent.parent.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="rejected")
