# Changelog

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
