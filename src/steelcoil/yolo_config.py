from pathlib import Path
from typing import Any
import yaml


def load_labels(labels_path: Path) -> dict[str, Any]:
    with Path(labels_path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_yolo_yaml(labels_path: Path, output_path: Path, dataset_root: Path) -> Path:
    labels = load_labels(labels_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "path": str(dataset_root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": labels["names"],
    }
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    return output_path
