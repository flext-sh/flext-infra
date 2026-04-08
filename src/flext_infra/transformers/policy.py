"""Compatibility module for transformer policy.

Canonical exports live in ``flext_infra._utilities.transformer_policy`` and on the
``flext_infra`` root package. This module remains importable, but it does not
re-export the policy class to avoid duplicate root exports during ``gen-init``.
"""

from __future__ import annotations

__all__: list[str] = []
