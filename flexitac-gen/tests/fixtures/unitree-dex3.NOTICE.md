# tests/fixtures/unitree-dex3.stl

A test fixture of gently curved faces (docs/CAD_MODE.md "Gently curved
faces"; tests/test_surface_curved.py, tools/browser/cad_checks.py
part_curved): the Unitree Dex3-1's fingertip, the Library's mesh until the
hand was removed from the Library on 2026-11-17, and again since it came
back on 2026-11-18 (`web/library/meshes/unitree-dex3.stl`; byte for byte
that file of bff728c, SHA-256
`9fb4d06c219e39c2578297a0638a76dd0b868823b659ebaa9e69143fa4e522d3`).

It is not the upstream file (BSD-3-Clause): it is unitree_ros's
(`b579bbe`)
`robots/dexterous_hand_description/dex3_1/meshes/left_hand_index_1_link.STL`
(SHA-256 `9e315ebc8a7a0cb98e033985b586b20d81cf8aa761181ae61ce56fcb14077a06`),
the Dex3-1's fingertip link, scaled from metres to millimetres, its bracket
unchanged and its fingertip cap, ridged up to 0.24 mm deep, replaced by the
cap's convex hull made mirror-symmetric across the link's mid-plane (z = 0),
written as a binary STL of 15524 facets, changed by the FlexiTac-Gen project
in 2026.  Unitree and Dex3 are trademarks of their holder; their use here
names the part only and implies no endorsement.

## Licence

BSD 3-Clause License

Copyright (c) 2016-2022 HangZhou YuShu TECHNOLOGY CO.,LTD. ("Unitree Robotics")
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
