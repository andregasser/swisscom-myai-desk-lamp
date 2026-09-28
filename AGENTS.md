# Arbeitsanweisungen für myAI Cube

Diese Hinweise gelten für das gesamte Repository. Konkrete Anforderungen der aktuellen Aufgabe haben Vorrang vor den hier beschriebenen Projektstandards.

## Projekt und Konstruktion

- Dieses Repository enthält eine parametrische, 3D-druckbare Würfellampe, keine Webanwendung. Kommunikation und Projektdokumentation sind auf Deutsch; bestehende englische Code- und Dateinamen beibehalten.
- Aktueller Entwurf: 150 × 150 × 150 mm **zusammengesetzt**, weißes PLA, Bambu Lab P1S mit 0,4-mm-Düse und LED Lamp Kit 001/MH001. Maße im CAD und in STL-Dateien sind Millimeter.
- Körper, Boden und abnehmbaren Deckel als getrennte Druckteile erhalten. Die Führungen sind lose Steckverbindungen, keine Verriegelungen.
- Leuchtflächen sind zunächst 0,8 mm dünn. Stabilität durch Rahmen und Ecken schaffen; größere Wandstärken beeinflussen die Lichtwirkung und müssen mit den Lichtproben bewertet werden.
- Das vollständige myAI-Logo gehört auf alle vier Seiten. Die **tatsächliche projizierte Kontur**, einschließlich der Reliefneigung, auf der montierten Seite zentrieren: aktuell 75 / 75 mm. Nicht lediglich die SVG-Zeichenfläche zentrieren.
- Der aktuelle Druck ist einfarbig, mit innen verstärktem Logo und glatter Außenfläche. Farbige Logos, AMS-Druck oder aufgeklebte Teile sind mögliche Alternativen, aber noch keine gewählte Änderung.
- Die Originaldateien in `assets/logos/` unverändert lassen. Druckkonturen daraus ableiten; keine Ersatzlogos zeichnen.

## Maßgebliche Dateien

| Aufgabe | Quelle |
|---|---|
| Maße und Toleranzen | `cad/parameters.json` |
| Geometrie und STL-/Geometrie-3MF-Export | `cad/build.py` |
| P1S-, Prozess- und Filamentprofile ableiten | `scripts/prepare_profiles.py` |
| Druckprojekte slicen und prüfen | `scripts/slice.py`, `scripts/validate_prints.py` |
| Modellansichten und Druckpaket erzeugen | `scripts/render.py`, `scripts/package.py` |
| Kurzer Projekteinstieg | `README.md` |
| Aufbau, Montage und Prüfdetails | `docs/PROJEKTDETAILS.md`, `docs/DRUCK_UND_MONTAGE.md`, `docs/CAD_UND_VALIDIERUNG.md` |

STL-Dateien, Geometrie-3MFs, Profile und Prüfberichte in `output/` sind abgeleitete Dateien. Änderungen an ihren Quellen vornehmen und die betroffenen Ergebnisse neu erzeugen. Geslicten G-Code nicht nachträglich von Hand korrigieren.

## Umgebung und Befehle

Vom Repository-Stamm aus arbeiten. Eine vorhandene `.venv` verwenden; andernfalls eine lokale Python-Umgebung mit `cad/requirements.txt` einrichten:

```sh
python3 -m venv .venv
.venv/bin/pip install -r cad/requirements.txt
.venv/bin/python cad/build.py
```

Für Slicing eine lokale Bambu-Studio-Installation und deren offizielle Ressourcen verwenden. Pfade unter `/tmp` aus früheren Aufgaben sind nicht dauerhaft verfügbar. Die ausführliche Einrichtung und die zuletzt verwendete Slicer-Version stehen in `docs/CAD_UND_VALIDIERUNG.md`.

```sh
.venv/bin/python scripts/prepare_profiles.py /pfad/zu/BambuStudio/resources/profiles/BBL
.venv/bin/python scripts/slice.py /pfad/zu/bambu-studio --plates 02_body
.venv/bin/python scripts/validate_prints.py
```

`--plates` entsprechend den tatsächlich betroffenen Platten wählen; ohne diese Option werden alle vier geslict. Profiländerungen erfordern das erneute Slicen aller betroffenen Druckprojekte. Nach Geometrieänderungen sind die bisherigen geslicten Dateien nicht automatisch aktuell.

## Prüfen und ausliefern

- **CAD-Änderungen:** Generator ausführen. Geschlossene, zusammenhängende Volumenkörper, Druckorientierung, Außenmaße, Logo-Zentrierung und kollisionsfreie Montage prüfen. Neue Geometrie slicen und anschließend `scripts/validate_prints.py` ausführen.
- **Druckprofile:** P1S, tatsächliche Düse und Druckplatte, Filament, Modell-/Brim-Bettgrenzen und Stützbedarf prüfen. Die vorhandenen Profile setzen weißes PLA, strukturierte PEI-Platte und 0,20-mm-Schichten voraus. Hersteller-Start-/End-G-Code aus den offiziellen Profilen übernehmen.
- **Vorschauen:** Nach sichtbaren Geometrieänderungen mit `blender -b -t 4 --python scripts/render.py` aktualisieren. Die Illustration in `assets/illustrations/` bei Bedarf nachführen. Renderbilder nicht als Beleg für reale Helligkeit oder Passung verwenden.
- **Dokumentation:** README kurz und bebildert halten; Details nach `docs/` verlagern. Relative Links und Bilder prüfen. Bei reinen Dokumentationsänderungen ist kein erneutes Slicing nötig.
- **Druckpaket:** Bei Änderungen an enthaltenen Dateien `scripts/package.py` ausführen; das Skript prüft Archiv und Prüfsummen. Bei einer neuen Designversion Paketnamen und Dokumentation konsistent aktualisieren. Frühere Versionspakete erhalten. `AGENTS.md` ist Repository-Anleitung und wird derzeit nicht ins Druckpaket aufgenommen.
- **Prüfstand:** Digital geprüft, geslict und physisch gedruckt ausdrücklich unterscheiden. Reale Passung, Wärmeverhalten und Lichtwirkung bleiben unbestätigt, bis entsprechende Probedruck-Ergebnisse vorliegen. Fehlende Werkzeuge oder ausgefallene Prüfungen konkret nennen.

## Git und Abschluss

- Vor Änderungen `git status` prüfen und fremde Änderungen erhalten. `.venv/`, `__pycache__/`, `output/logs/` und heruntergeladene Werkzeuge nicht committen.
- Quelländerungen zusammen mit den betroffenen aktuellen Druckdateien, Berichten und Dokumenten einchecken. Vor einem Commit `git diff --check` und den vorgemerkten Diff prüfen.
- Wenn Commit und Push zur Aufgabe gehören, diese nach den passenden Prüfungen vollständig ausführen. Eine vorhandene oder verifizierte Git-Identität verwenden; dafür keine globale Git-Konfiguration verändern.
- Nach dem Push Branch-Synchronisierung und Arbeitsverzeichnis prüfen. Ergebnis, relevante Prüfungen und verbleibende Einschränkungen knapp melden; auf die passenden Dateien oder den Commit verlinken.
