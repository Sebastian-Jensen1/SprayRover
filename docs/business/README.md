# Business Analysis

Can SprayRover, or the skills behind it, become a business? Researched October 2026.

| Document | Question |
|---|---|
| [market-navigation-module.md](market-navigation-module.md) | A navigation module (GNSS + IMU + Doppler radar + INS fusion) for outdoor robots that must work under trees and between buildings |
| [market-hardscape-weeding.md](market-hardscape-weeding.md) | Weed robots for paving, kerbs and gravel at municipalities, housing associations and cemeteries |

## Overall picture

| | Consumer garden robot | Paved-area weed robot (municipalities etc.) | Navigation module |
|---|---|---|---|
| Real pain | Medium | **High, documented** | **High, documented** |
| Money available | Low per customer, many customers | ≈ 30–150 M DKK/year in Danish municipalities (estimate) | Hundreds to a few thousand € per robot for professional robots |
| Competition | Robot-mower giants | 2–3 Danish startups ahead (Heibjerg, O-Robotics, Capra) | Vision fusion (Fixposition, in-house OEM). **No radar-aided product found** |
| Our unique edge | Little | Little | **INS/Doppler know-how from underwater navigation** |
| Capital needed | High | Medium–high | Low (services/software) to medium (hardware) |
| Verdict | Hobby project | Low as robot maker; **good as supplier** | **Best fit, low–medium probability, highest upside** |

**The two niches connect.** The paved-area robot startups (Heibjerg, O-Robotics, Capra) all need robust
positioning in urban multipath and under trees. Heibjerg says so in its own project description. They are the
natural **first customers for a navigation module**. That is the "sell shovels in the gold rush" route: don't
build the fourth weed robot, build the part the others are missing.

## Recommended next steps

1. Run the **navigation data logging and fusion test** (navigation analysis, section 8) using the SprayRover
   GNSS hardware from phase 0.
2. **Book 10–15 conversations** in the next 2–3 months: robot makers first (Heibjerg, O-Robotics, Capra,
   TinyMobileRobots, Turf Tank), then 3–5 buyers (municipality, housing association, cemetery).
3. **Clarify the employer question** (IP, non-compete) for the navigation track before talking to customers.
4. **Decide in ~6 months:** navigation business, supplier of detection/spot treatment, or keep SprayRover as an
   open-source hobby. Each analysis has a go/no-go criterion.
