# Rasterprobe 10 — verworfener 2-mm-Entwurf

**Status: am 18. Oktober 2026 anhand der Vorschau optisch verworfen. Nicht drucken.** Der Benutzer lehnt die grobe Farbaufteilung als klares No-Go ab. Das rechte Bild zeigt die tatsächlich vorgesehenen Farbflächen: Die großen weißen Rasterfelder gehören zum Entwurf und sind kein Darstellungsfehler. Die geringere rechnerische Lückenfläche rechtfertigt diese Verschlechterung des Logos nicht. Zusätzlich ist die vollständige Flächenprüfung weiterhin nicht bestanden. Kein physischer Test dieses Entwurfs; kein Übertrag auf die Lampenseiten. Dateien und Prüfungen bleiben ausschließlich zur Nachvollziehbarkeit erhalten.

[Archivdatei — nicht drucken](../output/multicolor_v4_2/print/10_raster_original_test_P1S.3mf) · [Prüfbericht](../output/multicolor_v4_2/raster_original_test/surface_coverage.json)

![Original-SVG und gröberer Entwurf](../output/multicolor_v4_2/preview/raster_original_comparison.png)

*Nominelle Bildschirmfarben, keine Vorhersage realer Filamentfarben oder Hinterleuchtung. Weiße Rasterfelder sind beabsichtigt. Die Darstellung zeigt die CAD-Flächen, keine zugesicherte Druckqualität.*

## Befund am bisherigen Druck

Das Foto der alten Probe 09 zeigt helle Stellen besonders an Rasterübergängen in Sternen und Schrift. Es gab keine sichtbaren Rückstände auf der noch lauwarmen Druckplatte. Ein Abreißen beim Ablösen ist damit nicht bewiesen. In den Druckbahnen lassen sich unabhängig davon unbedeckte Bereiche nachweisen; diese sind eine plausible Erklärung für einen Teil der sichtbaren Stellen. Glanz, mechanische Aufhellung und echte Schichttrennung lassen sich aus dem Foto nicht sicher ausschließen.

Die bisherige Prüfung kontrollierte nur den zentralen Bereich vollständiger Rasterzellen. Sie übersah Lücken zwischen den Bahnen und an angeschnittenen Zellen. Auch die erste Version der Probe 10 mit 0,8-mm-Raster war damit nicht ausreichend geprüft. Das Umdrehen auf die weiße Rückseite beseitigt solche Lücken nicht.

Die neue Prüfung schneidet **die vollständigen Materialflächen aus den exportierten STL-Dateien** und vergleicht sie mit den tatsächlichen G-Code-Bahnen einschließlich Linienbreite, runden Bahnenden und Kreisbögen. Gewollte weiße Rasterfelder zählen nicht als fehlende Farbe. Die Prüfung betrachtet zusätzlich die richtige Farbe und beide weißen Rückschichten.

| Variante | Rechnerisch unbedeckte Farbfläche | Physisch beurteilt |
|---|---:|---|
| Alte Probe 09, 0,8 mm | rund 3,3 % | ja, weiße Stellen und Farbwirkung beanstandet |
| Frühere Probe 10, 0,8 mm | rund 3,6 % | nein |
| Neuer 2-mm-Entwurf | **0,78 % / 13,08 mm²** | nein |

Das sind **geometrische Modellwerte, keine Messungen am Druck**. Selbst mit 0,03 mm rechnerischer Toleranz bleiben beim neuen Entwurf 5,08 mm² unbedeckt; die größte zusammenhängende Restfläche beträgt 0,20 mm². Die festgelegte Flächenprüfung wird weiterhin **nicht bestanden**. Eine geschlossene Farbfläche ist damit nicht nachgewiesen.

![Grün markiert rechnerische Restlücken, Weiß zeigt gewollte Rasterfelder und Hintergrund](../output/multicolor_v4_2/raster_original_test/surface_coverage.png)

*Grün markiert unbedeckte Farbflächen jenseits von 0,03 mm Toleranz. Die Markierung zeigt Lage und Verteilung, nicht die tatsächliche Sichtbarkeit unter LED-Licht.*

## Was am gröberen Entwurf geändert wurde

Der Benutzer hatte die vorhandene **0,4-mm-Düse behalten und ein gröberes Raster erproben** wollen. Daraufhin wurden die Zellen auf 2,0 statt 0,8 mm vergrößert. Die tatsächliche Originalkontur und die spätere Logo-Größe blieben erhalten. Die anschließende Ablehnung der Vorschau verwirft diesen konkreten Entwurf; sie ist keine generelle Aussage über alle Druckmöglichkeiten mit der 0,4-mm-Düse.

Am Rand werden Zellen, die nicht vollständig innerhalb einer um 0,45 mm zurückgesetzten Kontur liegen, mit der lokal vorherrschenden Logofarbe belegt. Dadurch entstehen weniger schmale Farbreste. Diese Vorgabe fließt in die Fehlerverteilung zurück, damit die entfernten weißen Flächen nicht einfach unberücksichtigt bleiben. Sie ist keine exakte farbmetrische Kompensation. Diagonale Verbindungen haben jetzt 0,28 mm Radius. Die blaue Geometrie besteht aus neun, die rote aus drei zusammenhängenden Körpern statt zuvor 22 beziehungsweise 23.

Der Verlauf stammt weiterhin aus **allen tatsächlichen Farbstopps der unveränderten dunklen Original-SVG**, separat für Sterne und Schrift. Die helle SVG besitzt einen einfarbigen Schriftzug. Das Raster verwendet Weiß, Blau und Rot; Violett wird bei der nominellen Palette nicht künstlich erzwungen und erscheint im Referenzfeld. Drei kleine Referenzfelder zeigen die realen Spulen Rot, Violett und Blau.

