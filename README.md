# myAI Cube

Eine kleine Würfellampe zum Selberdrucken: weißes PLA, sanftes Licht und das myAI-Logo mittig auf allen vier Seiten. Entwickelt für den **Bambu Lab P1S** und das **LED Lamp Kit 001 / MH001**.

![myAI Cube v3.2.1: integrierte farbige Logos und verdeckte Belüftung](output/multicolor_v3/preview/assembled.png)

*Technische Farbansicht der CAD-Geometrie: Die Logos zeigen die nominellen sRGB-Farben ohne Aufhellung durch Beleuchtung. Keine Vorhersage realer Filamentfarben oder Lichtwirkung.*

## Die Idee

Ein **15 × 15 × 15 cm** großer Würfel mit **0,8 mm dünnen Leuchtflächen**, integrierten Logos, Boden mit LED-Aufnahme und abnehmbarem Deckel. Für das Logo gibt es eine farbige AMS-Variante und eine einfarbige Alternative.

## Mehrfarbig mit AMS — v3.2.1

**Für ein AMS mit vier Farben:** Weiß, Blau, Violett und Rot. Vier identische Paneele mit bündig mitgedruckten Logos gleiten in einen weißen Rahmen. **Sterne und Schriftzug „myAI“ folgen Rot → Violett → Blau**, als feste Farbstufen entlang der Verlaufsrichtungen aus der dunklen Original-SVG. Sechs Farbwechsel pro Paneel; Montage ohne Aufkleben der Logos.

[Farbvergleich mit beiden Original-SVGs](output/multicolor_v3/preview/color_reference.png): Rot und Blau entsprechen Originalfarbwerten; Violett ist eine gewählte Zwischenfarbe. V3.2.1 korrigiert die zuvor zu helle Vorschau, die Druckdateien bleiben identisch zu v3.2.

Die Belüftung ist verdeckt: Lufteinlässe unter dem Boden, vier 2-mm-Druckfüße und Auslässe hinter der Deckelblende. Die Seiten haben keine sichtbaren Lüftungslöcher, die Deckelfläche ist geschlossen. **150 mm Gesamthöhe einschließlich Füßen.** Die Füße werden eingesteckt und mit etwas Klebstoff fixiert.

[Druckdateien & Montage v3.2.1](docs/MEHRFARBIG_V3.md) · [Kleine Farbprobe](output/multicolor_v3/print/01_color_test_P1S.3mf) · [Komplettpaket v3.2.1](output/myAI_Cube_150_P1S_AMS_v3_2_1.zip)

**Stand: Prototyp.** Digital geprüft und geslict. Physischer Probedruck und Temperaturtest stehen noch aus.

## Einfarbige Variante v2 drucken

Die ursprüngliche Variante besteht aus Körper, Boden und Deckel. Das innen verstärkte Logo soll sich im Licht dunkler abzeichnen; kein AMS erforderlich. Diese Variante besitzt noch sichtbare Lüftungsöffnungen.

Die 3MF-Projekte sind ausgerichtet und für **P1S · 0,4-mm-Düse · weißes PLA · strukturierte PEI-Platte** vorbereitet. In Bambu Studio **als Projekt** öffnen, eigenes Filament und Druckplatte prüfen und bei Änderungen neu slicen.

| Zuerst testen | Danach die Lampe drucken |
|---|---|
| [Testplatte: Licht und Passung](output/print/01_tests_P1S.3mf) | [Körper](output/print/02_body_P1S.3mf) · [Boden](output/print/03_base_P1S.3mf) · [Deckel](output/print/04_lid_P1S.3mf) |

**Druckprofil:** 0,20-mm-Schichten, keine Stützen. Die Hauptteile benötigen laut Slicer etwa **238 g PLA und 15 h 42 min**. LED-Kit und eine passende 5-V-USB-Stromversorgung kommen dazu.

**Stand: Prototyp v2.** Geometrie und Slicing sind geprüft; ein physischer Probedruck steht noch aus. Deshalb zuerst Lichtdurchlässigkeit und Passung mit der Testplatte prüfen.

## Weiterbauen

- [Druck & Montage](docs/DRUCK_UND_MONTAGE.md) — vom Probedruck zur fertigen Lampe.
- [Projektdetails](docs/PROJEKTDETAILS.md) — Maße, Druckzeiten, Aufbau und Quellen.
- [CAD & Validierung](docs/CAD_UND_VALIDIERUNG.md) — Konstruktion reproduzieren und prüfen.
- [STL-Dateien](output/stl) · [CAD-Parameter](cad/parameters.json) · [Generator](cad/build.py) — für eigene Anpassungen.
