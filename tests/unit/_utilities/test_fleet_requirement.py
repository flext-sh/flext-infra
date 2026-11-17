"""A fleet requirement carries its name, never a source URL.

The workspace elects the editable checkout and a standalone consumer takes the
locked git source. An embedded ``@ git+...`` makes uv see two URLs for the same
package and refuse the resolution, which stopped ``make upg``/``make gen``.
"""

from __future__ import annotations

from flext_infra import u


def test_a_fleet_git_requirement_becomes_the_plain_name() -> None:
    assert (
        u.Infra.fleet_requirement(
            "flext-cli @ git+https://github.com/flext-sh/flext-cli.git@0.12.0-dev"
        )
        == "flext-cli"
    )


def test_a_pinned_third_party_requirement_is_untouched() -> None:
    requirement = "rope @ git+https://github.com/marlon-costa-dc/rope.git@abc123"
    assert u.Infra.fleet_requirement(requirement) == requirement


def test_a_plain_or_versioned_requirement_is_untouched() -> None:
    assert u.Infra.fleet_requirement("flext-core") == "flext-core"
    assert u.Infra.fleet_requirement("pydantic>=2.14.1,<3") == "pydantic>=2.14.1,<3"
