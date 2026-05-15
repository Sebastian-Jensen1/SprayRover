# Obstacle Avoidance

## Existing systems

Obstacle Avoidance er også et emne som ikke er løst særlig godt i DIY miljøet.

Commercielle græsslåmaskiner som ikke bruger kabel i jorden, de bruger typisk Lidar + GPS.

Men den bedre/optimale løsning ville være at bruge en Radar med et phased array.
De løsninger er ikke rigtigt kommet til det almindelige maker marked endnu, så hvis vi bygger det - så er det en BIG THING.

Obstacle Avoidance i maker miljøet er mest single channel ultrasound og nogle få Radar typer også, men single channel. Dvs. On/Off, der er noget - i en vis afstand, men ikke detaljer og i en meget stor vinkel (80-120 grader). Det er ubrugeligt til vores behov.

## Plan phase 1

Brug Development Kit fra TI indtil videre, den generere 8 virtuelle kanaler i et lille array af 3 transmit of 4 receive kanaler, fra 60-64Ghz.
En MEGET godt ting er at deres reference design Antenne er bygget på billigt standard FP4 PCB substrat. Andre high-end systemer kræver specielle PCB typer som gør det meget vanskeligt at bygge selv.

Ulempen med denne er et meget stort Field Of View i det vertikale plan (80 grader). Ideelt skulle vi have kun 15-20 grader FOV, tætter på et 2D plan.

Vi kan bruge dette development kit out-of-the-box, med et USB interface.

## Plan phase 2

Når TI får rullet næste generation ud (er på vej) så skifter vi til den. Her får vi 16 virtuelle kanaler og bedre opløsning, i dette skift kan vi håbe på at de laver en model med mindre vertikal FOV, ellers kan selv bygge et PCB som har antenne elementerne lagt anderledes (hvis vi kan modellere det med TI tools).

## Design resourcer IWR6843LEVM

https://www.ti.com/tool/IWR6843LEVM

https://www.ti.com/lit/ug/swru585/swru585.pdf?ts=1694788452004&ref_url=https%253A%252F%252Fwww.ti.com%252Ftool%252FIWR6843LEVM%253FkeyMatch%253D%2526tisearch%253Dsearch-everything%2526usecase%253Dhardware

https://www.digikey.dk/da/products/detail/texas-instruments/IWR6843LEVM/18159132?s=N4IgTCBcDaIJIHUBKA2AHAFgMwBkCiAagLIgC6AvkA

## Rover implementation

2 units placed in a small enclosure in front and rear at an elevated point. Need calibration to the mechanical fit and FOV, in software we blank out large portions of the FOV in the vertical, where it has 80 degree opening angle.

Each powered and dat over USB-C, so host infrastructure need to include USB-C

Asume it will connect to an onboard computer, need probably high-end system like Raspberry PI, Jetson NANO or similar.
