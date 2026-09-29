# Firmware

| Folder | Target | Toolchain | Status |
|---|---|---|---|
| [`nav-mcu/`](nav-mcu/) | STM32H7 navigation & vehicle MCU: ESKF, vehicle controller, safety supervisor, spray driver | CMake + arm-none-eabi-gcc (STM32CubeMX HAL to be added) | Skeleton: portable app library + host tests |
| [`esc/`](esc/) | ST B-G431B-ESC1, one per hub motor | PlatformIO + Arduino + SimpleFOC | Skeleton |

See the build commands in the repository's `CLAUDE.md`.
