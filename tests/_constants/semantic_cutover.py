"""Test-only constants for the semantic cutover J2 scenarios.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar


class TestsFlextInfraConstantsSemanticCutover:
    """Small scenario values rendered through the shared J2 templates."""

    SEMANTIC_CUTOVER_RELATIVE: ClassVar[str] = "tests/unit/test_sample.py"
    SEMANTIC_CUTOVER_PYPROJECT: ClassVar[str] = (
        "[project]\nname = 'demo'\nversion = '0.1.0'\n\n"
        "[tool.ruff]\nline-length = 88\n\n"
        '[tool.ruff.lint]\nselect = ["E501"]\n'
    )
    """Synthetic project carrying the fleet formatting width a rewrite must fit."""
    """Synthetic module path for semantic cutover behaviour tests."""

    SEMANTIC_CUTOVER_META_RELATIVE: ClassVar[str] = (
        "tests/_meta/test_import_machinery.py"
    )
    """Declared import-machinery path for the cutover exemption."""

    SEMANTIC_CUTOVER_TEMPLATE_DIRECTORY: ClassVar[str] = "semantic_cutover"
    """Fixture directory that owns the reusable J2 cutover templates."""

    SEMANTIC_CUTOVER_TEMPLATES: ClassVar[Mapping[str, str]] = MappingProxyType({
        "import_from": "import_from.j2",
        "import_plain": "import_plain.j2",
        "module": "module.j2",
        "assertions": "assertions.j2",
    })
    """Reusable J2 templates for semantic cutover scenarios."""

    SEMANTIC_IMPORT_SCENARIOS: ClassVar[Mapping[str, Mapping[str, str]]] = (
        MappingProxyType({
            "direct": {
                "template": "import_from",
                "module": "flext_core",
                "names": "FlextCore",
                "body": "value = FlextCore",
            },
            "deep": {
                "template": "import_from",
                "module": "flext_core.lazy",
                "names": "install_lazy_exports",
                "body": "value = install_lazy_exports",
            },
            "tests_submodule": {
                "template": "import_from",
                "module": "tests.constants",
                "names": "c",
                "body": "value = c",
            },
            "relative": {
                "template": "import_from",
                "module": ".",
                "names": "helper",
                "body": "value = helper",
            },
            "alias": {
                "template": "import_from",
                "module": "tests",
                "names": "c",
                "alias": "tc",
                "body": "value = tc.Tests.VALUE",
            },
            "plain": {
                "template": "import_plain",
                "module": "flext_core",
                "alias": "core_module",
                "body": "value = core_module.VALUE",
            },
            "merged": {
                "template": "module",
                "body": (
                    "from flext_core import FlextCore\n"
                    "from tests.constants import c\n"
                    "import pytest\n\n"
                    "value = (FlextCore, c, pytest)"
                ),
            },
            "meta": {
                "template": "import_from",
                "module": "flext_core",
                "names": "FlextCore",
                "body": "value = FlextCore",
            },
        })
    )
    """Small import-law parameters rendered through the shared templates."""

    SEMANTIC_ASSERT_SCENARIOS: ClassVar[Mapping[str, Mapping[str, str]]] = (
        MappingProxyType({
            "truth": {
                "template": "assertions",
                "assertions": "value",
            },
            "equality": {
                "template": "assertions",
                "header": "from tests import c",
                "assertions": "value == expected",
            },
            "inequality": {
                "template": "assertions",
                "assertions": "value != expected",
            },
            "none": {
                "template": "assertions",
                "assertions": "value is None\nother is not None",
            },
            "membership": {
                "template": "assertions",
                "assertions": "item in items\nother not in items",
            },
            "isinstance": {
                "template": "assertions",
                "assertions": ("isinstance(value, str)\nnot isinstance(other, int)"),
            },
            "negation": {
                "template": "assertions",
                "assertions": "not value",
            },
            "message": {
                "template": "assertions",
                "assertions": "value",
                "message": "message",
            },
            "untouched": {
                "template": "module",
                "body": "from tests import c\n\nvalue = c.Tests.VALUE",
            },
            "comprehension": {
                "template": "assertions",
                "assertions": (
                    'not [d for d in docs if d.get("kind") == "ServiceAccount"]\n'
                    '"x" in [d for d in docs if d]'
                ),
            },
            "hash_in_string": {
                "template": "assertions",
                "assertions": 'value == "a#b"',
            },
            "compound": {
                "template": "assertions",
                "assertions": (
                    "value == 1 and other == 2\n"
                    "not value == expected\n"
                    "low < value < high"
                ),
            },
            "multiline": {
                "template": "module",
                "body": (
                    "def test_probe() -> None:\n"
                    "    assert value == (\n"
                    "        expected\n"
                    "    )\n"
                    "    assert (\n"
                    "        item in items\n"
                    '    ), "message"\n'
                ),
            },
            "parenthesized_import": {
                "template": "module",
                "body": (
                    '"""Probe module."""\n'
                    "\n"
                    "from collections.abc import (\n"
                    "    Mapping,\n"
                    "    Sequence,\n"
                    ")\n"
                    "\n"
                    "\n"
                    "def test_probe() -> None:\n"
                    "    assert value\n"
                ),
            },
            "unformattable": {
                "template": "module",
                "body": (
                    "def test_probe() -> None:\n"
                    "    assert value == expected\n"
                    "    assert (\n"
                    '        "' + "word " * 15 + '"\n'
                    "        in text\n"
                    "    )\n"
                ),
            },
            "typed_locals": {
                "template": "module",
                "body": (
                    "def test_probe(payload: object) -> None:\n"
                    "    rendered = load()\n"
                    "    assert isinstance(rendered, dict)\n"
                    '    assert payload is not None, "payload"\n'
                    "    assert isinstance(shared, str)\n"
                    "\n"
                    "\n"
                    "class TestsProbe:\n"
                    "    def test_other(self) -> None:\n"
                    "        assert isinstance(rendered, dict)\n"
                ),
            },
            "object_message": {
                "template": "module",
                "body": (
                    "def test_probe(route: dict[str, str]) -> None:\n"
                    "    assert len(hosts) == 1, route\n"
                    '    assert value == expected, f"{value}"\n'
                ),
            },
            "comments": {
                "template": "module",
                "body": (
                    "def test_probe() -> None:\n"
                    "    assert value == expected  # why\n"
                    "    assert other == (\n"
                    "        expected  # inner\n"
                    "    )\n"
                ),
            },
        })
    )
    """Small assertion-law parameters rendered through the shared templates."""


__all__: list[str] = ["TestsFlextInfraConstantsSemanticCutover"]
