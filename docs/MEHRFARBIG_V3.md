# myAI Cube v3 — Logo direkt mit dem AMS drucken

Der Würfel bleibt **150 × 150 × 150 mm** groß. Vier identische, flach gedruckte Leuchtpaneele werden von oben in einen weißen Rahmen eingeschoben. Das mehrfarbige Logo ist bündig in jedes Paneel integriert. Der abnehmbare Deckel schließt die Führungen. Die Logos benötigen keinen Klebstoff.

![Zusammengesetzter AMS-Entwurf](../output/multicolor_v3/preview/assembled.png)

*Ansicht der tatsächlichen CAD-Geometrie bei illustrativer Studiobeleuchtung. Keine Vorhersage der Leuchtwirkung oder realer Filamentfarben.*

## Vier Farben in einem AMS

| Projekt-Filament | PLA-Farbe | Verwendung |
|---|---|---|
| 1 | Weiß | Paneel, Rückschicht, Rahmen, Boden, Deckel |
| 2 | Dunkelblau | Schrift und dunkle Sternflächen |
| 3 | Hellblau | Helle Sternflächen |
| 4 | Rot | Rote Sternfläche |

Die Konturen stammen aus der unveränderten hellen Logo-SVG. Der ursprüngliche Farbverlauf wird in klar getrennte Farbflächen aufgeteilt; dunkles Sternblau und Schrift teilen sich ein Filament. Es ist eine **druckbare Vierfarben-Annäherung**, keine exakte Wiedergabe des Verlaufs. Eine winzige separate Kontur unterhalb der Düsenauflösung entfällt wie bei v2.

Die Paneele sind **133,4 × 139,4 × 0,8 mm** groß. Außen liegen 0,4 mm tiefe Farbeinlagen und weißer Hintergrund, dahinter eine durchgehende 0,4-mm-Schicht aus Weiß. Das Logo ist auf jeder montierten Würfelseite bei **75 / 75 mm** zentriert. Farbflächen dämpfen das Licht anders als weißes PLA; Farbe und Kontrast müssen mit dem eigenen Filament geprüft werden.

## Druckdateien

Alle Links führen zu geslicten **Bambu-Studio-Projekten** für P1S, 0,4-mm-Düse, 0,20-mm-Schichten und strukturierte PEI-Platte. Ein Paneel pro Druckplatte; viermal unverändert drucken.

| Druckprojekt | Anzahl | Slicer-Zeit je Druck | PLA je Druck¹ |
|---|---:|---:|---:|
| [Farb- und Lichtprobe](../output/multicolor_v3/print/01_color_test_P1S.3mf) | zuerst 1 | 34 min | 7,05 g |
| [Seitenpaneel mit Logo](../output/multicolor_v3/print/02_panel_P1S.3mf) | 4 | 91 min | 23,24 g |
| [Rahmen](../output/multicolor_v3/print/03_frame_P1S.3mf) | 1 | 5 h 53 min | 68,98 g |
| [Boden / LED-Aufnahme](../output/multicolor_v3/print/04_base_P1S.3mf) | 1 | 4 h 14 min | 89,08 g |
| [Deckel](../output/multicolor_v3/print/05_lid_P1S.3mf) | 1 | 3 h | 46,00 g |

¹ Einschließlich Brim, Spülmaterial und Reinigungsturm, soweit vom Slicer erfasst. Lampe ohne Testprobe insgesamt etwa **297 g PLA und 19 h 10 min**. Es werden keine Stützen erzeugt. Jedes Paneel benötigt sechs Farbwechsel.

**[Komplettes Druck- und Quellenpaket v3 herunterladen](../output/myAI_Cube_150_P1S_AMS_v3.zip)**. Das Paket enthält zusätzlich die bisherige einfarbige v2; für diesen Entwurf die Dateien unter `output/multicolor_v3/print/` verwenden.

1. Die Farbprobe **als Projekt** öffnen. Die vier Projekt-Filamente beim Senden den passenden realen AMS-Fächern zuordnen; die Datei kennt deine geladenen Spulen nicht. Für die weißen Druckprojekte Projekt-Filament 1 dem weißen Fach zuweisen.
2. Eigenes PLA und Druckplatte prüfen. Voreinstellung: Generic PLA, 220 °C Düse, 55 °C Bett. Bei Profil- oder Materialänderungen neu slicen und die Vorschau prüfen.
3. Die Logo-Vorderseite liegt auf dem Druckbett. Im Blick von oben erscheint die Rückseite entsprechend gespiegelt. **Nicht zusätzlich spiegeln oder wenden.** Alle vier Farbvolumen bleiben Teile eines gemeinsamen Objekts.
4. Zuerst die kleine Probe drucken und vor dem LED-Kit prüfen. Sie hat denselben Schichtaufbau, aber nur 35 % der Logo-Größe; sie dient dem Farb-/Lichtvergleich, nicht der Beurteilung feiner Details in Originalgröße oder der mechanischen Passung.
5. Danach einen Rahmen und zunächst ein vollständiges Paneel drucken. Brim sauber entfernen und den Sitz prüfen, bevor die drei übrigen Paneele gedruckt werden. Dünne Paneele erst vom abgekühlten Bett lösen und nicht stark knicken.

