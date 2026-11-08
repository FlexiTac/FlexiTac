"""The default electrodes of before the user's decision of 2026-11-06, for the tests whose pinned numbers were measured with them.

"默认的pitch/trace大小,现在都是0.7,直接都改成0.5": the default fill (electrode width / pitch) was 0.7 until then, both
Gen by Surface's fit option ``fill`` (surface.fit.DEFAULT_OPTIONS) and the rectangular default's 1.4 mm electrodes at
its 2 mm pitch (engine.core.default_design); it is 0.5 (1.0 mm electrodes) since.  The tests of the defaults themselves
(test_golden_default, test_core, the API's, the identity guards' records, test_surface_web, test_library,
test_docs_consistency) build with today's.  The geometry, DRC, export and fit regressions of the modules that use this
pin numbers measured on requests that leave the electrodes to the default (the masked boards' polygon field windows
need the merged window of 1.4 mm electrodes at 2 mm, whose coverlay bridges are 0.4 mm; the fits' taxel counts of the
fixtures' faces were measured at fill 0.7), so they build with the electrodes of before, from their setUpModule:

    def setUpModule() -> None:
        defaults_of_before.start()

``start`` patches both defaults until the module's tests are done (unittest.addModuleCleanup; a subprocess of such a
test that builds as it does calls ``start(cleanup=False)`` first); ``electrodes`` and
``fill`` are the two patches as context managers, for one test.  A request that names its electrodes (or a fit that
names its fill) builds as it does without them.

The PI stiffener of before the user's later decision of 2026-11-06 ("订单厚度对不上... 建议把补强改成 0.1 mm... 要不要现在改？"
-> "好的"): 0.225 mm until then, 0.1 mm since (the profile revision 2026-11-06b: the 2-layer 0.2 mm FPC + 0.1 mm, the
0.3 mm gold fingers by JLC's rule).  Every board carries the profile's thickness twice, in ``fpc.stackup`` and in each
``layers.bottom_stiffener`` item; its outline, side and material are the same.  The digests of layouts pinned before
then (the straight channel's records of before, ``CHANNEL_LAYOUT_SHA256``) are taken of the boards with the 0.225 mm
put back (``stiffener``), after checking that they carry the profile's thickness.  The profile itself cannot be
patched back: on the 2-layer order the check refuses 0.225 mm (0.2 + 0.225 = 0.425 mm).
"""

from __future__ import annotations

import copy
import unittest
from typing import Any
from unittest import mock

import engine.core
from surface import fit

# The rectangular default's electrodes at its 2 mm pitch and Gen by Surface's default fill, until 2026-11-06.
ELECTRODE_MM = 1.4
FILL = 0.7
# The PI stiffener's thickness until the user's later decision of 2026-11-06.
STIFFENER_MM = 0.225


def electrodes() -> Any:
    """engine.core.default_design with the 1.4 mm electrodes of before (the normalizer's defaults: a request that leaves
    an electrode width to the default gets 1.4 mm)."""

    current = engine.core.default_design

    def before(template_id: str = engine.core.TEMPLATE_ID) -> dict:
        design = current(template_id)
        design["matrix"].update(taxel_width_mm=ELECTRODE_MM, taxel_height_mm=ELECTRODE_MM)
        return design

    return mock.patch.object(engine.core, "default_design", before)


def fill() -> Any:
    """surface.fit.DEFAULT_OPTIONS with the fill of before (a fit that names no fill fits at 0.7)."""

    return mock.patch.dict(fit.DEFAULT_OPTIONS, {"fill": FILL})


def start(cleanup: bool = True) -> None:
    """Both defaults of before for the calling module's tests (call it from setUpModule; ``cleanup`` False: for the rest
    of the process, as a subprocess of such a test that builds as it does)."""

    for patch in (electrodes(), fill()):
        patch.start()
        if cleanup:
            unittest.addModuleCleanup(patch.stop)


def stiffener(boards: Any, thickness: float) -> Any:
    """``boards`` (a result's boards by key) with the stiffener's thickness of before (STIFFENER_MM) put back where it
    is the profile's ``thickness``, in ``fpc.stackup`` and in every ``layers.bottom_stiffener`` item: a copy, for the
    digest of a layout pinned before 2026-11-06.  A board that carries another thickness raises ``ValueError``."""

    boards = copy.deepcopy(boards)
    for key, board in boards.items():
        stackup = board["fpc"]["stackup"]
        items = board["layers"]["bottom_stiffener"]
        if stackup["stiffener_thickness_mm"] != thickness or any(item["thickness_mm"] != thickness for item in items):
            raise ValueError(f"board {key} does not carry the profile's {thickness} mm stiffener")
        stackup["stiffener_thickness_mm"] = STIFFENER_MM
        for item in items:
            item["thickness_mm"] = STIFFENER_MM
    return boards
