"""Fixture models for the green facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from pydantic import BaseModel


class FixtureModels:
    """Represents the fixture models."""

    class Entry(BaseModel):
        """Represents an entry in the fixture models."""

        label: str


m = FixtureModels

__all__ = ["FixtureModels", "m"]
