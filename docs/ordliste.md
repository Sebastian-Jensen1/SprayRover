# Ordliste: forkortelser og fagord

Alle de forkortelser og fagord, der bruges i SprayRover-dokumenterne, forklaret i almindeligt dansk.

## Position og navigation

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **GNSS** | Global Navigation Satellite System | Fællesbetegnelsen for alle satellitsystemer, der giver position. GPS er det amerikanske; der findes også Galileo (EU), GLONASS (Rusland) og BeiDou (Kina). En GNSS-modtager bruger dem alle samtidig |
| **GPS** | Global Positioning System | Det amerikanske satellitsystem. Bruges ofte i daglig tale om alle systemerne |
| **RTK** | Real-Time Kinematic | Teknik, der gør GNSS præcis ned til 1–2 cm i stedet for ca. 1–2 m. Kræver rettelsesdata fra en fast station tæt på |
| **Fix / float** | (RTK-tilstande) | **Fix:** RTK virker fuldt, positionen er på centimeteren. **Float:** RTK virker kun delvist, positionen er decimeter til meter forkert. **None:** intet signal |
| **Basestation** | | En ekstra GNSS-modtager, der står fast (fx på taget) og sender rettelser til robotten, så den kan få RTK |
| **NTRIP** | Networked Transport of RTCM via Internet Protocol | Måde at få RTK-rettelser over internettet fra en tjeneste i stedet for egen basestation |
| **RTCM** | Radio Technical Commission for Maritime Services | Standardformatet for RTK-rettelsesdata |
| **Galileo HAS** | High Accuracy Service | Gratis rettelser direkte fra de europæiske Galileo-satellitter. Giver ca. 20–40 cm uden basestation |
| **PPS** | Pulse Per Second | Et elektrisk puls-signal fra GNSS-modtageren præcis hvert sekund. Bruges til at give alle sensorer samme ur |
| **Multipath** | | Når satellitsignalet hopper af en husmur eller et træ, før det når antennen. Giver pludselige forkerte positioner |
| **IMU** | Inertial Measurement Unit | Lille chip med gyroskop (måler hvor hurtigt man drejer) og accelerometer (måler acceleration). Den samme slags sidder i en mobiltelefon |
| **MEMS** | Micro-Electro-Mechanical Systems | Den teknologi, billige IMU'er er lavet med: mikroskopiske mekaniske dele på en chip |
| **Bias** | | En IMU's nulpunktsfejl: den viser en lille værdi, selvom den står helt stille. Bias vandrer langsomt og skal løbende estimeres |
| **INS** | Inertial Navigation System | Et navigationssystem, der regner positionen ud fra IMU'en (og andre sensorer), uden at være afhængig af satellitter hele tiden |
| **Dead reckoning** | | At regne sig frem til positionen ud fra fart og retning, når man ikke har satellitter. Fejlen vokser med tiden |
| **Odometri** | | At måle tilbagelagt vej, fx ved at tælle hjulets omdrejninger. "Hjul-odometri" = position ud fra hjulet |
| **Encoder** | | Sensor, der tæller hvor meget et hjul eller en motor har drejet |
| **Slip** | | Når hjulet drejer uden at køretøjet flytter sig tilsvarende, fx på vådt græs. Gør hjul-odometri forkert |
| **DVL** | Doppler Velocity Log | Instrument på undervandsfartøjer, der sender lydstråler mod havbunden og måler farten med Doppler-effekten. Vores navigationsmodul er samme idé på land, med radar i stedet for lyd |
| **Land-DVL** | (vores arbejdsnavn) | Navigationsmodulet: GNSS + IMU + radar mod jorden + Kalman-filter |
| **Doppler-effekt** | | En bølges frekvens ændrer sig, når afsenderen bevæger sig (som lyden fra en ambulance, der kører forbi). Radar bruger det til at måle fart |
| **ENU** | East-North-Up | Et lokalt koordinatsystem i meter: x mod øst, y mod nord, z op. Lettere at regne i end længde- og breddegrader |
| **Lever arm** | (vægtarm) | Afstanden mellem to sensorer på køretøjet, fx fra IMU'en til GNSS-antennen. Skal måles og indregnes |

