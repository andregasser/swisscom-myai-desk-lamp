# Reproduzierbarkeit und Prüfstand

## Geometrie

`cad/build.py` erzeugt die Geometrie mit Manifold3D. Die SVG-Kontur wird aus dem unveränderten Light-Logo abgeleitet und als Relief mit der Wand vereinigt. Kurven werden mit höchstens etwa 0,2 mm Abtastabstand polygonisiert. Das separate Dreiecksfragment am A mit weniger als 0,02 mm² wird beim Ableiten ausgelassen, um einen nicht druckbaren Punktkontakt zu vermeiden.

Das Logo wird nach innen und gleichzeitig nach oben extrudiert. Die dadurch geneigten Unterkanten reduzieren freie Überhänge beim aufrechten Druck. Die äußeren Seitenflächen bleiben eben. Die Farbdaten beider Original-SVGs bleiben in `assets/logos` erhalten, werden aber nicht als Druckfarben übernommen.

Ab Version 2 wird die Begrenzungsbox der zusätzlichen Logo-Materialstärke auf die Mitte der zusammengesetzten Seite gesetzt, statt die SVG-Zeichenfläche zu zentrieren. Eine numerische Prüfung bestätigt 75 / 75 mm für die projizierte Kontur. Alle vier Seiten verwenden dieselbe Geometrie, jeweils um 90° gedreht.

Für Änderungen zuerst die Parameter anpassen und dann:

```sh
.venv/bin/python cad/build.py
```

Der Generator prüft geschlossene, zusammenhängende Volumenkörper, positive Volumina, Druckbettkontakt und Teilegrößen. Er prüft die zusammengesetzte Lampe auf paarweise Materialüberschneidungen. Ein nominaler Ø-59-mm-Zylinder als vereinfachter LED-Platzhalter kollidiert nicht mit der Aufnahme. Diese Prüfung ersetzt nicht das reale Kit samt Kabel und Fertigungstoleranzen.

## Bambu Studio

Die mitgelieferten Druckdateien wurden mit **Bambu Studio 02.08.02.61** und dessen offiziellen Ressourcen erzeugt. `scripts/prepare_profiles.py` löst die Vererbung einschließlich der originalen P1S-Start-/End-G-Code-Vorlagen auf. `output/profiles` enthält die konkret verwendeten Profile. Die Druckparameter sind in jedem fertigen 3MF eingebettet.

```sh
.venv/bin/python scripts/prepare_profiles.py /pfad/zu/BambuStudio/resources/profiles/BBL
.venv/bin/python scripts/slice.py /pfad/zu/bambu-studio
.venv/bin/python scripts/validate_prints.py
```

Die Linux-AppImage wurde für die Erstellung nur unter `/tmp` entpackt. Fehlende Laufzeitbibliotheken wurden ebenfalls dort bereitgestellt; sie gehören nicht zum Druckpaket. Zum Öffnen und Drucken genügt eine reguläre Bambu-Studio-Installation, empfohlen 2.8.2 oder neuer.

## Tatsächlich geprüft

- Alle zehn STL-Einzelteile erneut eingelesen: geschlossene, konsistent orientierte, zusammenhängende Körper.
- Zusammengebautes Außenmaß: 150 × 150 × 150 mm. Keine Überschneidung von Boden, Körper und Deckel.
- Vier Platten erfolgreich geslict; in den Slicer-Ergebnisdaten keine Druckwarnungen.
- Eingebettetes Profil: P1S / 0,4 mm / PLA / strukturierte PEI-Platte / 0,20 mm / keine Stützen.
- Die erzeugten Modell- und Brim-Extrusionskoordinaten liegen auf dem nutzbaren Bett und außerhalb des vorderen linken Ausschlussbereichs. Offizielle Start-/Reinigungsbewegungen werden davon getrennt behandelt.
- ZIP-Integrität der 3MFs und eingebettete MD5-Prüfsumme jedes G-Codes geprüft. SHA-256-Prüfsummen stehen in `output/print_validation.json`.

Die CLI kann in dieser Umgebung keine OpenGL-Plattenvorschaubilder erzeugen; sie meldet dafür einen Display-Fehler, exportiert aber erfolgreich Geometrie, Profile und geslicten G-Code. Die Projekte enthalten deshalb keine eingebetteten Platten-Thumbnails. Bambu Studio kann die Modelle beim Öffnen selbst anzeigen. Separate Modellansichten liegen unter `output/preview`.

**Nicht physisch geprüft:** Sitz am konkreten LED-Kit, Drucktoleranzen, Verzug, langfristige Wärmebeständigkeit, Leuchtdichte und Logo-Kontrast. Dafür liegt die Testplatte bei. Die Renderansichten zeigen die Geometrie; Material und Beleuchtung sind illustrativ.

## Vorschauen

`output/preview/assembly.glb` enthält die tatsächlichen drei montierten Druckmeshes und ist nicht als Druckplatte gedacht. `scripts/render.py` erzeugt mit Blender 5 die PNG-Ansichten aus den STL-Dateien:

```sh
blender -b -t 4 --python scripts/render.py
```

Die originalen P1S-/PLA-Grundprofile stammen aus [Bambu Studio](https://github.com/bambulab/BambuStudio/tree/v02.08.02.61/resources/profiles/BBL). Die Befehlszeile folgt der [offiziellen CLI-Dokumentation](https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage).
