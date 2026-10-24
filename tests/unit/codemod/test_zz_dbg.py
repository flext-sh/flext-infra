from pathlib import Path

from rope.base import builtins as rb
from flext_infra import infra
from tests import c, u


def test_dbg(tmp_path: Path) -> None:
    root, package = u.Tests.create_lazy_init_workspace(tmp_path)
    with infra.rope_workspace(root) as ws:
        proj = ws.rope_project
        mod = proj.get_module("builtins")
        print("MOD", type(mod), mod)
        s = mod["str"].get_object()
        print("STR", type(s), s, "same as rope builtins:", s is rb.builtins["str"].get_object())
        print("EXT", "builtins" in proj.prefs.get("extension_modules", []), type(proj).__mro__[:3])
    raise AssertionError
