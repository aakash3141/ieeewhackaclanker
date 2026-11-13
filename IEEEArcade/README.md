# IEEE Arcade

Open **IEEEArcade.kicad_pro** in KiCad. The main schematic, PCB and all five child sheets are required: button_bank_1–4.kicad_sch and scoreboard.kicad_sch. Keep Arcade.kicad_sym, Arcade.pretty, fp-lib-table and sym-lib-table with the project.

## Purchasing and assembly

- [DigiKey cart](Review/DigiKey-cart.html) and [upload CSV](Review/DigiKey-board-cart.csv).
- [Detailed BOM](Review/BOM.html), [part details](Review/DigiKey-board-details.csv), and [optional harness parts](Review/DigiKey-optional-harness.csv).
- [Design review](Review/DESIGN_REVIEW.md), [display wiring](Review/DISPLAY_WIRING.md), and [I/O notes](Review/IO_REVISION.md).
- Project Information retains the original project brief, BOM workbook, manufacturer datasheets, display reference photos and meeting documents.

## PCB status

Read [routing notes](Review/ROUTING.md) and the retained final reports before fabrication. These record the previous checks and unresolved design items; the cleanup did not rerun electrical validation or certify hardware. In particular, the routing notes document a deferred display supply source and existing footprint/parity warnings.

Current artwork: [3D preview](Review/PCB-routed-3D.png), [front copper](Review/PCB-routed-top.svg), [ground plane](Review/PCB-routed-ground.svg).

## Cleanup

On November 13, 2026, historical backups, browser caches, intermediate revision outputs, unused prototype sheets, obsolete scripts, local editor preferences and stale manufacturing outputs were moved to the Windows Recycle Bin. Editable design and library files were verified unchanged, and all six active schematic sheets remain available. Parent-repository Git history was retained. Generate fresh Gerbers/drill files from the current PCB before ordering boards.

The BOM generator and its helper, netlist and mating-part inputs remain in Review so the purchasing artifacts can be regenerated. Historical baseline-dependent audit/placement generators were removed together with their backups.
