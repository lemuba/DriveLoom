# Changelog

## 0.2.0b9 — Beta: sichtbare Suchtreffer und OCPDB-Zwischenspeicher

- Render manual charger search results as clickable DOM markers in MapLibre; keep selection and removal in sync with the search panel.
- Let manual search follow the chosen POI center by default, with explicit vehicle and map overrides.
- Page through German OCPDB candidate locations instead of stopping after 5,000 records; persist complete area snapshots in a separate SQLite cache, with short availability freshness and cautious offline fallback.
- Version the card and Lovelace resource as `driveloom-card-0.2.0b9.js`. Stable `v0.1.14` remains unchanged.

## 0.2.0b8 — Beta: OCPDB-Ladepunkte und manuelle Suche ohne KI

- OCPDB als optionale Datenquelle für deutsche Lade-POIs mit Betreiber, Stecker, Mindestleistung, eindeutig zugeordnetem Ad-hoc-Energiepreis und konservativ bewertetem Belegungsstatus. Gespeicherte Filter und GPS-Follow nutzen dieselbe Auswahl.
- Manuelle Suche voraus und Standtest direkt über OCPDB mit Radius, Richtung, CCS-Leistung, Preis- und Verfügbarkeitsfilter; Google-Maps-Übergabe. Keine KI- oder Tavily-Abfrage.
- Remove the Gemini and Tavily API key UI and network clients; delete previously saved DriveLoom search keys during setup.
- Distinguish OCM operator and station links in charging POIs; retain the explicitly marked Öschlesee third-party station link. Version the resource `driveloom-card-0.2.0b8.js`; stable `v0.1.14` remains untouched.

## 0.2.0b6 — Beta: Modellzugriff und lokale Schnelllader

- Explain the HTTP 404 from Gemini 2.5 Flash-Lite for projects without access to this model instead of reporting a generic unavailable search service.
- Offer a manual Open Charge Map charger search without a Gemini key. On a Gemini model 404, charger searches use the same OCM fallback automatically, while place and event searches show the limitation.
- Filter local stations by direction, radius and explicit CCS charging power. Their ad-hoc prices remain unknown; maximum price and arbitrary text criteria are not evaluated. Never switch to a paid model.
- Update the map resource to `driveloom-card-0.2.0b6.js` and add offline checks for the 404 and local charger normalization. Stable `v0.1.14` remains unchanged.

## 0.2.0b5 — Beta: manuelle Suche voraus und Standtest

- Add configurable, globally saved search profiles for chargers, places and events. The existing POI templates and travel archive continue to work independently.
- Add a backend-only Gemini 2.5 Flash-Lite web search with a separate admin-managed API key, no background queries, no automatic paid fallback, a 15-second request cooldown and explicit free-quota errors.
- Let a stationary user test from the vehicle or movable map center, with a compass heading or saved route destination as approximate bearing. Show up to 12 result pins, the first three in a mobile card, source links, unverified price status, travel-folder save and Google Maps handoff.
- Exclude ungrounded results, invalid links and coordinates, locations behind the chosen direction, underpowered chargers and known prices above the configured maximum. Unknown prices remain marked as unknown. Route deviation and ad-hoc price verification are not yet available.
- Add backend and frontend offline behavior checks. Version both Lovelace cards as `driveloom-card-0.2.0b5.js`. GitHub release `v0.2.0b5` is a prerelease; stable `v0.1.14` remains unchanged.

## 0.2.0b4 — Beta: sichtbare eigene Reise-POIs

- Render own travel POIs as interactive MapLibre DOM markers with the saved color and 1–2 character symbol, using the same marker path as the working vehicle pins. The map layer remains for search results and as a fallback when DOM markers are unavailable.
- Keep selected marker highlighting and click-to-focus behavior; remove markers when hidden and when the map is rebuilt. Avoid an undefined map canvas error during focus.
- Add a frontend behavior test for visible marker creation, styling, selection, and cleanup. Version both Lovelace cards as `driveloom-card-0.2.0b4.js`. GitHub release `v0.2.0b4` is a prerelease; stable `v0.1.14` remains unchanged.

## 0.2.0b3 — Beta: Reise-POI-Marker und Dokumente

- Fix the travel map source refresh after saving an existing map POI and after map style changes. Selected own POIs receive a visible, highlighted marker.
- Add a map switch for all own travel POIs, including unassigned POIs; hide global template POIs while it is active and restore them afterward. Pins remain visible if the travel panel is closed.
- Let each own POI choose a marker color and one or two alphanumeric symbol characters. Show a direct website link, assignment count, and an editable shared main note beneath the address.
- Remove the restrictive sandbox from PDF inline preview and provide a separate browser tab fallback; keep explicit Download for all document types.
- Move documents between any folders, including folders outside a trip. Check the destination trip quota or the ordinary top-level folder's quota; never reupload the document's content during a move.
- Version both Lovelace cards as `driveloom-card-0.2.0b3.js`. GitHub release `v0.2.0b3` is a prerelease; stable `v0.1.14` remains unchanged.

