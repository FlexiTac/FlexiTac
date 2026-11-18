# Tactile FPC Customizer — application and development handoff

Updated 2026-10-15 (UTC).  Source: branch `fpc-customizer-audit-fixes`,
based on `92cdcb6` (the code the 2026-10-12 audit examined).
`git log 92cdcb6..` lists the fix commits: C1, stages E, A, X, F, T and G,
the remote-access fix and the follow-ups of the final review.  What the
final review of 2026-10-15 left open is section 9 of
[the audit report](verification/2026-10-12-audit-report.md).

## What this is

A self-contained local application that generates the two flexible PCBs of
a matrix tactile sensor, a Row-electrode FPC and a Column-electrode FPC,
from a small versioned design.  It validates the design, builds both boards,
runs a whole-board DRC on the emitted geometry, shows copper-side previews
and an assembly preview, and exports deterministic Direct Gerber review
candidates with an IPC-D-356A netlist and a self-verifying review bundle.
It uses the Python standard library only (Python 3.9+), reads nothing from
`../fpc_design`, any EDA project or any Gerber at runtime, and has no LLM or
agent despite the directory name; the JSON Schema, validate and compact
endpoints and `cli.py` are the surface an agent would use.

Where to read further: [README](../README.md) (run, features, limits),
[docs/API.md](../docs/API.md), [docs/LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md),
[docs/INTEGRATION.md](../docs/INTEGRATION.md),
[docs/PHASE2_DIRECT_GERBER.md](../docs/PHASE2_DIRECT_GERBER.md), the plan
with its status in [docs/IMPLEMENTATION_PLAN.md](../docs/IMPLEMENTATION_PLAN.md)
and the [2026-10-12 audit report](verification/2026-10-12-audit-report.md).

## History

- 2026-09-13/14: Phase 1 (engine, UI, JSON) and Phase 2 (Direct Gerber
  exporter 0.1.0), recorded in [docs/PHASE1_TECHNICAL_RECORD.md](../docs/PHASE1_TECHNICAL_RECORD.md);
  imported as commit `045b737` (synced from `far-pi5`).
- 2026-10-11: a first review ([verification/2026-10-11-review.json](verification/2026-10-11-review.json)).
- 2026-10-12: the full audit (3 critical, 6 high, 14 medium, 13 low, 5 info).
- 2026-10-13: C1 fixed (exporter 0.1.1); the fix-all specification decided
  the product defaults D1-D24.
- 2026-10-13/14: the fix in five stages, each implemented, reviewed and
  repaired: **E** engine geometry and whole-board DRC, **A** API, identity,
  HTTP and SVG, **X** exporter 0.2.0, **F** browser UI, **T** tests and
  documents.  Dated session notes are in `claude/sessions/` (not in the public copy).
- 2026-10-14: stage **G**, approved by the user after a review of the
  reader-connector drawings: the default PI stiffener is 0.225 mm (was
  0.2 mm), and the profile's validated `order` block, with the stack-up of
  the ordered 0.11 mm build (1 oz copper), is written to `ORDER_NOTES.txt` in
  every ZIP, to both manifests (`order_requirements`), to `/api/default` and
  to the browser's manufacturing note; `engine.profile.order_requirements`
  words the entries from the profile values and cites the profile's JLCPCB
  and connector sources.  Profile revision 2026-10-14.2.  The gold-finger
  geometry is unchanged and is now measured on the emitted Gerbers
  (`test_export_gold_fingers`).
- 2026-10-15: **necked routing**, on the user's request ("the traces are too
  thick"): the fan-out trace width and spacing are design inputs
  (`routing.trace_width_mm` / `trace_space_mm`, 0.127 / 0.127 mm by
  default, from JLC's 1 oz minimum of 0.1016 mm up to the 0.254 mm finger
  width and the 0.246 mm finger gap); the traces converge into bundles at
  width + spacing with bus-style bends and widen to 0.254 mm in the tail,
  below every bend.  Layout v3 (a tail and a fan-out piece per net), the
  `route_width` record (30 per board), the route rule is the design's
  spacing on both boards, the trace minimum depends on the copper (closes
  re-audit N4: electrodes from 0.1016 mm), per-route SVG stroke widths
  (closes N18).  Generator 0.4.0, exporter 0.3.0, profile revision
  2026-10-15: every build id changed.  After its independent review the DRC
  also holds every route pair with a tail piece to the 0.246 mm
  finger-section spacing (the `finger_section` of `route_route_clearance`),
  the far bends of the diagonals are rounded away from the bundle (no
  diagonal leans past the 60 degree cap), each board's lines of
  `ORDER_NOTES.txt` say what JLC's -20% width tolerance makes of its fan-out
  traces, and `order_requirements` takes the default design from its caller.
- 2026-10-20: **CAD mode**.  The user asked for it and the build ran
  overnight without supervision; the log is
  `claude/specs/cad-mode/PROGRESS.md`, the decisions are in
  `claude/specs/cad-mode/SPEC.md` (C-D1 to C-D12; neither is in the public copy),
  and the feature is documented in [docs/CAD_MODE.md](../docs/CAD_MODE.md).
  - The workflow: drop in an STL, select a surface, set the resolution,
    Generate.
  - New package `surface/` (stdlib): mesh, selection, flattening, fit,
    placement, taxel map.  Routes `/api/surface/{inspect,select,fit,map}`
    take a framed body up to 64 MiB; `cli.py surface`.
  - A browser CAD mode with vendored three.js 0.186.1.
  - New engine template `surface_matrix_v1` with its own profile: margins
    0.5 mm, a tight Row channel, the bus angle searched up to 85°, a direct
    one-lane fan-out, up to 64 columns.  Generic designs keep their build
    ids (guard fixture).
  - Nothing is committed yet: the user decides.
- 2026-11-12/13: **the Library's realistic look** (the user's requests of
  2026-11-12: every gripper coloured after photos of the real product, with
  metal's lustre in the 3D view and the pictures, and at the top of the
  Library the original, hand-designed FlexiTac sensor on the xArm gripper;
  the project owner's decision of the same day that UFACTORY's "Gripper G1
  3D File" may be used).  Research notes first
  (`claude/specs/library-look/notes/`, not in the public copy), then two
  stages of parallel lines, each reviewed and fixed before its merge.
  Stage 1: the looks (optional keys of the scene format, `looks`,
  `part_look` and `smooth_deg`; the gripper studio of
  `web/cad/library_stage.js`; the base looks of
  `tools/library_looks/base.json`; `tools/library_split.py`), the xArm
  Gripper G1's meshes (split and decimated by `tools/mesh_decimate.py` into
  `web/vendor/ufactory-g1/`) and the hand-designed sensor
  (`web/vendor/flexitac-v2/`, `tools/flexitac_v2.py`, a placed record and
  `web/cad/drape.js`'s wrap).  Stage 2: the seven grippers' look files, the
  UMI finger and its tips in orange TPU (the rules' `part_looks`; Gen by
  Surface keeps its grey part, which `library_shots.py --check-generator`
  holds to a pin), and the showcase, the Library's first card and a page of
  its own (`web/library/showcase.json`, its scene and three pictures,
  `tools/library_showcase.py`, `library_shots.py --showcase`).
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) is the contract.  Three
  independent verifications of the merge (2026-11-13) and their fixes: the
  art's gzip header the same on every Python (`library_write.art_bytes`
  sets the OS byte 3; CI's 3.9 had failed `test_showcase`), the showcase's
  guard saying "remove it" of a file no tool writes, a refused site build
  leaving its folder empty, a one-file split's NOTICE wording; a turned
  Library view keeping the whole drawing on its canvas
  (`library_view.js` `fitLens`, held by `library_checks.py` `part_view`);
  the UMI orange matte (roughness 0.85: no salmon on faces turned to the
  lights), the showcase's Exploded camera of its own, the YAM's and the
  WidowX 250's fingers lighter than the film, the Trossen's actuator its
  darkest black, the ARX's rail with a lustre; every picture shot again.
- 2026-11-14: **the realistic look's follow-up** (the user's decisions of
  2026-11-14 on the merged Library), two lines, each reviewed and fixed
  before the merge: the UMI pad the photos' dark olive-brown in the
  Library's Assembled view (the rules' `part_pad`, `library_stage.js`
  `layPad`, `--check-generator`'s fifth comparison; Exploded and Gen by
  Surface unchanged) and the MakerMods Metal Arm's body drawn by eye after
  the maker's photos as the project's own shapes (`library_split.py`'s
  prism; no MakerMods file used).  No zoom in the 3D view (the user: "no
  need, now is good"); the showcase keeps HandUMI's holders.
- 2026-11-16: **the Library the first page** (the user's decisions of
  2026-11-15 and 2026-11-16: "我觉得之后可以让lib作为第一次点击进入时候使用的界面，然后在
  flexitac on xarm的details 后面，多一个按钮，generate sensor by yourself with cad
  file", the button named "Design your own", "是的 be first page"), on the
  line `fpc-int-n-first` beside `fpc-int-n-team`'s.  `web/index.html` is
  the Library (`library.html` before) and `web/gen.html` the generator
  (`index.html` before): Gen by Surface at `gen.html`, Rectangular at
  `gen.html#rect`, a Library sensor at `gen.html?part=<id>`;
  `library.html` is a forwarding page.  `web/forward.js` sends the
  addresses of before on (`./?part=<id>`, `./#rect`, `./#cad`, `?sample`,
  `?debug`, the generator's anchors to `gen.html`; `library.html#<id>` to
  `./#<id>`) with `location.replace`, their query and hash kept, before
  anything paints; the Library's own addresses stay.  `app.py` and the
  static site serve the three pages; every link, document and browser check
  follows ([docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The first
  page").  On the showcase's card, after Details, "Design your own" opens
  Gen by Surface in the same tab, the page's action blue's dated second use.
  Its independent review the same day (sound-with-fixes, six findings),
  fixed on the line: an old hash typed over the open Library (`./#rect`)
  sent on at its `hashchange`, the header's counts refreshed on the static
  site's first page (`web/counts.js`, out of `backend.js`), the forwarding
  page never counted by name (`FORWARD_PAGE`), the wordings of the old
  addresses swept, `ui_checks part_footer` waiting for Gen by Surface's
  build; the merge with `fpc-int-n-team` must point that line's new checks
  at the new addresses (the session log of 2026-11-15, its last section).
- 2026-11-16: **the UMI finger's shapes** (the user's request of 2026-11-16,
  of the UMI shelf's 1, 1.5, 2 and 3 mm cards: "后面这三种不是重复了吗，在第一个umi
  1mm点进去，config就可以选择毫米数量；我在这里更多想要体现umi不同shape我们都可以fit,
  你现在只有一个shape变体"; the shapes then chosen: concave arc, pointed, short
  taper), on the line `fpc-int-n-umi`.  The UMI shelf ("Six finger shapes,
  straight to pointed.") is one card per finger shape: the straight finger's,
  a gripper's card (its four pitches on its 2 mm page), then the tapered
  tips' family's cards, each its sensor's picture, two lines and page: Short
  taper (the last 40 mm, a trapezoid or a convex arc: Shape and Tip width),
  Convex arc, Trapezoid and Concave arc tips (the last 75 mm; Tip width
  21.8 to 5.8 mm) and the Pointed tip (a tangent ogive over 50 mm to a 2 mm
  point, chosen of four drawn and shot).  Sixteen sensors more, 58 in all,
  each a real fit by `tools/library_write.py` keeping every product rule,
  cut by `tools/library_tips.py`'s kinds (the ten of 2026-11-05 again byte
  for byte), with their pictures, art and Gen by Surface's pinned figure;
  every address of before still opens its page (`#umi-finray-1mm`,
  `#umi-tapers`).  `entries.json`'s family record is its cards
  (`card_record()`), a part's record names a shelved part's own card;
  `LABEL_MAX` 28 (measured on the file note); `web/library/` without its
  pictures 16.41 MB (`test_library`'s budget 12 MB raised to 17 MB).  After
  the lead's review the same day the shelf's cards show their sensor
  Assembled (`SHELF_VIEW`: from the Exploded home the tapered end was
  foreshortened under the exploded layers, the six shapes alike); no
  picture changed.
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The UMI shelf's shapes".
- 2026-11-16: **the review of the UMI finger's shapes** (sound with fixes,
  nine findings, each reproduced first; on `fpc-int-n-umi`).  The shelf is
  a grid as the grippers' section, three to a row from 735 px and two
  below, so its six shapes are side by side (in its row four showed at
  1440 px and one on a phone): the row's scroller, arrows and scroll
  listener are gone, nothing on the page scrolls sideways.  Each card's
  picture is its Assembled home framed on the fingertip (`.lib-shot-tip`:
  scaled 2.2 times about 41 % 3 % in its clipping box; the same file, no
  picture changed); the heading keeps "Six finger shapes," whole; a
  shape's page is titled by its card ("UMI Fin-Ray Gripper, concave arc
  tip") and every UMI shelf's page opens Assembled as its card; the 26
  tips' meshes are measured against `tools/library_tips.py`'s profiles by
  `test_library`'s `test_each_tip_is_cut_by_its_profile` (the profiles
  copied, the private tool's pinned to them); the order's reason "blunt to
  sharp" and the stale lines corrected; the 50 mm point kept (framed, it
  reads beside the convex arc).  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md)
  "The UMI shelf's shapes", the session log of 2026-11-15, its last section.
- 2026-11-16: **the cards aligned with the grippers** (the user's request
  of 2026-11-16, with a screenshot of the live shelf: "图一中umicard图太大，
  确保你要和上面的card大小保持一致；另外你这样是重新选择了一个角度，用户需要再完成一次gripper
  方向的空间转换，这样不好；你做成和这个finger一样的空间角度，而且可以做成exploded,这样所有
  card都是对齐的，大小对齐，空间朝向对齐。最上面的xarm gripper的空间朝向也要跟下面的这些家爪
  都对齐"), on the line `fpc-int-n-align`.  The UMI shelf is the grippers'
  grid (4 + 2, two on a phone; its own three-to-a-row rule, the frame on
  the fingertip and the Assembled cards and pages gone): each card a gripper
  card's size at every width, its Exploded card file, its page opening
  Exploded.  The UMI finger and its tips are drawn at the grippers' homes
  (scenes.json's rules' `part_homes`: the camera's up the finger's length
  toward its tip, the rules' camera about its face, as every gripper's
  scene, none of which overrides it: 30 degrees up, 65 / 57 off the face's
  normal, from the front; its stack spaced 0.8 of the boards' narrower side
  a layer); the 30 UMI sensors were shot again, the grippers' pictures the
  same bytes.  Gen by Surface keeps its figure (tilt 57 / spin -20, its
  pin unchanged); `--check-generator` holds the look and the tint at the
  figure's homes and the pictures as the rules are.  The showcase is at
  the rules' camera too (its own dropped; from the logo's side), its own
  bound re-measured (`assembled_opaque` below 0.65); its card stays
  Assembled.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The UMI
  shelf's shapes" ("Aligned with the grippers"), "Parts without a scene",
  "The showcase's scene and files".
- 2026-11-16: **the cards aligned, after their review** (sound with fixes,
  six findings, each reproduced first).  The showcase's near finger is
  see-through as every gripper's (solid, it hid its own pad whole from the
  grippers' homes: its card showed FlexiTac on one finger, its alt text
  "both"), its `near_seen` (0.891) and `ghost_cover` held to the rules again
  and its `opaque_max` to a bound of its own (below 0.55); its three
  pictures shot again.  `--check-generator` holds the look and the tint at
  the grippers' homes too (a sixth comparison, the part grey there the
  witness), the pictures' own.  The explode steps and the face's
  foreshortening (cos 65 degrees, 0.42) corrected in the docs, and
  `library.js`'s comments of the old shelf.  Not changed, with the
  measures for the user: the six shapes still alike at a card's size on a
  1x screen and on a phone (a frame leaving the tails out enlarges them
  1.27 times but cuts the tails at the picture's edge, and they still look
  alike at 155 px; each taper card's default its 5.8 mm tip is the other
  option), the UMI rows 20 px taller than the grippers' at 735 to 768 px
  ("Pick your tip width" on two lines), the showcase's shell a light grey
  from this side (a look, the user's to judge), its card Assembled.
- 2026-11-16: **the UMI cards zoomed on the tip, the showcase's card
  Exploded** (the user's decisions after seeing the cards aligned: "你可以show
  gripper的angle但是zoom in了，就是方向还是那个方向，但是用zoom in +exploded,那就可以tell了",
  then, of zoom 2 on the preview, "你现在zoom in 的太过了，tactile的tail都看不到";
  of the xArm card, "Switch to exploded"), on the line `fpc-int-n-zoom`.
  Each UMI card file is the Exploded home (the grippers' direction, up and
  explode, unchanged) drawn 1.25 times larger, a real render, and the
  1280 x 800 window of it on the tip (the tip 6 % below its top, the
  grippers' drawings' margin; the tails' roots and most of their length
  in, their ends off its bottom, the finger's base at least the top margin
  above it), downscaled to the card (`library_write.CARD_FRAMES`, the
  manifest's `card_frame`, `library_shots` `card_window()`); of 1.0 to 2
  compared on a sheet of the six cards at 297 and 155 px, 2 first cut the
  tails at their roots, 1.35 then put the finger's base on the card's
  bottom edge (the review), 1.25 keeps it 55 px of 800 above it at the
  least.  The shoot holds the card's read to the Exploded home's direction
  word for word (the stage's report), where `library_checks`' likeness
  let a degree through.  At 155 px (a phone at 1x) the five tapers still
  look alike, only the straight finger parting: no zoom that keeps the
  tails parts them from this direction; a phone-only remedy (one UMI card
  to a row there) is the user's to choose.  The UMI
  pages and pictures stay the whole drawing (the view has no zoom control):
  the card is the home's direction and explode framed on the tip, the one
  exception to "the card is the view's home".  The showcase's card is its
  Exploded drawing and its page opens Exploded, as a gripper's.  The 30 UMI
  card files and the showcase's card shot again; every other picture the
  same bytes.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The UMI
  shelf's shapes" ("Zoomed on the tip"), "The showcase's page", "The
  pictures' manifest".
- 2026-11-16, the LeFlexiTac (`fpc-int-n-leflexitac`; the user's request:
  "增加一个leflexitac的 放在最前面 ... 放在夹爪部分的最前面，就是franka
  gripper的最前面"): the Grippers' first card, before the Franka Hand
  ("Grippers. Eight, each fitted at four pitches."; the count is settled at
  the merge with the Robotiq line), LeRobot's SO-101 gripper with
  LeFlexiTac's moving jaw and wrist roll (TNA001-AI/LeFlexiTac `b61259f`,
  its project page's STL downloads) round SO-ARM100 `a758567`'s STS3215
  servo, placed by its `so101_new_calib.urdf`; our sensor fitted on the
  moving jaw's flat pad face (28.4 x 67.2 mm) at 1, 1.5, 2 and 3 mm, fill
  0.5, every product rule kept; a sensor on both jaws (the static jaw, a
  share of the wrist roll, is the see-through other finger, its sensor the
  same board turned onto its face); the rotary jaw drawn 39 degrees open of
  the URDF's 100 and the scene's explode at its bound, gap_share 0.45 (the
  one override, with its reason: `docs/LIBRARY_VIEW.md`, "The LeFlexiTac");
  black PLA and the servo's black case after LeFlexiTac's cover photo.
  LeFlexiTac's files state no licence: in the Library by
  `tools/library_write.py` `PENDING_LICENCES`, a dated entry pending the
  user's word (a co-author's), not to be published until then (Open
  items).
- 2026-11-17, the LeFlexiTac after its independent review (sound-with-fixes;
  `fpc-int-n-leflexitac`): the files stating no licence are now refused,
  not only warned of: `tools/build_static_site.py` stops before writing
  anything (naming them; `--allow-pending-licences` builds a local preview,
  which `tools/browser/static_checks.py` passes and the pages workflow never
  does) and `tools/export_public.py` exports nothing of such a commit
  (`library_write.unlicensed()`); LeFlexiTac's files credit the SO-ARM100
  parts they are remodelled from (Apache-2.0, `licenses/so-arm100.txt`) in
  their `NOTICE.md` rows, the part's holder and the project's note, and
  `pending_row()` / `pending_licence()` want that credit (`remodelled()`);
  a NOASSERTION body row is taken by its pending entry only, never by the
  Apache-2.0 it names; the importer's LeFlexiTac recipe is its own
  (`LEFLEXITAC_RECIPE`, the mesh the Library's copy where the source tree
  holds no download), so `--only leflexitac` runs from the user's tree; the
  words of the README, `NOTICE.md` and `docs/LIBRARY_VIEW.md` that said all
  eight grippers fully open, open-source or with a turned or mirrored other
  finger name the LeFlexiTac's exceptions.  Kept for the user, with the
  measures: which jaw carries LeFlexiTac's pad, and the card's near sensor
  almost edge-on (Open items).
- 2026-11-17, the user's word on LeFlexiTac's files ("leflexitac, i am the
  author, so its ok to use it in public": a co-author of LeFlexiTac;
  `fpc-int-n-leflexitac`): the entry is `tools/library_write.py`
  `PERMITTED_LICENCES`' (beside `PENDING_LICENCES`, empty now), dated
  (`permitted` 2026-11-17, `by` a co-author of LeFlexiTac); the files still
  state no licence (`NOASSERTION`); their `NOTICE.md` rows and the part's
  licence (`permission`) say `permission()`, "shared with the authors'
  permission (given by a co-author of LeFlexiTac, 2026-11-17)", the
  project's note says the permission is not a licence, and the page's link
  reads "Shared with the authors' permission"; the SO-ARM100 credit stays.
  `unlicensed()` holds only what no permitted entry takes: the site build
  and `tools/export_public.py` take the LeFlexiTac and still refuse a
  pending entry's files (a pending fixture in `test_library` and
  `test_static_site`); `library_checks.py` `part_downloads` checks the
  page's link; 6 `LEFLEXITAC` mutants, each killed alone.  The pictures are
  unchanged (`library_shots.py --check --only` the four LeFlexiTac sensors,
  `franka-hand-2mm` and `widowx-250-2mm`: 0 differ).  Its review
  (2026-11-17): a permitted entry without its day or who gave it was taken
  as a permission (its files published saying none); now `permission()`
  wants both, such an entry is no permission and its files are held; the
  importer's row takes the words from `permission()`; 2 mutants more.
- 2026-11-17: **the AgileX Piper** (the user's request of 2026-11-17,
  "AgileX Piper；ALOHA 2 夹爪；…这些先并行开始做"; the line `fpc-int-n-piper`):
  an eighth gripper card, last in the grid (the heading "Eight" on its
  branch; the merge settles the order and the count).  The real finger,
  MuJoCo Menagerie `agilex_piper`'s `link7.stl` at `fb36886` (2026-11-02,
  the newest commit to touch the model, which moved its lights only; the
  other menagerie grippers' `f3b6013` is older), unchanged (MIT, Copyright
  (c) 2024 RosenYin), not HandUMI's printed replica of its tip: its inner
  face is one clean face, 72 mm long in its chart (the finger 76.5 mm),
  20 mm wide at its end, 25.4 mm where the tip's flat ends and 56 mm at
  the root, flat but for a 2 mm rise over its tip half.  The face
  is grown whole by `surface` from the tip, inside a border 3 mm above the
  root (the root is 1 mm longer on one side and notched by the carriage's
  tabs: inside it the face is its own mirror image to 0.05 um, so every
  sensor is centred); 1, 2, 3 and 4 mm (32 x 30, 32 x 24, 23 x 17 and
  17 x 14), a large face as the ARX X5's.  Its scene: `piper.xml` at full
  opening (35 mm a finger, the jaws 70 mm apart), the other finger
  `link8.stl`, which is `link7.stl` turned (0.067 mm), the body
  `link6.stl` decimated (13422 to 7106 triangles, 0.44 mm) and shared out
  by look after AgileX's photos: matte black fingers (a non-metal, rubber
  in the gripper's listings) and cross plate (bead-blasted anodising), a
  satin black motor can, the ground steel rail (one).  The review of
  2026-11-17 (sound-with-fixes, six low findings): the pin moved from
  `f3b6013` to `fb36886`, the scene's "two guide rails" made one, the face's
  numbers, the fingers' finish worded as a non-metal, two stale counts and a
  line on the private video recipe reworded; the pictures came out the same
  bytes.  `library_write`'s
  recipe-key check passes an upstream folder (`agilex_piper/`, the licence
  text `mujoco_menagerie-agilex_piper.txt`).  The bodies', the art's and
  the Library's budgets raised by the Piper's share.
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The AgileX Piper".
- 2026-11-17: **the Galaxea R1 Lite** (the user's request of 2026-11-17:
  "AgileX Piper；ALOHA 2 夹爪；Galaxea R1 Lite；OpenArm（Enactic）；Rainbow
  RB-Y1；Seeed reBot DevArm；xarm原装夹爪；还有一个unitree的三爪也可以加上去；
  这些先并行开始做"), on the line `fpc-int-n-galaxea-r1lite`, one of the
  gripper cards built in parallel (the lead orders the cards and counts at
  the merge).  Its G1 gripper from GalaxeaManipSim at `abe7f51` (Apache-2.0
  by its `LICENSE`; its README says MIT): the finger
  `left_gripper_finger_link1.STL` unchanged as the part, the gripper link
  decimated and split into its motor can and plate, the URDF's full
  opening (the faces 100 mm apart), the other finger the part turned; the
  looks after Galaxea's product pictures (black anodised body, matt grey
  fingers); its four sensors (1 to 3 mm) on the flat contact face, bordered
  short of the carriage's notch; its card last in the grid ("Grippers.
  Eight, each fitted at four pitches.").  Its review the same day
  (sound-with-fixes, seven findings): `library_checks.py part_grid` counts
  eight cards; GalaxeaManipSim's `NOTICE` (MIT portions, Tianxing Chen)
  carried as `licenses/galaxeamanipsim-NOTICE.txt`; the reader test holds
  this line's fact alone; the face 26.2 mm wide at its base; no material
  claimed for the fingers; G1 among the trademarks; the carriage and rack
  the finger's mesh holds drawn black on the sensor's finger (the four
  sensors shot again).
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The Galaxea R1 Lite
  (2026-11-17)".
- 2026-11-17: **the Seeed reBot DevArm** (the user's request of that day,
  one of the grippers it asked for in parallel; line `fpc-int-n-rebot`), the
  eighth gripper card, last in the grid ("Grippers. Eight, each fitted at
  four pitches."): mujoco_menagerie `f3b6013` `seeed_rebot_devarm` (MIT,
  Copyright (c) 2026 Seeed Studio; derived from the URDF of Seeed's
  `Seeed-Projects/reBot-Isaacsim`, MIT since its top-level `LICENSE` of
  2026-07-30; its meshes are Seeed's, which its hardware repository
  `Seeed-Projects/reBot-DevArm` publishes under CERN-OHL-W-2.0 since
  2026-05-11, non-commercial CC BY-SA NC before, and Isaacsim's
  `urdf/RS/UPSTREAM_LICENSE` says so too: the review of 2026-11-17 traced
  the chain, `NOTICE.md` records both grants, the files are taken under
  MIT; at the merge of 2026-11-17 the CERN-OHL-W-2.0 text, reBot-DevArm's
  `LICENSE` at `eda479d`, ships beside the MIT one as
  `licenses/seeed-rebot_devarm.txt`, named by the part's row and fetched,
  pinned, by `tools/library_scenes.py`).
  The part is the left finger with the two 1.85 mm pockets of its contact
  face capped (the seats of its silicone grip pads; `meshes/seeed-rebot.stl`,
  written by the private `tools/library_scenes.py`, which pins every
  source), the face a symmetric triangle of 1440.8 mm2, fitted at 1, 1.5, 2
  and 3 mm (fill 0.5);
  the scene at full opening (50 mm a finger), the other finger turned, the
  bracket and rail, the printed supports and the slider extensions from the
  model, the RS-00 actuator drawn by the project to the model's sizes (its
  file is 1.03 MB decimated); the looks after Seeed's photos and bill of
  materials (`tools/library_looks/seeed-rebot.json`).  The bodies' (2.7 MB),
  the art's (0.65 MB) and `web/library/`'s (17.25 MB) budgets raised on the
  line, the merge's to set; [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md)
  "The Seeed reBot DevArm".
