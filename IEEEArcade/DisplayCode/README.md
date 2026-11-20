# IEEE Arcade display bring-up

C/C++ SDK project for an **original Raspberry Pi Pico (RP2040)** and a
**32 x 16 RGB panel**, using exactly the GPIO assignments supplied. Assumes
standard 1/8 scan: DR1/DG1/DB1 drive rows 0–7, DR2/DG2/DB2 drive rows 8–15,
ABC selects the row, rising CLK shifts data, STB latches, and OE is active low.
The photo labels match this interface; the actual panel scan mapping still needs
to be confirmed on hardware.

## Wiring

Connect to the panel's **input** connector; follow its printed labels and arrows.
Do not infer connector orientation from ribbon cable colors. Reference photo:
`../Scoreboard Display/DisplayConnections1.png`.

| Panel signal | Pico GPIO | Pico physical pin |
| --- | --- | --- |
| DR1 | GP28 | 34 |
| DG1 | GP27 | 32 |
| DB1 | GP26 | 31 |
| DR2 | GP22 | 29 |
| DG2 | GP21 | 27 |
| DB2 | GP20 | 26 |
| A | GP19 | 25 |
| B | GP18 | 24 |
| C | GP17 | 22 |
| D | GP13 | 17 |
| CLK | GP16 | 21 |
| STB / LAT | GP14 | 19 |
| OE | GP15 | 20 |
| GND | GND | e.g. 18 or 23 |

Power the panel from its separate power connector using the voltage and current
specified by its manufacturer (commonly 5 V for this type of panel). Do not power
the panel from Pico 3V3 or draw its LED current through the Pico. Join the panel
supply ground and Pico ground. Power off before rewiring.

Pico GPIO is 3.3 V and is not 5 V tolerant. If the panel requires 5 V logic,
use a unidirectional 3.3 V-to-5 V buffer with 3.3 V-compatible inputs, such as
74AHCT245, on all 13 signals. Verify the panel input specification; direct 3.3 V
drive is not guaranteed to work. A pull-up on OE to the appropriate logic supply
keeps the panel blank while the controller resets (use 3.3 V on the Pico side,
never pull a Pico GPIO up to 5 V).

## Build in VS Code

1. Open **this Display Code folder** using File → Open Folder.
2. Install/enable the **Raspberry Pi Pico** extension if prompted. The project
   targets `pico`, not Pico W or Pico 2.
3. Press **Ctrl+Shift+B** and select **Compile Project** if asked.
4. The firmware is `build/arcade_display.uf2`.

The included tasks use the tools already installed on this computer under
`%USERPROFILE%/.pico-sdk`: SDK 2.3.1, toolchain 15_2_Rel1, CMake v4.3.4,
Ninja v1.13.2, Python 3.13.7, and picotool 2.3.1. For another installation,
adjust the versions in CMakeLists.txt and .vscode/tasks.json. The standard
`pico_sdk_import.cmake` is included from the installed Raspberry Pi SDK.

## Load onto the Pico

1. Hold **BOOTSEL** while connecting the Pico to USB.
2. Release BOOTSEL when the **RPI-RP2** drive appears.
3. Copy `build/arcade_display.uf2` onto that drive. The Pico restarts automatically.

This overwrites the firmware currently on the Pico. No debug probe is needed.

## Expected display

On power-up, a steady IEEE message appears on black. Letters are red, white,
blue, green from left to right, centered in the 32x16 framebuffer and 14 pixels
tall. There is no startup scan comparison or animation. The Pico LED blinks.

This restores the original eight-address, 32-clock framebuffer mode. D remains
configured on GP13 and is held low in this mode. The diagnostic APIs remain in
display.c for later use. No scan profile was confirmed by the previous tests;
the panel's physical mapping and intermittent wiring/logic issue remain unresolved.
Changing the displayed message does not fix those electrical issues.

Only connect GP13 to an actual D input, never a GND position on the connector.

## Editing and diagnosis

- `display.h`: GPIO assignments and dimensions.
- `display.c`: framebuffer, eight-color RGB driver, digit rendering.
- `main.c`: steady IEEE lettering. The normal framebuffer driver remains available. Call
  `display_score(your_score)` to draw a score, and keep calling
  `display_refresh()` continuously to scan it. There is no background refresh;
  long sleeps, blocking input, or breakpoints will blank the panel.
- Blank panel: check separate panel power, shared ground, input connector,
  OE/STB wiring, and logic levels. The Pico LED only proves firmware is running.
- Wrong colors or halves: check the six RGB data connections against the table.
- Repeated/misordered rows: check A/B/C/D. If wiring is correct, the panel may use
  a different scan mapping; that requires its model/datasheet to adapt the driver.
- Mirrored image: column order may be reversed on the panel; reverse the x lookup
  in `display_refresh()` after confirming connector direction.

The driver uses conservative software clock pulses and about 250 microseconds of
illumination per row, blanks during shifting/latching, and leaves OE disabled
after each refresh. It provides eight colors without grayscale/PWM. Compilation
can verify the software, but display behavior and electrical compatibility must
be checked with the connected hardware.

Official setup references:
[Raspberry Pi C/C++ SDK documentation](https://www.raspberrypi.com/documentation/microcontrollers/c_sdk.html)
and [Raspberry Pi Pico VS Code extension](https://github.com/raspberrypi/pico-vscode).





