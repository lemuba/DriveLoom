# DriveLoom v0.2.0b1 — Beta

## Neu

- **Reisen** in der Fahrzeugkarte: eigene Ordner und Reiseordner auf beliebig vielen Ebenen anlegen, umbenennen, verschieben und archivieren. Die Struktur ist unabhängig von aufgezeichneten Fahrten.
- POIs aus der Karte oder von einem beliebigen Kartenpunkt als eigene, editierbare POIs speichern. Mehrfachzuordnung zu Reiseordnern, globale und reisebezogene POI-Notizen sowie mehrere Ordnernotizen.
- Ausgewählte eigene POIs auf der Karte anzeigen; Unterordner lassen sich ein- oder ausschließen.
- PDF, Bilder, Word, Excel und andere Dateien in Ordnern einer Reise speichern. Die Dokumente liegen in einer **separaten SQLite-Datenbank** in BLOB-Blöcken. Maßgeblich ist nur das einstellbare **Gesamtvolumen pro Reise**, anfangs 100 MiB; DriveLoom setzt keine zusätzliche Dokumentgrenze.
- Reisearchiv als ZIP exportieren und in ein **leeres** Reisearchiv zurückspielen. Der Export enthält Reiseordner, eigene POIs, Notizen und Dokumente. Er ist kein vollständiges Home-Assistant-Backup und umfasst weder Fahrzeugdaten noch regionale POI-Kataloge.

## Beta und manuelle Veröffentlichung

1. `DriveLoom_0.2.0b1_GitHub_HACS.zip` herunterladen und entpacken. Den **Inhalt des ZIP-Stammverzeichnisses** selbst in das GitHub-Repository übernehmen.
2. Auf GitHub einen neuen Tag **`v0.2.0b1`** auf genau diesem Stand erstellen. Ein Release mit diesem Tag anlegen, diese Notes als Beschreibung übernehmen, **„Set as a pre-release“** aktivieren und optional dasselbe ZIP als Asset hochladen. Die vorhandene stabile Version `v0.1.14` bleibt der stabile Kanal.
3. Wer HACS nutzt, kann Betaversionen in den HACS-Optionen dieser Integration einschalten und die Beta auswählen. Für eine manuelle Installation das ZIP aus dem GitHub-Release herunterladen, entpacken und `custom_components/driveloom` in die HA-Konfiguration kopieren. Danach Home Assistant neu starten und gegebenenfalls den Browser-Cache der Karte aktualisieren.

## Testhinweise

- In **Reisen** eine Reise mit Unterordner anlegen, einen bestehenden Karten-POI sowie einen freien Punkt übernehmen und die Unterordneranzeige umschalten.
- Eine globale und eine reisebezogene POI-Notiz anlegen; dasselbe POI einem zweiten Ordner zuordnen.
- Eine Datei hochladen, herunterladen und das Gesamtvolumen prüfen. Dann den gesamten Reiseexport laden und die Wiederherstellung nur in einem zuvor geleerten Testarchiv ausprobieren.
- Diese Beta wurde mit Offline-Backendtests, den bestehenden Kartentests sowie ZIP-Prüfungen getestet. Die Bedienung unter echtem Home Assistant und auf iPhone/iPad benötigt noch Praxistests.
