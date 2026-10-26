import sys
from pathlib import Path

project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))

metadata_file = Path(__file__).parent / "metadata.txt"

with open(metadata_file, mode="r", encoding="utf-8") as file:
    for line in file:
        if line.startswith("version="):
            print(line.strip().split("=")[1])
            break
