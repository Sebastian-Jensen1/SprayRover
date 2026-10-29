# Regulations and Safety

What limits how SprayRover may treat weeds and how it must be built. **This is research, not legal advice.**
Several points must be checked with the Danish EPA (Miljøstyrelsen, mst.dk) before we spray anything other
than water. mst.dk could not be reached from the research environment, so the points below come from
secondary Danish sources and are marked as such.

## 1. Pesticides in private gardens (Denmark)

| Rule | Source |
|---|---|
| Private persons may only use products approved for private use. They must be sold **ready-to-use** or be classified as **low-risk** | [Den Offentlige, citing MST](https://www.denoffentlige.dk/hus-og-have/disse-ukrudtsmidler-er-forbudt-i-din-private-have-her-er-miljoestyrelsens-regler) |
| Since 1 July 2020, private persons without authorisation may not buy concentrated products (e.g. Roundup concentrate) | [Bolius](https://www.bolius.dk/nu-bliver-det-ulovligt-at-koebe-koncentrerede-sproejtemidler-92692), [Folketinget answer](https://www.ft.dk/samling/20241/spoergsmaal/s652/svar/2112624/2978627.pdf) |
| Since 2024, persistent products such as **glyphosate** may not be used on paths, driveways, pavements, terraces and gravel. Products that break down easily (acetic acid, pelargonic acid) are not covered by this ban | [Ritzau](https://via.ritzau.dk/pressemeddelelse/13649366/nu-kommer-der-sprojteforbud-pa-fortove-og-terrasser?publisherId=13560422), [Verdensmål.org](https://www.verdensmaal.org/nyheder/folketinget-skrotter-skrappe-spr%C3%B8jtemidler) |
| Plain household vinegar, salt or chlorine may **not** be used as weedkiller. Only products approved for the purpose count | [Bolius](https://www.bolius.dk/maa-du-bruge-eddikesyre-som-ukrudtsmiddel-35665) |
| Using an unapproved product (including one bought abroad, or whose approval was withdrawn) is a criminal offence | [Den Offentlige](https://www.denoffentlige.dk/hus-og-have/disse-ukrudtsmidler-er-forbudt-i-din-private-have-her-er-miljoestyrelsens-regler) |
| Approvals change: 33 PFAS products were withdrawn in 2025, and propyzamide is under review | [Miljøministeriet](https://mim.dk/nyheder/pressemeddelelser/2025/september/otte-pfas-sproejtemidler-bliver-forbudt) |
| A full ban on herbicides in private gardens has been proposed politically several times but **not adopted** as of October 2026. A 2026 parliamentary motion (B 123) aims at groundwater areas | [DR](https://www.dr.dk/nyheder/politik/efter-roedt-pres-regeringen-vil-forbyde-private-sproejte-med-roundup), [Retsinformation](https://www.retsinformation.dk/api/pdf/255756) |

### What this means for SprayRover

- **Development and testing use plain water**, optionally with food colouring so we can see hits on the
  ground. This is always allowed and is the best way to measure how accurately the robot sprays.
- **For real use, the robot carries an approved ready-to-use product and applies it to single weeds.**
  Spot treatment fits the purpose of the rules well, because it uses far less product than spraying a whole area.
- **Before we spray a real product, ask Miljøstyrelsen** whether applying an approved ready-to-use product
  from an automated device in a private garden is in line with its label. Labels say how a product may be applied.
- **Design the treatment head so it can be swapped.** Spray (any approved liquid), hot water or a mechanical
  tool must fit the same mount and the same "treat this weed" command. Then a rule change doesn't kill the project.
- **Selling the robot or treating other people's gardens** brings in further rules (professional use,
  spraying certificate). That is out of scope until a product decision is made.

## 2. Machine safety

- **EU Machinery Regulation 2023/1230** replaces the Machinery Directive and applies from **January 2027**.
  Most sources give 20 January; check the Official Journal for the exact date.
  It explicitly covers **autonomous mobile machinery** and requires a **supervisory function**: a person must be
  able to monitor and stop the robot in autonomous mode
  ([EU-OSHA](https://osha.europa.eu/en/legislation/directive/regulation-20231230eu-machinery),
  [CEMA](https://www.cema-agri.org/publication/news/1025-the-new-machinery-regulation-is-published-new-requirements-and-upcoming-steps)).
  This only matters formally if SprayRover is sold, but it is a good design rule from day one.
- **Design rules we adopt now:**
  1. A physical **E-stop** button on the robot that cuts drive power.
  2. A **wireless stop** (remote kill), and the robot stops by itself if it loses contact with the operator or planner (watchdog).
  3. **Low speed** in autonomous mode (walking pace or slower) and a **geofence** the robot cannot leave.
  4. The spray valve is **normally closed** and only opens on a valid "treat" command.
  5. A **bumper or contact sensor** as the last line of defence, in addition to any radar, camera or ultrasound.

## 3. Other points

| Topic | Note |
|---|---|
| Lasers | Lasers strong enough to kill weeds (several watts) are a serious eye hazard (Class 4). Only consider this with an enclosed, downward-facing design and proper safety interlocks. Not part of the first versions |
| Radio | Off-the-shelf CE-marked radio modules (Wi-Fi, LoRa/telemetry for RTK, UWB) avoid our own radio certification |
| Cameras and privacy | A camera that points at the ground in your own garden is a minor issue. Avoid recording neighbours or people. Don't upload images with people in them to public datasets |
| Batteries | Hoverboard-type 36 V Li-ion packs need a proper BMS, fusing and a fire-safe charging place |
