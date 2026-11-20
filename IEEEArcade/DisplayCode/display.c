#include "display.h"
#include "pico/stdlib.h"
#include <string.h>

static uint8_t pixels[DISPLAY_HEIGHT][DISPLAY_WIDTH];
static const uint32_t data_mask =
    (1u << PIN_DR1) | (1u << PIN_DG1) | (1u << PIN_DB1) |
    (1u << PIN_DR2) | (1u << PIN_DG2) | (1u << PIN_DB2);

void display_init(void) {
    // Set the output latch before enabling the pin driver: OE is active low.
    gpio_init(PIN_OE);
    gpio_put(PIN_OE, 1);
    gpio_set_dir(PIN_OE, GPIO_OUT);
    const uint pins[] = {PIN_DR1, PIN_DG1, PIN_DB1, PIN_DR2, PIN_DG2,
                         PIN_DB2, PIN_A, PIN_B, PIN_C, PIN_D, PIN_CLK, PIN_STB};
    for (unsigned i = 0; i < sizeof(pins) / sizeof(pins[0]); ++i) {
        gpio_init(pins[i]);
        gpio_put(pins[i], 0);
        gpio_set_dir(pins[i], GPIO_OUT);
    }
    display_fill(BLACK);
}

void display_fill(uint8_t color) {
    memset(pixels, color & 7u, sizeof(pixels));
}

void display_pixel(int x, int y, uint8_t color) {
    if (x >= 0 && x < DISPLAY_WIDTH && y >= 0 && y < DISPLAY_HEIGHT)
        pixels[y][x] = color & 7u;
}

// test_color: -1 = framebuffer, -2 = address-color pattern, 0..7 = solid.
// Framebuffer mode uses eight addresses for the original 32x16 assumption.
// Diagnostic modes use 16 addresses without assuming a physical row mapping.
static void refresh_columns(unsigned shift_clocks, unsigned address_count, int test_color) {
    static const uint8_t address_colors[] = {RED, WHITE, BLUE, GREEN};
    for (unsigned row = 0; row < address_count; ++row) {
        gpio_put(PIN_OE, 1);
        gpio_put(PIN_A, (row >> 0) & 1u);
        gpio_put(PIN_B, (row >> 1) & 1u);
        gpio_put(PIN_C, (row >> 2) & 1u);
        gpio_put(PIN_D, (row >> 3) & 1u);
        for (unsigned clock = 0; clock < shift_clocks; ++clock) {
            unsigned x = clock % DISPLAY_WIDTH;
            uint8_t top, bottom;
            if (test_color == -1) {
                unsigned framebuffer_row = row % (DISPLAY_HEIGHT / 2);
                top = pixels[framebuffer_row][x];
                bottom = pixels[framebuffer_row + DISPLAY_HEIGHT / 2][x];
            } else {
                top = test_color == -2 ? address_colors[row % 4] : (uint8_t)test_color & 7u;
                bottom = top;
            }
            uint32_t data =
                ((uint32_t)((top >> 0) & 1u) << PIN_DR1) |
                ((uint32_t)((top >> 1) & 1u) << PIN_DG1) |
                ((uint32_t)((top >> 2) & 1u) << PIN_DB1) |
                ((uint32_t)((bottom >> 0) & 1u) << PIN_DR2) |
                ((uint32_t)((bottom >> 1) & 1u) << PIN_DG2) |
                ((uint32_t)((bottom >> 2) & 1u) << PIN_DB2);
            gpio_put_masked(data_mask, data);
            busy_wait_us_32(1);  // Data setup, CLK starts low.
            gpio_put(PIN_CLK, 1);
            busy_wait_us_32(1);
            gpio_put(PIN_CLK, 0);
        }
        gpio_put(PIN_STB, 1);
        busy_wait_us_32(1);
        gpio_put(PIN_STB, 0);
        busy_wait_us_32(1);
        gpio_put(PIN_OE, 0);
        busy_wait_us_32(250);
        gpio_put(PIN_OE, 1);
    }
}

void display_refresh(void) {
    refresh_columns(DISPLAY_WIDTH, DISPLAY_HEIGHT / 2, -1);
}

void display_refresh_solid_test(uint8_t color) {
    // A uniform pattern avoids assuming the panel's pixel-to-shift-register
    // mapping. Fill 64 stages per RGB lane to test for a longer chain.
    refresh_columns(64, 16, color & 7u);
}

void display_refresh_address_test(void) {
    // A=bit 0, B=bit 1, C=bit 2, D=bit 3. Shift both lanes uniformly
    // so the diagnostic works independently of column/bank interleaving.
    refresh_columns(64, 16, -2);
}

void display_refresh_scan_test(unsigned shift_clocks, unsigned address_count, uint8_t color) {
    if ((shift_clocks != 32 && shift_clocks != 64 && shift_clocks != 128) ||
        (address_count != 4 && address_count != 8 && address_count != 16)) {
        gpio_put(PIN_OE, 1);
        return;
    }
    refresh_columns(shift_clocks, address_count, color & 7u);
}

void display_score(unsigned score) {
    static const uint8_t digits[10][7] = {
        {14,17,19,21,25,17,14}, {4,12,4,4,4,4,14},
        {14,17,1,2,4,8,31}, {30,1,1,14,1,1,30},
        {2,6,10,18,31,2,2}, {31,16,16,30,1,1,30},
        {14,16,16,30,17,17,14}, {31,1,2,4,8,8,8},
        {14,17,17,14,17,17,14}, {14,17,17,15,1,1,14}
    };
    static const uint8_t colors[4] = {RED, GREEN, BLUE, WHITE};
    display_fill(BLACK);
    score %= 10000;
    for (int position = 3; position >= 0; --position) {
        unsigned digit = score % 10;
        score /= 10;
        for (int y = 0; y < 7; ++y)
            for (int x = 0; x < 5; ++x)
                if (digits[digit][y] & (1u << (4 - x))) {
                    display_pixel(4 + position * 6 + x, 1 + y * 2, colors[position]);
                    display_pixel(4 + position * 6 + x, 2 + y * 2, colors[position]);
                }
    }
}