## 0.2.0b2 — Beta: Reisekarte und Dokumentvorschau

- Open nested travel folders through an Explorer-style tree or breadcrumbs on desktop and touch screens. Expand branches and move folders by drag and drop, with the existing move selector as a touch fallback.
- Separate own travel POIs from global research POIs on the map. Choose an existing global POI template while planning a trip; selecting an own POI highlights and focuses it at the saved detail zoom, then returns to the prior map camera.
- Create a free travel POI with a long press on the map; cancel on movement. Search for a place or address with an explicit Photon request, or paste plain coordinates and supported Google Maps coordinate URLs locally to focus the map.
- Open document details and preview supported PDFs, images and text files before downloading. Office files and other types show details and a separate Download button. Large previews require another tap.
- Version both Lovelace cards as `driveloom-card-0.2.0b2.js`. GitHub release `v0.2.0b2` is a prerelease; stable `v0.1.14` remains unchanged.

## 0.2.0b1 — Beta: Reiseplanung und Reisearchiv

- Add an independent, freely nested and movable travel folder tree with trip/archive status; it does not alter recorded GPS trips.
- Save and edit own POIs from existing map POIs, any map point or coordinates; assign one POI to several folders and display selected folders with optional descendants on the map.
- Add multiple editable folder notes, global POI notes and trip-specific POI notes.
- Store arbitrary document types as SQLite BLOB chunks in a dedicated document database. Enforce a configurable total quota per trip (initially 100 MiB), with no separate per-file setting.
- Export folders, own POIs, notes and documents to a ZIP, and restore to an empty travel archive. Upload and export use chunked Home Assistant WebSocket transfers.
- Version both Lovelace cards as `driveloom-card-0.2.0b1.js`. GitHub release `v0.2.0b1` must be marked as a prerelease.

## 0.1.14 — Importfortschritt und kombinierte POI-Filter

- Show percentage and counted POIs during the built-in two-pass PBF import; keep download progress separate. The percentage represents PBF bytes processed across both passes and stays below 100 until the catalogue is ready.
- Filter charging station names separately from general POI names. Charging operator chips and the general search can now be combined in a saved global template, such as IONITY plus McDonald's fast food.
- Keep existing templates and preferences compatible by applying their prior shared search term to both groups when no charging search is stored.
- Allow deletion of a deselected, unused catalogue while another country imports; keep the active import file protected.
- Version both Lovelace cards as `driveloom-card-0.1.14.js`.

## 0.1.13 — POI-Downloadfortschritt

- Report bytes written and the advertised total while a country extract downloads. The POI panel shows a percentage and progress bar when total size is known, or an indeterminate indicator with the downloaded amount otherwise.
- Show the subsequent SQLite import as a separate indeterminate phase so a completed transfer cannot be mistaken for a completed catalogue.
- Poll catalogue status every five seconds while downloading and retain the previous completed catalogue until import succeeds.
- Version both Lovelace cards as `driveloom-card-0.1.13.js`.

## 0.1.12 — Lokale POI-Kataloge löschen

- List all completed country catalogue files with their on-disk size, including regions no longer selected for map searches.
- Let administrators delete an unselected catalogue after confirmation; block deletion during an import and verify the exact region database before removing it. DriveLoom's central database is never a deletion target.
- Keep country selection and scheduled refresh settings separate from the file deletion. Re-selecting a deleted country triggers a fresh download and import.
- Version both Lovelace cards as `driveloom-card-0.1.12.js`.

## 0.1.11 — Länderindex und POI-Panel

- Read the full Geofabrik country index in bounded chunks before decoding JSON. Fix the partial 8 KiB response that left only the built-in German regions visible.
- Show a prominent expandable catalogue header, an inline index error and a retry button that reloads the index without restarting Home Assistant.
- Keep country checkbox targets compact with labels directly beside them, preventing horizontal overflow on tablets and phones.
- Version both Lovelace cards as `driveloom-card-0.1.11.js`.

## 0.1.10 — Länderübergreifender POI-Katalog und Installationsfix

- Remove the mandatory `osmium==4.3.1` requirement that prevented Home Assistant from loading DriveLoom on incompatible installations. A bundled PBF reader imports nodes and POI ways without external Python dependencies; an already available osmium is used for faster imports.
- Select multiple Geofabrik country extracts, including German states. Refresh them on the shared local schedule or individually; retain each last complete database after failures and migrate an existing 0.1.9 catalogue.
- Merge and deduplicate nearby POIs across the selected countries, with status, counts, and errors per country. Preserve Open Charge Map for charging stations and the existing live search when no country is selected.
- Replace the old single-region picker with a touch friendly checklist, and version both Lovelace cards as `driveloom-card-0.1.10.js`.

## 0.1.9 — Regional POI catalogue

