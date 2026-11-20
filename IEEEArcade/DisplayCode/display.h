#ifndef ARCADE_DISPLAY_H
#define ARCADE_DISPLAY_H

#include <stdint.h>

#define DISPLAY_WIDTH 32
#define DISPLAY_HEIGHT 16

// GPIO numbers, NOT physical header pin numbers.
#define PIN_DR1 28
#define PIN_DG1 27
#define PIN_DB1 26
#define PIN_DR2 22
#define PIN_DG2 21
#define PIN_DB2 20
#define PIN_A   19
#define PIN_B   18
#define PIN_C   17
#define PIN_D   13
#define PIN_CLK 16
#define PIN_STB 14
#define PIN_OE  15

// Three-bit RGB: eight colors, no PWM/grayscale.
enum {
    BLACK = 0, RED = 1, GREEN = 2, YELLOW = 3,
    BLUE = 4, MAGENTA = 5, CYAN = 6, WHITE = 7
};

void display_init(void);
void display_fill(uint8_t color);
void display_pixel(int x, int y, uint8_t color);
void display_score(unsigned score);
// Refreshes all eight row addresses, then leaves OE high (blank).
// Must be called continuously; long sleeps stop the display.
void display_refresh(void);
// Diagnostic only: uniform color with 64 clocks per row address.
// Does not establish a working framebuffer mapping for a 1/4-scan panel.
void display_refresh_solid_test(uint8_t color);
// Scan all 16 DCBA addresses, with matching color on both RGB lanes.
// Diagnostic address coordinates; does not assume a physical row mapping.
void display_refresh_address_test(void);
// Raw uniform-color scan for comparing unknown panel layouts.
// Valid address counts: 4, 8, 16. Valid clock counts: 32, 64, 128.
void display_refresh_scan_test(unsigned shift_clocks, unsigned address_count, uint8_t color);

#endif
