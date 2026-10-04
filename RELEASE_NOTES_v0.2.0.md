# DriveLoom v0.2.0 — aktuelles Release

## Neu

- Der automatische GPS-Fahrtstart unterstützt neben einem SSID-Sensor nun einen vorhandenen Home-Assistant-**Binärsensor**. In **Tracking → GPS-Quellen verwalten** pro Fahrzeug die GPS-Quelle und den Auslöser wählen. `on` bedeutet verbunden; `off`, `unknown` und `unavailable` gelten als getrennt.
- Die bewährte Unterbrechung, Wiederaufnahme und das verzögerte Beenden der automatischen Fahrt gelten für beide Auslöser. Ein manuell gestoppter Automat startet erst nach einem Aus- und erneuten Einschalten wieder. Vorhandene SSID-Regeln bleiben ohne Migration nutzbar.
- Kartenposition, Zoom und offenes POI-Panel können nach einem App-Wechsel oder Karten-Neuaufbau wiederhergestellt werden. GPS-Follow behält die Fahrzeugkamera.
- Die Frontend-Ressource und die Integration tragen nun die reguläre Version `0.2.0`.

## Installation und Veröffentlichung

1. Das vollständige ZIP entpacken und die enthaltenen Dateien ins GitHub-Repository übernehmen. Vorherige versionierte Frontend-Dateien, alte Versions-Notizen und veraltete Übergabetexte im Repository **gezielt entfernen**: Ein GitHub-Datei-Upload löscht vorhandene Dateien nicht automatisch. Das ZIP enthält nur die aktuelle Release-Notiz.
2. Den Tag **`v0.2.0`** anlegen und das GitHub-Release als **reguläres Release** veröffentlichen, ohne Pre-release-Kennzeichnung. Dieser Schritt wird vom Projektinhaber ausgeführt; dieses Paket veröffentlicht nichts automatisch.
3. Home Assistant nach der Übernahme neu starten und die Karte neu laden. Im YAML-Ressourcenmodus `/driveloom/driveloom-card-0.2.0.js?v=0.2.0` als Modulressource eintragen.

## Prüfung auf der eigenen Installation

- Eine vorhandene SSID-Regel unverändert starten, trennen und wieder verbinden.
- Für ein Testfahrzeug einen vorhandenen `binary_sensor.*` wählen: `off → on` startet, `on → off` pausiert, erneutes `on` nimmt wieder auf. Nach längerem `off` endet die automatische Fahrt. Manuelles Stoppen bei `on` darf nicht sofort neu starten.
- GPS-Punktübernahme, optionale iPhone-Standortanfrage und Verhalten in der Companion-App prüfen. Ein Binärsensor muss bereits durch Home Assistant oder eine andere Integration/Automation bereitgestellt werden.
- Auf iPad/iPhone POI-Panel und verschobenen Kartenausschnitt nach einem App-Wechsel prüfen.

Offline-Tests prüfen die Regeln, Oberflächendaten und Paketdateien; eine reale Fahrt und das Verhalten eines konkreten iPhones/Home Assistant sind damit nicht simuliert. Die ausführliche README-Funktionsliste und bebilderte Installation werden nach den neuen Screenshots überarbeitet.
