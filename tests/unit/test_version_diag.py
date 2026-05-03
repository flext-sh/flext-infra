import flext_infra as infra_pkg
from flext_infra.__version__ import FlextInfraVersion


def test_version_diag() -> None:
    if "__version__" in infra_pkg.__dict__:
        del infra_pkg.__dict__["__version__"]
    version_value: str = infra_pkg.__version__
    assert version_value == FlextInfraVersion.__version__
