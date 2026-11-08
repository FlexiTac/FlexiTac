# EasyEDA Pro projects (`.epro2`)

`exporters/easyeda_pro.py` writes each board of a build as a native EasyEDA
Pro (JLCEDA Pro) project, so the user can import it into EasyEDA Pro (the
web editor at pro.easyeda.com, nothing to install, or the desktop app),
check it there and order from there.  EasyEDA then writes the Gerbers
itself; nothing here writes a Gerber or presents ours as EasyEDA's.  The
Direct Gerber archives ([PHASE2_DIRECT_GERBER.md](PHASE2_DIRECT_GERBER.md))
are unchanged.

## The archive

`build_easyeda_exports(result, *, cache=None)` returns
`{"easyeda_pro_zip": bytes}`; `easyeda_filenames(result)` names it
`{build_id}-easyeda-pro.zip` and gives the member of each board's project.
The HTTP route is `POST /api/export/easyeda-pro`; the web UI's button
"EasyEDA Pro projects ZIP" sits with the other downloads, in Rectangular
and CAD mode alike.

| Member | Content |
| --- | --- |
| `easyeda_pro/{build_id}-top-{role}.epro2` | the board on the top of the stack, one PCB |
| `easyeda_pro/{build_id}-bottom-{role}.epro2` | the board on the bottom of the stack, one PCB |
| `easyeda_pro/README_EASYEDA.txt` | the steps in EasyEDA Pro, each board's nets, pads, tracks, openings and stiffeners, and the profile's JLCPCB order options |
| `easyeda_pro/manifest.json` | `tactile-fpc-easyeda-export/v1`: the exporter, the build identity, per board the file, its SHA-256, its document UUIDs, its counts and layers and the read-back |

The projects are a separate archive, not new members of the project
review ZIP: adding members would change that ZIP's bytes and every digest
pinned on it (the default build, the masked and diagonal builds), and the
review bundle is the audit record of the Direct Gerber export.  A separate
archive and route keep every existing pin.

## A project

An `.epro2` is a ZIP of `IMAGE/`, `project2.json` and one `.epru` log
(EasyEDA Pro file format V3).  Each log line is `head||body`, two JSON
objects; lines are joined by `|` and a newline, as in the user's own JLCEDA
exports (`fpc_design/source/original_jlceda/`).  A document starts with a
`DOCHEAD`; the log holds, in this order, two FOOTPRINT documents (the
electrodes and the contacts), BOARD, SCH, SCH_PAGE, two DEVICE documents
and the PCB.  The library documents are local to the archive: EasyEDA Pro
drops free PCB pads and pads whose component has no schematic channel (the
lessons of the earlier source-independent writer, `fpc_design/easyeda/`),
so each footprint has a DEVICE, a component on the schematic page (its
`Unique ID`) and a PCB `COMPONENT` naming it (`Channel ID` `$1e<n>`), and
`PAD_NET` records give each pad its net.

## Mapping

| Our layer (`boards.*.layers`) | EasyEDA record | Layer |
| --- | --- | --- |
| `top_copper.routes` (centre line and width) | `POLY`, `polyType` NORMAL, the route's net and width: a native track | 1 Top Layer |
| `top_copper.electrodes` (rectangles) | `RECT` pads of the footprint `E1`, nets by `PAD_NET` | 1 Top Layer |
| `top_copper.pads` (the tail contacts) | `RECT` pads of the footprint `J1`, pad number = pin, nets by `PAD_NET` (`NC_<pin>` for an unused contact) | 1 Top Layer |
| `top_coverlay_openings` | `FILL` (`R` for a rectangle, a closed `L` ring for a masked field window) | 5 Top Solder Mask Layer |
| `outline.points` and each `outline.cutouts` ring | closed `POLY`, `polyType` BOARD_OUTLINE, 0.1 mm wide | 11 Board Outline Layer |
| `bottom_stiffener` | `FPC_FILL`, material `Polyimide`, thickness in mm | 59 Bottom Stiffener Layer |

Every route is a track.  The electrodes and contacts are rectangles, not
centre lines: a track has round ends, so a track over an electrode would
round its corners (about 0.21 w² less copper per electrode of width w).  A
`RECT` pad keeps the rectangle exactly and carries the net, as the
electrodes and contacts of the user's original projects do (their sensor
pads and FFC contacts are footprint pads).  No copper is a polygon (`FILL`
on layer 1): the earlier writer's copper fills misbehaved in EasyEDA, and
none is needed.  Every pad has a zero solder-mask expansion, so the pads add
no coverlay opening beyond their copper; the openings are the `FILL`s.

Each layer's contours are written clockwise (EasyEDA's outer contour) from
the layout's first vertex; outlines and arcs are the layout's straight
segments (fillets are already segments of at most 10 degrees).  Routed
cutouts are closed BOARD_OUTLINE rings inside the outline, the topology of
the user's 32-pin original.

**FPC mode** is the use of the stiffener layers 58 and 59: EasyEDA Pro's own
`setPcbType(2)` turns exactly these on.  The layer table is the originals'
(90 layers), with those two in use.

