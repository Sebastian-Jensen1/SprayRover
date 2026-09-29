#pragma once

// Entry points for the portable application, callable from the CubeMX-generated C code.

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Called once after the HAL and peripherals are initialised.
void app_init(void);

// Called from the main loop. now_us is a monotonic microsecond timestamp.
void app_step(uint64_t now_us);

// Number of app_step() calls since app_init(). Mainly useful for tests and diagnostics.
uint32_t app_step_count(void);

#ifdef __cplusplus
}
#endif
