# Telemetry Analysis Report

## 1. Speed statistics

- **Mean speed:** 62.35 km/h
- **Max speed:** 110 km/h
- **Min speed:** 0 km/h
- **Samples:** 135

## 2. Numeric summary (mean, max, min)

| Column               |       Mean |        Max |        Min |
|----------------------|------------|------------|------------|
| speed_kmh            |      62.35 |      110.0 |        0.0 |
| throttle_pct         |      26.77 |       75.0 |        0.0 |
| brake_pct            |      13.24 |       75.0 |        0.0 |
| regen_brake          |       0.27 |        1.0 |        0.0 |
| motor_rpm            |    3096.69 |     5463.0 |        0.0 |
| battery_voltage      |      396.8 |      400.8 |      391.5 |
| battery_current      |      30.23 |      105.7 |      -53.5 |
| battery_soc_pct      |      83.01 |       87.0 |       79.0 |
| battery_temp_c       |      31.13 |       40.2 |       18.5 |
| motor_temp_c         |      53.42 |       69.4 |       19.2 |
| inverter_temp_c      |      55.49 |       71.7 |       20.1 |
| cabin_temp_c         |      28.02 |       34.3 |       22.0 |
| odometer_km          |   45244.65 |    45254.8 |    45234.5 |
| power_kw             |      11.88 |      41.39 |     -21.42 |
| energy_used_kw       |        0.0 |        0.0 |        0.0 |

## 3. Warnings (event_type = WARNING)

| Timestamp            | Event description                                  |
|----------------------|----------------------------------------------------|
| 2026-02-05 08:18:45.920 | Lane departure detected - left                     |
| 2026-02-05 08:21:51.920 | Battery temperature elevated                       |
| 2026-02-05 08:25:18.920 | ABS limited functionality                          |
| 2026-02-05 08:25:26.920 | ABS fault requires service                         |
| 2026-02-05 08:30:26.560 | Thermal management degraded                        |
| 2026-02-05 08:30:40.180 | Battery temperature rising                         |
| 2026-02-05 08:30:55.920 | Motor temperature rising                           |

## 4. Threshold breaches (with timestamp)

When a value exceeds the configured max or goes below the configured min, the timestamp is recorded below.

No threshold breaches detected.