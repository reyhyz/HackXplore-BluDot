import json
from pathlib import Path
from typing import List, Any


def get_all_values(parameter_name: str) -> List[Any]:
    """Traverses the data/output directory to collect all values associated

    with a specific parameter across all batches and their files.
    """
    values = []

    # Define the base output path relative to the project root
    # Since compute_statistics.py is in /utils, we go up one level to reach root
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "data" / "output"

    # Ensure the directory exists to prevent crashes
    if not output_dir.exists():
        print(f"Error: Output directory not found at {output_dir}")
        return values

    # Iterate through every batch subdirectory inside data/output
    for batch_dir in output_dir.iterdir():
        if batch_dir.is_dir():

            # Find all JSON files inside this batch directory (handles multiple files per batch)
            json_files = batch_dir.glob("*.json")

            for json_file_path in json_files:
                try:
                    with open(json_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                        # Adjust this parsing logic depending on your exact JSON layout.
                        # Scenario A: If your JSON is a direct flat dictionary: {"parameter": value}
                        if (
                            isinstance(data, dict)
                            and parameter_name in data
                        ):
                            values.append(data[parameter_name])

                        # Scenario B: If your JSON contains a key/list like 'extracted_data'
                        elif (
                            isinstance(data, dict)
                            and "extracted_data" in data
                        ):
                            for item in data["extracted_data"]:
                                if (
                                    item.get("parameter")
                                    == parameter_name
                                ):
                                    values.append(item.get("value"))

                except (json.JSONDecodeError, IOError) as e:
                    print(
                        f"Skipping malformed or unreadable file {json_file_path.name}: {e}"
                    )

    return values


