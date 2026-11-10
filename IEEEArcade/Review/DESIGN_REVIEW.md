# IEEE Arcade — schematic review

Current I/O revision: [IO_REVISION.md](IO_REVISION.md), 2026-11-10. It supersedes the original I/O allocation, 32-lamp budget, and historical ERC counts below. The board and manufacturing files require synchronization with the revised schematic.

The saved design is a schematic for the 6-column by 5-row reaction arcade game described in Project Information. A Pico 2 W reads 30 playfield switches plus START/BACK, controls their individual 12 V lamps, drives a photo-matched HUB75 ABC scoreboard interface and stores high scores in EEPROM. Firmware implements timing/scoring/idle high score. Audio and battery operation are deferred as requested. No PCB placement, routing, outline changes or manufacturing files were made.

## Open the authoritative project

Open IEEEArcade.kicad_pro, then its root IEEEArcade.kicad_sch. The main A2 sheet contains the Pico 2 W, EEPROM, four I/O expanders, input protection and TPS54202H buck. Shared I2C/reset and the local power circuitry use direct wires. Four separate button-circuit sheets contain eight channels each. Two panel-button sheets document off-board parts and functional wire assignments. One scoreboard sheet contains level translation, termination and the photo-matched external connector. Total: eight sheets.

Original draft buck_converter.kicad_sch, buck_converter_max.kicad_sch and eeprom.kicad_sch are retained as user source material and are NOT linked into the active hierarchy. Do not add them as extra sheets or fit both converter designs. Superseded generated power/input/lamp sheets are archived under Review. There is only one active converter. The user selected the BOM TPS54202 design on November 5, rather than the older LMR36510 draft.

## Decisions and verified electrical details

* A1 is Raspberry Pi Pico 2 W, SC1633, rather than the first-generation Pico W selected in yesterday's draft. The installed KiCad wireless Pico symbol and Module:RaspberryPi_Pico_W_SMD_HandSolder footprint explicitly support Pico 2 W. Standard 40-pin edge pinout and 51 x 21 mm module dimensions match. Solder the castellated edge pads; the assigned footprint includes the antenna keepout. USB is on the module; no extra USB connector is needed.
* All logic/I2C operates at 3.3 V. GPIO14/15 use I2C1 (100 kHz); R1/R2 are the single 4.7k bus pull-ups. GPIO13 resets the expanders with a 10k pull-up. No external 5 V signals are applied to Pico GPIO.
* Four MCP23017T-E/SO devices provide 32 inputs and 30 outputs using mixed directions at addresses U1=0x20, U4=0x23, U5=0x21 and U6=0x22. GPA7/GPB7 are outputs or unused. Exact pin map and firmware direction masks: [IO_REVISION.md](IO_REVISION.md).
* U3 24LC256-I/SN uses address 0x50, A0/A1/A2 grounded and WP low. Save at round end or when a high score changes; do not write on every scan. Each IC has a local 100nF bypass capacitor; the 3.3 V rail also has 10uF bulk bypass. Estimated external 3.3 V consumption is well below the module's recommended 300 mA external-load ceiling.
* SW1..SW30 are playfield positions in row-major order, six columns per row; SW31 START/SELECT, SW32 BACK/RESET GAME. All are external. Their symbol pin names NO/COM/L+/L− are FUNCTIONAL wire names, not invented physical terminal numbers.
* J11..J42 are genuine JST XH 4-way PCB headers: pin1 +12V lamp, pin2 lamp cathode (MOSFET drain), pin3 normally-open switch, pin4 switch COM/GND. The cable-side housing is XHP-4 with four SXH-001T-P0.6 contacts. XH pitch is 2.50 mm, not 2.54 mm. J41/J42 are input-only menu headers: pins1/2 unused, pin3 NO, pin4 COM/GND. Each of the 30 playfield lamps has AO3400A gate1/source2/drain3, 1k gate resistor and 100k gate pull-down. RDS(on) is specified at 2.5 V gate drive; a 3.3 V GPIO can drive this part for the allocated 100 mA lamps. It is not selected solely from threshold voltage.
* Each switch has a 4.7k external pull-up, 1k series resistor and 10nF to ground. Approximate RC rise/fall time constants are 57us/10us. These suppress edges/noise; firmware must still debounce (1–2 ms polling, require about 10 ms stable state). Never apply 12 V to a switch-input terminal.
* At initialization, hold expander RESET low at least 10us, release, write lamp OLAT=0, THEN set IODIR to outputs. Gate pull-downs hold lamps off during reset. Use ordinary on/off updates, not high-frequency PWM over I2C.
* U7/U8 SN74AHCT245N translate 3.3 V Pico outputs to 5 V HUB75 signals. They now use the separate external +5V_DISPLAY supply. Twelve signal paths retain 33-ohm damping resistors; pin12 is grounded. GP9 controls the buffer enables through Q34; R510 is now a 10k disable pull-up and new R514 keeps panel OE inactive during reset. See [DISPLAY_WIRING.md](DISPLAY_WIRING.md).