**Stiffeners** take the profile's one value: `stackup.stiffener_material`
(`polyimide`, written `Polyimide`) and `stackup.stiffener_thickness_mm`
(0.1 mm since the user's decision of 2026-11-06, 0.225 mm before), which
every stiffener of the layout must carry.  EasyEDA Pro
offers PI stiffeners of 0.1, 0.15, 0.2, 0.225 and 0.25 mm (JLC's list) and
resets any other thickness to 0.2 mm on load, so the exporter refuses a
thickness outside that list; an unknown material name would become
Polyimide on load, so the name is checked too.  EasyEDA's own export then
names the layer `Gerber_BottomStiffenerLayer_pib_0.1.GBSL`.

**Stack.**  The originals' nine `LAYER_PHYS` records with the profile's
thicknesses (mil): coverlay and adhesive on layer 5, the copper on layer 1,
the polyimide core as the dielectric, the profile's 1 µm placeholder bottom
copper and no bottom coverlay (0.111 mm in all, the boards' own 0.11 mm stack-up; they are ordered as a
2-layer 0.2 mm FPC).

**Design rules.**  The originals' rule set (JLCPCB Capability, Two Layers
Board) with this board's own rules from its DRC (`verification.checks`,
each less the DRC's 1e-6 mm tolerance, floored to 1e-4 mil):

| EasyEDA Safe Clearance | Our DRC rule |
| --- | --- |
| Track to Track | `route_route_clearance` |
| Track to SMD Pad | the smaller of `pad_trace_clearance` and `electrode_route_clearance` |
| SMD Pad to SMD Pad | the smallest of `pad_pad_clearance`, `electrode_electrode_clearance`, `electrode_pad_clearance` |
| Board Outline to Track and to SMD Pad | the smallest of `copper_to_outline`, `copper_to_cutout`, `route_to_outline` |

The track-width rule spans the board's routes and the profile's
fabrication minimum; the solder-mask expansion is 0.  The other entries
(vias, holes, planes) are the originals'; our boards have none of those
objects.

## Coordinates and determinism

Coordinates are mils (EasyEDA's unit) in our millimetre frame, Y up and not
moved, rounded to 1e-6 mil, so EasyEDA's Gerbers come out in the frame of
ours.  The user's project as EasyEDA Pro saved it and EasyEDA's Gerber
export of it (`fpc_design/easyeda/epro2_based_native_jlc_candidate/`)
confirm the reading: the copper and stiffeners read from its records with
these conventions (an `R` rectangle anchored at its upper-left corner, pads
placed by their component) cover EasyEDA's Gerbers to within 0.003 mm²
(`tests/test_easyeda_export.py`).

The output is deterministic: UUIDs are digests of the build identity, the
board and the exporter version (`easyeda-pro-epro2/0.1.0`), the update time
is fixed (1980-01-01, the ZIP timestamp), every ZIP is stored (no zlib) and
the bytes are the same on Python 3.9 and 3.12 and under any hash seed; the
test pins the digests of four builds.  Before returning, every project is
read back (`verify_project`) and compared with the layout: the documents and
their links, FPC mode, every track, pad and net, opening, outline contour
and stiffener with its layer, material and thickness.

## In EasyEDA Pro

1. Open https://pro.easyeda.com in a browser and log in (or use the
   EasyEDA Pro desktop app).
2. File > Import > EasyEDA/JLCEDA (Professional) (the item reads
   `EasyEDA(Professional)...`, `JLCEDA(Professional)...` in the Chinese
   edition): choose one `.epro2`; it opens as a project of its own.  Open
   its PCB.
3. Check FPC mode (the Top and Bottom Stiffener Layers in the layer list),
   each FPC stiffener (Material Polyimide, the profile's thickness), the
   copper on the Top Layer, the openings on the Top Solder Mask Layer and
   the outline on the Board Outline Layer.
4. Design > Check DRC: 0 errors expected.
5. Order PCB..., or Export > PCB Fabrication File(Gerber)... and upload
   that ZIP to jlcpcb.com as a Flex PCB.  Set the order options of
   `README_EASYEDA.txt`.  Repeat with the other board.

To check EasyEDA's Gerbers against ours, run
`python3 tools/compare_easyeda_gerbers.py <EasyEDA Gerber ZIP> <our direct-gerber ZIP or the .epro2>`:
it fills the copper, coverlay, outline and stiffener layers of both by
scanlines and reports per layer the areas, bounding boxes and the area of
their symmetric difference, and the stiffeners of both `jlcpcb.json` files
(exit status 0 when every layer agrees).

## Not known until EasyEDA imports the files

These projects have not been opened in EasyEDA Pro by this work; the user's
import is the acceptance test.

- **Import of the pads.**  The archive-local footprint, device and
  schematic channel follow the earlier writer whose projects EasyEDA Pro
  imported with every pad; that EasyEDA keeps them for these files too is
  the first thing to check (24 pads for the default Row FPC, 64 for its
  Column FPC).
- **FPC mode** should show on import (layers 58 and 59 in use, as in the
  originals); if not, switch the board to FPC in the layer manager.
- **DRC.**  The rules are ours, but how EasyEDA measures copper to the
  outline (from the outline's centre line, as the originals' DRC result
  implies, or from its 0.1 mm stroke) and whether it treats an electrode
  touched by its route as connected decides the result.
- **Cutouts.**  A routed cutout is a closed Board Outline ring, as in the
  user's 32-pin original; that EasyEDA's export and 3D view treat it as a
  hole (and not, for instance, as a second board) needs a look.  The
  default boards have no cutout.
- **Stack and order.**  Whether EasyEDA's order page takes the copper
  weight and thickness from the stack (`LAYER_PHYS`) or only from the order
  form; set them on the form as `README_EASYEDA.txt` says.
- **Editor version.**  The files say 3.2.149 (the release on the user's
  Mac); newer releases open older files.
