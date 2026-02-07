#!/usr/bin/env python3
"""
Telemetry CSV analyzer: reads a CSV with vehicle/EV telemetry columns,
computes summary stats, extracts warnings, and reports threshold breaches with timestamps.
Outputs a Markdown report.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

# Expected CSV columns (order flexible, presence validated)
# If they any of these columns are missing, the script will raise an error. 
# In the future, I will problably add a way to automatically recognize the columns and add them to the list.
# Or I will make it take in a .json file with the specifications for each report.
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

# Thresholds: when a value goes over max or under min, we record the timestamp
# Omit min or max for columns you don't want to check
THRESHOLDS = {
    "speed_kmh": {"max": 120},
    "battery_temp_c": {"max": 50},
    "motor_temp_c": {"max": 90},
    "inverter_temp_c": {"max": 75},
    "battery_soc_pct": {"min": 15},
    "cabin_temp_c": {"max": 40, "min": 5},
}

# Numeric columns for stats and threshold checks (must be changeable to float)
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

# Loads the CSV file in the first place, reads the dataframe, each row is a data point and each column is a field
# Also add typo support for the column names
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize optional typo
    rename = {k: v for k, v in COLUMN_ALIASES.items() if k in df.columns}
    if rename:
        df = df.rename(columns=rename)
    return df

# The part of the code that throws an error if the columns are missing.
def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}. Found: {list(df.columns)}")

#Changning or coercing the numeric columns to float, making all of the columns actual numbers
def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in NUMERIC_COLUMNS:
        if col not in out.columns:
            continue
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out

#Building the speed statistics, mean, max, min for speed_kmh (ignoring any not numbers or NaN)
def build_speed_stats(df: pd.DataFrame) -> dict:
    s = df["speed_kmh"].dropna()
    if s.empty:
        return {"mean_kmh": None, "max_kmh": None, "min_kmh": None, "count": 0}
    return {
        "mean_kmh": round(s.mean(), 2),
        "max_kmh": round(s.max(), 2),
        "min_kmh": round(s.min(), 2),
        "count": int(len(s)),
    }

#Getting the warnings, event_type is WARNING, with timestamp and event_description
#So if there are no warnings, it will return an empty dataframe
#If there are warnings, it will return a dataframe with the timestamp, event_type, and event_description
#It will also remove any duplicate warnings
def get_warnings(df: pd.DataFrame) -> pd.DataFrame:
    if "event_type" not in df.columns:
        return pd.DataFrame()
    mask = df["event_type"].astype(str).str.upper() == "WARNING"
    out = df.loc[mask, ["timestamp", "event_type", "event_description"]].copy()
    return out.drop_duplicates().reset_index(drop=True)

#Getting the threshold breaches, for each threshold, collect (timestamp, column, value, limit_type, limit_value)
#By "breach", I mean that the valeu is over the max or under the min
#So if there are no threshold breaches, it will return an empty list
#If there are threshold breaches, it will return a list of dictionaries with the timestamp, column, value, limit_type, and limit_value
#It will also remove any duplicate threshold breaches
def get_threshold_breaches(df: pd.DataFrame) -> list[dict]:
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

#Writing the report, the report is a markdown file with the following sections:
#1. Speed statistics
#2. Numeric summary
#3. Warnings
#4. Threshold breaches
def write_report(
    out_path: Path,
    speed_stats: dict,
    warnings_df: pd.DataFrame,
    breaches: list[dict],
    numeric_summary: pd.DataFrame,
) -> None:
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
        # Format with fixed column widths for better alignment
        col_width = 20  # Column name width
        num_width = 10  # Numeric value width
        lines.append(f"| {'Column':<{col_width}} | {'Mean':>{num_width}} | {'Max':>{num_width}} | {'Min':>{num_width}} |")
        lines.append(f"|{'-'*(col_width+2)}|{'-'*(num_width+2)}|{'-'*(num_width+2)}|{'-'*(num_width+2)}|")
        for _, row in numeric_summary.iterrows():
            lines.append(
                f"| {row['column']:<{col_width}} | "
                f"{row['mean']:>{num_width}} | "
                f"{row['max']:>{num_width}} | "
                f"{row['min']:>{num_width}} |"
            )
        lines.append("")

    lines.extend([
        "## 3. Warnings (event_type = WARNING)",
        "",
    ])
    if warnings_df.empty:
        lines.append("No WARNING events found.")
    else:
        ts_width = 20  # Timestamp width
        desc_width = 50  # Description width
        lines.append(f"| {'Timestamp':<{ts_width}} | {'Event description':<{desc_width}} |")
        lines.append(f"|{'-'*(ts_width+2)}|{'-'*(desc_width+2)}|")
        for _, row in warnings_df.iterrows():
            ts = row.get("timestamp", "")
            desc = row.get("event_description", "")
            # Escape pipe in description for markdown table
            desc = str(desc).replace("|", "\\|")
            lines.append(f"| {str(ts):<{ts_width}} | {desc:<{desc_width}} |")
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
        ts_width = 20  # Timestamp width
        col_width = 20  # Column name width
        val_width = 10  # Value width
        limit_width = 15  # Limit width
        lines.append(
            f"| {'Timestamp':<{ts_width}} | {'Column':<{col_width}} | "
            f"{'Value':>{val_width}} | {'Limit (max/min)':<{limit_width}} |"
        )
        lines.append(f"|{'-'*(ts_width+2)}|{'-'*(col_width+2)}|{'-'*(val_width+2)}|{'-'*(limit_width+2)}|")
        for b in breaches:
            val = b["value"]
            if isinstance(val, float):
                val = round(val, 2)
            limit_str = f"{b['limit_type']}={b['limit_value']}"
            lines.append(
                f"| {str(b['timestamp']):<{ts_width}} | {b['column']:<{col_width}} | "
                f"{val:>{val_width}} | {limit_str:<{limit_width}} |"
            )
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")

#Building the numeric summary table, one row per numeric column with columns: column, mean, max, min (rounded)
#So if there are no numeric columns, it will return an empty dataframe
#If there are numeric columns, it will return a dataframe with the column, mean, max, and min
#It will also remove any duplicate numeric columns
def numeric_summary_table(df: pd.DataFrame) -> pd.DataFrame:
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

#The main function, it will parse the arguments, load the csv, validate the columns, coerce the numeric columns, build the speed statistics, get the warnings, get the threshold breaches, build the numeric summary table, and write the report
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
