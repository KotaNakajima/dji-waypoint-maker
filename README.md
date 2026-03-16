# Drone Route Maker

A tool for generating DJI-compatible drone flight routes (WPMZ/KMZ) for automated survey missions. Creates waypoint-based and area-mapping flight plans that can be imported into DJI Pilot 2.

> **Disclaimer**: This tool generates flight route files only. Users are responsible for ensuring safe and legal drone operations. Always comply with local aviation regulations, check airspace restrictions, and perform pre-flight safety checks before each mission.

## Supported Drones

| Model | Key | droneEnum | subEnum | payloadEnum |
|-------|-----|-----------|---------|-------------|
| Mavic 3 Enterprise | M3E | 77 | 0 | 66 |
| Mavic 3 Thermal | M3T | 77 | 1 | 67 |
| Mavic 3 Multispectral | M3M | 77 | 0 | 66 (proxy) |

## Route Types

- **VD (Vertical Down)**: Single overhead photo per target at configurable height. Use case: orthomosaic, mapping.
- **OBL (Oblique Photography)**: Angled photos from two directions (row + perpendicular) with 4x zoom. Generates two separate flight files. Use case: crop observation, multi-angle analysis.
- **mapping2d (Area Mapping)**: Area-based survey with configurable overlap. Serpentine flight path with automatic photo triggering. Use case: large area mapping, orthophoto generation.

## Prerequisites

- Python 3.8+
- For shapefile conversion: `pyproj`, `pyshp`
- Core flight generation uses only Python standard library

```bash
pip install -r requirements.txt
```

## Quick Start

### Generate Flight Routes

```bash
python generate_flight.py
```

Interactive prompts guide you through:
1. Route type (VD / OBL / mapping2d)
2. Input data — CSV file (VD/OBL) or manual 4-corner coordinates (mapping2d)
3. Route-specific settings (gimbal angle for OBL, overlap/direction for mapping2d)
4. Drone model (M3E / M3T / M3M)
5. Flight parameters (height, speed) — GSD and blur-free max speed are displayed for reference
6. Flight name and output directory

#### mapping2d Direction Calculation

The tool calculates the optimal flight direction based on the minimum area bounding rectangle of the survey polygon. This produces efficient serpentine coverage even for irregular quadrilaterals, unlike simple longest-edge alignment.

#### Blur-free Speed Reference

After entering flight height, the tool displays the ground sample distance (GSD) and maximum blur-free speed for common shutter speeds:

```
  GSD: 1.37 cm/px at 50m
  Blur-free max speed (max 0.5px motion blur):
    1/500 : 3.4 m/s
    1/800 : 5.5 m/s
    1/1000: 6.8 m/s
    1/1600: 10.9 m/s
    1/2000: 13.7 m/s
```

### Convert Shapefiles to CSV

```bash
python convert_shp2csv.py
```

Converts ESRI Shapefiles (polygon) to CSV format. Supports JGD2011, UTM, and Tokyo datum coordinate systems.

### Generate Template CSV

```bash
python src/generate_default_csv.py --output test.csv --num 5 --width 3 --height 3
python src/generate_grid_csv.py --output grid.csv --ew-count 10 --ns-count 10
```

## CSV Format

Each row = one target object with 4 corner coordinates (WGS84):

```
lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4
```

With optional identifier column:

```
lat1,lon1,lat2,lon2,lat3,lon3,lat4,lon4,SerialNumb
```

Header rows are auto-detected. `SerialNumb` takes priority over `plot_id` if both exist.

## Output Files

- **`.zip` (WPMZ)**: Import into DJI Pilot 2 app
- **`.kmz`**: Preview in Google Earth

Package structure:
```
wpmz/
  template.kml      # Mission template (WPML spec 1.0.2)
  waylines.wpml     # Execution waylines (WPML spec 1.0.6)
```

Output is saved to `output/{flight_name}_{timestamp}/`.

For missions with many waypoints, the tool offers splitting into multiple files.

## Project Structure

```
generate_flight.py          # Main entry point
convert_shp2csv.py          # Shapefile to CSV converter
lib/
  drone_config.py           # Drone model configs and camera specs
  csv_parser.py             # CSV input parser
  object_calculator.py      # Center/heading calculator
  file_creator.py           # VD + OBL KML/WPML generator
  mapping_creator.py        # mapping2d KML/WPML generator
  package_creator.py        # ZIP/KMZ packager
src/
  generate_default_csv.py   # Template CSV generator
  generate_grid_csv.py      # Grid CSV generator
```

## License

MIT
