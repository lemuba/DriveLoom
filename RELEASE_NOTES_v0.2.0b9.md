# DriveLoom v0.2.0b9 — Beta

## Änderungen

- Treffer der manuellen Schnellladersuche werden als anklickbare Kartenmarker dargestellt. Die Marker bleiben beim Wechsel der Kartenansicht erhalten, zeigen den ausgewählten Treffer an und verschwinden beim Löschen der Suche.
- Der Standtest nutzt mit „Wie POI-Zentrum“ standardmäßig die gewählte Fahrzeugposition oder Kartenmitte. Fahrzeug und Kartenmitte können weiterhin ausdrücklich gewählt werden.
- Die OCPDB-Abfrage beschränkt die Ladepunktsuche auf Deutschland und lädt alle verfügbaren Seiten bis zur Sicherheitsgrenze von 100.000 Kandidaten. Ein abgeschnittenes Ergebnis wird ausdrücklich gemeldet. Das beseitigt die Verzerrung, bei der in großen Suchkreisen die ersten 5.000 Datensätze überwiegend aus der Schweiz kamen.
- Vollständig geladene OCPDB-Abfragen werden in einer separaten Datei `.storage/driveloom-ocpdb.db` zwischengespeichert. Die Datei wird automatisch angelegt; bestehende DriveLoom-Datenbanken werden nicht migriert. Höchstens sechs Suchgebiete bleiben im Cache. Für reine Stations-/Preissuchen wird der Stand bis zu 15 Minuten wiederverwendet, für die Suche nach verfügbaren Anschlüssen höchstens 90 Sekunden. Bei einem API-Ausfall können gespeicherte Standorte und Preise angezeigt werden; die Belegung gilt dabei als unbekannt.

## Grenzen und Testhinweise

Dieser Cache ist ein Suchgebiets-Cache, noch kein planbarer Komplettimport aller Länder. Ein sehr großer Suchkreis kann beim ersten Abruf erheblich dauern oder nach 120 Sekunden abbrechen; unvollständig geladene Daten ersetzen niemals einen vollständigen Cache-Stand. Preise und Belegung vor dem Laden an der Station prüfen. Live-GPS, iPad und Home Assistant können nur auf deiner Installation abschließend geprüft werden.

## Manuelle Veröffentlichung

1. `DriveLoom_0.2.0b9_GitHub_HACS.zip` entpacken und das vollständige Stammverzeichnis in dein GitHub-Repository kopieren. Die bisherige `driveloom-card-0.2.0b8.js` im Repository entfernen; im ZIP liegt die b9-Datei.
2. Den neuen Tag **`v0.2.0b9`** anlegen und diese Notes als GitHub-Release verwenden; das Release als **Pre-release** markieren. Der stabile Tag `v0.1.14` bleibt unverändert. Hier wurde nichts auf GitHub veröffentlicht.
3. Home Assistant neu starten und die Kartenansicht neu laden. Im YAML-Ressourcenmodus die Modulressource `/driveloom/driveloom-card-0.2.0b9.js?v=0.2.0b9` setzen.

## Zweifache Prüfung

Vor Erstellung des ZIP: Python- und JavaScript-Syntax, Backend- und UI-Verhalten einschließlich Pagination über 5.000 Kandidaten, SQLite-Wiederverwendung sowie Marker-Erzeugung und Entfernung. Nach Erstellung: ZIP-Struktur, Versionsverweise, entpackte Dateien und Prüfsumme erneut kontrollieren. Eine reale Fahrt wurde nicht simuliert.