### Power path and budget

Certified external 12 V DC only. J1 PJ-063AH is rated 8 A / 24 V DC, two unswitched contacts; pin1 is center positive and pin2 return. F1 0154005.DR includes a 5 A fuse and holder. Q33 DMP4015SSS is reverse-polarity protection: drain pins5..8 toward fused input, source pins1..3 toward protected +12V, gate4 through 100k to ground. Its body diode starts the rail, then negative VGS turns it on. At 4.1 A and the nominal 11mohm on-resistance, loss is about 0.19 W; final copper/thermal behavior still needs layout review.

U2 TPS54202HDDCR is a 2 A regulator. Pin1 GND, 2 SW, 3 VIN, 4 FB, 5 EN, 6 BOOT. L1 15uH is rated 3.5 A, with typical 4.1 A saturation current. C19 is 100nF BOOT-to-SW; R9 511k enables it from +12V. Feedback R10=100k, R11=13.7k gives 0.596*(1+100/13.7)=4.946 V nominal. The 13.7k lower resistor replaces the TI example's 13.3k to leave more margin below 5.25 V. Reference and 1% resistor extremes give approximately 4.74–5.16 V before transient/ripple effects; the AHCT buffers and Pico VSYS operating range accommodate this. Check the actual display voltage limits.

C20..C23 are four 10uF/25V X7R, approximately 34uF typical at 5 V after DC bias, before capacitance tolerance/temperature/aging. The manufacturer bias curve was checked, rather than treating all 40uF as effective. Two 10uF/25V plus 100nF bypass VIN; C10 470uF/25V provides cable/input bulk capacitance. Layout must follow TI's switching-loop/FB-return guidance and be validated with load steps. A clean ERC does not test regulator stability, layout or temperature.

D1 SS14 has anode pin2 on +5V, cathode pin1 on Pico VSYS. This permits USB programming without back-powering the external buck. Pico VBUS is unused externally. USB can power the controller/3.3 V logic but cannot power the lamps or the separate 5 V scoreboard rail.

| Rail / load | Design allocation, not a measurement |
|---|---:|
| 30 lamps | 30 x 100mA = 3.0 A at 12 V |
| Pico including wireless activity | 0.5 A reserved at 5 V |
| Other logic allowance | 0.1 A reserved at 5 V |
| Display | Separate external supply; rating/current to be confirmed. No panel load on controller buck. |
| Controller 5 V load | <=0.6 A reserved (2 A regulator); display supply separate |
| 12 V adapter current at 85% buck efficiency | 3.0 + 3/(12*0.85) = 3.29 A (~40 W), excluding separate display supply |

The stated BOM adapter is 12 V / 60 W (nominal 5 A). Lamp current and actual adapter ratings still require confirmation. The display is now powered by a separate external regulated supply, with a direct panel harness and common GND; the prior 1.2 A controller-buck display allowance is retired. Its supply capacity must be selected from the actual panel rating and measured load.

### Photo-matched scoreboard interface

The user-supplied rear photos show a HUB75 RGB header with A/B/C addressing, **pin12 GND**, STB/LAT and active-low OE, plus a separate VCC/GND power header. The signal wiring is now matched to this evidence. Voltage/current, exact power mate, input pin-1 orientation and pixel/scan mapping still need confirmation. Full pin table, power harness and firmware sequence: [DISPLAY_WIRING.md](DISPLAY_WIRING.md).

No additional I2C expander or separate display-driver IC is needed. Retained AHCT buffers and the Pico PIO provide twelve signals; GP9 enables buffers after setup. J4 is now an external +5V_DISPLAY INPUT for the buffers only, isolated from the board +5V buck. Power the panel directly from the same external display supply and share GND.

## Footprints, source limitations and outstanding review

