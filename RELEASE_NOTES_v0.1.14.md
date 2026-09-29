# DriveLoom v0.1.14

## Änderungen

- Der Import eines regionalen POI-Katalogs zeigt nun einen eigenen Fortschrittsbalken und die bislang erfasste POI-Zahl. Der Prozentwert misst die gelesenen PBF-Dateiblöcke in bis zu zwei Durchläufen. Die abschließende SQLite-Verarbeitung kann noch dauern; erst der fertige Katalog gilt als 100 % abgeschlossen.
- Die POI-Suche bietet getrennte Textfelder für allgemeine POIs und Ladestationen. Beispiel für eine gespeicherte Vorlage: „Restaurants & Fast Food“ mit Suche `McDonald's` plus „Ladestationen“ mit Betreiber `IONITY`. Beide Gruppen werden gemeinsam in Karte und Follow-Hinweis berücksichtigt.
- Bestehende Vorlagen und gespeicherte Einstellungen behalten ihren bisherigen gemeinsamen Suchbegriff, bis die Filter getrennt bearbeitet und erneut gespeichert werden.
- Ein abgewählter Katalog kann gelöscht werden, während eine andere Region importiert wird. Die gerade importierte Region bleibt gesperrt.

## Installation

ZIP entpacken und den Inhalt des ZIP-Stammverzeichnisses in das GitHub-Repository übernehmen. Anschließend den Tag `v0.1.14` und dessen Release selbst auf GitHub anlegen. In Home Assistant DriveLoom aktualisieren, Home Assistant neu starten und bei einer älteren Kartenressource den Browser-Cache aktualisieren.
