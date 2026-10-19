# myAI Cube

Eine kleine Würfellampe zum Selberdrucken: weißes PLA, sanftes Licht und das myAI-Logo mittig auf allen vier Seiten. Entwickelt für den **Bambu Lab P1S** und das **LED Lamp Kit 001 / MH001**.

![myAI Cube v4.2: durchgehend plane Seiten mit integrierten farbigen Logos](output/multicolor_v4_2/preview/assembled.png)

*Technische Farbansicht der CAD-Geometrie: Die Logos zeigen die nominellen sRGB-Farben ohne Aufhellung durch Beleuchtung. Keine Vorhersage realer Filamentfarben oder Lichtwirkung.*

## Die Idee

Ein **15 × 15 × 15 cm** großer Würfel mit **0,6 mm dünnen Leuchtflächen**, integrierten Logos, Boden mit LED-Aufnahme und abnehmbarem Deckel. Für das Logo gibt es eine farbige AMS-Variante und eine einfarbige Alternative.

## Plane Seiten mit AMS — v4.2

**Vier vollflächige Seitenplatten, außen ohne Vertiefungen oder vorstehende Rahmen.** Die Befestigung liegt innen; nur schmale Montagefugen bleiben an den Würfelkanten. Die 0,6-mm-Leuchtflächen und Logos sind bündig. Innenliegende Führungsleisten erlauben das Einschieben von oben.

**Für ein AMS mit vier Farben:** Weiß, Blau, Violett und Rot. Sterne und Schriftzug „myAI“ folgen Rot → Violett → Blau als feste Farbstufen. Vier Farbwechsel pro Platte. [Farbvergleich mit den Original-SVGs](output/multicolor_v4_2/preview/color_reference.png).

Luft und Kabel führen unter dem Boden hindurch. Vier 4-mm-Druckfüße schaffen Abstand; die Gesamthöhe bleibt **150 mm einschließlich Füßen**. Die obere Entlüftung liegt in der 1,0-mm-Deckelfuge auf der Oberseite. Die Füße werden eingesteckt und angeklebt; die Seitenplatten kommen ohne Klebstoff aus.

[Druckdateien & Montage v4.2](docs/MEHRFARBIG_V4.md) · [Farbprobe](output/multicolor_v4_2/print/01_color_test_P1S.3mf) · [Führungs-Passprobe](output/multicolor_v4_2/print/07_fit_P1S.3mf) · [Komplettpaket v4.2](output/myAI_Cube_150_P1S_AMS_v4_2.zip)

Zehn vorbereitete P1S-Projekte einschließlich Vergleichstests, keine Stützen. Lampe ohne Proben laut Slicer etwa **241 g PLA und 16 h 10 min**. Der [Schichtvergleich](docs/LICHTVERGLEICH.md) ist abgeschlossen: **0,2 mm Farbe + 0,4 mm Weiß** für alle drei Logofarben. Die neue Führung separat mit der Passprobe prüfen. [Frühere AMS-Variante v3](docs/MEHRFARBIG_V3.md).

**Der [2-mm-Rasterentwurf](docs/RASTERPROBE.md) ist optisch verworfen. Nicht drucken.** Die Vorschau zeigt die tatsächliche grobe Farbaufteilung, die der Benutzer als No-Go abgelehnt hat. Zusätzlich besteht der Entwurf die vollständige Flächenprüfung nicht. Die Dateien bleiben als Studie erhalten; derzeit gibt es keine empfohlene Raster-Druckdatei. Die regulären Seitenplatten verwenden weiterhin die bisherigen festen Farbbänder.

**[Testkarte 11: gerade 0,48-mm-Farbbahnen](docs/FARBBAHNEN_TEST.md)** ist erstellt und mit Bambu Studio geprüft. Neue Palette: Weiss, Blau, Cyanblau, Rot. Auch nach vier Profileinstellungen bleiben rechnerische Lücken; die beste Variante nach gesamter Lückenfläche liegt bei **0,72 %**. Die Datei ist zur Prüfung enthalten, **nicht als lückenfreier Probedruck freigegeben**.

**[Weiterentwicklung: 0,44-mm-Streifen mit gerundeten Enden](docs/FARBBAHNEN_VERFEINERT.md)**: feinere Bänder, aber sichtbare Randänderungen und weiterhin Restlücken. Sieben neue Slicer-Läufe; beste nominelle Lückenfläche **0,55 %**. **Keine Druckempfehlung.** Der Vergleich und die Prüfdatei sind dokumentiert.

**Stand: Prototyp.** Die einfarbige Lichtprobe mit 0,6 mm überzeugt beim Probedruck: gute Helligkeit ohne sichtbare einzelne LEDs. LED-Passring und Kabel passen. Violett wirkt mit 0,2 mm Farbeinlage laut Vergleichstest deutlich besser. Die komplette Montage, das vollständige Logo mit diesem Aufbau und das Temperaturverhalten bleiben zu prüfen. [Probedruck-Ergebnisse](docs/PROBEDRUCKE.md).

## Einfarbige Variante v2 drucken

Die ursprüngliche Variante besteht aus Körper, Boden und Deckel. Das innen verstärkte Logo soll sich im Licht dunkler abzeichnen; kein AMS erforderlich. Diese Variante besitzt noch sichtbare Lüftungsöffnungen.

Die 3MF-Projekte sind ausgerichtet und für **P1S · 0,4-mm-Düse · weißes PLA · strukturierte PEI-Platte** vorbereitet. In Bambu Studio **als Projekt** öffnen, eigenes Filament und Druckplatte prüfen und bei Änderungen neu slicen.

| Zuerst testen | Danach die Lampe drucken |
|---|---|
| [Testplatte: Licht und Passung](output/print/01_tests_P1S.3mf) | [Körper](output/print/02_body_P1S.3mf) · [Boden](output/print/03_base_P1S.3mf) · [Deckel](output/print/04_lid_P1S.3mf) |

**Druckprofil:** 0,20-mm-Schichten, keine Stützen. Die Hauptteile benötigen laut Slicer etwa **238 g PLA und 15 h 42 min**. LED-Kit und eine passende 5-V-USB-Stromversorgung kommen dazu.

**Archiv v2:** Die Dateien behalten 0,8 mm Körperwand. Die zugehörige Testplatte wurde gedruckt; 0,6 mm wurde dabei für die neue v4.1 gewählt. Ergebnisse und offene Prüfungen stehen im [Probedruck-Protokoll](docs/PROBEDRUCKE.md).

## Weiterbauen

- [Druck & Montage](docs/DRUCK_UND_MONTAGE.md) — vom Probedruck zur fertigen Lampe.
- [Projektdetails](docs/PROJEKTDETAILS.md) — Maße, Druckzeiten, Aufbau und Quellen.
- [CAD & Validierung](docs/CAD_UND_VALIDIERUNG.md) — Konstruktion reproduzieren und prüfen.
- [STL-Dateien](output/stl) · [CAD-Parameter](cad/parameters.json) · [Generator](cad/build.py) — für eigene Anpassungen.
