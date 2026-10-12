# SprayRover

SprayRover is an autonomous weed-spraying rover project that combines hardware, software, AI, and computer vision to detect weeds and spray them precisely.

## Repository structure

- `documentation/` - Project documentation, diagrams, and source references (start with [`documentation/system-architecture.md`](documentation/system-architecture.md))
- `hardware/` - Schematics, component lists, and wiring documentation
- `software/` - Application modules for vision, rover control, and spray systems
- `tests/` - Unit tests, integration tests, and reusable test data

## Root files

- `README.md` - Project overview and repository guide
- `.gitignore` - Python-oriented ignore rules for local and generated files
- `requirements.txt` - Python dependency list for the software stack

## Branching workflow

- `main`: **release** branch. Only updated by merging `dev` when a release is ready.
- `dev`: **development** branch. All feature/fix pull requests target `dev`.
- Feature branches are created from `dev` and merged back into `dev` through a pull request.
