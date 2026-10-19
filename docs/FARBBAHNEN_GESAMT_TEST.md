# Testkarte 13 — variable gerade Streifen im gesamten Logo

**Testdatei erstellt und geslict; die vollständige Flächenprüfung ist nicht bestanden.** Die akzeptierte Gesamtvorschau wurde unverändert für den **P1S mit 0,4-mm-Düse** umgesetzt. Auch nach fünf Bahneinstellungen bleiben digitale Lücken. Die Datei ist zur Prüfung verfügbar, nicht als lückenfreier Probedruck freigegeben.

**Spätere Rückmeldung:** Fotos des Probedrucks zeigen störende weisse Streifen. Die [anschliessende Untersuchung von 20 weiteren Profileinstellungen](LUECKENSCHLUSS_PRUEFUNG.md) findet ebenfalls keine ausreichend geschlossenen Farbflächen. Die folgende Dokumentation beschreibt den ursprünglichen Auslieferungsstand; keine neue Druckfreigabe.

[P1S-Testdatei mit Restlücken](../output/line_gradient_full/print/13_full_line_test_P1S.3mf) · [Druckprüfung](../output/line_gradient_full/print_validation.json) · [Flächenprüfung](../output/line_gradient_full/surface_coverage.json) · [Profilvergleich](../output/line_gradient_full/profile_trials.json)

![CAD-Farbaufteilung der Testkarte, keine Simulation des Druckergebnisses](../output/line_gradient_full/preview/card.png)

## Unveränderte Gestaltung

Die Farbvolumen werden direkt aus der akzeptierten [Gesamtvorschau](../design_studies/line_gradient_full/README.md) extrudiert. Alle Übergänge in Sternen und Schrift verwenden variable, durchgehend gerade Farbbänder ab nominell **0,32 mm vor Konturbeschnitt**. An der Logokontur können kleinere Fragmente entstehen. Keine Randzone, keine neue Farbzuordnung und keine abgewinkelten oder gerundeten Streifenenden.

Die Karte ist **96,88 × 109,14 × 0,6 mm** gross, mit dem vollständigen Logo in Original-Druckgrösse und drei kleinen Farbreferenzfeldern. Sichtseite oben: zuerst **0,4 mm Weiss**, dann **0,2 mm Farbe**. Die ganze Karte ist verbunden; die vier Materialmeshes sind geschlossen und überlappen sich nicht. Die CAD-Farbflächen sind bündig. Eine ebene reale Druckoberfläche ist damit noch nicht bestätigt.

## Ergebnis im Slicer

Mit **Bambu Studio 02.08.02.61** wurden fünf Einstellungen an denselben vier Materialmeshes geprüft. Erfolgreiches Slicing und fehlende Slicer-Warnungen bestätigen allein keinen Flächenschluss. Die zusätzliche Prüfung vergleicht die gesamte Sollfläche mit den tatsächlichen G-Code-Bahnen einschliesslich Linienbreiten, runder Bahnenden und Kreisbögen. Auch die richtige Farbe und beide weissen Rückschichten werden geprüft.

| Einstellung bei 0,4-mm-Düse | Nominell unbedeckt | Nach 0,03 mm Rechentoleranz | Grösste Restlücke |
|---|---:|---:|---:|
| **Klassisch, 0,30-mm-Linien — ausgewählt** | **0,466 %** | **0,168 %** | **0,118 mm²** |
| Klassisch, 0,32-mm-Linien | 0,531 % | 0,204 % | 0,141 mm² |
| Arachne, 0,32-mm-Linien | 1,386 % | 0,544 % | 0,193 mm² |
| Arachne, kürzere Übergänge / kleinere Mindestbahnen | 1,386 % | 0,514 % | 0,137 mm² |
| Klassisch, 0,28-mm-Linien | 0,440 % | 0,151 % | 0,142 mm² |

Die ausgewählte Einstellung begrenzt die **grösste einzelne Restlücke** am besten unter diesen fünf Versuchen. Die 0,28-mm-Einstellung reduziert die gesamte Fehlfläche etwas, vergrössert aber die grösste Lücke. Keine Einstellung erfüllt die Kriterien. Düsendurchmesser, entworfene Bandbreite und Extrusionslinienbreite sind unterschiedliche Grössen; die schmalen Linien sind nur digital untersucht.

Bei der ausgelieferten Datei fehlen nominell **9,23 mm²** beziehungsweise **0,466 %** der Farbfläche. Nach 0,03 mm geometrischer Rechentoleranz bleiben **3,33 mm² / 0,168 %**. Die grösste zusammenhängende Restlücke beträgt **0,118 mm²**. Die richtige Farbe fehlt nach Toleranz auf insgesamt **7,83 mm²**, einschliesslich Stellen, die eine benachbarte Farbe abdeckt. Beide weissen Rückschichten bestehen die Prüfung. Die Flächenstatistik schliesst die drei kleinen Farbreferenzfelder ein.

