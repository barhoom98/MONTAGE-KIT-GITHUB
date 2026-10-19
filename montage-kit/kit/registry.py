"""يجمع كل الدفعات في قوائم موحدة.
NEW  = عناصر الدفعة 2 (⭐)    NEW3 = عناصر الدفعة 3 (🔥)
"""
from .effects import FX
from .sfx import SFX
from .luts import LUTS
from .overlays import OVERLAYS

KEYS = ("fx", "sfx", "luts", "overlays", "transitions")
NEW = {k: set() for k in KEYS}
NEW3 = {k: set() for k in KEYS}


def _merge(target, extra, key, mark):
    target.update(extra)
    mark[key].update(extra)


try:
    from .effects2 import FX2
    _merge(FX, FX2, "fx", NEW)
except ImportError:
    pass
try:
    from .sfx2 import SFX2
    _merge(SFX, SFX2, "sfx", NEW)
except ImportError:
    pass
try:
    from .luts2 import LUTS2
    _merge(LUTS, LUTS2, "luts", NEW)
except ImportError:
    pass
try:
    from .overlays2 import OVERLAYS2
    _merge(OVERLAYS, OVERLAYS2, "overlays", NEW)
except ImportError:
    pass
try:
    from .transitions import TRANS, BASIC
    NEW["transitions"].update(set(TRANS) - BASIC)
except ImportError:
    TRANS, BASIC = {}, set()

# ---- الدفعة 3 ----
try:
    from .effects3 import FX3
    _merge(FX, FX3, "fx", NEW3)
except ImportError:
    pass
try:
    from .sfx3 import SFX3
    _merge(SFX, SFX3, "sfx", NEW3)
except ImportError:
    pass
try:
    from .luts3 import LUTS3
    _merge(LUTS, LUTS3, "luts", NEW3)
except ImportError:
    pass
try:
    from .overlays3 import OVERLAYS3
    _merge(OVERLAYS, OVERLAYS3, "overlays", NEW3)
except ImportError:
    pass
try:
    from .transitions3 import TRANS3
    _merge(TRANS, TRANS3, "transitions", NEW3)
except ImportError:
    pass


def badge(key, name):
    if name in NEW3[key]:
        return " 🔥"
    if name in NEW[key]:
        return " ⭐"
    return ""
