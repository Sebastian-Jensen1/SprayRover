# Navigation

## Rover Design

Navigation er MEGA svært. Vi skal bruge Roveren i en have under træer og langs husmure. GPS har det med at "falde ud" og have problemer med multipaths i sådanne omgivelser og vi har brug for centimer nøjagtig position for at kunne køre præcist frem/tilbage langs med mure, græsplæne grænsen, genfinde ukrudt m.m.

Hvis vi kan løse Navigations udfordringen billigt, så er det et ekstremt hæderfuldt bidrag til Open Source community som ville gøre os berømte! - eller evt. kan vi bygge/sælge et produkt.


## Rover Navigation, "the standard solution"

For at komme igang hurtigt, så tager vi "standard løsningen".
U-Blox FP9 modulet i en Arduino formfactor.
https://www.ardusimple.com/product/simplertk3b-budget/

som har HAS support fra Galileo, det giver ca. 40 cm. nøjagtighed hvilket kunne være nok.
Alternativet er vi skal have en RTK base station på huset, det koster lige 250 EU mere så + kabling m.m.

Den er en ret dyr løsning, for vi skal både have det modul + en base station for korrektioner.

Jeg er ret glad for STM32 (ST Microsystems processorer), dette modul er kompatibelt med STM32 development kits, så kan vi bare køre med det!

F.eks. Nucelous med ethernet:
NUCLEO-H7S3L8
koster $51 pr. styk.


Så skal vi bruge en IMU i tillæg, og lave et lille navigations system ESKF kalman filter der skal køre i STM32'eren.

Vi skal overveje om vi skal have en større computer eller dele det i funktionelle moduler.


STM32H7
  ├── ZED-F9P via UART + PPS for timing (ardusimple modulet)
  ├── ICM-42688 via SPI (IMU fra TDK, skal findes i et færdigt modul helst)
  ├── UWB modules via SPI/UART (dette kan komme til i fase 2, det er mikrobølge positionering)
  ├── Wheel encoders via timer capture
  └── ESKF running at IMU rate (200-400Hz), aiding at lower rates (dette er INS systemet i software)


## Rover Navigation, "the smart UWB solution"

Vi har ikke her et krav om at den kan navigere "alle steder", så vi kunne lave et miniature Ultra Wideband Navigation system. Disse moduler er relativt billige, og det ville være meget innovativt. Vi har 40 cm. fra GPS,en, vi har en lille IMU og et INS ESKF Kalman filter system i software. Kan vi aide den med en UWB ranging, så bliver det meget præcist og robust.
Så kan Roveren køre hurtigt og overbevisende rundt på matriklen!




*********************** SENERE *******************

Jeg har en ide, baseret på det vi laver i firmaet til undervands brug. Men det er for stort et projekt at tage med til en start, vi kan evt. tage det op senere.


Et self-contained Navigations modul som består af:

1-2 GPS antenne, billigt, uden RTK eller Dual.antenna GNSS setup. Giver rough-position indenfor 1m
1 MEMS IMU
1 4-beams Doppler Radar
4 x motor feedback
1 x ARM processor med zephyr OS (f.eks. STM32)
og INS sensor fusion Software

Eksempel 2 x GPS antenner til 82 kr. !!
https://www.amazon.de/-/en/GY-NEO6MV2-Control-Ceramic-Antenna-Arduino/dp/B0DX1V4WS1/ref=sr_1_3?crid=3AWHCGQ2KGTIC&dib=eyJ2IjoiMSJ9.s4YOko11PIYMxUc-wvWYSwXuOXS2XBTzTtZIixorUNxHTdBQQw1DtyYGzuPR-rr1XKamKptCdIiod4JU-D1PB7zufSTUmF6xFCgHJSuUSMwWupW1EXfBaKsLJ2c4nDR42x74a7TZYX9lZgRyIczQ3pJV4GpI7i03Of1xt8hpCb-1xx0CZT38GKesJ_7tn872o22cFaOG_BXJxEDyL3hkuDOXay76JNbVmtvsf5cX1hs.sNcI5wgxJd0kaOi0C1MjQrTzpPCTGknF7rrk4WXXwtQ&dib_tag=se&keywords=DIY+GPS+receiver&qid=1778743797&sprefix=diy+gps+receiver%2Caps%2C137&sr=8-3


Eksempel IMU til 329 kr.
https://www.amazon.de/WT901B-Accelerometer-Gyroscope-Magnetometer-Barometer/dp/B07TD7N2DP/ref=sr_1_2_sspa?crid=10UBSO6LVN3UO&dib=eyJ2IjoiMSJ9.4OIOHQLWd_515N94nRTM6A.lOWkGenMzAjEiar6DrziKLZTRzpXaxynl_pk3WlEQO8&dib_tag=se&keywords=DIY+MEMS+IMU&qid=1778743870&sprefix=diy+mems+imu%2Caps%2C124&sr=8-2-spons&aref=ejvAyk713l&sp_csd=d2lkZ2V0TmFtZT1zcF9tdGY&psc=1


Doppler Radar til speed over ground detection, development kit er ret dyrt (+1.000 kr) men chipsettet er billigt, ca. 250 kr.
https://www.ti.com/tool/IWRL6844EVM

Chipsettet alene: https://www.digikey.dk/da/products/detail/texas-instruments/IWR6843ARQGALPR/15857294

Den gamle version er med 3 kanaler, hvilket ikke er optimalt, men vi kan udvikle konceptet på denne.
https://www.digikey.dk/da/products/detail/texas-instruments/IWR6843AOPEVM/12165115

Hvis vi kunne lave denne løsning, så er der penge i det. Men det er svært og Stort projekt!

INS softwaren er ikke triviel, men muligvis jeg kan få lidt hjælp til matematikken til dette af en kollega.
