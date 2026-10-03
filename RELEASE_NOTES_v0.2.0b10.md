# DriveLoom v0.2.0b10 — Beta

## Änderungen

- Das zusätzliche obere Menü „Schnelllader voraus · manuell“ entfällt. Die globale POI-Auswahl, gespeicherte POI-Vorlagen, Ladefilter und der Testknopf bleiben im unteren POI-Panel. Gespeicherte Suchprofile bleiben in den Daten erhalten, können in dieser Kartenansicht aber nicht mehr ausgeführt werden.
- Der POI-Standtest berechnet Abstände vom gewählten POI-Zentrum (Fahrzeug oder Kartenmitte). Zusätzlich können alle Richtungen, eine Himmelsrichtung oder bei vorhandenem Ziel die Richtung zum Routenziel gewählt werden. Im fahrenden GPS-Follow bleibt die ermittelte Fahrtrichtung maßgeblich.
- Bei Ladepunkten erscheint in Vorschau, Karten-Popup und Details zuerst der Betreiber hervorgehoben; darunter stehen, soweit vorhanden, Ort und Adresse. Technische Kennungen stehen nachgeordnet in den Details. Die normale POI-Benennung für andere Kategorien bleibt erhalten.

## Grenzen

Die Richtungswahl zum Ziel ist eine geometrische Peilung, keine Berechnung eines Straßenkorridors. Preise, Belegung und Betreiberangaben vor Ort prüfen. Kartenlayout auf iPhone/iPad und GPS während der Fahrt müssen auf der eigenen Home-Assistant-Installation geprüft werden.

## Manuelle Veröffentlichung

1. `DriveLoom_0.2.0b10_GitHub_HACS.zip` entpacken und das vollständige Stammverzeichnis in das GitHub-Repository kopieren. Die bisherige `driveloom-card-0.2.0b9.js` im Repository entfernen; im ZIP liegt die b10-Datei.
2. Den neuen Tag **`v0.2.0b10`** anlegen und diese Notes als GitHub-Release verwenden. Das Release als **Pre-release** markieren. Der stabile Tag `v0.1.14` bleibt unverändert. Es erfolgt keine automatische Veröffentlichung.
3. Home Assistant neu starten und die Kartenansicht neu laden. Im YAML-Ressourcenmodus `/driveloom/driveloom-card-0.2.0b10.js?v=0.2.0b10` als Modulressource setzen.

## Zweifache Prüfung

Quellcode und Verhalten werden vor dem Packen getestet. Das ZIP wird anschließend separat entpackt und auf vollständige Struktur, Versionen, Dateiprüfsummen und Tests geprüft. Eine reale Fahrt gehört nicht zu diesen Prüfungen.
