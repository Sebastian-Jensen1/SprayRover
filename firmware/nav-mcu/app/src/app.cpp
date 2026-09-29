#include "sprayrover/app.h"

namespace {

uint32_t step_count = 0;

}  // namespace

extern "C" void app_init(void) { step_count = 0; }

extern "C" void app_step(uint64_t now_us) {
    (void)now_us;
    // Scheduling of the ESKF, vehicle controller and safety supervisor goes here.
    ++step_count;
}

extern "C" uint32_t app_step_count(void) { return step_count; }
