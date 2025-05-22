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


def replace_cruise(dash: dict[Any, Any], cruise):
    dash["title"] = dash["title"].replace("CRUISE", cruise)
    for template_vars in dash["templating"]["list"]:
        if template_vars["name"] == "cruise":
            template_vars["current"]["text"] = cruise
            template_vars["current"]["value"] = cruise


def replace_uid(dash: dict[Any, Any], uid: str):
    dash["uid"] = uid


def template_dash(in_dash_file: Path | str, cruise: str, out_dir: Path | str):
    in_dash_file = Path(in_dash_file)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create output dash JSON file name. Assuming template JSON file is named
    # CRUISE-ByTime.json or CRUISE-Ops.json or some variant, replace CRUISE
    # with the actual cruise name and write the file to the output directory.
    out_dash_file = Path(in_dash_file.name.replace("CRUISE", cruise))
    out_dash_file = out_dir / out_dash_file
    
    with in_dash_file.open() as fh:
        dash = json.load(fh)

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
            dashboard JSON file for realtime monitoring. Updates dashboard
            title and dashboard UID. The UID is changed to the template JSON
            filename without the .json extension, with the text "CRUISE"
            replaced with the actual cruise name. e.g. If the template file is
            /dash/CRUISE-ByTime-Realtime.json, the output UID would be
            CMOP_3-ByTime-Realtime and the output file path would be
            out_dir/CMOP_3-ByTime-Realtime.json.
        """
    )
    parser.add_argument("template_file", help="Template dashboard JSON file.")
    parser.add_argument("cruise", help="Cruise name.")
    parser.add_argument("out_dir", help="Output directory.")
    args = parser.parse_args()
    
    try:
        template_dash(args.template_file, args.cruise, args.out_dir)
    except Exception as e:
        print(f"Error templating dashboard file: {e}")
        sys.exit(1)

