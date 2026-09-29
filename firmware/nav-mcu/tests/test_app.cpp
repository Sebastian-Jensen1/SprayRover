#include <cstdio>

#include "sprayrover/app.h"

#define CHECK(cond)                                                                       \
    do {                                                                                  \
        if (!(cond)) {                                                                    \
            std::fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #cond); \
            return 1;                                                                     \
        }                                                                                 \
    } while (0)

int main() {
    app_init();
    CHECK(app_step_count() == 0);

    app_step(1000);
    app_step(2000);
    CHECK(app_step_count() == 2);

    app_init();
    CHECK(app_step_count() == 0);
    return 0;
}
