# I/O schematic revision — 2026-11-10

The active schematic has 32 switch inputs and 30 lamp outputs. SW01–SW30 form six columns by five rows, numbered left-to-right, top-to-bottom. SW31 is START/SELECT and SW32 is BACK, both thumb-sized, input-only menu buttons. The two menu lamp drivers, gate resistors and gate pull-downs were removed. J41/J42 retain the existing keyed four-way XH footprint: use pin3 NO and pin4 COM/GND; leave cavities/pins1–2 unused. No lamp power is available at these two headers. Actual thumb-button model and terminal hardware remain to be selected.

All active global switch labels are SW_01 through SW_32; lamp labels are LAMP_01 through LAMP_30. The filter components remain fitted. The two unlinked expander template sheets in `i/` also now use MCP23017 symbols. Historical sheets in `Archived-generated-sheets/` remain historical and are not in the active hierarchy.

## Allocation and firmware

Four MCP23017T-E/SO devices fit all 62 used channels. Mixed input/output use avoids an additional expander. The T suffix selects tape/reel packaging; the device is MCP23017.

| Reference | 7-bit address | A2:A0 | Inputs | Outputs | IODIRA | IODIRB |
|---|---|---|---|---|---|---|
| U1 | 0x20 | 000 | SW01–14 | LAMP01–02 | 0x7F | 0x7F |
| U4 | 0x23 | 011 | SW15–28 | LAMP17–18 | 0x7F | 0x7F |
| U5 | 0x21 | 001 | SW29–30 | LAMP03–16 | 0x03 | 0x00 |
| U6 | 0x22 | 010 | SW31–32 | LAMP19–30 | 0x03 | 0x00 |

IODIR bits are 1=input, 0=output. GPA7 and GPB7 are never switch inputs. U6 GPB6/GPB7 are unconnected spares, configured as outputs held low by the masks above. Pin-by-pin assignments follow below and are also in `io-pin-map.json`.

Use 100 kHz I2C at 3.3V. Hold reset low for at least 10 microseconds, release, write OLATA/OLATB=0 to every expander, then apply the IODIR masks. Retain external switch pull-ups; read only the input bits and debounce in firmware. Firmware must adopt the new pin mapping and U4 address (previously 0x27). Existing gate pull-downs keep lamps off during reset.

## Device and footprint check

MCP23017 SOIC: pin9 VDD=3.3V, pin10 VSS=GND, pin12 clock, pin13 SDA, pin18 RESET. A0/A1/A2 pins15–17 are strapped as above. Pins11/14 are NC; pins19/20 are unused interrupts. C4/C5/C6/C7 provide individual 100nF bypassing. The cached symbol models GPA7/GPB7 as outputs. All four use `Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm`, with 28 pads and the correct SOIC pin order. U1/U4 were rewired for MCP23017; MCP23018 power, address and reset pin numbers are different.

U3 is 24LC256-I/SN: pin8=3.3V, pin4=GND, pins1/2/3=GND (7-bit address 0x50), pin5=SDA, pin6=SCL, pin7 WP=GND (writes enabled). C3 is 100nF. R1/R2 are the existing single 4.7k I2C pull-ups to 3.3V; R3 is the 10k reset pull-up. The unchanged EEPROM wiring is correct. Its eight-pin symbol matches the `/SN` narrow SOIC package and `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` footprint; pad numbers and 1.27mm pitch were checked.

Sources: [Microchip MCP23017 DS20001952D](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf), pin diagram/table, GPA7/GPB7 restriction and SO package identification; [Microchip 24LC256 DS20001203Y](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/24AA256-24LC256-24FC256-256K-I2C-Serial-EEPROM-DS20001203.pdf), pin diagram and SN package drawing. The local Project Information PDFs use encrypted streams that the available local reader could not decode, so the matching Microchip document IDs were read through their official web copies.

## Validation and deliverables

`verify_io.py` passes 591 assertions against KiCad's exported netlist and installed footprint libraries. These include all switch filter/harness paths, all lamp drivers, every device supply/bus/address pin, unused pins, symbol pin functions, footprint pad numbering and unchanged connectivity for every retained non-expander pin. Results: `io-connectivity-verification.txt`. Before/after netlists are `before-io.net` / `after-io.net`.

