# Testkarte 11 — gerade 0,48-mm-Farbbahnen

**Erstellt und geslict, aber nicht als lückenfreier Probedruck freigegeben.** Vier Einstellungen wurden an derselben Geometrie geprüft; keine besteht die vollständige Flächenprüfung. Die Slicer-Datei bleibt zur Inspektion erhalten. Die vorherigen weissen Stellen sind damit nicht nachweislich behoben. Ein physischer Druck dieser Karte wurde noch nicht beurteilt.

[P1S-Prüfdatei — mit Restlücken](../output/line_gradient_test/print/11_line_gradient_test_P1S.3mf) · [Druckstatus](../output/line_gradient_test/print/STATUS.md) · [Druckprüfung](../output/line_gradient_test/print_validation.json) · [Flächenprüfung](../output/line_gradient_test/surface_coverage.json)

## Entwurf und Aufbau

![Tatsächliche Farbflächen der Testkarte](../output/line_gradient_test/preview/card.png)

Die Karte übernimmt die vom Benutzer zum Test freigegebene [Vorschau mit geraden 0,48-mm-Bahnen](../design_studies/line_gradient_fine/README.md), inklusive Originalkonturen, Farbstopps und Logogrösse. Keine Wellen, kein Kurzlinienraster, keine weissen Rasterfelder innerhalb des Logos. Die kleinen Felder unter dem Logo sind einfarbige Referenzen. Ein isoliertes Originalfragment am A mit nur rund 0,0005 mm² wurde wie angekündigt aus der Druckableitung entfernt. Sonst wurde die Farbaufteilung nicht zugunsten einer günstigeren Prüfung verändert.

| Eigenschaft | Einstellung |
|---|---|
| Drucker / Düse | Bambu Lab P1S / 0,4 mm |
| Platte | Strukturierte PEI-Platte, 55 °C; tatsächliche Platte vor Verwendung abgleichen |
| Karte | 96,88 × 109,14 × 0,60 mm |
| Schichten | Zweimal 0,20 mm Weiss, danach 0,20 mm Farbe und weisser Hintergrund |
| Orientierung | Weisse Rückseite auf dem Bett, Logo oben, leserichtig |
| AMS | **1 Weiss · 2 Blau · 3 Cyanblau · 4 Rot** |
| Materialprofil | Generic PLA, 220 °C; Cyan ist ein neues Material, nicht ecoPLA Purple |
| Kühlung | Zusatzlüfter aus; Bauteillüfter 50 % nach zwei Schichten |
| Ausgewählter Prozess | Klassische Wände, Dünnwand-Erkennung, nominell 0,4-mm-Linien |
| Slicer-Schätzung | Etwa **1 h 7 min / 10,65 g**, inklusive Spülmaterial und Reinigungsturm |
| Farbwechsel / Stützen | Drei Farbwechsel, keine Stützen |

0,48 mm bezeichnet die **entworfene Farbbandbreite**. Die tatsächlich vom Slicer erzeugten Linien sind davon zu unterscheiden. Der Prüfer liest ihre Breiten aus dem G-Code. Das Cyanprofil ist generisch; der Farbwert ist ein nomineller Zielwert und keine Messung eines bestimmten Filaments. Die regulären Lampenseiten behalten ihre bisherige Palette mit Violett.

## Ergebnis der Slicer-Prüfung

Bambu Studio **02.08.02.61** slict die Karte ohne Druckwarnungen. Geprüft sind geschlossene Materialkörper, gemeinsame Karte, vier explizite AMS-Zuordnungen, Bettgrenzen einschliesslich Brim/Reinigungsturm, Schichtfolge, fehlender Stützbedarf und G-Code-Prüfsumme. Fremdfarben werden nicht in die weisse Rückschicht gespült.

Die zusätzliche Flächenprüfung vergleicht die **gesamten CAD-Farbflächen** mit den tatsächlichen Extrusionsbahnen, einschliesslich variabler Linienbreiten, runder Enden und Kreisbögen. Sie prüft sowohl fehlende Abdeckung als auch fehlende richtige Farbe und beide weissen Rückschichten. Zellmitten oder eine erfolgreiche Slicer-Meldung allein genügen nicht.

