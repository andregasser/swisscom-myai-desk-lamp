# Drucken und zusammenbauen

## 1. Testplatte

Die vier beschrifteten Lichtproben haben freie Flächen mit **0,6 / 0,8 / 1,0 / 1,2 mm** Materialstärke. Der Rahmen ist dicker; das kleine Logo trägt jeweils weitere 0,8 mm auf.

- Nach dem Abkühlen ablösen und den Brim entfernen. Die dünnen Flächen nicht vom warmen Bett ziehen.
- Jede Probe mit demselben LED-Kit, Abstand und Umgebungslicht beurteilen. Helligkeit, sichtbare LED-Hotspots und Logokontrast vergleichen.
- Die Proben liegen beim Druck flach. Die großen Körperwände werden aufrecht gedruckt; deshalb ist dies eine Vorauswahl, keine exakte optische Kalibrierung. Der Hauptentwurf verwendet zunächst **0,8 mm**.
- Das LED-Modul ohne Kraft in den offenen Passring setzen. Dieser hat dieselben 60,0 mm Innendurchmesser wie die Bodenaufnahme. Auch den Kabelausgang prüfen. Das Modul soll hineinpassen, ohne gequetscht zu werden; die endgültige Befestigung erfolgt mit Klebeband.
- Die beiden langen Steckproben prüfen: das U-förmige Gegenstück nach dem Druck umdrehen und auf den Streifen mit den Führungen setzen. Es soll leicht aufliegen, ohne die Wände auseinanderzudrücken. Die Form erprobt gegenüberliegende Führungen mit 0,35 mm Spiel pro Seite.

Wenn Wandstärke oder Passung geändert werden müssen, `cad/parameters.json` anpassen, Geometrie neu erzeugen und neu slicen. Die bestehenden Druckprojekte übernehmen Änderungen nicht automatisch. Noch keine volle Lampe drucken, wenn der Passring nicht zum vorhandenen LED-Kit passt.

## 2. Hauptteile drucken

Alle drei Projekte sind bereits ausgerichtet:

- **Körper:** aufrecht, die unten offene Kabelkerbe auf dem Bett. Nicht auf eine Seitenfläche legen, kein Vasenmodus.
- **Boden:** flache Außenseite auf dem Bett, LED-Ring und Führungen nach oben.
- **Deckel:** flache Außenseite auf dem Bett, Führungen nach oben. Bei der Montage wird er umgedreht.

Die Projekte sind für eine strukturierte PEI-Platte eingerichtet. Weißes PLA mit einem passenden Filamentprofil verwenden. 0,20 mm Schichthöhe, Arachne und die vorbereitete Orientierung beibehalten. 100 % Füllung verhindert ein sichtbares Infill-Raster in den Leuchtflächen und Logos. Die 45°-Übergänge und nach innen geneigten Logo-Reliefs sind ohne Stützen ausgelegt.

Das Bett vor dem Druck reinigen. Brim erst nach dem Abkühlen entfernen, besonders am unteren Körperrand. Die Lüftungs- und Kabelöffnungen von losen Fäden befreien. Keine Logo-Flächen durchschneiden: Die Innenflächen der Buchstaben und Sterne sind Teil der durchgehenden Wand.

## 3. Montage

Benötigt: die drei Druckteile, LED Lamp Kit 001/MH001, dessen doppelseitige Ø-40-mm-Klebescheibe und eine passende 5-V-USB-Stromversorgung. Keine zusätzlichen Schrauben und kein AMS erforderlich.

1. LED-Kit zunächst lose mittig einsetzen und die Kabelrichtung zur Öffnung des Rings ausrichten.
2. Mit der Klebescheibe unter dem LED-Kit am Boden befestigen. Nicht die Leuchtfläche abkleben.
3. Kabel nach hinten zwischen den unterbrochenen Führungsleisten führen.
4. Den Körper über die Führungen auf den Boden setzen. Die unten offene Kabelkerbe muss über dem Kabel liegen; das Kabel darf nicht eingeklemmt werden. USB-Stecker und Schalter bleiben außerhalb.
5. Deckel mit Führungsleisten nach unten einsetzen. An der kleinen rückseitigen Aussparung lässt er sich wieder anheben.
6. Einschalten und Lichtverteilung prüfen. Beim ersten Betrieb nach etwa 30–60 Minuten kontrollieren, dass sich PLA an der LED-Aufnahme nicht verformt. Die Lüftungsöffnungen frei halten.

**Die Steckverbindungen verriegeln nicht.** Zum Versetzen die Lampe am Boden halten. Der Deckel und der Körper bleiben für Wartung abnehmbar.

## Lichtwirkung

Der weiße Würfel leuchtet flächig; die dickeren Logo-Konturen sollen dunkler sichtbar werden. Der genaue Kontrast hängt vom weißen PLA ab. Eine einzelne nach oben gerichtete LED im Boden beleuchtet Seiten und Deckel unterschiedlich; eine gleichmäßige Helligkeit ist noch nicht am physischen Prototyp nachgewiesen. Der Entwurf ist eine diffuse Tischleuchte, ohne zugesicherte Arbeitsplatz-Beleuchtungsstärke.
