# Market Analysis: Weed Robots for Paved Areas (Municipalities and Housing Associations)

Can SprayRover's technology be sold to Danish municipalities, housing associations and similar customers to remove
weeds from paving, kerbs, paths and gravel?

Researched October 2026. Main sources:
- Miljøstyrelsen's 2019 case study of 15 municipalities
  ([MST 2019](https://www2.mst.dk/Udgiv/publikationer/2019/09/978-87-7038-102-4.pdf))
- the 2020 survey of pesticide use on public land
  ([MST 2021](https://www2.mst.dk/Udgiv/publikationer/2021/05/978-87-7038-315-8.pdf))
- company and press material

**Figures marked (estimate) are our own calculations.**

## 1. Verdict

| Question | Answer |
|---|---|
| Is the problem real? | **Yes, and well documented.** Municipalities find pesticide-free weed control on paving slow, labour-intensive and weather-dependent. Some went back to pesticides to save money |
| Is there money? | **Yes.** One municipality (Herning) spends about **2 million DKK a year** on weeds on hard surfaces. Hot water costs another (Egedal) **1,800 DKK per km of path per year** |
| Is the technology easier than lawns? | **Yes.** Green on grey/brown is easy to detect (OpenWeedLocator does it out of the box), and paved areas are flat, so the M1 can already drive there |
| Is there room for us? | **Tight.** At least two Danish startups are 2–3 years ahead: **Heibjerg** (hot water + mechanical, GNSS, trials with a cemetery and a housing association) and **O-Robotics** (brush robot). **Capra Robotics** ($12 M seed) also lists weed removal as an application |
| Probability of a business as a robot maker | **Low.** We would be the third or fourth Danish entrant in a small home market |
| Better angle | **Supply these companies** with the part they struggle with: navigation in urban multipath (see [market-navigation-module.md](market-navigation-module.md)), or weed detection / spot treatment. Or find a sub-niche they don't serve (section 7) |

## 2. The problem

- **Background:**
  - Since 1998, a voluntary agreement between the state, KL (the association of municipalities) and the
    regions aims to phase out pesticides on public land. It was renewed in 2007.
  - Since 2024, persistent products such as glyphosate are banned on paths, pavements and terraces
    (see [regulations-and-safety.md](../regulations-and-safety.md)).
- **Methods used instead:**
  - gas burning,
  - hot water (e.g. Heatweed) or hot water with foam,
  - steam,
  - brushes,
  - easily degradable products (pelargonic and acetic acid).
- **What municipalities report (MST 2019):**
  - Thermal methods need **many treatments a year at low speed**. Herning: every ~10 days would be needed,
    but they only manage every ~14 days, so weeds increase a little every year.
  - Herning treats **16 hours a day, 15 March–15 November, in all weather.**
  - Heavy machines (**2.5 t** when loaded) break and tilt paving.
  - Gas burning has caused fires.
  - Roundabouts and traffic islands with cobbles are "a big challenge", because the work needs traffic signage
    for safety.
  - Some municipalities **went back to pesticides** for economic reasons. Others chose methods based on a
    business case and then found running costs higher than expected.
  - Municipalities that still spray often have a political requirement for **sensor-based or spot sprayers**
    to minimise use.
- **Use of easily degradable actives on public land rose from 3,017 kg to 4,928 kg between 2016 and 2020**,
  partly because these products need more applications and larger amounts per area (MST 2021). A spot
  sprayer reduces exactly that.

## 3. The money

| Data point | Value | Source |
|---|---|---|
| Herning: budget for weeds on hard surfaces | **≈ 2 million DKK/year** (15–18% of the operations budget) | MST 2019 |
| Egedal: hot water (Heatweed), 6 treatments a year | **300 DKK per km per treatment, 1,800 DKK per km per year** (about 480 DKK/km/year more than expected) | MST 2019 |
| Herlev: weed budget for paving | ≈ 50,000 DKK/year (small municipality, mostly asphalt) | MST 2019 |
| Private market: brush machine on paving/gravel | ≈ 12–22 DKK/m² | [Aalborg Gartner](https://aalborggartner.dk/fjernelse-af-ukrudt/) |
| Private market: hot-water cleaning of paving | ≈ 29–46 DKK/m² | [Fliseguru](https://fliseguru.dk/fliserens-frederiksvaerk), [Håndværkerpris](https://xn--hndvrkerpris-tcbr.dk/hedvandsrens/fliserens/fliserens-prisberegner/) |
| Housing sector | **489 housing organisations** (2024), on average 1,219 homes and just under 15 estates each, so ≈ 7,000 estates (estimate) | [Landsbyggefonden](https://www.lbf.dk/media/oxtkjlcy/temastatistik-2024-11-organisatoriske-enheder-i-den-almene-boligsektor-2018-2024.pdf) |

**National size (estimate):** 98 municipalities spending between ~50,000 DKK (small, urban) and ~2 million DKK
(large, many paved areas) a year gives roughly **30–150 million DKK a year** for weeds on municipal hard surfaces
in Denmark. On top come housing associations, cemeteries, schools, business parks and private contractors.
**Nordic and North-European markets** (Netherlands, Germany, Sweden) have the same pesticide pressure and are
several times larger. Dutch sources call pesticide-free weed control on paving "a very big challenge"
([Stad & Groen](https://www.stad-en-groen.nl/article/47511/onkruidbeheer-op-bestrating-meer-en-beter-laten-samenwerken)).
German municipalities buy hot-water equipment
([kommunal.de](https://kommunal.de/Unkrautvernichtung-ohne-Pestizide-Heisswasser)).

## 4. Competitors

| Company | Country | Product | Status | Source |
|---|---|---|---|---|
| **Heibjerg** | DK | Small autonomous robot with service station (refills water, charges). Hot water + mechanical, vision spot treatment ("up to 65% less energy"), GNSS (looking at Galileo HAS and RTK) with IMU/encoder/vision fusion. App for mapping, geofence and fleet | ESA kick-start project ended summer 2025. Trials with Sdr. Nærå cemetery and Civica housing association. Pre-seed, 1–10 people. "Continuing towards commercialisation" | [ESA](https://business.esa.int/projects/heibjerg-apw-robot), [The Hub](https://thehub.io/startups/heibjerg-aps) |
| **O-Robotics** | DK (Aarhus/Odense) | AMR-Sweeper: brush robot for weeds, moss, algae, leaves, snow, litter. No chemicals or heat, runs around the clock | Founded 2022, 4 employees, Odense Robotics StartUp Fund. Focus on commercial customers (amusement parks, large organisations); municipalities waiting to test | [Teknologisk Institut](https://www.teknologisk.dk/ydelser/o-robotics/46492), [TechSavvy](https://techsavvy.media/robotten-fejer-og-bekaemper-ukrudt-man-er-noedt-til-at-loebe-langt-paa-literen/) |
| **Capra Robotics** | DK (Aarhus) | Hircus outdoor robot platform with tools. Its flyer lists weed removal and sidewalk de-icing | $12 M seed (2025). Best-known case is logistics at VELUX | [Capra](https://capra.ooo/), [Dealroom](https://dealroom.co/companies/capra-robotics/) |
| Municipal Robotics | US | Sidewalk robot with swappable tools (snow, debris, pressure washing) | Pilots with US cities, summer 2026 | [muni.works](https://muni.works/) |
| Heatweed, Kersten, Kärcher, SPUMA, CityZAS (electric) | NO/NL/DE/BE | Hot water, brushes, foam, high voltage. **Driven by an operator** | Established. Used by Danish municipalities | MST 2019, [Kersten](https://kerstenuk.com/weed-brush/weedo-series/weedo-ii), [Landbouwleven](https://www.landbouwleven.be/23639/article/2025-10-19/machinedemo-toont-doelgericht-onkruid-bestrijden-met-robotica-en-ai) |

**Summary:** the autonomous version of this market is **being formed right now**, and Danish startups are leading
it. We found no robot in large-scale commercial use yet. That is an opportunity, but two to three Danish teams are
already 2–3 years ahead, and one has real funding.

## 5. Customers and how they buy

| Customer | Who decides | How they buy | Notes |
|---|---|---|---|
| Municipalities | Operations manager (materielgård / park og vej) | Public tenders (udbud), framework contracts, or via contractors. Innovation pilots possible | Slow (budget year, politics). Need references, insurance, safety on public paths |
| Housing associations | Operations manager / estate management, board | Simpler procurement. Often own staff (ejendomsfunktionærer) | Many smaller areas. Want low effort and good looks for residents. Civica already tested Heibjerg |
| Cemeteries | Cemetery manager (parish council / municipality) | Small budgets, but large raked gravel areas and high quality demands | Fenced and calm, a good beachhead. Heibjerg already targets them |
| Landscaping contractors (anlægsgartnere) | Owner | Buy machines that raise their productivity in municipal contracts | Can be the channel to municipalities |
| Business parks, campuses, amusement parks | Facility manager | Direct purchase or service contract | O-Robotics' current focus |

**Business model that fits:** robot-as-a-service, paid per km or m² per season, priced below the current method.
The benchmark is Egedal's 1,800 DKK/km/year for hot water. That beats selling the robot outright, because
municipalities buy services more easily than new technology.

## 6. Fit with SprayRover

| Need | SprayRover status |
|---|---|
| Detect weeds in joints and gravel | **Easy.** OWL green detection works out of the box. Our YOLO model adds species detection |
| Drive on paving | **The M1 can drive there now** (indoor robot on hard, flat surfaces). Good for a demo, not for a product |
| Treatment | Spot spraying with easily degradable products (pelargonic or acetic acid), already used by municipalities, cuts volume a lot. Hot water and brushes need more energy and weight. **Check the rules for professional spot application** |
| Navigation in town (multipath between buildings) | Our planned GNSS + IMU + odometry fusion, later radar, is exactly this problem |
| Safety in public spaces | Must be designed in. EU Machinery Regulation from January 2027 requires a supervisory function for autonomous machines |

## 7. Where a newcomer could still fit

1. **Lightweight spot sprayer** for municipalities that still use easily degradable products. Cut volume by
   80–95% instead of replacing the method. This is a different product from Heibjerg's hot water and O-Robotics'
   brush. **Risk:** the political trend is towards zero chemicals.
2. **Cemeteries and raked gravel**, if Heibjerg doesn't cover them well.
3. **Component supplier:** sell navigation, weed detection or spot-treatment modules to Heibjerg, O-Robotics
   and Capra instead of competing with them. **This is the most realistic option for a two-person team**, and it
   joins up with the navigation-module track.

## 8. Risks

- **Competition ahead:** two to three Danish teams with a head start, one with $12 M.
- **Small home market:** about 98 municipalities. You need the Nordics, Netherlands or Germany to grow, which
  means more sales work.
- **Public sales cycles** are slow; references and insurance are needed.
- **Operations:** robots in public spaces face vandalism, theft, children, dogs, cyclists, weather and
  water/energy refilling.
- **Rules:** professional use of plant protection products and the trend towards zero chemicals may close the
  spot-spray angle.

## 9. Validation plan (2–3 months, low cost)

1. **Interview 5–8 buyers:**
   - 2 municipal operations managers (e.g. one that uses hot water, one that uses pesticides),
   - 1–2 housing associations,
   - 1 cemetery,
   - 1–2 landscaping contractors.

   Ask:
   - What do you spend per km or m² today?
   - How often do you treat?
   - What annoys you most?
   - Would you pay per km for a robot service?
   - Have you seen Heibjerg or O-Robotics?
2. **Talk to Heibjerg, O-Robotics and Capra as possible partners or customers.** What do they buy in? What is
   their biggest technical problem? Navigation? Detection?
3. **Demo on the M1:** detect weeds in paving joints and hit them with coloured water. Film it. This costs little,
   reuses phase 1 of the [project plan](../project-plan.md) and makes the interviews concrete.
4. **Go/no-go:** go if at least 2 buyers want a pilot **and** we find a gap the startups don't cover. Otherwise
   go for the supplier role (section 7, option 3).
