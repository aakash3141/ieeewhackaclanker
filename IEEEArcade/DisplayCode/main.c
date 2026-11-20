#include "display.h"
#include "pico/stdlib.h"

static void draw_ieee(void) {
    static const uint8_t letters[4][7] = {
        {31, 4, 4, 4, 4, 4, 31},       // I
        {31, 16, 16, 30, 16, 16, 31},  // E
        {31, 16, 16, 30, 16, 16, 31},  // E
        {31, 16, 16, 30, 16, 16, 31}   // E
    };
    static const uint8_t colors[4] = {RED, WHITE, BLUE, GREEN};
    const int left = (DISPLAY_WIDTH - 23) / 2;
    const int top = (DISPLAY_HEIGHT - 14) / 2;
    display_fill(BLACK);
    for (int letter = 0; letter < 4; ++letter)
        for (int y = 0; y < 7; ++y)
            for (int x = 0; x < 5; ++x)
                if (letters[letter][y] & (1u << (4 - x))) {
                    display_pixel(left + letter * 6 + x, top + y * 2, colors[letter]);
                    display_pixel(left + letter * 6 + x, top + y * 2 + 1, colors[letter]);
                }
}

int main(void) {
    display_init();
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    stdio_init_all();
    draw_ieee();
    while (true) {
        gpio_put(PICO_DEFAULT_LED_PIN, (to_ms_since_boot(get_absolute_time()) / 500) & 1u);
        display_refresh();
    }
}
