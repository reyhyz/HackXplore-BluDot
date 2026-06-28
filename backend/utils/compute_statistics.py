import json
import statistics
from pathlib import Path
from typing import Any, List


def get_all_values(section_id: str, parameter_name: str, sap_material: str, process_step: str) -> List[Any]:
    """
    Extracts parameter values safely out of files located in historical data paths:
    data/outputs/<sap_material>/<process_step>/*.json
    """
    values = []
    base_dir = Path(__file__).resolve().parent.parent
    target_dir = base_dir / "data" / "outputs" / sap_material / process_step

    if not target_dir.exists():
        return values

    for json_file in target_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                doc = json.load(f)
                
            # Safely trace down nested structured object: section -> parameter
            if isinstance(doc, dict) and section_id in doc:
                section = doc[section_id]
                if isinstance(section, dict) and parameter_name in section:
                    val = section[parameter_name]
                    if val is not None:
                        values.append(val)
        except (json.JSONDecodeError, IOError):
            continue

    return values

def calculate_mean(values: List[Any]) -> float:
    cleaned = [float(v) for v in values if v is not None and str(v).replace('.', '', 1).isdigit()]
    if not cleaned:
        raise ValueError("No numeric metrics found.")
    return float(statistics.mean(cleaned))

def calculate_stdev(values: List[Any]) -> float:
    cleaned = [float(v) for v in values if v is not None and str(v).replace('.', '', 1).isdigit()]
    if len(cleaned) < 2:
        return 0.0
    return float(statistics.stdev(cleaned))