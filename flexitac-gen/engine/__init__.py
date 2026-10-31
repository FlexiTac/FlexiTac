"""Deterministic, dependency-free tactile FPC geometry core.

The public API is a small boundary for the web app, the CLI and agents:
``default_design()``, ``check_design(data)`` (normalization, input rules and
feasibility, no geometry), ``generate_design(data)`` and ``result_view``,
plus the machine-readable contract ``design_schema()``, ``input_limits()``,
``issue_codes()`` and the strict request parser ``load_design_json``, and
``field_footprint(design, profile)``, the board material around the taxel
field from the plans (for fitting a sensor to a surface).  A design's
``template_id`` picks its locked profile (``generic_matrix_v1``, the
default, or ``surface_matrix_v1``); a design built as the diagonal Row bus
takes the surface profile on either template (``rules_template``).  A surface design's field mask
(``matrix.mask``) has its frames and construction classes in
``design_mask``, ``column_spans``, ``row_frame_spans``,
``column_frame_spans``, ``row_taper`` and ``mask_class``.  On either
template ``routing.row_sides`` (``left``, ``right``, ``both``) builds the
diagonal Row bus (``ROW_BUS_VERSION``, :mod:`engine.diagonal`; the generic
template's default) and ``channel`` the straight Row channel.
Geometry is derived from the normalized design and the locked manufacturing
profile in this package; it never reads an existing EDA project or Gerber at
runtime.
"""

from .core import (
    GENERATOR_VERSION,
    MASK_VERSION,
    ROW_BUS_VERSION,
    REQUEST_WARNING_CODES,
    SCHEMA_VERSION,
    BuildCache,
    check_design,
    default_design,
    generate_design,
    load_profile,
    result_view,
    rules_template,
    validate_design,
)
from .layout import column_frame_spans, column_spans, design_mask, field_footprint, mask_class, row_frame_spans, row_taper
from .schema import DesignJSONError, design_schema, input_limits, issue_codes, load_design_json

__all__ = [
    "GENERATOR_VERSION",
    "MASK_VERSION",
    "REQUEST_WARNING_CODES",
    "ROW_BUS_VERSION",
    "SCHEMA_VERSION",
    "BuildCache",
    "DesignJSONError",
    "check_design",
    "column_frame_spans",
    "column_spans",
    "default_design",
    "design_mask",
    "design_schema",
    "field_footprint",
    "generate_design",
    "input_limits",
    "issue_codes",
    "load_design_json",
    "load_profile",
    "mask_class",
    "result_view",
    "row_frame_spans",
    "row_taper",
    "rules_template",
    "validate_design",
]
