# Display connections and schematic revision

The added photos identify a HUB75 RGB panel interface. The decisive detail in `Project Information/DisplayConnections1.png` is **C / GND** on the sixth connector row: signal-header pin 12 is ground, not a fourth row address D. The previous schematic would have driven that ground contact. This revision corrects it.

The photos establish the signal names and a separate VCC/GND power connector. They do **not** establish a numeric supply voltage, maximum current, exact power-connector series, reliable model number, physical pin-1 orientation, or firmware pixel/scan mapping. The design uses an external regulated **5 V** rail because that is the usual HUB75 arrangement and the AHCT buffers require 4.5–5.5 V; confirm the actual panel rating before energizing it. Do not apply the arcade's 12 V lamp supply to the panel.

## Ribbon connection

J3 connects through a straight-through 16-conductor IDC ribbon to the panel's **INPUT** header. Use the data-flow arrow and input marking on the actual panel; the second header is a cascaded output and stays unused for a single panel. Confirm pin 1 and the mating views on both ends; the photograph of the connector cannot establish the cable's orientation by itself. Start with a short cable, approximately 30 cm or less, and check edges/timing on the assembled hardware.

| J3 pin | Photo marking / function | Pico GPIO before 5 V buffering |
|---|---|---|
| 1 | DR1 / R1 | GP0 |
| 2 | DG1 / G1 | GP1 |
| 3 | DB1 / B1 | GP2 |
| 4 | GND | Ground |
| 5 | DR2 / R2 | GP3 |
| 6 | DG2 / G2 | GP4 |
| 7 | DB2 / B2 | GP5 |
| 8 | GND | Ground |
| 9 | A | GP6 |
| 10 | B | GP7 |
| 11 | C | GP8 |
| 12 | **GND** | **Ground; never drive as D** |
| 13 | CLK | GP10 |
| 14 | STB / LAT | GP11 |
| 15 | OE, active low | GP12 |
| 16 | GND | Ground |

GP9 is now `DISP_ENABLE`, not address D. It enables U7/U8 through Q34. LOW or a floating/reset GPIO disables both buffers; R514 pulls panel OE HIGH to keep the panel blank. R610 is the 100k gate pull-down; R510 is repurposed from a 33-ohm series resistor to a 10k buffer-disable pull-up. Q34 is another AO3400A, the same MOSFET type already used for the lamps. R514 is an additional 10k resistor. The other twelve signal paths retain their 33-ohm damping resistors.

## Power wiring

Use an external regulated display supply, separate from the controller buck output. Its capacity must cover the actual panel's worst-case load plus the AHCT circuitry; the photos do not justify a specific current rating. The old 1.2 A allocation was not a panel specification and is no longer used to power this panel.

| External supply connection | Destination |
|---|---|
| Positive, nominal +5 V after rating confirmation | Panel power connector contacts labeled VCC, through its own suitable high-current harness |
| Supply return | Panel power connector contacts labeled GND, through the same direct harness |
| Low-current branch from supply positive | J4 pin 1: `+5V_DISPLAY`, supplying the two AHCT buffers and their pull-ups/bypass capacitors |
| Common return branch | J4 pin 2: controller/signal GND |

J4 is a two-pin JST XH **input on the controller PCB**. It is **not** the four-contact power connector shown on the panel, and it does **not** carry the panel's LED current. Obtain the panel's supplied power lead or identify its actual mating series/pitch. Check continuity to distinguish duplicate VCC/GND contacts before terminating an adapter; no unverified panel power-pin numbers have been assigned. Select cable gauge, connector ratings and branch protection for the measured load and supply capacity. Route panel load return directly to the supply rather than through J3 or the controller ground branch.

`+5V_DISPLAY` is electrically separate from the controller's `+5V` buck rail; their grounds are common. Do not bridge the positive rails. The AHCT buffers and panel share the display supply so buffer outputs cannot drive an unpowered panel when that supply is absent. With display power present and Pico power absent, Q34 stays off and R514 holds panel OE inactive. Recheck power sequencing on hardware, including USB-only controller power.

## Firmware

No additional I/O expander or separate display-driver IC is needed. U7/U8 translate the Pico's 3.3 V signals to 5 V; the panel already has onboard LED shift/current-driver circuitry. An I2C GPIO expander would be a poor fit for continuous pixel-clock and row-refresh timing. Use the Pico's PIO, optionally fed with DMA, for regular refresh while the main code handles the game.

1. Keep GP9 LOW during setup.
2. Set GP12/OE HIGH (blank), GP10/CLK and GP11/LAT LOW; initialize RGB and A/B/C outputs.
3. Initialize PIO refresh using RGB GP0–5, row select GP6–8, CLK GP10, LAT GP11 and OE GP12. Three row-address bits provide eight address codes; the panel's spatial pixel mapping and effective scan arrangement still need a test pattern or datasheet. Do not assume a 64x64 HUB75E example's width, height, D/E pins or row-data packing applies unchanged.
4. Set GP9 HIGH when signals are initialized, then refresh continuously. Blank OE while shifting/latching and changing row addresses. Start at low brightness and verify current/voltage, scan mapping and refresh timing.
5. Set GP9 LOW before stopping the refresh engine or shutting the controller down.

## Validation and remaining work

Native KiCad netlist assertions verify all sixteen header pins, the twelve signal paths, external supply isolation, buffer-enable polarity and pull-ups. Only sixteen expected existing component-pin net assignments changed; all other nets, including all buttons, expanders, EEPROM, buck and reverse-protection Q33, retain their previous pin assignments. Existing component identities and footprints were retained. Added components are Q34 and R514; R510's value changes to 10k.

The native ERC run has **no added findings** relative to the project as it stood immediately before this display revision: 1 existing VSYS power-pin error, 4 existing four-way-junction warnings, and 312 existing library-symbol mismatch warnings. This is not a clean ERC result; the old zero-message `ERC-final` report describes an earlier revision. See `ERC-display.rpt` and `display-connectivity-verification.txt` for current results. The PCB has not been updated to match these schematic changes.

Photos do not replace a panel datasheet or bench validation. Remaining hardware checks are rated voltage/current, input header orientation, exact power connector, pixel dimensions/scan mapping, any driver initialization sequence and signal integrity. The schematic is ready for those checks, not a claim that the unidentified panel has been operated successfully.

## Sources

- User-supplied `BackofDisplay.png`, `DisplayConnections1.png`, `DisplayConnections2.png` and `FrontofDisplay.png` in Project Information: physical evidence for this panel.
- [Adafruit RGB LED Matrix Basics](https://cdn-learn.adafruit.com/downloads/pdf/32x16-32x32-rgb-led-matrix.pdf): HUB75 signals, STB/LAT and the three-address-line variant with pin 12 grounded; general reference, not this panel's datasheet.
- [Adafruit matrix power guide](https://learn.adafruit.com/32x16-32x32-rgb-led-matrix/powering): separate panel supply and load-dependent current.
- [Raspberry Pi official HUB75 PIO example](https://github.com/raspberrypi/pico-examples/tree/master/pio/hub75): PIO refresh architecture; example targets a different panel and requires adaptation.
- [TI SN74AHCT245 datasheet](https://www.ti.com/lit/ds/symlink/sn74ahct245.pdf): TTL-compatible inputs, 4.5–5.5 V supply and active-low output enable.
- [Alpha & Omega AO3400A datasheet](https://www.aosmd.com/res/data_sheets/AO3400A.pdf): MOSFET pinout and operation at 2.5 V gate drive.
