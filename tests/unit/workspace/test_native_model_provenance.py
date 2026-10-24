"""Real model consumers of native source provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from inspect import getfile, isclass, isfunction, ismethod
from pathlib import Path

import pytest
from pydantic import RootModel
from ruamel.yaml import YAML
from typing_inspection.introspection import AnnotationSource, inspect_annotation


from flext_infra.docs import FlextInfraDocGenerator
from flext_infra.validate import FlextInfraValidateFreshImport
from tests import m, p, tm, u


class TestsFlextInfraNativeModelProvenance:
    """Conditional metaclasses and nested presets keep their real runtime contract."""

    @staticmethod
    def test_native_observation_defaults_preserve_mutable_evidence_contract() -> None:
        """Public contexts isolate defaults and validate incoming evidence records."""
        first = m.Infra.NativeObservationContext(paths=())
        second = m.Infra.NativeObservationContext(paths=())
        tm.that(first.evidence, eq=[])
        tm.that(first.evidence is not second.evidence, truth=True)

        record = m.Infra.NativeBindingEvidence(
            binding="builtins.len",
            kind="builtin",
            supplier="builtins",
            name="len",
            qualname="len",
        )
        first.evidence.append(record)
        tm.that(first.evidence, eq=[record])
        tm.that(second.evidence, eq=[])
        provided = m.Infra.NativeObservationContext(paths=(), evidence=[record])
        tm.that(provided.evidence, eq=[record])

        converted = m.Infra.NativeObservationContext.model_validate({
            "paths": (),
            "evidence": (),
        })
        converted.evidence.append(record)
        tm.that(converted.evidence, eq=[record])
        with pytest.raises(m.ValidationError, match="evidence"):
            m.Infra.NativeObservationContext.model_validate({
                "paths": (),
                "evidence": [{}],
            })

    @staticmethod
    def test_real_namespace_provider_retains_authenticated_native_sources() -> None:
        """An installed namespace is not duplicated by the cold import roots."""
        tm.that(tm.ok(u.Cli.yaml_parse("a: 1\n")), eq={"a": 1})
        tm.fail(u.Cli.yaml_parse("\0"))
        admission = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(Path.cwd(), entrypoint=YAML)
        )
        sources = tm.not_none(admission.generator_reference).sources
        expected_source = Path(getfile(YAML)).resolve()
        tm.that(
            any(Path(source).resolve() == expected_source for _, source, _ in sources),
            eq=True,
        )

    @staticmethod
    @pytest.mark.parametrize("mutation", ["none", "code", "source"])
    def test_parameterized_model_consumer_retains_authenticated_native_sources(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """A named source consumer keeps generic behavior and rejects tampering."""
        package = tmp_path / "parameterized_model_consumer"
        u.Tests.write_package_init(
            package,
            "from pydantic import RootModel\n"
            "def construct(value):\n"
            "    return RootModel[str].model_construct(value)\n",
        )
        metadata = tmp_path / "parameterized_model_consumer-1.0.dist-info"
        metadata.mkdir()
        for name, content in (
            (
                "METADATA",
                (
                    "Metadata-Version: 2.4\n"
                    "Name: parameterized-model-consumer\nVersion: 1.0\n"
                ),
            ),
            ("top_level.txt", "parameterized_model_consumer\n"),
            (
                "RECORD",
                (
                    f"{metadata.name}/METADATA,,\n"
                    f"{metadata.name}/top_level.txt,,\n"
                    f"{metadata.name}/RECORD,,\n"
                    "parameterized_model_consumer/__init__.py,,\n"
                ),
            ),
        ):
            tm.ok(u.Cli.atomic_write_text_file(metadata / name, content))
        native_consumer(
            """sys.path.insert(0, sys.argv[1])
from inspect import getfile
from pydantic import RootModel
module = importlib.import_module('parameterized_model_consumer')
value = module.construct('wire-value')
assert isinstance(value, RootModel[str])
assert value.model_dump() == 'wire-value'
source = Path(module.__file__)
mutation = sys.argv[2]
if mutation == 'code':
    module.construct.__code__ = module.construct.__code__.replace(co_name='foreign')
elif mutation == 'source':
    source.write_text(
        source.read_text(encoding='utf-8').replace('RootModel[str]', 'RootModel[int]'),
        encoding='utf-8')
