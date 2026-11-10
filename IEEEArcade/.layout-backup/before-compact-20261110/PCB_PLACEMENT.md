# IEEE Arcade PCB placement — 2026-11-05

The saved `IEEEArcade.kicad_pcb` contains 292 schematic components and seven PCB-only mounting holes. All schematic files were preserved byte-for-byte. There are **zero tracks, zero vias, and zero copper zones**. Existing Pico footprint rule areas are retained; these are keepouts, not copper pours. This is a placement proposal for enclosure review and subsequent routing.

## Outline and access

- Outline: **360 × 140 mm**, rectangular, x=30…390 and y=30…170 mm in the PCB editor. The long dimension follows from placing 32 independently accessible button connectors on one edge. Confirm enclosure fit and the fabricator's maximum board size before ordering.
- J11…J42: top edge, channel 01…32 left to right, 10.5 mm center spacing. All have identical 90° orientation, with their four-pin rows perpendicular to the edge. Pin 1 is the inboard end. Each has channel identification, reference, and `1:LED+ 2:LED- 3:NO 4:COM` legend. Existing square pin-1 pads and footprint markings are retained.
- The schematic specifies **vertical/top-entry** JST XH headers. Plugs withdraw upward; the latch side faces toward the board edge. The approximately 5.75 mm housing width leaves roughly 4.75 mm between adjacent housings. Actual cable plug, latch, finger and harness bend clearances must be checked with the physical harness. Right-angle headers would require an explicit schematic footprint change and a different placement.
- J1 barrel jack faces left at the left edge, with its body face about 0.5 mm inside the outline. F1 remains accessible beside it. Its named library footprint is exact to PJ-063AH, but independent drawing/plug-fit verification remains open: the manufacturer's PDF requests were blocked. J1 is **provisional mechanically**.
- J3 HUB75 and J4 external display-buffer 5 V input sit at the bottom edge, with room for upward plug removal. A1's USB faces the bottom edge. Do not confuse J4's external display supply with the controller buck output.
- Seven 3.2 mm NPTH M3 holes use 6.4 mm footprint courtyards. Positions in board coordinates: H1 (36,36), H2 (210,99), H3 (384,36), H4 (36,164), H5 (130,164), H6 (275,164), H7 (345,164). Subtract (30,30) to measure from the board's upper-left corner. H2 provides central support. These are proposed positions, not an enclosure-derived mounting pattern; verify actual screw heads, washers and standoffs.

## Functional placement

Each button channel's AO3400A, gate resistor/pull-down, switch pull-up/series resistor and filter capacitor are placed in a column behind its connector. U1/U5 serve channels 01–16; U4/U6 serve 17–32. Local bypass capacitors sit beside the actual VDD pads. The EEPROM, I2C/reset pull-ups and 3.3 V bulk decoupling are beside the Pico.

