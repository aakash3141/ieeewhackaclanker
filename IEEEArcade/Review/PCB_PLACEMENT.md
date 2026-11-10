# IEEE Arcade PCB — current routed revision

The current board is **200 x 125 mm, four layers, fully routed**. Button connectors are split into 16 top-edge and 16 bottom-edge positions. The Pico USB faces right, the power jack faces left, and HUB75 sits at the bottom left. Component placement, the seven mounting holes and Pico keepouts were retained during routing.

See [ROUTING.md](ROUTING.md) for copper/width details, outstanding issues and complete validation. There are 9 copper pours, 668 vias and 1,801 native teardrops. Physical DRC has **zero errors and zero unrouted connections**; one Pico footprint warning and 199 pre-existing native schematic-parity warnings remain. Independent checks verify all 867 schematic pad assignments.

**The display-buffer supply source remains deferred by the user.** This must be resolved before the scoreboard can operate. Old Gerbers were not regenerated.

[Current 3D preview](PCB-routed-3D.png) · [Front-layer artwork](PCB-routed-top.svg) · [Routing/validation report](ROUTING.md)

The original compact placement and routing-start snapshots are retained in `.layout-backup/`. Enclosure, actual plug/latch access, mounting fit, electrical loads and fabrication-release checks still apply.