admission = FlextInfraValidateFreshImport.capture_producer(
    runtime_root, entrypoint=module.construct)
if mutation == 'none':
    producer = admission.unwrap()
    reference = producer.generator_reference
    tm.not_none(reference)
    sources = {
        Path(origin).resolve() for _, origin, _ in reference.sources
    }
    assert source.resolve() in sources
    assert Path(getfile(RootModel)).resolve() in sources
    assert source.resolve() in {
        receipt.path.resolve() for receipt in reference.executed_sources
    }
else:
    assert admission.failure, admission
assert module.construct('wire-value').model_dump() == 'wire-value'
""",
            str(tmp_path),
            mutation,
        )

    @staticmethod
    @pytest.mark.parametrize("mutation", ["consumed", "unrelated"])
    def test_producer_authentication_retains_only_its_consumed_sources(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        mutation: str,
    ) -> None:
        """Reject changed executable input while preserving independent file work."""
        package = tmp_path / "source_provider"
        u.Tests.write_package_init(
            package,
            "from .helper import render\ndef operation():\n    return render()\n",
        )
        helper = package / "helper.py"
        helper.write_text("def render():\n    return 'original'\n", encoding="utf-8")
        unrelated = tmp_path / "tests" / "unconsumed.py"
        unrelated.parent.mkdir()
        unrelated.write_text("VALUE = 'original'\n", encoding="utf-8")
        metadata = tmp_path / "source_provider-1.0.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text(
            "Metadata-Version: 2.4\nName: source-provider\nVersion: 1.0\n",
            encoding="utf-8",
        )
        (metadata / "top_level.txt").write_text("source_provider\n", encoding="utf-8")
        (metadata / "RECORD").write_text(
            f"{metadata.name}/METADATA,,\n{metadata.name}/top_level.txt,,\n"
            f"{metadata.name}/RECORD,,\n"
            "source_provider/__init__.py,,\nsource_provider/helper.py,,\n",
            encoding="utf-8",
        )
        native_consumer(
            """sys.path.insert(0, sys.argv[1])
module = importlib.import_module('source_provider')
assert module.operation() == 'original'
admission = FlextInfraValidateFreshImport.capture_producer(
    runtime_root, entrypoint=module.operation).unwrap()
tm.not_none(admission.generator_reference)
sources = {
    Path(source).resolve()
    for _, source, _ in admission.generator_reference.sources
}
helper = Path(sys.argv[1]) / 'source_provider' / 'helper.py'
unrelated = Path(sys.argv[1]) / 'tests' / 'unconsumed.py'
assert helper.resolve() in sources
assert unrelated.resolve() not in sources
changed = helper if sys.argv[2] == 'consumed' else unrelated
replacement = "VALUE = 'independent change'\\n"
changed.write_text(replacement, encoding='utf-8')
assert module.operation() == 'original'
current = preconditions.producer_current(admission)
assert current.success == (sys.argv[2] == 'unrelated'), current.error
assert changed.read_text(encoding='utf-8') == replacement
""",
            str(tmp_path),
            mutation,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "entrypoint",
        [
            inspect_annotation,
            m.ContractModel.model_validate,
            u.Infra.docs_scope_artifacts,
            FlextInfraDocGenerator.plan_files,
            FlextInfraMiseArtifactsFiles.write_publication,
        ],
    )
    def test_real_model_module_retains_authenticated_native_sources(
        entrypoint: p.AttributeProbe,
    ) -> None:
        """Validate real model presets and generated annotation inspection payloads."""
        root = RootModel[str].model_validate("wire-value")
        tm.that(root.model_dump(), eq="wire-value")
        inspection = inspect_annotation(str, annotation_source=AnnotationSource.ANY)
        tm.that(inspection.type, eq=str)
        preset = m.ContractModel.model_validate({})
        tm.that(preset.model_dump(), eq={})
        if not (isclass(entrypoint) or isfunction(entrypoint) or ismethod(entrypoint)):
            pytest.fail("entrypoint is not a class, function or method")
        expected_source = Path(getfile(entrypoint)).resolve()
        admission = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(), entrypoint=entrypoint
            )
        )
        reference = tm.not_none(admission.generator_reference)
        sources = reference.sources
        tm.that(sources, empty=False)
        tm.that(
            any(Path(source).resolve() == expected_source for _, source, _ in sources),
            eq=True,
        )
