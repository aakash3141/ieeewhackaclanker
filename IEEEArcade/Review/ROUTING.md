# Four-layer PCB routing — 2026-11-10

The saved `IEEEArcade.kicad_pcb` is routed at **200 x 125 mm**, with 16 button connectors along each of the top and bottom edges. All 285 schematic components and seven mounting holes retain their current positions, orientations, footprints and numbered-pad nets. Schematics and project rules were preserved byte-for-byte.

## Copper and connections

| Layer | Use |
|---|---|
| F.Cu | Components, local signals, outer ground fill and local buck VIN/output copper |
| In1.Cu | Ground reference; one continuous filled copper island, respecting all Pico keepouts |
| In2.Cu | Split +12V, +3V3, +5V and +5V_DISPLAY pours plus selected signal routes |
| B.Cu | Signal routing, outer ground fill and a wide lamp-power bus |

There are **9 copper pours**, **6,234 track segments**, **668 through vias** and **1,801 filled native KiCad teardrops**. Vias are 0.60 mm diameter with 0.30 mm drills; 65 are dedicated ground stitching vias. Other vias provide actual signal/power transitions or plane connections. Unused fanout vias were omitted.

Signals generally use 0.25 mm tracks; lamp-cathode connections use 0.50 mm. Explicit 0.60 mm power links maintain +3V3 and +5V_DISPLAY continuity where inner pours are segmented by clearances. The VSYS feed uses 0.80 mm tracks. The 12V lamp supply has a 3.0 mm back-layer trunk and 1.0 mm connector branches, in addition to its internal copper. These geometry choices do not certify the actual load rating or board temperature; confirm lamp current and validate the assembled hardware.

The buck SW power path is entirely on F.Cu, with 0.80 mm main tracks and two short 0.60 mm necks at U2. The BOOT-capacitor branch remains narrow. Local VIN/output pours support the input and output loops. There are no vias in the SW, BOOT or FB connections. Layout still requires regulator load-step and thermal validation on hardware.

All existing Pico antenna, underside/test-pad and USB keepout geometry and restrictions remain intact. Two unnumbered paste-only rectangular pad objects that triggered false RF-pad keepout errors were converted to equivalent filled F.Paste rectangles. Their actual aperture bounds were checked to within 1 micrometre; copper, mask, numbered pads and stencil aperture geometry were preserved. The board-local Pico footprint therefore intentionally differs from the installed library and retains its mismatch warning. No keepout was weakened and no DRC exclusion was added.

HUB75 ground pads use solid zone connections to avoid incomplete thermal spokes; the display-buffer power pour also uses solid connections. Other ordinary through-hole ground connections retain thermal reliefs. Account for solid-plane connections when soldering.

## Validation

Final physical DRC: **0 errors, 0 unrouted connections, 1 warning**. The sole physical warning is the documented Pico/library-footprint mismatch. Native schematic parity still reports **199 pre-existing 'No corresponding pin found in schematic' warnings**. These were not suppressed. Independent validation checks all **867 schematic pad-to-net assignments** and passes **1,475 checks**, including placement, outline, keepouts, layer count, via dimensions, filled pours/teardrops and unchanged schematic/project files.

Reports: [routing-drc-final.json](routing-drc-final.json), [routing-verification.json](routing-verification.json), [routing-verification.txt](routing-verification.txt). The audit is repeatable with KiCad 10's bundled Python and `verify_routed_pcb.py`.

## Deferred power and fabrication status

At the user's explicit request, the missing supply connection to **+5V_DISPLAY is deferred**. Its existing loads are fully interconnected, but no external input was restored and it was not tied to the controller's +5V. The display buffers will need a defined supply before the scoreboard can operate. This board-level 'zero unrouted' result does not resolve that schematic-level missing source or establish the unidentified panel's voltage/current rating.

Existing `Gerber/` and `Gerber.zip` were not regenerated and do not represent this routed revision. Resolve the display-power connection and review the remaining footprint/native-parity warnings, fabrication stackup and actual load requirements before manufacturing release. No order or fabrication upload was made.

## Artifacts and backup

- [PCB-routed-3D.png](PCB-routed-3D.png): routed top-view preview.
- [PCB-routed-top.svg](PCB-routed-top.svg): zoomable front copper/silkscreen/outline.
- [PCB-routed-ground.svg](PCB-routed-ground.svg): inner ground-plane artwork.
- `.layout-backup/before-routing-20261110/`: original board/project/schematic snapshot and the verified routed board before final cleanup.
- `.layout-backup/routing-work-20261110.zip`: routing source code, intermediate grid/path data and initial DRC reports. These are historical/reproduction inputs; do not rerun the placement/routing generators over subsequent board edits.
