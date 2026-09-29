# SprayRover

SprayRover is an autonomous weed-spraying rover project that combines hardware, software, AI, and computer vision to detect weeds and spray them precisely.

## Repository structure

- `documentation/` - Project documentation, diagrams, and source references (start with [`documentation/system-architecture.md`](documentation/system-architecture.md))
- `firmware/` - Microcontroller firmware: `nav-mcu/` (STM32H7) and `esc/` (motor controllers, SimpleFOC)
- `companion/` - Python package `sprayrover` for the Linux companion computer (vision, planner, radar, simulation, UI)
- `shared/` - Rover configuration (`config/rover.yaml`) and MCU ↔ companion protocol definitions
- `hardware/` - Schematics, component lists, and wiring documentation
- `tests/` - Python unit tests, integration tests, and reusable test data
- `tools/` - Helper scripts (logging, plotting, calibration)

## Getting started

```bash
pip install -e ".[dev]"      # install the Python package and dev tools
pre-commit install           # run formatters/linters automatically on each commit
python -m pytest             # run the Python tests
```

Firmware build commands are listed in [`CLAUDE.md`](CLAUDE.md). CI runs all checks on every pull request.

## Branching workflow

- `main`: **release** branch. Only updated by merging `dev` when a release is ready.
- `dev`: **development** branch. All feature/fix pull requests target `dev`.
- Feature branches are created from `dev` and merged back into `dev` through a pull request.
