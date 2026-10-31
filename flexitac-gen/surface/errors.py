"""Issue codes of CAD mode (the surface pipeline).

They live outside ``engine/`` on purpose: the engine's issue catalogue covers
the board design (``tactile-fpc-design/v1``), and CAD mode only chooses and
places such a design.  Every code here is raised as :class:`SurfaceError` or
reported in a proposal's ``rejected`` list with its message.
"""

from __future__ import annotations

import math
from typing import Any

SURFACE_ERROR_CODES: dict[str, str] = {
    "E_SURFACE_MESH_EMPTY": "The file holds no triangle.",
    "E_SURFACE_MESH_FORMAT": "The file is neither a binary STL (84 + 50 n bytes) nor an ASCII STL ('solid ... endsolid').",
    "E_SURFACE_MESH_TRUNCATED": "The binary STL announces more triangles than the file holds.",
    "E_SURFACE_MESH_NONFINITE": "A coordinate is NaN, infinite or more than 1e9 mm from the origin (after the unit scale).",
    "E_SURFACE_MESH_TOO_LARGE": "The mesh has more triangles or bytes than are accepted.",
    "E_SURFACE_UNIT": "The unit is not one of m, cm, mm or in.",
    "E_SURFACE_REQUEST": "The surface request is malformed (a missing or invalid field).",
    "E_SURFACE_FACET": "A facet id is outside the mesh, degenerate or hidden inside the part.",
    "E_SURFACE_SELECTION_EMPTY": "The selection holds no usable facet.",
    "E_SURFACE_NOT_DISK": "The selected surface is not one piece without holes; it cannot be flattened into one chart.",
    "E_SURFACE_NOT_DEVELOPABLE": "The selected surface cannot be flattened within the strain limit.",
    "E_SURFACE_BASE_EDGE": "The base (tail exit) edge is not on the selection's outer boundary.",
    "E_SURFACE_NO_FIT": "No sensor design fits the selected surface with the given settings.",
    "E_SURFACE_PLACEMENT_MISMATCH": "The design differs from the design the placement was made for.",
    "E_SURFACE_BORDER": "The border is not a simple polygon of at least 3 vertices and 1 mm2 on the surface, or its exit edge is invalid.",
}


class SurfaceError(ValueError):
    """A CAD-mode input or geometry problem with a stable code."""

    def __init__(self, code: str, message: str = "", **details: Any) -> None:
        if code not in SURFACE_ERROR_CODES:
            raise KeyError(f"unknown surface code {code!r}")
        self.code = code
        self.message = message or SURFACE_ERROR_CODES[code]
        self.details = details
        super().__init__(f"{code}: {self.message}")

    def as_issue(self) -> dict[str, Any]:
        issue: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            issue["details"] = self.details
        return issue


def finite_number(value: Any, where: str, low: float = -math.inf, high: float = math.inf, code: str = "E_SURFACE_REQUEST") -> float:
    """A JSON number within ``low..high`` as a float; anything else is a SurfaceError, never a crash.

    Booleans are not numbers, and an integer too large for a float (JSON
    allows any number of digits) is refused like an infinite one.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SurfaceError(code, f"{where} must be a number.")
    try:
        number = float(value)
    except OverflowError:
        number = math.inf
    if not math.isfinite(number):
        raise SurfaceError(code, f"{where} must be a finite number.")
    if not low <= number <= high:
        raise SurfaceError(code, f"{where} must be a number within {low:g}..{high:g}.")
    return number

