# Lückenschluss bei unverändertem Verlauf — Slicer-Untersuchung

**Ergebnis: keine neue Druckfreigabe.** Nach den Fotos mit weissen Streifen wurden 20 weitere, vollständig angewendete Profileinstellungen an der unveränderten Geometrie von Testkarte 13 untersucht. Keine besteht die vollständige Flächenprüfung. Die Anforderung «weisse Lücken schliessen, Farbverlauf und gerade Streifen beibehalten, 0,4-mm-Düse» ist weiterhin nicht erfüllt. Bitte keinen weiteren vollständigen Probedruck auf Basis dieser Versuche starten.

## Was gleich blieb

- P1S, **0,4-mm-Düse**, AMS Weiss / Blau / Cyanblau / Rot.
- Exakt dieselben vier Materialmeshes und dieselbe akzeptierte SVG-Farbaufteilung; durch Dateihashes geprüft.
- Gerade Farbgrenzen bis zur Originalkontur; keine Randzonen, abgewinkelten Enden oder neue Farbzuordnung.
- **0,4 mm weisse Rückschicht + insgesamt 0,2 mm Farbe**, Gesamtstärke 0,6 mm.
- Die bereits ausgelieferte Testkarte 13 und ihre Prüfberichte bleiben als historischer Stand erhalten. Es wurde kein G-Code nachträglich geändert.

Unveränderte CAD-Farbflächen garantieren keine unveränderte reale Farbwirkung: Unterschiedliche Bahnbreiten und Schichtaufteilungen können Überlappungen und die Oberfläche beeinflussen. Keiner dieser Versuche wurde als optisch gleichwertig oder physisch lückenfrei bestätigt.

## Untersuchte Änderungen

Geprüft wurden zusätzliche Konturbahnen, eine engere Füllungsanbindung, feinere Behandlung schmaler Bereiche, klassische und variable Bahnbreiten (Arachne), andere Füllrichtungen und Füllmuster. Zusätzlich wurde die **0,2-mm-Farbschicht in zwei 0,1-mm-Schichten** geteilt. Die weisse Rückschicht bleibt dabei 0,4 mm dick. Der Slicer erzeugt dann fünf Schichten bei Z = 0,2 / 0,3 / 0,4 / 0,5 / 0,6 mm und sechs Farbwechsel.

Für die dünneren Schichten musste der Reinigungsturm weiter ins Druckbett verschoben werden; die erste Platzierung wurde vom Slicer wegen Überschreitung des Druckbereichs abgelehnt. Die ausgewerteten Dateien bestehen die Bettgrenzenprüfung und haben keine Slicer-Warnung. Die Farbflächenprüfung scheitert trotzdem.

Sechs zusätzliche Vorversuche sind von den 20 gültigen Vergleichen ausgeschlossen: zwei enthielten einen nicht übernommenen Profilparameter, drei brachen mit ungültigen Extrusionsabständen ab, einer lieferte keinen abgeschlossenen Export. Diese Versuche zählen nicht als erfolgreich geprüfte Druckeinstellungen. Rezepte und Ausschlussgründe stehen in der [Versuchsdefinition](../cad/line_gap_trials.json).

Der alte Parameter `only_one_wall_top` wurde nicht übernommen; die verwendete Version setzt diese Auswahl über `top_one_wall_type`. Das wurde am exportierten Projekt und an der [offiziellen Parameterdefinition von Bambu Studio 02.08.02.61](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/libslic3r/PrintConfig.cpp) überprüft. Die 20 gültigen Vergleiche prüfen alle angeforderten Optionen gegen die tatsächlich gespeicherten Werte.

## Resultate

Alle Werte beziehen sich auf die gesamte Farbfläche einschliesslich der drei kleinen Referenzfelder. Die Tabelle zeigt die oberste Farbschicht; beim Zweischichtaufbau wird zusätzlich die darunterliegende Farbschicht geprüft.

| Prüfstand | Nominell unbedeckt | Restfläche nach 0,03 mm Toleranz | Grösste Restlücke | Grösste Fehlfläche der richtigen Farbe |
|---|---:|---:|---:|---:|
| Bisherige Testkarte 13, 1 × 0,2 mm | 0,466 % | 0,168 % | 0,118 mm² | 0,118 mm² |
| Kleinste nominelle Fehlfläche: Arachne, 2 × 0,1 mm, Mindestbahn 85 % | 0,196 % | 0,022 % | 0,020 mm² | 0,046 mm² |
| Kleinste grösste Restlücke: Arachne, 2 × 0,1 mm, 0,30-mm-Konturbahnen | 0,236 % | 0,027 % | 0,019 mm² | 0,035 mm² |