- Import a selectable Geofabrik OSM extract into a spatially indexed SQLite catalogue on Home Assistant. A completed import atomically replaces the previous catalogue; errors retain the last good data.
- Schedule local-time refreshes and manual updates; show region, count, last successful time and errors. Only admins may change or refresh the shared catalogue.
- Apply saved POI presets and text filters locally, querying both vehicle-near and visible-map POIs for GPS follow and map markers.
- Set a 500–10,000 map result limit (3,000 when first enabling the catalogue). Keep OCM charging data and the old live search when the catalogue is off.
- Version both Lovelace cards as `driveloom-card-0.1.9.js`.

## 0.1.8 — POI touch scrolling

- Let the right POI settings panel scroll fully on iPad and retain its scroll position when refreshed.
- Swipe the visible POI rows to browse by touch; a compact slider offers direct positioning within the loaded result list, alongside the existing arrow buttons.
- Support mouse wheels and trackpads over the POI list without rendering all results as HTML rows.
- Version both Lovelace cards as `driveloom-card-0.1.8.js`.

## 0.1.7 — POI jumps and detail inspection

- Add double arrow buttons to jump to the first or last loaded POI window; keep one-step browsing and 44-pixel touch targets.
- Add a configurable POI detail zoom (12–20) in the POI panel and saved global templates, with 16 as the default for older templates.
- Tap a POI to inspect it on the map while live GPS positions continue updating without recentering the camera. A compact card keeps the precise Google Maps destination available.
- Return to vehicle follow with its prior zoom and current travel heading, or return to the previous camera in the stationary test preview.
- Version both Lovelace cards as `driveloom-card-0.1.7.js`.

## 0.1.6 — POI presets and browsing in GPS follow

- Add a compact selector for saved global POI presets to the map suggestion card; switches reload results around the current vehicle and show loading or failure states without offering old targets as new ones.
- Add up/down arrows to move the visible 1–3-POI window by one farther or nearer result, with a position indicator and stable target anchoring as GPS fixes advance.
- Keep target confirmation tied to the selected POI, including when browsing farther ahead.
- Version both Lovelace cards as `driveloom-card-0.1.6.js`.

## 0.1.5 — Adjustable POI list and driving view

- Save a 1–3 POI count for live follow and the stationary preview, retaining three as the default for existing users.
- Move the suggestion panel slightly lower on phones.
- Add a reversible driving view that hides the title and upper control rows, grows the map by their height and keeps a restore button on the map.
- Preserve GPS follow, basemap and zoom while resizing the map for the view switch.
- Version both Lovelace cards as `driveloom-card-0.1.5.js`.

## 0.1.4 — Larger three-destination POI suggestions

- Show up to three eligible POIs ahead in separate, larger touch targets during GPS follow; show fewer rows when fewer matches are available.
- Keep all three suggestions ordered by current straight-line distance and confirm the specifically tapped destination before Google Maps opens.
- Increase the mobile card width, name and distance text, and confirmation button sizes for use on a phone.
- Add a two-minute test preview in the POI panel: show the three nearest loaded POIs while stationary, clearly labeled without implying a direction of travel.
- Version both Lovelace cards as `driveloom-card-0.1.4.js`.

## 0.1.3 — POIs ahead during GPS follow

- Suggest the nearest loaded and filtered POI ahead of the followed vehicle, with an explicitly labeled straight-line distance.
- Consider all selected categories and all chosen charging operators together; keep the current suggestion stable until a clearly closer POI appears or it is passed.
- Show a two-step Google Maps navigation handoff after tapping the compact map hint.
- Add a saved switch in the POI panel to control the hint, and hide it without a recent reliable heading or when follow ends.
- Version both Lovelace cards as `driveloom-card-0.1.3.js`.

## 0.1.2 — Live GPS follow camera

- Keep GPS follow active across OSM, OSM+, Topo, Satellite and 3D, with the chosen zoom preserved and the active style shown alongside GPS.
- Recenter after phone GPS status updates (checked every five seconds during live follow) and style changes; keep the existing MapLibre map instance while the vehicle moves.
- Rotate the live map toward the direction of successive plausible fixes, retaining the last reliable heading through jitter, stops and gaps.
- Allow the GPS button to turn follow off; intentional panning and historical track actions still release the live camera.
- Bundle both Lovelace cards under the versioned `driveloom-card-0.1.2.js` resource.

## 0.1.1 — Entity name translations

- Show each sensor's translated function beside its vehicle name instead of repeating only the vehicle name.
- Apply the same correction to the global date and select controls.
- Keep unique IDs and existing entity IDs unchanged.

## 0.1.0 — Initial DriveLoom package

- Independent Home Assistant integration and Lovelace cards based on the tested Cardata Analytics 0.1.75 behavior.
- All DriveLoom-owned persistent vehicle, GPS, trip, route, template and map-preference data use one SQLite database.
- Daily consumption history and newly observed source and calculated counter samples are stored in database tables.
- Trip analytics and SoC repairs use DriveLoom samples; historical data from Cardata Analytics is not imported.
- No database backup or restore function in this release.
