# from flext-infra_docs/guides/using-flext-tests.md:81
from flext_core import FlextContainer, FlextSettings
from flext_tests import FlextTestsSettings

FlextSettings.reset_for_testing()
FlextTestsSettings.reset_for_testing()
FlextContainer.reset_for_testing()
