from flext_infra import (
    __version__,
)
from flext_infra.__version__ import FlextInfraVersion


def test_version_full_import() -> None:
    assert __version__ == FlextInfraVersion.__version__