- 2026-11-17: **the xArm Gripper's card** (the user's word, "xarm原装夹爪",
  one of the grippers asked for that day, each built on its own line;
  `fpc-int-n-xarm-gripper`): UFACTORY's xArm Gripper from MuJoCo
  Menagerie's `ufactory_xarm7` at `f3b6013` (BSD-3-Clause, UFACTORY Inc.),
  the eighth gripper card, last in the grid ("Grippers. Eight, each fitted
  at four pitches."), titled "xArm Gripper" (the label's 28 characters);
  the deny-list's names narrowed to the card's own (`DENIED_NAME`); the
  stock finger's flat 29.5 x 37.5 mm pad at 1, 1.5, 2 and 3 mm, each
  centred; `hand.xml`'s four-bar linkage fully open (pure translations,
  the pads' faces 88.9 mm apart), the other finger the part turned; drawn after
  UFACTORY's renders and photos (the glossy white shell, black anodised
  links and fingers, steel pins).  The budgets raised in a dated note
  (bodies 3.1 MB, art 625 KB, the Library 17.5 MB).
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The xArm Gripper".
  Its review the same day (sound-with-fixes): the deny-list's names after
  the card's id only the Library's extensions, its test without the
  Robotiq 2F-85 names (the Robotiq line's) and its mutants on its xArm
  lines alone (`S/xarm-*`, 7); the other finger about 1.0 mm from
  `right_finger.stl` at most (0.79 was a sample's).  With the card,
  `test_library`'s row below reads: the deny-list's names but the xArm
  Gripper card's own, the near finger see-through on all eight grippers,
  the mate turned on five (the xArm Gripper too), the bodies within
  3.1 MB and the art within 625 KB (the row's own words left for the
  merge, which sets the count of every line).
- 2026-11-17: **the Rainbow RB-Y1** (the user's request of 2026-11-17,
  "AgileX Piper；ALOHA 2 夹爪；Galaxea R1 Lite；OpenArm（Enactic）；Rainbow
  RB-Y1；..."), on the line `fpc-int-n-rby1`, one of that day's gripper lines
  (the lead orders the cards and sets the count at their merge).  The eighth
  gripper card, last on the line, from MuJoCo Menagerie `f3b6013`
  `rainbow_robotics_rby1` (Apache-2.0, Rainbow Robotics; the 1.2 model
  `rby1m_1.2.xml`): the gripper `EE_BODY`, both fingers `EE_FINGER_1` and
  the pad `EE_FINGER_0`, the Library's part (its mesh written by
  `tools/library_scenes.py`, as no video recipe holds it).  The jaws fully
  open (the pads' faces 100 mm apart), the mate the same finger turned (the
  model leaves `ee_finger_r2` unturned), the near finger see-through, the
  wrist not drawn (the gripper closes its own top); black anodised after
  Rainbow Robotics' photos, the pad black rubber as they show it (the
  review of 2026-11-17, sound-with-fixes: the pad was the model's light
  grey, the photos called the v1.3 gripper's and the meshes `rby1-sdk`'s;
  it also found Rainbow's own drawing and photos of the gripper taller than
  the v1.3 model's `EE_GR_TF`, which the card drew then, and the 1.2
  model's `EE_BODY` nearer them; the user said "you decide" and the lead
  chose the 1.2 gripper the same day: 126 x 55 mm at the rail and 73 mm
  from the fingers' root to its top as the drawing's 126 x 55 and 92.2, the
  v1.3 one's 120 x 65 and 54; its bodies 104 368 bytes where the v1.3
  gripper's and the project's ring over its open top were 1 294 852, the
  Library's heaviest).  Four sensors (1 to 3 mm at fill 0.5) on the pad's
  tapered face without its top 10 mm strip (under the gripper's rail
  block), each centred, their fits the same on both grippers; their
  pictures at the grippers' homes (`part_aligned` as the others).  Heading
  "Eight", the grid 4 + 4.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The Rainbow
  RB-Y1 (2026-11-17)".
- 2026-11-17: the OpenArm (the user's request of that day, one of the
  grippers added in parallel, each on its own branch; the lead orders the
  cards and counts at the merge).  Enactic's OpenArm 1.0 gripper is the
  grippers' eighth card, last ("OpenArm 1.0", 1 to 2.5 mm, "Pick your
  pitch"; the heading "Grippers. Eight, ..."): the part HandUMI's replica
  of the OpenArm finger (handumi-hw `1448278`, unchanged, Apache-2.0;
  Enactic's `finger.dae` surface, credited beside it), fitted since the
  user's correction of the same day ("openarm你选的面不对，我们可以只选取finger
  tip那个小圆弧三角的部分") on the small flat rounded pad at its fingertip
  alone (170 mm2, 21.9 by 11.2 mm, symmetric: each sensor centred, the
  tails across its root edge toward the mount, centred and ending
  together) at 1, 1.5, 2 and 2.5 mm (fill 0.5, as the others; 10 x 20,
  7 x 13, 5 x 9 and 4 x 7 lines), where the first build had grown the
  curved cradle behind it (1644 mm2, not symmetric; 3 mm too); its scene from openarm_description `81fe647` (Apache-2.0,
  Enactic, Inc.; its LICENSE.txt in `licenses/`): the hand, the gripper's
  motor and each finger's carriage, read from Collada by the scene
  builder's own reader, the jaws at `finger_joint1/2`'s 44 mm, the other
  finger the same one turned; its looks after Enactic's photos and renders
  (`tools/library_looks/enactic-openarm.json`: matte black printed
  fingers, a dark guide rail, stainless brackets and carriages, a black
  motor can between aluminium caps).  `test_library`'s
  `test_the_openarm_is_drawn_from_its_open_model` (the pad's selection
  measured, its four sensors' lines) and
  `test_the_collada_reader_takes_only_metres_and_z_up`, and
  `mutation_check`'s `OPENARM` (5), `OPENARM_REVIEW` (5: the title, the
  about, the looks' photo, the finger's credit twice) and `OPENARM_TIP`
  (3: the cradle again, the base at the tip, 3 mm again), each killed
  alone, with the private builder's three `dae_frame()` mutants killed
  alone outside the catalogue; the review of the first build (the title
  "OpenArm 1.0": OpenArm 2.0's default end effector is its
  `pinch_gripper`; the looks after openarm.dev's og:image of 1.0, its hero
  now 2.0's) taken on its merits; `library_checks` counts eight cards
  and Tabs to the UMI shelf from the grippers' last card.  The web
  library's budgets raised by what it takes (18 MB, the bodies 3.1 MB,
  the art 0.63 MB: 17.84, 3.04 and 0.61 MB with it).
- 2026-11-17: **the YUBI Gripper** (the user's words of that day, of a card
  made of a finger pad they had downloaded: "这个同样也只做fingertip的三角；名字
  不要叫genealist, 感觉是 yubi"; line `fpc-int-n-yubi`), the eighth gripper card,
  last in the grid ("Grippers. Eight, each fitted at four pitches."): the pad
  is Toyota/yubi-hw's `FINGER_PAD_t30_L.stl` (`dd8bd13`, its newest commit;
  CERN-OHL-W-2.0, Copyright 2026 Toyota Motor Corporation, its Frontier
  Research Center; with the AI Robot Association's project page and paper),
  the Library's part unchanged, its sensor on the pad's fingertip face alone
  (a flat trapezoid of 201.3 mm2, symmetric), at 1, 1.5, 2 and 2.5 mm (fill
  0.5).  The whole gripper from the project's STL files where its assembly
  STEP places them (the private `tools/library_scenes.py` reads the STEP's
  placements as text and CATIA's ASCII STL; the files registered in their
  parts' frames), the left finger the user's pad, the right one its mirror
  image; the rotary fingers 11 degrees open from the assembly's pose, of the
  38.5 their parts allow (since its review the least opening at which every
  pitch keeps the rules, so that the near finger's sensor reads as a face:
  at the first 16 degrees it was a line, the camera 3.2 degrees behind the
  near face; 7.9 now); the servo and the fisheye camera
  drawn by the project as plain shapes; black PLA and red pads after the
  project's photos (`tools/library_looks/yubi-gripper.json`).  CERN-OHL-W-2.0
  an open licence for the Library (`library_write.py` `OPEN_LICENCES`), its
  terms kept in `NOTICE.md` (the changed bodies under it, each dated, this
  repository their Source Location).  Budgets raised in dated lines, the
  merge's to set; [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The YUBI
  Gripper".  Its independent review (sound with fixes, six findings): the
  pose above; "full opening" in `NOTICE.md`, the key table and the scene
  builder's notes given the exception; the page's line "gripper finger pad"
  (was the file code "finger pad (t30)"); each changed body's header dated
  (CERN-OHL-W-2.0 section 3.3(b)); ELP among the trademarks.  Left to the
  user: the pads' black rubber sheets (not drawn: the sensor's tails run
  where they lie) and the card's small sensor (the fingertip alone, as
  asked).
- 2026-11-17: **the Unitree Dex3-1** (the user's request of 2026-11-17:
  "还有一个unitree的三爪也可以加上去", and that day's "看看每个手指都做出来的效果怎么样": a
  sensor on every finger), on the line `fpc-int-n-unitree-dex3`: the
  G1's three-finger hand, the eighth card of the Grippers grid, last
  ("Eight"; the lead orders the cards at the merge).  Its model is
  unitree_ros `b579bbe`'s `robots/dexterous_hand_description/dex3_1`
  (BSD-3-Clause), posed open (each finger 35 and 35 degrees, the thumb 0,
  10 and 15: the fingertips' pads 74.3 mm apart); the Library's part is
  the fingertip link with its ridged cap replaced by the cap's
  mirror-symmetric hull (`meshes/unitree-dex3.stl`, written by the private
  scene builder), fitted at 1, 1.5, 2 and 2.5 mm (12.5 x 13.5 to 11 x 11 mm:
  the dome's strain limit).  The index fingertip's stack explodes toward
  the thumb's (see-through), the middle fingertip is a scene's new
  `extra_fingers` with a still stack.  Its card's sensor is 14 px wide at
  the grippers' homes (the hand framed whole), so its scene carries the new
  `checks` override, `card_min_px` 14 with its reason (the rules' 20 out of
  reach for this hand: the user's to accept or to frame hands otherwise).
  `library_stage.js` changed, so every other picture's record names older
  view sources until the merge's full shoot.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md)
  "The Unitree Dex3-1" (under "Hands: a sensor on every finger" since the
  hands' merge; "A hand: the Unitree Dex3-1" on its line).  Its review (sound-with-fixes, 2026-11-17)
  and fixes: each further stack is measured now (its top FPC's seen share
  in both modes, the record's `extra_seen`, 1.0 on all four sensors and
  held to `near_seen_min`; its clearance to all but its own fingertip,
  beyond 12 mm, in `clearance_mm.bodies`), read in the browser by
  `library_checks.py`'s new `part_hands`; the `checks` override only in a
  hand's scene; `EXTRA_FINGERS_MAX` 4, as the LEAP Hand's line has it; the
  docs' numbers measured again (the ridges up to 0.24 mm, the thumb within
  8.3 degrees, the fields' positions and taxels); the knuckles' look lighter
  (metalness 0.5, environment 1.6: #777b7f against #595c60, the photo's
  #7c8590 to #919aa5), its four sensors shot again.  **For the lead**:
  (1) four hand lines (this one, `fpc-int-n-leap-hand`, `fpc-int-n-allegro`,
  `fpc-int-n-orca-hand`) each change `library_stage.js` and
  `library_write.py`'s scene schema for further fingers in their own way
  (this line's and the LEAP Hand's `extra_fingers` alike but for their
  measures; the Allegro's named `fingers`; the ORCA's copies): land one
  mechanism first (one key, up to 4 fingers, optional names for
  `see_through` and the bodies, each further stack measured), decide the
  `checks` override once for every hand, then rebase this line's scene,
  test pins and mutants on it; (2) on this line `test_library` has 3
  `ShowcasePageTests` failures (`test_its_pictures_go_stale_with_what_they_were_shot_from`,
  `test_the_committed_document_is_current`,
  `test_the_writer_says_the_showcase_s_own_fixes`: the 58 other pictures
  and the showcase are of older view sources) until the full re-shoot,
  which is the lead's, once, after the merged stage; (3) the budgets
  raised here (18 MB, the bodies 2.8 MB, the art 650 KB) are the merge's
  to set once for all lines.  **For the user**: whether a hand's card may
  show its sensors at 14 to 16 px (the hand whole) or hands are framed on
  their fingertips (about 21 to 24 px, the palm cut, which the approved
  whole-gripper rule and the shots tool refuse today).
- 2026-11-17: **the LEAP Hand** (the user's request of 2026-11-17 and
  words of that day, "先把这几个做出来，看看每个手指都做出来的效果怎么样": a
  dexterous hand with a sensor on every finger; the line
  `fpc-int-n-leap-hand`): an eighth card, last in the grippers' grid (the
  heading "Eight" on its branch; the merge settles the order and the
  count).  MuJoCo Menagerie `leap_hand` at `f3b6013` (MIT, Copyright 2023
  Ananye Agarwal; derived from dex-urdf `2ee2f70`, MIT, whose README row
  said CC BY-NC 4.0 until its `93505db` of 2024-12-05; not the
  LEAP_Hand_API, CC BY-NC 4.0, nor the request form's CAD, CC BY-SA 4.0).
  The part is the white fingertip, `distal.obj`'s object `fingertip_W`
  alone (1450 facets; until the review of 2026-11-17 a cut at the flange's
  plane, which took the link's six posts along), derived by the scene
  builder (`PART_MESHES`); its pad's flat face, 26.04 x 13.87 mm, grown
  with `flat` at `theta_c_deg` 1, is symmetric, so every sensor is
  centred; 1, 1.5, 2 and 3 mm (25 x 13, 17 x 9, 13 x 6, 8 x 4).  The
  scene: the right hand open and ready to grasp (each finger bent at the
  knuckle, the middle and ring spread and a little more bent, the thumb
  raised and straight, the index pad facing the thumb's 67.4 mm across),
  the index's stack exploded, the thumb the mate (the same fingertip
  turned) see-through, the middle and ring fingertips `extra_fingers`, at
  the grippers' homes with its scene's `checks` override (`card_min_px`
  14: the whole hand framed, the pad seen at cos 65; 45 degrees of its own
  until the review).  Since the review its `extra_fingers` are the Unitree
  Dex3-1 line's mechanism byte for byte (each further stack measured:
  `extra_seen`, its clearance, held apart on screen; the `checks`
  override; `library_checks` `part_hands`), with one addition the hand
  needs: a body's finger `extra<k>`, a further finger's own links, which
  its stack is not held apart from (2.7 mm from its own distal link
  otherwise).  **The lead**: the four hand lines (this, Dex3-1, Allegro,
  ORCA) still differ (Allegro's named `fingers`, ORCA's `copies`); merge
  one mechanism (this branch's is Dex3-1's plus `extra<k>`), and
  `library_scenes.py`'s `PART_MESHES` (one map, two entries) and the two
  lines' `PICTURE_HAND` and `axis_turn` (renamed here `LEAP_PICTURE` and
  `leap_turn`, radians, where the Dex3-1's `axis_turn` takes degrees);
  ORCA's `snap` change meets this branch's `squared_off()`.  This branch
  cannot land alone: `ShowcasePageTests`' three checks of current
  pictures fail until every picture and the showcase are shot again with
  the merged `library_stage.js` (the picture bytes do not change:
  `library_shots --check` 0 differing on the hand, `franka-hand-2mm`,
  `widowx-250-2mm` and `umi-finray-2mm`).  Its bodies decimated within
  1.0 mm and 45 degrees (2.18 MB; 5.37 MB at the grippers' 0.5 mm).  The
  look after the paper's photo: satin black links, a matte black palm,
  white fingertips.  The bodies', the art's and the Library's budgets
  raised by its share.
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The LEAP Hand".
- 2026-11-17: **the Allegro Hand** (the user's request of 2026-11-17 and
  their words that day on the dexterous hands, "先把这几个做出来，看看每个手指都
  做出来的效果怎么样": a sensor on every finger), on the line
  `fpc-int-n-allegro`, its card last in the Grippers grid ("Eight").  MuJoCo
  Menagerie's `wonik_allegro` at f3b6013 (the V3, BSD-2-Clause, SimLab;
  Wonik's `allegro_hand_model_v4`, MIT, measured and not taken: its CAD
  meshes decimated within 0.5 mm are 5.7 MB, the palm 2.3 MB), posed open
  and ready to grasp; the part the index finger's medial link (the motor
  housing's flat palmar face, 27.8 x 21.8 mm), 1, 1.5, 2 and 3 mm.  A
  scene's new optional `fingers` (`library_stage.js`, `library_write.py`):
  the middle and ring fingers the part turned with the same board, the
  thumb the mate (the same flat face on its distal link: the same board,
  its tails toward its base), see-through; the stage draws a stack on every
  finger and measures the further fingers as fingers and stacks that cover;
  a scene without them is as before (`library_shots.py --check` 0 differing
  on three other sensors).  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md)
  "The Allegro Hand" (under "Hands: a sensor on every finger" since the
  hands' merge; "A hand's further fingers" on its line).  The review that day (sound-with-fixes):
  the hand's border ran clockwise, which the server fits and the page
  refuses ("Not fitted: E_CLIENT_BORDER" at `gen.html?part=allegro-hand-*`),
  now counter-clockwise (the same four builds) and `library_write.compose()`
  refuses every border the page refuses (`border_problem()`: border.js
  `validate()` and runFit's own checks); the index finger's exploded stack
  lay over the middle finger's sensor, unmeasured: the stage measures the
  further fingers' top FPCs (`fingers_seen`, held to `near_seen_min`; 0.76
  then) and the middle and ring fingers curl more than the index (a
  cascade; 0.998 or more now); the thumb's base and proximal links solid;
  the distal border edge's eight pieces (the tails toward the palm)
  documented and pinned; the showcase shot again (its pictures the same
  bytes, its view hash).  Left for the merge: the four hand lines built the
  stage's further fingers under four keys (`fingers` here, LEAP's and
  Dex3-1's `extra_fingers`, ORCA's `copies`): one schema and one
  `library_stage.js` to pick; then a whole shoot (`library_shots.py`, every
  sensor: their records are of older view sources, the pictures the same
  bytes; `test_library`'s `test_the_writer_says_the_showcase_s_own_fixes`
  fails on that warning until then) and `library_shots.py --showcase` again
  if the stage changes once more.
- 2026-11-17: **the three hands merged, one mechanism** (the line
  `fpc-int-n-hands`, from `2d60728`: `fpc-int-n-unitree-dex3` `b2c6219`,
  `fpc-int-n-leap-hand` `24f313f` and `fpc-int-n-allegro` `ffcc680`
  merged; the user's decisions of that day: a hand's card shows the whole
  hand, its sensors small, the scene's `checks` override the way; the
  hands after the grippers in one grid, the Allegro Hand, the LEAP Hand,
  the Unitree Dex3-1: "Grippers. Ten" on this branch, after the MakerMods
  Metal Arm; ORCA, ALOHA 2 and the Generalist card dropped).  One
  mechanism of a hand's further fingers: the scene key `extra_fingers`
  with the Dex3-1 line's measuring stage (each further stack seen,
  `extra_seen`, and clear of every body and finger but its own fingertip)
  and the LEAP line's body finger `extra<k>` (a further finger's own
  links); the `checks` override (`card_min_px` 12 to 20) a hand's scene's
  alone.  The Allegro Hand's scene ported from its own key `fingers` (its
  middle and ring fingers `extra1`, `extra2`, the matrices, bodies, thumb
  base and border as its review left them) and its middle finger's first
  joint 0.1 rad more curled (1.15 rad: the one stage holds the exploded
  stack apart on screen from every further stack, and at the review's
  1.05 the index finger's stack was 14 and 19.2 px from the middle
  finger's at 1 and 1.5 mm, under `stacks_apart_min_px` 20; now 28 to 40
  px), its `fingers_seen` now `extra_seen` (0.997 to 0.998).  One set of
  tests (`test_library`'s two copies of
  `test_a_hand_s_further_fingers_and_its_card_override`, one hiding the
  other, made one for the three hands; the Allegro line's tests of its
  own key gone; one `GRIPPERS` list whence every count) and of mutants
  (the LEAP line's five copies of the Dex3-1 line's dropped, the Allegro
  line's eight of its own key retired, 37 hand mutants each killed alone
  on a scratch copy); `library_scenes.py`'s one `PART_MESHES` and one
  `hinge_turn()`; the counts of `library_checks.py`, the tests and the
  docs `entries.json`'s or set once (the budgets: 21.5 MB, the bodies 5.4
  MB, the art 700 KB).  The hands' 12 sensors shot again with the merged
  stage (the LEAP Hand's and the Dex3-1's pictures the same bytes);
  `library_shots.py --check` 0 differing on `franka-hand-2mm`,
  `widowx-250-2mm`, `umi-finray-2mm` and `i2rt-yam-2mm`.
  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "Hands: a sensor on
  every finger".  **For the lead**: the 58 other pictures and the
  showcase name older view sources until the full re-shoot (3
  `ShowcasePageTests` of `test_library` fail until then), and the other
  new grippers go before the hands at the final merge.  **For the user**:
  the Allegro Hand's middle finger 0.1 rad more curled than its review's
  pose, and the hands' small card sensors (14 to 16 px on the LEAP Hand
  and the Dex3-1).  Its independent review the same day (sound-with-fixes)
  found the mechanism one (no code of the Allegro line's `fingers` left),
  the roles and the measured rules holding on all three hands
  (`part_hands`), the grippers' pictures unchanged and the hands' scenes
  rebuilt byte for byte, and fixed three small things: `library_checks.py`
  words the grippers' count as library.js does (`count_word()`: eleven or
  more cards at the final merge had raised an IndexError), `test_library`'s
  gripper tables one literal each, and the two history entries above
  naming the docs' sections as they are now.  The Allegro Hand's 1.15 rad
  kept (the trial logs give 14 and 19.2 px at 1.05).
- 2026-11-17: **the FlexiTac hardware's files** (the user's request of
  2026-11-17 on the showcase's window: "把instruction里面的fpc gerber也都放到
  这边可以直接download；另外 所有的card加上一条：ordering and fabrication：
  放上instruction link；reading board download ... 小于32x16的sensor用32x16的
  board，小于32x32大于16的，用32x32的board"; his answers to the plan: copy
  the files into the site, a reading board one ZIP of its Gerber, BOM and
  pick and place; tail C, the tails one pin per line and the page naming
  the board; Gen too), on the line `fpc-int-n-boards`.  The pad's two FPC
  Gerber ZIPs are served unchanged in `web/vendor/flexitac-v2/` and the two
  reading boards' bundles in `web/vendor/flexitac-reader/`, CC BY-NC 4.0
  material of Columbia University (each folder's `NOTICE.md`), every byte
  pinned by `tools/flexitac_downloads.py`, whose check the site build runs.
  `web/boards.js` names a sensor's board from its rows and columns (32 x 16
  for at most 32 and 16 lines, 32 x 32 for at most 32 on each, else none:
  42 and 16 of the 58 sensors, none larger).  Every sensor's window drops
  its Reader row for "Ordering and fabrication" (the guide) and "Reading
  board" (the board, its ZIP and notice) under its facts; the showcase's
  window offers the pad's Gerbers and "Reading board 32 × 16" under its
  tutorial; Gen's step 3 (both modes) shows the same two rows over the
  Ordering notes, following the form.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md)
  "Ordering and the reading boards".
  After its independent review (sound-with-fixes, seven findings, each
  reproduced and fixed): Gen's step 3 names the board the design's tails
  plug into (`boards.js` `tailsBoard`: the lines' board while each tail is
  one pin per line; with a Reader or connector pins, the board with those
  connectors, 16 and 32 pins or 32 and 32, else "none (tails for another
  reader)"; the 32 x 32 reader's tails had been named the 32 x 16 board);
  the showcase's two FPC ZIPs on one line under the tutorial and its board
  in the sensors' own row (a third pill had wrapped alone); from 1200 px a
  sensor's facts and the two rows one table (one values' column), so a
  plain sensor's window fits 1440 x 900 again (747 px of 756; it scrolled
  by 12); the board's dots after a no-break space (one had started a line
  at 320 to 326 px) and its ZIP named in full to a screen reader; the guide
  linked once in step 3 (the Ordering notes' line went); the reading
  boards' notice names EasyEDA v6.5.51 for the 32 x 16 board's Gerbers and
  EasyEDA Pro v3.2.109 for the 32 x 32's; the tests tie the rule to
  `surface/reader.py`'s readers and the boards' BOMs and take every href
  from `boards.js`.  Left to the user: the tapered tips' Tip fact on two
  lines from 1200 px (the showcase's tutorial pill, "FlexiTac hardware
  tutorial (Gerbers)" at the guide's top then, is "FlexiTac fabrication
  guide" at its ordering section since the user's word of 2026-11-17, the
  merge).

- 2026-11-17: **the Library's lines merged** (`fpc-int-n-final`, from
  `2d60728`): the UMI cards zoomed on the tip (`fpc-int-n-zoom`), the Robotiq
  2F-85, the LeFlexiTac, the AgileX Piper, the Galaxea R1 Lite, the Seeed
  reBot DevArm, the xArm Gripper, the Rainbow RB-Y1, OpenArm 1.0, the YUBI
  Gripper, the three hands (`fpc-int-n-hands`), Gen by Surface's tool menu
  numbered and the FlexiTac order files and reading boards
  (`fpc-int-n-boards`), each merged with `--no-ff` in that order and each
  conflict joined (the session log of 2026-11-15 lists them).  The
  Grippers grid in the user's order: LeFlexiTac, Robotiq 2F-85, Franka
  Hand, WidowX 250, Trossen WidowX AI, ARX X5, I2RT YAM, Unitree Dex1-1,
  MakerMods Metal Arm, AgileX Piper, Galaxea R1 Lite, Seeed reBot DevArm,
  xArm Gripper, Rainbow RB-Y1, OpenArm 1.0, YUBI Gripper, then the Allegro
  Hand, the LEAP Hand and the Unitree Dex3-1 (`parts.json`'s order; 19
  cards, "Grippers. Nineteen, each fitted at four pitches.", the count a word
  to twenty (to twelve before this merge) and its digits past as `library.js` and `library_checks`'
  `count_word()` write it), then the UMI shelf; 106 sensors.  Joined:
  `OPEN_LICENCES` one tuple (Apache-2.0, MIT, BSD-3-Clause, BSD-2-Clause,
  CERN-OHL-W-2.0); `DENIED_NAME` one expression, the Robotiq 2F-85's first
  alternative then the xArm Gripper's (in `test_library`'s copy too); the
  recipe-key regex the Piper's lookarounds with the LeFlexiTac's one-word
  skip; `tools/library_scenes.py`'s tables one literal each, one
  `PART_MESHES` (the reBot's, the RB-Y1's and the hands' fingertips, each
  held to `parts.json`'s file, SHA-256 and bytes), `build_body()`'s memo by
  source, pick, object and decimation, `load()` reading OBJ (its objects),
  binary and ASCII STL and Collada (its pick); `test_library`'s per-gripper
  tables one literal each from one `GRIPPERS` list.  Decided at the merge:
  the reBot's CERN-OHL-W-2.0 text ships beside its MIT one
  (`licenses/seeed-rebot_devarm.txt`, reBot-DevArm's `LICENSE` at
  `eda479d`, named by the part's row); the Galaxea R1 Lite's border runs
  counter-clockwise (the hands' `border_problem()`, the page's border.js
  `validate()`, refused the line's clockwise one; its fits' first proposals
  the same builds); the showcase's pill "FlexiTac fabrication guide" at the
  guide's ordering section (the user's word of 2026-11-17); NOTICE.md's
  trademarks one sorted union.  Every picture re-shot once with the merged
  stage (`library_shots.py`, 106 sensors in 871 s, then `--showcase`: the
  pictures and the art the same bytes, the records the merged sources'); the budgets set once (`web/library/` 29.5 MB for 28.60, the pictures
  9.2 MB for 8.84, the bodies 8.6 MB for 8.27, the art 1.05 MB for 1.01).
  `tools/library_scenes.py` rebuilds every gripper's committed scene and
  bodies byte for byte (then `library_split.py`).  4 `MERGE_FINAL`
  mutants.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The Library's
  lines merged".  Its verification (pass-with-fixes, six findings) and
  their fixes: the public copy's suite failed (`test_library`'s reBot test
  read the private `tools/library_scenes.py` unasked; its pin now compared
  where the file is, and `test_static_site` asks every private path a test
  names for `exists()` first, `S/verify-private-read`); `cad_checks
  part_library` failed on the OpenArm 1.0's and the YUBI Gripper's eight
  sensors (their parts run off the on-part figure's bottom, as
  `drape.js` frames: held to the bottom edge, `LIBRARY_CUT_BELOW`, the
  choice the user's, Open items); the full mutation run's 5 unexpected
  survivors, all of before the merge, four killed by tests of their own
  (`G/stackup-check`, `S/map-infinite-record`, `S/centre-line-obstacles`,
  `M/field-budget-windows`) and `M/diag-shared-no-ear` equivalent; the 10
  expected survivors the suite kills now expected killed; the two pairs of
  identical mutants one each; stale counts and lines in the documents and
  the session log.

- 2026-11-17: **the Allegro Hand and the Unitree Dex3-1 removed, the
  Unitree Dex1-1 moved before the LEAP Hand** (`fpc-int-n-trim-hands`,
  from `bff728c`; the user's words of 2026-11-17 on the mainline,
  "现在这个版本去掉allegro,去掉dex3；加上unitredex1", and, asked whether the
  last part meant the Dex1-1, already the eighth card, moved to the end
  beside the LEAP Hand: "1. yes").  Out of the Library: the two parts,
  their fits, pictures and manifest records, art, meshes, bodies, scenes
  and `scenes.json`'s map, looks, the licence text only the Allegro Hand
  used (`licenses/mujoco_menagerie-wonik_allegro.txt`; `unitree_ros.txt`
  stays, the Dex1-1's; BSD-2-Clause stays in `OPEN_LICENCES`, the Robotiq
  2F-85's), their NOTICE.md sources, notes, rows and trademarks (Allegro,
  Dex3, Wonik Robotics), their scene builders (`tools/library_scenes.py`
  `allegro()`, `rigid6()`, `dex3()` and its helpers; scipy no longer
  needed), their `PART_MESHES` row, their own tests
  (`test_the_allegro_hand_s_thumb_and_cascade`,
  `test_the_allegro_hands_tails_leave_toward_the_palm`, the Dex3-1's
  NOTICE note) and table rows, and their own mutants.  **To restore
  them**, take their files and code from `bff728c` (the last mainline
  commit that has them; its docs/LIBRARY_VIEW.md has their sections "The
  Allegro Hand" and "The Unitree Dex3-1").  The grid, `parts.json`'s
  order: LeFlexiTac, Robotiq 2F-85, Franka Hand, WidowX 250, Trossen
  WidowX AI, ARX X5, I2RT YAM, MakerMods Metal Arm, AgileX Piper, Galaxea
  R1 Lite, Seeed reBot DevArm, xArm Gripper, Rainbow RB-Y1, OpenArm 1.0,
  YUBI Gripper, Unitree Dex1-1, LEAP Hand: 17 cards, "Grippers.
  Seventeen, each fitted at four pitches." (`count_word()`), then the UMI
  shelf; 98 sensors; `scenes.json`'s map, the scene builder's `GRIPPERS`
  and `test_library`'s `GRIPPERS` in that order.  No picture changed
  (the Dex1-1's card is the same card; the stage and the rules the same
  bytes).  The hands' one mechanism stays (`extra_fingers`, a body's
  `extra<k>`, a hand's `checks` override), held with the LEAP Hand alone:
  `test_a_hands_further_fingers_are_seen` on `leap-hand-2mm`,
  `test_every_border_is_one_the_page_fits` on the AgileX Piper's border;
  `mutation_check.py` `HAND_MECHANISM` (the mechanism's 15 mutants of the
  Dex3-1 line and 5 of the Allegro line, their ids kept), `UNITREE_DEX3`
  and `ALLEGRO_HAND` retired with five mutants of the two hands' own text.
  The budgets lowered with a dated note: `web/library/` 27.6 MB for 26.72,
  the pictures 8.55 MB for 8.23, the bodies 8.0 MB for 7.68, the art 0.985
  MB for 0.95.  `cad/library_stage.js`'s comments still name the two hands
  (it is a view source whose hash the pictures' records carry: left as
  it is).  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "Hands: a sensor
  on every finger".

- 2026-11-17: **gently curved faces** (`fpc-int-n-curved`; the user's report of
  that day on the Unitree Dex3-1's fingertip, the study in
  `library-look-work/look/out/curved/` and the user's decisions on it: "lets do
  1 and 2；soft tapes；然后whole fingertip的话先不做；…现在我们一般是自己
  laminate；0.2mm").  A curved chart beyond 0.05 % is the least-max-stretch one
  (`solve.least_stretch`, `bounded`: rounds of 20 steps stopping once two gain
  under 1 %), judged by the stretch a laminated sheet feels (smoothed over
  1 mm); the page's Surface click sends the strain limit as `stretch_budget`
  and on a doubly curved face selects the largest patch round the dome that
  flattens within it (`select.stretch_region`: Omega / 12 pi first, then
  regula falsi on the charts; the same symmetric patch from any click on
  it), on
  planar and developable faces the face as before; the fit takes a curved
  selection whole or refuses it saying how much fits round its click (no
  hidden disk: `fit.limit_strain` gone, `limited_chart` kept for placements
  saved before), its lattice along an elongated dome's axis and unturned;
  the map's strain checks pass on the smoothed stretch and report the facet's
  too (`measured_facet`).  The page: the strain limit one select of two
  tiers, 0.3 % and "1 % · bonded once" (its note: "Bonded once: test first, soft tape creeps."), and Shrink to fit with its line beside
  Generate sensor.  The real stack: the boards the profile's 0.2 mm, the
  field 2 x 0.2 + 0.1 film + 2 x 0.075 lamination = 0.65 mm, bends 6.5 and
  2 mm (4.7 and 1.1 before).  The user's case: their Custom 30 / 30 / 4 (31
  taxels on a hidden disk before) refused at 0.3 % (0.79 %, 279 mm2 fits, 55
  taxels after Shrink to fit) and fitted whole at 1 % (85); a click 55 at
  0.3 %, 94 at 1 %.  The Library: no build id changed but the Dex3-1's
  2.5 mm (its four keep 110, 49, 28, 18 taxels); 41 replies gained one bend
  obstacle (the UMI finger's 30, LeFlexiTac 4, OpenArm 4, the default part's
  fit); 42 written and shot again (38 pictures byte for byte), the UMI's 30
  generator pins again.  The charts the same on Python 3.9 to 3.12 and in
  Pyodide 0.27.8.  The prototype's options (selection.flatten, fit curved /
  strain_measure / exit_frame, preset dome) removed.  `test_surface_curved`
  (16), 16 `CURVED` mutants (4 of the disk retired), `cad_checks
  part_curved` (14 checks).  [docs/CAD_MODE.md](../docs/CAD_MODE.md)
  "Gently curved faces (2026-11-17)", with the study's classification.
  Screenshots: `library-look-work/look/out/curved/build/`.

- 2026-11-17: **gently curved faces, the review's fixes** (`fpc-int-n-curved`;
  the independent review's verdict sound-with-fixes).  The gate reads the
  stretch the sheet keeps on the part: the relaxed sheet's (ARAP's chart,
  `Chart.relaxed`; soft tape creeps to it, a^2 / 8 at a cap's rim against
  the least-max-stretch chart's a^2 / 12), smoothed over 1 mm, so the 0.3 %
  default keeps the copper elastic on the part (the bounded chart's gate
  left about 0.45 %, the 1 % tier 1.6 %); the lattice stays on the
  least-max-stretch chart.  The stretch click never returns a patch beyond
  the limit (a cone repeating an end's patch moved by bisection to one of
  its own; more steps while the best within is under 0.9 of the limit); a
  click off the dome's patch selects round the click; a face within the
  limit is selected whole (its graph undirected: the AgileX Piper's facet
  1008); the patch is filled to its convex outline (the Dex3-1's six inner
  corners now two); E_SURFACE_NO_FIT names the field's bend (half
  cylinders of R 5 and 6 mm refused since the 0.65 mm stack, as the docs
  now say); a tier changed keeps a flat face's sensor; the quick line
  offers 1 % only below it.  The trial patches skip the least-max-stretch
  rounds (`build_chart(least=False)`): a Dex3-1 click 0.9 s natively, 2.6 s
  in Pyodide (2 to 4 s and about 2.6 x that before).  The user's case: their
  selection 1.19 % on the part, refused at both tiers (239 and 405 mm2 fit:
  47 and 83 taxels after Shrink to fit); a click 238.8 mm2 (47) and 405.1
  mm2 (83).  The Library unchanged (106 current).  `test_surface_curved`
  16 -> 22 (1350 tests), `CURVED` 16 -> 22 mutants (eight added, four
  changed, two retired as equivalent), `cad_checks part_curved` 19 checks.

