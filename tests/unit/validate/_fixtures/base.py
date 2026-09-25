"""Base test class for namespace validator tests.

Provides common setup, validator instantiation, and shared test infrastructure
to eliminate duplication across rule-specific test files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests import t
