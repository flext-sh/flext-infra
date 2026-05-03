"""Tests for flext_infra.__version__ — package info and module-level exports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import flext_infra as infra_pkg
from flext_infra.__version__ import FlextInfraVersion


class TestsFlextInfraInfraVersionExtra:
    """Test FlextInfraVersion.resolve_package_info() method."""

    def test_resolve_package_info_returns_mapping(self) -> None:
        """Test that resolve_package_info() returns a mapping."""
        result = FlextInfraVersion.resolve_package_info()
        assert isinstance(result, dict)

    def test_resolve_package_info_has_name_key(self) -> None:
        """Test that resolve_package_info() has 'name' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "name" in result

    def test_resolve_package_info_has_version_key(self) -> None:
        """Test that resolve_package_info() has 'version' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "version" in result

    def test_resolve_package_info_has_description_key(self) -> None:
        """Test that resolve_package_info() has 'description' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "description" in result

    def test_resolve_package_info_has_author_key(self) -> None:
        """Test that resolve_package_info() has 'author' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "author" in result

    def test_resolve_package_info_has_author_email_key(self) -> None:
        """Test that resolve_package_info() has 'author_email' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "author_email" in result

    def test_resolve_package_info_has_license_key(self) -> None:
        """Test that resolve_package_info() has 'license' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "license" in result

    def test_resolve_package_info_has_url_key(self) -> None:
        """Test that resolve_package_info() has 'url' key."""
        result = FlextInfraVersion.resolve_package_info()
        assert "url" in result

    def test_resolve_package_info_all_values_are_strings(self) -> None:
        """Test that resolve_package_info() values are strings."""
        result = FlextInfraVersion.resolve_package_info()
        for value in result.values():
            assert isinstance(value, str)

    def test_module_level_version_is_string(self) -> None:
        """Test that module-level __version__ is a string."""
        if "__version__" in infra_pkg.__dict__:
            del infra_pkg.__dict__["__version__"]
        version_value: str = infra_pkg.__version__
        assert isinstance(version_value, str)

    def test_module_level_version_info_is_tuple(self) -> None:
        """Test that module-level __version_info__ is a tuple."""
        assert isinstance(infra_pkg.__version_info__, tuple)

    def test_module_level_title_is_string(self) -> None:
        """Test that module-level __title__ is a string."""
        assert isinstance(infra_pkg.__title__, str)

    def test_module_level_description_is_string(self) -> None:
        """Test that module-level __description__ is a string."""
        assert isinstance(infra_pkg.__description__, str)

    def test_module_level_author_is_string(self) -> None:
        """Test that module-level __author__ is a string."""
        assert isinstance(infra_pkg.__author__, str)

    def test_module_level_author_email_is_string(self) -> None:
        """Test that module-level __author_email__ is a string."""
        assert isinstance(infra_pkg.__author_email__, str)

    def test_module_level_license_is_string(self) -> None:
        """Test that module-level __license__ is a string."""
        assert isinstance(infra_pkg.__license__, str)

    def test_module_level_url_is_string(self) -> None:
        """Test that module-level __url__ is a string."""
        assert isinstance(infra_pkg.__url__, str)

    def test_module_level_version_matches_class_version(self) -> None:
        """Test that module-level __version__ matches class version."""
        # Workaround: Python places the submodule in __dict__ when loaded,
        # shadowing the lazy string export. Force re-resolution.
        if "__version__" in infra_pkg.__dict__:
            del infra_pkg.__dict__["__version__"]
        version_value: str = infra_pkg.__version__
        assert version_value == FlextInfraVersion.__version__

    def test_module_level_version_info_matches_class_version_info(self) -> None:
        """Test that module-level __version_info__ matches class version_info."""
        assert infra_pkg.__version_info__ == FlextInfraVersion.__version_info__