| Item | Checked / remaining |
|---|---|
| 1206 YAGEO resistors | 1%, nominal quarter-watt standard parts; body about3.1x1.6mm; hand-solder 3216 footprint |
| 1206 KEMET caps | Package/dielectric/voltage and individual manufacturer spec sheets; exact 3216 hand-solder footprint |
| MCP23017 | SOIC28 wide, 7.5x17.9mm body, 1.27mm pitch; actual pin maps checked |
| EEPROM / reverse MOSFET | SOIC8 3.9x4.9mm, 1.27mm pitch; DMP S=1..3,G=4,D=5..8 explicitly represented |
| TPS54202H | DDC TSOT23-6; exact six-pin mapping; hand-solder SOT23-6 assignment |
| AO3400A / SS14 | SOT23 G1/S2/D3 / SMA cathode1 anode2 checked |
| F1 | Native Littelfuse154 footprint: pads4.24x3.81mm centered +/-3.185mm, matches drawing outer10.62/inner2.13mm |
| C10 | Panasonic EEU-FR1E471, body10mm diameter x12.5mm nominal, 5mm leads; 25V, ripple1.29A@100kHz; allow manufacturer height tolerance in enclosure |
| L1 custom | 7447714150: body10x10x5mm max, lands2x3.5mm at +/-4.5mm; manufacturer drawing dimensions used. No approximate generic10mm inductor footprint substituted |
| J3 custom | 3M N2516-6002-RB: 27.64x8.59mm body, 9.91mm height, 2.54mm grid,1.02mm holes. Check polarization orientation when laying out cable path |
| J1 | Exact-MPN native PJ-063AH footprint selected; electrical/contact specification confirmed, but manufacturer mechanical PDF requests were blocked. Independent dimensional/pin-position drawing comparison remains OPEN before layout |
| Adafruit1194 | Manufacturer confirms 5–12V resistor-equipped LED and NO switch. 3835 fits switch tabs; 3838 fits lamp tabs. Manufacturer product pages are provided because no usable manufacturer PDF was available. Actual lamp current not documented/confirmed |
| Menu buttons | BOM Amazon EG STARTS12V item retained. Exact MPN, manufacturer datasheet, LED current/internal resistor and terminal widths remain UNVERIFIED. No DigiKey part number or claimed-compatible spade terminal invented |
| Display and adapter | Existing/source BOM items retained. Photos identify the HUB75 ABC protocol and signal pinout. Panel voltage/current, physical mating orientation, power connector, scan mapping and adapter model/plug/polarity require hardware checks. Do not assume a center-positive5.5x2.1mm adapter fits until checked |

J1 is explicitly marked with its open dimensional check in its component Verification field. Panel-mounted buttons and cable-side parts intentionally have no PCB footprint; their BOM says N/A, not an approximate footprint. All board-mounted parts have assigned footprints. Direct manufacturer datasheet links are included for the electrical components; manufacturer product pages replace unavailable PDFs for Adafruit consumer assemblies. The menu-button seller page is clearly identified as a seller source, not a manufacturer datasheet.

See BOM.html for minimum cable-side quantities. Thirty switches and lamps need three 10-pair packs each of 3835 and3838; their factory2-pin ends do NOT plug directly into the4-way board connector. Cut/reterminate using new genuine XH contacts/housings. Cabinet dimensions determine extensions/strain relief. Menu-button connector selection cannot be confirmed until its tabs are identified. The display power mate remains unidentified; J3 signal mapping follows the photos, with physical pin-1 orientation still to be checked.

## Validation and ERC interpretation

The display revision was checked against the current saved project before editing: both runs have 317 ERC findings (1 existing A1 VSYS power-pin error, 4 junction warnings and 312 library-symbol mismatch warnings). No additional findings were introduced. The earlier zero-message ERC-final files are historical. Current report: ERC-display.rpt. Netlist assertions and unchanged non-display connectivity: display-connectivity-verification.txt. The native BOM and PDF have been regenerated for the display revision; the earlier 324-reference claim no longer describes this revision.

No ERC exclusions were added. Footprint-filter, single-global-label and four-way-junction checks that were ignored in the original project are enabled as warnings. Original SPICE-model checks remain ignored because this is not a simulation project. Three power flags are justified after passive power paths: protected external12V, buck5V after L1, and VSYS after D1. Unused device pins and module ADC/AGND pins are intentionally no-connect; module AGND is internally grounded and unused externally because no ADC is used. The AHCT local symbol models A pins as inputs because DIR is permanently tied A-to-B; B pins remain tri-state outputs. This is a fixed-direction use model, not a disabled ERC check.

PCB SHA256 remains 11AEA2C4FE51607D5259807815A89546BF4C9B34B4513FD16C769A6FC3B8C48B. No Gerbers/drill/manufacturing archive was generated. Component datasheet validity, connectivity and ERC do not certify hardware operation; actual load/current, enclosure wiring, regulator thermal/stability and display compatibility checks remain necessary before fabrication.

Original-project-20261104.zip and Before-consolidation-20261105.zip in the chat output folder preserve the pre-edit project states. The completed package contains the active hierarchy, project files, local libraries and review outputs, without duplicate legacy schematic drafts. No purchasing or Git commit/push was performed.