The converter sits beside the left-edge input/fuse. C14 is nearest VIN/GND, with C12/C13 nearby. L1's switching end faces U2, C19 is beside BOOT, and R10/R11/C18 are on the feedback side. The output capacitors sit toward the output end of L1. Placement follows the intent of [TI's TPS54202H layout guidance, section 10](https://www.ti.com/lit/ds/symlink/tps54202h.pdf): short switching paths, nearby bypassing, and feedback separated from switching current. During routing, use a short/wide SW connection, Kelvin feedback ground and output sensing, and a compact input-current loop. Placement alone does not validate the converter's thermal behavior or stability.

The HUB75 buffers sit directly above the display connector, with local supply bypassing, source damping resistors and pull-down banks nearby. The Pico antenna and underside/test-pad keepouts remain present on all specified layers; keep the enclosure and harness away from the antenna as well. No new copper or components may be placed inside its RF keepouts during routing.

## Layers and fabrication defaults

Four copper layers are enabled. Intended routing use (no planes/pours have been created):

| Layer | Intended use | Copper thickness |
|---|---|---:|
| F.Cu | Components, local signals, short power connections | 35 µm / nominal 1 oz |
| In1.Cu | Future continuous ground reference | 35 µm / nominal 1 oz |
| In2.Cu | Future power distribution and sparse secondary signals | 35 µm / nominal 1 oz |
| B.Cu | Secondary signals and power connections | 35 µm / nominal 1 oz |

Nominal total stackup: **1.60 mm**, FR4, ENIG finish, 0.20/1.04/0.20 mm dielectric spacing, four 0.035 mm copper layers and two 0.010 mm solder masks. Dielectric constants are placeholders (Er 4.5); exact materials, finished copper, thickness tolerance, achievable core/prepreg construction and pricing must be confirmed with the selected fabricator. No impedance targets are specified. Four layers reserve a ground reference for the display/MCU signals and room for power distribution across the long connector row.

Initial minimums: 0.20 mm copper clearance and trace width, 0.50 mm copper-to-edge, 0.25 mm hole clearance and hole-to-hole spacing, 0.30 mm through drill, 0.60 mm via diameter, 0.15 mm annular ring, and 0.15 mm silk clearance. Defaults use 0.70/0.30 mm vias.

| Net class | Suggested starting width | Clearance |
|---|---:|---:|
| Default / Switch / Display | 0.25 mm | 0.20 mm |
| Power_3V3 | 0.60 mm | 0.20 mm |
| Power_5V (also GND) | 1.00 mm | 0.25 mm |
| Power_12V | 3.00 mm | 0.25 mm |
| Lamp | 0.50 mm | 0.25 mm |
| Buck_SW | 1.00 mm | 0.25 mm |

Assignments include the input-to-fuse net, supply rails, VSYS, lamp cathodes, raw switch nets, filtered switches, lamp enables, display signals and SW node. These are routing defaults, **not minimum-width current-rating guarantees**. The shared lamp supply/return must be sized for the actual aggregate load, board-length voltage drop and temperature rise. Prefer broad power distribution and a continuous ground return in the routing stage; use multiple vias for ampere-level layer transitions. Gate logic nets may use narrower local connections where appropriate. Power widths may need neck-downs at pads.

## Footprint and connectivity checks

All 292 schematic references are present exactly once. All assigned footprint files resolve, assigned library IDs match the schematic, and every schematic pin has a matching PCB pad number. All **883 schematic pad-to-net assignments** were checked after saving. No schematic symbol or footprint assignment was changed. Detailed footprint-file audit: `placement-footprint-audit.json`.

The custom L1 library and board silkscreen were trimmed around the existing lands to remove silk-over-mask warnings. Its lands, courtyard, dimensions and assignment were preserved. Originals of the board, project and inductor footprint are in `.layout-backup/before-placement-20261105/`.

Final KiCad DRC with schematic parity checking: `placement-drc.json`.

- **No courtyard overlaps, hole-clearance errors, solder-mask bridges, outline errors, copper-edge errors, or silkscreen clearance violations.**
- **499 unconnected items**, expected for this entirely unrouted board.
- **Two errors remain:** A1's own two paste-only pads are reported inside its RF keepout. These exact errors were also present in the pre-placement board. The footprint's copper/RF prohibitions were not weakened or excluded to hide them. Resolve the footprint's paste/keepout interaction before stencil/fabrication release.
- **One warning remains:** the rotated A1 footprint is reported as differing from the installed Module library. Review/reload the Pico footprint in the PCB editor before fabrication; preserve its nets and all RF/USB/underside keepouts.
- **199 schematic parity warnings remain**, all `No corresponding pin found in schematic`. The pre-placement board produces the same 199 warnings, including the same affected pad UUIDs. Independent XML-netlist-to-PCB checking passes for all 883 pin assignments. The native parity discrepancy remains unresolved; do not treat this as a clean native schematic-parity result. No DRC exclusions or lowered severities were added.

Baseline report: `.layout-backup/placement-baseline-drc.json`. The earlier schematic review documents are historical and do not describe this PCB placement.

## Review artifacts

- `PCB-placement.png`: top-view 3D preview. Missing or simple library 3D models do not imply missing footprints.
- `PCB-placement.svg`: native top copper/silkscreen/outline plot for zooming into labels.
- `placement-positions.csv`: component and mounting-hole position/orientation list.
- `placement-verification.json`: inventory, pad checks, schematic hashes and DRC summary.

Review the proposed dimensions, harness access, mounting pattern, J1 plug fit and remaining Pico/parity findings before proceeding to routing. No fabrication outputs were generated.
