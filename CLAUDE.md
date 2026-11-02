# SprayRover: rules for AI assistants

A father-and-son project (the son studies software, 5th semester; the father is an engineering manager with
underwater navigation experience). It started as an autonomous weed-spraying garden rover. It now also has a
business track for a **navigation module** (GNSS + IMU + Doppler radar). Start with `docs/README.md`.

## Talking to the user
- **Reply in Danish** in chat. Repository files (code, docs, commit messages) are in English. Exceptions
  written in Danish: `docs/ordliste.md` (glossary) and anything the user explicitly asks for in Danish.
- **Explain simply.** Assume no prior knowledge of robotics jargon. Explain every abbreviation the first time
  it appears in chat. When a new term shows up in the docs, **add it to `docs/ordliste.md`**.
- Be honest about uncertainty. Say clearly what is verified, what is an estimate and what is a simulation
  result. Never present simulated numbers as real measurements.
- Short and concrete beats long. When there are several options, recommend one and say why.
- The user is **cost-conscious about cloud session credits**. Prefer high-value work. Give rough sizes
  (small/medium) when proposing tasks, and don't start large unrequested work.
- The user works on a **Mac with VS Code**. Use `python3` and `source .venv/bin/activate` in instructions.
- The user likes **visualisations** (artifact pages, plots). When asked for a style, follow it exactly.

## Branches and pull requests
- **`v2` is the base branch for all current work.** Create feature branches from `v2` and open PRs **into
  `v2`**.
- `main` and `dev` hold the old v1 work. **Don't merge `v2` into `dev` or `main`** unless the user asks; a
  `v2 → dev` PR was closed on purpose.
- **Never merge a PR without the user's explicit go-ahead in the current conversation.** Wait for green CI,
  then ask.
- The session cannot delete remote branches. Tell the user when a merged branch should be deleted.
- Commit messages: imperative summary line, a short body explaining why, no model names.

## Research and facts
- **Cite sources** (links) for market data, prices, regulations and product specs. Mark your own estimates
  as estimates.
- Hardware facts (part numbers, voltages, dimensions, prices) must come from datasheets, official product
  pages or the docs. Don't guess. Put unresolved items in `docs/risks-and-open-questions.md`.
- Danish rules on pesticides and machine safety change. Check before relying on them and say when a source
  couldn't be reached.

## Project context to remember
- **Robot owned:** Yahboom **ROSMASTER M1**, Superior kit with Jetson Orin Nano Super. Mecanum wheels,
  28 × 23 × 18 cm, ROS 2 Humble. It is an indoor development platform, not a lawn robot. See
  `docs/platform-rosmaster-m1.md`.
- **Navigation track:** the "Land-DVL" module. The father works at Teledyne (DVL/INS products). Rights and
  contract questions are assumed resolved for planning, but **flag IP/employer conflicts** when work moves
  towards a product.
- **Strategy that was agreed:**
  - Reuse before building: ROS 2, Nav2, OpenWeedLocator, existing kits.
  - Measure before deciding: simulations first, then the measurement rig.
  - Each phase has an exit criterion. Avoid scope creep (the v1 lesson).

## Code: `navigation/` (Python package `landdvl`)
```bash
cd navigation
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[plot,dev]"
python -m pytest                            # tests
ruff check . && ruff format --check .        # lint/format (line length 100)
python -m landdvl.sim --out logs/sim01       # simulated log (mock data)
python -m landdvl.evaluate logs/sim01        # artificial GNSS-outage test + plots
python -m landdvl.sweep --out results/sweep  # sensitivity analysis (slow; --quick for a short run)
python -m landdvl.rig.loopback logs/sim01 logs/sim01_lb  # rig logger test without hardware
```
- The log format in `landdvl/logio.py` is shared by the simulator and the real measurement rig. Keep them
  compatible, and keep real-log support (no `truth.csv`) working. The rig logger lives in `landdvl/rig/`
  (docs: `docs/navigation/rig-logger.md`); its loopback test checks the two stay compatible.
- Validate results before reporting them. Look at the plots and sanity-check the numbers. Earlier bugs were
  found exactly this way.
- CI (`.github/workflows/navigation.yml`) runs lint, tests and a sim + evaluate smoke run on PRs to `v2`.
- Generated `logs/` and `results/` are not committed.
