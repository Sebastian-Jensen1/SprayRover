# Hardware

## Rover Design

Det mest almindelige Rover design til terrain-gående Rovers er baseret på NASA Mars Rover designet:
[nasa-jpl/open-source-rover](https://github.com/nasa-jpl/open-source-rover)

### 6-hjulet design (med drejelige hjul)

Den originale har 6 hjul der er individualt drejelige. Her er en variant med faste hjul:
[YouTube – Fixed wheel variant](https://www.youtube.com/watch?v=N7xY_O0PeXE)

> Den er meget dyr at bygge, men vil være det mest "proven" startpunkt.

### 4-hjulet design (simpelt og billigere)

Alternativet er en 4-wheeler, som er langt mere simpel og billigere at bygge – f.eks. dette tyrkiske projekt:
[ITU Rover Team](https://mkn.itu.edu.tr/en/students/project-teams/itu-rover-team)

**Eksempler:**
- [YouTube – ITU Rover eksempel](https://www.youtube.com/watch?v=4K8A91jxjwg)
- [YouTube – Alternativt design](https://www.youtube.com/watch?v=XiqmVLrzhZ0)

Jeg arbejder videre med 4-hjuls design med roterbare hjul.

### Servo mototer til at dreje hjulene individuelt og med seriel bus

Feetech STS321 ~€20 EUR, RS485 serial bus, daisy-chain all 4 til central computer

### Drive train motorer til at køre/skubbe egen rover + tools rover

Muligvis bedste mulighed er nok en "Hoverboard Hub Motor" i 10" størrelse
Der er motor og præcist feedback i samme enhed, færdiglavet plug-and-play
Skal bruge +250-350W hvis den skal kunne skubbe en græstrimmer. Ellers er 100W nok.
Forventer at vi skal skubbe med 150-200N, rough estimate
Vigtigt at den har luftfyldte dæk med dybe "offtrack" dækmønstre.
Købes på Alibaba eller Amazon

### FOC controller til at drive motorer

FOC Controller: ST B-G431B-ESC1
STMicro Electronics development kit. Kan altid senere lave eget PCB for cost-down, men denne er nem at starte med og er state-of-art. Har en UART com til central computer
https://www.st.com/en/evaluation-tools/b-g431b-esc1.html

Vi kan køre et Open Source closed loop PID controller på den som er sindssygt godt!!
Check dette ud: https://www.simplefoc.com/
Se deres demo videoer, dette virker out of the box med STM FOC controller hardware.
https://www.simplefoc.com/example_projects

STM page:
https://docs.simplefoc.com/stm32_mcu

