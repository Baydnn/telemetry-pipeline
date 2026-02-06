#!/usr/bin/env python3
"""
Telemetry CSV analyzer: reads a CSV with vehicle/EV telemetry columns,
computes summary stats, extracts warnings, and reports threshold breaches with timestamps.
Outputs a Markdown report.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Expected CSV columns (order flexible; we validate presence)
EXPECTED_COLUMNS = [
    "timestamp",
    "speed_kmh",
    "throttle_pct",
    "brake_pct",
    "regen_brake",
    "motor_rpm",
    "battery_voltage",
    "battery_current",
    "battery_soc_pct",
    "battery_temp_c",
    "motor_temp_c",
    "inverter_temp_c",
    "cabin_temp_c",
    "odometer_km",
    "power_kw",
    "energy_used_kw",
    "event_type",
    "event_description",
]

# Optional column name typo seen in CSVs
COLUMN_ALIASES = {"event_descirption": "event_description"}

# Thresholds: when a value goes over max or under min, we record the timestamp.
# Omit min/max for columns you don't want to check.
THRESHOLDS = {
    "speed_kmh": {"max": 120},
    "battery_temp_c": {"max": 50},
    "motor_temp_c": {"max": 90},
    "inverter_temp_c": {"max": 75},
    "battery_soc_pct": {"min": 15},
    "cabin_temp_c": {"max": 40, "min": 5},
}

# Numeric columns for stats and threshold checks (must be coercible to float)
NUMERIC_COLUMNS = [
    "speed_kmh",
    "throttle_pct",
    "brake_pct",
    "regen_brake",
    "motor_rpm",
    "battery_voltage",
    "battery_current",
    "battery_soc_pct",
    "battery_temp_c",
    "motor_temp_c",
    "inverter_temp_c",
    "cabin_temp_c",
    "odometer_km",
    "power_kw",
    "energy_used_kw",
]


def load_csv(path: Path) -> pd.DataFrame:
    """Load CSV and normalize column names (aliases)."""
    df = pd.read_csv(path)
    # Normalize optional typo
    rename = {k: v for k, v in COLUMN_ALIASES.items() if k in df.columns}
    if rename:
        df = df.rename(columns=rename)
    return df


def validate_columns(df: pd.DataFrame) -> None:
    """Ensure all expected columns exist."""
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}. Found: {list(df.columns)}")


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce numeric columns to float; non-numeric become NaN for that cell."""
    out = df.copy()
    for col in NUMERIC_COLUMNS:
        if col not in out.columns:
            continue
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def build_speed_stats(df: pd.DataFrame) -> dict:
    """Compute mean, max, min for speed_kmh (ignoring NaN)."""
    s = df["speed_kmh"].dropna()
    if s.empty:
        return {"mean_kmh": None, "max_kmh": None, "min_kmh": None, "count": 0}
    return {
        "mean_kmh": round(s.mean(), 2),
        "max_kmh": round(s.max(), 2),
        "min_kmh": round(s.min(), 2),
        "count": int(len(s)),
    }


def get_warnings(df: pd.DataFrame) -> pd.DataFrame:
    """Rows where event_type is WARNING, with timestamp and event_description."""
    if "event_type" not in df.columns:
        return pd.DataFrame()
    mask = df["event_type"].astype(str).str.upper() == "WARNING"
    out = df.loc[mask, ["timestamp", "event_type", "event_description"]].copy()
    return out.drop_duplicates().reset_index(drop=True)


def get_threshold_breaches(df: pd.DataFrame) -> list[dict]:
    """For each threshold, collect (timestamp, column, value, limit_type, limit_value)."""
    breaches = []
    for col, limits in THRESHOLDS.items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        ts = df.loc[series.index, "timestamp"]
        for limit_type, limit_value in limits.items():
            if limit_type == "max":
                over = series > limit_value
            else:  # min
                over = series < limit_value
            for idx in series.index[over]:
                breaches.append({
                    "timestamp": df.at[idx, "timestamp"],
                    "column": col,
                    "value": series.at[idx],
                    "limit_type": limit_type,
                    "limit_value": limit_value,
                })
    return breaches


