# FlexiTac-Gen: Tactile FPC Customizer

Online: <https://flexitac.github.io/flexitac-gen/> (the static site below:
everything runs in your browser).  For FlexiTac's assembly and applications
see <https://flexitac.github.io/>.

A local, deterministic generator for the two flexible PCBs of a matrix
tactile sensor: a Row-electrode FPC and a Column-electrode FPC.  It has two
modes: the **rectangular** mode designs the sensor from its numbers, and the
**CAD** mode fits it to a surface selected on a CAD part (an STL), see
[docs/CAD_MODE.md](docs/CAD_MODE.md).  Both build the Row traces as the
diagonal Row bus (below): the rectangular mode by default, with both sides
(its Row traces select keeps the straight Row channel one choice away).  It runs on
the Python standard library only, needs no installation and makes no
network request.  There is no LLM or agent at runtime; the API and CLI are
built so that tools and agents can drive it.  Approved earlier designs were
reference material only: nothing is read from them, or from any EDA project
or Gerber, at generation time.

## Run

Python 3.9 or newer (see `pyproject.toml`; there are no dependencies).  From
this directory:

```bash
python3 app.py                 # browser UI on http://127.0.0.1:8008
python3 app.py --port 8009     # another port; --host binds another address (with a warning if not loopback)
```

