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

## Rückmeldung zur Rasterprobe — 18. Oktober 2026

Die Farbqualität der Probe 09 ist ungenügend. Gewünscht ist eine Neuberechnung aus den tatsächlichen Originalfarben. Die alte Probe verwendete zwar Originalkonturen und -richtungen, aber künstliche Rot–Violett–Blau-Farbstopps. Dieser Fehler wird in [Probe 10](RASTERPROBE.md) korrigiert; die Original-SVG bleibt unverändert. Die vorhandene Palette kann das originale Cyan weiterhin nicht exakt wiedergeben.

Beim Ablösen erscheinen einzelne Farbstellen weggerissen und Weiß scheint durch. Rückfrage: **keine sichtbaren Rückstände auf der Platte**, Platte **noch lauwarm**. Der Plattentyp ist nicht bestätigt. Echter Materialverlust, Drucklücken und Spannungsaufhellung sind noch nicht voneinander unterschieden. Eine sichere Ursache lässt sich daraus nicht ableiten.

Das nachgereichte Foto zeigt helle Stellen insbesondere an Rasterübergängen in Sternen und Schrift. Die neue Prüfung der gesamten Fläche findet auch in den Druckbahnen der Probe 09 Lücken: nominell etwa 3,3 % der Farbfläche. Das stützt Drucklücken als mögliche Ursache, beweist aber nicht die Ursache jedes hellen Fotopunkts. Die bisherige Prüfung der Zellmitten war unzureichend.

Die erste Probe 10 mit 0,8-mm-Raster hatte ebenfalls digitale Restlücken; ihre Druckempfehlung ist zurückgenommen. Der Benutzer möchte die **0,4-mm-Düse behalten und ein gröberes Raster erproben**. Der neue 2-mm-Entwurf verwendet breitere diagonale Verbindungen und einen zusammenhängenden Farbrand an der Kontur. Die nominell unbedeckte Farbfläche sinkt auf 0,78 %, bleibt aber vorhanden. **Die vollständige Flächenprüfung ist weiterhin nicht bestanden; keine bestätigte Fehlerbehebung und kein physischer Test des neuen Entwurfs.**

**Anschließende Beurteilung der Vorschau:** Der Benutzer lehnt das rechte Bild mit der groben 2-mm-Farbaufteilung als „klares no go“ ab. Das Bild zeigt die tatsächlich vorgesehenen Farbflächen. Der Entwurf ist deshalb optisch verworfen und soll nicht gedruckt werden. Diese Rückmeldung betrifft die Bildschirmvorschau, keinen physischen Druck. Die 0,4-mm-Düse und der gewählte Schichtaufbau bleiben Anforderungen.

## Noch zu prüfen

**Neuer digitaler Prüfstand:** Die Vorschau mit Cyanblau und geraden 0,48-mm-Farbbahnen wurde anschliessend vom Benutzer zum Test freigegeben. Die [Testkarte 11](FARBBAHNEN_TEST.md) ist erstellt und geslict. Vier Profileinstellungen wurden geprüft; keine besteht die vollständige Flächenprüfung. Die ausgewählte Variante lässt nominell rund 0,72 % der Farbfläche rechnerisch unbedeckt. Kein physischer Test dieser Karte und keine bestätigte Behebung der weissen Stellen. Wellen und Kurzlinienraster sind verworfen.

1. **Logo mit gewähltem Aufbau:** Flächenschluss und Farbumsetzung sind noch ungelöst. Der [2-mm-Entwurf 10](RASTERPROBE.md) ist nach Sichtung der Vorschau verworfen; kein weiterer Druck dieser Variante. Derzeit gibt es keine empfohlene Rasterprobe. Die verworfene Probe 09 wurde physisch beurteilt, Probe 10 nicht.
2. **Führungs-Passprobe:** Der Plattenstreifen soll von oben ohne Gewalt in die Nut gleiten und seitlich gehalten werden.
3. **Ein Rahmen und eine vollständige Seitenplatte:** Ebenheit, Handhabung der dünnen Platte, Passung über die gesamte Führungslänge und Schatten der inneren Leisten beurteilen. Danach die übrigen drei Seitenplatten drucken.
4. **Komplette Lampe:** Gleichmäßigkeit der Beleuchtung, Kabelverlauf sowie Temperaturen bis zum stabilen Betriebszustand prüfen.

Die positive Rückmeldung zur kleinen Lichtprobe bestätigt weder die Stabilität der großen Seitenplatte noch das Wärmeverhalten der vollständigen Lampe.
