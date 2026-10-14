"""Exercise compiled YAML consumers through public source provenance.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import yaml

from flext_infra.workspace import FlextInfraWorkspaceEnvironmentProvenance
from tests import tm


class TestsFlextInfraNativeYamlProvenance:
    """Native extension exports retain their real supplier identity."""

    @staticmethod
    def test_compiled_yaml_roundtrip_retains_authenticated_sources() -> None:
        """Observe real Cython bindings after a compiled YAML round trip."""
        payload = "native-value"
        rendered = yaml.dump(payload, Dumper=yaml.CSafeDumper)
        tm.that(yaml.load(rendered, Loader=yaml.CSafeLoader), eq=payload)
        sources = FlextInfraWorkspaceEnvironmentProvenance.loaded_import_sources(
            yaml.__name__,
        ).unwrap()
        expected_source = Path(tm.not_none(yaml.__file__)).resolve()
        tm.that(
            any(Path(source).resolve() == expected_source for _, source, _ in sources),
            eq=True,
        )