## Filtre og matematik

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **Kalman-filter** | (efter Rudolf Kálmán) | Matematisk metode, der kombinerer flere upræcise sensorer til ét bedste bud på position og fart, og samtidig ved hvor sikkert buddet er |
| **EKF** | Extended Kalman Filter | Udgave af Kalman-filteret, der kan håndtere ikke-lineære sammenhænge (fx drejninger). Det er den, vores kode bruger |
| **ESKF** | Error-State Kalman Filter | Variant, der estimerer fejlene i stedet for selve tilstanden. Standard i INS-systemer |
| **UKF** | Unscented Kalman Filter | En anden variant af Kalman-filteret |
| **Sensorfusion** | | At kombinere flere sensorer, så de dækker hinandens svagheder |
| **Kovarians / usikkerhed** | | Filterets eget tal for hvor sikkert det er. Små tal = sikker |
| **Gate / outlier-afvisning** | | Filteret afviser målinger, der er alt for langt fra det forventede (fx et multipath-spring) |
| **Allan-varians** | | Metode til at måle en IMU's støj og bias-vandring ud fra en lang optagelse, hvor den står stille |
| **Median / p90** | | Median = den midterste værdi. p90 = 90 % af målingerne er bedre end denne |

## Sensorer og radar

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **Radar** | Radio Detection And Ranging | Sender radiobølger og måler ekkoet: afstand, retning og fart |
| **mmWave** | millimeter-wave | Radar ved meget høj frekvens (60–80 GHz). Små, billige chips, der kan måle fart præcist |
| **TI** | Texas Instruments | Firmaet, der laver de radarchips (fx IWR6843), vi vil bruge |
| **EVM** | Evaluation Module | Et udviklingskit: chippen på et færdigt print, klar til at afprøve |
| **Lidar** | Light Detection And Ranging | Som radar, men med laserlys. Laver et "billede" af omgivelserne. Sidder på M1-robotten |
| **ToF** | Time of Flight | Måling af afstand ud fra hvor lang tid lyset er om at komme tilbage |
| **FOV** | Field Of View | Synsfelt: hvor bredt en sensor kan se |
| **UWB** | Ultra-Wideband | Radioteknik til præcis afstandsmåling mellem små sendere (beacons). Bruges fx af Ecovacs-plæneklippere |
| **Beacon** | | Lille fast sender, der står i haven og hjælper robotten med at finde sin position |
| **Dybdekamera** | | Kamera, der også måler afstanden til hver pixel. M1 har et (Nuwa-HP60C) |

## Robotsoftware

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **ROS 2** | Robot Operating System 2 | Standard-software til robotter: deler data mellem programmer og har færdige værktøjer. Ikke et rigtigt styresystem |
| **Humble / Jazzy** | | Navne på ROS 2-versioner. M1 kører Humble |
| **Nav2** | Navigation 2 | Den færdige navigationspakke i ROS 2: planlægger ruter og undviger forhindringer |
| **SLAM** | Simultaneous Localization And Mapping | Robotten tegner et kort og finder sig selv på kortet samtidig |
| **VSLAM** | Visual SLAM | SLAM med kamera |
| **AMCL** | Adaptive Monte Carlo Localization | Metode i Nav2 til at finde robotten på et kort, den allerede har |
| **URDF** | Unified Robot Description Format | Fil, der beskriver robottens form og hvor sensorerne sidder |
| **Coverage planning** | | At planlægge en rute, der dækker hele plænen (som en plæneklipper) |
| **YOLO** | You Only Look Once | Populær AI-model til at finde ting i billeder, fx ukrudt |
| **OWL** | OpenWeedLocator | Open source ukrudtsfinder med Raspberry Pi, kamera og sprøjteventiler |
| **Mock data / simulering** | | Falske, men realistiske data fra en computer, så man kan udvikle software før hardwaren findes |
| **Log** | | Optagelse af alle sensordata fra en tur, gemt i filer |
| **CSV** | Comma-Separated Values | Simpel tabelfil, der kan åbnes i Excel |

