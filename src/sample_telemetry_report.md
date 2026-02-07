# Telemetry Analysis Report

## 1. Speed statistics

- **Mean speed:** 43.93 km/h
- **Max speed:** 125 km/h
- **Min speed:** 0 km/h
- **Samples:** 14

## 2. Numeric summary (mean, max, min)

| Column               |       Mean |        Max |        Min |
|----------------------|------------|------------|------------|
| speed_kmh            |      43.93 |      125.0 |        0.0 |
| throttle_pct         |       22.5 |       80.0 |        0.0 |
| brake_pct            |       2.86 |       30.0 |        0.0 |
| regen_brake          |       2.86 |       20.0 |        0.0 |
| motor_rpm            |    2057.14 |     6000.0 |        0.0 |
| battery_voltage      |     373.21 |      380.0 |      368.0 |
| battery_current      |       -8.0 |       12.0 |      -32.0 |
| battery_soc_pct      |       88.5 |       95.0 |       82.0 |
| battery_temp_c       |      30.14 |       52.0 |       22.0 |
| motor_temp_c         |      42.14 |       62.0 |       25.0 |
| inverter_temp_c      |      36.57 |       48.0 |       24.0 |
| cabin_temp_c         |      21.43 |       23.0 |       20.0 |
| odometer_km          |    1201.77 |     1202.5 |     1200.5 |
| power_kw             |      19.43 |       62.0 |        0.0 |
| energy_used_kw       |       0.21 |       0.31 |        0.0 |

## 3. Warnings (event_type = WARNING)

| Timestamp            | Event description                                  |
|----------------------|----------------------------------------------------|
| 2025-02-05T08:05:00  | High speed sustained                               |
| 2025-02-05T08:06:00  | Speed limit exceeded                               |
| 2025-02-05T08:20:00  | Battery temperature rising in sun                  |
| 2025-02-05T08:25:00  | Battery temp threshold approached                  |

## 4. Threshold breaches (with timestamp)

When a value exceeds the configured max or goes below the configured min, the timestamp is recorded below.

| Timestamp            | Column               |      Value | Limit (max/min) |
|----------------------|----------------------|------------|-----------------|
| 2025-02-05T08:06:00  | speed_kmh            |        125 | max=120         |
| 2025-02-05T08:25:00  | battery_temp_c       |         52 | max=50          |
