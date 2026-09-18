"""Tests for Pydantic v1/v2 legacy detection in namespace validator."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra.validate.namespace_validator import FlextInfraNamespaceValidator
from tests import u


class TestsPydanticLegacyDetection:
    """Test suite for the namespace validator rule under test."""

    _FIXTURES_DIR = (
        Path(__file__).parent.parent.parent / "fixtures" / "namespace_validator"
    )

    def _read_fixture(self, name: str) -> str:

        fixture_name = name.replace(".py", ".pysrc") if name.endswith(".py") else name

        return (self._FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")

    def _make_project_with_module(
        self, tmp_path: Path, *, module_source: str, module_name: str
    ) -> Path:

        project_root = tmp_path / "project"

        package_dir = project_root / "src" / "flext_test"

        package_dir.mkdir(parents=True)

        _ = (package_dir / "__init__.py").write_text("", encoding="utf-8")

        u.Tests.write_canonical_package_layout(package_dir)

        _ = (package_dir / module_name).write_text(module_source, encoding="utf-8")

        u.Tests.initialize_git_repo(project_root)

        return project_root

    """Test suite for Pydantic legacy decorator/method detection."""

    @pytest.mark.parametrize(
        ("imports", "body", "legacy"),
        [
            (
                "from collections.abc import Callable\n",
                (
                    "    def execute(self, validator: Callable[[], None]) -> None:\n"
                    "        validator()\n"
                ),
                False,
            ),
            (
                (
                    "from collections.abc import Callable\n"
                    "from pydantic import validator\n"
                ),
                (
                    "    def execute(self, validator: Callable[[], None]) -> None:\n"
                    "        validator()\n"
                ),
                False,
            ),
            (
                (
                    "from collections.abc import Callable\n"
                    "from pydantic import root_validator as validate\n"
                ),
                (
                    "    def execute(self, validate: Callable[[], None]) -> None:\n"
                    "        validate()\n"
                ),
                False,
            ),
            (
                (
                    "from collections.abc import Callable\n"
                    "from pydantic import validator\n"
                ),
                (
                    "    def execute(self, callback: Callable[[], None]) -> None:\n"
                    "        validator = callback\n"
                    "        validator()\n"
                ),
                False,
            ),
            (
                "from pydantic import validator\n",
                (
                    "    def execute(self) -> None:\n"
                    "        def validator() -> None:\n"
                    "            pass\n"
                    "        validator()\n"
                ),
                False,
            ),
            (
                "from unrelated import validator\n",
                (
                    "    @validator('value')\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                False,
            ),
            (
                "import unrelated as pd\n",
                (
                    "    @pd.root_validator()\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                False,
            ),
            (
                "from pydantic import validator\n",
                (
                    "    @validator('value')\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                True,
            ),
            (
                "from pydantic import validator as validate_field\n",
                (
                    "    @validate_field('value')\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                True,
            ),
            (
                "from pydantic.v1 import root_validator as validate_root\n",
                (
                    "    @validate_root()\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                True,
            ),
            (
                "from pydantic import root_validator as validate_root\n",
                (
                    "    @validate_root\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                True,
            ),
            (
                "import pydantic as pd\n",
                (
                    "    @pd.validator('value')\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                True,
            ),
            (
                "import pydantic.v1 as pd\n",
                (
                    "    @pd.root_validator()\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                True,
            ),
            (
                "",
                (
                    "    def execute(self) -> None:\n"
                    "        from pydantic.v1 import validator as validate\n"
                    "        validate('value')\n"
                ),
                True,
            ),
            (
                "from pydantic import validator as validate\n",
                (
                    "    def execute(self) -> None:\n"
                    "        label = 'caf\u00e9'; validate('value')\n"
                ),
                True,
            ),
            (
                "from pydantic import field_validator as validator\n",
                (
                    "    @validator('value')\n"
                    "    def validate(cls, value: str) -> str:\n"
                    "        return value\n"
                ),
                False,
            ),
        ],
    )
    def test_pydantic_decorator_binding_provenance(
        self, tmp_path: Path, imports: str, body: str, *, legacy: bool
    ) -> None:
        root = self._make_project_with_module(
            tmp_path,
            module_source=(
                "from __future__ import annotations\n"
                + imports
                + "\nclass FlextTestValidation:\n"
                + body
            ),
            module_name="validation.py",
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(report.passed, eq=not legacy, msg=str(report.violations))
        tm.that(
            sum("legacy Pydantic member" in item for item in report.violations),
            eq=int(legacy),
        )

    @pytest.mark.parametrize(
        ("call", "legacy"),
        [
            ("response.json()", False),
            ("response.dict()", False),
            ("model.parse_obj({})", True),
            ("model.parse_raw(b'{}')", True),
        ],
    )
    def test_pydantic_method_detection_requires_unambiguous_member(
        self, tmp_path: Path, call: str, *, legacy: bool
    ) -> None:
        root = self._make_project_with_module(
            tmp_path,
            module_source=(
                "from __future__ import annotations\n\n"
                "class FlextTestClient:\n"
                "    def execute(self, response, model) -> None:\n"
                f"        {call}\n"
            ),
            module_name="client.py",
        )

        report = tm.ok(FlextInfraNamespaceValidator().validate_project(root))

        tm.that(
            sum("legacy Pydantic member" in item for item in report.violations),
            eq=int(legacy),
        )


__all__: list[str] = ["TestsPydanticLegacyDetection"]
