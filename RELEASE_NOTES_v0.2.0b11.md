# DriveLoom v0.2.0b11 — Beta

## Änderungen

- Beim erneuten Öffnen der Karte bleibt das POI-Panel geöffnet. Kartenmitte und Zoom der Rechercheansicht werden wiederhergestellt, statt die Karte erneut auf die Fahrzeuge einzupassen.
- Die Ansicht wird im aktuellen Browser-Tab unmittelbar gesichert und zusätzlich mit den bisherigen Home-Assistant-Kartenpräferenzen des Benutzers gespeichert. Auch der Wechsel zu Safari und zurück auf dem iPad löst damit keinen absichtlichen Rücksprung zur Standardansicht aus.
- Im aktiven GPS-Follow bleibt die Fahrzeugposition maßgeblich. Das Schließen des POI-Panels beendet die temporäre Tab-Ansicht.
- `PROJEKT_UEBERGABE_v0.2.0b11.md` enthält den ausführlichen Projekt-Übergabe-Prompt mit Architektur, Datenhaltung, Test- und Releaseablauf.

## Test auf iPad

1. In **POIs** eine Vorlage und **Kartenmitte** wählen, die Karte auf einen anderen Ort bewegen und den Zoom ändern.
2. Zu Safari oder einer anderen App wechseln, dann zu Home Assistant zurückkehren. POI-Panel, Ort und Zoom prüfen. Auch einen kompletten Neuladevorgang der Karte prüfen.
3. POI-Panel schließen und erneut öffnen. Anschließend GPS-Follow einschalten und kontrollieren, dass die Fahrzeugkamera weiterhin folgt.

Die Browser-Laufzeit des iPads und eine reale Home-Assistant-Installation stehen den Offline-Tests nicht zur Verfügung. Ein bereits offenes Einzel-POI-Popup wird nach einem kompletten Seitenneuladen nicht automatisch wieder geöffnet. Falls Safari den Tab-Speicher sperrt, greift die zuletzt gespeicherte Home-Assistant-Präferenz.

## Manuelle Veröffentlichung

1. `DriveLoom_0.2.0b11_GitHub_HACS.zip` entpacken und das vollständige Stammverzeichnis ins GitHub-Repository kopieren. Die alte `driveloom-card-0.2.0b10.js` entfernen; im ZIP ist die b11-Datei enthalten.
2. Den Tag **`v0.2.0b11`** erstellen und diese Notes als GitHub-Release verwenden. Als **Pre-release** markieren. Der stabile Tag `v0.1.14` bleibt bestehen.
3. Home Assistant neu starten und die Karte neu laden. Im YAML-Ressourcenmodus `/driveloom/driveloom-card-0.2.0b11.js?v=0.2.0b11` als JavaScript-Modul eintragen.

Es wurde nichts automatisch auf GitHub veröffentlicht. Vor dem Packen wurden Syntax und Verhalten geprüft; danach werden das entpackte ZIP und dessen Tests erneut kontrolliert.
