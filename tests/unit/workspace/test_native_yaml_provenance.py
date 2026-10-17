"""Exercise compiled YAML consumers through public source provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from inspect import getfile
from pathlib import Path

import yaml

from flext_infra.validate import FlextInfraValidateFreshImport
from tests import tm


class TestsFlextInfraNativeYamlProvenance:
    """Native extension exports retain their real supplier identity."""

    @staticmethod
    def test_compiled_yaml_roundtrip_retains_authenticated_sources() -> None:
        """Observe real Cython bindings after a compiled YAML round trip."""
        payload = "native-value"
        rendered = yaml.dump(payload, Dumper=yaml.CSafeDumper)
        tm.that(yaml.load(rendered, Loader=yaml.CSafeLoader), eq=payload)
        admission = tm.ok(
            FlextInfraValidateFreshImport.capture_producer(
                Path.cwd(), entrypoint=yaml.CSafeDumper
            )
        )
        sources = tm.not_none(admission.generator_reference).sources
        expected_source = Path(getfile(yaml.CSafeDumper)).resolve()
        tm.that(
            any(Path(source).resolve() == expected_source for _, source, _ in sources),
            eq=True,
        )
