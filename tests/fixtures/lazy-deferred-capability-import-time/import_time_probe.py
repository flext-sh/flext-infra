"""Report whether importing the package read a stand-in at import time.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from importlib import import_module

from flext_core import lazy

package = import_module("flext_demo")
read = vars(sys.modules["flext_demo.__version__"])["FlextDemoCapabilityBase"]

print("__flext_lazy_target__" in vars(read))
print(package.__version__)
lazy.run_eager()
print("eager-ok")