Das originale Cyan und Hellblau sind mit der nominellen Palette nur eingeschränkt erreichbar. Weiße Rasterfelder hellen auf, ersetzen aber keine passende Cyan-Farbe. Der gröbere Entwurf ist sichtbar körniger. Weder die Bildschirmansicht noch die Palettenrechnung sagen die Farbe realer, hinterleuchteter Filamente voraus.

## Archivierte Druckdaten des verworfenen Modells

- **P1S, 0,4-mm-Düse, PLA, strukturierte PEI-Platte und AMS.** Technische Daten zur Nachvollziehbarkeit, keine Druckempfehlung.
- Slots: **1 Weiß · 2 Blau · 3 Violett · 4 Rot**. EcoPLA Purple 210 °C, übrige PLA-Profile 220 °C, Bett 55 °C.
- **Weiße Rückseite unten, Sichtseite oben:** zwei weiße Schichten mit zusammen 0,4 mm, anschließend 0,2 mm Farbe beziehungsweise weiße Rasterfelder. Gesamtdicke 0,6 mm. Nicht spiegeln oder wenden.
- Karte **96,9 × 109,1 mm**, Logo **86,9 × 99,1 mm**. Raster 2,0 mm.
- Etwa **1 h 7 min und 10,64 g PLA**, einschließlich Reinigungsturm und Spülmaterial. Drei Farbwechsel, keine Stützen.
- Eigenes langsames Profil: klassische Wandbahnen, 0,4-mm-Linien auf der Farbseite, keine absichtliche Nahtlücke. Außenwände/Oberseite/Lückenfüllung 25 mm/s, Innenwände 30 mm/s, Vollfüllung 40 mm/s. Zusatzlüfter aus, Bauteillüfter nach den ersten beiden Schichten 50 %.

Für diesen Entwurf ist kein weiterer Probedruck vorgesehen. Die Ursache der weißen Stellen am früheren Druck bleibt teilweise offen. Bei einem späteren geeigneten Test lässt sie sich durch Fotos vor und nach dem Ablösen besser eingrenzen; die Platte dabei vollständig bis Raumtemperatur abkühlen lassen.

## Prüfung und Reproduktion

- Original-Farbstopps gegen CairoSVG geprüft: 2.899 innere Bildpunkte, höchstens 0,53 von 255 Kanalwerten Abweichung beim Einlesen der Quelle.
- Geschlossene Materialnetze, unveränderte Außenkontur und Größe, zusammenhängende Karte, Materialabdeckung und fehlende Volumenüberschneidungen geprüft. Zwei winzige Randinseln mit zusammen 0,01 mm² wurden benachbarten Farben zugeordnet.
- P1S-Projekt geslict; AMS-Zuordnung, Bettgrenzen, G-Code-Prüfsumme, Schichten und fehlender Stützbedarf geprüft. Die Mittelpunkte von 238 vollständigen Rasterzellen und drei Referenzfeldern sind abgedeckt. **Dieser erfolgreiche Teilcheck ersetzt die fehlgeschlagene Flächenprüfung nicht.**
- Die Flächenprüfung verwendet nominelle, abgerundete Bahnbreiten; Kreisbögen werden mit höchstens 0,001 mm Sehnenfehler angenähert. Sie simuliert weder Schmelzfluss noch reale Haftung, optische Deckung oder die Druckreihenfolge an überlappenden Farbgrenzen.
- Das konservative Freigabekriterium erlaubt nach 0,03 mm Toleranz höchstens 0,1 % fehlende Farbfläche und keine einzelne Restfläche über 0,01 mm². Es ist ein Entwicklungsfilter, keine kalibrierte Sichtbarkeitsschwelle. Die weiße Rückseite und die richtige Farbe werden ebenfalls geprüft. **Aktueller Status: nicht bestanden.**

[Geometrie](../output/multicolor_v4_2/raster_original_test/geometry_validation.json) · [Originalfarben](../output/multicolor_v4_2/raster_original_test/color_validation.json) · [Zellmitten](../output/multicolor_v4_2/raster_original_test/toolpath_validation.json) · [Flächenprüfung](../output/multicolor_v4_2/raster_original_test/surface_coverage.json) · [Alte Probe 09](RASTERPROBE_09.md).

```sh
.venv/bin/python cad/build_raster_original_test.py
.venv/bin/python scripts/validate_original_colors.py
.venv/bin/python scripts/slice_multicolor.py /pfad/zu/bambu-studio --plates 10_raster_original_test
.venv/bin/python scripts/test_raster_coverage.py
.venv/bin/python scripts/validate_multicolor.py
# Der letzte Befehl scheitert derzeit ausdrücklich an der Flächendeckung.
# Nur für ein Bestandsaudit mit dokumentierter, weiterhin fehlender Freigabe:
.venv/bin/python scripts/validate_multicolor.py --allow-withheld-raster
blender -b -t 4 --python scripts/render_raster_original_test.py
.venv/bin/python scripts/package.py
```

Bambu Studio 2.8.2.61. Die ältere Probe 09 und ihre Druckdateien bleiben archiviert. Die frühere 0,8-mm-Version der Probe 10 ist über Git-Commit `fcbab89` reproduzierbar. Auch der 2-mm-Entwurf ist **verworfen**. Es gibt derzeit keine empfohlene Raster-Druckdatei.
