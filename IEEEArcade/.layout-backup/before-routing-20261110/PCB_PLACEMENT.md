# IEEE Arcade compact PCB placement — 2026-11-10

`IEEEArcade.kicad_pcb` now measures **200 x 125 mm**, reduced from 360 x 140 mm. Board area falls from 50,400 to 25,000 mm², a **50.4% reduction**. Actual fabrication cost depends on the fabricator, quantity and stackup; no quote or order was made.

## Arrangement

- Board outline: x=30…230 mm, y=30…155 mm.
- Top edge: J11…J26, channels 01…16, left to right.
- Bottom edge: J27…J42, channels 17…32, left to right in a top view.
- Button connector spacing is 8 mm center-to-center. Existing top-entry JST XH headers are retained; both banks face outward, with pin1 at the inboard end. Nominal 5.75 mm housing width leaves 2.25 mm between bodies. Physical plug/latch and finger access still need an enclosure/harness check.
- Channel parts follow their connectors inward. Channels31/32 retain only their switch input circuits; their unused lamp circuits are gone.
- Power input faces left; fuse, input bulk capacitor and buck components occupy the upper-left area. Relative positions within the existing buck cluster were preserved.
- U1/U5/U4/U6 sit across the middle. Their 100nF bypass capacitors are beside VDD pin9. The Pico USB faces the right edge; EEPROM and I2C/reset pull-ups sit below it. All existing Pico RF, underside and USB keepout polygons and restrictions are preserved. The channel12/28 filter components were offset to clear the RF region.
- U7/U8 and HUB75 J3 occupy the bottom-left area. Source damping resistors and input pull-downs remain beside the buffers.
- Seven 3.2 mm mounting holes remain: H1(36,36), H2(224,36), H3(36,149), H4(224,149), H5(121,86), H6(36,90), H7(224,60), in board coordinates. This is a proposed mounting pattern, not a verified enclosure pattern.

## Current schematic compatibility

The saved board contains all **285 current schematic components** and seven PCB-only mounting holes. Eight obsolete footprints absent from the current schematic were removed: J4, Q31/Q32, R131/R132, R231/R232 and R610. The current R613 was retained. The current schematic pad nets were already synchronized before compaction and remain unchanged.

Schematic files and `IEEEArcade.kicad_pro` were preserved byte-for-byte. No footprint assignments, component values, layer count, stackup, design rules or DRC severities were changed. Four copper layers remain enabled. There are still **zero tracks, zero vias and zero copper zones**; this is component placement, not a routed or fabrication-ready board. Existing Gerbers and Gerber.zip were not regenerated and do not describe this layout.

## Validation

`verify_compact_pcb.py` checks the current exported netlist against the saved PCB, all **867 pad-to-net assignments**, component inventory/footprints/values, the two connector banks, exact outline, layer count, preserved keepout rules/areas and unchanged schematic/project hashes. Detailed results: `compact-connectivity-verification.txt` and `compact-placement-verification.json`.

KiCad DRC has **no new findings** compared with the board saved at the start of this task. There are no courtyard overlaps, hole-clearance violations, solder-mask bridges, outline/copper-edge errors, silkscreen-clearance or text-height warnings.

The same two existing A1 paste-pad/antenna-keepout errors and one existing A1/library-footprint mismatch warning remain. They were not suppressed. The wholly unrouted board has 499 reported unconnected items. Native schematic parity has 199 existing `net_conflict` warnings; eight extra-footprint warnings were removed. Independent netlist-to-pad checks pass, but the native parity warnings remain unresolved. This is not a clean fabrication sign-off.

Reports: `compact-parity-drc.json` and `compact-baseline-parity-drc.json`. Before/after finding UUIDs were compared: no new physical or parity findings. Reference silkscreen placement was checked, including references that fit within component courtyards while clearing the actual pads and graphics.

## Review and restore

- `PCB-compact-3D.png`: top-view 3D preview; some custom components have no 3D model.
- `PCB-compact.svg` / `PCB-compact.png`: copper, silk and outline preview.
- `compact-placement-positions.csv`: final reference positions and rotations.
- `compact_pcb.py`: reproducible placement script loading the saved pre-compaction snapshot. Do not rerun it after making further PCB edits or routing.
- Original board/project and matching schematic context: `.layout-backup/before-compact-20261110/`.

Routing, power-distribution sizing, thermal/signal checks, enclosure fit and the remaining Pico/native-parity findings must be addressed before fabrication.