- 2026-11-17: **gently curved faces, symmetric and larger** (`fpc-int-n-curved`,
  after the mainline's trim was merged into it: the Dex3-1's fingertip a test
  fixture, `tests/fixtures/unitree-dex3.stl` with its BSD-3-Clause notice; the
  user's feedback on the preview, "finger应该是对称的，但是你select的面不对称，
  而且更大的curved surface应该也是可以选取的", and their choice "1% default on
  curves").  A face's mirror planes found on the mesh (`select.mirror_maps`:
  through its area centroid, across the coordinate and principal axes, 99 % of
  its area mirroring within 0.05 mm and 10°); every patch the stretch search
  tries taken with its mirror image where the two make one piece
  (`mirror_closure`), the dome's axis laid on the plane: the dome's patch
  symmetric and the same from every click on it, a click's patch reaching the
  plane symmetric, one on a side the mirror image of its mirror click's.  The
  page's strain limit 1 % on a doubly curved selection (its stretch on the part
  beyond 0.05 %), 0.3 % elsewhere; `Strict 0.3 %` in More options keeps 0.3 %;
  its note under 1 %, "Test first: rim may wrinkle or lift on tape."; the
  choice changed re-selects a curved selection from its middle (the select
  reply's `stretch.centre_facet`).  The Dex3-1: a click inside its dome's
  patch 405.1 mm2, 82 taxels (13 x 8) symmetric and centred (Strict: 238.8 mm2, 48);
  on the preview before, 279 mm2 and 55 taxels, lopsided.  The Library's 98
  fits the same requests and builds (`library_write --check`, which now
  refuses a doubly curved Library face, `curved_face`); a flat gripper, the
  LEAP tip and a cylinder the same build and pixels as the mainline's.  The
  docs say RA copper (JLC's FPC), the user's lamination, soft tape, why 1 %.
  `test_surface_curved` 22 -> 26 (`MirrorSymmetryTests`), `test_surface_web`
  and `test_library` one each (1354 tests), `CURVED` 22 -> 29 mutants,
  `cad_checks part_curved` 20 checks.  Screenshots:
  `library-look-work/look/out/curved/followup/`.

- 2026-11-17: **the review of the symmetric, larger selections fixed**
  (`fpc-int-n-curved`; verdict sound-with-fixes, seven findings): a click's
  patch is a disk (`select.fill_holes`: the holes it encloses filled with
  the part's facets in them; a curved ring judged beyond any limit), so the
  Dex3-1's tip-end click (8817) is 98.4 mm2 and its own mirror image, not a
  125 mm2 ring slit on one side, and the LEAP Hand's 11 refused curved-face
  clicks select; a mirror plane that fails through the face's centroid is
  fitted to the face (`_fitted_plane`, Gauss-Newton on the mirrored
  centroids' distance to the surface: a hole of 4 or 8 mm2 on one side keeps
  both planes); the dome's axis on its planes exactly; a doubly curved
  selection that is its own mirror image carries its planes' traces in its
  chart (`chart.mirror_traces`, `api.mirror_traces`): its sides split
  symmetrically about the trace (`api._mirrored_runs`: the Dex3-1 dome's
  base end one side across the plane, drawn so before Generate), the auto
  arcs turned onto the plane centred on it (`fit.axis_exit`, the exit's
  edges each other's mirror image), and an exit square across a trace takes
  it as the symmetric-face rule's axis, the outline allowed a facet off its
  mirror image (`fieldfit.mirror_axis`: a tessellation not itself symmetric
  gives a symmetric field, the synthetic dome's 59 taxels); a Library
  sensor's 0.3 % no longer chooses Strict 0.3 % (main.js
  `applyLibraryOptions`); the select reply's middle is a facet of the
  click's face (`select.click_face`).  The Dex3-1: 82 and 48 taxels as before, on the
  base end's side; Shrink to fit at the user's base point 82 symmetric (83
  asymmetric before).  The Library's 98 fits the same requests and build
  ids.  `test_surface_curved` 26 -> 35 (`SymmetricFollowupTests`, 9),
  `test_surface_web`'s strain-limit test (1363 tests), `CURVED` 29 -> 41
  mutants, `cad_checks part_curved` and `part_library` four checks more.
  `cad_checks` whole: 485 of 489 (the four Whole-board checks on the soft
  finger, the real stack's since 56624a1: resolved on 2026-11-18, below).
  Screenshots: `library-look-work/look/out/curved/followup/` (replaced).

- 2026-11-18: **Whole board on the real stack** (`fpc-int-n-curved`, the
  lead's decision on that day's open item: outside the taxel field the board
  is a single FPC, not the laminate): under `containment: board` F (P and its
  0.5 mm margin) keeps the laminated field's 6.5 mm bend rule, and the Row
  channel and expansion, the Column fan-out and the tails to the exit take
  one board's 2 mm, as Field only checks the routing off the field
  (`fit.surface_obstacles`: `bends` one board's under Whole board,
  `field_bends` the field's, counted apart in the reply; the rectangles'
  raster keeps F's box off them nearest its placement, `UsableRaster.field_y`;
  the masked walk each row's share of F, `FreeSpace.field_intervals`; a built
  field is checked exactly, `fit.field_bend_point`, and peeled as any
  containment failure).  The map's `board_clearance` takes one board's bends
  too (`field_bend_radius` the field's, as before).  The soft finger's face
  at side 0 under Whole board: 480 (50 x 12) again, its five proposals the
  mainline's (0.47 mm stack) byte for byte.  Field only unchanged: the
  Library's 98 requests and replies (350 build ids) byte for byte
  (`library_write --check`, and all 98 re-fitted by c4701b5's code and this
  one, compared), Gen by Surface's samples (`test_samples`).
  `test_surface_curved` 35 -> 37 (`WholeBoardBendTests`, a roof of two
  18-degree creases; 1365 tests), `CURVED` 41 -> 47 mutants, each killed
  alone.  `cad_checks` whole: 493 of 493 (the four Whole-board checks
  among them); `library_checks part_aligned part_pictures` 44 of 44.
  Screenshots:
  `library-look-work/look/out/curved/whole-board/`.
  Its review (the same day): the raster moved F only up and down and the
  walk only from the channel's edge, so a bend running toward the exit, no
  longer the boards' edge, left F no room beside it: the roof turned (its
  exit on the long side, the creases running to it) fell from 182 taxels
  (the rule before) to 132; the fill now also searches with the boards off
  the field's bends and takes the best of both (`fill._search_fill` twice,
  only with `field_bends`; the second search's account left out of the
  reply), 182 again; the soft finger the same five proposals (at Max rows
  and columns 64; 338 at the page's default 32, as on the mainline, the
  figure the open item gave), its fit 0.9 -> 2.4 s natively (the second
  search finds nothing there: its crease cuts every tail).  The fit's account says "1 field bends", not
  the reply's key.  `WholeBoardBendTests` 2 -> 3 (1366 tests), `CURVED`
  47 -> 49 (`S/field-bends-strict-search-dropped`, `-unkept`, each killed
  alone), `cad_checks part_field_soft` one check more; `cad_checks` whole
  494 of 494.  Screenshots replaced.

- 2026-11-18: **the Unitree Dex3-1 back, on its dome's curved fit**
  (`fpc-int-n-dex3-back`, from `b5403f3`; the user's word after trying the
  curved faces, "挺好的，这样你就可以把dex3加回去，然后可以push一版本": put the
  Dex3 back, then push a version; the lead pushes once it is merged).
  Restored from `bff728c`: the part, its mesh (the same bytes, the curved
  faces' test fixture), bodies, look file, NOTICE.md's source, modified-file
  notes, rows and Dex3 among the trademarks, the scene builder (`dex3()`,
  `dex3_links()`, `dex3_components()`, `dex3_tip()`, scipy's hull; its
  face's normal and centre now the dome patch's: the approach 4 degrees
  round, the gap 76.0 mm), its tests and `UNITREE_DEX3`.  Its face is one
  click on the dome as the page sends it (grow, Surface, `stretch_budget`
  0.01 from facet 9267; a click inside the patch the same 405.1 mm2, one
  on the dome's flanks or tip end a smaller patch round itself) and its requests
  carry 1 %: `library_write.py` composes a Library request as readOptions
  sends it after the select (`page_options(curved=True)`,
  `part_options()`; `stretch_problem()` refuses another budget), where it
  had refused a doubly curved face; `build_static_site.py` the same.  1,
  1.5, 2 and 2.5 mm: 26 x 15 (332 taxels), 18 x 10 (146), 13 x 8 (82), 11 x
  6 (52), symmetric and centred, the tails toward the finger's root (the
  disks at 0.3 % gave 110, 49, 28, 18); 3 mm keeps every rule too (35), not
  offered (a fifth pitch would end the heading's "each fitted at four
  pitches"; Open items).  The card between the Dex1-1 and the LEAP Hand: 18
  cards, "Grippers. Eighteen, each fitted at four pitches.", 102 sensors.
  The scene with the larger boards keeps every rule (`extra_seen` 1, the
  stacks 118 to 124 px apart, clearances beyond 12 mm); the card's top FPC
  19 px at every pitch, so the hand's override is `card_min_px` 19 (14
  with the disks).  Its four sensors shot (`library_shots --only`); the 98
  others' fits, entries, records and pictures the same bytes
  (`library_write --check` 102 current; `library_shots --check` on the
  four and three others 0 differing).  Budgets raised with a dated note
  (29.2, 8.9, 8.3, 1.02 MB).  `test_library`'s
  `test_no_library_face_is_doubly_curved` is now
  `test_a_doubly_curved_face_is_sent_at_the_curved_limit` (1366 tests),
  `UNITREE_DEX3` 8 mutants and `S/library-flat-unread`,
  `S/library-curved-unchecked` re-anchored (1307), each killed alone by
  `test_library`.  [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The
  Unitree Dex3-1", docs/CAD_MODE.md **The Library's Dex3-1 back on its
  dome**.  Screenshots: `library-look-work/look/out/dex3-back/`.
  Its review (sound-with-fixes, six findings) and its fixes (`5e47361`,
  `32352a0`, `435de9f`, `478ba2b` and the documents): a click inside the
  dome's patch (its middle band, within about 6 mm of the mid-plane, to
  about 45 mm out) selects the 405.1 mm2, one on its flanks or tip end a
  smaller patch round itself (`stretch_region`'s step 3; 152.9 mm2 from
  facet 11794, now in `test_library`), where the documents had said any
  click; the pose is `bff728c`'s, surveyed against the disks' normal (8.28
  degrees): the thumb's pad faces the dome patch's within 16.2, the gap
  76.0 mm (the builder's comments, LIBRARY_VIEW.md); the card override's
  reason in the scene's `about`, "the rules' 20 only in a hand no longer
  open" (the compact pose about 20 px; it had said 20 was out of reach),
  only the `about` changed (`--only unitree-dex3`, `library_split.py`; the
  four sensors shot again, their pictures and art the same bytes, the
  records' `scene_sha256` new); stale comments (the fixture's notice,
  `mutation_check.py`'s `HAND_MECHANISM`, `test_surface_web`, `cad_checks`,
  `select.py`'s `DOUBLY_CURVED_SR`).  3 mm left to the user (Open items).
  Its verification (`478ba2b`, the documents' commits after it): the full
  suite, 1366 on 3.12 in 877 s and on 3.10 in 1068 s; `mutation_check
  --check` 1307, and the 25 mutants of `UNITREE_DEX3`, `HAND_MECHANISM` and
  `CURVED`'s two re-anchored each killed alone by `test_library`;
  `library_write --check` 102 current, `library_split`, `library_showcase`
  and `flexitac_downloads --check`; `library_shots --check` 102 of 102 0
  differing, `--showcase --check` and `--check-generator` (30) the same;
  `library_checks` 425 of 425, `cad_checks` 494 of 494, `theme_checks` 133
  of 133; the static site (62.1 MiB, 102 sensors current) and
  `static_checks --site` 57 of 57; `export_public.py` into a scratch clone
  (not pushed) and that copy's suite, 1366 in 842 s on 3.12, 21 skipped
  (the files it leaves out, as before).  Screenshots replaced.

## Audit issue status

The status of each finding as its fix stage reported it after an
independent review and a repair round; stage T re-checked them through the
full suite and the mutation catalogue (which re-introduces the audit's
defects), not by re-auditing each one.  The final review of 2026-10-15
rates H4, M6, M9, M12, M14, L1, L7 and L13 only partly fixed (section 9.2 of
[the audit report](verification/2026-10-12-audit-report.md)).

| Issue | Status | Where |
| --- | --- | --- |
| C1 contact pads exported off-centre | fixed | exporter 0.1.1/0.2.0; read-back tests |
| C2 Column electrodes at the outline | fixed | 0.75 mm margin below the field, copper-to-outline DRC (E) |
| C3 tails do not fit the reader connectors | fixed | (P + 1) x 0.5 mm tails, 0.3 x 4.0 mm contacts, NC contacts, `connector.*_pins` (E); the default Row tail stays 12 positions (see open items) |
| H1 most of the pitch range infeasible | fixed | scaled tapers, feasibility errors with field bounds (E) |
| H2 previews mirrored | fixed | copper-side SVG top views (A), browser registration and pin-1 ring (F) |
| H3 0.2 mm copper-to-edge rule | fixed | 0.3 mm for all copper and slots, profile checked against JLC (E) |
| H4 tests blind to geometry | fixed | read-back, golden, chirality, negative DRC flow, HTTP and CLI tests, mutation check (A, X, T) |
| H5 verification gates missing | fixed | whole-board DRC, 30 records per board plus registration (E; `route_width` since 2026-10-15) |
| H6 unknown fields silently dropped | fixed | strict normalization, `E_UNKNOWN_FIELD`, normalization report (A) |
| M1 stiffener outside the outline | fixed | fixed 6.0 mm connector zone, flush (E) |
| M2 V-notch at the tail root | fixed | monotone hull, rolling-circle fillets, neck rule (E) |
| M3 assembly preview order and offset | fixed | top board upper, turned over about its tail axis (F) |
| M4 stale results downloadable | fixed | stale banner, downloads disabled (F) |
| M5 integration semantics undefined | fixed | monotonic pins, pinout and netlist (E, X), [INTEGRATION.md](../docs/INTEGRATION.md) (T) |
| M6 provenance and identity | fixed | identity over design, profile and versions (A); complete bundle, build-id names (X) |
| M7 profile not the single source | fixed | rules in the profile, profile checks, stiffeners from objects (E, X) |
| M8 vertex-normal offset | fixed | true offset with round joins (E) |
| M9 no width or size limits | fixed | 0.1016 mm electrodes (JLC's 1 oz minimum since 2026-10-15; re-audit N4), 234 x 490 mm boards (E) |
| M10 no netlist | fixed | `netlist.ipc`, `pinout.csv` (X); X2 object attributes not written |
| M11 two anchor meanings | fixed | anchored rectangles, layout v2 (E), [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md) (T) |
| M12 documents overclaim | fixed | documents rewritten; their tables, snippets and the quoted figures listed in `tests/test_docs_consistency.py` are checked there (prose without figures is not) (T) |
| M13 no observability | fixed | zoom and pan, DRC panel, failure clearing (F) |
| M14 not agent-ready | fixed | JSON Schema, `/api/validate`, compact view, CLI (A) |
| L1 / L2 HTTP robustness and origin | fixed | (A) |
| L3 validation edges | fixed | (A, F) |
| L4 0.005 mm tolerance | fixed | 1e-6 mm epsilon only (E) |
| L5 single-lane fan-out too wide | fixed | (E) |
| L6 coverlay bridges | fixed | merged windows, bridge rule (E) |
| L7 reference-design differences | partly | electrode overhang done (E); contact-zone thickness: 0.1 mm PI default since 2026-11-06, the 2-layer 0.2 mm FPC + 0.1 mm, the 0.3 mm gold fingers by JLC's rule (G: 0.225 mm from 2026-10-14); 0.6 mm electrodes and slits open (D8) |
| L8 / L9 / L10 exporter input, X2, ZIP bytes | fixed | (X) |
| L11 performance | fixed | sort-and-sweep DRC (E), build cache, no duplicated layout (A) |
| L12 UI details | fixed | (F) |
| L13 development hygiene | fixed | `pyproject.toml`, CI (suite on 3.9 and 3.12, catalogue check, manual mutation run of the mutants named), links and paths, `outputs/`, `tools/`, the test map; no lint step (T) |
| I1 no alignment features | open | product decision D8 |
| I2 no canonical 12 x 32 template | open | product decision D8 |
| I3, I4 | information | PCB-Agent-Teams is unrelated; the reader BOM's LCSC number needs an external check |
| I5 DRC counters | fixed | exact counters (E) |

## Architecture

```text
browser (web/) --HTTP--> app.py --+
                         cli.py --+--> engine.generate_design(data, cache=BuildCache)
                 Python callers --+      1 load_profile()               profile checked on every load
                                         2 _normalize_design()          strict keys, aliases, 1e-6 mm grid
                                         3 validate_design()            input rules, profile, feasibility
                                         4 _identity()                  design/profile digests, versions, build id
                                         5 _build_boards()              cached by build_sha256
                                             build_row_board, build_column_board   canonical frame, tail down
                                             apply_tail_side            whole-board quarter turns, origin at 0,0
                                             apply_physical_assignment  top/bottom from role_mapping
                                             verify_board x2 (with the design's routing), verify_registration  whole-board DRC
                                             _svg_for_board             copper-side top views
                                         6 _manifest()
                               --> exporters.build_exports(result, cache=)
                                         checks, regeneration binding, write, read-back, ZIPs
```

| Path | Responsibility |
| --- | --- |
| `app.py` | stdlib HTTP server: routes, request rules and limits, security headers, generation semaphore and build cache, `profile_for_ui()` / `display_rules()`; the routes' answers without HTTP (`answer()`, `Reply`), which the static site runs in the browser; the two pages (`PAGES`: `/`, `/index.html` and, since 2026-11-05, `/library.html`) with the header's counts; since 2026-11-16 (the Library the first page) `/` and `/index.html` the Library, `/gen.html` the generator, `/library.html` the forwarding page (no header: sent as it is, by its name, `FORWARD_PAGE`, since the review of 2026-11-16) |
| `cli.py` | `schema`, `validate`, `generate [--compact]`, `export --out DIR`, batches |
| `engine/__init__.py` | the public API |
| `engine/core.py` | orchestration, normalization and aliases, input validation, identity and manifest, `BuildCache`, `result_view`, SVG top views (with polygon windows and `data-active-outline` on masked boards); the optional surface fields `matrix.mask` and `routing.row_sides` (E_ROW_SIDES, E_ROW_BUS_TAILS for opposite tails, the identity extra `row_bus`, E_ROW_BUS_INFEASIBLE from the build); `rules_template(design)`, the template whose profile builds a design (the surface template for every bus design on either template, the plan's section 20), the defaulted bottom tail of the generic template (7.5 mm for the bus, 7 mm for the straight channel) |
| `engine/schema.py` | issue catalogue, field specs and form limits, JSON Schema, strict JSON loader |
| `engine/layout.py` | Row and Column plans and geometry (bundles, bus-style bends, tail and fan-out route pieces), contacts, openings, stiffener, rotation, assignment, metrics, feasibility errors, the field mask's frames and construction classes, and the masked boards' straight constructions (`masked_row_plan`, `masked_column_plan`, polygon field windows); both builders hand a `routing.row_sides` design to `engine/diagonal.py` first, and `mask_class` gives it `{row: diagonal, column: straight}`; `field_footprint` and `E_BOARD_SIZE` measure a diagonal Row bus on its built boards (phase P5d), the size advice modelled on the straight plans and verified on the bus |
| `engine/drc.py` | whole-board DRC (30 records) and cross-board registration; on masked boards records 11-15 measure the crossing region and the polygon windows (the strict window-to-trace rule), and a masked pair is registered in the stack frame (`stack_frame`: crossings against the mask, inactive separation, the masked grid, and the reported trace-over-trace runs, `trace_overlap_*`); a diagonal-bus board (`construction.row_bus`) is masked whatever it carries (the gate), and a diagonal-bus pair adds the stack keys (traces over the other board's electrodes or its field window, the union of its electrode openings; the tail gap and each tail to the other board, 1.0 mm; E_REGISTRATION, and W_STACK_TRACE_WINDOW at close windows; crossings and runs outside the field reported only, since the plan's section 12) |
| `engine/geometry.py` | stdlib geometry: anchors, rounding to the grid, offsets, fillets, distances, orthogonally convex unions (bands, fillers, slabs, rings) |
| `engine/bus.py` | the diagonal Row bus's primitives in integer nanometres (masked-field phase P5a): the west convex chain (exact orientation), the mitred offset (slanted segments 2 nm farther, rounded away from the chain), a lane's keep-out (its continuation and a box around its start; at a lane's inward turn, following a receding field, its offset cut on the vertical one pitch out, `lane_offset`), whether a segment enters an open box (exact, for the lanes turned down on the field's edge), boxes and the mirror |
| `engine/diagonal.py` | the diagonal Row bus `diagonal-bus/11` behind `routing.row_sides` on both templates, built with the surface profile's rules (`engine.core.rules_template`; the plan's section 20: the rectangular generator's bus is CAD mode's) (phase P5b, the tail redesign of the plan's section 12, the stacked tails of section 13, the one outline over the field of section 14, extended down to the tail roots in section 20, the regular outlines of section 15: no outline vertex turning by under 5 degrees but on a fillet or the tail, `_regular`, a flatter run one straight edge outside it; the chamfered notches of section 16, `_hull_sides`; the straight sides of section 17, `_straight_sides`: each side from the tip corner down to its widest point one line where one encloses it within `SIDE_STRAIGHTEN_MM`, 1.0 mm; the convex sides of section 24, `_convex_sides`: elsewhere that stretch its convex hull, each dent no deeper than a two-cell step, 2 p / sqrt 5, bridged): the Row frame (mirrored for the one-sided bus opposite ROW_01's side), the bands (diagonal-bus/1's onion around the windows, no Column copper in its keep-out, each lane of a receding field following it inward to its bottom edge, the convex hull of what it avoids, at the bundle pitch and no flatter than the taper cap; every lane turned down on the field's bottom edge where its band crosses it or just outside the Column windows' keep-out, `_cut_at_field`; the bottom row's corner raised before the onion only where that fails, none measured), lane starts, the Row tail (centred on the field in every side mode, as the Column tail, the plan's section 27: with both the funnel, one side fanning in under the field, the rows at the tail's positions 1..R, mirrored at its far end; one side's inner flank slanting out below F's bottom to a tail wider than F's bottom; its root just below the fans' junctions), the staggered fans (a run per side and way, at the cap that roots the tail highest, off the Column entry angle by 5 degrees; their clash check), the folded contact order, the Column board (the straight one of the same design without `routing.row_sides`, `layout._masked_column_board` on the design with its mask written out: its tail centred, the tails stacked, `TAILS`; one lane straight into its contacts, its V at most `COLUMN_V_CAP_DEG`, 80 degrees, where that roots the tails no deeper than the profile's own caps, `column_profile`, `_column_plan`), the y-monotone outline, the one outline down to the tail roots (`_build`: the deeper of the two boards' own roots lowered below the union's fillets into the tails, `_lowered` moving the Column root down to it; `_own_rings`, `_share_outline`: both boards' own outlines before their fillets united in the stack, made regular, straight sides, filleted once (a vertex turning under 4 micro-radians kept: its fillet is ill-conditioned and sub-grid); each board the shared path and its own tail, `_spliced`; checked to coincide), `construction.row_bus` and its measurements on the published outline (the flat lanes, the relative narrow tip, the shared level); with one side the flank without lanes convex from the field's outline corner down to the tail (`_convex_flank`, the plan's section 27.8: the Column fan-out's notch below that corner bridged, every corner 5 degrees or more, the tails' roots and the copper untouched); the pair is built once per design (a small cache) |
| `engine/profile.py` | profile loading and consistency checks (the `order` block included), `fabrication_minimum()` (JLC's trace minimum of the profile's copper), `order_requirements()` |
| `profiles/jlc_fpc_standard_v1.json` | the locked profile, with its JLCPCB, connector and reference sources |
| `exporters/direct_gerber.py` | Direct Gerber ZIPs with `ORDER_NOTES.txt`, review bundle, regeneration binding, read-back; for masked builds (masked-field phase P3) the polygon field window as a GTS region, the form checks of polygon openings, the taxel-field order note, `taxels.csv` and the review manifest's `taxel_map`, all read back; for a diagonal Row bus (phase P5c) `taxels.csv` always (every position active without a mask, and then no taxel-field note), the folded Row pins from the pads, and the review manifest's `diagonal_row_bus` (`construction.row_bus`, `tail.row_contact_order` with the pins of those contacts, its stacked tails since diagonal-bus/3) read back against `pinout.csv`; since P5d the Row board's `ORDER_NOTES.txt` states its folded pins, read back ("one side" for a one-sided bus since the P5d/P5e repair) |
| `exporters/ipc356.py` | IPC-D-356A writer and strict reader |
| `exporters/easyeda_pro.py` | the EasyEDA Pro projects ([EASYEDA_EXPORT.md](../docs/EASYEDA_EXPORT.md)): one native `.epro2` per board in a separate `{build_id}-easyeda-pro.zip` (route `/api/export/easyeda-pro`): tracks, `RECT` pads with their nets through archive-local footprints, devices and a schematic channel, coverlay `FILL`s on layer 5, the outline and cutouts on layer 11, `FPC_FILL` PI stiffeners on layer 59 with the profile's thickness, FPC mode, the board's own DRC rules; the environment records of the user's JLCEDA exports (`easyeda_pro_template.json`); read back against the layout; `tools/compare_easyeda_gerbers.py` compares EasyEDA's Gerbers with ours |
| `web/gen.html` (`web/index.html` until 2026-11-16), `web/app.js`, `web/styles.css`, `web/theme.css` | the browser UI (no framework); `theme.css`, linked once after `styles.css` (left unchanged; each theme rule repeats the selector it overrides), is the page's Apple-style look (2026-11-04), light for every visitor whatever the system's scheme and dark on the header's toggle (the user's request of 2026-11-06: `web/theme.js`, loaded by both pages in `<head>` before the style sheets and without defer, sets `<html data-theme>` from the visitor's choice in `localStorage` before the first paint; every dark rule hangs on it through a zero-specificity `:where()`, so the dark look is the one the system's dark scheme gave; the toggle `#themeToggle`, a moon or a sun, right before the GitHub card on both pages, the community's pill and round; where the header's line had no room, Discord's mark alone from 601 to 630 and from 1101 to 1220 px and the three circles up to 410 px, 44, 40, 36 or 32 px as the line leaves room for: the review of 2026-11-06), the drawings' areas light lightboxes in either, the system fonts, motion only as feedback to the pointer and the keyboard and none under reduced motion (`tests/test_web_theme.py`, `tools/browser/theme_checks.py`); `app.js` dispatches `fpc:result` / `fpc:cleared` for CAD mode; the form's Row traces select (`routing.row_sides`, shown and sent on both templates; on the generic template the form's bounds, badge and locked rules follow it: the bus's rule set, `profile.row_bus`, or the straight channel's own bounds, each limit's `channel`); the stacked view's pin-1 rings in the boards' colours, moved apart where they would clash, each still round its own triangle (P5-diagonal-bus.md sections 27.3-27.5), both drawn above both boards in an overlay (section 27.8), each as its board's ring lies on screen (section 27.9); the masked badge for a masked field only (not a bus's full field); since 2026-11-05 the stacked card's second figure in Gen by Surface, the sensor on the part (`index.html` `.stack-figures`: the registration and `#sensorOnPart`, a second `.stacked-canvas` lightbox, side by side where the card is 720 px wide or more, a container query on the card in that mode only), and `app.js`'s answer to `fpc:board-art`: each board's copper and polyimide sides as standalone SVGs in the page's look (`lookCss` inlines the look's rules of `styles.css`, the paints of `.look-defs` copied in); and the 3D views' light (2026-11-05, the user's "the new light on every 3D view"): the board cards' oblique views and the stacked view's exploded figure in the sensor on the part's lights and coverlay (`app.js` `lightBoard`, `lightView`, its numbers copied from `web/cad/studio.js` (the lights and the studio, shared with the 3D view since the merge of 2026-11-05) and `web/cad/onpart.js` (the coverlay, the edge bands) and kept equal by `test_surface_web`), each board's side shaded by the way it faces the viewer-fixed lights (unchanged at the stacked view's home) under a faint satin sweep that slides as the view turns, its walls lit by the way they face, its shadow cast away from the key on screen whatever the turn; leaves of the 3D context over each side (its outline less its cutouts, nothing painted outside the board) and a shadow leaf moved and faded, so a turn draws no art again; the plan view unlit; since the user's request of 2026-11-15 the FlexiTac team's footer at the bottom of both modes (`index.html` `footer.site-footer`, `theme.css` section 15: Awesome-FlexiTac's footer word for word, the team's site, GitHub, Discord, YouTube and the mail, on the header's bar under a hairline, light and dark), the Library's the same block byte for byte; with it Gen by Surface's guide (`main.js` `goTo`, `workEnd`) takes `<main>`'s end where it took the page's: its scrolls stop there (`scrollIntoView`'s start would have pushed the sticky guide up into the footer's room) and its last step is lit there, so the guide behaves as before the footer |
| `web/forward.js`, `web/library.html` | the first page (the user's decisions of 2026-11-15 and 2026-11-16: "是的 be first page"; [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The first page"): the Library is `index.html` at `./`, the generator `gen.html`; `forward.js`, the first script of the Library's `<head>` and of `library.html` (now a forwarding page with a plain link to `./`), sends the addresses of before on with `location.replace`, their query and hash kept, before anything paints (the page hidden by `visibility`, `<html data-forward>`, on which `library.js` does nothing): on the Library a query naming `GEN_KEYS` (`part`, `sample`, `debug`) or a hash of `GEN_HASHES` (`#rect`, `#cad`, `#drc-row`, `#drc-column`, `#maskNote`) to `gen.html`, on `library.html` everything to `./` (`library.html#<id>` to `./#<id>`) or a generator's address straight to `gen.html`; the Library's own addresses (its ids and places, `?probe`) stay (`test_library`'s `FirstPageTests`, `library_checks.py` and `static_checks.py`'s `part_first_page`); since its review of 2026-11-16 also at the open Library's `hashchange` (`./#rect` typed over `./`; `library.js`'s `route()` idle on a page being sent on) and a Library shown again by the back-forward cache shown; and since then the showcase's card's "Design your own" (`library.js` `showcaseCard()`, `.lib-design`: after Details, `gen.html` in this tab, the action blue's dated second use; `DesignYourOwnTests`, `showcase_checks.py` `part_page`) |
| `web/backend.js`, `web/py/`, `web/counts.js` | the page's one door to the API, `apiFetch` (`fetch` under `app.py`; in the static site a Web Worker, `py/worker.js`, running `app.answer` in Pyodide through `py/bridge.py`); `counts.js` (the review of 2026-11-16, out of `backend.js`, which the Library does not load): the header's star and fork counts refreshed from GitHub's API on the static site's two pages, the Library's (the first page) and the generator's, kept for an hour per tab (`app.py`'s pages carry the server's and ask nothing) |
| `web/cad/` | CAD mode in the browser (ES modules): mode switch, steps, `/api/surface/*` calls, the three.js viewer and picking, STL parsing for display; the Containment and Row traces selects (phase P5e: Field only, the default; no Field shape, Board rules or Largest rectangle since the plan's section 26.16: the field follows the selected area), the proposal card (tip, bands, the Row pins by pin, where the tails end, each board's share on the surface, overhang), the Tip column, the flat view's boards dotted off the surface, large dark markers where a board leaves the surface in 3D and a note under the view, the map's routing report with its advice and the Row pins by pin; since the P5d/P5e repair a changed option makes the proposals stale (Generate waits for a new fit), one map request at a time, the disabled controls' reasons, the CSV's readout rows for a masked field only, the shortfall of proposals explained; the sensor on the part (2026-11-05, `main.js` section 7b): `drape.js` (pure: each board a grid over its SVG's view box carried through `board_outlines_base`'s formulas, the placement's field frame and the fit's chart onto the part, flat on the nearest boundary facet's plane beyond it, the film over the field or its masked outline, exploded rigidly along the field's mean normal or, on a chart turning more than 60 degrees, along the normals; the framing and the checks' metrics against the map) and `onpart.js` (three.js, one transparent renderer for the page, the art rasterised through `data:` URLs onto both sides of each sheet, its alpha test as coverage (antialiased outlines) whose alpha never lowers what lies behind an outline (no seam of the pane's grey round it), the part in a matte light grey (the 3D view's darkened a little), with lights, a studio and materials of its own since its look of 2026-11-05 (a product shot's lights hung on the camera, a studio built in code and prefiltered by `PMREMGenerator` that the film and the boards mirror, none without half-float render targets with one warning, Khronos PBR Neutral tone mapping, the film a satin black, the boards' reflection tinted by their art, an edge band round each layer, in Assembled a contact shade baked once per drawing and no film face; its lights, studio, tone mapping and warnings in `studio.js` since 2026-11-05, which the 3D view draws in too), framed whole up to three times the sheets' radius with the same margin on both sides of the axis that binds, opening exploded as the left figure opens (the user's decision of 2026-11-05: `drape.js`'s `HOME_TILT_DEG` and `HOME_SPIN_DEG`, `app.js`'s `ORBIT_HOME`, the camera's up the stack's normal) and assembled at the same spin 35 degrees off the normal, turned with the mouse about the stack's normal and tilted as the left figure (a grab cursor), the arrow keys as the left figure's and Reset view over its top right, its Exploded | Assembled over its top left and the pane's top 40 px kept for them (2026-11-06), on demand only; its pixels read and the drape compared with the map with `?probe` only, the review of 2026-11-05 and its second), drawn from the map of the shown build with no request of its own, reported as `on_part` in `#cadState`; the 3D view in the same light since the user's request of 2026-11-05 (`studio.js`: the studio's lights, its reflections only and Khronos PBR Neutral on the part, its facets' meaning colours lifted 1.3 times, every marker unlit in its own colour, the studio made once a renderer and again for a restored context, its reads with `?probe` only, answering `fpc:view-look`; on a software renderer a drag's frames drawn with the part's diffuse light alone) |
| `web/vendor/three/` | vendored three.js 0.186.1 (MIT): `three.module.js`, `three.core.js`, `OrbitControls.js` (its bare import patched), `LICENSE`, `NOTICE.md` with the SHA-256 of each file |
| `web/vendor/ufactory-g1/` | the Library's showcase's gripper (2026-11-12): twelve meshes of UFACTORY's "Gripper G1 3D File", split and decimated within 0.1 mm by `tools/library_showcase.py` with `tools/mesh_decimate.py`, and `NOTICE.md` (UFACTORY's property, used with the project owner's decision of 2026-11-12, not covered by the repository's Apache-2.0 licence; "3D model", never "CAD"); a budget of its own, 2.2 MB, outside the Library's 12 MB; `tools/library_write.py` `showcase()` holds the folder to exactly those files at their pinned SHA-256 and refuses a byte copy of one of them, or of the undecimated file, anywhere else under `web/` |
| `web/vendor/flexitac-v2/` | the showcase's sensor (2026-11-12): the original hand-designed FlexiTac V2 pad, 12 x 32 taxels at 2 mm: `geometry.json` (its two FPCs read from the official Gerbers by `tools/flexitac_v2.py`), `art.json.gz` (the art of its two boards, of no build, by `tools/browser/flexitac_v2_art.py`), `umi-finray.placed.json` (where it lies on the UMI finger: a placed record, its tails wrapped round the finger's side to its back by `web/cad/drape.js`) and `NOTICE.md` (CC BY-NC 4.0, Columbia University: not free for commercial use, as README's License says); exactly these four files (`tests/test_showcase.py`) |
| `web/index.html` (`web/library.html` until 2026-11-16), `web/library.js`, `web/library.css` | the Library (2026-11-05): a page of its own laid out as the Apple Store, by gripper (the title and its line; since the user's requests of 2026-11-06 no tile and no "Start here.": the grippers' section first, one card per gripper but the UMI finger, four to a row from 735 px and two below, each its range ("1 to 3 mm") and "Pick your pitch", opening its 2 mm sensor whose Pitch offers the others, at `#gripper-<part>`, then the UMI finger's shelf, cards that scroll sideways inside it; the older `#shelf-<gripper>` lands on the card, `#shelf-start` at the top; Back and Forward put the grid back where it was; a family, the UMI finger's tapered tips, one card closing its shelf, its page at `#umi-tapers` with Shape and Tip width as segmented controls in place of the pitch), and a sensor's own page at `#<id>` (since the user's request of 2026-11-15, "after we click for all cards to details, we may not jump to a new page. lets bump our to a large window, and if you click the "x" of right top conrner, it will close and back show lib", in a large window over the grid: `dialog#libWindow` opened with `showModal()`, up to 1200 px wide and the window's height less the gutters, its page scrolling inside it (two even columns from 900 px), a sheet below 735 px and on a screen less than 501 px tall, the grid where it was under it, dimmed, the page not scrolling (a scroll bar's width made up on its right); its X at its top right, Escape (Android's Back too) and a press and release on the backdrop (never a double-click's second click) closing it to the grid's place of its sensor (the back link's of before, which is gone) with the card that opened it focused, with no new history entry since its review of 2026-11-15 (opened from the grid it goes back over the window's entries, opened at its own address it replaces its entry: a new entry had made Android's Back close it and open it again for ever); the address `#<id>` as before, so Back closes it and Forward opens it again; `docs/LIBRARY_VIEW.md` "The details window"; its facts, the pitch as a segmented control, Open in Gen by Surface at `gen.html?part=<id>` (`./?part=<id>` until 2026-11-16), its Top and Bottom FPC Gerber ZIPs: the site's prebuilt files or `app.py`'s exports, the part's STL and licence); no engine or Pyodide, and three.js on a sensor's page only (its 3D view, the user's request of 2026-11-05, "lib 点进去具体的每个夹爪的时候, 那个图也做成可以三维旋转的": the picture first, then the same scene drawn over it by `web/cad/library_view.js` with Gen by Surface's figure, `web/cad/onpart.js`, and for a gripper the whole gripper by `web/cad/library_stage.js`, turned by a drag or the arrow keys, its mode the Exploded | Assembled switch's, from the files `entries.json`'s `view` names; the picture kept without one, without WebGL or when a file fails; `docs/LIBRARY_VIEW.md`); every picture one 16:10 slot (`slot()`: the sensor's picture once `entries.json`'s `image` names one, the generator's on-part figure on a transparent ground in `web/library/shots/` (the pictures' contract of 2026-11-05 with `tools/library_write.py` and the shots tool: a card the Exploded card file, 640 x 400, lazy, decoded async and sized, its alt the entry's; a sensor's page the Exploded or the Assembled picture, 1280 x 800, with a grey Exploded | Assembled control under it, `gallery()`, the view kept across the pitch, Shape and Tip width), else, or when its file does not load, a drawing of its field; a sensor's page's 3:1 below 900 px, so Open is in a 390 x 844 phone's first screen on every sensor's page, the user's decision of 2026-11-05); each shelf heading in one wording (`<gripper>. Four pitches, 1 to 3 mm.`, the UMI's `, and tapered tips` after the range; `tools/library_write.py` `shelf()`; the grippers' section's heading, `Grippers. <count>, each fitted at four pitches.` (the count the cards', a word to twelve and its digits past: `19` since the merge of the Library's lines of 2026-11-17)); the header is the generator's (`gen.html`, `index.html` until 2026-11-16) with the modes as links; the generator's header links it in the same tab since the user's request of 2026-11-15 ("从gen by surface跳到lib,会重开一个页面，这个改掉，改成直接跳过去 不重开页面": a new tab before; leaving the generator for it leaves the generator's page as any link does, a loaded model and a generated sensor with it, and so does step 1's file note's link to it) (`.masthead-library`, dated blocks in `styles.css` and `theme.css`); `web/cad/main.js` opens `gen.html?part=<id>` (`./?part=<id>` until 2026-11-16, forwarded there since; `libraryPart`, `applyLibraryOptions`, `leaveLibrary`, the file note); since 2026-11-12 the showcase first, above the grippers' section (`showcaseOf()`, `showcaseCard()`: one large 4:5 card, "FlexiTac on xArm", labelled "Original FlexiTac · Hand-designed, pre-agent" (until 2026-11-15 "Hand-designed, not auto-generated"), from `library/showcase.json`; since 2026-11-15 no link itself: its smaller picture and its Details pill open the page; without that file the Library is the one of before), which opens its own page at `#flexitac-g1` with the same 3D view (the placed record and the showcase's scene, opening on Assembled; in the window too since 2026-11-15), the FlexiTac hardware tutorial's link for the Gerbers and no download of the generator's (`tests/test_library.py`, `tools/browser/library_checks.py`, `tools/browser/showcase_checks.py`); since 2026-11-15 the FlexiTac team's footer (`index.html`'s main block byte for byte) closes the page, the Library's fine print (the makers' trademarks, its sources and licences) its first row, hidden with the grid's title while a window's own address loads; since the user's request of 2026-11-15 ("箭头能不能做成像schetchfab一样的动画") the 3D view's drag hint (`library.js` `dragHint`, `.lib-drag`; [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md)): Sketchfab's hint drawn for the page, a hand between two arrows (one white cursor edged in ink) over "Drag to rotate" at the view's bottom centre, sized by the view's height (a size container; since its review of 2026-11-15, not the window's width), swaying while shown and faded out at the visitor's first use of the view on its page (a mouse's main button pressed, a turning key, a double click, a touch's turn; never a phone's scrolling swipe or a right click), the page's one motion of its own, off under reduced motion |
| `web/library/` | the Library's data (2026-11-05): `parts.json` (each gripper part's mesh, licence, the face the page selects and its variants; hand-maintained, written once by the private `tools/library_import.py` from the multi-gripper video's recipes), the gripper meshes (eight since the Robotiq 2F-85 of 2026-11-16: `meshes/`, unchanged but Franka's convex hull and the Seeed reBot DevArm's finger, whose contact face's pockets are capped, written by the private `tools/library_scenes.py` (`PART_MESHES`) since 2026-11-17) and the UMI finger's 26 tapered tips (`meshes/umi-<kind>-tip<w>.stl`, the family `umi-tapers`, since 2026-11-16 one card per shape: the last 40 mm a trapezoid or a convex arc, the last 75 mm a convex arc, a trapezoid or a concave arc, tips 21.8 to 5.8 mm, and the pointed tip over 50 mm to 2 mm; ten until then, the 75 mm trapezoid and convex arc; cut from the HandUMI mesh of `web/vendor/umi/` by the private `tools/library_tips.py`, which needs trimesh and manifold3d and also writes their parts and the family into `parts.json`) and their licence texts (`licenses/`) with `NOTICE.md` (sources at pinned commits, SHA-256, the modified files stated), and `tools/library_write.py`'s `fits/<id>.json` (the request the page sends and the engine's reply) and `entries.json` (the index the Library, `index.html` since 2026-11-16, and Gen by Surface's `gen.html?part=<id>` read; each sensor's `image` from `shots/manifest.json`), and the sensors' pictures (`shots/`, the user's request of 2026-11-05: the cards show the finger with the sensor on it; shot by `tools/browser/library_shots.py` from Gen by Surface's sensor on the part at its Exploded and Assembled homes, WebP with alpha at 1280 x 800 and a 640 x 400 card, with `manifest.json`: each file's bytes and SHA-256, the fit and build id shot, the hash of the figure's sources; the set of all 42 sensors shot once on 2026-11-05 with the approved look, each drawing centred in its picture: 126 files, 3.46 MB, the grid's eight "Start here." cards 0.15 MB; shot again by the shoot of 2026-11-06 from the Library's own 3D view, one stack exploded, at fill 0.5: 126 files, 3.50 MB, the grid's 12 cards since that day's layout, all asked for as the page opens, 0.24 MB; every sensor's required by `test_library` and `tools/library_write.py --check`); 42 sensors: 32 of the grippers, 1 to 4 mm pitch, and the 10 tips at 2 mm (58 since the UMI finger's shapes of 2026-11-16: the 26 tips of `meshes/umi-<kind>-tip<w>.stl`, the short trapezoid and convex arc over 40 mm, the concave arc over 75 mm and the pointed tip over 50 mm added, the family's cards one per shape on the UMI shelf; 174 pictures, 4.74 MB, the grid's 13 cards; `web/library/` without its pictures 16.41 MB); and the 3D view's files (the user's requests of 2026-11-05, `docs/LIBRARY_VIEW.md`): each sensor's art (`art/<id>.json.gz`, the generator's art of its two boards, written by the shots tool), the grippers' scenes (`scenes/scenes.json` with the approved rules, Exploded 65 and Assembled 57 degrees off the face and the 0.28 see-through, and `scenes/<part>.json`: every gripper whole (the sixteen grippers and the two hands, the Unitree Dex3-1 and the LEAP Hand, since the Dex3-1 came back on 2026-11-18; the sixteen and the LEAP Hand from the Allegro Hand's and the Dex3-1's removal on 2026-11-17; the three hands at the merge that day), both fingers (a hand's every finger), the jaws fully open, the other finger turned or mirrored, the near finger see-through on every gripper, in both views; one stack exploded (the sensor finger's), gap share 0.42: the user's decision of 2026-11-06) and their bodies (`bodies/<part>/`, the grippers' open models decimated, each tabled in `NOTICE.md`; the MakerMods tips on a rail of the project's own, `bodies/makermods-metal/rail.stl`, no MakerMods body), written by the private `tools/library_scenes.py`, checked by `tools/library_write.py` `scenes()` (`tests/test_library.py`); since the realistic look of 2026-11-12/13 (`docs/LIBRARY_VIEW.md` "The looks"): every gripper's components in looks after photos of the real product (`tools/library_looks/<part>.json`: the base looks of `tools/library_looks/base.json` by name, each part's own with its evidence; its bodies shared out into component files and the few plain shapes the photos show and a model lacks drawn by the project, `bodies/<part>/drawn-<name>.stl`, each a component with its look, by the public `tools/library_split.py`, which writes the scene's `looks`, `part_look`, `smooth_deg` and the bodies' looks and `NOTICE.md`'s rows; the bodies 2.45 of 2.5 MB after stage 2), the rules' `looks` and `part_looks` (the UMI finger and its tapered tips in the real finger's orange TPU, `umi-tpu-orange`; a record's `part_look_sha256`), and the showcase (`showcase.json`, written by hand but for its `placed`, `image` and `shot`; `showcase/` with its three pictures; `scenes/flexitac-g1.json` and `bodies/flexitac-g1/`, the holder and the shapes the project draws, written by `tools/library_showcase.py`; the vendor's meshes in `web/vendor/ufactory-g1/`, the pad in `web/vendor/flexitac-v2/`) |
| `surface/` | CAD mode (stdlib): `mesh` (STL, weld, orientation, covered walls), `select` (replayable operations, presets), `chart` and `solve` (projection, rigid unfold, band seam, LSCM+ARAP), `fit` (base sides, rotation, raster search on the engine's plans, strain-limited disks), `fill` (Whole board's masked fields (CAD mode's only shape since the plan's section 26.16, which removed `shape: rectangle`, the generic template and the rectangle preference from CAD mode; `fit.CAD_ONLY`): masked fields of the straight construction classes, within the rectangles' caps (`max_rows` x `max_columns`; 32 x 32 before the plan's section 21) and a named reader's lines, on an exact free space, each role mapping searched on its own and the lattices independent of the placement option, merged with the rectangles, peeled and re-ranked, one mask per readout and no dominated proposal; masked-field phase P4 and its reviews' fixes), `fieldfit` (the fit option `containment: field`, phase P5d, the default with `shape: fill` from P5e: only the taxel field F on the surface, every proposal a diagonal Row bus with the option `row_sides`; the exact largest row- and column-convex field per lattice by a DP with window and quadrant bounds, the full rectangles, the pruned phase search, a turned field only with 3 % more taxels, the narrow tip within 3 taxels with several exits, the tails sized to the surface below them, F checked exactly and peeled, the routing's share on the surface and overhang, and the map's records with the routing report and its warnings; the P5d/P5e repair: the unturned search first and never pruned by a turned field, phase 0 on the usable edge and the quarter phases on every exit, a lattice larger than the caps searched whole first, the phase-aware early exit, the deterministic work budget `WORK_BUDGET`, every frame tried listed, the narrow tip choosing the exit, both tails ending on the nearest line across the boards on which each is at least the shortest tail long and ends at least the extension past the edge under it (P5-diagonal-bus.md sections 27.3 and 27.4), the overhang without the tails, the fillet's and the base edge's bends in `W_BAND_EDGE_RADIUS`, F of a straight design; coverage first, the plan's section 21: shaped fields within the rectangles' caps; tip first, section 26: within 3 % of an exit's most taxels the field reaching nearest the fingertip first, the field it displaces after its own zero-cost tie, reach first since 26.16), `reader` (the fit option `reader`: 16x16, 32x16 FlexiTac, 32x32, 48x48, auto; the tails' pins, the walk's caps, the reader the metrics and the map name, and the lines and frame index of each taxel), `place` (taxel map, overlay, wrap template, verification; a masked field's active crossings, `readout` and `taxel_mask_matches_design`; a map without `containment` takes the design's: `field` for a diagonal Row bus; the readout's `row_pin_order` from the pads), `api` (the routes, framed bodies, mesh cache), `errors` |
| `web/samples/` | Gen by Surface's samples (2026-11-06, the user's request: "在这个索引的下方,放置两列stl ... 能从左边把cad 拖到右边框然后开始生成"): `samples.json` (hand-kept: eight samples, each its Library sensor, a whole gripper's mesh record, its `assembled` part and scene and its `camera`, each thumbnail's view), `thumbs/<id>.webp` (`tools/browser/sample_thumbs.py`: the 3D view's look, 240 x 110, 7.1 KB in all, the UMI tips seen from their contact face), the two whole grippers `franka-hand-gripper.stl` and `widowx-250-gripper.stl` (one binary STL each, the Library part's facets first, then the other finger and the scene's decimated bodies; written by a private assembly tool from the Library's scenes; 232 and 64 KB) with their licence texts (`licenses/`, the Library's) and `NOTICE.md`; the folder 325 KB; read by `web/cad/main.js` `loadSample` (`tests/test_samples.py`, `tools/browser/sample_checks.py`) |
| `profiles/jlc_fpc_surface_v1.json` | the locked profile of the `surface_matrix_v1` template (CAD mode's tight geometry policies) |
| `tests/` | the stdlib unittest suite (below) |
| `tools/` | `mutation_check.py`, `golden_values.py`, `build_static_site.py` (the static site, with `library.html`, the Library's gate and its prebuilt Gerber ZIPs; since 2026-11-16 its three pages, the Library `index.html`, the generator `gen.html` and the forwarding `library.html`), `library_write.py` (the Library's fits and `entries.json`, and the checks of its 3D view's art, stages and scenes; since 2026-11-12 the looks' checks, `scene_look_problems()`, and the showcase's guards, `showcase()` and `showcase_page()`), `library_split.py` (the looks: the bodies shared out by material, the drawn shapes, the scenes' looks and the notices' rows, stdlib, with `--check`), `library_showcase.py` (the showcase's meshes, holder, drawn shapes and scene; `--check` without the sources), `mesh_decimate.py` (a stdlib, deterministic quadric decimator with a deviation gate), `flexitac_v2.py` (the hand-designed pad's geometry from its official Gerbers), `browser/` (Playwright checks, and `library_shots.py`, the Library's pictures and art, the showcase's pictures with `--showcase`, Gen by Surface's figure of the parts without a scene against its pin, `browser/generator_figure.json`, with `--check-generator` and `--pin-generator`) |
| `docs/` | API, layout schema, integration, exporter, plan, historical record, CAD mode and its plan |
| `outputs/` | git-ignored scratch directory for CLI exports; the application stores nothing |
| `claude/` | this handoff, `verification/` (reviews and the audit), `sessions/` (dated notes) and `specs/` (feature specs and their logs) |

## Contracts

- **Input**: `tactile-fpc-design/v1`, strict; aliases, precedence, the
  normalization report and the JSON Schema with its three documented engine
  leniencies are in [API.md](../docs/API.md).
- **Result and layout**: `tactile-fpc-layout/v3`, anchored rectangles, NC
  contacts, the tail and fan-out route pieces, the 30 DRC records, the
  registration record and the issue catalogue are in
  [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md).
- **Identity**: `build_sha256` = SHA-256 of canonical `{design_sha256,
  profile_sha256, generator, exporter}` (plus `template` on the surface
  template and `mask` for a field mask), `build_id` = slug + 12 hex digits;
  generator `deterministic-sensor-core/0.4.0`, exporter
  `direct-gerber-pure-stdlib/0.3.0` (both since the necked routing of
  2026-10-15, which changed every build id).  Bumping either version changes
  every build id, deliberately.  The order-requirement wording
  (`engine.profile.order_requirements`) is engine code that reaches the
  archives but not the identity: a change of it needs a generator-version
  bump, or one build id names two sets of archive bytes (the golden digests
  notice; the build id does not).  A profile change changes the profile
  digest, and with it every build id; bump the profile `revision` too, as
  `ORDER_NOTES.txt` and the manifests quote it.
- **Exports**: board ZIP and review-bundle members, the regeneration binding,
  `build_exports(result, cache=)`, determinism, the order requirements and
  the JLC review items are in
  [PHASE2_DIRECT_GERBER.md](../docs/PHASE2_DIRECT_GERBER.md).
- **Ordering**: order each board as a 2-layer, 0.2 mm FPC with 1 oz copper
  and a 0.1 mm PI stiffener at the contacts, a +/-0.05 mm outline
  tolerance (a special request) and ENIG, and check that the 0.3 mm gold
  fingers come out within +/-0.05 mm (JLC's trace tolerance is +/-20%).
  By JLC's rule the thickness with a stiffener is the FPC's plus the
  stiffener's: 0.2 + 0.1 = 0.3 mm (the user's decision of 2026-11-06, the
  profile revision 2026-11-06b; 0.225 mm before, JLC's choice for a
  0.11 mm FPC).
  On the order form, Gold Fingers is Yes with Gold Fingers Thickness 0.3 mm,
  the stiffened contact zone in total (profile revision 2026-10-29: JLC gives
  it the highest priority when it chooses the stiffener under the gold
  fingers).  `engine.profile.order_requirements(profile)` resolves these
  entries (with the contact-zone, contact-start, contact-window and
  coverlay-window notes; each board's lines of `ORDER_NOTES.txt` name its
  coverlay windows and those longer than JLC's general 20 mm) from the
  profile for `ORDER_NOTES.txt`, the manifests and `/api/default`; the
  wording and the sources each entry cites are in that function, the
  figures and the source texts in the profile.
- **Integration**: pin 1, channel order, the stack, the assembly preview and
  the reader connectors are in [INTEGRATION.md](../docs/INTEGRATION.md).
- **Interfaces between components**: `exporters.artifact_filenames(result)`
  names every download (HTTP `Content-Disposition`, CLI, review manifest);
  the SVG root's `data-view="top"` and `data-active-region` register the
  boards in the browser; `/api/default` gives the browser `profile.limits`
  (form limits), `profile.display_rules` (rule text) and
  `profile.order_requirements` (the manufacturing note).

## Locked profile

`profiles/jlc_fpc_standard_v1.json`, id `jlc-fpc-standard-v1`, revision
2026-11-06b (stage G of 2026-10-14: 0.225 mm PI, the `order` block and the
stack-up of the ordered build; 2026-10-15: the fan-out trace limits, the
finger width, JLC's trace minimum per copper thickness and 0.1016 mm
electrodes, and the fixed route-space, lane and deck-pitch rules removed;
2026-11-06: the 2-layer 0.2 mm order; 2026-11-06b: its 0.1 mm PI
stiffener).  The engine checks it on every load (`E_PROFILE_*`):
every rule must be present and positive, no design rule may be looser than
the `fabrication` capability, the rules must be mutually consistent, and the
order must be orderable and fit the reader connectors: a JLC 1- or 2-layer
thickness, copper and finish, a stack-up whose layers add up to the ordered
thickness (on a 2-layer order to one of JLC's 1-layer thicknesses, the
boards' own build), an outline tolerance JLC offers on request that holds the
THD0515 tail width, and a contact zone within the connectors' 0.30 +/- 0.03
mm: on a 2-layer order JLC's rule, the ordered FPC + the stiffener (since
2026-11-06b), on a 1-layer order core + copper + stiffener under the open
coverlay.
Its `sources` block quotes the JLCPCB flexible-PCB capabilities page (fetched
2026-10-12), the two reader connectors and the reference design.

| Key | Value | Note |
| --- | --- | --- |
| `fabrication.copper_to_board_edge_mm` | 0.3 | JLC laser outline |
| `fabrication.copper_to_slot_mm` | 0.3 | JLC |
| `fabrication.outline_tolerance_mm` | 0.1 | JLC |
| `fabrication.outline_tolerance_on_request_mm` | 0.05 | JLC, on request |
| `fabrication.gold_finger_to_board_edge_mm` | 0.2 | JLC |
| `fabrication.trace_width_tolerance_fraction` | 0.2 | JLC trace width +/-20% |
| `fabrication.exposed_pad_to_trace_mm` | 0.15 | JLC |
| `fabrication.coverlay_expansion_mm` | 0.1 | JLC |
| `fabrication.coverlay_min_bridge_mm` | 0.5 | JLC |
| `fabrication.coverlay_opening_to_trace_mm` | 0.15 | JLC |
| `fabrication.maximum_outline_short_side_mm` | 234.0 | JLC regular size |
| `fabrication.maximum_outline_long_side_mm` | 490.0 | JLC regular size |
| `fabrication.single_layer_fpc_thickness_options_mm` | 0.07, 0.11, 0.12 | JLC 1-layer finished thicknesses |
| `fabrication.two_layer_fpc_thickness_options_mm` | 0.11, 0.12, 0.2 | JLC 2-layer finished thicknesses |
| `fabrication.single_sided_copper_thicknesses_mm` | 0.018, 0.035 | JLC single-sided copper |
| `fabrication.single_sided_copper_weights_oz` | 0.5, 1 | the same copper in oz |
| `fabrication.single_sided_min_trace_width_mm` | 0.0889, 0.1016 | JLC minimum trace width per copper: 3.5 mil (18 um), 4 mil (35 um); the ordered 1 oz gives 0.1016 |
| `fabrication.single_sided_min_trace_space_mm` | 0.0889, 0.1016 | JLC minimum spacing per copper, as above |
| `fabrication.gold_finger_thickness_tolerance_mm` | 0.03 | JLC FPC thickness tolerance, gold-finger area |
| `fabrication.surface_finish` | ENIG | JLC |
| `fabrication.pi_stiffener_thickness_options_mm` | 0.1, 0.15, 0.2, 0.225, 0.25 | JLC PI options |
| `fabrication.recommended_pi_stiffener_mm` | 0.225 | JLC: for a 0.3 mm connector on a 0.11 mm FPC (quoted; the 2-layer 0.2 mm order takes 0.1 mm) |
| `fabrication.recommended_pi_stiffener_fpc_thickness_mm` | 0.11 | |
| `fabrication.recommended_pi_stiffener_connector_thickness_mm` | 0.3 | |
| `stackup.construction` | single_copper_flexible | |
| `stackup.copper_layer` | top_copper | |
| `stackup.coverlay` | polyimide | |
| `stackup.coverlay_thickness_mm` | 0.025 | coverlay PI |
| `stackup.coverlay_adhesive_thickness_mm` | 0.025 | coverlay adhesive (JLC, on 1 oz copper) |
| `stackup.copper_thickness_mm` | 0.035 | 1 oz, the copper of the boards' own 0.11 mm build (ordered as JLC's 2-layer 0.2 mm FPC since 2026-11-06; was 0.018) |
| `stackup.core_polyimide_thickness_mm` | 0.025 | JLC 25 um dielectric (was 0.05) |
| `stackup.bottom_copper_placeholder_thickness_mm` | 0.001 | descriptive only, no second copper layer |
| `stackup.stiffener_side` | bottom | only bottom is supported |
| `stackup.stiffener_material` | polyimide | |
| `stackup.stiffener_thickness_mm` | 0.1 | since 2026-11-06: the 0.2 mm FPC + 0.1 mm, the 0.3 mm gold fingers by JLC's rule (0.225 from 2026-10-14, 0.2 before) |
| `routing.finger_trace_width_mm` | 0.254 | the tail (gold-finger) route pieces; the finger gap is 0.246 |
| `routing.min_pad_space_mm` | 0.2 | |
| `routing.min_pad_to_trace_mm` | 0.2 | |
| `routing.min_electrode_gap_mm` | 0.25 | |
| `routing.min_electrode_width_mm` | 0.1016 | JLC's 1 oz minimum (was 0.1, re-audit N4) |
| `routing.copper_to_edge_mm` | 0.3 | |
| `routing.copper_to_cutout_mm` | 0.3 | |
| `routing.active_edge_clearance_mm` | 0.75 | board margin around the taxel field |
| `routing.electrode_overhang_mm` | 0.2 | as the reference design |
| `connector.pad_pitch_mm` | 0.5 | |
| `connector.pad_width_mm` | 0.3 | |
| `connector.contact_length_mm` | 4.0 | THD0515 drawing |
| `connector.contact_tip_clearance_mm` | 0.3 | |
| `connector.contact_center_to_side_edge_mm` | 0.5 | one pitch: width (P + 1) x 0.5 mm |
| `connector.tail_tip_corner_radius_mm` | 0.3 | THD0515 drawing |
| `connector.tail_width_tolerance_mm` | 0.07 | THD0515 drawing |
| `connector.contact_width_tolerance_mm` | 0.05 | TXGA drawing |
| `connector.contact_zone_thickness_mm` | 0.3 | both drawings |
| `connector.contact_zone_thickness_tolerance_mm` | 0.03 | TXGA drawing |
| `connector.maximum_pins` | 64 | |
| `coverlay.coverlay_expansion_mm` | 0.1 | |
| `coverlay.coverlay_min_bridge_mm` | 0.5 | |
| `coverlay.coverlay_opening_to_trace_mm` | 0.15 | |
| `coverlay.coverlay_opening_general_max_length_mm` | 20.0 | JLC's general length of one opening (its FPC design rules); the order notes name the longer windows, nothing refuses them |
| `tail.minimum_length_mm` | 7.0 | |
| `tail.stiffener_length_mm` | 6.0 | connector drawings: 6.00 mm thick zone |
| `tail.stiffener_end_clearance_mm` | 0.5 | product default |
| `outline.outline_fillet_radius_mm` | 0.5 | |
| `outline.arc_segment_max_angle_deg` | 10.0 | |
| `outline.maximum_unfilleted_concave_turn_deg` | 15.0 | |
| `outline.offset_allowance_mm` | 0.001 | |
| `fanout.maximum_channels_per_lane` | 16 | |
| `fanout.maximum_lanes` | 2 | |
| `fanout.slot_width_mm` | 12.0 | |
| `fanout.minimum_slot_width_mm` | 4.0 | |
| `fanout.slot_height_fraction` | 0.3 | |
| `fanout.minimum_slot_height_mm` | 1.5 | |
| `fanout.maximum_slot_height_mm` | 4.0 | |
| `fanout.lane_to_slot_clearance_mm` | 0.75 | |
| `fanout.maximum_taper_angle_deg` | 60.0 | bus-style diagonals (both boards) |
| `drc.numeric_epsilon_mm` | 1e-06 | the only DRC tolerance |
| `limits.minimum_rows` | 1 | |
| `limits.maximum_rows` | 64 | |
| `limits.minimum_columns` | 1 | |
| `limits.maximum_columns` | 32 | |
| `limits.minimum_pitch_mm` | 0.6 | |
| `limits.maximum_pitch_mm` | 10.0 | |
| `limits.minimum_trace_width_mm` | 0.1016 | fan-out traces: JLC's 1 oz minimum |
| `limits.maximum_trace_width_mm` | 0.254 | the finger width |
| `limits.minimum_trace_space_mm` | 0.1016 | JLC's 1 oz minimum |
| `limits.maximum_trace_space_mm` | 0.246 | the finger gap (0.5 - 0.254) |
| `limits.maximum_tail_length_mm` | 80.0 | |
| `limits.maximum_outline_short_side_mm` | 234.0 | |
| `limits.maximum_outline_long_side_mm` | 490.0 | |
| `limits.high_fill_factor_warning` | 0.8 | |
| `limits.large_matrix_warning_taxels` | 1024 | |
| `limits.maximum_project_name_length` | 80 | |
| `order.fpc_layers` | 2 | the bottom copper empty (the FlexiTac fabrication guide's order) |
| `order.fpc_thickness_mm` | 0.2 | JLC 2-layer option |
| `order.outline_tolerance_mm` | 0.05 | a special request |
| `order.surface_finish` | ENIG | |
| `order.reference_contact_window_margin_mm` | 0.051 | the JLC-accepted reference's contact openings |
| `order.reference_field_window_length_mm` | 63.373 | the JLC-accepted reference's longest field window (23.368 x 63.373 mm, its GTS) |

## Default build

`default_design()` (12 x 32, pitch 2.0 mm, 1.0 mm electrodes since the user's
decision of 2026-11-06, the default fill 0.5 (1.4 mm, fill 0.7, before), tails 12 mm
top / 12 mm bottom since P5-diagonal-bus.md section 27.7, ending together
(7.5 mm bottom before), both tails at the bottom, rows on top, ascending,
0.127 mm fan-out traces at 0.127 mm spacing, the diagonal Row bus with
`both`: the generic default since P5-diagonal-bus.md section 18,
`diagonal-bus/8` with CAD mode's rule set, one outline down to the tail
roots and the Column V at 80 degrees since section 20, `diagonal-bus/9`
since section 24, the same boards, `diagonal-bus/10` since section 27, the
Row tail 0.048 mm east, on the field's centre line, `diagonal-bus/11` since
section 27.8, the same boards) gives build
`tactile-fpc-12x32-ba2e9b58bd8e` with no error or warning (with
`routing.row_sides` `channel`, the straight Row channel, and the 1.4 mm
electrodes of before, the boards of before, byte for byte, with the 0.225 mm
PI stiffener of before put back, its bottom tail 7 mm).  Values per
board (`—`: the board has no such key):

| Board value | Row | Column |
| --- | --- | --- |
| `id` | top_rows_fpc | bottom_columns_fpc |
| `metrics.outline_width_mm` | 67.520543 | 67.520543 |
| `metrics.outline_height_mm` | 41.365841 | 41.365841 |
| `tail.length_mm` | 12.0 | 12.0 |
| `tail.width_mm` | 6.5 | 16.5 |
| `tail.connector_pins` | 12 | 32 |
| `grid_registration.active_region.width` | 63.0 | 63.0 |
| `grid_registration.active_region.height` | 23.0 | 23.0 |
| `metrics.coverlay_opening_count` | 13 | 33 |
| `metrics.routed_cutout_count` | 0 | 0 |
| `construction.fanout_bundle_pitch_mm` | 0.254 | 0.254 |
| `construction.merger_taper_angle_deg` | — | 0.0 |
| `construction.channel_width_mm` | — | — |
| `verification.checks.route_route_clearance.measured_mm` | 0.127 | 0.169721 |
| `verification.checks.route_route_clearance.finger_section.measured_mm` | 0.246 | 0.246 |
| `verification.checks.route_width.measured_mm` | 0.0 | 0.0 |
| `verification.checks.pad_trace_clearance.measured_mm` | 0.223 | 0.223 |
| `verification.checks.copper_to_outline.measured_mm` | 0.3 | 0.3 |
| `verification.checks.route_to_outline.measured_mm` | 0.300999 | 0.364499 |
| `verification.checks.copper_to_cutout.measured_mm` | null | null |
| `verification.checks.stiffener_end_clearance.measured_mm` | 5.5 | 6.0 |
| `verification.all_checks_passed` | true | true |

Generation of the default takes about 0.1 s on this host (the DRC used to
take 1.1 s).  The three archives and their digests are in
[PHASE2_DIRECT_GERBER.md](../docs/PHASE2_DIRECT_GERBER.md#determinism);
`tests/test_golden_default.py` pins all of these values.

## Tests and tools

The suite is stdlib `unittest`: 1366 tests in 54 modules (2026-11-18, the Unitree Dex3-1 back, `fpc-int-n-dex3-back`:
`test_library`'s `test_no_library_face_is_doubly_curved` now `test_a_doubly_curved_face_is_sent_at_the_curved_limit`, the
count the same; before it Whole board on the real stack and its review,
`fpc-int-n-curved`: `test_surface_curved`'s `WholeBoardBendTests` (3, the review's a bend running toward the exit); 1363 before, 2026-11-17, the review of the symmetric, larger selections
fixed, `fpc-int-n-curved`: `test_surface_curved`'s `SymmetricFollowupTests` (9); 1354 before, gently curved faces symmetric and larger,
`fpc-int-n-curved`: `test_surface_curved`'s `MirrorSymmetryTests` (4), `test_surface_web`'s
`test_the_strain_limit_is_one_percent_on_curved_faces`, `test_library`'s `test_no_library_face_is_doubly_curved`; 1348 before,
the trim of the Allegro Hand and the Unitree Dex3-1
merged into gently curved faces, `fpc-int-n-curved`, the Dex3-1's fingertip a test fixture of its own; before it 1350 on that
branch, the review's fixes of gently curved faces: `test_surface_curved` 16 -> 22, a click off the dome's patch, a patch never
beyond the limit, a face selected whole, the outline drawn clean, the relaxed sheet judged, a face bent tighter than the field
refused saying so; 1328 in 53 modules on the mainline after the trim, the Allegro Hand's two tests gone with the hand,
`test_the_allegro_hand_s_thumb_and_cascade` and `test_the_allegro_hands_tails_leave_toward_the_palm`; 1344 before, with gently
curved faces: the new `test_surface_curved` (16), `test_surface_fit`'s disk tests replaced or retired with the disk (36 -> 34),
`test_border`'s dome on its whole chart; 1330 in 53 modules before, after the verification of the Library's lines
merged, `test_static_site`'s `test_the_tests_ask_for_a_private_file_before_reading_it`, `test_surface_fit`'s
`test_an_obstacle_blocks_every_raster_cell_it_touches` and `test_field_fit`'s `test_a_spent_work_budget_searches_no_window`;
2026-11-17, with the tool menu's order of work,
`test_surface_web`'s `ToolMenuTests` (4: the click tools numbered 1 and 2, Edit border marked Optional, both
aria-hidden, main.js renaming Edit border in its first span, the word hidden while the border is edited); 2026-11-16, with the UMI cards zoomed on the tip and the showcase's card Exploded, `test_library`'s `test_the_umi_cards_are_zoomed_on_the_tip`, `test_the_card_s_window_is_taken_on_the_tip` and `ViewTests`' `test_a_card_framed_otherwise_than_its_part_s_is_refused`; 2026-11-16, after the review of the Robotiq 2F-85,
`test_library`'s `test_a_model_under_the_2f85_name_is_one_the_library_pins`; 2026-11-16, with the Robotiq 2F-85,
`test_library`'s `test_the_menagerie_robotiq_alone_carries_its_name`; 2026-11-17, after the LeFlexiTac's review, `test_library`'s
`test_the_leflexitac_s_import_needs_no_scratch_recipe` and `test_static_site`'s
`test_files_stating_no_licence_are_built_only_for_a_local_preview`; 2026-11-16, with the LeFlexiTac, `test_library`'s
`test_the_leflexitac_s_scene` and `test_a_source_stating_no_licence_is_taken_only_by_its_dated_entry` (its name since the
user's word of 2026-11-17, `_dated_pending_entry` before); 2026-11-17, with the AgileX Piper, `test_library`'s
`test_the_agilex_piper_is_menagerie_s_finger_on_its_whole_face`; 2026-11-17, with the Galaxea R1 Lite, `test_library`'s
`GalaxeaR1LiteTests` (3; 4 since its review that day, `test_its_carriage_is_drawn_black_over_the_sensors_finger`); 2026-11-17, with the Seeed reBot DevArm, `test_library`'s
`test_the_rebot_is_the_menagerie_gripper_with_its_contact_face_whole`; 2026-11-17, with the xArm Gripper's card, `test_library`'s
`test_the_deny_list_lets_the_xarm_gripper_card_alone_pass` and `test_the_xarm_gripper_open_as_its_model_draws_it`;
2026-11-17, with the Rainbow RB-Y1, `test_library`'s
`test_the_rainbow_rby1_is_its_1_2_gripper_whole`, its v1.3 gripper's until the lead's decision of the same day; 2026-11-17, with the OpenArm, `test_library`'s
`test_the_openarm_is_drawn_from_its_open_model` and, after its review, `test_the_collada_reader_takes_only_metres_and_z_up`; 2026-11-17, with the YUBI Gripper, `test_library`'s
`test_the_yubi_gripper_is_drawn_from_its_open_model`; 2026-11-17, the three hands merged on `fpc-int-n-hands`, one
mechanism: `test_library`'s `test_a_hand_s_further_fingers_and_its_card_override` (one for the three hands),
`test_the_leap_hand_has_a_sensor_on_every_finger`, `test_the_allegro_hand_s_thumb_and_cascade`,
`test_a_hands_further_fingers_are_seen`, `test_every_border_is_one_the_page_fits` and
`test_the_allegro_hands_tails_leave_toward_the_palm` (the Allegro Hand's two gone with the hand on 2026-11-17); 3 of `test_library`'s `ShowcasePageTests` failed until the full
re-shoot, the other pictures and the showcase being of older view sources, and pass since the re-shoot at the merge (21ca0c4); 2026-11-17, after the review of the FlexiTac hardware's files,
`test_flexitac_downloads`' `test_the_rule_is_the_engine_s_readers`, `test_gen_s_board_follows_the_tails`,
`test_each_board_s_pins_are_its_bom_s_connectors` and `test_the_reading_boards_notice_names_the_easyeda_of_their_gerbers`;
2026-11-17, with the FlexiTac hardware's files,
`test_flexitac_downloads` (18: the served files and bundles, the tool, the notices, the rule under node, the pages);
2026-11-16, with the cards aligned with the grippers,
`test_library`'s `test_the_umi_finger_takes_the_grippers_homes`; 2026-11-16, after the review of the UMI finger's shapes,
`test_library`'s `test_each_tip_is_cut_by_its_profile` (the 26 tips' meshes measured against `tools/library_tips.py`'s
profiles); 2026-11-16, with the UMI finger's shapes, `test_library`'s
`test_the_umi_shelf_is_one_card_per_shape` and `FamilyTests`' `test_the_family_is_its_cards_each_complete` in place of
`test_the_family_is_complete_with_its_default`; 2026-11-16, after the review of the first page and Design your
own, `FirstPageTests`' `test_a_hash_of_before_on_the_open_library_goes_too` (a hash of before over the open Library,
a page shown again by the back-forward cache), `RouteTests`' `test_the_forwarding_page_is_never_counted` and
`test_static_site`'s `CountsTests` (2: `web/counts.js` on both pages, under node); 2026-11-16, with the Library the
first page and the generator
at `gen.html`, `test_library`'s `FirstPageTests` (7: `web/forward.js` under node, its keys and hashes the generator's, the
Library's addresses none of them, the pages' heads, `library.js`'s guard, every link) and `RouteTests`'
`test_the_pages_with_the_counts` in place of its Library page's, and with the showcase's Design your own,
`test_library`'s `DesignYourOwnTests` (2); 2026-11-15, with the FlexiTac team's footer on both pages,
`test_library`'s `test_the_team_footer_is_the_same_on_both_pages`, `test_web_theme`'s
`test_the_footer_takes_the_page_s_palette_and_type` and `test_surface_web`'s `test_the_guide_stops_at_the_work_s_end_above_the_footer`; with the Library's details in a window over the
grid, `test_library`'s `test_a_card_s_details_open_in_a_window_over_the_library`; 2026-11-14, with the UMI pad's tint in the Library's
Assembled view, `test_library`'s `test_the_rules_may_tint_the_assembled_pad_on_those_parts` and
`test_the_pad_s_tint_is_held_to_the_assembled_sheets`, and with the MakerMods Metal Arm's body drawn by eye:
`test_library_split`'s `test_a_prism_is_its_convex_profile_drawn_along_its_axis` and `test_library`'s
`test_the_makermods_body_is_the_project_s_drawing_by_eye`; 2026-11-13, with the second stage of the Library's realistic
look: the UMI rows' orange and Gen by Surface's figure held apart from it, `test_library`'s
`test_gen_by_surface_s_figure_is_pinned_apart_from_the_library_s_look` and `test_the_look_is_held_to_the_part_s_pixels`,
and the showcase's page and drawn shapes, `test_library`'s `ShowcasePageTests`, `test_library_showcase`'s `DrawnTests`
and `test_showcase`'s `test_the_view_s_document_names_the_showcase_s_page`; 2026-11-12, with the first stage of the
Library's realistic look: the looks, `test_library_split`, the showcase's files, `test_mesh_decimate` and `test_library_showcase`, and
the showcase's sensor, `test_showcase`; 2026-11-06, with the
0.1 mm PI stiffener of that day's last decision, `test_export_order_requirements`'
`test_the_gold_finger_thickness_of_a_2_layer_order_is_jlc_s_rule`; with the
verification's small findings of that day, `test_surface_web`'s
`test_the_stacked_card_s_last_row_is_rounded_as_its_foot`, `test_library`'s
`test_a_card_tabbed_to_comes_into_the_window_with_room_round_it`, `test_samples`'
`test_the_phone_row_s_tiles_are_one_height` and `test_docs_consistency`'s
`test_the_runner_s_timeout_outlasts_a_suite_run`; with the
review's second round of that day (a browser without `Element.checkVisibility`, the
Library opened at an address of its own, a card or a sample's tile Tabbed to shown
whole, the whole grippers' STL headers), `test_surface_web`'s
`test_the_clearance_of_the_controls_never_fails_a_build`, `test_library`'s two page
pins and `test_samples`' tile pin; with the
samples' parts loaded alone and a model loaded with no face selected, that day's
later request, `test_samples`'s `test_a_sample_loads_its_part_alone`,
`test_a_model_loaded_has_no_face_selected`,
`test_a_model_loaded_hides_the_build_below_until_its_own_generate` (its review) and
`test_a_whole_gripper_s_selection_on_its_finger_is_seen_from_its_camera`; with the
look's toggle of that day (light by default, dark on the header's toggle),
`test_web_theme`'s `ThemeToggleTests`; with
Gen by Surface's samples, `test_samples`, under 2 s, and their review; with the
shoot's pin of every sensor's 3D view, `test_library`'s
`test_every_sensor_of_the_library_has_its_3d_view`; with the
Library's grid of that day, `test_library`'s grid pins; with the
stacked card without its legend and notes, the figures' controls in their frames
(`test_surface_web`'s `FigureControlsTests`), the board cards without their layer
legends and the registration without its caption; 2026-11-05, with the
Library's 3D view (the user's requests of 2026-11-05: each sensor's page a
3D view to turn, the grippers drawn whole): `test_library`'s `SceneTests`
and `ViewTests` on tiny scenes and art, its files, licences and site gate,
`test_surface_web`'s `LibraryViewTests`; with the
3D views' light, `test_surface_web`'s `ViewLightTests`; the
sensor on the part beside the stacked view: its markup, its pure geometry and
lazy three.js, its art listener, its lightbox and its Gen-by-Surface-only
split, and its review: the checks' measurements with `?probe` only, its
buffers and mode, its coverage, and its second review: the split's caption
off the pin-1 rings (since 2026-11-06 no caption: the split's plan view as the
whole card's), the coverage's alpha kept off what lies behind an
outline and the figure's grab cursor, and its look: its own lights and
studio, the studio's fallback with one warning, its edge bands, contact
shade and film face, and the look's fix round: a lost context's objects
dropped, the measures guarded, an empty contact footprint kept, the shader
edits' names in the vendored three.js and the contact shade's core inside
the footprint's edge, and its Exploded home the left figure's as it opens
(the user's decision: one source for the two angles, its up, its keys),
and the Library's data, its page and its tapered
tips, `test_library`, about 12 s, and the two lines' integration: the
Library's minors of its review, and its polish (the user's decisions of
2026-11-05: one wording for every shelf heading, a sensor's picture 3:1 in
one column), and the 3D view in the figure's light: the studio both draw in,
`web/cad/studio.js`, its markers unlit and a drag's diffuse material on a
software renderer only, and the film's own lamp (the user's of 2026-11-05):
its shader's alone, aimed from the Exploded home, hung on the camera, and
the Library's pictures: each `image` its manifest's, a picture of another
fit refused and one of older figure sources a warning, on a fixture of two
tiny WebPs, the on-part figure on its cards and a sensor's page, the
pictures' contract in its script (the card file lazy and sized, the
placeholder for a picture that fails), the Exploded | Assembled control
and app.py serving the pictures as `image/webp`, and the set of pictures:
every sensor pictured by a shot of its own fit, `library_write.py
--check` wanting each, each drawing centred; 2026-11-04, with the
page's Apple-style theme, `test_web_theme`; 2026-10-30, with CAD
mode, the surface template and their three reviews, and phases P1, P2
(the builders, the DRC and the registration, and the fixes of their reviews), P3 (the exporter) and P4 (CAD mode's masked fields and readers, and the fixes of its reviews) of the masked field, and phases P5a (the diagonal Row bus's primitives), P5b (its construction, DRC and contract) and P5c (its exports), and the fixes of the P5 reviews, and P5d (CAD mode's field-only containment and the P5c carry-overs) and P5e (the browser's Containment and Row traces, and field-only containment the default), and the fixes of the P5d/P5e reviews, and the Row bus's tail redesign, diagonal-bus/2, and the fixes of its review, and its stacked tails, diagonal-bus/3, and its one outline over the field, diagonal-bus/4, with the lanes off the Column copper and following a receding field, and its regular outlines, diagonal-bus/5, and the corner tolerance, the rectangle preference and the chamfered notches, diagonal-bus/6, and the straight sides at the tip, diagonal-bus/7, and the diagonal Row bus as the rectangular generator's default, the plan's section 18, and the rectangular generator's bus as a subset of CAD mode with one outline down to the tail roots and the Column V at 80 degrees, diagonal-bus/8, sections 19-20, and the fixes of its review, and coverage first, section 21, and CAD mode's border of the taxels, docs/CAD_BORDER.md, and symmetric sensors on symmetric faces, section 22, and the caps keeping the exit, section 23, and the corner tolerance at every convex corner with the convex sides, section 24, and the EasyEDA Pro projects, docs/EASYEDA_EXPORT.md, about 5 s, and the taxels from the fingertip, section 26 (the rectangle's cap order, the exact filler band, tip-first fields and rectangles), about 75 s, and its round 2 (the lead's zero-cost tie, the tip-zone guard, `tip_first: false` as the ties alone, the rectangles' 80 % floor and column guard), about 30 s, and its round 3c (reach first, the tip-zone guard gone; CAD mode without rectangles, its rectangle and rectangle-preference tests gone, the removed options refused), and round 3c's review and the user's decision of 2026-10-27 on symmetric faces, section 26.17 (the lead's tie in the lead's place, the displaced field's rank and the taxels given, saved placements' removed options, symmetric faces' symmetric fields first, the symmetric tip share, T0's slack and ties, the pass's floor), and round 4's review, section 26.18 (every exit of the fit without the caps searched on its own when the proposals reach it, a symmetric group's eighth row phases and its slack, the taxels given from the lead and its pass, saved placements' generic-template options, the tie's place and peel at their edges), and the Row tail centred on the field, section 27, diagonal-bus/10, and the user's threshold of 20 % on symmetric faces, section 26.19, and one side's convex flank, section 27.8, diagonal-bus/11, and the profile revision 2026-10-29: the gold-finger thickness order option and the coverlay-window notes, and the coin for scale's vendored photo, and CAD mode's vendored default part and its shipped fit, and the static site: `app.answer`, the worker's bridge and the site build, and the header's GitHub counts under `app.py`), about 66 s on Python 3.12 on this host before the masked
field's guards, which add about 22 s, its P2 DRC tests about 10 s more, its P3 export tests about 2 s, its P4 fit tests about 30 s, the P5a bus tests under 1 s, the P5b diagonal-bus tests about 16 s with the P5 reviews' fixes, the P5c export tests about 2 s and the P5d field-fit tests about 35 s (53 s on 3.9), P5e's under 2 s more, the P5d/P5e reviews' fixes about 30 s (the whole suite took 149 s on 3.12 on 2026-10-21 before P5d; 273 tests took 65 s on 3.12, 76 s on
3.9 and 67 s on 3.13 on 2026-10-15).  The last full run: 1366 tests in 877 s on Python 3.12 on 2026-11-18 (the Unitree Dex3-1 back and its review's fixes, `fpc-int-n-dex3-back` at 478ba2b, a `git archive` copy of `fpc_agentic_customization/` with the CI workflow, 4 skipped: the three tests of the user's EasyEDA exports, which lie outside it, 29 of 29 `test_easyeda_export` on a copy of the whole repository, and the usual one; on Python 3.10 the same 1366 in 1068 s on a `git archive` copy of the whole repository, 1 skipped; the public copy's (`export_public.py` of 478ba2b into a scratch clone) 1366 in 842 s on Python 3.12, 21 skipped; the documents' commits after it, `test_docs_consistency` again on both); before it 1363 tests in 891 s on Python 3.12 on 2026-11-17 (the review of the symmetric, larger selections fixed, `fpc-int-n-curved` at 19c46b2, a `git archive` copy of the repository with the CI workflow, 1 skipped; on Python 3.10 the same 1363 in 1031 s, 1 skipped; the forty-one `CURVED` mutants each killed alone by its killers' module on a scratch copy before it; the documents' commits after it, `test_docs_consistency` again on both); before it 1350 tests in 968 s on Python 3.12 on 2026-11-17 (the review's fixes of gently curved faces, `fpc-int-n-curved` at 4d4f83f, a `git archive` copy of the repository with the CI workflow, 1 skipped; on Python 3.10 the same 1350 in 1171 s, 1 skipped; on a host running the twelve mutants' suites and the browser checks beside it; the documents' commit after it, 35aeb6e, `test_docs_consistency` again on both); before it, on the mainline, 1328 tests in 885 s on Python 3.12 on 2026-11-17 (the Allegro Hand and the Unitree Dex3-1 removed, `fpc-int-n-trim-hands` at ef79b22, a `git archive` copy of the repository with the CI workflow, 1 skipped; on Python 3.10 the six modules touched or reading what changed, `test_library`, `test_docs_consistency`, `test_library_split`, `test_library_showcase`, `test_showcase` and `test_static_site`, 285 tests in 68 s on a `git archive` copy of ef79b22, 2 skipped); before it 1344 tests in 1382 s on Python 3.10 on 2026-11-17 (gently curved faces, `fpc-int-n-curved` at 422edbd, a `git archive` copy of the repository with the CI workflow, 1 skipped; on Python 3.12 the mutation run's baseline on its scratch copy of 422edbd, 1344 in 1180 s, 4 skipped; on a host running the seventeen mutants' suites beside it); before it 1330 tests in 852 s on Python 3.12 on 2026-11-17 (the merge's verification fixed, `fpc-int-n-final` at b72d48d, a `git archive` copy of the repository with the CI workflow, 1 skipped; on Python 3.10 the same 1330 in 1018 s, 1 skipped; the public copy `tools/export_public.py` wrote from b72d48d, 1330 tests in 800 s, 21 skipped, where the verification's copy of c98e7d3 had failed one); before it 1327 tests in 859 s on Python 3.12 on 2026-11-17 (the verification of the merge, a `git archive` copy of c98e7d3 with the CI workflow, 4 skipped, three of them for no `fpc_design` beside the copy; on Python 3.10 1327 in 1075 s, 4 skipped); before it 1327 tests in 804 s on Python 3.12 on 2026-11-17 (the Library's lines merged, `fpc-int-n-final` at 21ca0c4, a `git archive` copy of the repository with the CI workflow, 1 skipped; the six modules the merge touched or reading what it changed, `test_library`, `test_docs_consistency`, `test_library_split`, `test_library_showcase`, `test_showcase` and `test_flexitac_downloads`, 290 tests in 66 s on Python 3.10 on a `git archive` copy of 21ca0c4, 2 skipped); before it 1277 tests in 1390 s on Python 3.12 on 2026-11-16 (the UMI cards
zoomed on the tip after their review, at 1.25, `fpc-int-n-zoom` at 4909091, a `git archive` copy of the repository with the CI workflow, 2 skipped: no `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the browser checks, the shots' checks and other sessions' work; the six test modules touched or reading what changed, `test_library`, `test_library_showcase`, `test_showcase`, `test_docs_consistency`, `test_static_site` and `test_library_split`, 262 tests in 72 s on Python 3.10 on a `git archive` copy of 4909091, 1 skipped); before it 1277 tests in 837 s on Python 3.12 on 2026-11-16 (the UMI cards
zoomed on the tip and the showcase's card Exploded, `fpc-int-n-zoom` at 16e59f4, a `git archive` copy of the repository with the CI workflow, 2 skipped: no `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the browser checks; the six test modules touched or reading what changed, `test_library`, `test_library_showcase`, `test_showcase`, `test_docs_consistency`, `test_static_site` and `test_library_split`, 262 tests in 38 s on Python 3.10 on a `git archive` copy of 16e59f4, 1 skipped); before it 1276 tests in 1057 s on Python 3.12 on 2026-11-17 (the
Robotiq 2F-85 after its review, `fpc-int-n-robotiq` at ff15419, a `git archive` copy of the repository with the CI
workflow, 2 skipped: no `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the browser
checks, the shots' checks and another branch's (load 35 to 72 on 32 cores); the seven test modules touched or reading
what changed, `test_library`, `test_library_split`, `test_library_showcase`, `test_showcase`, `test_docs_consistency`,
`test_static_site` and `test_samples`, 286 tests in 45 s on Python 3.10 on a `git archive` copy of ff15419, 1 skipped);
before it 1278 tests in 1850 s on Python 3.12 on 2026-11-17 (the
LeFlexiTac after its review, `fpc-int-n-leflexitac` at a8dd30c, a `git archive` copy of the repository with the CI
workflow, 2 skipped, on a host loaded by the other lines' work and the review's seven mutants' suites run beside it;
the six touched modules, `test_library`, `test_static_site`, `test_docs_consistency`, `test_library_split`,
`test_library_showcase` and `test_showcase`, 263 tests in 88 s on Python 3.10 on a `git archive` copy of a8dd30c, 1
skipped); before it 1276 tests in 1345 s on Python 3.12 on 2026-11-16 (the
LeFlexiTac, `fpc-int-n-leflexitac` at 8373829, a `git archive` copy of the repository with the CI workflow, 2 skipped, on
a host loaded by the nine `LEFLEXITAC` mutants' suites run beside it; the six touched modules, 261 tests in 48 s on
Python 3.10, 1 skipped); before it 1274 tests in 854 s on Python 3.12 on 2026-11-16 (the cards
aligned with the grippers after their review, `fpc-int-n-align` at d121388, a `git archive` copy of the repository with
the CI workflow, 2 skipped: no `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the
browser checks and the shots' checks; the six test modules touched or reading what changed, `test_library`,
`test_library_showcase`, `test_showcase`, `test_docs_consistency`, `test_static_site` and `test_library_split`, 259 tests
in 39 s on Python 3.10 on a `git archive` copy of ed383e3, 1 skipped); before it 1274 tests in 877 s on Python 3.12 on
2026-11-16 (the cards aligned with the grippers, `fpc-int-n-align` at 14c1233, a `git archive` copy of the repository with the CI workflow, 2
skipped: no `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the browser checks; the six
test modules touched or reading what changed, `test_library`, `test_library_showcase`, `test_showcase`,
`test_docs_consistency`, `test_library_split` and `test_static_site`, 259 tests in 39 s on Python 3.10, 1 skipped);
before it 1273 tests in 963 s on Python 3.12 on 2026-11-16 (the merge of
the UMI finger's shapes after their review, `fpc-int-n-umi`, with the first page's verified head: `fpc-int-n-umi-merge`
at 35aeba1, a `git archive` copy of the repository with the CI workflow and the user's EasyEDA files, 2 skipped: no
`FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the browser checks; the one test module
touched since 59da544, `test_library`, 142 tests in 29 s on Python 3.10, and nine more of the sources touched since then
(`test_docs_consistency`, `test_static_site`, `test_library_showcase`, `test_library_split`, `test_samples`,
`test_showcase`, `test_surface_web`, `test_web_theme`, `test_api_http`), 259 tests in 17 s, the same 2 skipped); before
it 1273 tests in 989 s on Python 3.12 on 2026-11-16 (the UMI finger's shapes after their review, `fpc-int-n-umi` at 5a05cc2, a `git archive` copy with the CI workflow, 2 skipped: no
`FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the browser checks and nine mutants'
suites; their 9 touched modules, 362 tests in 44 s on Python 3.10, the same 2 skipped); before it 1271 tests in 958 s on Python 3.12 on 2026-11-16 (the merge of
the drag hint, the Library in the same tab and the team's footer, `fpc-int-n-team`, with the Library the first page and
Design your own, `fpc-int-n-first`: `fpc-int-n-merge`, a `git archive` copy of the repository with the CI workflow and the
user's EasyEDA files, 2 skipped: no `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules; on a host busy with the
browser checks; the 16 modules either line touched, 647 tests in 665 s on Python 3.10, 7 skipped: the CI workflow and the
EasyEDA files not beside the project's copy too); before it 1271 tests in 770 s on Python 3.12 on 2026-11-16 (the Library the
first page and Design your own after their review, `fpc-int-n-first`, a `git archive` copy, 7 skipped; their 14 touched
modules, 609 tests in 507 s on Python 3.10, 7 skipped: no `FLEXITAC_V2_GERBERS`, no CI workflow and none of the user's
EasyEDA files beside the copy, node v18's `--check` of ES modules); before it 1258 tests in 1102 s on Python 3.12 on 2026-11-15 (after the review of the drag hint, the Library in the same tab and the
FlexiTac team's footer: a `git archive` copy with the CI workflow, 5 skipped, on a host busy with the browser checks; the touched
modules, 269 tests on Python 3.10); before it 1258 tests in 851 s on Python 3.12 on 2026-11-15 (the drag hint, the
Library in the same tab and the FlexiTac team's footer, a `git archive` copy, 7 skipped; their touched modules,
`test_library`, `test_web_theme`, `test_surface_web`, `test_docs_consistency` and `test_samples`, 269 tests on Python 3.10);
before it 1254 tests in 857 s on Python 3.12 and in 1020 s on
Python 3.10 on 2026-11-15 (the merge of the realistic look's follow-up, the UMI pad's tint and the MakerMods body, a
`git archive` copy of the project and the CI file with node v18 on the path; 5 skipped: the showcase's rebuild from
the official Gerbers without `FLEXITAC_V2_GERBERS`, node v18's `--check` of ES modules, the three EasyEDA tests
without the user's exports beside the copy, which pass alone on both with them, 29 tests), and 1254 in 810 s in the
public export's copy as its CI runs them (22 skipped).  Python 3.10 matters since the run of 2026-11-14: before it the
art's gzip header differed below 3.11 (`test_showcase` failed on CI's 3.9).  Branch coverage measured with coverage.py on 2026-10-15: 93%
overall (`app.py` 94%, `engine/core.py` 97%, `engine/drc.py` 96%,
`engine/layout.py` 97%, `exporters/direct_gerber.py` 92%; `cli.py` 63%
because its tests run it as a subprocess).

```bash
PYTHONPATH=. python3 -B -m unittest discover -s tests
```

| Module | Covers |
| --- | --- |
| `test_core` | the original engine regressions, updated for layout v3 |
| `test_geometry_column`, `test_geometry_connector`, `test_geometry_profile` | Column outline and fan-out, body-side steps, tails and contacts, profile rules and limits (E, T) |
| `test_geometry_bundle` | the necked routing of 2026-10-15: two route pieces per net with their widths, straight bundle sections exactly one bundle pitch apart, parallel diagonals, every gap and the finger-section gaps on every design (against the DRC's `finger_section`), the width change below every bend in the tail, the Row channel and expansion, the bend stagger and every diagonal within the bus angle and the cap, the shortest ones included; the `routing` inputs, ranges, aliases, schema and form |
| `test_geometry_drc` | every DRC rule on mutated layouts, exact counters, the finger-section spacing of route pairs with a tail piece, registration, feasibility, speed and determinism (E) |
| `test_direct_gerber_export` | the C1 read-back of the emitted GTL/GTS/GKO in every orientation, archive structure (C1, X) |
| `test_export_readback`, `test_export_artifacts` | exporter self-check against tampered emissions and results, stiffeners, netlist, pinout, names, archive metadata, bundle (X) |
| `test_api_normalization`, `test_api_schema`, `test_api_identity` | strict input, schema contract, identity and cache, browser payload guard (A, T) |
| `test_api_svg` | copper-side top views (A) |
| `test_api_http` | the HTTP server in-process on ephemeral ports: routes, malformed requests, Host/Origin/Content-Type, `--allow-host`, limits, timeouts, the 16-build cache, the header's GitHub counts (`--no-github`) (A, T) |
| `test_api_cli` | `cli.py` as a subprocess, batches and their exit status (A, T) |
| `test_export_gold_fingers` | the gold fingers measured on the emitted GTL, GTS, GKO and GBSL: pitch, outer contact centres, tail width, 0.30 x 4.00 mm contacts from 0.30 mm, R0.30 corners, the contact window and the flush 6.0 mm stiffener, for 12/16/32 pins, NC contacts and every tail side (G) |
| `test_export_order_requirements` | the profile's `order` block and its checks, the resolved order requirements, `ORDER_NOTES.txt` in every ZIP (with each board's trace widths and what JLC's tolerance makes of them), both manifests, `/api/default`, the browser note and the exporter's read-back of the notes (G) |
| `test_golden_default` | golden identity, geometry, DRC measurements and archive digests of the default build, the diagonal Row bus since the plan's section 18 (T); its straight Row channel keeps the golden layout and boards of before (with the 0.225 mm PI stiffener of before put back since 2026-11-06) |
| `test_chirality` | pin 1, `ROW_01`, `COL_01` and the tails on every side and role mapping, in the layout, the emitted Gerbers, netlist and pinout, and the stack view (T) |
| `test_negative_drc_flow` | one injected defect per DRC code through `generate_design`, the exporter, HTTP and the CLI (T) |
| `test_surface_mesh` | CAD mode's STL input (`surface/mesh.py`): binary and ASCII, padded files, units, bad files; welding, outward shells (inside-out, open shells wherever they sit, cavities), covered walls, T-junctions; repeated triangles and fans on one edge stay fast |
| `test_surface_chart` | selection (presets, growth, operations, the bend barrier at any tessellation and at creases) and flattening (planar, unfold, LSCM+ARAP; inside-out files give the same chart; one hole kept whole; bands opened; pieces refused; T-junctions on flat, folded and curved patches) |
| `test_surface_fit` | the fit (the soft-finger replica's 44 x 8, the whole board's full rectangle (shape rectangle's before section 26.16), and its masked 50 x 12 = 470 with `containment: board` (masked fields within the rectangles' caps, section 21), its default field-only 59 x 12 = 708 on the diagonal Row bus (phase P5e), the crank pad's 683 (34 x 34; 666 before section 21) against the board fit's 546, `max_area` with either containment, the overlay below an arc exit's chord, options (the removed CAD options refused) and their documented table, determinism, FlexiTac, cylinders, arcs, domes, bends, straight sides next to fine corners, the exit crossing's clearance, one proposal per shape) and the map (taxels, chirality of a rectangle's and of a masked field's map, reader lines from pins, mismatches, a masked design mapped only with the placement fitted for its mask, damaged placements, board clearance, tail reach, spacing along curved surfaces) |
| `test_surface_curved` | gently curved faces (2026-11-17, the study's root causes RC1-RC5 of the user's Dex3-1 report, the review's fixes and the user's feedback on symmetry): a face's mirror planes found on the mesh (the Dex3-1 fixture's z = 0, a synthetic dome's two on a tessellation not itself symmetric, none on its quarter, a lopsided dome's one; fitted where a one-sided hole moves the centroid) and every patch taken with its mirror image (before and after its outline is drawn, the dome's axis exactly on the planes) and its holes filled (a click's patch a disk: the Dex3-1's tip-end rings and the LEAP Hand's refused clicks; an open mesh's hole never enclosed), the sides and the auto exits laid on the plane and a tessellation not itself symmetric given a symmetric field (the review of the symmetric selections, `SymmetricFollowupTests`) (the same symmetric patch from every click on a dome's patch, 405.1 mm2 on the Dex3-1's at 1 %; a click's patch reaching the plane symmetric, one on a side its mirror click's image), the Dex3-1's field symmetric and centred (82 taxels at 1 %, 48 at 0.3 %); a click anywhere on the Dex3-1's dome patch selects that mirror-symmetric patch by stretch (238.8 mm2 within 0.3 % on the part, 405.1 mm2 at 1 %), a click off it a patch round itself, a patch never beyond the limit (a lat-long cap, saddles fine and in strips, the AgileX Piper's facets 60 and 920; Surface and Shrink to fit, both tiers), a face within the limit selected whole (its graph undirected), the outline drawn clean (at most two inner corners), a cap's patch centred on its apex, planar and developable faces (a plate, cylinders fine and in strips, a cone, the LEAP tip) as the Surface preset gives them, the total curvature the region's own; the user's selection refused at both tiers saying how much fits, Shrink to fit fitted whole at 1 % (82 taxels, symmetric; no hidden disk), the boards leaving the surface on the selection's own outline, the lattice along an elongated dome and unturned, a nearly flat pad keeping ARAP's chart; the least-max-stretch chart within 1.15 x a^2 / 12 on analytic caps, the gate on the relaxed sheet (a^2 / 8 at the rim; a chart without the rounds judging the same), its stop rule and its digests (the same on Python 3.9 to 3.12 and Pyodide); the stack (0.2 mm boards, 0.65 mm field), a face bent tighter than the field refused saying so, and the map's bend rules; Whole board on the real stack (2026-11-18, `WholeBoardBendTests`): on a roof of two 18-degree creases the boards and their tails cross both (one board's 2 mm), F stays off them (the laminated field's 6.5 mm: the raster's rectangles, the masked walk's fields, a built field's exact check), the maps pass, Field only as before |
| `test_surface_http` | the `/api/surface/*` routes: framing, 413/415/405/403, every bad value a 422, the header's long numbers, CAD mode's own slot, meshes beyond the JSON limit, the unit through the cache, the 413 of a body just over the limit, `/api/default?template=`; a rounded plate's fit and map, the removed CAD options refused (shape rectangle, the generic template, a rectangle preference) and a saved placement naming them mapped, `tip_first` |
| `test_surface_cli` | `cli.py surface` as a subprocess: the files of `fit --out`, `map` with the placement's selection and `--options` over the placement's (F's records by default, the board's with `containment: board`), exit statuses, NaN picks, invalid JSON, `--unit`, `--base N`; the removed CAD options refused by `fit` and a saved placement naming them mapped |
| `test_surface_contract` | contract details the API review found untested: mesh caps and units, hidden seeds, the operation cap, partly covered walls, unknown keys, error details, the header cap, and what each fit option does on a face with a block standing on it (placement, rotation, objective and side with either containment; the tails' reach with either containment) |
| `test_surface_web` | static checks of `web/cad/` and the vendored three.js: digests, the CAD hook events (and `fpc:board-art`, answered by an async function), no fetch patch, the fit options and limits copied from the server; no Field shape, Board rules or Largest rectangle control (section 26.16); the folds' names, Advanced Customization and More options (2026-11-04); the sensor on the part (2026-11-05): `#sensorOnPart` a `.stacked-canvas` after `#stackedPreview` and outside it, without the left figure's hooks or an SVG; `onpart.js` importing three.js and loaded only dynamically, `drape.js` without three.js or the DOM; its pixel reads and the map comparison with `?probe` only, its buffers reused across Exploded / Assembled, the mode clicked kept by a drawing, every sheet's alpha test as coverage (the review of 2026-11-05), the coverage's alpha never lowering a covered sample's, the sheets drawn after the part and back to front, its grab cursor (the second review); its look (2026-11-05): its lights and studio, `studio.js`'s since the 3D view took them (only `PART_RGB` imported from `viewer.js`, no `addViewLights` left), Khronos PBR Neutral tone mapping on a canvas still transparent, no shadow map, one `console.warn` (once a cause) and the studio's three fallbacks to none, the studio made again on a restored context, every shader edit through `patched()`, the edge bands drawn from the front, the contact shade made on the first Assembled and drawn in Assembled only, the film's face hidden assembled, `render()` building nothing, the positions drawn dynamic; its Exploded home the left figure's as it opens (the user's decision of 2026-11-05): `drape.js`'s tilt and spin `app.js`'s `ORBIT_HOME` and `styles.css`'s `.assembly-camera` defaults (its coin's too), `homeDirection`'s turn of them into the world, Assembled at the same spin nearer the normal, the camera's up the stack's normal set before `OrbitControls` and passed to `frameView`, the arrow keys the left figure's sense; the shader edits' anchors and names of `onpart.js` and `studio.js` in the vendored three.js; the 3D view in the studio (2026-11-05): `studio.js` importing three.js only, its lights, studio and tone mapping, the part's material mirroring it without its diffuse light, every marker made unlit, the studio made twice at most (the renderer, a restored context, never with a model), its reads with `?probe` only, a drag's diffuse material on a software renderer only, swapped at a drag's start and end, picking's non-indexed geometry; the 3D views' light (2026-11-05): `app.js`'s copies of the lights and studio (`studio.js`'s since the merge), the coverlay and the edge bands' shade (`onpart.js`'s) equal to them, the sweep's tints the coverlay's, nothing on the views' 3D elements that flattens them, the light's paths the outline less its cutouts; the film's own lamp (the user's of 2026-11-05): its edit through `patched()` (three.js's `RE_Direct`, its names in the vendored three.js) in the film's material only, aimed per drawing and aspect from the Exploded home (never from the camera as it is), hung on the camera by `place()`, never each frame; the figures' controls in their frames (the user's request of 2026-11-06, `FigureControlsTests`): no bar over a preview, the board cards' tabs "3D view" then "2D view" (the 2D view selected) and the zoom in the frame's controls, the stacked figures' switches there, Reset view over both stacked figures' top right, the drag hints hidden and still the views' descriptions, the controls' places and the phone's 24 px targets in `styles.css`, the zoom's level alone in sight (its scale in the tooltip and its text), the registration's Reset view the way home of 0 and a double click; the 3D view's help line hidden but while the border is edited; the board cards without their layer legends (2026-11-06: no `#rowLegend` or `#columnLegend`, their builder, the windows' names and the swatches gone, each card ending with its preview, rounded as the card's foot); the registration without its caption (2026-11-06: no `.assembly-caption` or its words in the page's files, `setAssemblyMode` setting no text, `separatePin1Rings` keeping its rings apart, off the other triangle, round their own and in the view, no longer off a caption; the oblique view's own caption kept); the guide above the FlexiTac team's footer (2026-11-15): its scrolls stopping at `<main>`'s end (`goTo`, `workEnd`), its last step lit there |
| `test_static_site` | the static site: `app.answer` equal to the server's replies byte for byte (routes, exports, a surface route, the error replies), only `/api/` and the body limits, the build cache; the worker's `bridge.handle` (its 500s); the site build: the page's policy and backend flag, the header's GitHub counts when built with them (optional: none offline or rate-limited, `GITHUB_TOKEN` sent), relative URLs and `apiFetch` only, a reproducible and complete `engine.zip` (it answers from its own files), the Pyodide archive's SHA-256, only an earlier build replaced; the public copy (`tools/export_public.py`): every file its documents link to and the site needs, none of the private notes, the commit's files only, only an earlier export replaced |
| `test_web_theme` | the page's Apple-style theme (`web/theme.css` over `web/styles.css`), read by a small CSS reader of its own (its rules, their selectors and the at-rules around them): `gen.html` (`index.html` until 2026-11-16) links it once, right after `styles.css`, by a relative URL; it loads nothing (no `@import`, `@font-face` or `@layer`, `url()` only `data:`, the system font stack); no animation, scroll or view timeline, `@starting-style`, `content-visibility` or smooth scrolling, nothing fixed or sticky of its own, a transform and a transition only on the disclosure arrows (no colour fades), every transition of the page (`styles.css`'s too) off under `prefers-reduced-motion`; none of the plan's forbidden properties (no SVG styled, the pin-1 rings, the zoom pane's SVG, the stacked view's faces and the view labels untouched, no input's `appearance`, the guide's and the map's sticky boxes, nothing that flattens the 3D chain or its boxes (`styles.css`'s own stale fade there only re-valued), overflow visible on the boxes that hold a sticky one, no flex status or banner, nothing hidden by opacity, one `!important`); a font shorthand with its family, `body`'s size and leading `styles.css`'s; the palette's text pairs at 4.5:1 and its edges and focus ring at 3:1 from the hex values, light and dark and with more contrast; the lightboxes light in every scheme; light by default and dark on the header's toggle (2026-11-06, `ThemeToggleTests`): no `prefers-color-scheme` in `web/`'s style sheets or scripts, every dark rule on `:root:where([data-theme="dark"])` or under `:where(:root[data-theme="dark"])` (each selector of its list), `theme.js` once in each page's `<head>` before its style sheets with no defer, async or module, its storage calls each in a try and light unless "dark" is stored, the toggle the same button on both pages (named Dark mode, aria-pressed, first in `.masthead-end` before the community links, the header's right byte for byte), its moon and sun filled shapes swapped by the attribute in `styles.css` and its look the community's pill; the 3D view's background `viewer.js`'s clear colour; the sensor on the part (2026-11-05) drawn on demand over its lightbox (a transparent renderer, no clear colour or frame loop of its own: one `requestAnimationFrame`, whose callback only renders, since the review of 2026-11-05) and the stacked card split in Gen by Surface only, the split's plan view's scene the window's rules' alone, centred in its pane as in the whole card and scaled by `--plan-fit`, no `.assembly-caption` rule (2026-11-06: the registration's caption, and the room the second review of 2026-11-05 had kept for it, gone); the figures' controls in the light palette with the lightboxes; no `IntersectionObserver` and no smooth scroll unguarded by `prefers-reduced-motion` in `web/`'s JavaScript; the reader and the contrast arithmetic on known values; the FlexiTac team's footer (2026-11-15): section 15 after the form's, its colours the palette's tokens on the header's bar (so the pairs measure them), its headings the guide's title, balanced where they wrap (its review of 2026-11-15), its links at once and underlined with more contrast |
| `test_library` | the Library's data (`web/library/`, the user's requests of 2026-11-05), against `tools/library_write.py` and a reader of its own: every file a third-party file of its `NOTICE.md` table (re-hashed) or the project's own, no vendor model of the deny-list (Robotiq 2F-85 and 3F, the MakerMods body, the xArm gripper's seven split meshes and, since 2026-11-12, UFACTORY's G1 3D file undecimated: the file by its triangles under any header and the sixteen pieces of its split; by SHA-256 anywhere under `web/`, and no part, entry, fit or sample whose id or title names Robotiq, the xArm or UFACTORY; the showcase's decimated meshes only in `web/vendor/ufactory-g1/` at their pins, `ShowcaseTests`), the 12 MB budget (17 MB since the UMI finger's shapes of 2026-11-16), each part's licence open, tabled, pinned to a commit and its change stated; `entries.json` recomputed from `parts.json` and the committed fits, the meshes' facts, the ids, labels (the file note of Gen by Surface within 45 characters, 46 since 2026-11-16), shelf headings (one wording, the count and the range of the pitches and a shelf's families after it: the user's decision of 2026-11-05; since 2026-11-16 the UMI shelf's its shapes, 'Six finger shapes, straight to pointed.') and `start`, each part's 2 mm sensor; every fit's request the one the page sends (the Resolution step's enabled controls at their defaults but the pitch, the fill and the part's rotation, each one its control takes in decimal; the mesh's file name, no unit, browser-style numbers; a control disabled in the page not sent, and a setup the page would send otherwise refused: a base point main.js's round6 changes, a base side, a base point with a border, another objective; no Row traces under Whole board, the second review of 2026-11-05), the UMI finger's 2 mm one the page's shipped default fit; the product rules on every proposal #1 without fitting (one tail pin per line, field-only containment, the tails centred and ending together, a symmetric face's sensor centred, no error or warning and the same build id) and `rules()` naming each broken rule; a staleness sample (each part's 2 mm sensor and the tapered tips' default fitted again, about 6 s); the tapered tips (the family complete, two shapes by five tip widths, its default one of them, closing the UMI shelf with no card or shelf of its own, an incomplete family refused, each tip's change a tip cut tabled as a modified file, its setup the video's on its contact face; since the UMI finger's shapes of 2026-11-16 the family's cards, one per shape, each complete with its height, picture and lines, every tip on one card, ten refusals, and the page's shelf of shapes, `test_the_umi_shelf_is_one_card_per_shape`; since its review the same day the shelf a grid of three to a row, its pictures framed on the fingertip, a shape's page titled by its card and opened Assembled, and each tip's mesh measured against the tool's profile, `test_each_tip_is_cut_by_its_profile`); the writer public and the importer and the tips' cutting tool private, the deny-list the writer's and this one's, the importer keeping no copy of its own and taking the writer's (by its source, when present; the integration's review of 2026-11-05); Python 3.9 syntax; and the page (the same day): library.html's two scripts (`theme.js` in its head, then `library.js`) and three style sheets by relative URLs, nothing inline, its header the generator's byte for byte, the header's Library link on both pages and its style beside the header's rules, never "CAD", no scroll observer, smooth scrolling, transition or absolute URL, the action blue only on Open in Gen by Surface, a sensor's picture 3:1 below 900 px and 16:10 elsewhere, contained and never hidden; the pictures' contract in the script (a card's the Exploded card file, lazy, decoded async, sized, the alt the entry's; a sensor's page's the view asked for; the placeholder for a missing picture or a file that fails; one image, `slot()`'s) and the Exploded | Assembled control (a fieldset with its legend View, radios swapping the picture in place without the address or the history, Exploded on each page opened, gone once both views failed; its thumb grey, its legend for a screen reader only, the phone's page tighter only with it); the grid of 2026-11-06 in the script and the style sheet (the UMI finger alone shelved and any part a family closes, a gripper's card its range and "Pick your pitch" opening its 2 mm sensor, the grippers' section before the shelves, the back links (since 2026-11-15 the window's place, which its X closes to), `#shelf-start` and `#shelf-<gripper>`, Back and Forward by the history's mark, four columns and two below 735 px, no tile); the details window of 2026-11-15 (`dialog#libWindow` with its X first and its scroller, `showModal()` once, the X, Escape, the close fallback and the backdrop's press and release (not a double-click's second) closing to the window's place with no new entry (`history.go` back over the window's entries, each marked with its depth and the visit, or its own entry replaced; the Pitch's replaced address keeping the mark; one close at a time), no back link, its size, look and sheet (on short screens too, no shadow), the root not scrolling and a scroll bar's width made up on its right (`--lib-bar`, no `scrollbar-gutter`), a sensor's page two even columns, the rows' arrows set as the grid is laid out); main.js's `./?part=<id>` (DEFAULT_PART and the shipped test as they were, a family's id its default, the sensor built from its fit's request, the user's own file and Remove model leaving it, each option off its control's default recorded whoever wrote it: a restored form, the integration of 2026-11-05); app.py's `/library.html` and its pictures as `image/webp` (the merge of 2026-11-05); the site build's `library.html`, its gate (ZIPs byte for byte `app.answer`'s exports, files.json, a stale fit stopping it, and a fit of a request the page no longer sends, a page default changed, the review of 2026-11-05); the pictures (`shots/`, the user's request of 2026-11-05): the files the project's own and within their budget (8 MB, the grid's first screen 1 MB), each sensor's `image` the one `shots/manifest.json` gives and none of another fit, every sensor of the shipped Library pictured by a shot of its own fit and build since the set of 2026-11-05 and each drawing centred within a pixel (the shots tool's `centring()`), and on a fixture of two tiny WebPs as `tools/browser/library_shots.py` writes them: the WebP format with alpha at 1280 x 800 and 640 x 400 (each layout's header), `entries.json`'s `image` exactly the contract's (null without a shot), the tool's records the writer's, `library_write.py --check` refusing a sensor without its picture (on a copy of the Library, none fitted; writing only reporting it), a picture of another fit or build refused, a broken one (its bytes, missing, its size, a stray file, a shot of no sensor, no manifest) refused, one of older figure sources (`web/cad/onpart.js` and the modules it imports, each in the hash) pictured with a warning, the site build stopped by a picture of another fit or an `image` the manifest does not give and warning on older sources; the 3D view (the user's requests of 2026-11-05, `docs/LIBRARY_VIEW.md`): the committed scenes current (`library_write.scenes`) and as the user approved them (every gripper but the UMI finger and its tips with its scene, the approved rules: Exploded 65 and Assembled 57 degrees, the 0.28 see-through; both fingers, the jaws fully open, the mate turned on Franka, WidowX 250, Unitree Dex1, MakerMods and the Seeed reBot DevArm (and the AgileX Piper, 2026-11-17) and mirrored on Trossen, ARX and I2RT, the near finger see-through on every gripper, in both views, one stack exploded (the sensor finger's), gap share 0.42 (the user's decision of 2026-11-06), the MakerMods tips on the project's own rail and no MakerMods body), the bodies within 2.5 MB and the art within 0.6 MB, the art, scenes and bodies the files the entries and scenes name, each body's notice row open, pinned and its change stated; on tiny scenes built in the test each check of `scenes()` naming its problem (the mate's kind by its determinant, rigid matrices, the part's mesh, frame, approach, opening, picture, keys and fingers, each body's file, folder, notice and licence, files of no scene, the overrides' bounds and reasons, every gripper and only the grippers, the frozen index, the deny-list over the bodies and `NOTICE.md`, the private importer's inputs); on tiny art and stages each sensor's `view` and a whole gripper's alt text, `entries()` writing them, the transition both ways (`VIEW_REQUIRED`, set since the shoot of 2026-11-06: every sensor's art and view and each gripper's stage in the committed Library), an art of another sensor or build, raster or boards, not the record's bytes or document, missing or not gzip JSON refused, a stray art, a stage of another scene or rules, for a fingertip or breaking each rule refused (since 2026-11-06 the rules' `explode_stacks` and `see_through_modes` and the checks `stacks_apart_min_mm`, `stacks_apart_min_px` and `near_seen_min`, `near_seen` null exactly when the mate's stack explodes), older view modules a warning; the site build stopped by a stale art, a `view` not the manifest's or a scene refused (another part's aside) and publishing `art/`, `scenes/` and `bodies/`; `tools/library_scenes.py` private and never linked; the looks (2026-11-12/13, `docs/LIBRARY_VIEW.md` "The looks"): each scene's looks by `scene_look_problems()` (a name a look of the scene, a colour and numbers within their ranges, every look used, no clear coat on the part's own, the crease angle), the rules' `looks` and `part_looks` as approved (`APPROVED_RULES`: the UMI finger and its tips in `umi-tpu-orange`; a base name held to `base.json`'s numbers), since 2026-11-14 their `part_pad` (the assembled pad's tint, `#545a3a` at 0.65: a colour and an opacity, only with `part_looks`, recorded with the part's look), a picture of another part look or pad refused (`part_look_sha256`), a drawn body the project's own by its name and header, the MakerMods scene its rail and then only its drawn shapes; Gen by Surface's figure of the parts without a scene pinned apart from the Library's look (`tools/browser/generator_figure.json`, a pin of another fit or build refused) and the look held to the part's pixels, the pad's tint to the Assembled sheets (`pad_differences()`); the showcase (2026-11-12/13, `ShowcaseTests` and `ShowcasePageTests`): the vendor folder exactly its twelve pinned meshes and its notice (its words checked) within 2.2 MB, no byte copy of a vendor mesh or of the undecimated file anywhere under `web/`, only the showcase's scene, `NOTICE.md` and `showcase.json` naming the folder, the scene's holder and drawn shapes at their pins, `showcase.json` current (its words; its placed record the pad's own with the showcase's scene; its pictures the files it names, stale with the scene, the rules, the art or the placed record; its stage numbers within the rules' checks and `SHOWCASE_BOUNDS`), the writer's own closing line for its fixes, every gate (`--check`, the site build, `scenes()`) taking it in, the grid's first card and a page of its own, a stale showcase stopping the build; the FlexiTac team's footer (2026-11-15): one `<footer>` on each page after `<main>`, its main block the same on both byte for byte, Awesome-FlexiTac's words, links (targets, rels, the mail) and headings, the Library's fine print its first row, the footer hidden with the grid's title under `data-lib-place`; the generator's Library links in the same tab; the 3D view's drag hint (2026-11-15): its markup and drawing (the arrows the hand's material), its place and its pointer passing through, its size the view's (the host a size container, the drawing 13.4 % of its height between 28 and 44 px, its label from a view 270 px tall, no rule of its by the window's width), shown once drawn, hidden at a mouse's or a pen's main button pressed, a turning key, a double click or a touch's turn (never a touch's press or a right click), kept hidden for a pitch, shown again on another gripper's page or the window opened again, its sway stopped once faded out, and the style sheet's one exception to its rule of no motion (its transitions and its one @keyframes, each off under reduced motion); since 2026-11-17 a hand's further fingers (a scene's `extra_fingers`, rigid, their kind their determinant's sign, the stage's still stacks on them) and a scene's own card override (`checks`: `card_min_px` within 12 to 20, its reason in `about`; `scene_checks()` in the writer and the shots tool), the Unitree Dex3-1's; since 2026-11-18 (the Dex3-1 back) a doubly curved face's fits at the page's curved 1 % (`CURVED_PARTS`, `test_a_doubly_curved_face_is_sent_at_the_curved_limit`: every part's selection curved exactly as listed, the Dex3-1's one dome click, four clicks inside the patch the same patch and one on its flank (facet 11794) a smaller one round itself, its 2 mm fit 13 x 8 = 82 from the writer's job) |
| `test_template_surface` | the surface template `surface_matrix_v1`: profile and policies, dispatch and limits, identity, a DRC-clean sweep, the footprint, exports and pinned values |
| `test_generic_identity_guard` | 200 seeded generic designs keep their builds byte for byte (`tests/fixtures/generic_builds.json`, written before the surface template and rewritten by the plan's section 18, the bus the generic default, and section 20, the bus built with CAD mode's rule set (`diagonal-bus/8`): the 75 bus requests' ids and boards, of which 37 build and the rest are refused by the 7.5 mm tail minimum, the 125 channel ones byte for byte; and by section 24, `diagonal-bus/9`: the 75 bus requests' ids, manifests and the 37 layouts, verdicts and codes held; and by section 27, `diagonal-bus/10`, the Row tail centred: the same, and one size refusal's report, which quotes the outline); under `routing.row_sides` `channel` the same requests keep the verdicts, boards and reports of before (`generic_builds_straight_channel.json`) and 8 of them every export member but the identity carriers (`generic_channel_exports.json`, from 8a4b2f1) |
| `test_surface_identity_guard` | 92 unmasked surface designs (85 seeded, aliases, partial, off-grid, rejected and oversize ones) keep their builds byte for byte (`tests/fixtures/surface_identity_baseline.json`, written from the working tree before the masked field) |
| `test_surface_fit_snapshot` | the raster search's rectangles keep their builds (build ids, metrics, outlines, field frames): since section 26.16 (no shape rectangle in CAD mode) among the whole board's proposals, all 35 recorded rectangles (5 per case) in order, on the soft finger's mount end (the replica, and the real mesh when `asset/` is present), the crank tip pad (when `asset/` is present) and three synthetic plates, `max_taxels` once (`tests/fixtures/surface_fit_rectangle_snapshot.json`; its generic-template cases kept, not run) |
| `test_samples` | Gen by Surface's samples (`web/samples/`, the step guide's "Try a sample"; the user's request of 2026-11-06): the palette under the guide's three steps (a heading, its hint, eight tiles in `samples.json`'s order, each a draggable button described by the hint, titled, its name shown and its kind for a screen reader, its thumbnail sized with an empty alt and not draggable itself, the hint saying click or tap by the pointer; two columns, compact on a desktop window under 920 px high, the guide a flex column over 980 px whose palette's grid, not the steps, gives way, beside the steps from 760 to 980 px, one sideways row under 760 px, the focus rings inside the scrollers' padding, 24 px targets, the theme's tokens and no motion); `samples.json` (two UMI tapered tips of two shapes, four other fingers of distinct Library parts, two whole grippers, each sensor a Library 2 mm one, a whole gripper's mesh record its file's, the UMI tips' thumbnails looking within 25 degrees of their contact face's normal); every file of the folder tabled in its `NOTICE.md` (re-hashed, the licence texts the Library's, the change "assembled from ... decimated") or the project's own, within its 360 KB budget, the thumbnails WebP of 240 x 110 within 8 KB; each whole gripper starting with its Library part record for record, the Library sensor's selection growing over exactly the Library fit's facets and the engine's fit of the page's request giving the Library's build, and, with the scenes line's files present, each STL its scene's assembly byte for byte (a fixture of the assembly's rules too); main.js's index, drag type, `./?sample=<id>`, the drop taking a sample before a file, a sample's part loaded alone (the user's later request of 2026-11-06: no fit fetched, no Library options, selection, fit or build, `./?sample=<id>` as the page opens not built, the default part's and `?part`'s built; `shippedFit`, `ownMesh` and `whenBuilt` gone), a model loaded with no face selected (`inspectMesh` without `autoSelect`), the build below hidden while a model loaded after it has had no Generate of its own (`cad.newPart`: set by `loadFile`, cleared by Generate and a map onto the part, `syncResults` hiding the results, `onResult` and the mode switch mapping no build meanwhile, Remove model leaving the build below), a whole gripper's selection on its finger framed from its camera (`sampleView` in `lookAtSelection`), the drop on the 3D view's whole window, `buildDefaultSensor` settling its own state (its run's `finally`), `loadSample` taking `cad.seq.load` only with its mesh in hand (the default part on its way given way), not loading in Rectangular, the sample on its way live until its part is loaded, the one shown framed again, its warning said again after a build under way (the default part's or Generate sensor's), `viewer.js` `setMarkScale` sizing every marker and `showMesh` giving it a whole gripper's finger; the assembly tool private, the thumbnails' and the checks' public; Python 3.9 |
| `test_library_split` | the Library's looks' tool (`tools/library_split.py`, the user's request of 2026-11-12, [docs/LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md) "The looks"), on small fixtures and on the committed look files (`tools/library_looks/`): the rules that share a body out (a connected component after welding at 0.01 mm by its box and triangle count, the triangles inside a box, the rest; every triangle once), the shapes the project draws (a box, a cylinder, a prism of a convex profile, refused clockwise, in line or twice round: closed, outward, the project's own by name and header), a base look by its name and a part's own with its evidence, what is written (the component files, the scene's bodies, `looks`, `part_look` and `smooth_deg`, `NOTICE.md`'s rows; the same bytes from the unsplit body or from its components), `--check` (a changed file, a stray body, a look or a drawn body without a look file, the showcase's scene's looks its own tool's), the pins (an unsplit body of other bytes refused), the committed files what the look files give, the base looks the document's table and no black under `#1c1c1c` |
| `test_mesh_decimate` | the showcase's decimator (`tools/mesh_decimate.py`, 2026-11-12), on fixtures made by arithmetic alone: a box down to its twelve triangles, an open cap's border kept, every vertex kept a vertex of the input, no face turned more than 15 degrees; the same bytes on every run and Python (pinned SHA-256, no `**` or `pow()`); the gate cutting a looser sequence back to the tolerance both ways; the deviation exact on known planes; the binary STL read and written, `weld()` and `components()`; the standard library alone |
| `test_library_showcase` | the builder of the Library's showcase (`tools/library_showcase.py`, the project owner's decision of 2026-11-12), without the vendor's file: `--check` on the thirteen committed meshes at their pins and the committed scene the one the tool writes (its looks the base table's, `tools/library_looks/base.json`, and seven of its own with their evidence, the fingers' the rules' `umi-tpu-orange` number for number); a source of other bytes refused, a build of other bytes not written without `--repin`; the split on a tiny gripper of boxes (shell, frame, flange, pins, the four links, each finger's coupler cut at the holder and its pins; the sliver, the pad and its screw left out); the pose (the sensors' centres 55 mm apart, the four-bar closed, the holder's holes on the finger's, the left side the right's mirror image, every matrix rigid); the part the gripper's left finger, its straps toward the shell's face without the logo; the drawn shapes (`DrawnTests`, 2026-11-12/13: each a plain shape of the project's own, the screws in the shell's wells and the bolts in the holders' holes, the extender board where the pad's tails end, a shape of other bytes not written without `--repin`); the notices' rows; the guards themselves are `test_library`'s `ShowcaseTests` and `ShowcasePageTests` |
| `test_showcase` | the showcase's sensor, the original hand-designed FlexiTac V2 pad (the user's request of 2026-11-12): `web/vendor/flexitac-v2/geometry.json` (`tools/flexitac_v2.py`: the pinned file, 12 sense and 32 drive lines at 2 mm on one origin, the slots, the A's window, the gold fingers, a trace from every electrode to a finger; the reader on small Gerbers of its own; the rebuild from the official ZIPs where `FLEXITAC_V2_GERBERS` names their folder; its notice, CC BY-NC 4.0, and README's License sentence), the two boards as the engine draws them (which is row and column, which lies outward, the 0.2 mm stiffeners alone), `art.json.gz` (of no build, of this geometry, in the Photo look, written deterministically), the placed record and `web/cad/drape.js`'s wrap (`tools/browser/wrap_checks.js` under node where there is one), and a generated sensor's stack built with no mapper; the normative document naming the showcase's page, its format, keys and pictures |
| `test_flexitac_downloads` | the FlexiTac hardware's own files in the site (the user's request of 2026-11-17): `tools/flexitac_downloads.py` (the pad's two FPC Gerber ZIPs and the reading boards' bundles at their pins, each bundle its Gerber ZIP, BOM and pick-and-place stored in name order with fixed metadata and re-derived byte for byte, what `--check` refuses, the folders' budgets, a write from the guide's files, the site build's gate and `BUILD.json`'s record), the two folders' notices and the README's licence section, `web/boards.js`'s rule at its edges under node (16 x 32 and its swap, 17 x 32, 32 x 32, 33 x 8), on every Library sensor and against `surface/reader.py`'s readers (1 to 40 lines a side), `tailsBoard` (the review of 2026-11-17) at its edges and on every reader's tails, the boards' pins their BOMs' FFC connectors, its files the tool's pins and its guide the generator's, the reading boards' notice naming each board's EasyEDA, the sensor windows' two rows (no Reader row; the dots after a no-break space, the ZIP named in full), the showcase's downloads (two pills, the board's row), Gen's step 3 (the board by the tails, the guide once) and every href `boards.js` names published |
| `test_mask_contract` | the field mask's contract (phase P1): each code at its field, null and full masks as the unmasked design, integral floats, the generic refusal, capped issues, the construction-class gate (phase P2), the inactive-gap warning, `mask` in the identity and the exports' identity fields, masked builds exporting from phase P3 on, the surface schema and limits against pinned pre-mask digests (without what the mask and `routing.row_sides` add), the size advice, the frames by hand and on stacked boards in every tail-side and role combination, the lane taper and the construction classes |
| `test_mask_layout` | the masked boards' builders (phase P2): full spans give today's boards byte for byte (eight designs, also turned, and on the generic profile), anchored masks keep today's routes, contacts, gang window, stiffener and tail, the lane taper's field start, electrode spans and stub ends, the polygon windows and the crossing region P (by area and containment), outlines (simple, counter-clockwise, 0.5 mm from P, following F), every DRC record and the registration passing, the masked keys, the crossings of the stacked boards in all 16 tail-side and role combinations, turned windows, the SVG, the footprint's mask block (and the fillets beside it, within their radius of its concave and tail-root corners), the class gate, pinned digests (3.9 and 3.12), no float `sum()` and no set iterated in order (checked on the syntax tree, the checker included), a 64 x 64 build under 5 s |
| `test_mask_drc` | the masked boards' DRC and registration (phase P2): the plan's corpus (right triangles, quarter disk, soft-finger taper, L shape, trapezoid, 0.6 mm tight, per-electrode windows, 64 x 64) with all 30 records and the registration passing, margin 0.5 from P, the strict window-to-trace rule (exact values), electrode exposure 0.1; tampered boards failing each masked check (P unlike the electrodes, too close or off the board, unsound or outside windows, a window touching the outline passing and one on a cutout failing, bridges to a polygon, routes beside or inside another electrode's window, an electrode outside its window, per-electrode windows); unmasked boards keeping today's semantics; the registration in all 16 tail-side and role combinations, mirrored spans, a too-long electrode, electrodes moved or widened across their length, different masks, the inactive separation (0.05 and 0.4 mm) and touching electrodes, the stack frame; the reported trace-over-trace runs (the soft-finger taper's 83.8 mm, the corpus against an independent measure, none with opposite tails, a Column trace laid on a lane); class refusals naming the first offending row or column; 200 seeded random class A+B designs; 64 x 64 under 5 s; pinned verification digests (3.9 and 3.12); no float `sum()` and no set iterated in order; the geometry helpers; the docs naming every masked key |
| `test_mask_export` | the exports of masked builds (phase P3): a right triangle (polygon windows), per-electrode windows, tails on the right with the columns on top, descending rows and NC contacts, and opposite tails; the usual members plus `taxels.csv`; each polygon window decoded from the GTS as its ring; `taxels.csv` (R x C lines, ROW-major, the mask's active positions, the nets and the pins of `pinout.csv`); the review manifest's `taxel_map` and digest; the order notes' taxel field in its place; one far-end land per trimmed electrode; no taxel map unmasked and a full mask as the unmasked build; polygon windows refused for each form defect (self-crossing, another kind, another shape, rectangle fields, an unmasked board, clockwise, off the grid, slanted, short, closed, non-finite); the read-back catching a bounding-box or moved window, a wrong taxel map (flipped, wrong pin, column-major, short, missing or unexpected) and a missing or miscounted order note; pinned archive digests (3.9.6 and 3.12, any hash seed); the documented sizes and order-note line; the HTTP export routes and `cli.py export` |
| `test_mask_fit` | CAD mode's masked fields (phase P4, `shape: fill` with `containment: board`, explicit since P5d) and readers: the reader option (choices, the `flexitac` alias, the legacy `connector`), the tails' pins per reader, `auto`, the lines and frame index of every reader, a square reader in the metrics and the map, a named reader capping the masked walk (16x16 finds what `max_rows`/`max_columns` 16 find), the metrics and the map naming the same reader (a 16 x 32 readout without a reader is the FlexiTac's); the exact free space against `check_containment` on random rectangles (holes, an obstacle, a bend; with and without an edge margin) and the tails' exit; the fill fit on the right-triangle (pinned proposals), equilateral and disk plates, the crank tip pad (549 of 30 x 33 and four more masks) and the soft finger (the masked 50 x 12 = 470 first since section 21, the 44 x 8 rectangle fifth; 32 x 12 masked within 32 rows), every masked proposal DRC-clean and mapped with every record (metrics, P as the field outline and its coverage, the wrap template's taxels), under 6 s, deterministic; a full mask's build id; the masked stack extent's taper slide; the peel and the re-ranking of a peeled candidate; one mask per readout and no proposal an earlier one dominates; the same count for every placement (the holed plate) and with `role_mapping: auto` at least what either role finds (a wide ellipse); the masked map's crossings, its mask record and readout, an edited mask refused; on the disk's and the wide ellipse's field fits with a diagonal Row bus no flat lane and the Row traces within a few millimetres of the field (3.85 / 6.15 and 3.80 / 5.27 mm with both / left; the wide ellipse's 38-row field of section 21 5.14 / 9.39 mm); the web client's mask (posted with the form, cleared by a rows or columns edit, kept through a mode switch, its server issues in the note with "Use the full field", "N of R x C"); no float `sum()` and no set iterated in order in the new code |
| `test_bus` | the diagonal Row bus's integer-nanometre primitives (`engine/bus.py`, phase P5a), by exact integer predicates of its own: hand chains and offsets at 0, 2.9, 45 and 84 degrees; seeded chains strictly convex with exact orientations, strictly descending, every point in range east of or on the chain, vertices from the input, blind to order, repeats and containers, and the mirrored frame's east chain; offsets at the distance exactly on axis-parallel segments and the distance + 2 nm on slanted ones, the exact perpendicular ends rounded away from the chain, joins on both offset lines and rounded along the normals' bisector, never nearer the chain than the distance (square joins beyond 120 degrees, steps at nearly straight joins); a keep-out's west hull holding every point at the distance from the lane and its continuation (jogs included, where a trim falls behind a short segment); onions of lanes nesting at the pitch with the continuation and the start box in the keep-out (without the continuation the next lane cuts the bend at 0.1598 of 0.2032 mm); a lane turning inward nests the next one exactly one pitch out at its turn (round the mitre it would spread), and every lane without such a turn keeps the mitred offset; the box helpers; a pinned digest of a seeded corpus (3.9 and 3.12), no float `sum()`, no set iterated in order, no libm call but `sqrt` |
| `test_diagonal_bus` | the diagonal Row bus `diagonal-bus/11` behind `routing.row_sides` (phases P5b, P5f, P5h and P5k, and the plan's sections 16, 17, 20, 24, 27 and 27.8), through `generate_design` and predicates of its own: the convex flank (section 27.8, `ConvexFlankTests`: the rule on synthetic rings, the multi-gripper video's WidowX 250 and Robotiq 3F one-sided designs and the corpora's kinds against the build without it, both sides untouched, the named corpus; `_flank_problems` in `_check_clean`: no notch below the field's outline corner on the side without the bus); the centred Row tail (section 27, `CentredTailTests`: an asymmetric field in every side mode and both role mappings, the Row tail centred on it and within it, the funnel's contacts on its centre line, not midway between the innermost lanes; a reader tail wider than the field centred, the rows at positions 1..R, no flat edge below F's bottom but a mirrored build's chord to its lanes; one side's inner flank leaving F's bottom corner on F's side and widening monotonically down to the tail's side, no edge flatter than 45 degrees; the mirrored contacts at the tail's far end from the band, beside it unmirrored; and, from the review of section 27 (27.3), the band's side taken from where the lanes leave their electrodes with four seeded reader designs on fields receding on the band's side (each reported at the wrong end when built with the side flipped), the inner flank's rule where each part decides (no step across F's bottom where the slant is 45 degrees or steeper, the slant meeting the tail's side at its hold, the side monotone below F's bottom: 31 x 2, 29 x 3, 12 x 2, the fin's 59 x 12 and the fine corpus's first design one-sided), and one side's lanes over straight Column copper, 5.667 and 5.529 mm, within the re-bounded 5.7 mm); the convex sides (section 24: no dent of a side from its tip corner to its widest point at most a two-cell step deep on any build, `_convex_problems`; against the build without them the old outline inside the new one, the new within the bound, the copper, the widest and the narrow tip kept, the changed cases pinned; the rule on a synthetic ring: the crank's kink bridged, a deeper pocket and an anchored dent kept); the Column V capped at 80 degrees where that roots the tails no deeper (each named build byte for byte the capped or the uncapped one, whichever roots the tails higher, ties (equal on the layout grid, as the construction's) capped; the fans at 85 where capped, one-sided too since the Row tail is centred); the straight sides (each side from the tip corner down to its widest point, and from there to F's bottom, one line wherever our own enclosing line within 1.0 mm exists, else unchanged; the old outline inside the new one, nowhere more than 1.0 mm outside it; the copper, the outlines more than 1.0 mm below the level, the widest and the relative narrow tip kept; on the named corpus, the regressions and the user's cases, the r4 plate's, the soft finger's and the crank's tip corners and vertex counts pinned, and the rule on a synthetic ring, its bound measured to the outline as filleted on a synthetic staircase); the shared outline's regressions (`tests/fixtures/diagonal_bus_shared_regressions.json`: the judge's one-sided masked fine-pitch designs, whose side over the Column board's staircase is one straight line with 74e90cd's tip, and designs whose Row tail is flush with the shared side, which meets the tail's edge on the level straight or at a filleted corner); regular outlines on every build checked (no vertex above its tail's tip corners, on and below the shared level too, turning by under 5 degrees but on a fillet, by circles of the fillet radius and its halvings; on and below the level a single-step arc's convex partner a flat vertex, but where the other board runs on below the level through it), each outline containing the one built without the regularization to the fillets' steps with its copper and relative narrow tip, the user's CAD fits' vertex counts (crank 325 -> 89) and the named corpus's tip and widest growth pinned, the regularization on synthetic rings (a bent edge, a roof, anchors, a 100-gon); the named corpus (rectangle 32x12, soft finger 59x12, and the crank, equilateral and disk masks of `tests/fixtures/diagonal_bus_masks.json`, at 2 mm, 4 mil, rows on top) with `both`, `left` and `right`: every DRC record, strict record 14, route-route at the trace space, the registration's stack keys (the tails on one side and their overlap), and our own: the fans' crossings with the Column copper at 5 degrees or more (a band beside the field may cross a raised Column stub at any angle), at most two bends per Row and per Column trace below its field and each trace straight down into its tail, no trace part over the other board's electrodes or field window, Row-on-Column runs of 5.7 mm at most off the stacked contact columns, both tails centred on the field (the Row tail within a nanometre in every side mode, its contacts the tail's positions 1..R, at its far end from the band where mirrored), the narrower lying wholly on the wider; pinned tips, widths, Row and Column roots, areas above them, the tails' overlap, the Column board's width and the bands, the bands never farther out than diagonal-bus/1's by more than 0.15 mm at any row but where the shared outline takes the Column board's own body, beside a field that does not recede never farther in either, and its tip never narrower (`tests/fixtures/diagonal_bus_v1_bands.json`), beside the receding disk the Row traces within their bundle and 1.5 mm of an electrode, the two outlines one over the field in the stack (our own clip and vertex sets) and the Row roots with both far shallower, never deeper than diagonal-bus/2's but by the entry-angle guard's allowance; `construction.row_bus` against the outline (the fans off the Column entry angle), its relative narrow tip and its flat lanes against predicates of our own (the rectangle's lanes leave at 16.7 degrees; no flat lane on the named corpus); the funnel (its near and far contacts parting on the field's centre line, half a contact pitch east of it with an odd row count) and one side's single inward fan under the field; the Column board the straight one's copper of the same design without `routing.row_sides` under the shared outline, field for field (from the active region's corner) but its classes, an unmasked design's masked records, its outline and the shared level, and its archive's members; the shared outline down to the tail roots (`tests/fixtures/diagonal_bus_shared_outline.json`: on the named corpus, 19 regressions of the judge's corpus and the user's CAD fits both boards' copper and their outlines more than 1.0 mm below the level are those of each board built with its own outline at that level; the union down to the tails' roots, both tails leaving its bottom edge, the shallower root moved down with its tail as long below it; outlines that differ above the roots fail the registration); the sides seen from outside the stack in both role mappings and the Row tail centred on the Column tail, and the same with the tails on the top, left and right (seen with the tails down; the tails, the record and every stack key as with bottom tails, and the turned bundle exports with the stacked tails); the folded contact order on the pads with `channel_order` and NC contacts; 100 seeded random designs, 30 at fine pitch (W_STACK_TRACE_WINDOW counted), reader tails of 16-64 pins (NC at the far end), narrow and tiny fields, 0.2 mm traces and 1.25 / 0.8 mm, and the regression designs of the design workflow judge and the review (`tests/fixtures/diagonal_bus_regressions.json`: Row roots within 1.0 mm of diagonal-bus/1's, where the prototypes went 50-113 mm deep, or within its noted allowance, and no deeper than diagonal-bus/2's but by rv:186's noted allowance and, one-sided, the centred Row tail's measured cost; the bands and tips of the onion, mirrored reader tails, tail sides slanting from above the field, thin rows clear of the Column windows; the Row tail centred on every one); the stack keys on edited pairs (stacked tails moved aside, widened or lengthened under the other board register, tails on two sides fail, outlines that differ over the field or a Row board without the shared level fail (a Column tail tip moved does not), crossings and a run on a Column trace outside the field reported only, a trace over a Column electrode, one over three counted once and failing without the Column openings, a trace over the Column field window only and the same between per-electrode windows, a warning) and the DRC gate; the codes (E_ROW_SIDES, E_ROW_BUS_TAILS for opposite tails only, a quarter turn E_TAIL_SIDE_PARALLEL alone, E_UNKNOWN_FIELD on the generic template, no E_MASK_ROUTING, E_ROW_BUS_INFEASIBLE, the fans' clash check, the raised corner where the lanes cannot turn down on the field's edge), the identity extra and the exporter's identity fields, the schema and catalogue; the pair built once; a pinned digest (3.9 and 3.12, any hash seed), no float `sum()`, no set iterated in order (the construction, the registration's stack keys and the field's contract), no `hypot` or `dist` |
| `test_generic_bus` | the diagonal Row bus in the rectangular generator, a subset of CAD mode (the plan's sections 18-20, `diagonal-bus/8`; `diagonal-bus/9` since section 24, `diagonal-bus/10` since section 27): the equivalence (on the named generic corpus, the default, the user's 13 x 32, 16 x 16, 32 x 32, 12 x 32 with 32- and 64-pin connectors, every tail side, the Row FPC at the bottom, scan reverse, with both, left and right, and a seeded random corpus of 40, the generic build equals the surface-template build of the same design but for the identity: boards byte for byte, issues, profile, manifest), every build through test_diagonal_bus's predicates (DRC, registration, Row and Column bends, stacked tails, one outline down to the tail roots, regular outlines, straight sides, the narrow tip), one Column lane without a slot, the fans at 60-85 degrees off the V's entry by the guard, the V at 80 and the fans at 85 on the named corpus in every side mode (one-sided too since the Row tail is centred; 82 one-sided before); the rule set (0.5 mm margin, 64 columns, 7.5 mm tails and the 7.5 mm default bottom tail; the channel's 32 columns, 7.0 mm tails and its own default; the generic profile refused for a bus design and the surface one for the channel); the channel kept (generic profile, two lanes and the slot), the default's figures, the folded Row pins in the exports, a digest equal on 3.9.6 and 3.12 and with any hash seed |
| `test_diagonal_export` | the exports of a diagonal Row bus (phase P5c): both sides with ascending and descending Row pins and NC contacts, each one side (one mirrored) and a diamond mask outside the straight classes; the members of a masked build; `pinout.csv`, the netlist's `J1` records and `taxels.csv` with the folded Row pins (computed by hand: 9 rows with `both` on pins 1, 9, 2, 8, 3, 7, 4, 6, 5), the far-end lands of the odd and even rows at opposite ends; every position active without a mask and no taxel-field note; the review manifest's `diagonal_row_bus` against the boards (the stacked tails; no stub drop, shift or neck), the identity extra in both manifests and the recipe, `derived-layout.json`; the read-back catching an unfolded pinout, a record that disagrees with the construction or names a row twice, and a missing taxel map; tampered contact orders refused; pinned archives (3.9 and 3.12, any hash seed); four straight-channel builds' archives pinned as they were before the phase; the figures LAYOUT_SCHEMA, PHASE2 and INTEGRATION quote; the order notes' folded Row pins (phase P5d: on the Row board's notes only, computed by hand, the read-back catching them missing or unfolded); the HTTP export route and `cli.py export`; "one side" in a one-sided bus's order note (the P5d/P5e repair) |
| `test_field_fit` | CAD mode's field-only containment (phase P5d, `containment: field`, `surface/fieldfit.py`): the DP of the largest row- and column-convex field against brute force (the definition) and a reference DP of our own on larger grids, with the filler rows, caps, thresholds and early exit; the full rectangle; the lattice, window and quadrant bounds never under the best field (a 9 x 9 grid with its centre blocked: 56, bound 76 and 56); the lattice against the exact free space (sparse pitches' filler bands); the caps per reader (shaped fields and rectangles alike since section 21) and the pitch ladder; the rank (a turned field with 3 % more taxels: the equilateral plate keeps its unturned 333 against 339 turned 30 degrees, and maps the turned one without the threshold; with several exits the narrowest tip within 3 taxels: the crank pad's 666 on its 70 mm leg under a 14.5 mm tip against 669 on its cut corner, 683 against 686 since section 21); the plan's targets (soft finger 708, with 48x48 620 turned 30 degrees since section 21 (576 before), 384 with 32x16; crank pad 666 (683); right triangle 559, equilateral 333, disk 436) and never worse than `containment: board`, every proposal DRC-clean, registered, its F inside the surface by our own check and mapped with every record passing (`field_clearance`, `strain_under_field`, F's bend, the tails' reach beyond the surface, the readout's `row_contact_order`, the routing report against the fit's), the holed plate's routing over its hole and the plates' square edges (`W_ROUTING_HOLE`, `W_BAND_EDGE_RADIUS`), reader caps, `row_sides`, columns on top, the tails; the map refusing F beside the surface and across the exit, and board containment refusing the proposal; the options; the peel; `field_footprint` and `E_BOARD_SIZE` on the diagonal boards (64 x 8 at 7.22 mm, the advice built); the cost against the board fit (a ratio); pinned fingerprints (3.9 and 3.12, any hash seed); no float `sum()` and no set iterated in order; phase P5e: field-only containment the default with `shape: fill` (the same proposals as an explicit `field`), a map without `containment` taking the design's, and the web client (the Row traces posted with the form on the surface template only and set from every applied design, the Containment and Row traces selects and their sync, the proposal card, the flat view's clip); the P5d/P5e reviews' fixes: an unturned lattice pruned by unturned fields only, every turned proposal 3 % over the exhaustive unturned optimum and rotation none's top found exactly (the triangle, the equilateral at 2.5 and 3 mm, the parallelogram's 105 against its 107 turned), narrow strips and small plates never worse than the board fit and phase 0 on the usable edge, auto finding the best exit (the right triangle at 5 mm), the frames tried listed (also with E_SURFACE_NO_FIT), the narrow tip choosing the exit, both tails ending together, the nearer the extension past the edge or both the shortest tail (since P5-diagonal-bus.md section 27.3 on one line across the boards, the nearest such line since section 27.4, `TailRunTests`' runs of 4 and -15 mm giving 24 mm: the stacked tails' centres and ends coincide on the slanted plate, the holed plate, the disk and the right triangle's legs turned under 12 rows in every side mode, `StackedTailEndTests`; a tail beside the surface past the base side's line continued; the soft finger's stacked tails, the Column tail under the face on the 30 mm Row tail, end 20 mm past it, measured on the outlines), the overhang and the share (holes out) against our own geometry (the overhang past the edge at the tail root's level, beside the surface too), the Row pins by pin with a reversed scan order, a straight design mapped with field containment, a fillet's inner edges and the base edge in `W_BAND_EDGE_RADIUS` (a R0.8 bracket), the work budget (a round-hole plate at 1.5 mm: 532 at about twice the board fit's cost; the meter at a small budget), the early exit near the threshold and the runs beside a column against references, the rectangle search with a threshold; the browser client's fixes (the badge and the CSV of a full field, the pins from the pads, the stale Generate, one map request at a time, the disabled controls' reasons and the tail extension's range); coverage first (section 21, `CoverageFirstTests`): the fin-gripper face (a synthetic plate of its outline) takes the masked 59 x 12 = 569 following its taper, unturned, its tails at the 25.8 mm mount end, ROW_01 the narrowest at the tip, every proposal built and mapped; the cut square's masked 575 before its full 552 (the rectangle preference that could swap them gone with section 26.16); symmetric sensors on symmetric faces (section 22, `SymmetryTests`): the detection (a trapezoid, turned, split sides, vertices moved 0.03 / 0.1 mm, holes, a disk faceted at uneven steps; the plates' exits), the symmetric lattice (columns mirrored, runs free with their mirror images), the symmetric DP against brute force restricted to symmetric runs (zones, caps, windows, rectangles, thresholds), the mirror test and the symmetric peel, the named faces (the long taper's 924 at its 40 mm end before the 937 on a long side, the isosceles base 318 before a leg's 327, the right triangle's hypotenuse 552 before a leg's 562, the equilateral 342, the disk 440, the rounded plates; the fin's 568 before its asymmetric 569, the soft finger's 708 centred and its readers' 576 unturned), a field that breaks the symmetry first only with 20 % more (section 26.19: 119 / 120 / 121 against a symmetric 100 on one exit, across exits, turned and in area, section 22's order across exits, the tip never flipping it; the axis-hole plates' 19.0 % and 21.4 %, the holed plates' turned 396 and 344 first, the isosceles base's 328 before the legs' 341 and 337, the right triangle's hypotenuse 576 before a leg's 595, the isosceles triangle under 12 rows still its base's 74, the holed plate under 12 rows its 285 before its symmetric 232; no turned frame on an exit whose symmetric field holds within 20 %; the crank pad, without a symmetric exit, keeps its 688), the narrow tip, a border (the border's part on the surface tested: an isosceles trapezoid, a right trapezoid, a rectangle beyond the plate's sides, a square inside the right triangle), a pinned fingerprint of a symmetric fit (3.9 and 3.12, another hash seed); the caps keep the exit (section 23, `CapsKeepTheExitTests`): the fin under 32 rows keeps its mount end and fills its tip (32 x 11 = 256 symmetric since section 24, ROW_01 5 wide at the tip, tails 68.07 mm), its 16 rows with 102 mm tails (past 80 mm: the surface's 200 mm), the 200 mm cap on the fin stretched 2.6 times (the capped field at its tip refused, its tails 293.196 mm, and searched again nearer the exit: 16 x 9 with 199.683 mm tails, the tip-first field of its window; the review of section 27.4), the 12 mm tip as the exit gives the far end's 16 rows, and the helpers `tip_rows`, `tip_window`, `far_row`, `keep_exits` and `uncapped`; the corner tolerance at every convex corner (section 24, `ConvexCornerTests`): the rule on hand-made grids (a triangle of runs with one zone blocked at a convex, a concave and an aligned end) and on random staircases against brute force, the crank pad's 696 (683 before: rows 2, 9-12, 19-22, 29-32 one cell longer), every proposal's F on eight faces by our own predicates (P on the surface, F off it only within the margin and reach of F's convex vertices, by at most 0.5 mm) and the map's records, `field_parts` leaving out only convex corners (an aligned pair of runs keeps its margin), the crank's hypotenuse one edge from the tip corner, convex down to the funnel arm, the lanes inside, the convex sides' growth within their bound; the taxels from the fingertip (section 26): the full rectangle's column cap before its zones against brute force (`RectangleCapTests`, 3000 grids), the filler band over the common extent against brute force for both DPs and the lattice's bands against the free space, a pointed tip gaining its row (`FillerBandTests`), the tip step on synthetic candidates (the floor in integers, the share from the exit's most, the p / 8 slack, the displaced lead following, turned, `max_area` and `tip_first: false` untouched, the leads among the proposals), the real pass keeping its group, the per-row DPs and rectangles against brute force, the named faces (the crank's 688 before its 696, the long taper's 842 before its 844, the disk's 24 x 24, the rounded plates full, the exits as before), the tapered plates, section 23's window, the fin plate at 3 mm reaching its tip (the tip-first 246 at 118.85 mm, the 248 next; kept from the quick fix, section 26.14), the report and the pass's budget (`TipFirstTests`; its round 2's tie and `tip_first: false`, `TipTieTests`, and the pass's centred phases, tails' reach and peel fallback, `TipPassTests`; round 3c's reach first, a pointed tip ending in a single taxel); CAD mode without rectangles (section 26.16, `CadWithoutRectanglesTests`: `CAD_ONLY`, every removed option refused in parse and fit, a saved placement naming them mapped as fitted, only the values a fit then accepted, a rectangular selection's full field); section 26.17: the lead's tie in the lead's place (`tip_first: false` keeps coverage alone's proposals, the lead back when its tie is peeled), the displaced field's place and the taxels given, T0's p / 8 slack and ties of more taxels, the pass's floor within the slack (`TipTieTests`, `TipPassTests`), symmetric faces' symmetric fields first (since section 26.19 within 20 %), the symmetric tip share (`SymmetryTests`, `TipFirstTests`); section 26.18: every exit of the fit without the caps keeping its capped fields, each searched when the proposals reach it (`CapsKeepTheExitTests`), a symmetric lead's eighth row phases and its slack (the isosceles triangle's 322 at 57.15 mm, the taper's 351; `TipPassTests`), the taxels given from the lead and its pass, a tip-first tie peeled under the lead leaving it its place, a tie's peel to the lead's taxels keeping it (`TipTieTests`), saved placements' generic-template refusals (`CadWithoutRectanglesTests`); section 26.19, the user's threshold of 20 % on symmetric faces (`SymmetryTests`) |
| `test_easyeda_export` | the EasyEDA Pro projects of the default design, a soft-finger fit, a masked field and a straight channel with a cutout: the archive and the `.epro2`/`.epru` structure like the user's JLCEDA exports, every record's field set against theirs (a fixture, recomputed from the originals when present) and the environment template against them, layers and FPC mode, the PI stiffeners against the profile (0.1 mm since 2026-11-06, 0.225 mm before, each one of EasyEDA's PI options), each line's net with its contact, electrodes and tracks, EasyEDA's element numbering, the schematic channel, the design rules against the board's DRC, the stack; every layer against our Gerbers by scanline fill (`tools/compare_easyeda_gerbers.py`, also its CLI, EasyEDA-style Gerbers and a missing track or moved stiffener found), a cutout as a hole, the reader against EasyEDA's own export of the user's project; pinned digests (3.9 and 3.12, any hash seed); refusals and the read-back; the Direct Gerber archives unchanged; the HTTP route and the web button |
| `test_border` | CAD mode's border of the taxels (`surface/border.py`, [CAD_BORDER.md](../docs/CAD_BORDER.md)): `E_SURFACE_BORDER` (the request's shape, fewer than 3 vertices, not simple, under 1 mm², off the surface, the base and the exit edge, the containment), the exact orientation predicate, the lattice's cell predicate against brute force and its runs capped by the border; a border inside a plate placing every taxel inside it, one partly beyond the surface, a quadrilateral and a non-convex one; the border's exits (`border_edge`, `auto` over its longest edges, a clockwise border, turned frames); the map's `taxels_inside_border` (passing, failing, its tolerance, absent without a border, a damaged placement border); `facets_uv`; a strain-limited fit carrying the border onto its disk; determinism |
| `test_docs_consistency` | the tables and Python snippets of these documents and the quoted figures it lists against the code and generated boards (including the INTEGRATION side and stack tables), this test map, the mutation summary, that every mutation-catalogue edit still applies and edits a public file (`tools/export_public.py` PUBLIC: the public copy's CI runs the same check, the integration's review of 2026-11-05), the CI description, links, paths, `pyproject.toml` (T) |

`tests/geometry_checks.py` re-implements the geometry predicates the tests
use, so an engine defect cannot hide itself.  HTTP tests start
`app.AppServer` on an ephemeral loopback port; CLI tests run `cli.py` as a
subprocess.  The older modules regenerate the default design where they need
it (about 100 times per run, 0.057 s each, under a tenth of the run); the
stage-T and stage-G modules generate once per class.  Tools are not part of the suite:

- `tools/mutation_check.py` applies known defects (the audit's 36 baseline
  mutants and the C1 extras re-expressed for the current code, plus mutants
  of every fix stage and of the documents) to scratch copies and runs the
  suite on each.  Catalogue of 2026-11-18: 1307 mutants, 1302 expected killed (the Unitree Dex3-1 back,
  `fpc-int-n-dex3-back`: `UNITREE_DEX3` again, 8: `S/dex3-scene-two-fingers` re-anchored on the restored scene,
  `S/dex3-curved-everywhere`, `S/dex3-curved-options-flat`, `S/dex3-job-flat`, `S/dex3-stretch-budget-any`,
  `S/dex3-override-loose`, `S/dex3-notice-unmodified`, `S/dex3-trademark`; `CURVED`'s `S/library-flat-unread` and
  `S/library-curved-unchecked` re-anchored on `page_options()` and `part_options()`; each killed alone by `test_library` on a
  scratch copy, 10 of 10, and again after its review's fixes (478ba2b) with `HAND_MECHANISM`'s 15, 25 of 25; before them
  1299 mutants, 1294 expected killed: Whole board on the real stack's review,
  `fpc-int-n-curved`: `CURVED` 47 -> 49, `S/field-bends-strict-search-dropped`, `S/field-bends-strict-search-unkept`, each killed
  alone by `test_surface_curved` on a scratch copy, 2 of 2; before them 1297 mutants, 1292 expected killed: Whole board on the real
  stack, `fpc-int-n-curved`: `CURVED` 41 -> 47, `S/board-bends-field-rule`, `S/field-bends-dropped`, `S/field-bends-walk-unchecked`,
  `S/field-bends-raster-unchecked`, `S/field-bends-built-unchecked`, `S/field-bends-block-tails`, each killed alone by
  `test_surface_curved` on a scratch copy, 6 of 6; before them 1291 mutants, 1286 expected killed: the review of the symmetric, larger
  selections fixed, `fpc-int-n-curved`: `CURVED` 29 -> 41, `S/holes-unfilled`, `S/ring-taken`, `S/mirror-plane-unfitted`,
  `S/mirror-plane-turned-first`, `S/dome-axis-off-plane`, `S/mirror-closure-late`, `S/sides-unmirrored`, `S/exit-off-trace`,
  `S/symmetry-axis-chord`, `S/traces-none`, `S/centre-off-face`, `S/library-strict-chosen`, and `S/stretch-click-outside` re-expressed, each
  killed alone by its killers' module on a scratch copy; before them 1279 mutants, 1274 expected killed: gently curved faces symmetric and larger,
  `fpc-int-n-curved`: `CURVED` 22 -> 29, `S/mirror-closure-off`, `S/mirror-planes-none`, `S/mirror-apart-joined`,
  `S/curved-limit-flat`, `S/curved-limit-everywhere`, `S/library-flat-unread`, `S/library-curved-unchecked`, each killed
  alone by its killers' module on a scratch copy, 7 of 7; before them 1272 mutants, 1267 expected killed: the trim of the
  Allegro Hand and the Unitree Dex3-1 merged into gently curved faces, `fpc-int-n-curved`; the trim's 1254 mutants, 1249 expected killed: the Allegro Hand and the Unitree Dex3-1
  removed the same day, `fpc-int-n-trim-hands`: `UNITREE_DEX3` and `ALLEGRO_HAND` retired, their mutants of the hands'
  mechanism one group, `HAND_MECHANISM`, 20, their ids kept, each killed alone again by `test_library` on a scratch copy
  with the LEAP Hand alone (`LEAP_HAND`'s 10 too), and five retired whose edits were the two hands' own text:
  `S/dex3-scene-two-fingers`, `S/allegro-links-not-own`, `S/allegro-thumb-solid`, `S/allegro-thumb-base-ghosted` and
  `S/allegro-border-pieces`; before the merge, gently curved faces' 1277 mutants, 1272 expected killed: the review's fixes of gently curved faces,
  `CURVED` 16 -> 22: eight added, `S/relaxed-ignored`, `S/stretch-beyond-kept`, `S/stretch-same-patch-stops`,
  `S/stretch-click-outside`, `S/face-graph-directed`, `S/face-whole-untried`, `S/outline-unfilled`, `S/no-fit-bend-unsaid`;
  four changed, `S/stretch-omega-only`, `S/least-stretch-off`, `S/least-stretch-everywhere`, `S/strain-check-facet`; two
  retired as equivalent, `S/stretch-axis-from-click`, `S/stretch-on-any-face`; the twelve added or changed run with
  `--only` on a scratch copy of 4d4f83f, 7 in parallel: baseline passed, 12 of 12 killed, 2011 s; the 22 of `CURVED`
  each killed alone by `test_surface_curved`).  Before them 1271 mutants, 1266 expected
  killed (16 of gently curved faces, `CURVED`, on
  `fpc-int-n-curved`: a curved selection beyond the limit fitted, the refusal's area unsaid, the dome's axis from the click,
  the regula falsi skipped, stretch on any face, the total curvature beyond the region, the least max stretch off, on every
  chart or never stopping, the facet judged, the axis ignored, fields turned, the stack of before, the strain checks on the
  facet, the tier sent as text by the page or the writer; each killed alone, the full suite on a scratch copy of 422edbd
  with `T/doc-test-count` moved to the new count: 17 of 17 killed, baseline passed, 1219 s; with them
  `S/no-strain-gate`, `S/side-renumbered`, `S/strain-bisect-cold` and `S/strain-repeats-count` retired with the strain-limited
  disk; 1259 before, 1254 expected killed, of which 1 of the verification of the merge of the
  Library's lines of 2026-11-17, `MERGE_VERIFY`: `test_library` reading the private scene builder unasked, killed alone by
  `test_static_site` on a scratch copy; at that verification `S/allegro-bsd2-closed` and `S/leap-key-folder` retired, on the
  merged files the edits of `R/robotiq-bsd2-closed` and `S/piper-key-folder` (the hands' 37 below are 35 since, `LEAP_HAND` 10, `ALLEGRO_HAND` 9); `X/pinout-index` and nine `F/on-part-`
  mutants expected killed, the suite kills them (the folded row order, the pinout rows and the archives' pins; for the nine
  `ShowcasePageTests`' pin of the showcase pictures' sources, for two of them `test_showcase`'s wrap and `test_surface_web`'s
  film lamp too); `M/diag-shared-no-ear`
  expected to survive, equivalent since diagonal-bus section 20; `G/stackup-check`, `S/map-infinite-record`,
  `S/centre-line-obstacles` and `M/field-budget-windows`, which the full run of that day found surviving (on 2d60728
  too), killed by tests of their own; the sixteen it added or changed run with `--only` on a `git archive` copy of b72d48d,
  baseline passed, 15 killed and `M/diag-shared-no-ear` surviving as expected, 1691 s with 9 jobs; 4 of the merge of the Library's lines of 2026-11-17, `MERGE_FINAL`: the showcase's pill at the guide's top or under its old label, the Galaxea R1 Lite's border clockwise again, the reBot part's row without its CERN-OHL-W-2.0 text, each killed alone by `test_library` on a scratch copy; the merge re-anchored 19 of the lines' mutants on the merged files, each killed alone again: the deny-list's three of the Robotiq line on the joined expression, the two BSD-2-Clause and the YUBI's CERN-OHL-W-2.0 on the one `OPEN_LICENCES`, the six trademark mutants on the sorted list, the LeFlexiTac's, the R1 Lite's and the RB-Y1's places in the merged grid, the R1 Lite's border, the LeFlexiTac's recipe key and the YUBI's two NOTICE sentences; 5 of the review of the UMI cards zoomed on the tip of 2026-11-16, in `CARDS_ZOOM` too: the cards zoomed 1.35 again (the finger's base on the card's bottom edge), the finger's base unchecked, the card's bottom margin unchecked (a whole drawing framed lower taken), the base read as the whole drawing's bottom, the card's read not held to the Exploded home's direction, up and explode, each killed alone by `test_library` on a scratch copy; 17 of the UMI shelf's cards zoomed on the tip and the showcase's card Exploded (the user's decisions of 2026-11-16: "你可以show gripper的angle但是zoom in了，就是方向还是那个方向，但是用zoom in +exploded,那就可以tell了", of zoom 2 "你现在zoom in 的太过了，tactile的tail都看不到", of the xArm card "Switch to exploded"), `CARDS_ZOOM`: no card framed, the UMI cards zoomed 2 again, a tip's frame not its family's, a record's card frame unchecked, the tip's place, the sides or the window unchecked, a frame of a part at no gripper's home taken, the card read at the pictures' own pane (a crop upscaled, no render), the sensors shot with no frame, `--check` blind to the frame, `--check-generator` shooting the pictures without it, the window from the tip itself or at the drawing's left edge, the showcase's card Assembled, its view and its page Assembled, each killed alone by `test_library` on a scratch copy, with `S/library-showcase-exploded` of 2026-11-12 retired (the page opening Exploded is the wanted behaviour now, its reverse `S/zoom-showcase-page-assembled`); 4 of the review of the Robotiq 2F-85 of 2026-11-16, `ROBOTIQ_REVIEW`: a 3D model under `web/` whose path names the 2F-85 taken at any SHA-256 (a copy of the user's own `2F85_Opened.stl` under another header and a 2F-85 name published), only the bodies' folder held, STL alone held, the pad's body unpinned, each killed alone by `test_library` on a scratch copy; 8 of the Robotiq 2F-85 of 2026-11-16 (the user's request "是不是可以加一个 robotiq的gripper card" and decision "Menagerie model"), `ROBOTIQ`: every Robotiq name refused again, any Robotiq name taken, the user's own 2F-85 file taken by its name or off the deny-list's hashes, BSD-2-Clause no open licence, the 2F-85's near finger solid, its sensor on the silicone pad's back face, its housing's look not its look file's, each killed alone by `test_library` or `test_library_split` on a scratch copy; 2 of the review of the authors' permission of 2026-11-17, in `LEFLEXITAC` too: a permitted entry without its day or who gave it taken as a permission, `permission()` taking any day and name, each killed alone by `test_library` on a scratch copy, with `S/leflexitac-permission-undated`, `S/leflexitac-permission-licence-unread` and `S/leflexitac-permission-row-unread` re-anchored on the new code (killed alone again); 6 of the user's word of 2026-11-17 on LeFlexiTac's files, in `LEFLEXITAC` too: the permission's words undated, a part's licence or a NOTICE row taken whatever permission it says, the site build and the export refusing the permitted rows, a pending entry's part taken as permitted, the page's 'Licence not stated' where the permission is recorded, each killed alone by `test_library` (the fourth by `test_static_site` too) on a scratch copy, with `S/leflexitac-pending-refused`, `S/leflexitac-licence-label` and `S/leflexitac-open-by-upstream` re-anchored on the new code (killed alone again), and `S/leflexitac-pending-any-source` killed again (a row of another source naming no upstream: it had survived since the credit of the review below); 6 of the LeFlexiTac's review of 2026-11-17, in `LEFLEXITAC` too: the site build never refusing the files stating no licence, its command line a local preview always, the public export writing them, a pending row or a part's holder taken without the credit of the SO-ARM100 part its file was remodelled from, a body's NOASSERTION row taken as open for that part's Apache-2.0, each killed alone by `test_library` or `test_static_site` on a scratch copy (the importer's own recipe has none: the importer is private), with `S/leflexitac-pending-refused` re-anchored on the writer's new branch (killed alone again); 9 of the LeFlexiTac (the user's request of 2026-11-16: a LeFlexiTac card first in the Grippers), `LEFLEXITAC`: the LeFlexiTac after the Franka Hand, a NOASSERTION row taken from any source, the pending entry never read for a body, a part's NOASSERTION licence taken whatever its text, a one-word id taken as a recipe key, 'Licence (NOASSERTION)' on its page, the site build silent of it, its scene at the rules' gap share, its other finger's sensor off the static jaw's face, each killed alone by `test_library` on a scratch copy; 10 of the AgileX Piper of 2026-11-17, in `AGILEX_PIPER`: the writer's recipe-key check refusing an upstream model's folder (`agilex_piper/`) or a key after "-" (`mujoco_menagerie-agilex_piper.txt`) again, the Piper's other finger 64 mm across the jaws, its border askew, and the review's 6: the part, the scene's opening or a NOTICE row pinned at `f3b6013` again, the scene's plate with two guide rails, the fingers drawn as a metal, their look based on a printed black, each killed alone by `test_library` on a scratch copy; 8 of the review of the Galaxea R1 Lite of 2026-11-17, `GALAXEA_R1_LITE_REVIEW`: GalaxeaManipSim's carried NOTICE without its row, unnamed by the finger's row, unsaid in the source's paragraph, G1 not among the trademarks, the drawn carriage in the finger's grey, its fillet left out of the boxes, the bar's box run up the contact face, the fingers called printed nylon again, each killed alone by `test_library` on a scratch copy, with `S/galaxea-trademark` re-anchored on 'G1' and `S/galaxea-mate-nearer` run again, each killed alone again; 9 of the Galaxea R1 Lite of 2026-11-17, `GALAXEA_R1_LITE`: its licence text another holder's, NOTICE.md naming the README's MIT for the LICENSE's Apache-2.0, Galaxea and R1 Lite not among the trademarks, its other finger called the mirror image, the jaws half open, the near finger solid, the other finger 26.9 mm nearer, its border moved onto the carriage's notch, its card before the MakerMods Metal Arm's, each killed alone by `test_library` on a scratch copy; 9 of the Seeed reBot DevArm of 2026-11-17, `SEEED_REBOT`: its part said unchanged, its scene not fully open, its mate called a mirror, its drawn actuator uncredited, its source and its maker's names left out of NOTICE.md, and, after that day's review, its part's modified-file note losing its opening, its pockets no longer said to seat the grip pads, Seeed's CERN-OHL-W-2.0 grant of the same meshes left out of its source, each killed alone by `test_library` on a scratch copy; 3 of the xArm Gripper's grey pad (the user's word of 2026-11-17, "xarm grey pad"), `XARM_GREY_PAD`, `S/xarm-pad-*`: the drawn pads in the finger's black, the other finger's pad on the sensor finger (solid through the see-through near finger), `NOTICE.md` without the pads' credit, each killed alone by `test_library` on a scratch copy (the look file and its scene edited alike, so `test_library_split` passes), with `S/xarm-scene-closed` re-anchored on the mate's own matrix (the other pad's matrix holds -140.93 too), killed alone again; 7 of the xArm Gripper's card (the user's word of 2026-11-17, "xarm原装夹爪"), `XARM_GRIPPER`, `S/xarm-*` (`X/` before its review that day): the deny-list letting any name after the card's id pass, or any after its id and a "." (not only the Library's extensions), or Menagerie's folder with any "." after it, or a name that begins with its title, or refusing every xarm and ufactory name again (its xArm lines alone), the scene's other finger 86 mm nearer, the other finger called the mirror image, each killed alone by `test_library` on a scratch copy; 14 of the Rainbow RB-Y1 of 2026-11-17, `RAINBOW_RBY1`: its pad's top strip selected again, its card not the grippers' last, its mate called a mirror, its near finger solid, its approach flipped, its makers' names not among the trademarks, the review's 3: its pad the model's light grey again, its photos called the v1.3 gripper's, its meshes said to be derived from `rby1-sdk`, and the 1.2 gripper's 5 (the lead's decision of the same day): its mate unturned as the model leaves `ee_finger_r2`, its gripper 20 mm low, its about naming `rby1m_1.3.xml`, `NOTICE.md`'s source the v1.3 `EE_GR_TF` again, the project's top ring drawn again; each killed alone by `test_library` on a scratch copy; the top ring's 2, `S/rby1-ring-uncredited` and `S/rby1-ring-unsized`, retired with the v1.3 gripper; 13 of the OpenArm of 2026-11-17 (the user's request of that day: the grippers' eighth card, Enactic's OpenArm 1.0 gripper from its open model), `OPENARM`: `NOTICE.md`'s trademarks without Enactic and OpenArm, a body of openarm_description's tabled under HandUMI's licence text, its other finger called the mirror image, its jaws short of full opening, its near finger solid; `OPENARM_REVIEW`: the card titled "OpenArm" again, the scene's about not saying it draws 1.0's parallel_link gripper, the looks said after openarm.dev's hero photo, `NOTICE.md`'s row and `parts.json`'s holder crediting HandUMI alone; `OPENARM_TIP` (the user's correction of that day, the fingertip pad alone): the face grown from the cradle again, the base at the pad's rounded end, 3 mm again; each killed alone by `test_library` on a scratch copy; 4 of the YUBI Gripper's review of 2026-11-17, in `YUBI` too: its scene's approach back at 16 degrees open (the near sensor a line), its page's line the file code again, `NOTICE.md`'s bodies' section without its exception, ELP out of the trademarks, each killed alone by `test_library` on a scratch copy, with `S/yubi-fully-open` and `S/yubi-trademark` re-anchored; 11 of the YUBI Gripper of 2026-11-17, `YUBI`: its card titled Generalist again, its sensor grown from the pad's arch, its licence said Apache-2.0, CERN-OHL-W-2.0 no open licence, its scene said fully open, its mate called turned, a changed body's note undated, its bodies' CERN-OHL-W-2.0 terms unsaid, its drawn servo uncredited, its names out of the trademarks, its licence text changed, each killed alone by `test_library` on a scratch copy; 37 of the three hands merged on `fpc-int-n-hands`, one mechanism: `UNITREE_DEX3`'s 16 the mechanism's, `LEAP_HAND`'s 11 (its five copies of them dropped), `ALLEGRO_HAND`'s 10 (its eight of its own key `fingers` retired, its frame and still stacks re-anchored on `extra_fingers`, its middle finger's links its own added), each killed alone by its test of `test_library` on a scratch copy; of them, from the lines: 16 of the Unitree Dex3-1 of 2026-11-17, in `UNITREE_DEX3`: a scene's extra_fingers unchecked, an extra finger's kind not held to its determinant, the checks override unbounded, ignored by `scene_checks()` or taking every key, the shots tool holding a shoot to the rules' checks alone, the stage drawing no further finger or measuring none of their stacks, the middle fingertip gone from the scene; and 7 of its review that day: the override on a two-finger gripper's scene, a hand's `extra_seen` unchecked, a hand's record or shoot checked as a two-finger gripper's, a further stack's clearance measured to its own fingertip, its top FPC unmeasured in Assembled, a hand's numbers without `extra_seen`; each killed alone by `test_library` on a scratch copy, with `S/library-view-rule` re-anchored on `scene_checks()` and the hand's extras (killed alone again); 3 of the tool menu's order of work of 2026-11-17, in `MENU_STEPS`: Edit border renamed by its whole text again (the word Optional gone), Select a surface's number read out, Optional left on Done editing, each killed alone by `test_surface_web` on a scratch copy; 10 of the review of the FlexiTac hardware's files of 2026-11-17, in `BOARDS` too: `tailsBoard` by the lines alone or giving sized tails the board their pins fit, the 32 x 16 board's connectors 16 and 16, Gen's step 3 not reading the connector pins, the board's dot free to start a line in a window or in step 3, its ZIP unnamed to a screen reader, the Ordering notes linking the guide again, the reading boards' notice calling both boards EasyEDA Pro's, the reading boards' downloads under a folder the site does not publish, each killed alone by `test_flexitac_downloads` on a scratch copy, with `B/showcase-board-gone` re-anchored on the showcase's board row (killed alone again); 13 of the FlexiTac hardware's files of 2026-11-17, in `BOARDS`: `web/boards.js`'s rule taking 17 lines on the smaller side, 33 on the larger, or rows and columns as they come, a board's size not its bundle's, a sensor's window without its two rows, the showcase without its reading board, Gen's board never refreshed, the bundles' members unsorted or dated otherwise, their members not held to their pins, the reading boards' budget loose, the site build's gate off, Gen's guide another address, each killed alone by `test_flexitac_downloads` on a scratch copy; 5 of the review of the cards aligned of 2026-11-16, in `CARDS_ALIGNED` too: the showcase's near finger solid again (its own pad hidden whole behind it from the grippers' homes), its near_seen and ghost_cover not held to the rules, its opaque_max unbounded again, `--check-generator`'s witness at the grippers' homes drawn at the figure's, its sixth comparison (the look and the tint at the grippers' homes) skipped, each killed alone by `test_library` or `test_library_showcase` on a scratch copy, with `S/aligned-showcase-bound` re-anchored on the two bounds (killed alone again) and `S/showcase-see-through` of 2026-11-12 retired (the near finger see-through is the wanted behaviour now); 15 of the cards aligned with the grippers (the user's request of 2026-11-16: "图一中umicard图太大，确保你要和上面的card大小保持一致 ... 你做成和这个finger一样的空间角度，而且可以做成exploded ... 最上面的xarm gripper的空间朝向也要跟下面的这些家爪都对齐"), `CARDS_ALIGNED`: the UMI shelf three to a row again, a shape's card its Assembled picture, a UMI page opened Assembled, the rules' home never handed to the stage, the aimed part's camera's up the figure's, its homes the figure's directions, its explode Gen by Surface's, its film lit by the figure's lamp, the writer's part_homes unchecked or naming a gripper, part_look() without the home, --check-generator serving the rules without the home or holding the look at the grippers' homes, the showcase's own camera again, its old bound, each killed alone by `test_library` or `test_library_showcase` on a scratch copy, with 8 retired (`S/umi-shapes-shelf-exploded`, `-assembled-card-file`, `-four-a-row`, `-tip-unframed`, `-tip-frame-lost`, `-page-exploded`, `S/showcase-camera-front`, `V/showcase-exploded-camera`) and 4 re-anchored (`S/library-picture-card-full`, `-view-kept`, `-look-part-gripper`, `-pad-unrecorded`), each killed alone again; 7 of the review of the UMI finger's shapes of 2026-11-16, `UMI_SHAPES_REVIEW`: the UMI shelf four to a row as the grippers' (4 + 2), a shelf's card's picture the whole finger (the class not put, or its frame's rule gone), the heading's count of shapes no unit ('Six / finger shapes,'), a shape's page titled 'UMI Fin-Ray Gripper, tapered tip', a UMI shelf's page opened Exploded, the 9.8 mm concave and convex arc tips' meshes swapped in `parts.json`, each record its file's hash (killed by `test_each_tip_is_cut_by_its_profile` alone among the measures; a mutant of the private `tools/library_tips.py` is out of the catalogue, whose files are the public copy's: the test pins the tool's `half_width()` to its own where the tool is), each killed alone by `test_library` on a scratch copy, with `S/library-view-kept` re-anchored on the card's first view and `S/umi-shapes-cards-dropped` on the shelf's grid, each killed alone again, and 3 retired with the UMI shelf's row that scrolled sideways (`S/library-row-reveal`, `S/library-shelf-card-margin`, `S/library-window-arrows-unset`); 13 of the UMI finger's shapes (the user's request of 2026-11-16: "我在这里更多想要体现umi不同shape我们都可以fit", one card per finger shape on the UMI shelf), `UMI_SHAPES`: the shelf's own card named by the gripper's title, the shelf without its families' cards, a shape's page showing its axes of one choice, every tip's Tip fact over 75 mm, the grippers' cards made by `map(gripperCard)` (every id but the first's lost), 'straight to pointed' no unit, the Short taper's card without 'Pick shape and width', the writer taking a family whose cards miss a tip or a card naming a foreign sensor, a shelved part's card name left out of `entries.json`, the labels at most 27 characters again, and of the lead's review the same day the shelf's cards in the Exploded view again and sized as a card file, each killed alone by `test_library` on a scratch copy, with `S/library-picture-card-full` re-anchored on the card's Exploded file (killed alone again), `S/library-shelf-family` (the long wording on a gripper's shelf), `S/library-shelf-families-unsaid` (the shapes unsaid) and `S/library-grid-umi-first` re-anchored on the writer's and the page's new lines and `S/library-family-grid` on a card's grid, each killed alone again; 7 of the review of 2026-11-16 of the first page and Design your own, `FIRST_PAGE_REVIEW`: `forward.js` without its `hashchange` listener (`./#rect` typed over the open Library: "No sensor in the library is named rect."), `library.js`'s `route()` at a hash being sent on, a Library shown again by the back-forward cache left hidden, `app.py` asking for the forwarding page's counts as any page's, `index.html` without `counts.js` (the site's first page keeping the build's counts), `counts.js` asking GitHub on `app.py`'s pages or on a Library being sent on, each killed alone by `test_library` or `test_static_site` on a scratch copy, with 4 of `FIRST_PAGE` re-anchored on `forward()`'s lines and `S/library-place-kept` on `route()`'s guard; 7 of the review of 2026-11-15 of the drag hint and the team's footer: in `LIBRARY_DRAG`, the hint sized by the window's width again (small without its label on a tablet's wide 3:1 view and the showcase's tall one, full over a 900 px window's short view), a touch's press hiding it (a phone's vertical swipe that scrolls the window), a right or middle click hiding it, a touch's turn leaving it swaying, a touch screen's double tap leaving it, its arrows the ink's again (grey on the black bases), each killed alone by `test_library` on a scratch copy, with `S/library-drag-stays` re-anchored on the main button's press of a mouse or a pen, killed alone again; in `TEAM_FOOTER`, the footer's headings unbalanced ("Team" alone on a line), killed alone by `test_web_theme`; 16 of the Library as the first page (the user's decisions of 2026-11-15 and 2026-11-16: "我觉得之后可以让lib作为第一次点击进入时候使用的界面", "是的 be first page"), `FIRST_PAGE`: `web/forward.js` leaving `./#rect` or `./?part=<id>` on the Library, forwarding by `location.assign` (an entry of its own), dropping the query, not hiding the page, sending the Library's own addresses to `./` (a page that reloads for ever), forwarding on any page (the generator's own for ever), `library.js` running on a page being forwarded, `index.html` loading `forward.js` after `theme.js`, the Library's Rectangular at `./#rect` and Open in Gen by Surface at `./?part=<id>` again, `app.py` without `/gen.html` or with the generator at `/`, the site build asking the forwarding page for counts, writing no `gen.html` or reading the gate's request defaults from the Library's page, each killed alone by `test_library` on a scratch copy; 6 of the showcase's Design your own (the user's decisions of 2026-11-15 and 2026-11-16: "在flexitac on xarm的details 后面，多一个按钮，generate sensor by yourself with cad file", named "Design your own"), `DESIGN_OWN`: the pill missing, in a new tab, without its name for a screen reader, before Details, grey, at Open's size, each killed alone by `test_library` on a scratch copy; with the pages' move 7 re-anchored on `gen.html`, `index.html` and `main.js`'s `./#<id>` (`X/easyeda-button`, `M/web-theme-system-meta`, `M/web-library-link-new-tab`, `M/web-library-note-new-tab`, `M/web-footer-pages-differ`, `M/web-footer-same-tab`, and `S/library-route`'s words), each killed alone again; 7 of the drag hint on the Library's 3D view (the user's request of 2026-11-15: "箭头能不能做成像schetchfab一样的动画", Sketchfab's hint drawn for the page in place of the turn's mark of that day, whose 2 `LIBRARY_TURN` mutants are retired with it), `LIBRARY_DRAG`: the hint taking the pointer, shown over the picture before the view is drawn, a press no longer hiding it, shown again for each pitch of a page already turned, not shown with the window opened again, its sway running unseen once faded out, its sway under reduced motion, each killed alone by `test_library` on a scratch copy; 6 of the FlexiTac team's footer (the user's request of 2026-11-15: Awesome-FlexiTac's footer under the generator's two modes and the Library, in the page's own palette), `TEAM_FOOTER`: the Library's footer not the generator's (YouTube left out), the footer's GitHub link in this tab on both pages, its links in the third grey (3.5:1 on the header's bar), the team's footer shown while a window's own address loads, the guide's scrolls past `<main>`'s end into the footer's room (the sticky guide pushed up), its last step lit only at the page's end, each killed alone by `test_library`, `test_web_theme` or `test_surface_web` on a scratch copy; 2 of the Library in the same tab from the generator (the user's request of 2026-11-15: "改成直接跳过去 不重开页面"), `LIBRARY_SAME_TAB`: the header's Library link and step 1's file note's link in a new tab again, each killed alone by `test_library` on a scratch copy; 11 of the details window's review of 2026-11-15, in `LIBRARY_WINDOW` too: a close from the grid pushing a new entry (with Android's Back a close request, Back closing it and opening it again for ever), a close on its way asked twice (two entries back, out of the Library), an entry's depth believed after a reload, a pitch's replaced address dropping the entry's mark, a close come back to the grid leaving its address or showing the grid as Back does (a window reached by Back focusing another card), a double-click's second click closing it, the bar's room kept by `scrollbar-gutter` (bright beside the backdrop, 100vw shrunk), a sensor's page 7 to 5 in the window again (its facts' column 440 px at 1440 px), the sheet by width alone (a landscape phone's 306 px card), the dark sheet's hairline framing the screen, each killed alone by `test_library` on a scratch copy, with `S/library-window-drag-closes`, `-jump` (now a window opened at its own address), `-page-scrolls`, `-bar-always` (now a fixed `--lib-bar`) and `-no-sheet` and `S/library-grid-history` re-anchored, each killed alone again; 7 of the Library's details window (the user's request of 2026-11-15: every card's page in a large window over the grid, its X closing it), `LIBRARY_WINDOW`: the window opened modeless (`show()`, not `showModal()`), a release over the backdrop closing it whatever the press began on (a turn of the 3D view dragged out), closing it by `location.hash` (the native jump scrolling the grid under it), the page behind scrolling while it is open, a scroll bar's room kept whether or not the bar takes room (the grid narrowed under the window by an overlay bar's width), the rows' arrows not set as the grid is laid out (the grid is never hidden now: they had been set as it was shown), no sheet on a phone, each killed alone by `test_library` on a scratch copy, with `S/library-grid-back-shelf` re-anchored on the window's place (`state.place`: the back link's address, which its X closes to) and `S/library-view-phone-room` on the phone's page without its back link's room, each killed alone again; 3 of the showcase's card worded and linked again (the user's request of 2026-11-15: a smaller picture, only the picture and a Details pill open the page, the label and line worded again, the page keeping the sensor's size), `SHOWCASE_CARD`: the picture's link in the Tab order, Back taking the card for its Details, the page's line of detail unchecked, each killed alone by `test_library` on a scratch copy, with `S/showcase-page-label` reworded to the new label's words and `M/web-theme-hook-specificity` re-anchored on `a.lib-card:hover`, each killed alone again; 6 of the MakerMods Metal Arm's body drawn by eye, `MAKERMODS_BODY`: a prism's corner in line, its profile twice round, its corners unbounded, its y axis read (x, z), a drawn shape of the body left uncredited in `NOTICE.md`, the scene's about no longer saying it is not MakerMods' 3D model, each killed alone by its killers' module, `test_library_split` or `test_library`, on a scratch copy; 5 of the UMI pad's tint in the Library's Assembled view (the user's decision of 2026-11-14), `LIBRARY_PAD`: the rules' `part_pad` unchecked, `part_look()` without the pad, `--check-generator`'s fifth comparison taking a tint on the part's pixels or in Exploded, `library_stage.js` showing the tint in Exploded too, each killed alone by `test_library` on a scratch copy, the last also in the browser by `tools/browser/mutants.py`'s `lib` kind with `library_checks.py`'s `part_pad`, with a second there, the tint never laid; 5 of the verification of the Library's realistic look, `VERIFY_FIX`: the art's gzip OS byte, a file to remove closed by its removal, a refused site build's folder emptied, a split body of one file worded so, the showcase's Exploded camera, each killed alone by its killers' module on a scratch copy of the fixed head; 40 of the second stage of the Library's realistic look, each killed alone by its killers' module, `test_library` or `test_library_showcase`, on a scratch copy of the nine lines' merge: the UMI rows' `LIBRARY_FIGURE` 6, the four comparisons and the pin of `library_shots.py --check-generator`, the showcase page's `SHOWCASE_PAGE` 25 and its reviews' fixes' `SHOWCASE_FIX` 9; 46 of 2026-11-12, the Library's looks' 22 and its showcase's 24, each killed alone by `test_library`, `test_library_split`, `test_library_showcase` or `test_mesh_decimate` on a scratch copy of the three lines' merge); the last full run is of 2026-11-17, the verification of the Library's lines merged (all 1260 mutants of then on a `git archive` copy of c98e7d3: the 497 with killers against their killers, the others through the suite to its first failure, the modules nearest the edit first, the whole suite where none failed; 1241 killed as expected, the 4 expected survivors survived, 10 expected survivors killed, 5 unexpected survivors, each surviving `--only` on 2d60728 too: the catalogue above is that run's, corrected), the one before it of 2026-10-21 (below), and each mutant added or retargeted since was run on its own through the full suite (the Library's writer's `LIBRARY` group of 4 added on 2026-11-05, all killed by `test_library`, and a fifth since its second review, a base point round6 changes taken, killed by `test_library` alone, and its page's `LIBRARY_PAGE` group of 4, the site build's gate (its reply, and its request since the review of 2026-11-05), the generator's `?part` on the user's own file and app.py's route, each killed by `test_library` alone, and its tapered tips' `LIBRARY_TAPERS` group of 3, a family's grid unchecked, a family's parts in "Start here." and a tip's label, each killed by `test_library` alone, and the integration's `LIBRARY_MINORS` group of 4 (fpc-library merged into fpc-stack-on-part, 2026-11-05: the options recorded only where written, `./?part=<family>` refused, the deny-list short of an xArm mesh (`S/library-deny-list`, since the integration's review the writer's list, which the private importer takes: the importer's own copy, outside the public copy, left its mutant stale there), a family's shelf heading the long range again), each killed by `test_library` alone on a scratch copy, and the Library's polish (the user's decisions of 2026-11-05: one wording for every shelf heading, a sensor's picture 3:1 below 900 px) retargeted `S/library-shelf-family` (the writer has no branch for a family's shelf now: the two wordings again, the long range on every shelf without a family) and added its `LIBRARY_POLISH` group of 2 (`S/library-detail-shot`, the picture 16:10 below 900 px again, and `S/library-shelf-families-unsaid`, the UMI shelf's tapered tips unsaid), each killed by `test_library` alone on a scratch copy, and the Library's pictures' `LIBRARY_SHOTS` group of 6 (the user's request of 2026-11-05: `S/library-picture-other-fit`, `-picture-sources-error`, `-picture-bytes`, `-picture-alpha`, `S/library-image-card` and `S/library-gate-pictures`: a picture of another fit taken, older figure sources refused, a picture's bytes unchecked, an opaque WebP taken, the card named the 1280 x 800 picture, the site build's pictures unchecked), each killed by `test_library` alone on a scratch copy, and the Library's pictures' display (the user's request of 2026-11-05: the generator's on-part figure on the cards and a sensor's page) added its `LIBRARY_PICTURES` group of 7 (`S/library-picture-eager`, `-unsized`, `-card-full` and `-broken`: the cards' pictures loaded at once, unsized, the full picture for the card file, a failed file left broken; `S/library-view-unnamed`, `-kept` and `-phone-room`: the Exploded | Assembled control without its legend, the view of the page before kept on a page opened anew, the phone's page not tighter with it), each killed by `test_library` alone on a scratch copy and in the browser by `library_checks.py`'s `part_pictures` (`-phone-room` by its `part_first_screen`) on a served copy, and the Library's grid of 2026-11-06 added its `LIBRARY_GRID` group of 8 (`S/library-grid-shelves`, `-family-shelf`, `-back-shelf`, `-three`, `-767`, `-wrong-card`, `-history` and `-umi-first`: every gripper shelved again, a family's part without its shelf, the back link at `#shelf-<part>`, three to a row, two to a row below 768 px, a back link restoring the card that opened the page whichever it names, the history unmarked, the UMI shelf first), each killed by `test_library` alone on a scratch copy, and the merge's `S/library-picture-type` (app.py's pictures as the host's mimetypes guesses), killed by `test_library` alone on a scratch copy, and the set of pictures' `LIBRARY_SHOT_SET` group of 2 (`S/library-picture-required`, `library_write.py --check` passing a sensor with no picture, and `S/library-shot-uncentred`, the shots tool leaving each drawing where `frameView` put it), each killed by `test_library` alone on a scratch copy; and the Library's 3D view (the user's requests of 2026-11-05) its `LIBRARY_VIEW` group of 23 (`S/library-view-art-build`, `-art-bytes`, `-unrecorded`, `-scene-hash`, `-rules-hash`, `-older-error`, `-rule`, `-umi-stage`, `-mirror-kind`, `-mesh-hash`, `-part-pin`, `-denied`, `-alt` and `-entry`: an art of another build or not the record's bytes taken, a record without its art accepted after the shoot, a gripper's stage of another scene or rules, breaking a rule or recorded for a fingertip taken, a picture of older view modules refused, a mirror pair said to be turned, a scene's bodies or part unchecked, the deny-list off the bodies, a whole gripper's alt text "on the part", a view written for a stale art; and `S/library-view-lazy`, library.js loading the 3D view as the page loads; each killed by `test_library` alone on a scratch copy; since the user's decision of 2026-11-06 (one stack exploded) `-stacks-floor`, `-screen-apart`, `-near-seen`, `-near-seen-null` and `-explode-rules`: the exploded stack's floor in mm to the other finger's stack, the stacks apart on screen, the near stack seen, a near_seen taken with the mate's stack exploding and the rules' `explode_stacks` and `see_through_modes` each unchecked, each killed by `test_library` alone on a scratch copy, and `-rule` re-anchored on the call that passes the rules' `explode_stacks`; and `M/web-on-part-stage-main` and `-stage-home`, Gen by Surface's figure made with a stage and `onpart.js`'s homes hook ignored, each killed by `test_surface_web` alone; and since the shoot of 2026-11-06, which wrote every sensor's art and each gripper's stage and set `VIEW_REQUIRED`, `S/library-view-transition`, the 3D view no longer required, killed by `test_library` alone on a scratch copy), and the look's toggle of 2026-11-06 (its review) its `THEME_TOGGLE` group of 5 (`M/web-theme-default-dark`, `-hook-specificity`, `-no-pressed`, `-system-meta` and `-clear-ignored`: the page dark unless light is stored, a dark rule without its `:where()`, the toggle's `aria-pressed` never set, a color-scheme meta of light and dark on `index.html`, another tab's `clear()` of the storage ignored), each killed by `test_web_theme` alone on a scratch copy, and the samples' parts loaded alone (that day's later request: "测试用的sensor,不要托进去之后直接就生成好了,包括新拖进去的cad,不要直接显示哪个面被选择") its `NO_AUTO` group of 3 (`M/web-sample-built-at-once` and `M/web-file-largest-face`: a sample's face selected and its sensor generated as it loads, the user's own file's largest flat face selected as it loads; since its review `M/web-results-of-another-part`, the build of the part before shown below a model loaded), each killed by `test_samples` alone on a scratch copy; and the review's second round of 2026-11-06 its `OLDER_BROWSER` group of 2 (`M/web-check-visibility-unguarded` and `M/web-fit-scene-throws`: app.js's `Element.checkVisibility` unguarded again, an error of `fitScene`'s clearance of the controls failing the build), each killed by `test_surface_web` alone on a scratch copy, which `cad_checks.py`'s `part_older_browser` sees in the browser, its `LIBRARY_PLACE` group of 2 (`S/library-place-unmarked` and `-place-kept`: the Library opened at an address of its own unmarked by theme.js, the first route no longer clearing the mark), each killed by `test_library` alone on a scratch copy, the second by `tools/browser/mutants.py`'s `lib` kind too, with `library_checks.py`'s `part_routes`, and its `TAB_REVEAL` group of 2 (`S/library-row-reveal`: a card Tabbed to left cut by its row, `M/web-sample-reveal`: a sample's tile Tabbed to left cut by the palette's scroller), each killed by `test_library` or `test_samples` alone on a scratch copy, the first by the `lib` kind too, with `part_layout`; and the verification's small findings of 2026-11-06 its `VERIFY_MINORS` group of 4 (`M/web-stack-foot-square`: the stacked card's last row square at its rounded foot, `S/library-shelf-card-margin`: a shelf's card Tabbed to without room round it in the window, `M/web-sample-row-heights`: the phone's row of samples of two heights, `T/doc-suite-timeout`: `mutation_check.py`'s default `--timeout` 900 s again), each killed alone on a scratch copy by `test_surface_web`, `test_library`, `test_samples` or `test_docs_consistency`, the first three seen in the browser by `cad_checks.py`'s `part_stack_feet`, `library_checks.py`'s `part_layout` and `sample_checks.py`'s `part_phones`; and the 0.1 mm PI stiffener of 2026-11-06 (the user's decision: the 2-layer 0.2 mm order's gold fingers by JLC's rule, FPC + stiffener) `G/zone-two-layer-rule` (a 2-layer order's contact zone taken as core + copper + stiffener again), killed alone by `test_export_order_requirements` on a scratch copy, with `G/stiffener-0.2`, `G/doc-zone` and `T/doc-thickness` retargeted to the new figures; the EasyEDA Pro projects' `EASYEDA` group of 16 added, all killed; section 24's 7 added, all killed; section 26's 16 added, all killed, run on their own; its round 2's 17 added and 3 retargeted, all killed, run on their own; its round 3c, section 26.16, retired 19 with the code they mutated and added 5 and retargeted 4, all killed, run on their own; round 3c's review, section 26.17, added 5 and retargeted 2; the user's decision of 2026-10-27 on symmetric faces, section 26.17, retired 1 and added 2; the review's test gaps, 3 added; the 14 new, retargeted and redescribed all killed, run on their own; round 4's review, section 26.18, added 10 and described 4 anew; those 14 and 4 re-checked all killed, run on their own; section 27 retired 5 of the Row tail's placement mutants with the code they mutated and added 6 `M/sec27-*`, all killed, and marked `M/sec20-level-points-merged` equivalent: with the Row tail centred no side meets a flush tail at a slant on the level; its review, section 27.3, added 4, `M/sec27-inner-slant-half`, `-inner-slant-to-root`, `-inner-unfilled` and `-tails-own-ends`, each killed alone, and re-checked `M/sec20-level-points-merged`, still an expected survivor; the review of 27.3, the plan's 27.4, retired `M/field-tail-reach-own` with the shared reach it mutated and added `M/sec27-tails-shared-reach`, killed alone, and the seeded flush regression r2712:0469 kills `M/sec20-level-points-merged` alone, so it is no longer equivalent; the review of 27.4, the plan's 27.5, added `M/sec27-tails-reach-floored`, `M/sec23-cap-not-searched-again` and `-cap-not-refused`, each killed alone; the merge of the two lines of 2026-10-27 (the plan's sections 26.16-26.18 and 27-27.5, its 27.6) added and retired none, and the ten whose code or tests it touched were run alone on the merged tree, all killed; the user's threshold of 20 % on symmetric faces, the plan's section 26.19, added `M/sec26-symmetric-without-threshold`, `-symmetric-threshold-boundary`, `-symmetric-threshold-after-tip` and `-symmetric-never-turned` and retargeted `M/sec26-symmetric-within-3-percent` (its threshold at 3 %) and `M/sec22-turned-on-symmetric-exit` (turned within the threshold), each run alone; the rectangular mode's default tails 12 / 12 mm, the plan's section 27.7, added `T/default-tail-surface` and retargeted `T/default-tail`, each run alone; the multi-gripper video's notch, the plan's section 27.8 (`diagonal-bus/11`), added 7 `M/sec27-flank-*` (`-none`, `-no-end-move`, `-unguarded`, `-corner-off-grid`, `-point-kept`, `-anchors-ignored`, `-irregular`) and retargeted `M/diag-shared-row-only` and `T/doc-build-id`, each run alone; the profile revision 2026-10-29 (the gold-finger thickness order option and the coverlay-window notes) added 7 `G/*` (`G/gold-finger-review-note`, `-gold-finger-stiffener`, `-window-key-unchecked`, `-window-none-longer`, `-window-limit-doubled`, `-window-line-dropped`, `-window-line-unchecked`), each run alone; the sensor on the part of 2026-11-05 added the `ON_PART` group: `M/web-on-part-gate` and `M/web-board-art-listener`, each killed alone, and the browser-only `F/on-part-mirror` and `F/on-part-texture-rows`, which `tools/browser/mutants.py`'s `cad` kind kills with `cad_checks.py`'s `part_on_part`; its review of 2026-11-05 added `M/web-on-part-probe-gate` and `M/web-on-part-buffers`, each killed alone, and the browser-only `F/on-part-coverage` and `F/on-part-framing`, which the `cad` kind kills with `part_on_part` and `part_crank_fill`; its second review of 2026-11-05 added `M/web-on-part-caption` (retired on 2026-11-06 with the registration's caption and the split's room for it) and `M/web-on-part-cursor`, each killed alone, and the browser-only `F/on-part-seams`, which the `cad` kind kills with `part_on_part`; its look of 2026-11-05 added 8 `M/web-on-part-*` (`-own-lights`, `-tone`, `-warn-once`, `-studio-fallback`, `-bands-side`, `-contact-lazy`, `-contact-mode`, `-film-face`), each killed alone, and the browser-only `F/on-part-film-flat`, `F/on-part-contact-never` and `F/on-part-bands-off`, which the `cad` kind kills with `part_on_part`; the look's fix round of 2026-11-05 added 9 `M/web-on-part-*` (`-restore-dispose`, `-restore-sheets`, `-measure-in-try`, `-measure-unguarded`, `-contact-none`, `-anchor`, `-contact-inner`, `-contact-facing`, `-contact-turned`), each killed alone by `test_surface_web`, four of which the `cad` kind kills too with `part_on_part_studio`, `part_on_part_patches` and `part_on_part_contact`, and retargeted `M/web-on-part-contact-lazy`; the user's decision of 2026-11-05 (the Exploded home the left figure's as it opens) added 4 `M/web-on-part-*` (`-home-left`, `-home-spin`, `-camera-up`, `-keys`), each killed alone by `test_surface_web` on a scratch copy, the last three of which the `cad` kind kills too with `part_on_part`'s comparison with the left figure; the 3D view in the figure's light (the user's request of 2026-11-05, `web/cad/studio.js`) retargeted 5 `M/web-on-part-*` to the shared studio (`-tone`, `-warn-once`, `-studio-fallback`, `-measure-in-try`, `-measure-unguarded`), retired `M/web-on-part-own-lights` with the 3D view's old lights it imported and added 8 `M/web-view-*` (`-own-lights`, `-tone`, `-markers-lit`, `-studio-per-model`, `-restore-dispose`, `-restore-none`, `-probe-gate`, `-drag-everywhere`), each killed alone by `test_surface_web` on a scratch copy, five of which the `cad` kind kills too with `cad_checks.py`'s `part_view_look`; the 3D views' light of 2026-11-05 added the `VIEW_LIGHT` group of 7 `M/web-view-light-*` (`-key`, `-softbox`, `-band`: app.js's copies of the sensor on the part's light; `-tint`: the sweep's tint in Photo; `-flatten`: an opacity on the stacked boards' faces; `-outline-twice` and `-unclipped`: the light's paths not the outline less its cutouts), each killed alone by `test_surface_web` on a scratch copy, and `tools/browser/mutants.py` its 4 light mutants, killed by `ui_checks.py`'s `part_view_light`; the film's own lamp (the user's of 2026-11-05, 再调一下你说的黑色压阻膜: at the left figure's home the film had mirrored the room between the studio's softboxes, nearly a flat black) added `M/web-on-part-film-lamp-anchor`, killed alone by `test_surface_web` on a scratch copy, and the browser-only `F/on-part-film-unlit`, which the `cad` kind kills with `part_on_part`'s film at discriminating levels again): the
  catalogue's totals once the `M/` mutants of the masked field's phases P1
  (11), P2 (the builders: 13 added, and P1's temporary-gate mutant
  replaced by the class gate's; the DRC and registration: 14; the fixes of
  the P2 reviews: 8), P3 (the exporter: 14 added, and P2's exporter-gate
  mutant retired with the gate), P4 (CAD mode's masked fields: 22 added,
  and P2's map-gate mutant retired with the gate) and the fixes of the P4
  reviews (11 added, and P4's readout-dedupe mutant retired: one mask per
  readout is now the rule) and P5a (the diagonal Row bus's primitives, the
  `DIAGONAL` group: 6) and P5b (its construction, DRC and contract: 24
  more in `DIAGONAL`) and P5c (its exports: 5 more in `DIAGONAL`) and the
  fixes of the P5 reviews (9 more in `DIAGONAL`; the tail redesign of the
  plan's section 12, diagonal-bus/2, retired 10 of these and P5b's with
  the corridor, the stub drop and the stack rules outside the field, and
  added 14; its review retired one more and added 13, 8 in `DIAGONAL`
  and 4 in `FIELD_FIT` and a retarget; the stacked tails of the plan's
  section 13, diagonal-bus/3, retired 8 (the fallback beside the Column
  tail twice, the Column tail's side and neck, the Row root's lowering
  below the Column board, the tail gap and clearance and their 0.9 mm
  variant), retargeted 3 and added 6 in `DIAGONAL`, run on their own and
  killed: the full run waits for the final tree; the one outline over the
  field, diagonal-bus/4, added 8 in `DIAGONAL`, run on their own with the
  stacked tails' 6 and killed; its later decisions, no Column copper in the
  lanes' keep-out and lanes following a receding field, retired 2 (the
  Column stubs left out of the keep-out, now the rule, and the stack trace
  gap kept from them), retargeted P5a's 2 keep-out mutants and added 5 in
  `DIAGONAL`, run on their own and killed; its regular outlines,
  diagonal-bus/5, retargeted 2 and added 6 in `DIAGONAL`, run on their
  own: the full run is not to be run for now, the user's decision of
  2026-10-23; the corner tolerance, the rectangle preference and the
  chamfered notches of the plan's section 16, diagonal-bus/6, retargeted 3
  and added 7, 2 in `DIAGONAL` and 5 in `FIELD_FIT`, run on their own; the
  straight sides of the plan's section 17, diagonal-bus/7, retargeted 1
  and added 3 in `DIAGONAL`, run on their own; the rectangular generator's
  bus of the plan's section 18 retired 2 (the generic template accepting
  `routing.row_sides` and the form sending it there, now the rule; their
  inverses are among the new), retargeted 12 and added 9 in `DIAGONAL`,
  run on their own; its one Column V of the plan's section 19,
  diagonal-bus/8, retargeted 3 and added 5 in `DIAGONAL`, run on their
  own, and retargeted 2 document mutants: the default build id and its
  Column tail's flexible length; the rectangular generator as a subset of
  CAD mode, the plan's section 20 (one rule set, one outline down to the
  tail roots, the Column V capped at 80 degrees), retired 9 (the shared
  level at the field's edge or window level, the fillets kept while the
  union is made regular, the standard profile's 60-degree fans, fan start
  and careful pass, the override's two lanes and lane capacity and its
  version per template), retargeted 12 (the default tail, build id and
  flexible tail length of the documents, the DRC gate, the identity
  extra, the necked Column root, no shared outline, the Row board's alone,
  sharp union corners, no straight sides, the bus's rule set reaching the
  straight channel, the overhang at the root's crossings) and added 8, 7
  in `DIAGONAL` and 1 in `FIELD_FIT`, run on their own; the fixes of its
  review retargeted 3 (no straight sides, sharp union corners, the Row
  board's outline alone) and added 4 in `DIAGONAL` (the straight sides'
  bound measured to the sharp union, the union's points on the level
  merged, the run below the level along the last edge, a tail's root
  corner merged), run on their own; coverage first, the plan's section 21,
  retired 1 (`M/fill-shaped-64`), retargeted 3 (a reader not capping the
  field search, the rectangle preference ignored or unbounded) and added
  5 in `FIELD_FIT`, run on their own; CAD mode's border of the taxels
  (docs/CAD_BORDER.md) added 3 in `BORDER` (the border ignored in the
  lattice, `taxels_inside_border` never failing, `base.border_edge` taken
  as the next edge), run on their own; symmetric faces, section 22, added 5
  in `FIELD_FIT` (no face symmetric, an asymmetric row accepted as
  symmetric, the symmetric DP's runs shifted, a symmetric exit turned, a
  symmetric field first however few taxels, retired with section 26.17)
  and retargeted 2 to the
  edited lines, run on their own; the caps keeping the exit, section 23,
  added 3 in `FIELD_FIT` (the caps choosing the exit, a capped field's
  rows next to the exit instead of at the far end, the surface's tails
  held at 80 mm) and retargeted 2 to the edited lines (the no-fit reason,
  the whole lattice's field taken unfit), run on their own; the corner
  tolerance at every convex corner and the convex sides, section 24
  (diagonal-bus/9), added 7 (5 in `FIELD_FIT`: aligned ends exempted in F's
  check or half in the DP, convex corners held in the DP, F's check at the
  field's four corners only, the symmetric DP's old rule; 2 in `DIAGONAL`:
  no convex sides, the hull's bound ignored), retargeted 2 to the edited
  lines (the DP's phases swapped, the Row board's outline alone) and the
  document mutant of the default build id, and re-described
  `M/corner-zones-every-row`, run on their own; the Row tail centred on the
  field, section 27 (diagonal-bus/10), added 6 in `DIAGONAL` (the tail a
  contact pitch off the centre, the funnel's old split midway between the
  innermost lanes, one side's old tail under the band, the mirrored rows on
  the tail's near end, one side's inner flank with its ledge back or
  slanting however flat) and retired 5 of P5b, P5f and P5g with the code
  they mutated (the mirrored contacts, the split, the flush tail, the
  reader's far contacts, the tail a pitch off the split), run on their
  own with the re-checked flush-tail and tail-side ones: the fin's 59 x 12
  with both, a tail flush with both sides of the union, kills
  `M/sec20-run-on-last-edge` and `-root-corners-merged` again, a check of
  `_side_chain` on its own `M/diag-tail-slant-above-field`, and
  `M/sec20-level-points-merged` is marked equivalent; its review, section
  27.3, added 3 in `DIAGONAL` (the inner flank slanting only within half its
  drop, to the tail's root instead of its hold, not made monotone) and 1 in
  `FIELD_FIT` (each tail ending past the edge under its own width, not on
  one line with the other), each run on its own and killed, and re-ran
  `M/sec20-level-points-merged`, still an expected survivor; the review of
  27.3 (the plan's 27.4) retired `M/field-tail-reach-own` with the shared
  reach it mutated, added `M/sec27-tails-shared-reach` (the line pushed by
  that reach), killed alone, and found `M/sec20-level-points-merged` not
  equivalent: the seeded r2712:0469, a flush regression now, kills it alone;
  the review of 27.4 (the plan's 27.5) added 3 in `FIELD_FIT` (a tail
  reaching the line rounded down; the 200 mm cap of section 23 not searched
  again nearer the exit, or its refusal off), each killed alone) and P5d (CAD mode's field-only containment and the P5c carry-overs: the
  `FIELD_FIT` group, 21) and P5e (the default flip, the map's containment
  from the design, the no-fit reason and the browser client's Row traces and
  Containment: 8 more in `FIELD_FIT`) and the fixes of the P5d/P5e reviews
  (24 more in `FIELD_FIT`) were added; a full run of these totals is
  pending.  The run of the 369 before them, on a frozen copy outside the
  repository, killed 363 (2026-10-21, 07:45 UTC): its one unexpected
  survivor, `T/doc-ci`, cannot be killed there because the copy has no
  repository-root CI workflow, and is killed when run from the project.
  Each P1 `M/` mutant was checked killed on its own and through the full
  suite, and each P2 one through the full suite (`--only` its ids), and so
  were each P3 and each P4 one, and each of the P4 reviews' fixes, and each
  P5a, each P5b and each P5c one, and each of the P5 reviews' fixes, and
  each P5d and each P5e one, and each of the P5d/P5e reviews' fixes.
  The `M/` mutants keep a full mask, accept a mask on the generic
  template, drop `mask` from the identity or
  from the exports' identity fields, skip the column-gap rule, the
  inactive-gap warning or the class gate, let the size advice change
  rows, swap the Row-frame sides, and drop the lane taper or the Column rule
  of the construction classes; the builders' mutants end the Row or the
  raised Column stubs at the field's common end, keep the unmasked field
  start, drop the fillers between bands or the window's expansion, make a
  full span's window a polygon, leave the polygon window or the active
  outline unturned, drop the Row body's bottom width or keep either body a
  rectangle, and write the taxel mask in frame slots; the DRC's mutants
  measure the margin to P's bounding box, skip P's equality with the
  electrodes, the window's shape, the inside test or the clip of the
  strict rule, keep its own-net skip or the edges on a route's own window,
  measure a polygon's bridge or exposure on its bounding box, leave the
  top board unturned in the stack frame, skip the crossing test, the
  masked grid's ends, the masks' comparison or the inactive separation; the
  review fixes' mutants skip the masked grid across the electrodes, judge a
  window touching the outline by one vertex, let a window overlap a cutout
  or P lie off the board, drop the trace overlap report or count crossings
  in it, and let the map take a masked build; the exporter's mutants (P3)
  write a polygon window as its bounding box or compare its region with
  itself, let any opening be a polygon, let one sit on an unmasked board,
  carry rectangle fields, cross itself, leave the grid, slant or turn
  clockwise, invert taxels.csv, drop it or its read-back, and drop or
  miscount the order notes' taxel field; the fit's mutants (P4) count
  positions as taxels, give a masked
  proposal its bounding rectangle as field outline, drop the peel, write
  the spans in slot order, drop the free space's edge inset, end a row's
  band half a pitch above it, drop the lane taper, propose masks without
  the rectangles, keep the rows' own far ends, take 64 masked rows (or a
  fill on the generic template, retired with section 26.16); the map's list every position, mirror the
  taxels, blind the mask record or want R x C taxels; the readers' take 16
  sense lines per frame row, the largest reader for `auto`, swap the sides
  or ignore the legacy `connector`; and the web client's post the form
  without the mask or keep it after a rows edit.  The P4 reviews' fixes'
  mutants leave the masked walk uncapped by a named reader, name the
  option's reader in the metrics, seed the lattices at the placement
  option only or from either role's rectangles, prune a role on the other
  role's masks, run the fine phases on either role's frames, keep a
  dominated proposal, drop the mask on a mode switch, show no issue at
  `matrix.mask` and leave "Use the full field" inert (keeping Field shape
  enabled on the Rectangular board rules retired with section 26.16).  The P5a mutants keep collinear
  points on the west chain, offset slanted segments without the 2 nm
  allowance, round offset vertices to the nearest grid value, bevel a
  sharp convex turn, and leave a lane's continuation or the box around its
  start out of its keep-out.  The P5b mutants, re-expressed for
  diagonal-bus/2, let a lane leave its own zone short of its corner or
  within the trace space of another row's electrode, start lanes at a
  corner, drop the tail root's hold, keep ROW_01..ROW_R on the contacts,
  never mirror, split in halves, turn off the DRC gate, accept traces over
  electrodes, warn of no close window, drop the identity extra, accept the
  field on the generic template and let an infeasible bus raise.  The tail
  redesign's mutants keep diagonal-bus/1's corners below the field (three
  bends), turn a thin row's lane down inside the Column windows' keep-out,
  raise the bottom row's corner before the onion (the bands move), let a
  tail side slant out however flat or from above the field, fail a trace
  over an electrode only with a window too or count it per electrode, run
  the fans a grid step inside the bundle pitch or unstaggered, allow the
  Column entry angle, ignore the fans' clash check, land the last lane one
  contact beyond, and leave traces over the field window uncounted or one
  opening per electrode out of the window.  The stacked tails' mutants neck
  the Column board 1.0 mm, give it the straight classes, let the registration
  accept traces over the other board's electrodes and window or tails on two
  sides, and report no tail overlap.  The later decisions' mutants on
  diagonal-bus/4 put the stacked Column copper back in the bands' keep-out,
  run a receding field's lanes straight down from their westmost point, ignore
  the inner lanes' offsets where they cross the field's bottom edge, let a
  lane lean past the taper cap toward it, and take the mitre at a lane's
  inward turn (the lanes outside it spread).  The regular outlines' mutants
  (diagonal-bus/5) leave the outlines as built, merge only vertices that do
  not turn at all, make a merged run's edge its chord (cutting inside a convex
  run), let the union's regularization move the boards' fillets, leave the
  corners where merged edges meet sharp, and make the tails regular too.  The
  chamfered notches' mutants (diagonal-bus/6) take the hull of P for a notch's
  chamfer (cutting inside F) or keep F's staircase; the corner tolerance's
  mutants let the zones reach along F's whole sides or into P and tolerate
  every row's corners (its two that ignored the rectangle preference or
  applied it beyond its share retired with section 26.16).  The straight
  sides' mutants (diagonal-bus/7) leave the sides' polylines, ignore the
  1.0 mm bound, and take the chord from the tip corner for the upper line (not
  enclosing the side).  The one Column V's mutants (section 19) reach the
  straight channel's Column board with the bus's rule set and keep the Row
  fans off the old 60-degree Column entry.  Section 20's mutants give the
  rectangular generator a rule of its own (its Column V always capped: parity
  broken), stop the shared outline at F's bottom, leave the tails' roots above
  the union's fillets, never or always cap the Column V, give the straight
  channel the bus's default tail, drop the channel's column bound from the
  served limits, and skip the side
  overhang where a straight side crosses the surface's lowest level.
  Section 21's mutants (coverage first) cap the field fit's shaped fields
  and the board fit's masked walk at 32 x 32 again (retiring P4's
  `M/fill-shaped-64`) and leave reader `auto` uncapped (its two rectangle
  preference mutants retired with section 26.16).  Section 24's mutants exempt aligned ends from F's
  check (or half of them in the DP), hold a lower run's top zones at its
  convex corners in the DP or check only the field's four corners in F's
  parts (section 16's rule: the crank's 696 back to 683), keep the
  symmetric DP's old rule, leave the convex sides out (the S-kink beside a
  narrow tip stays), and bridge any dent however deep.  Section 26's mutants
  (the taxels from the fingertip) read a capped rectangle's zones before its
  cap, leave the filler band unchecked or held over the lower run (and two of
  its phases wrong), keep no field but the lead, take the share from the lead,
  widen or drop the slack, let a full lead take notched fields, group across
  exits, drop the displaced lead or its proposal key; its round 2's drop the
  lead's zero-cost tie, let `tip_first: false` take the share or skip the
  step, and pin what the first round left open: the reach before the corner
  count, the centred phases, the tails' reach in the pass and the peel
  fallback; its round 3c's five (section 26.16) let a full lead's pass ignore
  section 23's window, drop the lead's ties short of the tip-first field from
  the pass or stop the pass at that field's reach, let a fit take shape
  rectangle, the generic template or a rectangle preference silently, and
  refuse a saved placement that names them.  Retired with what they mutated
  (section 26.16, 19 in all): the tip-first rectangles' three, round 2's
  tip-zone guard (2), tie-break (2), rectangle floor and column guard (4),
  P4's shape fill on the generic template, the browser's Field shape and
  Containment on the Rectangular board rules, the rectangle preference's four
  and the CAD fit's shape per pitch.  Section 26.17's ten (round 3c's review
  and the user's decision of 2026-10-27 on symmetric faces) propose the lead
  beside its zero-cost tie, keep a tie peeled under the lead's taxels in the
  lead's place, report the displaced field's rank only where it is proposed
  itself, count the taxels given from the lead, let the map take any value of
  the removed options, put a symmetric field first only within 3 % again
  (since section 26.19 its threshold at 3 % for the 20 %),
  measure a symmetric group's tip share from every field, drop T0's p / 8
  slack, take T0 of exactly the lead's taxels, and run the pass's lattices
  short of the farthest reach at the lead's value; retired with it: section
  22's symmetric field first however few taxels (its rule then; a defect
  again since section 26.19).  Section 26.19's four (the user's threshold
  of 20 %) put every symmetric exit's lead first however many more taxels
  another field holds, let the symmetric field still lead at exactly 20 %,
  count the tip's 3 % into the decision, and turn no exit with a symmetric
  field; `M/sec22-turned-on-symmetric-exit` turns an exit whose symmetric
  field holds within the threshold.  Section 27's
  mutants (diagonal-bus/10, the Row tail centred on the field) put the Row
  tail a contact pitch off the field's centre, part the funnel's contacts
  midway between the innermost lanes again, put one side's tail under the band
  again, take a mirrored build's contacts at the tail's near end, and give one
  side's inner flank its ledge along F's bottom back or slant it out however
  flat; its review's (section 27.3) slant that flank only within half its
  drop, slant it to the tail's root instead of its hold, leave it unmade
  monotone, and end each tail past the edge under its own width (not on one
  line with the other); its review's (27.4) push that line out by the shared
  reach, and 27.5's round a tail reaching it down and leave the 200 mm cap of
  section 23 without its search nearer the exit or without its refusal.  They
  retired diagonal-bus/2's and /3's placement mutants with the code they
  mutated (the mirrored build's near-end contacts, the funnel's split under
  the near band, the one-sided tail a contact outside the band, a mirrored
  reader tail's rows at its far end, the funnel's Row tail a contact pitch off
  its split).  The P5c
  mutants give an unmasked bus no taxel map, state its full field as a
  masked taxel field in the order notes, leave the bus's record out of
  the review manifest, skip its read-back against `pinout.csv`, and number
  the recorded Row pins by position.  The P5 reviews' fixes' mutants list
  no flat lane, take the plan's least-excess
  clause or every row for the relative narrow tip, and give any unequal
  tails E_ROW_BUS_TAILS.  CAD mode added 110 (`S/`; 46 with the first
  review's fixes, 64 with the second's): the STL weld,
  orientation (inside-out, open shells, cavities), repeated facets, covered
  walls, T-junctions, the selection's cone, blend barrier, creases and fine
  fillets, the chart's hinge, handedness, holes, bands and pieces, the
  fit's mirror, strain gate, arc exits, edge inset, obstacle cells, one proposal per shape,
  exit-crossing clearance and short sides, the map's mirror, mismatch
  checks (design, template, mesh, selection), containment, tail reach,
  reader lines, surface spacing, placement validation and JSON records,
  big integers, long header numbers, the mesh cache's unit, CAD mode's own
  slot, the 413 drain, the content type and two CLI statuses.  The run of
  2026-10-15 had 259 mutants, 254 killed (21 of them added with the necked routing:
  the bundle pitch, the bend stagger, the widening drop, the route rule, the
  `route_width` record, the copper's trace minimum, the input ranges and the
  per-route stroke widths; 6 with its review: the DRC's finger-section rule
  and its pairs, the widening drop for intermediate bundle widths, the grid
  rounding of the far bends and the trace-tolerance line of the order notes); the audit's 36 baseline mutants are all killed
  (9 at the audit; `audit/x`, whose defect, the missing `E_DUAL_LANE_WIDTH`
  check, is the intended behaviour since 2026-10-15, now drops the minimum
  slot of a narrow fan-out instead).  The 5 survivors are justified in the catalogue:
  3 equivalent (`E/F1-inputs`, `X/given-boards`, `M/diag-shared-no-ear`) and 2
  browser-only (`F/stale-banner`, `F/turn-over-axis`), which the Playwright
  checks kill.
- `tools/golden_values.py` prints the default-build values for
  `test_golden_default.py` after a deliberate change.
- `tools/library_write.py` fits the Library's sensors (`web/library/`, the
  user's requests of 2026-11-05) from the request the page sends for each,
  checks the product rules on each proposal #1 and writes the changed fits
  and `entries.json` (about 10 s for the 42 sensors with `--jobs 8`, 15 s for the
  58 of 2026-11-16; `--check` writes nothing; a family of parts, the UMI
  finger's tapered tips, is its cards on its shelf's part's shelf, one per
  finger shape since 2026-11-16, each card's grid checked complete and every
  tip on one card);
  re-run it after any change that moves a build id, as
  `tools/browser/write_default_fit.py` for the default part.  It writes
  each sensor's `image` from `web/library/shots/manifest.json` (null
  without a picture, and for a picture of another fit; `--check` refuses
  both, every sensor having its picture since 2026-11-05; one of older
  figure sources a warning), and each sensor's 3D view, `view` (the user's
  requests of 2026-11-05, `docs/LIBRARY_VIEW.md`: its art and a gripper's
  scene, for a record current with its art and stage; `pictures()` refuses
  an art or stage that is not the sensor's own, `scenes()` the grippers'
  scenes, their bodies and notices; `VIEW_REQUIRED` set by the shoot of
  2026-11-06 that wrote every sensor's art and each gripper's stage, a
  record without them refused since, a warning before it).  The grippers' scenes and bodies come from the private
  `tools/library_scenes.py` (numpy, trimesh, the private recipes).
