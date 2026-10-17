# Probedruck-Ergebnisse

## Rückmeldung vom 17. Oktober 2026

Der Benutzer hat die Testplatte der einfarbigen v2 beurteilt. Die Ergebnisse sind subjektive Praxisbeobachtungen mit dem vorhandenen LED-Kit; Filamentmarke, LED-Abstand und Umgebungslicht wurden nicht protokolliert.

| Probe | Rückmeldung | Konsequenz |
|---|---|---|
| Offener LED-Passring, innen Ø 60 mm | „passt perfekt, kabel hat genügend platz“ | Durchmesser der LED-Aufnahme beibehalten. V4.1 nutzt dieselbe Ringgeometrie; der gesamte Kabelweg im montierten Gehäuse bleibt separat zu prüfen. |
| Lichtproben 0,6 / 0,8 / 1,0 / 1,2 mm | „0.6 wirkt am besten. ich sehe da keine leds und die helligkeit ist gut.“ | V4.1 erhält 0,6 mm starke Seitenflächen. |
| Lange Steckproben der v2 | Keine Rückmeldung | Keine Aussage zur Passung. V4.1 verwendet andere Führungen und hat eine eigene Passprobe. |

Die v2-Testplatte und die archivierten v2-Druckdateien bleiben unverändert. Die kleine Lichtprobe besitzt ein einfarbiges, innen auftragendes Logo und sagt noch nichts über die realen AMS-Logofarben aus.

## Übertragung auf v4.1 (historischer Stand)

- Weiße Leuchtfläche: **0,6 mm**, entsprechend drei 0,20-mm-Schichten.
- Bündige Logo-Einlage: weiterhin **0,4 mm Farbe**, dahinter jetzt **0,2 mm Weiß**. Zum damaligen Zeitpunkt war dieser Schichtaufbau noch nicht physisch geprüft.
- Die inneren Führungen behalten Position, Profil und 2,8 mm Gesamttiefe. Ein schmaler innerer Hals verbindet sie mit der dünneren Leuchtfläche. Rahmen, Boden, Deckel und Füße bleiben gegenüber v4 geometrisch unverändert.
- Durch die dünnere Seitenplatte wächst die obere Montagefuge von 0,8 auf 1,0 mm. Die äußeren Seitenflächen bleiben plan; das Gesamtmaß bleibt 150 × 150 × 150 mm.

## Weitere Rückmeldung: AMS und Violett

Der Benutzer meldet den AMS-Druck als technisch in Ordnung; die harten drei Farbbänder gefallen ihm nicht. Ein gerasterter Verlauf liegt als separater Gestaltungsvorschlag vor. Das verwendete **3DJake ecoPLA Purple** wirkt ohne Hinterleuchtung zu hell für den Übergang und mit LED dahinter fast schwarz. Das spricht für geringe Lichtdurchlässigkeit im bisherigen Aufbau, ist aber noch keine isolierte Materialmessung. Eine Kaufentscheidung nur nach dem Oberflächenfarbton genügt deshalb nicht.

Anschließend wurde der [Schichtvergleich mit 0,2 und 0,4 mm Farbe](LICHTVERGLEICH.md) ausgeführt. Beide Varianten besitzen insgesamt 0,6 mm Materialstärke.

## Entscheidung nach dem Schichtvergleich — v4.2

Rückmeldung: „wir sollten für rot, violett und blau 0.2 verwenden. violett sieht viel besser aus.“

V4.2 verwendet deshalb **0,2 mm Farbe + 0,4 mm Weiß** für Rot, Violett und Blau. Die 0,6-mm-Gesamtdicke und die äußere Geometrie bleiben erhalten. Die subjektive Verbesserung von Violett ist bestätigt; dies ist keine quantitative Transmissionsmessung und noch kein Test des vollständigen Logos. Das ecoPLA-Purple-Profil mit 210 °C aus der Vergleichskarte wird für alle AMS-Projekte übernommen.

## Noch zu prüfen

1. **Logo mit gewähltem Aufbau:** Die Wirkung von 0,2 mm Farbe + 0,4 mm Weiß am vollständigen Logo beurteilen. Dafür liegt jetzt die [Rasterprobe 09 in Originalgröße](RASTERPROBE.md) geslict vor. Raster und Leuchtwirkung sind noch nicht physisch beurteilt.
2. **Führungs-Passprobe:** Der Plattenstreifen soll von oben ohne Gewalt in die Nut gleiten und seitlich gehalten werden.
3. **Ein Rahmen und eine vollständige Seitenplatte:** Ebenheit, Handhabung der dünnen Platte, Passung über die gesamte Führungslänge und Schatten der inneren Leisten beurteilen. Danach die übrigen drei Seitenplatten drucken.
4. **Komplette Lampe:** Gleichmäßigkeit der Beleuchtung, Kabelverlauf sowie Temperaturen bis zum stabilen Betriebszustand prüfen.

Die positive Rückmeldung zur kleinen Lichtprobe bestätigt weder die Stabilität der großen Seitenplatte noch das Wärmeverhalten der vollständigen Lampe.
