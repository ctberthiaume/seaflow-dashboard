"""
Script to fill out a SeaFlow Grafana dashboard JSON file.

Fills in cruise time range, cruise name, and sets the dashboard UID to the
cruise name.
"""
import argparse
from pathlib import Path
import json
import sys
from typing import Any

def read_date_range(tsdata: Path | str) -> tuple[str, str]:
    min_stamp, max_stamp = "", ""
    with Path(tsdata).open() as fh:
        for i, line in enumerate(fh):
            if i > 6:
                # Skip first six lines (header section)
                # First column is always an RFC3339 timestamp
                # Can get min/max lexicographically, no timestamp parsing necessary
                fields = line.split("\t")
                if not fields:
                    raise ValueError(f"No data found in {tsdata}")
                if len(fields) >= 1:
                    stamp = fields[0]
                    if not min_stamp or stamp < min_stamp:
                        min_stamp = stamp
                    if not max_stamp or stamp > max_stamp:
                        max_stamp = stamp
    if not min_stamp or not max_stamp:
        raise ValueError(f"Could not determine date range in {tsdata}")
    return (min_stamp, max_stamp)


def replace_time_range(dash: dict[Any, Any], from_time: str, to_time: str):
    dash["time"]["from"] = from_time
    dash["time"]["to"] = to_time


def replace_cruise(dash: dict[Any, Any], cruise):
    dash["title"] = dash["title"].replace("CRUISE", cruise)
    for template_vars in dash["templating"]["list"]:
        if template_vars["name"] == "cruise":
            template_vars["current"]["text"] = cruise
            template_vars["current"]["value"] = cruise


def replace_uid(dash: dict[Any, Any], uid: str):
    dash["uid"] = uid


def get_cruise_from_underway_filename(fn: Path | str) -> str:
    fn = Path(fn)
    parts = fn.name.split(".")
    if len(parts) < 1:
        raise ValueError(f"could not parse cruise from underway filename: {fn.name}")
    cruise = parts[0].replace("-geo", "")
    return cruise


def template_dash(in_dash_file: Path | str, underway_file: Path | str, out_dir: Path | str):
    in_dash_file = Path(in_dash_file)
    underway_file = Path(underway_file)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create output dash JSON file name. Assuming template JSON file is named
    # CRUISE-ByTime.json or CRUISE-Ops.json or some variant, replace CRUISE
    # with the actual cruise name and write the file to the output directory.
    cruise = get_cruise_from_underway_filename(underway_file)
    out_dash_file = Path(in_dash_file.name.replace("CRUISE", cruise))
    out_dash_file = out_dir / out_dash_file
    
    with in_dash_file.open() as fh:
        dash = json.load(fh)
    replace_time_range(dash, *read_date_range(underway_file))
    replace_cruise(dash, cruise)
    # Use the output dashboard JSON file name, without .json ext, as dashboard
    # UID.
    replace_uid(dash, out_dash_file.stem)
    with Path(out_dash_file).open("wt") as fh:
        fh.write(json.dumps(dash, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="template-dash.py",
        description="""
            Create a cruise-specific version of a templated SeaFlow Grafana
            dashboard JSON file. Updates starting date range, dashboard title,
            and dashboard UID. The UID is changed to the template JSON filename
            without the .json extension, and with the text "CRUISE" replaced
            with the actual cruise name. e.g. If the template file is /dash/CRUISE-ByTime.json,
            the output filename would be out_dir/CMOP_3-ByTime.json for the
            CMOP_3 cruise.
        """
    )
    parser.add_argument("template_file", help="Template dashboard JSON file.")
    parser.add_argument("underway_file", help="Underway TSDATA file with RFC3339 timestamps in the first column.")
    parser.add_argument("out_dir", help="Output directory.")
    args = parser.parse_args()
    
    try:
        template_dash(args.template_file, args.underway_file, args.out_dir)
    except Exception as e:
        print(f"Error templating dashboard file: {e}")
        sys.exit(1)