![Grün markiert Lücken jenseits der Rechentoleranz auf der CAD-Farbaufteilung](../output/line_gradient_full/surface_coverage.png)

**Unveränderte Kriterien:** höchstens 0,1 % Restfläche und keine einzelne Restfläche über 0,01 mm² nach 0,03 mm geometrischer Toleranz; ebenso für die richtige Farbe und jede weisse Rückschicht. Die grünen Markierungen zeigen unbedeckte Flächen jenseits dieser Toleranz, nicht alle Stellen mit falscher Farbe. Die Rechnung bildet nominelle Bahnbreiten ab; sie simuliert weder Schmelzfluss noch Haftung oder Hinterleuchtung. **Keine bestätigte Behebung der fotografierten weissen Stellen und noch kein physischer Probedruck.**

## Datei und Materialzuordnung

Die 3MF-Datei **als Projekt in Bambu Studio öffnen**; gespeicherte Bahnen in der Vorschau betrachten. Sie enthält das oben ausgewählte Profil und den geslicten Prüfstand.

| AMS-Slot | PLA-Farbe | Bildschirmreferenz |
|---|---|---|
| 1 | Weiss | `#FFFFFF` |
| 2 | Blau | `#0445C8` |
| 3 | **Cyanblau** | `#1FB9FF` |
| 4 | Rot | `#F23232` |

Cyanblau ersetzt hier Violett. Die Referenzen sind keine gemessenen Filamentfarben. Reguläre Lampenseiten und deren Palette bleiben unverändert.

- P1S, 0,4-mm-Düse, strukturierte PEI-Platte 55 °C, 0,20-mm-Schichten, keine Stützen.
- Generic PLA 220 °C für alle vier Farben, Bauteillüfter 50 % nach zwei Schichten, Zusatzlüfter aus.
- Klassische Bahnen, drei Wände, 30 % Überlappung zwischen Füllung und Wand; nominell 0,30-mm-Wand-/Decklinien.
- Reinigungsturm, drei Farbwechsel; keine Fremdfarben in weisse Objektflächen spülen.
- Slicer-Schätzung: **etwa 1 h 16 min und 10,66 g PLA**, einschliesslich Spülmaterial und Reinigungsturm.

Bei Änderungen an Material- oder Druckeinstellungen erneut slicen und prüfen; die Auswertung gilt nur für die gespeicherte Datei mit dem im Bericht festgehaltenen Hash. Ein späterer physischer Versuch müsste Flächenschluss, Farbe und Lichtwirkung getrennt bewerten. Vor dem Ablösen vollständig auf Raumtemperatur abkühlen lassen.

## Reproduktion

Eine Python-Umgebung mit den Abhängigkeiten aus `cad/requirements.txt` und eine lokale Bambu-Studio-Installation mit offiziellen P1S-Ressourcen verwenden. In dieser Sitzung: Python 3.14, Manifold 3.5.4, Shapely 2.2.0, NumPy 2.5.4, Trimesh 5.1.1, CairoSVG 2.9.1, svgpathtools 1.8.0 und Pillow 13.0.0. NumPy, Trimesh und Pillow weichen von den Projekt-Pins ab.

```sh
python design_studies/line_gradient_full/validate_preview.py
python cad/build_full_line_test.py
python scripts/slice_line_gradient_test.py /pfad/zu/bambu-studio --output output/line_gradient_full
python scripts/validate_line_gradient_test.py --output output/line_gradient_full
# Erwarteter Fehlerstatus: Restlücken; keine Freigabe.
# Nur für einen dokumentierten Audit ohne Druckfreigabe:
python scripts/validate_line_gradient_test.py --output output/line_gradient_full --allow-withheld
python scripts/test_raster_coverage.py
python scripts/package.py
```

Profilquelle ist `cad/full_line_process.json`. Der Kartengenerator verwendet die gespeicherte Vorschau, protokolliert Quell-Hashes und invalidiert alte Druck-/Prüfdateien beim Neubau. Der Slicer invalidiert alte geslicte Dateien und Flächenberichte vor dem Lauf. Die [Versuchsübersicht](../output/line_gradient_full/profile_trials.json) enthält vollständige Prozessprofile, Ergebnis- und Geometrie-Hashes für alle fünf Läufe; die vier nicht ausgewählten Zwischendateien sind nicht im Druckpaket enthalten. Die vollständige Flächenprüfung und ihre Grenzwerte wurden nicht verändert.
