# Market Analysis: Navigation Module for Outdoor Robots

Can the "self-contained navigation module" from the original notes become a business?
The idea is cheap GNSS + MEMS IMU + Doppler radar + wheel odometry + INS sensor fusion, built on the
underwater navigation experience at the notes author's company.

Researched October 2026. Market figures come from paid-report summaries and vendor material. They vary
a lot between sources and should be read as orders of magnitude. **Figures marked (estimate) are our own
calculations, not sourced numbers.**

## 1. Verdict

| Question | Answer |
|---|---|
| Is the problem real? | **Yes.** Every wire-free robot that works near trees and buildings has it, and the industry says so openly |
| Is there a market? | **Yes, but it is split.** Mass-market robot mowers are cost-driven and mostly build in-house. Small and mid-sized professional robot makers are the realistic customers |
| Is there room for a newcomer? | **Some.** Radar-aided navigation at a mid-range price appears to be an open spot. Vision-based fusion is already sold (Fixposition) and built into mowers |
| Fit with the team? | **Best fit in the whole SprayRover idea space.** INS and Doppler-aided navigation is the team's unique skill |
| Probability of a real business | **Low to medium**, with the highest upside of the options considered. It depends on proving that radar aiding beats vision/RTK fusion on cost or robustness |

**Recommendation:** treat it as a B2B track next to the SprayRover hobby build. Validate cheaply over 3–6 months
(section 8) before investing serious money. **Clarify with the notes author's employer** that this doesn't
conflict with their work, IP or non-compete terms.

## 2. The problem