On a remote machine (VS Code Remote-SSH, plain SSH), forward port 8008 and
open `http://localhost:8008` locally; VS Code's port preview works too.  A
tunnel, proxy or LAN name in the address bar needs `--allow-host <name>`
(otherwise 421, see [docs/API.md](docs/API.md#http-server)).

Command line and Python, with the same strict input as the HTTP API:

```bash
python3 cli.py schema                                # JSON Schema of the design
python3 cli.py validate design.json                  # input rules and feasibility, no geometry
python3 cli.py generate design.json --compact        # summary with every DRC measurement
python3 cli.py export design.json --out outputs/     # the three ZIPs, named by build id
python3 cli.py surface fit part.stl --pick X,Y,Z --out outputs/   # CAD mode: fit to the surface at X,Y,Z (mm)
```

```python
from engine import generate_design
from exporters import build_exports

result = generate_design({"matrix": {"rows": 16, "columns": 32}, "connector": {"row_pins": 16}})
assert result["ok"], result["validation"]["errors"]
zips = build_exports(result)
```

`outputs/` is a git-ignored scratch directory for such exports; the
application itself stores nothing.

### As a static website

`tools/build_static_site.py` writes the whole app as plain files for GitHub
Pages or any other static host.  The page answers its API in the visitor's
browser: `app.py` itself runs in [Pyodide](https://pyodide.org) (CPython
compiled to WebAssembly) in a Web Worker, so no server runs and no design or
mesh is uploaded.  The answers, build ids and files are `app.py`'s, byte for
byte (`tools/browser/static_checks.py` compares them).  The first visit
downloads about 7 MB (Pyodide, then cached by the browser), and a surface fit
takes about twice as long as under `app.py`.  The site carries the
generator's Python source (`static/py/engine.zip`); its URLs are relative,
so it works under any path.  Its one request elsewhere is GitHub's API for
the FlexiTac repository's star and fork counts in the header (written into
the page when it is built, refreshed as it opens, as on
flexitac.github.io).  `app.py` writes them into the page it serves: it reads
them from GitHub's API itself, hourly, so its page asks no other host
(`--no-github`: the card shows the name alone).

```bash
python3 tools/build_static_site.py --out site/   # downloads Pyodide 0.27.8 and checks its SHA-256
python3 -m http.server -d site 8010              # a local look on port 8010
```

### The Library

`library.html` (the header's Library link, in a new tab) lists sensors
already fitted to open-source gripper fingers, grouped by gripper: seven
gripper parts (Franka Hand, WidowX 250, Trossen WidowX AI, ARX X5, I2RT YAM,
Unitree Dex1-1, MakerMods Metal Arm), each at four pitches from a fine 1 mm,
and the UMI fin-ray finger at four pitches with its tapered tips (its last
75 mm narrowed to a trapezoid or a convex arc, five tip widths from 21.8 to
5.8 mm, 2 mm pitch; Shape and Tip width on their page).  The seven grippers
come first, one card each, four to a row (two on a phone), each with its
pitch range ("1 to 3 mm") and "Pick your pitch": it opens the gripper's
2 mm sensor, whose Pitch switch offers the others.  The UMI finger's shelf
follows, a card per pitch and one for the tapered tips, its heading naming
its pitches ("Four pitches, 1 to 3 mm, and tapered tips.").
Each sensor has its own address,
`library.html#<id>` (for example `library.html#widowx-250-1mm`; `#<part>`
shows its 2 mm sensor), with its Top and Bottom FPC Gerber ZIPs, the part's
STL and its licence, and opens in Gen by Surface at `./?part=<id>`, built at
once from its shipped fit and editable from there (on a phone the sensor's
page shows its picture as a 3:1 band, so Open in Gen by Surface is in a
390 x 844 phone's first screen).  The pictures are the generator's figure
of the sensor on its part: the seven grippers drawn whole, a sensor on both
fingers and the jaws fully open (the other finger is the same part turned,
carrying the same board, or a mirror-image part carrying the mirror-image
board, which is not the sensor's Gerbers; the finger nearer the viewer is
see-through in both views and its sensor stays assembled, the other
finger's sensor explodes into the gap; the MakerMods Metal Arm's two tips
stand on a plain rail drawn by this project, not MakerMods hardware), the
UMI finger and its tapered tips as the fingertip.  Each card shows it
exploded; a sensor's page shows its picture and, drawn over it, the same
scene in 3D to turn (drag it, or the arrow keys; 0 or a double click
brings it back; the Exploded | Assembled switch under it drives both)
where its entry names its 3D view (`view`); without one, without WebGL or
when a file does not load the picture stays.  Every sensor has its
picture, and where its file does not load a drawing of the sensor's taxel
grid takes its place.  On the static site the ZIPs are built with the
site; under `app.py` the page asks the server for them.  The page loads no
engine or Pyodide, and three.js only on a sensor's page.

The sensors are data in `web/library/`: `parts.json` (each part's mesh,
licence, the face the page selects and its pitches; edited by hand, the
tapered tips' parts and family written with their meshes by a private
cutting tool), the meshes and licence texts with their `NOTICE.md`, the
grippers' scenes of the 3D view (`scenes/`, with the rules every scene is
drawn by, and their bodies in `bodies/`: the grippers' open models,
decimated, each tabled in `NOTICE.md`; written by a private scene
builder), each sensor's art (`art/`, the generator's art of its two boards,
written by the shots tool), and what
`tools/library_write.py` writes from them: `fits/<id>.json` (the request the
page sends for the sensor and the engine's reply) and `entries.json` (the
index the page reads, with each sensor's picture and 3D view; the formats
are frozen in [docs/LIBRARY_VIEW.md](docs/LIBRARY_VIEW.md)).  After any
change of the page's defaults (a sensor's request changes with them) or a
change of the engine or the profile that moves a build id, refit and commit
them:

```bash
python3 tools/library_write.py            # fit every sensor, write what changed
python3 tools/library_write.py --check    # write nothing; exit 1 listing the stale sensors
```

The static site's build is the gate: it fits every sensor again and stops
("the library is stale: run tools/library_write.py") when a reply or a build
id differs from the committed one, or a fit's request is no longer the one
the page sends, so a stale library is never published.