Der Reinigungsturm ist aktiviert. Spülen in die Leuchtflächen ist deaktiviert, damit Restfarben nicht in der weißen Rückschicht landen. Vorgesehen sind konservative Spülmengen von 650 mm³ beim Wechsel auf Weiß und 450 mm³ bei anderen Farbwechseln; anhand der Probe für das eigene Filament bewerten. Die kleinen Vorschaubilder innerhalb der 3MF-Dateien fehlen wegen des kopflosen CLI-Exports; die Geometrie und der geslicte G-Code sind enthalten.

## Montage

![Deckel abgenommen, vorderes Paneel teilweise eingeschoben](../output/multicolor_v3/preview/insertion.png)

1. LED Lamp Kit 001/MH001 in die nominell 60-mm-Aufnahme des Bodens setzen und mit dem vorgesehenen Klebepad befestigen. Die Auslegung basiert auf einem nominell 59-mm-Modul; tatsächliches Kit vor Montage prüfen. Kabel durch die offene Aussparung führen.
2. Rahmen auf den Boden setzen, die hintere Kabelöffnung ausrichten. Die Verbindung steckt lose auf dem Boden; kein verriegelter Transportgriff.
3. Vier Paneele von oben in die Führungen schieben, bedruckte Bettseite nach außen und Schrift aufrecht. Seitlich sind nominal 0,3 mm Spiel je Kante vorgesehen; durch die Dicke ergibt sich 0,25 mm vorne und 0,35 mm hinten. Paneele nicht gewaltsam einschieben.
4. Deckel aufsetzen. Seine seitlichen Blenden schließen die oberen Fenster und halten die Paneele in den Führungen. Beim Tragen den Boden unterstützen.

Der Boden entspricht v2. **Rahmen und Deckel gehören zusammen zur v3**; den v2-Körper oder v2-Deckel nicht mit den v3-Paneelen kombinieren. Die Lüftungsöffnungen bleiben frei. Den ersten Betrieb beaufsichtigen und Erwärmung, Verformung und Lichtverteilung kontrollieren; Wärmeverhalten ist noch nicht praktisch geprüft.

## Quellen und digitale Prüfung

Maße/Farben: [Parameter](../cad/multicolor_parameters.json). Konturen, Rahmen und Montage: [Generator](../cad/build_multicolor.py). Die Original-SVGs bleiben unverändert. Die LED-Aufnahme und Grundfunktionen werden aus dem v2-Generator importiert.

```sh
.venv/bin/python cad/build_multicolor.py
.venv/bin/python scripts/prepare_profiles.py /pfad/zu/BambuStudio/resources/profiles/BBL
.venv/bin/python scripts/slice_multicolor.py /pfad/zu/bambu-studio
.venv/bin/python scripts/validate_multicolor.py
blender -b -t 4 --python scripts/render_multicolor.py
.venv/bin/python scripts/package.py
```

Python-Abhängigkeiten und Bambu-Studio-Einrichtung: [CAD & Validierung](CAD_UND_VALIDIERUNG.md). Verwendet: Bambu Studio 2.8.2.61. Der Slicer erzeugt zuerst eine native Mehrteil-Projektdatei; anschließend werden die vier Teile explizit den Filamenten zugeordnet und regulär geslict. G-Code wird nicht nachbearbeitet.

- [Geometrieprüfung](../output/multicolor_v3/geometry_validation.json): geschlossene Materialvolumen, vollständige Paneelabdeckung, keine relevanten Volumenüberschneidungen, kollisionsfreie Montage und Einschubbewegung, Außenmaße und Logo-Zentrierung. Getrennte Buchstaben/Sternflächen sind absichtlich mehrere Inseln eines Materialteils. Boolesche Abweichungen an gemeinsamen Grenzflächen werden mit 0,001 mm³ Toleranz bewertet.
- [Druckprüfung](../output/multicolor_v3/print_validation.json): geschlossene exportierte STL-Netze, vier korrekte Materialzuordnungen ohne Slicer-Netzreparatur, G-Code-Prüfsummen, Bettgrenzen einschließlich Brim/Reinigungsturm, keine Stützen oder Slicer-Druckwarnungen. Farbausgabe bei Z = 0,2/0,4 mm, ausschließlich Weiß im Paneel bei Z = 0,6/0,8 mm.

**Stand: digital geprüfter und geslicter Prototyp, noch kein physisch getestetes Modell.** Passung, Verzug, Lichtdurchlässigkeit, Farbsauberkeit und Dauerbetrieb bleiben durch Probedruck und Betrieb zu prüfen.
