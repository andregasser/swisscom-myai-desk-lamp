# Rasterprobe: ein vollständiges Logo

**Jetzt nur diese Datei einmal drucken:** [09_raster_test_P1S.3mf](../output/multicolor_v4_2/print/09_raster_test_P1S.3mf).

Eine flache Karte mit dem vollständigen myAI-Logo in derselben Größe wie auf der späteren Seitenplatte. Sterne und Schrift erhalten einen gerasterten Verlauf **Rot → Violett → Blau**. Der bisherige Schichtvergleich ist abgeschlossen und muss nicht wiederholt werden.

![Rasterprobe aus den tatsächlichen Druckgeometrien](../output/multicolor_v4_2/preview/raster_test.png)

*CAD-Vorschau mit nominellen Bildschirmfarben. Das gedruckte Filament und die Hinterleuchtung können anders wirken.*

## Drucken

- **P1S, 0,4-mm-Düse, strukturierte PEI-Platte, PLA und AMS.** Die Datei in Bambu Studio **als Projekt** öffnen, Orientierung und Größe beibehalten.
- Projekt-Filamente zuordnen: **1 Weiß · 2 Blau · 3 Violett · 4 Rot**. Dieselben Spulen wie beim Schichtvergleich verwenden; für Violett ist ecoPLA Purple mit 210 °C eingestellt. Weiß, Blau und Rot verwenden das bisherige Generic-PLA-Profil mit 220 °C, das Bett 55 °C. Bei Profiländerungen neu slicen.
- Karte **96,9 × 109,1 × 0,6 mm**, Logo **86,9 × 99,1 mm**, Raster **0,8 mm**. Unter dem Logo liegen **0,2 mm Farbe + 0,4 mm Weiß**. Außerhalb des Logos ist die ganze Fläche weiß.
- Die farbige Sichtseite liegt **auf dem Druckbett**. Nicht spiegeln, nicht aufstellen. Drei Schichten à 0,20 mm, keine Stützen.
- Laut Bambu Studio etwa **1 h 2 min und 11,16 g PLA**, einschließlich Spülmaterial und Reinigungsturm; vier Farbwechsel.

Neben der Karte druckt ein Reinigungsturm, um nach den Farbwechseln sauber weiterzudrucken. Der schmale Brim hält die Karte am Bett. **Beides sind keine weiteren Prüfteile.** Nach dem Abkühlen die Karte lösen und den Brim entfernen.

## Was du beurteilen sollst

1. **Ohne Licht dahinter:** Gefällt dir der Übergang besser als die bisherigen drei Farbbänder? Sterne und Schrift gemeinsam ansehen.
2. **Mit dem LED-Kit hinter der weißen Rückseite:** Bleibt Violett Teil des Verlaufs oder wirkt es wieder wie ein dunkles Loch? Möglichst denselben LED-Abstand wie beim Schichtvergleich verwenden, damit der Vergleich aussagekräftig bleibt.
3. **Aus normalem Betrachtungsabstand, etwa 50–100 cm:** Mischen sich die Rasterpunkte optisch angenehm? Aus der Nähe sollen die einzelnen Farbfelder erkennbar sein; entscheidend ist, ob dich die Körnung am Schreibtisch stört.

Eine kurze Rückmeldung zu **Verlauf, Violett mit Licht und sichtbarer Körnung** reicht für die nächste Entscheidung. Die Probe prüft Farben und Raster in Originalgröße. Führungen, Montage und Wärmeverhalten werden damit nicht geprüft. Die vier regulären Seitenplatten verwenden vorerst weiterhin die bisherigen Farbbänder.

## Konstruktion und digitaler Prüfstand

Die Konturen und getrennten Verlaufsrichtungen von Sternen und Schrift stammen aus der unveränderten dunklen Original-SVG. Ein geordnetes 8×8-Bayer-Raster verteilt Rot, Violett und Blau in 0,8-mm-Zellen. Die normierten Farbstopps 0,00 / 0,36 / 0,80 entsprechen dem vorherigen Gestaltungsvorschlag. Dies ist eine räumliche Mischung der vorhandenen drei Filamente, keine exakte Wiedergabe aller Original-Farbstopps.

An diagonalen Zellkontakten lösen Rundungen mit 0,08 mm Radius geometrische Mehrdeutigkeiten auf. 104 winzige, an der Kontur angeschnittene Farbinseln mit zusammen 11,86 mm² werden benachbarten Farben zugeordnet. Die Logo-Silhouette bleibt erhalten. Diese winzigen Rundungen sind Konstruktionshilfen, keine zugesicherte Druckauflösung.

Die Probe besitzt ein eigenes Prozessprofil: **0,4 mm Linienbreite in der ersten Schicht und keine Elefantenfuß-Kompensation**. Das erhält die kleinen Farbfelder besser als die bisherige Kombination aus 0,5 mm Linienbreite und 0,15 mm Kompensation. Die anderen Druckprojekte behalten ihre Profile. Fremdfarben werden nicht in die weiße Rückschicht gespült.

Geometrie und Slicing sind geprüft: vier geschlossene Materialnetze, ein zusammenhängendes Gesamtteil, vollständige Materialabdeckung ohne relevante Überschneidungen, korrekte AMS-Zuordnung, gültige G-Code-Prüfsumme, Bettgrenzen sowie keine Stützen oder Slicer-Druckwarnungen. Die erste Schicht enthält Weiß und drei Logofarben; die zwei folgenden Schichten enthalten nur Weiß.

Die zusätzliche Druckbahnprüfung berücksichtigt Bogenbewegungen, Linienbreiten und den Düsenversatz. In allen **2.366 vollständig innerhalb des Logos liegenden Zellen** erreicht die richtige Farbe den mittleren Bereich mit 0,2 mm Durchmesser; beide weißen Rückschichten decken die Zellmitten ab. Das belegt den Erhalt dieser Rasterzellen, nicht eine lückenlose Oberfläche oder die exakte Form jedes angeschnittenen Randpixels. Zwischen variablen Bahnen können kleine Restlücken bleiben; der größte berechnete Abstand einer Zellmitte zum vorgesehenen Farbauftrag beträgt 0,075 mm. Haftung, reale Farbmischung und Leuchtwirkung bleiben bis zum Probedruck offen.

[Geometrieprüfung](../output/multicolor_v4_2/raster_test/geometry_validation.json) · [Druckbahnprüfung](../output/multicolor_v4_2/raster_test/toolpath_validation.json) · [Erste Schicht aus den tatsächlichen Druckbahnen](../output/multicolor_v4_2/preview/raster_toolpaths.png). Die Druckbahnansicht ist eine Näherung, keine Foto- oder Flusssimulation.

## Reproduzieren

In der eingerichteten Projektumgebung, mit Bambu Studio 2.8.2.61:

```sh
.venv/bin/python cad/build_raster_test.py
.venv/bin/python scripts/slice_multicolor.py /pfad/zu/bambu-studio --plates 09_raster_test
.venv/bin/python scripts/validate_multicolor.py
blender -b -t 4 --python scripts/render_raster_test.py
.venv/bin/python scripts/package.py
```

Die Raster-Druckbahnprüfung läuft in der AMS-Gesamtprüfung mit; separat ist sie über `scripts/validate_raster_test.py` ausführbar. Die CLI-Druckdatei enthält Geometrie und G-Code, jedoch kein eingebettetes Vorschaubild.
