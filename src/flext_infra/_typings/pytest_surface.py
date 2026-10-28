"""pytest and pytest-markdown-docs types, declared once for the whole fleet.

flext-infra ships the runner's pytest plugin, so pytest and its Markdown SDK
are libraries of its facade families. ``t.Infra.Pytest`` is the single owner:
flext-tests inherits it under ``t.Tests`` and adds only test-tier extras.
Annotation-only types are PEP 695 aliases; classes checked or constructed at
runtime stay fields bound to the class itself.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

import pytest
from pytest_markdown_docs.definitions import FenceTestDefinition
from pytest_markdown_docs.plugin import (
    FenceSyntax,
    MarkdownInlinePythonItem,
    MarkdownTextFile,
)

if TYPE_CHECKING:
    import xdist.workermanage


class FlextInfraTypesPytest:
    """pytest types published under ``t.Infra.Pytest``."""

    class Pytest:
        """pytest and Markdown SDK types; flext-tests inherits them."""

        type CaptureFixture[AnyStrT: (str, bytes)] = pytest.CaptureFixture[AnyStrT]
        type Collector = pytest.Collector
        type Config = pytest.Config
        type FenceDefinition = FenceTestDefinition
        type FixtureRequest = pytest.FixtureRequest
        type Item = pytest.Item
        type LogCaptureFixture = pytest.LogCaptureFixture
        type MarkdownItem = MarkdownInlinePythonItem
        type Metafunc = pytest.Metafunc
        type MonkeyPatch = pytest.MonkeyPatch
        type Parser = pytest.Parser
        type PytestPluginManager = pytest.PytestPluginManager
        type Pytester = pytest.Pytester
        type RunResult = pytest.RunResult
        type Session = pytest.Session
        type TempPathFactory = pytest.TempPathFactory
        type TestReport = pytest.TestReport
        type WorkerController = xdist.workermanage.WorkerController
        FenceSyntax = FenceSyntax
        MarkdownInlinePythonItem = MarkdownInlinePythonItem
        MarkdownTextFile = MarkdownTextFile
        StashKey = pytest.StashKey
        failed = pytest.fail.Exception


__all__: list[str] = ["FlextInfraTypesPytest"]