def write_report(
    out_path: Path,
    speed_stats: dict,
    warnings_df: pd.DataFrame,
    breaches: list[dict],
    numeric_summary: pd.DataFrame,
) -> None:
    """Write Markdown report to out_path."""
    lines = [
        "# Telemetry Analysis Report",
        "",
        "## 1. Speed statistics",
        "",
    ]
    if speed_stats["count"] == 0:
        lines.append("No valid speed data.")
    else:
        lines.extend([
            f"- **Mean speed:** {speed_stats['mean_kmh']} km/h",
            f"- **Max speed:** {speed_stats['max_kmh']} km/h",
            f"- **Min speed:** {speed_stats['min_kmh']} km/h",
            f"- **Samples:** {speed_stats['count']}",
            "",
        ])

    lines.extend([
        "## 2. Numeric summary (mean, max, min)",
        "",
    ])
    if numeric_summary.empty:
        lines.append("No numeric summary available.")
    else:
        lines.append("| Column | Mean | Max | Min |")
        lines.append("|--------|------|-----|-----|")
        for _, row in numeric_summary.iterrows():
            lines.append(f"| {row['column']} | {row['mean']} | {row['max']} | {row['min']} |")
        lines.append("")

    lines.extend([
        "## 3. Warnings (event_type = WARNING)",
        "",
    ])
    if warnings_df.empty:
        lines.append("No WARNING events found.")
    else:
        lines.append("| Timestamp | Event description |")
        lines.append("|-----------|--------------------|")
        for _, row in warnings_df.iterrows():
            ts = row.get("timestamp", "")
            desc = row.get("event_description", "")
            # Escape pipe in description for markdown table
            desc = str(desc).replace("|", "\\|")
            lines.append(f"| {ts} | {desc} |")
        lines.append("")

    lines.extend([
        "## 4. Threshold breaches (with timestamp)",
        "",
        "When a value exceeds the configured max or goes below the configured min, the timestamp is recorded below.",
        "",
    ])
    if not breaches:
        lines.append("No threshold breaches detected.")
    else:
        lines.append("| Timestamp | Column | Value | Limit (max/min) |")
        lines.append("|-----------|--------|-------|-----------------|")
        for b in breaches:
            val = b["value"]
            if isinstance(val, float):
                val = round(val, 2)
            limit_str = f"{b['limit_type']}={b['limit_value']}"
            lines.append(f"| {b['timestamp']} | {b['column']} | {val} | {limit_str} |")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def numeric_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per numeric column with columns: column, mean, max, min (rounded)."""
    rows = []
    for col in NUMERIC_COLUMNS:
        if col not in df.columns:
            continue
        s = df[col].dropna()
        if s.empty:
            continue
        rows.append({
            "column": col,
            "mean": round(s.mean(), 2),
            "max": round(s.max(), 2),
            "min": round(s.min(), 2),
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze telemetry CSV and generate Markdown report.")
    parser.add_argument("input_csv", type=Path, help="Path to input CSV file")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output Markdown report path (default: <input_csv_stem>_report.md)",
    )
    args = parser.parse_args()

    if not args.input_csv.is_file():
        print(f"Error: input file not found: {args.input_csv}", file=sys.stderr)
        return 1

    out_path = args.output or (args.input_csv.parent / f"{args.input_csv.stem}_report.md")

    try:
        df = load_csv(args.input_csv)
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return 1

    try:
        validate_columns(df)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    df = coerce_numeric(df)
    speed_stats = build_speed_stats(df)
    warnings_df = get_warnings(df)
    breaches = get_threshold_breaches(df)
    numeric_summary = numeric_summary_table(df)

    write_report(out_path, speed_stats, warnings_df, breaches, numeric_summary)
    print(f"Report written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
