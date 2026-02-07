# Telemetry CSV Analyzer

Reads a telemetry CSV and generates a Markdown report with speed statistics, warnings, and threshold breach timestamps.
It uses docker to containerize the entire program for easy usage, and uploads the logs to an AWS S3 bucket via Github actions.

## CSV format

If you want to use the telemetry log generator, your .csv file must have these (in any order):

| Column | Description |
|--------|-------------|
| `timestamp` | Time of the sample |
| `speed_kmh` | Speed in km/h |
| `throttle_pct` | Throttle percentage |
| `brake_pct` | Brake percentage |
| `regen_brake` | Regen braking value |
| `motor_rpm` | Motor RPM |
| `battery_voltage` | Battery voltage |
| `battery_current` | Battery current |
| `battery_soc_pct` | State of charge (%) |
| `battery_temp_c` | Battery temperature (°C) |
| `motor_temp_c` | Motor temperature (°C) |
| `inverter_temp_c` | Inverter temperature (°C) |
| `cabin_temp_c` | Cabin temperature (°C) |
| `odometer_km` | Odometer in km |
| `power_kw` | Power in kW |
| `energy_used_kw` | Energy used in kW |
| `event_type` | `SYSTEM`, `INFO`, or `WARNING` |
| `event_description` | Description of the event |

### Docker Setup

## Build the Docker image

From the `telemetry-pipeline` directory:

```bash
docker build -t telemetry-analyzer .
```

### Run with Docker

Mount your data directory and run the analyzer:

```bash
docker run --rm -v "$(pwd)/data:/data" telemetry-analyzer /data/your_file.csv
```

**Windows PowerShell:**
```powershell
docker run --rm -v "${PWD}/data:/data" telemetry-analyzer /data/your_file.csv
```

### Specify output path with Docker

```bash
docker run --rm -v "$(pwd)/data:/data" telemetry-analyzer /data/your_file.csv -o /data/report.md
```

The report will be saved in your local `data/` folder.

### Non-docker Setup

##If you don't want to use docker, you can also install it like this:

```bash
python -m pip install -r requirements.txt
```

Then run it.

```bash
python src/analyze.py path/to/telemetry.csv
```

Report is written to `path/to/telemetry_report.md` by default.

Specify output path:

```bash
python src/analyze.py path/to/telemetry.csv -o report.md
```


## Report contents

1. **Speed statistics** – Mean, max, and min speed (km/h).
2. **Numeric summary** – Mean, max, and min for all numeric columns.
3. **Warnings** – Every row where `event_type` is `WARNING`, with timestamp and `event_description`.
4. **Threshold breaches** – For each configured threshold, every timestamp where a value exceeded the limit (e.g. speed over max, battery temp over max, SOC below min).

## Configuring thresholds

Edit `THRESHOLDS` in `src/analyze.py` to set max/min limits. When a value goes over `max` or under `min`, that row’s timestamp is included in the report.

Default example:

```python
THRESHOLDS = {
    "speed_kmh": {"max": 120},
    "battery_temp_c": {"max": 50},
    "motor_temp_c": {"max": 90},
    "inverter_temp_c": {"max": 75},
    "battery_soc_pct": {"min": 15},
    "cabin_temp_c": {"max": 40, "min": 5},
}
```

## Sample data

Run the analyzer on the included sample:

```bash
python src/analyze.py src/sample_telemetry.csv -o src/sample_report.md
```

Then open `src/sample_report.md` to see the report format.