- Robot mowers are moving from buried boundary wires to RTK GNSS with virtual boundaries
  ([The Robot Report](https://www.therobotreport.com/the-hidden-infrastructure-challenge-facing-outdoor-robotics-oems/)).
- **RTK degrades under trees and near buildings**:
  - signals are blocked, weakened or reflected,
  - which gives dropouts and sudden position jumps
  ([Mowrator](https://mowrator.com/blogs/news/rtk-robot-mower-signal-loss-trees),
  [RTKdata](https://rtkdata.com/blog/wire-free-robot-mower-rtk-accuracy-guide-2026/)).
- The CEO of the Danish line-marking robot maker TinyMobileRobots says trees and buildings degrade accuracy
  through multipath, so the robots need clearance from them
  ([ForConstructionPros](https://www.forconstructionpros.com/pavement-maintenance/marking-striping/article/22131633/can-robots-simplify-parking-lot-striping)).
- The Danish weeding-robot startup Heibjerg writes that it is adding IMU, wheel-encoder and vision fusion
  "to handle obstructions and multipath in urban areas"
  ([ESA Business Applications](https://business.esa.int/projects/heibjerg-apw-robot)).
- Without an absolute reference, uncertainty grows without bound, and fusion only slows the growth:
  - inertial error grows with time squared,
  - visual and wheel error grow with distance
  ([Fixposition](https://www.fixposition.com/blogs/field-guide/outdoor-robot-localization-gnss-blocked)).

  **The value of a module is how long and how far it keeps cm–dm accuracy without GNSS.**

## 3. Who has the problem (customer segments)

| Segment | Examples | Volume | Will they buy a module? |
|---|---|---|---|
| Mass-market robot mowers | Husqvarna, Segway Navimow, Mammotion, Ecovacs, Kress, Sunseeker | Europe market about USD 0.6–1.0 billion in 2025, growing 6–9% a year ([GMI](https://www.gminsights.com/industry-analysis/europe-robotic-lawn-mower-market), [Mordor](https://www.mordorintelligence.com/industry-reports/europe-robotic-lawn-mower-market), [IMARC](https://www.imarcgroup.com/europe-robotic-lawn-market)). Germany alone > 170,000 units in 2025 ([Arizton](https://www.arizton.com/news/press-release/robotic-lawn-mower-market-eu-2027-vendor-share)). Vision-guided models growing ~19% a year (Mordor) | **Unlikely.** They already ship their own fusion (Kress EyePilot, Mammotion Tri-Fusion, Ecovacs UWB) and design to a tight bill of materials. A licence deal for an algorithm is possible, but hard for a small team to win |
| Professional outdoor service robots (small/mid makers) | Heibjerg, O-Robotics, Capra Robotics (all Danish), Municipal Robotics (US), cemetery/park/campus robots | Tens to hundreds of units per year per maker (estimate) | **Most likely customers.** Small teams with no navigation specialists. Urban multipath and trees are their daily problem. Can pay hundreds to a few thousand € per unit |
| Line-marking and sports-turf robots | TinyMobileRobots (DK, uses Unicore UM960 RTK, [GPS World](https://www.gpsworld.com/?p=105938)), Turf Tank (DK) | Hundreds to low thousands of units per year (estimate) | **Possible.** Need cm accuracy. Today they ask for clearance from trees, so they might pay for an under-tree solution if it is accurate enough |
| Small agricultural robots | FarmDroid (DK), Agrointelli Robotti (DK), Naïo | Hundreds of units per year (estimate) | **Low priority.** Open fields mean little canopy. Radar ground speed is already a known farm technique |
| Hobby/open source | OpenMower community, ROS developers | Thousands of builders | **Not a revenue market**, but a good way to get known (section 7) |

## 4. What exists today and what it costs

| Product | What it is | Price | Source |
|---|---|---|---|
| u-blox ZED-F9R | RTK GNSS with built-in IMU dead reckoning (the "standard" fused module) | ~€116 (250-reel) to ~€142 (single) for the 03B variant | [DigiKey](https://www.digikey.it/en/products/detail/u-blox/ZED-F9R-03B/18880544) |
| ArduSimple simpleRTK3B Budget (Unicore UM980) | Triple-band RTK board | ~€223 | [ArduSimple](https://www.ardusimple.com/product/simplertk3b-budget) |
| Quectel LG69T | Dual-band RTK, optional dead reckoning, used in mowers | Not published | [BusinessWire](https://www.businesswire.com/news/home/20231010162980/en) |
| **Fixposition Vision-RTK 2** | Dual-antenna RTK + visual odometry + IMU + wheel speed fusion, ROS 1/2 drivers, "Lawnmower" mode, IP66 | **~€2,900–3,570** | [Generation Robots](https://www.generationrobots.com/en/404417-vision-rtk-2-starter-kit.html), [Reichelt](https://www.reichelt.com/de/en/shop/product/fixed_position_vision_sensor_fusion_-_rtk2_starter_kit-353613), [Husarion](https://store.husarion.com/products/fixposition-vision-rtk-2) |
| Point One Atlas | GNSS/INS sold as subscription incl. corrections | "$500" listed, sold via sales contact | [Point One](https://store.pointonenav.com/products/atlas-ins) |
| RTK correction services | Point One, RTKdata and others: managed NTRIP for fleets | Subscription | [The Robot Report](https://www.therobotreport.com/the-hidden-infrastructure-challenge-facing-outdoor-robotics-oems/) |
| In-house mower fusion | Kress EyePilot (RTK + vision + IMU + odometry), Mammotion (vision + RTK + lidar), Ecovacs GOAT (UWB beacons) | Part of the mower | [Kress](https://www.kress.com/en-ie/?p=1298295), [Mammotion](https://au.mammotion.com/blogs/news/ai-vision-vs-rtk-vs-lidar), [Ecovacs](https://www.ecovacs.com/global/campaign/goat-robotic-lawn-mower) |

**The gap:** between a ~€140 GNSS/IMU chip that drifts quickly without satellites and a ~€3,000 vision fusion box,
we found **no product that uses Doppler radar for speed over ground**.

The technique itself is old and proven in agriculture, where radar on the vehicle is compared with wheel speed
to measure slip ([patent US4728954](https://www.google.com.au/patents/US4728954)). TI describes using mmWave
radar against the ground as odometry for robots on gravel, dirt and wet ground
([Mouser/TI](https://resources.mouser.com/i/1442859/14)). Research has fused a low-cost Doppler radar with an
accelerometer for rover ground speed and slip control
([HAL](https://hal.archives-ouvertes.fr/hal-03177963)).

Radar is not affected by darkness, rain, dust or textureless surfaces, which are the cases where cameras fail.

**Known weaknesses of Doppler ground speed:**
- pitch and yaw errors on rough ground,
- worse accuracy at low speed,
- single-beam sensors can't tell forward from reverse
  ([patent US4942558](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4942558)).

The original notes' **4-beam** design addresses exactly these points: several beams give the full velocity
vector, including sideways and vertical. It is the land version of an underwater DVL (Doppler velocity log).

## 5. Possible offer

| Option | What we sell | Price point (estimate) | Pros | Cons |
|---|---|---|---|---|
| A. Hardware module | GNSS + IMU + 4-beam mmWave Doppler + fusion in one IP-rated box with ROS 2 driver | €400–1,000 per unit for small series | Clear product, placed between the ZED-F9R and Fixposition | Needs hardware development, certification (CE/radio), production, support |
| B. Fusion software + reference design | Licence the fusion software and a reference design built on off-the-shelf parts (u-blox/Unicore + TI radar chip) | Licence per unit or per project | Little capital, scales | Harder to protect. Customers must build hardware |
| C. Engineering services | Help robot makers integrate GNSS/INS/radar fusion | Hourly or project price | Revenue early, teaches what customers need | Doesn't scale. Competes with the day job |

**Suggested path:** C → B → A.
1. Start with projects for 1–3 Danish robot makers (C). That gives money, data and credibility.
2. Turn the fusion stack into a product (B).
3. Build hardware (A) only when several customers want the same box.

## 6. Market size (rough, bottom-up)

No source gives unit volumes for professional outdoor service robots. **Illustration only (estimate):**

| Scenario | Customers | Units per customer per year | Price per unit | Revenue per year |
|---|---|---|---|---|
| Small | 5 | 50 | €600 | ≈ €150,000 |
| Medium | 20 | 100 | €800 | ≈ €1.6 million |
| Large (one mid-size mower or line-marking OEM) | 1 + 20 | 5,000 + 100 | €150 (OEM) / €800 | ≈ €2.3 million |

A small-scenario business can support part-time founders. The medium scenario is a real company. Reaching it
needs proof in the field, at least one reference customer and probably outside funding.

## 7. Competitive position

**Strengths:**
- INS/DVL experience from underwater navigation. Few people outside defence and marine know this.
- A radar-based approach that differs from the vision-based competitors.
- A Danish robot cluster nearby (Odense Robotics, Aarhus) with several target customers in the same country.
- Open source as marketing: a working ROS 2 radar-odometry node would get attention.

**Weaknesses:**
- Part-time team.
- No hardware production experience (assumption).
- No customers yet.

**Opportunities:**
- Wire-free robots are growing in every outdoor segment.
- Small makers are stuck with multipath.
- Cheaper mmWave chips (TI IWR6843 and successors).

**Threats:**
- Vision fusion gets cheaper fast.
- Big GNSS vendors (u-blox, Septentrio, Unicore) add better dead reckoning.
- Mower OEMs keep everything in-house.
- Conflict with the employer's interests.

## 8. Validation plan (3–6 months, low cost)

1. **Data first.** Log GNSS (RTK fix status), IMU, wheel odometry and the TI mmWave radar kit (already in the
   v1 notes) while driving under trees and along walls. Use a pushed trolley or the outdoor chassis; the M1 is
   too small for lawn. Store the logs in `docs/results/`.
2. **Prototype fusion offline** (ESKF, as in the v1 notes) and measure: error after 10, 30 and 60 s without
   GNSS, with and without radar. **Success:** radar aiding at least halves the error growth compared with
   IMU + wheels alone.
3. **Talk to 10 potential customers:** Heibjerg, O-Robotics, Capra Robotics, TinyMobileRobots, Turf Tank,
   FarmDroid, Agrointelli, plus 3 outside Denmark. Ask:
   - What positioning do you use today?
   - What does it cost per unit?
   - Where does it fail?
   - What would a fix be worth?
4. **Go/no-go:** go on to a product if at least **3 companies agree to a paid pilot or sign a letter of intent**,
   and the radar result in step 2 holds. Otherwise keep it as open-source reputation work.

## 9. Funding options in Denmark (to check)

- **Innobooster** (Innovationsfonden) for small company innovation projects. Status not verified.
- **Odense Robotics StartUp Fund / incubator.** O-Robotics was selected for it
  ([Teknologisk Institut](https://www.teknologisk.dk/ydelser/o-robotics/46492)).
- **ESA Business Applications** kick-start funding for space-based services such as GNSS/Galileo HAS.
  Heibjerg used it ([ESA](https://business.esa.int/projects/heibjerg-apw-robot)).
- **MUDP** (130 million DKK in 2026, deadlines for 2026 passed;
  [DI](https://www.danskindustri.dk/politik-og-analyser/di-mener/miljoenergi/nyheder-fra-miljo-og-klima/2026/02/informationsmode-om-mudp-den-2.-marts-130-millioner-kroner-til-udvikling-af-fremtidens-miljoteknologier))
  fits better with the hard-surface weeding niche than with a navigation module.