Der zweite Versuch reduziert die nominelle Fehlfläche gegenüber der bisherigen Datei um etwa 58 %, ist aber weiterhin nicht lückenfrei. Beim dritten Versuch liegt auch die untere Farbschicht über dem Grenzwert für einzelne Lücken: 0,019 mm² unbedeckt beziehungsweise 0,035 mm² ohne die richtige Farbe. Verbesserte Durchschnittswerte allein reichen nicht für eine Freigabe.

**Grenzwerte unverändert:** höchstens 0,1 % unbedeckte Fläche und keine zusammenhängende Restfläche über 0,01 mm² nach 0,03 mm geometrischer Rechentoleranz. Dieselben Anforderungen gelten für die korrekte Farbe und jede weisse Rückschicht. Für die dünnen Varianten werden beide Farblagen einzeln geprüft; die Lücken werden nicht durch Zusammenlegen der Schichten weggerechnet.

[Vollständige Ergebnisse aller 20 Profile](../output/line_gradient_gap_audit/trials.json) · [Aktueller Status](../output/line_gradient_gap_audit/STATUS.md)

Die Flächenprüfung verwendet tatsächliche G-Code-Bahnen, Breiten, runde Bahnenden und Kreisbögen. Sie ist keine Simulation der Schmelze oder des Lichtdurchtritts und modelliert keine Verdrängung durch später gedruckte Nachbarfarben. Eine bestandene digitale Prüfung wäre nur die Voraussetzung für einen gezielten physischen Test; hier ist bereits diese Voraussetzung nicht erreicht.

## Foto-Rückmeldung

Der Benutzer zeigt nach der Auslieferung von Testkarte 13 helle Streifen entlang der Farbgrenzen, besonders im grossen Stern. Sie stören den Verlauf. Fehlende Farbabdeckung ist durch die digitale Prüfung weiterhin plausibel; aus den beleuchteten Fotos lässt sich nicht jeder helle Streifen sicher von einer Reflexion unterscheiden. Der tatsächlich verwendete G-Code und mögliche eigene Slicer-Änderungen wurden nicht separat verifiziert. Die Bilder bestätigen keine erfolgreiche Behebung.

## Reproduzieren

Benötigt die Python-Abhängigkeiten des Projekts und **Bambu Studio 02.08.02.61**. Die in dieser Sitzung verwendeten Python-Paketversionen sind in [Testkarte 13](FARBBAHNEN_GESAMT_TEST.md#reproduktion) dokumentiert.

```sh
python scripts/audit_line_gap_closure.py --bambu-studio /pfad/zu/bambu-studio
# Erwarteter Fehlerstatus: kein Profil besteht. Zwischendateien: output/logs/line_gap_audit/.
# Bereits geslicte Versuche erneut vollständig prüfen:
python scripts/audit_line_gap_closure.py --inspect-existing --workdir output/logs/line_gap_audit
# --allow-withheld ist ausschliesslich für ein dokumentiertes Audit ohne Druckfreigabe.
python scripts/test_raster_coverage.py
python scripts/package.py
```

Die Untersuchung prüft auch, dass die angeforderten Profilparameter im exportierten Projekt tatsächlich vorhanden sind. Der Flächenprüfer unterstützt nun explizite Schichthöhen und Rückschichtpositionen; dadurch wird die zusätzliche weisse Schicht bei Z = 0,3 mm nicht übergangen. Die sechs Regressionstests umfassen einen absichtlichen Defekt genau in dieser Zwischenlage. Die bisherigen 0,2-mm-Prüfergebnisse bleiben unverändert.

Es werden nur Rezepte und Berichte im Repository ausgeliefert, keine weitere fehlgeschlagene 3MF als neue Druckempfehlung. Die ursprüngliche Testkarte bleibt unverändert. Eine allgemeine Unmöglichkeit mit der 0,4-mm-Düse ist durch diese Versuche nicht bewiesen; eine belastbare Lösung unter den festgelegten Bedingungen liegt noch nicht vor.