## Elektronik og hardware

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **MCU** | Microcontroller Unit | Lille computer på én chip, der styrer hardware i realtid (fx STM32, Raspberry Pi Pico) |
| **STM32** | | En familie af mikrocontrollere fra firmaet ST |
| **Jetson Orin Nano** | | Kraftig lille computer fra NVIDIA med grafikkort til AI. Sidder i M1 |
| **GPIO** | General Purpose Input/Output | Ben på en chip, der kan tænde/slukke ting eller læse signaler |
| **USB / UART / SPI / I²C / CAN** | (forskellige forbindelser) | Måder elektronik taler sammen på: USB som på en PC; UART = simpel seriel; SPI og I²C = korte forbindelser mellem chips; CAN = robust bus i biler og maskiner |
| **NMEA** | National Marine Electronics Association | Standard tekstformat, som GNSS-modtagere sender position i |
| **FOC** | Field-Oriented Control | Smart måde at styre elmotorer på, så de kører jævnt og effektivt |
| **ESC** | Electronic Speed Controller | Motorstyring: elektronikken, der driver en motor |
| **PCB** | Printed Circuit Board | Printkort: det grønne kort, elektronikken sidder på |
| **SSD** | Solid State Drive | Hurtig harddisk uden bevægelige dele |
| **IP54 / IP67** | Ingress Protection | Tæthedsklasse. IP54 = tåler sprøjt; IP67 = tåler at blive dyppet i vand |
| **Mecanum-hjul** | | Hjul med små skrå ruller, så robotten kan køre sidelæns. M1 har dem |
| **Ackermann-styring** | | Styring som i en bil, hvor forhjulene drejer |
| **4WS** | Four-Wheel Steering | Alle fire hjul kan dreje (v1-designet) |
| **Hub-motor** | | Motor, der sidder inde i selve hjulet, som på et hoverboard |

## Udvikling og projekt

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **Git / branch** | | Versionsstyring af kode. En branch er en parallel kopi, man arbejder på uden at ødelægge hovedversionen |
| **PR** | Pull Request | Forslag om at flette ændringer fra én branch ind i en anden. Kan gennemgås, før de merges |
| **Merge** | | At flette ændringerne ind |
| **CI** | Continuous Integration | Automatisk test, der kører hver gang der laves en PR. "Grøn" = alt bestod |
| **Repo** | Repository | Projektets mappe med al kode og dokumentation på GitHub |
| **MVP** | Minimum Viable Product | Den mindste version, der faktisk virker og er brugbar |
| **F0, F1 …** | Fase 0, fase 1 … | Faserne i køreplanen for navigationsmodulet |

## Forretning og regler

| Ord | Står for | Hvad det betyder |
|---|---|---|
| **B2B** | Business to Business | Salg til virksomheder i stedet for til privatpersoner |
| **OEM** | Original Equipment Manufacturer | Producent, der bygger en komponent ind i sit eget produkt (fx en plæneklipper-fabrik, der køber vores modul) |
| **LOI** | Letter Of Intent | Hensigtserklæring: et skriftligt "vi vil gerne købe, hvis …" |
| **Pilot** | | Et prøveforløb hos en kunde, ofte betalt |
| **RaaS** | Robot as a Service | Kunden betaler for arbejdet (fx pr. km), ikke for selve robotten |
| **BOM** | Bill Of Materials | Styklisten: alle dele og hvad de koster |
| **CAGR** | Compound Annual Growth Rate | Hvor mange procent et marked vokser om året i gennemsnit |
| **CE-mærkning** | | EU-krav om at et produkt overholder sikkerhedsreglerne, før det må sælges |
| **IP (rettigheder)** | Intellectual Property | Rettigheder til opfindelser og kode (ikke det samme som IP-tæthedsklassen) |
| **MST** | Miljøstyrelsen | Den danske myndighed for bl.a. sprøjtemidler |
| **KL** | Kommunernes Landsforening | Kommunernes fælles organisation |
| **MUDP / Innobooster / ESA BA** | (støtteordninger) | Offentlige puljer, man kan søge penge fra til udvikling |