- `tools/browser/library_shots.py` shoots the Library's pictures and the
  art of each sensor's boards (the user's requests of 2026-11-05, the 3D
  view of `docs/LIBRARY_VIEW.md`) against a running `app.py`: each
  sensor's art from the generator's page (`"fpc:board-art"` for its fit's
  build, into `web/library/art/`), then its page at
  `?probe=shoot#<id>` (`library.html?probe=shoot#<id>` until 2026-11-16), the Library's own 3D view (a gripper
  drawn whole) at its Exploded and Assembled homes framed at 16:10, the
  canvas alone on a transparent background, each drawing moved to the
  middle of its picture, WebP with alpha into `web/library/shots/` with
  `manifest.json` (each record's art, the view's hash and a gripper's
  measured stage); `--check` shoots again and compares the bytes, and
  `--check-generator [ID,...]` (the UMI finger's and its tips' sensors, all
  30 without an id; since the UMI rows' orange of 2026-11-12 four
  comparisons, five with the pad's tint) holds Gen by Surface's figure to its pin
  (`tools/browser/generator_figure.json`, by fit, build and WebP hashes;
  `--pin-generator` writes it anew after a deliberate change of the figure
  or a new build), the Library's view without the look and the home to that
  figure, the view to the committed pictures, and, at the figure's homes
  (since the grippers' homes of 2026-11-16), the look to the part's own
  pixels alone (the sheets untouched) and the tint to the Assembled sheets.  `--showcase [--check]` shoots the
  showcase's three pictures from its own page into `web/library/showcase/`
  and writes `showcase.json`'s `placed`, `image` and `shot`, refusing a
  shoot whose stage numbers break the rules' checks or the showcase's own
  bounds (`library_write.SHOWCASE_BOUNDS`).
- `tools/library_split.py` (standard library, deterministic; 2026-11-12)
  writes each part's look file (`tools/library_looks/<part>.json`) into
  its bodies (component files picked by connected component, box or the
  rest; plain boxes, cylinders and prisms drawn as `drawn-<name>.stl`, the project's
  own by name and header), its scene's looks and `NOTICE.md`'s rows; `--only
  <part>` for one part, `--components` and `--pin` to write rules, `--out`
  for a dry run; `--check` proves the committed files are what the look
  files give and refuses a look or a drawn body of a part with no look file
  (the showcase's scene's looks are `tools/library_showcase.py`'s).  An
  unsplit body is pinned by SHA-256 in its look file; a later change of the
  pick rules needs it back from git (`--source`).
- `tools/library_showcase.py` builds the showcase from UFACTORY's file and
  HandUMI's holder (`--sources DIR`, about 2 minutes) and, without them,
  writes the scene and the drawn shapes again and checks every pinned file
  (`--check`); its looks (`BASE_LOOKS`, a copy of rows of `base.json` a test
  compares, and `OWN_LOOKS`, seven of the showcase's own with their
  evidence, the fingers' `umi-tpu-orange` equal to the rules' look), its
  camera and drawn shapes are in its source.  A deliberate change: `--repin`,
  `--notice`, then the pins of `tools/library_write.py` and its test.
  `tools/mesh_decimate.py` is its decimator; `tools/flexitac_v2.py --check
  [DIR]` checks the pad's committed geometry against its pin (and against
  the official Gerber ZIPs when DIR holds them; `test_showcase` rebuilds it
  where `FLEXITAC_V2_GERBERS` names their folder).
- `tools/browser/` holds the Playwright checks of the browser UI (their own
  virtual environment; see its README); since 2026-11-12 also
  `showcase_checks.py` (the showcase's wrap, tails, view, pictures and page,
  `--url` for a built site), `flexitac_v2_art.py` (the pad's art) and
  `wrap_checks.js` (the wrap mapper, under node in `test_showcase` too), and
  `library_checks.py`'s `part_looks`.

CI (`.github/workflows/fpc-agentic-customization.yml` at the repository
root) runs the suite on Python 3.9 and 3.12, `tools/mutation_check.py
--check` (every catalogue edit still applies) and `node --check
web/app.js`; a manual job of the same workflow runs the mutants named in
its `only` input (`--only`; each mutant is a run of the whole suite, about
29 minutes on a standard runner on 2026-11-06, so the whole catalogue never
fits the hosted runner's 6 hours; the unittest job's limit is 60 minutes
since the verification of 2026-11-06, 15 before).  There is no lint step: the project
stays free of third-party tools (pyflakes, run from a scratch environment,
reports nothing on any file as of 2026-10-15).

## Open items

Product decisions:

- The Unitree Dex3-1's pitches (2026-11-18, `fpc-int-n-dex3-back`): 1, 1.5,
  2 and 2.5 mm as before; 3 mm keeps every rule on the dome (9 x 5, 35
  taxels, 13.5 x 25.5 mm, tails 19.2 mm; 3.5 and 4 mm 24 and 20), but a
  fifth pitch would end the grid's heading "each fitted at four pitches"
  (`library.js` drops it when the cards' counts differ).  3 mm in place of
  2.5 (the LEAP Hand's 1, 1.5, 2, 3), or five pitches and the heading's
  words, is the user's call (its review refitted 3 mm: no rule broken).
  On the public site Gen by Surface opened from its card takes about 14 s
  (the stretch select on the dome in Pyodide; 1.5 s natively), the LEAP
  Hand's about 3 s.  Its pose is `bff728c`'s: the thumb's pad faces the
  dome's patch within 16.2 degrees (8.28 against the disks'); a pose
  surveyed again on the patch would change the look.  The push of the
  version the user asked for is the lead's, after this branch is merged.

- The real stack and Whole board (found by `cad_checks` whole on 2026-11-18,
  the review of the symmetric selections' verification): since the 0.65 mm
  stack (`fpc-int-n-curved`, 56624a1) every bend tighter than the field's
  6.5 mm was an obstacle to the whole board under `containment: board`, its
  tails and fan-out too, and the soft finger's face (`asset/`) fitted
  nothing at side 0 under Whole board ("a tail misses the exit"; at 0.47 mm,
  as on the mainline, 338 at the page's default Max rows and columns 32 and
  480, 50 x 12, at `cad_checks`' 64), so four `cad_checks` failed.
  Resolved the same day (the lead's decision: outside the taxel field the
  board is a single FPC, not the laminate): F keeps the laminated field's
  6.5 mm and everything outside it takes one board's 2 mm, as Field only
  checks the routing off the field; the face takes its 338 and 480 again,
  and with the review's second search a bend running toward the exit costs
  no taxels (the log above, docs/CAD_MODE.md **Whole board on the real
  stack**).

- Gently curved faces (2026-11-17): the 1 % limit, the default on curved
  faces since the user's choice that day ("1% default on curves"; JLC's FPC
  copper is RA, the user laminates, soft tape), rests on estimates; the study's printed-cap test (caps of R 20 mm at 8 to 20°, a
  Dex3-1 tip, laminated and bonded on the soft tape used; wrinkles and lift
  after 24 h and thermal cycles, every line's continuity) should say whether
  it holds before it is trusted, more so on tape that creeps.  Whole
  fingertips (slit or comb boards, petals) are not built (the user's
  decision).  The lamination's 2 x 0.075 mm is the 3 mil sheet the earlier
  estimate counted: a measured stack (calipers on a laminated pad) would
  settle the field's 6.5 mm bend: since the 0.65 mm stack, half cylinders of
  R 5 and 6 mm (133 and 171 taxels at 0.47 mm) take no field.  The Library's
  Dex3-1, its two 7 mm disks (110 / 49 / 28 / 18 taxels) removed with the
  hand on 2026-11-17, is back since 2026-11-18 on a click's patch at the
  curved 1 % (332 / 146 / 82 / 52), its hand scene's checks run again (every
  rule kept, its card override 19 px).  The gate reads the relaxed sheet since the
  review's fixes (2026-11-17): should the user want the looser gate of the
  least-max-stretch chart (55 and 94 taxels on a Dex3-1 click, 0.45 % and
  1.6 % left on the part on soft tape), the tiers would have to say so.  A
  click on a dome takes about 1 s natively, 2.6 s on the static site
  (Pyodide).

- The LeFlexiTac (2026-11-16): LeFlexiTac's two STL files (its moving jaw,
  the Library's part, and its wrist roll) state no licence.  Resolved on
  2026-11-17: the user, a co-author of LeFlexiTac, let them be published
  ("leflexitac, i am the author, so its ok to use it in public"); they are
  shared with the authors' permission (`tools/library_write.py`
  `PERMITTED_LICENCES`, dated; still `NOASSERTION`, no licence invented),
  and the site build and `tools/export_public.py` take them (a pending
  entry's files are still refused).  Also the user's to judge: the rotary jaw drawn
  39 degrees open (not fully open: the grippers' homes turn the static face
  toward the camera beyond about 40), the scene's explode at gap_share 0.45
  (the one override: a rotary jaw's faces are 33 mm apart at its hub, and at
  0.42 the explode's film is less than a quarter seen), so the card the
  weakest of the eight by the stage's numbers (the least visible layer
  0.254 against a floor of 0.25 and the others' 0.365 to 0.981, the stacks
  28 px apart against 31 to 199, the veil 0.59 against 0.98 to 1.00, 4.7 mm
  a layer against 7.5 to 13) and its near sensor, on the static jaw, almost
  edge-on (its amber a third of the far one's in the Assembled picture, the
  others' 0.9 to 1.3; the reviewer's count 0.22 against 0.59 to 1.12; the
  reviewer's variants, 25 to 60 degrees open, the face kept upright, the
  rules' 0.42, each worse or failing:
  `library-look-work/look/out/leflexitac-review/opening-variants-*.png`; a
  clearer card needs a dated rule for rotary jaws, such as the explode along
  the approach); a pass this near the floor breaks easily, so
  `library_shots.py --check` on the `leflexitac-*` pictures was run again
  after the merges (the merge's verification of 2026-11-17: 0 of the 106
  pictures differ); the title "LeFlexiTac" (not "LeFlexiTac (SO-101)"); and
  which jaw carries LeFlexiTac's pad: its assembly video ("Attach grip tape
  to sensor and attach to the static jaw"), its page's step ("onto the
  'Wrist Roll'") and its cover photo put it on the static jaw, its docs
  page's hardware text on the moving jaw (both of LeFlexiTac's jaws have a
  flat face, 28.4 mm wide, where SO-ARM100's stock jaws are stepped, so
  their files do not tell); the Library's sensors are on both jaws,
  fitted on the moving jaw's face, and the static jaw's (where LeFlexiTac's
  pad sits) is the one seen edge-on
  (`library-look-work/look/out/leflexitac-review/pad-location-video-cover-render.png`).
  If the user says the static jaw, the static jaw's share of the wrist roll
  (its flat face 28.4 x 79.2 mm) becomes the part, the moving jaw the mate,
  and the homes, fits and pictures are made again.
- The Library's size after the merge of the grippers' lines (2026-11-17,
  `fpc-int-n-final` 21ca0c4): `web/library/` is 28.60 MB without its
  pictures and 8.84 MB of pictures (about 37.4 MB, from 16.41 MB and 18 MB
  of budget before the twelve grippers and hands; bodies 8.27 MB, art 1.01
  MB).  The budgets (`tests/test_library.py` `BUDGET_BYTES`,
  `SHOTS_BUDGET_BYTES`, `BODIES_BUDGET_BYTES`, `ART_BUDGET_BYTES`) were set
  once for the merged set with one dated note: 29.5, 9.2, 8.6 and 1.05 MB.
  Since the two hands' removal of 2026-11-17: 26.72 MB and 8.23 MB of
  pictures (about 35 MB; bodies 7.68 MB, art 0.95 MB), the budgets lowered
  to 27.6, 8.55, 8.0 and 0.985 MB.
  Whether the published site may carry that much is the user's call.
- Gen by Surface's sensor on the part (the merge's verification of
  2026-11-17): at the Exploded home the OpenArm 1.0's finger (its mounting
  plate) and the YUBI Gripper's pad on its base plate run off the pane's
  bottom, on all eight of their sensors (`web/cad/drape.js` frames the
  sheets and the part within `PART_FRAME_SHARE`, 3 times the sheets'
  radius, and these parts reach farther; the stack stays whole, 33 px or
  more from the other edges).  `tools/browser/cad_checks.py part_library`
  holds their cut to the bottom edge (`LIBRARY_CUT_BELOW`).  Framing these
  parts whole (a smaller stack in the pane) is the user's call.
- The default Row tail has 12 contacts; the FlexiTac reader needs
  `connector.row_pins = 16`.  Whether the default should follow the reader is
  open.
- Contact-zone thickness about 0.3 mm with the 0.1 mm PI default (the
  user's decision of 2026-11-06: JLC's rule, the 0.2 mm FPC + the
  stiffener) against the connectors' 0.30 +/- 0.03 mm; JLC holds the
  gold-finger area to +/- 0.03 mm and says the finished thickness is less
  where an area has no copper or coverlay, as at the contacts (the coverlay
  open, the bottom copper empty), so the notes ask to measure it on delivery
  if it matters.  How much thinner JLC's 2-layer 0.2 mm FPC is there is not
  published.
- The 0.127 mm default fan-out traces may come out at 0.1016 mm (JLC's
  +/-20% trace tolerance, its 1 oz minimum); whether the default should keep
  more margin (a wider `routing.trace_width_mm`) is a product question, as
  is any rule for trace width near bends or stiffener edges, where JLC sets
  none.
- D8, not implemented: 0.6 mm reference electrodes (default 1.0 mm since 2026-11-06),
  inter-electrode slits, alignment holes or fiducials, the canonical 12 x 32
  compatibility template.
- `tail.stiffener_end_clearance_mm` 0.5 mm is a product default, not a JLC
  rule; the default 12 mm bottom tail leaves 6.0 mm of flexible tail (1.5
  mm with the 7.5 mm default before P5-diagonal-bus.md section 27.7; the
  diagonal Row bus's Column tail runs straight down from the shared bottom
  edge, section 20; the straight channel's 7 mm tail leaves 0.72 mm, 0.88
  mm before the necked routing, whose merger meets the tail at 60 degrees,
  so the shoulder fillet starts lower), still short for the half twist the
  bottom tail needs (see INTEGRATION.md).
- The bus angle is the 60 degree cap for every bundle pitch, as T-D4
  decided, so the bend stagger grows with the pitch while the lateral move
  of the expansion shrinks: a pitch above 0.25 mm makes the expansion taller
  (64 rows: 9.23 mm at the default 0.254 mm, 17.89 mm at 0.4999 mm, 0 at
  0.5 mm; [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md#row-channel)) and can
  decide whether a large design fits, which `E_BOARD_SIZE` does not trace
  to the routing fields.  Choosing each run's angle to make it as short as
  possible would remove this, but changes every design whose bundle pitch is
  above about 0.25 mm, the default included.
- The Robotiq 2F-85 (2026-11-16, MuJoCo Menagerie's model, the user's
  decision): its card is the first of the grippers' grid because the
  parts' order is the multi-gripper video's, where it is second after the
  UMI finger; the last place (after the MakerMods Metal Arm) is one line of
  `parts.json`'s order if the user prefers it.  Its look leaves out the
  outer links' bright machined edges, the ROBOTIQ lettering and the
  coupling's status light ([LIBRARY_VIEW.md](../docs/LIBRARY_VIEW.md),
  "The Robotiq 2F-85").  After its review (2026-11-16): the edges are the
  studio photo's most visible metal, but Menagerie's `coupler.stl` has no
  chamfer (faces and walls, 159 mm² between them), so no pick by normal can
  take them; a silver band the project draws round each outer link is the
  user's to ask for (the bodies' budget, 3.1 MB, has 1.2 % to spare at
  3,064,252 bytes, so such a band would likely need it raised).  The tails
  leave the pad toward the palm and, at full opening (the review's measure),
  pass 3 to 8 mm behind the inner link's bridge; on a gripper that closes,
  that link moves against the fingertip, worth a look on a physical build.

External evidence still missing: a JLCPCB upload of the current outlines,
coverlay windows (the contact window has 0.05 mm lateral expansion) and
stiffener layers; whether JLC uses the extra ZIP members (`ORDER_NOTES.txt`
included), comment-form X2 attributes and the 0.1 mm PI layer; whether the
+/-0.05 mm outline tolerance and the gold-finger width are held; that
JLC builds the 2-layer 0.2 mm FPC with 1 oz copper and the bottom copper
empty, and the contact-zone thickness it delivers; connector insertion, continuity and an assembled
stack.

Engine notes found while testing (stage T, code unchanged):

- `engine/drc.py` `_long_axis` infers the electrode axis from where the
  electrode field outgrows the taxel field.  One Column electrode moved 0.6
  mm sideways (edited geometry) is then reported as parallel boards, with an
  `E_REGISTRATION` error at `tail.column_side`, next to the real
  `E_COPPER_EDGE_CLEARANCE`.  Generated designs are unaffected.
- `engine/layout.py` `_body_side` keeps every body-side step flush or at
  least one fillet radius wide (D5).  No DRC rule notices its loss, because
  the rolling-circle fillets round a narrower step as well (without it 311
  of 3948 boards of 2000 random designs keep a narrow step, all passing the
  DRC); `test_geometry_column` therefore pins the step rule itself.
- `engine/layout.py` `matrix_values` rounds inputs that `generate_design`
  has already canonicalised (mutant `E/F1-inputs` is equivalent).
- `engine/schema.py`: the catalogue text of `E_CONTACT_EXPOSURE` ("the
  contact window ...") and `E_OUTLINE_SELF_INTERSECTION` ("the outline ...")
  served by `/api/schema` and `/api/default` is narrower than the DRC, which
  raises them for electrodes and for cutouts as well;
  [LAYOUT_SCHEMA.md](../docs/LAYOUT_SCHEMA.md#issue-catalogue) describes
  what the DRC does.

Engine notes of the necked routing (2026-10-15):

- `engine/layout.py` `_size_advice` lowers two fields in step only when no
  single field is enough.  With the locked profile that branch is never
  reached: one row always fits (the tallest one-row board of a search, 32
  columns at 10 mm, an 80 mm tail, 64 contacts and the widest bundle, is
  321.25 x 194.30 mm against 234 x 490 mm), so `test_geometry_profile`
  reaches it with a 150 mm short side (mutant `E/size-advice`).
- `engine/layout.py` `column_plan` rounds the junction level down to the
  grid although every bend and the widening drop already lie on it; the
  rounding only removes float noise (602 designs byte-identical without it).
  Mutant `E/F1-heights` therefore drops the grid rounding of the bends where
  a diagonal meets its route's own column, which the grid test notices.
- After the independent review: `engine/drc.py` holds a route pair with a
  tail piece to the finger-section spacing instead of the trace space
  (`route_route_clearance` and its `finger_section`).  Before, the 0.246 mm
  gap held by construction only, and two reviewer mutants that shortened the
  widening drop for bundle widths between 0.127 and 0.25 mm passed the suite
  (now mutant `E/junction-drop-mid`).  `engine/layout.py` `_bends` rounds the
  bend where a diagonal meets its own column away from the bundle: rounded
  to the nearest grid value, diagonals 1e-4 mm wide (a bundle pitch near
  0.5 mm) leaned past the cap, by up to 0.26 degrees in the review's sweep
  (mutant `E/bend-rounding`).

## Run and resume

From this directory (`fpc_agentic_customization/`):

```bash
PYTHONPATH=. python3 -B -m unittest discover -s tests
node --check web/app.js
python3 app.py                # http://127.0.0.1:8008 (the Library; the generator at /gen.html) ; --port 8009 for another port
python3 app.py --allow-host abc-8008.usw2.devtunnels.ms   # also serve a tunnel/proxy/LAN Host name
python3 cli.py export design.json --out outputs/
```

```python
from engine import default_design, generate_design
from exporters import build_exports

result = generate_design(default_design())
assert result["ok"], result["validation"]["errors"]
artifacts = build_exports(result)  # three bytes-valued ZIPs
```

No dependency installation is required; the engine finds its profile
relative to its source, independently of the working directory.  The
active-thread log `claude/WORK_LOG.md` is a local file, git-ignored by design
(see `.gitignore`) and not part of this checkout; start it from the
workspace's `WORK_LOG.template.md` at the repository root.  Dated session
notes go to `claude/sessions/week-of-<Monday>/<date>.md`.
