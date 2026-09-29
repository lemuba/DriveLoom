# Changelog

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
