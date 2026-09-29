# SprayRover: notes for AI assistants and contributors

Autonomous garden rover that detects weeds with a camera and sprays them. Start with
`documentation/system-architecture.md`; design details are in `documentation/design/`.

## Branching workflow
- `main` = releases, `dev` = development.
- Create feature branches from `dev` and open pull requests **into `dev`**, unless told otherwise.
- Only release PRs go from `dev` into `main`.

## Repository layout
- `firmware/nav-mcu/`: STM32H7 firmware (C++17, CMake). Portable logic in `app/` is unit-tested on the host.
  STM32CubeMX/HAL code will be added once the board is chosen.
- `firmware/esc/`: B-G431B-ESC1 motor controller firmware (PlatformIO + Arduino + SimpleFOC).
- `companion/sprayrover/`: Python package for the Linux companion computer (vision, planner, radar, sim, ui).
- `shared/config/rover.yaml`: single source of truth for geometry and sensor offsets. Don't hard-code these elsewhere.
- `shared/protocol/`: MCU ↔ companion message definitions (planned: nanopb/protobuf).
- `tests/`: Python tests. Firmware host tests live in `firmware/nav-mcu/tests/`.
- `documentation/sources/`: original notes and datasheets. **Never modify them.**

## Commands
```bash
pip install -e ".[dev]"            # Python package + dev tools
python -m pytest                   # Python tests
pre-commit run --all-files         # ruff, ruff-format, clang-format, whitespace

# Nav MCU firmware
cmake -S firmware/nav-mcu -B build-host && cmake --build build-host && ctest --test-dir build-host
cmake -S firmware/nav-mcu -B build-arm -DCMAKE_TOOLCHAIN_FILE=cmake/arm-none-eabi.cmake && cmake --build build-arm

# ESC firmware
cd firmware/esc && pio run
```
CI (`.github/workflows/ci.yml`) runs all of the above on every PR.

## Conventions
- Units are SI (metres, radians, seconds). The body frame is x forward, y left, z up.
- Firmware: no exceptions, no RTTI, no dynamic allocation after init. Keep hardware access out of `app/`
  so the logic stays testable on the host.
- Python: formatted and linted with ruff (line length 100), tested with pytest.
- Hardware facts (part numbers, voltages, pinouts) must come from datasheets or the docs. Don't guess.
  Unresolved items are tracked in `documentation/design/open-questions.md`.