| Profileinstellung | Nominell unbedeckte Farbfläche | Nach 0,03 mm Rechentoleranz | Grösste verbleibende Lücke |
|---|---:|---:|---:|
| Arachne, nominell 0,48-mm-Linien | 2,079 % | 1,071 % | 0,359 mm² |
| **Klassisch, nominell 0,4-mm-Linien — ausgewählt** | **0,720 %** | **0,338 %** | **0,412 mm²** |
| Arachne, 0,4 mm, geringere Mindestbreite / kürzerer Übergang | 1,805 % | 0,888 % | 0,199 mm² |
| Klassisch, nominell 0,3-mm-Linien | 1,001 % | 0,426 % | 0,082 mm² |

Alle vier Läufe verwenden dieselben Materialmeshes und die 0,4-mm-Düse. Die Auswahl minimiert die **gesamte nominelle Lückenfläche**, nicht die grösste Einzellücke. Profile, Dateihashes und Messwerte stehen in der [Versuchsübersicht](../output/line_gradient_test/profile_trials.json); Zwischenstände werden nicht als zusätzliche Druckempfehlungen ausgeliefert.

Beim ausgewählten Profil sind nominell **14,27 mm²** nicht durch Druckbahnen abgedeckt. Selbst nach 0,03 mm Rechentoleranz bleiben **6,71 mm²**. Bei Prüfung auf die richtige Farbe fehlen insgesamt 11,77 mm² jenseits dieser Toleranz. Vor allem schräg angeschnittene Streifenenden an der Logokontur bleiben problematisch. Auch die weissen Rückschichten überschreiten das konservative Kriterium für die grösste zusammenhängende Restfläche.

![Grün zeigt rechnerisch unbedeckte Farbfläche jenseits von 0,03 mm Toleranz](../output/line_gradient_test/surface_coverage.png)

Grün markiert die rechnerischen Restlücken; es ist keine zusätzliche Druckfarbe. Die Darstellung zeigt nicht sämtliche Stellen, an denen zwar Material, aber zu wenig der vorgesehenen Farbe liegt. Die vollständigen Werte stehen im JSON-Prüfbericht.

Die bestehenden Kriterien bleiben unverändert: höchstens 0,1 % Restfläche nach Toleranz und keine einzelne Lücke über 0,01 mm², zusätzlich für richtige Farbe und Rückschichten. Diese Grenzen sind konservative Entwicklungsfilter, keine kalibrierte Sichtbarkeitsschwelle. Die Rechnung simuliert weder Schmelzfluss noch Haftung, Druckreihenfolge an überlappenden Grenzen oder Hinterleuchtung. Trotzdem ist der digitale Befund ausreichend, um **keine geschlossene Farbfläche zuzusichern**.

## Konsequenz

Diese Datei ist eine **geslicte Prüfdatei mit dokumentierten Restlücken**, keine empfohlene Wiederholung des Probedrucks zur Fehlerbehebung. Für eine Freigabe müsste insbesondere die Umsetzung der Streifenenden verbessert und danach erneut geprüft werden. Ein solcher weiterer Geometrieentwurf ist nicht Bestandteil dieser Datei. Alle vier Lampenseiten bleiben unverändert.

## Reproduzieren

Vom Repository-Stamm mit einer Python-Umgebung gemäss `cad/requirements.txt`, zusätzlich Shapely für die bereits vorhandene Gestaltungsvorschau. Zum Bauen der Karte wird direkt deren gespeicherte SVG eingelesen; kein erneutes Rendern erforderlich.

```sh
python cad/build_line_gradient_test.py
python scripts/slice_line_gradient_test.py /pfad/zu/bambu-studio
python scripts/test_raster_coverage.py
python scripts/validate_line_gradient_test.py
# Erwartetes Ergebnis: Fehlerstatus wegen Restlücken.
# Nur für ein Audit der weiterhin nicht freigegebenen Datei:
python scripts/validate_line_gradient_test.py --allow-withheld
python scripts/package.py
```

Für Profilvergleiche nimmt das Slicing-Skript `--process /pfad/zu/override.json` entgegen. Es überschreibt ausschliesslich das eigene Testprojekt. Nach neuem CAD oder Slicing werden bisherige Freigabeberichte ungültig gemacht. Das unveränderte ältere Rasterprojekt 10 bleibt separat verworfen.