The pictures are the Library's own 3D view (Gen by Surface's figure of the
sensor on its part, with the gripper's scene) at its Exploded and
Assembled homes: `tools/browser/library_shots.py` shoots them in a browser
into `web/library/shots/` (WebP with alpha, each drawing centred in its
picture, with a manifest of the fit each was shot from, its art and a
gripper's measured stage) and `tools/library_write.py` writes them and
each sensor's 3D view into `entries.json`; a picture of another fit, an
art of another build, a gripper's stage of another scene or one breaking
the scenes' rules fails `--check` and the site build, and so does a scene
the writer refuses; a sensor without its picture fails `--check` and the
tests.  After a refit, a new sensor, a change of the figure or of a scene,
write, shoot the changed sensors again and write again.

## What it does

- **CAD mode** (browser: the page's default, the "Gen by Surface" switch
  beside the title, "FlexiTac-Gen" (the page itself never says "CAD": its
  workspace is "Pick a surface on a 3D model"); the "Rectangular" switch or
  `#rect` for the rectangular mode; CLI: `cli.py surface`; HTTP:
  `/api/surface/*`).  The header holds the title, the mode switch, the
  look's toggle and FlexiTac's GitHub (with the repository's stars and
  forks) and Discord on one line, centred on the title, with the line on
  FlexiTac under them.
  - The workflow: drop in an STL, rotate it, click a surface, set the
    resolution, Generate.  The browser opens with the UMI fin-ray finger
    loaded (`web/vendor/umi`, HandUMI, Apache 2.0) and its sensor already
    generated (a border of 65 mm of its contact face from the tip, the
    first proposal: 32 x 12; its fit shipped, so it shows at once) until a
    file is chosen, and fits at most 32 rows and 32 columns by default (Max
    rows, Max columns, up to 64).
  - Samples to try (the user's request of 2026-11-06): under the step
    guide, "Try a sample" holds eight parts in two columns (on a laptop's
    window compact, each picture beside its name; beside the steps on a
    narrow page; one row that scrolls sideways on a phone, so the page
    around it does not move): two of the UMI finger's tapered tips (the
    5.8 mm trapezoid and the 13.8 mm convex arc), four other Library
    fingers (ARX X5, I2RT YAM, Unitree Dex1-1, MakerMods Metal Arm) and two
    whole grippers with their jaws open (Franka Hand, WidowX 250).  Drag one
    onto the 3D view, or click it (Enter, Space or a tap): the part loads
    with no face selected and no sensor built (the user's later request of
    2026-11-06; only the default UMI finger's sensor is generated as the
    page opens), so you click the face the sensor goes on and press
    Generate sensor, as for your own file; on a whole gripper's finger the
    face is then seen from past the other finger.  The address becomes
    `./?sample=<id>`, so a reload shows it again.  A tile or a file may be
    dropped anywhere on the 3D view's window, its tools included.  The
    sample shown, pressed again, is only framed again; one that cannot be
    loaded leaves the part shown and its sensor as they were, with a
    warning.  Your own file, dropped or chosen, loads the same way, with
    no face selected.
    The samples are
    static files in `web/samples/`: `samples.json` (each one's Library
    sensor, named in step 1's note), the thumbnails (drawn by `tools/browser/sample_thumbs.py` in
    the 3D view's look) and the two whole grippers, each one binary STL
    assembled from the Library's scene of that gripper (the MuJoCo
    Menagerie's Franka Hand, Apache-2.0, and WidowX 250, BSD-3-Clause), its
    finger's facets first; their sources, changes and licences are in
    [web/samples/NOTICE.md](web/samples/NOTICE.md).
  - The surface may be flat, creased or singly curved (cylinders, cones,
    extrusions, bands opened along a seam).  A doubly curved surface is cut
    down to the disk a flat sheet covers within 0.3% stretch.
  - The fit chooses rows, columns (up to 64 x 64), pitch, routing, role
    mapping and tail lengths, on the engine's `surface_matrix_v1`
    template, whose margins are tighter.  The field follows the selected
    area (P5-diagonal-bus.md section 26.16: CAD mode has no rectangle
    shape, no generic template and no rectangle preference; rectangular
    fields are the rectangular mode's): it proposes masked fields (up to
    64 x 64, as the rectangles: coverage of the selection first) whose
    taxels follow the surface (a triangle on a triangular face) besides the
    rectangles, a symmetric field first on a face symmetric about its exit
    (unless a field that breaks the symmetry holds at least 20 % more,
    P5-diagonal-bus.md sections 26.17 and 26.19), and the fit
    option `reader` sizes the tails for a 16 x 16, 32 x 16 (FlexiTac),
    32 x 32 or 48 x 48 reader.
  - By default (`containment: field`) only the taxel field has to lie on
    the surface: every proposal is a diagonal Row bus (below), whose side
    bands, Column fan-out and tails may leave the surface, and the field
    may be any row- and column-convex shape (`row_sides`, the browser's
    Row traces, picks the bands' sides: `both`, `left` or `right`).  The
    soft finger's contact face through its mount end takes 708 taxels
    instead of 352; a turned field must have 3% more taxels than the best
    unturned one, and with an automatic exit the exit with the narrowest
    tip within 3 taxels of the most wins.  Both tails end together, on one
    line across the boards, so their stacked contacts line up (the nearer
    end `tail_extension_mm` past the base edge, or farther where the 7.5 mm
    shortest tail sets the line), and the map reports each board's share on
    the surface, its overhang and the edges it crosses too sharply, with
    what to do.  `containment: board` (the browser's Whole board) keeps
    everything above the tail roots on the surface, as before.  With
    `tip_first` (on by default) the field reaching nearest the fingertip,
    the face's end opposite the exit, within 3 % of the most taxels goes
    first.
  - It maps every taxel onto the part: the taxel map in the STL frame, a
    3D overlay and a 1:1 wrap template.
  - The geometry is the stdlib package `surface/`.  The 3D view is a
    vendored three.js (MIT, `web/vendor/three/NOTICE.md`), loaded only in
    CAD mode.

- **Design input** `tactile-fpc-design/v1`: rows (1-64), columns (1-64),
  X/Y pitch (0.6-10 mm), electrode widths, physical top/bottom tail lengths
  (7.5-80 mm), tail sides, which FPC is on top, channel order, connector
  sizes and the fan-out traces (`routing.trace_width_mm` 0.1016-0.254 mm and
  `routing.trace_space_mm` 0.1016-0.246 mm) and the Row traces
  (`routing.row_sides`: `both`, `left` or `right` build the diagonal Row
  bus, `channel` the straight Row channel, which takes at most 32 columns
  and tails from 7.0 mm).  On the surface template `matrix.mask` gives a
  masked field.  Unknown keys are errors with their JSON path; the
  documented aliases are reported; numbers are taken on a 1e-6 mm grid.
  Default: 12 x 32 at 2.0 mm pitch with 1.0 mm electrodes and 0.127 mm
  fan-out traces at 0.127 mm spacing (the electrodes at fill 0.5, the user's
  decision of 2026-11-06; 1.4 mm before), the diagonal Row bus with `both` and
  both tails 12 mm, so the stacked tails end together (the user's decision
  of 2026-10-27; the bottom tail 7.5 mm before; on the generic template
  `routing.row_sides` defaults to `both`, or to `channel` where the tails
  leave on opposite sides or the field is a single row or column, the
  bottom tail then 7.0 mm; on the surface template to `channel`, its bottom
  tail 7.5 mm), build `tactile-fpc-12x32-34a71a29e4d0`.
- **Geometry** (layout `tactile-fpc-layout/v3`): the traces leave the sensor
  thin, converge into a bundle at the trace width + spacing (0.254 mm by
  default) and expand again to the 0.5 mm contact pitch, with bus-style
  bends (parallel 60 degree diagonals, the bend points staggered); below
  every bend, in the tail, they widen to the 0.254 mm gold-finger width.  With
  `routing.row_sides` `channel` a Row board with a non-crossing left channel
  at the bundle pitch (the straight Row channel), and a
  Column board with one fan-out bundle (up to 16 columns) or two bundles
  around a routed slot, which spread wider than the sensor when the field is
  too narrow for them; tails for 0.5 mm-pitch ZIF connectors, (pins + 1) x
  0.5 mm wide with 0.30 x 4.0 mm contacts, R0.30 tip corners, isolated NC
  contacts and a 6.0 mm bottom PI stiffener; 0.3 mm copper to every edge and
  filleted outlines.  The diagonal Row bus (`routing.row_sides` `both`,
  `left` or `right`, `diagonal-bus/11`; the default) is built by one
  construction with CAD mode's rule set (the surface profile: a 0.5 mm field
  margin, up to 64 columns, tails from 7.5 mm) on either template, so the
  rectangular mode builds exactly the boards CAD mode builds for the same
  design (the straight channel keeps the generic profile).  It runs each
  Row trace as a slant from its row's end down one side of the field,
  hugging its boundary and following it inward where it recedes (with
  `both`, odd rows on one side and even rows on the other, so the tip
  carries one trace); below the field every Row trace turns once into a fan
  (at up to 85 degrees) and once into its contact, the two sides meeting in
  a funnel under the field with `both` (one side: the whole bundle fanning
  in under the field), into a Row tail centred on the field in every side
  mode, so the tails lie within the sensor's width wherever they are
  narrower than the field.  The Column board keeps the straight one's
  copper, converging in one V straight into its contacts (one lane, no
  slot; at most 80 degrees where that roots the tails no deeper, so the
  fans keep 85), its tail centred, and the tails are stacked: the Row tail
  lies on the Column tail, and they part to their own connectors.  Down to the
  tails' roots both boards have one outline (the union of the Row board's
  body with its bands and funnel and the Column board's with its fan-out;
  each carries blank film where only the other has copper), so the films
  align by their edges and both tails leave one bottom edge; below it each
  is its own tail.  Both outlines are regular: no corner flatter than 5
  degrees but on a fillet (a flatter run is one straight edge outside it),
  and each side from the tip corner down to its widest point is one
  straight line where one line encloses it within 1.0 mm.  Outside the
  taxel field the two boards may overlap.  Its Row pins fold (ROW_01, 03, ..., 04, 02
  with `both`): `pinout.csv`, the netlist, `taxels.csv` and the Row board's
  `ORDER_NOTES.txt` give each row's pin; see
  [docs/INTEGRATION.md](docs/INTEGRATION.md).
- **Trace rules (JLCPCB, rechecked 2026-10-15)**: one-layer FPCs come with
  18 um (0.5 oz) or 35 um (1 oz) copper, whose minimum trace width/spacing is
  3.5/3.5 mil or 4/4 mil; the ordered build has 1 oz copper, so the minimum
  is 0.1016 mm for traces, spacing and electrodes alike.  JLC holds trace
  widths to +/-20%, so a 0.127 mm trace may come out at 0.1016 mm; each
  board's `ORDER_NOTES.txt` says what that makes of its own fan-out traces.
- **Checks**: input rules and feasibility before any geometry, with
  field-level bounds; a whole-board DRC of 30 records per board plus the
  registration of the two boards, each with its measured value (the route
  spacing rule is the design's trace spacing, and the finger-section spacing
  for a pair with a wide tail piece; every route piece must have its width).  `ok` is true only when everything passes, and exports are
  blocked otherwise.
- **Previews**: copper-side SVG top views with a pin-1 marker, an oblique
  view and an assembly preview of the stack, zoom and pan, the design
  checks.  The previews come in two looks: **Photo** (the default; colours
  sampled from a photograph of a JLCPCB-made pad: the amber coverlay over
  the polyimide, the copper under it, the darker gaps between traces, ENIG
  where the coverlay is open, the stiffener darkening what lies above it)
  and **Diagram** (the server SVG's own colours).  The stack's exploded 3D
  view and each board's oblique view turn with the mouse (**Reset view**
  over the stacked view's top right, as 0 or a double click, brings it
  home), and draw each
  single-sided board's two sides: its copper side, or its polyimide with the
  copper seen through it and the stiffener outermost, each board as thick
  as its stack-up (0.11 mm, the PI stiffener 0.225 mm more; drawn at least
  2 px thick, the stiffener in proportion); the plan view shows
  the registration.  Every view has a coin for scale beside the board, clear
  of it (in a board's 2D view at the window's bottom right, the board
  centred): a US quarter (24.26 mm) drawn to scale, its face
  the US Mint's photo (`web/vendor/coin`, public domain), with its shadow; in
  the 3D views it lies on the table below the boards, as thick as a quarter
  (1.75 mm, its reeded side), with a gleam that keeps to the light as the
  view turns.  The 3D views are lit as the sensor on the part is (below;
  2026-11-05): the same lights, fixed to the viewer, shade each board's side
  by the way it faces them, a faint satin sweep slides over the coverlay as
  the view turns, the walls are lit by the way they face and the shadows fall
  away from the key whatever the turn; the plan view stays a flat plan.  In CAD mode the stacked view has a second figure beside it
  (the user's request of 2026-11-05; one under the other where the card is
  narrower than 720 px): the sensor on the part.  The loaded part is drawn
  (of a whole gripper's sample with the sensor on its Library finger, that
  finger alone, so the other finger and the body do not hide it) in a matte light grey, and outward from it, along the face's normal, come
  the bottom FPC (copper out), the film (velostat, black, over the taxel
  field or its masked outline) and the top FPC (turned over: polyimide out).
  Each layer is draped on the part's surface where the map puts it, and
  where a board leaves the surface (a tail, a band past an edge) it runs
  flat on the plane of the nearest facet.  The boards show their art in
  the page's look on both sides; **Exploded** and **Assembled** switch the
  spacing.  A drag turns it, as the other 3D views do, and **Reset view**
  (over the view's top right; also 0 or a double click) brings it home.
  The view frames a finger or a gripper's tip whole, with the same room
  above it as below (since the second review of 2026-11-05; its outlines
  no longer show a light seam where they cross the part).  Since the look
  of 2026-11-05 it is lit like a product shot under a soft studio that
  turns with the view: the film is a satin black with a soft gradient from
  top to bottom (a flat black had read as a hole in the stack), the boards'
  coverlay shows a faint amber sweep, each layer has a thin edge, and
  **Assembled**, which opens about 29 degrees off the face, shows a soft
  contact shade where the stack meets the part, starting at the stack's
  edge on a curved part too.  It is drawn in
  the browser from the map, with no request of its own.
- **Interface**: one step to a sensor.  In CAD mode ("Gen by Surface") the
  default part's sensor is generated as the page opens; a model loaded
  (your own file or a sample) has no face selected, a click selects the
  face the sensor goes on, and
  **Generate sensor**, alone under the 3D view, fits it and generates its
  proposal #1 onto the part (its tooltip says what the sensor is, or what
  to do next; the Gerber ZIPs are the downloads').  Everything else is
  folded under **Advanced Customization** ("Customize the sensor" until
  2026-11-04): the base edge, the resolution and
  Fit, the proposals, Generate and the checks on the part, with **More
  options** and the other folds inside it as before.  In the rectangular mode only
  the rows, columns, pitches and Generate are in sight, the rest under
  Advanced Customization with **More options** inside.  The design checks are
  one line ("all N checks pass"), opening on a failure with only the
  failing rules listed; the other files and the ordering notes are folded
  (the stacked view stays open).  CAD mode hides the rectangular form and shows the
  results once it has generated a build.  Each figure's controls sit in
  its frame, top left in one row (the user's request of 2026-11-06): the
  board cards' **3D view** and **2D view** (with the 2D view its zoom, the
  level alone in sight, the scale in its tooltip), the stacked view's
  **3D view** and **2D view**, the sensor on the part's **Exploded** and
  **Assembled**; what a figure draws at its home stays clear of them.
  The stacked view has no caption since 2026-11-06 (it had read
  "Exploded 3D registration review · ..."); the board cards' oblique
  view keeps its own.
- **Look**: the page is `web/index.html` with `web/app.js` and `web/cad/`,
  styled by `web/styles.css` and, linked right after it, `web/theme.css`
  (2026-11-04): an Apple-style look in the system's fonts, light for
  every visitor whatever the system's setting, dark once the visitor turns
  it on with the small toggle in the header right before GitHub (a moon,
  a sun while dark; 2026-11-06, `web/theme.js`: the choice is kept in the
  browser for both pages and applies before the page first shows, with no
  flash of the other look), the drawings' areas (the 3D view, the previews,
  the stacked view and the sensor on the part beside it, the map) light in
  either.  Blue fills only each region's
  primary action and what is chosen; motion is only feedback to the
  pointer and the keyboard (none under the system's reduced motion), and
  nothing moves with the scroll.
- **Exports** (the two Gerber ZIPs first among the page's downloads, set
  off): one Direct Gerber ZIP per FPC (GTL, GTS, GKO, GBSL,
  `jlcpcb.json`, an IPC-D-356A `netlist.ipc`, `ORDER_NOTES.txt`,
  `manifest.json`) and a project review ZIP (design, profile, validation,
  derived layout, pinout, taxels, order notes, previews, both Gerber ZIPs,
  manifest with every digest); the taxel map `taxels.csv` is in masked and
  diagonal Row bus builds only, the default among them.  Byte-identical output for the same input on any
  supported Python; the exporter reads back everything it writes.
- **EasyEDA Pro projects**: a separate ZIP with one native `.epro2` per FPC
  (tracks, pads with their nets, coverlay openings, outline, PI stiffeners
  in FPC mode, the board's own design rules) and `README_EASYEDA.txt`:
  import it into EasyEDA Pro (pro.easyeda.com), check it and order there,
  and EasyEDA writes the Gerbers itself.
- **Ordering**: the profile's `order` block and the stack-up of the ordered
  build say how to order the boards; `engine.profile.order_requirements`
  words each entry from those values and cites the profile's JLCPCB and
  connector sources.  Order each board as a 1-layer, 0.11 mm FPC with 1 oz
  copper and a 0.225 mm PI stiffener at the contacts, a +/-0.05 mm outline
  tolerance (a special request) and ENIG, and check that the 0.3 mm gold
  fingers come out within +/-0.05 mm (JLC's trace tolerance is +/-20%).
  The order form's Gold Fingers Thickness is 0.3 mm, the stiffened contact
  zone in total, which JLC gives the highest priority when it chooses the
  stiffener under the gold fingers (profile revision 2026-10-29); each
  board's lines name its coverlay windows and those longer than JLC's
  general 20 mm for one opening, to check on the upload.
  `ORDER_NOTES.txt` in every ZIP, both manifests (`order_requirements`),
  `/api/default` and the browser's manufacturing note list these entries
  with their reasons.

## Compatibility

The necked routing of 2026-10-15 (generator `deterministic-sensor-core/0.4.0`,
exporter `direct-gerber-pure-stdlib/0.3.0`, profile revision 2026-10-15,
layout `tactile-fpc-layout/v3` with two route pieces per net) changed every
board and every build id; a design saved before then builds again, with the
default fan-out traces unless it sets `routing`, under a new id.  Electrodes
narrower than 0.1016 mm (accepted down to 0.1 mm before) are now rejected.

## Limits

- CAD mode works on STL only.  A flat sheet covers doubly curved surfaces
  (domes, fingertips) only over small disks; slit (comb) boards are
  planned; see [docs/CAD_MODE.md](docs/CAD_MODE.md#limits).  Its masked
  fields ([`matrix.mask`](docs/API.md#field-mask-matrixmask): the polygon
  coverlay window in the GTS, a `taxels.csv` map of the active positions in
  the review bundle) are at most 64 x 64 (`max_rows` x `max_columns`, as
  the rectangles; 32 x 32 before 2026-10-25).  With `containment: board` they
  are of the engine's straight construction classes (a staircase on one
  side of the field and the lane taper on the Row channel's side); with
  `containment: field` any row- and column-convex field, on the diagonal
  Row bus, whose boards reach beyond the exit edge (their shared body 2.9-7.5 mm
  on the named CAD fixtures, before their tails) and wrap over the
  surface's side edges.

- The Gerbers are **Direct Gerber / JLC review candidates**, not EasyEDA
  exports and not production approval.  No package has been through a
  JLCPCB upload, a connector insertion or a continuity test.  Upload each
  board ZIP separately and check the outline, the coverlay openings and the
  detected PI stiffener before ordering.
- The default Row tail has 12 contacts; the FlexiTac reader's row connector
  has 16, so set `connector.row_pins` to 16 for it.  The contact zone is about
  0.285 mm thick with the 0.225 mm stiffener (an estimate from the stack-up of
  the ordered 0.11 mm build), within the connectors' 0.30 +/- 0.03 mm; JLC
  holds the gold-finger area to +/-0.03 mm, so measure it on delivery.  One
  of the two tails must be turned over to reach bottom-contact connectors on
  one reader face.  See [docs/INTEGRATION.md](docs/INTEGRATION.md).
- One template (`generic_matrix_v1`), one locked profile; no alignment
  features, no electrode slits, no canonical 12 x 32 compatibility template;
  no saved builds; the HTTP server has no authentication and is meant for
  the local machine.

## Tests and checks

```bash
PYTHONPATH=. python3 -B -m unittest discover -s tests   # stdlib unittest suite
node --check web/app.js                                  # browser script syntax (optional)
node --check web/library.js                              # the Library's script (optional)
node --check web/theme.js                                # the look's toggle, both pages' <head> (optional)
python3 -B tools/mutation_check.py                       # the suite against known defects (minutes)
```

`tests/test_docs_consistency.py` checks the tables and Python snippets of
these documents, and the quoted figures it lists, against the code, so a
change of the output fails there until the documents follow it; prose
without figures is not checked.  `tools/` also has
`golden_values.py` (refresh the default-build golden values after a
deliberate change) and, under `tools/browser/`, Playwright checks of the
browser UI that need their own virtual environment; none of them is part of
the unittest suite.  CI (`.github/workflows/fpc-agentic-customization.yml`
at the repository root) runs the suite on Python 3.9 and 3.12, checks that
the mutation catalogue still applies to the code and checks the syntax of
`web/app.js`; the full mutation run is a manual job of the same workflow.

## License

Apache License 2.0 ([LICENSE](LICENSE)).  The vendored files under `web/vendor/`
keep their own licences, each named in its folder's `NOTICE.md`: three.js
(MIT), the UMI finger (Apache-2.0) and the US Mint photo of the quarter
(public domain); the static site adds Pyodide (MPL-2.0, `static/py/pyodide/NOTICE.md`).
The Library's gripper parts, the bodies of its 3D view's grippers and their
licence texts (Apache-2.0, MIT and BSD-3-Clause, from their pinned upstream
commits; the Franka pad's hull, the UMI finger's tapered tips and the
decimated bodies are modified files, so stated; the MakerMods rail is this
project's own) are listed with
their sources in [web/library/NOTICE.md](web/library/NOTICE.md); part names are
their makers' trademarks, and FlexiTac is not affiliated with them.

## Documentation

- [docs/API.md](docs/API.md): Python, CLI and HTTP contract, input and its
  normalization, JSON Schema, build identity, SVG previews.
- [docs/LAYOUT_SCHEMA.md](docs/LAYOUT_SCHEMA.md): result and layout v3,
  DRC records, issue codes, profile rules.
- [docs/INTEGRATION.md](docs/INTEGRATION.md): pin 1, the stack, the reader
  connectors and which tail is turned over.
- [docs/PHASE2_DIRECT_GERBER.md](docs/PHASE2_DIRECT_GERBER.md): the exporter
  and its archives.
- [docs/EASYEDA_EXPORT.md](docs/EASYEDA_EXPORT.md): the EasyEDA Pro projects,
  their mapping, the steps in EasyEDA and the Gerber comparison tool.
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) and
  [docs/PHASE1_TECHNICAL_RECORD.md](docs/PHASE1_TECHNICAL_RECORD.md): the plan
  with its status, and the historical record.
- [docs/CAD_MODE.md](docs/CAD_MODE.md): CAD mode (pipeline, options, routes,
  outputs, limits), and [docs/SURFACE_TACTILE_PLAN.md](docs/SURFACE_TACTILE_PLAN.md):
  its plan, research and roadmap.
- [claude/APP_HANDOFF.md](claude/APP_HANDOFF.md): development handoff
  (architecture, contracts, profile, tests, open items).
