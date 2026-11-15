// The checks of drape.js wrapMapper on the UMI finger with the Library's showcase (docs/LIBRARY_VIEW.md "A placed
// sensor"): one function of drape.js's module D, the part's positions (mm), the placed record and its art, giving
// {problems: [...], ...numbers}.  Plain JavaScript with no import and no export, so that the probe's module of
// tools/browser/showcase_checks.py (in Chromium) and the node driver of tests/test_showcase.py share this text.
function wrapChecks(D, positions, placed, art) {
  const problems = [];
  const mapper = D.wrapMapper(placed, {positions, scale: 1});
  if (!mapper) return {problems: ["wrapMapper gave no map"]};
  const {origin: O, x: X, y: Y} = placed.face;
  const N = [X[1] * Y[2] - X[2] * Y[1], X[2] * Y[0] - X[0] * Y[2], X[0] * Y[1] - X[1] * Y[0]];
  const side = placed.wrap.side === "left" ? -1 : 1;
  const S = X.map(value => value * side);
  const {edge_mm: edge, radius_mm: r, fold} = mapper.wrap;
  const quarter = (Math.PI / 2) * r;
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  const angle = (a, b) => Math.acos(Math.max(-1, Math.min(1, dot(a, b) / (Math.hypot(...a) * Math.hypot(...b)))));
  const depthAt = t => {
    // The fold line's depth at height t (the majorant's, its end pieces running on), radius_mm at least.
    let k = 0;
    while (k + 2 < fold.length && fold[k + 1][0] <= t) k += 1;
    const [a, b] = [fold[k], fold[k + 1]];
    return Math.max(r, a[1] + ((t - a[0]) * (b[1] - a[1])) / (b[0] - a[0]));
  };
  // The fold line: a concave majorant of the part's section (its slopes never rise), over the part's whole height.
  let concave = true;
  for (let k = 0; k + 2 < fold.length; k += 1) {
    const s0 = (fold[k + 1][1] - fold[k][1]) / (fold[k + 1][0] - fold[k][0]); const s1 = (fold[k + 2][1] - fold[k + 1][1]) / (fold[k + 2][0] - fold[k + 1][0]);
    if (!(s1 < s0)) concave = false;
  }
  if (!concave) problems.push("the fold line is not concave");
  let under = 0;
  for (let k = 0; k + 2 < positions.length; k += 3) {
    const p = sub([positions[k], positions[k + 1], positions[k + 2]], O);
    under = Math.max(under, -dot(p, N) - depthAt(dot(p, Y)));
  }
  if (under > 1e-6) problems.push(`the part reaches ${under} mm past the fold line`);
  // 1. The face: the plane itself, its normal the face's, also beyond its far edge.
  let faceError = 0; let faceTurn = 0; let faceOn = true;
  for (let a = 0; a <= 2 * edge + 5; a += 0.7) for (let v = -60; v <= 40; v += 2.5) {
    const u = side * (edge - a);
    const hit = mapper.xyz([u, v]);
    const flat = [0, 1, 2].map(k => O[k] + (X[k] * u + Y[k] * v));
    faceError = Math.max(faceError, dist(hit.xyz, flat));
    faceTurn = Math.max(faceTurn, angle(mapper.outward([u, v]), N));
    faceOn = faceOn && hit.on === true;
  }
  if (faceError > 1e-12 || faceTurn > 1e-12 || !faceOn) problems.push(`the face is not its plane: ${faceError} mm, ${faceTurn} rad, on ${faceOn}`);
  // 2. No tear: steps of 0.02 mm across the folds at every height, down the sheet at every distance past the edge, and
  //    askew; level lines keep their length; up to the fold line every step keeps its length.
  const step = 0.02; const reach = 62;
  let stretch = 0; let level = 0; let rigid = 0; let inside = 0; let steps = 0;
  const walk = (from, to, kind) => {
    const count = Math.round(Math.hypot(to[0] - from[0], to[1] - from[1]) / step);
    let before = null; let uvBefore = null;
    for (let k = 0; k <= count; k += 1) {
      const uv = [from[0] + ((to[0] - from[0]) * k) / count, from[1] + ((to[1] - from[1]) * k) / count];
      const p = mapper.xyz(uv).xyz;
      const d = side * uv[0] - edge; const q = r + d - quarter;
      // Outside the finger's section: not nearer the middle than the side face unless behind the fold line.
      const rel = sub(p, O);
      if (d > 0 && dot(rel, S) < edge - 1e-9 && -dot(rel, N) < depthAt(dot(rel, Y)) - 1e-9) inside += 1;
      if (before) {
        const flat = Math.hypot(uv[0] - uvBefore[0], uv[1] - uvBefore[1]); const ratio = dist(p, before) / flat;
        stretch = Math.max(stretch, ratio);
        if (kind === "level") level = Math.max(level, Math.abs(ratio - 1));
        if (q <= depthAt(uv[1]) && r + (side * uvBefore[0] - edge) - quarter <= depthAt(uvBefore[1])) rigid = Math.max(rigid, Math.abs(ratio - 1));
        steps += 1;
      }
      before = p; uvBefore = uv;
    }
  };
  for (let v = -50; v <= 34; v += 3.5) walk([side * (edge - 2), v], [side * (edge + reach), v], "level");
  for (let d = 1; d <= reach; d += 4.3) walk([side * (edge + d), -50], [side * (edge + d), 34], "down");
  for (const [v0, v1] of [[-50, 20], [30, -45], [-20, 34]]) walk([side * (edge - 2), v0], [side * (edge + reach), v1], "askew");
  // (A step's chord over a turn of radius r is shorter than its arc by step^2 / 24 r^2 of it.)
  const chord = (step * step) / (24 * r * r) + 1e-9;
  if (stretch > 1.5) problems.push(`a step tears: ${stretch} times as long on the part`);
  if (level > 2 * chord) problems.push(`a level line changes its length by ${level}`);
  if (rigid > 2 * chord) problems.push(`the roll is not rigid up to the fold line: ${rigid}`);
  if (inside) problems.push(`${inside} points of the roll are inside the finger's section`);
  // 3. Where the real pad lands: the boards' own points (their art's outline frames: drape.js svgToBase and baseToUv).
  const region = art.boards.row.region;
  const frame = {O: [0, 0], F: [-region[2] / 2, -region[3] / 2], ex: [1, 0], ey: [0, 1]};
  const where = (key, sx, sy) => {
    // A point of a board's SVG on the part: {tip: mm from the fingertip, depth: behind the face, across, normal}.
    const uv = D.baseToUv(frame, D.svgToBase(art.boards[key], frame, [sx, sy]));
    const rel = sub(mapper.xyz(uv).xyz, O); const n = mapper.outward(uv);
    return {uv, depth: -dot(rel, N), across: dot(rel, S), n: [dot(n, S), dot(n, N), dot(n, Y)]};
  };
  const tipAt = Math.max(...fold.map(point => point[0]));
  const outline = key => D.outlineRings({outline: art.boards[key].outline});
  const landing = {};
  for (const key of ["row", "column"]) {
    const rings = outline(key);
    // The gold end: the outline's corners farthest along the sheet from the side edge.
    const corners = rings.outline.map(([sx, sy]) => where(key, sx, sy));
    const far = Math.max(...corners.map(corner => side * corner.uv[0]));
    const end = corners.filter(corner => side * corner.uv[0] > far - 1e-6);
    landing[key] = {end_tip_mm: [Math.min(...end.map(c => tipAt - c.uv[1])), Math.max(...end.map(c => tipAt - c.uv[1]))],
      end_behind: end.every(c => c.n[1] < -0.5 && c.across < edge), end_across: end.map(c => c.across)};
  }
  // The straps on the side face: the A's two arms (the Bottom FPC, the row board) and the Top FPC's tail (the column
  // board), each at its middle height, 5 mm down the side past the first quarter turn: of the board there (in its
  // outline, in no cut-out), on the side's plane, its normal the side's.
  const within = (ring, x, y) => {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
      const [xi, yi] = ring[i]; const [xj, yj] = ring[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  };
  const strap = (key, v) => {
    const [sx, sy] = D.baseToSvg(art.boards[key], frame, D.uvToBase(frame, [side * (edge + quarter + 5), v]));
    const rings = outline(key); const hit = where(key, sx, sy);
    return within(rings.outline, sx, sy) && !rings.cutouts.some(ring => within(ring, sx, sy)) && hit.n[0] > 0.999 && Math.abs(hit.across - (edge + r)) < 1e-9;
  };
  const straps = {upper_arm: strap("row", 16), lower_arm: strap("row", -15.7), top_tail: strap("column", -36.5)};
  // 4. The sheet lifted off the face (the explode): at 0 the map itself; lifted, the face's plane that much higher, a
  //    level line still its length, and lifted past its reach the A's far end hangs on the side's plane.
  let liftZero = 0; let liftFace = 0; let liftLevel = 0;
  for (let d = -20; d <= reach; d += 3.1) for (let v = -44; v <= 32; v += 4.7) {
    const uv = [side * (edge + d), v];
    liftZero = Math.max(liftZero, dist(mapper.lifted(0).xyz(uv), mapper.xyz(uv).xyz));
  }
  for (const h of [5, 14.19, 42.57]) {
    const held = mapper.lifted(h);
    for (let a = 0; a <= 2 * edge; a += 1.3) for (let v = -40; v <= 32; v += 6) {
      const u = side * (edge - a);
      liftFace = Math.max(liftFace, dist(held.xyz([u, v]), [0, 1, 2].map(k => O[k] + (X[k] * u + Y[k] * v) + N[k] * h)));
    }
    for (let v = -42; v <= 30; v += 8) {
      let before = null;
      for (let d = -2; d <= reach; d += step) {
        const p = held.xyz([side * (edge + d), v]);
        if (before) liftLevel = Math.max(liftLevel, Math.abs(dist(p, before) / step - 1));
        before = p;
      }
    }
  }
  if (liftZero > 0) problems.push(`the sheet lifted by 0 is not the sheet: ${liftZero} mm`);
  if (liftFace > 1e-9) problems.push(`the lifted face is not the face's plane lifted: ${liftFace} mm`);
  if (liftLevel > 2 * chord + 1e-6) problems.push(`a level line of the lifted sheet changes its length by ${liftLevel}`);
  const rowRings = outline("row");
  const farCorner = rowRings.outline.map(([sx, sy]) => D.baseToUv(frame, D.svgToBase(art.boards.row, frame, [sx, sy]))).sort((a, b) => side * (b[0] - a[0]))[0];
  const hung = mapper.lifted(60); const hungNormal = hung.outward(farCorner);
  const hangs = dot(hungNormal, S) > 0.999 && Math.abs(dot(sub(hung.xyz(farCorner), O), S) - (edge + r)) < 1e-9;
  if (!hangs) problems.push("lifted past its reach, the A's far end does not hang on the side's plane");
  // 5. The stack (placedStack): exploded by the lift, over the finger's width; its film seen through the slots; each
  //    layer's field its step higher than the one under it; no vertex of a sheet inside the finger's section, in either
  //    mode (the stack's world: x and y the face's, z its normal, the origin the field's centre).
  const boards = {row: {outline: art.boards.row.outline}, column: {outline: art.boards.column.outline}};
  const stack = D.placedStack({placed, vertices: {positions, scale: 1}, arts: art, boards, partBox: null});
  let leanDeg = 0;
  const facts = stack && {explode: stack.explode, gap_mm: stack.gap_mm, nest_mm: stack.nest_mm, width_mm: stack.width_mm, film_seen: stack.film_seen,
    bottom: stack.bottomKey, top: stack.topKey, vertices: {bottom: stack.sheets.bottom.count, film: stack.sheets.film.count, top: stack.sheets.top.count}};
  if (!stack) problems.push("placedStack gave no stack");
  else {
    let buried = 0; let apart = 0; let lifted = true; let hung = 0;
    const [, , aw, ah] = region;
    for (const sheet of Object.values(stack.sheets)) {
      lifted = lifted && sheet.liftedNormals instanceof Float32Array && sheet.liftedNormals.length === 3 * sheet.count;
      // Its normals exploded (liftedNormals, the mesh's own there) against the map's of the sheet so lifted.
      const held = lifted ? mapper.lifted(sheet.layer * stack.gap_mm) : null;
      for (let k = 0; k < sheet.count; k += 1) {
        if (!sheet.inside[k]) continue;
        if (held) {
          const normal = held.outward(D.baseToUv(stack.frame, [sheet.base[2 * k], sheet.base[2 * k + 1]]));
          const drawn = [sheet.liftedNormals[3 * k], sheet.liftedNormals[3 * k + 1], sheet.liftedNormals[3 * k + 2]];
          const lean = angle([dot(normal, X), dot(normal, Y), dot(normal, N)], drawn);
          leanDeg = Math.max(leanDeg, Number.isFinite(lean) ? (lean * 180) / Math.PI : 180);
          if (dot(normal, S) > 0.999) hung += 1;
        }
        for (const array of [sheet.positions, sheet.assembled]) {
          const across = side * array[3 * k]; const t = array[3 * k + 1]; const depth = -array[3 * k + 2];
          if (across < edge - 1e-3 && depth > 1e-3 && depth < depthAt(t) - 1e-3) buried += 1;
        }
        const bx = sheet.base[2 * k]; const by = sheet.base[2 * k + 1];
        if (bx >= 0 && bx <= aw && by >= 0 && by <= ah) {
          apart = Math.max(apart, Math.abs(sheet.positions[3 * k + 2] - sheet.assembled[3 * k + 2] - sheet.layer * stack.gap_mm));
        }
      }
    }
    if (buried) problems.push(`${buried} vertices of the stack are inside the finger's section`);
    if (apart > 1e-3) problems.push(`a layer's field is not its step higher exploded: ${apart} mm off`);
    if (!lifted) problems.push("a sheet has no lifted normals");
    // (Measured 5.4 degrees at most, where a triangle spans the start of a turn; a normal left the face's is 90 off on
    // the hanging tails, which several hundred vertices of the boards are on.)
    else if (leanDeg > 15) problems.push(`a sheet's lifted normals lean ${leanDeg} degrees off the lifted sheet's own`);
    else if (hung < 100) problems.push(`only ${hung} vertices of the exploded stack hang beside the finger`);
    if (typeof stack.respace !== "function") problems.push("the stack cannot be respaced");
    else {
      // Respaced (the Library's stage between a gripper's jaws): the same sheets at another step, then back.
      const before = Float32Array.from(stack.sheets.top.positions);
      stack.respace(6);
      const top = stack.sheets.top; let moved = 0; let k0 = -1;
      for (let k = 0; k < top.count && k0 < 0; k += 1) if (top.inside[k] && top.base[2 * k] > 1 && top.base[2 * k] < aw - 1 && top.base[2 * k + 1] > 1 && top.base[2 * k + 1] < ah - 1) k0 = k;
      moved = top.positions[3 * k0 + 2] - top.assembled[3 * k0 + 2];
      if (stack.gap_mm !== 6 || Math.abs(moved - 3 * 6) > 1e-3) problems.push(`respaced to 6 mm, the top FPC stands ${moved} mm higher (gap_mm ${stack.gap_mm})`);
      stack.respace(facts.gap_mm);
      let back = 0;
      for (let k = 0; k < before.length; k += 1) back = Math.max(back, Math.abs(before[k] - top.positions[k]));
      if (back > 1e-4) problems.push(`respaced back, the top FPC moved ${back} mm`);
    }
  }
  // 6. A part shallower than the bend (a slab 0.5 mm thick, the same radius): the fold line stays radius_mm deep, so
  //    the two quarter turns are one half turn about one line and the sheet goes on behind the slab, two radii behind
  //    the face, without a tear, a level line still its length.
  const slab = [];
  for (const x of [-10, 10]) for (const y of [-20, 20]) for (const z of [-0.5, 0]) slab.push(x, y, z);
  const thin = D.wrapMapper({face: {origin: [0, 0, 0], x: [1, 0, 0], y: [0, 1, 0]}, wrap: {side: placed.wrap.side, radius_mm: r}}, {positions: slab, scale: 1});
  let thinLevel = null;
  if (!thin) problems.push("wrapMapper gave no map of a thin slab");
  else {
    thinLevel = 0;
    let before = null;
    for (let d = -2; d <= 20; d += step) {
      const p = thin.xyz([side * (10 + d), 3]).xyz;
      if (before) thinLevel = Math.max(thinLevel, Math.abs(dist(p, before) / step - 1));
      before = p;
    }
    const far = [side * 30, 3]; const end = thin.xyz(far).xyz; const turned = thin.outward(far);
    if (thinLevel > 2 * chord + 1e-6) problems.push(`on a slab thinner than the bend a level line changes its length by ${thinLevel}`);
    if (Math.abs(end[2] + 2 * r) > 1e-9 || turned[2] > -0.999999) problems.push(`on a slab thinner than the bend the sheet ends ${-end[2]} mm behind the face, its normal ${turned}`);
  }
  return {problems, edge_mm: edge, radius_mm: r, fold: fold.length, face_error_mm: faceError, stretch, level, rigid, steps, landing,
    straps, width_mm: mapper.width_mm, tip_mm: tipAt, lift_level: liftLevel, lean_deg: leanDeg, thin_level: thinLevel, stack: facts};
}