ERC baseline: 319 findings = 3 power-drive errors, 4 four-way-junction warnings and 312 cached-symbol mismatch warnings. Revised: 307 = the same 3 power-drive errors, the same 4 junction warnings and 300 cached-symbol mismatch warnings. There are no new ERC findings or added exclusions. The three existing errors identify A1 VSYS, #PWR0004 and #PWR0014. This revision is not a clean ERC sign-off for the whole board. Reports: `ERC-before-io.json` and `ERC-io.json`.

Updated PDF: `IEEEArcade-schematic.pdf`. Refreshed BOM: `BOM-schematic.csv` and `BOM.html`. The board file and Gerbers were not changed; they still reflect the prior schematic and must be synchronized/reviewed before fabrication. Existing project settings and unrelated working changes were preserved. This is a schematic/static package check, not hardware validation.

## Pin map

| Device | Pin | Port | Net |
|---|---|---|---|
| U1 | 1 | GPB0 | SW_08 |
| U1 | 2 | GPB1 | SW_09 |
| U1 | 3 | GPB2 | SW_10 |
| U1 | 4 | GPB3 | SW_11 |
| U1 | 5 | GPB4 | SW_12 |
| U1 | 6 | GPB5 | SW_13 |
| U1 | 7 | GPB6 | SW_14 |
| U1 | 8 | GPB7 | LAMP_02 |
| U1 | 21 | GPA0 | SW_01 |
| U1 | 22 | GPA1 | SW_02 |
| U1 | 23 | GPA2 | SW_03 |
| U1 | 24 | GPA3 | SW_04 |
| U1 | 25 | GPA4 | SW_05 |
| U1 | 26 | GPA5 | SW_06 |
| U1 | 27 | GPA6 | SW_07 |
| U1 | 28 | GPA7 | LAMP_01 |
| U4 | 1 | GPB0 | SW_22 |
| U4 | 2 | GPB1 | SW_23 |
| U4 | 3 | GPB2 | SW_24 |
| U4 | 4 | GPB3 | SW_25 |
| U4 | 5 | GPB4 | SW_26 |
| U4 | 6 | GPB5 | SW_27 |
| U4 | 7 | GPB6 | SW_28 |
| U4 | 8 | GPB7 | LAMP_18 |
| U4 | 21 | GPA0 | SW_15 |
| U4 | 22 | GPA1 | SW_16 |
| U4 | 23 | GPA2 | SW_17 |
| U4 | 24 | GPA3 | SW_18 |
| U4 | 25 | GPA4 | SW_19 |
| U4 | 26 | GPA5 | SW_20 |
| U4 | 27 | GPA6 | SW_21 |
| U4 | 28 | GPA7 | LAMP_17 |
| U5 | 1 | GPB0 | LAMP_09 |
| U5 | 2 | GPB1 | LAMP_10 |
| U5 | 3 | GPB2 | LAMP_11 |
| U5 | 4 | GPB3 | LAMP_12 |
| U5 | 5 | GPB4 | LAMP_13 |
| U5 | 6 | GPB5 | LAMP_14 |
| U5 | 7 | GPB6 | LAMP_15 |
| U5 | 8 | GPB7 | LAMP_16 |
| U5 | 21 | GPA0 | SW_29 |
| U5 | 22 | GPA1 | SW_30 |
| U5 | 23 | GPA2 | LAMP_03 |
| U5 | 24 | GPA3 | LAMP_04 |
| U5 | 25 | GPA4 | LAMP_05 |
| U5 | 26 | GPA5 | LAMP_06 |
| U5 | 27 | GPA6 | LAMP_07 |
| U5 | 28 | GPA7 | LAMP_08 |
| U6 | 1 | GPB0 | LAMP_25 |
| U6 | 2 | GPB1 | LAMP_26 |
| U6 | 3 | GPB2 | LAMP_27 |
| U6 | 4 | GPB3 | LAMP_28 |
| U6 | 5 | GPB4 | LAMP_29 |
| U6 | 6 | GPB5 | LAMP_30 |
| U6 | 21 | GPA0 | SW_31 |
| U6 | 22 | GPA1 | SW_32 |
| U6 | 23 | GPA2 | LAMP_19 |
| U6 | 24 | GPA3 | LAMP_20 |
| U6 | 25 | GPA4 | LAMP_21 |
| U6 | 26 | GPA5 | LAMP_22 |
| U6 | 27 | GPA6 | LAMP_23 |
| U6 | 28 | GPA7 | LAMP_24 |
