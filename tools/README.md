# Tools

Helper scripts for development: log conversion, plotting, calibration.

| Script | What it does |
|---|---|
| `kinematics_viewer.py` | Interactive top-down view of the 4-wheel steering (`sprayrover.kinematics`). Sliders for forward speed, sideways speed and yaw rate; the rover drives around and shows wheel angles, wheel speeds and the turn centre. `--save modes.png` writes a picture of the driving modes instead. |

```bash
pip install -e ".[viz]"
python tools/kinematics_viewer.py
python tools/kinematics_viewer.py --save modes.png
```
